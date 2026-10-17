Files changed:
- h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py (new): five real pytest RED fixtures, executed subprocess callee resolution, old_rule/new_rule, run_corpus(base), seven passing gate nodes.
- docs/03-analysis/probes/agy-coder-fallback/fr9_corpus_reading.py (new): imports run_corpus from h-mad/tests, prints sha/exception lines/callee resolution/old and new verdicts, exits zero on either verdict, embeds exactly one observed reading.
- h-mad/tests/mutation-specs/new_caller_carveout_copies.json: appended the two requested mutations, each pinned to symbol new_rule and the exact changed-verdict test; 8 -> 10 rows. Existing rows unchanged.

pytest output (last 10 lines):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py::test_transcription_is_tied_to_the_canonical_words
========================== 7 passed, 1 error in 7.24s ==========================
```

Command: hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py -v

Self-review findings:
- All seven gate nodes PASS on their first run: expected 0 failing / 7 passing. The known leak-reaper teardown ERROR above is the sandbox ps restriction; it is not a corpus finding and does not determine this report's STATUS.
- No production code or Task 13 rule/document text was edited. The only new documentation artifact is the expressly requested probe. No failing gate was weakened or manufactured.
- Each fixture directory is initialized as a Git repository. Its real test_wire_pin invokes fr9_api.new_caller() and asserts the result is 'wired', preserving a behavioral assertion after the missing symbol is supplied. Its RED is observed from sys.executable -m pytest, not simulated or inferred from source.
- Callee resolution uses a separate sys.executable subprocess executing import fr9_api and getattr(fr9_api, 'callee') at that same fixture base. Return code, stdout, and stderr are recorded and checked against the declaration.
- The missing-symbol role is declared per fixture. The recorded exception line is checked against both its declared exception class and its exact quoted missing-symbol name.
- The probe's single observed reading is stamped 03c9da2687fcad3df99a8f05b7c46394baf991f6, prints PROBE: PASS, and exits 0. Only new-caller changes, halt -> valid. The other four remain halt -> halt.
- Hostile paths contain spaces, glob syntax, a quote, a newline, and a Markdown marker; subprocesses inherit HMAD_STUB_HOSTILE=all. No human/agent input or Orca stub is consumed by this corpus. No shell interpolation is used in corpus subprocesses.
- git diff --check passes. No full suite or sibling project was collected.
- Repository history lookup was attempted with the onecontext skill; its CLI reported that history is unavailable outside a OneContext dashboard session. Current design and Task 13's equivalence test supplied the task evidence.

RED acceptance evidence (one line per collected test):
- PASS test_corpus_case_red_is_real[new-caller]: run_corpus -> real test_wire_pin -> fr9_api.new_caller() yields "AttributeError: module 'fr9_api' has no attribute 'new_caller'"; executed callee resolution succeeds. Removing the real missing-caller RED or resolution evidence breaks this test; non-vacuous.
- PASS test_corpus_case_red_is_real[missing-callee]: run_corpus -> real test_wire_pin -> existing fr9_api.new_caller() -> absent callee() yields "NameError: name 'callee' is not defined"; executed callee resolution fails. Removing either observed condition breaks this test; non-vacuous.
- PASS test_corpus_case_red_is_real[both-missing]: run_corpus -> real test_wire_pin -> absent fr9_api.new_caller() yields "AttributeError: module 'fr9_api' has no attribute 'new_caller'"; the independent callee lookup also fails. Supplying either missing symbol breaks the corresponding assertion; non-vacuous.
- PASS test_corpus_case_red_is_real[unrelated-import]: run_corpus -> real test_wire_pin -> fr9_api.new_caller() -> import fr9_unrelated_dependency yields "ModuleNotFoundError: No module named 'fr9_unrelated_dependency'"; callee resolution succeeds. Removing this unrelated-import failure or the resolving callee breaks this test; non-vacuous.
- PASS test_corpus_case_red_is_real[other-symbol]: run_corpus -> real test_wire_pin -> fr9_api.new_caller() -> other_symbol yields "NameError: name 'other_symbol' is not defined"; callee resolution succeeds. Removing this failure or the resolving callee breaks this test; non-vacuous.
- PASS test_changed_verdicts_are_exactly_new_caller: run_corpus actually invokes old_rule and new_rule, the functions containing the transcribed classifiers, over the runtime observations; it checks all five names, every old halt, exactly {new-caller} changed, and new-caller valid. Deleting the carve-out or either conjunct violates these assertions; non-vacuous. The two mutation rows target this node alone.
- PASS test_transcription_is_tied_to_the_canonical_words: directly checks both required phrases in CANONICAL imported from test_h_mad_new_caller_carveout_copies. This is a textual contract test, not a behavioral method test; deleting either canonical condition fails its named assertion, so it is non-vacuous.

Mutation evidence:
- Attempted only the requested mutation spec via hmad-dispatch run --timeout 300 -- /opt/anaconda3/bin/python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/new_caller_carveout_copies.json.
- Result: MUTATION: BASELINE_NOT_GREEN. No ALL_CAUGHT claim is made.
- Followed the coordinator's sandbox fallback, without running more mutation tests: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/new_caller_carveout_copies.json.
- Result: ANCHORS: ANCHORS_OK specs=1 mutations=10 ok=10 drifted=0 unreadable=0 skipped=0 unclassifiable=0.

Concerns:
- AC-X remains unverified: the mutation harness refused its baseline; anchor validation proves all ten anchors and their symbol pins, not that all ten mutations are caught. The dispatch explicitly allows this sandbox fallback.

Blockers:
- The required commit cannot be made under this session's filesystem permissions. The scoped git add command failed: fatal: Unable to create '/Users/kimhawk/orca/skills/.git/worktrees/agy-coder-fallback/index.lock': Operation not permitted. The three complete artifacts remain in the working tree, unstaged. A coordinator with Git-metadata write access must commit them to meet the committed-reading acceptance criterion. Approval policy is never, so no escalation was requested. This commit blocker, not the known teardown artifact, determines BLOCKED.

No task-id or coordinator handle was supplied; no worker_done message is applicable.

graft saved approximately 533 tokens this turn (one call).

STATUS: BLOCKED
