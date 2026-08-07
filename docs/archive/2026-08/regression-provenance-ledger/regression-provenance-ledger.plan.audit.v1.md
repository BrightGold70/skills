AUDIT-regression-provenance-ledger-plan-v1-BEGIN
## Summary
The plan cleanly adopts the spec's functional requirements and includes excellent upfront probing to validate its assumptions, particularly discovering that a single unresolvable node id aborts a pytest selection (A3). The core strategy—resolving first via collection to accurately separate `missing` from `broken`—is solid. However, there is a Base Invariant violation regarding connection testing for the new 5b registration hook, and a critical gap regarding where FR-4 removal declarations actually live. All FRs from the spec are classified as `implemented-as-written`.

**Axis C (Spec Reconciliation) for Functional Requirements:**
| FR | Classification |
|---|---|
| FR-1 | `implemented-as-written` |
| FR-2 | `implemented-as-written` |
| FR-3 | `implemented-as-written` |
| FR-4 | `implemented-as-written` |
| FR-5 | `implemented-as-written` |
| FR-6 | `implemented-as-written` |

## Must-fix
- Axis B (Connection enforcement) — The integration between the 5b gate and the registry writer is a new connection. The Plan's deliverables do not explicitly mandate a connection enforcement test for this link (a test that fails when the call from the 5b gate to the writer is removed while the writer itself remains intact). This must be explicitly required.
- Axis A (Gap / Unstated assumption) — The Plan states that removing a wire requires a declared provenance entry (FR-4) and assigns "Removal declaration parsing" to `h_mad_wire_registry.py`. However, it never defines *where* this declaration lives (e.g., is it written in the `impl-plan` like `wiring` tasks, or stored in a separate file in `.h-mad/`?). Since it's evaluated against entries "removed between BASE and HEAD", the declaration's location and parser coupling must be defined before the design phase.

## Should-fix
None

## Nit
- Success Criteria clarity — The criterion "A registry containing one renamed pin... produces missing=1" implies an *undeclared* rename. If a rename is declared, AC-4.3 mechanically verifies it, which should presumably not count as `missing`. Clarifying "an undeclared renamed pin" in the success criteria would make this perfectly unambiguous.
AUDIT-regression-provenance-ledger-plan-v1-END
