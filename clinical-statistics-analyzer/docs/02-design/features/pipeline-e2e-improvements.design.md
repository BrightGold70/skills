# Pipeline E2E Improvements Design Document

> **Summary**: Detailed design for fixing pipeline issues from SAPPHIRE-G validation
>
> **Project**: clinical-statistics-analyzer
> **Version**: 3.2
> **Date**: 2026-03-04
> **Status**: Draft
> **Plan Reference**: `docs/01-plan/features/pipeline-e2e-improvements.plan.md`

---

## 1. FR-01: Smart SPSS Value Label Application

### Problem
After `ValueRecoder` applies SPSS labels, binary outcome variables become strings ("ORR"/"Non-ORR") which breaks `glm(family=binomial)` in R. Manual post-processing was needed to recode back to 0/1.

### Design

Add a new `_apply_spss_labels` method to `ValueRecoder` that:
1. Reads `spss_value_mapping` from config
2. For each mapped column, applies labels to create a `{col}_label` column
3. For binary columns (exactly 2 non-null distinct values), also creates `{col}_numeric` column with positive=1, negative=0
4. The original column keeps SPSS labels (for Table 1 display)

#### Interface Change in `value_recoder.py`

```python
class ValueRecoder(AbstractTransformer):
    # Existing methods unchanged

    def transform(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        derived = config.get("derived_columns", {})
        for col_name, spec in derived.items():
            # ... existing recode/bin logic ...

        # NEW: Apply SPSS value labels with dual-column output
        df = self._apply_spss_labels(df, config)
        return df

    def _apply_spss_labels(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Apply SPSS value labels and create numeric columns for binary outcomes."""
        spss_map = config.get("spss_value_mapping", {})
        column_mapping = config.get("column_mapping", {})
        # Reverse: R column name -> CRF variable name
        r_to_crf = {v: k for k, v in column_mapping.items()}

        # Define which outcomes are "positive" for binary coding
        POSITIVE_KEYWORDS = {"CR", "cCR", "ORR", "Yes", "Positive", "Male",
                             "CHR", "CCyR", "MMR", "DMR", "MR4", "MR4.5", "MR5"}

        for crf_var, mapping in spss_map.items():
            # Find the column in df (could be original or mapped name)
            col = crf_var
            r_col = column_mapping.get(crf_var, crf_var)
            target = r_col if r_col in df.columns else (crf_var if crf_var in df.columns else None)
            if target is None:
                continue

            # Build numeric-key -> label mapping
            num_to_label = {}
            for k, v in mapping.items():
                try:
                    float(k)
                    num_to_label[k] = v
                except (ValueError, TypeError):
                    pass

            if not num_to_label:
                continue

            # Apply labels
            original = df[target].copy()
            df[target] = df[target].astype(str).map(num_to_label).fillna(original.astype(str))
            df[target] = df[target].replace('nan', pd.NA)

            # For binary outcomes, create _numeric column (positive=1, negative=0)
            unique_labels = set(num_to_label.values()) - {None, "Unknown"}
            if len(unique_labels) == 2:
                positive_label = None
                for lbl in unique_labels:
                    if lbl in POSITIVE_KEYWORDS:
                        positive_label = lbl
                        break
                if positive_label is None:
                    # Use SPSS code 1.0 as positive
                    positive_label = num_to_label.get("1.0")

                if positive_label:
                    numeric_col = f"{target}_numeric"
                    df[numeric_col] = (df[target] == positive_label).astype(float)
                    df.loc[df[target].isna() | (df[target] == "Unknown"), numeric_col] = float('nan')
                    logger.info("Created binary numeric column '%s' (positive='%s')", numeric_col, positive_label)

        return df
```

#### Config Addition (per disease JSON)

No config changes needed — uses existing `spss_value_mapping` and `column_mapping`.

#### Output Columns

For SAPPHIRE-G AML data, produces:
- `Response` = "ORR" / "Non-ORR" (labeled, for Table 1)
- `Response_numeric` = 1.0 / 0.0 (for `glm(binomial)`)
- `CR` = "CR" / "Non-CR" (labeled)
- `CR_numeric` = 1.0 / 0.0
- `cCR` = "cCR" / "Non-cCR" (labeled)
- `cCR_numeric` = 1.0 / 0.0
- `Sex` = "Male" / "Female" (labeled, no `_numeric` needed by R)
- `Treatment` = "ICT" / "LIT" / "Unknown" (labeled, >2 values, no `_numeric`)

---

## 2. FR-02: Fix analysis_profiles.json Arguments

### Problem
Current `analysis_profiles.json` has:
```json
{"name": "03_efficacy.R", "args": ["{dataset}"], ...}
{"name": "04_survival.R", "args": ["{dataset}"], ...}
```
But scripts require:
- `03_efficacy.R <dataset> <outcome_var> [--disease <type>]`
- `04_survival.R <dataset> <time_var> <status_var> [--disease <type>]`

### Design

#### Updated analysis_profiles.json Structure

```json
{
  "profiles": {
    "aml": {
      "scripts": [
        {
          "name": "03_efficacy.R",
          "args": ["{dataset}", "{outcome_var}", "--disease", "{disease}"],
          "required": true
        },
        {
          "name": "04_survival.R",
          "args": ["{dataset}", "{time_var}", "{status_var}", "--disease", "{disease}"],
          "required": true,
          "run_variants": [
            {"time_var": "OS_months", "status_var": "OS_status", "suffix": "OS"},
            {"time_var": "PFS_months", "status_var": "PFS_status", "suffix": "PFS"}
          ]
        }
      ],
      "default_outcome_var": "Response_numeric",
      "default_time_var": "OS_months",
      "default_status_var": "OS_status"
    }
  }
}
```

#### Orchestrator `_resolve_args` Enhancement

```python
def _resolve_args(self, args_template: List[str], csv_path: str,
                  overrides: Optional[Dict[str, str]] = None) -> List[str]:
    """Resolve placeholders in script argument templates."""
    profile = self.analysis_profiles.get(self.disease, {})
    defaults = {
        "dataset": csv_path,
        "output_dir": str(self.output_dir),
        "disease": self.disease,
        "outcome_var": profile.get("default_outcome_var", "Response"),
        "time_var": profile.get("default_time_var", "OS_months"),
        "status_var": profile.get("default_status_var", "OS_status"),
    }
    if overrides:
        defaults.update(overrides)

    resolved = []
    for arg in args_template:
        if arg.startswith("{") and arg.endswith("}"):
            key = arg[1:-1]
            resolved.append(defaults.get(key, arg))
        else:
            resolved.append(arg)
    return resolved
```

#### `run_scripts` Enhancement for Variants

```python
def run_scripts(self, csv_path: str) -> List[ScriptResult]:
    scripts = self._get_scripts_for_disease()
    results = []

    for script_spec in scripts:
        variants = script_spec.get("run_variants")
        if variants:
            # Run once per variant (e.g., OS and PFS for survival)
            for variant in variants:
                # Check if variant columns exist
                header = pd.read_csv(csv_path, nrows=0).columns.tolist()
                time_col = variant.get("time_var", "")
                if time_col and time_col not in header:
                    logger.info("Skipping variant %s: column '%s' not in data",
                                variant.get("suffix", ""), time_col)
                    continue

                args = self._resolve_args(script_spec["args"], csv_path, overrides=variant)
                result = self._execute_script(script_spec, args, suffix=variant.get("suffix"))
                results.append(result)
        else:
            args = self._resolve_args(script_spec["args"], csv_path)
            result = self._execute_script(script_spec, args)
            results.append(result)

    return results
```

---

## 3. FR-03: Fix 21_aml_composite_response.R

### Problem 1: `color_map` undefined
`color_map` is defined at line 196 inside the waterfall plot block (`if (has_blast_cols)`). When waterfall is skipped, line 253 (`scale_fill_manual(values = color_map)`) crashes.

### Problem 2: cCR counting
The script uses `pull_col(df, "CR", FALSE)` (line 69) which looks for a column named exactly `CR`. After SPSS label application, `CR` contains "CR"/"Non-CR" strings. The `to_logical()` function at line 79 handles `1/0` but not `"CR"/"Non-CR"` — it returns FALSE for both since neither matches `c("true", "yes", "1")`.

### Fix Design

#### color_map fix (move to top level)

Move `color_map` definition before the waterfall conditional block:

```r
# Define color_map BEFORE waterfall block (used by both waterfall and bar plot)
color_map <- c(
  "CR MRD-neg"       = "#2ca02c",
  "CR MRD+/unknown"  = "#98df8a",
  "CRh"              = "#ff7f0e",
  "CRi"              = "#ffbb78",
  "MLFS"             = "#1f77b4",
  "PR"               = "#aec7e8",
  "PD"               = "#d62728",
  "NR"               = "#ff9896",
  "Unknown"          = "#7f7f7f"
)

# Waterfall plot (optional)
if (has_blast_cols) {
  # ... waterfall logic (no color_map definition here) ...
}

# Bar plot (always runs, uses color_map from above)
p_bar <- ggplot(resp_counts, ...) +
  scale_fill_manual(values = color_map) + ...
```

#### to_logical fix (handle SPSS-labeled strings)

Enhance `to_logical()` to handle SPSS value labels:

```r
to_logical <- function(x) {
  if (is.logical(x)) return(x)
  if (is.numeric(x)) return(x == 1)
  # Handle SPSS labels: "CR"/"Non-CR", "ORR"/"Non-ORR", "Positive"/"Negative"
  x_lower <- tolower(as.character(x))
  x_lower %in% c("true", "yes", "1", "cr", "cri", "crh", "mlfs", "pr",
                  "orr", "ccr", "positive", "achieved")
}
```

Also add handling for `Best_Response` column when individual response columns are missing:

```r
# If CR/CRi/CRh/MLFS columns don't exist, derive from Best_Response
if (!"CR" %in% names(df) & "Best_Response" %in% names(df)) {
  br <- tolower(as.character(df$Best_Response))
  df$CR   <- br %in% c("cr", "cr mrd-neg", "2", "2.0")
  df$CRi  <- br %in% c("cri", "4", "4.0")
  df$CRh  <- br %in% c("crh", "crm", "3", "3.0", "7", "7.0")
  df$MLFS <- br %in% c("mlfs", "1", "1.0")
  df$PR   <- br %in% c("pr", "8", "8.0")
}
```

---

## 4. FR-04: Graceful Degradation for ELN Risk

### Problem
`20_aml_eln_risk.R` requires 26 molecular/cytogenetic columns for full ELN 2022 classification. When most are missing, all patients default to "Intermediate".

### Design

Add a data availability check after loading:

```r
# Count available ELN-relevant columns
eln_cols <- c("t_8_21", "RUNX1_RUNX1T1", "inv16", "CBFB_MYH11",
              "NPM1_mut", "FLT3_ITD", "FLT3_ITD_VAF", "CEBPA_biallelic",
              "TP53_mut", "ASXL1_mut", "complex_karyotype")
available_eln <- sum(eln_cols %in% names(df))
total_eln <- length(eln_cols)

if (available_eln / total_eln < 0.5) {
  cat("WARNING: Only", available_eln, "of", total_eln,
      "ELN-relevant columns available. Using simplified classification.\n")
  cat("Available:", paste(eln_cols[eln_cols %in% names(df)], collapse=", "), "\n")
  cat("Missing:", paste(eln_cols[!eln_cols %in% names(df)], collapse=", "), "\n\n")

  # Simplified classification using available markers
  df$ELN_Risk <- "Intermediate"  # default
  if ("NPM1_mut" %in% names(df) & "FLT3_ITD" %in% names(df)) {
    npm1_pos <- to_logical(df$NPM1_mut)
    flt3_pos <- to_logical(df$FLT3_ITD)
    # NPM1+ without FLT3-ITD → Favorable (simplified)
    df$ELN_Risk[npm1_pos & !flt3_pos] <- "Favorable"
  }
  if ("TP53_mut" %in% names(df)) {
    tp53_pos <- to_logical(df$TP53_mut)
    df$ELN_Risk[tp53_pos] <- "Adverse"
  }
  if ("complex_karyotype" %in% names(df)) {
    ck <- to_logical(df$complex_karyotype)
    df$ELN_Risk[ck] <- "Adverse"
  }

  # Add note to output table
  df$ELN_Note <- paste0("Simplified (", available_eln, "/", total_eln, " markers)")
}
```

---

## 5. FR-05: Auto-detect Outcome Type in Efficacy Script

### Problem
`03_efficacy.R` passes outcome variable directly to `glm(family=binomial)` which requires 0/1. Character labels crash the model.

### Design

Add auto-detection before the GLM call at line 42:

```r
# Auto-detect outcome type and convert if needed
if (outcome_var %in% names(df)) {
  outcome_col <- df[[outcome_var]]
  if (is.character(outcome_col) || is.factor(outcome_col)) {
    positive_keywords <- c("cr", "orr", "ccr", "yes", "positive", "response",
                           "achieved", "mmr", "ccyr", "dmr")
    char_vals <- tolower(as.character(outcome_col))
    df[[outcome_var]] <- as.integer(char_vals %in% positive_keywords)
    cat("Auto-converted character outcome to binary (0/1).\n")
    cat("  Positive matches:", paste(unique(outcome_col[df[[outcome_var]] == 1]), collapse=", "), "\n")
    cat("  Negative matches:", paste(unique(outcome_col[df[[outcome_var]] == 0]), collapse=", "), "\n")
  }
}
```

Also check for `_numeric` suffix variant:

```r
# Prefer _numeric variant if available
numeric_var <- paste0(outcome_var, "_numeric")
if (numeric_var %in% names(df)) {
  cat("Using numeric variant:", numeric_var, "instead of", outcome_var, "\n")
  outcome_var <- numeric_var
}
```

---

## 6. FR-06: PFS Survival Analysis via Orchestrator

### Design

Handled by FR-02's `run_variants` mechanism. The `04_survival.R` entry in `analysis_profiles.json` gets:

```json
{
  "name": "04_survival.R",
  "args": ["{dataset}", "{time_var}", "{status_var}", "--disease", "{disease}"],
  "required": true,
  "run_variants": [
    {"time_var": "OS_months", "status_var": "OS_status", "suffix": "OS"},
    {"time_var": "PFS_months", "status_var": "PFS_status", "suffix": "PFS"}
  ]
}
```

The orchestrator skips the PFS variant if `PFS_months` or `PFS_status` columns are missing.

For SAPPHIRE-G: `PFS_months` exists (as `PFS_month` → mapped), but `PFS_status` needs derivation. Add to `derived_columns` in disease configs:

```json
"PFS_status": {
  "type": "recode",
  "source": "PFS_event",
  "mapping": {"0": 0, "1": 1, "Alive": 0, "Relapsed": 1, "Dead": 1}
}
```

If `PFS_event` doesn't exist but `PFS_months` does, the orchestrator can derive PFS_status from OS_status as fallback (event = death or relapse).

---

## 7. FR-07: SAPPHIRE-G E2E Test Suite

### Design

```
tests/
  test_sapphire_g_e2e.py       # Main E2E test
  fixtures/
    sapphire_g_mock.csv         # Anonymized 27-row fixture
    sapphire_g_expected.json    # Expected values for assertions
```

#### Fixture Data (`sapphire_g_mock.csv`)

Anonymized version of the 27-row SAPPHIRE-G dataset with:
- Scrambled patient IDs (PT-001 through PT-027)
- Preserved: distributions of Sex, Age, Treatment, Response, Molecular markers
- Preserved: exact counts (15M/12F, 25 FLT3+, ORR=16, CR=10, cCR=15)
- Removed: real dates, names, any identifiable information
- Columns: case_no, age, gender, Sal1, ECOG1, diag, FLT3ITD, FLT3TKD, NPM1, CEBPA, RUNX1, TP53, Rspn_Best, CR, cCR, ORR, alive, OS_months, PFS_month, hb_Rel, wbc_Rel, plt_Rel, blast_Rel

#### Expected Values (`sapphire_g_expected.json`)

```json
{
  "n_patients": 27,
  "transform_checks": {
    "columns_present": ["Patient_ID", "Age", "Sex", "Treatment", "OS_months", "OS_status",
                         "Response", "Response_numeric", "CR", "CR_numeric"],
    "sex_distribution": {"Male": 15, "Female": 12},
    "treatment_distribution": {"ICT": 16, "LIT": 10, "Unknown": 1},
    "response_counts": {"ORR": 16, "cCR": 15, "CR": 10}
  },
  "r_script_checks": {
    "02_table1.R": {"exit_code": 0, "output_file": "Table1_Baseline_Characteristics.docx"},
    "03_efficacy.R": {"exit_code": 0, "output_file": "Efficacy_Response_numeric_Analysis.docx"},
    "04_survival.R": {"exit_code": 0, "output_file": "KM_Plot_OS_months.eps"}
  }
}
```

#### Test Structure

```python
class TestSapphireGE2E:
    """End-to-end test using anonymized SAPPHIRE-G data."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Copy fixture and config to temp dir."""
        self.output_dir = tmp_path / "output"
        self.config_dir = tmp_path / "config"
        # Copy aml_fields.json with SAPPHIRE-G overrides
        # Copy analysis_profiles.json

    def test_transform_produces_correct_columns(self):
        """FR-01: Transform creates labeled + numeric columns."""

    def test_transform_response_counts_match_manuscript(self):
        """Verify ORR=16, CR=10, cCR=15 match manuscript."""

    def test_transform_demographics_match_manuscript(self):
        """Verify Sex, Age, ECOG, Diagnosis distribution."""

    def test_efficacy_script_runs_successfully(self):
        """FR-02/FR-05: Efficacy R script completes with correct args."""

    def test_survival_script_runs_successfully(self):
        """FR-02: Survival R script completes with OS args."""

    def test_table1_script_runs_successfully(self):
        """Table 1 R script produces docx."""

    def test_composite_response_no_crash(self):
        """FR-03: Composite response script doesn't crash on bar plot."""
```

---

## 8. Implementation Order

| Phase | FR | File | Change Type |
|-------|-----|------|-------------|
| 1.1 | FR-01 | `transformers/value_recoder.py` | Add `_apply_spss_labels()` method |
| 1.2 | FR-02 | `config/analysis_profiles.json` | Fix args with template vars + add variants |
| 1.3 | FR-02 | `orchestrator.py` | Enhance `_resolve_args()` + variant support |
| 1.4 | FR-03 | `scripts/21_aml_composite_response.R` | Move `color_map`, fix `to_logical()`, add `Best_Response` fallback |
| 2.1 | FR-04 | `scripts/20_aml_eln_risk.R` | Add simplified classification fallback |
| 2.2 | FR-05 | `scripts/03_efficacy.R` | Add auto-detect + `_numeric` preference |
| 3.1 | FR-06 | Disease config JSONs | Add PFS_status derived column |
| 3.2 | FR-07 | `tests/test_sapphire_g_e2e.py` | Create fixture + test suite |
| 3.3 | — | All | Run full regression test suite |

---

## 9. Backward Compatibility

| Change | Backward Compatible? | Mitigation |
|--------|---------------------|------------|
| New `_numeric` columns in CSV | Yes | Additive only — existing columns unchanged |
| analysis_profiles.json args | Yes | Old format still works via `_resolve_args` fallback |
| R script `to_logical()` enhancement | Yes | Superset of original behavior |
| `color_map` relocation | Yes | No behavior change when waterfall exists |
| Simplified ELN classification | Yes | Only activates when >50% columns missing |
| `_numeric` preference in efficacy | Yes | Falls back to original var if no `_numeric` exists |

---

## 10. Test Plan

| Test | Type | Validates |
|------|------|-----------|
| `test_value_recoder_spss_labels` | Unit | FR-01: Dual column output |
| `test_value_recoder_binary_numeric` | Unit | FR-01: Positive keyword detection |
| `test_resolve_args_template_vars` | Unit | FR-02: Template variable substitution |
| `test_resolve_args_with_overrides` | Unit | FR-02: Variant overrides |
| `test_composite_response_no_crash` | Integration | FR-03: Bar plot without waterfall |
| `test_eln_simplified_classification` | Integration | FR-04: Graceful degradation |
| `test_efficacy_auto_detect` | Integration | FR-05: Character → binary conversion |
| `test_sapphire_g_e2e_full` | E2E | FR-07: All scripts complete successfully |
| `test_existing_94_tests_pass` | Regression | No regressions |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-04 | Initial design from SAPPHIRE-G findings | Claude Code |
