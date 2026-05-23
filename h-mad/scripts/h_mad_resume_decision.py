#!/usr/bin/env python3
"""h_mad_resume_decision.py — read state file + feature; print decision token.

Tokens: start_fresh | resume_manual | enter_autonomous | halted | complete

v2.2 thresholds:
- complete: last_completed_phase >= 7 (was 9 in v1)
- enter_autonomous: last_completed_phase >= 4 (was 6 in v1)
- resume_manual: 1 <= last_completed_phase < 4
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def decide(state_file: Path, feature: str) -> str:
    if not state_file.is_file():
        return "start_fresh"
    try:
        state = json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        return "start_fresh"
    orchestrator_state = state.get("orchestrator_state") or {}
    feat_state = orchestrator_state.get(feature)
    if not feat_state:
        return "start_fresh"
    if feat_state.get("halt_reason"):
        return "halted"
    last = feat_state.get("last_completed_phase", 0)
    if last >= 7:
        return "complete"
    if last >= 4:
        return "enter_autonomous"
    return "resume_manual"


def main() -> int:
    parser = argparse.ArgumentParser(description="h-mad resume decision (v2.2)")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--feature", required=True)
    args = parser.parse_args()
    print(decide(args.state, args.feature))
    return 0


if __name__ == "__main__":
    sys.exit(main())
