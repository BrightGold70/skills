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
import re
import sys
from pathlib import Path


_AGY_EVENTS = frozenset({"init", "step_update", "result"})


# --- codex text transcripts (#27) ---------------------------------------------
#
# `scan()` reads agy NDJSON and nothing else, so a codex leg's transcript yielded
# no figures at all. #24 (`6f00f8c`) stopped that being reported as a FALSE ZERO;
# it did not make the surface measurable. This does.
#
# The header is codex's own and is what makes the rest a measurement rather than a
# guess about an unknown format.
_CODEX_HEADER_RE = re.compile(r"^OpenAI Codex v", re.M)
# A completed run prints its token total last. It is the COMPLETENESS ANCHOR: a
# transcript without it was truncated (killed, still running, copied mid-write), and
# a truncated transcript's zero is not a zero. This is #24's whole lesson kept
# intact one level down -- "could not measure" and "measured zero" must never take
# the same branch.
_CODEX_TOKENS_RE = re.compile(r"^tokens used$", re.M)
# The PRIMARY instrument. The leading space and the exact phrase make it
# near-impossible in prose, which matters because a codex transcript echoes the
# whole prompt -- and this repo's audit prompts are documents ABOUT running
# commands. Measured on a real transcript: a naive `exited` sweep returned 8 hits,
# every one of them prose from the prompt body.
_CODEX_OUTCOME_RE = re.compile(r"^ (succeeded|failed) in \d+(?:\.\d+)?m?s:", re.M)
# The CROSS-CHECK, deliberately a different instrument rather than a second reading
# of the same one. `^exec$` is one prompt code block away from a false positive, so
# it never overrides the outcome count -- a disagreement is REPORTED as its own
# field. Pairing by adjacency was rejected: the wrapper interleaves `#hmad-beat`
# heartbeat lines into the same file (measured: present in a real transcript), and
# anything positional breaks on them while counting does not.
_CODEX_EXEC_RE = re.compile(r"^exec$", re.M)


def scan_codex_text(log_text: str) -> dict | None:
    """Measure tool activity in a codex TEXT transcript.

    Returns None when this is not a codex transcript at all -- the caller must not
    read that as zero. Returns `complete=False` when the header is there but the
    token-total anchor is not: the run was truncated, and its zero is unjudgeable.
    """
    if not _CODEX_HEADER_RE.search(log_text):
        return None
    complete = bool(_CODEX_TOKENS_RE.search(log_text))
    outcomes = _CODEX_OUTCOME_RE.findall(log_text)
    ok = sum(1 for kind in outcomes if kind == "succeeded")
    failed = sum(1 for kind in outcomes if kind == "failed")
    exec_lines = len(_CODEX_EXEC_RE.findall(log_text))
    return {
        "tools": len(outcomes),
        "ok": ok,
        "failed": failed,
        "exec_lines": exec_lines,
        # Reported, never reconciled by picking a winner. Two instruments that
        # disagree are a fact about the transcript, not a number to average.
        "agrees": exec_lines == len(outcomes),
        "complete": complete,
    }


def scan(log_text: str) -> dict:
    """Count tool events by outcome, and sum reasoning effort. Any tool name counts.

    `thinking` is reported for the same reason `status` is: triage, never a verdict.
    Across the 8 audit passes of cycles 21-24 every substantive finding came from a
    pass with high thinking or ~34 tool calls, while a pass with 0 tool calls
    returned "CLEAN PASS" on a document another pass proved defective (J49). At the
    verdict line a hollow pass and a real clean pass look identical.

    Since #13 it IS a threshold in `h_mad_audit_cycle.combine()`, but in one
    direction only, and the counter-example this paragraph was built on is what
    fixes the direction. A pass that made 2 tool calls honoured the report-file
    delivery contract exactly as asked, and one such pass in this repo
    (5,356 thinking / 2 tools) still returned a REAL FINDING. So the floor is
    checked strictly AFTER the findings loop: a low-evidence pass that found
    something is scored on what it found, exactly as before, and only a
    low-evidence pass claiming a CLEAN is refused. Findings are evidence of
    reading; a clean is not.
    """
    tools = ok = failed = thinking = 0
    agy_events = 0
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
        # Format evidence, counted separately from tool evidence (#154). An agy
        # transcript carries `event` lines (init/step_update/result) — the SAME
        # criterion `hmad-dispatch`'s `_exec_log_format` keys on, and deliberately
        # not wider: a bare `{"step_update": …}` line with no `event` key is what
        # a hand-built fixture emits, never agy, and counting it here while the
        # shell calls the file codex-text would make the two instruments disagree.
        if event.get("event") in _AGY_EVENTS:
            agy_events += 1

        result = event.get("result")
        if isinstance(result, dict) and result.get("status"):
            status = str(result["status"])

        step = event.get("step_update")
        if not isinstance(step, dict):
            continue
        state = str(step.get("state") or "")

        # Reasoning effort rides `agent_response` steps, not tool steps. DONE only,
        # for the same reason tools count outcomes: ACTIVE is the start of the same
        # step and counting both doubles every response's usage.
        if step.get("step_type") == "agent_response":
            if state == "DONE":
                usage = step.get("usage")
                if isinstance(usage, dict):
                    # `thinking_tokens: null` occurs in real logs, and `None + int`
                    # raises -- which would abort the scan and lose the tool counts
                    # too, turning a reported hollow pass into a cannot-judge.
                    value = usage.get("thinking_tokens")
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        thinking += int(value)
            continue

        if step.get("step_type") != "tool":
            continue
        # ACTIVE is the start of a call, DONE/ERROR its outcome. Count outcomes only,
        # or every call is counted twice and a wedged call counts as an attempt.
        if state == "DONE":
            tools += 1
            ok += 1
        elif state == "ERROR":
            tools += 1
            failed += 1
    return {"tools": tools, "ok": ok, "failed": failed,
            "thinking": thinking, "status": status, "agy_events": agy_events}


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
    if counts["agy_events"] == 0:
        # #27. Publish the codex figures on their OWN token, and leave the
        # `EVIDENCE:` line below byte-identical.
        #
        # They deliberately do NOT go on the EVIDENCE line. A consumer globbing
        # `tools=` off that line would pick a codex number up as an agy one, and
        # #24's whole point is that those two zeros mean different things -- the
        # same reason the stamp token is spelled `GATESTAMP:` and not `GATE:`.
        # #24's rule is untouched: a codex leg does not satisfy this gate, the
        # verdict stays `UNREADABLE reason=unsupported_format`, and the rc stays 2.
        # What changes is that the surface is no longer BLIND.
        #
        # Measured on the fixture this shipped with, a real `doc-block-exec`
        # archreview: 0 tools over 196,184 tokens, with `ASSESSMENT: NO` emitted
        # anyway -- its own output saying `The requested view_file tool is
        # unavailable in this session, so I could not inspect the worktree`. A
        # verdict over a tree the leg never read, and nothing could see it.
        codex = scan_codex_text(text)
        if codex is not None:
            if codex["complete"]:
                print(f"CODEXEVIDENCE: tools={codex['tools']} ok={codex['ok']} "
                      f"failed={codex['failed']} exec_lines={codex['exec_lines']} "
                      f"agrees={'yes' if codex['agrees'] else 'no'}")
            else:
                # No trailing token total: killed, still running, or copied
                # mid-write. #24's lesson one level down -- "could not measure" and
                # "measured zero" must never take the same branch, so this
                # publishes NO count at all.
                print("CODEXEVIDENCE: UNREADABLE reason=truncated_no_token_total")
        print(f"ERROR: {path} carries no agy NDJSON event (init/step_update/"
              "result); this gate reads agy transcripts only. Either a codex-text "
              "transcript, or an agy run that died before emitting `init` (the "
              "wrapper's `#hmad-beat` lines alone are not evidence) — neither can "
              "be judged here", file=sys.stderr)
        print("EVIDENCE: UNREADABLE reason=unsupported_format")
        return 2
    verdict = "PASS" if counts["ok"] >= 1 else "NONE"
    line = (
        f"EVIDENCE: {verdict} tools={counts['tools']} "
        f"ok={counts['ok']} failed={counts['failed']} "
        f"thinking={counts['thinking']}"
    )
    if counts["status"]:
        line += f" status={counts['status']}"
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
