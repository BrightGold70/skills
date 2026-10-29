AUDIT-hmad-test-boundaries-impl-plan-v2-BEGIN
## Summary
`docs/01-plan/features/hmad-test-boundaries.impl-plan.md` (`v1.1`) resolves all Phase 5b Audit Cycle 1 findings (`v1.p1` and `v1.p2`), passes `h_mad_precheck_doc.py --phase impl-plan` (`PRECHECK: PASS issues=0`), `h_mad_ac_census.py` (`ACS: OK count=17 frs=6`), `h_mad_wire_pin_gate.py` (`WIREPIN: PASS tasks=5 wiring=1 unpinned=0 mislabeled=0`), and `h_mad_prescribed_block_guards.py` (`PRESCRIBED-BLOCKS: PASS checked=1 skipped=4 guards=0`), and maintains exact alignment with `docs/02-design/features/hmad-test-boundaries.design.md` (`v1.2`), `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.5`), `h-mad/invariants.base.md`, and `.h-mad/invariants.md`. All 5 task scopes, 35 test methods across 7 classes in `h-mad/tests/test_h_mad_test_boundaries_check.py` (plus `test_design_template_contains_test_boundaries_five_column_table` in `h-mad/tests/test_h_mad_doc_templates.py`), RED/GREEN splits and `--guard` declarations, 8 mutation rows in `h-mad/tests/mutation-specs/test_boundaries_gate.json`, and the 178-file mutation-spec non-interference table were independently re-derived against `HEAD` (`12fd1775f95952e136bf71d8d8889bdb2dcd0a1d`) with zero blocking or should-fix issues remaining.
Evidence: 14 files opened, 6 greps run.

## Must-fix
None

## Should-fix
None

## Nit
- In Task 4 (`audit_prompt_and_doc_auditor_test_boundaries`), line 776 of `docs/01-plan/features/hmad-test-boundaries.impl-plan.md` parenthetically refers to `h-mad/tests/test_h_mad_audit_spec_axis.py` as having `14` existing tests (`0 F, 14 P`), whereas `h-mad/tests/test_h_mad_audit_spec_axis.py` defines `16` test methods across `TestSpecSlot` (`4`), `TestAxisCContent` (`6`), `TestAssemblyStepsWired` (`3`), and `TestSizeConstraintDocumented` (`3`).
AUDIT-hmad-test-boundaries-impl-plan-v2-END
