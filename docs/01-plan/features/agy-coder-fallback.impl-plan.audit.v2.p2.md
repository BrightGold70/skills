AUDIT-agy-coder-fallback-impl-plan-v2-BEGIN
## Summary
The revised implementation plan (`docs/01-plan/features/agy-coder-fallback.impl-plan.md` v1.1 at `fc92becf`) resolves all Cycle 1 findings across both audit tracks (`p1` and `p2`). It passes `h_mad_wire_pin_gate.py` (`WIREPIN: PASS tasks=23 wiring=2 unpinned=0 mislabeled=0`), assembles cleanly across all 23 tasks in both `red` and `green` phases via `h_mad_assemble_tdd.assemble`, and the updated `docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py` probe passes in both `derived` and `shipped` modes while failing under `--control`. All task shapes, RED/GREEN node counts, mutation-row anchors (`CX-FOLD`, `CX-FORCE-SCRIPT`, converse wire rows, signal/marker discipline rows, and OD-2's `T2a`), and acceptance criteria are internally consistent and ready for Phase 5c/5d.

## Must-fix
None

## Should-fix
None

## Nit
None
AUDIT-agy-coder-fallback-impl-plan-v2-END
