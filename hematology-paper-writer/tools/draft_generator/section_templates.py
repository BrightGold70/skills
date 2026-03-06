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

This systematic review was conducted to evaluate the efficacy and safety of [intervention] compared with [comparator] in patients with [condition]. The primary objective was to determine [primary endpoint] at [assessment timepoint] in this population. Secondary objectives included characterizing [secondary objective 1], evaluating [secondary objective 2], and assessing the safety profile of [intervention] including the incidence and severity of adverse events, treatment discontinuation rates, and dose modification requirements. These objectives were pre-specified in the registered protocol prior to data collection.

### 1.3 Research Question

This systematic review evaluated the efficacy and safety of [intervention] at any approved dose in adults with [condition], compared with [comparator] or best available care, with [primary endpoint] as the primary outcome. The population of interest comprised adults aged 18 years or older with a confirmed diagnosis of [condition] according to current diagnostic criteria. Secondary outcomes included [secondary outcome 1], [secondary outcome 2], [secondary outcome 3], and overall survival. This PICO framework was defined a priori and remained unchanged throughout the review process.
""",

    "2. Methods": """
## 2. Methods

This systematic review was conducted and reported in accordance with the PRISMA 2020 statement [1] and was registered prospectively with PROSPERO (Registration Number: [CRDXXXXXXXXX]).

### 2.1 Eligibility Criteria

We included randomized controlled trials and prospective cohort studies enrolling adults aged 18 years or older with a confirmed diagnosis of [condition] according to current diagnostic criteria. Eligible studies were required to evaluate [intervention] at any approved or investigational dose as monotherapy or combination therapy, administered in comparison with [comparator], placebo, or best available care, and to report at least one pre-specified efficacy or safety endpoint with a minimum follow-up of [minimum follow-up]. Studies published in peer-reviewed journals in any language were eligible for inclusion, provided that a full-text version or complete translation could be obtained.

We excluded case reports and case series enrolling fewer than 20 participants, given the limited statistical precision of estimates derived from such studies. Animal studies, in vitro experiments, pharmacokinetic studies without clinical outcomes, and conference abstracts without an accompanying peer-reviewed full-text publication were not eligible. Duplicate publications reporting data from the same patient cohort were excluded; in cases of overlapping study populations, the publication with the longest follow-up or largest sample size was retained.

### 2.2 Information Sources

We conducted a systematic search of PubMed/MEDLINE, Embase, Cochrane Central Register of Controlled Trials (CENTRAL), and Web of Science Core Collection from inception through [date], with no date or language restrictions applied. Grey literature was systematically searched through ClinicalTrials.gov and the WHO International Clinical Trials Registry Platform (ICTRP) to capture data from completed and ongoing registered trials. Conference proceedings from the American Society of Hematology (ASH), European Hematology Association (EHA), and American Society of Clinical Oncology (ASCO) annual meetings from the preceding five years were hand-searched for relevant abstracts subsequently published as full-text articles. Reference lists of all included studies and pertinent systematic reviews were manually screened to identify additional eligible publications not captured by the electronic database search.

### 2.3 Search Strategy

The search strategy was developed in collaboration with a health sciences librarian with expertise in systematic review methodology, and was peer-reviewed by a second librarian using the Peer Review of Electronic Search Strategies (PRESS) checklist. The search combined controlled vocabulary terms (MeSH for PubMed/MEDLINE; Emtree for Embase) with free-text terms for [condition] and [intervention]. Boolean operators and truncation symbols were adapted to each database's syntax. Full search strings for all databases are provided in Supplementary Appendix 1.

### 2.4 Selection Process

Two independent reviewers screened all titles and abstracts identified by the search against the pre-specified eligibility criteria using a standardized screening form in [software]. Full-text articles were retrieved for all potentially eligible records and independently assessed for inclusion by both reviewers. Discrepancies at either the title/abstract or full-text screening stage were resolved through discussion, and where consensus could not be reached, a third independent reviewer adjudicated. Inter-rater reliability at the full-text screening stage was calculated using Cohen's kappa coefficient. The complete study selection process is documented in a PRISMA 2020 flow diagram (Figure 1).

### 2.5 Data Extraction

Two reviewers independently extracted data from each included study using a standardized extraction form developed and piloted prior to data collection. Extracted items included study characteristics (design, setting, enrollment period), participant demographics and disease characteristics at baseline, intervention details (dose, schedule, duration), primary and secondary outcome data with effect estimates and confidence intervals, and adverse event data stratified by grade. Discrepancies in extracted data were resolved by consensus or by consulting the original publication. Where data required for analysis were not reported in the manuscript, corresponding authors were contacted by electronic mail.

### 2.6 Risk of Bias Assessment

Risk of bias in randomized controlled trials was assessed using the revised Cochrane risk-of-bias tool (RoB 2.0) [2], which evaluates bias arising from the randomization process, deviations from intended interventions, missing outcome data, measurement of the outcome, and selection of the reported result. Non-randomized studies of interventions were assessed using the ROBINS-I tool [3], which evaluates confounding, selection bias, classification bias, and reporting bias. Each domain was rated as low, moderate, serious, or critical risk of bias. Two reviewers independently assessed each study, with disagreements resolved by consensus.

### 2.7 Synthesis Methods

A narrative synthesis was performed for all outcomes, organized by outcome type and study design. Quantitative meta-analysis was conducted where two or more studies reported the same outcome with sufficient data using a random-effects model with the DerSimonian-Laird estimator. Effect estimates are presented as risk ratios or mean differences with 95% confidence intervals. Statistical heterogeneity was quantified using the I² statistic and Cochran's Q test; I² values greater than 50% were considered indicative of substantial heterogeneity. Pre-specified subgroup analyses were performed to explore potential sources of heterogeneity. Publication bias was assessed using funnel plot asymmetry and Egger's test where ten or more studies contributed to a pooled estimate.
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
