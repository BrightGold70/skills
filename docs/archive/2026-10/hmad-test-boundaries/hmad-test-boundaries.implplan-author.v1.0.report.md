# Impl-Plan Author Report: `hmad-test-boundaries` (`v1.0`)

```
IMPLPLAN-AUTHOR: DONE version=v1.0 tasks=5 wiring=1 mutation_rows=8 path=docs/01-plan/features/hmad-test-boundaries.impl-plan.md lines=811 sha256=3b2895b86bfe59bbe9e0d42f905326773037df95a8aac86a49ef8ee823eff150
REPORT=docs/03-analysis/hmad-test-boundaries.implplan-author.v1.0.report.md
```

## 1. Premise Verification Against Working Tree (`HEAD = c8df5312bebfad93d95019db604686af3a5de068`)

1. **Input document versions on disk**:
   - `docs/01-plan/features/hmad-test-boundaries.spec.md`: `v1.5` (`17` active ACs across `6` FRs: `FR-1`..`FR-6`, `AC-1.1`..`AC-6.3`).
   - `docs/01-plan/features/hmad-test-boundaries.plan.md`: `v1.3`.
   - `docs/02-design/features/hmad-test-boundaries.design.md`: `v1.2` (`913` lines).
   - `.h-mad/invariants.md`: `I1`..`I7`.
2. **Template & shape-check premises**:
   - `REQUIRED_SECTIONS["design"]` in `h-mad/scripts/h_mad_doc_shape_check.py`: `7` headings (`['Executive Summary', 'Overview', 'Architecture', 'Detailed Design', 'Implementation Order', 'Test Plan', 'Version History']`), kept untouched per `FR-1.3` / `AC-1.2`.
   - Phase 4 design template in `h-mad/references/inline-protocols.md`: `13` `## ` headings before Task 2 (`14` after inserting `## Test Boundaries` between `## Test Plan` and `## Invariant Compliance`).
   - `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py`: `7` entries before Task 2 (`8` after adding `"Test Boundaries"` after `"Test Strategy"`).
3. **Existing files modified (`6`) & new files created (`3`)**:
   - Modified (`6`): `h-mad/references/inline-protocols.md`, `h-mad/agents/design-author.md`, `h-mad/scripts/h_mad_audit_gate.py`, `h-mad/audit-prompt.template.md`, `h-mad/agents/doc-auditor.md`, `h-mad/tests/test_h_mad_doc_templates.py`.
   - New (`3`): `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`.
4. **Active mutation spec non-interference (`I5`)**:
   - Checked all `40` files in `h-mad/tests/mutation-specs/*.json`; `14` reference one or more of the `6` modified files (`archreview_oversize_halt.json`, `audit_gate_nested_bullets.json`, `audit_gate_stamp.json`, `audit_leg_set_gate.json`, `audit_suite_gate.json`, `author_done_line.json`, `author_report_path.json`, `collect_report.json`, `grok_audit_surface.json`, `probe_hygiene_and_h8_extensions.json`, `suite_lock.json`, `suite_tree_digest.json`, `tdd_judge_wiring.json`, `wire_registry_runner.json`).
   - Verified `0` overlapping anchors with our planned edit sites, specifically preserving `stamped = ""\n    if args.gated and verdict == "PASS":` in `h-mad/scripts/h_mad_audit_gate.py`.

## 2. Rule 12 Override / Contradiction Notice (Dispatch Brief vs. Audited `design.md` `v1.2`)

Per `h-mad/agents/implplan-author.md` Rule 1 ("Verify every premise against the tree before writing it"), Rule 3 ("the total of per-task mutation rows equals the design's stated total"), and Rule 12 ("Announce the override, give the reasoning, offer the revert. If the brief contradicts the tree, file it; do not work around it"):
- **Contradiction observed**: Item 4 of the dispatch prompt listed class/test names (`TestHeadingAndFenceIsolation`, `TestMarkdownTableParserAndHeaderCheck`, `TestCellGrammarAndClassifier`, `TestSectionAbsenceAndEmptyTable`, `TestCrossReferenceComponentCoverage`, `test_exempt_no_production_code_passes_without_rows`, `audit_prompt_and_doc_auditor_real_or_mock_lens`, `TestMutationSpecContract::test_mutation_spec_json_has_18_mutations_and_passes_anchor_check`) and `M01`..`M18` (`18` mutations) from an obsolete/superseded mental draft that does not exist anywhere in the repository (`grep -rn "test_exempt_no_production_code" docs/ h-mad/` returned `0` matches).
- **Resolution**: `docs/01-plan/features/hmad-test-boundaries.impl-plan.md` (`v1.0`) faithfully implements the audited `docs/02-design/features/hmad-test-boundaries.design.md` (`v1.2`), `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.5`), and `docs/01-plan/features/hmad-test-boundaries.plan.md` (`v1.3`) on disk:
  - 5-column `## Test Boundaries` table (`Public interface | Acceptance criteria | Expected result source | Mocked dependencies | Exclusions`),
  - 7 test classes (`34` test methods) in `h-mad/tests/test_h_mad_test_boundaries_check.py`: `TestDesignAuthorAndSelfBootstrap`, `TestCliAndTableValidation`, `TestSpecAcCoverageAndNonTestRows`, `TestExemptionsAndAuditGateIntegration`, `TestAuditPromptAndDocAuditorContract`, `TestArchivedCalibrationAndPerformance`, `TestSeededBrokenFixtures`,
  - `8` mutation rows in `h-mad/tests/mutation-specs/test_boundaries_gate.json` (`2` two-direction connection mutations on `scripts/h_mad_audit_gate.py` + `6` guard mutations on `scripts/h_mad_test_boundaries_check.py`), matching `design.md` (`v1.2`) §5.2 verbatim.
- **Revert offer**: If the operator wishes to rename the test classes or expand `test_boundaries_gate.json` from `8` to `18` mutations, `design.md` §5.1–5.2 and `impl-plan.md` can be updated together in a subsequent revision.

## 3. Verification Script Outputs

All 4 required H-MAD verification gates were executed against `docs/01-plan/features/hmad-test-boundaries.impl-plan.md`:

1. **`h_mad_precheck_doc.py`**:
   ```
   python3 h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills
   PRECHECK: PASS issues=0
   [H-MAD] precheck hmad-test-boundaries.impl-plan.md PASS issues=0
   ```
2. **`h_mad_ac_census.py`**:
   ```
   python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.impl-plan.md
   ACS: OK count=17 frs=6
   ```
3. **`h_mad_wire_pin_gate.py`**:
   ```
   python3 h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md
   WIREPIN: PASS tasks=5 wiring=1 unpinned=0 mislabeled=0
   [H-MAD] hmad-test-boundaries wirepin PASS
   ```
4. **`h_mad_prescribed_block_guards.py`**:
   ```
   python3 h-mad/scripts/h_mad_prescribed_block_guards.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md --repo-root /Users/kimhawk/orca/skills
   PRESCRIBED-BLOCKS: PASS checked=1 skipped=4 guards=0
   ```
