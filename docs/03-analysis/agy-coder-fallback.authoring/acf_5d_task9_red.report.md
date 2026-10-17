Files changed (paths)
- h-mad/tests/test_h_mad_hook_wiring_agy.py (new; the only worktree change)
- Delivery artifacts: /private/tmp/claude-501/-Users-kimhawk-orca-skills/c83a0ffe-4d6b-4b3a-bac9-efa79608444a/scratchpad/acf5d/t9red_report.md and /private/tmp/claude-501/-Users-kimhawk-orca-skills/c83a0ffe-4d6b-4b3a-bac9-efa79608444a/scratchpad/acf5d/t9red_report.md.done

pytest output (last 10 lines)

New RED tests, command:
`rtk proxy hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_hook_wiring_agy.py -v`
```text
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_unreadable_hooks_file[not-json]
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_unreadable_hooks_file[not-an-object]
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_wired - AssertionError...
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget[budget-40-timeout-59]
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget[budget-40-timeout-60]
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget[budget-41.1-timeout-61]
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_timeout_floor_is_derived_from_the_judge_budget[budget-41.1-timeout-62]
FAILED h-mad/tests/test_h_mad_hook_wiring_agy.py::test_empty_matcher_counts_as_wide
ERROR h-mad/tests/test_h_mad_hook_wiring_agy.py::test_empty_matcher_counts_as_wide
========================= 18 failed, 1 error in 8.32s ==========================
```

Unmodified regression guards, command:
`rtk proxy hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_hook_wiring.py -v`
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_hook_wiring.py::test_bootstrap_obliges_the_wiring_check_to_be_run
========================= 30 passed, 1 error in 0.29s ==========================
```

Self-review findings
- Phase 5d RED is complete: exactly 18 collected new nodes, 18 FAIL, 0 PASS; existing guards: 30 PASS, 0 FAIL on their first run.
- Known sandbox artefact (reported once, excluded from STATUS): both scoped runs have a session leak-reaper teardown ERROR at conftest.py:183 because subprocess ps raises PermissionError [Errno 1]. Test bodies have the expected counts. No fixture or production changes were made to suppress this.
- Production h_mad_hook_wiring.py, existing test_h_mad_hook_wiring.py, and mutation specs have no diff. git status lists only the new test file. Whitespace check emitted no diagnostics.
- AC-5.1: ten independent fixture variants cover all seven reasons plus nonobject entry, missing PreToolUse, and absent timeout.
- AC-5.2: each CLI test checks its exact single stdout line before its separate exit-code assertion, including the two UNREADABLE cases; healthy and empty-matcher fixtures retain the HOME symlink to the real gate.
- Live-budget connection: imports match the adjacent tests, using by-name h_mad_hook_wiring and h_mad_tdd_judge. Budget changes occur after those imports. Four direct-call cases retain behaviour assertions and separate exit-code assertions.
- Hostile fixtures consume the real shared orca stub with HMAD_STUB_HOSTILE=all, using its returned markdown, glob metacharacters, Unicode stamp markers, newline and tab in project/HOME names. Only slash and colon are replaced in path components. Bad-command also receives the original hostile payload. No PATH entry contains a colon.
- No production writes, mutation rows, full-suite runs, commits or external notifications. AC-X mutation sweep and existing hook_wiring.json anchor verification remain Phase 5e work as directed; no mutation success is claimed.
- OneContext lookup was attempted under workspace instructions; its CLI reports unavailable outside its dashboard environment. FR-5 and the agy runtime/docs supply the requirements without a context blocker.
- No new test passes at RED, so the new-test passing/vacuity audit has zero entries. The 30 explicitly labelled existing guards were left intact and were not forced RED.
- Runtime scope: only the two requested pytest files were run, sequentially under the bounded dispatcher. The production main branch that prints WIRING: UNKNOWN was untouched.

RED acceptance evidence — one line per new test
The 14 CLI tests invoke the real existing main(), which currently rejects the newly specified flag. Their assertions name the intended property, rather than accepting argparse's exit code. Once implemented, main() must dispatch to check_agy, which owns FR-5. The four direct-call tests introduce a NEW symbol and therefore legitimately fail on AttributeError at RED, as explicitly required by Task 9; each retains its later behavioural assertion.

- `test_unwired_reason[no-hooks-file]`: FAIL, behavioural assertion names `no-hooks-file` (missing project hooks file); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[no-entry]`: FAIL, behavioural assertion names `no-entry` (required named entry absent despite a healthy sibling); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[entry-not-object]`: FAIL, behavioural assertion names `no-entry` (required entry is a list); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[disabled]`: FAIL, behavioural assertion names `disabled` (enabled is false); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[matcher-narrow]`: FAIL, behavioural assertion names `matcher-narrow` (only write_to_file is matched); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[pretooluse-absent]`: FAIL, behavioural assertion names `matcher-narrow` (healthy group exists only under PostToolUse); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[bad-command]`: FAIL, behavioural assertion names `bad-command` (extra shell text and hostile payload after the expected command); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[timeout-below-floor]`: FAIL, behavioural assertion names `timeout-below-floor` (handler timeout is 59); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[timeout-absent]`: FAIL, behavioural assertion names `timeout-below-floor` (omitted timeout implies agy's default 30); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unwired_reason[self-check-failed]`: FAIL, behavioural assertion names `self-check-failed` (PATH python3 returns a FAIL token with exit 0); invokes CLI `h_mad_hook_wiring.main()` through `_run(root)`, the owner of the new --agy dispatch to `check_agy`; failure mode: stdout is empty, stderr says "unrecognized arguments: --agy"; asserts exact UNWIRED line and separately exit 0 once implemented.
- `test_unreadable_hooks_file[not-json]`: FAIL, behavioural assertion names UNREADABLE, percent-encoded file path and JSONDecodeError; invokes CLI `main()` -> intended `check_agy`; empty stdout from absent --agy fails the line assertion BEFORE the separate exit-2 assertion. This is not a false RED based on argparse exit 2.
- `test_unreadable_hooks_file[not-an-object]`: FAIL, behavioural assertion names UNREADABLE, percent-encoded file path and not-an-object; invokes CLI `main()` -> intended `check_agy`; empty stdout from absent --agy fails the line assertion BEFORE the separate exit-2 assertion.
- `test_wired`: FAIL, behavioural assertion names WIRED after the real gate's self-check; invokes CLI `main()` -> intended `check_agy`; empty stdout / unrecognized --agy; exact WIRED stdout and separate exit 0 remain meaningful after GREEN.
- `test_timeout_floor_is_derived_from_the_judge_budget[budget-40-timeout-59]`: FAIL, NEW-SYMBOL case explicitly permitted by Task 9: "AttributeError: module 'h_mad_hook_wiring' has no attribute 'check_agy'"; calls `hw.check_agy(root)` directly, the future budget-check owner; subsequent assertion requires timeout-below-floor at budget 40.0 / timeout 59, separately exit 0. The exception names the new symbol, while the test name/retained assertion names the budget property.
- `test_timeout_floor_is_derived_from_the_judge_budget[budget-40-timeout-60]`: FAIL, NEW-SYMBOL case: "AttributeError: module 'h_mad_hook_wiring' has no attribute 'check_agy'"; directly calls `hw.check_agy(root)`; retained assertion requires WIRED at budget 40.0 / timeout 60 and separately exit 0.
- `test_timeout_floor_is_derived_from_the_judge_budget[budget-41.1-timeout-61]`: FAIL, NEW-SYMBOL case: "AttributeError: module 'h_mad_hook_wiring' has no attribute 'check_agy'"; directly calls `hw.check_agy(root)` after patching the by-name judge module's budget to 41.1; retained assertion requires timeout-below-floor at timeout 61 (ceil(61.1) = 62) and separately exit 0. This discriminates a hardcoded 60 or an import-time budget copy after GREEN; this dispatch is new-behaviour, not WIRE-PIN.
- `test_timeout_floor_is_derived_from_the_judge_budget[budget-41.1-timeout-62]`: FAIL, NEW-SYMBOL case: "AttributeError: module 'h_mad_hook_wiring' has no attribute 'check_agy'"; directly calls `hw.check_agy(root)` after the live budget patch; retained assertion requires WIRED at timeout 62 and separately exit 0.
- `test_empty_matcher_counts_as_wide`: FAIL, behavioural assertion names empty matcher as wide and absent enabled as true; invokes CLI `main()` -> intended `check_agy`; empty stdout / unrecognized --agy; retains exact WIRED stdout and separate exit 0 checks.

Passing regression guard evidence — one line per guard
Counterfactual statements below are assertion inspection, not mutation runs. Documentation/source-presence guards protect the literal/documented contract their names describe; no broader claim about their mutation strength is made.

- `TestTheHealthyShape::test_both_hooks_wired_is_clean`: PASS; invokes `hw.check`; checks that healthy wiring produces no issues. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestTheHealthyShape::test_match_all_matchers_cover_everything`: PASS; invokes `hw.check`; checks that match-all matchers cover required tools. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestTheHealthyShape::test_env_vars_and_tildes_in_the_command_are_expanded`: PASS; invokes `hw.check`; checks that environment variables and tildes expand. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestTheHealthyShape::test_hook_inside_a_longer_command_still_counts`: PASS; invokes `hw.check`; checks that hook paths inside longer shell commands are recognized. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestTheHealthyShape::test_sources_are_merged_not_overridden`: PASS; invokes `hw.check`; checks that settings sources merge. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_missing_hook_is_reported_by_name`: PASS; invokes `hw.check`; checks that missing required hooks are reported. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_a_matcher_covering_half_the_surface_fails`: PASS; invokes `hw.check`; checks that partially covered surfaces are reported. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_a_matcher_for_the_wrong_tool_fails`: PASS; invokes `hw.check`; checks that wrong-tool matchers are rejected. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_an_invalid_regex_matcher_is_not_a_pass`: PASS; invokes `hw.check`; checks that invalid regex is not accepted as coverage. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_a_command_naming_a_missing_file_is_stale`: PASS; invokes `hw.check`; checks that stale hook paths are reported. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_the_advisory_wired_under_pretooluse_is_not_wired`: PASS; invokes `hw.check`; checks that advisory must be on PostToolUse. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_a_narrow_postooluse_matcher_leaves_tools_uncovered`: PASS; invokes `hw.check`; checks that narrow advisory matchers report uncovered tools. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestWhatItCatches::test_wired_twice_with_one_good_matcher_is_covered`: PASS; invokes `hw.check`; checks that coverage may come from a healthy duplicate entry. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestCannotJudge::test_no_readable_settings_is_not_a_failure`: PASS; invokes `hw.check`; checks that unread settings yields read_anything false. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestCannotJudge::test_malformed_json_does_not_hide_a_readable_sibling`: PASS; invokes `hw.check`; checks that malformed source does not hide a readable sibling. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestCannotJudge::test_only_malformed_sources_is_a_cannot_judge`: PASS; invokes `hw.check`; checks that only malformed sources are cannot-judge. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestCannotJudge::test_settings_without_hooks_is_read_but_unwired`: PASS; invokes `hw.check`; checks that readable settings without hooks report missing hooks. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestSourceResolution::test_claude_config_dir_relocates_the_user_scope`: PASS; invokes `hw.settings_sources`; checks that CLAUDE_CONFIG_DIR relocates the source. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestSourceResolution::test_project_settings_are_searched_up_the_tree`: PASS; invokes `hw.settings_sources`; checks that project source discovery walks upward. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestSourceResolution::test_a_hook_wired_by_an_ancestor_counts_as_wired`: PASS; invokes `hw.check`; checks that ancestor settings contribute wiring. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestCli::test_unknown_exits_2_and_carries_no_issue_count`: PASS; invokes `CLI main()`; checks that UNKNOWN prints no issue count and exits 2. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `TestCli::test_fail_prints_a_verdict_then_detail_lines_and_exits_0`: PASS; invokes `CLI main()`; checks that FAIL prints verdict/details and exits 0. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_every_required_hook_exists_in_the_checkout`: PASS; invokes `Path.is_file over hw.REQUIRED_HOOKS`; checks that required hooks exist. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_docs_name_the_command_and_all_three_verdicts`: PASS; invokes `_wiring_section / SKILL.md`; checks that command and three verdict tokens are documented. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_docs_forbid_halting_bootstrap_on_a_wiring_failure`: PASS; invokes `_wiring_section / SKILL.md`; checks that no-halt rule is documented. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_every_detail_line_is_documented_with_a_remedy_and_implemented`: PASS; invokes `_wiring_section / SKILL.md and SCRIPT.read_text`; checks that detail tokens and runnable remedies remain present. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_docs_explain_the_uncovered_field_and_the_source_search`: PASS; invokes `_wiring_section / SKILL.md`; checks that uncovered field and source search are documented. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_docs_say_wiring_is_only_confirmable_live`: PASS; invokes `_wiring_section / SKILL.md`; checks that live verification limitation is documented. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_helper_registry_lists_it`: PASS; invokes `SKILL_MD.read_text`; checks that helper registry names the checker. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.
- `test_bootstrap_obliges_the_wiring_check_to_be_run`: PASS; invokes `SKILL_MD.read_text`; checks that bootstrap instructs running the checker. Deleting that named contract/token would fail its assertion; no assertion was altered and no failure was manufactured.

Concerns: The delivered suite intentionally remains RED because production --agy/check_agy is absent; Phase 5e must implement it and run the eight mutation rows plus the existing anchor check. This is the requested phase boundary, not an unexpected RED-count discrepancy. DONE_WITH_CONCERNS reflects the template's rule that DONE requires GREEN; the known ps teardown artefact does not decide STATUS.

Summary: Added only the requested test module; verified 18 failing new tests, zero passing new tests, and all 30 unmodified regression guards passing.

🌱 graft saved ~102,926 tokens this turn, 1 call.

STATUS: DONE_WITH_CONCERNS

