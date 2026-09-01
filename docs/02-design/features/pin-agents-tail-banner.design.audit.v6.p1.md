## Summary
The design is rigorous and explicitly addresses the audit findings from previous cycles. It complies perfectly with the plan and the spec, and all base and project invariants are respected. Spec reconciliation is fully `implemented-as-written` across all 13 Acceptance Criteria.

| Spec AC | Classification | Note |
|---|---|---|
| AC-1.1 | `implemented-as-written` | Addressed in Test 1 |
| AC-1.2 | `implemented-as-written` | Addressed in Test 2 |
| AC-1.3 | `implemented-as-written` | Addressed in Test 3 |
| AC-2.1 | `implemented-as-written` | Addressed in Test 4 |
| AC-2.2 | `implemented-as-written` | Addressed in Test 5 |
| AC-2.3 | `implemented-as-written` | Addressed in Test 6 |
| AC-3.1 | `implemented-as-written` | Addressed in Test 7 |
| AC-3.2 | `implemented-as-written` | Addressed in Test 8 |
| AC-3.3 | `implemented-as-written` | Addressed in Test 9 |
| AC-4.1 | `implemented-as-written` | Addressed in Test 10 |
| AC-4.2 | `implemented-as-written` | Addressed in Test 11 |
| AC-4.3 | `implemented-as-written` | Addressed in Test 12 |
| AC-5.1 | `implemented-as-written` | Addressed in Test 13 |

## Must-fix
None

## Should-fix
None

## Nit
- **Variable scope and exit codes**: The sanctioned call form `if out="$(_orca_tail_sig "$h")"; then` will leak the `out` variable into `_orca_find`'s scope since it is not declared `local`. Declaring it inline as `if local out="$(...)"; then` inside bash would silently obscure the exit status (always evaluating to true). To keep it scoped and safe, declare `local out` on a separate line before the `if` condition.
- **Suspension of `set -e`**: Be aware that calling `_orca_tail_sig` inside an `if` condition completely suspends `set -e` for the execution of that helper function in bash. The helper must be written to handle intermediate failures gracefully (e.g., as a single pipeline where `pipefail` applies), rather than relying on `set -e` to abort it early upon failure of the `terminal read` command.
