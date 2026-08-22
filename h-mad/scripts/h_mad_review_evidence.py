#!/usr/bin/env python3
"""Did a headless agy review actually READ anything before it judged?

Measured 2026-08-22 on a real Phase 6a-prime dispatch: the review made exactly one
tool call, a `view_file`; it errored; the run's result carried `status: "ERROR"`; and
the response was 1510 bytes of confident prose asserting "No Critical or Important
issues were found" about files it had never opened. `exec` returned rc 0,
`h_mad_extract_verdict.py` returned `ASSESSMENT: READY_TO_MERGE`, and the Phase-7
gate accepted it. Every signal in the chain was well-formed. The evidence under the
verdict did not exist.

`h_mad_extract_verdict.py` already closes the case where an agent says *nothing* --
silence must not read as approval. This closes the case one level up: a **fluent**
answer with nothing beneath it, which is strictly harder to spot because it reads
like a review.

Three things this deliberately does NOT do:

  1. **It does not gate on `result.status`.** `hmad-dispatch`'s `_agy_ndjson_response`
     ignores `.status` on purpose, and its reasoning is sound: a single denied tool
     call yields `status: ERROR` alongside a complete, correct answer, so refusing
     that response would manufacture a `no_verdict` halt out of a run that answered.
     One errored call out of many, and one out of one, are indistinguishable at the
     transport -- only the consumer knows which it needed. Status is reported here
     for triage and never decides.
  2. **It does not know any tool names.** The first probe of this very defect
     hardcoded `view_file|grep_search` from a previous dispatch and reported a false
     zero when agy switched to `run_command`. Any tool reaching DONE is evidence.
  3. **It does not read the report.** Whether the findings are correct is the
     reviewer's job and the operator's; this answers only "was anything looked at".
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def scan(log_text: str) -> dict:
    """Count tool events by outcome. Any tool name counts; none is special."""
    tools = ok = failed = 0
    status: str | None = None
    for line in log_text.splitlines():
        line = line.strip()
        # The transcript legitimately carries non-JSON: `#hmad-beat` heartbeat lines
        # and any content a caller left in an appended --log.
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(event, dict):
            continue

        result = event.get("result")
        if isinstance(result, dict) and result.get("status"):
            status = str(result["status"])

        step = event.get("step_update")
        if not isinstance(step, dict) or step.get("step_type") != "tool":
            continue
        state = str(step.get("state") or "")
        # ACTIVE is the start of a call, DONE/ERROR its outcome. Count outcomes only,
        # or every call is counted twice and a wedged call counts as an attempt.
        if state == "DONE":
            tools += 1
            ok += 1
        elif state == "ERROR":
            tools += 1
            failed += 1
    return {"tools": tools, "ok": ok, "failed": failed, "status": status}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", help="the dispatch's --log transcript (agy NDJSON)")
    args = ap.parse_args(argv)

    path = Path(args.log)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        # No counts on a cannot-judge, so it can never be read as a zero. "I could
        # not look" and "I looked and found nothing" are opposite facts.
        print("EVIDENCE: UNREADABLE reason=no_log")
        return 2
    if not text.strip():
        print(f"ERROR: empty transcript {path}", file=sys.stderr)
        print("EVIDENCE: UNREADABLE reason=empty_log")
        return 2

    counts = scan(text)
    verdict = "PASS" if counts["ok"] >= 1 else "NONE"
    line = (
        f"EVIDENCE: {verdict} tools={counts['tools']} "
        f"ok={counts['ok']} failed={counts['failed']}"
    )
    if counts["status"]:
        line += f" status={counts['status']}"
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
