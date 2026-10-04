#!/usr/bin/env python3
"""Phase 7c: archive a closed feature's documents COMPLETELY, or say it did not.

7c used to be four `mv docs/…/${FEATURE}* … 2>/dev/null || true` lines. For
doc-block-exec it moved 6 of 641 files and left the originals live, so a merged
feature's impl-plan kept gating live code until an unrelated commit turned the suite
red weeks later. The glob never reached `docs/03-analysis/probes/<feature>/`, and
`${FEATURE}*` matched every sibling sharing the prefix (`pin-agents` took
`pin-agents-tail-banner.*`). `|| true` hid all of it.

Usage:
  h_mad_archive_feature.py --feature F [--repo DIR] [--month YYYY-MM] [--apply | --check]

A feature's documents are, in docs/01-plan/features, docs/02-design/features,
docs/03-analysis and docs/04-report/features, the files named `F.*` or
`F-brainstorm*`, plus everything under docs/03-analysis/probes/F/ (archived under
`probes/`) unless tracked code outside it names that dir, in which case the dir is
live code and is KEPT (`KEPT:` line) rather than broken. They go to docs/archive/<month>/F/. Tracked files move with `git mv` so
history follows; untracked ones are renamed. An existing archive file is never
overwritten.

Default is a dry run: `ARCHIVE: PLAN would_move=N` and one `MOVE:` line each.
`--apply` moves, then re-checks: `ARCHIVE: COMPLETE moved=N`, or
`ARCHIVE: INCOMPLETE moved=N left=K` with `LEFT:`/`COLLISION:` lines (exit 2).
`--check` moves nothing: `ARCHIVE: COMPLETE left=0` or `ARCHIVE: INCOMPLETE left=K`
(exit 2). A name matching nothing, with no archive, is `ARCHIVE: NOTHING` (exit 2):
a typo must not certify a complete archive.
"""
from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

DOC_DIRS = ("docs/01-plan/features", "docs/02-design/features", "docs/03-analysis",
            "docs/04-report/features")
PROBES = "docs/03-analysis/probes"


def probe_readers(repo: Path, feature: str) -> list[str]:
    """Tracked files outside the probes dir and the archive that name it.

    A probes dir is sometimes live code: this repo's `test_host_runtime_docs.py`
    reads `probes/multi-host-runtime/`. Archiving such a dir breaks its reader, so
    it is kept. Markdown is excluded: a handoff or backlog row MENTIONING the path is
    prose, not a reader. Over-matching only keeps a dir live, the safe direction.
    """
    needle = f"{PROBES}/{feature}"
    # Anchored on a path boundary: `probes/foo-bar/` contains `probes/foo`.
    pattern = needle.replace(".", "\\.") + "([/\"'[:space:]]|$)"
    out = subprocess.run(["git", "-C", str(repo), "grep", "-l", "-E", "-e", pattern, "--",
                          ".", f":(exclude){needle}", ":(exclude)docs/archive", ":(exclude,glob)**/*.md"],
                         capture_output=True, text=True)
    if out.returncode not in (0, 1):
        raise RuntimeError(out.stderr.strip() or "git grep failed")
    return out.stdout.split()


def feature_files(repo: Path, feature: str, keep_probes: bool = False) -> list[tuple[Path, Path]]:
    """(source, path relative to the archive dir) for every live feature document."""
    out = []
    for d in DOC_DIRS:
        base = repo / d
        if not base.is_dir():
            continue
        for p in sorted(base.iterdir()):
            if p.is_file() and (p.name.startswith(f"{feature}.")
                                or p.name.startswith(f"{feature}-brainstorm")):
                out.append((p, Path(p.name)))
    probes = repo / PROBES / feature
    if probes.is_dir() and not keep_probes:
        out += [(p, Path("probes") / p.relative_to(probes))
                for p in sorted(probes.rglob("*")) if p.is_file()]
    return out


def _tracked(repo: Path, paths: list[Path]) -> set[Path]:
    if not paths:
        return set()
    out = subprocess.run(["git", "-C", str(repo), "ls-files", "-z", "--",
                          *[str(p.relative_to(repo)) for p in paths]],
                         capture_output=True, text=True, check=True).stdout
    return {repo / rel for rel in out.split("\0") if rel}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--feature", required=True)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--month", default=datetime.date.today().strftime("%Y-%m"))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    repo = args.repo.resolve()
    dest = repo / "docs" / "archive" / args.month / args.feature
    rel = lambda p: p.relative_to(repo)  # noqa: E731
    try:
        readers = probe_readers(repo, args.feature) if (repo / PROBES / args.feature).is_dir() else []
    except RuntimeError as exc:
        # "could not check for readers" must not read as "nothing reads it".
        print(f"ARCHIVE: UNREADABLE {exc}")
        return 2
    live = feature_files(repo, args.feature, keep_probes=bool(readers))
    if readers:
        print(f"KEPT: {PROBES}/{args.feature} — read by {', '.join(readers)}")

    if not live and not dest.is_dir():
        print(f"ARCHIVE: NOTHING feature={args.feature}")
        return 2

    if args.check:
        print(f"ARCHIVE: {'INCOMPLETE' if live else 'COMPLETE'} left={len(live)}")
        for src, _ in live:
            print(f"LEFT: {rel(src)}")
        return 2 if live else 0

    if not args.apply:
        print(f"ARCHIVE: PLAN would_move={len(live)}")
        for src, sub in live:
            print(f"MOVE: {rel(src)} -> {rel(dest / sub)}")
        return 0

    tracked = _tracked(repo, [src for src, _ in live])
    moved, collisions = 0, []
    for src, sub in live:
        target = dest / sub
        if target.exists():
            collisions.append(src)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if src in tracked:
            subprocess.run(["git", "-C", str(repo), "mv", str(rel(src)), str(rel(target))],
                           check=True, capture_output=True)
        else:
            src.rename(target)
        moved += 1

    left = feature_files(repo, args.feature, keep_probes=bool(readers))
    if not left:
        print(f"ARCHIVE: COMPLETE moved={moved}")
        return 0
    print(f"ARCHIVE: INCOMPLETE moved={moved} left={len(left)}")
    for src in collisions:
        print(f"COLLISION: {rel(src)} — {rel(dest)} already holds that name; not overwritten")
    for src, _ in left:
        if src not in collisions:
            print(f"LEFT: {rel(src)}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
