# Task 1 RED — correction cycle 2

Applied coordinator decision D5d-1. Changed only the assertion and its message in
`h-mad/tests/test_h_mad_state_schema_fr1_docs.py:49`:

```python
assert "agy is out too" in rows[0], "fallback_agent reference row must require that agy is out too"
```

The preceding assertion requiring exactly one `fallback_agent` reference row is unchanged.

Item 15 now fails at RED with:
`AssertionError: fallback_agent reference row must require that agy is out too`.
The single existing state-schema.md row lacks the literal `agy is out too`;
its existing `--surfaces agy,grok` text no longer satisfies the assertion.

Executed only the requested pytest selection (through `rtk proxy`):

```text
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_state_validate_fallback.py h-mad/tests/test_h_mad_state_schema_fr1_docs.py -q -p no:cacheprovider
```

Observed summary: **114 failed, 8 passed, 1 error in 0.90s** (exit code 1).

- New nodes: **114 failing, 2 passing**, matching the expected 116-node RED split.
- The two new passes are `test_fr1_record_without_new_fields_unchanged` for the library and bundled paths.
- All **6 pre-existing regression nodes passed**.
- The sole teardown ERROR is the known sandbox artefact: the session leak-reaper
  invokes `ps -axo pid=,command=` and receives
  `PermissionError: [Errno 1] Operation not permitted: 'ps'`.
  No changes were made for this error. No other discrepancies were observed.

A before/after content-hash comparison of tracked and non-ignored untracked files
confirmed that only the requested test file changed during this dispatch; its exact
content differs only by the requested assertion and message. Production files,
all other tests, and `h-mad/tests/mutation-specs/state_fr1_fields.json` are unchanged.
No full-suite run was performed.

Full pytest output: `/private/tmp/acf5d-t1red-c2-pytest.log`.
The concern is limited to the explicitly permitted sandbox teardown artefact.

STATUS: DONE_WITH_CONCERNS
