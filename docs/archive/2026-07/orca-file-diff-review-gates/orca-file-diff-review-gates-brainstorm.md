# Brainstorm: orca-file-diff-review-gates

## Executive Summary
Add Orca-only `hmad-dispatch` verbs `file-diff` and `file-open-changed` that surface Phase-5 diffs (and, for HemaSuite, generated manuscript DOCX / desk-check diffs) in the Orca editor at H-MAD human-in-loop review gates, instead of forcing the operator to review in terminal scrollback.

## Problem Statement
At H-MAD's human review gates — plan/design approval (Phases 3/4) and Phase-6 verification — the operator reviews changes as raw text in terminal scrollback. For a multi-file Phase-5 diff (or a HemaSuite manuscript DOCX), scrollback is a poor review surface: no syntax highlighting, no side-by-side, no file navigation. Orca has a native editor with `file diff` / `file open-changed`, but h-mad has no verb to invoke it.

## Proposed Approach
Two Orca-only `hmad-dispatch` verbs mirroring the Tier-2/Tier-3 guard+argv pattern:
- `file-diff <path> [--staged] [--worktree <sel>]` → wraps `orca file diff <path> [--staged] [--worktree <sel>] [--json]`.
- `file-open-changed [--mode edit|diff|both] [--worktree <sel>]` → wraps `orca file open-changed [--mode …] [--worktree …] [--json]`.

Then document, in `SKILL.md`, that at each human review gate (Phase 3/4 approval, Phase 6a) the orchestrator MAY call `file-open-changed --mode diff` so the operator reviews the diff in Orca's editor. The call is **best-effort and non-blocking**: on cmux (no Orca editor) it is skipped and the gate proceeds exactly as today. HemaSuite consumes the same verb to surface a generated manuscript DOCX diff — documented as usage, no HemaSuite code change required in this feature.

## Alternatives Considered
- **A dedicated diff-render in the terminal** (e.g. `git diff --color | less`): rejected — reinvents what Orca's editor already does natively; no DOCX rendering; still terminal-bound.
- **Auto-open on every gate (blocking)**: rejected — a blocking editor open would stall autonomous runs and cmux sessions; the verb must be best-effort and skip cleanly off-Orca.
- **Bake it into the existing `send`/`read` scrape flow**: rejected — diff-surfacing is a distinct concern from agent-pane I/O; a separate verb keeps the substrate abstraction clean.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| Verb blocks/hangs waiting for editor on Orca | M | Best-effort, non-blocking invocation; document that gate proceeds regardless of verb outcome |
| cmux path regresses (verb called where no Orca) | M | `_require_orca` guard → non-zero + skip; gate logic treats a non-zero file-verb as "diff not surfaced", never a gate failure |
| Live-Orca e2e gap (no Orca editor runtime to validate) | H | Stub-test argv/JSON; deferred live-Orca carry (shared gap) |
| Scope creep into HemaSuite manuscript rendering | L | HemaSuite is documented usage only; no HemaSuite code in this feature |

## Dependencies
- Tier-1 `orca-native-transport` (substrate detect, `_require_orca`).
- Tier-3 `_json_extract` helper (shipped `bba5123`) — reused for any JSON passthrough.
- Orca `file` command family (`diff`, `open`, `open-changed`) — verified in `agent-context --json` schema v1.

## Open Questions
- Does `file-diff` return diff text (for capture) or only open the editor? Schema shows `--json` — reconcile whether `--json` yields the diff payload or an editor-open ack, at design.
- Which gates get auto-surface vs operator-invoked-only? Lean: document at Phase 3/4/6 gates as an optional orchestrator step, not mandatory — confirm in spec.

## Version History
- v1.0: Initial brainstorm draft.
