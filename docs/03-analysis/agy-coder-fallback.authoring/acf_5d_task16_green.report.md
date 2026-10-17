Files changed:
- h-mad/SKILL.md
- h-mad/references/agy-runtime.md
- h-mad/tests/mutation-specs/agy_authorship_docs.json (new)

Implemented Task 16 (Phase 5e GREEN): documented FR-2 resolved implementer selection and FR-3 Claude-side authorship refusals, including agy-authorship and implementer-invalid. Preserved the Phase 5 heading, the Phase 5 implementation anchor, the teammate bullet anchor, and existing mutation rows. Added the single implementer-staging bullet with the exact --record command, token-only verdict reading, all dispatch branches, and record=failed checked first with the required refusal, halt, and marker. Documented the agy upgrade trigger and exec agy implementer role, and separated teammate audit routing from resolved authorship.

Installed-runtime evidence: agy --version printed 1.4.0. Read /Users/kimhawk/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md; SessionStart appears at lines 71, 89, and 253, documenting a once-per-new-conversation event with flat handlers. Corrected and version-stamped both runtime surfaces together. The TDD-gate section now names h-mad-agy-tdd-gate.py, the AGY-GATE: wiring check, and the retained step5:agy_tdd_hook_unverified halt.

Pytest output (last 10 lines of the scoped GREEN run):
```text
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/anaconda3/lib/python3.11/subprocess.py:1026: in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
/opt/anaconda3/lib/python3.11/subprocess.py:1953: in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
E   PermissionError: [Errno 1] Operation not permitted: 'ps'
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_agy_authorship_docs.py::test_record_failed_check_rejects_a_procedure_that_dispatches
========================== 9 passed, 1 error in 0.33s ==========================
```

Verification:
- Before edits, the scoped module matched the prescribed 8 failing assertions / 1 passing control. All 60 required regression assertions passed on their first run.
- GREEN: hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agy_authorship_docs.py -v --tb=short: all 9 test bodies passed.
- Required regression guards, re-run after edits: all 60 test bodies passed.
- h-mad/tests/test_h_mad_assemble_tdd.py::TestDocsPin: both test bodies passed.
- Known sandbox artefact, excluded from STATUS as explicitly instructed: each pytest invocation reports the leak-reaper session-teardown PermissionError because sandbox policy denies ps. No fixture, test, or sandbox policy was changed. One concurrent verification attempt hit the shared suite lock and measured nothing; it was re-run sequentially without altering the lock.
- git diff --check passed.
- The new spec has exactly 8 rows, each with name, _mechanism, file, symbol (enclosing heading), find, replace, and a distinct prescribed test node, in items 1–8 order. All anchors match exactly once. The final mutation replaces the failed-record refusal/halt with staging the resolved peer.
- Ran the requested installed harness with --check-anchors on agy_authorship_docs.json: ANCHORS: ANCHORS_OK specs=1 mutations=8 ok=8 drifted=0 unreadable=0 skipped=0 unclassifiable=0. Its last line was:
  [H-MAD] anchors ANCHORS_OK
- Discovered every tracked JSON mutation spec naming SKILL.md, plus the new spec, and ran --check-anchors over all of them: ANCHORS: ANCHORS_OK specs=21 mutations=358 ok=358 drifted=0 unreadable=0 skipped=0 unclassifiable=0. This includes the historical 16-spec scope and additional currently present specs. Its last line was:
  [H-MAD] anchors ANCHORS_OK
- Did not run the mutation harness without --check-anchors. MUTATION: ALL_CAUGHT remains for the coordinator to score; no mutation-execution result is claimed.

Self-review findings: none. All requested documentation branches and markers are present; no tests were modified or weakened, no existing mutation rows were edited, no doc pins moved, no out-of-scope production files changed, and no commit was created. All 8 originally failing documentation assertions and the discriminating control now pass.

Concerns: none.

Graft saved approximately 82,618 tokens this turn across 2 calls.

STATUS: DONE
