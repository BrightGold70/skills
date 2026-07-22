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
