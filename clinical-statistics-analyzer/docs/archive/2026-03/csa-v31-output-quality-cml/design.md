# CSA v3.1: Output Quality & CML Expansion — Design Document

> **Summary**: Detailed module interfaces, data flows, and config schemas for journal templates, mini-CSR report, PDF/HTML output, and 4 new CML R scripts
>
> **Project**: clinical-statistics-analyzer
> **Version**: 3.1.0 (target)
> **Author**: Claude
> **Date**: 2026-03-04
> **Status**: Draft
> **Planning Doc**: [csa-v31-output-quality-cml.plan.md](../01-plan/features/csa-v31-output-quality-cml.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **Publication-ready output**: Tables styled per target journal (NEJM, Lancet, Blood, JCO) without manual post-processing
2. **Unified reporting**: Single mini-CSR document aggregating all analysis outputs into ICH-E3 lite structure
3. **Format flexibility**: PDF and interactive HTML alongside existing .docx/.eps
4. **CML gap closure**: 4 new R scripts covering ELN milestones, BCR-ABL waterfall, resistance mutations, and deep TFR analysis
5. **Backward compatibility**: All existing 39 tests and CLI commands continue to work unchanged

### 1.2 Design Principles

- **Config-driven**: All journal styles, section orders, and thresholds in JSON — no hardcoded styling in R/Python code
- **Additive-only**: New modules and scripts; no modifications to existing transformer or orchestrator core logic
- **Convention-consistent**: New R scripts follow `NN_description.R` naming; new Python modules follow existing `crf_pipeline/` patterns
- **Independent outputs**: Each output format (docx, pdf, html) is independently toggleable via CLI flags

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI (cli.py)                                 │
│  run-analysis <data> -d cml [--journal blood] [--pdf] [--html]      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  AnalysisOrchestrator (orchestrator.py)              │
│                                                                     │
│  1. transform()  ──── existing transformers (unchanged)             │
│  2. run_scripts() ── R scripts (02-05 + NEW 26-29 for CML)         │
│  3. post_process() ── NEW: journal themes + PDF + HTML + mini-CSR   │
└───────────────┬──────────────┬───────────┬──────────────────────────┘
                │              │           │
    ┌───────────▼──┐  ┌───────▼────┐  ┌───▼──────────────┐
    │ JournalThemes │  │ PDFExporter │  │ ReportGenerator  │
    │ (journal_     │  │ (pdf_       │  │ (report_         │
    │  themes.py)   │  │  exporter.py│  │  generator.py)   │
    └───────┬───────┘  └──────┬─────┘  └────────┬─────────┘
            │                 │                  │
            ▼                 ▼                  ▼
    journal_templates   .pdf files         Mini-CSR .docx
    .json config        (tables+figs)      (ICH-E3 lite)
                                                 │
                                      ┌──────────▼──────────┐
                                      │  HTMLExporter        │
                                      │  (html_exporter.py)  │
                                      └──────────┬──────────┘
                                                 ▼
                                        Dashboard .html
                                        (Plotly + DT)
```

### 2.2 Data Flow

```
Transformed CSV
    │
    ├─→ R scripts (02-05, 22-23, NEW 26-29)
    │       │
    │       ├─→ .docx tables (Tables/)
    │       └─→ .eps figures (Figures/)
    │
    └─→ post_process() [NEW step in orchestrator]
            │
            ├─→ JournalThemes.apply(docx_files, journal)
            │       └─→ styled .docx files (in-place or Tables/journal/)
            │
            ├─→ PDFExporter.export(docx_files, eps_files)
            │       └─→ .pdf files (Tables/pdf/, Figures/pdf/)
            │
            ├─→ ReportGenerator.generate(all_outputs, disease)
            │       └─→ Reports/Mini_CSR_{disease}.docx
            │
            └─→ HTMLExporter.export(csv_path, results)
                    └─→ Reports/Dashboard_{disease}.html
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| JournalThemes | `journal_templates.json` | Style definitions per journal |
| PDFExporter | R `rmarkdown` package | PDF rendering via pandoc/LaTeX |
| ReportGenerator | `python-docx` | .docx assembly from components |
| HTMLExporter | R `rmarkdown`, `plotly`, `DT` | Self-contained HTML generation |
| Scripts 26-29 | `ggplot2`, `survival`, `cmprsk`, `flextable`, `officer` | R computation and output |
| Orchestrator | All above | Wiring and coordination |

---

## 3. Module Specifications

### 3.1 JournalThemes (`scripts/crf_pipeline/journal_themes.py`)

**Purpose**: Load journal-specific `flextable` styling and apply to generated .docx tables via an R helper script.

```python
class JournalThemes:
    """Applies journal-specific styling to flextable .docx outputs."""

    def __init__(self, config_path: str = None):
        """Load journal_templates.json.

        Args:
            config_path: Path to journal_templates.json. Default: config/journal_templates.json
        """

    def get_theme(self, journal: str) -> Dict[str, Any]:
        """Get theme config for a journal (nejm, lancet, blood, jco).

        Returns:
            Dict with font_family, font_size, header_bold, border_style,
            p_value_format, ci_format, footnote_style, etc.

        Raises:
            ValueError: If journal name is unknown.
        """

    def apply(self, docx_dir: str, journal: str, output_dir: str = None) -> List[str]:
        """Apply journal theme to all .docx files in directory.

        Generates a temporary R script that re-renders flextable objects
        with the specified theme, then runs via subprocess.

        Args:
            docx_dir: Directory containing .docx tables.
            journal: Journal name (nejm, lancet, blood, jco).
            output_dir: Output directory (default: same as docx_dir).

        Returns:
            List of styled .docx file paths.
        """

    @property
    def available_journals(self) -> List[str]:
        """List of configured journal names."""
```

**Strategy**: Rather than modifying existing R scripts, JournalThemes generates a small R script that:
1. Reads the existing .docx (which contains flextable output)
2. Applies theme overrides (font, border, formatting) using `flextable::set_flextable_defaults()` and `officer` read/write
3. Saves the styled .docx

This keeps existing R scripts untouched and makes journal theming a pure post-processing step.

### 3.2 PDFExporter (`scripts/crf_pipeline/pdf_exporter.py`)

**Purpose**: Convert .docx tables and .eps figures to PDF format.

```python
class PDFExporter:
    """Converts analysis outputs to PDF format."""

    def __init__(self, output_dir: str):
        """
        Args:
            output_dir: Base output directory (CSA_OUTPUT_DIR).
        """

    def export_tables(self, docx_dir: str) -> List[str]:
        """Convert .docx tables to .pdf using LibreOffice or pandoc.

        Strategy: Try `libreoffice --headless --convert-to pdf` first,
        fallback to pandoc if available. Logs warning if neither available.

        Returns:
            List of generated .pdf paths.
        """

    def export_figures(self, eps_dir: str) -> List[str]:
        """Convert .eps figures to .pdf using R's grDevices or ghostscript.

        Strategy: Generate small R script: `setEPS(); pdf(...); dev.off()`
        or use `gs` command line.

        Returns:
            List of generated .pdf paths.
        """

    def export_all(self, tables_dir: str, figures_dir: str) -> Dict[str, List[str]]:
        """Export all tables and figures to PDF.

        Returns:
            {"tables": [...pdf paths], "figures": [...pdf paths]}
        """
```

### 3.3 ReportGenerator (`scripts/crf_pipeline/report_generator.py`)

**Purpose**: Assemble all analysis outputs into a unified mini-CSR document following ICH-E3 lite structure.

```python
@dataclass
class CSRSection:
    """A section in the mini-CSR document."""
    title: str
    level: int  # heading level (1-3)
    narrative: str  # placeholder or auto-generated text
    tables: List[str]  # paths to .docx table files to embed
    figures: List[str]  # paths to .eps/.png figure files to embed


class ReportGenerator:
    """Generates ICH-E3 lite mini-CSR from analysis outputs."""

    ICH_E3_SECTIONS = [
        "title_page",
        "synopsis",
        "demographics",       # Table 1
        "efficacy",           # Efficacy table + forest plot
        "safety",             # Safety summary table
        "survival",           # KM curves + Cox tables
        "disease_specific",   # Disease-specific analyses (ELN risk, TFR, etc.)
        "conclusions",
    ]

    def __init__(self, output_dir: str, disease: str):
        """
        Args:
            output_dir: Base output directory (CSA_OUTPUT_DIR).
            disease: Disease type for disease-specific section routing.
        """

    def collect_outputs(self, script_results: List[ScriptResult]) -> Dict[str, List[str]]:
        """Map script outputs to ICH-E3 sections.

        Mapping rules:
            02_table1 → demographics
            03_efficacy → efficacy
            04_survival → survival
            05_safety → safety
            20-29 (disease-specific) → disease_specific

        Returns:
            Dict mapping section name to list of output file paths.
        """

    def generate(
        self,
        script_results: List[ScriptResult],
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Generate the mini-CSR .docx document.

        Args:
            script_results: Results from orchestrator.run_scripts().
            metadata: Optional dict with study_title, protocol_number, etc.

        Returns:
            Path to the generated mini-CSR .docx file.

        Process:
            1. Create Document with title page
            2. For each ICH-E3 section:
               a. Add heading
               b. Add narrative placeholder text
               c. Embed tables (read .docx tables, copy content)
               d. Embed figures (convert .eps to .png, insert image)
            3. Save to Reports/Mini_CSR_{disease}.docx
        """

    def _embed_table(self, doc: Document, docx_path: str) -> None:
        """Read a .docx table and copy its content into the CSR document."""

    def _embed_figure(self, doc: Document, eps_path: str, caption: str) -> None:
        """Convert .eps to .png and embed in document with caption."""

    def _generate_narrative(self, section: str, disease: str) -> str:
        """Generate placeholder narrative for a section.

        Returns template text like:
        '[NARRATIVE: Describe the baseline characteristics of the study population.
         Include median age, sex distribution, and key disease features.]'
        """
```

**ICH-E3 Lite Section Mapping**:

| ICH-E3 Section | Source Scripts | Content |
|----------------|---------------|---------|
| Title Page | metadata | Study title, protocol number, date, disease |
| Synopsis | all | One-paragraph auto-summary (patient count, disease, scripts run) |
| Demographics | 02_table1 | Table 1 embedded |
| Efficacy | 03_efficacy, 14_forest | Efficacy table + forest plot |
| Safety | 05_safety | Safety summary table |
| Survival | 04_survival | KM curves + Cox model results |
| Disease-Specific | 20-29 | AML: ELN risk + composite; CML: TFR + scores + milestones + waterfall + resistance; HCT: GVHD |
| Conclusions | — | Narrative placeholder |

### 3.4 HTMLExporter (`scripts/crf_pipeline/html_exporter.py`)

**Purpose**: Generate self-contained interactive HTML dashboards with Plotly KM curves and DT filterable tables.

```python
class HTMLExporter:
    """Generates interactive HTML dashboard from analysis outputs."""

    def __init__(self, output_dir: str, disease: str):
        """
        Args:
            output_dir: Base output directory.
            disease: Disease type for dashboard customization.
        """

    def generate(self, csv_path: str, script_results: List[ScriptResult]) -> str:
        """Generate self-contained HTML dashboard.

        Creates an R Markdown document (.Rmd) with:
        - Plotly interactive KM curves (zoomable, hover details)
        - DT filterable baseline characteristics table
        - DT filterable safety table
        - Summary statistics cards

        Then renders via `rmarkdown::render()` to self-contained HTML.

        Args:
            csv_path: Path to transformed R-ready CSV.
            script_results: Results for metadata (which scripts ran).

        Returns:
            Path to generated Dashboard_{disease}.html file.
        """

    def _create_rmd_template(self, csv_path: str) -> str:
        """Generate the .Rmd template with embedded R code chunks.

        Returns:
            Path to temporary .Rmd file.
        """

    def _render_html(self, rmd_path: str) -> str:
        """Render .Rmd to self-contained HTML via subprocess Rscript.

        Returns:
            Path to generated .html file.
        """
```

---

## 4. New CML R Scripts

### 4.1 `26_cml_eln_milestones.R`

**Purpose**: Generate ELN 2020 milestone response classification table at 3, 6, 12, and 18 months.

**CLI**: `Rscript 26_cml_eln_milestones.R <dataset> [--window 1.5]`

**Input columns required**:
| Column | Type | Description |
|--------|------|-------------|
| `Patient_ID` | character | Patient identifier |
| `Treatment` | character | First-line TKI |
| `bcr_abl_3m` | numeric | BCR-ABL % IS at 3 months |
| `bcr_abl_6m` | numeric | BCR-ABL % IS at 6 months |
| `bcr_abl_12m` | numeric | BCR-ABL % IS at 12 months |
| `bcr_abl_18m` | numeric | BCR-ABL % IS at 18 months |

**ELN 2020 Milestone Thresholds**:

| Timepoint | Optimal | Warning | Failure |
|-----------|---------|---------|---------|
| 3 months | BCR-ABL ≤10% | BCR-ABL >10% | No CHR or Ph+ >95% |
| 6 months | BCR-ABL ≤1% | BCR-ABL 1-10% | BCR-ABL >10% |
| 12 months | BCR-ABL ≤0.1% | BCR-ABL 0.1-1% | BCR-ABL >1% |
| 18 months | BCR-ABL ≤0.01% | BCR-ABL 0.01-0.1% | BCR-ABL >0.1% |

**Window**: ±1.5 months (configurable via `--window` arg). Measurements within the window are accepted for the timepoint.

**Outputs**:
- `Tables/CML_ELN2020_Milestones.docx` — Milestone classification table (N and % per treatment arm, per timepoint, per category)
- `Figures/CML_ELN2020_Milestones_Heatmap.eps` — Heatmap of response categories across timepoints

**R packages**: `flextable`, `officer`, `ggplot2`, `dplyr`, `tidyr`

### 4.2 `27_cml_waterfall.R`

**Purpose**: Individual patient BCR-ABL response depth waterfall plot with log-scale reduction from baseline.

**CLI**: `Rscript 27_cml_waterfall.R <dataset> [--timepoint 12]`

**Input columns required**:
| Column | Type | Description |
|--------|------|-------------|
| `Patient_ID` | character | Patient identifier |
| `Treatment` | character | First-line TKI |
| `bcr_abl_baseline` | numeric | BCR-ABL % IS at baseline |
| `bcr_abl_3m` through `bcr_abl_24m` | numeric | BCR-ABL % IS at timepoints |

**Logic**:
1. Calculate log10 reduction: `log10(bcr_abl_timepoint / bcr_abl_baseline)`
2. Sort patients by response depth (best to worst)
3. Color bars by treatment arm
4. Add horizontal lines for MMR (-3 log), MR4 (-4 log), MR4.5 (-4.5 log) thresholds

**Outputs**:
- `Figures/CML_Waterfall_BCR_ABL.eps` — Waterfall plot
- `Tables/CML_Response_Depth.docx` — Summary table of response categories by treatment arm

**R packages**: `ggplot2`, `dplyr`, `flextable`, `officer`

### 4.3 `28_cml_resistance.R`

**Purpose**: ABL1 kinase domain mutation tracking and resistance timeline visualization.

**CLI**: `Rscript 28_cml_resistance.R <dataset>`

**Input columns required**:
| Column | Type | Description |
|--------|------|-------------|
| `Patient_ID` | character | Patient identifier |
| `Treatment` | character | TKI at time of resistance |
| `resistance_mutation` | character | ABL1 mutation (e.g., T315I, E255K) |
| `resistance_date` | Date | Date mutation detected |
| `Treatment_Start_Date` | Date | TKI start date |

**Logic**:
1. Calculate time-to-resistance from treatment start
2. Tabulate mutation frequencies and TKI associations
3. Generate timeline plot (swimmer-style) with mutation events marked
4. Highlight clinically significant mutations (T315I, compound mutations)

**Outputs**:
- `Tables/CML_Resistance_Mutations.docx` — Mutation frequency table by TKI
- `Figures/CML_Resistance_Timeline.eps` — Patient timeline with mutation events

**R packages**: `ggplot2`, `dplyr`, `flextable`, `officer`, `lubridate`

### 4.4 `29_cml_tfr_deep.R`

**Purpose**: Deep TFR analysis — molecular relapse kinetics, sustained MR4 duration, loss-of-MMR cumulative incidence.

**CLI**: `Rscript 29_cml_tfr_deep.R <dataset>`

**Input columns required**:
| Column | Type | Description |
|--------|------|-------------|
| `Patient_ID` | character | Patient identifier |
| `tfr_start_date` | Date | Date of TKI discontinuation |
| `mmr_loss_date` | Date | Date of MMR loss (if occurred) |
| `mr4_duration_months` | numeric | Duration of sustained MR4 before TFR |
| `bcr_abl_post_tfr_*` | numeric | Serial BCR-ABL measurements post-TFR |
| `tfr_restart_date` | Date | Date of TKI restart (if applicable) |
| `tfr_restart_reason` | character | Reason for restart |

**Logic**:
1. **Molecular relapse kinetics**: Plot individual BCR-ABL trajectories post-TFR over time
2. **Sustained MR4 duration**: KM curve for time from TFR to MMR loss (censored at last follow-up)
3. **Loss-of-MMR cumulative incidence**: Fine-Gray competing risk (death as competing event)
4. **Predictors**: Cox model for MMR loss including MR4 duration, TKI type, Sokal risk

**Outputs**:
- `Figures/CML_TFR_Relapse_Kinetics.eps` — Spaghetti plot of BCR-ABL trajectories post-TFR
- `Figures/CML_TFR_MMR_Loss_KM.eps` — KM curve for time to MMR loss
- `Figures/CML_TFR_MMR_Loss_CI.eps` — Cumulative incidence with competing risks
- `Tables/CML_TFR_Deep_Analysis.docx` — Summary table with predictors of MMR loss

**R packages**: `survival`, `survminer`, `cmprsk`, `ggplot2`, `dplyr`, `flextable`, `officer`

---

## 5. Configuration Schemas

### 5.1 `config/journal_templates.json`

```json
{
  "version": "1.0",
  "templates": {
    "nejm": {
      "display_name": "New England Journal of Medicine",
      "font_family": "Arial",
      "font_size": 8,
      "header_font_size": 8,
      "header_bold": true,
      "header_bg_color": "#FFFFFF",
      "header_border_bottom": true,
      "body_border": "none",
      "table_border_top": true,
      "table_border_bottom": true,
      "p_value_format": "< 0.001",
      "p_value_digits": 3,
      "ci_format": "({lower} to {upper})",
      "ci_digits": 2,
      "footnote_style": "symbols",
      "decimal_separator": ".",
      "thousands_separator": ","
    },
    "lancet": {
      "display_name": "The Lancet",
      "font_family": "Times New Roman",
      "font_size": 9,
      "header_font_size": 9,
      "header_bold": true,
      "header_bg_color": "#FFFFFF",
      "header_border_bottom": true,
      "body_border": "horizontal_only",
      "table_border_top": true,
      "table_border_bottom": true,
      "p_value_format": "< 0.0001",
      "p_value_digits": 4,
      "ci_format": "{lower}\u2013{upper}",
      "ci_digits": 1,
      "footnote_style": "symbols",
      "decimal_separator": "\u00b7",
      "thousands_separator": " "
    },
    "blood": {
      "display_name": "Blood (ASH)",
      "font_family": "Arial",
      "font_size": 9,
      "header_font_size": 9,
      "header_bold": true,
      "header_bg_color": "#D9E2F3",
      "header_border_bottom": true,
      "body_border": "horizontal_only",
      "table_border_top": true,
      "table_border_bottom": true,
      "p_value_format": "< .001",
      "p_value_digits": 3,
      "ci_format": "({lower}-{upper})",
      "ci_digits": 1,
      "footnote_style": "numbers",
      "decimal_separator": ".",
      "thousands_separator": ","
    },
    "jco": {
      "display_name": "Journal of Clinical Oncology (ASCO)",
      "font_family": "Arial",
      "font_size": 8,
      "header_font_size": 8,
      "header_bold": true,
      "header_bg_color": "#F2F2F2",
      "header_border_bottom": true,
      "body_border": "none",
      "table_border_top": true,
      "table_border_bottom": true,
      "p_value_format": "< .001",
      "p_value_digits": 3,
      "ci_format": "{lower} to {upper}",
      "ci_digits": 2,
      "footnote_style": "symbols",
      "decimal_separator": ".",
      "thousands_separator": ","
    }
  }
}
```

### 5.2 CML Config Additions (`config/cml_fields.json`)

New `column_mapping` entries to add:

```json
{
  "column_mapping": {
    "...existing mappings...": "...",
    "bcr_abl_baseline": "bcr_abl_baseline",
    "bcr_abl_3m": "bcr_abl_3m",
    "bcr_abl_6m": "bcr_abl_6m",
    "bcr_abl_12m": "bcr_abl_12m",
    "bcr_abl_18m": "bcr_abl_18m",
    "bcr_abl_24m": "bcr_abl_24m",
    "resistance_mutation": "resistance_mutation",
    "resistance_date": "resistance_date",
    "tfr_start_date": "tfr_start_date",
    "mmr_loss_date": "mmr_loss_date",
    "mr4_duration_months": "mr4_duration_months",
    "tfr_restart_date": "tfr_restart_date",
    "tfr_restart_reason": "tfr_restart_reason"
  }
}
```

Note: Most CML molecular variables keep their CRF names since R scripts expect them as-is. Only variables that need renaming for R convention consistency are mapped.

### 5.3 Analysis Profiles Additions (`config/analysis_profiles.json`)

New CML script entries to append after `23_cml_scores.R`:

```json
{
  "name": "26_cml_eln_milestones.R",
  "args": ["{dataset}"],
  "required": false,
  "expected_outputs": ["CML_ELN2020_Milestones.docx", "CML_ELN2020_Milestones_Heatmap.eps"],
  "description": "CML ELN 2020 milestone response classification"
},
{
  "name": "27_cml_waterfall.R",
  "args": ["{dataset}"],
  "required": false,
  "expected_outputs": ["CML_Waterfall_BCR_ABL.eps", "CML_Response_Depth.docx"],
  "description": "BCR-ABL response depth waterfall plot"
},
{
  "name": "28_cml_resistance.R",
  "args": ["{dataset}"],
  "required": false,
  "expected_outputs": ["CML_Resistance_Mutations.docx", "CML_Resistance_Timeline.eps"],
  "description": "ABL1 kinase domain resistance mutation tracking"
},
{
  "name": "29_cml_tfr_deep.R",
  "args": ["{dataset}"],
  "required": false,
  "expected_outputs": [
    "CML_TFR_Relapse_Kinetics.eps",
    "CML_TFR_MMR_Loss_KM.eps",
    "CML_TFR_MMR_Loss_CI.eps",
    "CML_TFR_Deep_Analysis.docx"
  ],
  "description": "Deep TFR analysis with molecular relapse kinetics"
}
```

---

## 6. Orchestrator Modifications

### 6.1 New `post_process()` Method

Add to `AnalysisOrchestrator`:

```python
def post_process(
    self,
    csv_path: str,
    script_results: List[ScriptResult],
    journal: Optional[str] = None,
    generate_pdf: bool = False,
    generate_html: bool = False,
    generate_csr: bool = True,
) -> Dict[str, Any]:
    """Post-process R script outputs: journal themes, PDF, HTML, mini-CSR.

    Called after run_scripts() in run_full().

    Returns:
        Dict with keys: journal_files, pdf_files, html_path, csr_path
    """
```

### 6.2 Modified `run_full()` Flow

```python
def run_full(self, data_path, skip_validation=False,
             journal=None, generate_pdf=False, generate_html=False):
    # ... existing steps 1-4 unchanged ...

    # Step 5 (NEW): Post-processing
    if any([journal, generate_pdf, generate_html]):
        post_result = self.post_process(
            csv_path=csv_path,
            script_results=script_results,
            journal=journal,
            generate_pdf=generate_pdf,
            generate_html=generate_html,
        )
        result.steps["post_process"] = post_result

    # ... save summary (existing) ...
```

### 6.3 CLI Additions

New arguments for `run-analysis` subparser:

```python
analysis_cmd.add_argument(
    "--journal", choices=["nejm", "lancet", "blood", "jco"],
    help="Apply journal-specific table formatting"
)
analysis_cmd.add_argument(
    "--pdf", action="store_true",
    help="Generate PDF versions of tables and figures"
)
analysis_cmd.add_argument(
    "--html", action="store_true",
    help="Generate interactive HTML dashboard"
)
analysis_cmd.add_argument(
    "--no-csr", action="store_true",
    help="Skip mini-CSR report generation"
)
```

---

## 7. Error Handling

### 7.1 Error Scenarios

| Scenario | Handling | Severity |
|----------|----------|----------|
| Journal template not found | Raise `ValueError`, list available journals | Error |
| LibreOffice/pandoc not available for PDF | Log warning, skip PDF export, continue | Warning |
| R `plotly`/`DT` not installed for HTML | Log warning, skip HTML, continue | Warning |
| .eps to .png conversion fails | Log warning, skip figure in CSR | Warning |
| Missing BCR-ABL columns for CML scripts | Skip script (optional), log | Warning |
| BCR-ABL values all NA at a timepoint | Report as "Not evaluable" in milestone table | Info |
| rmarkdown::render fails for HTML | Log error, skip HTML dashboard | Warning |

### 7.2 Graceful Degradation

All new output formats are **optional**. Failure in any post-processing step does not affect:
- The transformed CSV output
- The standard .docx/.eps outputs from R scripts
- The analysis summary JSON

---

## 8. Test Plan

### 8.1 Test Scope

| Type | Target | Tool | Count |
|------|--------|------|-------|
| Unit | JournalThemes config loading | pytest | 4 |
| Unit | ReportGenerator section mapping | pytest | 3 |
| Unit | HTMLExporter .Rmd generation | pytest | 2 |
| Unit | PDFExporter path resolution | pytest | 2 |
| Integration | Orchestrator post_process (mocked R) | pytest | 3 |
| Script | 26_cml_eln_milestones.R with mock data | pytest + subprocess | 2 |
| Script | 27_cml_waterfall.R with mock data | pytest + subprocess | 2 |
| Script | 28_cml_resistance.R with mock data | pytest + subprocess | 1 |
| Script | 29_cml_tfr_deep.R with mock data | pytest + subprocess | 1 |
| Regression | Existing 39 tests still pass | pytest | 39 |

**Total new tests**: ~20

### 8.2 Key Test Cases

- [ ] `test_journal_theme_loads_valid_config` — All 4 journals load without error
- [ ] `test_journal_theme_rejects_unknown` — Unknown journal raises ValueError
- [ ] `test_journal_theme_schema_completeness` — All required keys present
- [ ] `test_report_generator_section_mapping` — Script outputs correctly mapped to ICH-E3 sections
- [ ] `test_report_generator_creates_docx` — Mini-CSR .docx file created with correct sections
- [ ] `test_report_generator_handles_missing_scripts` — Graceful handling when some R scripts didn't run
- [ ] `test_html_exporter_creates_rmd` — .Rmd template generated with correct chunks
- [ ] `test_orchestrator_post_process_with_journal` — Journal styling applied to .docx files
- [ ] `test_orchestrator_post_process_without_flags` — No post-processing when flags absent
- [ ] `test_cml_milestones_classification` — Correct optimal/warning/failure classification
- [ ] `test_cml_milestones_window` — ±1.5 month window applied correctly
- [ ] `test_cml_waterfall_log_reduction` — Log10 reduction calculated correctly
- [ ] `test_cml_waterfall_sort_order` — Patients sorted by response depth
- [ ] `test_cml_resistance_timeline` — Time-to-resistance calculated correctly
- [ ] `test_cml_tfr_deep_km_curve` — KM for MMR loss generated
- [ ] `test_orchestrator_cml_routes_new_scripts` — Scripts 26-29 included for CML disease

### 8.3 Mock Data

Create `tests/fixtures/cml_mock.csv` with columns:
- Standard: Patient_ID, Age, Sex, Treatment, OS_months, OS_status
- Molecular: bcr_abl_baseline, bcr_abl_3m, bcr_abl_6m, bcr_abl_12m, bcr_abl_18m
- Resistance: resistance_mutation, resistance_date
- TFR: tfr_start_date, mmr_loss_date, mr4_duration_months, tfr_restart_date

15 mock CML patients with realistic BCR-ABL trajectories.

---

## 9. File Structure

### 9.1 New Files

```
scripts/
├── 26_cml_eln_milestones.R              # ELN 2020 milestone table
├── 27_cml_waterfall.R                   # BCR-ABL waterfall plot
├── 28_cml_resistance.R                  # Resistance mutation tracking
├── 29_cml_tfr_deep.R                   # Deep TFR analysis
├── crf_pipeline/
│   ├── journal_themes.py                # Journal template loader + applier
│   ├── pdf_exporter.py                  # PDF conversion module
│   ├── report_generator.py              # Mini-CSR assembly engine
│   ├── html_exporter.py                 # HTML dashboard generator
│   └── config/
│       └── journal_templates.json       # Journal style definitions
tests/
├── fixtures/
│   └── cml_mock.csv                     # CML mock data (15 patients)
├── test_journal_themes.py               # Journal theme tests
├── test_report_generator.py             # Mini-CSR tests
├── test_html_exporter.py                # HTML dashboard tests
├── test_pdf_exporter.py                 # PDF export tests
└── test_cml_scripts.py                  # CML R script tests
```

### 9.2 Modified Files

```
scripts/crf_pipeline/
├── orchestrator.py                      # Add post_process() method
├── cli.py                               # Add --journal, --pdf, --html flags
├── config/
│   ├── analysis_profiles.json           # Add scripts 26-29 to CML profile
│   └── cml_fields.json                  # Add BCR-ABL/resistance/TFR column mappings
```

---

## 10. Implementation Order

### Phase 1: Output Infrastructure (journal_themes + pdf_exporter)
1. [ ] Create `config/journal_templates.json` with 4 journal definitions
2. [ ] Create `journal_themes.py` with config loading and R-based apply logic
3. [ ] Create `pdf_exporter.py` with LibreOffice/pandoc/gs conversion
4. [ ] Add `--journal` and `--pdf` flags to CLI
5. [ ] Wire into orchestrator.post_process()
6. [ ] Write `test_journal_themes.py` (4 tests) and `test_pdf_exporter.py` (2 tests)

### Phase 2: CML R Scripts (26-29)
1. [ ] Create `tests/fixtures/cml_mock.csv` (15 patients)
2. [ ] Create `26_cml_eln_milestones.R`
3. [ ] Create `27_cml_waterfall.R`
4. [ ] Create `28_cml_resistance.R`
5. [ ] Create `29_cml_tfr_deep.R`
6. [ ] Update `analysis_profiles.json` with new CML scripts
7. [ ] Update `cml_fields.json` with new column mappings
8. [ ] Write `test_cml_scripts.py` (6 tests)

### Phase 3: Mini-CSR Report Generator
1. [ ] Create `report_generator.py` with ICH-E3 lite structure
2. [ ] Implement section mapping from script names to CSR sections
3. [ ] Implement .docx table embedding via python-docx
4. [ ] Implement .eps→.png conversion and figure embedding
5. [ ] Wire into orchestrator.post_process()
6. [ ] Write `test_report_generator.py` (3 tests)

### Phase 4: HTML Dashboard + Integration
1. [ ] Create `html_exporter.py` with .Rmd template generation
2. [ ] Implement Plotly KM curve R code chunk
3. [ ] Implement DT filterable table R code chunks
4. [ ] Add `--html` flag to CLI
5. [ ] Wire into orchestrator.post_process()
6. [ ] Write `test_html_exporter.py` (2 tests)
7. [ ] Run all tests (existing 39 + new ~20) — verify zero regression

---

## 11. Coding Convention Reference

### 11.1 Naming Conventions

| Target | Rule | Example |
|--------|------|---------|
| R scripts | `NN_description.R` (numbered) | `26_cml_eln_milestones.R` |
| Python modules | `snake_case.py` | `journal_themes.py` |
| Python classes | `PascalCase` | `JournalThemes`, `ReportGenerator` |
| Config files | `snake_case.json` | `journal_templates.json` |
| Test files | `test_module_name.py` | `test_journal_themes.py` |
| Output tables | `{Analysis}_Description.docx` | `CML_ELN2020_Milestones.docx` |
| Output figures | `{Analysis}_Description.eps` | `CML_Waterfall_BCR_ABL.eps` |

### 11.2 R Script Conventions

All new R scripts follow the existing pattern:
- Read `CSA_OUTPUT_DIR` from environment variable
- Accept dataset path as first CLI argument
- Output .docx to `$CSA_OUTPUT_DIR/Tables/`
- Output .eps to `$CSA_OUTPUT_DIR/Figures/`
- Use `flextable` + `officer` for tables, `ggsave(device="eps")` for figures
- Print summary to stdout on success

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-04 | Initial draft | Claude |
