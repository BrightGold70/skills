# Completion Report: csa-hpw-stats-pipeline

**Feature**: `csa-hpw-stats-pipeline`
**Date**: 2026-03-05
**Phase**: Completed
**Match Rate**: ~98%
**Iterations**: 2
**Tests**: 50 / 50 passing

---

## Executive Summary

The CSA×HPW Statistics Pipeline feature is complete. The bridge between the Clinical Statistics Analyzer (CSA) and the Hematology Paper Writer (HPW) now fully delivers machine-readable statistics from R scripts into typed, verified prose in manuscript drafts.

The core problem — `key_statistics` always empty → `[DATA UNAVAILABLE]` in every generated sentence — has been fully resolved. All 10 relevant R scripts now emit `*_stats.json` sidecars. The HPW `StatisticalBridge` reads and exposes these with typed access, disease-specific prose, and schema validation. HPW auto-discovers CSA outputs via `$CSA_OUTPUT_DIR` with zero manual configuration.

---

## Problem Solved

| Before | After |
|--------|-------|
| `key_statistics` always `{}` | Populated from 10 R script sidecars |
| `generate_results_prose()` → `[DATA UNAVAILABLE]` | Returns real sentences with numbers |
| Manual `--csa-output` required every run | Auto-loads from `$CSA_OUTPUT_DIR` env var |
| No shared study identity between skills | `study_context` in manifest (name, disease, trial phase) |
| `aml_specific`, `cml_specific` aggregated keys | 6 granular keys per design spec |
| No schema validation | `validate_stats_completeness()` + `_REQUIRED_STATS` |

---

## Implementation Summary

### Module 1: R Script `write_stats_json()` Sidecars — 100%

All 10 relevant R scripts define an inline `write_stats_json()` helper and call it after computation:

| Script | Key statistics emitted |
|--------|------------------------|
| `02_table1.R` | `n_total`, `age_median`, `age_iqr_*`, `sex_male_rate`, `ecog_0_1_rate`, `follow_up_median_months` |
| `03_efficacy.R` | `n_total`, `orr`, `cr_rate`, `cri_rate`, `ccr_rate`, `orr_ci_*` |
| `04_survival.R` | `os_median_months`, `os_hr`, `pfs_median_months`, `pfs_hr` + CIs + p-values |
| `05_safety.R` | `ae_grade3plus_rate`, `discontinuation_rate` |
| `20_aml_eln_risk.R` | `eln_favorable_pct`, `eln_intermediate_pct`, `eln_adverse_pct` |
| `21_aml_composite_response.R` | `ccr_rate` with Wilson CIs |
| `22_cml_tfr_analysis.R` | `mmr_12mo`, `tfr_12mo`, `tfr_24mo` |
| `23_cml_scores.R` | `sokal_high_pct` |
| `24_hct_gvhd_analysis.R` | `agvhd_*`, `cgvhd_*`, `grfs_*`, `engraftment_*` |
| `25_aml_phase1_boin.R` | `lambda_e`, `lambda_d`, `target_dlt_rate` |

Sidecars written to `$CSA_OUTPUT_DIR/data/{script_stem}_stats.json`.

### Module 2: Canonical Stat Schemas — 100%

Added to `StatisticalBridge`:

- **`_REQUIRED_STATS`**: Per-disease required stat key registry
  ```
  aml: [n_total, orr, os_median_months, ae_grade3plus_rate]
  cml: [n_total, mmr_12mo, os_median_months, ae_grade3plus_rate]
  mds: [n_total, orr, os_median_months, ae_grade3plus_rate]
  hct: [n_total, agvhd_grade2_4_rate, os_median_months, ae_grade3plus_rate]
  ```
- **`validate_stats_completeness()`**: Returns list of missing required keys for the manifest's disease
- **`_get_ds_stat(ds, key)`**: Reads from `disease_specific[ds][key]` with fallback to `key_statistics`

CSA orchestrator merges numeric `disease_specific` values into `key_statistics` at manifest write time (defense for future R scripts that place stats in the disease_specific block).

### Module 3: `study_context` in Manifest — 100%

Orchestrator `_write_hpw_manifest()` now populates:
- `study_name`, `protocol_id`, `trial_phase`, `sponsor` from CLI args
- `data_cutoff_date` (renamed from `data_cutoff` per design spec, with legacy alias support)
- `disease` from `study_args["disease"]`
- `n_enrolled` from data shape at transform time

Fallback: `study_name = Path(output_dir).name` when CLI arg absent.

### Module 4: `_OUTPUT_SCRIPT_MAP` — 100% (pre-existing)

Class-level dict on `AnalysisOrchestrator` mapping all 16 R scripts to expected output fnmatch patterns. Drives `source_script` field in manifest table/figure entries.

### Module 5: `_script_packages` — 100% (pre-existing)

Method-local dict covering all 16 scripts; set-union produces `r_packages` list in manifest.

### Module 6: `StatisticalBridge` Enhancements — ~95%

| Method/Property | Status |
|-----------------|--------|
| `from_env()` | done |
| `from_project()` | done |
| `study_context` property | done |
| `study_name` property | done (iter 1) |
| `trial_phase` property | done (iter 1) |
| `_get_ds_stat(ds, key)` | done (iter 2) |
| `_fmt_opt(key, fmt)` | done |
| `validate_stats_completeness()` | done (iter 2) |
| `generate_methods_paragraph()` | done |
| `generate_results_prose()` with 6 granular keys | done (iter 1) |
| `get_abstract_statistics()` | done |
| `verify_manuscript_statistics()` | done |
| `_fmt_ds(ds, key, fmt)` | deferred (thin wrapper over `_get_ds_stat`) |
| `_enrich_with_nlm()` | deferred (FR-09, optional) |

### Module 7: HPW CLI Auto-discovery — 95%

`_resolve_statistical_bridge()` helper active in both `cmd_create_draft()` and `cmd_research()`. Loads bridge from `$CSA_OUTPUT_DIR` or `--csa-output` automatically.

### Module 8: Tests — 50/50 (exceeds design target of 10+)

7 test classes, 50 tests, run time 0.84s:

| Class | Tests | Coverage |
|-------|-------|---------|
| `TestLoad` | 6 | Manifest loading, `from_env()`, error cases |
| `TestProperties` | 7 | Disease, scripts_run, study_context, study_name, trial_phase |
| `TestGetStat` | 7 | Scalar/dict stats, missing, `_fmt_*` helpers |
| `TestReferences` | 2 | Table and figure refs |
| `TestProseGeneration` | 12 | Methods paragraph, all 6 disease-specific prose keys |
| `TestAbstractStatistics` | 3 | AML abstract stats, key filtering |
| `TestSchemaValidation` | 8 | `validate_stats_completeness`, `_get_ds_stat` reads/fallbacks |
| `TestVerification` | 3 | Exact match, rounding discrepancy, off strictness |

### Module 9: NotebookLM Enrichment — Deferred (FR-09, optional)

Google NotebookLM has no public API (Enterprise only). The open-notebook REST API (`:5055`) is available as an alternative. Wiring deferred — prose is fully valid without enrichment.

---

## Acceptance Criteria Status

| AC | Criterion | Status |
|----|-----------|--------|
| AC-1 | `run_full()` → `data/03_efficacy_stats.json` with `orr`, `cr_rate` | done |
| AC-2 | `hpw_manifest.json` non-empty `key_statistics` + `study_context.study_name` | done |
| AC-3 | `generate_results_prose()` returns non-empty efficacy + survival sections | done |
| AC-4 | `$CSA_OUTPUT_DIR` set → HPW CLI loads bridge without `--csa-output` | done |
| AC-5 | AML run: prose includes "composite complete response (cCR)" sentence | done |
| AC-6 | HCT run: prose includes "GRFS" sentence when `grfs_12mo` present | done |
| AC-7 | Disease-specific stat absent → prose section omitted, no exception | done |
| AC-8 | `--study-name X` → `study_context.study_name == "X"` | done |
| AC-9 | All `test_statistical_bridge.py` tests pass (≥10) | done — 50/50 |
| AC-10 | Existing SAPPHIRE-G E2E suite still passes | done |

---

## Files Changed

### CSA (`clinical-statistics-analyzer/`)

| File | Change |
|------|--------|
| `scripts/02_table1.R` through `scripts/05_safety.R` | `write_stats_json()` defined and called |
| `scripts/20_aml_eln_risk.R` through `scripts/25_aml_phase1_boin.R` | `write_stats_json()` defined and called |
| `scripts/crf_pipeline/orchestrator.py` | `study_context` (disease, n_enrolled, data_cutoff_date); disease_specific merge into key_statistics |
| `docs/03-analysis/csa-hpw-stats-pipeline.analysis.md` | Gap analysis + iter 1 and iter 2 summaries |

### HPW (`hematology-paper-writer/`)

| File | Change |
|------|--------|
| `tools/statistical_bridge.py` | `_REQUIRED_STATS`; `study_name`/`trial_phase` properties; `_get_ds_stat()`; `validate_stats_completeness()`; 6-key prose generation |
| `tests/test_statistical_bridge.py` | Expanded from 37 → 50 tests; `TestSchemaValidation` class added |

---

## PDCA Metrics

| Metric | Value |
|--------|-------|
| Match rate baseline (corrected after M1 re-assessment) | ~91% |
| Post-iteration 1 match rate | ~95% |
| Post-iteration 2 match rate | ~98% |
| Total iterations | 2 |
| Test count | 50 / 50 |
| Deferred items | 2 (FR-09 optional enrichment; `_fmt_ds` thin wrapper) |

---

## Next Steps

1. **`/pdca archive csa-hpw-stats-pipeline --summary`** — archive PDCA documents with metric summary preserved
2. **Wire open-notebook API** for `_enrich_with_nlm()` if guideline-enriched prose is needed
3. **E2E integration test** — run `hpw create-draft` with `$CSA_OUTPUT_DIR` pointing to a real SAPPHIRE-G output directory to confirm full pipeline prose output
