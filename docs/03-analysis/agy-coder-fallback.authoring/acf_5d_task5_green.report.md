Files changed:
- h-mad/hooks/h-mad-agy-tdd-gate.py (new, executable)
- h-mad/tests/mutation-specs/agy_tdd_gate.json (new, five symbol-pinned rows)

Implemented Task 5's bounded stdin reader, complete case-sensitive classification table, early class-(a) allowance, canonical git-root resolution and single chdir, shared activity scan, workspace cross-check under active/unknown only, and fail-closed class-(d) handling. Classes (b) and (c) deliberately use the same conservative rule pending Tasks 6 and 7. Normal hook decisions print exactly once from finally and exit 0. Self-check emits the exact PASS or FAIL line, with verdict failures returning 0 and operational import failures returning 2. Exception details never enter reasons, preserving the single trailing kind token even with hostile input.

pytest output (last 10 lines):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_agy_tdd_gate.py::test_self_check_policy_fail_is_a_verdict_with_exit_0[shell-policy]
========================= 31 passed, 1 error in 1.71s ==========================
```

Verification:
- Baseline before production edits: 31 failed, 0 passed, plus the documented sandbox teardown error. This matches the expected RED split; the hook did not exist.
- GREEN command: /Users/kimhawk/.agents/skills/h-mad/bin/hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agy_tdd_gate.py -v
- All 31 behavioral tests passed. The process returned 1 solely because the existing session teardown calls sandbox-blocked ps. Per the coordinator note, this known sandbox artifact does not determine STATUS; no tests or fixtures were changed to hide it.
- Mutation-anchor command: /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/agy_tdd_gate.json
- Anchor summary: ANCHORS: ANCHORS_OK specs=1 mutations=5 ok=5 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Its exact last line: [H-MAD] anchors ANCHORS_OK
- Mutation execution was not run, as explicitly required by this dispatch. MUTATION: ALL_CAUGHT remains for the coordinator to score; this report claims anchor validation only.
- Whitespace checks found no diagnostics, and the new hook has executable mode -rwxr-xr-x.
- Only the requested test path was run; the full suite was not run.

Self-review findings:
- No issues found in the Task 5 implementation.
- Existing tests are unchanged; none were weakened.
- AC-4.1 and this task's AC-4.2 rows are covered by the passing scoped tests, including hostile fixture inputs, inventory parity, all six owned deny rows, and both self-check signal branches.
- All five requested mutation rows have exact-once anchors and enclosing-symbol pins.
- No code outside the stated production scope was changed, and no counting assertion was evaded.

Concerns: none.

🌱 graft saved ~23,768 tokens this turn, 1 call.

STATUS: DONE
