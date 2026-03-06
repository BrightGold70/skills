# Plan: CSA×HPW Statistics Pipeline (Approach 2)

**Feature**: `csa-hpw-stats-pipeline`
**Date**: 2026-03-05
**Status**: Plan
**Skills Affected**: clinical-statistics-analyzer (CSA), hematology-paper-writer (HPW)

---

## Problem Statement

The CSA→HPW bridge (`hpw_manifest.json` → `StatisticalBridge`) exists in code but is functionally broken:

1. **Statistics don't flow**: R scripts write `.docx` tables and `.eps` figures but never write machine-readable statistics. The manifest's `key_statistics` field is always empty. `StatisticalBridge.generate_results_prose()` returns `[DATA UNAVAILABLE]` for every numeric value.

2. **No automatic handoff**: After CSA completes, HPW requires manual configuration to locate outputs. `StatisticalBridge.from_env()` exists but is not wired into the HPW CLI. There is also no shared study identity (study name, protocol ID) linking the two skills.

3. **Disease-specific gaps**: Six new disease-specific R scripts (20–25: AML ELN risk, AML composite response, CML TFR, CML scores, HCT GVHD, AML Phase 1 BOIN) have no JSON sidecar output, no `_script_packages` mapping, and no prose templates in `StatisticalBridge`.

---

## Goals

- R script statistics reach HPW as typed, verified numbers (not placeholders)
- HPW auto-discovers CSA outputs via `$CSA_OUTPUT_DIR` with zero manual config
- Both skills share a common study identity (study name, disease, trial phase)
- Disease-specific prose covers AML (cCR, ELN risk), CML (BCR-ABL kinetics, TFR), HCT (GRFS, aGVHD/cGVHD)

---

## Shared Study Context Design

**Core question**: how do CSA and HPW know they belong to the same study?

**Decision: `study_context` embedded in `hpw_manifest.json`**

CSA's orchestrator writes a `study_context` block when generating the manifest. HPW reads it via `StatisticalBridge`. No separate config file needed — the manifest is the single source of truth.

```json
{
  "study_context": {
    "study_name": "SAPPHIRE-G",
    "protocol_id": "SAPPHIRE-2024-001",
    "disease": "aml",
    "trial_phase": "2",
    "sponsor": "",
    "data_cutoff_date": "2025-12-31",
    "n_enrolled": 27
  }
}
```

**Setting study context**:
- CSA CLI: `--study-name SAPPHIRE-G --protocol-id SAPPHIRE-2024-001 --trial-phase 2`
- Falls back to `study_name = Path(output_dir).name` (directory name) if not specified
- HPW reads from `StatisticalBridge.study_context` property; uses `study_name` + `disease` for manuscript naming

**HPW manuscript naming**: `{study_name}_{disease.upper()}_draft.docx` (e.g., `SAPPHIRE-G_AML_draft.docx`)

---

## Functional Requirements

### FR-01: Core R scripts emit `*_stats.json` sidecars
**Scripts**: `02_table1.R`, `03_efficacy.R`, `04_survival.R`, `05_safety.R`, `10_sample_size.R`

Each script writes `data/{script_stem}_stats.json` alongside its `.docx`/`.eps` outputs.

**Standard sidecar schema**:
```json
{
  "key_statistics": {
    "n_total": 27,
    "orr": {"value": 67.3, "unit": "percent", "ci_lower": 54.1, "ci_upper": 78.7, "p_value": 0.001},
    "os_median_months": {"value": 14.2, "unit": "months", "ci_lower": 11.1, "ci_upper": 18.6},
    "os_hr": {"value": 0.62, "ci_lower": 0.41, "ci_upper": 0.94, "p_value": 0.024},
    "ae_grade3plus_rate": {"value": 42.0, "unit": "percent"}
  },
  "analysis_notes": {
    "survival_model": "Cox proportional hazards; cox.zph PH assumption verified",
    "multiple_testing": "All tests two-sided; p < 0.05 considered significant"
  }
}
```

**Output path**: `$CSA_OUTPUT_DIR/data/{script_stem}_stats.json`

### FR-02: Disease-specific R scripts emit `*_stats.json` sidecars (graceful)
**Scripts**: `20_aml_eln_risk.R`, `21_aml_composite_response.R`, `22_cml_tfr_analysis.R`, `23_cml_scores.R`, `24_hct_gvhd_analysis.R`, `25_aml_phase1_boin.R`

Disease-specific stats populate a `disease_specific` block (separate from `key_statistics`):
```json
{
  "disease_specific": {
    "eln_favorable_rate": {"value": 33.3, "unit": "percent"},
    "ccr_rate": {"value": 77.8, "unit": "percent"},
    "agvhd_grade2plus_rate": {"value": 38.5, "unit": "percent"},
    "grfs_12mo": {"value": 62.1, "unit": "percent"}
  }
}
```

HPW degrades gracefully when disease-specific stats are absent (omits those prose sentences).

### FR-03: Orchestrator `_script_packages` updated for disease-specific scripts
Add R package mappings for scripts 20–25 (e.g., `20_aml_eln_risk.R` → `["flextable", "officer", "ggplot2"]`).

### FR-04: `study_context` added to `hpw_manifest.json`
CSA orchestrator's `_write_hpw_manifest()` populates `study_context` from:
1. CLI args `--study-name`, `--protocol-id`, `--trial-phase`, `--sponsor`, `--data-cutoff`
2. Fallback: `study_name = Path(output_dir).name`

CSA CLI (`cli.py`) exposes these args on `run` and `run-analysis` subcommands.

### FR-05: HPW CLI auto-discovers manifest from `$CSA_OUTPUT_DIR`
Wire `StatisticalBridge.from_env()` into HPW `cli.py`. When `$CSA_OUTPUT_DIR` is set and `--csa-output` is not provided, the bridge loads automatically.

`StatisticalBridge` gains a `study_context` property returning the `study_context` dict.

### FR-06: `source_script` populated on each table/figure manifest entry
Orchestrator's manifest-writing logic populates `source_script` from `expected_outputs` in analysis profiles, not just filename heuristics.

### FR-07: Disease-specific prose in `StatisticalBridge`
`generate_results_prose()` extended with disease-aware sections:

| Disease | Section | New prose keys |
|---------|---------|----------------|
| AML | efficacy | `ccr_rate`, `eln_favorable_rate`, `eln_adverse_rate` |
| CML | efficacy | `mmr_rate`, `ccyr_rate`, `tfr_rate`, `bcr_abl_log_reduction` |
| HCT | survival | `grfs_12mo`, `agvhd_grade2plus_rate`, `cgvhd_moderate_severe_rate` |

All prose omitted gracefully if stat absent.

### FR-08: Tests
- `tests/test_statistical_bridge.py` — ≥10 unit tests for `StatisticalBridge` with populated manifest
- Python smoke test: mock manifest → `generate_results_prose()` returns non-empty sections per disease
- SAPPHIRE-G E2E suite (15 existing tests) must still pass

### FR-09: NotebookLM guideline enrichment of results prose (optional)
`StatisticalBridge.generate_results_prose()` optionally enriches disease-specific sentences with guideline context from `NotebookLMIntegration`.

**Prerequisite**: `hpw-notebooklm-py` is now ARCHIVED (100%) — `NotebookLMIntegration` makes real async calls via `notebooklm-py` to the single Hematology Guidelines notebook (`f47cebf8…`).

**Notebook scope** (each notebook covers multiple diseases):
| Notebook type | Covers | What it answers |
|---------------|--------|----------------|
| `classification` | ALL diseases (AML, CML, MDS, HCT, …) | WHO 2022 / ICC 2022 disease classification definitions; response criteria definitions (CR, CRi, MMR, etc.) |
| `therapeutic` | AML + CML (and others) | ELN 2022/2025 risk stratification; treatment response thresholds; milestone definitions |
| `gvhd` | HCT | NIH 2014 aGVHD/cGVHD grading; GRFS definition |
| `nomenclature` | ALL diseases | BCR::ABL1 notation; HGVS 2024; ISCN 2024 |

**Query routing by stat key**:
| Stat key | Primary notebook | Secondary notebook | Example enrichment |
|----------|-----------------|-------------------|-------------------|
| `ccr_rate`, `cr_rate`, `cri_rate` (AML) | `classification` | `therapeutic` | "cCR (CR+CRi+CRh+MLFS) per ELN 2022" |
| `eln_favorable_rate`, `eln_adverse_rate` (AML) | `therapeutic` | `classification` | "per ELN 2022 risk stratification" |
| `mmr_rate`, `ccyr_rate` (CML) | `classification` | `therapeutic` | "MMR (BCR::ABL1IS ≤0.1%) per ELN 2020" |
| `tfr_rate`, `bcr_abl_log_reduction` (CML) | `therapeutic` | — | "TFR attempt per ELN 2020 milestone criteria" |
| `hi_rate`, `transfusion_independence_rate` (MDS) | `classification` | `therapeutic` | "per IWG 2006 HI criteria" |
| `agvhd_grade2plus_rate`, `cgvhd_moderate_severe_rate` (HCT) | `gvhd` | `classification` | "graded per NIH 2014 consensus" |
| `grfs_12mo` (HCT) | `gvhd` | — | "GRFS (GVHD-free, relapse-free survival) at 12 months" |

**Rule**: always query `classification` first for response-rate stats (it defines the criteria); query `therapeutic` for risk/milestone stats.

**Invocation pattern** (in `StatisticalBridge`):
```python
from tools.notebooklm_integration import NotebookLMIntegration
nlm = NotebookLMIntegration()
guideline_ctx = nlm.query_classification_guidelines(f"ELN 2022 definition of {stat_key}")
# Append as parenthetical to prose sentence; skip silently if nlm unavailable
```

**Degradation**: If `notebooklm_config.json` is absent or the query fails, the prose sentence is emitted without enrichment — no exception raised.

**Scope**: Enrichment is a single appended parenthetical per sentence, not a full paragraph. Keep prose density appropriate for manuscript Results section.

---

## Implementation Phases

| Phase | Scope | Files |
|-------|-------|-------|
| 1 | Core R sidecar output | `02–05_*.R`, `10_sample_size.R` |
| 2 | `study_context` + CSA CLI args | `orchestrator.py`, `cli.py` |
| 3 | Disease-specific sidecars + orchestrator | `20–25_*.R`, `orchestrator.py` |
| 4 | HPW updates | `statistical_bridge.py`, `cli.py` (HPW) |
| 5 | Tests | `test_statistical_bridge.py` |

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `run_full()` with SAPPHIRE-G mock → `data/03_efficacy_stats.json` with `orr`, `cr_rate` |
| AC-2 | `hpw_manifest.json` has non-empty `key_statistics` and `study_context.study_name` |
| AC-3 | `StatisticalBridge.generate_results_prose()` returns non-empty efficacy + survival sections |
| AC-4 | `$CSA_OUTPUT_DIR` set → HPW CLI loads bridge without `--csa-output` flag |
| AC-5 | AML run: prose includes "composite complete response (cCR)" sentence |
| AC-6 | HCT run: prose includes "GRFS" sentence when `grfs_12mo` present |
| AC-7 | Disease-specific stat absent → prose section omitted, no exception |
| AC-8 | `--study-name SAPPHIRE-G` → manifest `study_context.study_name == "SAPPHIRE-G"` |
| AC-9 | All `test_statistical_bridge.py` tests pass (≥10) |
| AC-10 | Existing SAPPHIRE-G E2E suite (15 tests) still passes |

---

## Out of Scope

- Bidirectional flow (HPW triggering CSA re-runs)
- Watch mode / event-driven manifest detection
- Deep HPW PhaseManager integration (Approach 3)
- New R scripts beyond 20–25

---

## Files Changed

### CSA (`clinical-statistics-analyzer/`)
| File | Change |
|------|--------|
| `scripts/02_table1.R` | Add `write_stats_json()` helper + call |
| `scripts/03_efficacy.R` | Add `write_stats_json()` helper + call |
| `scripts/04_survival.R` | Add `write_stats_json()` helper + call |
| `scripts/05_safety.R` | Add `write_stats_json()` helper + call |
| `scripts/20_aml_eln_risk.R` | Add disease-specific sidecar |
| `scripts/21_aml_composite_response.R` | Add disease-specific sidecar |
| `scripts/22_cml_tfr_analysis.R` | Add disease-specific sidecar |
| `scripts/23_cml_scores.R` | Add disease-specific sidecar |
| `scripts/24_hct_gvhd_analysis.R` | Add disease-specific sidecar |
| `scripts/25_aml_phase1_boin.R` | Add disease-specific sidecar |
| `scripts/crf_pipeline/orchestrator.py` | `study_context`; `source_script`; `_script_packages` |
| `scripts/crf_pipeline/cli.py` | `--study-name`, `--protocol-id`, `--trial-phase`, `--sponsor`, `--data-cutoff` |
| `tests/test_statistical_bridge.py` | New: ≥10 unit tests |

### HPW (`hematology-paper-writer/`)
| File | Change |
|------|--------|
| `tools/statistical_bridge.py` | `study_context` property; disease-specific prose; optional NotebookLM enrichment (FR-09) |
| `cli.py` | `StatisticalBridge.from_env()` auto-discovery wired in |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| R variable names differ from canonical stat key names | Medium | Define canonical key mapping per script in design doc; validate with SAPPHIRE-G |
| `study_context` fallback produces ugly names | Low | Documented; `--study-name` overrides always available |
| HPW auto-discovery conflicts with existing `--csa-output` | Low | `from_env()` only runs when `--csa-output` not provided |
| Disease-specific scripts skipped (missing columns) | Low | Sidecars only written on script success; HPW degrades gracefully |
| FR-09: `notebooklm-py` not installed / browser auth not set up | Low | `notebooklm_config.json` absence → enrichment silently skipped; prose still valid |
| FR-09: `AskResult.sources` unavailable (library limitation) | Low | Known from `hpw-notebooklm-py`; use `result.answer` only; guideline text sufficient |
| FR-09: async `asyncio.run()` conflicts if HPW ever moves to async CLI | Low | HPW is synchronous today; bridge pattern is safe; revisit if HPW adopts asyncio |
