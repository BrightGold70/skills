"""Tests for handoff_commit — no path through WRITE ends with an unreferenced file.

The property under test is deliberately NOT "a commit happened". WRITE has three
routes to a commit and only one of them was ever broken; a test that asserts the
happy path leaves the linked-worktree branch exactly as broken as it was. So the
sweep below drives every route and asserts the same thing of each: after the run,
`git log --all -- <path>` is non-zero.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import handoff_commit as hc  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return r.stdout.strip()


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@t.t")
    _git(root, "config", "user.name", "t")
    (root / "README.md").write_text("seed\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-q", "-m", "init")


def _linked(root: Path, wt: Path, branch: str = "feature/x") -> Path:
    _git(root, "worktree", "add", "-q", "-b", branch, str(wt))
    return wt


def _write_handoff(root: Path, name: str = "h1.md") -> Path:
    d = root / "docs" / "handoffs"
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    f.write_text(f"# {name}\n")
    return f


def _refcount(root: Path, path: Path) -> int:
    rel = str(path.resolve().relative_to(root.resolve()))
    out = _git(root, "log", "--all", "--oneline", "--", rel)
    return len([ln for ln in out.splitlines() if ln.strip()])


# ---------------------------------------------------------------- routing


def test_main_worktree_routes_to_main(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    f = _write_handoff(repo)
    mode, _ = hc.choose_mode(repo, repo, [str(f.relative_to(repo))])
    assert mode == "main"


def test_linked_worktree_with_clean_default_main_routes_to_direct(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    f = _write_handoff(repo)
    mode, _ = hc.choose_mode(repo, wt, [str(f.relative_to(repo))])
    assert mode == "direct"


def test_linked_worktree_with_dirty_main_routes_to_ref(tmp_path):
    # The case that actually bites: HemaSuite's shared checkout, measured
    # 2026-08-30, was on a feature branch with 16 dirty lines.
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    (repo / "README.md").write_text("someone else is mid-work\n")
    f = _write_handoff(repo)
    mode, why = hc.choose_mode(repo, wt, [str(f.relative_to(repo))])
    assert mode == "ref"
    assert "uncommitted" in why


def test_linked_worktree_with_offdefault_main_routes_to_ref(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    _git(repo, "checkout", "-q", "-b", "some-feature")
    f = _write_handoff(repo)
    mode, why = hc.choose_mode(repo, wt, [str(f.relative_to(repo))])
    assert mode == "ref"
    assert "default branch" in why


def test_the_handoff_paths_themselves_never_count_as_dirt(tmp_path):
    # WRITE has already written the doc into this tree before the commit step,
    # so a naive `git status --porcelain` check is ALWAYS non-empty and would
    # send every run to `ref` mode, making `direct` dead code.
    repo = tmp_path / "r"
    _init_repo(repo)
    learnings = repo / "docs" / "learnings.md"
    learnings.parent.mkdir(parents=True, exist_ok=True)
    learnings.write_text("# Learnings\n")
    _git(repo, "add", "docs/learnings.md")
    _git(repo, "commit", "-q", "-m", "seed learnings")

    f = _write_handoff(repo)
    learnings.write_text("# Learnings\n- appended\n")
    rel = str(f.relative_to(repo))
    assert _git(repo, "status", "--porcelain") != ""
    assert hc.is_clean_ignoring(repo, [rel, "docs/learnings.md"]) is True
    assert hc.is_clean_ignoring(repo, [rel]) is False
    assert hc.is_clean_ignoring(repo, []) is False


# ---------------------------------------------------------------- the property


@pytest.mark.parametrize(
    "scenario,expect_mode",
    [("main", "main"), ("direct", "direct"), ("ref", "ref")],
)
def test_no_route_ends_with_an_unreferenced_file(tmp_path, scenario, expect_mode):
    repo = tmp_path / "r"
    _init_repo(repo)
    cwd = repo
    if scenario != "main":
        cwd = _linked(repo, tmp_path / "wt")
    if scenario == "ref":
        (repo / "README.md").write_text("foreign work in flight\n")
    f = _write_handoff(repo)

    assert _refcount(repo, f) == 0, "control: unreferenced before the run"
    rc, report = hc.run([str(f)], "chore(handoff): test", repo=str(cwd), push=False)
    assert rc == 0, report
    assert f"mode: {expect_mode}" in "\n".join(report), report
    assert _refcount(repo, f) > 0, report


def test_second_write_from_the_same_branch_keeps_the_first_referenced(tmp_path):
    # The regression the chained ref exists to prevent. A bare `update-ref` moves
    # refs/handoffs/<slug> off the first commit; that commit is reachable from
    # nothing else, so the doc it rescued goes straight back to zero refs — the
    # property regressing on the SECOND closeout of any branch.
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    (repo / "README.md").write_text("dirty, so both runs take the ref route\n")

    first = _write_handoff(repo, "h-first.md")
    rc, r1 = hc.run([str(first)], "chore(handoff): first", repo=str(wt), push=False)
    assert rc == 0 and _refcount(repo, first) > 0, r1

    second = _write_handoff(repo, "h-second.md")
    rc, r2 = hc.run([str(second)], "chore(handoff): second", repo=str(wt), push=False)
    assert rc == 0, r2

    assert _refcount(repo, second) > 0, r2
    assert _refcount(repo, first) > 0, "the first doc was re-orphaned by the second run"


# ---------------------------------------------------------------- blast radius


def test_ref_mode_touches_no_worktree(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    (repo / "README.md").write_text("foreign work in flight\n")
    f = _write_handoff(repo)

    head_before = _git(repo, "rev-parse", "HEAD")
    status_before = _git(repo, "status", "--porcelain")
    hc.run([str(f)], "chore(handoff): x", repo=str(wt), push=False)

    assert _git(repo, "rev-parse", "HEAD") == head_before, "main HEAD moved"
    assert _git(repo, "status", "--porcelain") == status_before, "main tree changed"
    assert _git(repo, "diff", "--cached", "--name-only") == "", "something was staged"


def test_direct_mode_does_not_sweep_up_foreign_staged_content(tmp_path):
    # A shared tree can gain a staged file between the cleanliness check and the
    # commit. `commit --only` must confine the commit to the handoff paths.
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    f = _write_handoff(repo)
    rel = str(f.relative_to(repo))

    (repo / "foreign.txt").write_text("another session's staged work\n")
    _git(repo, "add", "foreign.txt")

    sha = hc.commit_in_tree(repo, [rel], "chore(handoff): only mine")
    assert sha
    names = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert names == [rel], names
    assert "foreign.txt" in _git(repo, "diff", "--cached", "--name-only")


# ---------------------------------------------------------------- guards


def test_path_outside_the_canonical_root_is_refused(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    stray = tmp_path / "elsewhere.md"
    stray.write_text("x\n")
    with pytest.raises(hc.HandoffCommitError, match="outside the canonical root"):
        hc.to_repo_relative(repo, [str(stray)])


def test_missing_paths_are_dropped_not_fatal(tmp_path):
    # `--skip-learnings` means docs/learnings.md may not exist. That is a normal
    # closeout, not an error.
    repo = tmp_path / "r"
    _init_repo(repo)
    f = _write_handoff(repo)
    rc, report = hc.run(
        [str(f), str(repo / "docs" / "learnings.md")],
        "chore(handoff): partial",
        repo=str(repo),
        push=False,
    )
    assert rc == 0, report
    assert _refcount(repo, f) > 0


def test_rerunning_with_unchanged_content_adds_no_empty_commit(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    (repo / "README.md").write_text("dirty\n")
    f = _write_handoff(repo)

    hc.run([str(f)], "chore(handoff): x", repo=str(wt), push=False)
    slug = hc.branch_slug(wt)
    tip = _git(repo, "rev-parse", f"refs/handoffs/{slug}")
    rc, report = hc.run([str(f)], "chore(handoff): x again", repo=str(wt), push=False)
    assert rc == 0
    assert "NOTHING-TO-COMMIT" in "\n".join(report), report
    assert _git(repo, "rev-parse", f"refs/handoffs/{slug}") == tip


def test_dry_run_writes_nothing(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    wt = _linked(repo, tmp_path / "wt")
    (repo / "README.md").write_text("dirty\n")
    f = _write_handoff(repo)
    rc, report = hc.run(
        [str(f)], "chore(handoff): x", repo=str(wt), push=False, dry_run=True
    )
    assert rc == 0
    assert "DRY-RUN" in "\n".join(report)
    assert _refcount(repo, f) == 0


# ---------------------------------------------------------------- push ownership


def _with_origin(tmp_path: Path, repo: Path) -> Path:
    bare = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "-u", "origin", "main")
    return bare


def test_direct_mode_pushes_the_canonical_branch_itself(tmp_path):
    # SKILL.md's §Sync/§Push carry no `-C`, so from a linked worktree they would
    # act on the feature branch, not the canonical one the commit landed on. If
    # the script does not push here, the handoff commit silently never leaves the
    # machine while the closeout reports success.
    repo = tmp_path / "r"
    _init_repo(repo)
    bare = _with_origin(tmp_path, repo)
    wt = _linked(repo, tmp_path / "wt")
    f = _write_handoff(repo)

    rc, report = hc.run([str(f)], "chore(handoff): direct", repo=str(wt), push=True)
    assert rc == 0, report
    joined = "\n".join(report)
    assert "mode: direct" in joined, joined
    assert "push: OK" in joined, joined

    rel = str(f.relative_to(repo))
    assert _git(bare, "log", "--oneline", "main", "--", rel).strip(), (
        "the handoff commit never reached origin"
    )
    # and it must NOT have pushed the linked worktree's feature branch
    assert "feature/x" not in _git(bare, "branch", "--format=%(refname:short)")


def test_ref_mode_pushes_the_ref_as_a_normal_branch(tmp_path):
    # A custom refs/handoffs/* namespace on the remote is invisible to default
    # fetch refspecs and to the forge UI — which is the whole point of pushing.
    repo = tmp_path / "r"
    _init_repo(repo)
    _with_origin(tmp_path, repo)
    bare = tmp_path / "origin.git"
    wt = _linked(repo, tmp_path / "wt")
    (repo / "README.md").write_text("dirty\n")
    f = _write_handoff(repo)

    rc, report = hc.run([str(f)], "chore(handoff): ref", repo=str(wt), push=True)
    assert rc == 0 and "push: OK" in "\n".join(report), report
    branches = _git(bare, "branch", "--format=%(refname:short)").split()
    assert "handoff/feature-x" in branches, branches


# ---------------------------------------------------------------- input guard


def test_a_missing_handoff_doc_is_fatal_not_a_quiet_success(tmp_path):
    # Absorbing a mistyped path as "nothing to commit, rc=0" would end the
    # closeout with an unreferenced file while every observable said it worked —
    # the exact silent shape this script exists to remove, reintroduced at its
    # own front door.
    repo = tmp_path / "r"
    _init_repo(repo)
    with pytest.raises(hc.HandoffCommitError, match="refusing to report"):
        hc.run(
            [str(repo / "docs" / "handoffs" / "typo.md")],
            "chore(handoff): x",
            repo=str(repo),
            push=False,
        )


# ---------------------------------------------------------------- onto-default (row 2953)


def test_onto_default_from_feature_checkout_commits_to_main_and_restores_checkout(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    doc = repo / "docs" / "skill-candidates.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# Candidates\n- row 1 — candidate: yes\n")
    _git(repo, "add", "docs/skill-candidates.md")
    _git(repo, "commit", "-q", "-m", "seed candidates")
    _with_origin(tmp_path, repo)
    bare = tmp_path / "origin.git"

    _git(repo, "checkout", "-q", "-b", "feature/split")
    (repo / "feature.py").write_text("x = 1\n")
    _git(repo, "add", "feature.py")
    _git(repo, "commit", "-q", "-m", "feature commit")
    feat_head = _git(repo, "rev-parse", "HEAD")

    # Edit the doc in the feature checkout alongside unrelated in-flight work.
    (repo / "in_flight.txt").write_text("wip\n")
    doc.write_text("# Candidates\n- row 1 — candidate: yes\n  — **LANDED**\n")

    rc, report = hc.run(
        [str(doc)],
        "docs(skill-candidates): stamp row 1",
        repo=str(repo),
        push=True,
        onto_default=True,
    )
    assert rc == 0, report
    joined = "\n".join(report)
    assert "mode: onto-default" in joined, joined
    assert "push: OK" in joined, joined

    # Landed on main (and pushed to origin/main), while feature/split HEAD and tree are untouched.
    assert "LANDED" in _git(repo, "show", "main:docs/skill-candidates.md")
    assert "LANDED" in _git(bare, "show", "main:docs/skill-candidates.md")
    assert _git(repo, "rev-parse", "HEAD") == feat_head
    assert doc.read_text() == "# Candidates\n- row 1 — candidate: yes\n"
    assert (repo / "in_flight.txt").read_text() == "wip\n"
    assert _git(repo, "diff", "--name-only", "HEAD", "--", "docs/skill-candidates.md") == ""


def test_onto_default_from_linked_worktree_updates_checked_out_main_and_restores_wt(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    doc = repo / "docs" / "skill-candidates.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# Candidates\n- row 1 — candidate: yes\n")
    _git(repo, "add", "docs/skill-candidates.md")
    _git(repo, "commit", "-q", "-m", "seed candidates")
    _with_origin(tmp_path, repo)

    wt = _linked(repo, tmp_path / "wt", branch="feature/y")
    # Unrelated dirty file in the main worktree must not block or be swept into --only commit.
    (repo / "README.md").write_text("unrelated main edit\n")
    wt_doc = wt / "docs" / "skill-candidates.md"
    wt_doc.write_text("# Candidates\n- row 1 — candidate: yes\n  — **LANDED**\n")

    rc, report = hc.run(
        [str(wt_doc)],
        "docs(skill-candidates): stamp from wt",
        repo=str(wt),
        push=False,
        onto_default=True,
    )
    assert rc == 0, report
    assert "LANDED" in (repo / "docs" / "skill-candidates.md").read_text()
    assert "LANDED" in _git(repo, "show", "main:docs/skill-candidates.md")
    assert (repo / "README.md").read_text() == "unrelated main edit\n"
    assert wt_doc.read_text() == "# Candidates\n- row 1 — candidate: yes\n"
    assert _git(wt, "status", "--porcelain") == ""


def test_onto_default_refuses_when_path_differs_between_head_and_default(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    doc = repo / "docs" / "skill-candidates.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("base\n")
    _git(repo, "add", "docs/skill-candidates.md")
    _git(repo, "commit", "-q", "-m", "seed")

    _git(repo, "checkout", "-q", "-b", "feature/diverged")
    doc.write_text("feature committed change\n")
    _git(repo, "add", "docs/skill-candidates.md")
    _git(repo, "commit", "-q", "-m", "diverge doc on feature")
    doc.write_text("feature committed change + new stamp\n")

    with pytest.raises(hc.HandoffCommitError, match="differs between HEAD and main"):
        hc.run(
            [str(doc)],
            "docs: unsafe stamp",
            repo=str(repo),
            push=False,
            onto_default=True,
        )


def test_onto_default_refuses_when_checked_out_default_has_dirty_target_path(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    doc = repo / "docs" / "skill-candidates.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("base\n")
    _git(repo, "add", "docs/skill-candidates.md")
    _git(repo, "commit", "-q", "-m", "seed")

    wt = _linked(repo, tmp_path / "wt", branch="feature/z")
    # Main worktree has uncommitted edits to the same target file.
    doc.write_text("uncommitted edit in main\n")
    wt_doc = wt / "docs" / "skill-candidates.md"
    wt_doc.write_text("stamp in wt\n")

    with pytest.raises(hc.HandoffCommitError, match="uncommitted changes"):
        hc.run(
            [str(wt_doc)],
            "docs: conflict",
            repo=str(wt),
            push=False,
            onto_default=True,
        )


def test_onto_default_cli_flag_and_new_untracked_file_cleanup(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _git(repo, "checkout", "-q", "-b", "feature/newdoc")
    new_doc = repo / "docs" / "note.md"
    new_doc.parent.mkdir(parents=True, exist_ok=True)
    new_doc.write_text("# New note\n")

    rc = hc.main(
        [
            "--onto-default",
            "--no-push",
            "--repo",
            str(repo),
            "-m",
            "docs: add note on main",
            str(new_doc),
        ]
    )
    assert rc == 0
    assert _git(repo, "show", "main:docs/note.md") == "# New note"
    assert not new_doc.exists()
    assert _git(repo, "status", "--porcelain") == ""

