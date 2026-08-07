## Summary
The plan cleanly implements the specification, including the v1.1 spec amendments, and explicitly satisfies the base invariants (notably Connection Enforcement and Mutation Verification). Axis C alignment is complete, with all Functional Requirements implemented as written. However, there are two gaps in the execution strategy (Axis A) that must be addressed: a critical subprocess edge case where an empty resolving set could accidentally trigger a whole-suite pytest run, and a missing mechanism for how the verifier discovers the `BASE` commit for FR-4 checks.

| Functional Requirement | Classification |
|---|---|
| FR-1: A durable wire registry | `implemented-as-written` |
| FR-2: Standing re-verification of every registered wire | `implemented-as-written` |
| FR-3: Registry provenance must be distinguishable from registry absence | `implemented-as-written` |
| FR-4: Removing a wire requires a declared provenance entry | `implemented-as-written` |
| FR-5: Challenge an undeclared wiring task at 5b — warning first | `implemented-as-written` |
| FR-6: Registration happens on the existing wiring path, not as a parallel step | `implemented-as-written` |

## Must-fix
- **Empty resolving set triggers whole-suite run (Axis A - Gap)** — The plan states: "then a single run of the resolving set". If the resolving set is empty (e.g., the registry only contains `missing` or `removed` pins), passing an empty list of arguments to `pytest` will cause it to default to running the entire test suite. The verifier must explicitly guard the second subprocess call and skip execution (yielding `verified=0, broken=0`) if the resolving set is empty.
- **Discovery of BASE for FR-4 comparison (Axis A - Gap)** — The plan promises a "BASE..HEAD absent-vs-tombstoned comparison" but does not specify how `h_mad_wire_registry.py` obtains the `BASE` commit. The spec notes `BASE` is the 5c baseline commit recorded in the impl-plan; the verifier must either accept this as a CLI argument from the gate orchestrator or parse it from `.h-mad/impl-plan.md`, otherwise the mechanical check cannot execute.

## Should-fix
- **Successor linkage for renamed pins (Axis A - Gap)** — The plan states a declared rename requires "a successor pin that resolves and passes" (AC-4.3), but doesn't specify where this successor pin is declared. If a `renamed` tombstone requires a `successor_pin` field, this should be explicitly added to the schema. Alternatively, if renaming a test just means updating the `pin` field of the existing `id` in place (without a tombstone), the plan should clarify that mechanism.

## Nit
None
