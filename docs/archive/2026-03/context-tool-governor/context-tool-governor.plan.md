# Plan: Context Tool Governor

**Feature**: `context-tool-governor`
**Phase**: Plan
**Created**: 2026-03-06
**Scope**: Global (`~/.claude/`) — applies to all Claude Code sessions

---

## Overview

Extends `claude-context-reduction` by controlling context bloat at the **tool execution layer**
rather than the session baseline layer. Three coordinated mechanisms:

1. **PreToolUse `updatedInput` limiter** — auto-inject `limit` on Read calls for large files;
   prevents large tool outputs before they enter context (fixes GAP-11)
2. **Session read cache + block** — track files read this session in a local state file;
   block re-reads via `decision: "block"` with cached summary
3. **Grep-first rule** — CLAUDE.md behavioral instruction to prefer Grep+head_limit over Read
   for pattern/search tasks

---

## Problem Statement

GAP-11 from `mcp-context-compressor`: PostToolUse hooks **add** to context, never replace.
Raw tool output enters context first; hooks can only append. This makes post-execution
compression ineffective for primary context savings.

The only hook that can prevent large context entries is **PreToolUse**, which supports:
- `updatedInput`: modify tool parameters before execution (limit output at source)
- `decision: "block"` + `reason`: cancel the tool call entirely (re-read prevention)

Current per-call overhead from Read tool (without limiting):
- Typical Python file: 200–900 lines added per Read call
- Multiple reads of same file in one session: 2–5× redundant
- Analysis reads (to understand structure): often only 50–100 lines needed

---

## Goals

### Goal 1: PreToolUse Read Limiter (Structural Fix to GAP-11)

**Mechanism**: Shell hook fires on every `Read` tool call. Checks file size via `stat`.
If file is large (>8KB, ~250 lines), injects `"limit": 100` into the tool input.
Does NOT override explicitly provided `offset`/`limit` values.

**Acceptance Criteria**:
- Hook registered in `~/.claude/settings.json` under `PreToolUse` for `Read` tool
- Hook script at `~/.claude/hooks/pretooluse-read-limiter.sh`
- Files ≤8KB: pass through unchanged
- Files >8KB without existing limit: inject `{"updatedInput": {"limit": 100}}`
- Files with pre-specified `limit` or `offset`: pass through unchanged (no override)
- macOS and Linux compatible (`stat -f%z` / `stat -c%s`)

### Goal 2: Session Read Cache + Re-read Block

**Mechanism**: PreToolUse hook maintains a session state file at
`~/.claude/session-reads-YYYYMMDD-PID.txt` (date+PID ensures per-session reset).
For each Read call: check if file_path is in state file.
- First read: allow, then append `{file_path}|{line_count}` to state file
- Subsequent reads: output `{"decision": "block", "reason": "[CACHED] {file_path} ({N} lines) — already in context this session"}`

**Acceptance Criteria**:
- State file path uses `$$` (shell PID) to ensure uniqueness per session
- State file created on first Read; deleted on shell EXIT trap
- Re-read blocked with 1-line reason (vs full file content re-injected)
- Files that were subsequently Edited are NOT blocked (edit timestamp check)
- Block exemption: if `offset` is specified (partial read = intentional different section)

### Goal 3: Grep-First Rule in CLAUDE.md

**Mechanism**: Add behavioral instruction to `~/.claude/CLAUDE.md` gate section.
Instructs Claude to evaluate Grep before Read for pattern/search tasks.

**Acceptance Criteria**:
- Rule added to CLAUDE.md gate section (not a new section — extends existing guidance)
- Rule covers: function lookup, pattern search, config key lookup, import search
- Rule exemption: when file content is needed for Edit (Read is required)
- Rule references `head_limit` parameter for Grep
- ≤5 lines added to CLAUDE.md

---

## Non-Goals

- Do NOT modify Bash, Glob, or Grep tool hooks (Read is primary bloat source)
- Do NOT implement LLM-based summarization in the hook (shell only, fast)
- Do NOT persist session state across sessions (per-session PID isolation)
- Do NOT limit `offset`-specified reads (intentional partial reads are exempt)

---

## Architecture

```
PreToolUse hook pipeline (Read tool):

Read({file_path, offset?, limit?})
          │
          ▼
  pretooluse-read-limiter.sh
          │
    ┌─────┴──────────────────────┐
    │  1. Re-read check          │
    │     file in session cache? │
    │     → YES: block + reason  │◄── saves full file re-read
    │     → NO: continue         │
    └─────┬──────────────────────┘
          │
    ┌─────┴──────────────────────┐
    │  2. Size check             │
    │     stat file_path         │
    │     > 8KB AND no limit?    │
    │     → YES: inject limit:100│◄── saves ~200-800 lines
    │     → NO: pass through     │
    └─────┬──────────────────────┘
          │
          ▼
       Read executes with (possibly modified) params
          │
          ▼
       Append to session cache: {file_path}|{line_count}
       (via PostToolUse or inline in PreToolUse via background write)
```

```
CLAUDE.md Grep-first rule (behavioral):

Task requires finding something in a file?
  → Is it a pattern/name/keyword search? → Grep + head_limit (NOT Read)
  → Is it for Edit? → Read first (required for Edit context)
  → Is it exploring unknown file? → Read with limit:50 first, then Grep for details
```

---

## Files to Create / Modify

| File | Action | Goal |
|------|--------|------|
| `~/.claude/hooks/pretooluse-read-limiter.sh` | Create — main hook script | 1 + 2 |
| `~/.claude/settings.json` | Modify — add PreToolUse hook entry for Read | 1 + 2 |
| `~/.claude/CLAUDE.md` | Modify — add Grep-first rule (≤5 lines) | 3 |

---

## Key Risks

| Risk | Mitigation |
|------|------------|
| Hook injects limit on file needed for Edit | Edit tool checks: if file was limited, Read again with full content |
| PID reuse between sessions | Date+PID combination makes collision probability negligible |
| `stat` syntax differs macOS/Linux | Use `wc -c < file` as portable fallback |
| Hook outputs invalid JSON → silently ignored | Test hook with `echo '{"file_path":"~/.claude/CLAUDE.md"}' \| bash hook.sh` |
| Block exemption for edited files is complex | Simpler: allow re-read if `offset` param present; full block only for plain re-reads |
| settings.json hooks break existing aline hooks | Append to existing `PreToolUse` array; don't overwrite |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Lines injected per large-file Read | 200–900 | ≤100 (limited) |
| Redundant re-reads per session | ~3–5 | 0 (blocked) |
| Context savings per analysis session | 0 (GAP-11) | ~500–2,000 lines |
| Grep-first adoption rate | 0% | >70% pattern searches |

---

## Implementation Order

1. **Goal 3** first (zero risk, immediate value) — add Grep-first rule to CLAUDE.md (2 min)
2. **Goal 1** — write hook script + register in settings.json; test with manual file reads
3. **Goal 2** — extend hook with session cache + block logic; test re-read blocking
