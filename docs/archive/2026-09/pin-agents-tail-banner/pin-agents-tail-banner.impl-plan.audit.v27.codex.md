## Summary
The task graph, 41-node 29/12 RED split, and 31-mutation inventory reconcile, but the v26 prose-safety correction is incomplete and was not carried to the paired spec. The proposed pass can still resolve an ordinary shell pane from line-leading prose, so the plan is not ready to dispatch.

## Must-fix
- The proposed line-start anchor does not establish AC-3.17's claim that ordinary prose declines — direct probes using the actual `_agent_pv_re` output inside the prescribed `tail_re` matched `OpenAI Codex documentation changed`, `model: gpt-5 migration notes`, `Antigravity CLI documentation`, `Gemini 3.1 Pro compared with Claude`, and `## Gemini 3.1 Pro release notes`. With one such shell pane in `$scoped`, the pass still resolves it as the agent, contradicting the plan's “Never resolve to the wrong pane” goal and the base Assumption-verification requirement; add line-leading/heading prose to the negative corpus and narrow the tail-specific matcher to a measured banner/status-line grammar that rejects it while replaying the real pane artifacts as positive controls.
- The paired spec was not back-propagated with the new evidence rule — spec v1.8 still requires matching the existing `_agent_pv_re` signature, presents it as a program-banner discriminator, and contains no anchored/prose acceptance criterion, while impl-plan AC-3.17 labels itself “spec FR-2” even though FR-2 specifies only exactly-one cardinality. This cross-document contract gap leaves the load-bearing false-positive rule absent from the authoritative 15-AC spec; add the exact tail-only matcher constraint and a testable prose-rejection AC, then re-derive every affected AC/count citation.

## Should-fix
- The implementation-plan header cites design v1.21, but the current design is v1.22 and v1.22 is the revision that introduced the anchor — update the provenance citation so dispatch does not claim an older source than the code block it carries.
- Task 3 would leave `_agent_pv_re`'s existing source comment saying its strings cannot occur in ordinary prose while the new tail-pass comment says that premise was falsified — include correction of that nearby production comment so the implemented wrapper does not contain mutually exclusive guidance.

## Nit
None
