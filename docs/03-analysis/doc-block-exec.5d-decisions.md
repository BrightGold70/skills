# doc-block-exec — Phase 5d decisions

Decisions settled during 5d, per `h-mad/SKILL.md` §"Document-audit round cap — Phase 5 is
the gate": an open design-logic question surfaces at 5d as a blocked or failing RED and is
settled here, where a wrong choice costs minutes rather than a document round.

The five `OPEN-DECISION (r19, 5d)` lines carried on the impl-plan (Tasks 2/3/4, at
`:2635 :2871 :2873 :3374 :3376`) are NOT settled here. They are reached at their own Tasks.

---

## D1 — `_FenceEvent` field values on non-`open` events (Task 1)

**Raised by**: the Task 1 RED dispatch (`STATUS: NEEDS_CONTEXT`, 5d, session `93d3d858`),
which declined to invent them rather than guessing.

**The gap, exactly.** The impl-plan's `Code structure` block gives neutral-outside-their-kind
values for three of the kind-scoped fields —

    level: int      # heading events only (1-6, the opening-run length); 0 otherwise
    text: str       # heading events only: the compared text (closing-run stripped)
    candidate: bool # scanner-derived: True only for a BACKTICK opener whose first info word is "bash"

— and says nothing about `marker`, `run`, `indent` and `info` on a `close`, `body`, `prose`
or `heading` event. The design describes those four as "the opener's marker character, run
length, indentation and info string", which fixes their meaning on an `open` event and leaves
the other four kinds unstated. AC-1.8's `test_fence_events_trace_on_every_hostile_fixture`
pins **every** field of every event on LF and CRLF copies of each hostile fixture, so the test
cannot be written until this is decided. It is build-class: the 5e production code and that
test differ depending on the answer.

**Decision (operator, 2026-09-06): neutral on every non-`open` event.**

    open   : marker='`'  run=3 indent=<opener indent> info=<raw info string>
    close  : marker=None run=0 indent=0 info=''
    body   : marker=None run=0 indent=0 info=''
    prose  : marker=None run=0 indent=0 info=''
    heading: marker=None run=0 indent=0 info=''   (level and text carry the heading's own values)

**Why this and not the alternatives.**

1. It is the pattern the document already states for every other kind-scoped field: `level`
   is "0 otherwise", `text` is "heading events only", `candidate` is "True only for a
   backtick opener". Three fields neutral outside their kind and four inheriting would be two
   rules where the document reads as one.
2. `marker: str | None` is typed optional. Nothing but a non-opener needs the `None` arm.
3. No consumer reads any of the four on a non-`open` event. `extract` selects on `.candidate`
   and holds the `open` event it de-indents against; `fence_aware_end` reads `.kind`,
   `.level`, `.start` and `.end`; `find_heading` reads `.text`, `.level` and `.end`.
4. Carrying the opener's values onto `body`/`close` would make fence geometry readable off a
   body line, which is the property the design's single-scanner rule exists to prevent
   ("no consumer re-recognises a fence or a heading"). A future consumer could then branch on
   fence state without going through `_fence_events`, which is the shape
   `scanner-duplicated-in-consumer` and `test_extract_has_no_fence_state_of_its_own` guard.

**Residual, stated exactly.** A `close` event does not report the closer's own run length or
indentation, so nothing downstream can distinguish a 3-backtick closer from a 5-backtick one,
or a 0-space closer from a 3-space one. That information is used inside `_fence_events` to
decide closure and is deliberately not exported. If a later task needs it, it is a DESIGN
change and gains its own field and its own mutation row — it is not to be recovered by
re-scanning in a consumer.

**No mutation row follows.** The row list in the impl-plan MIRRORS the design's matrix and
the total is 87 at this batch; adding a row here would put the impl-plan one above the design.
A row for the neutral-fields rule, if the design wants one, is the design's to add. What
stands in for it is the fixture: the AC-1.8 trace test asserts the neutral values on every
non-`open` event of every hostile fixture, on LF and CRLF, so an implementation that carries
opener metadata through fails outright.

---

## D2 — 5d mutation specs are PARKED, not committed unanchored (Task 1)

**Raised by**: the Task 1 RED, which delivered `doc_block_exec.json` (25 rows) and a rewritten
`docsections.json` (8 rows) with anchors omitted or re-pointed at 5e source. Codex followed the
impl-plan's Conventions exactly; the Conventions are what turn out to conflict with an enforced
guard.

**The conflict, measured.** The impl-plan's Conventions say a 5d spec omits `file`/`find`/`replace`
until 5e source exists — "intentionally not yet harness-runnable". But
`h-mad/tests/test_h_mad_mutation_harness.py` sweeps `tests/mutation-specs/*.json` by **filesystem
glob** (`:1900`, `rglob`; also `:81`, `specs_dir.glob`), and `git-hooks/pre-push` sweeps every
tracked `*.json`, and both score an unanchored row as `ANCHORS_UNREADABLE`. Observed with the RED
in the working tree, before any commit:

    FAILED test_h_mad_mutation_harness.py::test_committed_mutation_specs_are_not_drifted
    FAILED test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok
    2 failed, 96 passed

So the Conventions' rule is unreachable as written: there is no state in which an unanchored spec
sits under `tests/mutation-specs/` and the repo's own guards are satisfied.

Second, narrower defect in the same delivery: 6 of `docsections.json`'s 8 rows had their anchors
re-pointed at post-5e source (`_dbe.fence_aware_end(...)`, `assert found`) and 2 stripped entirely
— but `h-mad/tests/docsections.py` is UNCHANGED at RED, so none of those anchors resolves on the
current tree. A guard that worked before this dispatch would have been disabled for the whole
5d-to-5e window.

**Positive control, run before deciding.** With both spec files moved aside and `docsections.json`
reverted, the sweep is `11 passed` and the WIRE-PIN still fails on its call-record assertion. So
the specs are the sole cause of the two failures, and parking them costs the RED nothing.

**Decision (operator, 2026-09-06): park both until 5e.**

- `docs/03-analysis/doc-block-exec.pending-mutation-specs/doc_block_exec.json.pending` — the 25 rows.
- `docs/03-analysis/doc-block-exec.pending-mutation-specs/docsections.json.pending` — the 8-row
  rewrite, including the 4 new rows and the 6 re-pointed anchors.
- `h-mad/tests/mutation-specs/docsections.json` reverted to its committed 4 anchored rows, which
  still resolve against the untouched `docsections.py`, so that guard stays ARMED through the window.

**The `.json.pending` suffix is load-bearing, not cosmetic.** The pre-push hook sweeps every tracked
`*.json` **anywhere in the repository**, not only under `tests/mutation-specs/`, so a parked spec
that still ended in `.json` would block the very push it was parked to unblock.

**At 5e**: move both files back under `h-mad/tests/mutation-specs/`, drop the `.pending` suffix, and
anchor every row against the source that now exists — which is the one moment an anchor can be
verified rather than guessed. The harness refuses any anchor not matching exactly once, so the
anchoring is checked at the moment it is written.

**Verified after parking**, NUL-safe over every tracked `*.json` (a whitespace-split first attempt
inflated the count with phantom paths and had to be redone):

    ANCHORS: ANCHORS_OK specs=46 mutations=490 ok=490 drifted=0 unreadable=0 unclassifiable=0

**Residual, stated exactly.** Nothing detects a parked spec that is never moved back. If 5e lands
without restoring these two files, the feature ships with no mutation coverage for the new module
and the sweep stays green, because a spec that is not under the glob is not a spec. The 5e task is
the only thing that closes this, and the impl-plan's Conventions bullet should be corrected to say
"write the spec at 5e" rather than "write it unanchored at 5d" — that is an `implplan-author`
revision, not an orchestrator edit, and it is owed.

---

## D3 — OPEN: the impl-plan's own noise floor cannot survive Phase 5 (Task 1, unresolved)

**Not a decision. A finding, recorded open, owed to 5e/5g.**

`test_noise_floor_on_documents_that_survived_eighty_cycles[...impl-plan]` went red on the RED
commit `954958a`. Re-derived rather than inferred:

    python3 h-mad/scripts/h_mad_precheck_doc.py \
      docs/01-plan/features/doc-block-exec.impl-plan.md --phase impl-plan --root .
    PRECHECK: FAIL issues=13
    PINDRIFT: L369  h-mad/tests/test_docsections.py:77      — changed since provenance 0021c77
    PINDRIFT: L3822 h-mad/tests/test_h_mad_audit_cycle.py:18 — changed since provenance 0021c77
    PLACEHOLDER: x11  (Tasks 2-4 template slots, all pre-existing)

The floor is 12. At `ce9ffe1` the count was exactly 12 — 11 PLACEHOLDER plus the one
`test_h_mad_audit_cycle.py` PINDRIFT that the `#49x` batch introduced — and the test passed, which
is why the 2026-09-06 baseline run was `2617 passed, 0 failed`. The RED commit added a test to
`h-mad/tests/test_docsections.py`, a file the impl-plan pins at L369, and that thirteenth issue
crossed the floor.

**The general shape, which is why this is not just a number to bump.** PINDRIFT means "a pin into a
file that changed since the document's own provenance commit". Phase 5 exists to change exactly
those files. So every 5d/5e commit that touches a file the impl-plan pins drifts another pin, and
the count only rises from here: Task 1 GREEN writes `h-mad/scripts/h_mad_doc_block_exec.py` and
edits `h-mad/tests/docsections.py`, both pinned; Tasks 2-5 add more. The guard cannot distinguish
"stale because nobody maintained it" — the decay it was written to catch — from "stale because the
implementation phase is underway", which is the feature working.

**Three remedies, none of them the orchestrator's to pick alone:**

1. **Bump the impl-plan's provenance sha** as each Phase-5 commit lands. Keeps the guard armed and
   honest, but it is a `implplan-author` revision per dispatch, on a document whose audit loop is
   capped and closed — and it re-stamps a gated document repeatedly, which is the measurement-layer
   churn the class rule was written to stop.
2. **Exempt the feature's own impl-plan while `phase == "step5"`.** Correct in principle — the
   document is by definition mid-implementation — but it is an h-mad tooling change made mid-feature,
   and it disarms the guard for the one document most likely to drift.
3. **Accept the red through 5e and settle it at 5g**, when the implementation is final and one
   provenance bump covers every drifted pin at once. Cheapest, and it leaves the suite reporting a
   failure unrelated to the wire for the whole window — the noise that hides a real one.

**Until it is settled, 5e must not be called green on a suite carrying this failure without saying
so explicitly.** A green claim that silently excludes a known red is the failure mode the whole
verification discipline exists to prevent.

**RED-state suite, for the record** (`954958a`, `--continue-on-collection-errors` required — see
below): `2 failed, 2616 passed, 1 error`. The error and the WIRE-PIN failure are the intended RED;
the second failure is this finding.

## D4 — the suite needs `--continue-on-collection-errors` during 5d

Task 1's prescribed RED is a module-level `import h_mad_doc_block_exec` in a test file, so pytest
raises a **collection** error and then refuses to run anything:

    pytest h-mad/tests -q -p no:cacheprovider
    !!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!
    1 error in 0.49s

Zero tests run — not "two red tests". For the whole 5d-to-5e window the suite gives no signal at
all unless `--continue-on-collection-errors` is passed, which is what produced the numbers in D3.
This is a property of the impl-plan's own prescribed RED shape and resolves itself the moment Task 1
GREEN creates the module. It is recorded because the next person to run the suite in this window
will otherwise read `1 error` as the suite being broken.
