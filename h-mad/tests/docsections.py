"""Bound a Markdown section on structure, never on a byte count.

Two failures produced this module, both measured in this repo.

**A fixed-width window goes vacuous as its section grows.** `s[i:i + 4000]`
silently stopped covering the end of its own section the moment a paragraph was
added: the `HALT`/`DENY` pin failed for the wrong reason ("the test lost sight of
the text", not "the doc regressed"), and had the growth been elsewhere it would
have PASSED while measuring nothing.

**A level-aware bound that ignores fences truncates at a bash comment.** A
`# comment` at column 0 inside a ``` block matches `^#{1,2} ` and ends the
section inside its own example. Measured 2026-09-01 against `h-mad/SKILL.md`:
the fence-blind bound ended `## Phase 5 (Implementation) sub-steps` at offset
54555 where the fence-aware one ends at 78825 — **24,270 characters** of the
section were invisible to the three tests reading it. No assertion was vacuous
at the time only because all of them happened to be positive and landed early;
a negative assertion over that range would have passed against text it never saw.

So both callers are served here rather than re-derived per file. Two same-named
helpers already grew inside one test file because the first was not found.
"""

from __future__ import annotations

import re

__all__ = ["titled_section", "section_from"]


def _fence_aware_end(text: str, start: int, level: int) -> int:
    """Offset of the next heading at `level` or higher, ignoring fenced blocks."""
    off = start
    in_fence = False
    for line in text[start:].splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(rf"^#{{1,{level}}} ", line):
            return off
        off += len(line)
    return len(text)


def titled_section(text: str, heading: str) -> str:
    """The named section's body, bounded by the next same-or-higher heading.

    `heading` is the text after the `#`s. The section OWNS its subsections: a
    bound that stopped at any heading would cut a `##` section short at its first
    `###` and every assertion about the later part would fail for the wrong
    reason.
    """
    match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)
    assert match, f"missing section {heading!r}"
    level = len(match.group("marks"))
    return text[match.end():_fence_aware_end(text, match.end(), level)]


def section_from(text: str, offset: int, level: int = 2) -> str:
    """From an arbitrary offset to the next heading at `level` or higher.

    For a pin anchored on a symbol rather than a heading — the case a byte window
    is usually reached for, because the anchor is mid-section and there is no
    title to name.
    """
    return text[offset:_fence_aware_end(text, offset, level)]
