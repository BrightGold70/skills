---
name: hematology-paper-writer
description: Write, analyze, and improve hematology manuscripts for journals like Blood, Blood Advances, JCO, BJH, and Blood Research. Features PubMed literature search, web search integration, manuscript drafting, quality analysis, reference verification, DOCX/PPT/PDF conversion, NotebookLM-powered research intelligence (WHO 2022, ICC 2022, ELN 2022/2025, NIH cGVHD, ISCN 2024, HGVS 2024), PRISMA/CONSORT/CARE compliance checking, nomenclature validation (BCR::ABL1 double-colon notation), statistical bridge for CSA integration, and Streamlit web UI. Use when asked to write, draft, review, improve, or analyze any hematology manuscript, systematic review, case report, or clinical trial report.
---

# Hematology Paper Writer

Expert system for creating publication-ready hematology manuscripts.

## Core Principles

1. **Clinical Accuracy**: Medical/scientific terminology must be correct and current
2. **Journal Compliance**: Follow target journal's specific formatting and content requirements
3. **Reference Integrity**: Verify all citations against PubMed (100% match required)
4. **Academic Rigor**: Maintain scholarly standards per hematology research conventions
5. **Research Integrity**: All claims must be supported by verified peer-reviewed sources
6. **Reproducibility**: Document methods and analyses clearly for replication
7. **Web-Enhanced Research**: Leverage web search for real-time evidence gathering

## Working Directory

All outputs go to:
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

1. **NotebookLM first** — query via `NotebookLMIntegration` (contains curated WHO 2022, ICC 2022, ELN 2022/2025, NIH cGVHD, BOIN, CTCAE v5 guidelines). Config: `notebooklm_config.json` in HPW root.
2. **PubMed fallback** — use `PubMedSearcher` only when NotebookLM has no relevant data.
3. **Web search** — use Tavily for current events, regulatory updates, and news not in PubMed.

## CLI Commands

```bash
# Activate venv first
source /Users/kimhawk/.config/opencode/skill/hematology-paper-writer/.venv/bin/activate

hpw search-pubmed "asciminib CML" --max-results 50 --time-period 5y
hpw create-draft "topic" --journal blood_research --docx
hpw research "topic" --journal blood                   # full workflow
hpw check-quality manuscript.md --journal blood
hpw verify-references manuscript.md
hpw check-concordance manuscript.docx --validate-format
hpw edit-manuscript manuscript.md --journal blood
hpw generate-report manuscript.md --verify-references
hpw convert manuscript.docx draft.md --format md

# Scientific skills (cross-phase)
hpw hypothesis "AML FLT3" --project SAPPHIRE
hpw brainstorm "venetoclax resistance" --project SAPPHIRE
hpw visualize-figure "KM curve" --project SAPPHIRE
hpw grant-draft "AML immunotherapy" --project SAPPHIRE
```

## Supported Journals

| Journal | Code | Abstract | Text | References |
|---------|------|----------|------|------------|
| Blood Research | `blood_research` | 250 w | 6000 w | Vancouver |
| Blood | `blood` | 200 w | 5000 w | Vancouver |
| Blood Advances | `blood_advances` | 250 w | 6000 w | Vancouver |
| JCO | `jco` | 250 w | 4000 w | Numbered |
| BJH | `bjh` | 200 w | 5000 w | Vancouver |
| Leukemia | `leukemia` | 200 w | 5000 w | Vancouver |
| Haematologica | `haematologica` | 250 w | 5000 w | Vancouver |

## Domain Constraints

- **Citation style**: Vancouver numbered (exception: JCO uses numbered non-Vancouver)
- **Reference count**: Minimum 25-35 refs for ~6,500-word manuscripts; every factual sentence must be cited
- **Abstracts**: Must reach near the journal's maximum word limit (not summarized)
- **Nomenclature**: BCR::ABL1 double-colon notation (HGVS 2024), ISCN 2024 karyotype format
- **Prose-only**: No bullet points in manuscript body text
- **Reporting guidelines** (mandatory): PRISMA 2020 (reviews), CONSORT 2010 (RCTs), CARE 2013 (case reports), STROBE (observational)

## Prose Density Mandates (CRITICAL — enforced on every draft)

These are hard minimums. Any section below minimum must be expanded before proceeding.

### Word Count Floors (Systematic Review)

| Section | Minimum words | Target | Paragraphs |
|---------|--------------|--------|------------|
| Abstract | 220 | 245 | 4-part structured |
| Introduction | 600 | 780 | 4 |
| Methods | 800 | 1050 | 6–8 |
| Results | 900 | 1200 | 5–7 |
| Discussion | 900 | 1200 | 5 |
| **Body total** | **3400** | **4430** | — |

### Paragraph Architecture Rules

1. **Minimum 5 sentences per paragraph** — any paragraph with fewer than 5 sentences is incomplete
2. **Medical PEEL structure**: Point → Evidence → Elaboration (×2) → Link
3. **Every data point requires elaboration**: p-values, CIs, percentages must be followed by a sentence explaining clinical significance
4. **Comparative specificity**: "Previous studies showed similar results" is NEVER acceptable — name the author, year, and specific value

### Anti-Bullet-List Rules (ABSOLUTE — no exceptions)

These sections must be written as prose paragraphs, never as bullet/numbered lists:
- Objectives → prose paragraph in Introduction para 4
- PICO elements → single compound prose sentence in Introduction para 4
- Inclusion criteria → one prose paragraph
- Exclusion criteria → one prose paragraph continuing inclusion para or separate paragraph
- Database list → prose sentence: "We searched X, Y, and Z from [date] through [date]"
- Outcome list → "The primary outcome was X. Secondary outcomes included Y, Z, and W."

### Abstract Non-Negotiables

- **Never use placeholders** ("A [study design] was conducted" = unacceptable)
- **Background**: 2–3 full sentences with disease burden data
- **Methods**: 2–3 sentences specifying design, databases, population, primary endpoint
- **Results**: 4–5 sentences with specific numbers, CIs, and p-values
- **Conclusions**: 2–3 sentences with clinical implication and future direction

## CSA Integration (Statistical Bridge)

When statistical data is available from the clinical-statistics-analyzer:
- Read `hpw_manifest.json` written by CSA orchestrator via `tools/statistical_bridge.py`
- `StatisticalBridge.generate_results_prose(disease)` auto-enriches 11 stat keys with NotebookLM guideline context
- Run with: `hpw research "topic" --csa-output /path/to/hpw_manifest.json`

## Reference Files

Load these on demand based on the task:

| File | Load When |
|------|-----------|
| `references/writing-standards.md` | Drafting manuscripts; web search integration; document type templates (systematic review, RCT, case report, etc.) |
| `references/citations.md` | Formatting references; verifying citations; Vancouver style details |
| `references/quality-workflow.md` | QA checklist; source discovery; end-to-end workflow examples |
| `references/prose-expansion.md` | **Load for every drafting task** — section word targets, Medical PEEL paragraph structure, section blueprints, anti-bullet conversion rules, sentence variety patterns, expansion triggers, positive humanization guide |
| `references/advanced-workflows.md` | Review simulation; Farquhar abstract method; brainstorming; prose polish; reader testing; goal-oriented recipes |
| `references/scientific-skills.md` | Using the 13 scientific skill classes (`HypothesisGenerator`, `StatisticalAnalyst`, etc.) |
| `references/2022_WHO_MyeloidClassificationDefinition.md` | WHO 2022 diagnostic criteria for all myeloid entities (AML blast thresholds, MDS, MPN, CML, CHIP). Load when writing disease classification or definition sections, verifying entity names, blast percentages, or molecular criteria per WHO 2022. |
| `references/2022_ICC_MyeloidClassificationDefinition.md` | ICC 2022 diagnostic criteria. Load alongside the WHO file when documenting WHO vs ICC divergence: CML accelerated phase (ICC-only), AML with NPM1 blast threshold (any% WHO vs ≥10% ICC), or MDS naming ("Neoplasms" WHO vs "Syndromes" ICC). |
| `references/nomenclature-guidelines.md` | Comprehensive HPW nomenclature rules: gene/chromosome naming, BCR::ABL1 double-colon notation, ISCN 2024 karyotype format, mutation/variant terminology. Load when drafting or verifying nomenclature in any section. |
| `references/hgvs-2024-update.md` | Summary of HGVS 2024 changes from the 2016 standard. Load when verifying fusion gene notation or variant nomenclature updates (e.g., double-colon for fusions). |
| `references/enhanced-editor.md` | Capabilities reference for the `EnhancedEditor` module: section-level enhancement, tracked-changes revision, prose polishing. Load when using `hpw edit-manuscript` or manuscript revision workflows. |
| `references/notebooklm-integration.md` | NotebookLM source configuration plan: notebook setup, source URLs, `bootstrap_notebooks.py` usage, and query patterns for WHO/ICC/ELN/NIH guidelines. Load when configuring or troubleshooting NotebookLM queries. |
| `references/examples.md` | Detailed usage examples and end-to-end workflows for the HPW skill. Load when looking for concrete command examples, output samples, or workflow recipes. |
