"""No path through WRITE ends with an unreferenced file.

The measured failure, 2026-08-29: three handoff docs became orphans. WRITE
reported success, the file was on disk, the INDEX entry was written and the
learnings landed -- and only `git log --all -- <path>`, which nothing prompted
anyone to run, showed zero commits. The old hand-written commit step declined to
commit whenever the canonical root was a linked worktree that was dirty or off
its default branch, and the decline was the last thing that ever happened to the
file. `handoff_commit.py` replaced that branch with three destinations, every one
of which is supposed to end with the file reachable from a ref.

Supposed to. Measured 2026-09-02: `grep -rln handoff_commit handoff/tests/`
returned nothing -- the module had no tests at all, so the property it exists to
provide was asserted nowhere. These tests are that assertion, one per mode.

Reachability is checked with `git rev-list --all`, which git defines as "all the
refs in refs/, along with HEAD". That deliberately includes `refs/handoffs/*`,
which is the whole point of ref mode: the commit touches no worktree and moves no
HEAD, so a check written against branches alone would call a correct ref-mode
commit an orphan, and a check written against `git cat-file -e` would call a
genuinely unreferenced blob reachable. Neither is the question. The question is
whether a future reader can get the file back.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import handoff_commit  # noqa: E402


def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"git {' '.join(args)} failed in {cwd}: {r.stderr}"
    return r.stdout.strip()


def _repo(root: Path) -> Path:
    """A repo on `main` with one commit, and no remote (push is skipped anyway)."""
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q", "-b", "main", str(root)], root.parent)
    _git(["config", "user.email", "t@example.com"], root)
    _git(["config", "user.name", "T"], root)
    (root / "README.md").write_text("seed\n")
    _git(["add", "README.md"], root)
    _git(["commit", "-qm", "seed"], root)
    return root


def _handoff_doc(root: Path, name: str = "docs/handoffs/2026-09-02-main__x.md") -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# Handoff — x\n")
    return p


def _reachable(root: Path, rel: str) -> bool:
    """Is any commit touching `rel` reachable from a ref (refs/handoffs included)?"""
    return bool(_git(["rev-list", "--all", "--", rel], root))


def _run(paths: list[Path], repo: Path) -> tuple[int, list[str]]:
    return handoff_commit.run(
        [str(p) for p in paths],
        "chore(handoff): test",
        repo=str(repo),
        push=False,
    )


def test_main_mode_leaves_the_doc_reachable(tmp_path: Path) -> None:
    """cwd IS the canonical root: an ordinary commit on the current branch."""
    root = _repo(tmp_path / "repo")
    doc = _handoff_doc(root)

    rc, report = _run([doc], root)

    assert rc == 0, report
    assert any(line.startswith("mode: main") for line in report), report
    assert _reachable(root, "docs/handoffs/2026-09-02-main__x.md"), report


def test_direct_mode_leaves_the_doc_reachable_from_a_worktree(tmp_path: Path) -> None:
    """Run from a linked worktree while the canonical tree is clean and on main.

    The commit lands in the canonical tree, not the worktree the session sits in.
    """
    root = _repo(tmp_path / "repo")
    wt = tmp_path / "wt"
    _git(["worktree", "add", "-q", "-b", "feature/x", str(wt)], root)
    doc = _handoff_doc(root)

    rc, report = _run([doc], wt)

    assert rc == 0, report
    assert any(line.startswith("mode: direct") for line in report), report
    assert _reachable(root, "docs/handoffs/2026-09-02-main__x.md"), report


def test_ref_mode_leaves_the_doc_reachable_without_touching_a_tree(
    tmp_path: Path,
) -> None:
    """The case that used to DECLINE, which is how three docs were orphaned.

    The canonical tree is dirty with unrelated work, so it must not be committed
    into — and the doc must still end up reachable.
    """
    root = _repo(tmp_path / "repo")
    wt = tmp_path / "wt"
    _git(["worktree", "add", "-q", "-b", "feature/x", str(wt)], root)
    (root / "unrelated.txt").write_text("someone else is mid-edit\n")
    head_before = _git(["rev-parse", "HEAD"], root)
    doc = _handoff_doc(root)

    rc, report = _run([doc], wt)

    assert rc == 0, report
    assert any(line.startswith("mode: ref") for line in report), report
    rel = "docs/handoffs/2026-09-02-main__x.md"
    assert _reachable(root, rel), report

    # The properties that make ref mode safe to use on a tree someone else owns.
    assert _git(["rev-parse", "HEAD"], root) == head_before, "ref mode moved HEAD"
    assert (root / "unrelated.txt").read_text() == "someone else is mid-edit\n"
    assert _git(["diff", "--cached", "--name-only"], root) == "", "ref mode staged"
    # And it is landed by cherry-pick, never by merging the ref.
    assert any("cherry-pick" in line for line in report), report


def test_every_mode_is_covered_by_a_reachability_test() -> None:
    """A new destination must arrive with a test, not silently widen the gap.

    `choose_mode` is the only place that names them, so read them from it rather
    than restating the list here — a restated list agrees with itself forever.
    """
    src = (SCRIPTS / "handoff_commit.py").read_text(encoding="utf-8")
    body = src[src.index("def choose_mode(") : src.index("def commit_in_tree(")]
    modes = {
        line.split('return "', 1)[1].split('"', 1)[0]
        for line in body.splitlines()
        if 'return "' in line
    }
    tested = {"main", "direct", "ref"}
    assert modes == tested, (
        f"handoff_commit.choose_mode returns {sorted(modes)} but reachability is "
        f"asserted for {sorted(tested)} — a mode with no test is how a WRITE ends "
        "with an unreferenced file"
    )
