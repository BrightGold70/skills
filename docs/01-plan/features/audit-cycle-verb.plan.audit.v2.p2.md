AUDIT-audit-cycle-verb-plan-v2-BEGIN
## Summary
The plan comprehensively covers all Functional Requirements from the spec, and its approach to connection-mutation testing represents an exceptionally strong validation strategy. However, there is a contradiction in the text regarding which layer (the shell verb or the Python helper) invokes the per-pass scripts, and the plan lacks exact file paths for its new deliverables.

### Spec Reconciliation (Axis C)

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
- Contradiction in process boundary (Axis A) — The text claims "The verb shells out to `h_mad_assemble_audit.py`, `h_mad_report_wait.py`, `h_mad_extract_report.py` and `h_mad_audit_gate.py`", but the layer placement table asserts the last three are "Invoked by Python helper". If the shell script is the "verb", it cannot shell out to them directly if the Python helper owns them. Clarify which process calls which.
- Missing exact file paths (Axis A / Impl-plan focus) — The "Collection + gating helper (stdlib-only Python)", "Offline test suite", and mutation specs are listed as deliverables but lack exact file paths. Provide exact paths for these new files to satisfy the impl-plan requirement for exact file paths.

## Should-fix
None

## Nit
- In the Deliverables table, the per-pass audit report files (`<feature>.<phase>.audit.v<N>.p<i>.md`) omit the `<audit-dir>/` directory prefix specified in AC-4.4. Including the directory makes the expected output location unambiguous.
AUDIT-audit-cycle-verb-plan-v2-END
