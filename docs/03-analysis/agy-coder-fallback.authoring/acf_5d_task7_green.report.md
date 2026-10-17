Files changed:
- h-mad/hooks/h-mad-agy-tdd-gate.py
- h-mad/tests/mutation-specs/agy_tdd_gate.json

Implemented FR-4 class (c) in main: missing/non-string CommandLine respects active/unknown versus inactive; unknown refuses judge-error; active computes root-relative Cwd with MALFORMED_WORKDIR for non-string values, changes directory only when possible, and composes the shared shell policy with operator allowances. Policy refusals carry shell-not-admitted and name all five class-(b) tools and SHELL_ALLOW_FILE.

pytest output (last 10 lines):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_agy_tdd_gate.py::test_operator_allowance_admits_a_listed_command
========================= 96 passed, 1 error in 11.54s =========================
```

Command: rtk proxy hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agy_tdd_gate.py -v

Self-review:
- Initial baseline: 23 failed, 73 passed, matching the stated Task 7 split of 23 failing and 7 passing nodes, plus 66 existing passing nodes.
- GREEN: all 96 collected test cases pass, including all 30 Task 7 nodes and all 17 test_deny_row_kind ids.
- AC-4.1: missing CommandLine, workspacePaths=[], read-only ls, and bad-Cwd ls fixtures pass.
- AC-4.2: all four added class-(c) deny rows pass with their required kinds.
- AC-6.1: unsafe tuple parity passes against the Codex gate's actual unsafe tuple.
- Appended exactly four required mutation rows, each with symbol=main. Preserved all 16 prior rows without re-anchoring.
- Anchor-only validation passed for 20/20 rows. No mutation sweep was run, as instructed; MUTATION: ALL_CAUGHT remains the coordinator's scoring responsibility.
- Harness command: rtk proxy hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/agy_tdd_gate.json
- Harness verdict: "ANCHORS: ANCHORS_OK specs=1 mutations=20 ok=20 drifted=0 unreadable=0 skipped=0 unclassifiable=0"
- Command's last line: "[H-MAD] anchors ANCHORS_OK"
- git diff --check passed. No tests were changed or weakened, no unrelated production files changed, and no unscoped suite or full mutation harness was run.
- Known sandbox artifact: the session leak-reaper teardown cannot launch ps (PermissionError). This caused the single teardown ERROR and pytest exit 1 in both baseline and GREEN; it is unrelated to behavioral assertions and does not determine STATUS, per coordinator instructions.
- Required history lookup was attempted; OneContext is unavailable outside a dashboard session. Implementation was grounded in the committed design and shared Codex gate behavior.

Concerns: none.

🌱 graft saved ~47,599 tokens this turn, 4 calls.
STATUS: DONE
