"""Resolve and measure a failing test for an H-MAD governed write."""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import NamedTuple, Optional, Sequence, Tuple, Union

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from h_mad_audit_gate import _SGR_RE, _SUMMARY_LINE_RE  # noqa: E402

KINDS = frozenset({"red-measured", "no-test-resolved", "test-missing",
                   "venv-escapes-root", "pytest-missing", "pytest-error",
                   "no-tests-ran", "no-summary", "test-passing", "timeout",
                   "judge-error"})
STATE_VALUES = ("none", "active", "unreadable")
JUDGE_BUDGET_S = 40.0
ESCAPE_STATUSES = frozenset({"unavailable", "exhausted"})
NAME_MAP = Path(_HERE) / "h_mad_derive_test_path.sh"


class Record(NamedTuple):
    key: str
    codex_status: str
    state_file: Path
    fallback: str


class Chain(NamedTuple):
    value: str
    records: tuple
    error_file: Optional[Path]
    error: str


class Verdict(NamedTuple):
    decision: str
    kind: str
    reason: str
    source: str
    test: Optional[Path]


class Resolution(NamedTuple):
    source: str
    present: Tuple[Tuple[Path, Path], ...]
    missing: Tuple[Path, ...]
    notes: Tuple[str, ...]
    verdict: Optional[Verdict]


def _inside(path: str, root: str) -> bool:
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


def _enc(value: str) -> str:
    return urllib.parse.quote(value, safe="/._-") or "%"


def _state_at(path: Path) -> Tuple[str, object]:
    try:
        os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):  # M:C6
        return "absent", None
    except OSError as exc:
        return "unreadable", type(exc).__name__
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as exc:
        return "unreadable", type(exc).__name__
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):  # M:C4
            return "unreadable", "not-a-regular-file"
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = json.loads(stream.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        return "unreadable", type(exc).__name__
    finally:
        os.close(fd)
    if not isinstance(data, dict) or ("orchestrator_state" in data and
                                      not isinstance(data["orchestrator_state"], dict)):
        return "unreadable", "not-an-object"
    return "read", data


def _fallback_tag(state: dict) -> str:
    if "fallback_agent" not in state:
        return "absent"
    value = state["fallback_agent"]
    if isinstance(value, str):
        if value in ("grok", "claude"):
            return value
    elif value is None:
        return "null"
    return "invalid:" + json.dumps(value, separators=(",", ":"))


def _active_records(data: dict, path: Path) -> Tuple[Record, ...]:
    states = data.get("orchestrator_state", {})
    return tuple(Record(str(key), "available" if value.get("codex_status") is None
                        else str(value["codex_status"]), path, _fallback_tag(value))
                 for key, value in states.items()
                 if isinstance(value, dict) and value.get("phase") == "step5")


def read_chain(root: Path, target: Optional[Path]) -> Chain:
    real_root = Path(os.path.realpath(root))
    dirs = [real_root]
    if target is not None:
        parent = Path(os.path.realpath(target.parent))
        if _inside(str(parent), str(real_root)):
            dirs = []
            while True:
                dirs.append(parent)
                if parent == real_root:
                    break
                parent = parent.parent
        else:
            dirs = [real_root]  # M:H14
    records = []
    for directory in dirs:
        path = directory / "docs" / ".bkit-memory.json"
        status, data = _state_at(path)
        if status == "absent":
            continue
        if status == "unreadable":
            return Chain("unreadable", (), path, data)  # M:C2
        records.extend(_active_records(data, path))  # M:C1
    return Chain("active" if records else "none", tuple(records), None, "")


def _deny(kind: str, reason: str) -> Verdict:
    return Verdict("DENY", kind, reason, "", None)


def _notes(notes: Sequence[str]) -> str:
    return "; " + "; ".join(notes) if notes else ""


def _display(path: Path, root: Path) -> str:
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    return Path(real_path).relative_to(real_root).as_posix() if _inside(real_path, real_root) else real_path


def _listing(paths: Sequence[Path], root: Path) -> str:
    return ", ".join(_display(path, root) for path in paths)


def _test_missing(candidates: Sequence[Path], notes: Sequence[str], root: Path) -> Verdict:
    return _deny("test-missing", f"no resolved test file exists ({_listing(candidates, root)}); author the failing test first{_notes(notes)}")  # M:R3


def _is_present(path: Path) -> bool:
    try:
        return stat.S_ISREG(os.stat(path).st_mode)
    except OSError:
        return False


def _run_bounded(argv: Sequence[str], cwd: Path, deadline: float) -> Tuple[Optional[int], str, str, bool, str]:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return None, "", "", True, ""
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
    except OSError as exc:
        return None, "", "", False, f"{type(exc).__name__}: {exc}"
    try:
        out, err = proc.communicate(timeout=remaining)
        timed_out = False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = proc.communicate()
        timed_out = True
    return proc.returncode, out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace"), timed_out, ""


def resolve(root: Path, target: Path, records: Sequence[Record], *, deadline: float) -> Resolution:
    real_root = Path(os.path.realpath(root))
    real_target = Path(os.path.realpath(target))
    notes = []
    candidates = []
    seen_candidates = set()
    matched = False
    plan_paths = list(dict.fromkeys(record.state_file.parent / "01-plan" / "features" /
                                    f"{record.key}.impl-plan.md" for record in records))
    for plan in plan_paths:
        try:
            text = plan.read_text(encoding="utf-8")
        except FileNotFoundError:
            notes.append(f"{plan}: absent")
            continue
        except (OSError, UnicodeDecodeError) as exc:
            notes.append(f"{plan}: impl-plan unreadable: {type(exc).__name__}")
            continue
        tasks = []  # M:W3
        plan_matched = False
        for task in tasks:
            if not _inside(str(real_target), str(real_root)):
                continue
            base = real_target.parent
            while _inside(str(base), str(real_root)):
                if any(os.path.realpath(base / entry) == str(real_target) for entry in task.production):
                    matched = plan_matched = True
                    for entry in task.tests:
                        candidate = Path(os.path.realpath(base / entry))
                        if not _inside(str(candidate), str(real_root)):
                            notes.append(f"candidate outside root dropped: {entry}")
                        elif candidate not in seen_candidates:
                            candidates.append((candidate, base))
                            seen_candidates.add(candidate)
                    break
                if base == real_root:
                    break
                base = base.parent
        notes.append(f"{plan}: {'matched' if plan_matched else 'matched none'}")
    present = [c for c in candidates if _is_present(c[0])]  # M:R4
    missing = tuple(c[0] for c in candidates if not _is_present(c[0]))
    if matched:  # M:R1
        if not present:
            return Resolution("impl-plan", (), missing, tuple(notes), _test_missing(missing, notes, root))
        return Resolution("impl-plan", tuple(present), missing, tuple(notes), None)
    if not _inside(str(real_target), str(real_root)):
        notes.append("name map: target outside root")
        return Resolution("", (), (), tuple(notes), _deny("no-test-resolved", "no test resolved" + _notes(notes)))
    rel = real_target.relative_to(real_root).as_posix()
    returncode, out, err, timed_out, error = _run_bounded(["bash", str(NAME_MAP), rel], real_root, deadline)
    mapped = out.strip()  # M:R5
    if timed_out:
        return Resolution("", (), (), tuple(notes), _deny("timeout", "name map timed out" + _notes(notes)))
    if not mapped:
        notes.append(f"name map: empty for {rel}")
        return Resolution("", (), (), tuple(notes), _deny("no-test-resolved", "no test resolved" + _notes(notes)))
    mapped_path = Path(os.path.realpath(real_root / mapped))
    if not _inside(str(mapped_path), str(real_root)):
        notes.append("name map: target outside root")
        return Resolution("", (), (), tuple(notes), _deny("no-test-resolved", "no test resolved" + _notes(notes)))
    notes.append(f"name map: {mapped_path}")
    if not _is_present(mapped_path):
        return Resolution("name-map", (), (mapped_path,), tuple(notes), _test_missing((mapped_path,), notes, root))
    return Resolution("name-map", ((mapped_path, real_root),), (), tuple(notes), None)


def venv_contained(venv_parent: Path, root: Path) -> bool:
    venv = venv_parent / ".venv"
    real_root = os.path.realpath(root)
    if not _inside(os.path.realpath(venv), real_root):  # M:V1
        return False
    if not _inside(os.path.realpath(venv / "bin"), real_root):  # M:V2
        return False
    try:
        return stat.S_ISREG(os.lstat(venv / "pyvenv.cfg").st_mode)  # M:V3
    except OSError:
        return False


def select_interpreter(test: Path, root: Path, fallback: str) -> Union[str, Verdict]:
    real_root = Path(os.path.realpath(root))
    directory = test.parent
    while _inside(os.path.realpath(directory), str(real_root)):
        python = directory / ".venv" / "bin" / "python"
        if os.path.lexists(python):
            if venv_contained(directory, real_root):
                return str(python)
            venv = directory / ".venv"
            return _deny("venv-escapes-root", f"venv {venv} is not contained in root (realpath {os.path.realpath(venv)})")
        if os.path.realpath(directory) == str(real_root):
            break
        directory = directory.parent
    return fallback


def _pytest_missing(output: str) -> bool:
    return any(_SGR_RE.sub("", line).strip().endswith(": No module named pytest")
               for line in output.splitlines())


def score(proc_output: str, timed_out: bool) -> str:
    if timed_out:
        return "timeout"
    if _pytest_missing(proc_output):  # M:K1
        return "pytest-missing"
    summary = None  # M:W4
    if summary is None:
        return "no-summary"
    if summary.no_tests_ran:
        return "no-tests-ran"
    if summary.errors >= 1:  # M:K2
        return "pytest-error"
    if summary.failed >= 1:
        return "red-measured"
    if summary.passed >= 1:
        return "test-passing"
    return "no-tests-ran"  # M:K4


def _output_entry(output: str, error: str) -> str:
    if error:
        return error
    last = ""
    summary = ""
    for raw in output.splitlines():
        line = _SGR_RE.sub("", raw).strip()
        if line:
            last = line
        clean = line.strip("=").strip()
        if _SUMMARY_LINE_RE.match(clean):
            summary = clean
    return summary or last


def judge(root: Path, target: Path, records: Sequence[Record], *, budget_s: float = JUDGE_BUDGET_S,
          fallback_interpreter: str = sys.executable) -> Verdict:
    deadline = time.monotonic() + budget_s
    resolution = resolve(root, target, records, deadline=deadline)
    if resolution.verdict is not None:
        return resolution.verdict
    outcomes = []
    for test, cwd in resolution.present:
        interpreter = select_interpreter(test, root, fallback_interpreter)
        if isinstance(interpreter, Verdict):
            return interpreter._replace(reason=interpreter.reason + _notes(resolution.notes))
        argv = [interpreter, "-m", "pytest", str(test), "-x", "-q", "--no-header"]
        returncode, out, err, timed_out, error = _run_bounded(argv, cwd, deadline)
        kind = "no-summary" if error else score(out + "\n" + err, timed_out)  # M:K3
        entry = _output_entry(out + "\n" + err, error)
        outcomes.append((test, kind, returncode, entry))
        if kind == "red-measured":
            return Verdict("ALLOW", kind, "", resolution.source, test)
        if kind in ("venv-escapes-root", "timeout", "pytest-missing"):
            break
    kinds = [item[1] for item in outcomes]
    kind = next((name for name in ("timeout", "pytest-missing", "pytest-error", "no-summary",
                                   "no-tests-ran", "test-passing") if name in kinds), "no-summary")
    details = [f"{_display(test, root)}: {result} (rc={rc}; {entry})"
               for test, result, rc, entry in outcomes]
    details.extend(f"{_display(test, root)}: missing" for test in resolution.missing)
    reason = "; ".join(details)
    if kind == "pytest-error":
        reason += "; import error inside the test body"
    return _deny(kind, reason + _notes(resolution.notes))


def format_state_line(chain: Chain, root: Path) -> str:
    if chain.value == "none":
        return "TDD-STATE: none"
    if chain.value == "unreadable":
        return f"TDD-STATE: unreadable file={_enc(str(chain.error_file))} error={chain.error}"
    escape = bool(chain.records) and all(r.codex_status in ESCAPE_STATUSES for r in chain.records)  # M:C3
    blocker = next((i for i, r in enumerate(chain.records, 1) if r.codex_status not in ESCAPE_STATUSES), 0)  # M:C5
    line = f"TDD-STATE: active codex-escape={'yes' if escape else 'no'} blocker={blocker} records={len(chain.records)}"
    for record in chain.records:
        fallback = record.fallback
        if fallback.startswith("invalid:"):
            fallback = "invalid:" + _enc(fallback[len("invalid:"):])
        line += f" record={_enc(record.key)},{_enc(record.codex_status)},{_enc(str(record.state_file))},{fallback}"
    return line


def format_verdict_line(verdict: Verdict, root: Path) -> str:
    if verdict.decision == "ALLOW":
        return f"TDD-JUDGE: ALLOW kind={verdict.kind} source={verdict.source} test={_enc(_display(verdict.test, root))}"
    reason = re.sub(r"[\x00-\x1f\x7f]", " ", verdict.reason)
    return f"TDD-JUDGE: DENY kind={verdict.kind} reason={reason}"


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("state", "judge"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--target")
    args = parser.parse_args(argv)
    if not args.root or not Path(args.root).is_dir():
        parser.error("--root must name a directory")
    root = Path(os.path.realpath(args.root))
    target = root / args.target if args.target else None
    try:
        chain = read_chain(root, target)
        if args.command == "state":
            print(format_state_line(chain, root))
            return 0
        if chain.value != "active":
            verdict = _deny("judge-error", f"chain is {chain.value} at judge time")
        else:
            verdict = judge(root, target or root, chain.records)
    except Exception as exc:
        if args.command == "state":
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        verdict = _deny("judge-error", f"{type(exc).__name__}: {exc}")
    print(format_verdict_line(verdict, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
