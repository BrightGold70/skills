AUDIT-pin-agents-tail-banner-impl-plan-v44-BEGIN
## Summary
The task graph, RED split, wire registry, prescribed matcher, and embedded mutation spec otherwise re-derive cleanly: 45 nodes at 32 FAIL / 13 PASS, three registered wires, and 39 mutation entries. One live mutation-count claim is stale, and the header's two paired-document revision citations also lag the files they identify.

## Must-fix
- The live proof-column explanation still says it is “not an index of the 38 mutations,” but the embedded JSON now contains 39 mutations — `tail-re-version-loosened` raised the inventory from 38 to 39 in v1.45, and the v1.46 history itself reports 39/39. This is a current carried count that was not re-derived after the mutation was added, violating the base “Counts a dispatch reports” invariant; change the live inventory reference to 39 (the historical v42 references to 38 remain valid).

## Should-fix
- The provenance header cites design v1.35 and spec v1.17, while the paired files now end at design v1.36 and spec v1.18 — both newer revisions contain the audit-v42 matcher/corpus tightening this implementation plan depends on, so the source pointers should be advanced together.

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v44-END
