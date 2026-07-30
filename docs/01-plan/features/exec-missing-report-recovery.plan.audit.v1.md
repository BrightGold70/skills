AUDIT-exec-missing-report-recovery-plan-v1-BEGIN
## Summary
The plan cleanly mirrors the spec's strategy, correctly utilizing the existing branch structure in `_cmd_exec` to implement recovery for empty output without risking the clean-success path. However, there is a gap in test deliverable mapping and a violation of the base invariant requiring cited evidence for assumptions. All functional requirements are addressed in the plan.

| Requirement | Classification |
|---|---|
| FR-1 | `implemented-as-written` |
| FR-2 | `implemented-as-written` |
| FR-3 | `implemented-as-written` |
| FR-4 | `implemented-as-written` |
| FR-5 | `implemented-as-written` |
| FR-6 | `implemented-as-written` |
| FR-7 | `implemented-as-written` |

## Must-fix
- Gap in Deliverables table — The `test_hmad_dispatch_exec.py` deliverable lists "FR-2..FR-5, FR-7" but omits FR-1. FR-1 contains critical acceptance criteria (default log creation, teardown, and regression guards) that must explicitly require automated tests.
- Invariant breach (Assumption verification) — The plan assumes rc 3 is unused by any existing callers (stating "grep all exec call sites ... none use 3 today"), but it does not cite the observed output of the `grep` throwaway command in the document to prove this assertion.

## Should-fix
None

## Nit
None
AUDIT-exec-missing-report-recovery-plan-v1-END
