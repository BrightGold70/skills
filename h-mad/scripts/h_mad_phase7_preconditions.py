#!/usr/bin/env python3
"""h_mad_phase7_preconditions.py - can this feature be closed and merged?

Phase 7 merges and pushes. Phase 6 verifies. SKILL.md documents that order, and
nothing enforced it: the sequence lived as prose in a document the orchestrator
trusts itself to follow.

A feature completed Phase 5, merged to main and pushed with no Phase 6 at all —
no gap analysis, no architectural review, no telemetry, no archive. The suite was
green, which was the only signal available, and green tests said nothing about
spec conformance: the gap analysis run afterwards measured 0%.

This makes the sequence checkable. It reads state and the analysis artifact and
reports; it merges nothing. Verdict travels in the PHASE7: token with exit 0,
matching the audit gate, so a BLOCKED verdict never registers as a tool failure.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MATCH_RATE_THRESHOLD = 90.0

# Tolerates "## Match Rate: 96%", "Match rate: 89.5%", and the bolded "**0%**"
# a real analysis used — 0 is a measurement, not an absence.
_RATE = re.compile(r"match\s*rate\s*[:=]\s*\**\s*(\d+(?:\.\d+)?)\s*%", re.I)


def parse_match_rate(text: str) -> float | None:
    """First match rate in the document, or None when none is stated."""
    found = _RATE.search(text)
    return float(found.group(1)) if found else None


def check(record: dict, analysis_path: Path) -> dict:
    """Report blockers and warnings for closing this feature."""
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if record.get("halt_reason"):
        blockers.append({
            "code": "halted",
            "detail": f"open halt: {record['halt_reason']}",
        })

    phase = record.get("last_completed_phase")
    phase_num = phase if isinstance(phase, int) and not isinstance(phase, bool) else -1
    if phase_num < 6:
        blockers.append({
            "code": "verification_not_run",
            "detail": (
                f"last_completed_phase is {phase!r}; Phase 6 must complete before "
                "Phase 7 merges. Merging first is how a feature reached main with "
                "no gap analysis at all."
            ),
        })

    try:
        text = Path(analysis_path).read_text(encoding="utf-8")
    except OSError:
        blockers.append({
            "code": "analysis_missing",
            "detail": f"no gap analysis at {analysis_path}",
        })
        text = None

    if text is not None:
        rate = parse_match_rate(text)
        if rate is None:
            blockers.append({
                "code": "match_rate_unreadable",
                "detail": (
                    f"no match rate stated in {analysis_path}. An analysis with no "
                    "measurement is not evidence of a passing one."
                ),
            })
        elif rate < MATCH_RATE_THRESHOLD:
            blockers.append({
                "code": "match_rate_below_threshold",
                "detail": f"match rate {rate}% is below {MATCH_RATE_THRESHOLD}%",
            })

    # The architectural review: a failure blocks, a deliberate skip is reported.
    # #10 permits proceeding without a reviewer pane; it must not vanish here.
    archreview = record.get("archreview")
    if archreview in ("WITH_FIXES", "NO"):
        blockers.append({
            "code": "archreview_failed",
            "detail": f"6a-prime returned {archreview}",
        })
    elif archreview == "SKIPPED_NO_PANE":
        warnings.append({
            "code": "archreview_skipped",
            "detail": (
                "6a-prime did not run (no reviewer pane). Carry SKIPPED_NO_PANE "
                "into the Phase 7 report — it is not READY_TO_MERGE."
            ),
        })

    return {"ready": not blockers, "blockers": blockers, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 7 precondition CLI."""
    parser = argparse.ArgumentParser(description="H-MAD Phase 7 preconditions")
    parser.add_argument("state_file", type=Path)
    parser.add_argument("--feature", required=True)
    parser.add_argument(
        "--analysis",
        type=Path,
        help="Path to the gap analysis; defaults to "
        "docs/03-analysis/<feature>.analysis.md",
    )
    args = parser.parse_args(argv)

    try:
        state = json.loads(args.state_file.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: {args.state_file}: {exc}", file=sys.stderr)
        return 2

    record = (state.get("orchestrator_state") or {}).get(args.feature)
    if not record:
        print(f"ERROR: no such feature: {args.feature}", file=sys.stderr)
        return 2

    analysis = args.analysis or Path("docs/03-analysis") / f"{args.feature}.analysis.md"
    result = check(record, analysis)

    verdict = "READY" if result["ready"] else "BLOCKED"
    print(f"PHASE7: {verdict} blockers={len(result['blockers'])}")
    for item in result["blockers"]:
        print(f"  BLOCKER {item['code']}: {item['detail']}")
    for item in result["warnings"]:
        print(f"  WARNING {item['code']}: {item['detail']}")
    print(f"[H-MAD] {args.feature} phase7 {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
