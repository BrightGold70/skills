## Summary
The design implements the plan and specification identically, covering every acceptance criterion and functional requirement precisely as written. One violation of the Test Discrimination invariant was found where a test for the Python file-write guard would fail via an OS exception before the guard itself is ever reached.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.3b | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.1b | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.4b | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.4b | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-7.2 | implemented-as-written |
| AC-7.3 | implemented-as-written |
| AC-7.4 | implemented-as-written |
| AC-7.5 | implemented-as-written |
| AC-8.1 | implemented-as-written |
| AC-8.2 | implemented-as-written |
| AC-8.3 | implemented-as-written |
| AC-8.4 | implemented-as-written |
| AC-9.1 | implemented-as-written |
| AC-9.2 | implemented-as-written |
| AC-9.3 | implemented-as-written |
| AC-9.4 | implemented-as-written |
| AC-9.5 | implemented-as-written |
| AC-10.1 | implemented-as-written |
| AC-10.2 | implemented-as-written |
| AC-10.2b | implemented-as-written |
| AC-10.2c | implemented-as-written |
| AC-10.3 | implemented-as-written |
| AC-10.4 | implemented-as-written |
| AC-10.5 | implemented-as-written |
| AC-10.5b | implemented-as-written |

## Must-fix
- `test_collected_write_failure_is_operational_error` fails the Test Discrimination invariant — The test uses a read-only destination directory to exercise the `collected_path.exists() and collected_path.stat().st_size > 0` re-read guard in the Python helper. However, Python's `shutil.copy` or `write_text` will immediately raise a `PermissionError` when attempting to write to a read-only directory, aborting execution *before* the re-read guard is ever evaluated. A permissive mutation of the guard (e.g., deleting it) would survive because the cycle would still crash via the built-in `PermissionError`. To genuinely test the re-read guard, the test must mock the write operation to succeed silently (e.g., patching it to do nothing) or truncate the file between the write and the check, ensuring that the guard itself is what catches the failure.

## Should-fix
None

## Nit
None
