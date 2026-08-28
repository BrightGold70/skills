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
    ARCHREVIEW: NO_EVIDENCE tools=0                                  exit 2
    ARCHREVIEW: NO_VERDICT tools=N                                   exit 2
    ARCHREVIEW: NOT_RECORDED verdict=<v>                             exit 2
    ARCHREVIEW: UNSUBSTITUTED slots=<a,b>                            exit 2
    ARCHREVIEW: DEGENERATE_RANGE base=<b>                            exit 2
    ARCHREVIEW: UNREADABLE reason=<r>                                exit 2

The gate ORDER is the contract: evidence before verdict, always. A review that
read nothing has no verdict to record, whatever its last line says — recording it
is precisely what let the 1510-byte defect survive. So `NO_EVIDENCE` and
`NO_VERDICT` write nothing, and neither carries a verdict word.

`NOT_RECORDED` exists because `archreview` is **not** in the schema's `required`
array: strict validation passes over a write that never landed, so the read-back
is the only thing that can catch a dropped write. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TOKEN = "ARCHREVIEW:"
SCRIPTS = Path(__file__).resolve().parent
ALLOWED = ("READY_TO_MERGE", "WITH_FIXES", "NO")
_PLACEHOLDER = re.compile(r"<INLINE_[A-Z_0-9]+>")


def _emit(line: str) -> None:
    print(f"{TOKEN} {line}")


def _tools_that_completed(log_path: Path) -> int:
    """Delegate the evidence count to the gate that owns it.

    Imported rather than re-counted: a second copy of "what counts as a tool call
    that reached DONE" is a second thing to drift, and the first probe of that
    defect hardcoded tool NAMES from an earlier dispatch and reported a false zero
    when agy switched to `run_command`.
    """
    sys.path.insert(0, str(SCRIPTS))
    from h_mad_review_evidence import scan

    result = scan(log_path.read_text(encoding="utf-8"))
    return int(result.get("ok", 0))


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


def score(feature: str, state_file: Path, log_path: Path, review_path: Path) -> int:
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
    # its last line says.
    tools = _tools_that_completed(log_path)
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

    writer = SCRIPTS / "h_mad_state_write.py"
    subprocess.run(
        [sys.executable, str(writer), str(state_file), "--feature", feature,
         "--set", f"archreview={verdict}"],
        capture_output=True, text=True,
    )
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

    _emit(f"{verdict} tools={tools} recorded=yes")
    if verdict != "READY_TO_MERGE":
        print("  halt `step6a-prime:architectural_review_failed` — surface the "
              "findings, fix, and re-run ONE more cycle.")
    print(f"[H-MAD] archreview {verdict}")
    return 0


def stage(feature: str, template: Path, base: str, head: str, design: Path,
          diff_files: str, summary: str, prompt: Path) -> int:
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

    for slot, value in (
        ("<INLINE_FEATURE>", feature),
        ("<INLINE_BASE_SHA>", base),
        ("<INLINE_HEAD_SHA>", head),
        ("<INLINE_DIFF_FILES>", diff_files),
        ("<INLINE_AUDITED_DESIGN>", design_text),
        ("<INLINE_PHASE_5_SUMMARY>", summary),
    ):
        body = body.replace(slot, value)

    left = sorted(set(_PLACEHOLDER.findall(body)))
    if left:
        _emit(f"UNSUBSTITUTED slots={','.join(left)}")
        print("  a prompt shipped with a live placeholder asks the reviewer to "
              "review the placeholder, and reads as a real prompt to everything else.")
        return 2

    prompt.write_text(body, encoding="utf-8")
    _emit(f"STAGED prompt={prompt} base={base} head={head} "
          f"bytes={len(body.encode('utf-8'))}")
    print(f"hmad-dispatch exec agy {prompt} \\")
    print(f"  --out /tmp/archreview_{feature}.md \\")
    print(f"  --log /tmp/archreview_{feature}.log --timeout 900")
    print(f"# then: {Path(__file__).name} score --feature {feature} "
          f"--state docs/.bkit-memory.json \\")
    print(f"#         --log /tmp/archreview_{feature}.log "
          f"--review /tmp/archreview_{feature}.md")
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

    c = sub.add_parser("score", help="evidence gate, verdict, record, read back")
    c.add_argument("--feature", required=True)
    c.add_argument("--state", type=Path, required=True)
    c.add_argument("--log", type=Path, required=True)
    c.add_argument("--review", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.verb == "stage":
        return stage(args.feature, args.template, args.base, args.head, args.design,
                     args.diff_files, args.summary, args.prompt)
    return score(args.feature, args.state, args.log, args.review)


if __name__ == "__main__":
    sys.exit(main())
