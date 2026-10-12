"""Is this branch's work already on the default branch?

Skill-candidates rows 2495 (an unpushed-work audit) and 2478 (a squash-merged branch before
`branch -D`). HemaSuite carried "26 unpushed commits" through three handoffs when all 26
were on main: the branch was ahead of its OWN remote, and the local `origin/main` was stale.
Every test here builds a throwaway repo with a bare origin, so the git is real.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "local_only_commits.py"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), *args],
                          capture_output=True, text=True)


def commit(repo: Path, path: str, text: str, msg: str) -> str:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text, encoding="utf-8")
    git(repo, "add", path)
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


def project(tmp_path: Path) -> tuple[Path, Path]:
    """A clone of a bare origin whose `main` holds one commit, origin/HEAD set."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    repo = tmp_path / "repo"
    git(tmp_path, "clone", "-q", str(origin), str(repo))
    git(repo, "checkout", "-q", "-b", "main")
    commit(repo, "a.txt", "one\n", "base")
    git(repo, "push", "-q", "-u", "origin", "main")
    git(repo, "remote", "set-head", "origin", "main")
    return repo, origin


def token(proc: subprocess.CompletedProcess) -> str:
    lines = [l for l in proc.stdout.splitlines() if l.startswith("LOCAL_ONLY: ")]
    assert len(lines) == 1, proc.stdout + proc.stderr
    return lines[0]


def ref_line(proc: subprocess.CompletedProcess, name: str) -> str:
    hits = [l for l in proc.stdout.splitlines() if l.split()[1:2] == [name]]
    assert len(hits) == 1, proc.stdout
    return hits[0]


def test_a_branch_whose_tip_is_on_main_is_merged(tmp_path: Path) -> None:
    repo, _ = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    commit(repo, "b.txt", "b\n", "feat work")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--ff-only", "feat")
    git(repo, "push", "-q", "origin", "main")

    proc = run(repo)
    assert proc.returncode == 0, proc.stderr
    assert ref_line(proc, "feat").split()[0] == "MERGED", proc.stdout
    assert token(proc).startswith("LOCAL_ONLY: ALL_ON_BASE "), proc.stdout


def test_a_cherry_picked_copy_is_on_base_by_patch(tmp_path: Path) -> None:
    repo, _ = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    sha = commit(repo, "b.txt", "b\n", "feat work")
    git(repo, "checkout", "-q", "main")
    commit(repo, "c.txt", "c\n", "unrelated on main")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "cherry-pick", sha)
    git(repo, "push", "-q", "origin", "main")

    line = ref_line(run(repo), "feat")
    assert line.split()[0] == "ON_BASE" and "via=patch" in line, line


def test_a_squash_merged_branch_is_on_base_by_tree_though_cherry_says_unique(
    tmp_path: Path
) -> None:
    """Row 2478. A squash leaves every commit `+` to `git cherry`: the squash's patch
    equals none of them. Only the per-path content says the work landed."""
    repo, _ = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    commit(repo, "b.txt", "b1\n", "step 1")
    commit(repo, "b.txt", "b2\n", "step 2")
    commit(repo, "d/e.txt", "e\n", "step 3")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--squash", "feat")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "squash")
    git(repo, "push", "-q", "origin", "main")
    assert "+" in git(repo, "cherry", "origin/main", "feat")

    line = ref_line(run(repo), "feat")
    assert line.split()[0] == "ON_BASE" and "via=tree" in line, line


def test_a_branch_with_its_own_content_is_unique(tmp_path: Path) -> None:
    """The negative control for the per-path compare: if path handling degrades to
    comparing nothing, every branch reads ON_BASE and this goes red."""
    repo, _ = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    commit(repo, "a.txt", "changed\n", "real work")
    git(repo, "checkout", "-q", "main")

    proc = run(repo)
    line = ref_line(proc, "feat")
    assert line.split()[0] == "UNIQUE", line
    assert "real work" in proc.stdout, proc.stdout
    assert token(proc).startswith("LOCAL_ONLY: HAS_UNIQUE "), proc.stdout


def test_a_branch_with_one_landed_and_one_unique_commit_is_partial(tmp_path: Path) -> None:
    repo, _ = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    landed = commit(repo, "b.txt", "b\n", "landed part")
    commit(repo, "c.txt", "c\n", "unique part")
    git(repo, "checkout", "-q", "main")
    commit(repo, "m.txt", "m\n", "unrelated on main")  # else the pick can re-create the same sha
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "cherry-pick", landed)
    git(repo, "push", "-q", "origin", "main")

    proc = run(repo)
    assert ref_line(proc, "feat").split()[0] == "PARTIAL", proc.stdout
    # Only the commit that still needs a home is listed; the landed one is not.
    assert "unique part" in proc.stdout, proc.stdout
    assert "landed part" not in proc.stdout, proc.stdout


def test_a_stale_local_origin_main_is_the_incident_and_fetch_fixes_it(tmp_path: Path) -> None:
    """The HemaSuite incident. The branch's tip is already on the REMOTE main, but this
    clone's `origin/main` predates it. Without a fetch that reads UNIQUE; the default
    fetches and reads MERGED, and the token says which happened."""
    repo, origin = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    commit(repo, "b.txt", "b\n", "feat work")
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(origin), str(other))
    git(repo, "push", "-q", "origin", "feat")
    git(other, "fetch", "-q", "origin", "feat")
    git(other, "merge", "-q", "--ff-only", "origin/feat")
    git(other, "push", "-q", "origin", "HEAD:main")

    stale = run(repo, "--no-fetch")
    assert ref_line(stale, "feat").split()[0] == "UNIQUE", stale.stdout
    assert "fetched=no" in token(stale), stale.stdout

    fresh = run(repo)
    assert ref_line(fresh, "feat").split()[0] == "MERGED", fresh.stdout
    assert "fetched=yes" in token(fresh), fresh.stdout


def test_the_base_is_the_default_branch_not_the_branchs_own_upstream(tmp_path: Path) -> None:
    """'Ahead of its own remote' was the misread. A branch pushed to its own upstream and
    not on main is still UNIQUE."""
    repo, _ = project(tmp_path)
    git(repo, "checkout", "-q", "-b", "feat")
    commit(repo, "b.txt", "b\n", "pushed but not merged")
    git(repo, "push", "-q", "-u", "origin", "feat")

    proc = run(repo)
    assert ref_line(proc, "feat").split()[0] == "UNIQUE", proc.stdout
    assert "base=origin/main" in token(proc), proc.stdout


def test_a_detached_linked_worktree_head_is_audited(tmp_path: Path) -> None:
    """h-mad lanes park detached. Its HEAD is read by sha through the shared object store;
    nothing is read from the other worktree's files."""
    repo, _ = project(tmp_path)
    wt = tmp_path / "lane"
    git(repo, "worktree", "add", "-q", "--detach", str(wt))
    commit(wt, "x.txt", "x\n", "detached lane work")

    proc = run(repo)
    hits = [l for l in proc.stdout.splitlines() if "detached@" in l]
    assert len(hits) == 1 and hits[0].split()[0] == "UNIQUE", proc.stdout
    assert "detached lane work" in proc.stdout, proc.stdout


def test_an_unresolvable_base_is_unreadable_not_merged(tmp_path: Path) -> None:
    repo, _ = project(tmp_path)
    proc = run(repo, "--no-fetch", "--base", "origin/nope")
    assert proc.returncode == 2, proc.stdout
    # The reason names the base, not a git error from some later call that tripped on it.
    assert token(proc).startswith("LOCAL_ONLY: UNREADABLE reason=base_unresolved: origin/nope"), \
        proc.stdout


def test_a_failed_fetch_is_unreadable_not_a_stale_verdict(tmp_path: Path) -> None:
    """A fetch that fails leaves exactly the stale base the incident came from, so it must
    not quietly produce a verdict against it."""
    repo, _ = project(tmp_path)
    git(repo, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    proc = run(repo)
    assert proc.returncode == 2, proc.stdout
    assert token(proc).startswith("LOCAL_ONLY: UNREADABLE "), proc.stdout
    assert "--no-fetch" in proc.stdout, proc.stdout


def test_not_a_repository_is_unreadable(tmp_path: Path) -> None:
    proc = run(tmp_path, "--no-fetch")
    assert proc.returncode == 2
    assert token(proc).startswith("LOCAL_ONLY: UNREADABLE "), proc.stdout
