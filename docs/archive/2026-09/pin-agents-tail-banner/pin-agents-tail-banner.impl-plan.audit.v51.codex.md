## Summary
The impl-plan is mostly internally consistent after v50: counts re-derive to 45 nodes, the embedded mutation JSON parses at 46 mutations, and the prescribed matcher still decides the 36/12 corpus as claimed. I found one hard mutation-traceability gap in Task 6, plus one design-level interface inconsistency.

## Must-fix
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md:2161` and `:2226` require the mutation harness `mechanism:` lines to name the pinned test/node, but the embedded JSON does not satisfy that contract; for example `tail-re-widened-to-launch-line-agy` at `:1858` names only AC-3.2, and `skill-md-description-reworded` at `:1946` names no pinned node at all. A mechanical scan found 24 of 46 `_mechanism` strings lacking the exact node id from their `test` field, so AC-6.9 is either unpassable as written or the claimed per-mutation traceability is not actually enforced.

## Should-fix
- The design says `Data Model / Schema Changes: None. ... no config` and `API / Interface Changes: None user-facing` at `docs/02-design/features/pin-agents-tail-banner.design.md:309` and `:313`, but the same document tells operators to lower `HMAD_TAIL_READ_TIMEOUT` at `:269` and the impl-plan tests that override as load-bearing. Either document the env var as an interface/config knob, including whether SKILL.md should mention it, or explicitly classify it as internal-only and remove the operator-facing tuning sentence.

## Nit
- `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md:1850` says "All all 14 AGY-arm negatives"; drop the duplicate word.
