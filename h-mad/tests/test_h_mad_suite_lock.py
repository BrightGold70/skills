"""One measured pytest session per working tree (rows 1391 and 2361).

Two pytest runs over one tree produced 6 and 3 failures in DIFFERENT sets, and 0
when the file ran alone; two full suites produced 11 phantom failures in a file
that passes 40/40 alone; a mutation harness ran during a full suite and was
harmless only by luck. The rule "never run two suites" was prose. These tests pin
the mechanism: the suite takes the SAME lock the mutation harness takes, a second
session on the same toplevel refuses with `SUITE: BUSY`, and the harness's own
inner pytest runs are exempt through the holder token it exports.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from suite_lock_support import (HOLDER_ENV, busy_exit, dead_pid, finish, git,
                                make_tree, run_session, session_env, start_blocking_session,
                                write_holder)
from h_mad_mutation_harness import _lock_path  # noqa: E402

HARNESS = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_mutation_harness.py"


def test_second_pytest_session_on_same_toplevel_exits_SUITE_BUSY(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    release = tmp_path / "release"
    first = start_blocking_session(root, tmp_path / "bt-a", release)
    try:
        second = run_session(root, tmp_path / "bt-b")
    finally:
        first_out = finish(first, release)
    out = second.stdout + second.stderr
    assert second.returncode == busy_exit(), out
    assert f"SUITE: BUSY holder={first.pid} age=" in second.stdout, out
    assert "what=pytest-session" in second.stdout, out
    assert "passed" not in second.stdout, "a refused session must measure nothing"
    assert first.returncode == 0, first_out
    assert not _lock_path(root).exists(), "the holding session did not release the lock"


def test_dead_holder_lock_is_taken(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    write_holder(root, dead_pid())
    proc = run_session(root, tmp_path / "bt")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 passed" in proc.stdout
    assert not _lock_path(root).exists(), "the taken lock outlived the session"


def test_unparseable_lock_blocks_and_names_the_file(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    lock = _lock_path(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("{not json at all", encoding="utf-8")
    proc = run_session(root, tmp_path / "bt")
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr
    assert "SUITE: BUSY holder=unparseable" in proc.stdout, proc.stdout
    assert str(lock) in proc.stdout, "the line must name the file a human deletes"
    assert lock.read_text(encoding="utf-8") == "{not json at all", "it was stolen"


def test_harness_inner_run_is_exempt_via_env_holder(tmp_path: Path) -> None:
    """The holder's children inherit the token and run; a stranger does not."""
    from h_mad_mutation_harness import tree_lock

    root = make_tree(tmp_path)
    with tree_lock(root, root / "spec.json"):
        child_env = dict(os.environ)
        inner = run_session(root, tmp_path / "bt-in", env=child_env)
        stranger = run_session(root, tmp_path / "bt-out", env=session_env())
    assert child_env.get(HOLDER_ENV) == f"{_lock_path(root)}:{os.getpid()}"
    assert inner.returncode == 0, inner.stdout + inner.stderr
    assert "1 passed" in inner.stdout
    assert stranger.returncode == busy_exit(), stranger.stdout + stranger.stderr
    assert os.environ.get(HOLDER_ENV) != child_env[HOLDER_ENV], "the token leaked past the lock"


def test_stale_env_holder_does_not_exempt(tmp_path: Path) -> None:
    """A token naming this lock but not its CURRENT holder is not an exemption."""
    root = make_tree(tmp_path)
    lock = write_holder(root, os.getpid())
    env = session_env(**{HOLDER_ENV: f"{lock}:{dead_pid()}"})
    proc = run_session(root, tmp_path / "bt", env=env)
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr


def test_a_real_harness_run_over_the_suite_does_not_deadlock(tmp_path: Path) -> None:
    """End to end: the harness holds the tree and its inner pytest still runs."""
    root = make_tree(tmp_path)
    (root / "h-mad" / "tests" / "guard.py").write_text("LIMIT = 5\n", encoding="utf-8")
    (root / "h-mad" / "tests" / "test_guard.py").write_text(
        "from guard import LIMIT\n\ndef test_limit():\n    assert LIMIT == 5\n",
        encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "guard")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        "root": str(root),
        "command": [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "h-mad/tests/test_guard.py"],
        "mutations": [{"name": "limit-moves", "file": "h-mad/tests/guard.py",
                       "find": "LIMIT = 5", "replace": "LIMIT = 6"}],
    }), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(HARNESS), str(spec)], cwd=root,
                          env=session_env(), capture_output=True, text=True, timeout=300)
    assert "MUTATION: ALL_CAUGHT" in proc.stdout, proc.stdout + proc.stderr


def test_harness_refuses_MUTATION_BUSY_while_suite_holds_lock(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({
        "root": str(root),
        "command": [sys.executable, "-c", "pass"],
        "mutations": [{"name": "m", "file": "notes.txt", "find": "tracked",
                       "replace": "moved"}],
    }), encoding="utf-8")
    release = tmp_path / "release"
    suite = start_blocking_session(root, tmp_path / "bt", release)
    try:
        proc = subprocess.run([sys.executable, str(HARNESS), str(spec)], cwd=root,
                              env=session_env(), capture_output=True, text=True, timeout=120)
    finally:
        finish(suite, release)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert f"MUTATION: BUSY holder={suite.pid} " in proc.stdout, proc.stdout
    assert "spec=pytest-session" in proc.stdout, proc.stdout
    assert (root / "notes.txt").read_text(encoding="utf-8") == "tracked\n"


def test_separate_worktree_toplevels_do_not_contend(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    worktree = tmp_path / "wt"
    git(root, "worktree", "add", "-q", "-b", "side", str(worktree))
    worktree = Path(git(worktree, "rev-parse", "--show-toplevel"))
    assert _lock_path(worktree) != _lock_path(root)
    write_holder(root, os.getpid())
    proc = run_session(worktree, tmp_path / "bt")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 passed" in proc.stdout


# --- the callers that run a repo pytest read BUSY as cannot-judge, never FAIL ---


def _busy_tree(tmp_path: Path) -> Path:
    root = make_tree(tmp_path)
    write_holder(root, os.getpid())
    return root


def test_audit_gate_reads_busy_exit_as_unreadable_not_fail(tmp_path: Path) -> None:
    from h_mad_audit_gate import run_suite

    root = _busy_tree(tmp_path)
    outcome = run_suite(root, command=[
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
        "--basetemp", str(tmp_path / "bt"), str(root / "h-mad" / "tests" / "test_probe.py")])
    assert outcome["verdict"] == "UNREADABLE", outcome
    assert outcome["reason"] == "suite_busy", outcome


def test_tdd_judge_reads_busy_exit_as_cannot_judge_not_red(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Needs no mapping of its own, and this pins that it stays so.

    A refused session prints no summary line, so the judge already scores it
    `no-summary` (DENY, cannot-judge) and its reason carries pytest's own
    `Exit: SUITE: BUSY …` line. A mapping added for it survived its mutation, so
    it was not kept; this test is what would notice the judge ever reading a
    busy tree as `red-measured`.
    """
    import h_mad_tdd_judge as judge

    root = _busy_tree(tmp_path)
    probe = root / "h-mad" / "tests" / "test_probe.py"
    monkeypatch.setattr(judge, "resolve", lambda *a, **k: judge.Resolution(
        "plan", ((probe, root),), (), (), None))
    monkeypatch.setattr(judge, "select_interpreter", lambda *a, **k: sys.executable)
    verdict = judge.judge(root, root / "notes.txt", (), budget_s=120.0)
    assert verdict.decision == "DENY", verdict
    assert verdict.kind == "no-summary", verdict
    assert "SUITE: BUSY" in verdict.reason, verdict


def test_wire_registry_reads_busy_exit_as_unreadable_not_broken(tmp_path: Path) -> None:
    import h_mad_wire_registry as registry

    root = _busy_tree(tmp_path)
    record = {"kind": "wire", "id": "w", "caller": "a", "callee": "b",
              "pin": "test_probe", "owning_feature": "f",
              "node_id": "h-mad/tests/test_probe.py::test_probe"}
    with pytest.raises(registry.RegistryError, match="SUITE: BUSY"):
        registry.run_pins([record], root)


# --- every pytest entry point over the repo takes the lock (review M1) ---------
#
# The lock lived in `pytest_sessionstart` of `h-mad/tests/conftest.py`, which
# fires only when that conftest is an INITIAL conftest. `pytest handoff/tests`,
# a single `handoff/scripts` file and `pytest .` never loaded it up front, so
# they measured a held tree in silence. The root conftest now registers the lock
# for every session under this rootdir, against the live `pytest.ini` testpaths.


@pytest.mark.parametrize("args", [
    ("handoff/tests",),
    ("handoff/scripts/test_script_probe.py",),
    (".",),
    ("h-mad",),
], ids=["handoff-tests", "one-handoff-scripts-file", "dot", "h-mad-dir"])
def test_every_entry_point_under_the_rootdir_exits_SUITE_BUSY(
        tmp_path: Path, args: tuple[str, ...]) -> None:
    root = make_tree(tmp_path)
    write_holder(root, os.getpid())
    proc = run_session(root, tmp_path / "bt", None, *args)
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr
    assert f"SUITE: BUSY holder={os.getpid()} " in proc.stdout, proc.stdout


def test_bare_pytest_over_the_declared_testpaths_exits_SUITE_BUSY(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    write_holder(root, os.getpid())
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           "--basetemp", str(tmp_path / "bt")], cwd=root, env=session_env(),
                          capture_output=True, text=True, timeout=180)
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr


def test_every_entry_point_takes_the_lock_exactly_once(tmp_path: Path) -> None:
    """Both conftests load in this run; a second registration would find the
    lock held by its own process and refuse the session it belongs to."""
    root = make_tree(tmp_path)
    proc = run_session(root, tmp_path / "bt", None,
                       "h-mad/tests/test_probe.py", "handoff/tests", "handoff/scripts")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "3 passed" in proc.stdout, proc.stdout
    assert not _lock_path(root).exists()


def test_install_path_through_a_symlink_still_takes_the_lock(tmp_path: Path) -> None:
    """`pytest ~/.claude/skills/h-mad/tests/` sees no pytest.ini and no root
    conftest above it; the h-mad conftest registers the lock itself."""
    root = make_tree(tmp_path)
    install = tmp_path / "install"
    install.mkdir()
    (install / "h-mad").symlink_to(root / "h-mad")
    write_holder(root, os.getpid())
    proc = run_session(root, tmp_path / "bt", None,
                       str(install / "h-mad" / "tests" / "test_probe.py"), cwd=install)
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr


# --- review S1-S3, N2, N4 -------------------------------------------------------


def test_dead_holder_token_naming_the_dead_holder_does_not_exempt(tmp_path: Path) -> None:
    """A SIGKILLed harness leaves its inner pytest holding a token whose pid IS
    the lock's holder. Dead, so it exempts nothing: the session takes the lock."""
    root = make_tree(tmp_path)
    pid = dead_pid()
    lock = write_holder(root, pid)
    proc = run_session(root, tmp_path / "bt", session_env(**{HOLDER_ENV: f"{lock}:{pid}"}))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not lock.exists(), "the session ran exempt instead of taking the dead holder's lock"


def test_an_unwritable_lock_runs_unlocked_and_says_so(tmp_path: Path) -> None:
    root = make_tree(tmp_path)
    (root / ".h-mad").write_text("a file where the lock directory goes\n", encoding="utf-8")
    proc = run_session(root, tmp_path / "bt")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SUITE: LOCK_UNAVAILABLE " in proc.stdout, proc.stdout
    assert "1 passed" in proc.stdout


def test_sigterm_releases_the_lock(tmp_path: Path) -> None:
    import signal

    root = make_tree(tmp_path)
    release = tmp_path / "release"
    proc = start_blocking_session(root, tmp_path / "bt", release)
    proc.send_signal(signal.SIGTERM)
    proc.communicate(timeout=60)
    release.write_text("go", encoding="utf-8")
    assert proc.returncode == -signal.SIGTERM, proc.returncode
    assert not _lock_path(root).exists(), "a SIGTERMed session left its lock behind"


def test_a_recycled_pid_holder_is_stale(tmp_path: Path) -> None:
    """A live pid that STARTED after the lock was written is not the holder."""
    root = make_tree(tmp_path)
    stranger = subprocess.Popen(["sleep", "60"])
    try:
        time.sleep(1.5)
        lock = _lock_path(root)
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps({"pid": stranger.pid, "spec": "pytest-session",
                                    "started": time.time() - 3600}), encoding="utf-8")
        proc = run_session(root, tmp_path / "bt")
    finally:
        stranger.kill()
        stranger.wait()
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 passed" in proc.stdout


def test_a_live_holder_that_predates_its_lock_still_blocks(tmp_path: Path) -> None:
    """The other direction: the recycled-pid rule must not steal a real holder."""
    root = make_tree(tmp_path)
    holder = subprocess.Popen(["sleep", "60"])
    try:
        time.sleep(1.5)
        lock = _lock_path(root)
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps({"pid": holder.pid, "spec": "pytest-session",
                                    "started": time.time()}), encoding="utf-8")
        proc = run_session(root, tmp_path / "bt")
    finally:
        holder.kill()
        holder.wait()
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr


def test_an_empty_lock_says_retry_before_delete(tmp_path: Path) -> None:
    """Between O_EXCL create and payload write a live lock reads empty."""
    root = make_tree(tmp_path)
    lock = _lock_path(root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("", encoding="utf-8")
    proc = run_session(root, tmp_path / "bt")
    assert proc.returncode == busy_exit(), proc.stdout + proc.stderr
    assert "retry in a second" in proc.stdout, proc.stdout


def test_audit_gate_names_the_holder_of_a_busy_suite(tmp_path: Path) -> None:
    from test_h_mad_audit_suite_gate import CLEAN, fake_suite, run

    audit = tmp_path / "f.plan.audit.v1.codex.md"
    audit.write_text(CLEAN, encoding="utf-8")
    sh = fake_suite(tmp_path, "busy.sh",
                    'echo "SUITE: BUSY holder=4242 age=9s what=pytest-session lock=/x"; exit 75')
    out = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout
    assert "SUITE: UNREADABLE reason=suite_busy" in out, out
    assert "holder=4242" in out, out


def test_audit_cycle_names_the_holder_of_a_busy_suite(capsys, tmp_path: Path) -> None:
    """Review N4: the cycle driver dropped the `holder` that `run_suite` returns."""
    from test_h_mad_audit_cycle import _two_leg_reports, audit_cycle, run_collect_cycle
    from test_h_mad_audit_suite_gate import fake_suite

    sh = fake_suite(tmp_path, "busy.sh",
                    'echo "SUITE: BUSY holder=4242 age=9s what=pytest-session lock=/x"; exit 75')
    rc, out, _ = run_collect_cycle(
        audit_cycle(), tmp_path=tmp_path, capsys=capsys, report_paths=_two_leg_reports(tmp_path),
        extra_args=["--project-tests", str(tmp_path), "--suite-cmd", str(sh)])
    assert "SUITE: UNREADABLE reason=suite_busy" in out, out
    assert "holder=4242" in out, out


# --- round 2 ------------------------------------------------------------------


BOTH = """\
import json, os, pathlib

def test_both(tmp_path_factory):
    stem = os.environ.get("HMAD_AUDIT_STEM_DIR")
    base = pathlib.Path(tmp_path_factory.getbasetemp()).resolve()
    assert stem and base in pathlib.Path(stem).resolve().parents, (stem, base)
    lock = pathlib.Path(__file__).resolve().parents[2] / ".h-mad" / "mutation.lock"
    assert json.loads(lock.read_text())["pid"] == os.getpid()
"""


def test_h_mad_conftest_takes_the_lock_and_exports_the_stem_dir(tmp_path: Path) -> None:
    """R2-M1: both `pytest_configure` jobs must run. Two module-level definitions
    merged without conflict and the second rebound the name, dropping the first.
    Run through the install path, where `h-mad/tests/conftest.py` is the ONLY
    conftest, so neither job can be covered by the root one."""
    root = make_tree(tmp_path)
    (root / "h-mad" / "tests" / "test_both.py").write_text(BOTH, encoding="utf-8")
    install = tmp_path / "install"
    install.mkdir()
    (install / "h-mad").symlink_to(root / "h-mad")
    proc = run_session(root, tmp_path / "bt", None,
                       str(install / "h-mad" / "tests" / "test_both.py"), cwd=install)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "1 passed" in proc.stdout, proc.stdout


def test_a_session_started_with_sigterm_ignored_still_ignores_it(tmp_path: Path) -> None:
    """R2-N2: `trap '' TERM` before pytest must still mean what it says."""
    import signal

    root = make_tree(tmp_path)
    release = tmp_path / "release"
    proc = start_blocking_session(
        root, tmp_path / "bt", release,
        preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_IGN))
    proc.send_signal(signal.SIGTERM)
    time.sleep(1)
    out = finish(proc, release)
    assert proc.returncode == 0, (proc.returncode, out)
    assert not _lock_path(root).exists()
