## Summary
The 45-node RED table and 41-entry mutation JSON re-derive cleanly, and the latest matcher tightening is consistent across the normative block, corpus, spec, and design. One per-arm discrimination gap remains: two independently encoded AGY grammar guards have no mutation that isolates them, while T6's closing AC range also has a count/mapping contradiction and the provenance header is one revision behind both paired documents.

## Must-fix
- The AGY arm's prefix and dotted-version guards are not mutation-verified — `tail-re-prefix-widened` and `tail-re-version-loosened` mutate only the codex arm, even though the plan independently encodes the same boundaries in the AGY arm and includes AGY negatives (`> Antigravity CLI 1.1.22`, `| Gemini 3.1 Pro`, `Antigravity CLI 2026`, `Gemini 3.1 Pro (2026)`). The existing `tail-re-unanchored-agy` changes the entire matcher and cannot attribute a kill to either guard; add AGY-specific, positive-preserving revert mutants pinned to AC-2.12 and update the mutation/anchor counts. Without them, the base Test-discrimination invariant is unmet and the design's claim that the revert mutants prove each closure is broader than what the spec measures.

## Should-fix
- AC-6.12…AC-6.20 says "nine mutations for nine AC numbers" but now enumerates nine green-at-RED proof mutations plus two SIGPIPE mutations, eleven total — state an explicit mapping or revise the AC range/count so dispatch cannot interpret nine criteria against eleven required mutations.
- The header cites design v1.36 and spec v1.18, while the paired files now end at design v1.37 and spec v1.19 after the matcher-prefix/cwd sweep — update both provenance revisions.

## Nit
None
