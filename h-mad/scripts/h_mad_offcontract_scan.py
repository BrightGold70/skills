#!/usr/bin/env python3
"""Where did the report actually go? Find an audit artifact written off-contract.

`exec agy` is dispatched with a `--report-file` slot and a per-cycle sentinel pair,
and it can honour NEITHER while still doing the work: it writes a real report, at a
path of its own choosing. Two were observed, eleven days apart:

  .design.audit.v14.md   (2026-08-11, J30) — a workspace dotfile
  audit_report.md        (2026-08-22)      — in agy's own scratch directory

The first is a workspace **dotfile**, invisible to the `*audit.v14*` glob the
orchestrator searches -- which is exactly how one cycle concluded "no file was
written" and re-dispatched over completed work. The second landed in agy's own
scratch directory while the run narrated "the current workspace".

**The defect this addresses is unfindability, not absence.** `h_mad_extract_report.py`
exiting 2 is the correct failure -- silence must never score as a clean gate -- but the
remedy it sends you to (`clear` and re-dispatch) is wrong when the audit already ran:
you pay another full cycle to reproduce a drop, and on a large prompt that is expensive.
Look for the artifact first.

Three things this deliberately does NOT do:

  1. **It does not feed the gate.** It prints candidate paths for a human to read.
     A report recovered from an off-contract path has had NO schema enforcement
     applied to it, so transcribing it into the gate's schema is a manual step, and
     every premise in it must be falsified against the source before it is acted on.
     Teaching `h_mad_extract_report.py` to glob these paths would score an
     unvalidated file as a clean gate -- the opposite of the fix.
  2. **It does not assume the `audit.vN` stem.** The whole failure is that the agent
     chose the name. Any markdown-ish file in range is a candidate; dotfiles included
     (`.design.audit.v14.md` is why).
  3. **It does not decide.** `OFFCONTRACT: NONE` means nothing matched the search,
     not that the work was never done. It narrows a re-dispatch decision; it does not
     make one.

Usage:
  h_mad_offcontract_scan.py --cd <workspace> [--expected <report-file>]
      [--minutes N] [--since <epoch>] [--extra-dir <dir> ...]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# agy's own scratch directory -- where a run that narrates "the current workspace"
# has been observed to write instead. Overridable because it is an agy install
# detail, not a contract.
AGY_SCRATCH = Path(
    os.environ.get("HMAD_AGY_SCRATCH", "~/.gemini/antigravity-cli/scratch")
).expanduser()

# Suffixes a report plausibly carries. A dotfile is matched by suffix like any
# other name -- `.design.audit.v14.md` has suffix `.md`.
SUFFIXES = (".md", ".markdown", ".txt")

# Directories never worth walking into.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache"}

# Content that marks a file as report-SHAPED. Ranking only: a candidate that
# matches none of these is still reported, because the agent chose the format too.
MARKERS = ("-BEGIN", "-END", "## Summary", "GATE:", "ASSESSMENT:", "VERDICT:",
           "MUST-FIX", "Must-fix")


def _walk(root: Path, max_depth: int) -> list[Path]:
    """Files under *root* to max_depth, dotfiles included, skip dirs pruned."""
    found: list[Path] = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        depth = len(here.relative_to(root).parts)
        if depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            found.append(here / name)
    return found


def _shape_score(path: Path) -> int:
    """How report-shaped the content looks. Ranking only, never a filter."""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return 0
    return sum(1 for m in MARKERS if m in head)


def scan(roots: list[Path], since: float, expected: Path | None,
         max_depth: int = 3) -> list[dict]:
    """Candidate artifacts under *roots* modified at or after *since*.

    *expected* is excluded: if the contract path exists there is nothing to
    recover, and reporting it would read as a find.
    """
    exp = expected.resolve() if expected else None
    seen: set[Path] = set()
    out: list[dict] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in _walk(root, max_depth):
            if path.suffix.lower() not in SUFFIXES:
                continue
            try:
                resolved = path.resolve()
                stat = path.stat()
            except OSError:
                continue
            if resolved in seen or resolved == exp:
                continue
            if stat.st_mtime < since or stat.st_size == 0:
                continue
            seen.add(resolved)
            out.append({
                "path": str(resolved),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "score": _shape_score(path),
                "hidden": path.name.startswith("."),
            })
    # Report-shaped first, then newest. A dotfile is not ranked up: the operator
    # needs the likeliest report, not the most surprising one.
    out.sort(key=lambda c: (-c["score"], -c["mtime"]))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cd", required=True,
                    help="the dispatch's workspace (its --cd)")
    ap.add_argument("--expected",
                    help="the --report-file path that is missing; excluded from results")
    ap.add_argument("--minutes", type=float, default=120.0,
                    help="only files modified within this many minutes (default 120)")
    ap.add_argument("--since", type=float,
                    help="epoch seconds floor; overrides --minutes")
    ap.add_argument("--extra-dir", action="append", default=[],
                    help="additional directory to search (repeatable)")
    ap.add_argument("--depth", type=int, default=3, help="max walk depth (default 3)")
    args = ap.parse_args(argv)

    workspace = Path(args.cd).expanduser()
    if not workspace.is_dir():
        print(f"ERROR: --cd is not a directory: {workspace}", file=sys.stderr)
        # No candidate count on a cannot-look. "I could not search" and "I searched
        # and found nothing" are opposite facts and must not print the same token.
        print("OFFCONTRACT: UNREADABLE reason=no_workspace")
        return 2

    since = args.since if args.since is not None else time.time() - args.minutes * 60
    expected = Path(args.expected).expanduser() if args.expected else None

    roots = [workspace, AGY_SCRATCH]
    if expected:
        roots.append(expected.parent)
    roots.extend(Path(d).expanduser() for d in args.extra_dir)

    candidates = scan(roots, since, expected, max_depth=args.depth)

    if not candidates:
        print("OFFCONTRACT: NONE searched=" + ",".join(str(r) for r in roots))
        return 0

    print(f"OFFCONTRACT: FOUND {len(candidates)}")
    for c in candidates:
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(c["mtime"]))
        flag = " hidden" if c["hidden"] else ""
        print(f"  {c['path']} {c['size']}B {stamp} shape={c['score']}{flag}")
    print("  ! Not validated. Transcribe into the gate's schema by hand and falsify "
          "every premise against the source before acting on it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
