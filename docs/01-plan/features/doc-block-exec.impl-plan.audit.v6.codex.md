## Summary
The plan is concrete about task boundaries, tests, mutation rows, and connection enforcement; I found no remaining hard invariant gap. Two non-blocking documentation/implementation-detail issues remain.

## Must-fix
None

## Should-fix
- The provenance header still identifies the source design as v1.53 and the paired plan as v1.55, while the current design is v1.55 and the implementation-plan text incorporates v1.54–v1.55 changes — update the source revision/commit references so implementation and later audits have one auditable contract baseline.
- Task 1 calls section boundaries “ATX headings” but never fixes the heading-recognition grammar (permitted indentation, required whitespace after the hash run, maximum run length, and treatment of closing hashes) or supplies a discriminator for malformed lookalikes — this leaves a safety-relevant scanner rule to implementer interpretation and can make `extract` and `fence_aware_end` select different textual boundaries from the stated contract.

## Nit
None
