# Design: CSA×HPW Statistics Pipeline

**Feature**: `csa-hpw-stats-pipeline`
**Date**: 2026-03-05
**Phase**: Design
**References**: `docs/01-plan/features/csa-hpw-stats-pipeline.plan.md`

---

## Architecture Overview

```
CSA run_full()
  ├── transform() → r_ready_{disease}.csv
  ├── run_scripts()
  │   ├── 02_table1.R      → Tables/table1.docx + data/02_table1_stats.json
  │   ├── 03_efficacy.R    → Tables/efficacy.docx + data/03_efficacy_stats.json
  │   ├── 04_survival.R    → Figures/os_km.eps   + data/04_survival_stats.json
  │   ├── 05_safety.R      → Tables/safety.docx  + data/05_safety_stats.json
  │   ├── 20_aml_eln_risk.R → ...                + data/20_aml_eln_risk_stats.json
  │   └── ...
  └── _write_hpw_manifest()
        reads data/*_stats.json → merges key_statistics + disease_specific
        scans Tables/*.docx, Figures/*.eps (with source_script from _output_script_map)
        adds study_context from CLI args / dir-name fallback
        writes hpw_manifest.json

User: export CSA_OUTPUT_DIR=/path/to/sapphire-g
      python -m scripts.crf_pipeline run data.sav -d aml \
             --study-name SAPPHIRE-G --trial-phase 2

User: python -m hpw.cli draft --disease aml
      (no --csa-output needed; StatisticalBridge.from_env() auto-loads manifest)
```

---

## Module 1: R Sidecar Helper (`write_stats_json`)

### Location
A shared R utility function included at the top of each R script. **Not a separate file** — inlined as a local function to avoid import complexity.

### Function Signature
```r
write_stats_json <- function(
  key_statistics   = list(),   # Named list; values are scalars or sub-lists with value/unit/ci_lower/ci_upper/p_value
  analysis_notes   = list(),   # Named character vector
  disease_specific = list(),   # Named list (same structure as key_statistics)
  script_stem      = NULL,     # Override auto-detection; defaults to script filename
  output_dir       = Sys.getenv("CSA_OUTPUT_DIR")
) {
  if (nchar(output_dir) == 0) {
    message("CSA_OUTPUT_DIR not set; skipping stats JSON")
    return(invisible(NULL))
  }
  if (is.null(script_stem)) {
    args      <- commandArgs(trailingOnly = FALSE)
    file_arg  <- grep("--file=", args, value = TRUE)
    script_stem <- if (length(file_arg) > 0) {
      tools::file_path_sans_ext(basename(sub("--file=", "", file_arg[1])))
    } else {
      "unknown"
    }
  }
  payload <- list(key_statistics = key_statistics, analysis_notes = analysis_notes)
  if (length(disease_specific) > 0) payload$disease_specific <- disease_specific

  out_dir  <- file.path(output_dir, "data")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  out_path <- file.path(out_dir, paste0(script_stem, "_stats.json"))
  jsonlite::write_json(payload, out_path, auto_unbox = TRUE, pretty = TRUE, null = "null")
  message("[write_stats_json] Written: ", out_path)
  invisible(out_path)
}
```

**Required R package**: `jsonlite` (already used in all scripts).

---

## Module 2: Canonical Stat Key Schemas

Each sidecar has a `key_statistics` block (for `StatisticalBridge`) and optionally a `disease_specific` block. Keys are snake_case strings. Numeric values use sub-list form when CI or p-value is available; plain scalars otherwise.

### `02_table1_stats.json`
```json
{
  "key_statistics": {
    "n_total": 27,
    "age_median": 58.0,
    "age_iqr_lower": 47.0,
    "age_iqr_upper": 68.0,
    "sex_male_rate":          { "value": 55.6, "unit": "percent" },
    "ecog_0_1_rate":          { "value": 74.1, "unit": "percent" },
    "follow_up_median_months":{ "value": 12.4, "unit": "months"  }
  },
  "analysis_notes": {}
}
```

### `03_efficacy_stats.json`
```json
{
  "key_statistics": {
    "n_total":  27,
    "orr":      { "value": 67.3, "unit": "percent", "ci_lower": 54.1, "ci_upper": 78.7 },
    "cr_rate":  { "value": 33.3, "unit": "percent", "ci_lower": 22.1, "ci_upper": 46.7 },
    "pr_rate":  { "value": 22.2, "unit": "percent" },
    "sd_rate":  { "value": 14.8, "unit": "percent" },
    "pd_rate":  { "value": 18.5, "unit": "percent" }
  },
  "analysis_notes": {
    "ci_method": "Wilson score interval"
  }
}
```

### `04_survival_stats.json`
```json
{
  "key_statistics": {
    "os_median_months":  { "value": 14.2, "unit": "months", "ci_lower": 11.1, "ci_upper": 18.6 },
    "os_hr":             { "value": 0.62, "ci_lower": 0.41,  "ci_upper": 0.94, "p_value": 0.024 },
    "os_12mo_rate":      { "value": 58.3, "unit": "percent" },
    "pfs_median_months": { "value": 8.4,  "unit": "months", "ci_lower": 6.2,  "ci_upper": 11.3 },
    "pfs_hr":            { "value": 0.71, "ci_lower": 0.48,  "ci_upper": 1.05, "p_value": 0.087 }
  },
  "analysis_notes": {
    "survival_model": "Kaplan-Meier; Cox proportional hazards regression",
    "ph_assumption":  "cox.zph: OS p=0.42, PFS p=0.38 (assumption satisfied)"
  }
}
```

### `05_safety_stats.json`
```json
{
  "key_statistics": {
    "ae_any_rate":          { "value": 96.3, "unit": "percent" },
    "ae_grade3plus_rate":   { "value": 44.4, "unit": "percent" },
    "ae_grade4plus_rate":   { "value": 14.8, "unit": "percent" },
    "ae_fatal_rate":        { "value": 3.7,  "unit": "percent" },
    "discontinuation_rate": { "value": 11.1, "unit": "percent" },
    "dose_reduction_rate":  { "value": 18.5, "unit": "percent" }
  },
  "analysis_notes": {
    "ctcae_version": "CTCAE v5.0",
    "threshold":     "AEs reported in ≥10% of patients"
  }
}
```

### `10_sample_size_stats.json`
```json
{
  "key_statistics": {
    "planned_n":     60,
    "power":         { "value": 80.0, "unit": "percent" },
    "alpha":         0.05,
    "effect_size":   0.35,
    "dropout_rate":  { "value": 10.0, "unit": "percent" }
  },
  "analysis_notes": {
    "calculation_method": "Two-sided z-test for proportions"
  }
}
```

### Disease-Specific Schemas

#### `20_aml_eln_risk_stats.json`
```json
{
  "disease_specific": {
    "eln_favorable_rate":    { "value": 33.3, "unit": "percent" },
    "eln_intermediate_rate": { "value": 40.7, "unit": "percent" },
    "eln_adverse_rate":      { "value": 25.9, "unit": "percent" }
  },
  "analysis_notes": { "eln_version": "ELN 2022" }
}
```

#### `21_aml_composite_response_stats.json`
```json
{
  "disease_specific": {
    "cr_rate":   { "value": 33.3, "unit": "percent", "ci_lower": 22.1, "ci_upper": 46.7 },
    "cri_rate":  { "value": 14.8, "unit": "percent" },
    "crh_rate":  { "value": 7.4,  "unit": "percent" },
    "mlfs_rate": { "value": 18.5, "unit": "percent" },
    "ccr_rate":  { "value": 74.1, "unit": "percent", "ci_lower": 60.2, "ci_upper": 84.6 }
  },
  "analysis_notes": {
    "response_criteria": "ELN 2022",
    "ci_method": "Wilson score interval"
  }
}
```

#### `22_cml_tfr_stats.json`
```json
{
  "disease_specific": {
    "mmr_rate":              { "value": 81.5, "unit": "percent" },
    "ccyr_rate":             { "value": 74.1, "unit": "percent" },
    "tfr_rate":              { "value": 55.6, "unit": "percent" },
    "tfr_duration_months":   { "value": 18.0, "unit": "months" },
    "bcr_abl_log_reduction": { "value": 3.2,  "unit": "log10_IS" }
  },
  "analysis_notes": {
    "milestone_criteria": "ELN 2020",
    "tfr_definition": "MR4 maintained off-therapy ≥12 months"
  }
}
```

#### `23_cml_scores_stats.json`
```json
{
  "disease_specific": {
    "sokal_low_rate":    { "value": 44.4, "unit": "percent" },
    "sokal_int_rate":    { "value": 33.3, "unit": "percent" },
    "sokal_high_rate":   { "value": 22.2, "unit": "percent" },
    "elts_low_rate":     { "value": 48.1, "unit": "percent" }
  },
  "analysis_notes": { "scores": "Sokal, Hasford, ELTS" }
}
```

#### `24_hct_gvhd_stats.json`
```json
{
  "disease_specific": {
    "engraftment_days_median":       { "value": 14.0, "unit": "days" },
    "agvhd_grade2plus_rate":         { "value": 38.5, "unit": "percent", "ci_lower": 28.1, "ci_upper": 50.1 },
    "agvhd_grade3plus_rate":         { "value": 15.4, "unit": "percent" },
    "cgvhd_moderate_severe_rate":    { "value": 23.1, "unit": "percent" },
    "grfs_12mo":                     { "value": 62.1, "unit": "percent", "ci_lower": 50.2, "ci_upper": 72.5 }
  },
  "analysis_notes": {
    "gvhd_criteria":     "NIH 2014 consensus criteria",
    "grfs_definition":   "Grade 2-4 aGVHD-free, moderate/severe cGVHD-free, relapse-free survival",
    "competing_risks":   "Fine-Gray subdistribution hazard model"
  }
}
```

#### `25_aml_phase1_boin_stats.json`
```json
{
  "disease_specific": {
    "mtd_dose_level":   2,
    "dlt_rate_at_mtd":  { "value": 25.0, "unit": "percent" },
    "n_dlt_events":     3,
    "target_dlt_rate":  { "value": 25.0, "unit": "percent" }
  },
  "analysis_notes": {
    "design": "BOIN (Liu & Yuan 2015)",
    "lambda_e": 0.236,
    "lambda_d": 0.359
  }
}
```

---

## Module 3: `study_context` in Manifest

### Schema
```json
{
  "study_context": {
    "study_name":       "SAPPHIRE-G",
    "protocol_id":      "SAPPHIRE-2024-001",
    "disease":          "aml",
    "trial_phase":      "2",
    "sponsor":          "",
    "data_cutoff_date": "2025-12-31",
    "n_enrolled":       27
  }
}
```

### Population Logic (orchestrator `_write_hpw_manifest`)
```python
def _build_study_context(self, result: AnalysisResult, cli_args: dict = None) -> dict:
    cli_args = cli_args or {}
    # n_enrolled from parse step
    n_enrolled = result.steps.get("parse", {}).get("rows", 0)
    return {
        "study_name":       cli_args.get("study_name") or Path(self.output_dir).name,
        "protocol_id":      cli_args.get("protocol_id", ""),
        "disease":          result.disease or self.disease,
        "trial_phase":      str(cli_args.get("trial_phase", "")),
        "sponsor":          cli_args.get("sponsor", ""),
        "data_cutoff_date": cli_args.get("data_cutoff", ""),
        "n_enrolled":       n_enrolled,
    }
```

`AnalysisOrchestrator.__init__` gains an optional `study_args: dict = None` parameter, passed through to `_write_hpw_manifest`.

### CSA CLI Args (added to `run` and `run-analysis` subcommands in `cli.py`)
```
--study-name TEXT       Study/trial name (e.g. SAPPHIRE-G)
--protocol-id TEXT      Protocol identifier
--trial-phase TEXT      Trial phase (1, 1b, 2, 3)
--sponsor TEXT          Sponsor name (optional)
--data-cutoff TEXT      Data cutoff date (YYYY-MM-DD)
```

---

## Module 4: `_output_script_map` in Orchestrator

Track which script produced which output file during execution, so `source_script` can be populated in the manifest.

```python
class AnalysisOrchestrator:
    def __init__(self, ...):
        ...
        self._output_script_map: dict[str, str] = {}  # filename → script_name
```

In `_run_single_script`, after `output_files` is collected:
```python
for f in output_files:
    self._output_script_map[Path(f).name] = script_name
```

In `_write_hpw_manifest`, when building table/figure entries:
```python
"source_script": self._output_script_map.get(docx.name, ""),
```

---

## Module 5: Updated `_script_packages`

```python
_script_packages: Dict[str, List[str]] = {
    "02_table1.R":                  ["table1", "flextable", "officer"],
    "03_efficacy.R":                ["flextable", "officer"],
    "04_survival.R":                ["survival", "survminer"],
    "05_safety.R":                  ["flextable", "officer"],
    "06_response.R":                ["flextable", "officer"],
    "07_competing_risks.R":         ["cmprsk"],
    "10_sample_size.R":             ["pwr"],
    "11_phase1_dose_finding.R":     ["dfcrm"],
    "12_phase2_simon.R":            ["clinfun"],
    "14_forest_plot.R":             ["forestplot", "ggplot2"],
    "15_swimmer_plot.R":            ["ggplot2"],
    "16_sankey.R":                  ["ggsankey"],
    "20_aml_eln_risk.R":            ["flextable", "officer", "ggplot2"],
    "21_aml_composite_response.R":  ["flextable", "officer", "ggplot2"],
    "22_cml_tfr_analysis.R":        ["survival", "survminer", "flextable", "officer"],
    "23_cml_scores.R":              ["flextable", "officer", "ggplot2"],
    "24_hct_gvhd_analysis.R":       ["cmprsk", "survival", "flextable", "officer"],
    "25_aml_phase1_boin.R":         ["flextable", "officer", "ggplot2"],
}
```

---

## Module 6: `StatisticalBridge` Changes

### New property: `study_context`
```python
@property
def study_context(self) -> Dict[str, Any]:
    """Study metadata written by CSA orchestrator."""
    return dict(self._data.get("study_context", {}))

@property
def study_name(self) -> str:
    return self.study_context.get("study_name", "")

@property
def trial_phase(self) -> str:
    return self.study_context.get("trial_phase", "")
```

### Disease-specific prose in `generate_results_prose()`

The method already reads `scripts_run`. Disease-specific sections additionally check `disease_specific` keys merged into a `_ds` dict:

```python
def generate_results_prose(self) -> Dict[str, str]:
    scripts = set(self.scripts_run)
    ds = self._data.get("disease_specific", {})   # merged disease_specific from all sidecars
    disease = self.disease
    prose: Dict[str, str] = {}

    # [existing baseline / efficacy / survival / safety sections unchanged]

    # --- AML: composite response ---
    if disease == "aml" and "ccr_rate" in ds:
        parts = []
        ccr  = self._get_ds_stat(ds, "ccr_rate")
        cr   = self._get_ds_stat(ds, "cr_rate")
        cri  = self._get_ds_stat(ds, "cri_rate")
        crh  = self._get_ds_stat(ds, "crh_rate")
        mlfs = self._get_ds_stat(ds, "mlfs_rate")
        parts.append(
            f"The composite complete response (cCR; CR + CRi + CRh + MLFS) rate was "
            f"{self._fmt_ds(ccr)} per ELN 2022 criteria (Table 3)."
        )
        if cr and cri:
            parts.append(
                f"Individual response rates: CR {self._fmt_ds(cr)}, CRi {self._fmt_ds(cri)}, "
                f"CRh {self._fmt_ds(crh)}, MLFS {self._fmt_ds(mlfs)}."
            )
        prose["aml_composite_response"] = " ".join(parts)

    # --- AML: ELN risk ---
    if disease == "aml" and "eln_favorable_rate" in ds:
        fav = self._get_ds_stat(ds, "eln_favorable_rate")
        int_ = self._get_ds_stat(ds, "eln_intermediate_rate")
        adv = self._get_ds_stat(ds, "eln_adverse_rate")
        prose["aml_eln_risk"] = (
            f"By ELN 2022 risk classification: favorable {self._fmt_ds(fav)}, "
            f"intermediate {self._fmt_ds(int_)}, adverse {self._fmt_ds(adv)} (Table 4)."
        )

    # --- CML: molecular response ---
    if disease == "cml" and "mmr_rate" in ds:
        parts = []
        mmr  = self._get_ds_stat(ds, "mmr_rate")
        ccyr = self._get_ds_stat(ds, "ccyr_rate")
        if mmr:
            parts.append(f"The major molecular response (MMR) rate was {self._fmt_ds(mmr)}.")
        if ccyr:
            parts.append(f"The complete cytogenetic response (CCyR) rate was {self._fmt_ds(ccyr)}.")
        prose["cml_molecular"] = " ".join(parts)

    # --- CML: TFR ---
    if disease == "cml" and "tfr_rate" in ds:
        tfr = self._get_ds_stat(ds, "tfr_rate")
        dur = self._get_ds_stat(ds, "tfr_duration_months")
        s = f"Treatment-free remission (TFR) was achieved in {self._fmt_ds(tfr)} of patients"
        if dur:
            s += f" with a median TFR duration of {self._fmt_ds(dur)} months"
        prose["cml_tfr"] = s + "."

    # --- HCT: GVHD + GRFS ---
    if disease == "hct" and "grfs_12mo" in ds:
        parts = []
        grfs  = self._get_ds_stat(ds, "grfs_12mo")
        agvhd = self._get_ds_stat(ds, "agvhd_grade2plus_rate")
        cgvhd = self._get_ds_stat(ds, "cgvhd_moderate_severe_rate")
        engr  = self._get_ds_stat(ds, "engraftment_days_median")
        if engr:
            parts.append(f"Median time to neutrophil engraftment was {self._fmt_ds(engr)} days.")
        if grfs:
            parts.append(
                f"The 12-month graft-versus-host disease-free, relapse-free survival (GRFS) "
                f"rate was {self._fmt_ds(grfs)} (Figure 3)."
            )
        if agvhd:
            parts.append(
                f"The cumulative incidence of grade 2–4 acute GVHD was "
                f"{self._fmt_ds(agvhd)} by the Fine–Gray method."
            )
        if cgvhd:
            parts.append(f"Moderate-to-severe chronic GVHD occurred in {self._fmt_ds(cgvhd)} of patients.")
        prose["hct_gvhd"] = " ".join(parts)

    return prose
```

### New private helpers
```python
def _get_ds_stat(self, ds: dict, key: str) -> Optional[StatValue]:
    raw = ds.get(key)
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return StatValue(value=raw)
    return StatValue(
        value=raw.get("value"),
        unit=raw.get("unit"),
        ci_lower=raw.get("ci_lower"),
        ci_upper=raw.get("ci_upper"),
        p_value=raw.get("p_value"),
    )

def _fmt_ds(self, sv: Optional[StatValue], fmt: str = "short") -> str:
    if sv is None:
        return "[N/A]"
    is_pct = sv.unit == "percent"
    val_str = f"{sv.value:.1f}%" if is_pct else str(sv.value)
    if fmt == "short" and sv.ci_lower is not None and sv.ci_upper is not None:
        ci_l = f"{sv.ci_lower:.1f}%" if is_pct else str(sv.ci_lower)
        ci_u = f"{sv.ci_upper:.1f}%" if is_pct else str(sv.ci_upper)
        return f"{val_str} (95% CI {ci_l}–{ci_u})"
    return val_str
```

### `disease_specific` merging in `_load()`
After loading manifest, merge all `disease_specific` blocks from sidecars that were scanned:
```python
# In _load(): disease_specific is already written by orchestrator into manifest
# No change to load logic needed — orchestrator merges disease_specific from sidecars
```

The orchestrator already merges `disease_specific` from `*_stats.json` files in `_write_hpw_manifest()`. No change to StatisticalBridge loading required.

### Updated `_ABSTRACT_KEYS`
```python
_ABSTRACT_KEYS: Dict[str, List[str]] = {
    "aml": ["n_total", "ccr_rate", "orr", "os_median_months", "os_hr", "ae_grade3plus_rate"],
    "cml": ["n_total", "mmr_rate", "ccyr_rate", "tfr_rate", "os_median_months", "ae_grade3plus_rate"],
    "mds": ["n_total", "orr", "hi_rate", "os_median_months", "ae_grade3plus_rate"],
    "hct": ["n_total", "engraftment_days_median", "grfs_12mo",
            "agvhd_grade2plus_rate", "os_median_months", "ae_grade3plus_rate"],
}
```

Note: keys not present in `key_statistics` are silently omitted by `get_abstract_statistics()`.

---

## Module 7: HPW CLI Auto-Discovery

### Change in `hematology-paper-writer/cli.py`

Find the section where `PhaseManager` is created (after argument parsing). Add:

```python
# Auto-discover CSA outputs if --csa-output not provided
if not args.csa_output and os.environ.get("CSA_OUTPUT_DIR"):
    bridge = StatisticalBridge.from_env()
    if bridge:
        args.csa_output = str(bridge._manifest_dir)
        logger.info(
            "Auto-discovered CSA output from $CSA_OUTPUT_DIR: %s (study: %s)",
            args.csa_output,
            bridge.study_name,
        )
```

This runs before PhaseManager construction, so `args.csa_output` is already set when PhaseManager reads it.

**Fallback behavior**: If `$CSA_OUTPUT_DIR` not set, or manifest not found, `args.csa_output` remains `None` and behavior is unchanged.

---

## Module 8: Test Design

### `tests/test_statistical_bridge.py`

```
TestStatisticalBridgeLoad (3 tests)
  test_load_minimal_manifest          — schema_version=1.0, empty stats → bridge.is_available
  test_load_wrong_major_version       — schema_version=2.0 → ManifestVersionError
  test_load_missing_file              — non-existent path → ManifestError

TestStatisticalBridgeStats (4 tests)
  test_get_stat_scalar                — key_statistics: n_total=27 → StatValue(value=27)
  test_get_stat_with_ci               — orr dict → StatValue with ci_lower/ci_upper
  test_get_stat_missing_key           — absent key → None (no exception)
  test_format_stat_standard           — orr → "67.3% (95% CI 54.1%–78.7%)"

TestStatisticalBridgeProse (6 tests)
  test_generate_methods_paragraph     — scripts_run includes 04_survival.R → "Kaplan–Meier" in text
  test_generate_results_prose_aml     — AML manifest with ccr_rate → "cCR" in prose["aml_composite_response"]
  test_generate_results_prose_cml     — CML manifest with mmr_rate + tfr_rate → both sections present
  test_generate_results_prose_hct     — HCT manifest with grfs_12mo → "GRFS" in prose["hct_gvhd"]
  test_generate_results_prose_graceful— manifest with no disease_specific → no exception, sections absent
  test_get_abstract_statistics_aml    — AML manifest → dict has "ccr_rate" key

TestStudyContext (2 tests)
  test_study_context_present          — manifest with study_context → bridge.study_name == "SAPPHIRE-G"
  test_study_context_absent           — no study_context → bridge.study_name == ""
```

**Total**: 15 tests (exceeds FR-08 requirement of ≥10).

**Fixture**: `tests/fixtures/test_manifest_aml.json` — a complete mock manifest covering all fields, usable across test classes.

---

## Data Flow Diagram

```
R Script (e.g. 03_efficacy.R)
  │ computes ORR, CR, PR rates
  │ calls write_stats_json(key_statistics=list(...), analysis_notes=list(...))
  └─→ data/03_efficacy_stats.json

orchestrator._write_hpw_manifest()
  ├── scans data/*_stats.json
  │   ├── merges key_statistics → manifest.key_statistics
  │   └── merges disease_specific → manifest.disease_specific
  ├── builds study_context from CLI args + parse result
  ├── scans Tables/*.docx, Figures/*.eps → with source_script from _output_script_map
  └─→ hpw_manifest.json (schema v1.0)

HPW cli.py (startup)
  │ StatisticalBridge.from_env() reads $CSA_OUTPUT_DIR/hpw_manifest.json
  └─→ bridge loaded with study_name, tables, figures, key_statistics, disease_specific

HPW draft phase
  │ bridge.generate_methods_paragraph() → Statistical Methods paragraph
  │ bridge.generate_results_prose()     → dict of section prose
  │   ├── "baseline", "efficacy", "survival", "safety"  (core)
  │   └── "aml_composite_response", "aml_eln_risk",     (disease-specific)
  │       "cml_molecular", "cml_tfr", "hct_gvhd"
  └── bridge.get_abstract_statistics()  → top-priority stats for Abstract
```

---

## Module 9: NotebookLM Guideline Enrichment (FR-09)

### Design

`StatisticalBridge.generate_results_prose()` optionally enriches each disease-specific prose sentence with a parenthetical guideline citation sourced from `NotebookLMIntegration`.

**Notebook scope** (each notebook covers multiple diseases — do not assume disease exclusivity):

| Notebook type | Covers | Use for |
|---------------|--------|---------|
| `classification` | ALL diseases | WHO 2022 / ICC 2022 response-criteria definitions |
| `therapeutic` | AML + CML (+ others) | ELN 2022/2025 risk; treatment milestones |
| `gvhd` | HCT | NIH 2014 aGVHD/cGVHD grading; GRFS definition |
| `nomenclature` | ALL diseases | BCR::ABL1 notation; HGVS 2024; ISCN 2024 |

**Query routing by stat section** (primary notebook first; secondary as fallback):

| Prose section | Primary | Secondary | Canonical query |
|---------------|---------|-----------|----------------|
| `aml_composite_response` | `classification` | `therapeutic` | "ELN 2022 definition of composite complete response CR CRi CRh MLFS" |
| `aml_eln_risk` | `therapeutic` | `classification` | "ELN 2022 AML risk stratification favorable intermediate adverse" |
| `cml_molecular` | `classification` | `therapeutic` | "ELN 2020 definition of MMR BCR-ABL1 IS 0.1 percent CCyR" |
| `cml_tfr` | `therapeutic` | — | "ELN 2020 treatment-free remission criteria MR4" |
| `hct_gvhd` | `gvhd` | `classification` | "NIH 2014 consensus aGVHD cGVHD grading criteria GRFS definition" |

**Rule**: response-rate stats → `classification` first (defines criteria); risk/milestone stats → `therapeutic` first.

### Implementation in `StatisticalBridge`

```python
def _enrich_with_nlm(self, section_key: str, base_prose: str) -> str:
    """Append a NotebookLM guideline parenthetical to base_prose.
    Returns base_prose unchanged if NotebookLM is unavailable or query fails."""
    _NLM_ROUTING = {
        "aml_composite_response": ("classification", "ELN 2022 definition of composite complete response CR CRi CRh MLFS"),
        "aml_eln_risk":           ("therapeutic",    "ELN 2022 AML risk stratification favorable intermediate adverse"),
        "cml_molecular":          ("classification", "ELN 2020 definition of MMR BCR-ABL1 IS 0.1 percent CCyR"),
        "cml_tfr":                ("therapeutic",    "ELN 2020 treatment-free remission criteria MR4"),
        "hct_gvhd":               ("gvhd",          "NIH 2014 consensus aGVHD cGVHD grading criteria GRFS definition"),
    }
    if section_key not in _NLM_ROUTING:
        return base_prose
    notebook_type, query = _NLM_ROUTING[section_key]
    try:
        from tools.notebooklm_integration import NotebookLMIntegration
        nlm = NotebookLMIntegration()
        if not nlm.is_available():
            return base_prose
        method = getattr(nlm, f"query_{notebook_type}_guidelines", None)
        if method is None:
            return base_prose
        answer = method(query)                  # returns str (result.answer)
        if not answer or len(answer.strip()) < 20:
            return base_prose
        # Extract first sentence of answer as parenthetical (keep prose concise)
        first_sentence = answer.strip().split(".")[0]
        return base_prose.rstrip(".") + f" ({first_sentence})."
    except Exception:
        return base_prose                       # never raise; enrichment is optional
```

Enrichment is called inside `generate_results_prose()` immediately after each prose string is assembled:
```python
prose["aml_composite_response"] = self._enrich_with_nlm(
    "aml_composite_response", " ".join(parts)
)
```

### `NotebookLMIntegration.is_available()` guard

`is_available()` returns `False` when `notebooklm_config.json` is absent or `notebooklm-py` is not installed. This keeps the guard cheap (no async call, no I/O besides one file check).

### Test additions (2 new tests in `TestStatisticalBridgeProse`)

```
test_enrich_with_nlm_unavailable  — notebooklm_config.json absent → prose unchanged
test_enrich_with_nlm_available    — mock NotebookLMIntegration → parenthetical appended
```

Total test count: **17** (previously 15).

---

## Data Flow Diagram

```
R Script (e.g. 03_efficacy.R)
  │ computes ORR, CR, PR rates
  │ calls write_stats_json(key_statistics=list(...), analysis_notes=list(...))
  └─→ data/03_efficacy_stats.json

orchestrator._write_hpw_manifest()
  ├── scans data/*_stats.json
  │   ├── merges key_statistics → manifest.key_statistics
  │   └── merges disease_specific → manifest.disease_specific
  ├── builds study_context from CLI args + parse result
  ├── scans Tables/*.docx, Figures/*.eps → with source_script from _output_script_map
  └─→ hpw_manifest.json (schema v1.0)

HPW cli.py (startup)
  │ StatisticalBridge.from_env() reads $CSA_OUTPUT_DIR/hpw_manifest.json
  └─→ bridge loaded with study_name, tables, figures, key_statistics, disease_specific

HPW draft phase
  │ bridge.generate_methods_paragraph() → Statistical Methods paragraph
  │ bridge.generate_results_prose()     → dict of section prose
  │   ├── "baseline", "efficacy", "survival", "safety"  (core)
  │   ├── "aml_composite_response", "aml_eln_risk",     (disease-specific)
  │   │   "cml_molecular", "cml_tfr", "hct_gvhd"
  │   └── [optional] _enrich_with_nlm() appends guideline parenthetical via NotebookLMIntegration
  │         classification → WHO/ICC response criteria
  │         therapeutic    → ELN risk/milestone context
  │         gvhd           → NIH 2014 grading context
  └── bridge.get_abstract_statistics()  → top-priority stats for Abstract
```

---

## Implementation Order

1. **R `write_stats_json`** — implement helper, add to `02_table1.R`, `03_efficacy.R`, `04_survival.R`, `05_safety.R`, `10_sample_size.R`
2. **Disease-specific sidecars** — add to scripts `20–25`
3. **Orchestrator: `_output_script_map`** — track output→script during execution
4. **Orchestrator: `_script_packages` + `study_context`** — update mapping, add `study_args` param
5. **CSA CLI: new args** — `--study-name`, `--protocol-id`, `--trial-phase`, `--sponsor`, `--data-cutoff`
6. **StatisticalBridge: `study_context` property + helpers** — `_get_ds_stat`, `_fmt_ds`, `study_name`, `trial_phase`
7. **StatisticalBridge: disease-specific prose** — AML, CML, HCT sections in `generate_results_prose()`
8. **StatisticalBridge: `_ABSTRACT_KEYS`** — update with disease-specific keys
9. **HPW CLI: auto-discovery** — wire `from_env()` before PhaseManager construction
10. **StatisticalBridge: `_enrich_with_nlm()`** — NotebookLM enrichment helper + routing table
11. **Tests** — `tests/test_statistical_bridge.py` (17 tests) + fixture manifest
