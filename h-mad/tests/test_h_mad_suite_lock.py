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
