# CSA v3.1: Output Quality & CML Expansion — Planning Document

> **Summary**: Publication-ready output polish, CML disease gap closure, and mini-CSR report generation
>
> **Project**: clinical-statistics-analyzer
> **Version**: 3.1.0 (target)
> **Author**: Claude
> **Date**: 2026-03-04
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Elevate clinical-statistics-analyzer output from functional to publication-ready quality, close CML disease coverage gaps, and add a unified mini-CSR report generator. This is the highest-priority improvement identified in the v3 brainstorming session.

### 1.2 Background

The v3.0 unified pipeline orchestrator successfully bridges the Python CRF pipeline with R analysis scripts. However:
- Output is single-format only (.docx tables, .eps figures) with no journal-specific styling
- No unified report combining all analyses into a single document
- CML coverage lacks milestone response tracking, waterfall plots, resistance mutation analysis, and deep TFR analysis
- No PDF direct export or interactive HTML dashboard option

### 1.3 Related Documents

- Roadmap: `docs/01-plan/features/csa-v3-improvement-roadmap.plan.md`
- Predecessor: `docs/01-plan/features/unified-pipeline-orchestrator.plan.md`
- CRF Pipeline Report: `docs/04-report/crf-pipeline-overhaul.report.md`

---

## 2. Scope

### 2.1 In Scope

- [ ] Journal-specific table templates (NEJM, Lancet, Blood, JCO) via `flextable` themes
- [ ] Unified mini-CSR report generator (ICH-E3 lite structure)
- [ ] PDF direct export alongside .docx/.eps
- [ ] Interactive HTML dashboards (optional `--html` flag)
- [ ] CML ELN 2020 milestone response table (`26_cml_eln_milestones.R`)
- [ ] CML BCR-ABL waterfall plots (`27_cml_waterfall.R`)
- [ ] CML TKI resistance mutation tracking (`28_cml_resistance.R`)
- [ ] CML TFR deep analysis (`29_cml_tfr_deep.R`)
- [ ] Update orchestrator config to route new CML scripts
- [ ] Tests for all new components

### 2.2 Out of Scope

- Pipeline robustness improvements (v3.2)
- MDS disease-specific scripts (v3.2)
- Cross-skill integration with `clinical-reports` / `academic-writing` (v3.3)
- HCT expansion scripts (v3.3)
- PowerPoint/LaTeX output formats (v3.3)
- Multi-study portfolio comparison (v3.3)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Journal-specific `flextable` themes (NEJM, Lancet, Blood, JCO) with configurable fonts, borders, p-value formatting | High | Pending |
| FR-02 | `--journal` CLI arg or config option for template selection | High | Pending |
| FR-03 | Mini-CSR report generator combining Demographics, Efficacy, Safety, Survival sections per ICH-E3 structure | High | Pending |
| FR-04 | Mini-CSR outputs .docx with embedded tables/figures, auto-generated narrative placeholders | High | Pending |
| FR-05 | PDF export via `officer::print()` or `rmarkdown` for tables and figures | Medium | Pending |
| FR-06 | Interactive HTML dashboards: Plotly KM curves, DT filterable tables, self-contained single HTML file | Medium | Pending |
| FR-07 | `--html` CLI flag to enable HTML dashboard generation | Medium | Pending |
| FR-08 | `26_cml_eln_milestones.R`: ELN 2020 milestone response table (3/6/12/18 mo optimal/warning/failure; BCR-ABL IS thresholds; ±1.5 mo window) | High | Pending |
| FR-09 | `27_cml_waterfall.R`: Individual patient BCR-ABL response depth waterfall; log-scale reduction from baseline | High | Pending |
| FR-10 | `28_cml_resistance.R`: ABL1 kinase domain mutation tracking; resistance timeline visualization | Medium | Pending |
| FR-11 | `29_cml_tfr_deep.R`: Molecular relapse kinetics; sustained MR4 duration; loss-of-MMR cumulative incidence | Medium | Pending |
| FR-12 | Update `analysis_profiles.json` to include scripts 26-29 for CML disease routing | High | Pending |
| FR-13 | Update CML config (`cml_fields.json`) with column mappings for milestone/resistance variables | High | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Output Quality | Journal tables pass visual inspection against published exemplars | Manual review against NEJM/Blood style guides |
| Performance | Mini-CSR generation < 60s for a 100-patient dataset | Timed test run |
| Compatibility | HTML dashboards render correctly in Chrome, Firefox, Safari | Browser testing |
| Maintainability | Journal templates abstracted into JSON config, not hardcoded | Code review |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] All 13 functional requirements implemented
- [ ] 4 new R scripts (26-29) produce correct output with mock CML data
- [ ] Mini-CSR generator produces valid .docx with all sections
- [ ] Journal templates produce visually distinct table styles
- [ ] PDF export generates valid PDF files
- [ ] HTML dashboards are self-contained and interactive
- [ ] Orchestrator routes new CML scripts correctly
- [ ] Unit and integration tests written and passing
- [ ] SKILL.md and CLAUDE.md updated

### 4.2 Quality Criteria

- [ ] 15+ new tests passing
- [ ] All 39 existing tests still pass (no regression)
- [ ] Zero R script errors with mock data
- [ ] Mini-CSR document structure matches ICH-E3 lite outline

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Journal template maintenance burden | Medium | Medium | Abstract templates into JSON config, not hardcoded R styles |
| HTML dashboard file size (large datasets) | Low | Medium | Lazy loading, data pagination, DT server-side processing |
| R package version conflicts (plotly, DT, rmarkdown) | Medium | Low | Pin versions in documentation, test with current R env |
| BCR-ABL IS threshold variability across labs | Medium | Low | Make thresholds configurable in CML config JSON |
| Mini-CSR narrative quality | Medium | Medium | Use placeholder text with clear section markers for manual editing |
| `officer` limitations for complex layouts | Low | Low | Fallback to `rmarkdown` for PDF if `officer` insufficient |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Dynamic** | Feature-based modules, config-driven | Clinical trial analysis skills | **X** |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Journal themes | Hardcoded R / JSON config | JSON config | Maintainable, extensible, no code changes to add journals |
| Mini-CSR engine | Python (python-docx) / R (officer+rmarkdown) | Python (python-docx) | Better programmatic control for section assembly; R generates component tables/figures |
| HTML dashboards | R Shiny / rmarkdown+plotly / standalone HTML | rmarkdown+plotly | Self-contained, no server needed, single HTML file |
| PDF generation | officer::print / rmarkdown::render / LaTeX | rmarkdown::render | Best quality, handles both tables and figures |
| CML milestone windows | Fixed ±1.5 mo / Configurable | Configurable in JSON | Different studies may use different windows |

### 6.3 Architecture Overview

```
New/Modified Files:
scripts/
├── 26_cml_eln_milestones.R      (NEW) CML milestone response table
├── 27_cml_waterfall.R           (NEW) BCR-ABL waterfall plots
├── 28_cml_resistance.R          (NEW) TKI resistance tracking
├── 29_cml_tfr_deep.R           (NEW) TFR deep analysis
├── crf_pipeline/
│   ├── report_generator.py      (NEW) Mini-CSR assembly engine
│   ├── html_exporter.py         (NEW) HTML dashboard wrapper
│   ├── journal_themes.py        (NEW) Journal template loader
│   ├── config/
│   │   ├── journal_templates.json  (NEW) NEJM/Lancet/Blood/JCO styles
│   │   ├── analysis_profiles.json  (MOD) Add scripts 26-29 for CML
│   │   └── cml_fields.json         (MOD) Add milestone/resistance mappings
│   ├── cli.py                      (MOD) Add --journal, --html, --pdf flags
│   └── orchestrator.py             (MOD) Wire journal themes + report gen
tests/
├── test_cml_scripts.py          (NEW) CML R script output tests
├── test_report_generator.py     (NEW) Mini-CSR tests
├── test_journal_themes.py       (NEW) Journal template tests
└── test_html_exporter.py        (NEW) HTML dashboard tests
```

### 6.4 Data Flow

```
Transformed CSV (from orchestrator)
    │
    ├─→ R scripts (02-05, 26-29) → .docx + .eps (standard)
    │     │
    │     ├─→ journal_themes.py applies journal style → styled .docx
    │     ├─→ PDF export → .pdf versions of tables/figures
    │     └─→ html_exporter.py → interactive .html dashboards
    │
    └─→ report_generator.py
          │
          ├─ Collects all .docx tables + .eps figures
          ├─ Assembles into ICH-E3 lite structure
          ├─ Inserts narrative placeholders
          └─→ Mini-CSR .docx output
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] R scripts follow numbered naming (`NN_description.R`)
- [x] Python modules in `scripts/crf_pipeline/` package
- [x] Config-driven behavior via JSON files in `config/`
- [x] Tests in `tests/` directory with `test_` prefix

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| **R script numbering** | 02-25 used | 26-29 for CML expansion | High |
| **Journal config schema** | Missing | JSON schema for journal templates | High |
| **Report sections** | Missing | ICH-E3 lite section order | High |
| **HTML dashboard naming** | Missing | `Dashboard_{analysis_type}.html` | Medium |

### 7.3 Environment Variables

| Variable | Purpose | Scope | Exists |
|----------|---------|-------|:------:|
| `CSA_OUTPUT_DIR` | R script output directory | R scripts | Yes |
| `CRF_OUTPUT_DIR` | CRF pipeline output | Python | Yes |

No new environment variables needed.

---

## 8. Implementation Phases

### Phase 1: Journal Templates & PDF Export (Output Infrastructure)
1. Create `config/journal_templates.json` with NEJM, Lancet, Blood, JCO styles
2. Create `journal_themes.py` — load and apply `flextable` themes
3. Add `--journal` CLI arg to orchestrator
4. Add PDF export via `rmarkdown::render` or `officer::print`
5. Add `--pdf` CLI flag
6. Tests for journal themes and PDF generation

### Phase 2: CML Expansion (4 New R Scripts)
1. Create `26_cml_eln_milestones.R` — ELN 2020 milestone response table
2. Create `27_cml_waterfall.R` — BCR-ABL waterfall plots
3. Create `28_cml_resistance.R` — resistance mutation tracking
4. Create `29_cml_tfr_deep.R` — TFR deep analysis
5. Update `analysis_profiles.json` — add scripts 26-29 for CML
6. Update `cml_fields.json` — add milestone/resistance column mappings
7. Tests with mock CML data

### Phase 3: Mini-CSR Report Generator
1. Create `report_generator.py` — ICH-E3 lite document assembly
2. Define section structure (Demographics, Efficacy, Safety, Survival)
3. Auto-embed tables (.docx) and figures (.eps→png) into unified document
4. Add narrative placeholders per section
5. Wire into orchestrator as post-analysis step
6. Tests for report structure and content

### Phase 4: HTML Dashboards & Integration
1. Create `html_exporter.py` — rmarkdown + plotly wrapper
2. Plotly KM curves with zoom/hover
3. DT filterable safety/baseline tables
4. Self-contained single HTML file output
5. Add `--html` CLI flag
6. Integration tests: full pipeline with all output formats

---

## 9. Next Steps

1. [ ] Write design document (`csa-v31-output-quality-cml.design.md`)
2. [ ] Review and approval
3. [ ] Start Phase 1 implementation

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-04 | Initial draft based on improvement roadmap v3.1 | Claude |
