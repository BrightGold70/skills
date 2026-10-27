# H-MAD test boundaries and oracle fields — scope (triage row 17, todo #5)

**Status:** draft scope for operator approval, 2026-10-27. Drafted from the backlog notes without
an interview (operator opted out). Everything below marked *(my call)* is a default the operator has
not confirmed.
**Source:** `docs/03-analysis/2026-10-23-mattpocock-skills-hmad-handoff-review.analysis.md` §2
(lines 46-72) and its checklist item at line 146; triage row 17 in
`docs/03-analysis/2026-10-25-backlog-triage.md`.

## Intent

H-MAD already requires testable acceptance criteria, a design Test Strategy, mock boundaries,
meaningful RED evidence and checks against vacuous tests. What it does not do is make two things
first-class, written down before Phase 5, and checked by a script:

1. **The test boundary**: which public interface a test drives and observes, and what it does *not*
   establish.
2. **The oracle**: where the expected result comes from. The recurring failure is an expected value
   computed the same way the implementation computes it, so the test cannot fail (memory:
   "A test helper that re-implements cannot fail": 3 tests green against mutated code in one session).

The why for "deterministic check" is this repo's own lesson: a documented rule is not an enforced
one. Five h-mad gates shipped as prose that nothing checked. A table that exists only in a template
decays the same way.

## Goals

- A **Test Boundaries** table in the design doc, one row per planned test group, with five fields
  (from the review):
  | Field | Purpose |
  |---|---|
  | Public interface | where behaviour is exercised and observed |
  | Acceptance criteria | which AC ids this row proves |
  | Expected result source | spec, independent worked example, known-good fixture, or another named oracle |
  | Mocked dependencies | the external or system boundary substituted, or `none` |
  | Exclusions | important behaviour this row does not establish |
- A **deterministic check** that fails a design doc whose table is missing, has an empty cell, or
  leaves an AC id from the spec uncovered by any row.
- The table is **approved through the existing Phase 2–4 checkpoints and audits**. The audit prompts
  ask the auditor to challenge oracle independence and boundary placement.

## Non-goals

- No new confirmation gate in Phase 5. Matt's skill confirms boundaries before testing; importing
  that literally would interrupt H-MAD's autonomous Phase 5 (review line 70, line 146).
- No change to RED/GREEN gates, the mutation harness, the TDD judge or task semantics.
- No attempt to verify *mechanically* that an oracle is truly independent. That is a judgement for
  the audit, not the script. The script checks only presence, completeness and AC coverage.

## Anti-goals (would be a failure even if it works)

- A check that passes on placeholder prose (`TBD`, `n/a` in every cell, `see code`). The check must
  reject a fixed set of placeholder values, and **`implementation` / `the code` / `computed`
  must not be accepted as an Expected result source**.
- A gate that blocks existing archived or in-flight features retroactively.
- Prose added to SKILL.md with no script behind it.

## Constraints

- Runs beside the existing doc-shape check (`h-mad/scripts/h_mad_doc_shape_check.py`, already run
  on every saved design per `h-mad/references/inline-protocols.md`), as a **separate h-mad-only
  layer** with its own inputs (spec path, exemption status). It must not touch the copied bkit rules:
  `TestMirrorFidelity` diffs `REQUIRED_SECTIONS` against bkit's live validator *(my call)*.
- The design template in `inline-protocols.md` (the `## Test Strategy` / `## Test Plan` block,
  ~line 241) gains a `## Test Boundaries` section *(my call: design doc, not spec; the spec owns
  the AC ids the table cross-references)*.
- **Applies only to features that start after it ships** *(my call)*: gated on the design's
  creation, so archived docs and the docs of in-flight features keep passing. The mechanism, for
  example a version marker or a feature start date in state, is left to the builder.
- Must follow h-mad's own discipline: test-first, a mutation row per guard, and calibrated against
  designs that already passed, so the new check rejects none of the docs it should accept (memory:
  "Calibrate a new gate on artifacts that already passed").

## Decided

- Five fields, exactly as above (from the review).
- Approval rides on existing checkpoints; no Phase 5 gate (review).
- A deterministic check exists (row 17's own wording).
- **Enforcement (operator, 2026-10-27):** the Phase 4 design audit gate refuses a design that fails
  the check. Not advisory, and not a Phase 5-entry precondition.
- **Coverage (operator, 2026-10-27):** every spec AC must appear in at least one row. A row may be a
  non-test row, `verified by: audit | live-run | operator | doc-review`, naming the artifact that
  proves it. That way an AC proven without a test is covered honestly rather than by a filler test
  row.
- **Calibration (operator, 2026-10-27):** write the table for 2–3 archived, already-passed designs as
  test fixtures. The check must accept them and must reject seeded broken copies (missing table,
  placeholder cell, uncovered AC, `implementation` as an oracle, a non-test row that names no
  artifact).

## Left to the builder

- Exact table syntax and how the check parses it.
- The placeholder blocklist, and how AC ids are read from the spec.
- The gating mechanism that exempts pre-existing features.
- The wording added to the **Phase 4 design** audit prompt (the design holds the table) for oracle
  and boundary review.

## Size

A project. Next step on approval is a full h-mad feature, starting with a plan from this scope.
