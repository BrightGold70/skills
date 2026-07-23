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
  python3 scripts/learn.py add "<pattern>" \\
      --category gotcha|solution|pattern \\
      [--confidence 0.3|0.5|0.7|0.9] \\
      --tags "tag1,tag2,handoff:2026-04-30-foo"
  python3 scripts/learn.py search <term>

Confidence semantics (adapted from continuous-learning-v2):
  0.3 — tentative (single observation, not yet validated)
  0.5 — moderate (observed 2-3 times or user confirmed once)
  0.7 — strong (repeatedly observed, no contradictions) [default]
  0.9 — near-certain (core pattern, multiple independent confirmations)

Project-root resolution mirrors the handoff skill itself — git toplevel /
cwd, in that order.

Format example (one line per entry):

  - 2026-04-30 · gotcha · [0.7] · `lightrag,nan-embed` — qwen3-embedding
    NaN's on long inputs; substitute random unit vector not zero

Why one line per entry: ``grep`` returns the whole entry on a hit, no
multi-line regex or context flags needed. Why backtick-quoted tags: lets
``grep '`lightrag,'`` match exactly the start of the tag list without
collapsing into prose mentions of the word.

Backward compatibility: old entries without [confidence] are parsed and
preserved as-is; new entries always include confidence.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

CATEGORIES = ("gotcha", "solution", "pattern")
CONFIDENCES = (0.3, 0.5, 0.7, 0.9)
DEFAULT_CONFIDENCE = 0.7

# Kernel length cap. Deliberately tight — docs/learnings.md is grepped one-liners
# — but 200 rejected drafts that were already tightened to their payoff (observed
# 271->216->198 and 243->216->207, the trailing figure being the fit-and-still-
# meaningful form). 240 accepts that band in one shot while still rejecting bloated
# first drafts (260+), so "tighten it" survives without the eyeball-retry loop.
MAX_KERNEL = 240

HEADER = """# Learnings — Durable Cross-Session Knowledge

Project-local kernel of gotchas, solutions, and patterns worth surviving
across sessions. Newest entries at the top. One line per entry.

Format: `- ISO-date · category · [confidence] · ` `` `tags` `` ` — pattern text`

Confidence: 0.3=tentative  0.5=moderate  0.7=strong  0.9=near-certain

Search via `grep <term> docs/learnings.md` or
`python3 ~/.claude/skills/handoff/scripts/learn.py search <term>`.

"""


sys.path.insert(0, str(Path(__file__).resolve().parent))
from handoff_paths import canonical_root, learnings_path  # noqa: E402


def _project_root() -> Path:
    """Canonical (main-worktree) root — shared across Orca linked worktrees.

    Delegates to handoff_paths.canonical_root so learnings written from any
    worktree land in ONE `docs/learnings.md` at the main worktree, rather than
    fragmenting per-worktree (and vanishing when a worktree is removed).
    """
    return canonical_root()


def _learnings_path() -> Path:
    return learnings_path()


class LearningLine:
    """Matches a single learning line. Tags are backtick-quoted to keep grep
    clean; pattern is everything after the em-dash.

    Supports both legacy format (no confidence) and current format with
    [confidence] for backward compatibility.
    """

    # Current format: date · category · [confidence] · `tags` — text
    PATTERN_NEW = re.compile(
        r"^- (\d{4}-\d{2}-\d{2}) · (gotcha|solution|pattern)"
        r" · \[([0-9.]+)\] · `([^`]*)` — (.+)$"
    )
    # Legacy format: date · category · `tags` — text (no confidence)
    PATTERN_LEGACY = re.compile(
        r"^- (\d{4}-\d{2}-\d{2}) · (gotcha|solution|pattern) · `([^`]*)` — (.+)$"
    )

    def __init__(
        self,
        date_str: str,
        category: str,
        confidence: float,
        tags: str,
        text: str,
    ):
        self.date_str = date_str
        self.category = category
        self.confidence = confidence
        self.tags = tags
        self.text = text

    def render(self) -> str:
        return (
            f"- {self.date_str} · {self.category} · [{self.confidence}]"
            f" · `{self.tags}` — {self.text}"
        )

    @classmethod
    def parse(cls, line: str) -> "LearningLine | None":
        s = line.strip()
        m = cls.PATTERN_NEW.match(s)
        if m:
            date_str, category, conf_str, tags, text = m.groups()
            return cls(date_str, category, float(conf_str), tags, text)
        m = cls.PATTERN_LEGACY.match(s)
        if m:
            date_str, category, tags, text = m.groups()
            return cls(date_str, category, DEFAULT_CONFIDENCE, tags, text)
        return None


def _trim_to(text: str, limit: int = MAX_KERNEL) -> str:
    """Trim `text` to <= `limit` chars at a word boundary, marking the cut with '…'.

    Returns text unchanged when already within the limit. The body is cut to
    limit-1 (leaving room for the one-char ellipsis) then back to the last space,
    so the result is a clean prefix of the input plus a visible truncation mark.
    Exists so hitting the MAX_KERNEL cap costs ONE step: --trim applies this and
    stores; a plain rejection prints its result as a paste-ready suggestion.
    """
    if len(text) <= limit:
        return text
    body = text[: limit - 1]
    sp = body.rfind(" ")
    if sp > 0:
        body = body[:sp]
    return body.rstrip() + "\u2026"


def cmd_add(args: argparse.Namespace) -> int:
    pattern = args.pattern.strip()
    if len(pattern) > MAX_KERNEL:
        suggestion = _trim_to(pattern, MAX_KERNEL)
        if getattr(args, "trim", False):
            print(f"NOTE: kernel was {len(pattern)} chars; trimmed to "
                  f"{len(suggestion)} at a word boundary.", file=sys.stderr)
            pattern = suggestion
        else:
            print(f"ERROR: pattern exceeds {MAX_KERNEL} chars ({len(pattern)}). "
                  f"Re-run with --trim to auto-trim at a word boundary, or use "
                  f"this {len(suggestion)}-char form:", file=sys.stderr)
            print(f'  "{suggestion}"', file=sys.stderr)
            return 1
    if args.category not in CATEGORIES:
        print(f"ERROR: category must be one of {CATEGORIES}", file=sys.stderr)
        return 1
    if args.confidence not in CONFIDENCES:
        print(f"ERROR: confidence must be one of {CONFIDENCES}", file=sys.stderr)
        return 1

    tags = args.tags.strip().lower().replace(" ", "-") if args.tags else ""
    today = date.today().isoformat()
    entry = LearningLine(today, args.category, args.confidence, tags, pattern)

    path = _learnings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = path.read_text() if path.exists() else ""

    # Idempotent: skip same-day exact-pattern duplicates
    for line in existing.splitlines():
        parsed = LearningLine.parse(line)
        if parsed and parsed.date_str == today and parsed.text == pattern:
            print(f"[skipped] identical entry already exists for {today}")
            return 0

    # Prepend new entry after header (or at top if no header)
    if existing.startswith("# Learnings"):
        lines = existing.split("\n")
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("- "):
                insert_at = i
                break
            if line.startswith("Search via"):
                insert_at = i + 2  # after "Search via" line + blank
                break
        else:
            insert_at = len(lines)
        lines.insert(insert_at, entry.render())
        content = "\n".join(lines)
    else:
        content = HEADER + entry.render() + "\n" + existing

    path.write_text(content)
    print(f"Learning saved to {path.relative_to(_project_root())}:")
    print(f"  {entry.render()}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    path = _learnings_path()
    if not path.exists():
        print(f"No learnings file at {path}", file=sys.stderr)
        return 1

    term = args.term.lower()
    matches = [
        line for line in path.read_text().splitlines()
        if term in line.lower() and LearningLine.parse(line)
    ]

    if not matches:
        print(f"No learnings matching '{args.term}'")
        return 0

    print(f"Found {len(matches)} matching learning(s):\n")
    for m in matches:
        print(f"  {m}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="learn.py",
        description="Durable cross-session learnings store (handoff skill)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="record a new learning")
    p_add.add_argument("pattern", help=f"≤{MAX_KERNEL}-char reusable finding")
    p_add.add_argument(
        "--trim", action="store_true",
        help=f"if the kernel exceeds {MAX_KERNEL} chars, auto-trim at a word boundary "
             "(marked with …) instead of rejecting — one step, no retry loop"
    )
    p_add.add_argument(
        "--category", required=True, choices=CATEGORIES,
        help="gotcha | solution | pattern"
    )
    p_add.add_argument(
        "--confidence", type=float, default=DEFAULT_CONFIDENCE,
        choices=CONFIDENCES,
        metavar="{0.3,0.5,0.7,0.9}",
        help=(
            "confidence weight: 0.3=tentative, 0.5=moderate, "
            "0.7=strong [default], 0.9=near-certain"
        )
    )
    p_add.add_argument(
        "--tags", default="",
        help="comma-separated lowercase tags (e.g. 'lightrag,nan-embed,handoff:2026-04-30-foo')"
    )

    p_search = sub.add_parser("search", help="grep-style search over learnings")
    p_search.add_argument("term", help="search term (case-insensitive)")

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.cmd == "add":
        return cmd_add(args)
    return cmd_search(args)


if __name__ == "__main__":
    sys.exit(main())
