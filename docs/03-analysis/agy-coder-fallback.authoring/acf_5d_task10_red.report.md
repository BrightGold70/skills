Files changed:
- h-mad/tests/test_h_mad_assemble_tdd_agent.py

pytest output (last 10 lines of the final requested scoped run):
```text
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_unwired_halts_with_exit_0[self-check-failed]
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_unreadable_halts_with_exit_2
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_no_token_halts_with_exit_2
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_check_timeout_halts_with_exit_2
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_wired_writes_the_prompt
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_default_timeouts[agy-1500]
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_docstring_states_the_agy_halt_exit_rule
FAILED h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_docstring_drops_the_any_halt_rule
ERROR h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_docstring_drops_the_any_halt_rule
==================== 16 failed, 12 passed, 1 error in 3.33s ====================
```

Commands and results:
- `rtk proxy hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_assemble_tdd_agent.py -v`: 16 failed, 12 passed. The 18 new-or-extended nodes split exactly 16 F / 2 P; all 10 other nodes are passing existing guards. Initial run: same split; final run after adding the assembly spy: same split.
- `rtk proxy hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_assemble_tdd.py -v --tb=short`: all 107 tests passed, including TestCli::test_a_clean_assembly_prints_pass_and_the_command_block.
- Each pytest process also reported the coordinator's known leak-reaper teardown ERROR: sandbox PermissionError running ps. This is an environmental teardown artifact, not a failed test assertion, and does not determine STATUS.
- `git diff --check`: passed.
- Final `git status --short`: only the assigned test file modified.

Self-review findings:
- RED only: no production code, mutation rows, anchors, runtime state, or unrelated repository files changed.
- Added the exact WIRE-PIN, all seven UNWIRED reasons, malformed JSON, missing token, checker timeout, WIRED success, three default-timeout ids, both docstring rules, and three-agent prompt independence.
- The WIRE-PIN patches AGY_WIRING_CHECK with raising=False and invokes the actual assembler main through run_main, which catches argparse SystemExit. The stub records argv; the test checks exact argv, exact ordered stdout, no call to assemble, no prompt, and exit 0.
- WIRE-PIN failure mode, quoted: "AssertionError: main must run the agy wiring check before assembling". The argv record is absent. This is the caller's missing observable invocation, never ImportError, AttributeError, or NameError.
- The fixture consumes the Orca stub with HMAD_STUB_HOSTILE=all. HOME retains shell/glob/markdown/newline/Unicode payloads, sanitizing slash and colon inside its component. PATH entries are colon-free. The fixture installs the real gate symlink and an isolated python3; hooks.json uses the exact FR-5 entry. run_cli now accepts environment overrides.
- UNWIRED and UNREADABLE tests assert HALT, indented checker token and final marker separately from exit status. Silent/timeout tests assert both ordered output lines before exit status. All halt cases assert prompt absence.
- The timeout test patches AGY_WIRING_TIMEOUT_S to 1 with raising=False, sleeps 5 seconds in the checker, and requires completion in less than 4 seconds; silently ignoring the configured bound will fail.
- Both docstring tests inspect the actual module docstring; no missing-symbol REDs.
- Existing guards were preserved without weakening. All relevant behavior assertions remain meaningful after GREEN; no forced failures.
- AC-5.1/5.2, AC-9.1, marker discipline and wire invocation all have corresponding tests. Mutation discrimination and AC-X remain GREEN-phase checks by explicit coordinator instruction.
- OneContext skill was located and consulted; its context command reported that history is unavailable outside the OneContext environment. No historical assumptions were needed.
- No task-id/coordinator-handle was supplied, so no worker_done message is applicable.

Concerns: This dispatch is verified RED, so the production agy path remains unimplemented and 16 new-or-extended nodes intentionally fail. Phase 5e must implement the behavior and establish GREEN, wire-cut/converse mutation discrimination, and the seven-spec anchor check before the full Task 10 acceptance criteria can be claimed. DONE_WITH_CONCERNS is used because this template reserves DONE for GREEN; the RED split itself matches exactly.

Per-node RED acceptance evidence for the assigned test file (all 28 collected nodes; all failing nodes are property-naming AssertionErrors):
- FAIL test_agent_agy_runs_the_wiring_check_before_assembling: invokes h_mad_assemble_tdd.main through run_main, the caller that must run the check; "main must run the agy wiring check before assembling"; record absent; behavioral wiring RED, no missing symbol.
- FAIL test_agent_agy_unwired_halts_with_exit_0[no-hooks-file]: invokes h_mad_assemble_tdd.main through run_cli; "no-hooks-file must print the agy wiring HALT first"; absent stdout is caught before exit 0 is asserted.
- FAIL test_agent_agy_unwired_halts_with_exit_0[no-entry]: invokes main through run_cli; "no-entry must print the agy wiring HALT first"; behavioral HALT propagation assertion.
- FAIL test_agent_agy_unwired_halts_with_exit_0[disabled]: invokes main through run_cli; "disabled must print the agy wiring HALT first"; behavioral HALT propagation assertion.
- FAIL test_agent_agy_unwired_halts_with_exit_0[matcher-narrow]: invokes main through run_cli; "matcher-narrow must print the agy wiring HALT first"; behavioral HALT propagation assertion.
- FAIL test_agent_agy_unwired_halts_with_exit_0[bad-command]: invokes main through run_cli; "bad-command must print the agy wiring HALT first"; behavioral HALT propagation assertion.
- FAIL test_agent_agy_unwired_halts_with_exit_0[timeout-below-floor]: invokes main through run_cli; "timeout-below-floor must print the agy wiring HALT first"; behavioral HALT propagation assertion.
- FAIL test_agent_agy_unwired_halts_with_exit_0[self-check-failed]: invokes main through run_cli; "self-check-failed must print the agy wiring HALT first"; behavioral HALT propagation assertion; fake self-check returns FAIL with rc 0 to reject rc-only judgment.
- FAIL test_agent_agy_unreadable_halts_with_exit_2: invokes main through run_cli; "unreadable hooks must print the agy wiring HALT"; behavioral HALT assertion, not an exit-only argparse false positive.
- FAIL test_agent_agy_no_token_halts_with_exit_2: invokes main through run_main with a real silent checker stub; "a checker with no token must print the no-token HALT then the marker"; behavioral output assertion before exit 2.
- FAIL test_agent_agy_check_timeout_halts_with_exit_2: invokes main through run_main with a real sleeping checker stub; "a checker timeout must print the no-token HALT then the marker"; behavioral output assertion before exit 2 and elapsed-time bound.
- FAIL test_agent_agy_wired_writes_the_prompt: invokes main through run_cli with WIRED configuration; "WIRED must allow assembly"; behavioral PASS assertion; subsequent assertions require prompt, agy dispatch and timeout 1500.
- PASS test_agent_default_timeouts[codex-900]: invokes main through run_cli, where agent timeout selection occurs; non-vacuous: deleting/changing codex's selected default or its command propagation removes "--timeout 900" and fails.
- PASS test_agent_default_timeouts[grok-1500]: invokes main through run_cli, where agent timeout selection occurs; non-vacuous: deleting/changing grok's default or its propagation removes "--timeout 1500" and fails.
- FAIL test_agent_default_timeouts[agy-1500]: invokes main through run_cli; "main must select the 1500 second default for agy"; behavioral command assertion with actual argparse rejection shown as diagnostic.
- FAIL test_docstring_states_the_agy_halt_exit_rule: inspects h_mad_assemble_tdd.__doc__, the documentation under test; "the module docstring must state the agy UNWIRED exit-0 rule"; documentation-content RED, not a missing symbol.
- FAIL test_docstring_drops_the_any_halt_rule: inspects h_mad_assemble_tdd.__doc__; "the docstring must drop the obsolete any-HALT exit rule"; documentation-content RED.
- FAIL test_prompt_file_is_agent_independent: invokes main through run_cli for codex, grok and agy after provisioning WIRED once; "--agent agy must stage a prompt independently"; behavioral missing-prompt assertion; after GREEN requires exactly three equal hashes.
- PASS test_no_agent_output_is_byte_identical_to_base: invokes current and archived assembler main through run_cli; non-vacuous: changing/deleting default-agent output or prompt rendering breaks exact stdout/prompt byte comparison.
- PASS test_agent_grok_block_names_exec_grok_with_1500: invokes main through run_cli; non-vacuous: dropping agent propagation or the grok command/default fails dispatch/timeout assertions. Its root still has no hooks.json, so a forced check for every agent will HALT and fail this guard.
- PASS test_agent_grok_explicit_timeout_wins[--timeout 600]: invokes main through run_cli; non-vacuous: deleting explicit-timeout precedence changes the selected 600 seconds and fails.
- PASS test_agent_grok_explicit_timeout_wins[--timeout 900]: invokes main through run_cli; non-vacuous: deleting explicit-timeout precedence changes the selected 900 seconds and fails.
- PASS test_agent_grok_explicit_timeout_wins[--timeout=900]: invokes main through run_cli; non-vacuous: removing equals-form parsing/precedence eliminates the requested 900-second command and fails.
- PASS test_agent_grok_explicit_timeout_wins[--ti 900]: invokes main through run_cli; non-vacuous: removing abbreviation parsing/precedence eliminates the requested 900-second command and fails.
- PASS test_agent_codex_default_timeout_is_900: invokes main through run_cli; non-vacuous: changing/deleting the codex default removes "--timeout 900". Its root has no hooks.json, so a forced check also fails this guard.
- PASS test_unknown_agent_exits_2_and_writes_no_prompt: invokes main through run_cli, where argparse validates agent choices; non-vacuous: allowing the unknown agent removes the invalid-choice diagnostic and fails.
- PASS test_state_fallback_agent_is_not_read: invokes main through run_cli, where the default selector is chosen; non-vacuous: honoring the hostile/default-overriding state fallback changes codex to grok and fails the dispatch assertion.
- PASS test_command_block_derives_grok_from_the_codex_line: invokes h_mad_assemble_tdd.command_block directly, the function containing command generation; non-vacuous: dropping grok derivation or changing later command lines breaks the asserted first-line/rest-of-block relationship.

Summary: RED verified at 16 F / 2 P across the 18 new-or-extended nodes; 10 existing agent guards and all 107 assembler regression tests passed. Production files untouched. Report completion marker is written only after this report.

🌱 graft saved ~127,254 tokens this turn, 3 calls.

STATUS: DONE_WITH_CONCERNS

