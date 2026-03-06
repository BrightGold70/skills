# Claude-Forge Selective Install Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Install claude-forge components into `~/.claude/` alongside OMC without conflicts, using selective symlinks, file copies, and settings.json merging.

**Architecture:** Clone repo to `~/claude-forge/`, symlink conflict-free dirs (agents, rules, hooks, cc-chips-custom, scripts), copy individual command/skill files, merge forge hooks and deny-list into existing settings.json via jq.

**Tech Stack:** Bash, jq, git, `claude mcp add`

---

### Task 1: Clone claude-forge Repository

**Files:**
- Create: `~/claude-forge/` (git clone)

**Step 1: Clone with submodules**

```bash
git clone --recurse-submodules https://github.com/sangrokjung/claude-forge.git ~/claude-forge
```

**Step 2: Verify clone**

Run: `ls ~/claude-forge/agents ~/claude-forge/commands ~/claude-forge/hooks ~/claude-forge/rules ~/claude-forge/skills`
Expected: All directories listed with contents

**Step 3: Commit note — no commit needed (external repo)**

---

### Task 2: Backup Current Config

**Files:**
- Read: `~/.claude/settings.json`

**Step 1: Create timestamped backup of settings.json**

```bash
cp ~/.claude/settings.json ~/.claude/settings.json.pre-forge.$(date +%Y%m%d_%H%M%S)
```

**Step 2: Verify backup exists**

Run: `ls ~/.claude/settings.json.pre-forge.*`
Expected: One backup file listed

---

### Task 3: Symlink Conflict-Free Directories

**Files:**
- Create symlinks: `~/.claude/agents`, `~/.claude/rules`, `~/.claude/hooks`, `~/.claude/cc-chips-custom`, `~/.claude/scripts`

**Step 1: Create symlinks for directories that don't exist yet**

```bash
ln -sf ~/claude-forge/agents ~/.claude/agents
ln -sf ~/claude-forge/rules ~/.claude/rules
ln -sf ~/claude-forge/hooks ~/.claude/hooks
ln -sf ~/claude-forge/cc-chips-custom ~/.claude/cc-chips-custom
ln -sf ~/claude-forge/scripts ~/.claude/scripts
```

**Step 2: Make hook scripts executable**

```bash
chmod +x ~/claude-forge/hooks/*.sh
chmod +x ~/claude-forge/skills/continuous-learning-v2/hooks/*.sh 2>/dev/null
chmod +x ~/claude-forge/skills/strategic-compact/*.sh 2>/dev/null
chmod +x ~/claude-forge/skills/skill-factory/scripts/*.sh 2>/dev/null
```

**Step 3: Verify symlinks**

Run: `ls -la ~/.claude/agents ~/.claude/rules ~/.claude/hooks`
Expected: All three show `->` pointing to `~/claude-forge/...`

---

### Task 4: Copy Command Files (Preserving Existing)

**Files:**
- Modify: `~/.claude/commands/` (add forge commands alongside existing `sc/`)

**Step 1: Copy forge commands into existing commands directory**

```bash
# Copy individual command files and directories (not the dir itself)
for item in ~/claude-forge/commands/*; do
  name=$(basename "$item")
  if [ ! -e ~/.claude/commands/"$name" ]; then
    cp -r "$item" ~/.claude/commands/"$name"
  else
    echo "SKIP (exists): $name"
  fi
done
```

**Step 2: Record copied files for uninstall tracking**

```bash
# List what was copied
ls ~/claude-forge/commands/ | while read name; do
  [ -e ~/.claude/commands/"$name" ] && echo "$name"
done
```

**Step 3: Verify commands coexist**

Run: `ls ~/.claude/commands/ | head -20`
Expected: Both `sc/` (existing) and forge commands (auto.md, build-fix.md, etc.) present

---

### Task 5: Copy Skill Files (Preserving Existing)

**Files:**
- Modify: `~/.claude/skills/` (add forge skills alongside existing `onecontext/`)

**Step 1: Copy forge skills into existing skills directory**

```bash
for item in ~/claude-forge/skills/*; do
  name=$(basename "$item")
  if [ ! -e ~/.claude/skills/"$name" ]; then
    cp -r "$item" ~/.claude/skills/"$name"
  else
    echo "SKIP (exists): $name"
  fi
done
```

**Step 2: Verify skills coexist**

Run: `ls ~/.claude/skills/`
Expected: Both `onecontext/` (existing) and forge skills (build-system/, security-pipeline/, etc.) present

---

### Task 6: Merge Forge Hooks into settings.json

**Files:**
- Modify: `~/.claude/settings.json`

**Step 1: Add forge's PreToolUse hooks (new event type)**

```bash
jq '.hooks.PreToolUse = (.hooks.PreToolUse // []) + [
  {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "~/.claude/hooks/remote-command-guard.sh", "timeout": 5000}]
  },
  {
    "matcher": "mcp__*",
    "hooks": [
      {"type": "command", "command": "~/.claude/hooks/rate-limiter.sh", "timeout": 5000},
      {"type": "command", "command": "~/.claude/hooks/mcp-usage-tracker.sh"}
    ]
  }
]' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 2: Add forge's PostToolUse hooks (new event type)**

```bash
jq '.hooks.PostToolUse = (.hooks.PostToolUse // []) + [
  {
    "hooks": [
      {"type": "command", "command": "~/.claude/hooks/output-secret-filter.sh", "timeout": 5000},
      {"type": "command", "command": "~/.claude/skills/continuous-learning-v2/hooks/observe.sh"}
    ]
  },
  {
    "matcher": "Edit|Write",
    "hooks": [
      {"type": "command", "command": "~/.claude/hooks/security-auto-trigger.sh"}
    ]
  }
]' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 3: Add forge's SessionStart hooks (new event type)**

```bash
jq '.hooks.SessionStart = (.hooks.SessionStart // []) + [
  {"hooks": [{"type": "command", "command": "~/.claude/hooks/context-sync-suggest.sh"}]},
  {"hooks": [{"type": "command", "command": "~/.claude/hooks/forge-update-check.sh", "timeout": 5000}]}
]' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 4: Append forge's Stop hooks to existing Stop array**

```bash
jq '.hooks.Stop += [
  {"hooks": [{"type": "command", "command": "~/.claude/hooks/session-wrap-suggest.sh"}]}
]' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 5: Add TaskCompleted hooks (new event type)**

```bash
jq '.hooks.TaskCompleted = (.hooks.TaskCompleted // []) + [
  {"matcher": "", "hooks": [{"type": "command", "command": "~/.claude/hooks/task-completed.sh", "timeout": 10000}]}
]' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 6: Verify hooks merged correctly**

Run: `jq '.hooks | keys' ~/.claude/settings.json`
Expected: `["PermissionRequest", "PostToolUse", "PreToolUse", "SessionStart", "Stop", "TaskCompleted", "UserPromptSubmit"]`

---

### Task 7: Add Forge Deny-List to settings.json

**Files:**
- Modify: `~/.claude/settings.json`

**Step 1: Add the comprehensive deny-list**

```bash
jq '.permissions.deny = [
  "Bash(rm -rf /)*", "Bash(rm -rf ~)*", "Bash(rm -rf .)*",
  "Bash(rm -r .)*", "Bash(rm -r ./)*", "Bash(rm -rf *)*",
  "Bash(sudo:*)", "Bash(chmod 777:*)", "Bash(>/dev/*)",
  "Bash(curl*|*sh)*", "Bash(wget*|*sh)*",
  "Bash(*>~/.ssh/*)", "Bash(*>~/.zshrc)*", "Bash(*>~/.bashrc)*",
  "Bash(*>~/.profile)*", "Bash(*>~/.zprofile)*",
  "Bash(git push --force*main)*", "Bash(git push -f*main)*",
  "Bash(git push --force*master)*", "Bash(git push -f*master)*",
  "Bash(git push --force-with-lease*main)*", "Bash(git push --force-with-lease*master)*",
  "Bash(git push origin +main)*", "Bash(git push origin +master)*",
  "Bash(git reset --hard origin/*)*", "Bash(git clean -f*)*",
  "Bash(git checkout -- .)*", "Bash(git restore .)*",
  "Bash(npm publish)*", "Bash(pnpm publish)*", "Bash(yarn publish)*",
  "Bash(docker system prune)*", "Bash(mkfs*)*", "Bash(dd if=*)*"
]' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 2: Add ENABLE_TOOL_SEARCH env var**

```bash
jq '.env.ENABLE_TOOL_SEARCH = "auto:5"' ~/.claude/settings.json > /tmp/settings-merge.json && mv /tmp/settings-merge.json ~/.claude/settings.json
```

**Step 3: Verify settings.json is valid JSON**

Run: `jq empty ~/.claude/settings.json && echo "VALID" || echo "INVALID"`
Expected: `VALID`

---

### Task 8: Add MCP Servers

**Step 1: Add memory MCP server**

```bash
claude mcp add memory -- npx -y @modelcontextprotocol/server-memory
```

**Step 2: Add jina-reader MCP server**

```bash
claude mcp add jina-reader -- npx -y @jina-ai/mcp-server
```

**Step 3: Verify MCP servers**

Run: `claude mcp list`
Expected: context7, filesystem, memory, jina-reader all listed

---

### Task 9: Write Forge Metadata

**Files:**
- Create: `~/.claude/.forge-meta.json`

**Step 1: Generate metadata file**

```bash
FORGE_DIR=~/claude-forge
VERSION=$(git -C "$FORGE_DIR" describe --tags 2>/dev/null || git -C "$FORGE_DIR" rev-parse --short HEAD)
COMMIT=$(git -C "$FORGE_DIR" rev-parse --short HEAD)

# Collect copied files for uninstall tracking
COPIED_COMMANDS=$(ls ~/claude-forge/commands/ | tr '\n' ',' | sed 's/,$//')
COPIED_SKILLS=$(ls ~/claude-forge/skills/ | tr '\n' ',' | sed 's/,$//')

jq -n \
  --arg repo "$FORGE_DIR" \
  --arg version "$VERSION" \
  --arg commit "$COMMIT" \
  --arg date "$(date -Iseconds)" \
  --arg commands "$COPIED_COMMANDS" \
  --arg skills "$COPIED_SKILLS" \
  '{
    repo_path: $repo,
    install_mode: "selective-cherry-pick",
    installed_at: $date,
    version: $version,
    git_commit: $commit,
    copied_commands: ($commands | split(",")),
    copied_skills: ($skills | split(",")),
    symlinked_dirs: ["agents", "rules", "hooks", "cc-chips-custom", "scripts"]
  }' > ~/.claude/.forge-meta.json
```

**Step 2: Verify metadata**

Run: `jq '.' ~/.claude/.forge-meta.json`
Expected: Valid JSON with all fields populated

---

### Task 10: Verify Full Installation

**Step 1: Check all symlinks resolve**

```bash
for dir in agents rules hooks cc-chips-custom scripts; do
  if [ -L ~/.claude/$dir ] && [ -d ~/.claude/$dir ]; then
    echo "OK: $dir -> $(readlink ~/.claude/$dir)"
  else
    echo "FAIL: $dir"
  fi
done
```

Expected: All 5 show OK

**Step 2: Check commands and skills coexist**

```bash
echo "Commands: $(ls ~/.claude/commands/ | wc -l) items"
echo "Skills: $(ls ~/.claude/skills/ | wc -l) items"
echo "Has sc/: $([ -d ~/.claude/commands/sc ] && echo YES || echo NO)"
echo "Has onecontext/: $([ -d ~/.claude/skills/onecontext ] && echo YES || echo NO)"
```

Expected: Both YES, command count ~41+, skills count ~16+

**Step 3: Check settings.json integrity**

```bash
jq empty ~/.claude/settings.json && echo "JSON: VALID" || echo "JSON: INVALID"
jq '.hooks | keys | length' ~/.claude/settings.json
jq '.permissions.deny | length' ~/.claude/settings.json
jq '.statusLine.command' ~/.claude/settings.json
```

Expected: VALID, 7 hook types, 31 deny rules, OMC HUD path

**Step 4: Remind user to restart Claude Code**

Print: "Installation complete. Restart Claude Code for all changes to take effect."
