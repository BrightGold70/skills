#!/usr/bin/env python3
"""h_mad_archreview_cycle.py — one Phase-6a-prime cycle, staged and scored.

`audit-cycle` exists for plan/design/impl-plan; 6a-prime had no equivalent, so its
seven mechanical steps were hand-assembled seven times in one session (and once
more while closing J43). Every step is already prescribed by SKILL.md. Two of them
have no other home, and those two are the ones that get skipped:

  * **the BASE/HEAD stamp** — a stale sha silently reviews the PREVIOUS commit and
    comes back clean. That is the J41 failure one level up: `git merge-base`
    returns 5c's parent, and nothing about the result looks wrong.
  * **the evidence gate** — `EVIDENCE: PASS tools=N` is the only thing separating a
    review that read from one that only sounds like it did. Measured: a dispatch
    whose single `view_file` errored returned `READY_TO_MERGE` in 1510 confident
    bytes, and rc, the extractor and the Phase-7 gate all took it.

Deliberately NOT built on `audit-cycle`, though the candidate row asked for "an
audit-cycle for the architectural gate". That tool is a multi-pass verdict
COMBINER: it takes `--pass` specs of runs that already finished, fans out N
parallel passes, and rejects any phase outside plan/design/impl-plan. 6a-prime is
ONE reviewer re-run sequentially after fixes, emitting a word rather than finding
counts. Same name, different machine — building it as a variant would have meant
widening a phase whitelist, swapping the assembler and replacing the verdict model.

**One cycle per invocation. It does not decide whether to run another.** That
judgement is the operator's, and it is the reason this is a driver and not a loop:
the seven-cycle run went to seven because cycle 3 came back clean and cycle 4 then
found a Critical vacuous pass. A loop-until-clean driver stops at three.

Two verbs, split where `h_mad_assemble_tdd.py` splits — the dispatch is the
side-effecting, agy-dependent, minutes-long part, while assembly and scoring are
pure. Both skip-prone steps land in the tested halves.

    stage  — substitute the template, refuse a degenerate range, write the prompt,
             print the exact `exec agy` command (with `--log`, which `score` needs)
    score  — evidence gate FIRST, then verdict, then record, then READ BACK

Verdicts, printed as a canonical token:

    ARCHREVIEW: STAGED prompt=<p> base=<b> head=<h> bytes=N          exit 0
    ARCHREVIEW: READY_TO_MERGE|WITH_FIXES|NO tools=N recorded=yes    exit 0
    ARCHREVIEW: OVERSIZE chars=N limit=M headroom=K                  exit 2
    ARCHREVIEW: NO_EVIDENCE tools=0                                  exit 2
    ARCHREVIEW: LOW_EVIDENCE_CLEAN tools=N floor=M                   exit 2
    ARCHREVIEW: NO_VERDICT tools=N                                   exit 2
    ARCHREVIEW: NOT_RECORDED verdict=<v>                             exit 2
    ARCHREVIEW: UNSUBSTITUTED slots=<a,b>                            exit 2
    ARCHREVIEW: DEGENERATE_RANGE base=<b>                            exit 2
    ARCHREVIEW: UNREADABLE reason=<r>                                exit 2
      (r ∈ review:<exc>, no_log, empty_log, unsupported_format — the last is a
       codex-text transcript, which this gate cannot read; never `tools=0`, #154)

The gate ORDER is the contract: evidence before verdict, always. A review that
read nothing has no verdict to record, whatever its last line says — recording it
is precisely what let the 1510-byte defect survive. So `NO_EVIDENCE`,
`LOW_EVIDENCE_CLEAN` and `NO_VERDICT` write nothing, and none carries a verdict
word.

`LOW_EVIDENCE_CLEAN` is `NO_EVIDENCE` at the floor this channel's contract sets
rather than at zero (`DELIVERY_FLOOR`), and it is asymmetric on purpose: only
READY_TO_MERGE is held to it, because findings are evidence of reading and a clean
is not. `OVERSIZE` is the staging-side sibling — a prompt no delivery surface
accepts, refused before it is written rather than after a surface rejects it.

`NOT_RECORDED` exists because `archreview` is **not** in the schema's `required`
array: strict validation passes over a write that never landed, so the read-back
is the only thing that can catch a dropped write. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TOKEN = "ARCHREVIEW:"
SCRIPTS = Path(__file__).resolve().parent
ALLOWED = ("READY_TO_MERGE", "WITH_FIXES", "NO")

# What this channel's own output contract costs in successful tool calls. ONE, not
# the audit path's two: `agy-architectural-reviewer-prompt.md` says "you must also
# WRITE your report file with `run_command`. That is the only write you may make",
# and it asks for no `.done` marker -- so a 6a-prime reviewer that read nothing and
# merely obeyed the delivery instruction scores exactly `tools=1`.
#
# The gate here was `tools == 0`, i.e. a floor of zero, while `h_mad_audit_cycle`
# has carried `DELIVERY_FLOOR = 2` for the same J49 failure -- cycle 24
# double-cleaned on delivery calls alone with no reads. Same defect, one channel
# guarded and the other not; this closes the asymmetry rather than re-deriving it.
#
# Derived from the CONTRACT, never from tool names, and NOT by discounting the
# report path inside `h_mad_review_evidence.scan`. That scanner knows no tool names
# on purpose: the first probe of this defect hardcoded `view_file|grep_search` and
# reported a false zero the moment agy switched to `run_command`. Classifying calls
# as reads-vs-writes there would re-create it, which is why the fix lives here --
# beside the contract that sets the number -- and not one file over.
DELIVERY_FLOOR = 1
_PLACEHOLDER = re.compile(r"<INLINE_[A-Z_0-9]+>")


def _emit(line: str) -> None:
    print(f"{TOKEN} {line}")


def _evidence_counts(log_text: str) -> dict:
    """Delegate the evidence count to the gate that owns it.

    Imported rather than re-counted: a second copy of "what counts as a tool call
    that reached DONE" is a second thing to drift, and the first probe of that
    defect hardcoded tool NAMES from an earlier dispatch and reported a false zero
    when agy switched to `run_command`.
    """
    sys.path.insert(0, str(SCRIPTS))
    from h_mad_review_evidence import scan

    return scan(log_text)


# 6a-prime is an agy-only channel, and agy receives the prompt as ONE argv
# element: `hmad-dispatch.sh:2944` does `args+=(--print "$prompt")` after reading
# the bounded prompt file with `$(cat …)`. So the ceiling here is `ARG_MAX`, which
# is NOT the character limit codex enforces on stdin. Two differences, and each
# one alone makes a char-count gate wrong in the permissive direction:
#
#   * ARG_MAX is a BYTE budget. A prompt of N characters costs more than N bytes
#     the moment it contains anything non-ASCII, and the design documents this
#     channel inlines measure 1.004-1.010 bytes/char in this repo.
#   * The kernel shares that one budget between argv AND envp. The environment is
#     not ours and not fixed: measured 9,586 bytes in this session's shell, and it
#     can be larger in the shell that later runs the dispatch.
#
# Measured on this machine (`getconf ARG_MAX` = 1048576, env 9,586 B): an argv
# payload of 1,048,512 bytes -- exactly what a `chars + 64 > 1048576` gate blesses
# -- fails with `OSError 7 Argument list too long`, while 1,037,859 B succeeds. So
# the char gate opened a ~10 KB window of prompts it called deliverable and no
# surface accepts, which is the very symptom the halt exists to remove.
#
# Derived at RUNTIME, not as a second hardcoded constant: the first one drifted
# precisely because it was a number rather than a measurement, and the env size is
# the operator's, not ours.
ENV_GROWTH_HEADROOM_BYTES = 8 * 1024
# `agy --dangerously-skip-permissions [--model X] [--effort X] [--sandbox]
# [--print-timeout Ns] --output-format stream-json --print` plus the binary path,
# plus the per-entry pointer the kernel charges for every argv and envp slot.
ARGV_SIBLING_RESERVE_BYTES = 4 * 1024


def _argv_budget() -> "tuple[int, int]":
    """`(budget, reserve)` in BYTES for a prompt delivered as one argv element."""
    sys.path.insert(0, str(SCRIPTS))
    from h_mad_assemble_audit import DISPATCH_OVERHEAD_CHARS

    try:
        arg_max = os.sysconf("SC_ARG_MAX")
    except (ValueError, OSError, AttributeError):
        # Only as a floor, and deliberately the POSIX-documented macOS/Linux
        # figure rather than something smaller: a wrong guess here is a refusal,
        # not a silent oversize, because the reserve is subtracted from it.
        arg_max = 1_048_576
    env_bytes = sum(len(k) + len(v) + 2 for k, v in os.environ.items())
    reserve = (env_bytes + ENV_GROWTH_HEADROOM_BYTES
               + ARGV_SIBLING_RESERVE_BYTES + DISPATCH_OVERHEAD_CHARS)
    return arg_max - reserve, reserve


def _size_gate(body: str) -> "tuple[bool, int, int, int]":
    """`(oversize, bytes, budget, reserve)` for THIS channel's delivery surface.

    Takes the text rather than a length so the caller cannot hand it the wrong
    unit -- which is exactly how the first version of this gate was wrong.

    Deliberately NOT `h_mad_assemble_audit.prompt_oversize`. That function is
    correct for the surface it guards (codex `exec` counts CHARACTERS on stdin and
    answers `input_too_large max_chars=1048576`) and reusing it here looked like
    the right kind of reuse -- one measured figure, one owner. It was not: the two
    channels have different limits in different units, and sharing the constant
    silently imported codex's units into an argv path. The assembler's check stays
    unchanged for the assembler's surface.
    """
    budget, reserve = _argv_budget()
    size = len(body.encode("utf-8"))
    return size > budget, size, budget, reserve


def _size_notes(size: int, text: str) -> list[str]:
    """The WARN tier below the refusal: an Agent-tool leg dies well before a CLI does.

    Same delegation, same reason. A 740 KB prompt killed an in-process Opus leg
    with "Prompt is too long" while both CLIs took it, so this is advice printed
    beside a PASS, never a blocker -- and it carries the prompt's region layout so
    a windowed leg can be briefed by line range instead of by feel.
    """
    sys.path.insert(0, str(SCRIPTS))
    from h_mad_assemble_audit import size_notes

    return size_notes(size, text)


def _trim_vh(text: str, keep: int | None, *, ref: str) -> str:
    """Keep only the last `keep` `## Version History` entries of an inlined doc.

    The remedy the oversize halt points at, so it has to exist HERE too: a halt
    whose prescribed escape hatch is unimplemented in the channel that halts is a
    wall. Version History measured ~36% of every doc-block-exec document, it is a
    dated record rather than the review's subject, and `keep=None` is a strict
    no-op so existing callers and prompt hashes are unaffected.

    Reaches for the assembler's private helper deliberately: copying 20 lines of
    entry-splitting here is the "fix one member of the class" failure -- the note
    it writes tells the reviewer how to get the omitted entries back, and two
    copies of that sentence drift apart silently.
    """
    sys.path.insert(0, str(SCRIPTS))
    from h_mad_assemble_audit import _trim_version_history

    return _trim_version_history(text, keep, ref=ref)


def _extract_assessment(text: str) -> str | None:
    """The LAST `ASSESSMENT:` whose value is one of the allowed words.

    Last, on the same rule as every other extractor here: a review carries the
    prompt's own instruction ("return ASSESSMENT: NO if your reads fail") before it
    carries the answer, so a first-match read returns the echo.
    """
    matches = re.findall(r"^[ \t]*ASSESSMENT:[ \t]*(\S+)", text, re.MULTILINE)
    for value in reversed(matches):
        if value in ALLOWED:
            return value
    return None


def _read_report_channel(report_path: Path | None) -> "tuple[str | None, str]":
    """Return `(text, channel)` for the report-file channel, or `(None, reason)`.

    The file EXISTING is not evidence it was written: an agent that created it and
    then produced nothing is the commonest partial failure, and an empty file read
    as authoritative turns that into `NO_VERDICT` while a perfectly good verdict sat
    in the last message. So empty routes to the fallback, exactly as absent does.

    NON-EMPTY is not evidence either, and that gap widened the moment the file
    started winning over an unreadable review: a write killed part-way leaves real
    prose with no verdict line, and preferring it DISCARDS a last message that may
    carry one. So the file wins on carrying a usable verdict, not on carrying bytes
    — which is what "the file WINS when it has content" was always reaching for.

    Deliberately NOT the audit path's third gate. `h_mad_audit_cycle._has_complete_report`
    adds `_done_path(...).exists()`, and copying it here would break this channel
    outright: neither `agy-architectural-reviewer-prompt.md` nor the head contract
    `stage()` injects ever asks the reviewer to create a `.done` marker (only the
    codex VERIFIER template does). Requiring one would send every report to the
    fallback and undo the channel. Same concern, different surface, different gate.
    """
    if report_path is None:
        return None, "not_requested"
    try:
        text = report_path.read_text(encoding="utf-8")
    except OSError:
        return None, "unreadable"
    if not text.strip():
        return None, "empty"
    if _extract_assessment(text) is None:
        # Falls back rather than failing: the last message is the channel this
        # exists to rescue, and it may hold the verdict this file lost.
        return None, "no_verdict_in_file"
    return text, "report-file"


def score(feature: str, state_file: Path, log_path: Path, review_path: Path,
          session_id: str | None = None, report_path: Path | None = None) -> int:
    # The report-file channel (#31). 6a-prime was the only `exec agy` path whose
    # deliverable rode the agent's LAST MESSAGE alone, and every observed failure
    # was a last-message failure — four dispatches, four NO_VERDICT, all four
    # having demonstrably read the tree.
    #
    # The file WINS when it has content: if the two disagree, the last message is
    # the unreliable surface and preferring it would buy nothing. The fallback is
    # NAMED in the emitted token rather than taken silently, because a verdict
    # recovered from the last message and one read from the file are different
    # evidence and must not print the same way.
    #
    # READ FIRST, and the order is the whole point. This used to read `--review`
    # up front and `return 2` on OSError, so an ABSENT `--out` refused the cycle
    # while a good report file sat unread — and an EMPTY `--out` succeeded on the
    # same report. Two spellings of "the last message carried nothing", opposite
    # outcomes. The absent case is not exotic: `exec` writes `--out` atomically
    # and the J29 clobber guard PRESERVES a stale file rather than removing it, so
    # reaching it takes a dispatch killed before `_write_out_atomic` ran — a
    # timeout — with the agent's report already on disk. That is precisely the
    # last-message failure this channel exists to rescue, refused at the door.
    report_text, channel = _read_report_channel(report_path)
    if report_text is not None:
        review = report_text
    else:
        # No usable file, so the last message is all there is — and only NOW is it
        # fatal that it cannot be read.
        channel = "last-message"
        try:
            review = review_path.read_text(encoding="utf-8")
        except OSError as exc:
            _emit(f"UNREADABLE reason=review:{exc.__class__.__name__}")
            return 2
    if not log_path.is_file():
        _emit("UNREADABLE reason=no_log")
        print("  no dispatch log, so whether the review read anything is unknown — "
              "that is a cannot-judge, not a verdict about the review.")
        return 2

    # Evidence FIRST. A review that read nothing has no verdict to record, whatever
    # its last line says. But a transcript this gate cannot READ is a cannot-judge,
    # not a zero (#154): an empty log, or a codex-text one, carries no counts.
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _emit(f"UNREADABLE reason=log:{exc.__class__.__name__}")
        print("  the dispatch log could not be read, so whether the review read "
              "anything is unknown — a cannot-judge, not a verdict about the review.")
        return 2
    counts = _evidence_counts(log_text)
    if not log_text.strip():
        _emit("UNREADABLE reason=empty_log")
        print("  the dispatch log is empty, so whether the review read anything is "
              "unknown — a cannot-judge, not a verdict about the review.")
        return 2
    if counts.get("agy_events", 0) == 0:
        _emit("UNREADABLE reason=unsupported_format")
        print("  the dispatch log carries no agy NDJSON event; this gate reads agy "
              "transcripts only. A codex-text review cannot be judged here and does "
              "not satisfy the 6a-prime evidence gate — this is not `tools=0`.")
        return 2
    tools = int(counts.get("ok", 0))
    if tools == 0:
        _emit("NO_EVIDENCE tools=0")
        print("  the reviewer judged without reading anything → halt "
              "`step6a-prime:review_read_nothing`. Do NOT record the ASSESSMENT; "
              "fix the prompt and re-dispatch.")
        return 2

    verdict = _extract_assessment(review)
    if verdict is None:
        _emit(f"NO_VERDICT tools={tools}")
        print("  no ASSESSMENT: line carrying an allowed word → halt "
              "`step6a-prime:no_verdict`. An empty review must never read as "
              "READY_TO_MERGE.")
        return 2

    # Checked AFTER the verdict is extracted, and only against the CLEAN one. The
    # asymmetry is the whole point and it is `h_mad_audit_cycle.combine`'s: findings
    # are evidence of reading, a clean is not. A reviewer that made one call and
    # still came back with WITH_FIXES or NO is scored on what it found, exactly as
    # before -- a pass in this repo with 2 tool calls returned a real finding. Only
    # a READY_TO_MERGE resting on no more calls than the delivery contract itself
    # costs is refused, because that is indistinguishable from a hollow pass and it
    # is the one direction that lets a defect through the Phase-7 gate.
    if verdict == "READY_TO_MERGE" and tools <= DELIVERY_FLOOR:
        _emit(f"LOW_EVIDENCE_CLEAN tools={tools} floor={DELIVERY_FLOOR}")
        print(f"  READY_TO_MERGE on {tools} successful call(s) — at or below the "
              f"{DELIVERY_FLOOR} this channel's report-file contract costs by itself, "
              "so the reviewer may have read nothing and a clean verdict cannot be "
              "distinguished from a hollow one → halt "
              "`step6a-prime:review_read_nothing`. Do NOT record the ASSESSMENT; "
              "fix the prompt and re-dispatch. A WITH_FIXES or NO at the same count "
              "is recorded, because findings are evidence of reading and a clean "
              "is not.")
        return 2

    writer = SCRIPTS / "h_mad_state_write.py"
    # `--session-id` when the caller has one: this is a phase write by the owner,
    # and the owner's `--set` is what refreshes the heartbeat (#126). Without it
    # the write still lands; only the beat is skipped.
    argv = [sys.executable, str(writer), str(state_file), "--feature", feature,
            "--set", f"archreview={verdict}"]
    if session_id:
        argv += ["--session-id", session_id]
    subprocess.run(argv, capture_output=True, text=True)
    # Read back, always. `archreview` is not in the schema's `required` array, so a
    # dropped write still reports STATE: PASS — the comparison is the only check.
    try:
        record = json.loads(state_file.read_text(encoding="utf-8"))
        stored = record["orchestrator_state"][feature].get("archreview")
    except (OSError, ValueError, KeyError):
        stored = None
    if stored != verdict:
        _emit(f"NOT_RECORDED verdict={verdict}")
        print(f"  wrote {verdict!r} but read back {stored!r} — the write did not "
              "land. Strict validation cannot see this.")
        return 2

    _emit(f"{verdict} tools={tools} recorded=yes channel={channel}")
    if verdict != "READY_TO_MERGE":
        print("  halt `step6a-prime:architectural_review_failed` — surface the "
              "findings, fix, and re-run ONE more cycle.")
    print(f"[H-MAD] archreview {verdict}")
    return 0


def _resolve_summary(summary: str) -> "tuple[str, str | None]":
    """Return ``(text, error)`` for a --summary that may be a path OR literal prose.

    `--design` is `type=Path` and is read; `--summary` was a bare string
    substituted verbatim, so `--summary /tmp/phase5.md` sent the reviewer a
    filename (J31). Accept both shapes rather than breaking callers that pass
    the summary inline:

      * an existing file            -> its contents
      * path-SHAPED but missing     -> an error, never pasted verbatim
      * anything else               -> the literal string

    "Path-shaped" is deliberately narrow — a single line, no blank space around
    a separator, or a document suffix. Real inline summaries are prose with
    spaces and usually newlines, so they do not collide.
    """
    if not summary or "\n" in summary:
        return summary, None
    candidate = Path(summary).expanduser()
    try:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8"), None
    except OSError as exc:
        return summary, exc.__class__.__name__
    looks_like_path = (
        " " not in summary
        and ("/" in summary or candidate.suffix.lower() in (".md", ".txt", ".log"))
    )
    if looks_like_path:
        return summary, f"no such file: {summary}"
    return summary, None


def stage(feature: str, template: Path, base: str, head: str, design: Path,
          diff_files: str, summary: str, prompt: Path,
          report_file: str | None = None, vh_tail: int | None = None) -> int:
    if base == head:
        _emit(f"DEGENERATE_RANGE base={base}")
        print("  BASE and HEAD are the same commit, so the diff is empty and the "
              "review would come back clean having examined nothing.")
        return 2
    try:
        body = template.read_text(encoding="utf-8")
        design_text = design.read_text(encoding="utf-8")
    except OSError as exc:
        _emit(f"UNREADABLE reason={exc.__class__.__name__}")
        return 2

    # Before substitution, so the size gate below measures what the reviewer will
    # actually receive. `ref` is what the omission note tells the reviewer to run
    # `git show <sha>:<ref>` on, so it must be the design's path as the repo knows
    # it, not a temp path -- relative to the repo root when it is inside one.
    try:
        ref = str(design.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        ref = design.name
    design_text = _trim_vh(design_text, vh_tail, ref=ref)

    # J31: --summary took a literal string while --design read a file, so an
    # operator who wrote the Phase-5 summary to a file and passed its path got
    # the PATH substituted into the prompt. Staging still said STAGED, and two
    # architectural review legs ran without the context they were handed. The
    # tell was byte length: two different summary files produced prompts of
    # identical size, both holding a path of equal length.
    summary_text, err = _resolve_summary(summary)
    if err is not None:
        _emit(f"UNREADABLE_SUMMARY reason={err}")
        print("  --summary looks like a path but does not resolve; pasting it "
              "verbatim would send the reviewer a filename instead of the summary.")
        return 2

    pairs = (
        ("<INLINE_FEATURE>", feature),
        ("<INLINE_BASE_SHA>", base),
        ("<INLINE_HEAD_SHA>", head),
        ("<INLINE_DIFF_FILES>", diff_files),
        ("<INLINE_AUDITED_DESIGN>", design_text),
        ("<INLINE_PHASE_5_SUMMARY>", summary_text),
    )

    # `<INLINE_REPORT_FILE>`, NOT `<REPORT_FILE_PATH>`: `_PLACEHOLDER` matches
    # `<INLINE_[A-Z_0-9]+>` only, so a slot outside that grammar inherits NEITHER
    # the UNSUBSTITUTED nor the MISSING_SLOTS guard, and a template that failed to
    # substitute it would ship a live placeholder reading as real prose.
    #
    # OPTIONAL rather than required, and the two existing guards then cover both
    # directions without a third rule: a template carrying the slot with no
    # --report-file leaves it unfilled and trips UNSUBSTITUTED, while --report-file
    # against a template without the slot trips MISSING_SLOTS. Making it required
    # instead would have broken every caller staged against a pre-slot template
    # and bought nothing the guards do not already give.
    if report_file is not None:
        pairs = pairs + (("<INLINE_REPORT_FILE>", report_file),)

    # J31: the UNSUBSTITUTED guard below catches a slot left unfilled. The
    # inverse — a required value whose slot the template does not carry — left
    # nothing behind and passed silently, so the value reached nobody. Both are
    # staging failures. Computed BEFORE substitution, reported AFTER, so that a
    # template shipping a live placeholder still fails as UNSUBSTITUTED: that
    # prompt reaches a reviewer and reads as real, which is the worse outcome.
    absent = [slot for slot, _ in pairs if slot not in body]

    for slot, value in pairs:
        body = body.replace(slot, value)

    left = sorted(set(_PLACEHOLDER.findall(body)))
    if left:
        _emit(f"UNSUBSTITUTED slots={','.join(left)}")
        print("  a prompt shipped with a live placeholder asks the reviewer to "
              "review the placeholder, and reads as a real prompt to everything else.")
        return 2

    if absent:
        _emit(f"MISSING_SLOTS slots={','.join(absent)} template={template}")
        print("  a required input with no slot in the template reaches the "
              "reviewer nowhere, and the staging otherwise looks successful.")
        return 2

    # HEAD CONTRACT. Measured, not guessed: with the design and the 62-path file
    # list substituted in, the template's own text is ~7 KB of a ~690 KB prompt, so
    # every instruction it carries — the report file AND the verdict line — sits in
    # the last 0.4%. Two live dispatches wrote no report file; the transcript of the
    # second never mentions the path at all, and the instruction was at char 686,590
    # of 689,456.
    #
    # `h_mad_assemble_audit.prepend_output_contract` already solved this for the
    # audit path, and takes `report_file` for the same reason. This mirrors it
    # rather than inventing a second mechanism.
    if report_file is not None:
        # NOT `head` — that is the git HEAD sha (param, substituted above and
        # emitted in the STAGED token below). Binding the contract to it put a
        # 16-line blob where the sha goes in every `--report-file` staging, which
        # is the one artifact SKILL.md §"archreview" says exists to catch a stale
        # sha. The prompt body was unaffected; only the audit trail was.
        contract_head = (
            "!!! READ THIS BLOCK FIRST AND OBEY IT LAST !!!\n"
            "OUTPUT CONTRACT — repeated at the very end of this prompt.\n\n"
            "1. WRITE your full report with `run_command` to this exact path:\n"
            f"       {report_file}\n"
            "   Do this BEFORE you compose your reply. A file you create and leave\n"
            "   empty counts as not written.\n"
            "2. The LAST line of that file AND the LAST line of your reply must both\n"
            "   be exactly one of these three, character for character, alone on the\n"
            "   line, with nothing after it:\n"
            "       ASSESSMENT: READY_TO_MERGE\n"
            "       ASSESSMENT: WITH_FIXES\n"
            "       ASSESSMENT: NO\n\n"
            "Everything between here and the contract at the end is context.\n"
            "----------------------------------------------------------------\n\n"
        )
        body = contract_head + body

    # AFTER the contract prepend, because that is the body a surface receives --
    # measuring before it passes a prompt whose last ~800 chars are the thing that
    # tips it over. Characters, not bytes: codex counts chars, and the STAGED token
    # below reports bytes for a different purpose (the audit trail).
    #
    # A verdict, not a process failure, and NO file is written: an unwritten prompt
    # cannot be dispatched by mistake. This channel had ZERO size guards against the
    # audit path's several, which is how a ~690 KB 6a-prime prompt was staged, said
    # STAGED, and was then refused or silently truncated by the surface -- read as
    # "6a-prime failed" rather than "the prompt was never delivered".
    oversize, size, budget, reserve = _size_gate(body)
    if oversize:
        _emit(f"OVERSIZE bytes={size} budget={budget} reserve={reserve}")
        print("  - this prompt cannot be delivered: `exec agy` passes it as a single "
              "argv element, so it must fit ARG_MAX minus the environment the kernel "
              "shares that budget with. Measured on this machine, an argv payload at "
              "the old character limit failed with `Argument list too long`. "
              "Re-run with --vh-tail N to inline only the last N Version History "
              "entries of the design; the omitted entries stay reachable via "
              "`git show <sha>:<doc>`.")
        return 2

    prompt.write_text(body, encoding="utf-8")
    _emit(f"STAGED prompt={prompt} base={base} head={head} "
          f"bytes={len(body.encode('utf-8'))}")
    # Advisory, printed after the verdict so nothing reads it as a blocker.
    for note in _size_notes(len(body.encode("utf-8")), body):
        print(note)
    print(f"hmad-dispatch exec agy {prompt} \\")
    print(f"  --out /tmp/archreview_{feature}.md \\")
    print(f"  --log /tmp/archreview_{feature}.log --timeout 900")
    print(f"# then: {Path(__file__).name} score --feature {feature} "
          f"--state docs/.bkit-memory.json \\")
    print(f"#         --log /tmp/archreview_{feature}.log "
          f"--review /tmp/archreview_{feature}.md \\")
    # The operator copies this line. Omitting --report-file here would build the
    # channel and then not use it, which looks identical to never having built it.
    if report_file is not None:
        print(f"#         --report-file {report_file}")
    print("[H-MAD] archreview STAGED")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One Phase-6a-prime cycle")
    sub = parser.add_subparsers(dest="verb", required=True)

    s = sub.add_parser("stage", help="substitute the template and print the dispatch")
    s.add_argument("--feature", required=True)
    s.add_argument("--template", type=Path,
                   default=SCRIPTS.parent / "references" / "agy-architectural-reviewer-prompt.md")
    s.add_argument("--base", required=True, help="the 5c sha (see h_mad_baseline_sha.py)")
    s.add_argument("--head", required=True, help="the 5g sha")
    s.add_argument("--design", type=Path, required=True)
    s.add_argument("--diff-files", required=True)
    s.add_argument("--summary", required=True)
    s.add_argument("--prompt", type=Path, required=True)
    s.add_argument("--report-file", default=None, metavar="PATH",
                   help="where the reviewer must WRITE its report. Optional to "
                        "argparse, but pass it whenever the template carries "
                        "<INLINE_REPORT_FILE>: an unfilled slot trips "
                        "UNSUBSTITUTED, and passing it against a template without "
                        "the slot trips MISSING_SLOTS. Both directions fail closed.")
    s.add_argument("--vh-tail", type=int, default=None, metavar="N",
                   help="inline only the last N `## Version History` entries of the "
                        "design. The remedy OVERSIZE prescribes; omitted entries stay "
                        "reachable with `git show <sha>:<doc>`. Default: inline all.")

    c = sub.add_parser("score", help="evidence gate, verdict, record, read back")
    c.add_argument("--feature", required=True)
    c.add_argument("--state", type=Path, required=True)
    c.add_argument("--log", type=Path, required=True)
    c.add_argument("--review", type=Path, required=True)
    c.add_argument("--report-file", type=Path, default=None, metavar="PATH",
                   help="the file the reviewer was told to write. Preferred over "
                        "--review when it has content; the fallback is named in "
                        "the emitted token, never taken silently.")
    c.add_argument("--session-id", default=None,
                   help="this session's id; the owner's archreview write also beats "
                        "the claim heartbeat (#126)")

    args = parser.parse_args(argv)
    if args.verb == "stage":
        return stage(args.feature, args.template, args.base, args.head, args.design,
                     args.diff_files, args.summary, args.prompt, args.report_file,
                     vh_tail=args.vh_tail)
    return score(args.feature, args.state, args.log, args.review,
                 session_id=args.session_id, report_path=args.report_file)


if __name__ == "__main__":
    sys.exit(main())
