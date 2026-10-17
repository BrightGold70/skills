Files changed:
- h-mad/tests/test_h_mad_agy_authorship_docs.py (new; the only repository change)
- This report and its completion marker are delivery artifacts outside the repository.

pytest output (last 10 lines):
```text
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_phase5_authorship_section_names_the_resolver_and_agy_authorship
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_phase5_authorship_section_states_the_agy_upgrade_trigger
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_exit_code_dispatch_section_lists_exec_agy_as_an_implementer
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_teammate_bullet_separates_audit_selection_from_authorship
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_agy_runtime_tdd_gate_names_the_agy_gate_and_keeps_the_halt
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_agy_runtime_sessionstart_claim_is_rechecked_and_stamped
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_staging_step_runs_the_verb_with_record_and_names_every_branch
FAILED h-mad/tests/test_h_mad_agy_authorship_docs.py::test_staging_step_halts_on_record_failed_before_any_dispatch
ERROR h-mad/tests/test_h_mad_agy_authorship_docs.py::test_record_failed_check_rejects_a_procedure_that_dispatches
==================== 8 failed, 1 passed, 1 error in 12.24s =====================
```

Commands and results:
- RED: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agy_authorship_docs.py -v
- Observed test-body split: exactly 8 failed, 1 passed, matching the dispatch.
- Guards: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_grok_fallback_docs.py h-mad/tests/test_h_mad_tdd_gate_docs.py h-mad/tests/test_h_mad_context_budget_docs.py -v
- All 59 regression-guard test bodies passed on their first run.
- Known sandbox artifact in both runs: the session leak-reaper teardown raises PermissionError when executing ps. Each run reports one teardown ERROR; this is the coordinator-described artifact, not a test-body discrepancy or an input to STATUS.

Self-review findings:
- RED scope complete: all nine requested test functions are present, with the exact requested names.
- Production documentation was not modified; no mutation rows were added, no full-suite run occurred, and no commit was made.
- Section extraction uses docsections.titled_section. Teammate/staging bullets use the existing anchor-and-blank-paragraph split.
- Existing Phase 5 heading, authorship sentence, and teammate anchor are explicitly pinned.
- Staging checks pin the full resolver command including --record, token-vs-exit-status instruction, dispatch timing, agent staging, peer switches, and every named branch.
- Both SessionStart surfaces are checked independently for the obsolete denial and the 1.4.0 stamp.
- The discriminating control uses the shared orca stub with HMAD_STUB_HOSTILE=all and a 30-second subprocess timeout, so its synthetic agent-authored procedure includes markdown, newline, tab and marker payloads.
- The control first proves acceptance of a valid procedure, then rejects all four required doctored versions; a constant-False checker cannot satisfy it.
- Whitespace check produced no diagnostics; git status confirms only the new test file, and the production-document diff is empty.
- OneContext context retrieval was attempted as required by workspace policy but is unavailable outside a OneContext dashboard. The supplied dispatch and current repository files provide the test requirements.

Required per-test RED evidence (all names below are in h-mad/tests/test_h_mad_agy_authorship_docs.py):
1. test_phase5_authorship_section_names_the_resolver_and_agy_authorship — FAIL, AssertionError: "Phase 5 authorship must document 'h_mad_tdd_judge.py implementer'". Yes, the message names the missing resolver contract. Actual invocation: _section -> docsections.titled_section on the Phase 5 authorship section, followed by assertions on that document body. This is a missing-documentation behavior assertion, not a missing-symbol/import failure.
2. test_phase5_authorship_section_states_the_agy_upgrade_trigger — FAIL, AssertionError: "Phase 5 authorship must require re-verification after any agy upgrade". Yes, it names the upgrade trigger. Actual invocation: _section -> docsections.titled_section on the Phase 5 authorship section, then regex/token assertions for FR-8 steps 2/2a and the inventory. Documentation assertion, not a missing-symbol/import failure.
3. test_exit_code_dispatch_section_lists_exec_agy_as_an_implementer — FAIL, AssertionError: "exit-code dispatch must name exec agy as an implementer on the same line". Yes, it names the dispatch property. Actual invocation: _section -> docsections.titled_section on the exit-code dispatch section, followed by line/token assertions including TDD-IMPLEMENTER:. Documentation assertion, not a missing-symbol/import failure.
4. test_teammate_bullet_separates_audit_selection_from_authorship — FAIL, AssertionError: "teammate audit/authorship bullet must state 'h_mad_tdd_judge.py implementer'". Yes, it names the separation/resolver property. Actual invocation: Path.read_text and the existing _skill_gate_bullet anchor/split procedure, then token assertions on that exact bullet. Documentation assertion, not a missing-symbol/import failure.
5. test_agy_runtime_tdd_gate_names_the_agy_gate_and_keeps_the_halt — FAIL, AssertionError: "agy TDD gate contract must document 'h-mad-agy-tdd-gate.py'". Yes, it names the missing gate. Actual invocation: _section -> docsections.titled_section on agy-runtime.md's The TDD gate, followed by gate/token/halt assertions. Documentation assertion, not a missing-symbol/import failure.
6. test_agy_runtime_sessionstart_claim_is_rechecked_and_stamped — FAIL, AssertionError: "Hooks must remove the obsolete 'no SessionStart' claim". Yes, it names the stale claim. Actual invocation: _section -> docsections.titled_section for Hooks and Construct mapping, extraction of the hook-event row, then independent claim/version assertions. Documentation assertion, not a missing-symbol/import failure.
7. test_staging_step_runs_the_verb_with_record_and_names_every_branch — FAIL, AssertionError: "SKILL.md must contain exactly one '- **Stage the implementer.**' bullet with the resolver command and fail-closed dispatch branches". Yes, it names the missing staging contract. Actual invocation: _staging_bullet -> Path.read_text, failing its explicit missing-bullet assertion. Once the bullet exists, the same test checks the command, --record, token handling and all branches. No ImportError/AttributeError/NameError.
8. test_staging_step_halts_on_record_failed_before_any_dispatch — FAIL with the same explicit missing-staging-bullet AssertionError. Yes, the message names the missing prerequisite. Actual invocation: _staging_bullet; record_failed_branch_refuses_dispatch cannot yet be called on the absent shipped bullet. The test explicitly asserts its True result after that prerequisite exists, and item 9 already exercises the function's behavior. No ImportError/AttributeError/NameError.
9. test_record_failed_check_rejects_a_procedure_that_dispatches — PASS, labelled discriminating control. Actual invocation: record_failed_branch_refuses_dispatch on one valid hostile procedure and all four doctored procedures (dispatch instruction, deleted halt sentence, dropped marker, and wrong branch ordering). It would not pass if the named rejection behavior were removed: an always-True checker fails the negative controls, an always-False checker fails the positive control, and removing the halt/marker/order checks admits their corresponding doctored input. Not vacuous.

Concerns: The required eight documentation contracts remain intentionally RED. GREEN documentation implementation and the eight mutation rows/anchor sweep remain unverified and belong to the subsequent Phase 5e dispatch; this report claims only completion of Phase 5d.

RED implementation complete: expected 8F/1P established, all 59 regression guard bodies passed, and production files are untouched.
🌱 graft saved ~55,696 tokens this turn, 1 call.
STATUS: DONE_WITH_CONCERNS

