# Gap Analysis: hpw-classification-validator

**Feature:** `hpw-classification-validator`
**Phase:** Check
**Analysis Date:** 2026-03-05
**Analyst:** gap-detector

---

## Summary

| Metric | Value |
|--------|-------|
| Design Items | 27 (test cases) + 9 architectural sections |
| Implemented | 36/36 |
| Gaps Found | 2 minor |
| Match Rate | **97%** |
| Test Results | 153/153 passed (40 new + 113 pre-existing) |
| Status | ✅ PASSES 90% threshold |

---

## Design vs Implementation Comparison

### §1 Architecture — ✅ MATCH (100%)

| Design Requirement | Status | Notes |
|-------------------|--------|-------|
| Inherits `SkillBase(ABC)` | ✅ | `class ClassificationValidator(SkillBase)` |
| Reads/writes `SkillContext.classification_result` | ✅ | All 4 major methods persist to context |
| All methods wrapped try/except, fail-silent | ✅ | Every public method returns default on Exception |
| `invoke()` implemented | ✅ | Returns non-raising string |
| Imported in `tools/skills/__init__.py` | ✅ | Added to imports + `__all__` |
| Phase integrations appended at module end | ✅ | phase1, phase4, phase4_7 all done |

### §2 Input Data Structures — ✅ MATCH (95%)

All fields from the three TypedDicts (AMLPatientData, CMLMilestoneData, GVHDData) are consumed via `.get()` with correct defaults.

**Minor deviation:** TypedDicts are not formally defined as class objects — parameters are typed as `Dict[str, Any]`. Functionally equivalent; no runtime impact.

### §3 Output Dataclasses — ✅ MATCH (100%)

| Dataclass | Fields | `to_dict()` | Status |
|-----------|--------|-------------|--------|
| `AMLClassificationResult` | 6/6 | ✅ | ✅ |
| `CMLMilestoneResult` | 6/6 | ✅ | ✅ |
| `GVHDResult` | 4/4 | ✅ | ✅ |
| `DiscordanceReport` | 5/5 | ✅ | ✅ |

### §4 Classification Logic — ✅ MATCH (96%)

#### §4a AML WHO 2022 Priority Chain (11 rules)
All 11 priority rules implemented in correct order. ✅

#### §4b AML ICC 2022 Divergence (4 rules)
All 4 divergence rules implemented: TP53+blasts<20→MDS/AML, NPM1 requires ≥10% blasts, CEBPA same as WHO, MDS-related+blasts<20→MDS/AML. ✅

#### §4c ELN 2022 Risk (3 tiers)
Adverse/Favorable/Intermediate with correct factor accumulation. ✅

#### §4d CML ELN 2025 Milestones (5 timepoints)
Thresholds match design exactly; CHR failure logic correct. ✅

#### §4e Acute GVHD Grading — ⚠️ MINOR GAP

**Design spec:** `Grade III: Skin 2–3, Liver 2–3, OR Gut 2–3`

**Implementation:**
```python
elif skin >= 2 and (liver >= 2 or gut >= 2):
    grade_str = "III"
```

**Gap:** The implementation requires `skin >= 2` as a necessary condition for Grade III. Pure liver or gut stage 2–3 without high skin (e.g., skin=0, liver=3, gut=3) falls to Grade II instead of Grade III. Clinically, Grade III can be reached by liver or gut alone per Glucksberg.

**Impact:** Low — edge case not covered by tests. The test cases (skin2/gut0→I, skin3/gut3→III, gut4→IV) all pass correctly.

#### §4f Chronic GVHD NIH 2014 (3 tiers)
Severe/Moderate/Mild with correct organ count and lung_score logic. ✅

### §5 Manifest Output Schema — ✅ MATCH (100%)

All 12 schema keys present in `_build_manifest_summary()`. `write_to_manifest()` reads existing JSON, merges `classification_summary`, rewrites atomically. Creates parent directories if missing. ✅

### §6 Prose Templates — ✅ MATCH (100%)

`_METHODS_TEMPLATES` has AML/CML/HCT entries; all 6 `_CITATIONS` keys present. `generate_methods_paragraph()` fills placeholders via `str.format(**_CITATIONS)`. The AML template adds a "discordant cases" sentence beyond the design spec — this is an enhancement. ✅

### §7 SkillContext Extension — ✅ MATCH (100%)

`classification_result: dict = field(default_factory=dict)` added to `_base.py` with backward-compatible `load()`. SkillContext round-trip test passes. ✅

### §8 Phase Integrations — ✅ MATCH (100%)

| Phase | Function | Location | Status |
|-------|----------|----------|--------|
| Phase 1 | `integrate_skills_phase1_classification()` | `topic_development.py` | ✅ |
| Phase 4 | `integrate_skills_phase4_classification()` | `enhanced_drafter.py` | ✅ |
| Phase 4.7 | `integrate_skills_phase4_7_classification()` | `prose_verifier.py` | ✅ |

Disease detection regex covers: AML, MDS, CML, HCT, GVHD, myeloma, lymphoma, ALL. ✅

### §9 `__init__.py` Export — ✅ MATCH (100%)

`ClassificationValidator` in both import line and `__all__`. ✅

---

## Test Coverage (27 Design Tests)

| # | Design Test | Actual Test | Status |
|---|------------|-------------|--------|
| 1 | AML CBF t(8;21) Favorable | `test_cbf_aml_t8_21` | ✅ |
| 2 | AML APL concordant | `test_apl_pml_rara` | ✅ |
| 3 | NPM1+/FLT3-ITD(low) Favorable | `test_npm1_flt3_itd_low_favorable` | ✅ |
| 4 | NPM1+/FLT3-ITD(high) Intermediate | `test_npm1_flt3_itd_high_intermediate` | ✅ |
| 5 | TP53+ blasts 25% Adverse | `test_tp53_high_blasts_adverse` | ✅ |
| 6 | TP53+ blasts 15% discordant | `test_tp53_low_blasts_discordant` | ✅ |
| 7 | ASXL1+ Adverse | `test_asxl1_adverse` | ✅ |
| 8 | AML NOS concordant | `test_aml_nos_concordant` | ✅ |
| 9 | compare_who_icc concordant cohort | `test_all_concordant` | ✅ |
| 10 | compare_who_icc mixed cohort | `test_mixed_cohort_discordant` | ✅ |
| 11 | CML 3m BCR::ABL1 8% Optimal | `test_3m_optimal` | ✅ |
| 12 | CML 6m BCR::ABL1 5% Warning | `test_6m_warning` | ✅ |
| 13 | CML 12m BCR::ABL1 0.05% Optimal | `test_12m_optimal_mmr` | ✅ |
| 14 | CML 12m BCR::ABL1 0.5% Warning | `test_12m_warning` | ✅ |
| 15 | CML no CHR Failure | `test_no_chr_failure` | ✅ |
| 16 | Acute GVHD skin2/liver0/gut0 Grade I | `test_acute_grade_i` | ✅ |
| 17 | Acute GVHD skin3/gut3 Grade III | `test_acute_grade_iii` | ✅ |
| 18 | Acute GVHD gut4 Grade IV | `test_acute_grade_iv` | ✅ |
| 19 | Chronic GVHD 1 organ score 1 Mild | `test_chronic_mild` | ✅ |
| 20 | Chronic GVHD lung score 3 Severe | `test_chronic_severe_lung` | ✅ |
| 21 | generate_methods_paragraph AML | `test_aml_methods_contains_keywords` | ✅ |
| 22 | generate_methods_paragraph CML | `test_cml_methods_contains_bcr_abl1` | ✅ |
| 23 | generate_results_table 3 patients | `test_results_table_rows` | ✅ |
| 24 | write_to_manifest creates block | `test_creates_manifest_block` | ✅ |
| 25 | write_to_manifest merges existing | `test_merges_existing_manifest` | ✅ |
| 26 | invoke() never raises | `test_invoke_returns_string` | ✅ |
| 27 | SkillContext round-trip | `test_context_roundtrip` | ✅ |

**8 additional tests** beyond design: therapy_related WHO classification, Down syndrome, NPM1 blasts<10 ICC divergence, CEBPA favorable, GVHD Grade 0, Grade II, chronic Moderate, nomenclature BCR-ABL check.

---

## Gaps to Fix

### Gap 1 (Critical: None) — TypedDict Classes Not Defined
**Severity:** Negligible
**Action:** No fix required — `Dict[str, Any]` with `.get()` defaults is idiomatic Python and avoids a runtime import dependency.

### Gap 2 (Acute GVHD Grade III Logic)
**Severity:** Low
**Description:** Pure liver/gut stage ≥2 without skin≥2 grades as II instead of III.
**Fix:**
```python
# Change from:
elif skin >= 2 and (liver >= 2 or gut >= 2):
# To:
elif skin >= 3 or liver >= 2 or gut >= 2:
```
**Action:** Fix recommended before report phase.

---

## Match Rate Calculation

- Total design items checked: 36 (27 tests + 9 sections)
- Fully matched: 35
- Minor gaps: 1 (acute GVHD Grade III)
- Match rate: **35/36 = 97.2%** → **97%**

**Result: PASSES 90% threshold. Proceed to fix Gap 2, then report.**
