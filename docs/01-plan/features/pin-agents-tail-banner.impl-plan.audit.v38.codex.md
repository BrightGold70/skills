AUDIT-pin-agents-tail-banner-impl-plan-v38-BEGIN
## Summary
The implementation plan is structurally coherent: I re-derived 45 test nodes (32 RED failures, 13 RED passes), 38 unique parsed mutations, 34 fence markers, and a zero-test pre-feature mutation selector baseline. The Task 4 scoping and bidirectional-wire corrections now agree across code blocks, tests, and mutations; no blocking implementation or invariant gap remains.

## Must-fix
None

## Should-fix
- The implementation plan header still cites the design as post-audit `v1.32`, but the paired design now ends at `v1.33` after adding the second Pass 4 cross-reference component — update the provenance so the declared source revision includes the cross-document correction this plan relies on.
- `pin-agents-tail-banner.plan.md:88` still attributes the direct 24-negative/12-positive matcher corpus to impl-plan AC-3.17, while the implementation plan and design now assign that helper-level corpus to AC-2.12 and reserve AC-3.17 for the mixed caller-connection fixture — the stale pointer sends verification to the wrong test surface.

## Nit
- `test_tail_pass_prose_mentioning_agent_does_not_resolve` now names a mixed fixture whose expected result is a successful resolution to the real-banner pane; the historical name is misleading even though the AC text and mutation mapping are explicit.
AUDIT-pin-agents-tail-banner-impl-plan-v38-END
