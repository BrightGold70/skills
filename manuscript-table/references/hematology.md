# Hematology-Specific Table Guidelines

## Table of Contents
1. [AML Response Criteria](#aml-response-criteria)
2. [MDS Response Criteria](#mds-response-criteria)
3. [CML Endpoints and Biomarkers](#cml-endpoints-and-biomarkers)
4. [General Hematology Biomarkers](#general-hematology-biomarkers)
5. [Adverse Event Patterns in Hematology](#adverse-event-patterns-in-hematology)

---

## AML Response Criteria

**Standard**: Modified 2003 IWG criteria (Cheson et al.).

| Response | ANC | Platelets | BM Blasts | Other |
| :--- | :--- | :--- | :--- | :--- |
| **CR** (Complete Remission) | >1.0 ×10⁹/L | ≥100 ×10⁹/L | ≤5% | Transfusion independent |
| **CRi** (CR with incomplete counts) | <1.0 ×10⁹/L or | <100 ×10⁹/L | ≤5% | Otherwise meets CR |
| **CRp** (CR with incomplete platelets) | >1.0 ×10⁹/L | <100 ×10⁹/L | ≤5% | Otherwise meets CR |
| **PR** (Partial Remission) | >1.0 ×10⁹/L | ≥100 ×10⁹/L | 5–25% | ≥50% blast reduction |
| **Morphologic Leukemia-Free State** | — | — | <5% | No hematopoietic recovery required |

*Always specify IWG version used. ANC = absolute neutrophil count; BM = bone marrow.*

### Early-Phase AML Endpoint Table Structure

| Endpoint | Definition | Assessment Timepoint |
| :--- | :--- | :--- |
| CR rate | Meets all CR criteria | End of cycle 1/2 |
| CRi rate | CR with incomplete recovery | End of cycle 1/2 |
| ORR (CR + CRi + PR) | Combined response | Pre-specified |
| Event-free survival | Time to treatment failure/death | Landmark analysis |
| MRD negativity | ctDNA/flow cytometry threshold | Post-remission |

---

## MDS Response Criteria

**Standard**: 2006 IWG criteria.

### Response Categories

| Response | Peripheral Blood | Bone Marrow | Duration |
| :--- | :--- | :--- | :--- |
| **CR** | ANC ≥1.0, Plt ≥100, Hgb ≥11 g/dL, blasts 0% | ≤5% blasts | ≥4 weeks |
| **PR** | CR criteria except blasts decreased ≥50% | Blasts still >5% | ≥4 weeks |
| **mCR** (marrow CR) | No peripheral normalization required | ≤5% blasts | ≥4 weeks |
| **HI** (hematological improvement) | See below | N/A | ≥8 weeks |
| **Stable disease** | No CR/PR/mCR/HI but no progression | — | — |

### Hematological Improvement Sub-categories (HI)

| Domain | Major HI | Minor HI |
| :--- | :--- | :--- |
| **HI-E** (Erythroid) | Hgb rise ≥2 g/dL or TI for ≥8 weeks | Hgb rise 1–2 g/dL |
| **HI-P** (Platelet) | Platelets ≥30 ×10⁹/L (absolute) or increase ≥100% to >20 | Increase 50–100% from <20 |
| **HI-N** (Neutrophil) | ANC ≥0.5 ×10⁹/L and ≥100% increase | ANC increase ≥100% to <0.5 |

**IPSS/WPSS**: Cite prognostic scoring system version in table footnote (IPSS or IPSS-R for modern studies; WPSS for WHO classification-based scoring).

---

## CML Endpoints and Biomarkers

### Cytogenetic and Molecular Response Definitions

| Response | Definition |
| :--- | :--- |
| **CCyR** (Complete Cytogenetic Response) | 0% Ph+ metaphases |
| **PCyR** (Partial Cytogenetic Response) | 1–35% Ph+ metaphases |
| **MiCyR** (Minor Cytogenetic Response) | 36–65% Ph+ metaphases |
| **MMR** (Major Molecular Response) | BCR-ABL1 ≤0.1% (IS) |
| **MR4** (Deep Molecular Response) | BCR-ABL1 ≤0.01% (IS) |
| **MR4.5** | BCR-ABL1 ≤0.0032% (IS) |
| **CMR** (Complete Molecular Response) | Undetectable BCR-ABL1 |

*IS = International Scale. Always state IS when reporting BCR-ABL1 PCR results.*

### BCR-ABL Mutant Resistance Table

Useful for TKI comparison papers (e.g., ponatinib, asciminib):

| Mutation | IC50 — Imatinib (nM) | IC50 — Nilotinib | IC50 — Dasatinib | IC50 — Ponatinib | Clinical CCyR Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Wild-type | [X] | [X] | [X] | [X] | [X]% |
| T315I (gatekeeper) | Resistant | Resistant | Resistant | [X] | [X]% |
| [Other mutant] | [X] | [X] | [X] | [X] | [X]% |

*IC50 values from in vitro cell-based assays. CCyR = predicted clinical cytogenetic response rate.*

### Schedule-Dependent Toxicity Note

When reporting CML trial designs (e.g., dasatinib), state the dosing schedule rationale. Once-daily schedules may preserve efficacy while improving tolerability vs. twice-daily — this distinction must appear in the methods/table footnote.

---

## General Hematology Biomarkers

| Biomarker | Type | Measurement Timepoint | Table Column Example |
| :--- | :--- | :--- | :--- |
| **ctDNA** | Circulating tumor DNA | Baseline + cycle 1 D15 + EOT | ctDNA clearance rate (%) |
| **MRD** (flow cytometry) | Minimal residual disease | Post-remission (≥10⁻⁴ sensitivity) | MRD-negative, n (%) |
| **MRD** (NGS/ddPCR) | Molecular MRD | Post-remission | MRD <10⁻⁵, n (%) |
| **pRSK/pERK** | Pharmacodynamic (PD) target | Cycle 1 D1 pre/post-dose | Target inhibition (%) |
| **Ex vivo drug sensitivity** | Leukemic cell assay | Baseline + steady-state | IC50 shift (fold) |

**Biomarker table guidance**:
- Always state assay platform (flow cytometry panel, ddPCR, NGS) in footnote
- State sensitivity threshold for MRD (10⁻⁴, 10⁻⁵, etc.)
- PD biomarker tables should pair with PK parameters in Phase 1 (see clinical-trials.md for integrated PK/PD guidance)

---

## Adverse Event Patterns in Hematology

### Hematologic Toxicity (CTCAE v5.0)

Must be tracked separately from non-hematologic toxicity in AML/MDS/CML studies:

| Toxicity | Grade 3 (CTCAE) | Grade 4 | Clinically Important Threshold |
| :--- | :--- | :--- | :--- |
| Neutropenia | ANC 500–1000 /μL | ANC <500 /μL | Grade ≥3: report febrile neutropenia separately |
| Thrombocytopenia | Plt 25,000–50,000 | Plt <25,000 | Grade ≥3: report bleeding events |
| Anemia | Hgb 8–10 g/dL | Hgb <8 g/dL | Transfusion requirement |

### Arterial Occlusive Events (AOEs) — CML/Ponatinib Studies

AOEs require dedicated sub-table when reporting ponatinib or 3rd-gen TKI trials:

| AOE Category | [Drug] (n=[X]), n (%) | [Control] (n=[X]), n (%) |
| :--- | :--- | :--- |
| **Any AOE** | [N] ([X]%) | [N] ([X]%) |
| — Cardiovascular (MI, unstable angina) | [N] ([X]%) | [N] ([X]%) |
| — Cerebrovascular (stroke, TIA) | [N] ([X]%) | [N] ([X]%) |
| — Peripheral vascular | [N] ([X]%) | [N] ([X]%) |

*AOE definition: arterial thrombotic/embolic event (cardiovascular, cerebrovascular, or peripheral arterial) regardless of grade.*
