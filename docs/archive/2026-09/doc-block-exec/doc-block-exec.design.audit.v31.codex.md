## Summary
The design is largely aligned with the 49 spec acceptance criteria, but two contracts remain non-deterministic or contradictory at the API boundary. Axis C reconciliation: 

| ACs | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.2, AC-2.4–AC-2.8 | implemented-as-written |
| AC-2.3 | absent |
| AC-3.1–AC-3.11, AC-3.13–AC-3.14 | implemented-as-written |
| AC-3.12 | restated (internally contradictory) |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix
- AC-2.3’s ordering guarantee is absent. The spec requires “one `missing_key: <k>` detail line each in block order,” while the design says only “every missing key gets its own detail line” and has no ordering algorithm or test. An absent key has no position in the block, so this cannot be implemented faithfully as written; choose and state a meaningful deterministic order (for example input-map insertion order or lexicographic order), amend the spec to that rule, and pin it with a multi-key test.
- AC-3.12 has two incompatible `rc` contracts. The spec says “A run with a preamble reports `rc`/`stdout`/`stderr` for the combined invocation”; the design’s preamble prose agrees, but `RunResult.rc` is documented as “the BLOCK’s exit code.” A failing strict preamble can prevent any block command from running, so no separate block rc exists. Define `rc` as the combined shell invocation’s exit code everywhere (including the dataclass comment) and test the preamble-failure case against that single meaning.

## Should-fix
None

## Nit
None
