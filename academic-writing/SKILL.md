---
name: academic-writing
description: Comprehensive academic paper writing skill supporting plan-outline, write, review, switch-venue, and switch-language modes. Integrates AI pattern removal, hallucination-proof citation workflow, top-tier conference writing philosophy, and stable diagram generation.
---

# Academic Writing

A comprehensive skill for academic paper writing with structured workflows and quality assurance.

## Core Workflow Modes

### 1. `plan-outline` (Outline Planning)
Generate paper outline and content structure.
- **Operation**: Based on scientific-writing two-stage planning method, determine IMRAD structure.
- **Narrative Principle**: Ensure paper has clear one-sentence core contribution and build story around it.

### 2. `write` (Section Writing & Integration)
Support in-depth writing or revision of specified sections, integrating multiple chapters for consistency.
- **Proactive Delivery**: Deliver complete drafts proactively when context is clear, rather than asking repeatedly.
- **Auto-adaptation**: Automatically adjust content detail based on current venue (e.g., NeurIPS 9 pages, ICML 8 pages).
- **AI Pattern Removal**: After writing, MUST call humanizer (English) or humanizer-zh (Chinese) for language optimization.

### 3. `review` (Multi-Reviewer Review)
Simulate multi-reviewer mode of top-tier journals/conferences.
- **Operation**: Simulate 2-3 reviewers with different perspectives for rigorous review.
- **Output**: Generate review.md file.

### 4. `switch-venue` (Venue Switching)
Convert between different conference or journal formats.
- **Operation**: Adjust page limits, section structure (e.g., whether Broader Impact or Limitations needed), reference format.
- **Reference**: references/venue_templates.md

### 5. `switch-language` (Language Switching)
Switch between Chinese and English writing environments.
- **Chinese Mode**: Follow chinese-copywriting-guidelines (Chinese-English spacing, full-width punctuation).
- **English Mode**: Follow ml-paper-writing concise principles, avoid over-decoration.

## ⚠️ Strictly Prohibit Hallucination Citations
**Strictly forbidden to generate BibTeX from memory.** All citations must go through API verification process in references/citation_workflow.md. If unable to verify, must mark as [CITATION NEEDED].

## Enhanced Features

### Diagrams & Typesetting
- **Matplotlib**: Diagram labels must be consistent with current language (default English).
- **Typesetting**: Strictly handle Chinese-English mixed spacing.

## Domain References
- **CS/ML**: references/cs_ml_guide.md (includes Farquhar 5-sentence abstract method).
- **General Science**: references/general_science_guide.md.
- **Citation Workflow**: references/citation_workflow.md.
- **Venue Templates**: references/venue_templates.md.
