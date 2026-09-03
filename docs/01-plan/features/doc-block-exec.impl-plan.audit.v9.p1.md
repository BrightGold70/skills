## Summary
The implementation plan is structurally precise and rigorously specifies state transitions, exception handling, and mutation coverage. However, the prose enumeration of variable fields that `main` is supposed to append contradicts the verdict table by missing several required fields, which will cause an implementer to drop them from the CLI output. Additionally, `StreamCloseFailed` captures the stream name but discards it in the user-facing diagnostic.

## Must-fix
- Task 4 variable fields list omission — The prose explicitly lists the variable fields `main` appends as `(rc=/blocks=/shell=, count=, index=, value=, keys=, heading=)`. This strictly omits `path=` (`CLEANUP_FAILED`), `key=` (`BAD_INFO`), `seconds=` (`TIMEOUT`), and `arg=` (`BAD_SUBST`), contradicting the verdict table which requires them to be appended.

## Should-fix
- `StreamCloseFailed` omission in CLI — The `StreamCloseFailed` exception captures `stream: str`, but the specified verdict line `DOCBLOCK: UNREADABLE reason=stream_close_failed + os_error: <text>` drops it completely. The CLI output should include the stream name (e.g., as a detail key) so the user knows which stream failed to close.

## Nit
- `StreamWriteFailed` types `written` and `skipped` as `list[str]`, but the description and detail line examples show them formatted as scalar strings (e.g., `written: stdout`). A note to explicitly format/join the list elements would prevent the implementer from printing literal Python list syntax like `['stdout']`.
