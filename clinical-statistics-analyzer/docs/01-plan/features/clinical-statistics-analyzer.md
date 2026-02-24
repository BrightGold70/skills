# Plan: Clinical Statistics Analyzer Skill

## Overview

A comprehensive new skill called `clinical-statistics-analyzer` designed to assist with rigorous statistical analysis for hematological clinical trials across all phases (1-3). It leverages the `rmcp` MCP server and integrates with existing capabilities like `clinicaltrials-database`, `table1` R package, and `pubmed-database` to provide an end-to-end workflow from trial design to reporting.

## Goals

- Provide Phase-Specific Clinical Trial Workflows (Phase 1 dose-finding, Phase 2 efficacy, Phase 3 RCTs).
- Automatically organize project folders to store output/products, reference Case Report Forms (CRFs), and input data under `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer`.
- Accept and parse multiple input data formats including Excel spreadsheets, SPSS data files, and native R data structures.
- Extract and map Case Report Form (CRF) data variables from DOCX and PDF documents.
- Compute required sample sizes and target populations for each trial phase.
- Perform core statistical integrations using RMCP and Python libraries.
- Automate "Table 1" generation (baseline characteristics).
- Generate structured efficacy tables (inclusive of subgroup comparisons) specific to AML, CML, MDS, and Hematopoietic Cell Transplantation (HCT).
- Evaluate specific HCT outcomes including engraftment, GVHD cumulative incidence, and GVHD-free & relapse-free survival (GRFS).
- Execute univariate and multivariate analysis for efficacy, toxicities, and primary endpoints to adjust for confounding clinical factors.
- Generate safety summary tables (≥10% AE frequency default).
- Execute comprehensive survival analysis (Kaplan-Meier, log-rank tests, 95% CIs) and competing risk models, including univariate and multivariate Cox proportional hazards models.
- Support academic reporting rigorously in accordance with STROBE/CONSORT guidelines.
- Adapt the `clinical-reports` skill to automatically generate regulatory-compliant Clinical Study Reports (ICH-E3), Serious Adverse Event (SAE) reports, and standard clinical case reports using the analyzer's outputs.
- Visualize longitudinal medication changes (treatment switching, adherence, sequential therapy) using advanced techniques like Swimmer Plots, Sankey Diagrams, Sunburst Charts, and Heatmaps.
- Enforce publication-ready output formats: `.docx` for all tabular data (Table 1, efficacy, safety) and `.eps` for all generated plots and figures.
- Provide pre-made, ready-to-use scripts housed in a `scripts/` directory for each statistical analysis (Table 1, efficacy, survival, safety) and for parsing CRFs.
- Ensure any parsed output files (e.g., from CRFs or initial data processing) are stored in a dedicated `data/` folder within the Dropbox project structure (`/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer`).

## User Stories

- As a data manager, I want to automatically parse PDF or DOCX Case Report Forms (CRFs) to map variable names to specific clinical factors for my dataset.
- As a data manager, I want the system to accept Excel, SPSS, and R data directly so I don't have to manually convert my dataset beforehand.
- As a researcher, I want all output reports, figures, and reference CRFs to be automatically organized by project in my Dropbox folder so my workspace remains tidy.
- As a biostatistician or clinical researcher, I want to calculate target populations based on primary endpoints for varying trial phases so that the trial is properly powered.
- As a researcher, I want an automated generation of baseline characteristic tables ("Table 1") so that I can easily insert it into my academic manuscript.
- As a medical writer, I want to seamlessly feed statistical outputs and visual assets into the `clinical-reports` skill to draft ICH-E3 structure Clinical Study Reports (CSR) and standardized case reports.
- As an investigator, I want to automatically compute Kaplan-Meier curves and competing risk cumulative incidence to accurately report survival and disease-free endpoints.
- As a hematology researcher, I want efficacy and safety summaries tailored specifically to endpoints in AML, CML, and MDS so that my reports meet strict domain standards.
- As a clinical data scientist, I want to visualize patient treatment pathways (e.g., first-line to second-line therapies) using Sankey diagrams or Swimmer plots to easily spot patterns of medication switching and adherence gaps.
- As a researcher preparing a manuscript, I want all tables to be exported as `.docx` and all plots as `.eps` so that they meet strict journal submission requirements without manual formatting.

## Success Criteria

- [x] SKILL.md covers target population calculations.
- [x] SKILL.md includes logic for extracting CRF metadata from DOCX/PDF files.
- [x] SKILL.md instructions for using R `table1` package.
- [x] SKILL.md guidelines for AML, CML, and MDS specific efficacy tables.
- [x] SKILL.md guidelines for safety summaries (10% frequencies).
- [x] SKILL.md workflows for survival graphs and competing risks.
- [x] SKILL.md includes logic for executing univariate and multivariate analysis across efficacy, toxicities, and survival.
- [x] SKILL.md guidelines for HCT specific outcome analysis (engraftment, GVHD, GRFS).
- [x] Integration mapped with `clinicaltrials-database` and `pubmed-database`.
- [x] Clear instructions for leveraging `rmcp` execute calls.
- [x] Integration mapped with `clinical-reports` skill for generating CSRs, SAE narratives, and CARE-compliant case reports.
- [x] SKILL.md contains logic to orchestrate file saving and automatic project folder creation inside `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer`.
- [x] SKILL.md outlines instructions and required R packages (`haven`, `readxl`) to properly load and parse `.xlsx`, `.sav`, and `.RData`/`.rds` files into the RMCP environment.
- [x] SKILL.md outlines instructions and required R packages (`ggplot2`, `ggsankey`, `patientProfilesVis`) for creating Swimmer Plots, Sankey diagrams, Sunburst charts, and Heatmaps.
- [ ] SKILL.md mandates exporting tables (Table 1, efficacy, safety) as `.docx`.
- [ ] SKILL.md mandates exporting all plots (Kaplan-Meier, Swimmer, Sankey, Forest) as `.eps`.
- [ ] Implement a `scripts/` folder containing ready-to-use scripts for statistical analysis and parsing CRFs.
- [ ] Ensure parsed output files are automatically stored in the Dropbox project's `data/` directory.

## Implementation Approach

The implementation focuses on defining the skill's capabilities, workflows, and exact tool dependencies within a `SKILL.md` file located at `~/.config/opencode/skill/clinical-statistics-analyzer/SKILL.md`. By chaining 9 existing skills, the analyzer outlines a 5-step process: Planning & Contextual Review, Baseline & Safety, Efficacy & Subgroup Analysis, Survival & Competing Risks, and Review & Academic Reporting. (Status: This implementation approach was executed, and the SKILL.md has been generated).

## Risks

| Risk | Impact | Mitigation |
| ------------- | -------- | ------------------------------------------------------------- |
| Inaccurate usage of `rmcp` | High | Specify the exact use of `mcp_rmcp_execute_r_analysis` and explicitly mention the R packages to be run (`table1`, `cmprsk`, `survival`, `pwr`). |
| Hallucinated citations in reports | High | Enforce stringent dependence on the `pubmed-database` and explicitly forbid generating citations from LLM memory. |
| Misinterpreting endpoints across diseases | Moderate | Explicitly spell out the expectations per disease (e.g., MRD for AML, MMR for CML) inside the `SKILL.md`. |

## Timeline

- **Plan Generation**: Immediate.
- **Implementation (SKILL.md creation)**: Complete.
- **Validation**: User review of document.
