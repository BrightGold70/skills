#!/usr/bin/env python3
"""h_mad_extract_verdict.py - read a dispatch verdict line off a pane scrape.

Three contracts end in a machine-parsed line:

    STATUS:     DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT   (5d/5e codex)
    VERDICT:    COMPLIANT | DRIFT                                     (5e-review agy)
    ASSESSMENT: READY_TO_MERGE | WITH_FIXES | NO                      (6a-prime agy)

Each is read off a live pane, so each inherits the two failures the audit path
hit: a previous module's verdict still sitting in scrollback, and an agent that
went idle without emitting anything at all.

The second is why this exists. With no verdict line, a naive grep simply finds
nothing, and "the agent produced nothing" is indistinguishable from "the agent
raised no objection" - so a module can be committed on the strength of silence.
Absence therefore raises here; it is never returned as a value.

Selection takes the LAST matching line, so a stale verdict above cannot win.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CONTRACTS = {
    "STATUS": ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"],
    "VERDICT": ["COMPLIANT", "DRIFT"],
    "ASSESSMENT": ["READY_TO_MERGE", "WITH_FIXES", "NO"],
}


class VerdictError(Exception):
    """No usable verdict line in the scrape."""


def extract_verdict(
    scrape: str, key: str, allowed: list[str] | None = None
) -> str:
    """Return the value of the last `<key>:` line in *scrape*."""
    pattern = re.compile(rf"^[ \t]*{re.escape(key)}:[ \t]*(.*)$", re.MULTILINE)
    matches = pattern.findall(scrape)
    if not matches:
        raise VerdictError(
            f"no {key}: line in scrape - the agent produced no verdict"
        )

    value = matches[-1].strip()
    if not value:
        raise VerdictError(f"{key}: line is empty")

    if allowed and value not in allowed:
        raise VerdictError(f"{key}: {value!r} is not one of {allowed}")
    return value


def main(argv: list[str] | None = None) -> int:
    """Run the verdict extraction CLI."""
    parser = argparse.ArgumentParser(
        description="Extract a dispatch verdict line from a pane scrape"
    )
    parser.add_argument("scrape_file", type=Path)
    parser.add_argument(
        "--key",
        required=True,
        help="Verdict key: STATUS, VERDICT, or ASSESSMENT",
    )
    parser.add_argument(
        "--allowed",
        help="Comma-separated permitted values. Defaults to the known "
        "contract for STATUS/VERDICT/ASSESSMENT; pass explicitly to override.",
    )
    parser.add_argument("--feature", help="Emit an [H-MAD] marker for this feature")
    parser.add_argument("--phase", default="5", help="Phase label for the marker")
    args = parser.parse_args(argv)

    if args.allowed is not None:
        allowed = [v.strip() for v in args.allowed.split(",") if v.strip()]
    else:
        allowed = CONTRACTS.get(args.key)

    try:
        scrape = args.scrape_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        value = extract_verdict(scrape, args.key, allowed)
    except VerdictError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"{args.key}: {value}")
    if args.feature:
        print(f"[H-MAD] {args.feature} phase{args.phase} {args.key.lower()}_{value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
