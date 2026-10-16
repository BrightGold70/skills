Files changed (paths):
- h-mad/scripts/h_mad_state_schema.json
- h-mad/scripts/h_mad_state_validate.py
- h-mad/references/state-schema.md
- h-mad/tests/mutation-specs/state_fr1_fields.json (new)

Implemented the five optional fields immediately after fallback_agent in the specified order, preserving the top-level required array and additionalProperties: false. Added rfc3339_datetime, _semantic_ok and per-call property_valid. classify retains its initial non-dict refusal and applies the timestamp refusal before both schema tiers. Updated both availability descriptions and reference rows to require both peers to be out before fallback_agent applies. Added all four requested mutation rows. No test assertions or writer code were changed.

pytest output (last 10 lines), scoped GREEN run:
Command: hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_state_validate_fallback.py h-mad/tests/test_h_mad_state_schema_fr1_docs.py -v
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_state_schema_fr1_docs.py::test_new_properties_follow_fallback_agent_in_order
========================= 122 passed, 1 error in 0.43s =========================
```

pytest output (last 10 lines), post-change regression guards:
Command: hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_state_fallback_agent.py::test_fallback_agent_description_states_the_four_facts h-mad/tests/test_h_mad_state_write.py -v
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_state_write.py::TestHeartbeatBeats::test_a_set_key_named_like_the_signature_is_refused_not_swallowed[fields]
========================= 56 passed, 1 error in 1.87s ==========================
```

Self-review findings:
- All 116 new task cases pass on GREEN, including both library/bundled paths, timestamp cases, property validation and documentation/order checks. All 6 existing validator tests pass too: 122 passing test bodies total.
- All 56 writer/description regression test bodies passed before changes and after changes. The description guard retains all four phrases and its index assertion.
- The RED verification produced exactly the task's 114 new failures and 2 new passes, plus 6 existing passes. It also encountered the same unrelated teardown error described below.
- An initial overlapping scoped launch was refused with SUITE: BUSY while the guard run held the tree lock. It was rerun sequentially after that run finished; no lock was deleted.
- The required pre-edit wording scan listed only h-mad/tests/test_h_mad_state_schema_fr1_docs.py. Its assertions are unchanged and all pass.
- Hostile module input continues to use HMAD_STUB_HOSTILE=all through the existing tests.
- git diff --check passed.
- All four mutation find strings matched exactly once. The requested bounded --check-anchors command reported:
  ANCHORS: ANCHORS_OK specs=1 mutations=4 ok=4 drifted=0 unreadable=0 skipped=0 unclassifiable=0
  Last line: [H-MAD] anchors ANCHORS_OK
- The harness also emitted its advisory that these four rows have no optional symbol pin. Anchor counts passed.
- No full mutation run was performed, as explicitly required by this dispatch. MUTATION: ALL_CAUGHT remains for the orchestrator to score.
- No test was weakened, no source-count assertion evasion was performed, and no out-of-scope production file was edited.

Blockers: Both pytest commands exit 1 solely because the shared session teardown in h-mad/tests/conftest.py:183 calls find_leaked, which invokes ps in h-mad/tests/leak_reaper.py:34. This sandbox refuses process inspection with PermissionError: [Errno 1] Operation not permitted: 'ps'. The same error occurred before any production edits. All 178 test bodies pass, but the commands are not fully GREEN: each has one teardown error. The fixture has no supported environment opt-out, is outside this task's scope, and was left unchanged. This session cannot request elevated sandbox permissions. Completion needs the same scoped commands rerun in an environment that permits the existing leak-reaper's ps call.

The implementation and mutation anchors are ready for review; reporting BLOCKED because clean pytest completion is required and cannot be obtained in this sandbox.

🌱 graft saved ~86,929 tokens this turn, 3 calls.

STATUS: BLOCKED

