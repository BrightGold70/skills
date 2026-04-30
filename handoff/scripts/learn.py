#!/usr/bin/env python3
"""Bundled durable-learnings store for the handoff skill.

Stores cross-session learnings in ``<project>/docs/learnings.md`` —
project-local, version-controlled, grep-friendly markdown. Newest entries
at the top, one line per entry, tags backtick-quoted so grep can match
them cleanly without false-positives from prose.

This is a self-contained replacement for the previously-external ``/learn``
skill. No plugin or external skill dependency — the handoff skill bundles
this script directly so durable-learning persistence works regardless of
which plugins are loaded in a given session.

Usage:
  python scripts/learn.py add "<pattern>" \\
      --category gotcha|solution|pattern \\
      --tags "tag1,tag2,handoff:2026-04-30-foo"
  python scripts/learn.py search <term>

Project-root resolution mirrors the handoff skill itself — git remote /
git toplevel / cwd, in that order.

Format example (one line per entry):

  - 2026-04-30 · gotcha · `lightrag,nan-embed` — qwen3-embedding NaN's on
    long inputs; substitute random unit vector not zero (L2-norm poisons)

Why one line per entry: ``grep`` returns the whole entry on a hit, no
multi-line regex or context flags needed. Why backtick-quoted tags: lets
``grep '`lightrag,'`` match exactly the start of the tag list without
collapsing into prose mentions of the word.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CATEGORIES = ("gotcha", "solution", "pattern")
HEADER = """# Learnings — Durable Cross-Session Knowledge

Project-local kernel of gotchas, solutions, and patterns worth surviving
across sessions. Newest entries at the top. One line per entry.

Format: `- ISO-date · category · ` `` `tags` `` ` — pattern text`

Search via `grep <term> docs/learnings.md` or
`python ~/.claude/skills/handoff/scripts/learn.py search <term>`.

"""

# Matches a single learning line. Tags are backtick-quoted to keep grep
# clean; pattern is everything after the em-dash.
ENTRY_RE = re.compile(
    r"^- (?P<date>\d{4}-\d{2}-\d{2}) · "
    r"(?P<category>gotcha|solution|pattern) · "
    r"`(?P<tags>[^`]*)` — (?P<pattern>.+)$"
)


def project_root() -> Path:
    """Resolve project root via git toplevel; fall back to cwd.

    Matches the handoff skill's project-slug derivation logic so learnings
    end up in the same repo as the handoff doc that referenced them.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        top = result.stdout.strip()
        if top and Path(top).is_dir():
            return Path(top)
    except FileNotFoundError:
        pass
    return Path.cwd()


def learnings_file(root: Path | None = None) -> Path:
    return (root or project_root()) / "docs" / "learnings.md"


def cmd_add(args: argparse.Namespace) -> int:
    pattern = args.pattern.strip()
    if not pattern:
        print("error: pattern is empty", file=sys.stderr)
        return 2
    if len(pattern) > 250:
        print(
            f"warning: pattern is {len(pattern)} chars (>250); kernel-only "
            "is recommended (under ~200 chars). Long patterns dilute search "
            "quality — split into a tighter kernel + put context in the "
            "handoff's Key Learnings section.",
            file=sys.stderr,
        )

    path = learnings_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    tags = (args.tags or "").strip()
    line = f"- {today} · {args.category} · `{tags}` — {pattern}\n"

    existing = path.read_text(encoding="utf-8") if path.is_file() else HEADER

    # Same-day exact-pattern dedup: refuse identical pattern text added on
    # the same calendar day. Tunable later if cross-day dedup proves needed.
    for old in existing.splitlines():
        m = ENTRY_RE.match(old)
        if m and m.group("pattern") == pattern and m.group("date") == today:
            print(
                f"skip: same-day duplicate already present in {path}",
                file=sys.stderr,
            )
            return 0

    # Insert at top of entry list (after header). The header trailer is the
    # blank line right before the first existing entry; we re-emit the full
    # canonical header on legacy files that predate the header convention.
    if HEADER in existing:
        head_end = existing.index(HEADER) + len(HEADER)
        new_text = existing[:head_end] + line + existing[head_end:]
    else:
        new_text = HEADER + line + existing

    path.write_text(new_text, encoding="utf-8")
    print(f"added: {line.strip()}")
    print(f"  -> {path}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    path = learnings_file()
    if not path.is_file():
        print(f"no learnings file at {path}", file=sys.stderr)
        return 1
    term = args.term.lower()
    hits: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if ENTRY_RE.match(line) and term in line.lower():
            hits.append(line)
    if not hits:
        print(f"no matches for {args.term!r} in {path}")
        return 1
    print(f"{len(hits)} match(es) in {path}:")
    for h in hits:
        print(h)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="learn",
        description=(
            "Bundled durable-learnings store for the handoff skill. "
            "Stores entries in <project>/docs/learnings.md, no external "
            "plugin dependency."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser(
        "add",
        help="record a durable learning",
        description=(
            "Append one entry to <project>/docs/learnings.md. Same-day "
            "exact-pattern duplicates are skipped silently. Pattern text "
            "should be the kernel of the lesson (≤200 chars); put narrative "
            "context in the handoff's Key Learnings section instead."
        ),
    )
    pa.add_argument("pattern", help="kernel of the learning")
    pa.add_argument(
        "--category",
        required=True,
        choices=CATEGORIES,
        help=(
            "gotcha (failure pattern with reusable diagnostic value), "
            "solution (working fix that codifies a pattern), or "
            "pattern (architectural shape worth remembering)"
        ),
    )
    pa.add_argument(
        "--tags",
        default="",
        help=(
            "comma-separated tags. Convention: include 'handoff:<date>-<slug>' "
            "to cross-reference the originating handoff doc. Example: "
            "'lightrag,nan-embed,handoff:2026-04-28-rebuild'"
        ),
    )
    pa.set_defaults(fn=cmd_add)

    ps = sub.add_parser(
        "search",
        help="case-insensitive substring search over learning entries",
    )
    ps.add_argument("term", help="substring to match against learning lines")
    ps.set_defaults(fn=cmd_search)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
