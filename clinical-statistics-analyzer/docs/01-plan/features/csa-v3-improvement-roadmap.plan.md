# Clinical Statistics Analyzer — Improvement Roadmap

**Created**: 2026-03-04
**Status**: Planned
**Current Version**: 3.0.0 (with unified pipeline orchestrator)

## Overview

Multi-phase improvement plan addressing output quality, disease coverage gaps, pipeline robustness, and cross-skill integration. Priorities based on brainstorming session identifying output format/quality as the top pain point.

---

## v3.1: Output Quality & CML Expansion

**Theme**: Publication-ready polish + CML disease gaps + mini-CSR report

### Output Improvements

1. **Journal-specific table templates**
   - NEJM, Lancet, Blood, JCO styling via `flextable` themes
   - Configurable fonts, borders, p-value formatting per journal
   - Template selection via `--journal` CLI arg or config

2. **Unified mini-CSR report generator (ICH-E3 lite)**
   - Single document combining all tables/figures with auto-generated narrative
   - Sections: Demographics, Efficacy, Safety, Survival (per ICH-E3 structure)
   - Integrates with `clinical-reports` skill for full CSR handoff
   - Output: .docx with embedded tables/figures

3. **PDF direct export**
   - Generate PDF alongside .docx/.eps using `officer::print()` or `rmarkdown`
   - Vector graphics preserved in PDF figures

4. **Interactive HTML dashboards** (optional output)
   - Plotly KM curves (zoomable, hover details)
   - DT filterable safety/baseline tables
   - Self-contained single HTML file per analysis
   - Enabled via `--html` flag

### CML Expansion (4 new R scripts)

| Script | Purpose | Key Features |
|--------|---------|--------------|
| `26_cml_eln_milestones.R` | ELN 2020 milestone response table | 3/6/12/18mo optimal/warning/failure classification; BCR-ABL IS thresholds |
| `27_cml_waterfall.R` | BCR-ABL waterfall plots | Individual patient response depth; log-scale reduction from baseline |
| `28_cml_resistance.R` | TKI resistance mutation tracking | ABL1 kinase domain mutations; resistance timeline visualization |
| `29_cml_tfr_deep.R` | TFR deep analysis | Molecular relapse kinetics; sustained MR4 duration; loss-of-MMR cumulative incidence |

### Estimated Scope
- ~8 new/modified R scripts
- ~2 new Python modules (report generator, HTML exporter)
- Config additions for journal templates
- 15-20 new tests

---

## v3.2: Pipeline Robustness & MDS Coverage

**Theme**: Data pipeline hardening + MDS disease-specific scripts

### Pipeline Improvements

1. **Fix pre-existing test import paths** — All 25 legacy tests green
2. **SPSS label decoding** — Add `spss_decode` type to `value_recoder` transformer
3. **Fuzzy column name matching** — Auto-suggest mappings for unknown columns using `thefuzz`
4. **Data quality dashboard** — Completeness heatmap, outlier flagging, type mismatch detection
5. **Parallel R script execution** — `concurrent.futures` in orchestrator for independent scripts

### MDS Disease-Specific Scripts (5 new)

| Script | Purpose | Key Features |
|--------|---------|--------------|
| `30_mds_ipss_scoring.R` | IPSS-R/IPSS-M risk scoring | Calculate from raw variables; risk group distribution; KM by risk |
| `31_mds_iwg_response.R` | IWG 2006 response assessment | CR/mCR/PR/HI-E/HI-P/HI-N/SD/PD; response waterfall |
| `32_mds_transfusion.R` | Transfusion burden analysis | RBC units/8wk tracking; TI milestone; ferritin trends |
| `33_mds_hma_response.R` | HMA response tracking | Response by cycle; cumulative best response; time to response |
| `34_mds_aml_transform.R` | AML transformation monitoring | Cumulative incidence with competing risks; risk factors |

### Estimated Scope
- 5 new R scripts
- ~3 Python modules (fuzzy matcher, quality dashboard, parallel executor)
- Test infrastructure overhaul
- 20-25 new tests

---

## v3.3: Integration & Advanced Capabilities

**Theme**: Cross-skill integration + HCT expansion + advanced analyses

### Cross-Skill Integration

1. **Mini-CSR → `clinical-reports` handoff** — ICH-E3 full document generation
2. **Auto IMRAD sections** — `academic-writing` skill generates Methods/Results text
3. **PowerPoint slide deck** — Auto-generated slides for investigator meetings
4. **LaTeX/RTF output** — Regulatory submission formats
5. **Multi-study portfolio comparison** — Cross-study statistical summaries

### HCT Expansion (3 new R scripts)

| Script | Purpose |
|--------|---------|
| `35_hct_chimerism.R` | Chimerism kinetics visualization (D+30/D+100/D+180 trends) |
| `36_hct_immune_recon.R` | Immune reconstitution monitoring (lymphocyte subsets over time) |
| `37_hct_gvhd_organ.R` | Organ-specific GVHD deep analysis (skin/liver/GI staging) |

### Advanced Capabilities

- Bayesian analysis modules (beyond BOIN)
- Meta-analysis support across disease types
- Automated subgroup discovery (interaction screening)

### Estimated Scope
- 3+ new R scripts
- 3-5 Python integration modules
- Cross-skill API contracts
- 15-20 new tests

---

## Dependencies & Prerequisites

| Phase | Depends On | External |
|-------|-----------|----------|
| v3.1 | v3.0 orchestrator (done) | `officer`, `rmarkdown`, `plotly`, `DT` R packages |
| v3.2 | v3.1 output infrastructure | None new |
| v3.3 | v3.2 pipeline robustness | `clinical-reports` skill, `academic-writing` skill |

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Journal template maintenance | Med | Abstract templates into config JSON, not hardcoded |
| HTML dashboard size | Low | Lazy loading, data pagination |
| Cross-skill API stability | High | Define contract interfaces before implementation |
| R package version conflicts | Med | Pin versions in documentation, test matrix |
