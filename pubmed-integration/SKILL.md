---
name: pubmed-integration
description: PubMed database search and paper retrieval. Use when searching biomedical literature, finding studies, or retrieving abstracts. Triggers: "pubmed", "medline", "biomedical search", "ncbi", "find papers".
allowed-tools: websearch, webfetch, Grep
---

# PubMed Integration Skill

## Purpose

Search and retrieve biomedical literature from PubMed. Find relevant studies, extract abstracts, and gather citation information.

## When to Use

- Searching biomedical literature
- Finding clinical studies
- Retrieving abstracts
- Citation checking
- Systematic review searching

---

## PubMed Overview

**URL:** https://pubmed.ncbi.nlm.nih.gov/

**Coverage:**
- 35+ million citations
- Biomedical literature
- Clinical trials
- Reviews
- Preprints (some)

---

## Search Strategies

### Basic Search

**Single term:**
```
cancer
```

**Multiple terms:**
```
cancer treatment
```

### Advanced Search Operators

| Operator | Example | Description |
|---------|---------|-------------|
| AND | cancer AND treatment | Both terms |
| OR | cancer OR tumor | Either term |
| NOT | cancer NOT lung | Exclude term |
| [ti] | cancer[ti] | Title only |
| [ab] | cancer[ab] | Abstract only |
| [tiab] | cancer[tiab] | Title/abstract |
| [au] | smith[au] | Author |
| [dp] | 2023[dp] | Date published |

### Field Tags

| Tag | Field | Example |
|-----|-------|---------|
| [ti] | Title | HIV[ti] |
| [ab] | Abstract | HIV[ab] |
| [tiab] | Title/Abstract | HIV[tiab] |
| [au] | Author | Smith[au] |
| [dp] | Publication Date | 2023[dp] |
| [dp] | Date Range | 2020:2023[dp] |
| [pt] | Publication Type | review[pt] |
| [me] | MeSH Terms | hypertension[me] |
| [jw] | Journal | JAMA[jw] |

### Publication Types

| Type | Tag | Examples |
|------|-----|-----------|
| Review | [pt] | review[pt] |
| Clinical Trial | [pt] | clinical trial[pt] |
| Meta-Analysis | [pt] | meta-analysis[pt] |
| Randomized Controlled Trial | [pt] | "randomized controlled trial"[pt] |

---

## Search Examples

### Clinical Question (PICO)

**P (Population):** patients with hypertension
**I (Intervention):** ACE inhibitors
**C (Comparison):** placebo
**O (Outcome):** cardiovascular events

**Search:**
```
(hypertension[tiab] AND ("ACE inhibitor"[tiab] OR "angiotensin"[tiab])) AND (placebo[tiab] OR control[tiab]) AND (cardiovascular[tiab] AND (mortality[tiab] OR event[tiab]))
```

### Finding Systematic Reviews
```
systematic review[pt] AND diabetes[tiab]
```

### Finding Clinical Trials
```
clinical trial[pt] AND cancer[tiab]
```

### Recent Publications (Last 5 Years)
```
COVID-19[tiab] AND (2020:2025[dp])
```

---

## Retrieving Papers

### By PMID

**URL format:**
```
https://pubmed.ncbi.nlm.nih.gov/{PMID}/
```

**Example:**
```
https://pubmed.ncbi.nlm.nih.gov/34567890/
```

### By DOI

**URL format:**
```
https://doi.org/{DOI}
```

### Export Options

- **RIS** - Import to reference managers
- **BibTeX** - LaTeX compatible
- **CSV** - Spreadsheet
- **PMID List** - Bulk export

---

## Data Extraction

### Abstract Template
```markdown
## [Title]

**PMID:** [number]
**Authors:** [list]
**Journal:** [name] [Year];[Volume]([Issue]):[pages]
**DOI:** [doi]

### Background
[Abstract text]

### Methods
[Abstract text]

### Results
[Abstract text]

### Conclusions
[Abstract text]
```

---

## Quality Assessment

### Study Types (Publication Types)

| Type | Evidence Quality |
|------|-----------------|
| Meta-Analysis | Highest |
| Systematic Review | High |
| RCT | High |
| Cohort | Moderate |
| Case-Control | Moderate |
| Case Series | Low |
| Case Report | Lowest |

### Filter by Evidence

**To find high-quality evidence:**
```
"systematic review"[pt] OR "meta-analysis"[pt] OR "randomized controlled trial"[pt]
```

---

## Common Searches

### Diagnostic Test
```
sensitivity AND specificity AND test[tiab]
```

### Prognosis
```
prognosis[tiab] AND survival[tiab]
```

### Therapy
```
therapy[tiab] AND (randomized[tiab] OR controlled[tiab])
```

### Etiology
```
etiology[tiab] OR cause[tiab]
```

---

## Tips & Tricks

1. **Start broad** then refine
2. **Use MeSH terms** for systematic searches
3. **Check "Similar articles"** for related papers
4. **Set up alerts** for new publications
5. **Use filters** (date, species, language)

---

## Output Format Example

```markdown
## Search Results: [Query]

**Results:** 1,234 papers found
**Date:** [current date]
**Database:** PubMed

### Top 5 Relevant Papers

| # | PMID | Title | Authors | Year | Journal |
|---|------|-------|---------|------|---------|
| 1 | 34567890 | Title here | Smith et al. | 2023 | NEJM |
| 2 | 34567889 | Title here | Jones et al. | 2022 | Lancet |

### Key Studies
#### Study 1: [Title]
- PMID: 34567890
- Design: RCT
- Sample: N=500
- Finding: 30% reduction in...
```

---

## Related Skills

- **literature-review**: Systematic review process
- **citation-management**: Reference formatting
- **peer-review**: Manuscript evaluation
- **hematology-paper-writer**: Domain writing
