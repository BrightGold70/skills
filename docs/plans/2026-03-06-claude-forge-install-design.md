# Design: Install claude-forge alongside OMC

**Date:** 2026-03-06
**Status:** Approved

## Goal

Install [claude-forge](https://github.com/sangrokjung/claude-forge) into `~/.claude/` alongside the existing oh-my-claudecode (OMC) plugin without interfering with OMC's configuration, hooks, HUD, or plugin system.

## Current State

- **OMC v4.7.6** installed as a Claude Code plugin
  - `~/.claude/CLAUDE.md` with OMC markers + user customizations (Aline OneContext)
  - `~/.claude/settings.json` with Aline hooks, OMC plugin, HUD statusline, agent teams env
  - `~/.claude/hud/omc-hud.mjs` for statusline
  - `~/.claude/.omc-config.json` for preferences
  - `~/.claude/commands/sc/` (SuperClaude)
  - `~/.claude/skills/onecontext/` (Aline)
- **No existing:** `agents/`, `rules/`, `hooks/` directories

## Approach: Selective Cherry-Pick Install

Clone claude-forge to `~/claude-forge/`, then selectively install components. Never run `install.sh`.

### Component Strategy

| Component | Method | Rationale |
|-----------|--------|-----------|
| `agents/` (11) | Symlink dir | New dir, zero conflict |
| `rules/` (9) | Symlink dir | New dir, zero conflict |
| `hooks/` (15) | Symlink dir | New dir, OMC uses plugin hooks |
| `commands/` (40) | Copy contents | Preserves existing `sc/` |
| `skills/` (15) | Copy contents | Preserves existing `onecontext/` |
| `cc-chips-custom/` | Symlink dir | Needed by forge scripts |
| `scripts/` | Symlink dir | Utility scripts |

### settings.json Merge

**Hooks:** Append forge's hook arrays to existing arrays per event type.

```
Existing events: Stop, UserPromptSubmit, PermissionRequest (Aline)
Added events:    PreToolUse, PostToolUse, SessionStart, TaskCompleted
Appended to:     Stop (forge adds session-wrap-suggest, work-tracker-stop)
                 UserPromptSubmit (forge adds work-tracker-prompt)
```

**Permissions:** Add forge's deny-list only. Do not modify allow-list.

**Preserved (no change):**
- `statusLine` (OMC HUD)
- `enabledPlugins` (OMC + all plugins)
- `extraKnownMarketplaces` (OMC)
- `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` (already set)

**Added:**
- `env.ENABLE_TOOL_SEARCH: "auto:5"` (forge default)
- `permissions.deny` array (comprehensive deny-list)

### MCP Servers

Add via `claude mcp add` (skip if already configured):
- `memory` — knowledge graph MCP
- `jina-reader` — web content reader
- Skip: `context7` (already installed), `exa` (skipped earlier), `github` (skipped earlier), `fetch` (redundant with WebFetch)

### Tracking

Write `~/.claude/.forge-meta.json` containing:
- Repo path, install date, version
- List of copied command/skill files (for uninstall/update)

### Uninstall Path

Script removes:
1. Symlinked dirs: `agents/`, `rules/`, `hooks/`, `cc-chips-custom/`, `scripts/`
2. Forge-origin files from `commands/` and `skills/` (via meta tracking)
3. Forge hooks from `settings.json`
4. Forge deny-list from `settings.json`
5. `.forge-meta.json`

### Update Path

- `git pull` in `~/claude-forge/` auto-updates symlinked dirs
- Re-run copy step for commands/skills
- Re-run settings merge (idempotent)

## Risks

| Risk | Mitigation |
|------|-----------|
| Forge hooks fail (not executable) | `chmod +x` during install |
| Hook timeouts slow Claude | Forge hooks have 5s timeouts |
| Future OMC update conflicts | Different layers (plugin vs filesystem) |
| Forge `settings.json` drift | Never run `install.sh`; use merge script |
| Name clashes in commands/skills | Verified: zero current clashes |
