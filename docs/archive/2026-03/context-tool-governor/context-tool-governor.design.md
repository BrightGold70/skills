# Design: Context Tool Governor

**Feature**: `context-tool-governor`
**Phase**: Design
**Created**: 2026-03-06
**Depends On**: Plan — `docs/01-plan/features/context-tool-governor.plan.md`
**Scope**: Global (`~/.claude/`) — applies to all Claude Code sessions

---

## Summary

Three coordinated mechanisms that prevent context bloat at the tool execution layer:

| Goal | Mechanism | Files |
|------|-----------|-------|
| G3 | Grep-first rule in CLAUDE.md | `~/.claude/CLAUDE.md` |
| G1 | PreToolUse size limiter (updatedInput) | `~/.claude/hooks/pretooluse-read-limiter.sh` + `settings.json` |
| G2 | Session re-read block (decision: block) | same hook + session cache file |

Implementation order: G3 → G1 → G2 (risk-ascending).

---

## Goal 3: Grep-First Rule (CLAUDE.md)

### Exact Text to Add

Append to the existing `# === PDCA STUB PREFERENCE ===` section, or add after it as a new block:

```markdown
# === GREP-FIRST RULE ===
# Before using Read to find something in a file, evaluate Grep instead:
#   - Pattern/name/keyword/import search? → Grep (with context or head_limit) NOT Read
#   - Need file for Edit? → Read first (Edit requires file content in context)
#   - Exploring an unknown file? → Read with limit:50 first, then Grep for details
# Grep is faster, uses less context, and finds what you need without loading the full file.
```

**Line budget**: 5 lines added to CLAUDE.md. No section deletion required.

### Acceptance Criteria (G3)

- [ ] Rule present in `~/.claude/CLAUDE.md` after the PDCA stub section
- [ ] Covers: pattern search, Edit exemption, unknown-file exploration
- [ ] ≤5 non-blank lines added

---

## Goal 1: PreToolUse Size Limiter

### Hook Input Contract

Claude Code delivers tool call info to the hook script via stdin as JSON:

```json
{
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/abs/path/to/file.py",
    "limit": 200,
    "offset": 50
  }
}
```

- `limit` and `offset` are optional fields; absent = not specified by Claude

### Hook Output Contract

**Pass-through** (no output, exit 0):
```
(empty stdout)
```

**Inject limit** (updatedInput):
```json
{"updatedInput": {"file_path": "/abs/path/to/file.py", "limit": 100}}
```
Note: `updatedInput` replaces entire `tool_input`; must include `file_path`.

**Block re-read** (decision: block):
```json
{"decision": "block", "reason": "[CACHED] file.py already read this session — use existing context or specify offset for a different section"}
```

### Decision Flow

```
stdin → parse JSON
  |
  ├─ tool_name != "Read"? → exit 0 (pass-through, no output)
  |
  ├─ file_path empty? → exit 0
  |
  ├─ [G2] offset absent AND file in session cache?
  |     → output block JSON, exit 0
  |
  ├─ [G1] limit absent AND offset absent AND file exists?
  |     file_size = wc -c < file_path
  |     file_size > 8192?
  |     → append file_path to cache, output updatedInput JSON, exit 0
  |
  └─ [pass] append file_path to cache (first-read, small file), exit 0
```

### Session Cache Design

**File path**: `~/.claude/session-reads-${PPID}.txt`

- `$$` = hook script PID (changes each call) — DO NOT use
- `$PPID` = parent process PID (Claude Code's hook runner) — stable across calls within one session
- If `$PPID` is unstable across calls (verify during Do phase), fallback: `~/.claude/session-reads-$(date +%Y%m%d-%H).txt` (hourly granularity)

**Cache format**: one absolute file path per line

```
/Users/kimhawk/.claude/CLAUDE.md
/Users/kimhawk/.config/opencode/skill/docs/.pdca-status.json
```

**Cleanup strategy**:
- On hook script startup: if cache file's modification date < today, delete it
- This provides automatic daily cleanup without a SessionStop hook
- One-liner: `find ~/.claude -name "session-reads-*.txt" -mtime +1 -delete 2>/dev/null`

### Hook Script: `~/.claude/hooks/pretooluse-read-limiter.sh`

```bash
#!/usr/bin/env bash
# PreToolUse hook: limit large Read calls + block session re-reads
# Input: JSON on stdin | Output: JSON or empty

set -euo pipefail

# Read full stdin
INPUT=$(cat)

# Extract tool_name (fast grep before python3 invocation)
echo "$INPUT" | grep -q '"tool_name".*"Read"' || exit 0

# Parse fields via python3 (handles edge cases in paths)
read -r FILE_PATH HAS_LIMIT HAS_OFFSET < <(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    ti = d.get('tool_input', {})
    print(
        ti.get('file_path', ''),
        'yes' if 'limit' in ti else 'no',
        'yes' if 'offset' in ti else 'no'
    )
except:
    print('', 'no', 'no')
" <<< "$INPUT")

[ -z "$FILE_PATH" ] && exit 0

# Session cache (PPID = Claude Code's hook runner, stable per session)
CACHE_DIR="$HOME/.claude"
CACHE_FILE="${CACHE_DIR}/session-reads-${PPID}.txt"

# Cleanup stale caches (previous sessions/days)
find "$CACHE_DIR" -name "session-reads-*.txt" -not -newer "$CACHE_DIR" -delete 2>/dev/null || true

# G2: Block re-reads (exempt if offset specified — intentional partial read)
if [ "$HAS_OFFSET" = "no" ] && [ -f "$CACHE_FILE" ] && grep -qxF "$FILE_PATH" "$CACHE_FILE" 2>/dev/null; then
    BASENAME=$(basename "$FILE_PATH")
    python3 -c "import json; print(json.dumps({'decision': 'block', 'reason': '[CACHED] $BASENAME already read this session — use existing context or specify offset for a different section'}))"
    exit 0
fi

# G1: Inject limit for large files (exempt if limit/offset already provided)
if [ "$HAS_LIMIT" = "no" ] && [ "$HAS_OFFSET" = "no" ] && [ -f "$FILE_PATH" ]; then
    FILE_SIZE=$(wc -c < "$FILE_PATH" 2>/dev/null || echo 0)
    if [ "$FILE_SIZE" -gt 8192 ]; then
        # Record in cache before injecting limit
        echo "$FILE_PATH" >> "$CACHE_FILE"
        python3 -c "
import sys, json
d = json.loads(sys.argv[1])
ti = d.get('tool_input', {})
ti['limit'] = 100
print(json.dumps({'updatedInput': ti}))
" "$INPUT"
        exit 0
    fi
fi

# Pass-through: record first-read in cache
echo "$FILE_PATH" >> "$CACHE_FILE"
exit 0
```

### settings.json Addition

Current `~/.claude/settings.json` has no `PreToolUse` hooks. Add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/pretooluse-read-limiter.sh"
          }
        ]
      }
    ]
  }
}
```

**Merge strategy**: Use `jq` to merge into existing `hooks` object without overwriting existing hook types (Stop, UserPromptSubmit, PermissionRequest):

```bash
jq '.hooks.PreToolUse = [{"matcher":"Read","hooks":[{"type":"command","command":"bash ~/.claude/hooks/pretooluse-read-limiter.sh"}]}]' \
  ~/.claude/settings.json > /tmp/settings.tmp && mv /tmp/settings.tmp ~/.claude/settings.json
```

### Acceptance Criteria (G1 + G2)

**G1 — Size limiter**:
- [ ] Hook registered in `settings.json` under `PreToolUse` → `matcher: "Read"`
- [ ] Files ≤8KB: pass-through (no updatedInput, no block)
- [ ] Files >8KB, no limit/offset: inject `{"updatedInput": {"file_path": "...", "limit": 100}}`
- [ ] Files with existing `limit` param: pass-through unchanged
- [ ] Files with `offset` param: pass-through unchanged (exempt from both G1 and G2)

**G2 — Re-read block**:
- [ ] Session cache file created at `~/.claude/session-reads-${PPID}.txt`
- [ ] First read of any file: allowed + appended to cache
- [ ] Second read of same file (no offset): blocked with 1-line reason
- [ ] Read with `offset` specified: always allowed (intentional partial read)
- [ ] Stale cache files (previous sessions) auto-deleted on startup

---

## Edge Cases and Exemptions

| Case | Behavior | Rationale |
|------|----------|-----------|
| Read with `offset` (any file) | Pass-through, no limit, no block | Partial read = intentional; different section of file |
| Read with `limit` (any file) | Pass-through, no additional limit | Claude already constrained it |
| File doesn't exist | Pass-through | Let Read return its own error |
| hook script exits non-zero | Claude Code ignores hook (pass-through) | Fail-safe: never break reads |
| hook script outputs invalid JSON | Claude Code ignores hook (pass-through) | Fail-safe per hook spec |
| File modified after first read (Edit) | Re-read is blocked | Known gap: acceptable for now; offset-based re-reads are exempt |
| Jupyter `.ipynb` files | Treated same as other files (size-based) | ipynb files are typically large → limit applies |
| Binary/image files | Pass-through if ≤8KB, limited if >8KB | Read tool handles binary; limit is still valid |
| Multiple Claude sessions same PPID | Theoretical; PID reuse requires reboot | Negligible collision risk |

---

## Testing Plan

### Manual Tests (during Do phase)

**Test 1: Large file → limit injected**
```bash
# Create test file > 8KB
python3 -c "print('x' * 10000)" > /tmp/bigfile.txt
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/bigfile.txt"}}' | bash ~/.claude/hooks/pretooluse-read-limiter.sh
# Expected: {"updatedInput": {"file_path": "/tmp/bigfile.txt", "limit": 100}}
```

**Test 2: Small file → pass-through**
```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/smallfile.txt"}}' | bash ~/.claude/hooks/pretooluse-read-limiter.sh
# Expected: (empty output, exit 0)
```

**Test 3: Re-read block**
```bash
# After Test 1 (file already in cache)
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/bigfile.txt"}}' | bash ~/.claude/hooks/pretooluse-read-limiter.sh
# Expected: {"decision": "block", "reason": "[CACHED] bigfile.txt already read..."}
```

**Test 4: Re-read with offset → exempt**
```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/bigfile.txt","offset":50}}' | bash ~/.claude/hooks/pretooluse-read-limiter.sh
# Expected: (empty output, no block)
```

**Test 5: Non-Read tool → pass-through**
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | bash ~/.claude/hooks/pretooluse-read-limiter.sh
# Expected: (empty output, exit 0)
```

**Test 6: File with pre-specified limit → pass-through**
```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/bigfile.txt","limit":500}}' | bash ~/.claude/hooks/pretooluse-read-limiter.sh
# Expected: (empty output, no additional limit)
```

---

## Files to Create / Modify

| File | Action | Content |
|------|--------|---------|
| `~/.claude/hooks/pretooluse-read-limiter.sh` | **Create** | Hook script above |
| `~/.claude/settings.json` | **Modify** — add PreToolUse entry | `jq` merge |
| `~/.claude/CLAUDE.md` | **Modify** — append Grep-first rule | 5-line block |

---

## Success Metrics (Verification)

| Metric | Verification Command |
|--------|---------------------|
| Hook registered | `jq '.hooks.PreToolUse' ~/.claude/settings.json` |
| Script executable | `bash -n ~/.claude/hooks/pretooluse-read-limiter.sh && echo ok` |
| Grep-first rule present | `grep -c 'GREP-FIRST' ~/.claude/CLAUDE.md` |
| Large file injection works | Test 1 above produces `updatedInput` |
| Re-read blocked | Test 3 above produces `decision: block` |
| Offset exemption works | Test 4 above produces empty output |
