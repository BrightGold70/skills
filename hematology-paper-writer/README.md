# 🩸 Hematology Paper Writer

**Expert system for writing, analyzing, and improving hematology manuscripts with integrated literature search, quality analysis, and multi-format conversion.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Examples](#examples)
- [Supported Journals](#supported-journals)
- [Documentation](#documentation)

---

## Overview

The **Hematology Paper Writer** is a comprehensive skill for creating publication-ready manuscripts targeting top hematology journals.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Literature Search** | PubMed queries with time filtering and multi-strategy repeat searches |
| **Manuscript Drafting** | Generate structured drafts from research topics |
| **Quality Analysis** | Assess IMRaD compliance, clarity, methods, results |
| **Reference Verification** | Vancouver format parsing and PubMed validation |
| **Content Enhancement** | Gap identification and improvement suggestions |
| **File Conversion** | DOCX ↔ Markdown ↔ PDF ↔ PPTX |

---

## Features

### 1. Literature Search
- **PubMed Integration**: Search by topic, keywords, or DOI
- **Time Filtering**: all, 1y, 2y, 5y, 10y
- **Multi-Strategy Search**: Repeat searches with different queries
- **Batch Processing**: Retrieve up to 50+ articles
- **JSON Export**: Save results for later use

### 2. Manuscript Drafting
- **Structured Templates**: IMRaD format per journal
- **Auto-References**: Include relevant PubMed citations
- **Journal Compliance**: Follow target journal guidelines
- **DOCX Output**: Word-compatible manuscripts

### 3. Quality Analysis
- **Structure Assessment**: Validate IMRaD compliance
- **Clarity Scoring**: Evaluate writing quality
- **Completeness Check**: Ensure all sections present
- **Journal-Specific Standards**: Apply target requirements

### 4. Reference Verification
- **PubMed Integration**: Query by DOI, title, or PMID
- **Vancouver Format**: Parse numbered citations
- **Automated Validation**: Check DOI, authors, year, journal
- **Confidence Scoring**: Fuzzy matching with similarity scores

### 5. Content Enhancement
- **Gap Identification**: Find missing sections
- **Terminology Checking**: Proper hematology terminology
- **Statistical Validation**: Verify complete stats reporting
- **Actionable Suggestions**: Specific improvement recommendations

### 6. File Conversion
- **DOCX → Markdown**: Extract text and tables
- **Markdown → DOCX**: Full formatting preservation
- **PDF → Markdown**: Text extraction
- **PPTX → Markdown**: Slide content extraction

---

## Quick Start

```bash
# Navigate to skill directory
cd /Users/kimhawk/.openclaw/skills/hematology-paper-writer

# Activate virtual environment
source .venv/bin/activate

# Quick search
hpw search-pubmed "asciminib CML" --max-results 10

# Create draft
hpw create-draft "novel mutations myeloproliferative" --docx

# Check quality
hpw check-quality manuscript.md --journal blood

# Verify references
hpw verify-references manuscript.md
```

---

## Commands

### 🔍 search-pubmed
Search PubMed for relevant articles.

```bash
hpw search-pubmed "asciminib chronic myeloid leukemia" --max-results 50 --time-period 5y
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `topic` | Search query | Required |
| `--max-results` | Maximum results | 50 |
| `--time-period` | all, 1y, 2y, 5y, 10y | all |
| `--no-repeat` | Disable repeat search | False |
| `-o, --output` | Save to JSON | None |

---

### 📝 create-draft
Generate manuscript draft from research topic.

```bash
hpw create-draft "asciminib first-line CML" --journal blood_research --docx
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `topic` | Research topic | Required |
| `--journal` | Target journal | blood_research |
| `--study-type` | Type of study | observational |
| `--max-articles` | Articles to cite | 50 |
| `--docx` | Create DOCX | False |
| `--time-period` | all, 1y, 2y, 5y, 10y | all |
| `--no-search` | Skip literature | False |

---

### 🔬 research
Complete workflow: search, draft, quality check, verify.

```bash
hpw research "novel mutations myeloproliferative" --journal blood
```

---

### 📊 check-quality
Analyze manuscript quality.

```bash
hpw check-quality manuscript.md --journal blood
```

---

### ✅ verify-references
Verify citations against PubMed.

```bash
hpw verify-references manuscript.md --journal blood
```

---

### 🔗 check-concordance
Check citation-reference concordance in manuscript.

```bash
hpw check-concordance manuscript.docx --validate-format
```

Checks that:
- All citations in text have corresponding references
- All references are cited in text
- Reference format is valid (Vancouver style)

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `input` | Manuscript file | Required |
| `--validate-format` | Also check format | False |
| `--json` | Save results as JSON | None |

---

### ✍️ edit-manuscript
Enhance and improve content.

```bash
hpw edit-manuscript manuscript.md --journal blood --max-suggestions 10
```

---

### 📄 generate-report
Comprehensive manuscript report.

```bash
hpw generate-report manuscript.md --verify-references
```

---

### 🔄 convert
Convert between document formats.

```bash
# DOCX to Markdown
hpw convert manuscript.docx draft.md --format md

# Markdown to DOCX
hpw convert draft.md manuscript.docx --format docx --title "My Paper"
```

---

## Examples

### Example 1: Complete Manuscript Preparation

```bash
# 1. Research and draft
hpw research "novel mutations in myeloproliferative neoplasms" \
  --journal blood_research \
  --max-articles 30 \
  --time-period 5y \
  --docx

# 2. Check quality
hpw check-quality novel_mutations_mpn.md \
  --journal blood_research

# 3. Verify references
hpw verify-references novel_mutations_mpn.md

# 4. Enhance content
hpw edit-manuscript novel_mutations_mpn.md \
  --journal blood_research \
  --max-suggestions 15

# 5. Generate report
hpw generate-report novel_mutations_mpn.md \
  --journal blood_research \
  --verify-references \
  -o final_report.txt
```

### Example 2: Literature Review

```bash
# Search for recent articles
hpw search-pubmed "CAR-T cell therapy ALL" \
  --max-results 50 \
  --time-period 5y \
  -o cart_literature.json

# Create draft
hpw create-draft "CAR-T cell therapy outcomes" \
  --journal blood \
  --study-type review \
  --max-articles 30 \
  --docx
```

### Example 3: DOCX Workflow

```bash
# Convert existing DOCX to Markdown
hpw convert manuscript.docx draft.md --format md

# Enhance
hpw edit-manuscript draft.md --journal blood --apply

# Convert back to DOCX
hpw convert enhanced.md final.docx --format docx --title "Final Manuscript"
```

---

## Supported Journals

| Journal | Code | Abstract | Text | Reference Style |
|---------|------|----------|------|----------------|
| Blood Research | blood_research | 250 | 6000 | Vancouver |
| Blood | blood | 200 | 5000 | Vancouver |
| Blood Advances | blood_advances | 250 | 6000 | Vancouver |
| JCO | jco | 250 | 4000 | Numbered |
| BJH | bjh | 200 | 5000 | Vancouver |
| Leukemia | leukemia | 200 | 5000 | Vancouver |
| Haematologica | haematologica | 250 | 5000 | Vancouver |

### Journal Guidelines

- **Blood Research**: https://link.springer.com/journal/44313/submission-guidelines
- **Blood**: https://ashpublications.org/blood
- **Blood Advances**: https://ashpublications.org/bloodadvances
- **JCO**: https://ascopubs.org/journal/jco
- **BJH**: https://onlinelibrary.wiley.com/journal/14700505

---

## Python API

### Literature Search

```python
from tools.draft_generator import PubMedSearcher

searcher = PubMedSearcher()
articles = searcher.search_by_topic(
    "asciminib chronic myeloid leukemia",
    max_results=50,
    time_period="5y"
)

for art in articles:
    print(f"{art.title}")
    print(f"  PMID: {art.pmid}")
    print(f"  DOI: {art.doi}")
```

### Manuscript Drafting

```python
from tools.draft_generator import ManuscriptDrafter, Journal

drafter = ManuscriptDrafter(Journal.BLOOD_RESEARCH)
manuscript = drafter.create_draft(
    topic="asciminib as first-line CML therapy",
    articles=articles,
    study_type="clinical_trial"
)

with open("draft.md", "w") as f:
    f.write(manuscript)
```

### File Conversion

```python
from tools.file_converter import FileConverter, markdown_to_docx

# DOCX to Markdown
converter = FileConverter()
doc = converter.convert("manuscript.docx")
print(doc.text)

# Markdown to DOCX
markdown_to_docx(
    manuscript_text,
    "article.docx",
    title="My Manuscript"
)
```

### Quality Analysis

```python
from tools.quality_analyzer import ManuscriptQualityAnalyzer

analyzer = ManuscriptQualityAnalyzer("blood")
quality = analyzer.analyze_manuscript("manuscript.md")

print(f"Overall Score: {quality.overall_score:.1%}")
for cat_score in quality.category_scores.values():
    print(f"{cat_score.category.value}: {cat_score.score:.0%}")
```

---

## Installation

```bash
cd /Users/kimhawk/.openclaw/skills/hematology-paper-writer
source .venv/bin/activate

# Install dependencies (if needed)
pip install python-docx PyPDF2 python-pptx
```

---

## Files Structure

```
hematology-paper-writer/
├── SKILL.md                    # Skill definition
├── cli.py                     # Command-line interface
├── README.md                  # This file
├── requirements.txt           # Python dependencies
│
├── tools/
│   ├── __init__.py
│   ├── file_converter.py     # DOCX/PDF/PPTX conversion
│   ├── pubmed_verifier.py    # Reference verification
│   ├── quality_analyzer.py   # Quality assessment
│   ├── content_enhancer.py   # Content improvement
│   ├── draft_generator/
│   │   ├── __init__.py
│   │   ├── pubmed_searcher.py     # PubMed API
│   │   ├── manuscript_drafter.py    # Draft creation
│   │   └── research_workflow.py     # Complete workflow
│   └── requirements.txt
│
└── hematology-journal-specs/
    └── journal-specs.yaml    # Journal requirements
```

---

## Tips

1. **Specific Topics**: Use specific search terms ("asciminib CML" not "leukemia")
2. **Time Periods**: Use `--time-period 5y` for recent reviews
3. **DOCX Output**: Use `--docx` for Word-compatible files
4. **Quality First**: Run `check-quality` before submission
5. **Reference Verification**: Always verify before submission

---

## Version

- **v2.0.0** (2026-02-11): Added literature search, DOCX conversion, workflow automation

---

**Happy Writing! 🩸**
