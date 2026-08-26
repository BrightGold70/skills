I have completed the final architectural review for Phase 6a-prime, thoroughly inspecting the implementation and tests across both projects (`h-mad` and `handoff`).

The single-source contract around `_resolve_root` is structurally sound. The integration of `classify_spec_file` successfully keys on `_load_spec`'s own gate without introducing a second definition. Sibling scoping in `run_spec` is implemented exactly as designed, correctly preserving the pre-existing test vectors and the `REFUSED` verdict for self-drift.

However, there are two Critical invariant violations that must be fixed before this can merge. 

## Critical Issues

1. **Guard Narrowing Invariant Violation (Missing AC-6.6)**
   - **File:** `h-mad/tests/test_h_mad_mutation_harness.py`
   - **What's wrong:** The differential corpus test defined in AC-6.6 is entirely missing. The current implementation verifies that the classifier agrees with `_load_spec` (AC-6.1), but it does not execute the specified 8-shape corpus through both the pre-change classification and the post-change classification to diff their verdicts.
   - **Why it matters:** This is a hard violation of the Guard Narrowing invariant. Without explicitly diffing against the pre-change baseline and accounting for every softened verdict against an enumerated intended list, the classifier might introduce unintended silent softenings that remain unverified.
   - **How to fix:** Implement AC-6.6 as stated in the implementation plan (Task 3). Define the 8 enumerated shapes, run them through the old baseline validation path versus the new classifier path, diff the results, and strictly assert the expected relaxations.
   - **Operator override:** No. Invariants (Axis B) cannot be overridden.

2. **Connection Enforcement Invariant Violation (Vacuous Wire-Pin Pass)**
   - **File:** `h-mad/tests/test_h_mad_mutation_harness.py:L941-945` (inside `test_clean_spec_beside_a_drifted_sibling_refuses_before_mutating`)
   - **What's wrong:** The test asserts that the sibling precheck fires *before* mutating by verifying that `result` lacks `"caught"`/`"survived"` keys and that the target file is byte-identical at the end. This is a vacuous pass: `run_spec` builds a fresh return dictionary when `PRECHECK_FAILED` triggers (omitting those keys by construction), and the mutation loop natively restores the tree on exit regardless.
   - **Why it matters:** If the sibling precheck block were incorrectly moved to the very end of `run_spec` (after all baseline mutation runs had executed), this test would still pass. This violates the Connection Enforcement invariant, as the connection could fire incorrectly and still certify itself as correct.
   - **How to fix:** Explicitly assert that no mutations were executed. You can use `monkeypatch.setattr("h_mad_mutation_harness._suite_is_green", MagicMock(side_effect=Exception("Should not be called")))` (or target `_run`) to definitively prove that the run aborted *before* applying any mutations.
   - **Operator override:** No. Invariants (Axis B) cannot be overridden.

ASSESSMENT: WITH_FIXES
