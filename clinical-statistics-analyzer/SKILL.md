---
name: clinical-statistics-analyzer
description: Comprehensive statistical analysis skill for hematological clinical trials (Phases 1-3). Integrates RMCP for R-based computing, Python statistical libraries, academic writing standards, biometric sequence analysis, pubmed-database, and clinicaltrials-database to provide an end-to-end workflow from trial design to reporting.
---

# Clinical Statistics Analyzer For Hematology Trials

This skill orchestrates multiple specialized sub-skills and the R MCP server (`rmcp`) to perform rigorous, publication-ready statistical analyses for clinical trials in hematology.

## Path Structure (IMPORTANT)

- **Skill Scripts**: `/Users/kimhawk/.config/opencode/skill/clinical-statistics-analyzer/scripts/`
- **Output/Products**: `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer/`

When working with this skill:
1. All Python/R scripts should be in the skill's `scripts/` folder
2. All outputs (parsed data, reports, tables, figures) should be saved to the Dropbox `Paper/Clinical_statistics_analyzer/` folder

## Core Capabilities

1. **Baseline Characteristics ("Table 1")**:
   - Utilizes the R package `table1` via RMCP to generate standard demographic and clinical baseline characteristic tables, comparing across treatment arms.

2. **Efficacy Analysis & Tables**:
   - Generates structured efficacy tables comparing treatment arms and subgroups, including p-values and 95% Confidence Intervals (CIs).
   - Context-aware analysis customized for hematological malignancies:
     - **AML**: CR/PR rates, MRD negativity status.
     - **CML**: Major molecular response (MMR), complete cytogenetic response (CCyR).
     - **MDS**: Hematologic improvement (HI), transfusion independence.
     - **HCT**: Engraftment analysis, GVHD cumulative incidence, GVHD-free & relapse-free survival (GRFS/GFRFS).
   - Generate automated subgroup comparisons by mapped variables (e.g., genetic mutations evaluated from CRF data).
   - Create detailed publication-ready Forest Plots visualizing subgroup effects (Odds Ratios, Hazard Ratios, 95% CIs, interaction p-values) using R libraries like `forestplot` or `ggplot2` via `rmcp`.

3. **Safety Summaries**:
   - Generates adverse event (AE) and toxicity tables based on Common Terminology Criteria for Adverse Events (CTCAE).
   - Evaluates specific toxicities using univariate and multivariate logistic regression analysis to adjust for confounding clinical factors and baselines.
   - Defaults to reporting events with >=10% frequency, with capabilities to adjust the threshold as specified.

4. **Survival & Time-to-Event Analysis**:
   - **Survival Graphs**: Generates Kaplan-Meier plots with integrated log-rank test p-values and 95% CIs. Endpoints include Overall Survival (OS), Progression-Free Survival (PFS), Leukemia-Free Survival (LFS), Event-Free Survival (EFS), and GVHD-free & relapse-free survival (GRFS).
   - **Cox Models**: Performs univariate and multivariate Cox proportional hazards models to control for confounding variables on primary survival outcomes.
   - **Competing Risks**: Analyzes cumulative incidence (e.g., relapse vs. non-relapse mortality, GVHD cumulative incidence) using R packages like `cmprsk` via `mcp_rmcp_execute_r_analysis`.

5. **Target Population & Sample Size Calculation**:
   - Computes required sample sizes powered by specific endpoints for each trial phase using R (`pwr` package, simulation) or Python calculation tools.
   - Adjusts for expected dropout rates and specific hematological effect sizes.

6. **Case Report Form (CRF) Recognition & Mapping**:
   - Extracts clinical factor metadata and variable structures from CRFs (often in DOCX or PDF format) using the `docx` or `pdf` skills.
   - Maps raw dataset columns to their specific clinical/hematological definitions as dictated by the trial's CRF, ensuring accurate subgroup analysis and table generation.

7. **Protocol/CRF Validation Framework**:
   - Parse clinical trial protocols (DOCX/PDF) to extract endpoints, treatment arms, sample size
   - Parse CRF specifications (DOCX/XLSX) to extract variable definitions, valid ranges
   - Validate patient data against protocol and CRF specifications
   - Generate validation reports (JSON/HTML)

8. **Trial Phase Specific Workflows**:
   - **Phase 1**: Dose finding (3+3, CRM), Safety/Toxicity analysis, Maximum Tolerated Dose (MTD), target population appropriate for safety bounds.
   - **Phase 2**: Efficacy, Simon's two-stage designs (Optimal & Minimax sample sizes), biomarker associations.
   - **Phase 3**: Randomized Controlled Trials (RCTs), superiority/non-inferiority margins, stratified randomization, power analysis for time-to-event endpoints.

9. **Longitudinal Visualization**:
   - Generates treatment pathway visualizations (Swimmer Plots, Sankey Diagrams, Sunburst Charts, Heatmaps) to track medication changes, treatment switching, and adherence.
   - Leverages R packages like `ggsankey`, `patientProfilesVis`, and `ggplot2` via `rmcp`, addressing implementation challenges such as overlapping treatments and time normalization (days since start of treatment).

10. **Bundled Analysis Scripts**:
    - All scripts are located in: `~/.config/opencode/skill/clinical-statistics-analyzer/scripts/`
    - **Protocol/CRF Parsing Scripts**:
      - `06_parse_protocol.py` - Parse clinical trial protocol documents (DOCX/PDF)
      - `07_parse_crf_spec.py` - Parse CRF specification documents (DOCX/XLSX)
      - `08_parse_data.py` - Parse patient data files (XLSX/CSV/SPSS/JSON)
      - `09_validate.py` - Validate data against protocol/CRF specifications
    - **Statistical Analysis Scripts**:
      - `01_parse_crf.py` - CRF parsing
      - `02_table1.R` - Table 1 Generation
      - `03_efficacy.R` - Efficacy Analysis
      - `04_survival.R` - Survival Analysis
      - `05_safety.R` - Safety Analysis
      - `generate_mock.py` - Mock Data Generation

## Integrated Skills & Dependencies

To execute tasks under this skill, coordinate the following dependencies:

- **R MCP Server (`rmcp`)**: Primary engine for robust statistical tests and validation. Use `mcp_rmcp_execute_r_analysis` to run specific R packages like `table1`, `survival`, and `cmprsk`.
- **Clinical Study Analysis (`clinical-study-analysis`)**: Provides domain context on trial endpoints and compliance (CONSORT for RCTs, STROBE for observational).
- **ClinicalTrials Database (`clinicaltrials-database`)**: Query ClinicalTrials.gov to analyze statistical designs, primary endpoints, and characteristics of comparable hematology trials.
- **PubMed Database (`pubmed-database`)**: Performs deep literature searches using E-utilities across MEDLINE for comparable trials and hallucination-proof citations.
- **DOCX / PDF Skills (`docx`, `pdf`)**: Used to parse Case Report Forms (CRFs) for automatic data variable recognition.
- **Academic Writing Skills (`academic-writing`, `academic-research-writer`)**: Ensure outputs are formatted correctly in IEEE reference style for final reports in an IMRAD structure.
- **Biopython (`biopython`)**: Parses FASTA/PDB or explores bioinformatics data when clinical trial patients have sequence data.
- **Clinical Reports (`clinical-reports`)**: Formats outputs and visualizations into ICH-E3 compliant Clinical Study Reports (CSR), Case Reports (CARE guidelines), and regulatory Serious Adverse Event (SAE) narratives.

## Unified Workflow

When asked to analyze clinical trial data, follow these steps sequentially:

### 1. Planning, Contextual Review & Project Initialization

- **Project Folder Setup**: Automatically orchestrate and create a project-specific folder structure under `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer` to systematically store raw inputs, reference CRFs, and generated outputs/reports.
- **Data Import**: Load the dataset into the analytical environment. Natively parse multiple formats: use `readxl` for Excel (`.xlsx`), `haven` for SPSS (`.sav`), or base R functions for R data (`.RData`/`.rds`) via RMCP.
- Understand the trial phase, endpoints, and data structure.
- If provided with a Case Report Form (CRF) in DOCX or PDF format, execute the bundled `scripts/01_parse_crf.py` via Python or standard terminal to extract data variable definitions. Save the mapping (`crf_mapping.json`) to the Dropbox project's `data/` folder (`/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer/data/`). Map the raw dataset to the clinical factors for accurate analysis.
- Construct queries using **clinicaltrials-database** and **pubmed-database** to review comparable trials, ensuring the planned statistical methodologies align with current hematology standards.
- Evaluate the required target population: perform formal sample size calculations (e.g., via R's `pwr` or custom survival design packages in RMCP) powered to the primary endpoint depending on the specific trial Phase (1, 2, or 3).

### 2. Baseline & Safety Analysis

- **Table 1**: Use `mcp_rmcp_execute_r_analysis` or standard terminal execution to run the bundled `scripts/02_table1.R` script on the dataset to create the baseline characteristics table. The script will save the `.docx` to the Dropbox `Tables/` folder.
- **Safety Sumary**: Run the `scripts/05_safety.R` script to calculate AE frequencies and create a summary table reporting events occurring in >=10% of patients (or as requested). It saves a `.docx` summary in the Dropbox `Tables/` folder.

### 3. Efficacy & Subgroup Analysis

- Use the bundled `scripts/03_efficacy.R` script to perform regression and standard efficacy outputs.
- Calculate response rates (CR, PR, HI, MMR) based on the disease context (AML, CML, MDS).
- Perform specific analysis for HCT outcomes (e.g., engraftment kinetics).
- Perform univariate and multivariate regression (logistic or custom GLM) to evaluate primary efficacy endpoints and adjusting for baseline subgroups.
- Automate deep subgroup analysis based on established clinical factors mapped during Phase 1.
- Perform formal interaction testing between subgroups and treatment arms.
- Generate standard Forest Plots via R (`forestplot`, `ggplot2`) demonstrating Hazard Ratios (HR) or Odds Ratios (OR) with exact 95% CIs and interaction P-values.
- Generate efficacy tables detailing treatment effects, subgroup comparisons, p-values, and 95% CIs. Use `mcp_rmcp_logistic_regression` or custom R code for odds ratios/relative risks.

### 4. Survival & Competing Risks

- **Survival**: Run the bundled `scripts/04_survival.R` script to produce Kaplan-Meier survival curves using `survival` and `survminer` packages. Explicitly include 95% confidence intervals (`conf.int = TRUE`) and log-rank p-values (`pval = TRUE`) directly on the plots, saved to the Dropbox `Figures/` directory. Use for endpoints like OS, PFS, or GRFS.
- If analyzing relapse, GVHD, or specific events with competing mortality, execute competing risk analyses using R's `cmprsk` to plot cumulative incidence functions.

### 5. Review, Reporting & Longitudinal Visualization

- Evaluate statistical output (Akaike/Bayesian info criteria, residual analysis).
- **Longitudinal Visualization**: Create Swimmer Plots, Sankey Diagrams, Sunburst Charts, or Heatmaps to visualize patient treatment pathways over time (e.g., first-line to second-line therapies) using `ggsankey` or `patientProfilesVis` via `mcp_rmcp_execute_r_analysis`. Save these visualizations directly to the Dropbox project folder as `.eps` files.
- **Reporting**: Compile statistical outputs and visualizations (mandating **.docx** for tables and **.eps** for plots) and feed them into the **clinical-reports** skill to generate ICH-E3 structured Clinical Study Reports (CSR), Case Reports (CARE), SAE narratives, or standard clinical documents. Use **academic-writing** guidelines to ensure outputs are formatted correctly in IEEE reference style for final IMRAD reports.
- Ensure all references are retrieved using real querying rather than hallucinations.

## Key Guidelines

- **Always Validate**: Clinical trial analysis demands accuracy. Reject analyses that fail assumption checks (e.g., Cox proportional hazards violation) without applying appropriate corrections.
- **Disease-Specific Logic**: Ensure interpretation matches the disease (e.g., MRD negativity is highly relevant in AML, molecular response in CML).
- **Explicit R Code**: For advanced features (`table1`, competing risks, complex survival plots), always utilize `mcp_rmcp_execute_r_analysis` with appropriate R syntax.
- **Output Artifact Formatting**: ALWAYS export all generated tabular data (Table 1, Efficacy, Safety summaries) as **.docx** files using R packages like `flextable` and `officer`. ALWAYS export all generated plots and figures (Kaplan-Meier, Swimmer, Sankey, Forest plots) as **.eps** format using `ggsave(device="eps")` or `postscript()`.
