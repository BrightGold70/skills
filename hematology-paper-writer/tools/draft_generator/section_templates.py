"""
HPW Skill Upgrade - Section Templates
=================================
Comprehensive section templates for PRISMA 2020, CONSORT 2010, and CARE 2013 compliance.
"""

from typing import Dict

# ============================================================================
# PRISMA 2020 Section Templates
# ============================================================================

PRISMA_TEMPLATES = {
    "1. Introduction": """
## 1. Introduction

### 1.1 Background and Rationale

[Topic] represents a significant clinical challenge in [disease area]. The condition affects approximately [X] individuals per 100,000 population annually and is associated with substantial morbidity and mortality [1]. Current treatment approaches include [standard treatments], though limitations persist in [specific areas of concern].

The pathophysiology of [topic] involves [brief mechanistic description], which has been elucidated through decades of basic and clinical research [2, 3]. Key risk factors include [risk factors], while prognostic markers help stratify patients into risk categories that guide treatment decisions.

Despite advances in therapeutic options over the past two decades, several unmet needs remain in the management of [topic]. These include [unmet need 1], [unmet need 2], and [unmet need 3] [4, 5].

### 1.2 Objectives

This systematic review addresses the following objectives:

**Primary Objective:**
To evaluate the efficacy and safety of [intervention] compared to [comparator] in patients with [condition].

**Secondary Objectives:**
1. To characterize the dose-response relationship
2. To identify patient subgroups who may derive differential benefit
3. To assess long-term outcomes

### 1.3 Research Question (PICO Framework)

**Population:** Adults and children with [specific condition]
**Intervention:** [Intervention name] at [dose/schedule]
**Comparison:** Standard of care, placebo, or alternative treatment
**Outcome:** [Primary and secondary outcomes]
""",

    "2. Methods": """
## 2. Methods

This systematic review was conducted and reported in accordance with the PRISMA 2020 statement [1] and was registered prospectively with PROSPERO (Registration Number: [CRDXXXXXXXXX]).

### 2.1 Eligibility Criteria

**Inclusion Criteria:**
- Randomized controlled trials and high-quality observational studies
- Adults with [condition]
- [Intervention] versus [comparator]
- Studies reporting efficacy or safety outcomes

**Exclusion Criteria:**
- Case reports and case series with <10 participants
- Animal or laboratory studies
- Studies with high risk of bias

### 2.2 Information Sources

Electronic databases searched from inception through [date]:
- PubMed/MEDLINE
- Embase
- Cochrane Central Register of Controlled Trials
- Web of Science

Grey literature:
- ClinicalTrials.gov
- WHO ICTRP
- Conference proceedings

### 2.3 Search Strategy

The search strategy was developed in consultation with a librarian. Full search strings are provided in Supplementary Material.

**Example PubMed Search:**
```
(exp [Topic]/) AND (exp [Intervention]/) AND (random$.ti,ab. OR placebo$.ti,ab.)
```

### 2.4 Selection Process

Two independent reviewers screened titles and abstracts, then full texts. Discrepancies were resolved through discussion. The PRISMA flow diagram documents the selection process.

### 2.5 Data Extraction

Two reviewers extracted data using standardized forms including:
- Study characteristics and methodology
- Participant demographics
- Intervention details
- Outcome data and effect estimates
- Adverse events

### 2.6 Risk of Bias Assessment

Risk of bias in randomized trials was assessed using the Cochrane RoB 2.0 tool [2]. Non-randomized studies were assessed using ROBINS-I [3].

### 2.7 Synthesis Methods

A narrative synthesis was performed for all outcomes. Meta-analysis was conducted when ≥2 studies reported sufficient data using random-effects models. Heterogeneity was quantified using I² statistics.
""",

    "3. Results": """
## 3. Results

### 3.1 Study Selection

The searches identified [X] records. After duplicates removal, [Y] records were screened. Following full-text assessment, [Z] studies met inclusion criteria. The PRISMA flow diagram is presented in Figure 1.

**Studies Excluded:**
- Wrong population: [n]
- Wrong intervention: [n]
- Wrong study design: [n]

### 3.2 Study Characteristics

[Z] studies ([N] participants) were included, published between [year] and [year]. Studies were conducted in [geographic regions].

### 3.3 Risk of Bias

Risk of bias assessment revealed [summary of findings]. Key concerns included [issues].

### 3.4 Synthesis Results

**Primary Outcome:**

Meta-analysis of [n] studies ([N] participants) found [effect estimate] (95% CI [X.XX to X.XX]; I² = [XX]%).

**Secondary Outcomes:**

[Summary of secondary outcomes with effect estimates]

### 3.5 Adverse Events

[Summary of adverse event data including serious adverse events]
""",

    "4. Discussion": """
## 4. Discussion

### 4.1 Summary of Main Findings

This systematic review synthesized evidence from [n] studies ([N] participants). The findings indicate [summary of main findings].

### 4.2 Comparison with Existing Literature

Our findings are [consistent/inconsistent] with previous systematic reviews [X, Y].

### 4.3 Strengths

1. Comprehensive search across multiple databases
2. Adherence to PRISMA 2020 guidelines
3. Dual screening and data extraction
4. Risk of bias assessment using validated tools

### 4.4 Limitations

1. Substantial heterogeneity across studies
2. Some studies at high risk of bias
3. Limited long-term outcome data

### 4.5 Implications

**Clinical Practice:**
[Clinical implications]

**Future Research:**
[Research priorities]
""",

    "5. Conclusion": """
## 5. Conclusion

This systematic review provides evidence that [intervention] [effect] compared to [comparator]. The certainty of evidence is [high/moderate/low/very low] for [outcome].

**Key Message:**
[Principal conclusion for clinical practice]
"""
}


# ============================================================================
# CONSORT 2010 Section Templates
# ============================================================================

CONSORT_TEMPLATES = {
    "1. Introduction": """
## 1. Introduction

### 1.1 Background and Rationale

[Condition] affects approximately [X] per 100,000 population annually [1]. Despite advances in treatment, [unmet need]. Standard therapies including [treatments] have limitations including [limitations].

### 1.2 Objectives

**Primary Objective:**
To compare [intervention] versus [comparator] on [primary endpoint].

**Secondary Objectives:**
1. To assess overall survival
2. To evaluate safety and tolerability
3. To characterize quality of life

### 1.3 Hypotheses

**Primary Hypothesis:**
H₀: No difference in [primary endpoint] between groups
H₁: Significant difference exists between groups
""",

    "2. Methods": """
## 2. Methods

### 2.1 Trial Design

This [phase], multicenter, [parallel/crossover], randomized controlled trial compared [intervention] to [comparator] with [1:1] randomization.

### 2.2 Participants

**Inclusion Criteria:**
- Adults ≥18 years with [condition]
- Confirmed diagnosis by [criteria]
- Adequate organ function
- ECOG PS 0-1

**Exclusion Criteria:**
- Prior treatment with [therapy]
- Significant comorbidities
- Concomitant medications contraindicated

**Settings:** [Number] sites in [countries]

### 2.3 Interventions

**Experimental Arm:**
- [Intervention]: [Dose] [route] [schedule]

**Control Arm:**
- [Comparator]: [Dose] [route] [schedule]

### 2.4 Outcomes

**Primary Endpoint:** [Primary endpoint] at [timepoint]

**Secondary Endpoints:**
1. [Secondary 1] at [timepoint]
2. [Secondary 2] at [timepoint]
3. Overall survival
4. Safety endpoints

### 2.5 Sample Size

Based on [assumptions], [N] patients ([N] per group) were required to detect [effect size] with [power]% power at α=[X].

### 2.6 Randomization

**Sequence Generation:** [Method, e.g., "permuted block randomization"]

**Allocation Concealment:** [Method, e.g., "central randomization system"]

**Implementation:** [Details]

### 2.7 Blinding

This was a [double-blind/single-blind/open-label] trial. [Blinding procedures]

### 2.8 Statistical Methods

Primary analysis was ITT using [method]. Two-sided α=[X]. Analyses were performed using [software].
""",

    "3. Results": """
## 3. Results

### 3.1 Participant Flow

[N] patients were randomized: [N] to [intervention], [N] to [comparator]. The CONSORT flow diagram is presented in Figure 1.

**Enrollment:**
- Randomized: [N]
- Allocated intervention: [N]
- Received allocated intervention: [N]

**Follow-up:**
- Lost to follow-up: [N] per arm

**Analysis:**
- Analyzed: [N] per arm

### 3.2 Baseline Data

Baseline characteristics were balanced between arms.

**Table 1. Baseline Characteristics**

| Characteristic | Intervention | Control |
|--------------|--------------|----------|
| Age, mean (SD) | XX.X | XX.X |
| Male, n (%) | XX (XX.X) | XX (XX.X) |

### 3.3 Outcomes

**Primary Endpoint:**

At [timepoint], [X]% achieved [endpoint] with [intervention] versus [Y]% with [comparator] (HR [X.XX], 95% CI [X.XX-X.XX], P=[X.XXX]).

**Table 2. Efficacy Outcomes**

| Endpoint | Intervention | Control | HR/RR (95% CI) | P-value |
|----------|--------------|----------|------------------|----------|
| [Primary] | XX.X% | XX.X% | X.XX (X.XX-X.XX) | X.XXX |

### 3.4 Adverse Events

| Category | Intervention n (%) | Control n (%) |
|----------|-------------------|---------------|
| Any AE | XX (XX.X) | XX (XX.X) |
| Grade ≥3 AE | XX (XX.X) | XX (XX.X) |
| SAE | XX (XX.X) | XX (XX.X) |
""",

    "4. Discussion": """
## 4. Discussion

### 4.1 Interpretation

This trial demonstrated that [intervention] significantly [improved/did not improve] [endpoint] compared to [comparator] in [population].

### 4.2 Generalizability

The findings may apply to [population] but may not generalize to [limitations].

### 4.3 Limitations

1. [Limitation 1]
2. [Limitation 2]

### 4.4 Trial Registration

Registered at ClinicalTrials.gov (NCT[XXXXXXXX]) on [date].
""",

    "5. Other Information": """
## 5. Other Information

### 5.1 Conflicts of Interest

[Author conflicts]

### 5.2 Funding

[Funding sources]

### 5.3 Author Contributions

- Study concept: [Authors]
- Data collection: [Authors]
- Statistical analysis: [Authors]
- Manuscript writing: [Authors]
"""
}


# ============================================================================
# CARE 2013 Section Templates
# ============================================================================

CARE_TEMPLATES = {
    "1. Introduction": """
## 1. Introduction

### 1.1 Background and Context

[Condition] is characterized by [pathophysiology]. Standard presentation includes [features], but atypical presentations occur.

### 1.2 Why Is This Case Significant?

This case demonstrates [unique feature 1], [unique feature 2], and [unique feature 3]. Such presentations are rare, with limited reports in the literature.

### 1.3 Objective

This report aims to document [objective] and inform clinical practice.
""",

    "2. Case Presentation": """
## 2. Case Presentation

### 2.1 Patient Information

A [XX]-year-old [male/female] presented with [chief complaint].

**History:** [Chronological presentation]

**Past Medical History:** [Relevant conditions]

**Medications:** [Current medications]

### 2.2 Clinical Findings

**Vital Signs:** [Vitals]

**Physical Examination:**
- [Relevant findings]

**Laboratory Studies:**
- [Results]

**Imaging:**
- [Findings]

**Biopsy:**
- [Histopathological findings]

### 2.3 Timeline

| Date | Event |
|-------|--------|
| [Date] | Presentation |
| [Date] | Diagnosis |
| [Date] | Treatment initiated |
| [Date] | Response assessment |

### 2.4 Diagnostic Assessment

**Differential Diagnosis:**
1. [DDx 1]
2. [DDx 2]
3. [DDx 3]

**Final Diagnosis:** [Confirmed diagnosis]

### 2.5 Therapeutic Intervention

[Treatment rationale and details]

### 2.6 Follow-up and Outcomes

At [timepoint] follow-up: [outcome]
""",

    "3. Discussion": """
## 3. Discussion

### 3.1 Strengths and Limitations

**Strengths:** Comprehensive diagnostic workup, detailed documentation.

**Limitations:** Single case, cannot generalize.

### 3.2 Comparison with Similar Cases

This case [shares similarities with/differs from] previous reports [1, 2].

### 3.3 Clinical Implications

Clinicians should consider [recommendation] in similar presentations.
""",

    "4. Informed Consent": """
## Informed Consent

Written informed consent was obtained from the patient for publication of this case report.
"""
}


# ============================================================================
# Template Access Functions
# ============================================================================

def get_prisma_template(section_name: str) -> str:
    """Get PRISMA 2020 section template."""
    return PRISMA_TEMPLATES.get(section_name, "## " + section_name + "\n\n[Content to be added]")

def get_consort_template(section_name: str) -> str:
    """Get CONSORT 2010 section template."""
    return CONSORT_TEMPLATES.get(section_name, "## " + section_name + "\n\n[Content to be added]")

def get_care_template(section_name: str) -> str:
    """Get CARE 2013 section template."""
    return CARE_TEMPLATES.get(section_name, "## " + section_name + "\n\n[Content to be added]")

def get_all_prisma_sections() -> Dict[str, str]:
    """Get all PRISMA section templates."""
    return PRISMA_TEMPLATES.copy()

def get_all_consort_sections() -> Dict[str, str]:
    """Get all CONSORT section templates."""
    return CONSORT_TEMPLATES.copy()

def get_all_care_sections() -> Dict[str, str]:
    """Get all CARE section templates."""
    return CARE_TEMPLATES.copy()


if __name__ == "__main__":
    print("HPW Section Templates Module Loaded")
    print(f"PRISMA sections: {list(PRISMA_TEMPLATES.keys())}")
    print(f"CONSORT sections: {list(CONSORT_TEMPLATES.keys())}")
    print(f"CARE sections: {list(CARE_TEMPLATES.keys())}")
