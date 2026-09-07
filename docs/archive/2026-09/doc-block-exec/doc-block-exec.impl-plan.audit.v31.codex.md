## Summary
The plan is otherwise unusually concrete about paths, types, mutation anchors, and post-task verification. Task 5s RED setup, however, contradicts the wiring-task contract enforced by the stated assembler.

## Must-fix
- Task 5’s RED WIRE-PINs are specified to fail with `NameError` because `_gate_block` and `_run_recipe` do not exist (`impl-plan.md:1571–1579`), while `h_mad_assemble_tdd.py` explicitly requires a wiring pin’s RED to be a caller-observable assertion, never a missing symbol — this does not demonstrate that the connection is absent or make the planned RED discriminating, violating the connection-enforcement/test-discrimination contract. Define RED-safe callable legacy scaffolds for both helpers and have each pin fail on its empty `dbe` call record; retain the connection-only mutation for the 5e proof.

## Should-fix
None

## Nit
None
