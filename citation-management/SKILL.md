---
name: citation-management
description: Academic citation formatting and reference management. Use when formatting bibliography, citations, or reference lists. Triggers: "citation", "reference", "bibliography", "APA", "Vancouver", "format".
allowed-tools: Grep, Read, Write
---

# Citation Management Skill

## Purpose

Format citations and references in various academic styles. Generate bibliography, in-text citations, and manage reference lists.

## When to Use

- Formatting reference list
- Converting citation styles
- Creating bibliography
- Following journal guidelines

---

## Common Citation Styles

### APA 7th Edition

**In-Text Citation:**
- Single author: (Smith, 2023)
- Two authors: (Smith & Jones, 2023)
- 3+ authors: (Smith et al., 2023)

**Reference Entry:**
```
Author, A. A., & Author, B. B. (Year). Title of article. 
Journal Name, Volume(Issue), pages. https://doi.org/xx.xxx
```

### Vancouver

**In-Text Citation:**
- Number in brackets [1]
- Number in superscript¹

**Reference Entry:**
```
Author AA, Author BB. Title of article. Journal Abbrev. Year;Volume(Issue):pages.
```

### Nature

**In-Text Citation:**
- Single author: (Smith 2023)
- Two authors: (Smith & Jones 2023)
- 3+ authors: (Smith et al. 2023)

**Reference Entry:**
```
Smith, A. A. Title of article. Journal Name Volume, pages (Year).
```

### AMA

**In-Text Citation:**
- Number in superscript¹ or (1)

**Reference Entry:**
```
Author AA, Author BB. Title of article. Journal Abbrev. Year;Volume(Issue):pages.
```

---

## Reference Types

### Journal Article
```
[APA] Author, A. A., & Author, B. B. (2023). Title. Journal, Volume(Issue), pages.
[Vancouver] Author AA, Author BB. Title. Journal. Year;Volume:pages.
```

### Book
```
[APA] Author, A. A. (2023). Title of book. Publisher.
[Vancouver] Author AA. Title of book. Publisher; Year.
```

### Book Chapter
```
[APA] Author, A. A. (2023). Chapter title. In B. B. Editor (Ed.), Book title (pp. pages). Publisher.
```

### Conference Paper
```
[APA] Author, A. A. (2023). Title. In Proceedings of Conference Name (pp. pages). Publisher.
```

### Preprint
```
[APA] Author, A. A. (2023). Title. Preprint. Repository. https://doi.org/xxx
```

### Website
```
[APA] Author, A. A. (2023, Month Day). Title. Site Name. URL
```

---

## DOI Formatting

**Correct DOI format:**
- https://doi.org/10.1000/xyz123
- DOI: 10.1000/xyz123

**NOT:**
- doi:10.1000/xyz123
- https://doi.org/https://doi.org/...

---

## PMID Format

- PubMed ID: 12345678
- URL: https://pubmed.ncbi.nlm.nih.gov/12345678/

---

## Auto-Format Examples

### Converting Vancouver to APA

**Original (Vancouver):**
```
1. Smith AA. Title. J Clin Oncol. 2023;41:100-110.
```

**APA:**
```
Smith, A. A. (2023). Title. Journal of Clinical Oncology, 41, 100-110.
```

### Converting DOI to URL

**DOI:**
```
10.1056/NEJMoa2024560
```

**URL:**
```
https://doi.org/10.1056/NEJMoa2024560
```

---

## Citation Tools

| Tool | Best For |
|------|----------|
| Zotero | Reference management |
| EndNote | Large libraries |
| Mendeley | PDF annotation |
| Paperpile | Google Docs |
| Citation Machine | Quick formatting |

---

## Quality Checks

| Check | What to Verify |
|-------|----------------|
| Authors | All authors listed? |
| Year | Correct publication year? |
| Volume/Issue | Complete citation? |
| Pages | Page range correct? |
| DOI | Valid DOI format? |
| Abbreviations | Journal abbreviations correct? |

---

## Output Templates

### Reference List (APA)
```
References

Author, A. A., & Author, B. B. (2023). Title of the article. Journal of Name, Volume(Issue), page-page. https://doi.org/xxxxx

Author, C. C. (2023). Title of the book. Publisher.
```

### Bibliography (Vancouver)
```
References

1. Author AA. Title. Journal. Year;Volume(Issue):pages.

2. Author BB. Title of book. Publisher; Year.
```

---

## Related Skills

- **literature-review**: Finding papers
- **peer-review**: Reviewing manuscripts
- **scientific-writing**: Paper structure
- **hematology-paper-writer**: Domain writing
