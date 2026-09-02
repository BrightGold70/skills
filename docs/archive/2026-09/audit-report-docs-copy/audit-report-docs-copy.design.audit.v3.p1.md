## Summary
The design fully captures the spec's intent to move the codex-leg audit docs copy into a derived, mechanical step while preventing `/tmp`-only reports from scoring. Axis C reconciliation confirms all 40 ACs are `implemented-as-written` and handled thoroughly, including the new property test for grammar disjointness and dual-rung readbacks. However, the design contains one critical omission in its Python implementation that breaks invariant signal discipline by leaking tracebacks on common I/O errors.

| Spec AC | Classification |
|---|---|
| AC-1.1 – AC-1.6 | `implemented-as-written` |
| AC-2.1 – AC-2.12 | `implemented-as-written` |
| AC-3.1 – AC-3.7 | `implemented-as-written` |
| AC-4.1 – AC-4.3 | `implemented-as-written` |
| AC-5.1 – AC-5.4 | `implemented-as-written` |
| AC-6.1 – AC-6.5 | `implemented-as-written` |

## Must-fix
- `collect()` leaks `OSError` tracebacks — The design prose states "`collect()` itself also wraps its `read_bytes()` comparisons the same way", but the code block for the AC-2.11 short-circuit (`collected_path.read_bytes() == spec.report_path.read_bytes()`) lacks the `with _fs_errors(...):` guard. An unwritable or vanished file here will raise a raw `OSError` (e.g., `PermissionError`), escaping the CLI's `except OperationalError` block and crashing the script with a traceback (exit 1, no marker). This violates the **Audit-gate signal discipline** and **Marker discipline** invariants.

## Should-fix
None

## Nit
None
