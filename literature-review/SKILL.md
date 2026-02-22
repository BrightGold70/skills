---
name: literature-review
description: Systematic literature review with multi-database search. Use for finding, screening, and synthesizing academic papers. Triggers: "literature review", "search papers", "find studies", "systematic review", "meta-analysis".
allowed-tools: websearch, webfetch, Grep, Read
---

# Literature Review Skill

## Purpose

Conduct comprehensive literature reviews using multiple academic databases. Find, screen, and synthesize relevant papers.

## When to Use

- Writing literature review section
- Systematic review or meta-analysis
- Finding related work
- Research background
- Paper comparison

---

## Workflow

### Step 1: Define Search Strategy

1. **Identify key concepts**
   - Extract main keywords
   - Create synonyms
   - Define inclusion/exclusion

2. **Select databases**
   - PubMed (biomedical)
   - Semantic Scholar (general)
   - arXiv (preprints)
   - Google Scholar (broad)
   - Web of Science (citations)

### Step 2: Search

**Search Query Structure:**
```
(topic AND keywords) NOT exclusion
```

**Example:**
```
(cancer AND immunotherapy) NOT animal
```

### Step 3: Screen Results

1. **Title/Abstract Screening**
   - Relevance score (1-5)
   - Include/Exclude decision
   - Notes

2. **Full Text Evaluation**
   - Methodology assessment
   - Data availability
   - Quality score

### Step 4: Extract & Synthesize

**Data Extraction:**
- Author, Year
- Research question
- Methods
- Key findings
- Limitations

**Synthesis:**
- Thematic grouping
- Gap identification
- Consensus/controversy

---

## Database Access

### PubMed Search
- Use Medical Subject Headings (MeSH)
- Filter by: date, species, article type
- Export citations

### Semantic Scholar
- Citation counts
- Paper influential score
- Related papers
- TL;DR summaries

### arXiv
- Preprint availability
- Version history
- Category filters

---

## Output Format

```markdown
## Literature Review: [Topic]

### Search Strategy
- Keywords: [list]
- Databases: [list]
- Date Range: [range]
- Results: [count]

### Included Studies

| Author | Year | Title | Method | Key Finding |
|--------|------|-------|--------|-------------|
| Smith  | 2023 | ...   | RCT    | Significant |

### Excluded Studies
| Author | Reason |
|--------|--------|
| Jones  | Wrong population |

### Synthesis
#### Theme 1: [Theme Name]
- Finding 1: [citation]
- Finding 2: [citation]

### Gaps Identified
1. [Gap 1]
2. [Gap 2]

### Quality Assessment
- High quality: N
- Medium: N
- Low: N
```

---

## Quality Indicators

**High Quality Paper:**
- Clear research question
- Appropriate methodology
- Adequate sample size
- Reproducible
- Peer-reviewed

**Red Flags:**
- No control group
- Small sample (n<30)
- No statistical analysis
- Conflicts of interest undisclosed
- Predatory journal

---

## Related Skills

- **pubmed-integration**: Direct PubMed search
- **citation-management**: Reference formatting
- **scientific-writing**: Paper structure
- **hematology-paper-writer**: Domain-specific writing
