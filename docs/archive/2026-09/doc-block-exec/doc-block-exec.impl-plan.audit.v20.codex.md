## Summary
The plan is highly specific about production APIs, task order, and the two connection wires. One required verification artifact remains under-specified, so its claimed `ALL_CAUGHT` result is not reproducibly implementable from this plan.

## Must-fix
- `h-mad/tests/mutation-specs/doc_block_exec.json` is specified as 75 harness rows, but the plan gives most rows only a name/mechanism (for example all Task 2–4 rows and most Task 1 rows), not their concrete `file`, exact-once `find`, `replace`, and full `test` payloads. The harness applies literal `str.replace` and rejects non-exact anchors; leaving those values to the implementer means the required `ALL_CAUGHT` evidence and the stated one-mutation-per-guard contract cannot be reproduced or audited, violating mutation verification/test discrimination. Spell out every row (or include the complete JSON) with its exact payload, as the plan already does for the Task 1 `docsections.json` and Task 5 wire rows.

## Should-fix
None

## Nit
None
