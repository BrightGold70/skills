# Plan: orca-git-native-checkpoints-and-merge-gate

## Executive Summary
Add a single `worktree-comment` wrapper verb, flip the substrate default to Orca, and thread Orca-native checkpoints + a safety-valve merge gate through `handoff` and `h-mad`, all substrate-gated so non-Orca runs are byte-identical to today.

## Overview
Orca exposes git-native surfaces (`worktree set --comment`, `worktree current/ps`, `orchestration gate-create/resolve`) that `handoff` ignores entirely and `h-mad` uses only partially. This plan wires those surfaces into both skills behind the existing `hmad-dispatch` abstraction so progress is durable and mobile-visible and the Phase-5 merge carries a decision record — without adding an Orca hard dependency.

## Scope
`hmad-dispatch.sh` (one new verb + one detection-default change), `handoff/SKILL.md` (WRITE stamp + READ reconcile, both gated), `h-mad/SKILL.md` + `references/orchestration-mode.md` (merge-gate contract, progress checkpoints, diff-anchoring note, ship-path doc). Tests in `h-mad/tests/`. No product/runtime code outside the skills.

## Goals
- G1 — one shared Orca-comment chokepoint both skills call (FR-1).
- G2 — Orca becomes the default substrate when both binaries present (FR-2).
- G3 — `handoff` gains durable WRITE checkpoints + READ worktree reconcile (FR-3, FR-4).
- G4 — non-Orca behavior is unchanged and every Orca enrichment degrades non-fatally (FR-5).
- G5 — Phase-5 winner-merge carries a decision record; conflicts/ambiguity block for a human (FR-6).
- G6 — follow-on: progress checkpoints, diff-anchored review, documented ship path (FR-7, FR-8, FR-9).

## Requirements
- FR-1 `worktree-comment` verb · FR-2 default flip · FR-3 WRITE stamp · FR-4 READ reconcile · FR-5 degradation · FR-6 merge gate · FR-7 progress checkpoints · FR-8 diff-anchoring · FR-9 ship-path doc.

## Implementation Strategy
- **Wrapper (FR-1, FR-2)**: add `_cmd_worktree_comment()` mirroring `_cmd_worktree_rm` — `_require_orca` guard, `_need text`, default selector `active`, call `orca worktree set --worktree <sel> --comment <text> --json`, propagate non-zero + Orca stderr on `ok:false`. Add `_cmd_worktree_current()` mirroring `_cmd_worktree_ps` — `_require_orca` guard, `orca worktree current --json`, emit the JSON payload (read-only, no mutation). Register both `worktree-comment` and `worktree-current` in `main()` and the header verb list. For FR-2, reorder the two binary-presence branches in `_detect_substrate` so "both present" falls to `orca`; keep the `HMAD_SUBSTRATE` and marker branches above it untouched; update the precedence comment.
- **handoff (FR-3, FR-4, FR-5)**: the skill is prose-driven (`SKILL.md`), so changes are added *protocol steps* that invoke `hmad-dispatch`, not new code. WRITE gains a final "stamp checkpoint" step (calls `worktree-comment active`), READ gains a "worktree reconcile" step under the existing reconcile section (calls `worktree-current` + `worktree-ps`, both existing/new wrapper verbs — never raw `orca`). Both steps are prefixed with a substrate check and a documented non-fatal skip marker. `handoff` invokes `hmad-dispatch` by its installed path, preserving skill self-containment (no import of h-mad internals — the wrapper is a CLI, not a library) and the single-Orca-chokepoint invariant (no raw `orca` in the skill body).
- **merge gate (FR-6)**: in the Phase-5 fanout section of `references/orchestration-mode.md` (and the SKILL Phase-5 sub-section), replace the bare `git merge --no-ff` step with a gated sequence: attempt merge; on clean success + clean verdict → `gate-create`+`gate-resolve yes` (recorded, non-blocking) + marker; on conflict → `git merge --abort` + blocking `gate-create` + `await`/`gate-resolve`; on `DRIFT`/non-clean verdict → no merge, blocking gate. Guard the whole gated path on `orchestration: on`; else the existing serial fallback runs unchanged.
- **follow-on docs (FR-7, FR-8, FR-9)**: progress-checkpoint calls added to the fanout loop; a note that review-diff surfacing anchors to the worktree base ref; a ship-path subsection documenting Orca commit→push(`--force-with-lease`)→PR with the force-push invariant restated.
- **Deliberately untouched**: existing verbs, `_send_text`/`_resolve_target`/`_orca_find` logic, cmux paths, the audit-gate/state scripts.

## Architecture Considerations
- **Single Orca chokepoint**: both skills route ALL Orca access through `hmad-dispatch` verbs — writes via `worktree-comment`, READ reconcile via `worktree-current` (new) + `worktree-ps` (existing); no raw `orca` calls land in skill bodies (repo Axis B: self-containment; matches the existing wrapper abstraction). FR-4 therefore requires a `worktree-current` verb, added under FR-1.
- **Fail-open enrichment**: Orca calls are best-effort; a non-zero result is logged and swallowed by the caller, never propagated as a skill failure (FR-5). This mirrors the existing `diff_surface_skipped` pattern already in the SKILL.
- **Default-flip blast radius**: the flip only changes the "both binaries present, no override, no marker" case. HemaSuite pins `HMAD_SUBSTRATE=cmux`; document the flip in `agent-substrate.md` so the cmux fallback is explicit.
- **Gate only under orchestration**: the merge gate requires a pinned coordinator (`orchestration: on`); serial/non-orchestrated Phase-5 keeps its gate-free `git merge --no-ff` so the change cannot stall existing flows.
- **Two handoff copies**: repo copy is authoritative for development; the `~/.claude/skills/handoff` install copy sync is a closure step, not code.

## Deliverables
| Deliverable | Type | Satisfies |
|---|---|---|
| `_cmd_worktree_comment` + `main()` case + header verb list | CLI verb | FR-1 |
| `_cmd_worktree_current` + `main()` case + header verb list | CLI verb | FR-1, FR-4 |
| `_detect_substrate` both-present → orca + comment | detection change | FR-2 |
| handoff WRITE checkpoint-stamp step | SKILL protocol | FR-3, FR-5 |
| handoff READ worktree-reconcile step | SKILL protocol | FR-4, FR-5 |
| handoff SKILL.md contract/frontmatter update | manifest | FR-3 |
| Phase-5 merge-gate sequence | SKILL + reference protocol | FR-6 |
| Progress-checkpoint calls in fanout loop | reference protocol | FR-7 |
| Diff-anchoring note | reference doc | FR-8 |
| Ship-path subsection | reference doc | FR-9 |
| `test_hmad_dispatch` cases for the new verb + detection flip | pytest | FR-1, FR-2 |

## Risks and Mitigation
| Risk | Impact | Mitigation |
|---|---|---|
| Default flip breaks HemaSuite cmux dispatch | Wrong agent substrate | Only "both present" case changes; `HMAD_SUBSTRATE=cmux`/markers still win; document in agent-substrate.md; test AC-2.3/2.4 |
| Blocking merge gate stalls autonomous block | Hung Phase-5 | Gate blocks only on conflict/DRIFT/dirty; clean path auto-resolves; gated path guarded on `orchestration: on` |
| Prose SKILL changes untestable by pytest | Silent contract drift | Testable surface (verb + detection) covered by pytest; SKILL prose changes verified by gap-analysis + agy 6a-prime reachability, not unit tests |
| Worktree comment overwrites user's manual status | Lost UI note | Namespaced `handoff:`/`h-mad` prefixes; documented as skill-owned prefixes |
| handoff install copy diverges | Stale installed skill | Closure step: re-sync `~/.claude/skills/handoff` from repo; flagged in report |

## Convention Prerequisites
- Branch `feature/NNN-orca-git-native-checkpoints-and-merge-gate` off `main` at Phase 5c.
- `hmad-dispatch` on PATH; conda `python3` (jsonschema) for state scripts.
- Repo Axis B (skill self-containment, manifest integrity) governs the audit.

## Success Criteria
- All spec ACs pass automated tests where testable (FR-1, FR-2 via pytest); prose-protocol ACs (FR-3…FR-9) verified by gap-analysis ≥90% + agy 6a-prime reachability review.
- `hmad-dispatch env` under Orca still resolves agents + orchestration; non-Orca `handoff` output byte-identical to pre-feature.
- No new push/force-push automation; force-push invariant intact.

## Out-of-Scope (confirmed from spec)
- Replacing the markdown handoff doc with Orca comments.
- Syncing the `~/.claude/skills/handoff` install copy (manual closure step).
- A new automated commit/push/PR verb (FR-9 document-only).
- Any HemaSuite code change.
- Gating merges when orchestration is off.

## Next Steps
Approve plan v1.0 → agy audit cycle (Axis A/B/C) → exit on must=0 AND should=0 → Phase 4 design.

## Version History
- v1.0: Initial plan draft.
- v1.1: Resolved plan-audit cycle-1 must-fix (FR-4 contradiction). READ reconcile now routes through wrapper verbs `worktree-current` (new, added to FR-1 deliverables) + `worktree-ps` (existing), removing the raw-`orca`-vs-chokepoint contradiction. Chokepoint architecture note clarified to cover reads as well as writes.
