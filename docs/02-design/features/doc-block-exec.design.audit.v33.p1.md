## Summary
The design fully realizes the plan's requirements, maintaining strict alignment with the specified invariants and API contracts. The separation of extraction and selection, stream handling semantics, timeout process-group lifecycle, and cleanup verification are all thoroughly addressed and accurately translated into the test plan and mutation specs.

## Must-fix
None

## Should-fix
None

## Nit
- In the "API / Interface Changes" section, the prose summary for exceptions raised by `substitute` omits `BadSubstArg`, and `run_block` omits `BadTimeout`. Both exceptions are fully documented in the `Error Handling Strategy` table and the Plan, but they should be included in the API prose paragraph for completeness.
