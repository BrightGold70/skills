Files changed:
- h-mad/scripts/h_mad_tdd_judge.py
- h-mad/tests/mutation-specs/tdd_judge_implementer.json (new; four rows, each with symbol)
- h-mad/tests/mutation-specs/tdd_gate_fallback_agent.json (only g3 find/replace re-anchored; test unchanged)

pytest output (last 10 lines):
```text
h-mad/tests/test_h_mad_tdd_judge_implementer.py:88: AssertionError
=========================== short test summary info ============================
FAILED h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_line[switch-none]
FAILED h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_line[peer-switch]
FAILED h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_reads_the_record_whatever_its_phase
FAILED h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_record_writes_switch_once
FAILED h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_record_failed
FAILED h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_switch_none_writes_nothing
ERROR h-mad/tests/test_h_mad_tdd_judge_implementer.py::test_implementer_verb_switch_none_writes_nothing
==================== 6 failed, 41 passed, 1 error in 1.07s =====================
```

Implementation:
- Added trailing defaulted Record fields, Implementer, _implementer_tag, and the sole resolve_implementer resolver.
- Added implementer --root/--feature/--record with the FR-2 token rows, phase-independent root record lookup, shared state writer, UTC timestamps, idempotent switch recording, and StateWriteError/OSError handling.
- Preserved the existing TDD-STATE output and four-argument Record construction.
- Added the four requested mutation rows; re-anchored g3 without changing intent or its test.

Verification:
- Bounded commands used hmad-dispatch run --timeout <seconds> -- <command>.
- Initial overlapping new-test launch was refused by the tree lock (SUITE: BUSY); it measured nothing. Subsequent measured pytest sessions ran sequentially.
- Pre-edit regression guards: 451 passed, 1 teardown error in 252.23s. All regression assertions passed from the first measured run.
- Pre-edit new tests: 47 failed, 0 passed, 1 teardown error. Missing symbols/subparser matched the declared new-behaviour RED.
- Post-edit scoped new tests: 41 passed, 6 failed, 1 teardown error. Every in-process resolver/tag/default/status case passes. Six CLI cases encounter the invalid PATH fixture described below.
- The known sandbox-only teardown error is conftest.py -> leak_reaper.find_leaked -> ps -> PermissionError. Reported here once; per coordinator instruction it does not determine STATUS.
- New spec: ANCHORS: ANCHORS_OK specs=1 mutations=4 ok=4 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Last line of the requested new-spec anchor command: [H-MAD] anchors ANCHORS_OK
- Eight existing specs: ANCHORS: ANCHORS_OK specs=8 mutations=104 ok=104 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Last line of the existing-spec anchor command: [H-MAD] anchors ANCHORS_OK
- git diff --check passed.
- Mutation scoring was not run, as explicitly instructed; MUTATION: ALL_CAUGHT is not claimed.
- Post-edit regression guards were not rerun after confirming the fixture blocker; the pre-edit result above is baseline evidence only.

Self-review findings:
- No test file was changed or weakened. All three regression guards remain unchanged.
- AC-2.1 is green. AC-2.2 is blocked by the fixture; switch idempotence and both writer failure branches are not fully verified because the affected tests fail at the earlier token assertion.
- Anchor portion of AC-X passes; mutation scoring is reserved for the coordinator.
- No counting assertion was evaded, no out-of-scope production file was changed, and no workflow state was edited.
- OneContext context retrieval was attempted as required but is unavailable outside its dashboard environment; the committed FR-2 design was used.

Blockers: The CLI test fixture contradicts FR-2's required shutil.which discovery. h-mad/tests/test_h_mad_tdd_judge_implementer.py defines HOSTILE with [H-MAD:MARKER], _root embeds HOSTILE in the root directory, and _verb sets PATH to root/controlled-bin. On macOS os.pathsep is ':', so this splits the actual stub directory into two nonexistent PATH entries. The six failing tests expect codex/agy to be discoverable anyway. A read-only probe against test_implementer_verb_line[switch-none]'s actual fixture confirmed:
- fixture controlled-bin exists;
- agy exists and is executable: True;
- shutil.which("agy", path=str(controlled_bin)): None;
- shutil.which("codex", path=str(controlled_bin)): None;
- PATH splits inside [H-MAD:MARKER].

Required correction before redispatch: Give _verb a colon-free executable directory outside the hostile root, while preserving the full hostile feature/root payload passed to --feature/--root and all existing assertions. A POSIX PATH entry cannot encode a colon within a directory name. Changing production discovery to compensate would violate the required shutil.which contract. I stopped without modifying the test fixture.

Graft saved approximately 25,289 tokens across 3 calls.
STATUS: BLOCKED
