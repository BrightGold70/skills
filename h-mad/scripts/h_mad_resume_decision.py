#!/usr/bin/env python3
"""h_mad_resume_decision.py — read state file + feature; print decision token.

Tokens: start_fresh | resume_manual | enter_autonomous | halted | complete
        | owned_elsewhere | cannot_judge

`cannot_judge` is the one token that is not a decision. It means the state file
EXISTS and could not be read -- truncated mid-write, invalid JSON, unreadable --
and it exists because all three of "no file", "no record" and "unreadable file"
used to return `start_fresh`. Only the first two are legitimately that: a feature
with no record has been looked up in a file that parsed fine. An unreadable file
is not evidence that nothing is claimed; it is the absence of evidence either way,
and answering `start_fresh` there tells a caller to initialise a feature that may
be mid-flight and owned by a live session. WSG-6 was a state file that vanished
with the cause undetermined, and this is the half of that incident a tool can
defend against.

An ABSENT file still answers `start_fresh`, deliberately: a feature that has never
been started is the common case and the callers that know better (the handoff
skill's HANDOVER and TAKEOVER) check for the file before asking. Distinguishing
"never existed" from "vanished" needs evidence this script does not have.

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

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_state_ownership import (  # noqa: E402
    OWNERSHIP_STALE_AFTER_SECONDS,  # noqa: F401  (re-exported: callers import it from here)
    owner_is_live,
)


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


def _owned_elsewhere(feat_state: dict, session_id: str | None, now: str | None) -> bool:
    """True when another session holds this feature and was seen recently.

    A claim older than the staleness window is treated as abandoned — otherwise
    a session that crashed mid-feature would own it permanently. Callers that
    pass no session id opt out entirely, so existing callers keep their
    behaviour rather than meeting a token they cannot interpret.

    The window and the "is it live" rule live in `h_mad_state_ownership` because
    `--claim` must answer this question identically: a router that releases a
    feature the writer then refuses to hand over is a deadlock only `--force`
    can break.
    """
    if not session_id:
        return False
    owner = feat_state.get("owner_session_id")
    if not owner or owner == session_id:
        return False
    return owner_is_live(feat_state.get("owner_heartbeat_ts"), now)


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
        # NOT `start_fresh`. The file is there and something is in it; we could not
        # read it. "I could not check" and "nothing is claimed" lead to opposite
        # correct actions, so they must not share a token -- a truncated write on a
        # store holding dozens of records would otherwise route a second session to
        # initialise a feature another session is actively working.
        return "cannot_judge"
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
