## Summary
The design, spec, and plan for the `doc-block-exec` helper are exceptionally detailed, robust, and well-aligned. The architecture soundly handles shell execution, stream artifact reservation, and mutation-verified failure paths. A few minor documentary inconsistencies exist around the exhaustive listing of `exit 2` classes in summaries and the exact formatting of exception details in tables.

## Must-fix
None

## Should-fix
- Incomplete `exit 2` summaries — The Design's Test Plan row for AC-4.1–4.5 and the Plan's FR-4 description both summarize the `exit 2` partition as just "UNREADABLE and CLEANUP_FAILED", omitting `LAUNCH_FAILED`. This contradicts the Spec (AC-4.2), the Design's own verdict table, and the Plan's Implementation Strategy which all correctly include `LAUNCH_FAILED` in the `exit 2` class.
- Missing `os_error:` detail in the Error Handling Strategy table — The Design's Error Handling Strategy table lists the verdict line for `CleanupFailed` as simply `CLEANUP_FAILED path=<p>`, silently omitting the `+ os_error: <text>` detail line that is correctly mandated by the Verdict Lines table and the Spec.

## Nit
- Multiple kill tests for a single mutation key — The Design's helper mutation spec table lists two distinct tests (`test_final_write_close_failure_is_mapped` and `test_final_write_failure_before_close_still_closes`) as the kill for `final-write-close-not-in-finally`. Since the JSON schema requires a single `test` key string per mutant, the document should clarify which of the two is the authoritative key in the spec.
- Test Plan row omits `wait()` step — The Design's Test Strategy clearly details a three-step teardown for the AC-4.6 reap test (killpg, wait, assert ProcessLookupError), but the corresponding Test Plan row for AC-4.6 omits the `wait()` step in its summary of the teardown.
