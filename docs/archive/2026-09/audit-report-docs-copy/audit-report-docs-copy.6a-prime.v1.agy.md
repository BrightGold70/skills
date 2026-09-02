I have reviewed the Phase 5 implementation against the detailed design and identified several critical deviations in `h_mad_audit_cycle.py` that break core H-MAD invariants related to report collection and the `.done` marker lifecycle.

*   **File:** `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_audit_cycle.py:285-292` (and lines 135-154)
*   **Issue:** The implementer deviated from the provided design template for `_collect_unguarded` and `_copy_collected_report`. Specifically:
    1. The same-file check uses string equality (`if spec.report_path == collected_path:`) instead of the required `.resolve() == .resolve()`.
    2. Same-file marker removal was moved out of `_copy_collected_report` into `_collect_unguarded`. By hoisting it, the implementation bypasses `_has_complete_report` and `_run_report_wait`. If the marker is absent, it returns `MISSING` instantly instead of waiting `grace` seconds.
    3. In `_copy_collected_report`, the explicit design check `if not data: raise OperationalError(f"report is empty: {report_path}")` was omitted. The implementer attempted to replace it with a `try... except OperationalError` wrapper around `_finalize_write`, but `_finalize_write` successfully writes empty bytes and does not throw, rendering the empty-file safeguard dead code.
*   **Why it matters:** This violates the AC-2.8 and AC-2.11 invariants. If the same file is specified via differing paths (e.g., one relative, one absolute), the string equality check fails, the byte-identity short-circuit triggers instead, and the `.done` marker is silently left on disk. Furthermore, the collector will instantly abort without waiting for the report if the marker is not yet present, and will happily copy and accept an empty file as a complete audit report. 
*   **Fix:** Revert `_collect_unguarded` and `_copy_collected_report` to exactly match the design template provided in the D1 constraints. 
    1. Restore `if not data: raise OperationalError(f"report is empty: {report_path}")` in `_copy_collected_report`.
    2. Move the same-file marker removal logic (`report_path.resolve() == collected_path.resolve()`) back into `_copy_collected_report`.
    3. Use `same = spec.report_path.resolve() == collected_path.resolve()` in `_collect_unguarded`, and call `_has_complete_report` and `_run_report_wait` on the same-file branch to wait `grace` seconds before giving up.

ASSESSMENT: WITH_FIXES
