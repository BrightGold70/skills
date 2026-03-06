# Completion Report: hpw-phase1-update

**Date:** 2026-03-06
**Feature:** Phase 1 (Topic Development) — PubMed relevance & pipeline data flow
**Final Match Rate:** 100% (13/13)
**Iterations:** 1 (69% → 100%)
**Status:** COMPLETED

---

## Executive Summary

Phase 1 of the hematology-paper-writer had two user-reported problems:

1. **PubMed search results were mostly irrelevant** — caused by naive word extraction from PICO text that produced generic, overly broad queries (e.g., `"Adults"[Title/Abstract]`), violation of the CLAUDE.md "NotebookLM first" rule, and no publication-type or date filtering.

2. **Research data didn't flow to Phase 2 or later** — `ResearchTopic` (PICO) existed only in-memory; Phase 2 constructed `StudyDesign` from scratch with no knowledge of Phase 1 output; `literature_seed.json` didn't exist.

Both problems are now fully resolved across 5 modified files with 1 new dataclass and 11 new/rewritten methods.

---

## Files Changed

| File | Type | Change |
|------|------|--------|
| `phases/phase1_topic/topic_development.py` | Core logic | MeSH queries, `LiteratureSeed`, persistence, `integrate_skills_phase1()` overhaul |
| `phases/phase2_research/study_design_manager.py` | Phase wiring | `load_phase1_topic()` |
| `tools/draft_generator/research_workflow.py` | Phase 4 | `_load_from_seed()`, seed-first logic in `run()` |
| `cli.py` | CLI | `--disease`, `--intervention`, `--manual-selection` args; Phase 1 pipeline call |
| `ui/components/action_panel.py` | UI | `_render_literature_selection()` with checkbox panel |

---

## Implementation Details

### 1. MeSH-Anchored PubMed Queries (R1–R4)

Replaced `_extract_search_terms()` (naive regex word extraction) with:

- `DISEASE_MESH_TERMS` — 9 disease-specific MeSH entries (AML, CML, MDS, GVHD, ALL, MPN, HCT, Lymphoma, Myeloma)
- `INTERVENTION_MESH_TERMS` — 14 drug-specific term sets (venetoclax, azacitidine, asciminib, ruxolitinib, etc.)
- `STUDY_TYPE_PUBMED_FILTERS` — publication-type filters per `StudyType` enum
- `generate_literature_search_strategy()` now produces: disease block + intervention block + outcome keywords + pub-type filter + date filter (2015+) + English filter

**Before** (example query for AML/venetoclax):
```
("Adults"[Title/Abstract] OR "newly"[Title/Abstract]) AND ("Venetoclax"[Title/Abstract])
```

**After:**
```
("Leukemia, Myeloid, Acute"[MeSH] OR "acute myeloid leukemia"[tiab] OR "AML"[tiab])
AND ("venetoclax"[tiab] OR "ABT-199"[tiab] OR "Venclexta"[tiab])
AND ("survival"[tiab])
AND ("Randomized Controlled Trial"[pt] OR "Clinical Trial"[pt] OR "cohort"[tiab])
AND ("2015/01/01"[PDAT] : "3000"[PDAT])
AND "English"[Language]
```

### 2. NotebookLM-First Pipeline (R5)

`integrate_skills_phase1()` now follows CLAUDE.md data-source priority:
1. Query NotebookLM via `nlm.ask(notebooklm_query)` — uses if response > 100 chars
2. Fall back to PubMed MeSH query only if NLM unavailable or sparse

### 3. Persistence Layer (R6–R8)

New `LiteratureSeed` dataclass stores: `pmid`, `title`, `authors`, `journal`, `year`, `abstract`, `relevance_score`, `selected`, `notebooklm_added`.

New `TopicDevelopmentManager` methods:
- `save_project_topic(project_dir)` → `research_topic.json`
- `load_project_topic(project_dir)` → `Optional[ResearchTopic]`
- `save_literature_seed(articles, project_dir)` → `literature_seed.json`
- `load_literature_seed(project_dir)` → `List[LiteratureSeed]`

PICO relevance scoring via `_score_pico_relevance()` ranks articles 0.0–1.0 by keyword overlap with PICO before saving.

### 4. NotebookLM Project Notebook (R9)

After PubMed search, `integrate_skills_phase1()` calls `nlm.create_notebook()` with project name + PICO description, then adds top-20 article URLs via `nlm.add_source_url()`. Articles with confirmed addition are flagged `notebooklm_added=True` in the seed.

### 5. Phase 2 PICO Inheritance (R10)

`StudyDesignManager.load_phase1_topic(project_dir)` reads `research_topic.json` and pre-populates `current_design.primary_endpoint`, `primary_objective`, `title`, and `design_type` (mapped from Phase 1 `StudyType`).

### 6. CLI Wiring (R11)

`hpw research` now supports:
```bash
hpw research "venetoclax AML elderly" \
  --disease AML \
  --intervention venetoclax \
  --manual-selection
```
`cmd_research()` calls `integrate_skills_phase1()` first, prints article count + notebook ID, then passes `output_dir` to `ResearchWorkflow`.

### 7. Phase 4 Seed Loading (R12)

`ResearchWorkflow._load_from_seed(output_dir)` checks `literature_seed.json` and returns duck-typed `_SeedArticle` objects (with `.title`, `.authors`, `.journal`, `.year`, `.abstract`, `.pmid`). `run()` uses these instead of a live PubMed query — eliminating redundant network calls and ensuring manual deselections are respected.

### 8. UI Article Selection Panel (R13)

`action_panel._render_literature_selection()` renders inside an `st.expander` with:
- One `st.checkbox` per article, keyed by PMID
- Relevance score bar (`█░` format, 0–10 blocks)
- Author, journal, year, PMID metadata per row
- Auto-saves on any checkbox change back to `literature_seed.json`
- Article count badge in expander header updates live

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| MeSH dictionary over dynamic extraction | PubMed MeSH terms are stable; pre-built templates for 9 diseases + 14 drugs give precision without NLP overhead |
| `selected=True` default | Auto-include reduces friction for most users; `--manual-selection` flag inverts for power users who want explicit review |
| Duck-typed `_SeedArticle` | Avoids importing Phase 1 classes into draft generator; maintains backward compatibility with `ManuscriptDrafter.create_draft()` |
| Seed-first in `run()` | Phase 4 respects user's manual curation; avoids re-querying PubMed with potentially less specific queries |

---

## Testing

All 5 modified files pass `py_compile` syntax check.

Smoke test verified:
- MeSH query generation for AML + venetoclax (correct MeSH terms, filters, date range)
- `research_topic.json` round-trip (save → load → field equality)
- `literature_seed.json` round-trip (save → load → type check)
- PICO relevance scoring (0.182 for matching abstract)
- Phase 2 `load_phase1_topic()` pre-populates `primary_endpoint`

---

## Next Steps (optional)

- Add MeSH terms for additional diseases (Lymphoma subtypes, Myeloma sub-entities)
- Add `--intervention` auto-detection from `research_topic.json` when PICO has intervention set
- UI: add "Re-run search" button in the selection panel to refresh with updated PICO
