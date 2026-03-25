# Systematic Review & Meta-Analysis Table Guidelines

## Table of Contents
1. [PRISMA 2020 Requirements](#prisma-2020-requirements)
2. [Characteristics of Included Studies](#characteristics-of-included-studies)
3. [Risk of Bias 2.0 (Cochrane RoB 2)](#risk-of-bias-20-cochrane-rob-2)
4. [GRADE Summary of Findings (SoF)](#grade-summary-of-findings-sof)
5. [Effect Measure Reference](#effect-measure-reference)
6. [Narrative & Clinical Review Tables](#narrative--clinical-review-tables)

---

## PRISMA 2020 Requirements

Tables are **mandatory** under PRISMA 2020, not illustrative. Required:
1. Characteristics of Included Studies
2. Risk of Bias assessment (per study)
3. Summary of Findings (SoF) with GRADE certainty ratings

PRISMA 2020 updates vs. 2009:
- Requires reporting of database search strings (often as supplemental table)
- Mandates reporting of deviations from registered protocol
- Adds requirements for automation tools used in screening

---

## Characteristics of Included Studies

**Purpose**: Line-by-line account of every study meeting inclusion criteria.

### Minimum Required Columns
| Study | Design | Population (N) | Intervention | Comparator | Follow-up | Key Outcome | Quality Rating |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

### Column guidance
- **Study**: Author(Year) format — enables cross-referencing with bibliography
- **Design**: RCT, cohort, case-control, cross-sectional, etc.
- **Population**: N enrolled, demographics, clinical status, inclusion/exclusion summary
- **Intervention**: Drug name, dose, schedule, duration
- **Key Outcome**: Primary outcome value + measure used
- **Quality Rating**: RoB 2.0 overall rating or Newcastle-Ottawa Scale score

### Inclusion/Exclusion Criteria Table (Optional but valued)
Elite journals increasingly prefer a structured table over a textbox:
| Criteria Type | Criterion | Rationale |
| :--- | :--- | :--- |
| Inclusion | Adults ≥18 years with confirmed AML | Defines target population |
| Exclusion | Prior allogeneic HCT | Confounds treatment outcomes |

---

## Risk of Bias 2.0 (Cochrane RoB 2)

**Standard for RCTs**. Five domains, each rated: Low / Some concerns / High.

### Domain Reference
| Code | Domain | What It Assesses |
| :--- | :--- | :--- |
| **D1** | Randomization process | Allocation concealment + sequence generation |
| **D2** | Deviations from intended interventions | Performance bias (blinding, adherence) |
| **D3** | Missing outcome data | Attrition bias, completeness of follow-up |
| **D4** | Measurement of the outcome | Detection bias (blinded assessment?) |
| **D5** | Selection of the reported result | Reporting bias (selective outcome reporting) |
| **Overall** | Overall judgment | Summary across all 5 domains |

### Visualization Options
- **Traffic light table**: Each cell colored green/yellow/red — requires `robvis` R package
- **Weighted bar plot**: Shows proportion of studies at each risk level per domain
- **Standard table**: Plain text ratings (Low/Some concerns/High) — universally accepted

---

## GRADE Summary of Findings (SoF)

**Purpose**: Definitive synthesis showing certainty of evidence for each key outcome.

### Required SoF Columns
| Outcome | N Studies (N Participants) | Relative Effect (95% CI) | Anticipated Absolute Effect | Certainty (GRADE) | Importance |
| :--- | :--- | :--- | :--- | :--- | :--- |

### GRADE Certainty Levels
| Rating | Meaning | Symbol |
| :--- | :--- | :--- |
| **High** | True effect close to estimated effect | ⊕⊕⊕⊕ |
| **Moderate** | Moderate confidence; true effect likely close | ⊕⊕⊕◯ |
| **Low** | Limited confidence; true effect may be substantially different | ⊕⊕◯◯ |
| **Very Low** | Very little confidence | ⊕◯◯◯ |

### Downgrading Factors (each can lower certainty by 1–2 levels)
1. **Risk of bias** — serious/very serious risk across studies
2. **Inconsistency** — unexplained heterogeneity (I² >50%, wide prediction interval)
3. **Indirectness** — PICO mismatch (different population, intervention, or outcomes)
4. **Imprecision** — wide 95% CI, small sample size, few events
5. **Publication bias** — asymmetric funnel plot, selective reporting

### Upgrading Factors
1. Large magnitude of effect (RR >2 or <0.5)
2. Dose-response gradient
3. All plausible confounders would reduce effect

### MCID Note
For continuous outcomes (e.g., quality-of-life scores), include the **Minimal Clinically Important Difference (MCID)** in the SoF table or footnote. A statistically significant result below the MCID is clinically meaningless.

**Header requirement**: SoF table header must specify the PICO: "Population: [X], Intervention: [Y] vs. [Z], Outcomes: [A, B, C]"

---

## Effect Measure Reference

| Measure | Best Use | Interpretation |
| :--- | :--- | :--- |
| **Risk Ratio (RR)** | Prospective RCTs, cohort studies | RR <1 favors intervention for harmful events |
| **Odds Ratio (OR)** | Case-control, logistic regression | Can overestimate effect vs. RR when event is common (>10%) |
| **Mean Difference (MD)** | Continuous outcomes, same scale | Report with SD; pooling requires SD |
| **Standardized MD (SMD)** | Continuous outcomes, different scales | 0.2=small, 0.5=moderate, 0.8=large (Cohen's d) |
| **Hazard Ratio (HR)** | Time-to-event (OS, PFS, EFS) | Assumes proportional hazards — verify with log-log plot |
| **Rate Ratio** | Count data (events per person-time) | Use for recurrent events |

---

## Narrative & Clinical Review Tables

### Study Characteristics Table (Narrative Review)
Include: Study ID (Author Year), Design, Population (N + demographics), Intervention (dose/duration), Key Findings, Quality Rating.

**Guidance**: Focus on "rationale for inclusion" and "clarity of boundaries" — avoid presenting opinion as objective conclusion.

### Thematic Organization
For large narrative reviews (>20 studies), organize by:
- **Theme** (e.g., frontline therapy, relapsed/refractory, elderly patients)
- **Chronology** (historical to contemporary)
- **Clinical challenge** (e.g., resistance mechanisms, toxicity management)
