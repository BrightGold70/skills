#!/usr/bin/env python3
"""h_mad_extract_report.py - pull a reviewer's report out of a pane scrape.

`hmad-dispatch read` scrapes a live terminal, so the capture routinely holds
the previous cycle's report above the new prompt. Extracting on the first
`## Summary` therefore scored a stale verdict against the current cycle - a
trap the skill warned about without giving anyone a mechanism to avoid.

The reviewer brackets its report in a per-cycle sentinel:

    AUDIT-<feature>-<phase>-v<N>-BEGIN
    ## Summary
    ...
    AUDIT-<feature>-<phase>-v<N>-END

Extraction takes the LAST complete pair, so neither an older cycle's report
nor a retry earlier in the same cycle can win. A missing pair or an empty body
raises rather than returning something scoreable: "the reviewer produced
nothing" must never look like "the reviewer found nothing".
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


class ExtractionError(Exception):
    """No usable report in the scrape."""


def sentinel_for(feature: str, phase: str, cycle: int | str) -> str:
    """Build the per-cycle sentinel stem the reviewer is told to emit."""
    return f"AUDIT-{feature}-{phase}-v{cycle}"


def extract(scrape: str, sentinel: str) -> str:
    """Return the body of the last complete sentinel pair in *scrape*."""
    begin = f"{sentinel}-BEGIN"
    end = f"{sentinel}-END"

    end_idx = scrape.rfind(end)
    if end_idx == -1:
        raise ExtractionError(
            f"no complete {sentinel} pair in scrape (no {end})"
        )

    begin_idx = scrape.rfind(begin, 0, end_idx)
    if begin_idx == -1:
        raise ExtractionError(
            f"no complete {sentinel} pair in scrape ({end} without {begin})"
        )

    body = scrape[begin_idx + len(begin) : end_idx].strip("\n")
    if not body.strip():
        raise ExtractionError(
            f"{sentinel} pair is empty - the reviewer produced no report"
        )
    return body


def main(argv: list[str] | None = None) -> int:
    """Run the report extraction CLI."""
    parser = argparse.ArgumentParser(
        description="Extract a sentinel-framed reviewer report from a scrape"
    )
    parser.add_argument("scrape_file", type=Path)
    parser.add_argument("--sentinel", help="Full sentinel stem, e.g. AUDIT-foo-plan-v2")
    parser.add_argument("--feature")
    parser.add_argument("--phase")
    parser.add_argument("--cycle")
    args = parser.parse_args(argv)

    sentinel = args.sentinel
    if not sentinel:
        if not (args.feature and args.phase and args.cycle):
            print(
                "ERROR: pass --sentinel, or all of --feature/--phase/--cycle",
                file=sys.stderr,
            )
            return 2
        sentinel = sentinel_for(args.feature, args.phase, args.cycle)

    try:
        scrape = args.scrape_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        print(extract(scrape, sentinel))
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
