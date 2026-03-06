# Citations & Reference Formats

## Table of Contents
- [Part 3: Reference Formats](#part-3-reference-formats) — L1 (Vancouver, numbered, APA styles)
- [Part 3A: Citation Verification Protocol](#part-3a-citation-verification-protocol) — L109 (PubMed verification, concordance)

---

## Part 3: Reference Formats

### Vancouver (Numbered Format) - WITH PMID REQUIRED

**CRITICAL**: Every reference MUST include PMID for verification.

**Citation Method for Plagiarism Prevention:**

Every sentence that contains factual information, data, or claims MUST have a citation. This includes:

1. **Statistical data**: Any numbers, percentages, rates must cite source
   ```
   The MMR rate at 48 weeks was 67.7% in the asciminib arm [1].
   ```

2. **Study mentions**: Any named trial/study must have citation
   ```
   The ASC4FIRST trial demonstrated superior efficacy [1].
   ```

3. **Guideline statements**: Clinical recommendations need citation
   ```
   ELN recommendations endorse TKI discontinuation in eligible patients [15].
   ```

4. **Mechanistic facts**: Biological mechanisms need citation
   ```
   Asciminib binds to the myristate pocket, inducing conformational change [7].
   ```

5. **Historical facts**: Treatment evolution needs citation
   ```
   Imatinib became standard first-line therapy in 2001 [2].
   ```

**Common Citation Patterns:**

| Situation | Format | Example |
|-----------|--------|---------|
| Single fact | [1] | "MMR was achieved by 67.7% [1]." |
| Multiple facts | [1][2] | "Higher than imatinib (49.0%) [1] and dasatinib [2]." |
| Multiple studies | [1-3] | "Confirmed by multiple trials [1-3]." |
| Supporting + contrasting | [1][4] | "Efficacy shown [1] but safety concerns remain [4]." |

**DO NOT:**
- ❌ Make claims without citations
- ❌ State facts without attribution
- ❌ Describe study results without citation
- ❌ Mention guidelines without citation

**DO:**
- ✅ Cite every factual statement
- ✅ Use multiple citations when claiming multiple facts
- ✅ Cite primary sources for data (clinical trials, not reviews only)
- ✅ Include PMID for verification

**Journal Article:**
```
[1] Author AB, Author CD, Author EF. Title of article. Journal Name. Year;Volume(Issue):Pages. doi:xxx. PMID: 12345678
```

**Journal Article with Multiple Authors (>6):**
```
[2] Author A, Author B, Author C, et al. Title of article. Journal Name. Year;Volume:Pages. doi:xxx. PMID: 12345678
```

**Reference Verification Rule:**
- ❌ **NEVER** finalize manuscript without PubMed verification
- ✅ **ALWAYS** include PMID in reference
- ✅ Verify 100% match with PubMed record
- ✅ Fix any discrepancies before output

### Key Vancouver Rules

- Number references consecutively in order of appearance
- Use square brackets [1], [2], [3]
- List all authors up to 6; use "et al." if >6
- Use initials for first/middle names
- Abbreviate journal names per NLM standards
- Include DOI when available
- Maintain consistent formatting throughout

---

### Integrated Skill: citation-management

For multi-format citation handling and advanced reference management, use the **`citation-management`** skill:

**When to invoke:**
- Converting between citation styles (APA, AMA, Chicago, Harvard)
- Managing large reference libraries
- Formatting complex citations (conference proceedings, preprints, patents)
- Generating formatted bibliographies

**Skill invocation:**
```
Use the citation-management skill for:
- Vancouver format expansion (APA 7th, AMA, Chicago, Harvard)
- Reference library organization and deduplication
- Citation style conversion for journal requirements
- In-text citation formatting (author-date vs. numbered)
- Bibliography generation with multiple output formats
```

**Complementary use:** The citation-management skill enhances Part 3 by providing additional citation format options beyond Vancouver for journals requiring different styles.

---

## Part 3A: Citation Verification Protocol

### Overview

Citation verification ensures that every claim in the manuscript is supported by the cited source. This prevents academic misconduct and ensures scientific integrity.

### Verification Workflow

**STEP 1: Authentication**
```
1. notebooklm_setup_auth (if not authenticated)
2. notebooklm_get_health (verify auth)
```

**STEP 2: Source Query**
```
For each citation [X]:
1. Query NotebookLM: "What does [source] say about [claim]?"
2. If NotebookLM has data → Verify claim matches
3. If NotebookLM lacks data → Query PubMed
4. Record verification status
```

**STEP 3: Data Verification**
For each claim-citation pair:
- Extract specific data from source
- Compare with manuscript claim
- Flag any discrepancies

### Verification Checklist

| Check | Status |
|-------|--------|
| Source contains cited data | ☐ |
| Statistics match exactly | ☐ |
| Percentages verified | ☐ |
| Study name/trial correct | ☐ |
| PMID valid (if PubMed) | ☐ |
| Context appropriate | ☐ |

### Common Issues and Fixes

| Issue | Fix |
|-------|-----|
| Citation doesn't support claim | Find correct source or remove claim |
| Data misquoted | Use exact data from source |
| Wrong study cited | Swap to correct reference |
| PMID invalid | Search PubMed for correct ID |

### Verification Documentation

Create a verification log:
```
Manuscript Claim → Source Check → Data Match → Status
--------------------------------------------------------------
"MMR 67.7% at 48w" → [3] NEJM 2024 → "67.7%" → VERIFIED
"5-year OS 83%" → [1] NEJM 2006 → "83%" → VERIFIED
```

### Table Design Principles

Tables are essential for presenting complex data in medical manuscripts. Every table MUST include comprehensive abbreviations for clarity and journal compliance.

### Required Table Elements

**Every table MUST include:**
1. **Clear title** - Descriptive title explaining table content
2. **Abbreviations footnote** - Complete list of all abbreviations used
3. **Proper alignment** - Left-align text, right-align numbers
4. **Consistent decimals** - Same decimal places within columns
5. **Units in header** - Include units or specify in footnotes
6. **Source citation** - If data from published study, cite reference

### Abbreviation Requirements (MANDATORY)

**CRITICAL**: Every table MUST have an abbreviations footnote. Format:

```
Abbreviations: TKI, tyrosine kinase inhibitor; MMR, major molecular response; MR4, deep molecular response (BCR::ABL1 ≤0.01% IS); MR4.5, deep molecular response (BCR::ABL1 ≤0.0032% IS); EMR, early molecular response; IS, International Scale; CI, confidence interval; OR, odds ratio; HR, hazard ratio; RR, relative risk; AE, adverse event; SAE, serious adverse event; OS, overall survival; PFS, progression-free survival; EFS, event-free survival; CR, complete response; PR, partial response; NR, no response; NE, not evaluable; NA, not applicable.
```

### Standard Table Format

```
**Table 1. [Descriptive Title]**

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1a | Data 2a | Data 3a |
| Data 1b | Data 2b | Data 3b |

Abbreviation: [Complete list of all abbreviations in alphabetical order]

Source: [Reference number] or Data on file.
```

### Table Types in Medical Manuscripts

| Table Type | Purpose | Example |
|-----------|---------|---------|
| **Baseline characteristics** | Demographics, patient features | Age, sex, disease stage |
| **Treatment outcomes** | Efficacy endpoints | Response rates, survival |
| **Safety data** | Adverse events | AE frequencies, grades |
| **Comparative data** | Multiple arms/studies | Trial A vs Trial B |
| **Multivariable analysis** | Adjusted outcomes | Cox regression |
| **Mutation profiles** | Genetic associations | Mutation frequencies |

### Common Medical Abbreviations by Category

**Disease/Staging:**
- CML, chronic myeloid leukemia
- CP, chronic phase
- AP, accelerated phase
- BP, blast phase
- Ph+, Philadelphia chromosome-positive

**Treatment:**
- TKI, tyrosine kinase inhibitor
- Im, imatinib
- Das, dasatinib
- Nil, nilotinib
- Bos, bosutinib
- Asc, asciminib

**Response Criteria:**
- MMR, major molecular response (≤1% IS)
- MR4, deep molecular response (≤0.01% IS)
- MR4.5, deep molecular response (≤0.0032% IS)
- MR5, deep molecular response (≤0.001% IS)
- CCyR, complete cytogenetic response
- PCyR, partial cytogenetic response

**Endpoints:**
- OS, overall survival
- PFS, progression-free survival
- EFS, event-free survival
- TTR, time to response
- DoR, duration of response

**Statistics:**
- CI, confidence interval
- HR, hazard ratio
- OR, odds ratio
- RR, relative risk
- SD, standard deviation
- SE, standard error
- IQR, interquartile range
- P, p-value
- n, number
- N, total number

**Safety:**
- AE, adverse event
- SAE, serious adverse event
- TEAE, treatment-emergent adverse event
- DLT, dose-limiting toxicity
- MTD, maximum tolerated dose

### Table Checklist (BEFORE FINALIZING)

- [ ] Title clearly describes table content
- [ ] All abbreviations defined in footnote
- [ ] Units included in column headers
- [ ] Numbers formatted consistently
- [ ] Percentages include sample sizes (n/N)
- [ ] Statistical significance indicated (p-values, CI)
- [ ] Sources cited if applicable
- [ ] No vertical lines (AMA style)
- [ ] Horizontal lines only at top, bottom, and under headers
- [ ] Table number matches text reference

---

