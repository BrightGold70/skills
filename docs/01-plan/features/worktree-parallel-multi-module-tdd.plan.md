# Plan: worktree-parallel-multi-module-tdd

## Executive Summary
Add three Orca-only worktree verbs to `hmad-dispatch.sh` and a Phase-5 parallel-fanout protocol to `SKILL.md`, additively, so independent impl-plan modules implement concurrently in isolated Orca worktrees while every non-orca / linear-DAG / unpinned path keeps the current serial behavior.

## Overview
The Orca adaptation arc gave h-mad substrate-agnostic dispatch (Tier 1) and structured orchestration/`await`/gates (Tier 2). This plan spends those primitives on the actual bottleneck: Phase 5 runs modules serially in one tree. Worktrees are Orca's isolation primitive; combined with Tier-2 `await`, they let independent modules run at once. The change is additive and guarded — it must not alter the serial path that cmux and linear DAGs still use.

## Scope
- In: three `hmad-dispatch` verbs (`worktree-create`, `worktree-ps`, `worktree-rm`); their argv-construction + substrate-guard + JSON-parse logic; a documented Phase-5 fanout protocol in `SKILL.md`; a concurrency cap knob; unit tests against `orca` stubs.
- Out: live-Orca e2e; auto merge-conflict resolution; dependent-task parallelism; any change to Tier-2 verbs or the cmux path.

## Goals
- G1: Independent impl-plan modules implement concurrently in isolated worktrees (FR-1, FR-2, FR-3, FR-4).
- G2: Zero behavioral change on cmux / linear-DAG / unpinned-coordinator paths (FR-5).
- G3: Bounded concurrency via a documented, overridable cap (FR-6).
- G4: All Orca-touching argv reconciled against `orca agent-context --json` schema v1 at build time (cross-cutting invariant).

## Requirements
- FR-1 `worktree-create` verb; FR-2 `worktree-ps` verb; FR-3 `worktree-rm` verb.
- FR-4 Phase-5 fanout protocol; FR-5 serial fallback preserved; FR-6 concurrency bound.

## Implementation Strategy
- **Layer 1 — dispatch verbs** (`h-mad/scripts/hmad-dispatch.sh`): add `worktree-create|worktree-ps|worktree-rm` to the verb dispatch `case`. Each: (a) assert substrate=orca via the existing substrate-detect helper, refuse with a `[H-MAD]` marker + non-zero otherwise (mirror Tier-2 `task-create`/`dispatch` guard); (b) build the `orca worktree …` argv from the schema-verified usage strings; (c) run, capture `--json` stdout, extract the documented key (selector for create; passthrough `.result` for ps), print to stdout. **Single-source extraction (resolves design-audit-v1 must-fix):** the three new verbs MUST route their JSON extraction through ONE shared helper `_json_extract <alternation>` added in this feature — Tier-2 currently *inlines* the `jq '… // empty'` idiom with no shared function, so there is no pre-existing extractor to call; introducing one authoritative helper for the new verbs (rather than three inlined copies that can silently diverge) is what satisfies the Axis B single-source contract. Retrofitting the shipped Tier-2 verbs onto the helper is out-of-scope (would touch guarded, backward-compat verbs).
- **Layer 2 — Phase-5 protocol** (`h-mad/SKILL.md` + `h-mad/references/orchestration-mode.md`): document the partition (independent vs dependent from impl-plan `Dependencies` field), the engage-conjunction (orca ∧ coordinator-pin ∧ ≥2 independent), the fanout loop (create worktree → dispatch Codex RED/GREEN into it → `await` `worker_done` → merge per module in dep order), the cap, and the halt-path `worktree-rm` cleanup. The serial path stays the documented fallback and default.
- **Merge-conflict detection (resolves audit-v1 must-fix 1)**: per-module merge is `git merge --no-ff <module-branch>` executed in the feature branch. A conflict is detected by the merge's **non-zero exit** AND/OR the presence of unmerged paths (`git ls-files --unmerged` non-empty / `git status --porcelain` `UU` entries). On detection: `git merge --abort`, emit `[H-MAD] ... merge_conflict module=<m>`, halt that module and re-dispatch it on the **serial path** (shared tree, after siblings merge). Detection is a mechanical git-exit check — no heuristic.
- **Concurrency cap default (resolves audit-v1 must-fix 2)**: `HMAD_ORCA_MAX_WORKTREES` defaults to **4** when unset (matches spec FR-6 AC-6.1). The fanout holds at most that many live worktrees; independent tasks beyond the cap queue and are logged (`[H-MAD] ... worktree_queued module=<m>`), never dropped.
- **Halt cleanup scope (resolves audit-v1 should-fix)**: on any Phase-5 halt during an active fanout, the halt path tears down **all worktrees in the current fanout group** (enumerate via `worktree-ps`, `worktree-rm` each), not only the failed one — a halt ends the run, so leaving siblings live would orphan them. Cleanup is idempotent (`worktree-rm` on an already-gone selector is a logged no-op).
- **Schema-pin note (resolves audit-v1 nit)**: `orca worktree …` verbs are part of the SAME `orca agent-context --json` schema v1 surface (they appear in that command inventory); the usage strings are pinned from that single schema at build time — no separate worktree schema versioning exists.
- **Deliberately untouched**: existing verbs, the cmux send/read/wait scrape flow, Tier-2 orchestration verbs, the audit gate, the state schema (fanout adds only optional telemetry, no required field).

## Architecture Considerations
- **Substrate abstraction**: worktree verbs are Orca-only by nature (cmux has no worktree primitive). The guard must be a hard refusal, not a silent no-op, so a mis-substrate call is loud. This mirrors how Tier-2 orchestration verbs already refuse on cmux.
- **Identity via handle pin** (Tier-1 lesson): the worktree selector returned by `create` is the handle used by `rm`/`await`; never match worktrees by name-substring (`worktree list` field names are not stable — same class of bug as `terminal list`). The create→selector→rm chain threads the explicit handle.
- **File-indirection** (CLAUDE.md §F-12): `--prompt` content for a worktree-seeded agent comes from a staged file (`--prompt-file`), never a bare argv blob.
- **No-barrier ethos** (Tier-2): prefer streaming per-module merge on `worker_done` over barrier-then-merge-all, so a fast module isn't held by a slow sibling.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `worktree-create` verb | CLI subcommand | FR-1 |
| `worktree-ps` verb | CLI subcommand | FR-2 |
| `worktree-rm` verb | CLI subcommand | FR-3 |
| Phase-5 fanout protocol | SKILL.md + orchestration-mode.md docs | FR-4, FR-5 |
| `HMAD_ORCA_MAX_WORKTREES` cap | env knob + doc | FR-6 |
| `_json_extract` shared helper | bash function (`hmad-dispatch.sh`) | single-source contract (all 3 new verbs) |
| Stub-based verb tests | pytest (`test_hmad_dispatch.py` additions) | FR-1..FR-3, FR-6 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Live-Orca e2e gap | Verbs unvalidated against real runtime | Stub-test argv/JSON; deferred-carry the e2e (explicit, non-blocking) |
| Worktree-create attaches agent vs needs separate dispatch | Fanout wiring wrong | Reconcile `--agent` semantics against `agent-context --json` in design; design branches on the answer |
| Shared-file collision across "independent" modules | Merge conflict mid-fanout | `git merge --no-ff` non-zero exit / unmerged-paths detection → `git merge --abort` → halt module → serial re-dispatch |
| Orphaned worktrees on halt | Resource leak | Halt tears down ALL fanout-group worktrees (`worktree-ps` enumerate → `worktree-rm` each, idempotent) + Phase-5-entry `worktree-ps` reconcile |
| JSON key drift in `orca worktree` output | Selector parse breaks | Pin the key from schema v1 at build time; centralize in one extraction helper |

## Convention Prerequisites
- Feature branch `feature/NNN-worktree-parallel-multi-module-tdd` (Phase 5c).
- Tier 1 + Tier 2 shipped (they are — `a2cdfe2`, `f1bcf97`).
- `orca` present for stub-substitution in tests (tests inject a stub `orca` on PATH, per existing `test_hmad_dispatch.py` pattern).

## Success Criteria
- All spec ACs pass automated tests (stub-asserted argv + JSON parse + substrate guard).
- `test_hmad_dispatch.py` full file stays green (existing verbs untouched).
- SKILL.md fanout section documents partition + engage-conjunction + cap + halt cleanup.
- Every `orca worktree …` argv in the verbs matches the `agent-context --json` schema v1 usage strings.

## Out-of-Scope (confirmed from spec)
- Live-Orca e2e against real Orca-hosted agents.
- Auto merge-conflict resolution.
- Dependent-task parallelism / DAG re-ordering.
- Tier-2 verb changes; cmux-path changes.

## Next Steps
Approve plan v1.0 → agy audit cycle (Axis B: base invariants + skills-repo `.h-mad/invariants.md`) → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v2.0: Audit-v1 fixes — defined `git merge --no-ff` exit/unmerged-paths conflict detection (must-fix 1); stated `HMAD_ORCA_MAX_WORKTREES` default = 4 (must-fix 2); halt tears down ALL fanout-group worktrees (should-fix); clarified `orca worktree` shares agent-context schema v1 (nit).
- v3.0: Back-propagation from design-audit-v1 — corrected the inaccurate "reuse Tier-2's JSON helper" premise (Tier-2 has no shared extractor; it inlines the idiom) and mandated ONE new shared `_json_extract` helper for the three new verbs to satisfy the single-source contract; Tier-2 retrofit declared out-of-scope.
