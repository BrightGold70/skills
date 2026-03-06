# Design: Claude Context Reduction

**Feature**: `claude-context-reduction`
**Phase**: Design
**Created**: 2026-03-06
**Scope**: Cross-project (`~/.claude/CLAUDE.md`, `~/.claude/pdca-stubs/`, session notepad protocol)

---

## Overview

Three phases implemented in order B → A → C. This document specifies exact file changes,
gate keyword mappings, stub file content, and the notepad deduplication protocol.

---

## Phase B: CLAUDE.md Lazy Import Gate

### Current State

`~/.claude/CLAUDE.md` contains 21 `@FILE` imports that load unconditionally on every session:

```
@BUSINESS_PANEL_EXAMPLES.md   (long)
@BUSINESS_SYMBOLS.md          (medium)
@FLAGS.md                     (medium)
@PRINCIPLES.md                (short)
@RESEARCH_CONFIG.md           (very long)
@RULES.md                     (long)
@MODE_Agents.md               (medium)
@MODE_Brainstorming.md        (short)
@MODE_Business_Panel.md       (long)
@MODE_DeepResearch.md         (short)
@MODE_Introspection.md        (short)
@MODE_Orchestration.md        (medium)
@MODE_Task_Management.md      (medium)
@MODE_Token_Efficiency.md     (medium)
@MCP_Context7.md              (short)
@MCP_Magic.md                 (short)
@MCP_Morphllm.md              (short)
@MCP_Playwright.md            (short)
@MCP_Sequential.md            (short)
@MCP_Serena.md                (short)
@MCP_Tavily.md                (long)
```

Estimated total: ~2,000 lines added to every session context.

### Target State

Keep 3 `@FILE` imports unconditionally. Replace 18 with a gate table instruction.

**Always-loaded files** (3):
- `@FLAGS.md` — mode flag triggers (needed for all tasks)
- `@PRINCIPLES.md` — core engineering values (always relevant)
- `@RULES.md` — safety, git, workflow rules (always relevant)

**Gate table** — read these files with `Read` only when the task matches keywords:

| Domain | Keywords (any match) | Files to Read |
|--------|---------------------|---------------|
| hematology | hematology, manuscript, HPW, blood, journal, paper, AML, CML, MDS, HCT | `~/.claude/MCP_Serena.md`, `~/.claude/MODE_Agents.md` |
| business | business, strategy, Porter, Collins, Drucker, Taleb, panel, market | `~/.claude/BUSINESS_PANEL_EXAMPLES.md`, `~/.claude/BUSINESS_SYMBOLS.md`, `~/.claude/MODE_Business_Panel.md` |
| research | research, pubmed, search, Tavily, web, investigate, current events | `~/.claude/RESEARCH_CONFIG.md`, `~/.claude/MCP_Tavily.md`, `~/.claude/MODE_DeepResearch.md` |
| UI/frontend | UI, frontend, component, React, Vue, Angular, design system, button, form | `~/.claude/MCP_Magic.md` |
| browser | browser, E2E, Playwright, visual, screenshot, accessibility | `~/.claude/MCP_Playwright.md` |
| bulk-edit | bulk edit, transform, pattern, Morphllm, refactor all, rename across | `~/.claude/MCP_Morphllm.md` |
| docs/library | docs, library, framework, Context7, official docs, import, require | `~/.claude/MCP_Context7.md` |
| statistics | statistics, clinical, CSA, analysis, sequential thinking, multi-step | `~/.claude/MCP_Sequential.md` |
| brainstorm | brainstorm, explore, discover, maybe, thinking about, not sure | `~/.claude/MODE_Brainstorming.md` |
| orchestrate | orchestrate, parallel, delegate, concurrency, multi-agent | `~/.claude/MODE_Orchestration.md` |
| task-manage | task, todo, manage, coordinate, phase, milestone, session resume | `~/.claude/MODE_Task_Management.md` |
| token-efficiency | token, efficient, compress, ultracompressed, context tight | `~/.claude/MODE_Token_Efficiency.md` |
| introspect | introspect, reflect, analyze reasoning, why did, meta | `~/.claude/MODE_Introspection.md` |

**Fallback rule**: If task domain is ambiguous or spans ≥3 domains, load all 18 gated files.
Instruction in CLAUDE.md: "When uncertain, err toward loading; prefer false positives over misses."

### CLAUDE.md Diff

**Remove** (from the Framework Components section):
```markdown
@BUSINESS_PANEL_EXAMPLES.md
@BUSINESS_SYMBOLS.md
@RESEARCH_CONFIG.md
@MODE_Agents.md
@MODE_Brainstorming.md
@MODE_Business_Panel.md
@MODE_DeepResearch.md
@MODE_Introspection.md
@MODE_Orchestration.md
@MODE_Task_Management.md
@MODE_Token_Efficiency.md
@MCP_Context7.md
@MCP_Magic.md
@MCP_Morphllm.md
@MCP_Playwright.md
@MCP_Sequential.md
@MCP_Serena.md
@MCP_Tavily.md
```

**Add** (replacing the removed imports):
```markdown
# Domain Gate — load with Read only when task matches these keywords
# (See gate table below — always load FLAGS.md, PRINCIPLES.md, RULES.md above)
# When uncertain about domain, load all files in the relevant row(s).
# Fallback: if task spans 3+ domains, load all gated files.
[gate table as markdown table, embedded in CLAUDE.md]
```

### Expected Savings

- 18 files removed from unconditional loading → ~1,500 lines saved per session baseline
- Typical task loads 1–2 domain groups → ~4–8 files loaded on-demand vs 21 always

---

## Phase A: PDCA Micro-Stub Files

### Problem

The bkit:pdca skill manifest is ~300 lines injected via system-reminder on every `/pdca` invocation.
A 5-call session (plan, design, do, analyze, report) injects ~1,500 lines of repeated content.

### Solution

Create 7 lightweight stub files at `~/.claude/pdca-stubs/`. Add a CLAUDE.md instruction:
> "For routine `/pdca [action]` commands, read `~/.claude/pdca-stubs/pdca-{action}.md` and follow
> it directly. Only invoke the full `bkit:pdca` skill when: (a) the user asks for `--help` or team
> mode, (b) the stub content is insufficient for the task, or (c) first call of a new session."

### Stub File Specifications

Each stub: ≤20 lines. Format: numbered steps + Output path + Next command.

**`~/.claude/pdca-stubs/pdca-plan.md`** (≤18 lines):
```markdown
## PDCA: plan [feature]

1. Check `docs/01-plan/features/{feature}.plan.md`
2. If absent: create from template
   - Sections: Overview, Problem, Goals (with Acceptance Criteria), Non-Goals,
     Architecture Concept, Files to Create/Modify, Key Risks, Success Metrics
3. Update `docs/.pdca-status.json`: phase="plan", startedAt=now
4. Show plan summary to user

Output: `docs/01-plan/features/{feature}.plan.md`
Next: `/pdca design {feature}`
Full guide: invoke `bkit:pdca` skill for templates and team mode.
```

**`~/.claude/pdca-stubs/pdca-design.md`** (≤18 lines):
```markdown
## PDCA: design [feature]

Prereq: Plan doc must exist at `docs/01-plan/features/{feature}.plan.md`

1. Read Plan doc
2. Create `docs/02-design/features/{feature}.design.md`
   - Sections: Architecture, Component Specs, Data Flow, File Changes table,
     API/Interface contracts, Acceptance Criteria mapping
3. Update `docs/.pdca-status.json`: phase="design"
4. Show design summary

Output: `docs/02-design/features/{feature}.design.md`
Next: Implement code, then `/pdca analyze {feature}`
```

**`~/.claude/pdca-stubs/pdca-do.md`** (≤16 lines):
```markdown
## PDCA: do [feature]

Prereq: Design doc must exist at `docs/02-design/features/{feature}.design.md`

1. Read Design doc — extract implementation order and file list
2. Present implementation checklist to user:
   - Files to create/modify (in dependency order)
   - Key interfaces and contracts
   - Test file locations
3. Update `docs/.pdca-status.json`: phase="do"

Output: Implementation guide (no files created by this command)
Next: Write the code, then `/pdca analyze {feature}`
```

**`~/.claude/pdca-stubs/pdca-analyze.md`** (≤20 lines):
```markdown
## PDCA: analyze [feature]

Prereq: Implementation code must exist.

1. Read Design doc at `docs/02-design/features/{feature}.design.md`
2. Read key implementation files listed in Design
3. Build checklist: each Design item → Implemented? (yes/partial/no)
4. Calculate Match Rate = (yes + 0.5*partial) / total * 100
5. If Match Rate < 90%: list gaps with recommended fixes
6. Write `docs/03-analysis/{feature}.analysis.md`
7. Update `docs/.pdca-status.json`: phase="check", matchRate=N

Output: `docs/03-analysis/{feature}.analysis.md`
Next: if <90% → `/pdca iterate {feature}`; if >=90% → `/pdca report {feature}`
```

**`~/.claude/pdca-stubs/pdca-iterate.md`** (≤20 lines):
```markdown
## PDCA: iterate [feature]

Prereq: Analysis doc with Match Rate < 90%.

1. Read `docs/03-analysis/{feature}.analysis.md` — extract Gap list
2. Fix each gap in priority order (Critical > Major > Minor)
3. Re-run analysis: re-read Design + implementation, recalculate Match Rate
4. Update analysis doc with new Match Rate
5. Update `docs/.pdca-status.json`: phase="act", iterationCount+=1
6. Stop when Match Rate >= 90% or iteration count = 5

Output: Updated implementation files + updated analysis doc
Next: if >=90% → `/pdca report {feature}`; else repeat
```

**`~/.claude/pdca-stubs/pdca-report.md`** (≤18 lines):
```markdown
## PDCA: report [feature]

Prereq: Match Rate >= 90% in analysis doc.

1. Read Plan, Design, Analysis docs
2. Write `docs/04-report/{feature}.report.md`
   - Sections: Executive Summary, Implementation Summary (table),
     Plan Goals vs Delivery, Acceptance Criteria Verification,
     PDCA Cycle Summary, Deferred Items, Success Metrics
3. Update `docs/.pdca-status.json`: phase="completed"

Output: `docs/04-report/{feature}.report.md`
Next: `/pdca archive {feature}`
```

**`~/.claude/pdca-stubs/pdca-archive.md`** (≤18 lines):
```markdown
## PDCA: archive [feature] [--summary]

Prereq: Report doc must exist (phase="completed").

1. Create `docs/archive/YYYY-MM/{feature}/`
2. Move plan, design, analysis, report docs into archive folder
3. Update `docs/archive/YYYY-MM/_INDEX.md`
4. Update `docs/.pdca-status.json`:
   - Default: delete feature entry
   - With --summary: replace with {phase, matchRate, iterationCount, archivedAt, archivedTo}

Output: `docs/archive/YYYY-MM/{feature}/`
Note: Archive is irreversible. Documents deleted from original locations.
```

### Expected Savings

- Each `/pdca` call: ~280 lines saved (300 manifest - 20 stub)
- 5-call session: ~1,400 lines saved

---

## Phase C: Notepad Deduplication Protocol

### MEMORY.md Split

Current `MEMORY.md`: ~200 lines (approaching truncation limit).

**Action**: Split into topic files, each ≤80 lines. MEMORY.md becomes an index only (≤60 lines).

| Topic File | Content | Est. Lines |
|------------|---------|------------|
| `memory/project-overview.md` | CSA architecture, R scripts, Dropbox paths | 40 |
| `memory/pdca-hpw.md` | HPW PDCA history (protocol-extraction, skills integration, classification-validator) | 70 |
| `memory/pdca-csa.md` | CSA PDCA history (CRF pipeline, E2E improvements, scientific skills) | 50 |
| `memory/hpw-tools.md` | HPW tool inventory (open-notebook, notebooklm, statistical_bridge, skills/) | 60 |
| `memory/archived-features.md` | All archived feature summaries | 60 |

MEMORY.md index: title + one-line summary + file link per topic (≤60 lines total).

### Notepad Session Protocol

Tool: `mcp__plugin_oh-my-claudecode_t__notepad_write_working`

**Session start** (write priority):
```
notepad_write_priority: "[SESSION] {YYYY-MM-DD} Context tracking active"
```

**Before any Read**:
1. `notepad_stats` → check if file path appears in notepad
2. If found: use the summary line from notepad, skip Read
3. If not found: Read → `notepad_write_working: "{file_path} | {one-line summary}"`

**Before any skill invocation** (bkit:pdca or similar):
1. Check notepad for "PDCA manifest loaded"
2. If found: use stub directly (skip full invocation)
3. If not: invoke skill → `notepad_write_working: "bkit:pdca manifest | loaded at turn {N}"`

**Before loading MEMORY.md topic file**:
1. Check notepad for that topic file path
2. If found: use cached summary, skip Read

### MEMORY.md Topic File Size Rule

- Each topic file: hard limit 80 lines
- If a topic file exceeds 80 lines: split into two files, update MEMORY.md index
- MEMORY.md index: hard limit 60 lines (well below 200-line truncation)

---

## Files to Create / Modify

| File | Action | Phase | Est. Lines Changed |
|------|--------|-------|--------------------|
| `~/.claude/CLAUDE.md` | Modify — remove 18 @imports, add gate table | B | −18, +30 |
| `~/.claude/pdca-stubs/pdca-plan.md` | Create | A | 18 |
| `~/.claude/pdca-stubs/pdca-design.md` | Create | A | 18 |
| `~/.claude/pdca-stubs/pdca-do.md` | Create | A | 16 |
| `~/.claude/pdca-stubs/pdca-analyze.md` | Create | A | 20 |
| `~/.claude/pdca-stubs/pdca-iterate.md` | Create | A | 20 |
| `~/.claude/pdca-stubs/pdca-report.md` | Create | A | 18 |
| `~/.claude/pdca-stubs/pdca-archive.md` | Create | A | 18 |
| `~/.claude/CLAUDE.md` | Add stub-preference instruction | A | +8 |
| `~/.claude/projects/.../memory/MEMORY.md` | Replace with index-only content | C | −140, +40 |
| `~/.claude/projects/.../memory/pdca-hpw.md` | Create (split from MEMORY.md) | C | 70 |
| `~/.claude/projects/.../memory/pdca-csa.md` | Create (split from MEMORY.md) | C | 50 |
| `~/.claude/projects/.../memory/hpw-tools.md` | Create (split from MEMORY.md) | C | 60 |
| `~/.claude/projects/.../memory/archived-features.md` | Create (split from MEMORY.md) | C | 60 |

---

## Acceptance Criteria (Design-level)

| Criterion | Verification Method |
|-----------|---------------------|
| CLAUDE.md has exactly 3 @FILE imports remaining | `grep "^@" ~/.claude/CLAUDE.md | wc -l` = 3 |
| Gate table covers all 18 removed files | Each file appears in exactly one table row |
| Fallback rule present and unambiguous | Gate table section includes "if uncertain, load all" note |
| 7 stub files created, each ≤20 lines | `wc -l ~/.claude/pdca-stubs/*.md` |
| Each stub has Output path + Next command | Manual review |
| CLAUDE.md stub-preference instruction present | `grep -c "pdca-stubs" ~/.claude/CLAUDE.md` > 0 |
| MEMORY.md index ≤60 lines | `wc -l MEMORY.md` ≤60 |
| Each topic file ≤80 lines | `wc -l memory/*.md | sort -n` all ≤80 |
| Notepad protocol described in CLAUDE.md or session instructions | Present in gate/stub instruction block |

---

## Implementation Order

1. **Phase B** (highest impact, lowest risk):
   - Edit `~/.claude/CLAUDE.md`: remove 18 @imports, insert gate table
   - Test: start a new Claude Code session, confirm only FLAGS/PRINCIPLES/RULES load initially

2. **Phase A** (medium impact, medium effort):
   - Create `~/.claude/pdca-stubs/` directory
   - Write 7 stub files
   - Add stub-preference instruction to CLAUDE.md

3. **Phase C** (ongoing):
   - Split MEMORY.md into topic files
   - Establish notepad habit (no code change required)

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Gate misses domain → rules not available | Fallback: "if uncertain, load all" + broad keywords |
| Stub content insufficient for edge case | Stubs reference full bkit:pdca for fallback |
| CLAUDE.md edit breaks OMC/bkit instructions | Only touch Framework Components section; leave OMC block untouched |
| MEMORY.md split loses cross-references | Each topic file is self-contained; index has one-line summaries |
