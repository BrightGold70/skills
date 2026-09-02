## Summary
The implementation plan is thorough, cleanly enforcing the `[H-MAD]` marker discipline, the audit-gate signal contract, and mutation verification. It correctly isolates the transport refusal to the gate and leverages the existing collector logic to serve both audit legs byte-identically. However, there is a missing seam in the readback logic that blocks the subprocess CLI tests from verifying readback failures.

## Must-fix
- Gap in D1's `_readback_equal` — The design omits the `HMAD_COLLECT_TEST_BREAK_READBACK` environment variable check that AC-2.12 explicitly requires to simulate a readback failure from the CLI subprocess. Without adding this seam directly into the production `_readback_equal` function (e.g., `if os.environ.get("HMAD_COLLECT_TEST_BREAK_READBACK") == "1": return False`), the AC is impossible to implement using a sitecustomize-free seam as mandated.

## Should-fix
None

## Nit
- In D1's `_copy_collected_report`, the code manually constructs the marker path with `marker = Path(str(report_path) + ".done")`. It should reuse the existing `_done_path(report_path)` helper already defined in `h_mad_audit_cycle.py` for DRYness.
