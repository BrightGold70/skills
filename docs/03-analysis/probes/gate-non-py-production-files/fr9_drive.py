"""Drive one host's real TDD hook against the FR-9 fixture or incident replay.

Run with python3.11 -I from the checkout being measured. This probe uses only
the standard library; pytest must be available to that interpreter's venvs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


PLAN = "docs/01-plan/features/exec-missing-report-recovery.impl-plan.md"
HOOKS = {
    "claude": "h-mad/hooks/h-mad-tdd-gate.sh",
    "codex": "h-mad/hooks/h-mad-codex-tdd-gate.py",
    "agy": "h-mad/hooks/h-mad-agy-tdd-gate.py",
}
AUTHOR = "TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env"


class Refusal(Exception):
    """A declared cannot-judge condition, rather than a measured FAIL."""


def _environment() -> dict[str, str]:
    # Match hermetic() in hmad-verify.sh; inherit no GIT_* or HMAD_* knobs.
    return {
        "HOME": os.environ["HOME"],
        "PATH": os.environ["PATH"],
        "LANG": os.environ.get("LANG") or "en_US.UTF-8",
        "TMPDIR": os.environ.get("TMPDIR") or "/tmp",
    }


def _run(argv: list[str], cwd: Path, *, env: dict | None = None,
         data: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, env=_environment() if env is None else env,
                          input=data, capture_output=True, timeout=90, check=check)


def _git(top: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return _run(["git", *args], top, check=check)


def _value(proc: subprocess.CompletedProcess) -> str:
    return proc.stdout.decode("utf-8").strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def _refuse(reason: str) -> int:
    print(f"FR9-DRIVE: UNREADABLE {reason}")
    return 2


def _replay_base(top: Path) -> str:
    result = _git(top, "merge-base", "HEAD", "origin/main", check=False)
    if result.returncode != 0 or not result.stdout.strip():  # M:D-MISSING-BASE
        raise Refusal("missing-base")
    base = _value(result)
    if base == _value(_git(top, "rev-parse", "HEAD")):  # M:D-BASE-IS-HEAD
        raise Refusal("base-is-head")
    return base


def _check_hook_identity(top: Path, hook: Path) -> dict:
    if _git(top, "status", "--porcelain", "--", "h-mad").stdout.strip():  # M:D-DIRTY-HOOKS
        raise Refusal("dirty-hooks")
    realpath = hook.resolve()
    if not realpath.is_relative_to(top):  # M:D-HOOK-OUTSIDE-TREE
        raise Refusal("hook-outside-tree")
    path = hook.relative_to(top).as_posix()
    committed = _git(top, "rev-parse", f"HEAD:{path}", check=False)
    hashed = _git(top, "hash-object", str(hook), check=False)
    if committed.returncode or hashed.returncode or _value(hashed) != _value(committed):  # M:D-HOOK-BLOB
        raise Refusal("hook-blob-mismatch")
    return {"path": str(hook), "realpath": str(realpath), "sha256": _sha256(hook),
            "source_commit": _value(_git(top, "rev-parse", "HEAD")),
            "blob": _value(committed), "hash_object": _value(hashed)}


def _copy_plan(top: Path, base: str, root: Path) -> dict:
    result = _git(top, "cat-file", "blob", f"{base}:{PLAN}", check=False)
    if result.returncode != 0:  # M:D-PLAN-ABSENT
        raise Refusal("plan-absent-at-base")
    plan = root / PLAN
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_bytes(result.stdout)
    blob = _value(_git(top, "rev-parse", f"{base}:{PLAN}"))
    # Source checkout cwd is deliberate: core.autocrlf can change this hash.
    hashed = _value(_git(top, "hash-object", str(plan)))
    if hashed != blob:  # M:D-PLAN-BLOB
        raise Refusal("plan-blob-mismatch")
    return {"source_commit": base, "path": PLAN, "plan_blob": blob,
            "copy_sha256": _sha256(plan), "copy_blob": hashed}


def _check_authorship(judge: Path, root: Path, key: str, env: dict, out: Path) -> None:
    result = _run(["python3", str(judge), "implementer", "--root", str(root),
                   "--feature", key], root, env=env, check=False)
    (out / "implementer.txt").write_bytes(result.stdout)
    if result.stdout.decode("utf-8").splitlines() != [AUTHOR]:  # M:D-AUTHORSHIP
        raise Refusal("authorship-line")


def _write(root: Path, name: str, content: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prepare(root: Path, scenario: str) -> tuple[str, str, list[tuple]]:
    (root / ".agents").mkdir()
    _git(root, "init", "--quiet")
    if scenario == "fixture":
        key, test = "f", "tests/test_tool.py"
        _write(root, "docs/01-plan/features/f.impl-plan.md",
               "## Task 1: tool\n**Task shape**: `new-behaviour`\n"
               "**Production file**: `scripts/tool.sh`, `bin/launch`, `README.md`, `CHANGES.MD`\n"
               "**Test file**: `tests/test_tool.py`\n")
        for name in ("scripts/tool.sh", "bin/launch", "scripts/other.sh", "README.md", "CHANGES.MD"):
            _write(root, name, "x\n")
        rows = [("listed-absent", "scripts/tool.sh", False),
                ("listed-failing", "scripts/tool.sh", True),
                ("unlisted-absent", "scripts/other.sh", False)]
    else:
        key, test = "exec-missing-report-recovery", "h-mad/tests/test_hmad_dispatch_exec.py"
        for name in ("h-mad/scripts/hmad-dispatch.sh", "h-mad/SKILL.md",
                     "h-mad/scripts/h_mad_derive_test_path.sh"):
            _write(root, name, "x\n")
        rows = [("listed-absent", "h-mad/scripts/hmad-dispatch.sh", False),
                ("listed-failing", "h-mad/scripts/hmad-dispatch.sh", True),
                ("unlisted-absent", "h-mad/scripts/h_mad_derive_test_path.sh", False),
                ("doc-absent", "h-mad/SKILL.md", False)]
    state = root / "docs/.bkit-memory.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    _json(state, {"orchestrator_state": {key: {"phase": "step5"}}})
    return key, test, rows


def _payload(host: str, root: Path, target: str) -> dict:
    if host == "claude":
        return {"tool_name": "Write", "tool_input": {
            "file_path": str(root / target), "content": "x"}}
    if host == "codex":
        return {"tool_name": "apply_patch", "tool_input": {"command":
                f"*** Begin Patch\n*** Update File: {target}\n@@\n-x\n+y\n*** End Patch\n"},
                "cwd": str(root)}
    return {"toolCall": {"name": "write_to_file", "args": {"TargetFile": str(root / target)}},
            "workspacePaths": [str(root)]}


def _verdict(host: str, result: subprocess.CompletedProcess) -> tuple[str, str]:
    # A crash, malformed JSON or unexpected stdout must never count as ALLOW.
    if result.returncode != 0:
        return "ERROR", ""
    if host != "agy" and result.stdout == b"":
        return "ALLOW", ""
    try:
        value = json.loads(result.stdout)
        if host == "agy":
            if value == {"decision": "allow"}:
                return "ALLOW", ""
            if value.get("decision") != "deny":
                return "ERROR", ""
            reason = value.get("reason", "")
        else:
            hook = value["hookSpecificOutput"]
            if hook["permissionDecision"] != "deny":
                return "ERROR", ""
            reason = hook["permissionDecisionReason"]
        kinds = re.findall(r"\bkind=([a-z-]+)", reason)
        return ("DENY", kinds[0]) if len(kinds) == 1 else ("ERROR", "")
    except (ValueError, KeyError, TypeError, AttributeError):
        return "ERROR", ""


def _drive(args: argparse.Namespace, top: Path, base: str | None,
           hook_info: dict | None) -> int:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fr9-drive-", dir=_environment()["TMPDIR"]) as temp:
        scratch = Path(temp).resolve()
        root = scratch / "root"
        root.mkdir()
        plan_info = _copy_plan(top, base, root) if base else {}
        if args.side == "before":
            before = scratch / "before"
            before.mkdir()
            archive = _git(top, "archive", base, "h-mad").stdout
            _run(["tar", "-x", "-C", str(before)], scratch, data=archive)
            hook = before / HOOKS[args.host]
            hook_info = {"path": str(hook), "realpath": str(hook.resolve()),
                         "sha256": _sha256(hook), "source_commit": base,
                         "blob": _value(_git(top, "rev-parse", f"{base}:{HOOKS[args.host]}")),
                         "hash_object": _value(_git(top, "hash-object", str(hook)))}
        else:
            hook = top / HOOKS[args.host]
        key, test, rows = _prepare(root, args.scenario)
        env = _environment()
        if args.host == "claude":
            env.update(CLAUDE_PROJECT_DIR=str(root), HMAD_CODEX_UNAVAILABLE="1",
                       HMAD_AGY_UNAVAILABLE="1")
        _run([sys.executable, "-I", "-m", "venv", "--without-pip",
              "--system-site-packages", str(root / ".venv")], root)
        python3 = shutil.which("python3", path=env["PATH"])
        python_version = _value(_run(["python3", "--version"], root, env=env))
        provenance = {"scenario": args.scenario, "side": args.side, "host": args.host,
                      "commit_under_test": _value(_git(top, "rev-parse", "HEAD")),
                      "base": base, **plan_info, "hook": hook_info,
                      "python3": {"realpath": str(Path(python3).resolve()), "version": python_version},
                      "interpreter": {"path": sys.executable, "realpath": os.path.realpath(sys.executable),
                                      "version": sys.version, "venv": str(root / ".venv/bin/python")}}
        provenance_path = out / "provenance.json"
        invocations = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else []
        invocations.append(provenance)
        _json(provenance_path, invocations)
        number = max((int(p.name.split("-", 1)[0]) for p in out.iterdir()
                      if p.is_dir() and p.name.split("-", 1)[0].isdigit()), default=0)
        mismatched = 0
        with (out / "readings.tsv").open("a", encoding="utf-8", newline="") as readings:
            writer = csv.writer(readings, delimiter="\t")
            for case, target, failing in rows:
                number += 1
                evidence = out / f"{number:03d}-{args.scenario}-{args.side}-{args.host}-{case}"
                evidence.mkdir()
                test_path = root / test
                if failing:
                    _write(root, test, "def test_red(): assert False\n")
                else:
                    test_path.unlink(missing_ok=True)
                payload = _payload(args.host, root, target)
                argv = ["/bin/bash" if args.host == "claude" else "python3", str(hook)]
                cwd = root / ".agents" if args.host == "agy" else root
                _json(evidence / "stdin.json", payload)
                _json(evidence / "argv.json", argv)
                _json(evidence / "env.json", env)
                _json(evidence / "hook.json", hook_info)
                _json(evidence / "cwd.json", str(cwd))
                if args.host == "claude":
                    _check_authorship(hook.parent.parent / "scripts/h_mad_tdd_judge.py",
                                      root, key, env, evidence)
                result = _run(argv, cwd, env=env, data=json.dumps(payload).encode("utf-8"), check=False)
                (evidence / "stdout").write_bytes(result.stdout)
                (evidence / "stderr").write_bytes(result.stderr)
                (evidence / "rc").write_text(str(result.returncode) + "\n", encoding="utf-8")
                expected = ("DENY", "test-missing") if case == "listed-absent" and args.side == "after" else ("ALLOW", "")
                actual = _verdict(args.host, result)
                matched = actual == expected
                mismatched += not matched
                writer.writerow([number, args.scenario, args.side, args.host, case, target,
                                 "failing" if failing else "absent", *expected, *actual,
                                 result.returncode, "PASS" if matched else "FAIL",
                                 json.dumps(result.stdout.decode("utf-8", errors="replace"), ensure_ascii=False)])
    verdict = "FAIL" if mismatched else "PASS"
    print(f"FR9-DRIVE: {verdict} rows={len(rows)} mismatched={mismatched}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=("fixture", "replay"))
    parser.add_argument("--side", required=True, choices=("after", "before"))
    parser.add_argument("--host", required=True, choices=("claude", "codex", "agy"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.scenario == "fixture" and args.side == "before":  # M:D-NO-BEFORE-SIDE
            raise Refusal("no-before-side")
        top = Path(_value(_git(Path.cwd(), "rev-parse", "--show-toplevel"))).resolve()
        base = _replay_base(top) if args.scenario == "replay" else None
        hook_info = _check_hook_identity(top, top / HOOKS[args.host]) if args.side == "after" else None
        return _drive(args, top, base, hook_info)
    except Refusal as exc:
        return _refuse(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
