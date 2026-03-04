# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An OpenCode skill that orchestrates end-to-end statistical analysis for hematological clinical trials (AML, CML, MDS, HCT) across Phases 1-3. It combines Python for data parsing/extraction and R (via RMCP MCP server) for statistical computation, producing publication-ready outputs (.docx tables, .eps figures).

## Path Structure

- **Skill scripts**: `scripts/` (this repo)
- **CRF pipeline**: `scripts/crf_pipeline/` — unified CRF extraction, parsing, and validation package (v3.0.0)
- **Output directory**: Set via environment variables (no hardcoded paths). Organized into `data/`, `Tables/`, and `Figures/` subdirectories
- **Validation schemas**: `schemas/` — JSON schemas for CRF specs, protocols, and validation rules

## Running Scripts

### Environment Variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `CSA_OUTPUT_DIR` | All R scripts | Base output directory for Tables/, Figures/, data/ |
| `CRF_OUTPUT_DIR` | CRF pipeline (`run` subcommand) | Output directory for CRF extraction results |

```bash
# Set before running any script
export CSA_OUTPUT_DIR="/path/to/output"        # R scripts
export CRF_OUTPUT_DIR="/path/to/crf_output"    # CRF pipeline
```

### Python

Python scripts use the venv at `venv/`:
```bash
source venv/bin/activate
# CRF pipeline (unified CLI with subcommands)
python -m scripts.crf_pipeline run <input_dir> -d aml -o /path/to/output
python -m scripts.crf_pipeline parse-crf <crf_doc>
python -m scripts.crf_pipeline parse-protocol <protocol_doc>
python -m scripts.crf_pipeline parse-data <data_file>
python -m scripts.crf_pipeline validate <data_file> --protocol spec.json
python -m scripts.crf_pipeline run-analysis <data_file> -d aml -o /path/to/output
```

### R Scripts

R scripts are executed via the RMCP MCP server (`mcp_rmcp_execute_r_analysis`) or directly:
```bash
export CSA_OUTPUT_DIR="/path/to/output"
Rscript scripts/02_table1.R <dataset_path>
```

Python dependencies: `pip install -r requirements.txt` (python-docx, pypdf, pandas, openpyxl, pyreadstat, thefuzz, jsonschema)

R packages used: `table1`, `survival`, `survminer`, `cmprsk`, `pwr`, `flextable`, `officer`, `ggplot2`, `forestplot`, `ggsankey`, `patientProfilesVis`, `readxl`, `haven`

## Architecture

### CRF Pipeline (`scripts/crf_pipeline/`)

Unified Python package (v3.0.0) for CRF extraction, document parsing, and data validation. Supports AML, CML, MDS, HCT via layered JSON config.

| Module | Purpose |
|--------|---------|
| `orchestrator.py` | Analysis orchestrator: chains transform → R scripts → summary |
| `transformers/column_mapper.py` | Config-driven CRF → R column name mapping |
| `transformers/date_calculator.py` | Date arithmetic for time-to-event computation |
| `transformers/value_recoder.py` | Categorical recoding and numeric binning |
| `config/analysis_profiles.json` | R script routing per disease type |
| `parsers/crf_parser.py` | Extract CRF variable definitions with fuzzy matching → JSON |
| `parsers/protocol_parser.py` | Parse clinical trial protocols (DOCX/PDF) → endpoints, arms, sample size |
| `parsers/crf_spec_parser.py` | Parse CRF specifications (DOCX/XLSX) → variable definitions, ranges |
| `parsers/data_parser.py` | Parse patient data (XLSX/CSV/SPSS/JSON) → structure analysis |
| `validators/temporal_validator.py` | Temporal consistency checks (date sequences, visit order) |
| `validators/rule_validator.py` | Rule-based validation against protocol/CRF specs |
| `validators/schema_validator.py` | JSON schema validation |
| `cli.py` | Unified CLI with subcommands: `run`, `parse-crf`, `parse-protocol`, `parse-data`, `validate`, `run-analysis` |
| `pipeline.py` | Full extraction pipeline orchestrator |

### R Analysis Scripts (numbered by execution order)

| # | Script | Purpose |
|---|--------|---------|
| 02 | `table1.R` | Baseline characteristics table → .docx |
| 03 | `efficacy.R` | Efficacy + subgroup forest plot; supports `--disease aml/cml/mds/hct` for disease-specific subgroup sets; regression table → .docx, forest plot → .eps |
| 04 | `survival.R` | Kaplan-Meier, Cox models, competing risks, GRFS (Fine-Gray) → .eps; supports `--disease aml/cml/hct`; `cox.zph()` PH testing built-in |
| 05 | `safety.R` | CTCAE adverse event summaries (≥10% default) → .docx |
| 10 | `sample_size.R` | Power calculations (binary/continuous/survival) |
| 11 | `phase1_dose_finding.R` | 3+3 and CRM dose-finding designs |
| 12 | `phase2_simon.R` | Simon two-stage (Optimal/Minimax) designs |
| 14 | `forest_plot.R` | Subgroup analysis forest plots → .eps |
| 15 | `swimmer_plot.R` | Patient treatment pathway visualization → .eps |
| 16 | `sankey.R` | Treatment flow Sankey diagrams → .eps |
| 20 | `20_aml_eln_risk.R` | **AML**: ELN 2022 risk stratification (Favorable/Intermediate/Adverse); all molecular/cytogenetic criteria → .docx + .eps bar chart |
| 21 | `21_aml_composite_response.R` | **AML**: cCR composite response (CR+CRi+CRh+MLFS) per ELN 2022; Wilson score CIs; waterfall + bar plots → .docx + .eps |
| 22 | `22_cml_tfr_analysis.R` | **CML**: BCR-ABL kinetics (log10 IS), ELN 2020 milestone table (3/6/12/18 mo), TFR KM + Cox → .docx + .eps |
| 23 | `23_cml_scores.R` | **CML**: Sokal/Hasford/ELTS score calculation from raw variables; risk group distribution table; concordance table; KM by risk → .docx + .eps |
| 24 | `24_hct_gvhd_analysis.R` | **HCT**: aGVHD/cGVHD cumulative incidence (Fine-Gray, NIH 2014), GRFS, engraftment kinetics → .docx + .eps |
| 25 | `25_aml_phase1_boin.R` | **AML Phase 1**: BOIN dose-finding (Liu & Yuan 2015); λ_e/λ_d boundaries; Monte Carlo OC simulation; isotoxicity plot → .docx + .eps |

### Integrated Skills

This skill coordinates with other OpenCode skills at runtime:
- **rmcp**: R execution engine (primary computation)
- **clinicaltrials-database** / **pubmed-database**: Comparable trial lookup and literature search
- **clinical-reports**: ICH-E3 CSR formatting
- **academic-writing**: IEEE IMRAD structure for publications
- **docx** / **pdf**: Document parsing

## Key Conventions

- **Output formats**: Always `.docx` for tables (via `flextable`/`officer`), `.eps` for plots (via `ggsave(device="eps")` or `postscript()`)
- **Disease-specific endpoints**: AML uses CR/PR/CRi/CRh/cCR (ELN 2022), ELN risk groups; CML uses MMR/CCyR/TFR (ELN 2020 milestones); MDS uses HI/transfusion independence; HCT uses engraftment/GVHD (NIH 2014)/GRFS via Fine-Gray competing risks
- **Statistical rigor**: All p-values and CIs must come from R computation — never hallucinate statistics. Reject analyses that fail assumption checks (e.g., Cox proportional hazards violation) without appropriate corrections.
- **CRF pipeline**: Run via `python -m scripts.crf_pipeline <subcommand>`. Parsers follow stateless pattern: `__init__(config)` + `parse(input_path) -> Dict`
- **CRF mapping outputs** are saved to the `data/` subfolder (under `CSA_OUTPUT_DIR`) as `crf_mapping.json`
