#!/usr/bin/env python3
"""Collect a worktree executor's evidence from the tree, not from its reply.

Four of six worktree executors in one session ended on "Done.", "No action." or
"Nothing new." with no evidence, and one ended "No change." while it had
committed (skill-candidates row "collect a worktree executor's evidence
mechanically"). Each time the orchestrator re-derived the result by hand: the
branch tip and dirty state, the changed tests re-run, every mutation spec over
the changed scripts re-run. This does that sequence, once, from the worktree.

Usage:
  h_mad_branch_evidence.py <worktree-or-branch> [--base main] [--no-mutation]
                           [--child-timeout S]

The target is a worktree's top directory, or a branch name resolved to the
worktree that has it checked out (`git worktree list`, from the current
directory's repository). A directory that is not a worktree's top (a leftover
`.claude/worktrees/agent-X` with no `.git`, which git would resolve to the
enclosing checkout) is UNREADABLE. Everything else derives from
`git diff --name-status <base>...HEAD`, deletions included:

  * test     any `test_*.py` (also outside a `tests` directory, as in handoff/scripts)
  * spec     a JSON file the harness's `classify_spec_file` calls a spec
  * support  any `conftest.py` (anywhere), or another `.py` under a `tests` directory
  * prod     any other `.py` or `.sh`, or a file starting with `#!` (a hook)
  * doc      anything else outside a `tests` directory

The pytest set is the changed tests, every tracked test whose source names the
stem of a changed or deleted prod/support file (or the name of a deleted
document) as a whole word, and every tracked test under a changed `conftest.py` (for the repo root's, every test in `pytest.ini` testpaths).
The documents go to `h_mad_doc_consumers.py --run`, whose `CONSUMERS-RUN:` token
is forwarded. Specs: the changed specs plus every committed spec with a mutation
whose `file` is changed or deleted code are RUN; a spec whose mutations only
target a changed document is anchor-checked, not run, because the document's
consumer tests already ran and `--check-anchors` sees a moved or duplicated
anchor.

Steps run strictly one after another, never concurrently: pytest, consumers,
`--check-anchors <specs>`, then the harness once per run spec. Children run with
this interpreter (`sys.executable`), in their own process group.

Prints, first line `EVIDENCE: sha=<tip9> base=<base9> ahead=<n> dirty=<n>`,
then `TESTS:`, `CONSUMERS-RUN:`, `ANCHORS:` (the harness's own line) and one
`MUTATION: <spec> <verdict …>` per run spec with its `survived:`/`refused:` rows,
and last line one of

    EVIDENCE-VERDICT: COMPLETE [waived=no-mutation]     exit 0
    EVIDENCE-VERDICT: INCOMPLETE reason=<r>[,<r>…]      exit 0
    EVIDENCE-VERDICT: UNREADABLE reason=<r>[,<r>…]      exit 2

INCOMPLETE: a dirty tree (`dirty`: the evidence must be of a sha), no commits
beyond base (`no-commits`), a changed script with no changed test (`no-tests`),
a changed script no spec targets (`no-mutation-spec`; `--no-mutation` waives
only this, every existing spec still runs, and COMPLETE then names the waiver),
a deleted test or spec (`deleted-guard`), failing tests, drifted anchors, or a
spec that is not ALL_CAUGHT. UNREADABLE: pytest missing, crashed, timed out,
passed nothing, or printed no summary; `SUITE: BUSY` (`suite-busy`, wait and
retry) or `SUITE: TREE_MOVED` from the suite lock; a child with no token or a
token of UNREADABLE, BUSY, TREE_MOVED or RESTORE_FAILED; an interrupt
(`interrupted`); and a tree whose HEAD or status changed during the run
(`tree-moved`, listed first, never replacing the other reasons). Read the token,
never `$?`.

It never writes into the worktree: children run with PYTHONDONTWRITEBYTECODE and
`PYTEST_ADDOPTS=-p no:cacheprovider`, and a child that times out or is
interrupted gets SIGTERM first, so the harness restores its mutant, then
SIGKILL for its whole process group, so no orphan pytest keeps running in the
tree. HEAD and `git status` are compared before and after.
"""
from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from h_mad_audit_gate import SUITE_BUSY_EXIT  # noqa: E402
from h_mad_mutation_harness import _resolve_root, classify_spec_file  # noqa: E402

CHILD_TIMEOUT = 3600.0
STOP_GRACE = 30.0
CHILD_UNREADABLE = {"UNREADABLE", "BUSY", "TREE_MOVED", "RESTORE_FAILED"}
_COUNT_RE = re.compile(r"(\d+) (passed|failed|errors?|skipped)\b")
_SUMMARY_RE = re.compile(r"\bin [\d.]+s\b")
# The conftest's own TREE_MOVED line, whole: a test that QUOTES the token in an
# assertion or its captured output must not turn a real FAIL into a wait-and-retry.
_TREE_MOVED_RE = re.compile(r"SUITE: TREE_MOVED paths=\S* n=\d+")


class Unreadable(Exception):
    pass


def _script(name: str) -> Path:
    """A sibling script path, with a test-only directory override."""
    override = os.environ.get("HMAD_BRANCH_EVIDENCE_SCRIPT_DIR")
    if override:
        return Path(override) / name
    return Path(__file__).resolve().parent / name


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise Unreadable(out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout


def _resolve_worktree(target: str) -> Path:
    if Path(target).is_dir():
        try:
            top = Path(_git(Path(target), "rev-parse", "--show-toplevel").strip())
        except Unreadable:
            raise Unreadable("not-a-worktree")
        if top.resolve() != Path(target).resolve():
            raise Unreadable("not-a-worktree")
        return top
    try:
        listing = _git(Path.cwd(), "worktree", "list", "--porcelain")
    except Unreadable:
        raise Unreadable("no-worktree")
    path = None
    for line in listing.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line in (f"branch refs/heads/{target}", f"branch {target}") and path:
            return Path(path)
    raise Unreadable("no-worktree")


def _state(top: Path) -> tuple[str, list[str]]:
    head = _git(top, "rev-parse", "HEAD").strip()
    status = [e for e in _git(top, "status", "--porcelain=v1", "-z",
                              "--untracked-files=all").split("\0") if e]
    return head, status


def _in_tests(rel: str) -> bool:
    return "tests" in Path(rel).parts[:-1]


def _is_test(rel: str) -> bool:
    name = Path(rel).name
    return name.startswith("test_") and name.endswith(".py")


def _content(top: Path, rel: str, merge_base: str, deleted: bool) -> bytes:
    if not deleted:
        try:
            return (top / rel).read_bytes()
        except OSError:
            return b""
    out = subprocess.run(["git", "-C", str(top), "show", f"{merge_base}:{rel}"],
                         capture_output=True)
    return out.stdout if out.returncode == 0 else b""


def _classify(top: Path, rel: str, merge_base: str, deleted: bool) -> str:
    name = Path(rel).name
    if rel.endswith(".json"):
        if deleted:
            with tempfile.TemporaryDirectory() as scratch:
                copy = Path(scratch) / name
                copy.write_bytes(_content(top, rel, merge_base, True))
                verdict = classify_spec_file(copy)[0]
        else:
            verdict = classify_spec_file(top / rel)[0]
        if verdict != "not-a-spec":
            return "spec"
    if name == "conftest.py":
        return "support"
    if _is_test(rel):
        return "test"
    if _in_tests(rel):
        return "support" if name.endswith(".py") else "other"
    if rel.endswith((".py", ".sh")) or _content(top, rel, merge_base, deleted).startswith(b"#!"):
        return "prod"
    return "doc"


def _spec_targets(top: Path, rel: str) -> set[str]:
    path = top / rel
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
        root = _resolve_root(spec, path)
        files = {(root / m["file"]).resolve() for m in spec["mutations"] if m.get("file")}
    except (OSError, ValueError, KeyError, TypeError):
        return set()
    real_top = top.resolve()
    return {str(f.relative_to(real_top)) for f in files if f.is_relative_to(real_top)}


def _signal_group(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def _stop(proc: subprocess.Popen) -> None:
    """SIGTERM first so the harness restores its mutant; SIGKILL never does."""
    _signal_group(proc.pid, signal.SIGTERM)
    try:
        # Wait on the PROCESS: an orphaned grandchild holds the pipes open, so
        # waiting for their EOF would sit out the whole grace after a finished restore.
        proc.wait(timeout=STOP_GRACE)
    except subprocess.TimeoutExpired:
        pass
    _signal_group(proc.pid, signal.SIGKILL)
    proc.communicate()


def _child(argv: list[str], top: Path, timeout: float) -> subprocess.CompletedProcess:
    addopts = (os.environ.get("PYTEST_ADDOPTS", "") + " -p no:cacheprovider").strip()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": addopts}
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            errors="replace", cwd=str(top), env=env, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except BaseException:  # TimeoutExpired, KeyboardInterrupt
        _stop(proc)
        raise
    # A grandchild the child left behind (an orphaned pytest) dies with its group.
    _signal_group(proc.pid, signal.SIGKILL)
    return subprocess.CompletedProcess(argv, proc.returncode, out, err)


def _suite_signal(text: str, returncode: int | None) -> str | None:
    """The suite lock's verdict, from the conftest's own line, never a quoted substring."""
    lines = text.splitlines()
    if returncode == SUITE_BUSY_EXIT and any(ln.startswith("SUITE: BUSY ") for ln in lines):
        return "suite-busy"
    if any(_TREE_MOVED_RE.fullmatch(ln.strip()) for ln in lines):
        return "suite-tree-moved"
    return None


def _pytest(top: Path, files: list[str], timeout: float) -> tuple[str, str | None, list[str]]:
    """(token body, outcome, detail lines); outcome None=pass, 'failed', or 'u:<reason>'."""
    try:
        proc = _child([sys.executable, "-m", "pytest", "-q", *files], top, timeout)
    except subprocess.TimeoutExpired:
        return "UNREADABLE reason=pytest-timeout", "u:pytest-timeout", []
    text = proc.stdout + proc.stderr
    lines = proc.stdout.splitlines()
    failed_ids = [ln for ln in lines if ln.startswith(("FAILED ", "ERROR "))]
    summary = next((ln for ln in reversed(lines) if _SUMMARY_RE.search(ln)), None)
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for n, word in _COUNT_RE.findall(summary or ""):
        counts["errors" if word.startswith("error") else word] += int(n)
    suite = _suite_signal(text, proc.returncode)
    if suite:
        reason = suite
    elif proc.returncode not in (0, 1):
        reason = f"pytest-rc{proc.returncode}"
    elif summary is None:
        reason = "pytest-no-summary"
    elif proc.returncode == 0 and counts["passed"] and not counts["failed"] + counts["errors"]:
        skipped = f" skipped={counts['skipped']}" if counts["skipped"] else ""
        return f"PASS files={len(files)} passed={counts['passed']}{skipped}", None, []
    elif proc.returncode == 1 and counts["failed"] + counts["errors"]:
        return (f"FAIL files={len(files)} failed={counts['failed']} errors={counts['errors']} "
                f"passed={counts['passed']}", "failed", failed_ids)
    else:
        reason = "pytest-inconsistent"
    tail = [f"  | {ln}" for ln in text.strip().splitlines()[-5:]]
    return f"UNREADABLE reason={reason}", f"u:{reason}", tail


def _token(proc: subprocess.CompletedProcess, prefix: str) -> str | None:
    hits = [ln for ln in proc.stdout.splitlines() if ln.startswith(prefix)]
    return hits[-1] if hits else None


def _testpaths(top: Path) -> list[str]:
    """A repo-root conftest's reach: pytest.ini `testpaths`, or the whole repo (\"\")."""
    ini = configparser.ConfigParser()
    try:
        ini.read(top / "pytest.ini", encoding="utf-8")
        paths = ini.get("pytest", "testpaths", fallback="").split()
    except (OSError, configparser.Error):
        paths = []
    return [p.rstrip("/") for p in paths] or [""]


def _names(text: str, token: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(token)}(?!\w)", text) is not None


def collect(target: str, base: str, no_mutation: bool,
            timeout: float) -> tuple[list[str], str, int]:
    out: list[str] = []
    incomplete: list[str] = []
    unreadable: list[str] = []

    top = _resolve_worktree(target)
    head, status = _state(top)
    try:
        _git(top, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
        merge_base = _git(top, "merge-base", base, "HEAD").strip()
    except Unreadable:
        raise Unreadable("unknown-base")
    ahead = int(_git(top, "rev-list", "--count", f"{merge_base}..HEAD").strip())
    branch = _git(top, "rev-parse", "--abbrev-ref", "HEAD").strip()

    out.append(f"EVIDENCE: sha={head[:9]} base={merge_base[:9]} ahead={ahead} dirty={len(status)}")
    out.append(f"  worktree={top} branch={branch} base_ref={base}")
    for line in _git(top, "log", "--format=%h %s", "--abbrev=9", f"{merge_base}..HEAD").splitlines():
        out.append(f"  commit {line}")
    for entry in status:
        out.append(f"  dirty {entry}")
    if status:
        incomplete.append("dirty")
    if ahead == 0:
        incomplete.append("no-commits")

    fields = [f for f in _git(top, "diff", "--name-status", "--no-renames", "-z",
                              f"{merge_base}...HEAD").split("\0") if f]
    entries = list(zip(fields[0::2], fields[1::2]))
    deleted = {rel for letter, rel in entries if letter == "D"}
    kinds: dict[str, list[str]] = {k: [] for k in ("prod", "test", "spec", "support", "doc", "other")}
    for _, rel in entries:
        kinds[_classify(top, rel, merge_base, rel in deleted)].append(rel)
    changed = [rel for _, rel in entries]
    live = {k: [r for r in v if r not in deleted] for k, v in kinds.items()}
    out.append("CHANGED: files={} prod={} tests={} specs={} docs={} support={} deleted={}".format(
        len(changed), len(kinds["prod"]), len(kinds["test"]), len(kinds["spec"]),
        len(kinds["doc"]), len(kinds["support"]), len(deleted)))
    for kind in ("prod", "test", "spec", "support", "doc", "other"):
        out.extend(f"  {'deleted' if rel in deleted else kind} {rel}" for rel in kinds[kind])

    guards = [rel for rel in kinds["test"] + kinds["spec"] if rel in deleted]
    out.extend(f"DELETED-GUARD: {rel}" for rel in guards)
    if guards:
        incomplete.append("deleted-guard")

    if incomplete and ("dirty" in incomplete or "no-commits" in incomplete):
        out.append(f"TESTS: SKIPPED reason={','.join(incomplete)}")
        return out, _verdict(incomplete, unreadable, no_mutation), 0

    # The pytest set: changed tests, tests naming a changed script, tests under a changed conftest.
    why: dict[str, str] = {rel: "changed" for rel in live["test"]}
    tokens = {Path(rel).stem for rel in kinds["prod"] + kinds["support"]}
    tokens |= {Path(rel).name for rel in kinds["doc"] if rel in deleted}
    conftest_dirs: list[str] = []
    for rel in kinds["support"]:
        if Path(rel).name == "conftest.py":
            parent = str(Path(rel).parent)
            conftest_dirs += _testpaths(top) if parent == "." else [parent]
    tracked_tests = [rel for rel in _git(top, "ls-files", "-z", "--", "*.py").split("\0")
                     if rel and _is_test(rel)]
    for rel in tracked_tests:
        if rel in why:
            continue
        under = [d for d in conftest_dirs if not d or rel.startswith(d + "/")]
        if under:
            why[rel] = "under a changed conftest (" + (under[0] or "repo root") + ")"
            continue
        if not tokens:
            continue
        try:
            text = (top / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        named = sorted(tok for tok in tokens if _names(text, tok))
        if named:
            why[rel] = "names " + ",".join(named)
    pytest_set = sorted(why)
    out.append(f"PYTEST-SET: n={len(pytest_set)}")
    out.extend(f"  {rel} ({why[rel]})" for rel in pytest_set)
    if live["prod"] and not live["test"]:
        incomplete.append("no-tests")

    # Specs over changed code are RUN; specs over a changed document only anchor-checked.
    code = set(kinds["prod"] + kinds["support"] + kinds["test"])
    prose = set(kinds["doc"] + kinds["other"])
    run_specs = set(live["spec"])
    anchor_only: set[str] = set()
    covered: set[str] = set()
    for rel in live["spec"]:
        covered |= _spec_targets(top, rel)
    for rel in _git(top, "ls-files", "-z", "--", "*.json").split("\0"):
        if not rel or classify_spec_file(top / rel)[0] != "spec":
            continue
        targets = _spec_targets(top, rel)
        if targets & code:
            run_specs.add(rel)
            covered |= targets
        elif targets & prose:
            anchor_only.add(rel)
    anchor_only -= run_specs
    specs = sorted(run_specs | anchor_only)
    out.append(f"SPEC-SET: n={len(specs)} run={len(run_specs)} anchors-only={len(anchor_only)}")
    out.extend(f"  {rel}" + (" (anchors only)" if rel in anchor_only else "") for rel in specs)
    unspecced = [rel for rel in live["prod"] if rel not in covered]
    out.extend(f"UNSPECCED: {rel}" for rel in unspecced)
    if unspecced and not no_mutation:
        incomplete.append("no-mutation-spec")

    try:
        _execute(top, pytest_set, live["doc"], specs, sorted(run_specs), timeout,
                 out, incomplete, unreadable)
    except KeyboardInterrupt:
        out.append("INTERRUPTED: the step in flight got SIGTERM, then its group SIGKILL")
        unreadable.insert(0, "interrupted")

    try:
        moved = _state(top) != (head, status)
    except Unreadable:
        moved = True
    out.append(f"TREE: {'MOVED' if moved else 'UNCHANGED'}")
    if moved:
        unreadable.insert(0, "tree-moved")
    verdict = _verdict(incomplete, unreadable, no_mutation)
    return out, verdict, 2 if unreadable else 0


def _execute(top: Path, pytest_set: list[str], docs: list[str], specs: list[str],
             run_specs: list[str], timeout: float,
             out: list[str], incomplete: list[str], unreadable: list[str]) -> None:
    """Every step, strictly in sequence; each child finishes before the next starts."""
    if not pytest_set:
        out.append("TESTS: NONE")
    elif _child([sys.executable, "-c", "import pytest"], top, timeout).returncode != 0:
        out.append("TESTS: UNREADABLE reason=pytest-missing")
        unreadable.append("tests-pytest-missing")
    else:
        body, outcome, detail = _pytest(top, pytest_set, timeout)
        out.append(f"TESTS: {body}")
        out.extend(f"  {ln}" if not ln.startswith("  ") else ln for ln in detail)
        if outcome == "failed":
            incomplete.append("tests-failed")
        elif outcome:
            unreadable.append("tests-" + outcome[2:])

    if not docs:
        out.append("CONSUMERS-RUN: NONE docs=0")
    else:
        argv = [sys.executable, str(_script("h_mad_doc_consumers.py")), "--repo", str(top),
                "--run", "--timeout", f"{timeout:g}", *docs]
        try:
            proc = _child(argv, top, timeout + STOP_GRACE + 30)
            line = _token(proc, "CONSUMERS-RUN: ")
        except subprocess.TimeoutExpired:
            proc, line = None, "CONSUMERS-RUN: UNREADABLE reason=timeout"
        if line is None:
            out.append("CONSUMERS-RUN: UNREADABLE reason=no-token")
            unreadable.append("consumers-no-token")
        else:
            out.append(line)
            word = line.split()[1] if len(line.split()) > 1 else ""
            text = (proc.stdout + proc.stderr) if proc else ""
            if word == "FAIL":
                after = proc.stdout.split(line, 1)[1].splitlines()
                out.extend(ln for ln in after if ln.startswith("  "))
                incomplete.append("consumers-failed")
            elif suite := _suite_signal(text, int(rc.group(1)) if (rc := re.search(r"\brc=(\d+)", line)) else None):
                unreadable.append("consumers-" + suite)
            elif word not in ("PASS", "NONE"):
                found = re.search(r"reason=([\w-]+)", line)
                unreadable.append("consumers-" + (found.group(1) if found else "unreadable"))

    harness = str(_script("h_mad_mutation_harness.py"))
    if not specs:
        out.append("ANCHORS: NONE specs=0")
    else:
        try:
            line = _token(_child([sys.executable, harness, "--check-anchors", *specs], top, timeout),
                          "ANCHORS: ")
        except subprocess.TimeoutExpired:
            line = "ANCHORS: UNREADABLE reason=timeout"
        if line is None:
            out.append("ANCHORS: UNREADABLE reason=no-token")
            unreadable.append("anchors-no-token")
        else:
            out.append(line)
            word = line.split()[1] if len(line.split()) > 1 else ""
            if word == "ANCHORS_DRIFTED":
                incomplete.append("anchors-drifted")
            elif word != "ANCHORS_OK":
                found = re.search(r"reason=([\w-]+)", line)
                unreadable.append("anchors-" + (found.group(1) if found else
                                  word.removeprefix("ANCHORS_").lower().replace("_", "-")))

    if not run_specs:
        out.append("MUTATION: NONE specs=0")
    for spec in run_specs:
        try:
            proc = _child([sys.executable, harness, spec], top, timeout)
            line = _token(proc, "MUTATION: ")
        except subprocess.TimeoutExpired:
            out.append(f"MUTATION: {spec} UNREADABLE reason=timeout")
            unreadable.append("mutation-timeout")
            continue
        if line is None:
            out.append(f"MUTATION: {spec} UNREADABLE reason=no-token")
            unreadable.append("mutation-no-token")
            continue
        rest = line[len("MUTATION: "):].strip()
        out.append(f"MUTATION: {spec} {rest}")
        # Name the rows that did not bite, so nobody re-runs the harness to learn which.
        out.extend(ln for ln in proc.stdout.splitlines()
                   if ln.startswith(("  survived: ", "  refused: ")))
        word = rest.split()[0] if rest else ""
        reason = "mutation-" + word.lower().replace("_", "-")
        if word in CHILD_UNREADABLE or not word:
            unreadable.append(reason)
        elif word != "ALL_CAUGHT":
            incomplete.append(reason)


def _verdict(incomplete: list[str], unreadable: list[str], no_mutation: bool) -> str:
    def join(reasons: list[str]) -> str:
        return ",".join(dict.fromkeys(reasons))
    if unreadable:
        return f"EVIDENCE-VERDICT: UNREADABLE reason={join(unreadable)}"
    if incomplete:
        return f"EVIDENCE-VERDICT: INCOMPLETE reason={join(incomplete)}"
    return "EVIDENCE-VERDICT: COMPLETE" + (" waived=no-mutation" if no_mutation else "")


def _interrupt(signum, frame):
    raise KeyboardInterrupt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("target", help="worktree path, or a branch checked out in a worktree")
    ap.add_argument("--base", default="main", help="base ref (default: main)")
    ap.add_argument("--no-mutation", action="store_true",
                    help="waive only the missing-spec refusal; existing specs still run")
    ap.add_argument("--child-timeout", type=float, default=CHILD_TIMEOUT,
                    help=f"seconds per child step before it is stopped (default {CHILD_TIMEOUT:g})")
    args = ap.parse_args(argv)
    signal.signal(signal.SIGTERM, _interrupt)
    try:
        lines, verdict, code = collect(args.target, args.base, args.no_mutation, args.child_timeout)
    except KeyboardInterrupt:
        print("EVIDENCE: UNREADABLE reason=interrupted")
        print("EVIDENCE-VERDICT: UNREADABLE reason=interrupted")
        return 2
    except Unreadable as exc:
        reason = str(exc) if re.fullmatch(r"[a-z-]+", str(exc)) else "git"
        if reason == "git":
            print(f"EVIDENCE: UNREADABLE — {exc}")
        else:
            print(f"EVIDENCE: UNREADABLE reason={reason}")
        print(f"EVIDENCE-VERDICT: UNREADABLE reason={reason}")
        return 2
    print("\n".join(lines))
    print(verdict)
    return code


if __name__ == "__main__":
    sys.exit(main())
