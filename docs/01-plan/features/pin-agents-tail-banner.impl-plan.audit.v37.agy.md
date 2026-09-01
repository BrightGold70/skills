AUDIT-pin-agents-tail-banner-impl-plan-v37-BEGIN
## Summary
The implementation plan is highly detailed, well-structured, and correctly implements the changes required by the design. However, the hoisting of the rival banner computation in Task 4 introduces a bash local scoping bug that silently disables the rival rejection logic.

## Must-fix
- **`rival_tail_re` assignment shadowed by `local` declaration** — In Task 4, the assignment `rival_tail_re="$(_agent_tail_re "$rival")"` is placed immediately after the Pass 1 `case "$token" in` block (around line 536). However, Task 3 adds the declaration `local tail_re rival_tail_re ...` inside Pass 3 (inserted after Pass 2, around line 574). Because Bash's `local` creates an uninitialized local variable that shadows any previously assigned value in the same scope, the `rival_tail_re` variable assigned at line 536 is wiped out when Pass 3 begins, causing the rival rejection test to always fail silently. The assignment must either be moved down into Pass 3 (beside `tail_re=...`), or the `local rival_tail_re` declaration must be hoisted up to the `local rival_re="" rival=""` declaration above Pass 1.

## Should-fix
None

## Nit
- **Contradictory location described in T4 prose** — Task 4 states that `rival_tail_re` is computed "HERE, beside `tail_re`", but the accompanying code block explicitly attaches it to the Pass 1 `case` statement, which is physically separated from `tail_re` by several dozen lines (Pass 1 and Pass 2). This discrepancy makes the instructions confusing.
AUDIT-pin-agents-tail-banner-impl-plan-v37-END
