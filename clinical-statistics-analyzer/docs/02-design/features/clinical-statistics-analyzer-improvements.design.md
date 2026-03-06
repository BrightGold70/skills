# Design: Clinical Statistics Analyzer Skill Improvements

## Architecture

The improvements follow a modular architecture extending the existing skill:

```
clinical-statistics-analyzer/
├── scripts/
│   ├── 10_sample_size.R          # NEW - Sample size calculations
│   ├── 11_phase1_dose_finding.R  # NEW - 3+3, CRM designs
│   ├── 12_phase2_simon.R         # NEW - Simon two-stage
│   ├── 13_phase3_power.R         # NEW - RCT power for survival
│   ├── 14_forest_plot.R          # NEW - Subgroup forest plots
│   ├── 15_swimmer_plot.R         # NEW - Treatment response
│   ├── 16_sankey.R               # NEW - Treatment flow
│   ├── 17_generate_csr.py        # NEW - Auto CSR generation
│   ├── 01_parse_crf.py           # ENHANCED - Fuzzy matching
│   └── 09_validate.py             # ENHANCED - Auto validation rules
├── schemas/
│   └── validation_rules.json      # ENHANCED - Extended validation
└── SKILL.md                       # UPDATED - All new capabilities
```

## New Scripts Specification

### 10_sample_size.R

**Purpose**: Sample size calculations for clinical trials

**Functions**:
- `calc_sample_size_binary()` - Two-group chi-square for response rates
- `calc_sample_size_continuous()` - Two-group t-test
- `calc_sample_size_survival()` - Log-rank test for time-to-event
- `calc_sensitivity_analysis()` - Vary parameters table

**Parameters** (via command-line or config):
- alpha (default: 0.05)
- power (default: 0.80)
- effect_size (OR, Cohen's d, or hazard ratio)
- allocation_ratio (default: 1)

**Output**: .docx table with sample size and sensitivity analysis

---

### 14_forest_plot.R

**Purpose**: Subgroup analysis visualization

**Workflow**:
1. Fit Cox model stratified by subgroup
2. Extract HR, 95% CI, p-value for each subgroup
3. Calculate interaction p-value
4. Generate forest plot with ggplot2/forestplot

**Parameters**:
- dataset path
- outcome variable (time, status)
- treatment variable
- subgroup variables (comma-separated)

**Output**: .eps forest plot, .csv with results

---

### 11_phase1_dose_finding.R

**Purpose**: Dose-finding designs for Phase 1

**Implementations**:
- `design_3_plus_3()` - Classical 3+3
- `design_crm()` - Continual Reassessment Method

**Parameters**:
- Dose levels
- Target toxicity rate (e.g., 0.33)
- Maximum cohort size

**Output**: MTD recommendation, dose escalations table

---

### 12_phase2_simon.R

**Purpose**: Simon two-stage design for Phase 2

**Parameters**:
- p0 (null response rate)
- p1 (alternative response rate)
- alpha, power

**Output**: Optimal/Minimax sample sizes, interim analysis boundaries

---

### 15_swimmer_plot.R

**Purpose**: Patient-level treatment response over time

**Visualizations**:
- Treatment duration bars
- Response milestones (CR, PR, SD, PD)
- Time to response
- Stem cell transplant markers

**Output**: .eps swimmer plot

---

### 16_sankey.R

**Purpose**: Treatment flow between lines of therapy

**Visualizations**:
- Sankey diagram showing patient flow
- Treatment switch points
- Response transitions

**Output**: .eps sankey diagram

---

### 17_generate_csr.py

**Purpose**: Automated Clinical Study Report generation

**Workflow**:
1. Run all analysis scripts sequentially
2. Collect outputs from Tables/ and Figures/
3. Use clinical-reports skill for ICH-E3 structure
4. Generate formatted CSR document

**Parameters**:
- Trial name
- Phase
- Primary endpoint
- Data file path

**Output**: Complete CSR in .docx

---

### Enhanced: 01_parse_crf.py

**Improvements**:
- Fuzzy matching for variable names (fuzzywuzzy)
- Auto-detect variable types (continuous, categorical, date)
- Generate validation rules JSON
- Support XLSX with complex merged cells

---

### Enhanced: 09_validate.py

**Improvements**:
- Auto-generate validation rules from CRF
- Range validation for numeric
- Category validation for categorical
- Date consistency checks
- Cross-variable validation
- Generate HTML validation report

---

## Output Specifications

| Output Type | Format | Directory |
|-------------|--------|-----------|
| Tables | .docx | Tables/ |
| Figures | .eps | Figures/ |
| Validation | .json | data/ |
| CSR | .docx | Reports/ |

## Dependencies

**R Packages** (via RMCP):
- pwr, powerSurvEpi
- survival, survminer
- table1, flextable, officer
- forestplot, ggplot2
- cmprsk
- ggsankey

**Python Packages**:
- fuzzywuzzy, python-Levenshtein
- pandas, openpyxl
- docx, reportlab

## Integration Points

| System | Integration Method |
|--------|-------------------|
| RMCP | mcp_rmcp_execute_r_analysis |
| Dropbox | Automatic folder creation |
| ClinicalTrials | MCP query for comparable trials |
| PubMed | MCP query for citations |
| clinical-reports | Skill orchestration |
