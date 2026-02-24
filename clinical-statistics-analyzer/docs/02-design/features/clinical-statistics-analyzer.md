# Design: Clinical Statistics Analyzer Skill

## Architecture Overview
The `clinical-statistics-analyzer` operates as an intelligent orchestrator within the OpenCode/Agent ecosystem. It relies heavily on the `rmcp` Model Context Protocol (MCP) server to execute precise R-based statistical functions while leveraging other specialized skills inside the agent's context (e.g., `clinicaltrials-database`, `academic-writing`) to gather constraints and finalize reports. The system is entirely prompt-driven, relying on strict markdown-based instructions to guide the agent through a robust 5-step clinical analysis pipeline.

## Components
- **Project File Management Module**: Automatically orchestrates project-specific folder structures under `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer` to systematically store raw inputs (Excel, SPSS, R data), reference CRFs, and generated outputs/reports. Also utilizes a `data/` directory within this structure for storing intermediate parsed output files.
- **Script Repository**: A dedicated `scripts/` directory bundled within the skill containing pre-made, ready-to-use scripts for CRF parsing and all standard statistical analyses (Table 1, Survival, Efficacy, Safety).
- **Planning & Extraction Module**: Parses input Data and Case Report Forms (CRFs) using `docx`/`pdf` tools and custom scripts to map dataset variables to clinical terminologies. Evaluates sample sizes via `rmcp`. Parses outputs are stored in the Dropbox `data/` folder.
- **Literature & Trial Context Module**: Integrates `clinicaltrials-database` and `pubmed-database` to query standard practices and ensure correct endpoint selection and acceptable sample sizes.
- **Biostatistical Core Module**: The execution engine that sends precise R scripts via `mcp_rmcp_execute_r_analysis` to generate Table 1 (`table1` package), perform univariate and multivariate efficacy analyses, and generate safety/toxicity summaries.
- **Subgroup & Forest Plot Module**: Executes formal subgroup interaction tests and generates highly customized forest plots (e.g., via `forestplot` or `ggplot2` in R) to visually display hazard ratios, odds ratios, and 95% CIs across baseline clinical factors.
- **Survival Analysis Module**: Specifically handles Kaplan-Meier generation (`survival` package), univariate/multivariate Cox proportional hazards models, HCT-specific endpoints (GRFS, engraftment), and competing risk models (`cmprsk` package), analyzing end points like PFS, OS, CIR, and GVHD cumulative incidence.
- **Reporting Module**: Compiles statistical outputs and visualizations (mandating **.docx** for tables and **.eps** for plots) and feeds them into the `clinical-reports` skill (alongside `academic-writing`) to generate IEEE-compliant IMRAD structures, ICH-E3 structured Clinical Study Reports (CSR), Case Reports (CARE), and regulatory SAE narratives.
- **Longitudinal Visualization Module**: Generates treatment pathway visualizations (Swimmer Plots, Sankey Diagrams, Sunburst Charts, Heatmaps) to track medication changes, treatment switching, and adherence. Leverages R packages like `ggsankey`, `patientProfilesVis`, and `ggplot2` via `rmcp`, addressing implementation challenges such as overlapping treatments and time normalization (days since start of treatment).

## Data Models
As a skill, data models represent the expected inputs and configurations:
- **Input Dataset**: Configured to parse multiple input file formats natively, explicitly accepting Excel (`readxl`), SPSS (`haven`), and native R data formats (`.Rdata`, `.rds`) directly into the analytical environment.
- **CRF Metadata**: Unstructured text from PDF/DOCX mapped by the agent into key-value pairs (`Variable_Name` -> `Clinical_Definition`).
- **Phase Target Configs**:
  - Phase 1: MTD, DLT limits, safety constraints.
  - Phase 2: Optimal/Minimax sample sizes, efficacy margins.
  - Phase 3: Superiority/Non-inferiority margins, stratified groups.
- **Output Artifacts**: Enforces publication-ready formats consisting of `.docx` for all generated tables (baseline, efficacy, safety) using packages like `flextable`/`officer`, and `.eps` format for all scalable vector plots and figures.

## API Specifications
While the skill doesn't expose a REST API, it interacts with standard MCP tools:
| Tool / Server | Action | Description |
|----------|--------|-------------|
| `rmcp` | Execute | Runs R code for `table1`, `cmprsk`, `pwr`, survival analysis, subgroup interaction tests, forest plots (`forestplot` / `ggplot2`), and longitudinal visualizations (`ggsankey`, `patientProfilesVis` for Swimmer/Sankey/Sunburst/Heatmaps). |
| `docx` / `pdf` | Parse | Extracts variable mappings from uploaded CRFs. |
| `clinical-reports` | Write | Formats outputs into ICH-E3 compliant CSRs, case reports, and standard clinical documents. |
| `clinicaltrials-database` | Query | Retrieves standard trial endpoint designs for AML/CML/MDS. |
| `pubmed-database` | Query | Retrieves literature citations to back up clinical methodologies. |

## Security Considerations
- **Data Privacy**: Ensure that the agent does not upload Patient Health Information (PHI) to external literature databases. All data processed via `rmcp` should ideally be anonymized clinical data.
- **Hallucination Prevention**: Statistical inferences must be grounded in explicit output from the R console. No LLM-generated P-values are allowed. Citations must only come from `pubmed-database`.

## Testing Strategy
- **Unit Validation**: Test the agent's ability to trigger the `mcp_rmcp_execute_r_analysis` tool with correct R syntax for `table1`.
- **Integration Validation**: Upload a dummy CRF (DOCX) and a dummy dataset (CSV); verify that the agent correctly maps variables and generates a basic survival curve without hallucinating columns.
- **E2E Validation**: Process a generalized mock clinical trial request from Planning to Academic Report output, ensuring all steps in the SKILL.md are hit in sequence.
