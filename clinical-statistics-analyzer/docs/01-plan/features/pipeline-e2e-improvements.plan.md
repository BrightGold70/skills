# Pipeline End-to-End Improvements Planning Document

> **Summary**: Fix pipeline issues discovered during SAPPHIRE-G real-data end-to-end validation
>
> **Project**: clinical-statistics-analyzer
> **Version**: 3.1
> **Author**: Claude Code
> **Date**: 2026-03-04
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Address concrete pipeline issues discovered during end-to-end testing with real SAPPHIRE-G AML study data (27 patients, SPSS .sav format). The test revealed 3 categories of issues: data transformation gaps, R script argument mismatches, and R script bugs.

### 1.2 Background

The SAPPHIRE-G validation achieved **12/14 exact matches** against the published manuscript, confirming the pipeline's core accuracy. However, several issues required manual workarounds:

1. **SPSS value labels not auto-applied to binary outcomes** — `Response` became "ORR"/"Non-ORR" strings but `glm(binomial)` requires 0/1
2. **Analysis profiles argument mismatch** — `analysis_profiles.json` omits required positional args for R scripts
3. **R script bugs** — `21_aml_composite_response.R` crashes when waterfall plot is skipped; `20_aml_eln_risk.R` classifies all as Intermediate when detailed cytogenetic columns are missing

### 1.3 Related Documents

- SAPPHIRE-G test report: This session (2026-03-04)
- Previous PDCA: `docs/archive/2026-03/csa-v31-output-quality-cml/` (97.6% match)
- Pipeline overhaul: `docs/01-plan/features/crf-pipeline-overhaul.plan.md` (98.9% match)

---

## 2. Scope

### 2.1 In Scope

- [x] FR-01: Smart SPSS value label application (categorical display vs numeric regression)
- [x] FR-02: Fix analysis_profiles.json argument specifications
- [x] FR-03: Fix 21_aml_composite_response.R color_map bug
- [x] FR-04: Graceful degradation for 20_aml_eln_risk.R with limited molecular data
- [x] FR-05: Auto-detect outcome variable type (binary 0/1 vs labeled) in efficacy script
- [x] FR-06: Add PFS survival analysis to orchestrator (currently only OS)
- [x] FR-07: Pipeline validation test suite using SAPPHIRE-G as reference dataset

### 2.2 Out of Scope

- New disease type support (e.g., ALL, lymphoma)
- CRF document parsing improvements (separate feature)
- New R analysis scripts
- Multi-study comparison features

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | ValueRecoder produces dual columns: numeric (0/1) for regression + labeled for display. Binary outcome variables (Response, CR, cCR) get `_numeric` suffix for GLM and original column keeps labels. R scripts use `_numeric` variant for `glm(binomial)`. | High | Pending |
| FR-02 | Fix `analysis_profiles.json` args: efficacy needs `["{dataset}", "{outcome_var}", "--disease", "{disease}"]`, survival needs `["{dataset}", "{time_var}", "{status_var}", "--disease", "{disease}"]`. Add `default_outcome_var`, `default_time_var`, `default_status_var` per disease profile as template variables. | High | Pending |
| FR-03 | Fix `21_aml_composite_response.R`: move `color_map` definition outside waterfall conditional block so bar plot works independently. Also fix cCR counting to use labeled `Best_Response` values correctly (CR+CRi+CRh+CRm+MLFS). | High | Pending |
| FR-04 | `20_aml_eln_risk.R`: when >50% of molecular columns are missing, emit warning and use simplified classification (FLT3-ITD + NPM1 + cytogenetics only) instead of full ELN 2022 algorithm. Report which criteria were available vs missing. | Medium | Pending |
| FR-05 | `03_efficacy.R`: auto-detect if outcome variable is numeric 0/1 or character. If character, auto-convert using mapping: positive outcome keywords → 1 (CR, ORR, cCR, Yes, Positive, Response), negative → 0. | Medium | Pending |
| FR-06 | Orchestrator `run_scripts()`: add PFS KM analysis by default when `PFS_months` column exists. Run `04_survival.R` twice: once for OS, once for PFS. | Medium | Pending |
| FR-07 | Create `tests/test_sapphire_g_e2e.py`: end-to-end test using anonymized SAPPHIRE-G fixture data (27 rows, key columns only). Verify transform output column names, response rate counts (ORR=16, CR=10, cCR=15), and R script exit codes. | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Accuracy | Pipeline output matches manuscript within 5% for all baseline variables | Automated comparison test |
| Robustness | Pipeline completes without error on SPSS, CSV, and XLSX inputs | Multi-format test suite |
| Backward Compatibility | Existing 94 tests still pass after changes | `pytest tests/` |
| Performance | Full pipeline (transform + 4 core R scripts) completes in < 120 seconds | Timed E2E test |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] All 7 functional requirements implemented
- [ ] SAPPHIRE-G E2E test passes with 14/14 manuscript matches (fixing BM_Blast mapping and NPM1 delta explanation)
- [ ] All existing 94 tests still pass (zero regressions)
- [ ] `run-analysis` subcommand works end-to-end without manual workarounds
- [ ] R scripts handle both labeled and numeric input gracefully

### 4.2 Quality Criteria

- [ ] Test coverage above 80% for new transformer logic
- [ ] Zero R script crashes on missing optional columns
- [ ] All R scripts produce expected output files

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Dual-column approach (numeric + label) bloats CSV | Low | Medium | Only create dual columns for binary outcomes used in regression (3-4 columns max) |
| R scripts may have other undiscovered column expectations | Medium | Medium | Add column validation step before each R script invocation in orchestrator |
| Anonymized fixture data may not cover all edge cases | Medium | Low | Include edge cases: missing values, single-arm studies, all-same-response |
| Changing efficacy script auto-detection may break CML/HCT analyses | High | Low | Test with all 4 disease types; keep explicit numeric mode as fallback |

---

## 6. Architecture Considerations

### 6.1 Files to Modify

| File | Change | Priority |
|------|--------|----------|
| `scripts/crf_pipeline/transformers/value_recoder.py` | FR-01: Dual-column output for binary outcomes | High |
| `scripts/crf_pipeline/config/analysis_profiles.json` | FR-02: Fix args with template variables | High |
| `scripts/21_aml_composite_response.R` | FR-03: Fix color_map scope + cCR counting | High |
| `scripts/20_aml_eln_risk.R` | FR-04: Graceful degradation | Medium |
| `scripts/03_efficacy.R` | FR-05: Auto-detect outcome type | Medium |
| `scripts/crf_pipeline/orchestrator.py` | FR-02, FR-06: Template variable substitution + PFS | Medium |
| `tests/test_sapphire_g_e2e.py` | FR-07: New E2E test | Medium |

### 6.2 Data Flow (Fixed)

```
Input SPSS/CSV/XLSX
    │
    ├─→ DataParser → parsed data
    ├─→ RuleValidator → validation report
    │
    ▼
Transform Layer
    ├─→ DateCalculator: compute OS_months, PFS_months (skip if pre-computed)
    ├─→ ValueRecoder:
    │     ├─→ Derived columns: OS_status, Treatment_Label, Age_group
    │     ├─→ SPSS label application: Sex, Treatment, molecular markers
    │     └─→ NEW: Binary dual-columns: Response + Response_numeric (0/1)
    └─→ ColumnMapper: CRF names → R names
    │
    ▼
R-Ready CSV
    │
    ├─→ 02_table1.R [subset_csv]
    ├─→ 05_safety.R [full_csv]
    ├─→ 03_efficacy.R [csv] [Response_numeric] --disease aml  ← FR-02 fixed args
    ├─→ 04_survival.R [csv] [OS_months] [OS_status] --disease aml
    ├─→ 04_survival.R [csv] [PFS_months] [PFS_status] --disease aml  ← FR-06 PFS
    ├─→ 20_aml_eln_risk.R [csv]  ← FR-04 graceful degradation
    └─→ 21_aml_composite_response.R [csv]  ← FR-03 bug fix
```

### 6.3 Template Variable System for analysis_profiles.json

```json
{
  "scripts": [
    {
      "name": "03_efficacy.R",
      "args": ["{dataset}", "{outcome_var}", "--disease", "{disease}"],
      "template_vars": {
        "outcome_var": "default_outcome_var"
      }
    },
    {
      "name": "04_survival.R",
      "args": ["{dataset}", "{time_var}", "{status_var}", "--disease", "{disease}"],
      "template_vars": {
        "time_var": "default_time_var",
        "status_var": "default_status_var"
      }
    }
  ],
  "default_outcome_var": "Response_numeric",
  "default_time_var": "OS_months",
  "default_status_var": "OS_status"
}
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` has coding conventions section
- [x] R scripts follow numbered execution order (02-29)
- [x] Python follows stateless parser pattern: `__init__(config)` + method → Dict
- [x] Output formats: .docx tables, .eps figures
- [x] Config-driven disease field mapping via JSON

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| **Binary outcome naming** | Inconsistent (Response=label, CR=numeric) | `*_numeric` suffix for GLM-ready columns | High |
| **R script argument order** | Documented in script headers | Enforce via analysis_profiles.json validation | High |
| **Missing column handling** | Per-script, inconsistent | Standard `tryCatch` + warning pattern for all R scripts | Medium |

### 7.3 Environment Variables

| Variable | Purpose | Scope | Status |
|----------|---------|-------|:------:|
| `CSA_OUTPUT_DIR` | R script output base | All R scripts | Exists |
| `CRF_OUTPUT_DIR` | CRF pipeline output | Python pipeline | Exists |

---

## 8. Implementation Phases

### Phase 1: Critical Fixes (FR-01, FR-02, FR-03)
1. Fix value_recoder dual-column output
2. Fix analysis_profiles.json with template variables
3. Fix orchestrator template variable substitution
4. Fix 21_aml_composite_response.R color_map bug

### Phase 2: Robustness (FR-04, FR-05)
1. Add graceful degradation to 20_aml_eln_risk.R
2. Add auto-detection to 03_efficacy.R

### Phase 3: Enhancement + Testing (FR-06, FR-07)
1. Add PFS survival analysis to orchestrator
2. Create SAPPHIRE-G E2E test suite
3. Run full regression test suite

---

## 9. SAPPHIRE-G Validation Reference

### Exact Matches (12/14)
N=27, Sex 15M/12F, Age median 63, ECOG 0-1 48.1%, Primary refractory 8, Early relapse 16, FLT3-ITD+ 25 (92.6%), Hb 9.2, WBC 12.6, Plt 40.5, ORR 16 (59.3%), cCR 15 (55.6%), CR 10 (37.0%)

### Discrepancies
- NPM1+ (9 vs 7): Data version difference SPSS 2024-11 vs manuscript 2025-07
- BM blast median (14.0% vs 54.0%): `blast_Rel` has 7/27 missing + 3 zeros; likely different data version

---

## 10. Next Steps

1. [ ] Write design document (`pipeline-e2e-improvements.design.md`)
2. [ ] Implement Phase 1 critical fixes
3. [ ] Re-run SAPPHIRE-G E2E test to validate

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-04 | Initial draft from SAPPHIRE-G E2E test findings | Claude Code |
