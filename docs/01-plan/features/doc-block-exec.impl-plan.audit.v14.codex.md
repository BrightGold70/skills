## Summary
The plan is detailed and largely internally coherent, but two of the promised eight Task 5 wire mutations are not implementable from it. It also retains a now-false cross-document statement about the fault-injection count.

## Must-fix
- Task 5 does not specify the `find`/`replace` bodies for `exec-scan-executes` or `consumer-from-import` — the plan promises `doc_block_exec_wire.json` with eight exact-once `str.replace` mutations and an `ALL_CAUGHT` result, but these two rows provide only a mechanism. Their actual anchors, complete type-correct replacement text, and named-killer execution must be stated; otherwise the mutation verification required for two wire guards is not reproducible and a no-op/incorrect mutation can falsely certify the connection tests.

## Should-fix
- The Conventions claim that design v1.65 and spec v1.39 still require “exactly six named fault injections” and leave that contradiction for a later design cycle, but the paired current documents say seven (`design` Test Strategy; `spec` v1.40). Update the stale sentence and make one authoritative taxonomy: six module-level seams plus the instance-level Popen injection, seven total.

## Nit
None
