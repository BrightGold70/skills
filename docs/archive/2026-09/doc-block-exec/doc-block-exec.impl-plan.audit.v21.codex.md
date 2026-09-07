## Summary
The plan is unusually specific about wiring, fault seams, mutation anchors, and verification boundaries. One Task 5 acceptance statement contradicts its own per-row collateral-failure specification.

## Must-fix
None

## Should-fix
- Task 5's wire-spec acceptance criterion says each of the four revert mutants has "only" its named WIRE-PIN failure, but `wire-revert-extract` explicitly and necessarily also fails `test_only_the_exec_scan_hand_rolls_extraction` and `test_gate_block_refuses_an_untagged_recipe` — this makes the stated mutation success condition internally inconsistent; qualify the universal sentence to allow the documented collateral failures (or state that it applies only to the other three reverts).

## Nit
None
