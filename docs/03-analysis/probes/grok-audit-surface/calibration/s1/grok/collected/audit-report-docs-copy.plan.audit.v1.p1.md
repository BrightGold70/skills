## Summary
FR-1 and FR-4 are implemented-as-written. FR-2, FR-3, and FR-6 are restated: the requirements line drops `CONFLICT` from the collect token, the transport-refusal marker slot is the filename stem while the spec still says `<feature>`, and Success Criteria demands 25 mutations where the enumerated set is 23. The SKILL.md anchor risk names `test_h_mad_audit_cycle_slices.py`, which is not in `h-mad/tests`; the anchors live in `test_h_mad_audit_cycle_docs.py`.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | restated |
| FR-3 | restated |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | restated |

Evidence: 5 files opened, 11 greps run.

## Must-fix
- FR-2's requirements contract prints `COLLECT: OK|MISSING` and omits `CONFLICT`, which is narrower than the spec's `COLLECT: OK|MISSING|CONFLICT` token set — AC-2.5 and AC-5.4 require a `CONFLICT` verdict, and the same plan's Goals bullet still names `COLLECT: MISSING|CONFLICT`, so a CLI built from the requirements line would not emit the token the rest of the feature gates on.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `COLLECT: OK|MISSING path=<docs path>`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `COLLECT: OK|MISSING|CONFLICT path=<docs path>`
- FR-3 is restated: Requirements name the refusal marker `[H-MAD] <stem>` and say the feature slot is the dot-free transport stem, while the spec (and this plan's Scope line) still say `[H-MAD] <feature>`. Those are different strings in the slot (`audit_f_plan_cycle3_codex` versus a feature name), so the gate line an implementer prints is not fixed.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `[H-MAD] <stem>`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `the feature slot carries the dot-free transport`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `[H-MAD] <feature> gate INVALID`
- FR-6's Success Criteria requires 25 mutations on `collect_report.json`. The plan's own FR-6 line and deliverable say 23, spec AC-6.3 labels 23 mutants (`a` through `l′`), and `h-mad/tests/mutation-specs/collect_report.json` holds 23 mutation objects. A verifier scoring the success line rejects a spec-complete spec.
  class: measurement
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `(25 mutations, every connection dropped`
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `23 named-test mutations`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `23 mutations.`
- The SKILL.md edit risk names `test_h_mad_audit_cycle_slices.py` as the anchor test. Spec AC-5.2 names `test_h_mad_audit_cycle_docs.py`, and that is the file under `h-mad/tests` that slices `## Audit prompt assembly` and `6.6.`. No `*slices*` file exists under `h-mad/`, so the "insert outside these anchors" instruction points at a test that cannot go red.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `test_h_mad_audit_cycle_slices.py`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `test_h_mad_audit_cycle_docs.py`

## Should-fix
- Implementation Strategy cites `h_mad_new_gate.py` as "exit 0 on any verdict" and "a cannot-judge carries no counts". FR-3 and the spec require `GATE: INVALID must=0 should=0` with exit 2, the shape `h_mad_audit_cycle.GATE_RE` parses and the transport refusal already returns. Treating INVALID as a count-free exit-0 verdict changes the token the cycle combiner reads.
  class: build
  quote: docs/01-plan/features/audit-report-docs-copy.plan.md › `cannot-judge carries no counts, exit 0 on any verdict`
  quote: docs/01-plan/features/audit-report-docs-copy.spec.md › `GATE: INVALID must=0 should=0`

## Nit
None
