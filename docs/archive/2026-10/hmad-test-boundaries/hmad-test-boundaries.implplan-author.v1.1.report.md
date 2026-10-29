IMPLPLAN-AUTHOR: DONE version=v1.1 tasks=5 wiring=1 mutation_rows=8 path=docs/01-plan/features/hmad-test-boundaries.impl-plan.md lines=936 sha256=f85d24a432d08fca856b9f71153d65f8457af180143cbfebca35d6aa8785302d
REPORT=docs/03-analysis/hmad-test-boundaries.implplan-author.v1.1.report.md

## Resolution of Phase 5b Audit Cycle 1 Findings (`v1.p1` & `v1.p2`)

### `v1.p1` (`codex`, 5 must-fix, 2 should-fix)
1. **Must-fix #1 (`none — explanation` / `none (explanation)` placeholder assertion outside column 4):**
   - Updated Task 1 (`is_placeholder_cell` contract and `TestCliAndTableValidation::test_mocked_dependencies_allows_none_and_none_explanations_only_in_col_4`) so bare `"none"` (in `PLACEHOLDER_EXACT`) is accepted in `Mocked dependencies` (column 4) and rejected as `placeholder_cell` in columns 1, 2, 3, and 5, while explanatory `"none — ..."` / `"none (...)"` phrases are accepted in `Mocked dependencies` and pass `is_placeholder_cell` (`False`) in the other 4 columns per `spec.md` `v1.5` `FR-2.4` Residual (where column-specific rules in `FR-2.5` and `FR-3` then evaluate them, e.g. `invalid_columns` zero-AC check in `Acceptance criteria`).
2. **Must-fix #2 (`infer_project_root` archive-root formula):**
   - Reconciled `infer_project_root` in Task 1 so that when `"docs"` and `"archive"` appear as adjacent segments `("docs", "archive")` in `abs_design.parts[:-1]`, it finds the index `i` where `abs_design.parts[i : i + 2] == ("docs", "archive")` and returns `Path(*abs_design.parts[:i])` (the ancestor immediately above `"docs"`, e.g. `/project` for `/project/docs/archive/2026-08/demo/demo.design.md` regardless of archive nesting depth), and added a direct unit-test assertion on `/project/docs/archive/2026-08/demo/demo.design.md` -> `/project` in `TestCliAndTableValidation::test_infer_project_root_and_two_branch_resolve_spec_path_from_external_cwd`.
3. **Must-fix #3 (Task 2 template table assertion in `test_h_mad_doc_templates.py`):**
   - Added `test_design_template_contains_test_boundaries_five_column_table` in `h-mad/tests/test_h_mad_doc_templates.py` (`7 -> 8` pytest nodes) asserting that `_template_blocks()["design"]` has `14` headings with `"Test Boundaries"` between `"Test Plan"` and `"Invariant Compliance"` and that the `## Test Boundaries` section body contains the 5-column Markdown pipe table header `| Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions |` and separator row `|---|---|---|---|---|`.
4. **Must-fix #4 (Task 3 activated-success `PASS` and `EXEMPT` gate cases for `AC-4.3`):**
   - Added `TestExemptionsAndAuditGateIntegration::test_gate_passes_and_writes_stamp_when_activated_design_passes_or_is_exempt` in Task 3 asserting that when `h_mad_audit_gate.py` runs on a clean `must=0 should=0` report with `--gated` pointing to (a) an activated `.design.md` that passes (`TEST-BOUNDARIES: PASS ...`) and (b) an activated `.design.md` that is exempt (`TEST-BOUNDARIES: EXEMPT ...`), `h_mad_audit_gate.py` emits `GATE: PASS`, prints the `TEST-BOUNDARIES: PASS` / `TEST-BOUNDARIES: EXEMPT` line immediately after `GATE:` / `GATE-CLASS:` / `GATE-LEGS:`, and writes a valid `.gated.json` stamp (`--verify-stamp` -> `STAMP: CURRENT`).
5. **Must-fix #5 (Non-Interference with Active Mutation Specs corpus census):**
   - Re-derived the Non-Interference table across all `178` tracked JSON files in `h-mad/tests/mutation-specs/*.json` using an inline runnable `python3 -c` command and recorded the exact observed counts and `find` anchors.
6. **Should-fix #1 (`_candidate_design_paths` existence filtering before fallback):**
   - Updated `_candidate_design_paths` in Task 3 to check `if path.name.endswith(".design.md") and path.exists():` (and `if candidate.exists():` on positional fallback) so a nonexistent explicit `--gated missing.design.md` falls back to positional `<feature>.design.audit.v1.md` candidate resolution, and added a test case for this in `TestExemptionsAndAuditGateIntegration::test_gate_fails_and_suppresses_stamp_when_design_boundaries_fail`.
7. **Should-fix #2 (Verification pointer and AC-2.2/2.3/2.4 labels):**
   - Fixed the `AC-1.2` verification matrix pointer to `h-mad/tests/test_h_mad_doc_shape_check.py::TestMirrorFidelity::test_required_sections_match_the_live_validator`, and aligned Task 1's `AC-2.2` (missing section/table, invalid columns, fenced code blocks), `AC-2.3` (empty/placeholder cells and `Mocked dependencies = none`), and `AC-2.4` (tautological oracle + provenance suffix stripping) labels and matrix rows with `spec.md` `v1.5`.

### `v1.p2` (`agy`, 4 must-fix, 2 should-fix, 1 nit)
1. **Must-fix #1 (Move all `h_mad_test_boundaries_check.py` tests into Task 1 so no unlabelled new test passes at RED):**
   - Moved `TestDesignAuthorAndSelfBootstrap::test_hmad_test_boundaries_design_passes_self_check`, `TestArchivedCalibrationAndPerformance` (`4` methods), and the `5` `test_seeded_broken_*` methods of `TestSeededBrokenFixtures` into **Task 1** (`24` methods total in Task 1, `24 F, 0 P` at RED, `0 F, 24 P` at GREEN, and all `6` Task 1 mutation rows reference test node IDs created in Task 1).
2. **Must-fix #2 (Remove fabricated `I1`/`I4`/`I5`/`I7` invariant IDs and drop the `<= 6` `## ` section assertion):**
   - Replaced all `I1`/`I4`/`I5`/`I7` shorthand references with exact invariant section names in `h-mad/invariants.base.md` and `.h-mad/invariants.md`, and removed the `<= 6` `## ` section count assertion from Tasks 2 and 4.
3. **Must-fix #3 (Inline complete helper and `Issue` coordinate contracts into Task 1):**
   - Inlined the exact `normalize_cell`, `is_placeholder_cell`, `is_tautological_oracle` (including `PROVENANCE_SUFFIX_RE` stripping inside `is_tautological_oracle`), `has_proving_artifact`, `validate_non_test_row`, `extract_spec_acs`, and `Issue(row, col, code, detail)` coordinate and deterministic ordering contracts into Task 1.
4. **Must-fix #4 (Non-Interference table counts and anchors):**
   - Replaced the fabricated `40`-file count and inaccurate spec/anchor attributions with the verified `178`-file sweep, exact referencing spec lists (`1`, `3`, `11`, `1`, `1`, `0`), and real `find` anchors.
5. **Should-fix #1 (Label regression guards `--guard` in Tasks 2, 3, 4, 5 RED specifications):**
   - Explicitly labeled all regression guards (`--guard`) and `--expect-fail` / `--expect-pass` counts in Tasks 2, 3, 4, and 5 (including `test_gate_does_not_activate_on_bare_synthetic_design_in_tmp_path` in Task 3).
6. **Should-fix #2 (Exclude `test_mutation_spec_schema_and_check_anchors_pass` from `test_boundaries_gate.json`'s `"command"`):**
   - Set `"command"` in `h-mad/tests/mutation-specs/test_boundaries_gate.json` to `["python3.11", "-m", "pytest", "tests/test_h_mad_test_boundaries_check.py", "-k", "not test_mutation_spec_schema_and_check_anchors_pass", "-q"]` so active mutations on disk do not trigger `ANCHORS_DRIFTED` inside `test_mutation_spec_schema_and_check_anchors_pass` during mutation runs.
7. **Nit #1 (`<skill_dir>` parenthetical phrasing in Task 2):**
   - Updated Task 2's `design-author.md` Rule `7a.` block to `(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. \`h-mad\` in this checkout, ...)` matching `design.md` `v1.2` line 144 while passing `h_mad_precheck_doc.py --phase impl-plan`.

## Verification Output
- `python3 h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills` → `PRECHECK: PASS issues=0`
- `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.impl-plan.md` → `ACS: OK count=17 frs=6`
- `python3 h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md` → `WIREPIN: PASS tasks=5 wiring=1 unpinned=0 mislabeled=0`
- `python3 h-mad/scripts/h_mad_prescribed_block_guards.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md --repo-root /Users/kimhawk/orca/skills` → `PRESCRIBED-BLOCKS: PASS checked=1 skipped=4 guards=0`
