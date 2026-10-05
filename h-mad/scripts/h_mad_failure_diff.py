#!/usr/bin/env python3
"""h_mad_failure_diff.py — diff a change's failure SET against a clean control.

A failure on a branch has two readings with opposite consequences: the change
caused it, or the tree fails that way anyway (pre-existing, environmental, load).
Seven sessions settled it by hand — `git worktree add --detach <scratch> <base>`,
rerun the same selection there, diff the FAILED node ids — and the comparison was
rebuilt per feature each time (row 2364). This is that comparison, once.

    run   --base <ref> [--subject <dir>] [--repeat N] [--log-dir DIR] -- <selection…>
          Runs the selection on the subject tree and on a throwaway detached
          worktree at <ref>. The selection is relative to the subject's toplevel,
          where pytest runs. Runs are interleaved (subject, control, subject, …)
          so load drift lands on both sides, and strictly SERIAL — see below.
          The control is removed on every path (return, exception,
          SIGTERM/SIGHUP/SIGINT), and only its own worktree entry is deleted,
          never by a repo-wide `git worktree prune`; a control that could not be
          removed turns the token into UNREADABLE. Each run's full output is
          kept and named on its `RUN:` line (`log=`), so an attributed id is
          investigated from the run that produced it.
    logs  --run <pytest log> --control <pytest log | id list>
          Compares two existing readings. An id list is one node id per line
          (`#` comments and blank lines ignored), as in `baseline_failures.txt`.

Output: one line per node id, then the token as the LAST line.

    SUBJECT_ONLY <id>       fails on every subject run, no control run — or fails
                            on both but differently (`subject=ERROR control=FAILED`)
    BOTH <id>               fails the same way on every run of both sides:
                            pre-existing or environmental
    CONTROL_ONLY <id>       fails on every control run, no subject run
    FLAKY <id> subject=k/N control=k/N
                            fails in some but not all runs of a side, or fails on
                            every run with a kind that varies (`kind=varies`);
                            never attributed

    FAILDIFF: SAME       subject_only=0 both=<b> control_only=0 flaky=0 runs=N   exit 0
    FAILDIFF: NEW        subject_only=<k> …                                       exit 1
    FAILDIFF: FLAKY      subject_only=0 … flaky=<f>                               exit 3
    FAILDIFF: FIXED_ONLY subject_only=0 control_only=<c> flaky=0 …                exit 0
    FAILDIFF: UNREADABLE reason=<r> side=<subject|control|run|both> [run=i/N]     exit 2

NEW outranks FLAKY (a flake beside a real new failure does not hide it), FLAKY
outranks FIXED_ONLY. Read the token, never `$?`. A FAILED and an ERROR are both
failures and both kept; their kind is compared too, because a change that turns
an assertion failure into a setup error has broken something new.

Fail closed — each of these is UNREADABLE, never "no new failures":
  * `suite-busy`: the session was refused by the tree lock (`SUITE: BUSY` with
    exit 75, `h_mad_audit_gate.suite_busy_line`). It measured nothing.
  * `crashed` (killed by a signal), `launch-failed`, `timeout`, `interrupted`.
    A timeout or a signal kills pytest's whole process group: a SIGKILLed
    pytest never reaches the conftest's leak reaper.
  * `collection-error` (an `Interrupted:` banner or exit 2), `internal-error`,
    `usage-error`, `no-tests-ran`, `all-skipped`, any other exit as `exit-<rc>`;
  * `stopped-early`: `-x`/`--maxfail` stopped the run (`stopping after N
    failures`). Both sets are then prefixes, and a new failure behind the first
    one is never reached;
  * `no-summary`: no pytest summary line, the shape of a run cut off mid-way;
  * `count-mismatch`: the FAILED/ERROR lines disagree with the summary counts or
    with the exit code — the set read is not the whole set;
  * `control-imports-subject`: the control's interpreter has a path inside the
    SUBJECT on `sys.path` (a `.pth` file, the shape of an editable install), or
    a PEP 660 `__editable__*` file in its site directories names the subject.
    The control would then measure the subject's code and the two would agree
    (HemaSuite 2026-09-16: two readings through one instrument agree). The
    interpreter's own prefix is exempt, so an in-tree `.venv` is usable. An
    absolute `PYTHONPATH` entry inside the subject is rewritten to the control's
    copy instead. Not seen: any other import hook that maps a package to the
    subject (a custom `sitecustomize`, a non-`__editable__` finder), and a
    NON-editable `pip install .` of the subject, which both sides import as
    the same installed snapshot;
  * `probe-failed`: that check could not read the control interpreter;
  * `disjoint-ids` (logs mode only): two non-empty sets with no id in common, the
    collection-root mismatch of row 1880. In run mode both sides run one
    selection from the same relative root by construction, so it does not apply.

Only the short test summary section is read — for `FAILED`/`ERROR` lines and
for the `Interrupted:`/`stopping after` banners: a test that prints a pytest log
of its own puts those lines in the FAILURES section, and they are not this run's.
Node ids may carry brackets and spaces (`test_p[a b]`); an id containing `] - `
is ambiguous in pytest's own summary format and may be cut short.

Serial, on purpose. The control is its own git toplevel, so its session takes
its OWN tree lock and is never refused by the subject's. That is lock
independence, not isolation: the h-mad conftest removes `/tmp/audit_*_run*`
files created during its session, and `/tmp` is shared, so two sessions at once
— on any toplevels — can delete each other's files and manufacture failures.
The sides therefore never overlap. Other sessions' suites on the same machine
race the same way, which this tool cannot prevent; that load is one reason
`--repeat` and FLAKY exist.

Where the control lives matters. A `/tmp` worktree fails path-coupled tests
(skills 2026-07-29) and a detached worktree has no gitignored `.venv`
(HemaSuite learnings 2026-09-08), so a control can fail for reasons the subject
does not share. The control is therefore created BESIDE the subject's toplevel
by default (`--control-parent` overrides), the run uses one interpreter for both
sides (`--python`), and its path is printed — flushed — on the `CONTROL:` line.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from h_mad_audit_gate import _suite_summary, suite_busy_line

EXIT = {"SAME": 0, "FIXED_ONLY": 0, "NEW": 1, "UNREADABLE": 2, "FLAKY": 3}

_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")
_SHORT_SUMMARY_RE = re.compile(r"^=+ short test summary info =+$")
# `[^\s\[]+` is the path::name part; the optional bracket group is the
# parametrize id, matched lazily so a ` - message` that itself holds brackets
# is not swallowed, while backtracking still admits a `]` inside the id.
_RESULT_RE = re.compile(r"^(?P<kind>FAILED|ERROR) (?P<id>[^\s\[]+(?:\[.*?\])?)(?: - .*)?$")
_INTERRUPTED_RE = re.compile(r"^!+ Interrupted: .*!+$", re.MULTILINE)
_STOPPED_RE = re.compile(r"^!+ stopping after \d+ failures? !+$", re.MULTILINE)
_EXIT_REASON = {2: "collection-error", 3: "internal-error", 4: "usage-error",
                5: "no-tests-ran"}
PYTEST_FLAGS = ["-q", "-rfE", "-p", "no:cacheprovider"]

# Set by the signal handler, read by the run loop. The handler never raises:
# an exception raised asynchronously can land inside the cleanup and leak the
# control (review of 8d2901be, M2), so it records the signal and kills the
# running pytest's process group, and the loop stops at its next check.
_STATE: dict = {"stop": None, "child": None}


class Unreadable(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def failure_set(output: str, rc: int | None = None) -> tuple[dict[str, str], object]:
    """{node id: kind} for one pytest run, and its summary.

    The kind is `FAILED`, `ERROR`, or `ERROR+FAILED` for a test that failed and
    also errored in teardown. `rc` is None for a stored log, whose exit code is
    unknown.
    """
    text = _SGR_RE.sub("", output)
    if rc is not None:
        if suite_busy_line(rc, text):
            raise Unreadable("suite-busy")
        if rc < 0:
            raise Unreadable("crashed")
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if _SHORT_SUMMARY_RE.match(line.strip())]
    tail = lines[starts[-1] + 1:] if starts else lines
    tail_text = "\n".join(tail)
    if _INTERRUPTED_RE.search(tail_text):
        raise Unreadable("collection-error")
    if rc is not None and rc not in (0, 1):
        raise Unreadable(_EXIT_REASON.get(rc, f"exit-{rc}"))
    summary = _suite_summary(text)
    if summary is None:
        raise Unreadable("no-summary")
    if summary.no_tests_ran or summary.passed + summary.failed + summary.errors == 0:
        raise Unreadable("all-skipped" if "skipped" in summary.phrases else "no-tests-ran")
    if _STOPPED_RE.search(tail_text):
        raise Unreadable("stopped-early")
    failed, errors = [], []
    kinds: dict[str, set[str]] = {}
    for line in tail if starts else []:
        match = _RESULT_RE.match(line.rstrip())
        if match:
            (failed if match["kind"] == "FAILED" else errors).append(match["id"])
            kinds.setdefault(match["id"], set()).add(match["kind"])
    if len(failed) != summary.failed or len(errors) != summary.errors:
        raise Unreadable("count-mismatch")
    if rc is not None and (rc == 1) != bool(failed or errors):
        raise Unreadable("count-mismatch")
    return {node: "+".join(sorted(kind)) for node, kind in kinds.items()}, summary


def _id_list(text: str) -> dict[str, str] | None:
    ids = [line.strip() for line in text.splitlines()
           if line.strip() and not line.strip().startswith("#")]
    if ids and all("::" in node for node in ids):
        return {node: "" for node in ids}   # kind unknown: never compared
    return None


def classify(subject_runs: list[dict[str, str]], control_runs: list[dict[str, str]],
             runs: int) -> int:
    s_always = set.intersection(*(set(run) for run in subject_runs))
    s_ever = set.union(*(set(run) for run in subject_runs))
    c_always = set.intersection(*(set(run) for run in control_runs))
    c_ever = set.union(*(set(run) for run in control_runs))
    flaky = (s_ever - s_always) | (c_ever - c_always)

    def kinds(node: str, side_runs: list[dict[str, str]]) -> set[str]:
        return {run[node] for run in side_runs if run.get(node)}

    # A failure whose KIND is not constant across one side's runs (FAILED on one
    # run, ERROR on the next) is an unstable failure mode: a flake, never
    # attributed by comparing kinds (review round 2, S2).
    unstable = {node for node in s_always & c_always
                if len(kinds(node, subject_runs)) > 1 or len(kinds(node, control_runs)) > 1}
    flaky |= unstable
    subject, control = s_always - flaky, c_always - flaky

    def kind(node: str, side_runs: list[dict[str, str]]) -> str:
        return "+".join(sorted(kinds(node, side_runs)))

    changed = {node: (kind(node, subject_runs), kind(node, control_runs))
               for node in subject & control}
    changed = {node: pair for node, pair in changed.items() if all(pair) and pair[0] != pair[1]}
    subject_only = (subject - control) | set(changed)
    both, control_only = (subject & control) - set(changed), control - subject
    for node in sorted(subject_only):
        if node in changed:
            print(f"SUBJECT_ONLY {node} subject={changed[node][0]} control={changed[node][1]}")
        else:
            print(f"SUBJECT_ONLY {node}")
    for node in sorted(both):
        print(f"BOTH {node}")
    for node in sorted(control_only):
        print(f"CONTROL_ONLY {node}")
    for node in sorted(flaky):
        s_hits = sum(node in run for run in subject_runs)
        c_hits = sum(node in run for run in control_runs)
        print(f"FLAKY {node} subject={s_hits}/{len(subject_runs)} "
              f"control={c_hits}/{len(control_runs)}"
              + (" kind=varies" if node in unstable else ""))
    if subject_only:
        verdict = "NEW"
    elif flaky:
        verdict = "FLAKY"
    elif control_only:
        verdict = "FIXED_ONLY"
    else:
        verdict = "SAME"
    print(f"FAILDIFF: {verdict} subject_only={len(subject_only)} both={len(both)} "
          f"control_only={len(control_only)} flaky={len(flaky)} runs={runs}")
    return EXIT[verdict]


def _unreadable(reason: str, side: str, run: str = "", tail: str = "",
                log: Path | None = None) -> int:
    for line in tail.splitlines()[-15:]:
        print(f"  | {line}")
    if log is not None:
        print(f"  log={log}")
    suffix = f" run={run}" if run else ""
    print(f"FAILDIFF: UNREADABLE reason={reason} side={side}{suffix}")
    return EXIT["UNREADABLE"]


# --- logs mode ---------------------------------------------------------------

def logs_mode(args) -> int:
    sets = {}
    for side, path, ids_ok in (("run", args.run, False), ("control", args.control, True)):
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return _unreadable("unreadable-file", side)
        listed = _id_list(text) if ids_ok and _suite_summary(text) is None else None
        if listed is not None:
            sets[side] = listed
            continue
        try:
            sets[side] = failure_set(text)[0]
        except Unreadable as exc:
            return _unreadable(exc.reason, side)
    if sets["run"] and sets["control"] and not set(sets["run"]) & set(sets["control"]):
        return _unreadable("disjoint-ids", "both")
    return classify([sets["run"]], [sets["control"]], 1)


# --- run mode ----------------------------------------------------------------

def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def _control_env(subject: Path, control: Path) -> dict:
    """The environment for the control side: absolute PYTHONPATH entries inside
    the subject point at the control's copy instead (review of 8d2901be, M3)."""
    env = dict(os.environ)
    entries = env.get("PYTHONPATH")
    if entries:
        top, ctl = os.path.realpath(subject), str(control)
        rebased = []
        for entry in entries.split(os.pathsep):
            real = os.path.realpath(entry) if os.path.isabs(entry) else ""
            if real and _under(real, top) and not _under(real, ctl):
                entry = os.path.join(ctl, os.path.relpath(real, top))
            rebased.append(entry)
        env["PYTHONPATH"] = os.pathsep.join(rebased)
    return env


# Run under the control's interpreter and environment: its sys.path, its own
# install prefixes, and the text of every PEP 660 `__editable__*` file in its
# site directories (an editable install can map a package to a directory through
# an import hook without putting that directory on sys.path).
_PROBE = r"""
import json, os, site, sys
dirs = list(getattr(site, "getsitepackages", lambda: [])())
user = getattr(site, "getusersitepackages", lambda: None)()
if user:
    dirs.append(user)
hooks = []
for d in dirs:
    try:
        names = sorted(os.listdir(d))
    except OSError:
        continue
    for name in names:
        if name.startswith("__editable__"):
            path = os.path.join(d, name)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    hooks.append([path, fh.read()])
            except OSError:
                pass
print(json.dumps({"path": sys.path, "hooks": hooks,
                  "prefixes": sorted({sys.prefix, sys.base_prefix, sys.exec_prefix})}))
"""


def _subject_on_control_path(python: str, subject: Path, control: Path, env: dict) -> list[str]:
    """What would make the control import the SUBJECT's code: sys.path entries
    inside the subject, and editable-install hooks that name it.

    Entries under the interpreter's own prefix are its installation — an in-tree
    `.venv` is the interpreter, not the subject's code (review round 2, M1) — so
    they are exempt. An editable `.pth` path such as `<subject>/src` lies outside
    the prefix and is still caught. Raises `ValueError` on an unreadable probe.
    """
    probe = subprocess.run([python, "-c", _PROBE], cwd=control, env=env,
                           capture_output=True, text=True, timeout=120)
    found = json.loads(probe.stdout)
    top, ctl = os.path.realpath(subject), str(control)
    prefixes = [os.path.realpath(p) for p in found["prefixes"]
                if not _under(top, os.path.realpath(p))]
    leaked = []
    for entry in found["path"]:
        real = os.path.realpath(entry) if entry else ""
        if real and _under(real, top) and not _under(real, ctl) \
                and not any(_under(real, prefix) for prefix in prefixes):
            leaked.append(entry)
    names = {top, str(subject)}
    leaked += [path for path, text in found["hooks"] if any(name in text for name in names)]
    return leaked


def _kill_group(proc) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, AttributeError):
        pass


def _run_one(argv: list[str], root: Path, env: dict, timeout: int, log: Path):
    """(reason or None, rc, output). pytest runs in its own process group, which
    is killed whole on a timeout, on a signal, and after it exits — so nothing
    it started outlives the run."""
    proc = subprocess.Popen(argv, cwd=root, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, start_new_session=True)
    _STATE["child"] = proc
    if _STATE["stop"] is not None:   # a signal between Popen and the line above
        _kill_group(proc)
    reason = None
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        output, _ = proc.communicate()
        reason = "timeout"
    finally:
        _STATE["child"] = None
        _kill_group(proc)
    if _STATE["stop"] is not None:
        reason = "interrupted"
    log.write_text(output or "", encoding="utf-8")
    return reason, proc.returncode, output or ""


def run_mode(args) -> int:
    top = _git(Path(args.subject), "rev-parse", "--show-toplevel")
    if top.returncode != 0 or not top.stdout.strip():
        return _unreadable("no-subject-repo", "subject")
    subject = Path(top.stdout.strip())
    base = _git(subject, "rev-parse", "--verify", "--quiet", f"{args.base}^{{commit}}")
    if base.returncode != 0 or not base.stdout.strip():
        return _unreadable("bad-base", "control")
    base_sha = base.stdout.strip()
    try:
        logs = Path(args.log_dir) if args.log_dir else Path(
            tempfile.mkdtemp(prefix="h-mad-failure-diff-logs-"))
        logs.mkdir(parents=True, exist_ok=True)
    except OSError:
        return _unreadable("log-dir", "both")
    try:
        parent = Path(args.control_parent) if args.control_parent else subject.parent
        control = Path(os.path.realpath(tempfile.mkdtemp(prefix=".h-mad-control-", dir=parent)))
    except OSError:
        return _unreadable("control-dir", "control")
    admin: list[str] = []
    try:
        code = _compare(args, subject, control, base_sha, admin, logs)
    finally:
        removed = _remove_control(subject, control, admin[0] if admin else None)
    if not removed:
        # Printed last, so it is the token a reader takes: a leaked control is a
        # broken run even when the comparison itself finished.
        return _unreadable("control-not-removed", "control", tail=f"path={control}")
    return code


def _compare(args, subject: Path, control: Path, base_sha: str, admin_out: list,
             logs: Path) -> int:
    added = _git(subject, "worktree", "add", "--detach", "--quiet", str(control), base_sha)
    if added.returncode != 0:
        return _unreadable("worktree-add-failed", "control", tail=added.stderr)
    found = _git(control, "rev-parse", "--absolute-git-dir")
    if found.returncode == 0:
        admin_out.append(found.stdout.strip())
    head = _git(subject, "rev-parse", "HEAD").stdout.strip()
    dirty = len(_git(subject, "status", "--porcelain").stdout.splitlines())
    print(f"SUBJECT: path={subject} head={head} dirty={dirty}")
    print(f"CONTROL: path={control} base={args.base} sha={base_sha}")
    envs = {"subject": dict(os.environ), "control": _control_env(subject, control)}
    try:
        leaked = _subject_on_control_path(args.python, subject, control, envs["control"])
    except (OSError, subprocess.SubprocessError) as exc:
        return _unreadable("launch-failed", "control", tail=str(exc))
    except (ValueError, KeyError, TypeError) as exc:
        return _unreadable("probe-failed", "control", tail=str(exc))
    if leaked:
        return _unreadable("control-imports-subject", "control", tail="\n".join(leaked))
    argv = [args.python, "-m", "pytest", *PYTEST_FLAGS, *args.selection]
    results: dict[str, list[dict[str, str]]] = {"subject": [], "control": []}
    for index in range(1, args.repeat + 1):
        where = f"{index}/{args.repeat}"
        for side, root in (("subject", subject), ("control", control)):
            if _STATE["stop"] is not None:
                return _unreadable("interrupted", "both")
            log = logs / f"{side}-{index}.log"
            try:
                reason, rc, output = _run_one(argv, root, envs[side], args.timeout, log)
            except OSError as exc:
                return _unreadable("launch-failed", side, where, tail=str(exc))
            if reason == "interrupted":
                return _unreadable("interrupted", "both", log=log)
            if reason is not None:
                return _unreadable(reason, side, where, tail=output, log=log)
            try:
                ids, summary = failure_set(output, rc)
            except Unreadable as exc:
                return _unreadable(exc.reason, side, where, tail=output, log=log)
            results[side].append(ids)
            print(f"RUN: side={side} run={where} rc={rc} passed={summary.passed} "
                  f"failed={summary.failed} errors={summary.errors} log={log}")
    return classify(results["subject"], results["control"], args.repeat)


def _remove_control(subject: Path, control: Path, admin: str | None) -> bool:
    """Remove this run's worktree and ONLY its entry; True when nothing is left.

    Never a repo-wide `git worktree prune`: that also drops the registration of
    any other worktree whose directory is absent at this moment (the same rule
    `h_mad_expect_screens._remove` keeps).
    """
    _git(subject, "worktree", "remove", "--force", "--force", str(control))
    if admin and os.path.basename(os.path.dirname(admin)) == "worktrees" \
            and os.path.isdir(admin):
        shutil.rmtree(admin, ignore_errors=True)
    shutil.rmtree(control, ignore_errors=True)
    listed = _git(subject, "worktree", "list", "--porcelain")
    return (listed.returncode == 0 and not os.path.lexists(control)
            and f"worktree {control}" not in listed.stdout.splitlines())


def _on_signal(signum, frame):
    _STATE["stop"] = signum
    if _STATE["child"] is not None:
        _kill_group(_STATE["child"])


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="run a selection on the subject and on a control")
    run.add_argument("--base", required=True, help="ref the control worktree is detached at")
    run.add_argument("--subject", default=".", help="subject tree (default: cwd's toplevel)")
    run.add_argument("--repeat", type=int, default=1, help="runs per side; exposes flakes")
    run.add_argument("--python", default=sys.executable, help="interpreter for both sides")
    run.add_argument("--timeout", type=int, default=3600, help="seconds per pytest run")
    run.add_argument("--control-parent", help="directory the control is created in "
                     "(default: beside the subject's toplevel)")
    run.add_argument("--log-dir", help="where each run's output is kept "
                     "(default: a new directory under the system temp dir)")
    run.add_argument("selection", nargs="+", help="pytest selection, after `--`, "
                     "relative to the subject's toplevel (pytest runs there)")
    logs = sub.add_parser("logs", help="compare two existing readings")
    logs.add_argument("--run", required=True, help="pytest log of the run under test")
    logs.add_argument("--control", required=True, help="pytest log, or node-id list")
    args = parser.parse_args(argv)
    if args.mode == "logs":
        return logs_mode(args)
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, _on_signal)
    return run_mode(args)


if __name__ == "__main__":
    sys.exit(main())
