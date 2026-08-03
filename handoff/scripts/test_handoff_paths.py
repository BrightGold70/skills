"""Tests for handoff_paths — canonical, worktree-shared handoff/learnings paths."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import handoff_paths as hp  # noqa: E402


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t.t")
    _git(root, "config", "user.name", "t")
    _git(root, "commit", "--allow-empty", "-q", "-m", "init")


def test_canonical_root_in_main_repo_is_toplevel(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    assert hp.canonical_root(repo).resolve() == repo.resolve()


def test_canonical_root_from_linked_worktree_points_to_main(tmp_path):
    # THE fragmentation fix: a linked worktree must resolve to the MAIN root, so
    # handoffs/learnings are one shared store, not per-worktree.
    repo = tmp_path / "repo"
    _init_repo(repo)
    wt = tmp_path / "wt-feature"
    _git(repo, "worktree", "add", "-q", "-b", "feature/x", str(wt))

    # show-toplevel from the worktree is the worktree itself...
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=wt,
                         capture_output=True, text=True, check=True).stdout.strip()
    assert Path(top).resolve() == wt.resolve()
    # ...but canonical_root must be the MAIN worktree root.
    assert hp.canonical_root(wt).resolve() == repo.resolve()


def test_handoffs_dir_and_learnings_path_anchor_to_canonical(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", "-b", "b1", str(wt))
    assert hp.handoffs_dir(wt).resolve() == (repo / "docs" / "handoffs").resolve()
    assert hp.learnings_path(wt).resolve() == (repo / "docs" / "learnings.md").resolve()


def test_branch_slug_sanitizes(monkeypatch):
    monkeypatch.setattr(hp, "_git", lambda args, cwd=None:"feature/189-foo bar")
    assert hp.branch_slug() == "feature-189-foo-bar"


def test_branch_slug_detached_head(monkeypatch):
    monkeypatch.setattr(hp, "_git", lambda args, cwd=None:"HEAD")
    assert hp.branch_slug() == "nobranch"


def test_find_latest_prefers_branch_then_newest(tmp_path):
    d = tmp_path / "repo" / "docs" / "handoffs"
    d.mkdir(parents=True)
    (d / "2026-07-20-feature-a__old.md").write_text("x")
    (d / "2026-07-22-feature-a__new.md").write_text("x")
    (d / "2026-07-23-feature-b__newest.md").write_text("x")

    # repo-wide newest ignores branch
    latest_any = hp.find_latest(branch=None, start=tmp_path / "repo")
    assert latest_any is not None and latest_any.name == "2026-07-23-feature-b__newest.md"
    # branch filter picks that branch's newest, not the repo newest
    latest_a = hp.find_latest(branch="feature-a", start=tmp_path / "repo")
    assert latest_a is not None and latest_a.name == "2026-07-22-feature-a__new.md"


def test_find_latest_branch_does_not_false_match_prefix_sibling(tmp_path):
    # HIGH regression: resuming `feat` must NOT pick up a `feat-ab` sibling's
    # handoff. The `__` separator + anchored match guarantees exactness even
    # though `feat` is a `-`-boundary prefix of `feat-ab`.
    d = tmp_path / "repo" / "docs" / "handoffs"
    d.mkdir(parents=True)
    (d / "2026-07-23-feat-ab__other.md").write_text("x")   # sibling branch
    (d / "2026-07-22-feat__mine.md").write_text("x")        # my branch (older)

    assert hp.find_latest(branch="feat", start=tmp_path / "repo").name == "2026-07-22-feat__mine.md"
    assert hp.find_latest(branch="feat-ab", start=tmp_path / "repo").name == "2026-07-23-feat-ab__other.md"
    # `feat` must NOT return the newer sibling file
    assert "feat-ab" not in hp.find_latest(branch="feat", start=tmp_path / "repo").name


def test_find_latest_same_day_discriminator_orders_by_mtime(tmp_path):
    # LOW: a same-day concurrency-guard discriminant (`…-2.md`) sorts before the
    # base name lexically (`-` < `.`); the mtime tiebreak must still rank it newer.
    import os
    d = tmp_path / "repo" / "docs" / "handoffs"
    d.mkdir(parents=True)
    base = d / "2026-07-22-b1__topic.md"; base.write_text("x")
    disc = d / "2026-07-22-b1__topic-2.md"; disc.write_text("x")
    # make the discriminated file newer by mtime
    os.utime(base, (1000, 1000)); os.utime(disc, (2000, 2000))

    assert hp.find_latest(branch="b1", start=tmp_path / "repo").name == "2026-07-22-b1__topic-2.md"


def test_find_latest_none_when_empty(tmp_path):
    assert hp.find_latest(start=tmp_path) is None


def test_cli_dir_and_branch_slug_run(tmp_path, capsys):
    repo = tmp_path / "repo"
    _init_repo(repo)
    import os
    cwd = os.getcwd()
    try:
        os.chdir(repo)
        assert hp.main(["dir"]) == 0
        out = capsys.readouterr().out.strip()
        assert out.endswith("docs/handoffs")
    finally:
        os.chdir(cwd)


# --- `--repo`: resolving ANOTHER repo's store (HANDOVER mode) --------------
#
# A handover writes the brief into the RECEIVER's canonical store, not the
# sender's. Every function here already took a `start` argument; the CLI just
# never exposed it, so callers had to `cd` and hope. These pin the flag and,
# more importantly, pin that a bad target fails LOUDLY — silently resolving a
# wrong-but-plausible path would write the receiver's brief somewhere they will
# never look while reporting success.


def _cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "handoff_paths.py"), *args],
        cwd=cwd, capture_output=True, text=True,
    )


def test_repo_flag_resolves_the_target_store_not_the_cwd(tmp_path):
    sender, receiver = tmp_path / "sender", tmp_path / "receiver"
    _init_repo(sender)
    _init_repo(receiver)
    proc = _cli("--repo", str(receiver), "dir", cwd=sender)
    assert proc.returncode == 0, proc.stderr
    assert Path(proc.stdout.strip()).resolve() == (receiver / "docs" / "handoffs").resolve()


def test_repo_flag_reports_the_target_branch_not_the_senders(tmp_path):
    # The filename carries the branch slug, and READ matches on it exactly. A
    # brief written under the sender's branch is invisible to the receiver's
    # resume even though it sits in the right directory.
    sender, receiver = tmp_path / "sender", tmp_path / "receiver"
    _init_repo(sender)
    _init_repo(receiver)
    _git(receiver, "checkout", "-q", "-b", "feature/196-grounding")
    proc = _cli("--repo", str(receiver), "branch-slug", cwd=sender)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "feature-196-grounding"


def test_repo_flag_finds_the_targets_latest_handoff(tmp_path):
    sender, receiver = tmp_path / "sender", tmp_path / "receiver"
    _init_repo(sender)
    _init_repo(receiver)
    d = receiver / "docs" / "handoffs"
    d.mkdir(parents=True)
    (d / "2026-08-03-main__theirs.md").write_text("x", encoding="utf-8")
    proc = _cli("--repo", str(receiver), "latest", cwd=sender)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("2026-08-03-main__theirs.md")


def test_without_the_flag_the_cwd_still_wins(tmp_path):
    # Counter-direction: the flag must not become the only path that works.
    sender = tmp_path / "sender"
    _init_repo(sender)
    proc = _cli("dir", cwd=sender)
    assert proc.returncode == 0, proc.stderr
    assert Path(proc.stdout.strip()).resolve() == (sender / "docs" / "handoffs").resolve()


def test_a_nonexistent_target_is_refused(tmp_path):
    # Assert the SPECIFIC diagnostic, not merely that something was refused.
    # Both guards reject a nonexistent path — a missing directory also makes the
    # git probe fail — so a test that only checks "non-zero" passes with the
    # existence check deleted and hands a typo the message "not inside a git work
    # tree", sending the operator to debug git instead of their spelling.
    sender = tmp_path / "sender"
    _init_repo(sender)
    proc = _cli("--repo", str(tmp_path / "nope"), "dir", cwd=sender)
    assert proc.returncode != 0, f"a bogus target resolved to {proc.stdout.strip()!r}"
    assert "no such directory" in proc.stderr, (
        f"a missing path must be named as missing, not misreported: {proc.stderr!r}"
    )


def test_a_target_that_is_not_a_git_repo_is_refused(tmp_path):
    # The dangerous case, because it looks like it worked: a real directory that
    # is not a repo would resolve to `<dir>/docs/handoffs` and the brief would be
    # written to a store nothing ever reads.
    sender = tmp_path / "sender"
    _init_repo(sender)
    plain = tmp_path / "just-a-folder"
    plain.mkdir()
    proc = _cli("--repo", str(plain), "dir", cwd=sender)
    assert proc.returncode != 0, f"a non-repo target resolved to {proc.stdout.strip()!r}"
    assert "git" in proc.stderr.lower(), proc.stderr
