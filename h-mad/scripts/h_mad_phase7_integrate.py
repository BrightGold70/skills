#!/usr/bin/env python3
"""Phase 7f — integrate the feature branch, or say why it was not integrated.

**The hole this fills.** Phase 5c creates `feature/NNN-<slug>` (SKILL.md), and
Phase 7 is telemetry → report → archive → commit → push. `references/phase-table.md`
states the exit criterion as "Push to origin/main succeeds". Nothing between 5c and
that line merges the branch: a repo-wide grep for merge language returns 5f's
baseline-sha warning and the orchestration-mode `--no-ff` note, neither of which is
a Phase-7 step. So the stated commands cannot reach the stated exit — on a feature
branch `git push origin main` pushes nothing of the feature — and the merge has
been done by hand, carried between sessions as a handoff Next Step, every time.

**What it does NOT do.** It never pushes (that is 7e), never deletes a branch or a
worktree, and never merges without `--apply`. The default is a PLAN: every gate is
evaluated and the exact commands are printed. This is deliberate. A merge is the
one irreversible-ish step in the phase, and h-mad's own resolve discipline says a
repair that the next reader cannot undo is not mechanical.

**Verdicts** (read the token, never `$?` — every verdict exits 0):

    INTEGRATE: PLANNED route=merge base=<b> branch=<f> ahead=<n> identity=<y/n>
    INTEGRATE: MERGED base=<b> branch=<f> commit=<sha> identity=<y/n>
    INTEGRATE: KEPT route=<pr|keep> base=<b> branch=<f>
    INTEGRATE: BLOCKED reason=<r>
    INTEGRATE: UNREADABLE reason=<r>                                    exit 2

`BLOCKED` is a verdict about the world (a dirty tree, a detached HEAD, a base that
is not an ancestor). `UNREADABLE` is a cannot-judge — git did not answer — and it
carries no counts, on the same rule as every other gate here: "I could not check"
and "I checked and it is fine" must never take the same branch.

**The identity check is the point of the verification half.** Superpowers'
finishing-a-development-branch reruns the suite on the merged result. When the base
is strictly behind, `git merge --no-ff` produces a tree byte-identical to the
feature tip, so comparing `<base>^{tree}` to `<branch>^{tree}` PROVES the green run
you already have covers the merge — a proof rather than a second measurement.
Measured 2026-09-07 on doc-block-exec: both trees `381aaba2`, standing in for an
eight-minute suite run. `identity=n` means the base has moved since the fork
point, so the merged tree is new and the suite genuinely must be re-run on it
before 7e. After an `--apply` the claim is re-checked against the real trees
(`merged_tree_matches`) rather than trusted from the prediction.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TOKEN = "INTEGRATE:"
ROUTES = ("merge", "pr", "keep")
# The exclusion the closure/implementation commits use. BOTH halves are anchored at
# the repository root: a CWD-relative pair stages only the subtree you happen to be
# standing in, and excludes only that subtree's markers (measured from a
# subdirectory: 1 of 3 changed files staged, and a root marker committed).
MARKER_EXCLUDE = ":(top,exclude)*.done"
ROOT_PATHSPEC = ":/"
# ...and the second step, which stages a TRACKED `.done` file's real modification
# that the exclusion alone would suppress forever.
TRACKED_SWEEP = "git add -u -- ':/'"


class GitError(RuntimeError):
    """git did not answer. A cannot-judge, never a verdict about the tree.

    `kind` classifies it, because a reason that is always the class name is not a
    diagnostic: every UNREADABLE read `reason=giterror` while the real text sat
    only on stderr.
    """

    def __init__(self, message: str, kind: str = "git_failed") -> None:
        super().__init__(message)
        self.kind = kind


def git(repo: Path, *args: str) -> str:
    try:
        run = subprocess.run(["git", "-C", str(repo), *args],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitError(f"{exc.__class__.__name__}: {' '.join(args)}",
                       "git_unavailable") from exc
    if run.returncode != 0:
        stderr = run.stderr.strip()
        kind = "not_a_repo" if "not a git repository" in stderr else f"{args[0]}_failed"
        raise GitError(f"git {' '.join(args)} exited {run.returncode}: {stderr[:200]}",
                       kind)
    return run.stdout.strip()


def default_base(repo: Path) -> str | None:
    """The repo's own default branch, never a hardcoded `main`.

    `origin/HEAD` when the remote sets it, else the first of main/master that
    resolves. h-mad hardcoded `main` while `handover_landed.py` in the same
    checkout already resolved this properly — two rules for one fact.
    """
    try:
        ref = git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
        if ref.startswith("origin/"):
            return ref[len("origin/"):]
    except GitError:
        pass
    for candidate in ("main", "master"):
        if local_branch_exists(repo, candidate):
            return candidate
    # git ANSWERED — there is no origin/HEAD and neither conventional name exists
    # (a repo whose trunk is `trunk`, say). That is a fact about the world, so the
    # caller turns it into a BLOCKER; raising here would report it as a
    # cannot-judge, which is the one confusion this whole family of gates exists
    # to prevent.
    return None


def local_branch_exists(repo: Path, name: str) -> bool:
    """True only for `refs/heads/<name>`.

    `rev-parse --verify <x>^{commit}` accepts a TAG, a remote-tracking ref and a
    raw sha, and `git checkout` on any of those DETACHES: the merge then lands on
    no branch, the base never moves, and the merge commit is unreferenced while
    the verdict says MERGED at exit 0. Measured by review probe with `--base v1`
    and `--base origin/main`.
    """
    try:
        git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}")
    except GitError:
        return False
    return True


def worktree_holding(repo: Path, branch: str) -> str | None:
    """The worktree path that has `branch` checked out, when it is not this one.

    Under Orca's sibling-worktree layout the base is checked out in the primary
    worktree, and `git checkout <base>` there dies `fatal: '<base>' is already
    used by worktree at ...`. That is a fact this gate can state up front instead
    of a merge failure discovered after the plan said identity=y.
    """
    try:
        listing = git(repo, "worktree", "list", "--porcelain")
    except GitError:
        return None
    here = repo.resolve()
    path = None
    for line in listing.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch ") and path:
            name = line[len("branch "):].replace("refs/heads/", "")
            if name == branch and Path(path).resolve() != here:
                return path
            path = None
        elif not line.strip():
            path = None
    return None


def untracked_collisions(repo: Path, base: str) -> list[str]:
    """Untracked files that `base` tracks — `git checkout <base>` aborts on these.

    Only these, never every untracked file: 88 untracked audit markers are the
    NORMAL state of this repository, and blocking on them would block every
    closure.
    """
    untracked = [line[3:] for line in git(repo, "status", "--porcelain").splitlines()
                 if line.startswith("?? ")]
    if not untracked:
        return []
    try:
        tracked = set(git(repo, "ls-tree", "-r", "--name-only", base).splitlines())
    except GitError:
        return []
    return sorted(path for path in untracked if path in tracked)


def environment(repo: Path) -> dict:
    """Branch, worktree shape and tree cleanliness.

    `git_dir != git_common_dir` means a LINKED worktree, which h-mad runs under
    constantly (Orca's sibling-dir layout) and which Phase 7 assumed away.
    """
    git_dir = Path(git(repo, "rev-parse", "--absolute-git-dir")).resolve()
    common = Path(git(repo, "rev-parse", "--path-format=absolute",
                      "--git-common-dir")).resolve()
    head = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    # Tracked changes only: the audit `.done` markers are untracked by design and
    # are counted, not committed (see `--marker-safe-add`).
    dirty = [line for line in git(repo, "status", "--porcelain").splitlines()
             if not line.startswith("??")]
    return {
        "branch": head,
        "detached": head == "HEAD",
        "linked_worktree": git_dir != common,
        "git_dir": str(git_dir),
        "git_common_dir": str(common),
        "dirty": dirty,
    }


def ahead_behind(repo: Path, base: str, branch: str) -> tuple[int, int]:
    """`(behind, ahead)` of `branch` relative to `base`."""
    out = git(repo, "rev-list", "--left-right", "--count", f"{base}...{branch}")
    left, _, right = out.partition("\t")
    return int(left.strip() or 0), int(right.strip() or 0)


def merged_tree_matches(repo: Path, base: str, branch: str) -> bool:
    """After a merge: is the base's tree byte-identical to the branch's?"""
    return git(repo, "rev-parse", f"{base}^{{tree}}") == git(
        repo, "rev-parse", f"{branch}^{{tree}}")


def removable_worktrees(repo: Path, base: str | None, branch: str) -> list[str]:
    """Other worktrees whose branch is already merged into `base`.

    Merged-ness is CHECKED, not assumed: an earlier draft's docstring claimed it
    and the code listed every worktree but the current one, so in a linked-worktree
    layout it named the PRIMARY worktree holding the base and advised deleting the
    base branch. Reported, never removed — the lane may have a live owner, and
    #111 sat across five handoffs precisely because nothing in the protocol
    named it.
    """
    if base is None:
        return []
    try:
        listing = git(repo, "worktree", "list", "--porcelain")
        # `git branch --merged` marks the current branch with `*` AND a branch
        # checked out in another worktree with `+`. Stripping only `*` silently
        # drops every worktree branch — which is the entire population this
        # function exists to report.
        merged = {line.strip().lstrip("*+ ").replace("refs/heads/", "")
                  for line in git(repo, "branch", "--merged", base).splitlines()}
    except GitError:
        return []
    here = repo.resolve()
    out: list[str] = []
    path = None
    prunable = False
    for line in listing.splitlines():
        if line.startswith("worktree "):
            path, prunable = line[len("worktree "):], False
        elif line.startswith("prunable"):
            # The directory is gone; `git worktree remove` fails on it and the
            # remedy is `git worktree prune`. Naming the wrong command is worse
            # than naming none.
            prunable = True
        elif line.startswith("branch ") and path:
            name = line[len("branch "):].replace("refs/heads/", "")
            if (name not in (branch, base) and name in merged
                    and not prunable and Path(path).resolve() != here):
                out.append(f"{path} [{name}]")
            path, prunable = None, False
        elif not line.strip():
            path, prunable = None, False
    return out


def plan(repo: Path, base: str, branch: str, route: str) -> dict:
    """Evaluate every gate. Returns a report; performs nothing."""
    env = environment(repo)
    blockers: list[str] = []
    # `keep` performs NOTHING — no checkout, no merge, no push — so no fact about
    # the tree can stop it, and reporting one would make the honest no-op read as
    # a failure. `pr` keeps these two, because a pull request implies pushing a
    # branch that a detached HEAD does not have and a dirty tree misrepresents.
    if route != "keep":
        if env["detached"]:
            blockers.append("detached_head")
        if env["dirty"]:
            blockers.append(f"dirty_tree:{len(env['dirty'])}_tracked_changes")
    behind = ahead = 0
    identity = False
    # The base-relative gates apply to the merge route ONLY. `keep` integrates
    # nothing, so "the base is the branch you are on" is not a blocker there — it
    # is the ordinary state of a feature already closed out on its own trunk, and
    # reporting it as a blocker would make the honest route look like a failure.
    if route != "merge" and base is not None and local_branch_exists(repo, base) \
            and base != branch and local_branch_exists(repo, branch):
        # Measured for `pr` too: it used to print "0 commit(s) ahead" for every
        # branch, because the counts were computed on the merge route alone.
        behind, ahead = ahead_behind(repo, base, branch)
        identity = behind == 0

    if route == "merge" and not blockers:
        if base is None:
            # No origin/HEAD and no main/master. git answered; this is a fact.
            blockers.append("no_default_base")
        elif not local_branch_exists(repo, base):
            # Split deliberately: "there is no such ref" and "that ref is not a
            # local branch" have different remedies, and a tag or a
            # remote-tracking ref would DETACH rather than fail.
            try:
                git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
                blockers.append(f"base_not_a_local_branch:{base}")
            except GitError:
                blockers.append(f"unknown_base:{base}")
        elif not local_branch_exists(repo, branch):
            blockers.append(f"unknown_branch:{branch}")
        elif base == branch:
            blockers.append(f"base_is_the_feature_branch:{base}")
        else:
            held = worktree_holding(repo, base)
            if held:
                blockers.append(f"base_checked_out_elsewhere:{held}")
            collisions = untracked_collisions(repo, base)
            if collisions:
                blockers.append(
                    f"untracked_collision:{len(collisions)}:{collisions[0]}")
            behind, ahead = ahead_behind(repo, base, branch)
            if ahead == 0:
                blockers.append(
                    f"nothing_to_integrate:{branch}_is_not_ahead_of_{base}")
            identity = behind == 0
    return {"env": env, "base": base, "branch": branch, "route": route,
            "behind": behind, "ahead": ahead, "identity": identity,
            "blockers": blockers, "worktrees": removable_worktrees(repo, base, branch)}


def merge(repo: Path, base: str, branch: str, message: str) -> str:
    """`--no-ff` merge of `branch` into `base`. Returns the merge sha.

    Re-checks the base here as well as in `plan()`: `git checkout` on a tag or a
    remote-tracking ref detaches, and a detached merge reports MERGED while the
    base never moves.
    """
    if not local_branch_exists(repo, base):
        raise GitError(f"{base!r} is not a local branch; refusing to checkout")
    git(repo, "checkout", base)
    git(repo, "merge", "--no-ff", branch, "-m", message)
    return git(repo, "rev-parse", "--short", "HEAD")


def _emit(line: str) -> None:
    print(f"{TOKEN} {line}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--feature", required=True)
    ap.add_argument("--base", help="target branch; default: the repo's own default")
    ap.add_argument("--branch", help="feature branch; default: the checked-out one")
    ap.add_argument("--route", choices=ROUTES, default="merge",
                    help="merge (default) integrates; pr and keep report and stop. "
                         "A route is RECORDED, never asked: Phase 7 is autonomous, "
                         "so a blocking menu would break its contract.")
    ap.add_argument("--apply", action="store_true",
                    help="perform the merge. Without it this plans and verifies only.")
    ap.add_argument("--message", help="merge commit subject")
    args = ap.parse_args(argv)

    repo = args.repo_root
    try:
        base = args.base or default_base(repo)      # None when none resolves
        branch = args.branch or environment(repo)["branch"]
        report = plan(repo, base, branch, args.route)
    except GitError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        _emit(f"UNREADABLE reason={exc.kind}")
        return 2

    for path in report["worktrees"]:
        print(f"  worktree {path} — not removed; remove it yourself when that lane "
              "is idle: git worktree remove <path> && git branch -d <branch>")

    if args.route == "keep" and not report["blockers"]:
        _emit(f"KEPT route=keep base={base or 'none'} branch={branch}")
        print(f"  route keep: {branch} is left exactly as it is. Nothing was "
              "merged, deleted or pushed.")
        return 0

    if report["blockers"]:
        _emit(f"BLOCKED reason={','.join(report['blockers'])}")
        for blocker in report["blockers"]:
            print(f"  BLOCKER {blocker}")
        return 0

    if args.route != "merge":
        _emit(f"KEPT route={args.route} base={base or 'none'} branch={branch}")
        print(f"  route {args.route}: the branch is left as it is, {report['ahead']} "
              f"commit(s) ahead of {base}. Nothing was merged, deleted or pushed.")
        return 0

    identity = "y" if report["identity"] else "n"
    if not args.apply:
        _emit(f"PLANNED route=merge base={base} branch={branch} "
              f"ahead={report['ahead']} identity={identity}")
        print(f"  git checkout {base} && git merge --no-ff {branch}")
        if report["identity"]:
            print(f"  identity=y — {base} is strictly behind, so the merged tree is "
                  f"byte-identical to {branch}'s tip and the suite run you already "
                  "have covers it. Verify with `git rev-parse "
                  f"{base}^{{tree}} {branch}^{{tree}}` after the merge.")
        else:
            print(f"  identity=n — {base} has moved ({report['behind']} commit(s) "
                  "ahead of the fork point), so the merged tree is NEW: re-run the "
                  "suite on it before 7e.")
        return 0

    message = args.message or f"merge: {branch} — {args.feature} closure"
    try:
        sha = merge(repo, base, branch, message)
        matched = merged_tree_matches(repo, base, branch)
    except GitError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        _emit(f"UNREADABLE reason=merge_failed:{exc.kind}")
        return 2
    _emit(f"MERGED base={base} branch={branch} commit={sha} "
          f"identity={'y' if matched else 'n'}")
    if not matched:
        print("  identity=n — the merged tree differs from the branch tip, so no "
              "existing run covers it. Re-run the suite before 7e.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
