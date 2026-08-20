## Summary
The design comprehensively implements the audit-cycle verb, meticulously handling the complex failure modes and concurrency constraints of a multi-pass union gate. It fulfills all Functional Requirements and Acceptance Criteria from the plan and spec exactly as written. However, two logic gaps in the Python helper's boundary and combination logic need to be addressed to prevent false operational errors and duplicate directory-mapping logic.

### Axis C: Spec Reconciliation
| Identifier | Classification |
|---|---|
| AC-1.1 through AC-10.5b | `implemented-as-written` |
| FR-1 through FR-10 | `implemented-as-written` |

## Must-fix
- **False Operational Error on missing report** — The `combine` function raises an `OperationalError` if `any(r.verdict is None for r in results)` *before* checking for `r.delivered == "none"`. If a pass fails to deliver a report, `gate()` cannot run, so `r.verdict` will naturally be `None`. This ordering will cause a missing report to crash the cycle (exit 4, no token) instead of cleanly returning `UNVERIFIED reason=no_report:p<i>` (exit 0) as required by AC-6.2 and AC-6.3. The `OperationalError` check must exempt passes where `delivered == "none"`.
- **Unstated shell directory mapping logic** — The helper's CLI signature requires the shell to pass `<collected_i>` (e.g., `--pass 1:...:<collected_1>`). This forces the shell to duplicate the logic of mapping `--phase` to the correct `<audit-dir>` (`docs/01-plan` vs `docs/02-design`). The design does not state that the shell will perform this mapping. Since the Python helper receives `--feature`, `--phase`, and `--cycle`, it should compute the `<collected>` path internally. If the shell is intended to compute it, that logic must be explicitly designed; otherwise, `<collected_i>` should be removed from the `--pass` payload.

## Should-fix
None

## Nit
None
