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
from datetime import datetime, timezone
from pathlib import Path


def _phase_num(value) -> int:
    """Coerce a phase marker to its integer index (0-7).

    Tolerant of every form the state file actually carries: the schema's
    integer (0-7), the orchestrator's "stepN" string (the `phase` enum form
    that also leaks into current/last_completed_phase), and the "complete"
    sentinel. Anything unrecognized maps to 0 so the caller degrades to
    resume_manual rather than crashing. `bool` is special-cased because it
    is an int subclass (`True >= 7` would otherwise silently mislead).
    """
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        token = value.strip().lower()
        if token == "complete":
            return 7
        for prefix in ("step", "phase"):  # both prefixes occur in real state
            if token.startswith(prefix) and token[len(prefix):].isdigit():
                return int(token[len(prefix):])
        if token.isdigit():
            return int(token)
    return 0


OWNERSHIP_STALE_AFTER_SECONDS = 2 * 60 * 60


def _parse_ts(value) -> "datetime | None":
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _owned_elsewhere(feat_state: dict, session_id: str | None, now: str | None) -> bool:
    """True when another session holds this feature and was seen recently.

    A claim older than the staleness window is treated as abandoned — otherwise
    a session that crashed mid-feature would own it permanently. Callers that
    pass no session id opt out entirely, so existing callers keep their
    behaviour rather than meeting a token they cannot interpret.
    """
    if not session_id:
        return False
    owner = feat_state.get("owner_session_id")
    if not owner or owner == session_id:
        return False

    heartbeat = _parse_ts(feat_state.get("owner_heartbeat_ts"))
    if heartbeat is None:
        return True  # held, with no evidence of when — treat as live

    reference = _parse_ts(now) or datetime.now(timezone.utc)
    age = (reference - heartbeat).total_seconds()
    return age <= OWNERSHIP_STALE_AFTER_SECONDS


def decide(
    state_file: Path,
    feature: str,
    session_id: str | None = None,
    now: str | None = None,
) -> str:
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
    # Ownership is checked before halt: a halted feature held by a live session
    # is still held, and routing a second session to `halted` would send it to
    # fix something the first is already working on.
    if _owned_elsewhere(feat_state, session_id, now):
        return "owned_elsewhere"
    if feat_state.get("halt_reason"):
        return "halted"
    if feat_state.get("complete") is True:
        return "complete"
    if str(feat_state.get("current_phase", "")).strip().lower() == "complete":
        return "complete"
    last = _phase_num(feat_state.get("last_completed_phase", 0))
    if last >= 7:
        return "complete"
    if last >= 4:
        return "enter_autonomous"
    return "resume_manual"


def main() -> int:
    parser = argparse.ArgumentParser(description="h-mad resume decision (v2.2)")
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--feature", required=True)
    parser.add_argument(
        "--session-id",
        help="This session's id. Pass it to get the owned_elsewhere token when "
        "another live session holds the feature; omit to opt out of the check.",
    )
    parser.add_argument("--now", help="Reference time for staleness (testing)")
    args = parser.parse_args()
    print(decide(args.state, args.feature, session_id=args.session_id, now=args.now))
    return 0


if __name__ == "__main__":
    sys.exit(main())
