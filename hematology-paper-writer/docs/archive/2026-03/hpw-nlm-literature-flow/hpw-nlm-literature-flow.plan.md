# Plan: hpw-nlm-literature-flow

## Overview

Redesign the HPW literature flow so that the project-specific NotebookLM (open-notebook) note
becomes the **single source of truth** for all manuscript drafting in phases 2-9.
Phase 1 creates or updates the project NLM note; `research_topic.json` is extended to store
the notebook reference and stays in sync at every article-selection event.

## Problem Statement

**Current gap**: Phase 1 creates a project NLM notebook and returns its `notebook_id`, but
never persists it to `research_topic.json`. As a result, phases 2-9 have no knowledge of the
project notebook and fall back to raw `literature_seed.json` (PubMed data) for all drafting —
bypassing the curated, AI-queryable NLM knowledge base entirely.

## Goals

1. `research_topic.json` stores the NLM notebook reference (`notebook_id`, `notebook_name`,
   `pmids_added`, `last_synced`) and is always kept in sync.
2. Phase 1 resolves the notebook via: existing `notebook_id` → name-pattern match → user prompt
   → create new. Only user-selected articles are added.
3. All phases 2-9 query the project NLM notebook with section-specific prompts before drafting.
4. NLM unavailability produces a visible warning (not silent fallback).
5. Users can manually add PMIDs to the project notebook from any phase ≥ 2 (UI + CLI).

## Non-Goals

- Replacing `literature_seed.json` entirely (kept as reference/backup)
- Changing the PubMed search logic in Phase 1
- Modifying journal-spec YAML or nomenclature checking

## Requirements

### FR-01: research_topic.json NLM Block
`research_topic.json` MUST include an `nlm` block:
```json
{
  "nlm": {
    "notebook_id": "uuid-or-null",
    "notebook_name": "HPW-{disease}-{intervention}-{year}",
    "pmids_added": ["38234567"],
    "last_synced": "2026-03-06T10:00:00"
  }
}
```
`save_project_topic()` and `load_project_topic()` must preserve this block.

### FR-02: Phase 1 Notebook Resolution
Resolution order on every Phase 1 run:
1. Load `research_topic.json` → check `nlm.notebook_id`
2. If present → verify notebook exists via GET `/api/notebooks/{id}`
   - If alive → reuse; skip to article-add step
   - If dead (404) → fall through to name search
3. Name search: `list_notebooks()` filtered by `"HPW-{disease}-{intervention}"` prefix
   - If match found → ask user via CLI/UI prompt: "Found note '{name}'. Use it? [y/N]"
   - If user confirms → adopt that `notebook_id`
   - If no match or user declines → create new notebook named `"HPW-{disease}-{intervention}-{year}"`
4. Add only `selected=True` articles (by PMID URL `https://pubmed.ncbi.nlm.nih.gov/{pmid}/`)
5. Write `nlm` block back to `research_topic.json`

### FR-03: NotebookLMIntegration Extensions
New methods on `NotebookLMIntegration`:
- `list_notebooks() -> list[dict]` — GET `/api/notebooks`
- `find_by_name(prefix: str) -> Optional[dict]` — filter by name prefix
- `add_source_pmid(notebook_id: str, pmid: str) -> bool` — add single PMID URL

### FR-04: tools/nlm_query.py — Phase-Specific Query Module
New module exposing:
```python
def query_for_phase(
    phase: str,               # e.g. "phase2", "phase3", "phase4_draft"
    topic: ResearchTopic,
    notebook_id: str,
    section: str = "",        # for phase4 per-section queries
    timeout: int = 10,
) -> str
```
Section-specific prompt templates per phase:

| Phase key | Prompt template |
|-----------|----------------|
| `phase2` | `"{disease} {intervention} clinical trial study designs, primary endpoints, eligibility criteria, and response definitions"` |
| `phase3` | `"Publication impact and novelty arguments for {disease} {intervention}: key findings, journal fit, knowledge gaps"` |
| `phase4_draft` | `"Key results, statistics, and comparisons for {section} in {disease} {intervention} studies"` |
| `phase4_5` | `"Latest updates, new trial data, and guideline changes for {disease} {intervention} since {year}"` |
| `phase4_7` | `"Core claims and supporting evidence most cited in {disease} {intervention} literature"` |
| `phase8` | `"Common reviewer critiques and methodological concerns in {disease} {intervention} manuscripts"` |
| `phase9` | `"Current consensus statements and practice guidelines for {disease} {intervention}"` |

Returns empty string and logs a warning if NLM is unavailable (does NOT silently fallback).

### FR-05: Phase Integration (2-9)
Each phase listed in FR-04 must call `query_for_phase()` at its main entry point and pass
the result as `nlm_context` into its drafting/analysis logic. If `nlm_context` is empty,
emit: `logger.warning("NLM unavailable for %s — proceeding without literature context", phase)`
and show a user-visible warning in the UI (yellow banner / CLI stderr message).

### FR-06: Manual PMID Adding (Phase ≥ 2)
- **CLI**: `hpw add-to-nlm --pmid <PMID> [--project-dir <dir>]`
  - Adds PMID URL to notebook; updates `research_topic.json.nlm.pmids_added` + `last_synced`
- **UI**: "Add PMID to NLM" input + button in sidebar, visible for all phases ≥ 2
  - Same update logic; shows success/error feedback inline

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-01 | `research_topic.json` written by Phase 1 contains `nlm.notebook_id` (non-null when NLM online) |
| AC-02 | Re-running Phase 1 with existing `notebook_id` reuses the notebook (no duplicate created) |
| AC-03 | Re-running Phase 1 with dead `notebook_id` triggers name search |
| AC-04 | Only `selected=True` articles appear in `nlm.pmids_added` |
| AC-05 | Phase 2 `StudyDesignManager` calls `query_for_phase("phase2", ...)` and uses result |
| AC-06 | Phase 3 `JournalStrategyManager` calls `query_for_phase("phase3", ...)` and uses result |
| AC-07 | Phase 4 `ResearchWorkflow` calls `query_for_phase("phase4_draft", ..., section=...)` per section |
| AC-08 | Phases 4.5, 4.7, 8, 9 each call their respective `query_for_phase()` variant |
| AC-09 | NLM offline → user-visible warning in UI (yellow banner) + `logger.warning(...)` |
| AC-10 | `hpw add-to-nlm --pmid 38234567` updates both notebook and `research_topic.json` |
| AC-11 | UI "Add PMID to NLM" button works in phases ≥ 2 |
| AC-12 | `NotebookLMIntegration.list_notebooks()` and `find_by_name()` implemented and tested |

## Files to Change

| File | Type | Change |
|------|------|--------|
| `tools/notebooklm_integration.py` | Modify | + `list_notebooks()`, `find_by_name()`, `add_source_pmid()` |
| `tools/nlm_query.py` | **New** | Phase-specific query module |
| `phases/phase1_topic/topic_development.py` | Modify | Notebook resolution logic; `nlm` block in `save/load_project_topic()` |
| `phases/phase2_research/study_design_manager.py` | Modify | `query_for_phase("phase2", ...)` at load |
| `phases/phase3_journal/journal_strategy_manager.py` | Modify | `query_for_phase("phase3", ...)` at load |
| `tools/draft_generator/research_workflow.py` | Modify | `query_for_phase("phase4_draft", ..., section=...)` per section |
| `phases/phase4_5_updating/manuscript_updater.py` | Modify | `query_for_phase("phase4_5", ...)` |
| `phases/phase4_7_prose/prose_verifier.py` | Modify | `query_for_phase("phase4_7", ...)` |
| `phases/phase8_peerreview/peer_review_manager.py` | Modify | `query_for_phase("phase8", ...)` |
| `phases/phase9_publication/publication_manager.py` | Modify | `query_for_phase("phase9", ...)` |
| `cli.py` | Modify | + `add-to-nlm` subcommand |
| `ui/components/action_panel.py` | Modify | "Add PMID to NLM" widget for phases ≥ 2 |

## Implementation Order

1. `tools/notebooklm_integration.py` — new methods (foundation)
2. `tools/nlm_query.py` — query module (foundation)
3. `phases/phase1_topic/topic_development.py` — notebook resolution + `nlm` block persistence
4. Phases 2, 3, 4, 4.5, 4.7, 8, 9 — integrate `query_for_phase()` (parallel, no inter-deps)
5. `cli.py` — `add-to-nlm` command
6. `ui/components/action_panel.py` — UI widget

## Success Metrics

- All 12 acceptance criteria pass
- NLM context non-empty in ≥ 1 phase when open-notebook server is running
- No regressions in existing Phase 1 PubMed search behavior
- `literature_seed.json` still written (unchanged)

## Status
- Phase: plan
- Created: 2026-03-06
