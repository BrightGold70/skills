#!/usr/bin/env python3
"""Append one entry to a phase doc's `## Version History`, or refuse loudly.

The 27x-per-session step this replaces was a hand-written anchored substitution,
and the reason it needs a script is not the append -- it is the *assert*. A
`.replace()` whose anchor has drifted writes nothing and returns success, so a
skipped bump and a completed bump are byte-identical from the caller's side.
Every refusal below is a case that a hand-rolled substitution performs silently
and wrongly.

Measured over 713 real `## Version History` sections (2128 files across
HemaSuite + this repo, 2026-08-25):

  * 713/713 headers are `##`. No other level exists, so the anchor is exact.
  * Section terminators: EOF 687, a `---` rule 20, a following header 6. All
    three are honoured; stopping only at a header would splice into the next
    section for the 20 rule-terminated cases.
  * Shapes: 573 bullet, 140 table. Tables are report/archive docs, not the
    audit-loop docs this serves -- they are REFUSED, never reformatted.
  * Ordering over the 246 sections carrying >=2 entries: ascending 191,
    descending 29, unsorted 26. **A blind append-at-end is wrong for 55 of
    246 (22%) and silently so**, which is why placement is derived from the
    section rather than assumed.
  * Entry form: 998 of 1103 bullets are `- vX.Y: text`. That is the only form
    emitted. A date belongs inside the text, as the corpus already writes it.

Verdict line (mutator convention, per `h_mad_state_write.py`):

    VERSION-HISTORY: OK path=<p> version=<v> line=<n> placement=<append|prepend>
    VERSION-HISTORY: REFUSED path=<p> reason=<reason>
    VERSION-HISTORY: UNREADABLE path=<p>

exit 0 on a completed write (or `--dry-run`), 2 on any refusal. `UNREADABLE`
and `REFUSED` carry no `line=`, so a cannot-judge can never be read as a write
that landed. Stdlib-only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOKEN = "VERSION-HISTORY"

# All 713 corpus headers are `##`; trailing whitespace only.
ANCHOR = re.compile(r"^##[ \t]*Version History[ \t]*$", re.IGNORECASE)
HEADER = re.compile(r"^#{1,6} ")
RULE = re.compile(r"^[ \t]*---+[ \t]*$")
# Anchored at column 0 on purpose: an INDENTED bullet is a sub-bullet of the
# entry above it, not an entry. Four exist in this corpus, and one of them
# (`  - v1.4 made ...` under a v1.1 entry) made a correctly ascending section
# read as unsorted, so a real impl-plan was REFUSED. Measured 2026-08-25:
# zero top-level entries are indented, so nothing legitimate is lost.
BULLET_VERSION = re.compile(r"^[-*][ \t]+\**v(\d+)\.(\d+)")
BULLET_ANY = re.compile(r"^[-*][ \t]+")
TABLE_ROW = re.compile(r"^[ \t]*\|")
VERSION_ARG = re.compile(r"^v(\d+)\.(\d+)$")


class Refusal(Exception):
    """A condition under which the append must not happen."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def find_anchor(lines: list[str]) -> int:
    """Index of the sole `## Version History`, or refuse.

    Zero matches is the drifted-anchor case the hand-rolled substitution
    performs as a no-op. More than one is worse: a substitution picks the
    first, which for `references/inline-protocols.md` (7 headers, the only
    such file in the corpus) is a template example rather than the live log.
    """
    hits = [i for i, ln in enumerate(lines) if ANCHOR.match(ln)]
    if not hits:
        raise Refusal("anchor_missing")
    if len(hits) > 1:
        raise Refusal("anchor_ambiguous", f"matches={len(hits)}")
    return hits[0]


def section_bounds(lines: list[str], anchor: int) -> tuple[int, int]:
    """Half-open body range after `anchor`, stopping at header, `---`, or EOF.

    Fenced blocks are tracked because a ``` block inside the section can contain
    a `# heading` line, and treating that as the section boundary truncates the
    section and splices the new entry into the middle of the code block.
    """
    end = anchor + 1
    fenced = False
    while end < len(lines):
        line = lines[end]
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and (HEADER.match(line) or RULE.match(line)):
            break
        end += 1
    return anchor + 1, end


def entry_lines(lines: list[str], start: int, end: int) -> list[int]:
    """Indices of the section's bullet entries, in document order."""
    return [i for i in range(start, end) if BULLET_ANY.match(lines[i])]


def classify_shape(lines: list[str], start: int, end: int) -> str:
    """`bullet`, `empty`, or a refusal for anything this must not rewrite."""
    body = [i for i in range(start, end) if lines[i].strip()]
    if not body:
        return "empty"
    first = lines[body[0]]
    if TABLE_ROW.match(first):
        raise Refusal("table_shape")
    if BULLET_ANY.match(first):
        return "bullet"
    raise Refusal("unknown_shape", f"first={first.strip()[:40]!r}")


def parse_versions(lines: list[str], indices: list[int]) -> list[tuple[int, int]]:
    out = []
    for i in indices:
        m = BULLET_VERSION.match(lines[i])
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return out


def classify_order(versions: list[tuple[int, int]]) -> str:
    """`ascending`, `descending`, or refuse when the section is unsorted.

    Fewer than two parsable versions cannot express an order; those sections
    take the corpus majority (ascending, 191 of 246) rather than a guess that
    reads as knowledge.
    """
    if len(versions) < 2:
        return "ascending"
    asc = all(versions[i] <= versions[i + 1] for i in range(len(versions) - 1))
    desc = all(versions[i] >= versions[i + 1] for i in range(len(versions) - 1))
    if asc and not desc:
        return "ascending"
    if desc and not asc:
        return "descending"
    if asc and desc:  # every entry the same version; order is unobservable
        return "ascending"
    raise Refusal("mixed_order")


def plan_insertion(text: str, version: str, entry_text: str) -> tuple[list[str], int, str]:
    """Return (new_lines, insert_index, placement) without touching the file."""
    version_match = VERSION_ARG.match(version)
    if version_match is None:
        raise Refusal("bad_version", f"version={version!r}")
    if not entry_text.strip():
        raise Refusal("empty_text")
    if "\n" in entry_text:
        raise Refusal("multiline_text")

    lines = text.split("\n")
    anchor = find_anchor(lines)
    start, end = section_bounds(lines, anchor)
    shape = classify_shape(lines, start, end)
    indices = entry_lines(lines, start, end)
    versions = parse_versions(lines, indices)

    new_version = (int(version_match.group(1)), int(version_match.group(2)))
    if new_version in versions:
        # 27x per session means re-runs happen; a second append is the failure
        # a substitution cannot see, because its anchor still matches.
        raise Refusal("duplicate_version", f"version={version}")

    order = classify_order(versions)
    new_line = f"- {version}: {entry_text.strip()}"

    if shape == "empty" or not indices:
        insert_at = start
        placement = "append"
    elif order == "descending":
        insert_at = indices[0]
        placement = "prepend"
    else:
        # An entry is its bullet PLUS any indented continuation beneath it, and
        # 43 sections in this corpus wrap their last entry that way. Inserting
        # at `indices[-1] + 1` splices the new bullet between an entry and its
        # own continuation, divorcing the text from its owner.
        insert_at = indices[-1] + 1
        while insert_at < end and lines[insert_at].strip() and not BULLET_ANY.match(lines[insert_at]):
            insert_at += 1
        placement = "append"

    new_lines = lines[:insert_at] + [new_line] + lines[insert_at:]
    return new_lines, insert_at, placement


def assert_insertion_only(old: list[str], new: list[str], index: int) -> None:
    """The splice added exactly one line at `index` and changed nothing else.

    A slice assignment that quietly ate a neighbouring line is the failure this
    repo has shipped before; removing the inserted index must reproduce the
    original byte-for-byte.
    """
    if len(new) != len(old) + 1:
        raise Refusal("splice_not_additive", f"delta={len(new) - len(old)}")
    rebuilt = new[:index] + new[index + 1:]
    if rebuilt != old:
        raise Refusal("splice_not_additive", "surrounding lines changed")


def bump(path: Path, version: str, entry_text: str, dry_run: bool = False) -> dict:
    try:
        raw = path.read_bytes()
    except OSError:
        raise Refusal("unreadable") from None

    # Read and write at the BYTE level, preserving the file's own line endings.
    # `read_text()` normalises CRLF to LF and `write_text()` emits the platform
    # default, so a CRLF document would be rewritten end to end while every
    # assertion above still reported an insertion of one line -- they all
    # operate on the already-normalised list. The self-check cannot see a change
    # it has been handed in normalised form, so it is done on bytes.
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")

    old_lines = text.split("\n")
    new_lines, index, placement = plan_insertion(text, version, entry_text)
    assert_insertion_only(old_lines, new_lines, index)

    new_raw = newline.join(new_lines).encode("utf-8")
    inserted = (new_lines[index] + newline).encode("utf-8")
    cut = len(newline.join(new_lines[:index]).encode("utf-8"))
    cut += len(newline.encode("utf-8")) if index else 0
    if new_raw[:cut] + new_raw[cut + len(inserted):] != raw:
        raise Refusal("splice_not_additive", "byte-level check: the file changed elsewhere")

    if not dry_run:
        path.write_bytes(new_raw)

    return {"line": index + 1, "placement": placement, "version": version}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append one entry to a phase doc's `## Version History`, or refuse."
    )
    parser.add_argument("path", help="phase doc to bump")
    parser.add_argument("--version", required=True, help="new version, e.g. v1.3")
    parser.add_argument("--text", required=True, help="entry body (put any date in here)")
    parser.add_argument("--dry-run", action="store_true", help="compute and verify, write nothing")
    args = parser.parse_args(argv)

    path = Path(args.path)
    try:
        result = bump(path, args.version, args.text, dry_run=args.dry_run)
    except Refusal as exc:
        if exc.reason == "unreadable":
            print(f"{TOKEN}: UNREADABLE path={path}")
        else:
            detail = f" {exc.detail}" if exc.detail else ""
            print(f"{TOKEN}: REFUSED path={path} reason={exc.reason}{detail}")
        return 2

    verb = "DRY-RUN" if args.dry_run else "OK"
    print(
        f"{TOKEN}: {verb} path={path} version={result['version']} "
        f"line={result['line']} placement={result['placement']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
