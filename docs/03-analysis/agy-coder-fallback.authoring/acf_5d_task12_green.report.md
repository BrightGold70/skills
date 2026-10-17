Files changed (paths)
- h-mad/scripts/h_mad_phase7_preconditions.py
- h-mad/tests/mutation-specs/phase7_review_independence.json (new)

pytest output (last 10 lines)
```text
E       AssertionError: assert not [{'code': 'review_independence_unrecorded', 'detail': '6a-prime review independence is unrecorded; authors=unrecorded'}]

=========================== short test summary info ============================
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestParkedMutationSpecs::test_a_parked_spec_with_a_live_twin_is_provenance_not_a_blocker
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestParkedMutationSpecs::test_no_pending_dir_is_silent
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestParkedMutationSpecs::test_no_specs_dir_at_all_is_a_warning_not_a_verdict
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestParkedMutationSpecs::test_no_docs_root_skips_with_a_warning_never_derives_from_the_analysis_path
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestVersionedAnalysis::test_a_versioned_analysis_is_ready
ERROR h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_warning_lines_print_through_main
==================== 5 failed, 66 passed, 1 error in 1.32s =====================
```

Command: /Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_phase7_preconditions.py -v

Self-review findings
- Reproduced the expected RED behavior before production edits: TestReviewIndependence had 16 failed and 5 passed (plus the known sandbox teardown error).
- All 21 TestReviewIndependence nodes now pass, including hostile-module fixtures, consistency validation, routing-independent triggers, sorted distinct entry authors, readiness preservation, and main's warning output. AC-7.1, AC-7.2 and the switch/recovery fixture pass.
- Added _review_independence_warnings using property_valid and the agent/boolean consistency check. check extends warnings immediately before its existing return; blockers and main are unchanged. Missing or malformed 6a-prime evidence warns for all three reviewed archreview values. Detail reads only well-formed 5e review entries.
- Added the four requested mutation rows, each pinned to symbol _review_independence_warnings. Existing mutation rows were not edited.
- Anchor check command: /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/phase7_analysis_anchor.json h-mad/tests/mutation-specs/phase7_preconditions_gates.json h-mad/tests/mutation-specs/phase7_review_independence.json
- Anchor summary: ANCHORS: ANCHORS_OK specs=3 mutations=18 ok=18 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Anchor command's last line: `[H-MAD] anchors ANCHORS_OK`
- New spec alone accounts for 4/4 matching, symbol-pinned anchors. No mutation execution was attempted, as instructed; AC-X MUTATION: ALL_CAUGHT remains for coordinator scoring.
- git diff --check passed. No tests were edited or weakened, no suite outside the specified file was run, and no source-count evasion was performed.

Blockers: Five existing assertions conflict with the newly required warning. Their READY fixtures contain archreview=READY_TO_MERGE without well-formed 6a-prime review evidence, so FR-7 requires review_independence_unrecorded. These assertions demand no warnings or an exact pre-FR-7 set:
- h-mad/tests/test_h_mad_phase7_preconditions.py:354 — test_a_parked_spec_with_a_live_twin_is_provenance_not_a_blocker: `assert result["ready"] and not result["warnings"]`.
- h-mad/tests/test_h_mad_phase7_preconditions.py:367 — test_no_pending_dir_is_silent: same empty-warning assertion.
- h-mad/tests/test_h_mad_phase7_preconditions.py:379 — test_no_specs_dir_at_all_is_a_warning_not_a_verdict: exact warning set {pending_specs_unverified}.
- h-mad/tests/test_h_mad_phase7_preconditions.py:385 — test_no_docs_root_skips_with_a_warning_never_derives_from_the_analysis_path: exact warning set {pending_specs_unverified, analysis_versions_unverified}.
- h-mad/tests/test_h_mad_phase7_preconditions.py:492 — test_a_versioned_analysis_is_ready: `assert not result["warnings"]`.

Stopped under the dispatch's test-conflict rule. Coordinator must reconcile these existing test fixtures/assertions with FR-7 before the scoped file can be GREEN. Suppressing the required warning to satisfy these assertions would violate the design. Production implementation and mutation rows are retained for review.

The known leak-reaper teardown ERROR is PermissionError from sandbox-blocked `ps` in h-mad/tests/leak_reaper.py:34, reached via conftest.py:183. It does not determine STATUS; the five behavioral assertion failures do.

Graft saved approximately 84,165 tokens across 3 calls.

STATUS: BLOCKED
