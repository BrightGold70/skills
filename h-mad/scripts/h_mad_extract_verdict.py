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

# The boundary line `hmad-dispatch send` appends as the FINAL line of every
# prompt. The agent's reply always renders after the echoed prompt, so slicing
# the scrape to the region past the boundary's LAST occurrence discards the
# echoed prompt wholesale — including any `STATUS: DONE` the output contract
# quotes. Without it, a silent agent's buffer holds only the echoed prompt, and
# the contract line the prompt states is read back as the agent's own verdict
# (a false STATUS: DONE). Constant, not per-dispatch: taking the LAST occurrence
# means each fresh dispatch's boundary also fences off the previous cycle's
# scrollback, so uniqueness buys nothing over "last wins".
DISPATCH_BOUNDARY = "===HMAD-DISPATCH-BOUNDARY==="


class VerdictError(Exception):
    """No usable verdict line in the scrape."""


def slice_after_boundary(scrape: str, marker: str) -> str:
    """Return the scrape region after *marker*'s last occurrence.

    Raises if *marker* is absent: a scrape that never captured the boundary is
    a scrape of the wrong pane, or one taken before the dispatch echoed — either
    way there is no verdict to trust, so fail closed rather than fall back to
    scanning the whole buffer (which is exactly the echoed-prompt trap).
    """
    idx = scrape.rfind(marker)
    if idx == -1:
        raise VerdictError(
            f"boundary marker {marker!r} not in scrape — the dispatch was not "
            "captured (wrong pane, or read before the prompt echoed)"
        )
    return scrape[idx + len(marker):]


def extract_verdict(
    scrape: str,
    key: str,
    allowed: list[str] | None = None,
    after: str | None = None,
) -> str:
    """Return the value of the last `<key>:` line in *scrape*.

    When *after* is given, only the region past its last occurrence is
    considered — see :func:`slice_after_boundary`.
    """
    if after is not None:
        scrape = slice_after_boundary(scrape, after)
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


# --- contentless DONE_WITH_CONCERNS (J10) -----------------------------------
#
# A verdict that declares doubt without stating it is unactionable and cannot be
# told apart from DONE, so it must fail the way silence does rather than pass as
# nuance. Measured on this machine: 7 of 13 historical DONE_WITH_CONCERNS reports
# name no concern anywhere.

_LABEL_WORD = re.compile(r"\b(?:concerns?|blockers?)\b", re.I)
_SECTION_START = re.compile(r"^(?:#{1,6}[ \t]|STATUS:|VERDICT:|ASSESSMENT:)")
_NEGATIONS = {
    "", "-", "none", "n a", "na", "no", "nil", "nothing",
    "no concern", "no concerns", "no blockers", "not applicable",
}


def _strip_decor(line: str) -> str:
    """Remove list bullets, markdown headings and emphasis from a line."""
    s = line.strip()
    s = re.sub(r"^[-*+][ \t]+", "", s)
    s = re.sub(r"^#{1,6}[ \t]*", "", s)
    return s.strip().strip("*_`").strip()


def _normalise(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace — for negation matching."""
    s = _strip_decor(text)
    s = re.sub(r"[^0-9a-z ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _is_concern_label(head: str) -> bool:
    """True when *head* looks like a concerns section label or heading.

    Matches on CONTAINMENT, not prefix: a real report used the label
    'Working-tree concern:', which a prefix test rejects — wrongly discarding a
    report that did state its concern. Bounded to 60 characters so a prose
    sentence merely mentioning "concerns" is not mistaken for a section label.
    """
    label, sep, _ = head.partition(":")
    target = label if sep else head
    return len(target) <= 60 and bool(_LABEL_WORD.search(target))


def concern_stated(scrape: str) -> bool:
    """True when the report names at least one concern."""
    lines = scrape.splitlines()
    for i, line in enumerate(lines):
        head = _strip_decor(line)
        if not _is_concern_label(head):
            continue
        _, sep, rest = head.partition(":")
        if sep and _normalise(rest):
            return _normalise(rest) not in _NEGATIONS
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            if _SECTION_START.match(nxt.strip()):
                break
            return _normalise(nxt) not in _NEGATIONS
        return False
    return False


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
    parser.add_argument(
        "--after-marker",
        nargs="?",
        const=DISPATCH_BOUNDARY,
        default=None,
        help="Extract only past this marker's last occurrence (fail closed if "
        f"absent). Bare flag uses the default boundary {DISPATCH_BOUNDARY!r} "
        "that `hmad-dispatch send` appends; pass a value to override.",
    )
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

    # Slice once here so both the verdict scan and the concern scan see only the
    # agent's reply, never the echoed prompt above the boundary.
    if args.after_marker is not None:
        try:
            scrape = slice_after_boundary(scrape, args.after_marker)
        except VerdictError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    try:
        value = extract_verdict(scrape, args.key, allowed)
    except VerdictError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Scoped to ONE key and ONE value, so the VERDICT: and ASSESSMENT: contracts
    # cannot become collateral damage. extract_verdict() itself is unchanged: it
    # answers "what is the last value of this key", and widening it to read
    # surrounding prose would make its name a lie.
    if (
        args.key == "STATUS"
        and value == "DONE_WITH_CONCERNS"
        and not concern_stated(scrape)
    ):
        print(
            "ERROR: STATUS: DONE_WITH_CONCERNS but the report names no concern "
            "— re-dispatch, or have the agent report DONE",
            file=sys.stderr,
        )
        return 2

    print(f"{args.key}: {value}")
    if args.feature:
        # J26 — this marker goes to STDERR, unlike every sibling h-mad script,
        # which prints its `[H-MAD]` marker to stdout. That is deliberate, and the
        # inconsistency is the point: the siblings' stdout is a REPORT to be read
        # (`GATE: PASS must=0 should=0`), while this script's stdout is a VALUE to
        # be captured — extracting a verdict for programmatic use is its whole job.
        # On stdout the marker made `V=$(...)` yield two lines, and
        # `h_mad_state_write.py` refused the malformed value; observed live on
        # gate-blindness-hardening's 6a-prime, where the read-back reported `None`.
        print(
            f"[H-MAD] {args.feature} phase{args.phase} {args.key.lower()}_{value}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
