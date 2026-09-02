## Summary
The design covers every spec acceptance criterion as written, and its plan-to-design scope is otherwise aligned. I found two hard consistency gaps outside Axis C: the collector pseudocode does not actually place all filesystem reads under `_fs_errors`, and the SKILL.md insertion point silently diverges from the spec/plan placement constraint.

| Classification | ACs |
| --- | --- |
| implemented-as-written | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.6a, AC-2.6b, AC-2.7, AC-2.8, AC-2.9, AC-2.10, AC-2.11, AC-2.12, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.5a, AC-3.6, AC-3.7, AC-4.1, AC-4.2, AC-4.3, AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 |
| restated | None |
| absent | None |

## Must-fix
- D1's guard contract is contradicted by its own `collect()` pseudocode — the design says "Every filesystem call in the writers and in `collect()` runs under this guard" and that a vanished report becomes `OperationalError`, but the shown control flow calls `_has_complete_report(...)` and `_run_report_wait(...)` outside `_fs_errors`; those helpers perform filesystem probes in the current code path, so a race or unreadable stat can escape as a traceback instead of the required exit 2 plus `[H-MAD] … collect operational_error|readback_failed` marker.
- SKILL.md placement silently drifts from the source spec and paired plan — spec FR-5 says the new block goes "outside the slices `test_h_mad_audit_cycle_docs.py` pins" and the plan risk says "insert outside `## Audit prompt assembly`→`## Putting …`", but design D5 says "inside `## Audit prompt assembly`, directly after the `audit-cycle` paragraph block"; if that relocation is intentional it must be reconciled in the spec/plan, otherwise the design should move the block to the promised location.

## Should-fix
None

## Nit
None
