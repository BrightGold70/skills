# Writing Standards Reference

## Table of Contents
- [Part 1: Web Search Integration](#part-1-web-search-integration-for-medical-writing) — L1
- [CRITICAL: Manuscript Writing Standards](#critical-manuscript-writing-standards) — L150
- [Part 2: Document Type Templates](#part-2-document-type-templates) — L248 (systematic review, RCT, case report, clinical trial)

---

## Part 1: Web Search Integration for Medical Writing

### Overview

The hematology paper writer integrates web search capabilities to:
- Find recent publications and preprints
- Access clinical trial registries (ClinicalTrials.gov, ICTRP)
- Gather guideline information (NCCN, ELN, ESMO)
- Retrieve regulatory updates (FDA, EMA)
- Collect real-world evidence and real-time data

### NotebookLM Integration (PRIMARY DATA SOURCE)

**IMPORTANT**: Before any PubMed search, MUST query NotebookLM first:

1. **NotebookLM MCP Authentication** (REQUIRED for every session):
   - Use `notebooklm_setup_auth` for initial Google authentication
   - Use `notebooklm_get_health` to verify authentication status
   - Authentication is session-based - re-authenticate if needed

2. **Query NotebookLM Research**:
   - Use `notebooklm_ask_question` to query existing research data
   - If NotebookLM has relevant data, USE IT as primary source
   - Extract key findings, trial data, and clinical evidence from NotebookLM

3. **Fallback to PubMed** (ONLY if NotebookLM has no data):
   - If NotebookLM query returns "no relevant information" or similar
   - Then proceed with PubMed search using PubMedSearcher
   - Document that NotebookLM was checked first

**Workflow:**
```
1. notebooklm_setup_auth (if not authenticated)
2. notebooklm_get_health (verify auth)
3. notebooklm_ask_question("What is the evidence for [topic]?")
4. IF response has relevant data → Use as primary source
5. ELSE → Proceed with PubMed search
```

### NotebookLM Query Templates

Use these templates for common manuscript queries:

**Trial Results Query:**
```
What are the key efficacy results from [trial name]? Include specific data: [response rate], [survival endpoints], [p-values].
```

**Safety Data Query:**
```
What are the safety and adverse event data from [study/trial]? Include: [specific AEs], discontinuation rates, serious events.
```

**Mechanism Query:**
```
What is the mechanism of action for [drug]? How does it differ from [comparator drugs]?
```

**Guideline Query:**
```
What are the current [ELN/NCCN] recommendations for [disease] treatment? Include specific criteria for [treatment decision].
```

**Epidemiology Query:**
```
What is the epidemiology of [disease]? Include incidence, prevalence, risk factors, and mortality data.
```

**Comparison Query:**
```
Compare [treatment A] vs [treatment B] for [disease]. Include efficacy, safety, and response rates.
```

### Web Search Sources

**Academic Databases:**
- **PubMed** (pubmed.ncbi.nlm.nih.gov) - Primary medical literature
- **Google Scholar** (scholar.google.com) - Broad academic search
- **IEEE Xplore** - Engineering/biomedical research
- **Cochrane Library** - Systematic reviews and meta-analyses
- **EMBASE** - European biomedical literature

**Clinical Registries:**
- **ClinicalTrials.gov** - Clinical trial results and status
- **ICTRP** (WHO) - International clinical trial registry
- **EudraCT** - European clinical trial registry

**Guidelines:**
- **NCCN Guidelines** - National Comprehensive Cancer Network
- **ELN Recommendations** - European LeukemiaNet
- **ESMO Guidelines** - European Society for Medical Oncology

**Regulatory:**
- **FDA** (fda.gov) - Drug approvals, safety alerts
- **EMA** (ema.europa.eu) - European Medicines Agency
- **PMDA** (pmda.go.jp) - Pharmaceuticals and Medical Devices Agency (Japan)

### Search Strategy Framework

**Step 1: Broad Discovery**
```
Search: "chronic myeloid leukemia treatment 2024"
Targets: PubMed, Google Scholar, ClinicalTrials.gov
```

**Step 2: Focused Retrieval**
```
Search: "asciminib versus imatinib ASC4FIRST trial results"
Targets: PubMed, ClinicalTrials.gov
```

**Step 3: Grey Literature**
```
Search: "asciminib FDA approval label indication"
Targets: FDA website, EMA, regulatory databases
```

**Step 4: Guideline Integration**
```
Search: "ELN 2025 CML treatment recommendations"
Targets: NCCN, ELN, ESMO websites
```

---

### Integrated Skill: literature-review

For systematic literature reviews requiring rigorous methodology, use the **`literature-review`** skill:

**When to invoke:**
- Systematic reviews with PRISMA compliance
- Meta-analyses requiring pooled effect estimates
- Scoping reviews withArksey & O'Malley framework
- Rapid reviews with accelerated timelines

**Skill invocation:**
```
Use the literature-review skill for:
- Structured review protocols (PICO, SPIDER)
- Search strategy development with Boolean operators
- Study selection and data extraction workflows
- Risk of bias assessment (ROB 2.0, ROBINS-I)
- Evidence synthesis and heterogeneity analysis
```

**Complementary use:** The literature-review skill enhances Part 1 by providing systematic review methodology for comprehensive literature searches.

---

## CRITICAL: Manuscript Writing Standards

### Prose-Only Requirement (MANDATORY)

When writing any manuscript section:
- ❌ **NEVER use bullet points** (`•`, `-`, `*`)
- ❌ **NEVER use numbered lists** for content
- ✅ **ALWAYS use flowing prose** with complete paragraphs
- ✅ **Use academic transitions** between ideas
- ✅ **Provide comprehensive explanations** - don't just list facts

**Example Conversion:**
```
BAD (bullet points):
• MMR at 48 weeks: 67.7% vs 49.0%
• MR4 at 48 weeks: 38.8% vs 20.6%
• Discontinuation: 4.5% vs 11.1%

GOOD (prose):
The major molecular response rate at 48 weeks was significantly higher in the asciminib group compared to standard therapy, with 67.7% of patients achieving MMR versus 49.0% in the control arm [1]. This represents an absolute difference of 18.9 percentage points. Furthermore, deep molecular responses were substantially more common with asciminib, as MR4 was achieved by 38.8% of patients receiving asciminib compared to only 20.6% of those on standard tyrosine kinase inhibitors [1]. The clinical significance of these deeper responses is particularly relevant for patients who may be candidates for treatment-free remission, as sustained MR4 or better for at least two years is considered a prerequisite for attempting therapy discontinuation [2]. Notably, the rate of treatment discontinuation due to adverse events was substantially lower with asciminib at 4.5% compared to 11.1% in the imatinib group, suggesting improved tolerability that may facilitate long-term treatment adherence [1].
```

### Citation Density Rule (MANDATORY - PLAGIARISM PREVENTION)

**THIS IS CRITICAL**: Every sentence that presents data, makes claims, or references specific findings MUST have a citation.

**Citation Requirements:**
- Minimum 25-35 references for a systematic review (~5,000-7,000 words)
- Every factual statement needs a citation
- Multiple citations per sentence are acceptable
- Claims without citations = PLAGIARISM concern

**Citation Placement Examples:**
```
BAD (no citation - plagiarism):
Chronic myeloid leukemia is a hematologic malignancy characterized by the
Philadelphia chromosome.

GOOD (with citation):
Chronic myeloid leukemia is a hematologic malignancy characterized by the
Philadelphia chromosome, which results from the t(9;22)(q34;q11) translocation
that creates the BCR::ABL1 fusion oncogene [1].

BAD (multiple claims, single citation):
Imatinib revolutionized CML treatment and has high response rates.

GOOD (multiple claims, multiple citations):
Imatinib revolutionized CML treatment by targeting the BCR::ABL1 tyrosine kinase,
becoming the standard of care since its introduction in 2001 [2]. Subsequent
generations of TKIs have demonstrated higher response rates compared with
imatinib in randomized trials [3][4].
```

**Reference Diversity Target:**
| Type | Target Count | Purpose |
|------|-------------|---------|
| Clinical trials | 8-12 | Primary efficacy/safety data |
| Systematic reviews | 3-5 | Evidence synthesis |
| Guidelines | 2-3 | Clinical practice standards |
| Mechanistic studies | 3-5 | Biological rationale |
| Real-world evidence | 2-3 | Generalizability |
| Safety/pharmacovigilance | 2-3 | Adverse event data |

### Abstract Expansion (MANDATORY)

The abstract is the most critical part - it must be fully expanded:
- Target **95-100% of journal's word limit**
- Include comprehensive background, methods, results, conclusions
- Every sentence should convey substantial information
- Avoid redundancy - each word should add value

**Blood Research Abstract Structure (~250 words):**
```
Background: [2-3 sentences on disease burden and treatment evolution]
Objective: [1 sentence on systematic review purpose]
Methods: [2-3 sentences on search strategy, inclusion criteria, endpoints]
Results: [4-5 sentences on key findings with specific data]
Conclusions: [2-3 sentences on clinical implications]
```

### Detailed Explanations Throughout

Every manuscript section must include:
1. **Mechanistic explanations** - How and why things work
2. **Clinical significance** - Why it matters for patients
3. **Contextual background** - Historical and current perspectives
4. **Limitations and strengths** - Critical appraisal
5. **Future directions** - Research gaps and opportunities

**Section Expansion Guidelines:**
- Introduction: 3-4 substantial paragraphs per subsection
- Methods: 2-3 paragraphs explaining each procedure
- Results: Narrative descriptions, not just data presentation
- Discussion: 3-4 paragraphs per major finding
- Conclusion: 1-2 paragraphs synthesizing key points

---

## Part 2: Document Type Templates

### 2.1 Systematic Review (PRISMA 2020 Compliant)

**CRITICAL Requirements:**
- Abstract: ~250 words (target 240-250 for Blood Research)
- NO bullet points - all prose
- Detailed explanations in every section
- Include PMID for all references
- Verify 100% match with PubMed

**Structure:**
```
1. Title
   - Clear indication of systematic review
   - "A Systematic Review" or "Systematic Review and Meta-Analysis"

2. Abstract (250 words - EXPANDED)
   - Background: 2-3 sentences on disease burden, treatment evolution, rationale
   - Methods: 2-3 sentences on databases, search terms, inclusion criteria
   - Results: 4-5 sentences on key findings with specific data points
   - Conclusions: 2-3 sentences on clinical implications
   - Registration: PROSPERO registration number

3. Introduction
   3.1 Background and rationale (3-4 substantial paragraphs)
   3.2 Objectives (1-2 paragraphs)
   3.3 Research questions (PICO framework) (1 paragraph)

4. Methods
   4.1 Protocol and registration (PROSPERO) (2-3 paragraphs)
   4.2 Eligibility criteria (PICO) (2-3 paragraphs)
   4.3 Information sources (databases, date ranges) (2 paragraphs)
   4.4 Search strategy (full search strings) (2 paragraphs)
   4.5 Selection process (PRISMA flow diagram) (2 paragraphs)
   4.6 Data extraction process (2 paragraphs)
   4.7 Data items (1-2 paragraphs)
   4.8 Study risk of bias assessment (ROB 2.0, ROBINS-I) (2 paragraphs)
   4.9 Effect measures (1-2 paragraphs)
   4.10 Synthesis methods (fixed vs random effects) (2 paragraphs)

5. Results
   5.1 Study selection (PRISMA flow diagram with numbers) (2-3 paragraphs)
   5.2 Study characteristics (Table 1) (2-3 paragraphs)
   5.3 Risk of bias in studies (2 paragraphs)
   5.4 Results of individual studies (3-4 paragraphs)
   5.5 Results of syntheses (forest plots) (2-3 paragraphs)
   5.6 Reporting biases assessment (funnel plots) (1-2 paragraphs)

6. Discussion
   6.1 Discussion of results (3-4 paragraphs with detailed explanations)
   6.2 Discussion of limitations (2-3 paragraphs)
   6.3 Implications for practice (2-3 paragraphs)
   6.4 Implications for research (2 paragraphs)

7. Conclusion
   7.1 Main findings (1-2 paragraphs)
   7.2 Strengths and limitations (2 paragraphs)
   7.3 Future directions (1-2 paragraphs)

8. References (ALL with PMID)
```

**Key PRISMA 2020 Items:**
- Item 1: Title identifies as systematic review, meta-analysis, or both
- Item 2: Structured summary in abstract
- Item 4: Explicit statement of eligibility criteria
- Item 5: Information sources with dates searched
- Item 6: Full electronic search strategy for at least one database
- Item 7: Process for selecting studies
- Item 8: Process for data extraction
- Item 9: List of all studies and justification for exclusions
- Item 10: Description of risk of bias in studies
- Item 11: Methods for effect measures
- Item 12: Methods for synthesis methods
- Item 13: Methods for assessing risk of bias from synthesis
- Item 14: Description of heterogeneity
- Item 15: Reporting of results from syntheses
- Item 16: Results of syntheses
- Item 17: Results of risk of bias assessments
- Item 18: Results of study certainty assessments

### 2.2 Meta-Analysis Structure

**Additional Elements for Meta-Analysis:**

```
4.11 Statistical Methods for Meta-Analysis
   - Fixed-effect vs random-effects models
   - Methods for handling missing data
   - Assessment of publication bias (Egger's test)
   - Sensitivity analyses
   - Subgroup analyses
   - Meta-regression (if applicable)

5. Results
   5.7 Quantitative Synthesis (Meta-Analysis Results)
      - Pooled effect estimates with 95% CI
      - Heterogeneity statistics (I², tau²)
      - Forest plot interpretation
      - Subgroup analyses results
      - Sensitivity analyses results

Reporting Checklist for Meta-Analysis:
- PRISMA flow diagram with meta-analysis specifics
- Characteristics of included studies (Table)
- Risk of bias assessment for each study
- Forest plots for all outcomes
- Funnel plots for publication bias
- GRADE assessment for evidence quality
```

### 2.3 Clinical Trial Reporting (CONSORT 2010 Compliant)

**Structure:**
```
1. Title
   - Trial design identification
   - "Randomized Controlled Trial" specified

2. Authors and Affiliations

3. Abstract (Structured, 250 words)
   - Background
   - Methods (trial design, participants, interventions, outcomes)
   - Results (numbers randomized, analyzed, main outcomes)
   - Conclusions (interpretation, generalizability)
   - Trial registration (NCT number)
   - Funding source

4. Introduction
   4.1 Background and rationale
   4.2 Objectives
   4.3 Hypotheses

5. Methods
   5.1 Trial design (parallel, crossover, factorial)
   5.2 Changes to methods after trial start
   5.3 Eligibility criteria
   5.4 Settings and locations
   5.5 Interventions (detailed description)
   5.6 Outcomes (primary and secondary, changes)
   5.7 Sample size calculation
   5.8 Randomization sequence generation
   5.9 Allocation concealment mechanism
   5.10 Implementation of randomization
   5.11 Blinding (who was blinded, how)
   5.12 Statistical methods (primary/secondary analyses)

6. Results
   6.1 Participant flow (CONSORT flow diagram)
   6.2 Recruitment dates
   6.3 Baseline demographic data (Table)
   6.4 Numbers analyzed
   6.5 Outcomes and estimation for each group
   6.6 Ancillary analyses
   6.7 Harms (adverse events)

7. Discussion
   7.1 Limitations
   7.2 Generalizability
   7.3 Interpretation

8. Other Information
   8.1 Registration number and name
   8.2 Protocol access
   8.3 Funding

9. References
```

**CONSORT 2010 Checklist Items:**
- Title identifies as randomized trial
- Structured abstract
- Scientific background and rationale
- Specific objectives/hypotheses
- Trial design description
- Changes to methods after trial start
- Eligibility criteria, settings, locations
- Detailed interventions per group
- Completely defined pre-specified outcomes
- Sample size determination
- Randomization sequence generation
- Allocation concealment mechanism
- Implementation of random allocation
- Blinding details
- Statistical methods for each outcome
- Participant flow diagram (CONSORT)
- Dates of recruitment and follow-up
- Baseline demographic data
- Numbers analyzed per group
- Outcomes and estimation with CIs
- Ancillary analyses
- Adverse events in each group
- Limitations, generalizability, interpretation
- Registration, protocol access, funding

### 2.4 Case Report (CARE Compliant)

**Structure:**
```
1. Title
   - "Case Report" or "Case Series" in title
   - Patient identifier optional (e.g., "A case of...")

2. Abstract (Structured, 200 words)
   - Context: What makes this case unique?
   - Case: Summary of patient(s)
   - Conclusions: What is the main takeaway?

3. Introduction
   3.1 Background and context
   3.2 Why is this case significant?
   3.3 Objective: What does this report aim to achieve?

4. Case Presentation
   4.1 Patient information
      - Age, sex, presenting concerns
      - Medical, family, psychosocial history
      - Relevant past interventions
   4.2 Clinical findings
      - Physical examination findings
      - Laboratory and imaging results
   4.3 Timeline
      - Detailed chronological sequence
      - From presentation to outcome
   4.4 Diagnostic assessment
      - Diagnostic methods
      - Diagnostic challenges
      - Differential diagnosis
   4.5 Therapeutic intervention
      - Types of interventions
      - Administration and duration
      - Modifications to intervention
   4.6 Follow-up and outcomes
      - How outcomes were assessed
      - Relevant follow-up findings
      - Patient perspective (if available)
      - Adverse events

5. Discussion
   5.1 Strengths and limitations
   5.2 Comparison with similar cases
   5.3 Scientific background and rationale
   5.4 Systematic literature review
   5.5 Theoretical implications
   5.6 Practical implications
   5.7 Conclusions

6. Patient Perspective (Optional)
   - Patient's experience and outcomes

7. Informed Consent
   - Statement of consent obtained

8. References
```

**CARE Checklist Items:**
- Title identifies as case report
- Structured abstract
- Context and clinical significance
- Patient information (anonymized)
- Case presentation with timeline
- Clinical findings
- Diagnostic assessments
- Therapeutic interventions
- Follow-up and outcomes
- Discussion of differential diagnosis
- Comparison with literature
- Informed consent statement

---

