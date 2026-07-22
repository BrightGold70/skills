#!/usr/bin/env python3
"""h_mad_audit_gate.py - classify H-MAD audit files for blocking findings."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


BLOCKING_SECTIONS = {
    "## Must-fix": "must_count",
    "## Should-fix": "should_count",
}


# Bullet markers a reviewer may emit. agy (Antigravity/Gemini) renders `• `, other
# tools `* `; the template asks for `- `. A trailing space is REQUIRED so markdown
# emphasis lines placed under a section (`**Note:** …`, `*(no issues)*`) are not
# miscounted as findings — those start with `*` but not `* `. Leading whitespace is
# stripped before matching because the Gemini TUI indents every captured line ~2
# spaces, which previously hid `## Must-fix` from a column-0 match and silently
# scored a real finding as PASS.
_BULLET_MARKERS = ("- ", "* ", "• ")


def _bullet_remainder(stripped: str) -> str | None:
    """Return the text after a bullet marker, or None if not a bullet line."""
    for mark in _BULLET_MARKERS:
        if stripped.startswith(mark):
            return stripped[len(mark):].strip()
    return None


def _payload(line: str) -> str:
    """The finding text of a content line: its bullet remainder, or the line itself.

    Lets `- None` and `None` both read as the empty-section sentinel, and lets a
    non-bulleted finding (prose / `1.` numbered / `> blockquote`) still be seen as
    content rather than silently ignored.
    """
    stripped = line.strip()
    remainder = _bullet_remainder(stripped)
    return remainder if remainder is not None else stripped


def _count_section_findings(content: list[str], acknowledged: set[str]) -> int:
    """Findings in one blocking section's non-blank content lines.

    A section is CLEAN (0) iff every line's payload is the `None` sentinel — this
    covers an empty section, `None`, and a stray `- None`. Otherwise it has
    findings. When the section carries `-`/`*`/`•` bullets we count them (so a
    wrapped multi-line bullet counts once, not once per line). When it carries
    non-`None` content but NO bullet — a prose, numbered, or blockquote finding a
    reviewer wrote off-template — we count 1 rather than 0, so such a finding
    fails the gate (fail-safe) instead of being silently missed (F14).
    """
    payloads = [_payload(line) for line in content]
    if all(p.lower() == "none" for p in payloads):
        return 0
    bullets = [
        p for line, p in zip(content, payloads)
        if _bullet_remainder(line.strip()) is not None
        and p and p.lower() != "none" and p not in acknowledged
    ]
    if bullets:
        return len(bullets)
    # Non-None content with no countable bullet → at least one off-template finding.
    joined = " ".join(p for p in payloads if p)
    return 0 if joined in acknowledged else 1


def has_gate_sections(text: str) -> bool:
    """True iff BOTH `## Must-fix` and `## Should-fix` headers are present.

    An extract that lacks them is not a clean audit — it is no audit at all (an
    empty/garbled scrape). The gate must refuse to score it rather than report
    the absent findings as zero findings.
    """
    seen = {line.strip() for line in text.splitlines()}
    return all(section in seen for section in BLOCKING_SECTIONS)


def classify(text: str, acknowledged: set[str] | None = None) -> dict:
    """Count findings in Must-fix/Should-fix (indent-, marker- and prose-tolerant).

    A finding is a `-`/`*`/`•` bullet, OR — fail-safe — any non-`None` content in a
    blocking section that carries no bullet (prose / numbered / blockquote), so an
    off-template finding fails the gate rather than being silently missed.
    """
    acknowledged_items = acknowledged or set()
    section_content: dict[str, list[str]] = {key: [] for key in BLOCKING_SECTIONS.values()}
    current_count_key: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped in BLOCKING_SECTIONS:
            current_count_key = BLOCKING_SECTIONS[stripped]
            continue
        if stripped.startswith("## "):
            current_count_key = None
            continue
        if current_count_key and stripped:
            section_content[current_count_key].append(line)

    counts = {
        key: _count_section_findings(content, acknowledged_items)
        for key, content in section_content.items()
    }
    verdict = "FAIL" if counts["must_count"] or counts["should_count"] else "PASS"
    return {"verdict": verdict, **counts}


def _acknowledged_from_text(text: str) -> set[str]:
    acknowledged: set[str] = set()
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Acknowledged-not-fixed":
            in_section = True
            continue
        if stripped.startswith("## "):
            in_section = False
            continue
        if in_section:
            item = _bullet_remainder(stripped)
            if item:
                acknowledged.add(item)
    return acknowledged


def _read_ack_file(path: Path) -> set[str]:
    acknowledged: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if stripped:
            acknowledged.add(stripped)
    return acknowledged


def main(argv: list[str] | None = None) -> int:
    """Run the audit gate CLI."""
    parser = argparse.ArgumentParser(description="H-MAD audit gate")
    parser.add_argument("audit_file", type=Path)
    parser.add_argument("--ack-file", type=Path)
    parser.add_argument("--must-only", action="store_true")
    args = parser.parse_args(argv)

    try:
        text = args.audit_file.read_text(encoding="utf-8")
        acknowledged = _acknowledged_from_text(text)
        if args.ack_file:
            acknowledged.update(_read_ack_file(args.ack_file))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Feature name derived from the audit filename (project-agnostic):
    # "<feature>.<phase>.audit.v<N>.md" -> "<feature>".
    feature = args.audit_file.name.split(".")[0] or "unknown"

    # An input lacking the mandatory `## Must-fix`/`## Should-fix` sections is not
    # a clean audit — it is an empty or garbled scrape (e.g. the reviewer emitted
    # nothing and the extractor wrote an empty file). Scoring it would report the
    # missing findings as zero findings. Refuse with a distinct token + non-zero
    # exit (an operational error, not a verdict), so "no report" can never read as
    # "no findings". Signal discipline holds: exit 0 is reserved for PASS/FAIL.
    if not has_gate_sections(text):
        print("GATE: INVALID must=0 should=0")
        print(f"[H-MAD] {feature} gate INVALID (missing Must-fix/Should-fix sections)")
        return 2

    result = classify(text, acknowledged)
    verdict = "FAIL" if result["must_count"] or (result["should_count"] and not args.must_only) else "PASS"
    print(f"GATE: {verdict} must={result['must_count']} should={result['should_count']}")
    print(f"[H-MAD] {feature} gate {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
