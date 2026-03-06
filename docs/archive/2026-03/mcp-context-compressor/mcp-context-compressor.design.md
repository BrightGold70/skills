# Design: MCP Context Compressor

**Feature**: `mcp-context-compressor`
**Phase**: Design
**Created**: 2026-03-06
**References**: [Plan](../../01-plan/features/mcp-context-compressor.plan.md)

---

## Architecture Overview

```
Claude Code Tool Call
        │
        ▼
┌─────────────────────────────┐
│  PreToolUse Hook            │  ← mcp-pre-tool.sh
│  • Cache lookup             │
│  • Return [cached] if hit   │
└────────────┬────────────────┘
             │ cache miss
             ▼
     Real MCP Server
             │
             ▼ raw response
┌─────────────────────────────┐
│  PostToolUse Hook           │  ← mcp-post-tool.sh
│  • Save original to cache   │
│  • Detect tool type         │
│  • Apply compression rule   │
│  • Inject compressed output │
└─────────────────────────────┘
        │
        ▼
 Claude Context Window
 (compressed response)
```

---

## Hook Contracts

### PreToolUse Hook: `mcp-pre-tool.sh`

**Trigger**: Every MCP tool call, before execution
**Input** (env vars set by Claude Code):
```
CLAUDE_TOOL_NAME      e.g. "mcp__serena__read_file"
CLAUDE_TOOL_INPUT     JSON string of tool arguments
CLAUDE_SESSION_ID     unique per conversation session
```

**Cache lookup logic**:
```bash
CACHE_KEY=$(echo "${CLAUDE_TOOL_NAME}:${CLAUDE_TOOL_INPUT}" | sha256sum | cut -c1-16)
CACHE_FILE="${WORKTREE}/.omc/mcp-cache/${CLAUDE_SESSION_ID}/${CACHE_KEY}.json"

if [ -f "$CACHE_FILE" ]; then
    TURN=$(jq -r '.turn' "$CACHE_FILE")
    FULL_PATH=$(jq -r '.fullPath' "$CACHE_FILE")
    # Output intercept signal
    echo "CACHE_HIT:${TURN}:${FULL_PATH}"
    exit 0
fi
exit 0  # cache miss — proceed normally
```

**Output**: Writes to stdout only. `CACHE_HIT:` prefix tells the PostToolUse hook to skip compression and inject the reference text instead.

---

### PostToolUse Hook: `mcp-post-tool.sh`

**Trigger**: Every MCP tool call, after execution
**Input** (env vars):
```
CLAUDE_TOOL_NAME      tool identifier
CLAUDE_TOOL_INPUT     original arguments JSON
CLAUDE_TOOL_OUTPUT    raw response (may be very large)
CLAUDE_SESSION_ID     session identifier
CLAUDE_TURN_NUMBER    current conversation turn
```

**Processing flow**:
```
1. If output line count <= MIN_LINES (20): skip, pass through unchanged
2. Load compression rule for CLAUDE_TOOL_NAME from mcp-compressor.json
   - If no specific rule: use "default" rule
3. Save full output to .omc/mcp-cache/{session}/{hash}.json
4. Apply compression rule → compressed_output
5. Prepend compression header to compressed_output
6. Write compressed_output back (replaces CLAUDE_TOOL_OUTPUT)
7. Update cache index with {key, turn, fullPath, lineCount}
```

**Compression header format**:
```
[MCP Compressor] {tool_name} response compressed {original}→{compressed} lines.
Full output saved: .omc/mcp-cache/{session}/{hash}.json (use Read tool if needed)
────────────────────────────────────────────────────────────
{compressed content}
```

---

## Compression Rules Schema

**File**: `.claude/mcp-compressor.json`

```json
{
  "version": "1.0",
  "settings": {
    "min_lines_to_compress": 20,
    "cache_max_entries": 50,
    "budget_tiers": {
      "normal":     { "threshold": 0.75, "max_lines_multiplier": 1.0 },
      "aggressive": { "threshold": 0.50, "max_lines_multiplier": 0.5 },
      "emergency":  { "threshold": 0.00, "max_lines_multiplier": 0.25 }
    }
  },
  "rules": {
    "default": {
      "strategy": "truncate",
      "keep_first": 20,
      "keep_last": 10,
      "separator": "... [{omitted} lines omitted] ..."
    },
    "mcp__serena__read_file": {
      "strategy": "truncate",
      "keep_first": 50,
      "keep_last": 20
    },
    "mcp__serena__list_dir": {
      "strategy": "head",
      "max_lines": 30,
      "separator": "... [{omitted} more entries] ..."
    },
    "mcp__serena__search_for_pattern": {
      "strategy": "snippet",
      "max_matches": 10,
      "context_lines": 2,
      "separator": "... [{omitted} more matches] ..."
    },
    "mcp__serena__find_symbol": {
      "strategy": "snippet",
      "max_matches": 5,
      "context_lines": 3
    },
    "mcp__plugin_context-mode_context-mode__search": {
      "strategy": "snippet",
      "max_matches": 8,
      "context_lines": 1
    },
    "mcp__plugin_serena_serena__read_file": {
      "strategy": "truncate",
      "keep_first": 50,
      "keep_last": 20
    },
    "mcp__plugin_serena_serena__list_dir": {
      "strategy": "head",
      "max_lines": 30
    },
    "mcp__plugin_serena_serena__search_for_pattern": {
      "strategy": "snippet",
      "max_matches": 10,
      "context_lines": 2
    }
  }
}
```

### Compression Strategies

| Strategy | Description | Parameters |
|----------|-------------|------------|
| `truncate` | Keep first N + last M lines, omit middle | `keep_first`, `keep_last` |
| `head` | Keep only first N lines | `max_lines` |
| `tail` | Keep only last N lines | `max_lines` |
| `snippet` | Keep top-N match blocks with context | `max_matches`, `context_lines` |

---

## Cache File Structure

**Directory**: `.omc/mcp-cache/{CLAUDE_SESSION_ID}/`

**Per-entry file**: `{hash16}.json`
```json
{
  "key": "mcp__serena__read_file:abc123...",
  "tool": "mcp__serena__read_file",
  "turn": 5,
  "timestamp": "2026-03-06T10:30:00Z",
  "lineCount": { "original": 342, "compressed": 72 },
  "fullPath": ".omc/mcp-cache/sess_abc/abc123def456.json",
  "fullContent": "... raw MCP output ..."
}
```

**Cache index**: `{session_id}/index.json`
```json
{
  "entries": [
    { "key": "abc123", "tool": "...", "turn": 5, "lru": 3 }
  ],
  "count": 1,
  "maxEntries": 50
}
```

LRU eviction: when `count >= maxEntries`, remove entry with lowest `lru` value.

---

## Budget Tier Estimation

Context budget is estimated by tracking cumulative output length across the session.
No exact token counting — approximate heuristic:

```bash
BUDGET_FILE=".omc/mcp-cache/${SESSION_ID}/budget.json"
# Each PostToolUse adds compressed_chars to running total
# Remaining % = max(0, 1 - total_chars / 200000)
# 200000 chars ≈ ~50K tokens (rough estimate for 200K token window)
```

Tier selection uses `budget_tiers` thresholds from config. Multiplier applied to `max_lines`:
- Normal (>75%): `max_lines * 1.0`
- Aggressive (50–75%): `max_lines * 0.5`
- Emergency (<50%): `max_lines * 0.25`

---

## File Structure to Create

```
.claude/
  hooks/
    mcp-pre-tool.sh          # PreToolUse hook
    mcp-post-tool.sh         # PostToolUse hook
  mcp-compressor.json        # Compression rules config

.omc/
  mcp-cache/
    {session_id}/
      index.json             # LRU cache index
      budget.json            # Context budget tracker
      {hash16}.json          # Per-response cache entries
```

**Hook registration** (in `.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "mcp__*", "hooks": [{ "type": "command", "command": "bash .claude/hooks/mcp-pre-tool.sh" }] }
    ],
    "PostToolUse": [
      { "matcher": "mcp__*", "hooks": [{ "type": "command", "command": "bash .claude/hooks/mcp-post-tool.sh" }] }
    ]
  }
}
```

---

## Edge Cases & Handling

| Case | Handling |
|------|---------|
| Hook script fails | Silent fail — pass through original response unchanged |
| Cache directory missing | Auto-create on first PostToolUse call |
| JSON parse error in config | Use hardcoded default rule |
| Tool name not in rules | Apply `default` rule |
| Response already short (≤20 lines) | Skip compression entirely |
| Binary/non-text response | Skip compression (detect via `file` command) |
| `.omc/` not writeable | Disable caching, compression-only mode |

---

## Implementation Order (Do Phase)

1. Create `.claude/mcp-compressor.json` with default rules
2. Implement `mcp-post-tool.sh` (compression engine — core value)
3. Implement `mcp-pre-tool.sh` (cache lookup)
4. Register hooks in `.claude/settings.json`
5. Manual test: trigger a large MCP response, verify compression header appears
6. Test cache hit: call same tool twice, verify `[cached]` reference on second call

---

## Success Criteria (from Plan)

- Large MCP responses (>100 lines) reduced by ≥50% in context
- Cache hit rate ≥30% in multi-tool sessions
- Hook overhead <100ms per call
- No information loss: full content always accessible via `.omc/mcp-cache/`
