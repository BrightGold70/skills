# Design: claude-forge-install

**Created:** 2026-03-06
**Status:** Completed
**Plan Reference:** `docs/01-plan/features/claude-forge-install.plan.md`
**Detailed Design:** `docs/plans/2026-03-06-claude-forge-install-design.md`

## 1. Architecture Overview

```
~/claude-forge/              (git clone, source of truth)
├── agents/     ──symlink──→ ~/.claude/agents/
├── rules/      ──symlink──→ ~/.claude/rules/
├── hooks/      ──symlink──→ ~/.claude/hooks/
├── cc-chips-custom/ ─sym──→ ~/.claude/cc-chips-custom/
├── scripts/    ──symlink──→ ~/.claude/scripts/
├── commands/*  ──copy────→  ~/.claude/commands/* (alongside existing sc/)
├── skills/*    ──copy────→  ~/.claude/skills/*   (alongside existing onecontext/)
└── settings.json ─merge──→  ~/.claude/settings.json (jq append, never overwrite)
```

## 2. Component Strategy

| Component | Count | Method | Conflict Risk |
|-----------|-------|--------|---------------|
| agents/ | 11 | Symlink dir | None (new dir) |
| rules/ | 9 | Symlink dir | None (new dir) |
| hooks/ | 15 | Symlink dir | None (OMC uses plugin hooks) |
| commands/ | 40 | Copy files | Low (no name clashes verified) |
| skills/ | 15 | Copy files | Low (no name clashes verified) |
| cc-chips-custom/ | 1 | Symlink dir | None (new dir) |
| scripts/ | 1 | Symlink dir | None (new dir) |

## 3. settings.json Merge Design

### 3.1 Hook Merge (Append Strategy)

Existing hook events are preserved. Forge hooks are **appended** to arrays, never replacing.

| Event | Existing (Keep) | Added from Forge |
|-------|----------------|-----------------|
| PermissionRequest | Aline hook | — |
| UserPromptSubmit | Aline hook | work-tracker-prompt |
| Stop | Aline hook | session-wrap-suggest, work-tracker-stop |
| PreToolUse | — (new) | remote-command-guard (Bash), rate-limiter + mcp-usage-tracker (mcp__*) |
| PostToolUse | — (new) | output-secret-filter, continuous-learning observe, security-auto-trigger (Edit\|Write) |
| SessionStart | — (new) | context-sync-suggest, forge-update-check |
| TaskCompleted | — (new) | task-completed |

### 3.2 Permissions (Deny-List Only)

Add forge's 31-rule deny-list covering:
- Destructive filesystem ops (rm -rf /, sudo, chmod 777)
- Pipe-to-shell attacks (curl|sh, wget|sh)
- Dangerous git ops (force-push main/master, reset --hard, clean -f)
- Shell config overwrites (~/.zshrc, ~/.bashrc, ~/.ssh)
- Package publishing (npm/pnpm/yarn publish)
- System-level ops (docker prune, mkfs, dd)

**Do NOT adopt** the allow-list (keeps current permission prompting behavior).

### 3.3 Preserved Fields (No Change)

- `statusLine` → OMC HUD (`node ~/.claude/hud/omc-hud.mjs`)
- `enabledPlugins` → All current plugins
- `extraKnownMarketplaces` → OMC marketplace
- `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` → Already "1"

### 3.4 Added Fields

- `env.ENABLE_TOOL_SEARCH` → `"auto:5"` (forge default)
- `permissions.deny` → 31-rule array

## 4. MCP Server Additions

| Server | Status | Action |
|--------|--------|--------|
| context7 | Already installed | Skip |
| filesystem | Already installed | Skip |
| memory | Not installed | `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory` |
| jina-reader | Not installed | `claude mcp add jina-reader -- npx -y @jina-ai/mcp-server` |
| exa | User skipped | Skip |
| github | User skipped | Skip |
| fetch | Redundant with WebFetch | Skip |

## 5. Tracking & Metadata

`~/.claude/.forge-meta.json` records:
- Repo path, version, git commit
- Install mode ("selective-cherry-pick")
- Lists of copied commands and skills (for uninstall)
- Symlinked directory names

## 6. Lifecycle Operations

### Update
```bash
cd ~/claude-forge && git pull   # Updates symlinked dirs automatically
# Re-copy commands/skills for updated copies
```

### Uninstall
1. Remove symlinks: agents, rules, hooks, cc-chips-custom, scripts
2. Remove copied files from commands/ and skills/ (per .forge-meta.json)
3. Remove forge hooks from settings.json (reverse jq merge)
4. Remove forge deny-list
5. Remove .forge-meta.json

## 7. Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Hook scripts not executable | `chmod +x` during install |
| Hook timeouts slow Claude | All forge hooks have 5s timeout caps |
| Future name clashes | .forge-meta.json tracks forge-origin files |
| OMC update breaks merge | OMC operates at plugin layer, forge at filesystem layer |
| settings.json corruption | Pre-install backup with timestamp |

## 8. Implementation Plan

See `docs/plans/2026-03-06-claude-forge-install-plan.md` for the 10-task step-by-step implementation.
