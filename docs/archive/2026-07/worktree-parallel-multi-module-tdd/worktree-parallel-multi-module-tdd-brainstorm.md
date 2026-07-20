# Brainstorm: worktree-parallel-multi-module-tdd

## Executive Summary
H-MAD Phase 5 dispatches Codex serially in one shared working tree; add Orca-worktree-backed parallel fanout so independent impl-plan modules run concurrently (one isolated worktree + one dispatched agent each), collapsing multi-module wall-clock toward the slowest single module.

## Problem Statement
Phase 5 (Implementation) runs the impl-plan task DAG **one module at a time** in the shared working tree, even though the impl-plan already declares per-module dependencies and many modules are independent. A feature with N independent modules pays ~N× the wall-clock of a single module for no correctness reason — the serialization is an artifact of the shared tree (parallel Codex agents would collide on files), not of the task graph.

## Proposed Approach
Add three Orca-only `hmad-dispatch` verbs mirroring the Tier-2 guard/JSON pattern:
- `worktree-create <name> [--agent <a>] [--base <ref>]` → wraps `orca worktree create --name <module> [--agent <id>] [--base-branch <ref>] --json`; returns the worktree id/handle.
- `worktree-ps` → wraps `orca worktree ps --json`; compact orchestration summary across worktrees.
- `worktree-rm <sel> [--force]` → wraps `orca worktree rm --worktree <sel> [--force] --json`.

Then Phase 5 fans out: for each **independent** impl-plan task, create one Orca worktree + dispatch one Codex agent (RED then GREEN) into it, `await` each `worker_done` via the Tier-2 orchestration verbs, and merge per module. **Dependent** tasks stay serial (topological order preserved). This turns Tier-2's coordination primitives into true parallelism — the missing piece of the arc.

Fanout is **additive and Orca-only**: when substrate is cmux, or Orca has no coordinator pin, or the impl-plan DAG is fully linear, Phase 5 falls back to the existing serial path unchanged.

## Alternatives Considered
- **cmux multi-pane parallelism** (one Codex pane per module in the shared tree): rejected — panes share one working tree, so concurrent writes collide; no isolation primitive. Worktrees are the isolation Orca gives natively.
- **git worktree directly (no Orca)**: rejected — the h-mad Orca layer already owns worktree lifecycle via `orca worktree *`, and Orca-hosted agents attach to the worktree by handle; hand-rolling `git worktree add` + agent placement duplicates that and breaks the substrate abstraction.
- **Parallelize inside a single Codex session** (one agent, many modules at once): rejected — defeats per-module RED/GREEN TDD isolation and the per-module agy spec-compliance review; a drifted module would contaminate the shared session.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Live-Orca e2e gap — no Orca-hosted-agent runtime to validate against (cmux session only) | H | Unit-test verb argv/JSON against `orca` stubs (same standing gap as Tier 1/2/launch-profile); mark live-Orca e2e as an explicit deferred carry, not a completion blocker |
| Merge conflicts when independent worktrees touch a shared file the DAG didn't mark dependent | M | Merge per module in dependency order; on conflict, halt that module → serial-fallback re-dispatch; document that "independent" = no shared production file in impl-plan |
| Orphaned worktrees on halt mid-fanout | M | `worktree-rm` cleanup in the halt path + a `worktree-ps` reconcile at Phase-5 entry |
| DAG mis-classification (task marked independent but truly dependent) | L | Parallelize only tasks whose `Dependencies on other tasks: None`; anything with a dep stays serial |
| Fanout obscures which module failed | L | Per-worktree labels + `worker_done` carries module id (Tier-2 contract) |

## Dependencies
- **Tier 1 `orca-native-transport`** (shipped `a2cdfe2`) — corrected Orca verbs, handle-pin identity.
- **Tier 2 `orca-native-orchestration`** (shipped `f1bcf97`) — `task-create/dispatch/await/gate-*`, structured `worker_done` collection, coordinator-handle injection. Fanout `await` reuses these.
- Orca `worktree` command family (`create/ps/list/rm`) — verified present in `orca agent-context --json` schema v1.

## Open Questions
- Merge strategy for parallel worktrees: merge each module branch back to the feature branch as it completes (streaming) vs. barrier-then-merge-all? Lean streaming (per-module merge on `worker_done`) to preserve Tier-2's no-barrier ethos — confirm in design.
- Does `orca worktree create --agent` place the agent in the worktree, or must a separate `orchestration dispatch` target the worktree handle? Reconcile against `agent-context --json` at design time.
- Cap on concurrent worktrees (resource bound)? Propose a configurable `HMAD_ORCA_MAX_WORKTREES` (default e.g. 4) — confirm in spec.

## Version History
- v1.0: Initial brainstorm draft.
