---
title: trail overrides the OMC HUD status line
author: Hawk
date: 2026-10-18
branch: main
cost: { minutes: 2, tokens: 37552 }
touches:
  - docs/bug-trail-statusline-overrides-omc-hud.md
---

## Decided
- Root cause: trail's mergeTrailLocal writes statusLine into <repo>/.claude/settings.local.json whenever that file has none; it never reads ~/.claude/settings.json, where the OMC HUD lives. Project-local beats user scope, so the HUD disappears per repo. Full note: docs/bug-trail-statusline-overrides-omc-hud.md.
- Durable fix: GRAFT_NO_STATUSLINE=1 in ~/.claude/settings.json env, plus deleting statusLine/subagentStatusLine from the repo's local settings.
- Both bars at once: the user-level statusLine runs ~/.claude/hud/omc-plus-trail.sh. It reads stdin once, prints the OMC HUD, then `node <project>/.trail/statusline.cjs` on the same input when that file exists (errors swallowed). Repos without trail show the HUD alone.
- The .mcp.json deletion is trail 0.23's intended migration (clearOldLayout → dropServer removes graft/trail servers; the file goes when empty). trail gives Claude Code no MCP server, only hooks + the `trail` CLI.

## Tried and ruled out
- "OMC HUD broken": hud files and the global statusLine are intact; the 12:30 rewire only added graft hooks globally.
- An OMC HUD option to include another command's output: none in 5.7.4 (omc-hud.mjs only loads the plugin's dist/hud), hence the wrapper.
- "Deleted at 12:42": those mtimes were a `git rebase --autostash` writing stashed files back. The deletion was the 12:30:38 rewire. Read mtimes against `git reflog`.

## Watch out
- trail's session-start upkeep re-runs init on every version change and on graft→trail migration, replaying statusline:true, so a hand-deleted override returns after an upgrade unless the env opt-out is set.
- Restoring graft's layout (.mcp.json, AGENTS.md, opencode.json) may be undone at the next session start: shouldMoveToTrail fires while trail is on PATH, unless GRAFT_NO_TRAIL_SWITCH=1.
- An OMC update or omc-setup may reset statusLine to the plain HUD, dropping the wrapper.
