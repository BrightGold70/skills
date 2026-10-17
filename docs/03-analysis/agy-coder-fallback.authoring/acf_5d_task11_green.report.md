Files changed:
- h-mad/scripts/h_mad_state_write.py
- h-mad/tests/mutation-specs/state_write_append.json

Implemented repeatable --append KEY=JSON with strict json.loads decoding and writer ERROR diagnostics. merge_fields now accepts appends, protects both APPEND_ONLY fields for CLI and library callers, refuses overlapping set/append keys and non-array targets, and accumulates entries from the updated record in one _mutate operation with all set fields. The OK line includes appended keys. The original record merge and owner-heartbeat statements remain byte-for-byte unchanged. No tests were modified.

pytest output (last 10 lines):
```text
  Instance attributes set in this fixture will NOT be visible to test methods,
  as each test gets a new instance while the fixture runs only once per class.
  Use @classmethod decorator and set attributes on cls instead.
  See https://docs.pytest.org/en/stable/deprecations.html#class-scoped-fixture-as-instance-method
    fixturefunc = resolve_fixture_function(fixturedef, request)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_state_write.py::TestAppend::test_append_implementation_authors_entry
==================== 68 passed, 1 warning, 1 error in 3.18s ====================
```

Verification:
- Before production edits: the scoped file reported 13 failed, 55 passed, matching the required RED split. All 13 TestAppend nodes failed; all existing regression tests passed.
- After implementation: all 68 test cases passed, including all 13 TestAppend nodes, owner-set heartbeat refresh, and bystander-set heartbeat preservation.
- Both runs used: hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_state_write.py -v
- Known sandbox artifact: session teardown's leak reaper invokes ps and raises PermissionError. This produced the additional teardown ERROR and process exit 1 in both runs. Per coordinator instructions it does not determine STATUS; no test or teardown fixture was weakened or bypassed. The existing class-scoped-fixture deprecation warning also remains unchanged.
- New spec: five required mutation rows, each with name, _mechanism, file, symbol, find, replace, and test. The repeated-append mutant reads records[feature] (the prior record) rather than the updated record. Module constants are pinned to <module>; the other anchors are pinned to merge_fields or merge_fields.apply.
- Required standalone anchor check: hmad-dispatch run --timeout 60 -- /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/state_write_append.json
- Standalone result: ANCHORS: ANCHORS_OK specs=1 mutations=5 ok=5 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Standalone last line: [H-MAD] anchors ANCHORS_OK
- Combined --check-anchors over heartbeat_beat.json, lane_liveness.json, release_ownership_guard.json, state_undeclared_keys.json, and state_write_append.json: ANCHORS: ANCHORS_OK specs=5 mutations=47 ok=47 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Combined last line: [H-MAD] anchors ANCHORS_OK
- The combined check reports existing self-matching advisories and 18 existing unpinned rows; all five new rows have symbol pins. Existing specs were not changed.
- Mutation scoring was not run, as explicitly instructed. MUTATION: ALL_CAUGHT remains for the coordinator to score outside the sandbox; no mutation-execution verdict is claimed here.
- git diff --check passed. Only the two task-owned files changed. The full suite was not run.

Self-review findings: none. All requested behavior is covered by the unchanged tests: preservation/order and schema rejection (AC-7.1), rejected implementation-authors entries preserving bytes (AC-1.3), both append-only fixtures, strict parsing, non-array refusal, same-key refusal, OK output, and owner heartbeat. Schema refusal leaves combined set/append changes byte-identical. No dependencies or unrelated production changes were introduced.

Concerns: none.

🌱 graft saved ~119,400 tokens this turn, 3 calls.
STATUS: DONE
