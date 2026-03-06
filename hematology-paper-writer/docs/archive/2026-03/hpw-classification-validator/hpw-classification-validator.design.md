# Design: HPW Classification Validator

**Feature:** `hpw-classification-validator`
**Phase:** Design
**Created:** 2026-03-05
**References Plan:** `docs/01-plan/features/hpw-classification-validator.plan.md`

---

## 1. Architecture Decision

`ClassificationValidator` follows the exact pattern established by the 13 existing skill
classes (`StatisticalAnalyst`, `CriticalThinker`, etc.):

- Inherits `SkillBase(ABC)` from `tools/skills/_base.py`
- Reads/writes `SkillContext` — adds `classification_result: dict` field
- All methods wrapped in `try/except`, return empty/default on failure
- Imported and re-exported from `tools/skills/__init__.py`
- Phase integrations appended at module end as `integrate_skills_phaseN()` functions

---

## 2. Input Data Structures

```python
# AML patient data (one patient or cohort-level dict)
AMLPatientData = TypedDict("AMLPatientData", {
    "blasts_pct": float,            # 0–100
    "cytogenetics": str,            # "favorable"|"intermediate"|"adverse"|"normal"
    "npm1": bool,
    "flt3_itd": bool,
    "flt3_itd_allelic_ratio": float,  # 0.0–1.0; default 0.0
    "cebpa_bzip": bool,
    "runx1": bool,
    "asxl1": bool,
    "tp53": bool,
    "mds_related_changes": bool,    # morphologic or prior MDS
    "therapy_related": bool,        # t-AML flag
    "down_syndrome": bool,
}, total=False)                     # all fields optional — absent = False/0.0

# CML milestone data
CMLMilestoneData = TypedDict("CMLMilestoneData", {
    "months": int,                  # 3|6|12|18|24
    "bcr_abl_is": float,            # BCR::ABL1 IS% (0.0–100.0)
    "achieved_chr": bool,           # Complete Hematologic Response
    "ph_positive_pct": float,       # 0–100
}, total=False)

# GVHD grading data
GVHDData = TypedDict("GVHDData", {
    "type": str,                    # "acute"|"chronic"
    # Acute: skin/liver/gut organ stages
    "skin_stage": int,              # 0–4
    "liver_stage": int,             # 0–4
    "gut_stage": int,               # 0–4
    # Chronic: NIH 2014 organ scores
    "skin_score": int,              # 0–3
    "mouth_score": int,
    "eye_score": int,
    "gi_score": int,
    "liver_score_chronic": int,
    "lung_score": int,
    "joint_score": int,
    "genital_score": int,
    "ps_score": int,                # Performance status 0–3
}, total=False)
```

---

## 3. Output Data Structures

```python
@dataclass
class AMLClassificationResult:
    who_2022: str               # e.g. "AML with NPM1 mutation"
    icc_2022: str               # e.g. "AML with NPM1 mutation" or "MDS/AML"
    eln_2022_risk: str          # "Favorable"|"Intermediate"|"Adverse"
    eln_factors: list[str]      # contributing factors
    is_concordant: bool         # WHO == ICC entity class
    discordance_reason: str     # "" if concordant

@dataclass
class CMLMilestoneResult:
    months: int
    bcr_abl_is: float
    status: str                 # "Optimal"|"Warning"|"Failure"
    threshold_optimal: float
    threshold_warning: float
    recommendation: str

@dataclass
class GVHDResult:
    gvhd_type: str              # "acute"|"chronic"
    grade: str                  # Acute: "0"|"I"|"II"|"III"|"IV"
                                # Chronic: "None"|"Mild"|"Moderate"|"Severe"
    organ_scores: dict[str, int]
    overall_score: int          # acute: 0–4; chronic: NIH global 0–3

@dataclass
class DiscordanceReport:
    concordant_n: int
    discordant_n: int
    discordant_pairs: list[dict]  # [{who, icc, n, reason}]
    total_n: int
    concordance_rate: float       # 0.0–1.0
```

---

## 4. Classification Logic

### 4a. AML WHO 2022 (priority order)

```
1. Therapy-related AML → "AML, therapy-related"
2. Down syndrome → "ML-DS" (myeloid leukemia of Down syndrome)
3. t(8;21) → "AML with RUNX1::RUNX1T1"
4. inv(16)/t(16;16) → "AML with CBFB::MYH11"
5. t(15;17) → "APL with PML::RARA"
6. NPM1 (blasts any %) → "AML with NPM1 mutation"
7. CEBPA bZIP → "AML with CEBPA mutation"
8. TP53 (blasts ≥20%) → "AML with TP53 mutation"
9. mds_related_changes or RUNX1/ASXL1/SRSF2 → "AML, myelodysplasia-related"
10. blasts ≥20% → "AML NOS"
11. blasts 10–19% (no defining) → "MDS/AML" in ICC only; WHO = "MDS"
```

### 4b. AML ICC 2022 divergence rules

```
- TP53 + blasts 10–19%: ICC = "MDS/AML" (not AML with TP53)
- NPM1: ICC requires blasts ≥10% to qualify as AML (WHO: no threshold)
- CEBPA: ICC requires in-frame bZIP mutation (same as WHO, explicit)
- MDS/AML category: blasts 10–19% with qualifying mutation → ICC = "MDS/AML"
```

### 4c. ELN 2022 risk (applies after WHO/ICC classification)

```
Favorable:  CBF AML (t(8;21), inv(16)) OR NPM1+/FLT3-ITD(low/neg) OR CEBPA-bZIP
Adverse:    TP53 OR RUNX1 OR ASXL1 OR complex karyotype OR t(6;9) OR inv(3)
            OR cytogenetics == "adverse"
Intermediate: everything else
```

### 4d. CML ELN 2025 milestones

```python
THRESHOLDS = {
    3:  {"optimal": 10.0,  "warning": 10.0},   # >10% = warning/failure by context
    6:  {"optimal": 1.0,   "warning": 10.0},
    12: {"optimal": 0.1,   "warning": 1.0},
    18: {"optimal": 0.1,   "warning": 1.0},
    24: {"optimal": 0.1,   "warning": 1.0},
}
# 3m: ≤10% optimal; no CHR = failure regardless
# Any: loss of CCyR or MMR confirmed = failure
```

### 4e. Acute GVHD grading (Glucksberg)

```
Overall grade = worst organ stage combination:
Grade I:   Skin 1–2, Liver 0, Gut 0
Grade II:  Skin 1–3, Liver 1, or Gut 1
Grade III: Skin 2–3, Liver 2–3, or Gut 2–3
Grade IV:  Skin 4, Liver 4, or Gut 4 (life-threatening)
```

### 4f. Chronic GVHD grading (NIH 2014)

```
Count of organs with score ≥1:
Mild:     1–2 organs, max score 1, lung score 0
Moderate: 3+ organs, or 1 organ score ≥2, or lung score 1
Severe:   any organ score 3, or lung score ≥2
```

---

## 5. Manifest Output Schema

```json
{
  "classification_summary": {
    "schema_version": "1.0",
    "disease": "AML",
    "n_patients": 120,
    "who_2022": {"AML with NPM1 mutation": 34, "...": 0},
    "icc_2022": {"AML with NPM1 mutation": 34, "MDS/AML": 9, "...": 0},
    "discordant_n": 12,
    "concordance_rate": 0.90,
    "discordant_pairs": [{"who": "AML NOS", "icc": "MDS/AML", "n": 9, "reason": "TP53 blasts 10-19%"}],
    "eln2022_risk": {"Favorable": 52, "Intermediate": 41, "Adverse": 27},
    "cml_milestones": {"3m": {"optimal": 0, "warning": 0, "failure": 0}},
    "gvhd_grades": {"acute": {"I": 0, "II": 0, "III": 0, "IV": 0}, "chronic": {"Mild": 0, "Moderate": 0, "Severe": 0}},
    "generated_at": "2026-03-05T00:00:00"
  }
}
```

`write_to_manifest()` reads existing JSON, merges `classification_summary` key, rewrites.
If manifest file does not exist, creates minimal wrapper with just this block.

---

## 6. Prose Templates

Stored as module-level constants `_METHODS_TEMPLATES` dict keyed by disease:

```python
_METHODS_TEMPLATES = {
    "AML": "Patients were classified according to the 2022 World Health Organization "
           "(WHO) Classification of Haematolymphoid Tumours[{who_ref}] and the "
           "International Consensus Classification (ICC) 2022[{icc_ref}]. Risk "
           "stratification followed European LeukemiaNet (ELN) 2022 "
           "recommendations[{eln_ref}].",
    "CML": "Treatment response was assessed at 3, 6, and 12 months according to the "
           "2025 European LeukemiaNet (ELN) recommendations for CML[{eln_cml_ref}]. "
           "BCR::ABL1 transcript levels are reported on the International Scale (IS).",
    "HCT": "Acute GVHD was graded per modified Glucksberg criteria[{glucksberg_ref}]. "
           "Chronic GVHD was classified per NIH 2014 consensus criteria[{nih_gvhd_ref}] "
           "as mild, moderate, or severe.",
}

_CITATIONS = {
    "who_ref": "Khoury JD, et al. Leukemia. 2022;36(7):1703-19",
    "icc_ref": "Arber DA, et al. Blood. 2022;140(11):1200-28",
    "eln_ref": "Döhner H, et al. Blood. 2022;140(12):1345-77",
    "eln_cml_ref": "Apperley JF, et al. Leukemia. 2025;39(8):1797-813",
    "glucksberg_ref": "Przepiorka D, et al. Bone Marrow Transplant. 1995;15(6):825-8",
    "nih_gvhd_ref": "Jagasia MH, et al. Biol Blood Marrow Transplant. 2015;21(3):389-401",
}
```

`generate_methods_paragraph(disease)` → replaces `{ref}` placeholders with citation strings.
`generate_results_table(results_list)` → markdown table with WHO/ICC/ELN columns.

---

## 7. SkillContext Extension (`_base.py`)

Add after `quality_scores`:

```python
# Phase 4 — Classification Validation
classification_result: dict = field(default_factory=dict)
```

Backward-compatible: `SkillContext.load()` already uses `known_keys` filtering.

---

## 8. Phase Integration Points

### Phase 1 — append to `topic_development.py`

```python
def integrate_skills_phase1_classification(project_name, project_dir, topic, disease=""):
    # Detect disease from topic string → set ctx.classification_result["disease"]
    # Follows exact pattern of existing integrate_skills_phase1()
```

Disease detection: regex match against `["AML", "MDS", "CML", "HCT", "GVHD", "myeloma", "lymphoma"]`

### Phase 4 — append to `enhanced_drafter.py`

```python
def integrate_skills_phase4_classification(project_name, project_dir, disease="", n_patients=0):
    # Calls ClassificationValidator(ctx).generate_methods_paragraph(disease)
    # Appends to ctx.draft_sections["methods_classification"]
```

### Phase 4.7 — append to `prose_verifier.py`

```python
def integrate_skills_phase4_7_classification(project_name, project_dir, text=""):
    # Checks text for classification nomenclature issues
    # Writes issues to ctx.prose_issues list
```

Checks:
1. If AML in ctx: WHO 2022 citation present
2. If AML in ctx: ICC 2022 citation present
3. If CML in ctx: "BCR::ABL1" (double colon) not "BCR-ABL"
4. If GVHD in ctx: NIH 2014 citation keyword present

---

## 9. `tools/skills/__init__.py` Export

Add `ClassificationValidator` to the existing `__all__` list and import line.

---

## 10. Test Design (`tests/test_classification_validator.py`)

| # | Test | Assertion |
|---|------|-----------|
| 1 | AML favorable CBF t(8;21) | WHO = "AML with RUNX1::RUNX1T1", ELN = Favorable |
| 2 | AML APL | WHO = "APL with PML::RARA", ICC concordant |
| 3 | AML NPM1+/FLT3-ITD(low) | ELN = Favorable |
| 4 | AML NPM1+/FLT3-ITD(high) | ELN = Intermediate |
| 5 | AML TP53+ blasts 25% | WHO = "AML with TP53 mutation", ELN = Adverse |
| 6 | AML TP53+ blasts 15% | WHO = "MDS" or "AML with TP53", ICC = "MDS/AML", discordant |
| 7 | AML ASXL1+ normal karyotype | ELN = Adverse |
| 8 | AML NOS (blasts 22%, no markers) | WHO = ICC = "AML NOS", concordant |
| 9 | compare_who_icc concordant cohort | discordant_n = 0 |
| 10 | compare_who_icc mixed cohort | discordant_pairs has TP53 entry |
| 11 | CML 3m BCR::ABL1 8% | Optimal |
| 12 | CML 6m BCR::ABL1 5% | Warning |
| 13 | CML 12m BCR::ABL1 0.05% | Optimal (MR3) |
| 14 | CML 12m BCR::ABL1 0.5% | Warning |
| 15 | CML no CHR at 3m | Failure |
| 16 | Acute GVHD skin2/liver0/gut0 | Grade I |
| 17 | Acute GVHD skin3/gut3 | Grade III |
| 18 | Acute GVHD gut4 | Grade IV |
| 19 | Chronic GVHD 1 organ score 1 | Mild |
| 20 | Chronic GVHD lung score 3 | Severe |
| 21 | generate_methods_paragraph AML | contains "WHO" and "ICC" and "ELN" |
| 22 | generate_methods_paragraph CML | contains "BCR::ABL1" and "ELN 2025" |
| 23 | generate_results_table 3 patients | markdown table with 3 rows |
| 24 | write_to_manifest creates block | JSON has classification_summary key |
| 25 | write_to_manifest merges existing | existing keys preserved |
| 26 | invoke() never raises | returns string on empty input |
| 27 | SkillContext round-trip | classification_result saved/loaded correctly |
