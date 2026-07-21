# Brainstorm: orca-git-native-checkpoints-and-merge-gate

## Executive Summary
Exploit Orca's git-native surfaces (worktree comments, worktree enumeration, decision gates) to give the `handoff` and `h-mad` skills durable cross-session progress checkpoints and a safety-valve merge gate, all substrate-detected so a non-Orca environment keeps today's pure-git behavior unchanged.

## Problem Statement
`handoff` has zero Orca integration: its resume/write flow is pure-git and blind to Orca's worktree model, so parallel-work state and mobile-visible progress are invisible to it. `h-mad` Phase-5 fanout merges each winner with an unconditional `git merge --no-ff` (no decision record) and its fanned worktrees are opaque until `worker_done`. Both skills leave Orca's free-text worktree checkpoints, `worktree ps` enumeration, and `gate-create` decision gates unused. Separately, `hmad-dispatch` defaults to `cmux` when both binaries are present, which is the wrong default for this Orca-first environment.

## Proposed Approach
Add one shared wrapper verb and thread it through both skills, gate the merge as a safety valve, and flip the detection default:

- **W (wrapper)**: new `hmad-dispatch worktree-comment <selector> <text>` — thin wrapper over `orca worktree set --worktree <selector> --comment <text> --json`. Single Orca-invocation chokepoint both skills call; non-orca substrate → loud no-op exit (best-effort, non-blocking callers).
- **H1**: `handoff` WRITE mode also stamps a structured worktree comment (`handoff: <slug> · <status> · next: <step>`).
- **H2**: `handoff` READ mode reconciles the doc against live `orca worktree current`/`worktree ps` (right-worktree check + sibling in-flight enumeration) in addition to today's PID/git reconcile.
- **H3**: everything above is substrate-gated — orca present → enrich; else → unchanged pure-git path. Includes flipping the `_detect_substrate` default: both binaries → orca; cmux only → cmux; `HMAD_SUBSTRATE`/session markers still override.
- **M2**: wrap Phase-5 winner-merge in a decision gate. Clean audit + clean merge → auto-resolve `yes` (recorded, no human stop). Conflict / `DRIFT` / dirty tree → blocking `gate-create` for human resolution.
- **M1** (follow-on): fanned workers stamp `worktree-comment` at RED/GREEN/audit boundaries (`h-mad <feature> · <module> · <RED|GREEN|audit> · n/total`).
- **M3** (follow-on): review-gate diffs anchored to the worktree's recorded start-from ref via `hmad-dispatch file-diff`/`file-open-changed` (already present) instead of `HEAD~n`.
- **M4** (follow-on): post-merge ship path documented to use Orca commit→push(`--force-with-lease`)→PR.

## Alternatives Considered
- **Replace the markdown handoff doc entirely with Orca comments**: rejected — the `.md` carries far more than a comment field holds (learnings, blocked items, resume context) and must survive outside Orca. Comment is an *augmentation*, not a replacement.
- **Gate every winner-merge (full human-in-loop)**: rejected — defeats Phase-5 autonomy; a per-module human stop on clean merges is friction without safety gain. Chosen: gate as a conflict/ambiguity safety valve.
- **Flip default to orca unconditionally (cmux only via explicit override)**: rejected — needlessly risks HemaSuite cmux flows; "orca preferred, cmux fallback" achieves the intent with a graceful fallback.
- **Inline `orca worktree set` at each call site**: rejected — violates the substrate-abstraction already built into `hmad-dispatch`; a single wrapper verb keeps Orca invocation in one place (Axis B: skill self-containment).

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Default-flip breaks HemaSuite cmux dispatch | M | `HMAD_SUBSTRATE=cmux` pin + session markers still win; regression surfaced to audit; document in agent-substrate.md |
| Blocking merge gate stalls autonomous block | L | Gate only opens on conflict/DRIFT/dirty; clean path auto-resolves and logs |
| `handoff` install copy (`~/.claude/skills/handoff`, real dir) diverges from repo copy | H | Develop in repo; flag install-sync as an explicit closure step (out of code scope) |
| Worktree-comment fails silently, callers assume it ran | M | Wrapper returns non-zero + stderr message on non-orca/failure; callers log `_skipped` marker, never block |
| Comment overwrites a user's manual worktree status | L | Structured prefix (`handoff:` / `h-mad`) namespaces skill-written comments; document that skill owns those prefixes |

## Dependencies
Orca CLI (`orca worktree set/current/ps`, `orca orchestration gate-create/gate-resolve`) — already used by `hmad-dispatch`. No new external dependency. `jsonschema` (state writer) present via conda interpreter.

## Open Questions
- Should `handoff` H2 sibling-enumeration surface *all* repo worktrees or only those whose comment carries a `handoff:`/`h-mad` prefix? (Lean: all, labeled; let the human read intent.) — resolve in spec.
- M4 ship path: document-only in this feature, or add a `hmad-dispatch commit-push` verb? (Lean: document-only; commit/push stays a UI/AI action per Orca's safety model.) — resolve in spec.

## Version History
- v1.0: Initial brainstorm draft.
