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
import math
import re
import shlex
import sys
from pathlib import Path


_AGY_EVENTS = frozenset({"init", "step_update", "result"})
_GROK_TYPES = frozenset({"thought", "text", "available_commands", "tool_call",
                         "tool_call_update", "usage", "end"})
GROK_MAX_DEPTH = 64
CODEX_BANNER_HEAD = 4096


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


def codex_banner_in_head(text: str) -> bool:
    return _CODEX_HEADER_RE.search(text[:CODEX_BANNER_HEAD]) is not None


# --- distinct TARGETS, beside the call count (skill-candidates row 1937) ------
#
# `tools=41` is the same figure whether a pass opened the module under discussion or
# spent every call re-reading documents. This reports WHAT the calls touched: the
# distinct paths their arguments name that EXIST, split into `code` (under the project
# root and not under its docs/ tree) and `other` (docs/, or outside the root), plus
# `unmeasured` -- calls whose targets the transcript does not show. Advisory, never a
# gate: nothing here changes a verdict or an exit code.
#
# Calibrated 2026-10-05 on 12 real pass logs (HemaSuite `preflight-command-aware`,
# plan/design/impl-plan x cycles 1-2 x {agy NDJSON, codex text}):
#   1. agy shows its targets only on `tool` steps: `tool_info.parameters`, where
#      `run_command`.`CommandLine` is SHELL TEXT and the other tools carry path-valued
#      params (`write_to_file`.`TargetFile`). Shell-splitting command lines, splitting
#      again on shell operators, and keeping only tokens that resolve to an EXISTING
#      path gave 0-18 distinct code files per pass -- a real signal, not noise.
#   2. The split is code-vs-other, NOT docs-vs-code as the row first proposed: the
#      docs/ count was 0 in all 12 passes, because the audit assembler INLINES the
#      documents into the prompt, so a leg never opens them. A docs/-vs-code column
#      would have been a constant.
#   3. codex text transcripts print MCP calls as `mcp: <server>/<tool> started` with
#      NO arguments (context-mode ctx_execute/ctx_batch_execute/...: 7-22 per pass).
#      Those are counted `unmeasured`, never silently as zero targets. codex `exec`
#      blocks DO print their command line and are measured.
#
# Tool NAMES are still not known here, for the reason the module docstring gives:
# only parameter KEYS that carry shell text are named, and every other string
# parameter is tried as a whole path. A content parameter (a file body, a search
# string) does not resolve to an existing path, so it falls out on the existence test.
#
# KNOWN UNDERCOUNTS, both reading as measured zeros rather than `unmeasured`: a shell
# `cd` inside one command line is not followed (relative tokens after it resolve
# against the step's cwd), and a path quoted inside an inline script (`python3 -c
# "...open('cli/_main.py')..."`) is one opaque word. The calibration corpus carries 4
# such agy calls; the dominant case is `cd "$(git rev-parse ...)/x"`, whose target no
# static reader can resolve. Read `code=` as a floor, never as an exact count.
_SHELL_TEXT_KEYS = frozenset({"CommandLine", "command"})
_SHELL_WRAPPER_FLAGS = frozenset({"-c", "-lc"})
_CODEX_MCP_RE = re.compile(r"^mcp: \S+ started$", re.M)


def _shell_tokens(text: str) -> list[str]:
    """Words of a shell command, split on whitespace AND on `| & ; < > ( )`."""
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:  # unbalanced quote: fall back to whitespace words
        return [word.strip("'\"") for word in text.split()]  # M:TGT-QUOTEFALLBACK


def _param_candidates(params: dict, cwd: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for key, value in params.items():
        if not isinstance(value, str):
            continue
        if key in _SHELL_TEXT_KEYS:  # M:TGT-SHELLKEY
            out.extend((token, cwd) for token in _shell_tokens(value))
        else:
            out.append((value, cwd))
    return out


def _agy_candidates(log_text: str, root: str) -> tuple[list[tuple[str, str]], int]:
    cwd, candidates, unmeasured = root, [], 0
    for line in log_text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except (RecursionError, TypeError, ValueError):
            continue
        if not isinstance(event, dict):
            continue
        init = event.get("init")
        # A relative or empty cwd would resolve against the SCANNER's own cwd; it is
        # treated as absent, so tokens fall back to the root.
        if (isinstance(init, dict) and isinstance(init.get("cwd"), str)
                and Path(init["cwd"]).is_absolute()):  # M:TGT-AGYCWDABS
            cwd = init["cwd"]  # M:TGT-AGYCWD
        step = event.get("step_update")
        # ACTIVE, the start of each call: it carries the parameters, and one per call
        # (DONE/ERROR repeat them). An ERRORed call still names what it tried.
        if not (isinstance(step, dict) and step.get("step_type") == "tool"
                and step.get("state") == "ACTIVE"):  # M:TGT-ACTIVE
            continue
        info = step.get("tool_info")
        params = info.get("parameters") if isinstance(info, dict) else None
        if not isinstance(params, dict):
            unmeasured += 1  # M:TGT-AGYHIDDEN
            continue
        candidates.extend(_param_candidates(params, cwd))
    return candidates, unmeasured


def _grok_candidates(log_text: str, root: str) -> tuple[list[tuple[str, str]], int]:
    # A grok stream carries no cwd of its own, so relative tokens resolve against the
    # root. `rawInput` is grok's argument object (`read_file`.`target_file` in the
    # committed fixture); `run_terminal_command`.`command` is assumed shell text by the
    # same key rule as agy, and is not calibrated against a real grok run.
    candidates, unmeasured = [], 0
    for line in log_text.split("\n"):
        try:
            event = json.loads(line)
        except (RecursionError, ValueError):
            continue
        if not isinstance(event, dict) or event.get("type") != "tool_call":
            continue
        if _json_deeper_than(event, bound=GROK_MAX_DEPTH):
            continue
        raw = event.get("rawInput")
        if not isinstance(raw, dict):
            unmeasured += 1  # M:TGT-GROKHIDDEN
            continue
        candidates.extend(_param_candidates(raw, root))
    return candidates, unmeasured


def _codex_candidates(log_text: str, root: str) -> tuple[list[tuple[str, str]], int]:
    # An `exec` block is `exec`, then the command line(s) ending ` in <cwd>`, then
    # (usually) the outcome line. The command and its cwd are what is measured, so a
    # block is read up to its outcome OR the next `exec` -- codex prints two headers
    # back to back when calls overlap, and the first command is still fully visible.
    # codex interleaves `hook: ...` lines inside a block; they are not part of the
    # command, and left in they ran on into the cwd and turned a visible read into a
    # silent zero (review M1, design_cycle2_p2:4601). A block whose text does not end
    # in a single-line ` in /<cwd>` is not a parseable call: unmeasured, not dropped.
    # Every block names its own cwd, so `root` is not needed here.
    unmeasured = len(_CODEX_MCP_RE.findall(log_text))  # M:TGT-MCP
    candidates: list[tuple[str, str]] = []
    lines = log_text.split("\n")
    i = 0
    while i < len(lines):
        if lines[i] != "exec":
            i += 1
            continue
        j, body = i + 1, []
        while j < len(lines) and lines[j] != "exec" and not _CODEX_OUTCOME_RE.match(lines[j]):
            if not lines[j].startswith("hook: "):  # M:TGT-HOOKLINE
                body.append(lines[j])
            j += 1
        i = j
        head, sep, tail = "\n".join(body).rpartition(" in ")
        if not (sep and tail.startswith("/") and "\n" not in tail):  # M:TGT-EXECPARSE
            unmeasured += 1  # M:TGT-EXECORPHAN
            continue
        words = _shell_tokens(head)
        if len(words) >= 3 and words[1] in _SHELL_WRAPPER_FLAGS:
            words = _shell_tokens(words[2])  # `/bin/zsh -lc '<the real command>'`
        candidates.extend((word, tail) for word in words)  # M:TGT-EXECCWD
    return candidates, unmeasured


_CANDIDATES = {"agy": _agy_candidates, "grok": _grok_candidates, "codex": _codex_candidates}


def measure_targets(log_text: str, root: Path | str | None, fmt: str) -> dict | None:
    """Distinct existing targets one pass's tool calls named, for `fmt` in agy/grok/codex.

    Returns None when there is no project root to measure against (or it is not a
    directory): absent means "not measured", never zero. Otherwise
    `{"paths", "code", "other", "unmeasured"}` with `paths == code + other`. A target
    is an existing regular file or directory (so `/dev/null` is not one), counted once
    however many calls or spellings reach it. The root and its ANCESTORS (`..`, `/`,
    `~`) name no part of the tree and are not targets. `other` still carries delivery
    mechanics -- the pass's own report file and its `.done` marker, interpreter
    binaries -- so `code=` is the figure that answers "did it open the code".
    Pure apart from the existence checks it is defined by.
    """
    if root is None or not Path(root).is_dir():  # M:TGT-NOROOT
        return None
    base = Path(root).resolve()
    candidates, unmeasured = _CANDIDATES[fmt](log_text, str(base))
    seen: set[Path] = set()
    for token, cwd in candidates:
        if not token:
            continue
        try:
            path = Path(token).expanduser()
            if not path.is_absolute():
                path = Path(cwd) / path  # M:TGT-RELCWD
            if not (path.is_file() or path.is_dir()):  # M:TGT-EXISTS
                continue
            path = path.resolve()  # M:TGT-DEDUP: one spelling per target
        except (OSError, ValueError, RuntimeError):
            continue
        if not base.is_relative_to(path):  # M:TGT-ROOTSELF
            seen.add(path)
    code = sum(1 for path in seen
               if path.is_relative_to(base)
               and path.relative_to(base).parts[0] != "docs")  # M:TGT-DOCS
    return {"paths": len(seen), "code": code, "other": len(seen) - code,
            "unmeasured": unmeasured}


def format_targets(counts: dict) -> str:
    """The ` paths=N code=C other=O unmeasured=U` suffix, or "" when not measured."""
    targets = counts.get("targets")
    if not isinstance(targets, dict):
        return ""  # M:TGT-FMTABSENT
    return (f" paths={targets['paths']} code={targets['code']} "
            f"other={targets['other']} unmeasured={targets['unmeasured']}")


def scan_codex_text(log_text: str, root: Path | str | None = None) -> dict | None:
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
    result = {
        "tools": len(outcomes),
        "ok": ok,
        "failed": failed,
        "exec_lines": exec_lines,
        # Reported, never reconciled by picking a winner. Two instruments that
        # disagree are a fact about the transcript, not a number to average.
        "agrees": exec_lines == len(outcomes),
        "complete": complete,
    }
    targets = measure_targets(log_text, root, "codex")
    if targets is not None:
        result["targets"] = targets
    return result


def _json_deeper_than(value: object, bound: int) -> bool:
    stack = [(value, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > bound:
            return True
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)
    return False


def scan_grok(log_text: str, root: Path | str | None = None) -> dict | None:
    seen = False
    tools: set = set()
    ok: set = set()
    thinking = 0
    complete = False
    stop_reason = None
    for line in log_text.split("\n"):
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if not isinstance(event, dict):
            continue
        if _json_deeper_than(event, GROK_MAX_DEPTH):
            continue
        t = event.get("type")
        if not (isinstance(t, str) and t in _GROK_TYPES):
            continue
        seen = True
        call_id = event.get("toolCallId")
        if t in ("tool_call", "tool_call_update") and isinstance(call_id, str):
            tools.add(call_id)
        if t == "tool_call_update" and event.get("status") == "completed" and isinstance(call_id, str):
            ok.add(call_id)
        if t == "usage":
            usage = event.get("usage")
            value = usage.get("reasoning_tokens") if isinstance(usage, dict) else None
            if type(value) in (int, float) and (not isinstance(value, float) or math.isfinite(value)):
                thinking += int(value)
        if t == "end":
            complete = True
            reason = event.get("stopReason")
            stop_reason = reason if isinstance(reason, str) else None
    if not seen:
        return None
    result = {"tools": len(tools), "ok": len(ok), "unresolved": len(tools) - len(ok),
              "thinking": thinking, "complete": complete, "stop_reason": stop_reason}
    targets = measure_targets(log_text, root, "grok")
    if targets is not None:
        result["targets"] = targets
    return result


def scan(log_text: str, root: Path | str | None = None) -> dict:
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
        except (ValueError, TypeError, RecursionError):
            continue
        if not isinstance(event, dict):
            continue
        # Format evidence, counted separately from tool evidence (#154). An agy
        # transcript carries `event` lines (init/step_update/result) — the SAME
        # criterion `hmad-dispatch`'s `_exec_log_format` keys on, and deliberately
        # not wider: a bare `{"step_update": …}` line with no `event` key is what
        # a hand-built fixture emits, never agy, and counting it here while the
        # shell calls the file codex-text would make the two instruments disagree.
        event_name = event.get("event")
        if isinstance(event_name, str) and event_name in _AGY_EVENTS:
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
                    if (isinstance(value, (int, float)) and not isinstance(value, bool)
                            and (not isinstance(value, float) or math.isfinite(value))):
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
    result = {"tools": tools, "ok": ok, "failed": failed,
              "thinking": thinking, "status": status, "agy_events": agy_events}
    # With a project root, WHAT the calls touched rides beside how many there were
    # (row 1937). Without one the key is absent -- not measured, never zero.
    targets = measure_targets(log_text, root, "agy")
    if targets is not None:
        result["targets"] = targets
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", help="the dispatch's --log transcript (agy NDJSON or grok streaming-json)")
    ap.add_argument("--project-root", type=Path, default=None,
                    help="measure distinct targets against this root and print "
                         "paths=/code=/other=/unmeasured= (advisory; absent when not given)")
    args = ap.parse_args(argv)
    root = args.project_root
    if root is not None and not root.is_dir():
        # Not a zero and not silent: the fields are absent, and this says why.
        print(f"WARNING: --project-root {root} is not a directory; targets not "
              "measured", file=sys.stderr)  # M:TGT-ROOTWARN

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

    counts = scan(text, root=root)
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
        grok = None if codex_banner_in_head(text) else scan_grok(text, root=root)
        if grok is not None:
            if not grok["complete"]:
                print(f"ERROR: {path} is a grok stream with no `end` event (killed, still "
                      "running, or copied mid-write) — no counts published", file=sys.stderr)
                print("EVIDENCE: UNREADABLE reason=truncated_no_end")
                return 2
            verdict = "PASS" if grok["ok"] >= 1 else "NONE"
            line = (f"EVIDENCE: {verdict} tools={grok['tools']} ok={grok['ok']} "
                    f"unresolved={grok['unresolved']} thinking={grok['thinking']} format=grok")
            if grok["stop_reason"]:
                line += f" stop_reason={grok['stop_reason']}"
            print(line + format_targets(grok))
            return 0
        codex = scan_codex_text(text, root=root)
        if codex is not None:
            if codex["complete"]:
                print(f"CODEXEVIDENCE: tools={codex['tools']} ok={codex['ok']} "
                      f"failed={codex['failed']} exec_lines={codex['exec_lines']} "
                      f"agrees={'yes' if codex['agrees'] else 'no'}" + format_targets(codex))
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
    # Appended LAST rather than between `tools=` and `ok=`: consumers and tests match
    # the `tools=N ok=K failed=J` run as a prefix, and an advisory field must not
    # move a gate's tokens.
    print(line + format_targets(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
