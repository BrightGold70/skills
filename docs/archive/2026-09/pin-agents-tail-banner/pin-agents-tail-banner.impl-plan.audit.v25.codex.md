## Summary
The prescribed production flow, 290-test baseline, and authoritative 40-node 28/12 RED split are otherwise coherent. Three live verification/mutation instructions still breach base invariants, and the implementation plan's design-version citation is stale.

## Must-fix
- The live RED-count paragraph still says its commands were “verified to return 40 / 11 / 29,” while the immediately preceding authoritative table and the commands themselves produce 40 / 12 / 28 — this is a live dispatch instruction, not version-history text, and breaches the Counts-a-dispatch-reports invariant by directing readers to a demonstrably false measured split.
- Task 6 mutates only the stream routing of the success marker (`marker-to-stdout`); it has no content-only mutation that keeps `>&2` intact while removing or changing `bound <handle> by tail evidence`, even though AC-3.1 and the live check consume that exact content — the base Mutation-verification invariant requires separate same-anchor mutations for separable stream-routing and message-content guards, so add a content-only marker mutant pinned to AC-3.1 and update the mutation accounting.
- The impl-plan, source plan, and paired design now instruct the operator to remove the isolated pin file's `mktemp -d` directory, but none requires re-reading the resulting state to confirm that directory is absent — directory removal mutates filesystem state, so treating the cleanup command as sufficient violates the base Mutation-verification invariant; retain the directory path and assert it no longer exists after removal on all three live-check surfaces.

## Should-fix
- The impl-plan header still cites the paired design as post-audit v1.18, while the saved design's version history now reaches v1.20 and contains the v23/v24 back-propagations this plan relies on — update the source citation so provenance matches the actual paired document.

## Nit
None
