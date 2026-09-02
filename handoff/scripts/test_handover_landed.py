"""Checking once that a handover landed — and refusing to guess when it can't.

The asymmetry is the whole design. The sender has already released the claim and
stopped watching, so a false NOT_YET is expensive: it invites them to re-deliver
work that is already in progress, and two sessions on one feature produce
contradictory conclusions on one branch. "I could not check" therefore has its
own verdict and its own exit code, and never borrows NOT_YET's.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "handover_landed.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def state(tmp_path: Path, record: dict | None) -> str:
    p = tmp_path / ".bkit-memory.json"
    body = {"orchestrator_state": {"feat": record} if record is not None else {}}
    p.write_text(json.dumps(body), encoding="utf-8")
    return str(p)


def fake_dispatch(tmp_path: Path, payload: str, rc: int = 0) -> str:
    """A stub standing in for the wrapper. The script must go through
    `hmad-dispatch` and never call `orca` — this skill states that twice."""
    p = tmp_path / "hmad-dispatch"
    p.write_text(f"#!/bin/sh\ncat <<'JSON'\n{payload}\nJSON\nexit {rc}\n", encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def ps(path: str, comment: str) -> str:
    return json.dumps({"worktrees": [{"path": path, "comment": comment}]})


# --- the claim signal -------------------------------------------------------


def test_a_claim_held_by_someone_else_is_pickup(tmp_path) -> None:
    s = state(tmp_path, {"owner_session_id": "receiver-1", "owner_heartbeat_ts": "2026-09-01T10:00:00Z"})
    r = run("--state", s, "--feature", "feat", "--sender-session", "sender-1")
    assert r.returncode == 0, r.stdout
    assert "LANDED" in r.stdout and "receiver-1" in r.stdout


def test_still_owned_by_the_sender_is_not_pickup(tmp_path) -> None:
    s = state(tmp_path, {"owner_session_id": "sender-1"})
    r = run("--state", s, "--feature", "feat", "--sender-session", "sender-1")
    assert r.returncode == 1 and "NOT_YET" in r.stdout


def test_released_and_unclaimed_is_not_pickup(tmp_path) -> None:
    """The normal state right after a correct handover: the sender released, and
    nobody has claimed yet."""
    s = state(tmp_path, {"owner_session_id": None})
    r = run("--state", s, "--feature", "feat", "--sender-session", "sender-1")
    assert r.returncode == 1 and "NOT_YET" in r.stdout


def test_a_missing_record_is_answered_not_guessed(tmp_path) -> None:
    s = state(tmp_path, None)
    r = run("--state", s, "--feature", "feat", "--sender-session", "sender-1")
    assert r.returncode == 1 and "unclaimed" in r.stdout


def test_an_unreadable_state_file_is_unknown_not_not_yet(tmp_path) -> None:
    """The load-bearing asymmetry: a sender who has let go must not be told the
    receiver dropped it because a file would not parse."""
    p = tmp_path / ".bkit-memory.json"
    p.write_text("{not json", encoding="utf-8")
    r = run("--state", str(p), "--feature", "feat", "--sender-session", "s1")
    assert r.returncode == 2, r.stdout
    assert "UNKNOWN" in r.stdout and "NOT evidence" in r.stdout


def test_a_missing_state_file_is_unknown(tmp_path) -> None:
    r = run("--state", str(tmp_path / "nope.json"), "--feature", "feat", "--sender-session", "s1")
    assert r.returncode == 2 and "UNKNOWN" in r.stdout


# --- the worktree-comment signal --------------------------------------------


def test_a_taken_over_stamp_is_pickup(tmp_path) -> None:
    s = state(tmp_path, {"owner_session_id": None})       # claim says not yet
    d = fake_dispatch(tmp_path, ps("/repo/wt", "taken over: feat · phase 5 · next: task 2"))
    r = run("--state", s, "--feature", "feat", "--sender-session", "s1",
            "--worktree-path", "/repo/wt", "--hmad-dispatch", d)
    assert r.returncode == 0, r.stdout
    assert "LANDED" in r.stdout, "one receiver-produced signal is proof"


def test_a_stamp_the_receiver_overwrote_is_pickup(tmp_path) -> None:
    """The measured regression. A handover that was picked up, fixed and merged
    as 282a3a5 read NOT_YET because the receiver replaced Step 4's stamp with its
    own completion note instead of the words `taken over:`. NOT_YET prescribes
    re-delivery, so the tool asked for work already on main to be dispatched
    again. Visible completion outranks the expected prefix."""
    d = fake_dispatch(tmp_path, ps("/wt/x", "Complete: SIGPIPE wait gates fixed; main @ 282a3a5"))
    r = run("--state", state(tmp_path, {"owner_session_id": "sender-1"}), "--feature", "feat",
            "--sender-session", "sender-1", "--worktree-path", "/wt/x", "--hmad-dispatch", d)
    assert r.returncode == 0, r.stdout
    assert "LANDED" in r.stdout


def test_an_empty_comment_is_not_pickup(tmp_path) -> None:
    """Control for the rule above: 'the stamp is gone' must not become 'anything
    non-empty counts', or an empty comment would read as a receiver signal."""
    d = fake_dispatch(tmp_path, ps("/wt/x", ""))
    r = run("--state", state(tmp_path, {"owner_session_id": "sender-1"}), "--feature", "feat",
            "--sender-session", "sender-1", "--worktree-path", "/wt/x", "--hmad-dispatch", d)
    assert r.returncode == 1 and "NOT_YET" in r.stdout


def test_a_handover_stamp_appended_after_a_human_note_is_not_pickup(tmp_path) -> None:
    """Step 4 PRESERVES a human note by appending, so the sender's own stamp
    legitimately sits mid-string. Under a prefix test that comment matches
    neither stamp and would now read as a receiver rewrite -- the sender echoed
    back at themselves as proof of pickup."""
    d = fake_dispatch(tmp_path, ps("/wt/x", "do not kill this pane - handover: feat - next: fix it"))
    r = run("--state", state(tmp_path, {"owner_session_id": "sender-1"}), "--feature", "feat",
            "--sender-session", "sender-1", "--worktree-path", "/wt/x", "--hmad-dispatch", d)
    assert r.returncode == 1 and "NOT_YET" in r.stdout


# --- the branch signal ------------------------------------------------------


def _repo(tmp_path: Path, *, branch: str | None, commit_on_branch: bool = False,
          merge: bool = False) -> str:
    r = tmp_path / "repo"
    r.mkdir()
    def g(*a): subprocess.run(["git", "-C", str(r), *a], check=True, capture_output=True)
    subprocess.run(["git", "init", "-q", str(r)], check=True, capture_output=True)
    g("config", "user.email", "t@e.com"); g("config", "user.name", "T")
    (r / "a.txt").write_text("1\n"); g("add", "a.txt"); g("commit", "-qm", "base")
    g("branch", "-M", "main")
    if branch:
        g("checkout", "-q", "-b", branch)
        if commit_on_branch:
            (r / "b.txt").write_text("2\n"); g("add", "b.txt"); g("commit", "-qm", "work")
        g("checkout", "-q", "main")
        if merge:
            g("merge", "-q", "--no-ff", "-m", "merge", branch)
    return str(r)


def _branch_run(tmp_path, repo, branch):
    """Point --state at a MISSING file so the claim signal is `unknown`.

    Isolating the branch signal needs the other two silent, and `unknown` is the
    only silence there is: a readable state file with the sender still owning is
    a real `not_yet`, which would decide the verdict before the branch signal was
    consulted and make every assertion below measure the wrong thing.
    """
    return run("--state", str(tmp_path / "no-such-state.json"), "--feature", "feat",
               "--sender-session", "sender-1", "--repo", repo, "--branch", branch)


def test_commits_on_the_target_branch_are_pickup(tmp_path) -> None:
    """The receiver who claims nothing and stamps nothing, and just does the
    work. Both other signals read negative there, honestly."""
    r = _branch_run(tmp_path, _repo(tmp_path, branch="recv", commit_on_branch=True), "recv")
    assert r.returncode == 0, r.stdout
    assert "LANDED" in r.stdout


def test_a_merged_target_branch_is_unknown_because_it_is_indistinguishable(tmp_path) -> None:
    """The limitation, pinned rather than papered over.

    A branch that merged and one that never committed are BOTH level with the
    default and both listed by `git branch --merged`, so refs alone cannot tell
    them apart. This test and the level-with-default one below deliberately
    assert the SAME verdict: that identity is the evidence that the tie is real,
    and it is why this signal only ever adds pickup evidence. The merged case is
    recovered by the claim or comment signal, or not at all.
    """
    r = _branch_run(tmp_path, _repo(tmp_path, branch="recv", commit_on_branch=True, merge=True), "recv")
    assert r.returncode == 2, r.stdout
    assert "UNKNOWN" in r.stdout


def test_an_absent_target_branch_is_unknown_not_not_yet(tmp_path) -> None:
    """The commonest reason a handover branch is gone is that it merged and was
    deleted -- pickup, not absence. Rendering that as NOT_YET is the same
    conflation the UNKNOWN verdict exists to refuse, on a new surface."""
    r = _branch_run(tmp_path, _repo(tmp_path, branch=None), "recv")
    assert r.returncode == 2, r.stdout
    assert "UNKNOWN" in r.stdout


def test_a_target_branch_level_with_default_is_unknown_not_a_verdict(tmp_path) -> None:
    """`git branch --merged` lists a merged branch and an untouched one alike,
    so zero-ahead cannot be resolved either way. Guessing `taken` invents
    evidence; guessing `not_yet` is the false-absence failure this tool exists
    to refuse."""
    r = _branch_run(tmp_path, _repo(tmp_path, branch="recv"), "recv")
    assert r.returncode == 2, r.stdout
    assert "UNKNOWN" in r.stdout


def test_a_non_repo_path_is_unknown_not_not_yet(tmp_path) -> None:
    d = tmp_path / "notarepo"; d.mkdir()
    r = _branch_run(tmp_path, str(d), "recv")
    assert r.returncode == 2 and "UNKNOWN" in r.stdout


def test_the_senders_own_handover_stamp_is_not_pickup(tmp_path) -> None:
    s = state(tmp_path, {"owner_session_id": None})
    d = fake_dispatch(tmp_path, ps("/repo/wt", "handover: feat · delivered · next: pick up"))
    r = run("--state", s, "--feature", "feat", "--sender-session", "s1",
            "--worktree-path", "/repo/wt", "--hmad-dispatch", d)
    assert r.returncode == 1 and "NOT_YET" in r.stdout


def test_a_missing_worktrees_container_is_unknown_not_absent(tmp_path) -> None:
    """`.get("worktrees", [])` would turn a wrong key into 'no such worktree' —
    the same value, the opposite answer. Asserted instead."""
    s = state(tmp_path, {"owner_session_id": None})
    d = fake_dispatch(tmp_path, json.dumps({"result": {"worktrees": []}}))
    r = run("--state", s, "--feature", "feat", "--sender-session", "s1",
            "--worktree-path", "/repo/wt", "--hmad-dispatch", d)
    assert "container" in r.stdout
    assert r.returncode == 1, "the claim signal still answered, so this is not UNKNOWN"


def test_no_wrapper_on_path_is_unknown_not_a_crash(tmp_path) -> None:
    """Off Orca this is the normal case, and the claim signal alone must still
    produce a verdict."""
    s = state(tmp_path, {"owner_session_id": "receiver-1"})
    r = run("--state", s, "--feature", "feat", "--sender-session", "s1",
            "--worktree-path", "/repo/wt", "--hmad-dispatch", str(tmp_path / "absent"))
    assert r.returncode == 0 and "LANDED" in r.stdout


def test_both_signals_unavailable_is_unknown(tmp_path) -> None:
    r = run("--state", str(tmp_path / "nope.json"), "--feature", "feat",
            "--sender-session", "s1", "--worktree-path", "/repo/wt",
            "--hmad-dispatch", str(tmp_path / "absent"))
    assert r.returncode == 2 and "Do not re-deliver" in r.stdout


def test_the_script_never_invokes_orca_directly() -> None:
    """This skill states twice that all Orca access goes through the wrapper."""
    src = SCRIPT.read_text(encoding="utf-8")
    import re
    calls = re.findall(r'"orca[ "]|\borca\s+terminal\b|\borca\s+worktree\b', src)
    assert not calls, f"direct orca invocation in the script: {calls}"
