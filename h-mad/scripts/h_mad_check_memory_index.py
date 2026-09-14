#!/usr/bin/env python3
"""Pre-check a memory index against the caps Claude Code enforces at LOAD time.

Why a pre-check rather than the warning that already exists: the built-in warning
fires on the write that crosses the line, which is one write too late and lands
in a hook message rather than anywhere a later session looks. The failure it
describes is worse than "a warning was missed" — quoting the binary:

    Error: this write left the <index>, over its <cap> read limit. The write
    succeeded, but everything past the limit IS SILENTLY DROPPED EACH TIME THE
    INDEX IS LOADED — entries at the end are already invisible to readers.

So the write SUCCEEDS, the file on disk is complete and correct, and the loss
happens on every subsequent load with no error at the point of loss. `wc -c` on
the file cannot see it; only a comparison against the cap can. That is the whole
reason this script exists and why it prints the dropped text rather than a count:
`dropped=254` is a number, and the two backlog entries it is deleting are the
finding.

CONSTANTS, decoded from the 2.1.270 binary (minified names recorded to make the
transcription auditable, never matched on — they are regenerated per build):

    F2  = 25000   byte cap   -> rendered "24.4KB"  (25000/1024 = 24.41)
    hD  = 200     line cap
    Ams = 0.8     warn threshold: warn once the WORST dimension reaches 80%
    xZn = 0.7     compaction target -> 17500 bytes / 140 lines ("17.1KB")

The selection rule is the binary's own and is not an embellishment: it scores
EVERY dimension, takes the one with the highest fraction, and reports that one
(`n.reduce((d,m)=>m.frac>d.frac?m:d)`). An index can sit at 40% of its byte cap
and still be over on lines, so a byte-only check reports OK on a broken index.

`tests/test_h_mad_check_memory_index.py` re-greps the live binary for these four
values on every run and fails when they drift; when the binary cannot be read it
SKIPS rather than passes, because "I could not check" and "the check said yes"
must not be spelled the same way.

Usage:
    h_mad_check_memory_index.py [<path-to-MEMORY.md> ...]

With no argument it resolves every `~/.claude/projects/*/memory/MEMORY.md`,
de-duplicated by inode — those directories are commonly symlinks onto ONE shared
store, and reporting the same file 40 times hides whether there is one problem or
forty.

Exit 0 when every index is under the warn threshold, 1 when any is WARN or OVER,
2 on a usage error or an unreadable index. Unreadable is NOT clean.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

BYTE_CAP = 25000
LINE_CAP = 200
WARN_FRAC = 0.8
TARGET_FRAC = 0.7


def render_kb(n: int) -> str:
    """The binary's own byte formatting: KiB to one decimal. 25000 -> '24.4KB'."""
    return f"{n / 1024:.1f}KB"


def measure(path: pathlib.Path) -> tuple[int, int]:
    """(bytes, lines). Lines counted the way a loader splits them, not `wc -l`:
    a final line without a trailing newline is still a line."""
    raw = path.read_bytes()
    if not raw:
        return (0, 0)
    return (len(raw), len(raw.split(b"\n")) - (1 if raw.endswith(b"\n") else 0))


def assess(size_bytes: int, line_count: int,
           byte_cap: int = BYTE_CAP, line_cap: int = LINE_CAP) -> dict:
    """Score both dimensions and return the WORST, mirroring the loader.

    Returning the worst rather than the first is the whole correctness of this:
    the dimensions fail independently, and whichever is further along is the one
    that decides whether content is being dropped.
    """
    dims = [
        {"dimension": "bytes", "frac": size_bytes / byte_cap,
         "over": size_bytes > byte_cap, "size": size_bytes, "cap": byte_cap},
        {"dimension": "lines", "frac": line_count / line_cap,
         "over": line_count > line_cap, "size": line_count, "cap": line_cap},
    ]
    worst = max(dims, key=lambda d: d["frac"])
    worst["verdict"] = (
        "OVER" if worst["over"] else "WARN" if worst["frac"] >= WARN_FRAC else "OK"
    )
    worst["target"] = int(worst["cap"] * TARGET_FRAC)
    return worst


def dropped_text(path: pathlib.Path, byte_cap: int = BYTE_CAP) -> str:
    """The bytes past the cap — what is invisible to every session, right now."""
    raw = path.read_bytes()
    return raw[byte_cap:].decode("utf-8", "replace") if len(raw) > byte_cap else ""


def default_indexes() -> list[pathlib.Path]:
    """Every project memory index, de-duplicated by inode.

    Those project directories are routinely symlinks onto a single shared store —
    measured on this machine: 40+ paths, one inode — so without the de-dup the
    report multiplies one problem into dozens and a reader cannot tell which.
    """
    seen: dict[tuple[int, int], pathlib.Path] = {}
    root = pathlib.Path.home() / ".claude" / "projects"
    for p in sorted(root.glob("*/memory/MEMORY.md")):
        try:
            st = p.stat()
        except OSError:
            continue
        seen.setdefault((st.st_dev, st.st_ino), p)
    return list(seen.values())


def check(path: pathlib.Path) -> tuple[str, str]:
    """(verdict, one-line report). UNREADABLE is its own verdict, never OK."""
    try:
        size_bytes, line_count = measure(path)
    except OSError as exc:
        return ("UNREADABLE", f"UNREADABLE {path} ({exc})")
    a = assess(size_bytes, line_count)
    over_by = max(0, a["size"] - a["cap"]) if a["dimension"] == "bytes" else 0
    return (a["verdict"], (
        f"{a['verdict']:<4} {path} "
        f"bytes={size_bytes}/{BYTE_CAP} lines={line_count}/{LINE_CAP} "
        f"worst={a['dimension']} frac={a['frac']:.0%} "
        f"dropped={over_by} target={a['target']}"
    ))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Pre-check a memory index against its load-time caps")
    ap.add_argument("paths", nargs="*", type=pathlib.Path,
                    help="MEMORY.md paths; default: every project memory index, de-duped by inode")
    ap.add_argument("--show-dropped", action="store_true",
                    help="print the text past the byte cap — what is invisible today")
    args = ap.parse_args(argv)

    paths = args.paths or default_indexes()
    if not paths:
        print("MEMORY_INDEX: NONE no memory index found", file=sys.stderr)
        return 2

    worst = 0
    for path in paths:
        verdict, line = check(path)
        print(line)
        if verdict == "UNREADABLE":
            worst = max(worst, 2)
        elif verdict in ("WARN", "OVER"):
            worst = max(worst, 1)
        if verdict == "OVER" and args.show_dropped:
            text = dropped_text(path)
            print(f"     --- {len(text.encode('utf-8', 'replace'))} bytes DROPPED on every load ---")
            for ln in text.splitlines():
                print(f"     | {ln}")
    if worst:
        print(
            f"  a memory index at or past its cap loses its TAIL silently — the write "
            f"succeeds and the overflow is dropped on every load. Compact to "
            f"{int(BYTE_CAP * TARGET_FRAC)} bytes / {int(LINE_CAP * TARGET_FRAC)} lines: "
            f"one line per entry, detail into topic files.",
            file=sys.stderr,
        )
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
