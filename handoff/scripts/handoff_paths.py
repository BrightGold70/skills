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
import re
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

    The `p.name == ".git"` guard targets the linked-worktree case. Other layouts
    fall through *safely* to `--show-toplevel`/cwd rather than misresolving: a
    submodule (`--git-common-dir` = `.git/modules/<name>`) resolves to the
    submodule tree, and a bare repo to cwd. Those simply opt out of canonical
    cross-worktree sharing, which is fine — Orca worktrees are neither.
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
    Underscores are mapped to `-` so a branch slug can never contain `_`; the
    handoff filename then uses `__` as the branch|slug separator (see SEP), which
    is therefore unambiguous even when both the branch and the slug contain `-`.
    """
    base = Path(start) if start else Path.cwd()
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=base)
    if not branch or branch == "HEAD":
        return "nobranch"
    # allow only alnum, '-', '.'  (NOT '_', so '__' cannot appear in a branch slug)
    safe = "".join(c if (c.isalnum() or c in "-.") else "-" for c in branch)
    return safe.strip("-") or "nobranch"


# Separator between the branch slug and the free slug in a handoff filename:
#   YYYY-MM-DD-<branch-slug>__<slug>.md
# Distinct from '-' (legal in both branch and slug) so branch matching is exact.
SEP = "__"
_DATE_LEN = len("YYYY-MM-DD-")  # 11: chars before the branch slug begins


def find_latest(branch: str | None = None, start: Path | None = None) -> Path | None:
    """Newest handoff in the canonical store, optionally filtered to a branch.

    Files are `YYYY-MM-DD-<branch-slug>-<slug>.md`; the ISO date prefix sorts
    lexically, so the last match is the newest. A branch filter matches the
    `-<branch>-` segment so a resume prefers its own branch's handoff.
    """
    d = handoffs_dir(start)
    if not d.is_dir():
        return None
    files = [p for p in d.glob("*.md") if p.is_file()]
    if branch:
        # Exact branch match: the segment right after the ISO date must be
        # "<branch>__". Anchoring past the date + requiring the '__' separator
        # means branch `feat` never matches a `feat-ab__…` file (the failure a
        # bare `-{branch}-` substring caused). Old branch-less files (no `__`)
        # simply don't match a branch filter, which is correct.
        pfx = f"{branch}{SEP}"
        files = [p for p in files if p.name[_DATE_LEN:].startswith(pfx)]
    if not files:
        return None
    # Primary sort = ISO date prefix (lexical). Secondary = mtime, so a same-day
    # concurrency-guard discriminant (`…-2.md`, added on collision) still orders
    # as newer even though `-` sorts before `.` lexically.
    files.sort(key=lambda p: (p.name[:10], p.stat().st_mtime))
    return files[-1]


# The bolded field forms, anchored to line start. Briefs discuss handovers in
# prose constantly -- matching a bare mention would turn every retrospective into
# a pending queue.
_HANDOVER_FROM_RE = re.compile(r"^\*\*Handover-From:\*\*", re.MULTILINE)
_TAKEN_OVER_BY_RE = re.compile(r"^\*\*Taken-Over-By:\*\*", re.MULTILINE)


def pending_handovers(start: Path | None = None) -> tuple[list[Path], list[Path]]:
    """Briefs addressed to this repo that nobody has taken over yet.

    Returns `(pending, unreadable)`, both oldest-first by filename date. A brief
    is pending when it carries `**Handover-From:**` and does NOT carry
    `**Taken-Over-By:**`.

    This exists because READ Step 1's branch-scoped check (check 2) short-circuits
    the repo-wide check that knows about `**Handover-From:**`, so an inbound brief
    filed under the sender's branch slug is unreachable from any branch that has a
    handoff of its own -- the common case. The scan therefore runs IN ADDITION to
    check 2, never as a fallback to it.

    `**Taken-Over-By:**` is the discriminator because it is the only marker that
    lives in the store the locator reads. The `taken over:` worktree comment is
    worktree-scoped and the advisory claim lives in a gitignored, machine-local
    state file; neither travels with the doc.

    `unreadable` is returned rather than swallowed. A brief that cannot be decoded
    is the same value as no brief at all and leads to the opposite correct action,
    which is the exact asymmetry this whole defect is made of.
    """
    d = handoffs_dir(start)
    if not d.is_dir():
        return ([], [])
    pending: list[Path] = []
    unreadable: list[Path] = []
    for path in sorted(p for p in d.glob("*.md") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable.append(path)
            continue
        if _HANDOVER_FROM_RE.search(text) and not _TAKEN_OVER_BY_RE.search(text):
            pending.append(path)
    return (pending, unreadable)


_SUPERSEDES_RE = re.compile(r"^\*\*Supersedes:\*\*(.*)$", re.MULTILINE)


def _superseded_names(field: str) -> set[str]:
    """Filenames named by one `**Supersedes:**` field. Comma-separated, possibly
    backticked.

    A handoff absorbs more than one source -- the branch predecessor plus every
    taken-over brief whose items it carried -- so one name per field cannot retire
    them all, and the ones it cannot retire surface on every later WRITE forever.
    A queue that only grows is abandoned exactly as fast as one that silently
    empties, and the abandoned queue is where the next dropped handover hides.

    Only `.md` tokens count, which is what keeps the documented
    `none — first on this branch` sentinel from matching anything: it is prose,
    and prose split on commas must not accidentally retire a source.
    """
    names: set[str] = set()
    for token in field.split(","):
        name = token.strip().strip("`").strip()
        if name.endswith(".md"):
            names.add(name)
    return names


def carry_forward_sources(
    branch: str | None = None, start: Path | None = None
) -> tuple[list[Path], list[Path]]:
    """Docs a WRITE on this branch owes open items to. `(sources, unreadable)`.

    Two kinds, because a handover is filed under the SENDER's branch slug and so
    is invisible to a branch-scoped lookup -- the same construction as the READ
    defect `pending_handovers` exists for:

    1. This branch's newest handoff, the ordinary predecessor.
    2. Any brief this lane already stamped `**Taken-Over-By:**` that no handoff
       yet names in its `**Supersedes:**` field.

    Without (2) a taken-over backlog can still evaporate in one hop: the taker
    stamps the brief, restores the todos into the session-scoped task tool, and
    the session ends before it writes a handoff. The next session on the branch
    runs WRITE without READ, finds an empty task list and no branch predecessor,
    and writes a doc that owes nothing -- while the stamp has already removed the
    brief from `pending_handovers`, so nothing re-offers it either.
    """
    d = handoffs_dir(start)
    if not d.is_dir():
        return ([], [])
    sources: list[Path] = []
    unreadable: list[Path] = []
    latest = find_latest(branch, start)
    if latest is not None:
        sources.append(latest)

    superseded: set[str] = set()
    taken: list[Path] = []
    for path in sorted(p for p in d.glob("*.md") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable.append(path)
            continue
        for match in _SUPERSEDES_RE.finditer(text):
            superseded.update(_superseded_names(match.group(1)))
        if _TAKEN_OVER_BY_RE.search(text):
            taken.append(path)

    for path in taken:
        if path.name not in superseded and path not in sources:
            sources.append(path)
    return (sources, unreadable)


def _resolve_start(repo: str | None) -> Path | None:
    """Validate a `--repo` target, or None to resolve from the cwd as before.

    Both checks exist because every failure here is SILENT otherwise:
    `canonical_root` falls back to the path it was handed when git cannot answer,
    so a typo'd or non-repo target resolves to `<that path>/docs/handoffs` — a
    real-looking directory the writer would happily create and the receiver would
    never read. A handover that reports success while filing the brief somewhere
    nobody looks is worse than one that refuses.
    """
    if repo is None:
        return None
    path = Path(repo).expanduser()
    if not path.is_dir():
        raise SystemExit(f"handoff_paths: --repo {repo}: no such directory")
    if _git(["rev-parse", "--is-inside-work-tree"], cwd=path) != "true":
        raise SystemExit(f"handoff_paths: --repo {repo}: not inside a git work tree")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Canonical handoff/learnings paths")
    # Resolve against ANOTHER repo/worktree instead of the cwd. Every function
    # below already took `start`; this exposes it, which is what a handover needs
    # to write into the RECEIVER's store rather than the sender's.
    ap.add_argument(
        "--repo",
        default=None,
        metavar="PATH",
        help="resolve paths for the repo/worktree at PATH instead of the cwd",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dir")           # canonical docs/handoffs dir
    sub.add_parser("learnings")     # canonical docs/learnings.md
    sub.add_parser("branch-slug")   # fs-safe current branch
    sub.add_parser("root")          # canonical main-worktree root
    p_latest = sub.add_parser("latest")
    p_latest.add_argument("--branch", default=None)
    sub.add_parser("pending-handovers")  # inbound briefs nobody has taken over
    p_cfs = sub.add_parser("carry-forward-sources")  # docs a WRITE owes items to
    p_cfs.add_argument("--branch", default=None)
    args = ap.parse_args(argv)
    start = _resolve_start(args.repo)

    if args.cmd == "dir":
        print(handoffs_dir(start))
    elif args.cmd == "learnings":
        print(learnings_path(start))
    elif args.cmd == "branch-slug":
        print(branch_slug(start))
    elif args.cmd == "root":
        print(canonical_root(start))
    elif args.cmd == "latest":
        latest = find_latest(args.branch, start)
        if latest is None:
            return 1
        print(latest)
    elif args.cmd == "pending-handovers":
        pending, unreadable = pending_handovers(start)
        for path in pending:
            print(path)
        for path in unreadable:
            print(f"UNREADABLE:{path}", file=sys.stderr)
        # Exit 2 outranks "nothing found" on purpose: a brief that could not be
        # read might be the handover, so the caller must not read this run as an
        # empty queue. Whatever DID read is still printed -- refusing to answer at
        # all would hide the briefs that are provably pending.
        if unreadable:
            return 2
        if not pending:
            return 1
    elif args.cmd == "carry-forward-sources":
        sources, unreadable = carry_forward_sources(args.branch, start)
        for path in sources:
            print(path)
        for path in unreadable:
            print(f"UNREADABLE:{path}", file=sys.stderr)
        # Same fail-closed ordering as pending-handovers: a doc that could not be
        # read may be the one holding the open items, so "I could not check" must
        # not be reported as "there is nothing to carry".
        if unreadable:
            return 2
        if not sources:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
