# Medical Reporting Guidelines Reference

## Table of Contents
1. [CONSORT 2025 (RCTs)](#consort-2025-rcts)
2. [STROBE (Observational Studies)](#strobe-observational-studies)
3. [STARD (Diagnostic Accuracy)](#stard-diagnostic-accuracy)
4. [STREGA (Genetic Association)](#strega-genetic-association)
5. [TIDieR (Intervention Description)](#tidier-intervention-description)
6. [PROCESS (Case Series)](#process-case-series)
7. [STROCSS (Surgical Cohort/Case-Control)](#strocss-surgical-cohortcase-control)
8. [Reconciliation Tables (Living Meta-Analyses)](#reconciliation-tables-living-meta-analyses)

---

## CONSORT 2025 (RCTs)

**Updated**: 30-item checklist (up from 25 in 2010). Mandatory flow diagram.

### Key 2025 Additions vs. 2010
- TIDieR-compliant intervention description required
- Explicit reporting of deviations from registered protocol
- Automation tools used in trial management must be stated
- Digital health and remote monitoring elements

### Three Mandatory Table Types
1. **Table 1**: Baseline characteristics (no P-values — see clinical-trials.md)
2. **Outcomes table**: Primary + secondary endpoints with effect estimates
3. **Safety/AE table**: CTCAE-graded events ≥5% frequency + all SAEs

### CONSORT Extensions (cite when applicable)
| Extension | Use When |
| :--- | :--- |
| CONSORT-Adaptive | Adaptive trial designs with interim analyses |
| CONSORT-Cluster | Cluster-randomized trials |
| CONSORT-Crossover | Crossover designs |
| CONSORT-Non-inferiority | Non-inferiority/equivalence margins |
| CONSORT-Pragmatic | Pragmatic real-world trials |
| CONSORT-Pilot | Pilot/feasibility studies |

*In the methods section, state the CONSORT extension used. Checklist should be included as supplementary material.*

---

## STROBE (Observational Studies)

**Applies to**: Cohort, case-control, and cross-sectional studies.

### Required Table Elements (vs. RCTs)
- **No randomization** → justify comparability of groups in Table 1 (P-values acceptable for observational studies)
- **Confounders**: List all adjusted covariates; justify selection
- **Missing data**: Report missingness pattern (MCAR/MAR/MNAR); state imputation method

### STROBE-Specific Table Structure

| Variable | Exposed/Cases (n=[X]) | Unexposed/Controls (n=[X]) | P-value |
| :--- | :--- | :--- | :--- |

*P-values permitted in observational Table 1 to describe group differences.*

**Adjusted Effect Estimates**: Always distinguish crude vs. adjusted ORs/HRs/RRs in separate columns or footnotes.

---

## STARD (Diagnostic Accuracy)

**Applies to**: Studies evaluating sensitivity/specificity of diagnostic tests.

### Core STARD Table

| Metric | Value (95% CI) |
| :--- | :--- |
| Sensitivity | [X]% ([X]–[X]) |
| Specificity | [X]% ([X]–[X]) |
| Positive Predictive Value | [X]% ([X]–[X]) |
| Negative Predictive Value | [X]% ([X]–[X]) |
| Positive Likelihood Ratio | [X] ([X]–[X]) |
| Negative Likelihood Ratio | [X] ([X]–[X]) |
| Area Under ROC Curve | [X] ([X]–[X]) |

**Mandatory**: Flow diagram showing patient disposition through index test and reference standard.

---

## STREGA (Genetic Association)

**Applies to**: Genome-wide association studies (GWAS) and candidate gene studies.

### Required Table Elements
- Population stratification: principal components or genomic inflation factor (λ)
- Hardy-Weinberg equilibrium P-values
- Minor allele frequency (MAF)
- Genotyping platform and quality control filters

### Genetic Association Table Structure

| SNP / Variant | Gene | MAF | OR (95% CI) | P-value | HWE P |
| :--- | :--- | :--- | :--- | :--- | :--- |

*P-value threshold for GWAS: <5×10⁻⁸. Replication threshold: <0.05 with same direction of effect.*

---

## TIDieR (Intervention Description)

**Applies to**: All clinical trials (now integrated into CONSORT 2025).

Detailed description of intervention and comparator must be reportable in tabular form:

| TIDieR Item | Intervention | Comparator |
| :--- | :--- | :--- |
| Name/Materials | [Drug, formulation] | [Placebo/SOC] |
| Procedure | [Route, infusion time] | — |
| Who provides | [Oncologist/pharmacist] | — |
| How (delivery) | [IV push, oral tablet] | — |
| Where | [Outpatient clinic] | — |
| When/How much | [Dose, schedule, duration] | — |
| Tailoring | [Dose modifications] | — |
| Modifications | [Protocol deviations logged] | — |

---

## PROCESS (Case Series)

**Applies to**: Case series without a control group.

### Minimum Required Elements
- Case selection criteria (consecutive vs. selected)
- Follow-up duration
- Completeness of data

### Case Series Table

| Case | Age/Sex | Diagnosis | Intervention | Outcome | Follow-up |
| :--- | :--- | :--- | :--- | :--- | :--- |

*No denominator = no incidence rates. Describe as frequency only.*

---

## STROCSS (Surgical Cohort/Case-Control)

**Applies to**: Observational surgical studies (cohort, cross-sectional, case-control).

Key additions beyond STROBE for surgical literature:
- Describe surgeon volume/experience
- Describe institutional volume
- Learning curve considerations

---

## Reconciliation Tables (Living Meta-Analyses)

Used in **living systematic reviews** or **updated meta-analyses** to track study status between review versions.

### Reconciliation Table Structure

| Study | Included in Prior Review | Status in Current Review | Reason for Change |
| :--- | :--- | :--- | :--- |
| [Author Year] | Yes | Included — updated data | New trial report available |
| [Author Year] | Yes | Excluded | Post-hoc: PICO mismatch identified |
| [Author Year] | No | Newly included | Published after prior search |

*Required for: Cochrane living reviews, annual GRADE updates, living network meta-analyses.*
