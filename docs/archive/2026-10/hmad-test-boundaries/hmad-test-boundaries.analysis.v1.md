# Analysis: hmad-test-boundaries

## Executive Summary
All 6 Functional Requirements (`FR-1`..`FR-6`) and all 17 Acceptance Criteria (`AC-1.1`..`AC-6.3`) specified in `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.5`) and `docs/02-design/features/hmad-test-boundaries.design.md` (`v1.2`) are 100% implemented and verified between baseline `35b013b5d577120def63dee4742ff8c287031641` and head `9c6d54740403b817a875e84b916f4efa93dc7255`, with 427/427 targeted tests passing, 1159/1159 doc-consumer tests passing, 8/8 mutation rows caught (`MUTATION: ALL_CAUGHT`), and Phase 6a-prime architectural review scored `ARCHREVIEW: READY_TO_MERGE`.

## Match Rate: 100%

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: Phase 4 Design Template & Authoring Contract | 3 | 3 | ✅ Complete | `h-mad/references/inline-protocols.md`, `h-mad/agents/design-author.md`, `h-mad/tests/test_h_mad_doc_templates.py` (`AC-1.1`, `AC-1.2`, `AC-1.3`) |
| FR-2: Standalone Test Boundaries Checker (`h_mad_test_boundaries_check.py`) | 4 | 4 | ✅ Complete | `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py` (`AC-2.1`, `AC-2.2`, `AC-2.3`, `AC-2.4`) |
| FR-3: Spec AC Coverage & Non-Test (`verified by:`) Row Rules | 2 | 2 | ✅ Complete | `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py` (`AC-3.1`, `AC-3.2`) |
| FR-4: Pre-Existing & Archive Exemption and Phase 4 Audit Gate Integration | 4 | 4 | ✅ Complete | `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/scripts/h_mad_audit_gate.py`, `.h-mad/wires.jsonl` (`AC-4.1`, `AC-4.2`, `AC-4.3`, `AC-4.4`) |
| FR-5: Phase 4 Design Audit Prompt & Doc-Auditor Instructions | 1 | 1 | ✅ Complete | `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md` (`AC-5.1`) |
| FR-6: Calibration Corpus & Mutation-Tested Suite | 3 | 3 | ✅ Complete | `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json` (`AC-6.1`, `AC-6.2`, `AC-6.3`) |

## Per-AC Verification Matrix

| AC | Status | Verification Evidence |
|---|---|---|
| `AC-1.1` | ✅ Met | `h-mad/references/inline-protocols.md` (`## Phase 4 — Design`) includes `## Test Boundaries` and the 5-column table `\| Public interface \| Acceptance criteria \| Expected result source \| Mocked dependencies \| Exclusions \|` (14 headings total); `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` includes `"Test Boundaries"` (`8 passed`). |
| `AC-1.2` | ✅ Met | `REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py` remains the 7 bkit-mirrored headings (`51 passed` in `test_h_mad_doc_shape_check.py`). |
| `AC-1.3` | ✅ Met | `h-mad/agents/design-author.md` requires populating `## Test Boundaries` for every active spec `AC-X.Y[a-z]` and verifying `TEST-BOUNDARIES: PASS` before `DESIGN-AUTHOR: DONE`; `docs/02-design/features/hmad-test-boundaries.design.md` passes `h_mad_test_boundaries_check.py` with `TEST-BOUNDARIES: PASS path=... rows=9 acs=17/17`. |
| `AC-2.1` | ✅ Met | `h-mad/scripts/h_mad_test_boundaries_check.py` implements `<design_path>`, `--spec`, `--root` (inferring `abs_design.parents[3]` for canonical design/archive paths), and `--no-exempt`, emitting `PASS`/`EXEMPT`/`FAIL` (exit `0`) and `UNREADABLE` (exit `2`). |
| `AC-2.2` | ✅ Met | Rejects missing section (`missing_section`), missing/empty table (`missing_table`), wrong header or `!= 5` cells or zero-AC-token `Acceptance criteria` cells (`invalid_columns`). |
| `AC-2.3` | ✅ Met | Rejects empty cells (`empty_cell`) and closed placeholder tokens/prefixes (`placeholder_cell`) while permitting `none` (and `none ...` explanations) in `Mocked dependencies`. |
| `AC-2.4` | ✅ Met | Rejects exact and regex tautological oracles (`implementation`, `the code`, `computed`, `return value`, `same function`, etc.) in `Expected result source` with `code=tautological_oracle`. |
| `AC-3.1` | ✅ Met | Extracts head-anchored active `AC-X.Y[a-z]` definitions from `.spec.md`, excludes retired ACs (`17`, `24`, `40`, `44`, and `63` active ACs on the 5 reference specs), extracts all `AC-X.Y[a-z]` tokens per design row, and reports `uncovered_ac` and `unknown_ac`. |
| `AC-3.2` | ✅ Met | Validates `verified by: audit \| live-run \| operator \| doc-review` rows and requires a concrete proving artifact (file path, `TOKEN:`, or backticked command/section) in `Expected result source`, emitting `invalid_non_test_row` otherwise. |
| `AC-4.1` | ✅ Met | Emits `TEST-BOUNDARIES: EXEMPT` (`reason=pre_existing_feature` or `reason=archived`) on the 10 `PRE_EXISTING_FEATURES` stems and unaugmented `docs/archive/**` designs, and forces strict evaluation (`missing_section`) under `--no-exempt`. |
| `AC-4.2` | ✅ Met | `h_mad_test_boundaries_check.py` owns `should_activate_design_check`; `h_mad_audit_gate.py` selects candidates via `Path(design_path).exists()`, loads the checker via `importlib.util.spec_from_file_location`, evaluates before `.gated.json` stamping, suppresses stamps on `FAIL`/`UNREADABLE`, and prints `TEST-BOUNDARIES:` lines immediately after `GATE:` / `GATE-CLASS:` / `GATE-LEGS:`. |
| `AC-4.3` | ✅ Met | Emits `GATE: PASS` and writes `.gated.json` when all activated designs emit `PASS` or `EXEMPT` and `must=0`; `TestAuditGateIntegration::test_activation_parity_across_direct_and_isolated_gate_loading` verifies parity across fenced headings, active lettered ACs vs retired-only specs, and both spec resolution paths. |
| `AC-4.4` | ✅ Met | `h_mad_audit_gate.py` keeps stdlib-only top-level imports, preserves the `stamped = ""\n    if args.gated and verdict == "PASS":` mutation anchor, skips `.plan.audit.` / `.impl-plan.audit.` reports (`_NON_DESIGN_AUDIT_RE`) and bare synthetic `tmp_path` fixtures, and passes all 349 tests across `test_h_mad_test_boundaries_check.py`, `test_h_mad_audit_gate.py`, `test_h_mad_audit_leg_set_gate.py`, and `test_h_mad_audit_cycle.py`. |
| `AC-5.1` | ✅ Met | `h-mad/audit-prompt.template.md` (`{{ONLY:design}} ... {{END-ONLY}}` under Axis A) and `h-mad/agents/doc-auditor.md` require `Must-fix` (`build` class) findings for missing/incomplete `## Test Boundaries`, semantic oracle tautologies, internal-helper boundary drift / over-mocking, and `verified by:` misuse (`16 passed` in `test_h_mad_audit_spec_axis.py`). |
| `AC-6.1` | ✅ Met | `TestArchivedDesignCalibration` verifies all 3 archived designs (`exec-path-hardening` `24/24`, `audit-report-docs-copy` `40/40`, `tdd-gate-fail-opens` `44/44`) pass `--no-exempt` in `< 200ms` (`time.monotonic() < 0.200`) with `docs/archive/` unmodified. |
| `AC-6.2` | ✅ Met | `TestSeededBrokenFixtures` verifies all 5 seeded broken fixture classes fail with exact reason codes (`missing_section`/`missing_table`, `placeholder_cell`, `uncovered_ac`, `tautological_oracle`, `invalid_non_test_row`). |
| `AC-6.3` | ✅ Met | `h-mad/tests/mutation-specs/test_boundaries_gate.json` passes `--check-anchors` (`ANCHORS: ANCHORS_OK`) and catches all 8 mutations (`MUTATION: ALL_CAUGHT mutations=8 caught=8 survived=0 refused=0`). |

## Gaps

None (`0` gaps). All 6 FRs and 17 ACs are completely satisfied.

## Test Results
```
pytest h-mad/tests/test_h_mad_test_boundaries_check.py h-mad/tests/test_h_mad_doc_templates.py h-mad/tests/test_h_mad_doc_shape_check.py h-mad/tests/test_h_mad_audit_gate.py h-mad/tests/test_h_mad_audit_leg_set_gate.py h-mad/tests/test_h_mad_audit_cycle.py h-mad/tests/test_h_mad_audit_spec_axis.py -v --tb=short
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAxisCContent::test_defines_the_three_classifications PASSED [ 97%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAxisCContent::test_restatement_requires_quoting_both_forms PASSED [ 98%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAxisCContent::test_divergence_is_a_blocking_finding PASSED [ 98%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAxisCContent::test_axis_c_is_scoped_to_the_audits_that_derive_from_the_spec PASSED [ 98%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAssemblyStepsWired::test_skill_md_instructs_inlining_the_spec PASSED [ 98%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAssemblyStepsWired::test_spec_inlining_is_ordered_with_the_other_slot_steps PASSED [ 99%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestAssemblyStepsWired::test_every_template_slot_has_an_assembly_instruction PASSED [ 99%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestSizeConstraintDocumented::test_skill_md_warns_about_prompt_size PASSED [ 99%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestSizeConstraintDocumented::test_skill_md_rejects_trimming_the_design PASSED [ 99%]
h-mad/tests/test_h_mad_audit_spec_axis.py::TestSizeConstraintDocumented::test_skill_md_names_the_safe_failure_mode PASSED [100%]

============================= 427 passed in 20.48s =============================
```

## Verdict
Match rate: 100% (threshold: 90%). Tests: 427/427 passing (plus 1159/1159 doc-consumer tests and 8/8 mutations caught).
→ Advance to Phase 7

## Version History
- v1.0: Initial gap analysis draft verifying 100% FR/AC match rate (6/6 FRs, 17/17 ACs) across baseline `35b013b5d577120def63dee4742ff8c287031641` to head `9c6d54740403b817a875e84b916f4efa93dc7255`.
