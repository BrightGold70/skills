## Summary
I audited the supplied v1.39 plan and re-derived 45 nodes (32 RED failures, 13 RED passes), 38 mutation entries with complete `_mechanism` metadata, and a green 290-test baseline. The executable plan is coherent, but two required source edits are still described without exact production blocks, and several explanatory surfaces have drifted from the current mixed-fixture and traceability contracts.

## Must-fix
- Task 3 AC-3.18 and Task 5's `h-mad/SKILL.md:315` change lack exact production code blocks — AC-3.18 tells the implementer to rewrite `_agent_pv_re`'s falsified comment without prescribing the replacement, while T5 places its required SKILL wording only in the test constant `_CODEX_CLAIM_NEW`; both leave production text to be invented despite this plan's exact-code contract.

## Should-fix
- Task 3's wire rationale still says `wire-wanted-matcher-disconnected` makes “a prose-only tail resolve,” contradicting AC-3.17 and the mutation's own `_mechanism` — AC-3.17 is now a mixed two-candidate fixture, so an empty matcher matches both panes and causes an ambiguity decline instead of resolving prose.
- AC-3.17 still calls the prose false-positive a violation of FR-2, although the paired spec's FR-2 is only the exactly-one cardinality rule; this is the FR-1 / spec AC-1.4 wrong-pane rule, as the plan's own v1.25 history says.
- The paired design's Components/Implementation Order inventory omits two edits T5 now requires: the Codex fallback enumeration at `hmad-dispatch.sh:513` and the banner-decay claim at `h-mad/SKILL.md:315` — the impl-plan's claim to map all work to design steps 5–6 is therefore broader than the declared source design.

## Nit
- AC-4.6 has a stray closing `**` after “both directions,” despite v1.39's history claiming that marker is absent.
- AC-6.5 says the mutation deletes the rival-rejection `continue`, while the prescribed `drop-rival-rejection` mutation actually keeps the block and replaces its condition with `if false`.
