Files changed:
- h-mad/scripts/h_mad_hook_wiring.py
- h-mad/tests/mutation-specs/hook_wiring_agy.json

Implemented Task 9 (Phase 5e GREEN): --agy dispatches to check_agy and returns its one-line verdict and exit code. FR-5 reasons run in order. JSON read errors percent-encode the path; exact shlex command matching, strict enabled and integer timeout checks, the live h_mad_tdd_judge.JUDGE_BUDGET_S-derived floor, and the 30-second real gate self-check are enforced. Existing CLI behavior is preserved.

pytest output (last 10 lines):

Command: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_hook_wiring_agy.py -v
Log: /private/tmp/t9green-agy-pytest.log
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_hook_wiring_agy.py::test_empty_matcher_counts_as_wide
========================= 18 passed, 1 error in 1.46s ==========================
```

Regression command: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_hook_wiring.py -q
Log: /private/tmp/t9green-regression-pytest.log
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_hook_wiring.py::test_bootstrap_obliges_the_wiring_check_to_be_run
30 passed, 1 error in 0.34s
```

Self-review findings:
- Baseline commit: 2a57481b892c5e327ac6d24f1f5479c7835e5083; initial working tree clean. Actual checked-out branch: feature/agy-coder-fallback.
- Baseline reproduced the expected 18 failing new nodes; all 30 regression assertions passed from the first run. Four direct check_agy tests initially raised AttributeError for the new symbol, with behavioral assertions remaining after the call.
- Final verification: all 18 new nodes and all 30 regression assertions pass. AC-5.1 and AC-5.2 are covered, including the four live-budget cases, real installed-path gate self-check, unreadable configuration, and empty matcher.
- The documented sandbox leak-reaper teardown artifact (ps PermissionError) occurs after passing assertions, causes pytest exit 1, and was present at baseline. Per coordinator instruction, it does not determine STATUS. No fixture or test was changed to suppress it.
- Both test files and hook_wiring.json are unchanged. Its unknown-exits-0 row remains byte for byte.
- Eight new mutation rows have unique anchors, symbol=check_agy, _mechanism and test fields. The connection row replaces math.ceil(h_mad_tdd_judge.JUDGE_BUDGET_S + 20) with 60; the budget-41.1/timeout-61 assertion distinguishes this from the live formula. No source assertion evasions or out-of-scope production edits.
- Mutation harness was invoked only with --check-anchors, as instructed; the coordinator owns the scoring sweep. MUTATION: ALL_CAUGHT is not claimed here.
- New spec anchor result: ANCHORS: ANCHORS_OK specs=1 mutations=8 ok=8 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- New spec harness last line: [H-MAD] anchors ANCHORS_OK
- Existing spec anchor result: ANCHORS: ANCHORS_OK specs=1 mutations=12 ok=12 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Existing spec harness last line: [H-MAD] anchors ANCHORS_OK
- git diff --check passed. No full suite or mutation sweep was run. No commits or workflow-state changes were made.
- OneContext was attempted per repository instructions but is unavailable outside its dashboard session; the current task and checked-in FR-5 design supplied the implementation requirements.

Concerns: none.

🌱 graft saved ~20,716 tokens this turn, 2 calls.
STATUS: DONE
