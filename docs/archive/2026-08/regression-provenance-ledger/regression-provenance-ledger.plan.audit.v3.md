## Summary
The plan is strong and directly addresses the specification with well-justified mechanisms, particularly the resolve-first approach to mitigate `pytest` collection aborts. Axis C reconciliation shows all functional requirements are implemented as written in the spec. However, there are three Axis B invariant violations related to connection enforcement (missing the unconditional-fire mutation), audit-gate signal discipline (handling missing `--base` via a distinct token instead of an exit 2 operational error), and test isolation for the registry writer.

| Functional Requirement | Classification |
|---|---|
| FR-1 (Durable registry) | `implemented-as-written` |
| FR-2 (Standing re-verification) | `implemented-as-written` |
| FR-3 (Provenance vs absence) | `implemented-as-written` |
| FR-4 (Declared removal) | `implemented-as-written` |
| FR-5 (Shape challenge) | `implemented-as-written` |
| FR-6 (Registration on 5b path) | `implemented-as-written` |

## Must-fix
- Connection enforcement violation — The plan specifies that the connection-enforcement test must fail when the call from the 5b gate to the registry writer is removed. However, the Base Invariant mandates mutating the connection in **both directions**: you must also force it to fire unconditionally and verify that the fall-through/negative test fails. The plan omits this second required direction.
- Audit-gate signal discipline violation — The plan states that an invocation without `--base` "reports its own distinct token and never `PASS`". Since `--base` is a required input to perform the FR-4 comparison, omitting it constitutes missing input, which is a genuine operational error. Per the invariant (and Spec AC-2.5), this MUST trigger an `exit 2` rather than inventing a new custom stdout token and exiting normally.
- Test discrimination (Sandbox isolation) violation — The plan proposes unit testing the registry writer (`test_h_mad_wire_registry.py`), which requires redirecting its output to prevent overwriting the real `.h-mad/wires.jsonl`. The invariant requires that before mutating anything that decides where state is written, the real target must be explicitly snapshotted and restored, or run in a sandboxed working directory. The plan fails to specify this mandatory safety mechanism for the writer's tests.

## Should-fix
- Missing schema fields in deliverables — The plan's deliverable for the registry writer mentions `id` and `kind` but omits the other fields required by Spec AC-1.1 (`caller`, `callee`, `pin`, `owning_feature`, `registered_ts`). While it mentions "schema" broadly, explicitly listing the full set of required fields ensures the implementation does not miss them.
- Implicit BASE extraction — The plan mentions a `BASE..HEAD absent-vs-tombstoned comparison` but leaves the mechanism for extracting the BASE registry file unspecified. To adhere to the focus on exact paths and no vague requirements, explicitly state the use of `git show <base>:.h-mad/wires.jsonl` (or equivalent) for this comparison.

## Nit
None
