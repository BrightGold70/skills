# Handoff — Orca pin identity ('id:' line)

**Date:** 2026-07-28
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Shipped a TUI-independent pin-identity diagnostic into `hmad-dispatch env`. Trigger was an operator misread: on 2026-07-28 correct auto-detect pins were re-flagged as false positives because `terminal read`/`.preview` showed `cursor:0` + empty on both Codex/agy panes. That emptiness is an artifact of a full-screen TUI running on the alternate screen buffer — not a dead/wrong pane. Resolution code was already correct (Pass 0 paneKey join). Fixed the *diagnosability* gap. Merged to main via PR #15 (`d3e216e`), 226 dispatch tests green.

## Key Learnings

- Orca full-screen TUI (Codex, agy) runs on the **alternate screen buffer**; `terminal read` reports `cursor:0` and `.preview` reads empty even while live mid-audit. API artifact, NOT a dead/wrong pane — never read identity/liveness off preview emptiness for a TUI pane.
- `worktree ps --json` `agents[]` carries TUI-independent confirmation fields beyond agentType/paneKey: `state`, `updatedAt`, `taskTitle`, `lastAssistantMessage` — all populated regardless of screen buffer. `lastAssistantMessage` independently identified the reviewer pane (still held last session's plan-cycle-4 audit).
- Resolution logic (`_orca_find` Pass 0 = `_orca_find_by_pane`) was already correct and prioritized first; the episode was operator-side, not a code bug. Fix was additive diagnostics only, no resolution contract touched.

## Next Steps

None required — work shipped and merged. Optional follow-ups if the pattern recurs:

1. `[suggested]` If two same-`agentType` agents ever share one worktree, Pass 0 declines (n>1) → falls to unreliable title/preview passes. Consider a `lastAssistantMessage`/`taskTitle` tie-break in `_orca_find_by_pane` — `h-mad/scripts/hmad-dispatch.sh:260`.
2. `[suggested]` Confirm whether a **human-adopted** pane (typing `codex` into an already-open shell) registers in `worktree ps agents[]` — open question from #9870 closeout.

## Open / Blocked Items

- None — PR #15 merged, branch deleted, local main synced.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — new `_orca_identity` helper + `env` `id:` line
- `docs/learnings.md` — gotcha entry (alt-screen buffer)

**Uncommitted changes:** none

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
git pull --ff-only
# confirm identity line:
bash h-mad/scripts/hmad-dispatch.sh env   # look for 'id: <agentType> state=... last="..."'
```

**Related docs:**
- Auto-memory `feedback_orca_agent_identity_by_content.md` (updated with the alt-screen-buffer refinement)
- PR: https://github.com/BrightGold70/skills/pull/15
- Orca issue [#9870](https://github.com/stablyai/orca/issues/9870) (closed — the missing identity field, found in a different call)
