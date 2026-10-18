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

## Tried and ruled out
- "OMC HUD broken": hud files and the global statusLine are intact; the 12:30 rewire only added graft hooks globally.

## Watch out
- trail's session-start upkeep re-runs init on every version change and on graft→trail migration, replaying statusline:true, so a hand-deleted override returns after an upgrade unless the env opt-out is set.
