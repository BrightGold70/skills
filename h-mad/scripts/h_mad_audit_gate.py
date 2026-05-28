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


def _is_blocking_bullet(line: str, acknowledged: set[str]) -> bool:
    """Return True iff line is a non-empty, non-acknowledged blocking bullet."""
    if not line.startswith("- "):
        return False
    remainder = line[2:].strip()
    return bool(remainder) and remainder.lower() not in {"none"} and remainder not in acknowledged


def classify(text: str, acknowledged: set[str] | None = None) -> dict:
    """Count blocking bullets in Must-fix/Should-fix."""
    acknowledged_items = acknowledged or set()
    counts = {"must_count": 0, "should_count": 0}
    current_count_key: str | None = None

    for line in text.splitlines():
        if line in BLOCKING_SECTIONS:
            current_count_key = BLOCKING_SECTIONS[line]
            continue
        if line.startswith("## "):
            current_count_key = None
            continue
        if current_count_key and _is_blocking_bullet(line, acknowledged_items):
            counts[current_count_key] += 1

    verdict = "FAIL" if counts["must_count"] or counts["should_count"] else "PASS"
    return {"verdict": verdict, **counts}


def _acknowledged_from_text(text: str) -> set[str]:
    acknowledged: set[str] = set()
    in_section = False
    for line in text.splitlines():
        if line == "## Acknowledged-not-fixed":
            in_section = True
            continue
        if line.startswith("## "):
            in_section = False
            continue
        if in_section and line.startswith("- "):
            item = line[2:].strip()
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

    result = classify(text, acknowledged)
    verdict = "FAIL" if result["must_count"] or (result["should_count"] and not args.must_only) else "PASS"
    # Feature name derived from the audit filename (project-agnostic):
    # "<feature>.<phase>.audit.v<N>.md" -> "<feature>".
    feature = args.audit_file.name.split(".")[0] or "unknown"
    print(f"GATE: {verdict} must={result['must_count']} should={result['should_count']}")
    print(f"[H-MAD] {feature} gate {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
