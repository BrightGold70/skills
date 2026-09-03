## Summary
The design and plan are highly detailed, correctly mapping edge cases, timeout races, and strict bounding policies. However, there are architectural contradictions regarding the exception data model for the CLI dispatcher and the exact location of the AC-1.8 delegation test which breaks the test floor calculation invariant.

## Must-fix
- Exception signatures lack fields required by the dispatcher — `StreamWriteFailed` has no arguments in the table to carry the partial write state (`written`, `failed`, `skipped`), and `LaunchFailed` lacks a `pgid` field. Since `main` catches `DocBlockError` and dispatches solely on type to print these detail lines, the exceptions must carry this data.
- The suite floor calculation misses additions to `test_docsections.py` — The plan claims "every other new test, AC-1.8's delegation and collect-alone pins included, lives in the new module", but the `docsections.json` mutation spec explicitly anchors the delegation test as `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`. If this test lives in `test_docsections.py`, the `2747 + new_module + 6` floor computation fails to count it, allowing a deleted pre-existing test in `test_docsections.py` to hide behind the uncounted addition.

## Should-fix
- Missing `pgid` in the verdict table — The text states `LAUNCH_FAILED stage=reap` reports `pgid=<n>` in its detail, but the verdict table's `LAUNCH_FAILED` row omits any mention of a `pgid=` detail line.

## Nit
- None
