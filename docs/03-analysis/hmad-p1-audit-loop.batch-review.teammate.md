## Summary

No Must-fix. The three commits are sound in the direction that matters: nothing here can produce a
false clean, and the #13 reversal is complete, correctly ordered and well tested. I re-derived
every number in #17 independently and all four reproduce exactly, including the 1x occurrence count
that corrects the old 2x assumption. The findings below are one surviving stale comment, one input
shape whose remedy token points the wrong way, one dispatch that omits an input its own agent
contract requires, one unconditional statement of a conditional fact, and one number with no source
in the repository.

Evidence: 11 files opened, 16 greps run, 2 direct probes of `combine()` and `measure_effort()` over
six constructed inputs, 1 independent re-derivation of the size fixture, 1 full suite run
(2519 passed in 385s, matching fea38c6's claim).

## Must-fix

None

## Should-fix

- **The empty-log and the garbage-log cases are each routed to the other's remedy, because
  `readable` does not measure what the two-way split needs.** I probed `measure_effort` directly.
  A zero-byte log returns `{"readable": False}` and `combine()` answers
  `low_evidence_unmeasurable` — whose documented remedy is "find the log" — but a zero-byte log is
  what a dispatch that died instantly writes, and there is nothing to find; the remedy is
  re-dispatch. The mirror also holds: a log full of non-JSON returns `readable: True, tools=0` and
  answers `low_evidence` — "re-dispatch" — when the file plainly is not the transcript and the
  remedy is to find the right one. Neither case can produce a false clean, so this is a wrong hint
  rather than a wrong verdict. Prescription: discriminate on parseability, not on byte-readability.
  Treat "read, non-blank, but zero recognisable NDJSON events" as unmeasurable, and treat an
  existing-but-empty log as hollow. The pre-existing `measure_effort` docstring justifies the
  empty→`readable: False` choice on rendering grounds ("rendering an unread log as zeros would
  manufacture the very finding this exists to surface"), which was sound when nothing routed on the
  token and is what #13 changed underneath it.
  instance of: the class is "every input shape a log can take, and which of the two remedies each
  one deserves". I enumerated it: `None` (correct, scored normally), missing file (correct,
  unmeasurable), empty file (mis-routed), non-JSON bytes (mis-routed), parsed with `ok=0 failed=5`
  (correct — `low_evidence`, and `ok` IS the right field, since a failed call read nothing), parsed
  above the floor (correct). Residual after fixing the two: `ok=3, failed=20` certifies a clean,
  because two of those three calls are the delivery contract itself, so one real read clears the
  floor. That is the floor working as designed, not a defect, but it is where the next false clean
  will come from if one does.
  quote: h-mad/scripts/h_mad_audit_cycle.py:576-577 › `# A log was named and could not be read: a cannot-judge, and it fails
            # closed. Its own reason token, because the remedy differs -- find the`

- **A surviving comment states the reversed rule in the present tense, with its rejected defence
  intact.** You inverted the assertion in `test_h_mad_audit_cycle.py`, but the same rule is asserted
  again as a section header in a different test file, using the same 2-call argument the reversal
  explicitly calls "true and beside the point". It is true of `h_mad_review_evidence.py` itself,
  which still only reports, so no test asserts wrong behaviour — but the sentence is written as a
  general rule about effort, not as a statement scoped to that CLI. This is the sweep miss for the
  reversal. Prescription: scope it, along the lines of "this CLI reports; since #13
  `h_mad_audit_cycle.combine()` decides on the same counts, in one direction."
  quote: h-mad/tests/test_h_mad_review_evidence.py:210-212 › `# This reports effort. It must NEVER decide: a pass that made 2 tool calls honoured
  # the delivery contract exactly as asked, and one such pass in this very repo
  # (5,356 thinking / 2 tools) still returned a real finding.`

- **#11's dispatch omits `PROMPT`, which the `doc-auditor` contract lists as a required input and
  tells the agent to read first.** The delta dispatch supplies `PROJECT_ROOT`, `REPORT` and a
  `Subject:`, but the agent file opens with three inputs and instructs "Read this file first, in
  full." An agent following its own contract looks for a path it was not given. The intent is
  clearly right — there is no assembled prompt for a delta review — but the omission is undeclared.
  Prescription: say so in the dispatch, e.g. `PROMPT=<none — this pass has no assembled prompt;
  your subject is the diff below>`, and add one line to the agent file allowing a subject in place
  of a `PROMPT` path. This is the one place these three commits contradict what 6db8e50
  established.
  quote: h-mad/agents/doc-auditor.md:35-36 › `- `PROMPT`: path to the assembled audit prompt. It contains the rubric, the project invariants, and
  the phase documents inlined verbatim. **Read this file first, in full.**`

- **The template tells every reviewer it is scored on effort, which is true only for a pass
  dispatched through `audit-cycle` with its NDJSON supplied.** The guard arms on the 5th `--pass`
  field, and SKILL.md says so plainly ("the guard only arms when you give it the log"). But a codex
  leg and every `Agent()` teammate pass read this same template and are told, unconditionally, that
  a low-effort pass "is scored `UNVERIFIED`, not clean" — and for them nothing measures it. The
  teammate leg is the one that currently gates, so the surface with no measurement is the one told
  most confidently that it is measured. Prescription: condition the sentence, e.g. "when this pass
  is dispatched with its transcript captured, the combiner enforces this; when it is not, the rule
  still binds you and only you can honour it."
  quote: h-mad/audit-prompt.template.md:132 › `Effort contract (this pass is scored on it, not only on its verdict):`

- **`unverified` — "four consecutive cycles where the fix produced the next defect" has no source
  in this repository.** I could not verify it, and I am not claiming it is wrong. Grepping the
  whole of `docs/` and `h-mad/` for the phrase returns exactly one hit: the SKILL.md sentence
  itself. The figure does exist in durable session memory, in the gateway-consolidation Phase 4
  record, so it is recalled rather than invented — but it is uncitable from the tree, and it sits in
  the same sentence as two figures that ARE sourced, so a reader cannot tell them apart. Your other
  two claims in that paragraph both check out: the impl-plan v1.35 entry says exactly what you
  attribute to it, and "roughly half" matches the 2026-09-04 handoff. Prescription: cite the memory
  record by name, or drop the clause. It is the weakest sentence in a paragraph whose whole argument
  is that unsourced numbers are the defect.
  quote: h-mad/SKILL.md:1193 › `and one arc recorded four consecutive cycles where the fix produced the next defect.`

## Nit

- `_effort_items`'s docstring still ends "Never a verdict." That remains true of the function, which
  only renders lines, but it is the reversed rule's exact wording sitting 200 lines above the loop
  that now decides. One clause scoping it to the rendering would remove the trap.
  quote: h-mad/scripts/h_mad_audit_cycle.py:364 › `"""One human line per pass that carried a log. Never a verdict."""`

- Two spellings of the evidence line are now in circulation for the same surface. The template asks
  for `Evidence: <N> files opened, <M> searches run.` and the agent file asks for `<M> greps run.`
  Nothing parses either today, so this costs nothing yet; it would cost something the moment anyone
  greps for it.

- Answering your questions 1 and 3 as verified rather than as findings, since a null result here is
  the useful part. The ordering holds on every path I could construct: the FAIL loop and the rc loop
  both precede the effort loop, so a hollow pass that found something scores `FAIL`, a timeout
  explains itself rather than reading as hollowness, and in the multi-pass case one hollow leg
  unverifies a cycle its deep leg would have passed — each of which has its own test. The
  counter-example in `h_mad_review_evidence`'s docstring is genuinely preserved by that ordering. On
  #17, all four measured claims reproduce exactly on my own run: 2389 → 89,999 B, 2689 → 96,899 B,
  the old 2440 anchor → 91,172 B, and the new section occurs exactly **1** time in an assembled
  prompt while "Output framing (mandatory" occurs **2**, which is the direct evidence that only the
  output contract is head-duplicated. No efficacy claim appears in the commit message; it states the
  opposite explicitly and names task #25 as the thing that would measure it. The template's own
  overclaim is filed above, and it is about scoring rather than about efficacy.
