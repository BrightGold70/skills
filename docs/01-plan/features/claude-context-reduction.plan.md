# Plan: Claude Context Reduction

**Feature**: `claude-context-reduction`
**Phase**: Plan
**Created**: 2026-03-06
**Scope**: Cross-project (applies to all Claude Code sessions in this workspace)

---

## Overview

Three-phase initiative to reduce the context window burden in Claude Code sessions caused by
eagerly-loaded framework files, repeated skill manifests, and redundant tool-call guidance.
Implementation order is B → A → C, from highest-impact/lowest-risk to lower-impact/runtime.

---

## Problem Statement

Each Claude Code session in this workspace loads ~4,000–6,000 lines of baseline context:

| Source | Lines | Frequency |
|--------|-------|-----------|
| CLAUDE.md @imports (20 framework files) | ~2,000 | Every session |
| bkit session startup block | ~200 | Every session |
| PDCA skill manifest per invocation | ~300 × N calls | Per `/pdca` call |
| Hook messages (Read/Edit/Write/Bash) | ~4 × M tool calls | Per tool call |
| Git status (100+ untracked files) | ~120 | Every session |
| MEMORY.md (approaching 200-line truncation) | 116+ | Every session |

A 5-call PDCA session (plan → design → do → analyze → report) adds ~1,500 lines of repeated
skill content alone. Combined with always-loaded framework imports, the context window is
heavily consumed before any task-specific content arrives.

---

## Goals

### Phase B: CLAUDE.md Lazy Import Gate (Immediate, High Impact)

Convert 20 eager `@FILE` imports in CLAUDE.md into conditional/on-demand references.
Only a minimal core set (~3 files) loads always; domain-specific files load only when
a relevant task keyword is detected.

**Acceptance Criteria**:
- CLAUDE.md baseline loads ≤ 3 framework files unconditionally
- Domain gate table maps task keywords → file groups
- All existing behavioral rules remain reachable via gate triggers
- Session startup context reduced by ≥ 50% (from ~2,000 to ≤ 1,000 lines)
- No regression: hematology, statistics, UI, and git workflow rules still apply when triggered

### Phase A: PDCA Micro-Skill Stubs (Medium-term, High Savings per Call)

Replace the monolithic bkit:pdca skill (300 lines) with 7 per-action stub files (15–20 lines
each). Only the relevant stub is injected per `/pdca` call. The full manifest is only loaded
on explicit `--help` or first-session initialization.

**Acceptance Criteria**:
- 7 stub files created: `pdca-plan.md`, `pdca-design.md`, `pdca-do.md`, `pdca-analyze.md`,
  `pdca-iterate.md`, `pdca-report.md`, `pdca-archive.md`
- Each stub: action steps only + output path + next-phase hint (≤ 20 lines)
- Local override mechanism prevents bkit marketplace version from expanding
- Per-call context savings: ~280 lines per invocation
- 5-call session savings: ~1,400 lines vs baseline

### Phase C: Session Notepad as Context Deduplication Layer (Runtime Discipline)

Use `notepad_write_working` (oh-my-claudecode) to track which files and skill sections have
been loaded in the current session. Before reading a file or loading reference content, check
the notepad. Skip if already loaded; use the cached summary from notepad instead.

**Acceptance Criteria**:
- Session notepad initialized at start with `[CONTEXT LOADED]` header
- Each Read/skill-load records: `{timestamp} | {file_or_skill} | {summary_line}`
- Before loading any reference file: check notepad for prior load; use summary if found
- MEMORY.md topic files split so no single file exceeds 80 lines
- Estimated context deduplication: 20–40% reduction in re-read content per session

---

## Non-Goals

- Do NOT modify bkit marketplace source files directly (local overrides only)
- Do NOT remove any behavioral rules — only gate their loading
- Do NOT require user to manually annotate tasks with domain tags
- Do NOT implement LLM-based context compression (already evaluated in mcp-context-compressor)

---

## Architecture Concept

### Phase B: Gate Table in CLAUDE.md

```markdown
# Core (always loaded)
@PRINCIPLES.md
@RULES.md

# Domain Gates — load when task contains these keywords:
# hematology, manuscript, HPW, blood, journal → @MCP_Serena.md @MODE_Agents.md
# statistics, CSA, AML, clinical → @MCP_Sequential.md
# UI, frontend, Streamlit, component → @MCP_Magic.md @MODE_Business_Panel.md
# git, commit, PR, branch → (no extra files needed; RULES.md covers git)
# research, pubmed, search → @MCP_Tavily.md @MODE_DeepResearch.md
```

### Phase A: Local Skill Override Structure

```
~/.claude/skills/pdca/
  pdca-plan.md      (18 lines)
  pdca-design.md    (16 lines)
  pdca-do.md        (15 lines)
  pdca-analyze.md   (20 lines)
  pdca-iterate.md   (18 lines)
  pdca-report.md    (15 lines)
  pdca-archive.md   (17 lines)
```

Register in Claude Code settings as local skill overrides that shadow the bkit marketplace
versions. Each stub references the full manifest path for fallback: `See bkit:pdca --help`.

### Phase C: Notepad Protocol

```
Session start:
  notepad_write_priority: "[SESSION] Context tracking initialized: {date}"

Before any Read:
  notepad_stats → check if file is already in notepad
  If found: use notepad summary, skip Read
  If not: Read → notepad_write_working: "{file} | {key_facts}"

Before any /pdca call:
  notepad_stats → check for "PDCA manifest loaded"
  If found: use stub directly
  If not: allow full load → notepad_write_working: "PDCA manifest | loaded turn N"
```

---

## Files to Create / Modify

| File | Action | Phase |
|------|--------|-------|
| `~/.claude/CLAUDE.md` | Modify — gate @imports | B |
| `~/.claude/skills/pdca/pdca-{action}.md` × 7 | Create — action stubs | A |
| `~/.claude/settings.json` | Modify — register local skill overrides | A |
| MEMORY.md topic files | Split — no file > 80 lines | C |
| Session notepad protocol | Runtime habit — no file change | C |

---

## Key Risks

| Risk | Mitigation |
|------|-----------|
| Gate keywords miss task domain → rules not loaded | Add broad fallback: "if unsure, load all" escape |
| Local PDCA stubs shadow bkit fully → lose functionality | Stubs include link to full manifest; `--help` loads all |
| Notepad check adds latency per tool call | Notepad is fast; only check before expensive reads |
| CLAUDE.md gate not interpreted correctly | Test with representative tasks before committing |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Baseline context at session start | ~2,200 lines | ≤ 1,000 lines |
| Context per `/pdca` call | ~300 lines | ≤ 20 lines |
| Re-read rate (same file multiple times) | ~40% of reads | ≤ 10% |
| MEMORY.md truncation risk | High (116/200 lines) | None (split into topic files) |

---

## Implementation Order

1. **Phase B** — Edit CLAUDE.md: move 17 @imports behind domain gate table (1 session)
2. **Phase A** — Create 7 PDCA stub files + settings.json local skill registration (1 session)
3. **Phase C** — Split MEMORY.md topic files + establish notepad protocol (ongoing habit)
