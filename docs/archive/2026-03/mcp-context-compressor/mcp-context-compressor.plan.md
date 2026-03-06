# Plan: MCP Context Compressor

**Feature**: `mcp-context-compressor`
**Phase**: Plan
**Created**: 2026-03-06
**Approach**: Idea G — MCP Proxy / Compression Layer

---

## Overview

MCP tool responses frequently flood the Claude Code context window with raw, unfiltered data.
A local MCP Proxy sits between Claude Code and all MCP servers, intercepting responses and
applying configurable compression rules before they enter the context window.

This is a standalone local service (or Claude Code hook chain) that requires no changes to
existing MCP servers.

## Problem Statement

MCP tool responses can be extremely large:
- File listings return hundreds of paths when only a few are relevant
- Log reads return thousands of lines when only the tail matters
- Search results include full content when snippets suffice
- Repeated calls return identical data that has already been seen

These responses consume context window budget unnecessarily, reducing the space available
for actual reasoning and increasing cost per session.

Current workaround (`context-mode`) requires manual opt-in per command. An automatic proxy
layer would protect context without requiring behavioral changes from the user or Claude.

## Goals

### Goal 1: Transparent Response Interception

The proxy intercepts all MCP tool responses before they reach Claude's context window,
applying size-based and content-type-based compression rules.

**Acceptance Criteria**:
- Any MCP response exceeding a configurable line threshold (default: 100 lines) is compressed
- Compressed output includes a header noting the truncation and where to find the full output
- Original full response is saved to `.omc/mcp-cache/{tool}-{hash}.txt` for on-demand access
- Claude can retrieve full content via `Read` if needed

### Goal 2: Rule-Based Compression Engine

A plugin-style rule system where each rule targets a specific MCP tool or response pattern.

**Acceptance Criteria**:
- Rules are defined in `.claude/mcp-compressor.json` (user-editable)
- Built-in rules cover: file listings (top N), log output (last N lines), search results (snippets only)
- Rules support: `max_lines`, `keep_first`, `keep_last`, `snippet_length`, `deduplicate`
- Unknown tools fall back to generic truncation rule

### Goal 3: Session-Scoped Response Cache

Within a single conversation session, identical MCP calls return a reference token instead
of repeating the full response.

**Acceptance Criteria**:
- Cache key = `{tool_name}:{args_hash}`
- Cache hit returns: `[cached response from turn N — use Read('.omc/mcp-cache/...') for full content]`
- Cache invalidated on session end
- Cache size capped at 50 entries (LRU eviction)

### Goal 4: Context Budget Awareness

The proxy tracks estimated remaining context budget and tightens compression as budget decreases.

**Acceptance Criteria**:
- Three compression tiers: Normal (>75% remaining), Aggressive (50–75%), Emergency (<50%)
- Each tier applies stricter `max_lines` limits
- Budget estimation uses rough heuristic (not exact token count)

## Non-Goals

- Do NOT modify any MCP server implementations
- Do NOT require changes to Claude Code itself (hook-based implementation only)
- Do NOT implement semantic summarization via LLM (rule-based only, to avoid latency)
- Do NOT compress responses below 20 lines (small responses don't need compression)
- Do NOT support cross-session cache persistence (session-scoped only for v1)

## Architecture Concept

```
Claude Code
    │
    ▼
[PreToolUse Hook] ── checks cache ──► cache hit → inject [cached] reference
    │ (cache miss)
    ▼
Real MCP Server ──► raw response
    │
    ▼
[PostToolUse Hook]
    ├── save full response to .omc/mcp-cache/
    ├── apply compression rule for this tool
    ├── add cache entry
    └── replace response with compressed version
```

## Implementation Approach

This is implemented entirely as Claude Code hooks (no separate process):

- `PreToolUse` hook: cache lookup
- `PostToolUse` hook: compression engine + cache write
- Config file: `.claude/mcp-compressor.json`
- Cache directory: `.omc/mcp-cache/`

Hooks are shell scripts that read/write JSON, keeping the implementation dependency-free.

## Files to Create

| File | Purpose |
|------|---------|
| `.claude/hooks/mcp-pre-tool.sh` | PreToolUse hook — cache lookup |
| `.claude/hooks/mcp-post-tool.sh` | PostToolUse hook — compression + cache write |
| `.claude/mcp-compressor.json` | User-configurable compression rules |
| `docs/02-design/features/mcp-context-compressor.design.md` | Design (next phase) |

## Key Risks

| Risk | Mitigation |
|------|-----------|
| Hook execution latency | Keep compression logic in pure bash/awk, no external processes |
| Compressed output loses needed detail | User can always `Read` the cached full file |
| Cache key collision | Use SHA-256 of `{tool}:{args}` as key |
| Hook not triggered for all MCP tools | Test against all installed MCP servers |

## Success Metrics

- Average MCP response size entering context reduced by ≥50% for large responses
- Zero instances of "context window full" errors during a typical coding session
- Cache hit rate ≥30% in multi-tool sessions (repeated searches, repeated file reads)
- Hook overhead <100ms per tool call
