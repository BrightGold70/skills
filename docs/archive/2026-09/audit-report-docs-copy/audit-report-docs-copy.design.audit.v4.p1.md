## Summary
The design cleanly introduces the second-surface `codex` collection leg, correctly shifting the fallback/copy logic into a unified entry point while tightening the gate against transport filenames. All functional requirements and base invariants are meticulously upheld, including correct readback handling on both delivery rungs and consistent marker signaling. A single test-design gap requires adjustment to reliably simulate an unwritable docs file in POSIX environments.

## Must-fix
- Unachievable test scenario — The design proposes verifying operational error handling by making the docs file read-only (`chmod 0o444`) and asserting that an `OSError` (exit 2) is triggered during a `--force` overwrite. However, in POSIX, `unlink(missing_ok=True)` on a read-only file succeeds if its parent directory is writable, allowing `write_bytes()` to subsequently create a new file and exit 0 successfully. To reliably trigger a `PermissionError` and validate the error path, the test must make the parent directory unwritable (`chmod 0o555` on the directory) or use an unwritable directory in place of the file.

## Should-fix
None

## Nit
None
