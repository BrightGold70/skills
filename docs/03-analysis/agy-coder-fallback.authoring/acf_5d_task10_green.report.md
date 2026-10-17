Files changed:
- h-mad/scripts/h_mad_assemble_tdd.py
- h-mad/tests/mutation-specs/assemble_tdd_agent.json
- h-mad/tests/mutation-specs/assemble_tdd_agy.json (new)

Implemented Task 10 / assemble-tdd-agy, Phase 5e GREEN. The assembler accepts agy, selects the specified timeout table, and invokes Task 9's checker only for agy, before assemble. The subprocess uses sys.executable, AGY_WIRING_CHECK, --agy, --project-root and the selected root, bounded by AGY_WIRING_TIMEOUT_S=60. WIRED continues; UNWIRED prints the three required lines and returns 0; UNREADABLE returns 2; missing tokens and timeouts print the required no-token HALT and return 2. Every new halt prints its marker after the token. The module docstring states the new exit rule. Existing Halt branches are unchanged.

pytest output (last 10 lines, agent test run):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_docstring_drops_the_any_halt_rule
========================= 28 passed, 1 error in 5.67s ==========================
```

pytest output (last 10 lines, final regression run):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_assemble_tdd.py::TestReferencedGlobalSections::test_the_cli_reports_inlined_and_unresolved_under_the_pass_line
========================= 107 passed, 1 error in 8.83s =========================
```

Commands:
- hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_assemble_tdd_agent.py -v
- hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_assemble_tdd.py -v

Baseline evidence:
- Before production changes, agent tests: 16 failed, 12 passed, plus the documented sandbox teardown artifact. This is the specified 18-node Task 10 split of 16 failing / 2 passing, with 10 other existing cases passing.
- WIRE-PIN failure mode: "AssertionError: main must run the agy wiring check before assembling"; the checker record file was absent. No missing-symbol exception stood in for the caller assertion.
- All 107 regression tests passed from the first run.
- After implementation, all 28 agent tests and all 107 regression tests passed their assertions.
- A concurrent regression invocation encountered SUITE: BUSY and measured nothing; the final regression evidence above comes from the completed sequential rerun.

Self-review findings:
- No issues found. No tests modified or weakened; the existing env override, hostile fixtures and three-agent prompt equivalence test were already staged by RED.
- AC-5.1 and AC-5.2: all seven UNWIRED reasons, UNREADABLE, missing-token, timeout and WIRED cases pass; token, ordering, prompt absence and return-code assertions remain intact.
- AC-9.1: codex, grok and agy produce identical prompt bytes in the existing extended test.
- Timeout defaults: codex=900, grok=1500, agy=1500; explicit grok timeout regression cases all pass.
- Exact argparse and timeout line forms preserved as requested. The existing agent=args.agent call line remains unchanged and occurs once; no source-level assertion evasion.
- Four new mutation rows include symbol=main: fr5-unwired-exits-2, wire-check-not-run, wire-check-runs-for-every-agent and halt-marker-dropped. The wire-cut replaces only the subprocess invocation with a synthetic WIRED result, leaving verdict handling, the real checker module and assemble available. The WIRE-PIN asserts the call's record file before the other assertions, so this row targets caller observability. The converse targets the existing grok regression guard.
- Re-anchored only w10a-grok-by-default in assemble_tdd_agent.json, retaining the codex default and including agy in both find and replace.
- git diff --check passed.
- Only the three listed task files changed. No full-suite run, state changes, commits or external notifications.

Mutation anchor verification:
Ran /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/assemble_tdd_agy.json
```text
ANCHORS: assemble_tdd_agy.json ok ok=4/4
ANCHORS: ANCHORS_OK specs=1 mutations=4 ok=4 drifted=0 unreadable=0 skipped=0 unclassifiable=0
[H-MAD] anchors ANCHORS_OK
```
Quoted last line: "[H-MAD] anchors ANCHORS_OK".

Also ran --check-anchors over all seven requested assembler specs: assemble_tdd.json, assemble_tdd_agent.json, assemble_tdd_env_known.json, assemble_tdd_mutation_rows.json, fill_slots.json, grok_wire_reverts.json, assemble_tdd_agy.json.
```text
ANCHORS: ANCHORS_OK specs=7 mutations=84 ok=84 drifted=0 unreadable=0 skipped=0 unclassifiable=0
[H-MAD] anchors ANCHORS_OK
```
The harness noted 76 pre-existing rows lack symbol pins; all four new rows are pinned. Existing specs outside the requested re-anchor were preserved.

Coordinator verification: As explicitly instructed, no mutation harness execution without --check-anchors was performed. MUTATION: ALL_CAUGHT and dynamic mutant-kill scoring remain for the coordinator; they are not claimed here.

Environment note: The documented leak-reaper teardown invokes ps, which the sandbox denies with PermissionError. This makes pytest return 1 despite all test assertions passing; it is recorded once here and does not determine STATUS, per the coordinator instruction. OneContext context retrieval was attempted but unavailable outside a OneContext dashboard; the explicit dispatch and repository evidence were sufficient.

Concerns: none.

🌱 graft saved ~54,543 tokens this turn, 3 calls.

STATUS: DONE

