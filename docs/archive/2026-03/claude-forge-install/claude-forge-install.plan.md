# Plan: claude-forge-install

**Created:** 2026-03-06
**Status:** Completed
**Phase:** Plan → Design

## 1. Feature Overview

Install [claude-forge](https://github.com/sangrokjung/claude-forge) (11 AI agents, 40 commands, 15 skills, 6-layer security hooks) alongside the existing oh-my-claudecode (OMC) plugin without conflicts.

## 2. Problem Statement

- claude-forge provides valuable agents, commands, and security hooks not available in OMC
- Running `install.sh` directly would destroy OMC's settings.json, HUD, and plugin configuration
- Both tools write to `~/.claude/` — need a coexistence strategy

## 3. Goals

- [ ] Install all claude-forge components (agents, commands, skills, rules, hooks)
- [ ] Preserve OMC plugin config, HUD statusline, Aline hooks
- [ ] Merge forge's security hooks and deny-list into settings.json
- [ ] Add forge's MCP servers (memory, jina-reader)
- [ ] Enable clean uninstall path

## 4. Constraints

- Never run claude-forge's `install.sh` (it does `rm -rf` then symlinks)
- Never overwrite `settings.json` (must merge via jq)
- Preserve existing `~/.claude/commands/sc/` and `~/.claude/skills/onecontext/`
- Keep OMC HUD statusline (not forge's cc-chips)

## 5. Success Criteria

- All 11 forge agents discoverable by Claude Code
- All 40 forge commands available as slash commands
- All 15 forge skills loadable
- Security hooks (secret filter, remote command guard, etc.) active
- OMC features (HUD, plugin system, magic keywords) unaffected
- `settings.json` valid JSON with merged hooks from both systems

## 6. Scope

**In scope:** Selective install of forge components, settings.json merge, MCP server addition, metadata tracking
**Out of scope:** Forge's work tracker (Supabase sync), cc-chips statusline, fork maintenance
