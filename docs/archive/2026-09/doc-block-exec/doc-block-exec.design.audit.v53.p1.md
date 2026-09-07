## Summary
The design presents a robust, heavily tested module for extracting and executing bash blocks from markdown with precise error handling and fallback behaviors. It fully specifies the mapping of OS errors into standard verdict lines, introduces a clear isolation strategy, and establishes solid connection invariants. A detail requires tightening around the exact boundary of `try`/`except` blocks and explicit closure to ensure the alias check's tests function as designed.

## Must-fix
- Alias check's handle closure contradicts its test assertion — If the alias check explicitly closes the handles inside the reservation's `try/except OSError` mapped region (as "The refusal closes both handles" suggests), a mocked `_close_stream` raising `OSError` will be caught and mapped to `StreamPathUnwritable`. However, `test_backstop_close_failure_does_not_outrank_a_refusal` asserts the verdict remains `stream_paths_alias`. To satisfy the test, the alias check must rely on the backstop `finally` to close the handles, leaving only the `unlink` inside the check.

## Should-fix
None

## Nit
- Unused `stream` property on `StreamCloseFailed` — The exception takes `stream` and `close_error`, but the verdict output `UNREADABLE reason=stream_close_failed` only prints the `os_error: <text>` detail line, making the `stream` argument unused in the CLI output.
- `RunResult` dataclass includes `shell` — The Plan states the returned value carries `rc`, `stdout`, and `stderr` as separate fields. The Design adds `shell` to the dataclass; this is harmless and useful for printing `RAN`, but it is not listed in the Plan's return values summary.
