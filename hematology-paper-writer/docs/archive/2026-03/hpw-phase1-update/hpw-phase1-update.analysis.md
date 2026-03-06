# Gap Analysis: hpw-phase1-update

**Date:** 2026-03-06
**Feature:** Phase 1 (Topic Development) improvements — PubMed relevance + pipeline data flow
**Match Rate:** 100% (13 / 13 requirements implemented) — after iteration 1

---

## Requirements vs Implementation

| # | Requirement (from brainstorm) | Status | Evidence |
|---|-------------------------------|--------|---------|
| R1 | Disease-specific MeSH terms replace naive word extraction | PASS | `DISEASE_MESH_TERMS` dict; `_build_disease_mesh_block()` |
| R2 | Drug/intervention MeSH term templates (14 drugs) | PASS | `INTERVENTION_MESH_TERMS` dict; `_build_intervention_block()` |
| R3 | Study type → publication filter (Clinical Trial, cohort, etc.) | PASS | `STUDY_TYPE_PUBMED_FILTERS`; `THERAPEUTIC`, `PROGNOSTIC`, etc. |
| R4 | Date filter (2015+) and English-only filter | PASS | `full_query` includes both filters |
| R5 | NotebookLM queried first before PubMed | PASS | `integrate_skills_phase1()` Step 1: NLM health check → `ask()` |
| R6 | Persist `ResearchTopic` to `research_topic.json` | PASS | `save_project_topic()` / `load_project_topic()` |
| R7 | Save PubMed results to `literature_seed.json` | PASS | `save_literature_seed()` / `load_literature_seed()` |
| R8 | Manual selection flag (`manual_selection` param) | PASS | `LiteratureSeed.selected`; `manual_selection=False` default |
| R9 | Create project NotebookLM notebook + add top-20 article URLs | PASS | Step 3 in `integrate_skills_phase1()`: `create_notebook()` + `add_source_url()` |
| R10 | Phase 2 (`StudyDesignManager`) loads Phase 1 PICO automatically | PASS | `load_phase1_topic()` pre-populates `current_design` |
| R11 | CLI (`cli.py`) exposes new Phase 1 parameters and return value | PASS | `--disease`, `--intervention`, `--manual-selection` args added; `integrate_skills_phase1()` called in `cmd_research()` |
| R12 | Phase 4 draft generator loads `literature_seed.json` as reference pool | PASS | `ResearchWorkflow._load_from_seed()` added; `run()` tries seed before live PubMed |
| R13 | UI (Streamlit) shows manual article selection panel for literature review | PASS | `_render_literature_selection()` added to `action_panel.py`; checkbox per article, auto-saves selections to seed file |

---

## Gap Detail

### GAP-11: CLI not wired to new Phase 1 pipeline
- **Location:** `cli.py` — the `research` and `create-draft` commands
- **Impact:** Users running `hpw research "topic"` still get the old NLM/PubMed flow; `research_topic.json` and `literature_seed.json` are never created from the CLI
- **Fix:** Call `integrate_skills_phase1()` inside the `research` command handler; expose `--manual-selection` flag

### GAP-12: Phase 4 draft generator ignores `literature_seed.json`
- **Location:** `tools/draft_generator/manuscript_drafter.py` and `enhanced_drafter.py`
- **Impact:** Phase 1 literature search results are saved but never read during manuscript generation — draft references are re-queried from scratch, defeating the purpose of the seed
- **Fix:** In `EnhancedManuscriptDrafter._gather_references()`, check `literature_seed.json` first before running a new PubMed query; include selected articles in the reference pool

### GAP-13: No UI panel for manual article selection
- **Location:** `ui/components/action_panel.py` or a new `literature_review.py` component
- **Impact:** The `manual_selection` feature exists in the backend but users have no way to see or deselect articles from the UI
- **Fix:** Add a table/checkbox component in Phase 1 UI tab showing articles sorted by `relevance_score`; deselected articles update `selected=False` and re-save the seed

---

## Positive Findings

- MeSH query output verified via smoke test; produces clinically-scoped queries (e.g., `"Leukemia, Myeloid, Acute"[MeSH] AND "venetoclax"[tiab] AND "Clinical Trial"[pt]`)
- `literature_seed.json` round-trips correctly (save → load → verify)
- `research_topic.json` persists and `load_phase1_topic()` in Phase 2 correctly pre-populates `primary_endpoint` and `primary_objective`
- PICO relevance scoring works (0.0–1.0 scale based on keyword overlap)
- All code compiles; syntax verified via `py_compile`

---

## Next Steps

Match rate 69% → below 90% threshold. Recommend `/pdca iterate hpw-phase1-update` to fix:
1. **GAP-11** (CLI wiring) — highest impact; makes everything accessible from `hpw` command
2. **GAP-12** (Phase 4 loading literature_seed) — closes the full pipeline loop
3. **GAP-13** (UI selection panel) — enhances usability; can be done last
