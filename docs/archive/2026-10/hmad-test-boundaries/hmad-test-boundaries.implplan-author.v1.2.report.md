IMPLPLAN-AUTHOR: DONE version=v1.2 tasks=5 wiring=1 mutation_rows=8 path=docs/01-plan/features/hmad-test-boundaries.impl-plan.md lines=950 sha256=1519fb50e8ae1e5207786a3dfa2984cd9ed80892c4c563cc0388daf70562066e
REPORT=docs/03-analysis/hmad-test-boundaries.implplan-author.v1.2.report.md

## Resolution of Phase 5b Audit Cycle 2 Findings (`v2.p1` & `v2.p2`)

### `v2.p1` (`codex`, 1 must-fix, 1 should-fix)
1. **Must-fix #1 (Operational-input error precedence on non-exempt designs vs structural early returns):**
   - Updated Task 1 (`check_design` item 6, Steps 6a–6e) so that after checking `<design_path>` readability (Step 6a) and checking whether the design is exempt (Step 6b: `if not has_section and not no_exempt:`), for any **non-exempt** design (including one missing `## Test Boundaries`), `check_design` validates the paired `spec_path` for operational-input errors (`UNREADABLE`, exit `2`) in Step 6c **before** evaluating section/table structural early returns (`missing_section`, `missing_table`, header `invalid_columns`) in Step 6d:
     - When `spec_path is not None` (explicit `--spec <spec_path>`), if `not spec_candidate.exists()`, `spec_candidate.is_dir()`, or reading/decoding raises `(OSError, UnicodeDecodeError)`, `check_design` returns `CheckResult(status="UNREADABLE", exit_code=2, path=str(spec_candidate), error_type=type(exc).__name__)` immediately.
     - When `spec_path is None` (default-resolved `spec_candidate = resolve_spec_path(design_path, None, root)`) and `spec_candidate.exists()` is `True`, if `spec_candidate.is_dir()` or reading/decoding raises `(OSError, UnicodeDecodeError)`, `check_design` returns `CheckResult(status="UNREADABLE", exit_code=2, path=str(spec_candidate), error_type=type(exc).__name__)` immediately.
     - Only after confirming neither `<design_path>` nor `spec_path` has an operational-input `UNREADABLE` error does `check_design` evaluate the structural early returns (`missing_section`, `missing_table`, header `invalid_columns`) in Step 6d and record `missing_spec` (when `spec_path is None` and `not spec_candidate.exists()`) in Step 6e.
   - This makes Task 1's `check_design` contract and Task 3's `test_unreadable_paired_spec_fails_gate_closed` 100% consistent, and `TestCliAndTableValidation::test_cli_tokens_and_unreadable_vs_missing_spec_disambiguation` in Task 1 explicitly covers the combined-invalid case (non-exempt design omitting `## Test Boundaries` paired with an unreadable `.spec.md` -> `TEST-BOUNDARIES: UNREADABLE`, exit `2`).
2. **Should-fix #1 (Task 2 explanatory substring backtick match):**
   - Aligned Task 2's prescribed Rule `7a.` block in `h-mad/agents/design-author.md` and `TestDesignAuthorAndSelfBootstrap::test_design_author_requires_test_boundaries_and_pre_done_check` to use the exact same spelling `(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout` without inline backtick mismatch so a literal substring assertion passes.

### `v2.p2` (`agy`, 0 must-fix, 0 should-fix, 1 nit)
1. **Nit #1 (`test_h_mad_audit_spec_axis.py` test count in Task 4):**
   - Updated Task 4's GREEN verification note for `h-mad/tests/test_h_mad_audit_spec_axis.py` from `14` existing tests (`0 F, 14 P`) to `16` existing tests (`0 F, 16 P`).

## Verification Output
- `python3 h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills` → `PRECHECK: PASS issues=0`
- `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.impl-plan.md` → `ACS: OK count=17 frs=6`
- `python3 h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md` → `WIREPIN: PASS tasks=5 wiring=1 unpinned=0 mislabeled=0`
- `python3 h-mad/scripts/h_mad_prescribed_block_guards.py docs/01-plan/features/hmad-test-boundaries.impl-plan.md --repo-root /Users/kimhawk/orca/skills` → `PRESCRIBED-BLOCKS: PASS checked=1 skipped=4 guards=0`
