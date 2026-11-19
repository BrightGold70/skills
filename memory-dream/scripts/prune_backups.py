#!/usr/bin/env python3
"""Retention for memory-dream backups: delete backup directories older than N days (default 30).

Backups are the only undo for an unversioned memory store, so deletion is narrow:
  - only DIRECT children of the backup root whose names start with a backup timestamp
    (`YYYYMMDD-HHMMSS`, as dream_lint and the dream scripts write them); anything else is
    left alone and reported as `ignored`;
  - symlinks, and anything that resolves outside the root, are never deleted;
  - age comes from the timestamp in the NAME, not mtime (backups are copied with
    `copy2`, which keeps the original files' mtimes);
  - the newest FULL snapshot (both indexes plus every file they link to) is always kept,
    however old: it is the only complete restore point. A backup that merely holds
    MEMORY.md is partial — the index is often one of the files an edit touched.

Dry run by default: prints what it would delete. `--apply` deletes.
Exit: 0 done (or nothing to do) · 2 usage error or unreadable root.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import shutil
import sys

DEFAULT_ROOT = pathlib.Path.home() / ".claude" / "memory-dream-backups"
NAME = re.compile(r"^(\d{8})-(\d{6})")
INDEX_LINK = re.compile(r"\]\((?:\./)?([^)\s#]+\.md)(?:#[^)\s]*)?\)")
INDEXES = ("MEMORY.md", "MEMORY-ARCHIVE.md")


def is_full(d: pathlib.Path) -> bool:
    """A complete restore point: both indexes, and every file either index links to.

    Holding MEMORY.md is not enough — a partial backup holds it whenever the index was one
    of the files an edit touched.
    """
    try:
        if not all((d / i).is_file() for i in INDEXES):
            return False
        targets = set()
        for i in INDEXES:
            targets |= set(INDEX_LINK.findall((d / i).read_text(encoding="utf-8")))
        return bool(targets) and all((d / t).is_file() for t in targets)
    except (OSError, UnicodeDecodeError):
        return False


def stamp(name: str) -> _dt.datetime | None:
    m = NAME.match(name)
    if not m:
        return None
    try:
        return _dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return None


def plan(root: pathlib.Path, days: int, now: _dt.datetime) -> dict[str, list[pathlib.Path]]:
    """Classify every child of `root`: delete / keep / protected / ignored."""
    real_root = root.resolve()
    out: dict[str, list[pathlib.Path]] = {"delete": [], "keep": [], "protected": [], "ignored": []}
    dated = []
    for p in sorted(root.iterdir()):
        ts = stamp(p.name)
        if (ts is None or p.is_symlink() or not p.is_dir()
                or p.resolve().parent != real_root):
            out["ignored"].append(p)
            continue
        dated.append((ts, p))
    full = [(ts, p) for ts, p in dated if is_full(p)]
    newest_full = max(full)[1] if full else None
    cutoff = now - _dt.timedelta(days=days)
    for ts, p in dated:
        if p == newest_full:
            out["protected"].append(p)
        elif ts < cutoff:
            out["delete"].append(p)
        else:
            out["keep"].append(p)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Prune memory-dream backups older than N days")
    ap.add_argument("--root", type=pathlib.Path, default=DEFAULT_ROOT)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--apply", action="store_true", help="delete; without it, only report")
    ap.add_argument("--now", help=argparse.SUPPRESS)   # test seam: ISO datetime
    args = ap.parse_args(argv)
    if args.days < 1:
        print("PRUNE: USAGE --days must be >= 1", file=sys.stderr)
        return 2
    if not args.root.is_dir():
        print(f"PRUNE: NONE no backup root at {args.root}")
        return 0
    now = _dt.datetime.fromisoformat(args.now) if args.now else _dt.datetime.now()
    try:
        p = plan(args.root, args.days, now)
    except OSError as exc:
        print(f"PRUNE: UNREADABLE {args.root} ({exc})", file=sys.stderr)
        return 2
    verb = "deleted" if args.apply else "would_delete"
    print(f"PRUNE: {verb}={len(p['delete'])} keep={len(p['keep'])} "
          f"protected={len(p['protected'])} ignored={len(p['ignored'])} days={args.days}")
    for d in p["delete"]:
        print(f"  {verb.upper():<12} {d.name}")
        if args.apply:
            shutil.rmtree(d)
    for d in p["protected"]:
        print(f"  PROTECTED    {d.name} (newest full snapshot)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
