## Summary
The implementation plan is concrete about the five task boundaries, APIs, mutation guards, wire-only reversions, and verification commands. I found no blocking invariant breach, but one task classification disagrees with the paired design and can select different TDD/assembler handling.

## Must-fix
None

## Should-fix
- Align Task 1\047s task shape across the paired documents: the implementation plan declares it `wiring` (and therefore omits assembler RED counts), while the design\047s Implementation Order calls the same Task 1 a “New-behaviour shape, plus one wire.” — This task creates the new module and most of its API/tests, so the disagreement leaves the executing workflow ambiguous about whether the new-behaviour RED-count contract applies.

## Nit
None
