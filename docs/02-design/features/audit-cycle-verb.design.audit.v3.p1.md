AUDIT-audit-cycle-verb-design-v3-BEGIN
## Summary
The design for the `audit-cycle` verb is exceptionally rigorous, fully reconciling the shell/Python boundary and executing all load-bearing assumptions beforehand. It perfectly aligns with the plan and spec, implementing every acceptance criterion exactly as written with no silent narrowing or omissions. All base and project invariants (including connection enforcement and test discrimination for shell-level guards) are thoroughly covered. 

**Axis C — Spec Reconciliation Table:**
| AC | Classification | AC | Classification |
|---|---|---|---|
| AC-1.1 to AC-1.4 | `implemented-as-written` | AC-6.1 to AC-6.4 | `implemented-as-written` |
| AC-2.1 to AC-2.5 | `implemented-as-written` | AC-7.1 to AC-7.5 | `implemented-as-written` |
| AC-3.1 to AC-3.5 | `implemented-as-written` | AC-8.1 to AC-8.4 | `implemented-as-written` |
| AC-4.1 to AC-4.6 | `implemented-as-written` | AC-9.1 to AC-9.5 | `implemented-as-written` |
| AC-5.1 to AC-5.7 | `implemented-as-written` | AC-10.1 to AC-10.5b| `implemented-as-written` |

## Must-fix
None

## Should-fix
None

## Nit
- The Python pseudo-code snippet illustrating `combine` checks `if any(r.verdict is None for r in results):` and then immediately raises using `first_such.index`. A literal implementation will need to bind the matching `PassResult` (e.g., via `next(...)`) before accessing its index.
AUDIT-audit-cycle-verb-design-v3-END
