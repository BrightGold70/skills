# Plan: HPW Classification Validator

**Feature:** `hpw-classification-validator`
**Phase:** Plan
**Created:** 2026-03-05
**Status:** 📋 Planning

---

## 1. Overview

Port the patient-data classification logic from **HemaCalc** (iOS) into a new HPW skill
`ClassificationValidator` covering AML (WHO 2022 vs ICC 2022), CML (ELN 2025 milestones),
and HCT/GVHD (NIH grading). The skill generates:

1. Manuscript-ready prose and tables (Methods + Results sections)
2. A `classification_summary` block written to the CSA `hpw_manifest.json`

**Motivation:** `WHOICCComparator` in `tools/nomenclature_checker.py` is a static text
lookup only — it maps entity names to WHO/ICC description strings. It cannot classify
a patient from raw data (blasts%, cytogenetics, mutations). HemaCalc has that runtime
logic; this feature ports it to Python and wires it into HPW phases 1, 4, and 4.7.

---

## 2. Scope

| Disease | Logic Source (HemaCalc) | HPW Phase Target |
|---------|------------------------|-----------------|
| AML — WHO 2022 | `MyeloidClassifier.classifyAMLWHO()` | Phase 1, 4, 4.7 |
| AML — ICC 2022 | `ICCClassifier.classifyAMLICC()` | Phase 1, 4, 4.7 |
| AML — discordance | `ClassificationEngine.identifyDifferences()` | Phase 4 |
| CML — ELN 2025 milestones | `CMLResponseCalculator.assessMilestone()` | Phase 4 |
| HCT/GVHD — NIH grading | `AcuteGVHDInputView` / `ChronicGVHDInputView` logic | Phase 4 |

**Out of scope (this feature):**
- MDS classification (separate IPSS-R focus; future feature)
- Myeloma, Lymphoma, ALL (future `30_myeloma_response.R` track)
- KaryotypeParser / NGSParser Python ports (separate CSA feature)

---

## 3. New File

### `hematology-paper-writer/tools/skills/classification_validator.py`

**Class:** `ClassificationValidator(SkillBase)`

Core methods:

| Method | Input | Output |
|--------|-------|--------|
| `classify_aml(data)` | `AMLPatientData` dict | `AMLClassificationResult` dict |
| `classify_cml_milestone(data)` | `CMLMilestoneData` dict | `CMLMilestoneResult` dict |
| `classify_gvhd(data)` | `GVHDData` dict | `GVHDResult` dict |
| `compare_who_icc(who_result, icc_result)` | two result dicts | `DiscordanceReport` dict |
| `generate_methods_paragraph(disease, n_patients)` | str, int | str (prose) |
| `generate_results_table(results_list)` | list[result] | str (markdown table) |
| `write_to_manifest(manifest_path, summary)` | Path, dict | None |

#### AML Classification Logic (ported from HemaCalc)

**WHO 2022 AML entities (from `MyeloidClassifier.classifyAMLWHO`):**
- AML with defining genetic abnormalities (CBF, APL, NPM1, CEBPA-bZIP, etc.)
- AML with myelodysplasia-related gene mutations (ASXL1, RUNX1, TP53, SRSF2, etc.)
- AML NOS (blast threshold: ≥20% unless defining abnormality)

**ICC 2022 AML divergence points (from `ICCClassifier.classifyAMLICC`):**
- TP53-mutated: ICC classifies as "MDS/AML" when blast 10–19%
- NPM1: ICC requires blast ≥10% (WHO does not)
- CEBPA: ICC requires bZIP mutations only
- MDS/AML: ICC-specific category absent from WHO 2022

**ELN 2022 AML risk stratification (from `ELN2022Calculator`):**
- Favorable: CBF, NPM1+/FLT3-ITD(low), CEBPA-bZIP
- Intermediate: Normal karyotype, t(9;11), other
- Adverse: TP53, RUNX1, ASXL1, complex/monosomal karyotype, t(6;9), inv(3)

**CML milestone logic (from `CMLResponseCalculator`, ELN 2025):**
- 3-month: BCR::ABL1 IS ≤10% = optimal; >10% = warning; no hematologic remission = failure
- 6-month: BCR::ABL1 IS ≤1% = optimal; 1–10% = warning; >10% = failure
- 12-month: BCR::ABL1 IS ≤0.1% (MR3) = optimal; 0.1–1% = warning; >1% = failure
- Any time: Loss of CHR, PCyR, MMR, or confirmed doubling = failure

**GVHD grading (NIH 2014/2005):**
- Acute GVHD: Grades 0–IV (skin, liver, gut scoring; overall grade by worst organ)
- Chronic GVHD: Mild/Moderate/Severe (organ score 0–3; summary score)

---

## 4. SkillContext Extension

Add three fields to `SkillContext` in `tools/skills/_base.py`:

```python
# Phase 4 — Classification
classification_result: dict = field(default_factory=dict)
# Keys: {
#   "aml_who": list[str],      # WHO classifications for each patient group
#   "aml_icc": list[str],      # ICC classifications
#   "discordant_n": int,        # count of discordant cases
#   "discordant_pairs": list,   # [{who: str, icc: str, n: int}]
#   "cml_milestones": dict,     # {timepoint: {optimal:n, warning:n, failure:n}}
#   "gvhd_grades": dict,        # {acute: {I:n, II:n, III:n, IV:n}, chronic: {...}}
# }
```

---

## 5. CSA Manifest Output

`write_to_manifest(manifest_path, summary)` appends a `classification_summary` block
to the existing `hpw_manifest.json`:

```json
{
  "classification_summary": {
    "schema_version": "1.0",
    "disease": "AML",
    "n_patients": 120,
    "who_2022": {
      "AML with NPM1 mutation": 34,
      "AML with RUNX1::RUNX1T1": 18,
      "AML NOS": 41,
      "...": "..."
    },
    "icc_2022": {
      "AML with NPM1 mutation": 34,
      "MDS/AML": 9,
      "AML NOS": 35,
      "...": "..."
    },
    "discordant_n": 12,
    "discordant_pairs": [
      {"who": "AML NOS", "icc": "MDS/AML", "n": 9},
      {"who": "AML with TP53", "icc": "MDS/AML", "n": 3}
    ],
    "eln2022_risk": {"Favorable": 52, "Intermediate": 41, "Adverse": 27},
    "generated_at": "2026-03-05T00:00:00"
  }
}
```

---

## 6. Prose Generation Templates

### 6a. Methods paragraph (AML)

```
Patients were classified according to the 2022 World Health Organization
(WHO) Classification of Haematolymphoid Tumours[REF] and the International
Consensus Classification (ICC) 2022[REF]. Risk stratification followed the
European LeukemiaNet (ELN) 2022 recommendations[REF]. Discordant cases between
the two classification systems were adjudicated by [ADJUDICATION_METHOD].
```

### 6b. Results text (AML — discordance)

```
Of {n_patients} patients, {concordant_n} ({concordant_pct}%) were classified
concordantly by WHO 2022 and ICC 2022. Discordant classification was observed
in {discordant_n} ({discordant_pct}%) cases, most commonly involving TP53-mutated
disease classified as AML (WHO 2022) versus MDS/AML (ICC 2022) (n={n_tp53}).
```

### 6c. Methods paragraph (CML)

```
Treatment response was assessed at 3, 6, and 12 months according to the 2025
European LeukemiaNet (ELN) recommendations for CML[REF]. Optimal response,
warning, and failure criteria were applied as defined. BCR::ABL1 transcript
levels were reported on the International Scale (IS).
```

### 6d. Methods paragraph (HCT/GVHD)

```
Acute GVHD was graded according to the modified Glucksberg criteria[REF] and
the Mount Sinai Acute GVHD International Consortium (MAGIC) criteria[REF].
Chronic GVHD was classified using NIH 2014 consensus criteria[REF] as
mild, moderate, or severe based on the global severity score.
```

---

## 7. Phase Integration

### Phase 1 (`phase1_topic/topic_development.py`)
- `integrate_skills_phase1()` already exists — add call to
  `ClassificationValidator(ctx).set_disease_context(topic)` to detect
  whether AML/CML/HCT terminology is present and pre-populate
  `ctx.classification_result["disease"]`

### Phase 4 (`tools/draft_generator/enhanced_drafter.py`)
- In `_generate_methods_section()`: call
  `ClassificationValidator(ctx).generate_methods_paragraph(disease, n)`
  and append to methods draft if disease is AML/CML/HCT

### Phase 4.7 (`phases/phase4_7_prose/prose_verifier.py`)
- Add `_check_classification_nomenclature()` pass that verifies:
  - WHO/ICC citations present in methods
  - BCR::ABL1 double-colon notation (already checked by nomenclature_checker)
  - ELN 2022/2025 citation year is correct
  - "MDS/AML" (ICC term) not used without qualification when WHO system declared

---

## 8. References to Encode

| Entity | Reference |
|--------|-----------|
| WHO 2022 | Khoury JD, et al. Leukemia. 2022;36(7):1703-19 |
| ICC 2022 | Arber DA, et al. Blood. 2022;140(11):1200-28 |
| ELN 2022 AML | Döhner H, et al. Blood. 2022;140(12):1345-77 |
| ELN 2025 CML | Apperley JF, et al. Leukemia. 2025;39(8):1797-813 |
| Acute GVHD | Przepiorka D, et al. Bone Marrow Transplant. 1995 |
| Chronic GVHD | Jagasia MH, et al. Biol Blood Marrow Transplant. 2015 |

---

## 9. Implementation Order

```
Step 1 — New skill file (standalone):
  tools/skills/classification_validator.py
  - AMLPatientData / CMLMilestoneData / GVHDData input structs
  - classify_aml(), classify_cml_milestone(), classify_gvhd()
  - compare_who_icc() + generate_methods_paragraph() + generate_results_table()
  - write_to_manifest()

Step 2 — SkillContext extension:
  tools/skills/_base.py
  - Add classification_result: dict field (additive, backward-compatible)

Step 3 — Phase 4 integration:
  tools/draft_generator/enhanced_drafter.py
  - Inject methods paragraph when disease in {AML, CML, HCT}

Step 4 — Phase 4.7 integration:
  phases/phase4_7_prose/prose_verifier.py
  - Add _check_classification_nomenclature() pass

Step 5 — Phase 1 integration:
  phases/phase1_topic/topic_development.py
  - Detect disease context from topic string

Step 6 — Tests:
  tests/test_classification_validator.py
  - AML: WHO-only, ICC-only, discordant TP53 case
  - CML: 3/6/12-month milestone each category
  - GVHD: acute grade III, chronic severe
  - Manifest write: verify JSON structure
  - Prose: check methods paragraph contains required citations
```

---

## 10. Risk Assessment

| Area | Risk | Mitigation |
|------|------|------------|
| Blast threshold edge cases | Medium — WHO/ICC differ on 10% vs 20% | Encode as explicit enum with comment |
| TP53 AML/MDS overlap | Medium — ICC "MDS/AML" is new category | Document expected behavior in tests |
| Manifest append logic | Low — existing manifest may not have block | Check for existing key before writing |
| Phase integration | Low — additive `try/except` pattern | Follow established `integrate_skills_phaseN()` pattern |
| CML milestone months | Low — timepoints are discrete | Map to nearest: 3, 6, 12, 18, 24 months |

---

## 11. Success Criteria

| Item | Done When |
|------|-----------|
| AML classifier | Given blasts%, cytogenetics, mutations → correct WHO 2022 entity |
| ICC divergence | TP53 10–19% blasts → "MDS/AML" (ICC) vs "AML with TP53" (WHO) |
| ELN risk | NPM1+/FLT3-ITD(low) → Favorable; TP53 → Adverse |
| CML milestones | BCR::ABL1 IS 0.08% at 12 months → Optimal |
| GVHD grading | Skin grade 3 + gut grade 4 → acute GVHD grade IV |
| Prose output | Methods paragraph contains all 3 required citation keys |
| Manifest write | `hpw_manifest.json` has `classification_summary` block with correct counts |
| Tests | ≥20 tests passing, zero regressions in existing 113 tests |
