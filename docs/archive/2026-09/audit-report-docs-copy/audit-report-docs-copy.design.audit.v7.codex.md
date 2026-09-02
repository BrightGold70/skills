## Summary
The design matches the spec and paired plan at the FR/AC level, but one CLI error-path sketch is internally inconsistent with the declared bad-surface contract. Axis C reconciliation:

| Classification | Items |
|---|---|
| implemented-as-written | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.6a, AC-2.6b, AC-2.7, AC-2.8, AC-2.9, AC-2.10, AC-2.11, AC-2.12, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.5a, AC-3.6, AC-3.7, AC-4.1, AC-4.2, AC-4.3, AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 |
| restated | None |
| absent | None |

## Must-fix
- Bad `--surface` can still leak as an uncaught `ValueError` in the CLI sketch — D1 defines `validate_surface()` as raising `ValueError`, while D2's exact outer handler is `except (OperationalError, OSError)` and the shown nested handler only catches `CollectConflict`; unless the semantic check explicitly converts `ValueError` to `OperationalError` or the outer handler catches it, AC-2.7/AC-2.10's required exit 2, no `COLLECT:` line, and `[H-MAD] ... usage_error|operational_error` marker are not guaranteed.

## Should-fix
None

## Nit
None
