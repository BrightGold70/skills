# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An OpenCode skill (`hematology-paper-writer`) that provides an expert system for writing, analyzing, and improving hematology manuscripts targeting journals like Blood, Blood Advances, JCO, BJH, and Blood Research. It exposes a CLI (`hpw`), a Streamlit web UI, and a Python API.

## Commands

```bash
# Activate virtual environment (required)
source .venv/bin/activate

# Run CLI commands
python cli.py <command> [options]
# or via installed entry point:
hpw <command> [options]

# Launch Streamlit web UI
streamlit run ui/app.py

# Install dependencies
pip install -r requirements.txt
pip install -r ui/requirements.txt   # UI-specific deps
pip install -r tools/requirements.txt
```

### Key CLI Commands

```bash
hpw search-pubmed "asciminib CML" --max-results 50 --time-period 5y
hpw create-draft "topic" --journal blood_research --docx
hpw research "topic" --journal blood                 # full workflow
hpw check-quality manuscript.md --journal blood
hpw verify-references manuscript.md
hpw check-concordance manuscript.docx --validate-format
hpw edit-manuscript manuscript.md --journal blood
hpw generate-report manuscript.md --verify-references
hpw convert manuscript.docx draft.md --format md
```

Journal codes: `blood_research`, `blood`, `blood_advances`, `jco`, `bjh`, `leukemia`, `haematologica`

## Architecture

### Layer Structure

```
cli.py                          # Argparse CLI entry point
ui/app.py                       # Streamlit web UI (4 components)
tools/                          # Core analysis/generation library
  draft_generator/              # PubMed search + manuscript drafting
  hematology_guidelines/        # Domain rules (ELN, WHO, ICC, GVHD)
phases/                         # 11-phase workflow state machine
hematology-journal-specs/       # Journal requirements YAML
```

### `tools/` — Core Library

All public classes are re-exported from `tools/__init__.py`:

| Module | Key Class | Purpose |
|--------|-----------|---------|
| `quality_analyzer.py` | `ManuscriptQualityAnalyzer` | IMRaD compliance scoring |
| `pubmed_verifier.py` | `PubMedVerifier`, `BatchReferenceVerifier` | PubMed citation validation |
| `content_enhancer.py` | `ContentEnhancer` | Gap identification, improvement suggestions |
| `file_converter.py` | `FileConverter` | DOCX ↔ Markdown ↔ PDF ↔ PPTX |
| `reference_manager.py` | `ReferenceManager` | Vancouver-format reference handling |
| `nomenclature_checker.py` | `NomenclatureChecker`, `WHOICCComparator`, `ELNRiskStratification`, `GVHDGrader` | Hematology nomenclature validation (BCR::ABL1, HGVS 2024, ISCN 2024) |
| `notebooklm_integration.py` | `NotebookLMIntegration` | NotebookLM MCP primary data source |
| `citation_concordance.py` | — | Text citation ↔ reference list cross-check |
| `enhanced_editor.py` | `EnhancedEditor` | Section-level content enhancement |
| `manuscript_revisor.py` | `ManuscriptRevisor` | Tracked-changes revision |

### `tools/draft_generator/` — Manuscript Generation

| Module | Purpose |
|--------|---------|
| `pubmed_searcher.py` | PubMed E-utils API wrapper; returns `PubMedArticle` dataclass |
| `manuscript_drafter.py` | Base drafter; `Journal` enum; `JOURNAL_GUIDELINES` dict |
| `enhanced_drafter.py` | `EnhancedManuscriptDrafter` with academic style; `DocumentType`, `ReferenceStyle` enums |
| `compliance_checkers.py` | PRISMA 2020, CONSORT 2010, CARE 2013 checklist validators |
| `research_workflow.py` | `ResearchWorkflow` orchestrates search → draft → quality → verify |
| `tavily_searcher.py` | Web search integration via Tavily |
| `section_templates.py` | Per-journal IMRaD section templates |

### `phases/` — 11-Phase Workflow

Phases are state-managed via `phases/phase_manager.py` (`PhaseManager` class, JSON persistence). Each phase subdirectory has its own module:

| Phase | Directory | Main Class |
|-------|-----------|------------|
| 1 – Topic Selection | `phase1_topic/` | `TopicDevelopmentManager` |
| 2 – Research Design | `phase2_research/` | `StudyDesignManager` |
| 3 – Journal Strategy | `phase3_journal/` | `JournalStrategyManager` |
| 4 – Manuscript Prep | `phase4_manuscript/` | (delegates to `tools/`) |
| 4.5 – Updating | `phase4_5_updating/` | `ManuscriptUpdater` |
| 4.6 – Concordance | `phase4_6_concordance/` | (delegates to `tools/pubmed_verifier.py`) |
| 4.7 – Prose Verification | `phase4_7_prose/` | `ProseVerifier` |
| 5 – Quality | `phase5_quality/` | (delegates to `tools/quality_analyzer.py`) |
| 6 – Submission | `phase6_submission/` | `SubmissionManager` |
| 8 – Peer Review | `phase8_peerreview/` | `PeerReviewManager` |
| 9 – Publication | `phase9_publication/` | `PublicationManager` |
| 10 – Resubmission | `phase10_resubmission/` | `ResubmissionManager` |

### `ui/` — Streamlit Web Interface

`ui/app.py` is the entry point; four components in `ui/components/`:
- `phase_selector.py` — Phase navigation
- `status_dashboard.py` — Progress/milestone display
- `action_panel.py` — Command execution panel
- `file_manager.py` — Input/output file handling

### Journal Specs

`hematology-journal-specs/journal-specs.yaml` is the single source of truth for per-journal word limits, reference styles, section requirements, and reporting guideline mandates.

## Output Directory Convention

All generated files go to:
```
/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/[Project_Name]/
  docs/submissions/    # Final DOCX/PDFs
  docs/manuscripts/    # Design docs and brainstorming
  docs/drafts/         # Incremental section drafts
  literature/          # PDFs and exported PMIDs
  data/                # Raw CSVs and analysis scripts
```

Every output file **must** be prefixed with a timestamp: `YYYYMMDD_HHMMSS_filename.ext`

## Data Source Priority

When preparing manuscript content:
1. **NotebookLM first** — query via `NotebookLMIntegration` (contains curated research intelligence including WHO 2022, ICC 2022, ELN 2022/2025, NIH cGVHD guidelines)
2. **PubMed fallback** — use `PubMedSearcher` only when NotebookLM has no relevant data

## Domain Constraints

- All manuscripts use **Vancouver numbered citation style** (exceptions: JCO uses numbered, non-Vancouver)
- Minimum **25–35 references** for ~6,500-word manuscripts; every factual sentence must be cited
- Abstracts must reach **near the journal's maximum word limit** (not summarized)
- Nomenclature: BCR::ABL1 double-colon notation (HGVS 2024), ISCN 2024 karyotype format
- Manuscript body is **prose-only** — no bullet points in the body text
- Reporting guidelines are mandatory: PRISMA 2020 (reviews), CONSORT 2010 (RCTs), CARE 2013 (case reports), STROBE (observational)
