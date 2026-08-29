#!/usr/bin/env python3
"""handoff_commit.py — close the loop so no WRITE ends with an unreferenced file.

WRITE saves the handoff doc (and appends learnings) into the **canonical**
main-worktree store resolved by `handoff_paths.py`. When WRITE runs from a
linked worktree, SKILL.md deliberately declines to commit into the main
worktree — that tree may be mid-work on an unrelated branch, and a surprise
handoff commit there is worse than none. Correct on its own; jointly broken,
because nothing then closes the loop: the doc exists on disk, every observable
says the handoff worked, and `git log --all -- <path>` returns zero. Three docs
became untracked orphans that way on 2026-08-29.

This script is the destination the skip was missing. Three modes, chosen for
you, and every one of them ends with the file referenced by some ref:

  main   — the canonical root IS the current worktree. Commit normally.
  direct — linked worktree, but the canonical tree is clean (ignoring the very
           paths we are about to commit) and sits on its default branch, so a
           commit there surprises nobody. Commit there.
  ref    — linked worktree and the canonical tree is dirty or off-default: the
           case that actually bites. Build the commit with a throwaway index and
           point `refs/handoffs/<branch-slug>` at it. No worktree is touched, no
           HEAD moves, nothing is staged in anyone's tree, and the file becomes
           reachable. Then push it to `origin` as `handoff/<branch-slug>` so the
           durability is cross-machine rather than one laptop's object store.

`ref` mode CHAINS: the new commit's parent is the previous `refs/handoffs/<slug>`
when one exists, and the new tree is read from that commit and overlaid. Without
the chain, the second closeout from a branch would move the ref off the first
commit and re-orphan the doc it just rescued — the exact property this script
exists to hold, regressing on the second run. Chaining also keeps the push a
fast-forward and leaves every past handoff present at the ref tip.

No third-party deps (stdlib only), mirroring the rest of the handoff skill.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from handoff_paths import branch_slug, canonical_root  # noqa: E402

LOCAL_REF_PREFIX = "refs/handoffs/"
REMOTE_BRANCH_PREFIX = "handoff/"
_CAS_ATTEMPTS = 3


class HandoffCommitError(RuntimeError):
    """A failure the caller must see rather than a condition we can absorb."""


def _git(
    args: list[str],
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    r = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, env=env
    )
    if check and r.returncode != 0:
        raise HandoffCommitError(
            f"git {' '.join(args)} (in {cwd}) failed rc={r.returncode}: "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    return r


def _out(args: list[str], cwd: Path, check: bool = True) -> str:
    return _git(args, cwd, check=check).stdout.strip()


# --------------------------------------------------------------------------
# repo state
# --------------------------------------------------------------------------


def status_entries(root: Path) -> list[tuple[str, str]]:
    """`(XY, path)` for every dirty/untracked entry in `root`.

    Two non-default flags, both load-bearing for `is_clean_ignoring`:

    `-z` because handoff filenames are generated from branch names, so a branch
    with a space or a quote makes the default porcelain output quote the path,
    and a quoted path never equals the repo-relative string we compare against.

    `--untracked-files=all` because the default collapses an untracked directory
    to a single `docs/handoffs/` entry. On the very first handoff in a repo that
    directory IS new, so the entry never matches the file path we are committing
    and every run reads as "some other file is dirty" — routing a safe `direct`
    commit into `ref` mode. Both failures degrade quietly rather than breaking,
    which is why they need a test rather than a code read (this one was found by
    `test_the_handoff_paths_themselves_never_count_as_dirt`).
    """
    raw = _git(
        ["status", "--porcelain", "-z", "--untracked-files=all"], root
    ).stdout
    fields = raw.split("\0")
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        f = fields[i]
        i += 1
        if not f:
            continue
        xy, _, path = f.partition(" ")
        # Rename/copy records spend a second NUL-separated field on the source
        # path. Consume it, or it parses as a bogus entry of its own.
        if xy and xy[0] in ("R", "C"):
            i += 1
        entries.append((xy, path))
    return entries


def is_clean_ignoring(root: Path, rel_paths: list[str]) -> bool:
    """Is `root` clean apart from the paths this run is about to commit?

    A bare `git status --porcelain` is always non-empty here: WRITE has already
    written the handoff doc into this tree, so the doc itself (and the appended
    learnings file) are exactly the dirt we are looking at. Ignoring anything
    else would sweep a foreign session's work into a handoff commit.
    """
    ignore = set(rel_paths)
    return all(path in ignore for _, path in status_entries(root))


def default_branch(root: Path) -> str | None:
    """The repo's default branch, or None when it cannot be established.

    `origin/HEAD` is the honest answer but is frequently unset in a local clone
    (it is only written at clone time or by an explicit `set-head`), so falling
    back to a `main`/`master` probe is the difference between this check working
    and it always answering None — which would strand every repo in `ref` mode.
    """
    head = _out(
        ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root, check=False
    )
    if head.startswith("origin/"):
        return head[len("origin/") :]
    for name in ("main", "master"):
        if _git(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{name}"], root, check=False
        ).returncode == 0:
            return name
    return None


def current_branch(root: Path) -> str | None:
    b = _out(["rev-parse", "--abbrev-ref", "HEAD"], root, check=False)
    return None if (not b or b == "HEAD") else b


# --------------------------------------------------------------------------
# path handling
# --------------------------------------------------------------------------


def to_repo_relative(root: Path, paths: list[str]) -> list[str]:
    """Repo-relative paths, refusing anything outside the canonical root.

    A path outside `root` cannot be committed by any of the three modes, and the
    failure would otherwise surface as an opaque git pathspec error at the end
    of a closeout rather than here.
    """
    rel: list[str] = []
    root_r = root.resolve()
    for p in paths:
        pr = Path(p).expanduser().resolve()
        try:
            rel.append(str(pr.relative_to(root_r)))
        except ValueError:
            raise HandoffCommitError(
                f"path is outside the canonical root: {p} (root: {root_r})"
            ) from None
    return rel


def existing(root: Path, rel_paths: list[str]) -> list[str]:
    """Drop paths that do not exist — `--skip-learnings` leaves nothing to add."""
    return [r for r in rel_paths if (root / r).exists()]


# --------------------------------------------------------------------------
# modes
# --------------------------------------------------------------------------


def choose_mode(root: Path, cwd: Path, rel_paths: list[str]) -> tuple[str, str]:
    """`(mode, why)` — the routing decision, as a pure read of repo state."""
    top = _out(["rev-parse", "--show-toplevel"], cwd, check=False)
    if top and Path(top).resolve() == root.resolve():
        return "main", "canonical root is the current worktree"
    db = default_branch(root)
    cb = current_branch(root)
    if db is None:
        return "ref", "canonical tree's default branch could not be established"
    if cb != db:
        return "ref", f"canonical tree is on {cb!r}, not the default branch {db!r}"
    if not is_clean_ignoring(root, rel_paths):
        return "ref", "canonical tree has unrelated uncommitted changes"
    return "direct", f"canonical tree is clean and on {db!r}"


def commit_in_tree(root: Path, rel_paths: list[str], message: str) -> str | None:
    """Stage + commit `rel_paths` in `root`'s working tree. Returns the SHA.

    `commit --only` rather than a plain `commit`: another session may have staged
    something in this shared tree between our cleanliness check and this call,
    and a plain commit would sweep it into a handoff commit. `--only` restricts
    the commit to the named paths and leaves the rest of the index alone, so the
    race degrades into "we committed exactly what we meant to".
    """
    _git(["add", "--", *rel_paths], root)
    if not _out(["diff", "--cached", "--name-only", "--", *rel_paths], root):
        return None
    _git(["commit", "--only", "-m", message, "--", *rel_paths], root)
    return _out(["rev-parse", "HEAD"], root)


def commit_to_ref(
    root: Path, rel_paths: list[str], message: str, slug: str
) -> tuple[str | None, str]:
    """Commit `rel_paths` onto `refs/handoffs/<slug>` without touching any tree.

    Returns `(sha_or_None, ref)`. None means the ref tip already carries exactly
    this content, so there was nothing to record.
    """
    ref = f"{LOCAL_REF_PREFIX}{slug}"
    last_err = ""
    for _ in range(_CAS_ATTEMPTS):
        old = _out(["rev-parse", "--verify", "--quiet", ref], root, check=False)
        base = old or _out(["rev-parse", "HEAD"], root)
        with tempfile.TemporaryDirectory() as td:
            env = dict(os.environ)
            env["GIT_INDEX_FILE"] = str(Path(td) / "index")
            _git(["read-tree", base], root, env=env)
            _git(["add", "--", *rel_paths], root, env=env)
            tree = _git(["write-tree"], root, env=env).stdout.strip()
        # Identical tree = this closeout adds nothing the ref does not already
        # carry. Committing anyway would chain an empty commit onto the ref
        # every time a WRITE is re-run, which is noise, not a record.
        if tree == _out(["rev-parse", f"{base}^{{tree}}"], root, check=False):
            return None, ref
        parents = ["-p", base]
        sha = _git(["commit-tree", tree, *parents, "-m", message], root).stdout.strip()
        # Compare-and-swap: two sessions on the same branch can close out at
        # once (the skill already expects that — hence the `-2` filename
        # discriminator), and a bare update-ref would let the loser silently
        # discard the winner's commit.
        r = _git(["update-ref", ref, sha, old or ""], root, check=False)
        if r.returncode == 0:
            return sha, ref
        last_err = r.stderr.strip()
    raise HandoffCommitError(f"could not update {ref} after {_CAS_ATTEMPTS} tries: {last_err}")


def push_ref(root: Path, ref: str, slug: str) -> tuple[bool, str]:
    """Push the handoff ref to origin as a normal branch. Best-effort.

    Pushed to `refs/heads/handoff/<slug>` and not to a matching custom namespace
    because a custom namespace is invisible to default fetch refspecs and to the
    forge UI — which is precisely the cross-machine discoverability the push is
    being done to buy.

    Failure is reported, never fatal: the commit already exists locally, so the
    "no unreferenced file" property holds with or without the remote.
    """
    if not _out(["remote"], root, check=False):
        return False, "no remote configured"
    dest = f"refs/heads/{REMOTE_BRANCH_PREFIX}{slug}"
    r = _git(["push", "origin", f"{ref}:{dest}"], root, check=False)
    if r.returncode == 0:
        return True, dest
    return False, (r.stderr.strip() or r.stdout.strip())


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


def run(
    paths: list[str],
    message: str,
    repo: str | None = None,
    push: bool = True,
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    cwd = Path(repo).expanduser() if repo else Path.cwd()
    root = canonical_root(cwd)
    rel = existing(root, to_repo_relative(root, paths))
    report: list[str] = [f"canonical-root: {root}"]
    if not rel:
        report.append("result: NOTHING-TO-COMMIT (none of the given paths exist)")
        return 0, report

    mode, why = choose_mode(root, cwd, rel)
    report.append(f"mode: {mode} ({why})")
    report.append("paths: " + ", ".join(rel))
    if dry_run:
        report.append("result: DRY-RUN (nothing written)")
        return 0, report

    if mode in ("main", "direct"):
        # Re-read the state we routed on. `direct` commits into a tree shared
        # with other live sessions, and the window between choose_mode and here
        # is enough for one of them to start work; falling through to `ref`
        # keeps the property without touching their tree.
        if mode == "direct" and not is_clean_ignoring(root, rel):
            mode = "ref"
            report.append("mode: ref (canonical tree became dirty; fell through)")
    if mode in ("main", "direct"):
        sha = commit_in_tree(root, rel, message)
        if sha is None:
            report.append("result: NOTHING-TO-COMMIT (paths already match HEAD)")
        else:
            report.append(f"result: COMMITTED {sha[:12]} on {current_branch(root)}")
            report.append("push: not attempted (SKILL.md §Sync/§Push owns this mode)")
        return 0, report

    slug = branch_slug(cwd)
    sha, ref = commit_to_ref(root, rel, message, slug)
    if sha is None:
        report.append(f"result: NOTHING-TO-COMMIT ({ref} already carries this content)")
        return 0, report
    report.append(f"result: COMMITTED {sha[:12]} -> {ref} (no worktree touched)")
    if push:
        ok, detail = push_ref(root, ref, slug)
        report.append(
            f"push: OK -> origin {detail}" if ok else f"push: FAILED ({detail}) "
            "— the commit is local; the file is still referenced"
        )
    else:
        report.append("push: skipped (--no-push)")
    # Deliberately cherry-pick and never merge: the ref's first commit is
    # parented on whatever the canonical tree's HEAD happened to be, which can
    # be an arbitrary stale feature tip. Merging would drag that whole history
    # onto the default branch.
    report.append(f"to land on the default branch later: git cherry-pick {sha[:12]}")
    return 0, report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Commit handoff artifacts so no WRITE ends with an unreferenced file"
    )
    ap.add_argument("paths", nargs="+", metavar="PATH", help="absolute paths §Save wrote")
    ap.add_argument("-m", "--message", required=True, help="commit message")
    ap.add_argument("--repo", default=None, help="resolve from PATH instead of the cwd")
    ap.add_argument("--no-push", action="store_true", help="do not push the handoff ref")
    ap.add_argument("--dry-run", action="store_true", help="print the routing decision only")
    args = ap.parse_args(argv)
    try:
        rc, report = run(
            args.paths,
            args.message,
            repo=args.repo,
            push=not args.no_push,
            dry_run=args.dry_run,
        )
    except HandoffCommitError as e:
        print(f"handoff_commit: {e}", file=sys.stderr)
        return 2
    print("\n".join(report))
    return rc


if __name__ == "__main__":
    sys.exit(main())
