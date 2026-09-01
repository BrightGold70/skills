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

from h_mad_telemetry import resolve_docs_root

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
        blockers.append({
            "code": "archreview_skipped",
            "detail": (
                "6a-prime did not run (no reviewer pane). A headless review "
                "satisfies the gate: `hmad-dispatch exec agy` needs no pane. If "
                "no reviewer exists at all, record "
                "archreview=SKIPPED_OPERATOR_OVERRIDE as a deliberate operator "
                "decision - it closes with a warning."
            ),
        })
    elif archreview == "SKIPPED_OPERATOR_OVERRIDE":
        warnings.append({
            "code": "archreview_overridden",
            "detail": (
                "6a-prime was skipped by explicit operator override. Carry "
                "SKIPPED_OPERATOR_OVERRIDE into the Phase 7 report - no architectural "
                "review happened; this is not READY_TO_MERGE."
            ),
        })
    elif archreview == "READY_TO_MERGE":
        pass                        # the only clean pass
    else:                           # absent, None, or any unrecognised value
        blockers.append({
            "code": "archreview_not_run",
            "detail": (
                "no architectural review recorded (orchestrator_state[<feature>]"
                ".archreview is absent or unrecognised). Run 6a-prime headlessly "
                "with `hmad-dispatch exec agy`, then record the extracted "
                "ASSESSMENT with `h_mad_state_write.py <state> --feature "
                "<feature> --set archreview=<value>`. A feature cannot close "
                "without one."
            ),
        })

    return {"ready": not blockers, "blockers": blockers, "warnings": warnings}


def resolve_analysis_path(
    explicit: Path | None, state_path: Path, feature: str
) -> Path:
    """Where the gap analysis lives, anchored to the STATE FILE, never to the CWD.

    The state file argument already names the project tree the feature belongs to.
    Where the operator started the process does not, and H-MAD is routinely driven
    from a monorepo root against a sub-project's state file -- which is HemaSuite's
    whole layout (`hematology-paper-writer/docs/.bkit-memory.json`).

    The default used to be a relative `docs/03-analysis/<feature>.analysis.md`, so
    the same state and the same files produced `BLOCKED analysis_missing` from the
    monorepo root and `READY blockers=0` from the sub-project. The false BLOCKED is
    the safe direction; its mirror is not. Start the process in any tree holding a
    file at the matching relative path and the gate closes Phase 7 on ANOTHER
    feature's analysis, with nothing in the output saying which file it read.

    An explicit `--analysis` is returned untouched. Re-rooting a path the operator
    typed would be a second surprise in the opposite direction.

    Shares `resolve_docs_root` with telemetry rather than re-deriving it: two
    copies of one rule is how the audit-gate caller drifted from the gate CLI (#39).
    """
    if explicit is not None:
        return explicit
    return resolve_docs_root(None, state_path) / "03-analysis" / f"{feature}.analysis.md"


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

    analysis = resolve_analysis_path(args.analysis, args.state_file, args.feature)
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
