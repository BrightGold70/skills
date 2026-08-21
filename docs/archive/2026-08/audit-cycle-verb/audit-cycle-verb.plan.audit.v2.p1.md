AUDIT-audit-cycle-verb-plan-v2-BEGIN
## Summary
The plan successfully consolidates the manual audit cycle into a single command with robust per-pass isolation and an explicit fallback mechanism. All functional requirements from the spec are fully covered and mapped to specific acceptance criteria. However, there is a critical misunderstanding of the connection mutation invariant and a direct contradiction in how script exit codes are handled versus stated ACs.

| Requirement | Classification |
|---|---|
| FR-1 | `implemented-as-written` |
| FR-2 | `implemented-as-written` |
| FR-3 | `implemented-as-written` |
| FR-4 | `implemented-as-written` |
| FR-5 | `implemented-as-written` |
| FR-6 | `implemented-as-written` |
| FR-7 | `implemented-as-written` |
| FR-8 | `implemented-as-written` |
| FR-9 | `implemented-as-written` |
| FR-10 | `implemented-as-written` |

## Must-fix
- Axis B (Connection enforcement) violation in the mutation spec — The plan proposes mutating the *callee* rather than the connection logic for the "force it to fire unconditionally" direction (e.g., "assembly forced to report PASS on a halted prompt → the slot-preflight test fails"). The invariant explicitly requires the callee to be left intact. The mutation must force the *caller* (the verb/helper) to bypass its own check, and a test of the caller's fall-through behavior must fail, rather than relying on a callee-scoped test.
- Axis A contradiction regarding exit code branching — AC-2.1 states the verb "never branches on the script's exit code" for assembly, but AC-2.4 states a "non-zero exit from `h_mad_assemble_audit.py` ... produces a non-zero exit from the verb". The verb must branch on the exit code to distinguish a script crash (operational error, exit non-zero) from a clean completion, otherwise operational errors will be swallowed as missing tokens. This contradiction also applies to the gate script (AC-5.5 vs operational error handling).

## Should-fix
None

## Nit
None
AUDIT-audit-cycle-verb-plan-v2-END
