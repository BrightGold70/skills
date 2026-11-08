---
title: "Commit trail's graft-to-trail rename of the repo agent config, but keep the new Gemini and grok configs local"
author: Hawk
date: 2026-11-08
branch: main
cost: { minutes: 4, tokens: 40761 }
id: l-e5e4f0d3
scope: repo
status: active
src: agent
touches:
  - AGENTS.md
  - opencode.json
---

## Decided
- trail's session-start upkeep rewrote the repo's agent config from graft to trail. Commit that rename as its own chore commit: the AGENTS.md block, the opencode MCP entry, and the deletion of the graft-only Claude MCP file. The committed config named `graft`, which is no longer installed, so it pointed at a missing binary.
- The Gemini and grok configs trail also generated stay untracked, matching the 2026-11-06 operator choice not to commit untracked files.

## Tried and ruled out
- Committing the Gemini/grok configs too: it changes every machine and agent that uses the repo, and nobody asked for it.
- Discarding with git restore: trail's upkeep rewrites these files again on its next version change.
- Leaving them uncommitted: the tree stays dirty, and the two Macs drift apart.

## Watch out
- Expect the same rewrite on the other Mac. Once this commit is pulled it is already resolved; don't re-commit it from there.

In the code:
- committed: AGENTS.md (graft:start→trail:start block), opencode.json (mcp.graft→mcp.trail), .mcp.json deleted (graft mcp only)
- left untracked: GEMINI.md, .gemini/settings.json, .grok/config.toml, .grok/skills/
- commit msg: `chore(trail): migrate repo agent config from graft to trail`
