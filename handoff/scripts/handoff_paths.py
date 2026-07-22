#!/usr/bin/env python3
"""handoff_paths.py — canonical, worktree-shared locations for handoff artifacts.

Under Orca, one git repo is checked out into several linked worktrees running in
parallel. `git rev-parse --show-toplevel` returns the *current worktree's* root,
so a per-worktree `docs/handoffs/` (and `docs/learnings.md`) fragments the record
across worktrees and loses it when a worktree is archived/removed.

The canonical root is the **main worktree** — the parent of the shared git dir
returned by `git rev-parse --git-common-dir` (which every linked worktree shares).
Anchoring handoffs + learnings there gives one store all worktrees read and write,
that survives worktree removal. Handoffs are then disambiguated *within* that store
by branch (see `branch_slug`), so concurrent sessions on different branches don't
collide and a resume can prefer its own branch's handoff.

No third-party deps (stdlib only), mirroring the rest of the handoff skill.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _git(args: list[str], cwd: Path | None = None) -> str | None:
    try:
        r = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
        )
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def canonical_root(start: Path | None = None) -> Path:
    """The main-worktree root shared by every linked worktree of this repo.

    `--git-common-dir` is the shared git dir (`<main>/.git` for a normal repo,
    the same value from any linked worktree). Its parent is the main worktree
    root. Falls back to `--show-toplevel` then cwd when that can't be resolved
    (e.g. not a git repo, or an unusual git-dir layout).
    """
    base = Path(start) if start else Path.cwd()
    common = _git(["rev-parse", "--git-common-dir"], cwd=base)
    if common:
        p = Path(common)
        if not p.is_absolute():
            p = (base / p).resolve()
        if p.name == ".git":
            return p.parent
    top = _git(["rev-parse", "--show-toplevel"], cwd=base)
    if top:
        return Path(top)
    return base


def handoffs_dir(start: Path | None = None) -> Path:
    return canonical_root(start) / "docs" / "handoffs"


def learnings_path(start: Path | None = None) -> Path:
    return canonical_root(start) / "docs" / "learnings.md"


def branch_slug(start: Path | None = None) -> str:
    """Filesystem-safe short branch name for the handoff filename.

    `feature/189-foo` → `feature-189-foo`. Detached HEAD / no branch → `nobranch`.
    """
    base = Path(start) if start else Path.cwd()
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=base)
    if not branch or branch == "HEAD":
        return "nobranch"
    safe = "".join(c if (c.isalnum() or c in "-_.") else "-" for c in branch)
    return safe.strip("-") or "nobranch"


def find_latest(branch: str | None = None, start: Path | None = None) -> Path | None:
    """Newest handoff in the canonical store, optionally filtered to a branch.

    Files are `YYYY-MM-DD-<branch-slug>-<slug>.md`; the ISO date prefix sorts
    lexically, so the last match is the newest. A branch filter matches the
    `-<branch>-` segment so a resume prefers its own branch's handoff.
    """
    d = handoffs_dir(start)
    if not d.is_dir():
        return None
    files = sorted(p for p in d.glob("*.md") if p.is_file())
    if branch:
        files = [p for p in files if f"-{branch}-" in p.name]
    return files[-1] if files else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Canonical handoff/learnings paths")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dir")           # canonical docs/handoffs dir
    sub.add_parser("learnings")     # canonical docs/learnings.md
    sub.add_parser("branch-slug")   # fs-safe current branch
    sub.add_parser("root")          # canonical main-worktree root
    p_latest = sub.add_parser("latest")
    p_latest.add_argument("--branch", default=None)
    args = ap.parse_args(argv)

    if args.cmd == "dir":
        print(handoffs_dir())
    elif args.cmd == "learnings":
        print(learnings_path())
    elif args.cmd == "branch-slug":
        print(branch_slug())
    elif args.cmd == "root":
        print(canonical_root())
    elif args.cmd == "latest":
        latest = find_latest(args.branch)
        if latest is None:
            return 1
        print(latest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
