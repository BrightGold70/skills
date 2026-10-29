# Design Author Report — `hmad-test-boundaries` (`v1.0`)

- **Document:** `docs/02-design/features/hmad-test-boundaries.design.md`
- **Version:** `v1.0`
- **Lines:** `869`
- **SHA-256:** `04381d07a822c7b0d5c0f8b988a49717cb08e37d46046a23487283d8e0e6e87b`
- **Inputs Read:**
  - `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.3`)
  - `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.3`)
  - `docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md`
  - `h-mad/invariants.base.md` and `.h-mad/invariants.md`
  - `h-mad/agents/design-author.md`, `h-mad/agents/doc-auditor.md`, `h-mad/audit-prompt.template.md`, `h-mad/references/inline-protocols.md`
  - `h-mad/scripts/h_mad_audit_gate.py`, `h-mad/scripts/h_mad_doc_shape_check.py`, `h-mad/scripts/h_mad_mutation_harness.py`
  - `h-mad/tests/test_h_mad_doc_templates.py`, `h-mad/tests/test_h_mad_audit_gate.py`, `h-mad/tests/mutation-specs/audit_suite_gate.json`, `h-mad/tests/mutation-specs/audit_gate_stamp.json`

## 1. Summary of Authored Design

Authored `docs/02-design/features/hmad-test-boundaries.design.md` (`v1.0`) with all 14 required `## ` headings in exact Phase 4 template order (`Executive Summary`, `Overview`, `Architecture Overview`, `Detailed Design`, `Components Changed / Added`, `Implementation Order`, `Data Model / Schema Changes`, `API / Interface Changes`, `Error Handling Strategy`, `Test Strategy`, `Test Plan`, `Test Boundaries`, `Invariant Compliance`, `Version History`), covering all 6 functional requirement groups (`FR-1`..`FR-6`) and all 17 active acceptance criteria (`AC-1.1`..`AC-6.3`):

1. **Component 1 (`FR-1`, `AC-1.1`..`AC-1.3`):** Structural locators and exact diffs for `h-mad/references/inline-protocols.md` (adding `## Test Boundaries` and the 5-column table skeleton between `## Test Plan` and `## Invariant Compliance`), `h-mad/tests/test_h_mad_doc_templates.py` (appending `"Test Boundaries"` to `PRIOR_HMAD_HEADINGS["design"]` so the list grows from `7` to `8` entries while `h-mad/scripts/h_mad_doc_shape_check.py`'s `REQUIRED_SECTIONS["design"]` remains untouched at `7`), and `h-mad/agents/design-author.md` (Rule 11 requiring `## Test Boundaries` and `h_mad_test_boundaries_check.py` self-check before `DESIGN-AUTHOR: DONE`).
2. **Component 2 (`FR-2`, `FR-3`, `FR-4.1`, `FR-4.2`, `AC-2.1`..`AC-4.3`):** Full architecture, data structures (`Issue`, `CheckResult`), constants (`EXPECTED_COLUMNS` with `REQUIRED_COLUMNS = EXPECTED_COLUMNS` alias, `PRE_EXISTING_FEATURES`, `REASON_CODES`, `PLACEHOLDER_EXACT`, `PLACEHOLDER_PREFIXES`, `MOCKED_NONE_PREFIXES`, `TAUTOLOGICAL_EXACT`, `TAUTOLOGICAL_RE`, `VERIFIED_BY_KINDS`, `HEAD_AC_RE`, `RETIRED_LINE_RE`, `CELL_AC_RE`), and public/helper functions (`has_test_boundaries_heading`, `resolve_spec_path`, `extract_spec_acs`, `should_activate_design_check`, `normalize_cell`, `is_placeholder_cell`, `is_tautological_oracle`, `has_proving_artifact`, `validate_non_test_row`, `check_design`, `format_check_result`, `main`) for `h-mad/scripts/h_mad_test_boundaries_check.py`.
3. **Component 3 (`FR-4.2`, `AC-4.2`..`AC-4.4`):** Structural locators and exact helper functions (`_DESIGN_AUDIT_RE`, `_load_test_boundaries_checker` using `importlib.util.spec_from_file_location`, `_candidate_design_paths`, `_run_design_boundaries_checks`) in `h-mad/scripts/h_mad_audit_gate.py`, preserving the exact two-line mutation anchor `    stamped = ""\n    if args.gated and verdict == "PASS":` required by `audit_suite_gate.json` and `audit_gate_stamp.json`.
4. **Component 4 (`FR-5`, `AC-5.1`):** Structural locators and exact `{{ONLY:design}}...{{/ONLY}}` block in `h-mad/audit-prompt.template.md` plus Phase 4 `## Test Boundaries` rubric in `h-mad/agents/doc-auditor.md` (formatted so no literal `{{ONLY:design}}` token appears in `hmad-test-boundaries.design.md`, keeping `h_mad_assemble_audit.py` clean).
5. **Component 5 (`FR-6`, `AC-6.1`..`AC-6.3`):** Architecture of `h-mad/tests/test_h_mad_test_boundaries_check.py` (including isolated-loading parity tests, two-direction connection-enforcement tests, 3-design archived calibration asserting `< 200ms` via `time.monotonic()`, and 5 broken fixture classes) and `h-mad/tests/mutation-specs/test_boundaries_gate.json` (`6` mutations covering both connection directions in `h_mad_audit_gate.py` and core guards in `h_mad_test_boundaries_check.py`).
6. **Self-Validating `## Test Boundaries` Section (`AC-1.3`):** 7 rows covering all 17 active ACs (`AC-1.1`..`AC-6.3`) with concrete independent expected result sources (`(verified by: ...)`), explicit mocked dependencies (`none` or `tmp_path` isolation), and explicit exclusions.

## 2. Tree Verification & Reconciliation Notes

- **Verified Premises at `HEAD` (`9f330f71d65b5e667bd42a92065e77b9bd030d82`):**
  - `h_mad_doc_shape_check.REQUIRED_SECTIONS["design"]` = `7` headings (`['Executive Summary', 'Overview', 'Architecture', 'Detailed Design', 'Implementation Order', 'Test Plan', 'Version History']`).
  - `h-mad/references/inline-protocols.md` Phase 4 template = `13` `## ` headings before this change (`14` after adding `## Test Boundaries`).
  - `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` = `7` entries before this change (`8` after adding `"Test Boundaries"`).
  - `git ls-files 'docs/**/*.design.md' | wc -l` = `39` (`10` in `docs/02-design/features/`, `29` in `docs/archive/`), `0` of which currently contain `Test Boundaries`.
  - Reference spec AC counts verified against the live files: `hmad-test-boundaries.spec.md` = `17` active / `0` retired; `exec-path-hardening.spec.md` = `24` active / `0` retired; `audit-report-docs-copy.spec.md` = `40` active / `0` retired; `tdd-gate-fail-opens.spec.md` = `44` active / `0` retired; `grok-audit-surface.spec.md` = `63` active / `1` retired (`AC-3.7`).
- **Note on Spec Premise 3 (`docs/01-plan/features/hmad-test-boundaries.spec.md`):**
  - `spec.md` Premise 3 states that `4` of the `10` pre-existing `.design.md` files in `docs/02-design/features/` have a paired `.spec.md` in `docs/01-plan/features/` and `6` do not. In `git ls-files 'docs/01-plan/features/*.spec.md'`, the exact `4` paired specs are `exec-missing-report-recovery`, `orca-native-orchestration`, `orca-native-transport`, and `tdd-dispatch-verification-discipline` (`spec.md` Premise 3's parenthetical list had named `claude-context-reduction` and `hemasuite-100-percent` instead of `orca-native-orchestration` and `orca-native-transport`). `hmad-test-boundaries.design.md` states the exact verified list from `git ls-files` while preserving `PRE_EXISTING_FEATURES` with all `10` stems (`FR-4.1`). No spec edit was made per `design-author` scope rules.
- **Note on Column Names & Failure Codes:**
  - The approved `spec.md` (`v1.3`), `plan.md` (`v1.3`), and `docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md` all pin the 5 column headers `| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |` and the 10 failure codes (`missing_section`, `missing_table`, `invalid_columns`, `empty_cell`, `placeholder_cell`, `tautological_oracle`, `invalid_non_test_row`, `missing_spec`, `uncovered_ac`, `unknown_ac`). `hmad-test-boundaries.design.md` implements the `spec.md`/`plan.md` contract verbatim, aliases `REQUIRED_COLUMNS = EXPECTED_COLUMNS`, and includes `(verified by: ...)` provenance in every row of its own `## Test Boundaries` table.

## 3. Self-Check Verification Outputs

All 4 mandatory self-checks passed with 0 issues:

1. **`h_mad_precheck_doc.py`:**
   ```text
   PRECHECK: PASS issues=0
   [H-MAD] precheck hmad-test-boundaries.design.md PASS issues=0
   ```
2. **`h_mad_doc_shape_check.py`:**
   ```text
   DOC-SHAPE: PASS path=docs/02-design/features/hmad-test-boundaries.design.md type=design
   ```
3. **`h_mad_ac_census.py`:**
   ```text
   ACS: OK count=17 frs=6
   ```
4. **`h_mad_assemble_audit.py`:**
   ```text
   ASSEMBLE: PASS /tmp/preflight_design_v1.0.prompt.md 249576B (243.7 KB) sentinel=AUDIT-hmad-test-boundaries-design-v1 size_status=unverified
   ```
