Files changed:
- h-mad/tests/test_h_mad_phase7_preconditions.py — added TestReviewIndependence (21 collected nodes), class-local fixtures/helpers, and the pytest import. Existing tests unchanged.
- Delivery artifacts: this report and its .done marker.

pytest output (last 10 lines):
```text
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_implementer[claude]
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_archreview_value[READY_TO_MERGE]
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_archreview_value[WITH_FIXES]
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_fires_for_each_archreview_value[NO]
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_malformed_6a_prime_entry_is_not_recorded
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_detail_names_entry_authors_not_routing
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_unrecorded_detail_without_5e_entries_says_unrecorded
FAILED h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_warning_lines_print_through_main
ERROR h-mad/tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence::test_warning_lines_print_through_main
==================== 16 failed, 55 passed, 1 error in 1.00s ====================
```

Summary:
Phase 5d RED is complete. The 21 new nodes split exactly as requested: 16 failed, 5 passed. All 50 existing tests passed on the first and repeat scoped runs.
Command: hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_phase7_preconditions.py -v
No production code or mutation specs were modified; no mutation sweep or anchor check was run, per the coordinator's RED-only instruction. git diff --check passed.
The actual warnings are asserted through p7.check; CLI output is asserted through p7.main calling the real p7.check. No warning helper is mocked or imported. All 16 RED failures are AssertionError failures naming the relevant behavior; none is an ImportError, AttributeError, NameError, or manufactured pytest.fail.

Self-review findings:
- AC-7.1: per-entry non-independent and malformed warnings, per-implementer unrecorded warning, and unchanged ready/blockers are covered.
- AC-7.2: all five routing fixtures, all three archreview trigger values, and all four quiet cases are covered.
- The required recovery fixture uses implementer_switch.to=agy and exactly one well-formed 5e entry implemented by codex; its assertion excludes agy from the detail. A second check in the same test covers sorted distinct authors using grok/codex/grok entries. implementation_authors also names agy, so its unrelated attribution cannot satisfy the assertion.
- Malformed fixtures test two malformed entries per list, both directions of a contradictory independence boolean, and one non-list field warning.
- A malformed 6a-prime is required to produce both malformed and unrecorded warnings.
- Non-independent warnings must preserve leg, hostile module text, and agent; main must print all three warning codes and the exact returned details.
- Agent/human free-form module values come from the real tests/stubs/orca knob HMAD_STUB_HOSTILE=all, with assertions confirming markdown, newline, and marker payloads; structured enum values remain the exact task-defined values.
- Readiness stability checks both a ready record and an already blocked record, for non-independent entries, malformed entries, a non-list field, and an empty list.
- No existing test was changed, weakened, or forced to fail. No production source was changed. No fixture touches live routing state.
- No task-id or coordinator handle was provided, so worker_done emission is not applicable.

RED acceptance evidence (one line per new node; all names are under tests/test_h_mad_phase7_preconditions.py::TestReviewIndependence):
1. test_non_independent_entry_warns — FAIL; p7.check via _check is the actual production entry point containing warning integration; AssertionError "review_non_independent must warn once per non-independent entry" (0 versus 2); behavioral missing-warning failure, not missing-symbol failure; later assertions require each leg/module/agent detail and stable readiness.
2. test_malformed_entry_warns[bad-leg] — FAIL; invokes actual p7.check; AssertionError "review_independence_malformed must warn 2 times for bad-leg"; behavioral missing-warning failure, not missing-symbol failure.
3. test_malformed_entry_warns[lying-boolean] — FAIL; invokes actual p7.check; AssertionError "review_independence_malformed must warn 2 times for lying-boolean"; behavioral missing-warning failure, not missing-symbol failure; fixtures cover equal agents with true and unequal agents with false.
4. test_malformed_entry_warns[field-not-a-list] — FAIL; invokes actual p7.check; AssertionError "review_independence_malformed must warn 1 times for field-not-a-list"; behavioral missing-warning failure, not missing-symbol failure.
5. test_unrecorded_fires_for_each_implementer[codex-field-absent] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire independently of routing {}"; behavioral missing-warning failure, not missing-symbol failure.
6. test_unrecorded_fires_for_each_implementer[codex] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and routing implementer=codex; behavioral missing-warning failure, not missing-symbol failure.
7. test_unrecorded_fires_for_each_implementer[agy] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and routing implementer=agy; behavioral missing-warning failure, not missing-symbol failure.
8. test_unrecorded_fires_for_each_implementer[grok] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and implementer_switch.to=grok; behavioral missing-warning failure, not missing-symbol failure.
9. test_unrecorded_fires_for_each_implementer[claude] — FAIL; invokes actual p7.check; AssertionError names review_independence_unrecorded and implementer_switch.to=claude; behavioral missing-warning failure, not missing-symbol failure.
10. test_unrecorded_fires_for_each_archreview_value[READY_TO_MERGE] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=READY_TO_MERGE"; behavioral missing-warning failure, not missing-symbol failure.
11. test_unrecorded_fires_for_each_archreview_value[WITH_FIXES] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=WITH_FIXES"; behavioral missing-warning failure, not missing-symbol failure.
12. test_unrecorded_fires_for_each_archreview_value[NO] — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must fire for archreview=NO"; behavioral missing-warning failure, not missing-symbol failure.
13. test_unrecorded_is_quiet[has-6a-prime-entry] — PASS; invokes actual p7.check; deleting warning emission entirely would still pass (yes); prescribed negative guard checks silence with a valid independent 6a-prime entry; generation is separately pinned by the failing unrecorded cases.
14. test_unrecorded_is_quiet[archreview-absent] — PASS; invokes actual p7.check; deleting warning emission entirely would still pass (yes); prescribed negative guard checks silence with absent archreview; generation is separately pinned by the three failing archreview trigger cases.
15. test_unrecorded_is_quiet[SKIPPED_NO_PANE] — PASS; invokes actual p7.check; deleting warning emission entirely would still pass (yes); prescribed negative guard checks silence for this skipped status; generation is separately pinned by the three failing archreview trigger cases.
16. test_unrecorded_is_quiet[SKIPPED_OPERATOR_OVERRIDE] — PASS; invokes actual p7.check; deleting warning emission entirely would still pass (yes); prescribed negative guard checks silence for explicit override and valid independent entries; generation is separately pinned by the failing warning-presence cases.
17. test_malformed_6a_prime_entry_is_not_recorded — FAIL; invokes actual p7.check; AssertionError "a malformed 6a-prime must warn as malformed AND leave review independence unrecorded"; behavioral missing-warning failure, not missing-symbol failure.
18. test_unrecorded_detail_names_entry_authors_not_routing — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must expose entry authors"; behavioral missing-warning failure, not missing-symbol failure; subsequent assertions require codex, exclude agy, and check sorted distinct authors.
19. test_unrecorded_detail_without_5e_entries_says_unrecorded — FAIL; invokes actual p7.check; AssertionError "review_independence_unrecorded must warn when the entry list is empty"; behavioral missing-warning failure, not missing-symbol failure; subsequent assertion requires authors=unrecorded.
20. test_warnings_never_move_ready — PASS; invokes actual p7.check repeatedly on ready and blocked controls; deleting warning emission entirely would still pass (yes); prescribed invariant guard checks exact ready/blockers stability while failing presence tests independently pin generation.
21. test_warning_lines_print_through_main — FAIL; invokes actual p7.main, which calls actual p7.check and owns the WARNING printing loop; AssertionError "main must print WARNING review_non_independent: <detail>"; output is "PHASE7: READY blockers=0" plus the H-MAD marker with no WARNING lines; behavioral missing-output failure, not missing-symbol failure.

Concerns:
- The five explicitly requested passing guards necessarily pass when warning generation is absent, as the specified RED split requires. Thus they cannot independently establish warning generation under the generic deletion/vacuity rule; they are retained as prescribed guards and paired with 16 behavioral presence assertions. No failure was manufactured and no expected count was reconciled away.
- This is a completed RED deliverable, not GREEN: the 16 intentional behavioral failures remain for Phase 5e, and AC-X mutation verification remains pending there. DONE_WITH_CONCERNS is used because the report contract reserves DONE for GREEN.
- Known sandbox artifact: session leak-reaper teardown attempts ps and raises PermissionError at h-mad/tests/conftest.py:183, producing one teardown ERROR. This does not change the 16/5 new-node split or the status, per the coordinator instruction.
- OneContext could not provide history outside its dashboard session; the current design FR-7 and checked-in implementation were used directly.

🌱 graft saved ~34,556 tokens this turn, 3 calls.
STATUS: DONE_WITH_CONCERNS
