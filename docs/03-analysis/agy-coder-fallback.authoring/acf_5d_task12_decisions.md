# agy-coder-fallback — 5d Task 12 decisions

## D5d-5 · five existing guards pinned an exact warning set that FR-7 now extends (2026-10-17)
- **Found by:** Codex GREEN (`STATUS: BLOCKED`, `acf_5d_task12_green.report.md`), reproduced:
  `5 failed, 66 passed`. The shared `READY` record carries `archreview=READY_TO_MERGE` and no
  `review_independence`, so FR-7's `review_independence_unrecorded` correctly fires. Five tests
  assert no warnings or an exact pre-FR-7 set:
  `TestParkedMutationSpecs::{test_a_parked_spec_with_a_live_twin_is_provenance_not_a_blocker,
  test_no_pending_dir_is_silent, test_no_specs_dir_at_all_is_a_warning_not_a_verdict,
  test_no_docs_root_skips_with_a_warning_never_derives_from_the_analysis_path}`,
  `TestVersionedAnalysis::test_a_versioned_analysis_is_ready`.
- **Plan gap:** impl-plan Task 12 says no existing row/test is touched; its "Regression guards"
  did not account for guards that pin the whole warning set.
- **Settlement (orchestrator):** a module constant `REVIEWED = dict(READY,
  review_independence=[<one well-formed 6a-prime entry>])`, used by exactly those five tests in
  place of `READY`. Every assertion is byte-identical; each test's subject (pending-spec and
  analysis-version warnings) is unchanged. `READY` itself is not changed — the new
  `TestReviewIndependence` tests need a record with no 6a-prime entry. Codex correctly refused
  to suppress the warning.
- **Gates (outside sandbox):** file `71 passed`; `phase7_analysis_anchor` 8/8,
  `phase7_preconditions_gates` 6/6 (was `BASELINE_NOT_GREEN` only from these five),
  `phase7_review_independence` 4/4 (symbols set) `ALL_CAUGHT`; anchors OK 18/18; revert probe
  `16 failed, 55 passed` = RED split.
- **Owed:** impl-plan Task 12 regression-guard paragraph to name the `REVIEWED` fixture at the
  next impl-plan revision.
