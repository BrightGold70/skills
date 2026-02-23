# PDCA Design: Hematology Clinical Analysis Skill Upgrade

## 1. System Architecture

The upgrade involves modifying the `SKILL.md` to include specialized Hematology knowledge and R-based workflows. It will also add external reference files and scripts to maintain modularity.

## 2. Component Design

### 2.1 SKILL.md Updates

- **Metadata**: Add `hematology` to tags.
- **Overview**: Add text about bone marrow transplant and leukemia analysis.
- **rmcp Tool Table**: Expand with `cmprsk`, `mstate`, and `gsDesign`.
- **Synergy Patterns**: A new section detailing interaction with `statistical-analysis` for pre-analysis (assumptions) and post-analysis (APA reporting).

### 2.2 New References

- `references/hematology_response_criteria.md`: Markdown tables for IWG (Leukemia/Lymphoma/Myeloma) and ELN (AML) criteria.

### 2.3 New Scripts

- `scripts/example_hematology_survival.R`: R script demonstrating:
  - Survival data preparation.
  - Competing risk analysis (Relapse vs DWR).
  - Subgroup forest plot generation.

## 3. Data Model / API

- **MCP Integration**: Uses `rmcp` standard tools via `skill_mcp`.
- **Cross-Skill API**: Uses `scripts/assumption_checks.py` from the `statistical-analysis` skill when analyzing datasets.

## 4. UI/UX Design (Agent Interaction)

- The agent will first suggest checking assumptions via `statistical-analysis`.
- The agent will use `rmcp` for complex survival tasks.
- The agent will suggest `scientific-visualization` for Swimmer/Waterfall plots.

## 5. Security & Performance

- De-identification of patient data is emphasized (HIPAA).
- R script execution is handled via `rmcp` MCP server which manages session safety.
