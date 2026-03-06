# Gap Analysis: MCP Context Compressor

**Feature**: `mcp-context-compressor`
**Phase**: Check
**Date**: 2026-03-06
**Analyzer**: Manual (Design doc vs Implementation code)

---

## Match Rate Summary

| Category | Implemented | Total | Rate |
|----------|-------------|-------|------|
| Architecture & Files | 4 | 5 | 80% |
| Hook Contracts | 7 | 8 | 88% |
| Compression Strategies | 2 | 4 | 50% |
| Budget Tier System | 0 | 4 | 0% |
| Edge Case Handling | 3 | 6 | 50% |
| **TOTAL** | **16** | **27** | **59%** |

**Overall Match Rate: 59%** — Iterate required (threshold: 90%)

---

## Implemented (16/27) ✅

1. `mcp-pre-tool.sh` — cache lookup hook exists and functional
2. `mcp-post-tool.sh` — compression + cache save hook exists and functional
3. `mcp-compressor.json` — rules config with version, settings, rules sections
4. `settings.json` — hook registration with `mcp__*` matcher
5. stdin JSON parsing (tool_name, tool_input, tool_response)
6. `mcp__*` tool filter in both hooks
7. MIN_LINES=20 threshold — small responses skipped
8. Cache key = `sha256(tool_name:sorted_input_json)[:16]` — consistent between pre/post
9. Full response saved to cache file per call
10. `index.json` written by post-tool with LRU eviction (max 50)
11. Compression header with cache path and line counts
12. `truncate` strategy (keep_first + keep_last + omission marker)
13. `head` strategy (keep first N lines)
14. Cache directory auto-created if missing
15. JSON parse error fallback to default rule
16. Tool name not in rules → `default` rule applied

---

## Gaps (11/27) ❌

### GAP-01: `snippet` strategy not implemented [HIGH]
**Design**: snippet strategy keeps top-N match blocks with context_lines around each match.
**Impact**: 5 rules in config specify `strategy: "snippet"` (search_for_pattern, find_symbol, context-mode search). These all fall through to `else` branch → exit 0 → no compression.
**Fix**: Implement snippet strategy in post-tool.sh using awk/python3 to extract match blocks.

### GAP-02: `tail` strategy not implemented [LOW]
**Design**: tail keeps last N lines only.
**Impact**: No rule currently uses tail; future rules can't use it.
**Fix**: Add `elif [ "$STRATEGY" = "tail" ]` branch.

### GAP-03: Budget tier system not implemented [MEDIUM]
**Design**: Track cumulative context usage per session via `budget.json`. Apply multipliers (1.0/0.5/0.25) to max_lines based on remaining budget.
**Impact**: Compression aggressiveness doesn't adapt as context fills up.
**Fix**: Implement budget tracking in post-tool; read/write budget.json; apply multiplier to KEEP_FIRST/KEEP_LAST.

### GAP-04: `budget.json` file not created [MEDIUM]
**Design**: File structure includes `{session_id}/budget.json`.
**Impact**: Dependency of GAP-03.
**Fix**: Create budget.json on first PostToolUse call.

### GAP-05: `set -euo pipefail` breaks "silent fail" contract [MEDIUM]
**Design**: "Hook script fails → Silent fail — pass through original response unchanged."
**Actual**: Both hooks use `set -euo pipefail`. Any unhandled error exits non-zero and may surface error output rather than silently passing through.
**Fix**: Wrap main logic in function with `|| true` trap, or use `set -uo pipefail` without `-e`.

### GAP-06: Cache file extension mismatch [LOW]
**Design**: Cache files are `{hash16}.json` with structured JSON content.
**Actual**: Cache files are `{hash16}.txt` containing raw text only (no JSON wrapper with metadata fields key/tool/turn/lineCount/fullPath/fullContent).
**Impact**: Pre-tool reads from `index.json` which points to `.txt` files — functionally works, but violates design contract.
**Fix**: Either change design to use .txt (simpler) or wrap content in JSON per design schema.

### GAP-07: Binary/non-text response not detected [LOW]
**Design**: "Binary/non-text response → Skip compression (detect via `file` command)."
**Fix**: Add `file` command check before compression attempt.

### GAP-08: `.omc/ not writeable` not handled [LOW]
**Design**: "`.omc/` not writeable → Disable caching, compression-only mode."
**Fix**: Wrap mkdir/write in check; fall through to compression-only if write fails.

### GAP-09: `lru` field missing from index entries [LOW]
**Design index schema**: entries have `{ key, tool, turn, lru }` field.
**Actual**: index entries have `{ key, tool, turn, file, line_count, timestamp }` — no `lru` counter.
**Impact**: LRU eviction uses `turn` instead of a dedicated access counter. This means oldest-by-creation is evicted, not least-recently-accessed.
**Fix**: Add `lru` field, increment on each access in pre-tool.

### GAP-10: Settings.json uses absolute path for hook command [MEDIUM]
**Design**: `"command": "bash .claude/hooks/mcp-pre-tool.sh"` (relative)
**Actual**: `"command": "bash /Users/kimhawk/.config/opencode/skill/.claude/hooks/mcp-pre-tool.sh"` (absolute)
**Impact**: Hook breaks if repo is moved or used on a different machine.
**Fix**: Use relative path or `$PWD`-based path in settings.json.

### GAP-11: Fundamental hook limitation not documented [CRITICAL/DESIGN]
**Design assumption**: PostToolUse hook "replaces CLAUDE_TOOL_OUTPUT" with compressed version.
**Reality**: Claude Code PostToolUse hooks inject `<system-reminder>` additional context — they do NOT replace or suppress the raw tool output already in context. The raw response still enters the context window; the hook only adds a compressed summary afterward.
**Impact**: True context volume reduction only occurs on cache hits (PreToolUse blocks re-calling), not on first calls. First-call compression is a cognitive aid only (summary + cache path), not a token saver.
**Fix**: Document this clearly in SKILL.md / README. For true first-call compression, would need an MCP proxy server (not hooks).

---

## Priority Fix Plan for Iterate

| Gap | Priority | Effort | Fix |
|-----|----------|--------|-----|
| GAP-01: snippet strategy | HIGH | Medium | Add awk-based snippet extraction |
| GAP-05: silent fail | MEDIUM | Low | Wrap logic in main() with trap |
| GAP-03+04: budget tier | MEDIUM | Medium | Add budget.json tracking + multiplier |
| GAP-10: absolute path | MEDIUM | Trivial | Change to relative path |
| GAP-02: tail strategy | LOW | Trivial | Add elif branch |
| GAP-06: .txt vs .json | LOW | Low | Align to .txt (simpler) in design |
| GAP-09: lru field | LOW | Low | Add lru counter to index |
| GAP-07,08: edge cases | LOW | Low | Add guards |
| GAP-11: design flaw | DESIGN | N/A | Document limitation, update design |

**Target after iterate**: Fix GAP-01, GAP-05, GAP-10, GAP-02, GAP-06, GAP-09 → estimated 83%
**Full fix (all gaps)**: GAP-03+04, GAP-07+08 → estimated 93%

---

## Conclusion

Implementation covers core functionality (compression + caching for truncate/head strategies)
but is missing the snippet strategy (affects all search tool responses — the most impactful
use case), lacks budget-adaptive compression, and has a fundamental design assumption mismatch
regarding how PostToolUse hooks actually work in Claude Code.

Recommend two iteration rounds:
1. **Iterate 1**: GAP-01, 05, 10, 02, 06, 09 (code fixes) → ~83%
2. **Iterate 2**: GAP-03/04, 07, 08 (budget system + edge cases) → ~93%
