    AUDIT-doc-block-exec-design-v23-BEGIN
## Summary
The design meticulously satisfies the plan's requirements, bringing a robust, well-tested execution environment for bash blocks that explicitly handles edge cases like escapees, silent cleanup failures, and CommonMark fence rules. It strictly adheres to the stated invariants and properly maps operational failures to exit 2 verdicts. One subtle but critical file I/O behavior must be fixed to prevent tracebacks on disk-full errors.

## Must-fix
- `_final_write(handle, text)` MUST call `handle.flush()` after `handle.write(text)` — Python's `TextIOWrapper` is buffered, so a write (and even `truncate()`) may not hit the OS until the file is closed. Without an explicit `flush()`, an `OSError` (e.g. disk full) will be delayed until `handle.close()` or the `with` block exit. Because the file is closed outside `_final_write`, this error will bypass the specific `try/except` block intended to map it to `StreamWriteFailed` and will instead escape as an unhandled traceback, violating the Audit-gate signal discipline invariant.

## Should-fix
- TOCTOU on `exists()` check for stream rollback — The design relies on checking if the stream file existed before opening it with `"a"` to know if it should be unlinked on a subsequent reservation refusal. If another process creates the file in that small window, the rollback will wrongly delete a file it didn't create. Consider using `os.open` with `O_CREAT | O_EXCL` to atomically determine creation, or explicitly accept this race if deemed acceptable for the test harness.

## Nit
- `CLEANUP_FAILED` carries the recorded `OSError` (`cleanup_error`), but the verdict table specifies `DOCBLOCK: CLEANUP_FAILED path=<p>` without any `os_error: <text>` detail line (unlike `LAUNCH_FAILED`). Consider emitting the error text so the operator has immediate context on why the cleanup failed.
    AUDIT-doc-block-exec-design-v23-END
