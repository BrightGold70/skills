#!/usr/bin/env python3
"""h_mad_state_ownership.py — one answer to "is this feature's owner still live?".

The feature claim is advisory, and two components act on it: the resume router
(`h_mad_resume_decision.py`) decides whether to hand a feature to a new session,
and the writer (`h_mad_state_write.py --claim`) decides whether to let that
session record ownership. Read and write must agree, or the router authorises
work the writer then refuses.

They did not agree. The router treated a claim older than two hours as
abandoned; the writer had no staleness allowance at all, so a 19.6h-dead session
still blocked the claim and `--force` was the only way through (observed
2026-08-02). The cost is not the extra flag — it is what the flag came to mean.
`--force` is the verb for stealing a claim from a LIVE session, and routing the
routine "the previous session crashed" case through it trains an operator to
reach for it reflexively, wearing out the one guard that protects a live run.

This module is the single source of truth so the two cannot drift again. It is
deliberately tiny and stdlib-only: both callers are standalone scripts invoked
with a bare `python3`.
"""
from __future__ import annotations

from datetime import datetime, timezone

# Two hours. Long enough that an operator stepping away mid-phase does not lose
# the feature, short enough that a crashed session does not hold it overnight.
OWNERSHIP_STALE_AFTER_SECONDS = 2 * 60 * 60


def parse_ts(value) -> "datetime | None":
    """An ISO-8601 timestamp as an aware datetime, or None if unreadable.

    Naive input is read as UTC: every producer here stamps UTC, and guessing a
    local zone would silently shift a heartbeat across the staleness boundary.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def owner_is_live(heartbeat_ts, now: str | None = None) -> bool:
    """True when a claim stamped `heartbeat_ts` still counts as held.

    Fails CLOSED — an absent or unparseable heartbeat reads as live. "Held, with
    no evidence of when" is not evidence of abandonment, and the safe error is
    to leave a possibly-running session in possession rather than to hand its
    feature to a second one.

    The boundary is inclusive: age exactly equal to the window is still live, so
    a claim becomes stale only once it is strictly older.
    """
    heartbeat = parse_ts(heartbeat_ts)
    if heartbeat is None:
        return True
    reference = parse_ts(now) or datetime.now(timezone.utc)
    age = (reference - heartbeat).total_seconds()
    return age <= OWNERSHIP_STALE_AFTER_SECONDS
