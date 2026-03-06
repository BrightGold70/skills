# Plan: HPW Improvements — Batch 2 (Proposals #3, 4, 6–10)

**Feature:** `hpw-improvements-batch2`
**Phase:** Plan
**Created:** 2026-03-04
**Status:** 📋 Planning

---

## 1. Overview

This plan covers the second batch of improvements to the `hematology-paper-writer` skill,
building on Batch 1 (journal-specs additions, SKILL.md statistical-skill fix). These
proposals range from documentation fixes to major new integrations.

---

## 2. Proposals in Scope

| # | Title | Effort | Impact |
|---|-------|--------|--------|
| 3 | Fix IMPLEMENTATION_STATUS.md accuracy | Small | Medium |
| 4 | Document missing tools in SKILL.md | Small | Medium |
| 6 | Add STROBE checklist support | Medium | Medium |
| 7 | Expand journal-specs.yaml with compliance fields | Medium | Medium |
| 8 | clinical-statistics-analyzer bridge in Phase 4 | Large | High |
| 9 | Blood Research full journal support (workflow) | Medium | High |
| 10 | NotebookLM cross-phase session persistence | Large | Medium |

---

## 3. Proposal Details & Requirements

### Proposal #3 — Fix IMPLEMENTATION_STATUS.md

**Problem:** IMPLEMENTATION_STATUS.md incorrectly marks `phase4_manuscript/`,
`phase4_6_concordance/`, and `phase5_quality/` as "EMPTY". COMPLETION_REPORT.md's
Phase Verification table confirms the actual implementation files live in `tools/`
(e.g., `tools/citation_concordance.py`, `tools/hematology_quality_analyzer.py`).

**Requirements:**
- Update status table to reflect actual file locations
- Add cross-reference: "Implemented in `tools/X.py`" for each delegated phase
- Correct Success Metrics table (currently claims 0 empty dirs, which is misleading)
- Fix `phase4_7_prose/` entry — `__init__.py` now exists (previously flagged as missing)

**Deliverable:** Updated `IMPLEMENTATION_STATUS.md`

---

### Proposal #4 — Document Missing Tools in SKILL.md

**Problem:** These tools exist and are functional but are not mentioned in SKILL.md's
workflow steps, commands, or integrated skills sections:
- `tools/systematic_review_workflow.py` — PRISMA-compliant systematic review
- `tools/source_discovery.py` — Literature search automation
- `tools/notebook_integrated_workflow.py` — NotebookLM-native workflow
- `tools/hematology_quality_analyzer.py` — Phase 5 quality analysis (392 lines)
- `tools/enhanced_editor.py` — Enhanced manuscript editor
- `tools/project_notebook_manager.py` — Project notebook management

**Requirements:**
- Add each tool to Part 7 (Commands) or appropriate Part in SKILL.md
- Include brief description, trigger conditions, and example invocation
- Link to existing phase workflow where appropriate (e.g., `hematology_quality_analyzer.py` → Phase 5)
- Do NOT duplicate existing documented tools

**Deliverable:** Updated `SKILL.md` (Part 7 Commands section + cross-references)

---

### Proposal #6 — Add STROBE Checklist Support

**Problem:** SKILL.md Part 11 (QA) lists PRISMA, CONSORT, CARE but omits STROBE
(Strengthening the Reporting of Observational Studies in Epidemiology). Retrospective
cohort studies and case-control analyses are extremely common in hematology (e.g.,
AML outcome analyses, HCT registry studies).

**Requirements:**
- Add STROBE 2007 checklist items to `tools/quality_analyzer.py` or create
  `tools/strobe_checker.py`
- Items required: Title/Abstract (1), Background (2), Objectives (3), Study design (4),
  Setting (5), Participants (6), Variables (7), Data sources (8), Bias (9),
  Study size (10), Quantitative variables (11), Statistical methods (12),
  Results sections (13-17), Discussion (18-21), Other info (22)
- Add STROBE to SKILL.md Part 11 QA workflow with trigger: "observational study",
  "retrospective", "cohort", "case-control", "registry"
- Update `journal-specs.yaml` compliance_checklist to include `strobe_if_observational`
- Add STROBE to Haematologica spec (already noted in reporting_guidelines)

**Deliverable:**
- `tools/strobe_checker.py` (new) OR STROBE section added to `quality_analyzer.py`
- Updated `SKILL.md` Part 11
- Updated `journal-specs.yaml`

---

### Proposal #7 — Expand journal-specs.yaml with Compliance Fields

**Problem:** Current YAML has basic formatting fields but lacks:
- Reporting guideline requirements per journal (CONSORT, PRISMA, STROBE, CARE)
- Distinction between original article vs review article word limits
- Supplementary data policy
- Figure/table count limits per article type
- Open access / APC info

**Requirements:**
- Add `reporting_guidelines` block to each journal entry:
  ```yaml
  reporting_guidelines:
    clinical_trials: "CONSORT"
    observational: "STROBE"
    systematic_reviews: "PRISMA"
    case_reports: "CARE"
  ```
- Add `article_types` sub-blocks (original vs review) where they differ
- Add `supplementary_policy` field
- Add `open_access` and `apc` fields
- Keep backward-compatible with existing `journal_loader.py`
- Apply to all 7 journals (4 existing + 3 new from Batch 1)

**Deliverable:** Updated `journal-specs.yaml` (all 7 journals enriched)

---

### Proposal #8 — clinical-statistics-analyzer Bridge in Phase 4

**Problem:** HPW Phase 4 (manuscript drafting) has no workflow for importing statistical
outputs from the `clinical-statistics-analyzer` (CSA) sibling skill. CSA produces:
- `.docx` tables (Table 1, efficacy tables, safety tables)
- `.eps` figures (KM curves, forest plots, waterfall plots, swimmer plots)

These outputs need to be referenced and integrated into the manuscript body,
but there is no documented handoff protocol.

**Requirements:**
- Add "Statistical Integration" step to Phase 4 workflow in SKILL.md:
  - Step: Receive CSA output directory, enumerate produced files
  - Step: Map each file to manuscript section (e.g., `survival.eps` → Results §3.2)
  - Step: Generate figure legends using CSA R script names as anchors
  - Step: Insert formatted table references into manuscript body
- Add `tools/csa_bridge.py`:
  - `scan_csa_outputs(csa_output_dir)` → list of tables + figures with metadata
  - `map_to_sections(outputs, manuscript_outline)` → section mapping
  - `generate_figure_legends(outputs)` → draft legends for each `.eps`
  - `generate_table_titles(outputs)` → draft titles for each `.docx` table
- Document the bridge in SKILL.md Part 19 Recipe 2 (Clinical Trial) — already
  references CSA but has no concrete handoff step
- Add to Recipe 2: "Pass `CSA_OUTPUT_DIR` to HPW Phase 4 statistical integration step"

**Deliverable:**
- `tools/csa_bridge.py` (new, ~200 lines)
- Updated `SKILL.md` (Phase 4 workflow + Recipe 2)
- Updated `IMPLEMENTATION_STATUS.md`

---

### Proposal #9 — Blood Research Full Journal Support

**Problem:** Blood Research (`journal-specs.yaml` entry added in Batch 1) lacks:
- SKILL.md workflow guidance specific to Blood Research
- Compliance checklist (journal uses Springer Nature submission system)
- Korean Society of Hematology-specific considerations
- Actual usage was confirmed (manuscript `.docx` files exist in root)

**Requirements:**
- Add Blood Research to SKILL.md Part 3 (Supported Journals) narrative section
  with: scope, typical article types, key requirements, submission notes
- Add Blood Research to SKILL.md Part 8 (Venue Selection) decision table
- Add Blood Research-specific quality checks to `quality_analyzer.py`:
  - Structured abstract check (Purpose/Methods/Results/Conclusion)
  - Word count ≤3,500 (original) / ≤5,000 (review)
  - Reference limit: ≤30 (original) / ≤150 (review)
  - DOI required in reference list
- Update `journal_loader.py` to expose the new YAML fields added in Batch 1

**Deliverable:**
- Updated `SKILL.md` (Parts 3 and 8)
- Updated `tools/quality_analyzer.py` (Blood Research checks)
- Verified `journal_loader.py` compatibility with new YAML schema

---

### Proposal #10 — NotebookLM Cross-Phase Session Persistence

**Problem:** Each HPW phase independently invokes NotebookLM via `notebooklm_integration.py`.
There is no session_id persistence, meaning:
- Same sources re-uploaded per phase
- No conversational context carried across phases
- Redundant queries consuming daily quota (50 queries/day free tier)

**Requirements:**
- Add session management to `tools/notebooklm_integration.py`:
  - `start_manuscript_session(project_name, notebook_id)` → returns `session_id`
  - `save_session(project_name, session_id)` → persist to `project_notebooks/{project}.session.json`
  - `load_session(project_name)` → retrieve saved `session_id`
  - `query_with_session(question, session_id)` → use existing session
- Update `phases/phase_manager.py` to:
  - Store `notebooklm_session_id` in `ManuscriptMetadata`
  - Pass session_id to each phase that calls NotebookLM
- Update all phase modules that call NotebookLM to use `load_session()` first
- Add session expiry handling (sessions expire after ~24h inactivity)
- Add to SKILL.md Part 16 (NotebookLM): "Session persistence — one session per manuscript project"

**Phases that invoke NotebookLM (to update):**
- Phase 1 (topic discovery)
- Phase 3 (journal strategy context)
- Phase 4 (drafting context)
- Phase 4.5 (update context)
- Phase 4.7 (prose polish context)

**Deliverable:**
- Updated `tools/notebooklm_integration.py` (session management methods)
- Updated `phases/phase_manager.py` (session_id in metadata)
- Updated phase modules (5 files)
- Updated `SKILL.md` Part 16
- Session file schema: `project_notebooks/{project}.session.json`

---

## 4. Implementation Order

Recommended sequencing based on dependencies:

```
Week 1 (Documentation, no code risk):
  #3 → IMPLEMENTATION_STATUS.md fix
  #4 → SKILL.md missing tools documentation

Week 2 (Data / config):
  #7 → journal-specs.yaml compliance fields (depends on Batch 1 journals)
  #9 → Blood Research SKILL.md + quality_analyzer (depends on #7)

Week 3 (New features):
  #6 → STROBE checker (standalone, no dependencies)
  #8 → CSA bridge (standalone new tool)

Week 4 (Complex integration):
  #10 → NotebookLM session persistence (touches 7+ files)
```

---

## 5. Risk Assessment

| Proposal | Risk | Mitigation |
|----------|------|------------|
| #3 | Low — doc only | Review COMPLETION_REPORT carefully before editing |
| #4 | Low — doc only | Read each tool before documenting |
| #6 | Medium — new checker logic | Test against real observational manuscript |
| #7 | Low — YAML only | Verify journal_loader.py compatibility after |
| #8 | Medium — new tool, real integration | Keep csa_bridge.py stateless, purely additive |
| #9 | Low-Medium — quality_analyzer changes | Add Blood Research as new branch, don't touch existing |
| #10 | High — touches 7+ files, external API | Add session_id as optional param (backward compat) |

---

## 6. Success Criteria

| Proposal | Done When |
|----------|-----------|
| #3 | IMPLEMENTATION_STATUS.md accurately reflects actual file locations |
| #4 | All 6 undocumented tools appear in SKILL.md with usage guidance |
| #6 | STROBE checker runs on observational manuscript and produces itemized report |
| #7 | All 7 journals have `reporting_guidelines` + `article_types` blocks in YAML |
| #8 | `csa_bridge.py` can scan a CSA output dir and return section-mapped file list |
| #9 | Blood Research manuscript passes quality_analyzer with journal-specific checks |
| #10 | Single session_id persists across ≥3 consecutive phase invocations |
