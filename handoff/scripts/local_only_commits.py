#!/usr/bin/env python3
"""local_only_commits.py — is each local branch's work already on the default branch?

Skill-candidates rows 2495 (an unpushed-work audit before resetting a diverged clone) and
2478 (prove a squash-merged branch is on main before `branch -D`), folded into one tool
because they ask one question.

The incident that upgraded the row: HemaSuite carried "26 unpushed commits" through three
handoffs when all 26 were already on main. Two misreads stacked. The branch was ahead of
its OWN remote, which says nothing about main. And the local `origin/main` was stale, so
even the right comparison would have said "not there". So the base is the DEFAULT branch,
never `@{u}`, and the default run fetches first.

Every local branch, plus every linked worktree's HEAD (detached included — h-mad lanes park
there), is classified by the strongest evidence available, cheapest first:

    MERGED   the tip is an ancestor of the base (`merge-base --is-ancestor`)
    ON_BASE  not an ancestor, but every commit is there anyway:
               via=patch  `git cherry` finds each commit's patch on the base (rebase, pick)
               via=tree   every path the branch changed is byte-identical on the base
                          (a squash merge, which `git cherry` cannot see)
    PARTIAL  some commits' patches are on the base, some are not
    UNIQUE   none of it is on the base

PARTIAL and UNIQUE rows list each commit that still needs a home, annotated
`(subject on base)` when a base commit since the fork carries the same subject. That is a
hint to go and look, never evidence: it upgrades no verdict.

Worktrees are read by sha through the shared object store. Nothing is read from another
worktree's files, and nothing is ever written: this tool reports, the user deletes.

Token line, exit 0 on any real verdict:

    LOCAL_ONLY: ALL_ON_BASE refs=4 merged=3 on_base=1 partial=0 unique=0 base=origin/main fetched=yes
    LOCAL_ONLY: HAS_UNIQUE  refs=4 merged=2 on_base=0 partial=1 unique=1 base=origin/main fetched=no
    LOCAL_ONLY: UNREADABLE  reason=<why>                                                  exit 2

UNREADABLE covers a base that does not resolve, a git error, and a FAILED fetch. A failed
fetch leaves exactly the stale base the incident came from, so it refuses rather than
answering against it; `--no-fetch` accepts the base as it stands and says so in the token.

Stdlib only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TOKEN = "LOCAL_ONLY"


class Unreadable(Exception):
    pass


def _git(repo: Path, *args: str) -> str:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              text=True, stdin=subprocess.DEVNULL)
    except OSError as exc:
        raise Unreadable(f"git_unrunnable ({exc})") from exc
    if proc.returncode != 0:
        raise Unreadable(f"git_failed: git {' '.join(args[:2])}: {proc.stderr.strip()[:200]}")
    return proc.stdout


def _ok(repo: Path, *args: str) -> bool:
    """A git predicate: rc 0 is yes, rc 1 is no, anything else is a failure to answer."""
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)
    if proc.returncode not in (0, 1):
        raise Unreadable(f"git_failed: git {' '.join(args[:2])}: {proc.stderr.strip()[:200]}")
    return proc.returncode == 0


def resolve_base(repo: Path, base: str | None) -> str:
    if base is None:
        proc = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "--quiet", "--short",
                               "refs/remotes/origin/HEAD"], capture_output=True, text=True)
        base = proc.stdout.strip() if proc.returncode == 0 else "origin/main"
    if not _ok(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"):
        raise Unreadable(f"base_unresolved: {base}")
    return base


def _refs(repo: Path) -> list[tuple[str, str]]:
    """(name, sha) for every local branch and every detached linked-worktree HEAD."""
    refs = []
    for line in _git(repo, "for-each-ref", "refs/heads",
                     "--format=%(refname:short) %(objectname)").splitlines():
        name, sha = line.rsplit(" ", 1)
        refs.append((name, sha))
    path = head = None
    for line in _git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if line.startswith("worktree "):
            path, head = line[len("worktree "):], None
        elif line.startswith("HEAD "):
            head = line[len("HEAD "):]
        elif line == "detached" and head:
            refs.append((f"detached@{path}", head))
    return refs


def _tree(repo: Path, rev: str) -> dict[str, str]:
    """path -> blob id for a whole tree, in ONE call. Never a multi-path pathspec: this
    machine's wrapped git has joined multi-path argv into one pathspec at rc 0, which here
    would compare nothing and read as ON_BASE."""
    out = {}
    for entry in _git(repo, "ls-tree", "-r", "-z", rev).split("\0"):
        if entry:
            meta, path = entry.split("\t", 1)
            out[path] = meta.split()[2]
    return out


def classify(repo: Path, base: str, sha: str, base_tree: dict[str, str]) -> dict:
    if _ok(repo, "merge-base", "--is-ancestor", sha, base):
        return {"verdict": "MERGED", "via": "ancestor", "commits": 0, "unique": []}
    fork = _git(repo, "merge-base", sha, base).strip()
    marks = [l.split(" ", 1) for l in _git(repo, "cherry", base, sha).splitlines() if l]
    unique = [c for mark, c in marks if mark == "+"]
    result = {"commits": len(marks)}
    if not unique:
        return {**result, "verdict": "ON_BASE", "via": "patch", "unique": []}
    changed = [p for p in _git(repo, "diff", "--name-only", "-z", fork, sha).split("\0") if p]
    tip_tree = _tree(repo, sha)
    if changed and all(tip_tree.get(p) == base_tree.get(p) for p in changed):
        return {**result, "verdict": "ON_BASE", "via": "tree", "unique": []}
    base_subjects = set(_git(repo, "log", "--format=%s", f"{fork}..{base}").splitlines())
    rows = []
    for c in unique:
        subject = _git(repo, "log", "-1", "--format=%s", c).strip()
        rows.append((c, subject, subject in base_subjects))
    verdict = "PARTIAL" if len(unique) < len(marks) else "UNIQUE"
    return {**result, "verdict": verdict, "via": "", "unique": rows}


def audit(repo: Path, base: str | None, fetch: bool) -> tuple[str, list[str]]:
    if not _ok(repo, "rev-parse", "--is-inside-work-tree"):
        raise Unreadable(f"not_a_work_tree: {repo}")
    fetched = "no"
    if fetch:
        proc = subprocess.run(["git", "-C", str(repo), "fetch", "--quiet", "origin"],
                              capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if proc.returncode != 0:
            raise Unreadable("fetch_failed: the local base may be stale, which is the defect "
                             "this tool exists for; rerun with --no-fetch to accept it as is "
                             f"({proc.stderr.strip()[:160]})")
        fetched = "yes"
    base = resolve_base(repo, base)
    base_tree = _tree(repo, base)
    counts = {"MERGED": 0, "ON_BASE": 0, "PARTIAL": 0, "UNIQUE": 0}
    lines = []
    for name, sha in _refs(repo):
        r = classify(repo, base, sha, base_tree)
        counts[r["verdict"]] += 1
        via = f" via={r['via']}" if r["via"] else ""
        lines.append(f"  {r['verdict']} {name} {sha[:9]} commits={r['commits']}{via}")
        for c, subject, seen in r["unique"]:
            lines.append(f"    unique {c[:9]} {subject}" + ("  (subject on base)" if seen else ""))
    head = "ALL_ON_BASE" if counts["PARTIAL"] + counts["UNIQUE"] == 0 else "HAS_UNIQUE"
    token = (f"{TOKEN}: {head} refs={sum(counts.values())} merged={counts['MERGED']} "
             f"on_base={counts['ON_BASE']} partial={counts['PARTIAL']} "
             f"unique={counts['UNIQUE']} base={base} fetched={fetched}")
    return token, lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    ap.add_argument("--repo", default=".", help="any work tree of the repository")
    ap.add_argument("--base", help="base ref (default: origin/HEAD, else origin/main)")
    ap.add_argument("--no-fetch", action="store_true",
                    help="do not fetch origin first; the token then says fetched=no")
    args = ap.parse_args(argv)
    try:
        token, lines = audit(Path(args.repo), args.base, not args.no_fetch)
    except Unreadable as exc:
        print(f"{TOKEN}: UNREADABLE reason={exc}")
        return 2
    print(token)
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
