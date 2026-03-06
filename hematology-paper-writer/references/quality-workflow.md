# Quality Assurance & Workflow Reference

## Table of Contents
- [Part 4: Source Discovery and Verification](#part-4-source-discovery-and-verification) — L1
- [Part 5: Quality Assurance Checklist](#part-5-quality-assurance-checklist) — L80
- [Part 6: Commands Reference](#part-6-commands) — L152
- [Part 7: Supported Journals](#part-7-supported-journals) — L232
- [Part 8: Workflow Examples](#part-8-workflow-examples) — L247

---

## Part 4: Source Discovery and Verification

### Finding Sources

Search these academic databases:
- **PubMed** (pubmed.ncbi.nlm.nih.gov) - Primary for medical research
- **Google Scholar** (scholar.google.com) - Broad academic search
- **IEEE Xplore** (ieeexplore.ieee.org) - Engineering/biomedical
- **Cochrane Library** - Systematic reviews
- **EMBASE** - European biomedical literature
- **ClinicalTrials.gov** - Clinical trial results
- **ICTRP** - WHO clinical trial registry

### Web Search Integration

```python
# Example: Search for clinical trial data
web_search("ASC4FIRST asciminib clinical trial results site:clinicaltrials.gov")

# Search for guidelines
web_search("NCCN CML guidelines 2024")

# Search for regulatory updates
web_search("asciminib FDA approval hematologic malignancies")
```

### Source Verification Checklist

For each source, verify:

- [ ] Published in peer-reviewed journal or conference
- [ ] Author credentials and institutional affiliation
- [ ] Publication venue reputation (impact factor)
- [ ] Citation count (higher indicates impact)
- [ ] Methodology soundness
- [ ] Relevance to research question
- [ ] **PMID/DOI available for PubMed verification (MANDATORY)**
- [ ] For clinical trials: NCT registration verified
- [ ] For guidelines: Organization credibility confirmed
- [ ] **Reference matches PubMed record exactly (100% match required)**

### Red Flags (Exclude These Sources)

- ❌ Predatory journals (check Beall's List)
- ❌ Lack of peer review process
- ❌ No institutional affiliation
- ❌ Suspicious publication practices
- ❌ Pay-to-publish without legitimate review
- ❌ Non-peer-reviewed websites (Wikipedia, blogs)
- ❌ Unregistered clinical trials
- ❌ References without PMID (cannot verify)

---

### Integrated Skill: pubmed-integration

For advanced PubMed search capabilities and biomedical literature discovery, use the **`pubmed-integration`** skill:

**When to invoke:**
- Complex PubMed queries with Boolean operators
- Biomedical literature with MeSH term exploration
- Citation chaining (forward/backward)
- Clinical query filtering (therapy, diagnosis, prognosis)
- PubMed API integration for automated searches

**Skill invocation:**
```
Use the pubmed-integration skill for:
- Advanced PubMed search syntax (AND, OR, NOT, [MeSH], [Title/Abstract])
- Clinical query filters (therapeutic, diagnostic, etiological)
- Citation network analysis
- PubMed API batch search operations
- MeSH heading exploration and hierarchy navigation
```

**Complementary use:** The pubmed-integration skill enhances Part 4 Source Discovery with advanced PubMed search capabilities and biomedical-specific search features.

---

## Part 5: Quality Assurance Checklist

### Before Finalizing, Verify:

**Content:**
- [ ] Clear research question/objective stated
- [ ] Logical flow and organization
- [ ] **Adequate source coverage (≥25-35 references for systematic reviews)**
- [ ] All sources verified as peer-reviewed
- [ ] **All claims supported by citations (citation density check PASSED)**
- [ ] **NO uncited factual statements - every sentence with data has [citation]**
- [ ] Methodology clearly explained (if applicable)
- [ ] Results/findings clearly presented with statistics
- [ ] Limitations acknowledged

**Citation Density Verification (MANDATORY):**
- [ ] Count total references (target: 25-35 for ~6,500 words)
- [ ] Review each paragraph for uncited factual claims
- [ ] Ensure every statistical data point has citation
- [ ] Ensure every study/trial mentioned has citation
- [ ] Ensure every guideline statement has citation
- [ ] Verify no "copying" of ideas without attribution

**Citation VERIFICATION Process (MANDATORY - Every citation):**
- [ ] Query NotebookLM for each cited source
- [ ] Verify claimed data exists in source
- [ ] Confirm statistics/percentages match exactly
- [ ] Check PMID validity (for PubMed sources)
- [ ] Document verification status for each claim
- [ ] Fix any discrepancies before finalizing

**For Systematic Reviews:**
- [ ] PRISMA flow diagram included
- [ ] Search strategy fully documented
- [ ] Risk of bias assessment performed
- [ ] Heterogeneity statistics reported
- [ ] Registration number (PROSPERO) provided

**For Clinical Trials:**
- [ ] CONSORT flow diagram included
- [ ] Sample size calculation justified
- [ ] Randomization methods described
- [ ] Blinding procedures documented
- [ ] Adverse events fully reported
- [ ] Trial registration number included

**For Case Reports:**
- [ ] CARE checklist completed
- [ ] Timeline clearly presented
- [ ] Diagnostic reasoning explained
- [ ] Treatment rationale provided
- [ ] Informed consent statement included
- [ ] Patient perspective considered

**Technical:**
- [ ] Reference format consistent (Vancouver)
- [ ] All in-text citations match reference list
- [ ] No missing references in list
- [ ] Citation numbering sequential
- [ ] DOI included when available

**Writing Quality:**
- [ ] Academic tone maintained throughout
- [ ] Clear and concise language
- [ ] No grammatical or spelling errors
- [ ] Smooth transitions between sections
- [ ] Abstract accurately summarizes paper
- [ ] Keywords appropriately selected

---

## Part 6: Commands

### 1. Literature Search

```bash
# Search PubMed for articles
hpw search-pubmed "asciminib chronic myeloid leukemia" --max-results 50

# With time period filter
hpw search-pubmed "CAR-T cell therapy ALL" --max-results 30 --time-period 5y

# Save results to JSON
hpw search-pubmed "novel mutations myeloproliferative" -o references.json

# Web search for clinical trials
hpw web-search "asciminib clinical trial NCT" --source clinicaltrials.gov

# Search guidelines
hpw web-search "ELN CML recommendations 2025" --source nccn.org
```

### 2. Manuscript Draft Creation

```bash
# Create systematic review draft
hpw create-systematic-review "asciminib first-line CML"   --journal blood_research   --prisma-compliant   --meta-analysis

# Create clinical trial report
hpw create-clinical-trial-report "phase III trial results"   --journal blood   --consort-compliant   --trial-registration NCT00000000

# Create case report
hpw create-case-report "rare CML presentation"   --journal blood_research   --care-compliant

# Create enhanced draft with web search
hpw create-enhanced "novel therapy myeloproliferative"   --document-type systematic_review   --web-search-enabled   --reference-style vancouver
```

### 3. Citation Concordance Check

```bash
# Check citation-reference consistency
hpw check-concordance manuscript.docx

# With format validation
hpw check-concordance manuscript.md --validate-format
```

### 4. Complete Research Workflow

```bash
# All-in-one: web search, PubMed search, draft, quality check, verify
hpw research "novel mutations myeloproliferative neoplasms"   --journal blood_research   --max-articles 30   --time-period 5y   --web-search   --docx
```

### 5. Quality Analysis

```bash
# Check manuscript quality
hpw check-quality manuscript.md --journal blood

# Validate against reporting guidelines
hpw check-quality manuscript.md --journal blood --prisma-check

# Save JSON report
hpw check-quality draft.md --journal blood -o quality_report.json
```

### 6. Reference Verification

```bash
# Verify all references against PubMed
hpw verify-references manuscript.md --journal blood

# Include clinical trial verification
hpw verify-references manuscript.md --verify-trials
```

---

## Part 7: Supported Journals

| Journal | Code | Abstract Limit | Text Limit | Reference Style |
|---------|------|--------------|------------|-----------------|
| Blood Research | blood_research | 250 | 6000 | Vancouver |
| Blood | blood | 200 | 5000 | Vancouver |
| Blood Advances | blood_advances | 250 | 6000 | Vancouver |
| JCO | jco | 250 | 4000 | Numbered |
| BJH | bjh | 200 | 5000 | Vancouver |
| Leukemia | leukemia | 200 | 5000 | Vancouver |
| Haematologica | haematologica | 250 | 5000 | Vancouver |

---

## Part 8: Workflow Examples

### Complete Systematic Review

```bash
# 1. Web search for recent evidence
hpw web-search "asciminib CML systematic review 2024"   --sources pubmed,clinicaltrials.gov,nccn.org

# 2. Systematic review draft with PRISMA compliance
hpw create-systematic-review "asciminib first-line CML"   --journal blood_research   --prisma-compliant   --meta-analysis   --max-references 50

# 3. Check concordance
hpw check-concordance asciminib_cml_systematic_review.md

# 4. Check quality with PRISMA validation
hpw check-quality asciminib_cml_systematic_review.md   --journal blood_research   --prisma-check

# 5. Verify references
hpw verify-references asciminib_cml_systematic_review.md   --verify-trials

# 6. Generate report
hpw generate-report asciminib_cml_systematic_review.md   --journal blood_research   --verify-references   -o final_report.txt
```

### Clinical Trial Report

```bash
# Create clinical trial report
hpw create-clinical-trial-report "novel agent phase III"   --journal blood   --consort-compliant   --trial-registration NCT00000000   --docx

# Quality check
hpw check-quality phase_iii_trial_report.md   --journal blood   --consort-check
```

### Case Report

```bash
# Create CARE-compliant case report
hpw create-case-report "atypical CML presentation"   --journal blood_research   --care-compliant   --include-patient-perspective

# Quality check
hpw check-quality atypical_cml_case.md   --journal blood_research   --care-check
```

---

