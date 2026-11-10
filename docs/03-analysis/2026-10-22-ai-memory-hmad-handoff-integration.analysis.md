# ai-memory integration assessment for H-MAD and handoff

Date: 2026-10-22
Status: Investigation only; no integration implemented or configuration changed
Upstream: https://github.com/akitaonrails/ai-memory
Reviewed upstream commit: `1c86aebc14addccc7ac875913d565c681bfa4a50`
Upstream workspace version at that commit: `3.2.0` (not a claim about the latest published release)
Local scope: `h-mad/` and `handoff/` in the skills worktree

## Recommendation

Adopt ai-memory as an optional shared memory and retrieval layer. Keep workflow state, feature ownership, reconciliation, and task restoration in the existing H-MAD and handoff skills.

| Rank | Integration opportunity | Assessment | Confidence |
| --- | --- | --- | --- |
| 1 | Retrieve past decisions, failed approaches, and lessons | Strong fit | High |
| 2 | Discover closeouts across agents and machines | Useful with explicit branch and worktree matching | High |
| 3 | Replace H-MAD state and ownership | Poor fit | High |
| 4 | Replace handoff reconciliation and task restoration | Poor fit | High |

These assessments are architectural inferences from the source evidence below, not runtime validation of an integration.

## Responsibilities and evidence

### ai-memory

Ai-memory supplies searchable session evidence, durable knowledge, and cross-agent continuity through MCP. Basic write, query, and handoff operations work without an LLM provider. This could improve H-MAD's initial research and make handoff learnings available outside Claude's local memory store.

Source: [Programmatic API](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/docs/programmatic-memory.md).

### H-MAD

H-MAD should continue owning phase transitions, approval evidence, halt conditions, and feature claims. Its resume router distinguishes unreadable state, ownership conflicts, completion, and autonomous entry. A retrieved summary is evidence for reconciliation, not a substitute for those decisions.

Local evidence: [resume router](../../h-mad/scripts/h_mad_resume_decision.py#L182), [state writer](../../h-mad/scripts/h_mad_state_write.py#L320), and [Codex runtime contract](../../h-mad/references/codex-runtime.md).

Project state remains `docs/.bkit-memory.json`; project invariants remain `.h-mad/invariants.md`. An ai-memory handoff must not authorize a phase transition, clear a halt, or force a feature takeover.

### handoff

The local handoff skill should continue owning canonical documents, branch selection, reconciliation against git and live state, task restoration, and ownership transfer. It resolves linked worktrees to a shared document store and selects branch-specific closeouts.

Local evidence: [canonical paths and branch identity](../../handoff/scripts/handoff_paths.py#L37), [READ contract](../../handoff/SKILL.md#reading-a-handoff-resume-mode), and [persistent auto-memory handling](../../handoff/references/auto-memories.md).

The existing ai-memory-specific skills were available in the evaluation environment. The local `handoff/SKILL.md` reviewed here contained no direct ai-memory calls; skill availability alone does not establish a working integration.

## Integration issues

### Message acceptance does not acquire feature ownership

Ai-memory atomically consumes a handoff row. That does not acquire the H-MAD feature claim. A receiver must still run H-MAD's ownership checks before starting work. Successful delivery and successful adoption need separate outcomes; there is no demonstrated transaction spanning both stores.

Source: [atomic handoff acceptance](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/crates/ai-memory-store/src/ops.rs#L5041).

Investigate recovery when a message has been accepted but the local feature is owned elsewhere, state is unreadable, or task restoration fails. Do not equate message consumption with a completed takeover.

### Manual handoffs can cross worktree boundaries

`memory_handoff_begin` creates a project-wide handoff even when given `cwd`. Manual rows outrank automatic handoffs. The exposed begin arguments do not include branch, feature, or recipient targeting. Therefore, accepting the latest handoff is unsuitable for concurrent Orca lanes without additional identity checks.

Sources: [begin arguments](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/crates/ai-memory-mcp/src/server.rs#L1397) and [selection logic](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/crates/ai-memory-store/src/reader.rs#L14477).

An adapter should select an exact handoff ID and validate repository identity, branch, worktree, and feature before adoption. Recording `cwd` on a manual handoff does not enforce delivery isolation.

### Skill triggers overlap

Both the local handoff skill and `ai-memory-handoff` claim requests such as "where did we leave off" and "wrap up." Local READ mode also requires a fresh context unless the user explicitly overrides that requirement.

Define routing so the local skill owns the workflow and ai-memory supplies retrieval or transport underneath it. Automatic history injection must not silently bypass local READ or TAKEOVER semantics.

Sources: [local READ contract](../../handoff/SKILL.md#reading-a-handoff-resume-mode) and [upstream handoff skill](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/crates/ai-memory-core/src/routing_skills/ai-memory-handoff/SKILL.md).

### Durable-page skill guidance contradicts the API

The upstream durable-page skill says: "There is no patch or compare-and-write precondition." The implementation supports `expected_page_id` and `create_only`, and includes tests rejecting stale writes. The same stale guidance appears in the Codex and Claude Code plugin copies at the reviewed commit.

An adapter should use the concurrency controls and correct or explicitly supersede that guidance before enabling shared-page updates. Writes replace whole pages and metadata, so a plain read followed by an unconditional write can lose another writer's changes.

Sources: [stale core skill guidance](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/crates/ai-memory-core/src/routing_skills/ai-memory-durable-pages/SKILL.md#L33), [API guide](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/docs/programmatic-memory.md#L108), and [implementation tests](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/crates/ai-memory-mcp/src/server.rs#L22464).

### Static MCP clients need explicit scope

Static clients must pass `workspace` and `project` together. A repository marker should resolve consistently across worktrees. Do not depend on the server's last active project. Session-aware clients that forward the real lifecycle session identity have a different automatic routing contract.

Source: [marker and scope rules](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/docs/marker-file.md).

## Minimum integration proposal

1. **H-MAD entry:** retrieve relevant decisions and gotchas as historical evidence. Current repository files, explicit approvals, and gate results remain authoritative.
2. **Handoff WRITE:** finish the canonical document first, then publish a searchable projection containing repository identity, branch, worktree, feature, source commit, and document path. Define retry and failure behavior before introducing a second write destination.
3. **Handoff READ and TAKEOVER:** validate identity, reconcile current reality, restore tasks, and acquire the local feature claim separately from consuming the ai-memory message.
4. **LEARN:** retain `docs/learnings.md` as the canonical record and publish selected lessons for shared retrieval. Define correction and supersession behavior to prevent drift between stores.

For a pilot, consider offer-only startup behavior:

```toml
[handoff]
claim_on_session_start = false
```

This leaves handoffs open until explicitly accepted. The setting is server-wide, requires a server restart, and affects other operators using that server. It is a proposed configuration, not a change made during this assessment.

Source: [offer-only configuration](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/docs/usage.md#L86).

## Follow-up investigation

- [ ] Inventory the installed ai-memory version, server configuration, lifecycle hooks, and MCP identity support for each host actually used by this worktree.
- [ ] Define one routing owner for local handoff versus ai-memory handoff requests, including fresh-context and mid-session takeover behavior.
- [ ] Specify the adapter's identity envelope and exact-ID selection rules for sibling branches, linked worktrees, and other machines.
- [ ] Define recovery after message acceptance when local adoption or feature claiming fails; verify retries cannot duplicate or lose work.
- [ ] Confirm page precondition support in the deployed version and correct the stale durable-page skill guidance.
- [ ] Verify sibling-worktree isolation, two receivers racing, service unavailability, stale source commits, and page-update conflicts.
- [ ] Check that H-MAD status remains read-only and memory operations cannot bypass approval, TDD, ownership, or halt gates.
- [ ] Decide whether a canonical document plus a searchable projection is sufficient before adding a second single-use handoff mechanism.
- [ ] If external lifecycle capture is later added, choose one capture owner and preserve native session identity rather than duplicating native and orchestrator capture. See [external lifecycle contract](https://github.com/akitaonrails/ai-memory/blob/1c86aebc14addccc7ac875913d565c681bfa4a50/docs/external-lifecycle.md).

## Validation limits

The assessment used source and documentation inspection. Upstream tests were inspected, not executed; no live integration was exercised. No ai-memory MCP tools were exposed in the evaluation session, so installed skill availability did not establish service connectivity.

OneContext and Graft execution were blocked by the active H-MAD Phase 5 shell policy. Local read-only files and the GitHub connector supplied the evidence; prior conversation history remained unverified. No hook policy or workflow state was changed.
