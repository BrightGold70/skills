# billion-context integration assessment for H-MAD and handoff

Date: 2026-10-22
Status: Investigation only; no installation, integration, or configuration change
Upstream: https://github.com/ranxianglei/billion-context
Reviewed upstream commit: `0a9c639e5339d495fbc458f25ea8f15b3c2d355a`
Upstream package version at that commit: `0.1.204` (not a claim about the latest published release)
Local scope: `h-mad/` and `handoff/` in the skills worktree
Related assessment: [ai-memory integration](2026-10-22-ai-memory-hmad-handoff-integration.analysis.md)

## Recommendation

Billion-context is worth an isolated pilot for long H-MAD implementation sessions. Default adoption should wait until parallel reviews, hook activation, and evidence preservation are verified. Its integration surface is substantially more invasive than ai-memory's.

| Component | Appropriate responsibility |
| --- | --- |
| billion-context | Compress the active conversation; search and restore compressed history |
| ai-memory | Retrieve durable knowledge and session history across agents and projects |
| H-MAD and handoff | Own gates, feature claims, reconciliation, task restoration, and canonical artifacts |

Billion-context sits between the agent and model API, rewrites conversation history, and supplies compression tools. Its exported handoff is a conversation export; it does not implement the local handoff skill's ownership-transfer protocol.

Sources: [architecture](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/README.md#how-it-works) and [handoff export implementation](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/kernel/src/handoff.ts#L59).

The proposed division of responsibilities is an architectural inference from the reviewed implementation, not a validated integration.

## Integration findings

### Parallel Codex launcher processes conflict over one home

Confidence: High for the launcher constraint; compatibility with the local parallel workflow remains unverified.

`bili codex` uses a fixed `<CODEX_HOME>-bili` overlay. A second live launcher using that home is explicitly refused, with tests verifying the refusal. Wrapping every H-MAD reviewer command with `bili codex` would therefore need a different, validated launch arrangement.

This restriction concerns launcher processes. It does not establish that native subagents within one process fail. Separate host homes or a shared-proxy routing arrangement are investigation candidates, not proven remedies; they must preserve credentials, hooks, trust, identity, and reviewer independence.

Sources: [launcher implementation](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/src/launcher.ts#L2973) and [overlay concurrency tests](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/tests/overlay-busy-lock.test.ts#L57).

### Exact audit evidence needs explicit preservation

Confidence: High for the compression policy; the necessary H-MAD preservation mapping remains unverified.

The kernel provides configurable protection, but its defaults deliberately allow `read` and `bash` results to become compressible immediately. H-MAD depends on exact verdicts, source reads, approvals, and RED/GREEN evidence. Those records should remain in canonical files and be reread when making gate decisions. A compressed recollection cannot establish that a gate passed.

Do not assume the generic tool patterns match the tools exposed by every host. Verify actual tool names and any wrapper projections before defining protection rules. Keep implementation authors and independent reviewers on the existing fresh-context contracts.

Sources: [kernel protection rules](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/kernel/src/protected.ts#L12) and [local H-MAD runtime contract](../../h-mad/references/codex-runtime.md).

### The runtime takes over parts of host compaction and configuration

Confidence: High for the documented and implemented launch behavior; local hook activation under that behavior is unverified.

The documented Codex path requires traffic routing through the proxy. Installing its MCP companion alone does not enable compression. The launcher supplies proxy and CA settings, changes `CODEX_HOME`, and can force embedded execution with `--no-daemon`. Codex compaction interception is enabled by default.

H-MAD hook trust and activation must be verified under that effective configuration. A parser self-check alone does not prove the hook fires in a launched session. Existing feature claims, halt conditions, and the canonical handoff document remain owned by their current local mechanisms.

Sources: [Codex integration](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/CLIENTS.md#L466), [compaction configuration](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/CONFIGURATION.md#L242), and [local H-MAD hook requirements](../../h-mad/references/codex-runtime.md).

### Independent review isolation requires host-specific verification

Confidence: Medium for compatibility with H-MAD; direct implementation evidence exists for the supported metadata path.

The implementation partitions non-root Codex threads when matching thread metadata is present and includes isolation tests. Missing or mismatched metadata falls back to the older identity chain. This is promising engineering evidence, but insufficient to assume installed hosts preserve fresh reviewer contexts.

Verify both model-request identity and MCP tool-call identity. Successful compression in the main thread does not prove an independent reviewer is isolated or bound to the right compression state.

Sources: [thread identity implementation](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/src/session-id.ts#L290), [thread isolation test](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/tests/codex-turn-isolation.test.ts#L68), and [MCP per-call identity handling](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/src/mcp.ts#L327).

### Some API continuation shapes remain incompatible

Confidence: High for the documented limitation; whether local clients exercise it is unknown.

The project documents incomplete support for Responses API continuations using `previous_response_id`. Stripping that reference from a delta-only request can lose earlier context while still returning HTTP 200. Full-history replay is an important prerequisite for a pilot; verify the actual client and provider request shape rather than assuming all Responses traffic is equivalent.

Source: [native chaining limitation](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/TECHNICAL-NOTES.md#L269).

## Savings claims and evidence limits

Billions of tokens describes cumulative processing across a long session, including repeated inputs. It does not mean simultaneous billion-token attention. The paper's approximately 5.3-fold saving is a counterfactual estimate. Its controlled pilot reports roughly 31–54% fewer billed tokens under specific workloads.

The pilot used a particular evaluation model and workload; it does not establish savings or quality parity for H-MAD. The paper also identifies observational deployment evidence, instrument sensitivity limits, and pending broader evaluations. Benefit for the local workflow remains unmeasured.

Source: [paper, savings model and controlled pilot](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/paper/model-driven-incremental-hierarchical-compression-training-free-multi-generational-context-management-for-long-lived-coding-agents.md#L230).

## Pilot boundaries

Start with one implementation lane, retaining fresh independent reviewers and the existing handoff workflow. Compare an equivalent run without compression. Measure total cost including summarization, latency, exact-evidence recovery, restart recovery, and hook enforcement.

Pin the build and account for both update mechanisms. The advisory watcher can install a different version, including a rollback target, even when ordinary auto-update is disabled. Disabling only ordinary auto-update does not establish a fixed-version experiment.

Source: [advisory update implementation](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/src/advisory.ts#L1).

The license includes an additional attribution requirement. Incorporation into a product or service needs to account for the actual license text rather than relying only on the package's MIT label.

Source: [license](https://github.com/ranxianglei/billion-context/blob/0a9c639e5339d495fbc458f25ea8f15b3c2d355a/LICENSE).

## Follow-up investigation

- [ ] Record exact host and provider versions and confirm that their model traffic can be routed through the intended proxy path.
- [ ] Establish a launch arrangement for concurrent H-MAD lanes that avoids overlay collisions and preserves hook trust and credentials.
- [ ] Verify root, author, reviewer, and guardian thread isolation using actual request and tool-call identities.
- [ ] Prove the H-MAD TDD hook is active under the effective launched configuration, including its denial behavior.
- [ ] Map evidence-protection patterns to actual host tool names and verify recovery of exact approvals, verdicts, source spans, and RED/GREEN results after compression.
- [ ] Confirm full-history replay and exercise native and intercepted compaction paths.
- [ ] Test restart and handoff recovery while keeping canonical local documents and feature claims authoritative.
- [ ] Freeze all applicable update mechanisms for a reproducible pilot and record the effective build throughout the run.
- [ ] Compare total billed usage, summarization overhead, latency, re-reads, and task correctness against an equivalent uncompressed run.
- [ ] Review storage, retention, optional encryption, and license attribution before broader adoption.

## Validation limits

This assessment used source, documentation, and test inspection. The package was not installed, configuration was not changed, and upstream tests were not executed. No live H-MAD or handoff integration was exercised.

Graft execution was blocked by the active H-MAD Phase 5 shell policy. Local read-only files and the GitHub connector supplied the evidence. No hook policy or workflow state was changed.
