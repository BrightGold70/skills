# Clinical Trial Table Guidelines

## Table of Contents
1. [Phase 1 — Safety, Tolerability & PK](#phase-1--safety-tolerability--pk)
2. [Phase 2 — Signal Detection](#phase-2--signal-detection)
3. [Phase 3 — CONSORT Confirmatory](#phase-3--consort-confirmatory)
4. [Safety / Adverse Events (All Phases)](#safety--adverse-events-all-phases)

---

## Phase 1 — Safety, Tolerability & PK

**Primary objective**: Identify Maximum Tolerated Dose (MTD) and Recommended Phase 2 Dose (RP2D).

### Dose-Escalation Table (Required)
Must include for each cohort:
- Dose level (mg or mg/m²)
- N enrolled and N evaluable for toxicity
- DLTs observed (count + description)
- Toxicity details: CTCAE grade + event name
- Cumulative dose exposure if relevant

**DLT definition**: Typically Grade 3–4 adverse events (CTCAE) possibly related to study drug within the DLT evaluation window.

### Pharmacokinetics Table (Required)
Mandatory PK parameters:
| Parameter | Description |
| :--- | :--- |
| **C_max** | Maximum observed plasma concentration |
| **T_max** | Time to reach C_max |
| **AUC** | Area Under the Concentration-time Curve (AUC₀₋ₜ and AUC₀₋∞) |
| **t½** | Terminal elimination half-life |
| **CL/F** | Apparent oral clearance |
| **V_z/F** | Apparent volume of distribution |

**High-value practice**: Integrate PK parameters with toxicity data in a single table showing AUC vs. DLT occurrence — 84% of Phase 1 papers fail to do this (separated reporting criticized by elite journals).

### Dose-Toxicity Curve
When space permits, include a column associating systemic exposure (AUC) with each toxicity grade to demonstrate the therapeutic window.

---

## Phase 2 — Signal Detection

**Primary focus**: Surrogate endpoints (ORR, PFS, CBR) and dose optimization.

### Efficacy Table
- Define all endpoints clearly (e.g., ORR = ≥30% tumor reduction by RECIST 1.1)
- Report: N per arm, response rate (%), 95% CI, median PFS/DOR with Kaplan-Meier estimates
- For adaptive designs: document timing and rationale for interim arm reassignments

### Dose-Ranging Table
When multiple doses tested:
- Columns: Dose level, N, Primary outcome (%), Serious AEs (%), Dose reductions (%)
- Label the selected RP2D with a footnote

### Surrogate Endpoint Reference
| Endpoint | Definition |
| :--- | :--- |
| **ORR** | Proportion with CR + PR by RECIST 1.1 or equivalent |
| **DCR** | Disease control rate = CR + PR + SD |
| **DOR** | Duration of response (median, KM) |
| **PFS** | Progression-free survival (median, KM, HR) |
| **CBR** | Clinical benefit rate = CR + PR + SD ≥24 weeks |

---

## Phase 3 — CONSORT Confirmatory

Governed by **CONSORT 2025**. Three mandatory table types:

### Table 1: Baseline Characteristics
**Purpose**: Demonstrate randomization balance; assess generalizability.
- Group columns by intervention vs. control (no P-values for baseline — randomization makes them uninformative)
- Include: Age (median/IQR or mean/SD), Sex, ECOG PS, disease stage, prior therapies, key comorbidities
- Imbalances in any variable → must be addressed as potential confounder in statistical analysis

### Outcome Table (Primary + Secondary)
Must include for each pre-specified endpoint:
- Both arms: point estimate + 95% CI
- Effect estimate: HR (time-to-event), RR or OR (binary), MD or SMD (continuous)
- P-value (primary outcome only for confirmatory; exploratory secondary outcomes labeled as such)
- Label primary outcome clearly and prominently

### Safety/AE Table
- Report all events occurring in >5% of patients in either arm
- Report ALL serious adverse events (SAEs) regardless of frequency
- **Report absolute counts BEFORE relative risks** (enables NNH calculation)
- Organize by: System Organ Class → Preferred Term (MedDRA hierarchy)
- Separate columns for: Any grade, Grade 3, Grade 4, Grade 5 (fatal)
- Include treatment discontinuations and dose modifications

---

## Safety / Adverse Events (All Phases)

**Grading**: CTCAE v5.0 (Common Terminology Criteria for Adverse Events).

### Standard AE Table Structure
| Adverse Event | Any Grade N(%) | Grade 3 N(%) | Grade 4 N(%) | Related N(%) |
| :--- | :--- | :--- | :--- | :--- |

**Footnote requirements**:
- CTCAE version used
- Definition of "related" (possibly, probably, or definitely)
- Denominator (ITT vs. safety population)

**Number Needed to Harm (NNH)**: = 1 / (AE rate intervention − AE rate control). Include when reporting statistically significant safety differences.
