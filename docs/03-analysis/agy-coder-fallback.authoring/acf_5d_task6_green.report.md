Files changed:
- h-mad/hooks/h-mad-agy-tdd-gate.py
- h-mad/tests/mutation-specs/agy_tdd_gate.json

Implemented class (b), T1–T7 and OD-2 T2a. Targets must be recognised non-empty strings. Directory targets deny judge-error under active/unknown and allow under inactive. Containment runs before the shell-allowance helper; outside-root Python names are refused even beneath artifactDirectoryPath. Production detection covers every resolved hard-link name, selects the minimum production tuple, and reads the governing chain regardless of the workspace scan status. Judge denials preserve the judge's kind. Untrusted diagnostic text is escaped so it cannot inject a second kind= token.

pytest output (last 10 lines):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_agy_tdd_gate.py::test_class_b_directory_target[src-inactive]
========================= 66 passed, 1 error in 7.97s ==========================
```

Command: hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agy_tdd_gate.py -v

All 66 test assertions passed, including all 35 Task 6 nodes and all seven new deny-kind rows. The process exited 1 solely because the documented leak-reaper session teardown cannot execute ps inside the sandbox. Per the coordinator note, this known environment artefact does not decide STATUS. No test or fixture was changed to suppress it.

Self-review findings: no implementation issues found.
- The pre-edit RED run matched the dispatch: Task 6 had 24 failures and 11 passes; the full scoped file had 24 failures and 42 passes, plus the same environment teardown error.
- AC-4.1, AC-4.2, and the OD-2 baseline tests all pass. Tests retain their hostile inputs and assertions unchanged.
- Exactly 11 mutation rows were appended, each with symbol=main and the requested behavioural test. Task 5's five rows are unchanged, verified against HEAD.
- Production source and all 11 mutated source variants parse successfully. git diff --check passed.
- OD-2 discriminator review: disabling T2a leaves an existing directory with no production names, yielding allow under active; dot-active and src-active therefore reach assertion failures.
- I1 discriminator review: key-presence-only selection sends 5 and ["x"] to T1, which raises TypeError. The existing exception/finally path emits deny judge-error, contradicting the number-inactive and list-inactive allow assertions.
- The discriminator explanations above are source review, not executed mutant results. As instructed, only --check-anchors was run; the coordinator owns mutation execution and the MUTATION: ALL_CAUGHT score.
- No out-of-scope implementation edits, test weakening, dependency additions, or full-suite run.

Mutation anchor command: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/agy_tdd_gate.json

Anchor summary:
```text
ANCHORS: ANCHORS_OK specs=1 mutations=16 ok=16 drifted=0 unreadable=0 skipped=0 unclassifiable=0
```
Last command-output line:
```text
[H-MAD] anchors ANCHORS_OK
```
The checker also emitted its non-refusing self-matching advisory for the inactive-scan mutation: its insertion retains the production=[] anchor. That row is caught by a behavioural decision assertion, rather than a source-containment assertion.

Concerns: none. Mutation scoring remains the coordinator's explicitly assigned follow-up.

graft saved approximately 49,835 tokens this turn across 4 calls.

STATUS: DONE
