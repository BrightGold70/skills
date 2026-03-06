# Plan: Unified Pipeline Orchestrator

## Context

The clinical-statistics-analyzer skill currently has two disconnected layers:
- **Python CRF pipeline** (`scripts/crf_pipeline/`): Extracts, validates, and exports patient data
- **R analysis scripts** (`scripts/*.R`): Produce publication-ready tables (.docx) and figures (.eps)

Users must manually invoke each R script with correct arguments after running the CRF pipeline. Additionally, CRF pipeline variable names (snake_case: `case_no`, `alive`, `treat_group`) don't match R script expectations (mixed-case: `Patient_ID`, `OS_status`, `Treatment`), requiring manual data preparation.

**Goal**: A single `python -m scripts.crf_pipeline run-analysis` command that takes raw patient data through the full chain: parse → validate → transform → R analysis → output verification.

## Scope

### In Scope (Tier 1)
1. **Data Transformation Layer** — Config-driven variable mapping (CRF → R columns) per disease
2. **Analysis Orchestrator** — Subprocess-based R script execution with dependency ordering
3. **Config-driven R Script Routing** — Disease configs specify which R scripts to run and with what arguments
4. **New CLI subcommand** — `run-analysis` that chains everything end-to-end

### Out of Scope (Future Tiers)
- Multi-study portfolio management (Tier 2)
- New disease-specific R modules (Tier 3)
- CSR generation (Tier 4)
- Statistical rigor enhancements (Tier 5)

## Requirements

### FR-01: Data Transformer Module
- Config-driven variable name mapping per disease (CRF variable → R column name)
- Date arithmetic: compute time-to-event in months from raw dates (diagnosis → death/last follow-up)
- Categorical recoding: SPSS numeric codes → labels (or vice versa) as needed by R
- Derived variables: OS_status from `alive`, OS_months from dates, Treatment from `treat_group`/`induction_ct`
- Output: R-ready CSV file with transformed column names

### FR-02: Analysis Orchestrator Module
- Execute R scripts via subprocess with correct arguments derived from config
- Disease-aware script selection: AML runs 02/03/04/05 + 20/21, CML runs 02/03/04/05 + 22/23, HCT runs 02/03/04/05 + 24
- Ordered execution: table1 → safety → efficacy → survival → disease-specific
- Capture stdout/stderr, detect errors, continue on non-fatal failures
- Collect all output files (.docx, .eps, .csv) and report summary

### FR-03: Config-Driven R Script Routing
- New `analysis_scripts` section in each disease config JSON
- Each entry: script name, required args (mapped from transformed data), expected outputs
- Default outcome variables per disease (e.g., AML: CR for efficacy, OS_months/OS_status for survival)
- Optional scripts can be enabled/disabled via config

### FR-04: CLI Subcommand `run-analysis`
- Arguments: `<data_file> -d <disease> [-o <output_dir>] [--skip-validation] [--scripts <list>]`
- Flow: load data → parse-data → validate → transform → run R scripts → summary
- Uses `CSA_OUTPUT_DIR` for R output, `CRF_OUTPUT_DIR` for pipeline output
- Exit codes: 0 = all success, 1 = partial (some R scripts failed), 2 = pipeline failure

### FR-05: Output Summary Report
- JSON summary of all steps: parse status, validation status, each R script's exit code and outputs
- List of all generated files (.docx, .eps) with paths and sizes
- Elapsed time per step

## Architecture

### New Files

```
scripts/crf_pipeline/
├── transformers/
│   ├── __init__.py
│   ├── base.py              # AbstractTransformer with transform(df, config) → df
│   ├── column_mapper.py     # Variable name mapping (CRF → R)
│   ├── date_calculator.py   # Date arithmetic (time-to-event computation)
│   └── value_recoder.py     # Categorical recoding (SPSS codes ↔ labels)
├── orchestrator.py           # AnalysisOrchestrator: chains transform → R scripts
└── config/
    └── analysis_profiles.json  # R script routing per disease
```

### Modified Files

```
scripts/crf_pipeline/
├── cli.py                    # Add run-analysis subcommand
├── config/aml_fields.json    # Add column_mapping section
├── config/cml_fields.json    # Add column_mapping section
├── config/hct_fields.json    # Add column_mapping section
├── config/common_fields.json # Add common column_mapping
└── config/loader.py          # Load analysis_profiles.json
```

### Data Flow

```
Input CSV/XLSX/SAV
    │
    ├─→ parse-data (DataParser) → parsed JSON
    ├─→ validate (RuleValidator) → validation report
    │
    ▼
Transform Layer (column_mapper + date_calculator + value_recoder)
    │
    ▼
R-Ready CSV (with Treatment, OS_months, OS_status, Patient_ID, etc.)
    │
    ├─→ 02_table1.R [dataset] → Tables/Table1_Baseline_Characteristics.docx
    ├─→ 05_safety.R [dataset] → Tables/Safety_Summary_Table.docx
    ├─→ 04_survival.R [dataset] [time_var] [status_var] → Figures/KM_*.eps
    ├─→ 03_efficacy.R [dataset] [outcome_var] [--disease] → Tables/Efficacy_*.docx
    │
    ├─→ (AML) 20_aml_eln_risk.R [dataset] → Tables/AML_ELN2022_*.docx
    ├─→ (AML) 21_aml_composite_response.R [dataset] → Tables/AML_Composite_*.docx
    ├─→ (CML) 22_cml_tfr_analysis.R [dataset] → Tables/CML_*.docx
    ├─→ (CML) 23_cml_scores.R [dataset] → Tables/CML_Scores_*.docx
    ├─→ (HCT) 24_hct_gvhd_analysis.R [dataset] → Tables/HCT_*.docx
    │
    ▼
Summary Report (JSON) listing all generated files
```

### Variable Mapping Strategy

The `column_mapping` section in each disease config maps CRF variables to R-expected names:

```json
{
  "column_mapping": {
    "case_no": "Patient_ID",
    "age": "Age",
    "gender": "Sex",
    "treat_group": "Treatment",
    "alive": "OS_status",
    "FLT3ITD": "FLT3_ITD",
    "NPM1": "NPM1_mut"
  },
  "derived_columns": {
    "OS_months": {"type": "date_diff_months", "from": "reg_date", "to": "date_death", "censor": "date_last_fu"},
    "PFS_months": {"type": "date_diff_months", "from": "reg_date", "to": "relapse_date", "censor": "date_last_fu"},
    "OS_status": {"type": "recode", "source": "alive", "mapping": {"1": 0, "2": 1}},
    "Age_group": {"type": "bin", "source": "age", "bins": [0, 60, 200], "labels": ["<60", ">=60"]}
  }
}
```

### Analysis Profile Structure (`analysis_profiles.json`)

```json
{
  "version": "1.0",
  "profiles": {
    "aml": {
      "core_scripts": [
        {"script": "02_table1.R", "args": ["{dataset}"], "outputs": ["Tables"]},
        {"script": "05_safety.R", "args": ["{dataset}"], "outputs": ["Tables"]},
        {"script": "04_survival.R", "args": ["{dataset}", "OS_months", "OS_status"], "outputs": ["Figures", "Tables"]},
        {"script": "03_efficacy.R", "args": ["{dataset}", "CR", "--disease", "aml"], "outputs": ["Tables", "Figures"]}
      ],
      "disease_scripts": [
        {"script": "20_aml_eln_risk.R", "args": ["{dataset}"], "outputs": ["Tables", "Figures"]},
        {"script": "21_aml_composite_response.R", "args": ["{dataset}"], "outputs": ["Tables", "Figures"]}
      ],
      "default_outcome": "CR",
      "default_time_var": "OS_months",
      "default_status_var": "OS_status"
    },
    "cml": {
      "core_scripts": [
        {"script": "02_table1.R", "args": ["{dataset}"], "outputs": ["Tables"]},
        {"script": "05_safety.R", "args": ["{dataset}"], "outputs": ["Tables"]},
        {"script": "04_survival.R", "args": ["{dataset}", "OS_months", "OS_status"], "outputs": ["Figures", "Tables"]},
        {"script": "03_efficacy.R", "args": ["{dataset}", "MMR", "--disease", "cml"], "outputs": ["Tables", "Figures"]}
      ],
      "disease_scripts": [
        {"script": "22_cml_tfr_analysis.R", "args": ["{dataset}"], "outputs": ["Tables", "Figures"]},
        {"script": "23_cml_scores.R", "args": ["{dataset}"], "outputs": ["Tables", "Figures"]}
      ],
      "default_outcome": "MMR",
      "default_time_var": "OS_months",
      "default_status_var": "OS_status"
    },
    "hct": {
      "core_scripts": [
        {"script": "02_table1.R", "args": ["{dataset}"], "outputs": ["Tables"]},
        {"script": "05_safety.R", "args": ["{dataset}"], "outputs": ["Tables"]},
        {"script": "04_survival.R", "args": ["{dataset}", "OS_months", "OS_status", "hct"], "outputs": ["Figures", "Tables"]},
        {"script": "03_efficacy.R", "args": ["{dataset}", "CR", "--disease", "hct"], "outputs": ["Tables", "Figures"]}
      ],
      "disease_scripts": [
        {"script": "24_hct_gvhd_analysis.R", "args": ["{dataset}"], "outputs": ["Tables", "Figures"]}
      ],
      "default_outcome": "CR",
      "default_time_var": "OS_months",
      "default_status_var": "OS_status"
    }
  }
}
```

## Implementation Phases

### Phase 1: Data Transformer (Core)
1. Create `transformers/base.py` — AbstractTransformer interface
2. Create `transformers/column_mapper.py` — Rename columns per config mapping
3. Create `transformers/date_calculator.py` — Compute time-to-event from date pairs
4. Create `transformers/value_recoder.py` — Recode categoricals using SPSS mapping
5. Add `column_mapping` and `derived_columns` to disease config JSONs
6. Unit tests for each transformer

### Phase 2: Analysis Profiles & Orchestrator
1. Create `config/analysis_profiles.json` — Script routing per disease
2. Update `config/loader.py` — Load analysis profiles
3. Create `orchestrator.py` — AnalysisOrchestrator class
   - `transform(data_path, disease) → r_ready_csv_path`
   - `run_scripts(csv_path, disease, output_dir) → List[ScriptResult]`
   - `run_full(data_path, disease, output_dir) → AnalysisResult`
4. Unit tests for orchestrator (mock subprocess)

### Phase 3: CLI Integration & E2E Testing
1. Add `run-analysis` subcommand to `cli.py`
2. Wire orchestrator into CLI with argument parsing
3. Create E2E test: mock data → run-analysis → verify all outputs
4. Update SKILL.md with new subcommand documentation

## Verification

1. **Unit tests**: Each transformer, orchestrator mock tests
2. **E2E test**: `python -m scripts.crf_pipeline run-analysis tests/fixtures/aml_mock.csv -d aml` produces all expected .docx and .eps files
3. **Multi-disease**: Run for AML, CML, HCT — verify correct script selection
4. **Error handling**: Missing columns, missing R packages, invalid disease
5. **Existing tests**: All 25 existing E2E tests still pass (no regression)

## Dependencies

- Existing: pandas (for DataFrame transforms), subprocess (for R invocation)
- No new Python packages required
- R packages already installed: table1, cmprsk, forestplot, survival, survminer, flextable, officer, ggplot2

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| R script column mismatches | Config-driven mapping validated before R invocation |
| Date format variations | date_calculator handles ISO, DD/MM/YYYY, MM/DD/YYYY |
| Missing optional columns | Orchestrator checks required vs optional before running each script |
| R script failures | Non-fatal: log error, continue to next script, report in summary |
