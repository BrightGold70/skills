## Summary
The plan is highly detailed, rigorously aligned with the invariants, and successfully maps all Functional Requirements from the spec without narrowing their scope. The FR reconciliation is below:

| FR | Classification |
|---|---|
| FR-1 | `implemented-as-written` |
| FR-2 | `implemented-as-written` |
| FR-3 | `implemented-as-written` |
| FR-4 | `implemented-as-written` |
| FR-5 | `implemented-as-written` |
| FR-6 | `implemented-as-written` |

## Must-fix
- Axis A (Gap) — The `substitute` API signature in the Implementation Strategy table omits the `BadSubstArg` exception. Spec AC-2.8 explicitly requires the empty-key rule to live in the API where `substitute(block, subs)` raises `BadSubstArg("")` for an empty key. The plan's table currently lists only `MissingSubstitution` and `OverlappingSubstitution`.

## Should-fix
None

## Nit
None
