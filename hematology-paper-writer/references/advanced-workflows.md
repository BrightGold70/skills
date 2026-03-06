# Advanced Workflow Reference

## Table of Contents
- [Part 9: Review Simulation Mode](#part-9-review-simulation-mode) — L1 (3-reviewer mock peer review)
- [Part 10: Farquhar 5-Sentence Abstract Method](#part-10-farquhar-5-sentence-abstract-method) — L105
- [Part 11: Enhanced Venue Templates](#part-11-enhanced-venue-templates-for-hematology-journals) — L147
- [Part 12: Plan-Outline Enhanced Workflow](#part-12-plan-outline-enhanced-workflow) — L185
- [Part 13: Prose Polish & Humanization](#part-13-prose-polish--humanization) — L330
- [Part 14: Style Register Options](#part-14-style-register-options) — L414
- [Part 15: Enhanced NotebookLM Features](#part-15-enhanced-notebooklm-features) — L487
- [Part 16: Manuscript Brainstorming Workflow](#part-16-manuscript-brainstorming-workflow) — L533
- [Part 17: Manuscript Writing Plans](#part-17-manuscript-writing-plans) — L639
- [Part 18: Reader Testing for Manuscripts](#part-18-reader-testing-for-manuscripts) — L724
- [Part 19: Goal-Oriented Workflow Recipes](#part-19-goal-oriented-workflow-recipes) — L793

---

## Part 9: Review Simulation Mode

### Overview
Simulate multi-reviewer feedback from top-tier hematology journals to identify weaknesses before submission.

### Reviewer Simulation Framework

**Operation**: Generate manuscript review simulating 2-3 reviewers with different perspectives.

**Reviewer Types:**
1. **Clinical Reviewer**: Focuses on clinical relevance, practical applications, and real-world applicability
2. **Basic Science Reviewer**: Evaluates mechanistic rigor, molecular pathways, and scientific novelty
3. **Statistical/Methodology Reviewer**: Assesses study design, statistical methods, and data analysis quality

### Review Output Format

Generate `review.md` with the following structure:

```markdown
# Manuscript Review Simulation

## Reviewer 1: Clinical Perspective
### Strengths
- [List clinical strengths]

### Concerns
- [List clinical concerns with page/section references]

### Suggestions
- [Specific suggestions for improving clinical impact]

---

## Reviewer 2: Basic Science Perspective  
### Strengths
- [List mechanistic/scientific strengths]

### Concerns
- [List mechanistic concerns]

### Suggestions
- [Suggestions for strengthening scientific rationale]

---

## Reviewer 3: Methodology Perspective
### Strengths
- [List methodological strengths]

### Concerns
- [List statistical/design concerns]

### Suggestions
- [Suggestions for improving rigor]

---

## Overall Assessment
### Major Issues (Must Address)
1. [Critical issue 1]
2. [Critical issue 2]

### Minor Issues (Recommended)
1. [Minor issue 1]
2. [Minor issue 2]

### Final Recommendation
[Accept / Minor Revision / Major Revision]
```

### Applying Reviewer Feedback

After receiving simulated reviews:
1. **Address ALL Major Issues** before submission
2. **Prioritize Minor Issues** based on space/time constraints
3. **Document Changes**: Keep track of how each reviewer concern was addressed
4. **Response Letter**: Prepare point-by-point responses to all reviewer comments

---

### Integrated Skill: peer-review

For formal manuscript peer review requiring structured evaluation frameworks, use the **`peer-review`** skill:

**When to invoke:**
- Journal submission preparation
- Pre-submission manuscript review
- Grant proposal review
- Abstract review for conferences

**Skill invocation:**
```
Use the peer-review skill for:
- Structured reviewer reports (EASE, COPE guidelines)
- Reviewer recommendation matrices (Accept/Revise/Reject)
- Constructive feedback frameworks
- Author response letter templates
- Review quality assessment
```

**Complementary use:** The peer-review skill enhances Part 9 Review Simulation Mode with formal peer review methodology and structured evaluation criteria.

---

## Part 10: Farquhar 5-Sentence Abstract Method

### The Narrative Principle
A hematology paper is not a collection of data, but a coherent clinical story backed by evidence.
- **One-sentence contribution**: Must summarize your core finding in one sentence
- **Three Pillars**:
  - **What**: Your novel clinical or scientific finding
  - **Why**: Evidence supporting the finding (trial data, mechanistic insights)
  - **So What**: Why clinicians/researchers should care (clinical implications)

### 5-Sentence Abstract Structure (Farquhar's Method)

For hematology manuscripts, apply this structure:

1. **Achievement** (Context + Main Finding)
   - "We report [main outcome] in [patient population] with [disease]"
   - Example: "We report the 5-year outcomes of first-line asciminib therapy in patients with chronic myeloid leukemia"

2. **Difficulty/Importance** (Clinical Challenge)
   - Why this problem matters and why it's challenging
   - Example: "Despite advances in tyrosine kinase inhibitors, a significant proportion of patients develop intolerance or resistance"

3. **Method** (Study Design + Key Intervention)
   - How you solved it (include study type, patient numbers, key methods)
   - Example: "In this multicenter, phase 3 trial, 400 patients were randomized to receive asciminib versus standard-of-care TKIs"

4. **Evidence** (Key Results with Data)
   - Your experimental/clinical support with specific numbers
   - Example: "At median follow-up of 58 months, major molecular response rates were 78% with asciminib versus 62% with standard TKIs (P<0.001)"

5. **Conclusion** (Most Significant Impact)
   - The most important clinical or scientific takeaway
   - Example: "These results establish asciminib as a new standard-of-care for frontline CML treatment"

### Hematology-Specific Tips

- **Include specific endpoints**: Mention MR4.5, PFS, OS, ORR with actual percentages
- **Cite pivotal trials**: Reference registration numbers (e.g., ASC4FIRST, NCT02081378)
- **State significance**: Connect findings to clinical practice guidelines (ELN, NCCN)

---

## Part 11: Enhanced Venue Templates for Hematology Journals

### Major Hematology Journals

| Journal | Impact Factor | Abstract Limit | Word Limit | Key Requirements |
|---------|---------------|----------------|------------|------------------|
| **Blood** | 25 | 200 words | ~5000 | Must include clinical trial registration, STRENGTHening the Reporting of OBservational studies in Epidemiology (STROBE) for observational |
| **Blood Advances** | 8 | 250 words | ~6000 | More flexible format, accepts brief reports, encourages data supplements |
| **Blood Research** | 3 | 250 words | ~6000 | Broad scope, accepts case reports, emphasis on Asian populations |
| **JCO** | 45 | 250 words | ~4000 | Oncology-focused, emphasizes clinical significance, requires CONSORT for trials |
| **BJH** | 8 | 200 words | ~5000 | British Society of Haematology affiliation valued, accepts review articles |
| **Leukemia** | 12 | 200 words | ~5000 | Molecular/mechanistic focus, requires mechanistic diagrams |
| **Haematologica** | 10 | 250 words | ~5000 | European Society of Haematology, accepts concise reports |

### Submission Format Requirements

**Blood Journal Specifics:**
- Title: Max 120 characters
- Abstract: Structured (Background, Methods, Results, Conclusions)
- References: Vancouver style, max 100
- Figures: Max 7 figures, upload separately
- Supplemental: Allowed, must be referenced in main text

**JCO Specifics:**
- Abstract: Must include Trial Information section
- Word limit strictly enforced (excess will be returned)
- Requires Disclosure Statement for all authors
- Clinical trial phase must be clearly stated

### Venue Conversion Guidelines

- **Blood → Blood Advances**: Add ~1000 words, expand discussion
- **JCO → Blood**: Reduce by 1000 words, increase clinical focus
- **Leukemia → Blood**: Add mechanistic details, ensure molecular focus
- **General → BJH**: Add UK/European context, consider British Haematology Society guidelines

---

## Part 12: Plan-Outline Enhanced Workflow

### Two-Stage Planning Method

Based on scientific-writing best practices, use this two-stage approach:

### Stage 1: Conceptual Outline

**Purpose**: Define the paper's core contribution and narrative structure

**Output**: 1-page outline with:
1. **One-sentence core contribution**: The single most important finding
2. **Story arc**: How the paper builds to that finding
3. **Key data points**: 3-5 critical numbers/results that support the conclusion
4. **Target venue**: Journal selection with word limit

**Template:**
```
Core Contribution: [One sentence describing the main finding]

Story Arc:
- Opening: [What clinical/problem gap motivates this study]
- Build: [What preliminary data or context supports the study]
- Peak: [What is the main result]
- Resolution: [What does this mean for clinical practice]

Key Data Points:
1. [Primary endpoint result]
2. [Secondary endpoint result]  
3. [Safety/safety profile result]

Target Venue: [Journal name] - [Word limit]
```

### Stage 2: Detailed IMRAD Structure

**Purpose**: Convert conceptual outline into detailed manuscript sections

**Output**: Detailed section-by-section outline with:
- Introduction: Problem statement, gap identification, study objective
- Methods: Study design, patient population, endpoints, statistical methods
- Results: Organized by endpoint (primary first), include all relevant subgroups
- Discussion: Interpret results, compare with literature, clinical implications, limitations

### Workflow Commands

```bash
# Stage 1: Create conceptual outline
hpw plan-outline "novel therapy for CML" --type clinical_trial --core-finding "asciminib shows superior MRR"

# Stage 2: Generate detailed structure
hpw create-outline draft_concept.md --expand-imrad --target-journal blood

# Full workflow: Plan to draft
hpw plan-to-draft "first-line asciminib CML" --journal blood --include-review
```

---

### Integrated Skill: scientific-writing

For advanced academic writing templates and structure guidance, use the **`scientific-writing`** skill:

**When to invoke:**
- Complex manuscript structures beyond standard IMRAD
- Grant proposal writing and specific aims development
- Thesis/dissertation chapters
- Review article organization

**Skill invocation:**
```
Use the scientific-writing skill for:
- IMRAD+ manuscript templates with extended sections
- Specific Aims page structure for grants
- Literature review frameworks (thematic, chronological, methodological)
- Discussion section argumentative structures
- Conclusion synthesis patterns
```

**Complementary use:** The scientific-writing skill enhances Part 12 Plan-Outline Workflow with advanced writing templates and structural frameworks for complex manuscripts.

---

## Tips for Best Results

1. **Specific Topics**: Use specific search terms ("asciminib CML" not "leukemia treatment")
2. **Time Periods**: Use `--time-period 5y` for recent literature reviews
3. **Web Search**: Enable `--web-search` for real-time evidence
4. **Verify Sources**: Always check citation-reference concordance
5. **DOCX Output**: Use `--docx` for submission-ready manuscripts
6. **Quality First**: Run `check-quality` before final submission
7. **Reference Verification**: Verify PubMed citations before submission
8. **Reporting Guidelines**: Use `--prisma-check`, `--consort-check`, `--care-check`
9. **Pre-submission Review**: Use Review Simulation Mode before final submission

---

## Tool Integration

Import modules directly:

```python
from tools.draft_generator import (
    PubMedSearcher,
    ManuscriptDrafter,
    EnhancedManuscriptDrafter,
    ResearchWorkflow,
    DocumentType,
    ReferenceStyle,
    SystematicReviewDrafter,
    ClinicalTrialDrafter,
    CaseReportDrafter,
    MetaAnalysisDrafter
)

from tools.quality_analyzer import ManuscriptQualityAnalyzer
from tools.pubmed_verifier import PubMedVerifier, ReferenceManager
from tools.citation_concordance import check_concordance
from tools.content_enhancer import ContentEnhancer, analyze_and_enhance
from tools.file_converter import FileConverter
from tools.hematology_guidelines import HematologyGuidelines
from tools.web_search_integration import WebSearchIntegration, ClinicalTrialsSearch
```

---

## Document Type Comparison Table

| Feature | Systematic Review | Meta-Analysis | Clinical Trial | Case Report |
|---------|------------------|---------------|----------------|-------------|
| **Guideline** | PRISMA 2020 | PRISMA 2020 | CONSORT 2010 | CARE 2013 |
| **Abstract Structure** | Yes | Yes | Yes | Yes |
| **Methods Section** | Extensive | Extensive | Detailed | N/A |
| **Flow Diagram** | PRISMA | PRISMA | CONSORT | N/A |
| **Sample Size** | N/A | Required | Required | N/A |
| **Randomization** | N/A | N/A | Required | N/A |
| **Timeline** | N/A | N/A | Required | Required |
| **Informed Consent** | N/A | N/A | Required | Required |
| **Registration** | PROSPERO | PROSPERO | ClinicalTrials.gov | Optional |
| **Heterogeneity** | Required | Required | N/A | N/A |
| **Forest Plots** | Optional | Required | N/A | N/A |
| **Adverse Events** | Summarized | Summarized | Detailed | Required |

---

## Part 13: Prose Polish & Humanization

### Overview

AI-generated scientific writing often exhibits detectable patterns that reduce credibility and readability. This section provides tools to polish manuscripts and remove common AI writing artifacts while maintaining academic rigor.

### Core Principle

> "LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases." — Wikipedia AI Writing Project

### 24 AI Writing Patterns to Remove

#### Content Patterns

| # | Pattern | Detection | Correction |
|---|---------|-----------|------------|
| 1 | **Significance inflation** | "marking a pivotal moment in the evolution of..." | State actual significance without hyperbole |
| 2 | **Notability name-dropping** | "cited in NYT, BBC, FT, and The Hindu" | Cite specific sources when relevant |
| 3 | **Superficial -ing analyses** | "symbolizing... reflecting... showcasing..." | Remove or expand with specific evidence |
| 4 | **Promotional language** | "nestled within the breathtaking region" | Use neutral, descriptive language |
| 5 | **Vague attributions** | "Experts believe it plays a crucial role" | Cite specific studies or data |
| 6 | **Formulaic challenges** | "Despite challenges... continues to thrive" | State specific challenges with evidence |

#### Language Patterns

| # | Pattern | Detection | Correction |
|---|---------|-----------|------------|
| 7 | **AI vocabulary** | "Additionally... testament... landscape... showcasing" | Use simpler alternatives: "also... remain common" |
| 8 | **Copula avoidance** | "serves as... features... boasts" | Use direct forms: "is... has" |
| 9 | **Negative parallelisms** | "It's not just X, it's Y" | State the point directly |
| 10 | **Rule of three overuse** | "innovation, inspiration, and insights" | Use natural number of items |
| 11 | **Synonym cycling** | "protagonist... main character... central figure" | Repeat the clearest term |
| 12 | **False ranges** | "from the Big Bang to dark matter" | List topics directly |

#### Style Patterns

| # | Pattern | Detection | Correction |
|---|---------|-----------|------------|
| 13 | **Em dash overuse** | "institutions—not the people—yet" | Use commas or periods |
| 14 | **Boldface overuse** | "**Performance:** Performance improved" | Convert to prose |
| 15 | **Inline-header lists** | "**Performance:** Performance improved" | Write as flowing paragraphs |
| 16 | **Title Case Headings** | "Strategic Negotiations And Partnerships" | Use sentence case |
| 17 | **Emojis** | "🚀 Key Insight:" | Remove entirely |
| 18 | **Curly quotes** | `said "the project"` | Use straight quotes |

#### Communication Patterns

| # | Pattern | Detection | Correction |
|---|---------|-----------|------------|
| 19 | **Chatbot artifacts** | "I hope this helps! Let me know if..." | Remove entirely |
| 20 | **Cutoff disclaimers** | "While details are limited..." | Find sources or remove |
| 21 | **Sycophantic tone** | "Great question! You're absolutely right!" | Respond directly |

#### Filler and Hedging

| # | Pattern | Detection | Correction |
|---|---------|-----------|------------|
| 22 | **Filler phrases** | "In order to", "Due to the fact that" | Use "To", "Because" |
| 23 | **Excessive hedging** | "could potentially possibly" | Use single "may" |
| 24 | **Generic conclusions** | "The future looks bright" | State specific plans or facts |

### Hematology-Specific Examples

**Before (AI-sounding):**
> Our study represents a groundbreaking advancement in the field of hematology, marking a pivotal moment in our understanding of hematologic malignancies. The transformative potential of these findings cannot be overstated, as they potentially could possibly revolutionize treatment paradigms.

**After (Humanized):**
> This study adds to the growing body of evidence on treatment approaches in hematologic malignancies. Our findings are consistent with previous reports and suggest that the intervention may warrant further investigation in larger trials.

### Prose Polish Checklist

Before finalizing any manuscript section, verify:

- [ ] No significance inflation (avoid "groundbreaking," "paradigm shift," "revolutionary")
- [ ] No vague attributions (cite specific studies)
- [ ] No em-dash overuse (limit to 2-3 per manuscript)
- [ ] No chatbot artifacts (remove "I hope this helps")
- [ ] No excessive hedging (use "may" not "could potentially possibly")
- [ ] No generic conclusions (state specific implications)
- [ ] Concrete data over abstractions
- [ ] Active voice preferred where appropriate

### Part 13b: Prose Enrichment — What to ADD

Part 13 above removes AI patterns. This section adds the positive markers of human-authored medical writing. See `references/prose-expansion.md` for full guidance; the six core techniques are:

**1. Historical anchoring** — Place every clinical development in a temporal frame
> BAD: "Imatinib is the standard first-line agent for CML."
> GOOD: "Since its regulatory approval in 2001, imatinib has remained the most widely used frontline agent for CML, transforming a once-fatal disease into a manageable chronic condition for the majority of patients."

**2. Mechanistic interpretation after every key result** — Explain WHY the number matters
> BAD: "Grade ≥3 neutropenia occurred in 20% of patients."
> GOOD: "Grade ≥3 neutropenia occurred in 20% of patients, a rate consistent with on-target myelosuppression from BCR::ABL1 kinase inhibition and comparable to that reported with bosutinib in the third-line setting [ref]."

**3. Comparative specificity** — Name authors, year, and exact value; never say "previous studies"
> BAD: "These results are consistent with previous studies."
> GOOD: "These findings are broadly consistent with those of Hochhaus et al. (2020), who reported MMR rates of 62.5% at 24 months with nilotinib in the ENESTnd trial [ref]."

**4. Clinical "so what" sentence at end of every results paragraph**
> BAD: Paragraph ends after the data.
> GOOD: "The clinical relevance of this finding is particularly salient for patients who prioritize treatment-free remission, as current ELN 2022 recommendations require sustained deep molecular response for at least 24 months before a discontinuation attempt [ref]."

**5. Limitation directionality** — State HOW each limitation affects results (over/underestimate)
> BAD: "A limitation is the lack of randomization."
> GOOD: "The absence of randomization is the principal methodological limitation and may have introduced selection bias, most likely inflating estimated response rates given the tendency to assign more treatment-experienced patients to novel agents in real-world practice."

**6. Paragraph-level bridging** — Last sentence of each paragraph links to the next
> "Whether these molecular response advantages translate into long-term outcomes relevant to patients, including treatment-free remission eligibility and progression to advanced phase, is the question addressed by the survival analyses described below."

### Prose Density Checklist (use alongside Polish Checklist)

- [ ] Every paragraph has minimum 5 sentences
- [ ] Every data point (p-value, %, CI) has a following elaboration sentence
- [ ] Every comparison names the specific prior study (author, year, value)
- [ ] Every results paragraph ends with a clinical "so what" sentence
- [ ] Every limitation states directional impact
- [ ] No section below word count floor (see `references/prose-expansion.md`)
- [ ] No bullet lists in objectives, PICO, criteria, or outcome sections
- [ ] Abstract has no placeholder sentences and is ≥220 words

---

## Part 14: Style Register Options

### Overview

Different contexts require different writing styles. This section provides guidance for adapting the manuscript voice to match the target audience and purpose.

### Available Style Registers

#### 1. Formal Academic (Default for Journals)

**Characteristics:**
- Passive voice acceptable for methods
- Complex sentences permitted
- Third-person preferred
- Minimal emotional language
- Full technical terminology

**Example:**
> The efficacy of the intervention was evaluated in a randomized controlled trial (N=250). Statistical analysis revealed a significant difference in the primary endpoint (p<0.001).

#### 2. Clinical Narrative (Case Discussions)

**Characteristics:**
- First-person acceptable for observations
- More conversational tone
- Clinical reasoning emphasized
- Patient-centered language
- Real-world applicability highlighted

**Example:**
> We observed a notable response in a 45-year-old patient with refractory disease. After three cycles, the patient achieved a partial response, which we attributed to the aggressive salvage regimen.

#### 3. Journalistic (Reviews, Press Releases)

**Characteristics:**
- Short paragraphs
- Impact-focused opening
- Minimal jargon
- Quotable statistics
- Broader context provided

**Example:**
> A new treatment approach shows promise for patients with advanced disease. In a study of 250 patients, nearly half responded to the therapy.

### Register Conversion Guide

| Element | Formal Academic | Clinical Narrative | Journalistic |
|---------|-----------------|-------------------|--------------|
| Opening | Background → Gap → Purpose | Case/example → Question | Impact → Key finding |
| Methods | Detailed, technical | Summarized, clinical relevance | Brief, numbers-focused |
| Results | Comprehensive statistics | Key clinical outcomes | Headline numbers |
| Discussion | Full context, limitations | Clinical implications | Future directions |
| Word count | Full limit | 80% of limit | 60% of limit |

### Choosing the Right Register

**Use Formal Academic when:**
- Target is a peer-reviewed journal
- Full methods reporting required
- Academic tenure/promotion purposes

**Use Clinical Narrative when:**
- Writing case reports or case series
- Medical education context
- Clinical decision-making focus

**Use Journalistic when:**
- Writing review articles
- Press releases or summaries
- Patient-facing materials

---

## Part 15: Enhanced NotebookLM Features

### Audio Generation for Manuscript Review

NotebookLM can generate audio overviews of your manuscript, serving as a powerful review tool.

**Use Cases:**
1. **Draft Review**: Listen to identify awkward phrasing or logical gaps
2. **Final Proofreading**: Hear errors that visual scanning misses
3. **Collaborator Feedback**: Share audio for quick review
4. **Patient/Public Summary**: Generate accessible summaries

**Available Audio Styles:**
- **Deep Dive**: Comprehensive coverage, slower pace
- **Quick Overview**: Concise summary, faster pace
- **Learning Guide**: Educational tone, explains terminology
- **Conversational**: Two-host discussion format

### Source Organization Best Practices

**Recommended Folder Structure:**
```
Research Project/
├── Literature Reviews/
├── Clinical Guidelines/
├── Trial Data/
├── Methodology/
└── Discussion Background/
```

**Source Naming Convention:**
- `[Year] [First Author] [Topic]`
- Example: `2023 Smith AML consolidation therapy`

### Generating Studio Content

NotebookLM Studio features available:
- **Audio Overview**: Two-host discussion of sources
- **Video Explainers**: Visual summaries
- **Infographics**: Single-topic visual summaries
- **Mind Maps**: Concept relationship diagrams
- **Flashcards**: Study cards from key concepts
- **Briefing Docs**: Concise summary documents

---

## Part 16: Manuscript Brainstorming Workflow

### Overview

Adapted from superpowers/brainstorming for academic manuscript development. This workflow ensures thorough planning before writing any manuscript section.

> **⚠️ MANDATORY WORKFLOW**: Do NOT start writing any manuscript section (Introduction, Methods, Results, Discussion) until you have completed the brainstorming phase and have a clear design document.

### Integration with HPW Core Workflow

This workflow integrates with the core HPW skills:
- **Part 1**: Use web search for initial literature discovery
- **Part 3/3A**: Verify all citations before including in design
- **Part 4**: Use source discovery for background research
- **Part 9**: Run review simulation after completing draft
- **Part 18**: Apply reader testing before submission

## When to Use

- Starting a new manuscript
- Planning a major revision
- Responding to reviewer comments
- Adding new analysis to existing manuscript

## 6-Step Brainstorming Process

### Step 1: Explore Project Context

Check existing work:
- Literature review status
- Available data
- Previous drafts or versions
- Target journal requirements

### Step 2: Ask Clarifying Questions

One at a time, understand:
- **Purpose**: What question does this manuscript answer?
- **Audience**: Who will read this? (clinicians, researchers, policymakers?)
- **Impact**: What is the single most important finding?
- **Constraints**: Word limits, timeline, required sections

### Step 3: Propose Approaches

Present 2-3 structural options:
- **Option A**: Clinical trial report approach
- **Option B**: Basic science mechanism approach  
- **Option C**: Meta-analysis/review approach

Include trade-offs and your recommendation.

### Step 4: Present Design

Present in sections scaled to complexity:
- **Title & Abstract Structure** (100 words)
- **Introduction Arc** (200 words) — background → gap → hypothesis
- **Methods Framework** (150 words) — design → participants → analysis
- **Results Hierarchy** (150 words) — primary → secondary → exploratory
- **Discussion Framework** (200 words) — interpretation → limitations → implications

Get user approval after each section.

### Step 5: Write Design Document

Save to: `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/[Project_Name]/docs/manuscripts/[YYYYMMDD_HHMMSS]-<topic>-design.md`

Template:
```markdown
# Manuscript Design: [Title]

## Core Contribution
[One sentence: What does this paper add?]

## Target Journal
[Journal name, impact factor, word limits]

## Structure
### Introduction
- Current state of field
- Knowledge gap
- Study objective

### Methods
- Study design
- Population
- Outcomes
- Analysis plan

### Results
- Primary outcome
- Secondary outcomes
- Subgroup analyses

### Discussion
- Interpretation
- Limitations
- Clinical implications
- Future directions
```

### Step 6: Transition to Writing

Invoke the writing-plans skill to create detailed section plans.

---

## Part 17: Manuscript Writing Plans

### Overview

Adapted from superpowers/writing-plans for manuscript section development. Create detailed, bite-sized tasks for writing each manuscript section.

## Plan Document Header

```markdown
# [Manuscript Section] Implementation Plan

**Goal:** [One sentence describing what this section accomplishes]

**Section Type:** [Introduction/Methods/Results/Discussion/Abstract]

**Word Target:** [X words]

---
```

## Task Structure for Manuscript Writing

````markdown
### Task N: [Specific Component]

**Word Target:** X words

**Step 1: Outline the component**

Write a brief outline:
- Point 1: [topic]
- Point 2: [topic]
- Point 3: [topic]

**Step 2: Write first draft**

Write the component focusing on:
- Clear topic sentence
- Supporting evidence
- Logical transitions

**Step 3: Revise for clarity**

Check:
- Passive voice appropriate for methods?
- Active voice for results?
- Jargon explained?
- Citations complete?

**Step 4: Word count check**

Target: X words
Current: Y words
Action: [expand/cut]

**Step 5: Save to manuscript**

Add to: `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/[Project_Name]/docs/drafts/[YYYYMMDD_HHMMSS]-{section}-draft.md`
````

## Bite-Sized Task Examples

For an Introduction section:
- Task 1: Write disease background (100 words)
- Task 2: Write current treatment landscape (100 words)
- Task 3: Identify knowledge gap (50 words)
- Task 4: State study objective (50 words)

For Methods section:
- Task 1: Study design description (75 words)
- Task 2: Participant selection criteria (75 words)
- Task 3: Outcome definitions (100 words)
- Task 4: Statistical analysis plan (100 words)

## Quality Checklist

Before marking task complete:
- [ ] Word count within target ±10%
- [ ] All citations present ([Author, Year] format)
- [ ] Technical terms defined
- [ ] Logical flow between paragraphs
- [ ] Consistent tense usage

---

## Part 18: Reader Testing for Manuscripts

### Overview

Adapted from anthropics/doc-coauthoring reader-testing phase. Test the manuscript with a fresh perspective to catch gaps before submission.

## When to Use

- After completing first draft
- Before submission to journal
- After major revisions
- When collaborators have conflicting feedback

## Testing Process

### Step 1: Predict Reader Questions

Generate 5-10 questions reviewers or readers might ask:

1. "Why was this specific population chosen?"
2. "How does this compare to previous studies?"
3. "What are the main limitations?"
4. "What is the clinical relevance?"
5. "How would this change clinical practice?"

### Step 2: Self-Testing

Answer each question by reading your manuscript:
- Can you find the answer easily?
- Is the answer clearly stated?
- Are there any contradictions?

### Step 3: Fresh Reader Testing

If available, have a colleague read and ask them:
- What was unclear?
- What questions did they have?
- What seemed redundant?
- What needed more explanation?

### Step 4: Gap Analysis

Document gaps found:
| Question | Found in Section | Answer Clarity |
|----------|-----------------|----------------|
| Why this population? | Methods | Clear |
| Comparison to prior work | Discussion | Missing |
| Limitations | Discussion | Brief |

### Step 5: Revision Planning

Create revision tasks:
1. Add comparison to [Study X] in Discussion
2. Expand limitations section
3. Clarify [specific point]

## Journal-Specific Testing

Different journals have different reviewers:

| Journal Type | Focus Areas |
|--------------|-------------|
| Clinical journals | Clinical implications, practical applications |
| Basic science | Mechanism, novelty, rigorous methods |
| Review articles | Comprehensiveness, synthesis |
| Case reports | Educational value, rarity |

---

## Part 19: Goal-Oriented Workflow Recipes

### Overview
This section outlines how to combine external skills sequentially to achieve specific manuscript types in Hematology.

### Recipe 1: The AI-Assisted Meta-Analysis
**Focus:** Systematic identification of literature, quantitative pooling, and structured manuscript drafting.
1. **Literature Discovery (`pubmed-integration` + `literature-review`)**: Execute PICO searches and export PMIDs for RCTs.
2. **Quantitative Synthesis (`clinical-statistics-analyzer`)**: Provide data to calculate I², perform fixed/random-effects, and prepare Forest Plot inputs (uses R scripts: `forest_plot.R`, `efficacy.R`).
3. **Manuscript Generation (HPW)**: Use Systematic Review Drafter (PRISMA template). Ensure prose-only results explicitly cite pooled data.
4. **Verification & Formatting (`citation-management`)**: Auto-format bibliography to target journal style.

### Recipe 2: The Clinical Trial / Cohort Report
**Focus:** Transforming raw clinical/observational data into a CONSORT-compliant manuscript.
1. **Exploratory Data Analysis (`clinical-statistics-analyzer`)**: Read dataset, run assumption checks, and calculate primary endpoints (Log-rank, T-tests, Cox regression — uses R scripts: `survival.R`, `efficacy.R`, `table1.R`).
2. **Trial Manuscript Drafting (HPW)**: Pass verified statistics to Clinical Trial Drafter adhering to CONSORT guidelines.
3. **Baseline Consistency Check (`notebooklm` / `pubmed-integration`)**: Query latest standards (e.g., ELN) to ensure survival statistics align with or are contextualized against benchmarks.

### Recipe 3: The Comprehensive Narrative Review
**Focus:** Synthesizing large volumes of recent literature into a high-depth, submission-quality narrative driven review.
**CRITICAL REQUIREMENT:** You must NEVER attempt to draft the entire manuscript in a single pass or rely exclusively on abstracts. A submission-quality review requires exact p-values, mechanistic context, and highly specific evidence synthesis without generalized fluff.

1. **The Deep Dive Search (`pubmed-database` / `pubmed-integration`)**: Query past 5 years of review articles/landmark studies on target topic.
2. **Mandatory Full-Text Integration (`notebooklm-assistant`)**: You MUST halt standard generation and strictly instruct the user to upload the full-text PDFs of the pivotal literature discovered in Step 1 into a specific NotebookLM notebook. *Do not proceed to drafting without deep context initialization.*
3. **Argument Structuring (`scientific-writing` + HPW)**: Build a structured outline mapping Farquhar methodology (Landscape, Gap, Innovations, Future) to standard academic headers (e.g., Introduction, Mechanisms of Action, Clinical Evidence Review, Discussion).
4. **Section-by-Section Sequencing (HPW + `notebooklm-assistant`)**: Draft exactly ONE section at a time. Query NotebookLM for deep, specific context bridging the current section's topic. Draft the section, ensure citations are aggressively placed, and wait for user approval before moving to the next section.
5. **The Prose Polish (HPW)**: Execute HPW's AI Pattern Removal guidelines across the unified manuscript.

---

## Workflow Integration Summary

This HPW skill is organized in three phases:

### Phase 1: Planning (Parts 1-8)
- Web search, reference formatting, verification, quality checks

### Phase 2: Writing (Parts 9-12)  
- Review simulation, abstract methods, venue selection, planning

### Phase 3: Refinement (Parts 13-18)
- Prose polish, style registers, NotebookLM, brainstorming, testing

**Recommended Workflow:**
1. Start with **Part 16** (Brainstorming) for new manuscripts
2. Use **Part 17** (Writing Plans) for section development
3. Apply **Part 13** (Prose Polish) before final review
4. Complete with **Part 18** (Reader Testing) before submission

---

## Integrated Skills Invocation Guide

The following specialized skills can be invoked to enhance specific HPW workflows:

### Skill Invocation Matrix

| Skill | When to Invoke | HPW Part | Use Case |
|-------|----------------|----------|----------|
| **literature-review** | Systematic reviews, meta-analyses | Part 1, Part 2 | PRISMA-compliant reviews, search strategy development, risk of bias assessment |
| **peer-review** | Pre-submission, formal reviews | Part 9 | Structured reviewer reports, COPE guidelines, author response letters |
| **citation-management** | Format conversion, large libraries | Part 3 | APA/AMA/Chicago conversion, bibliography generation |
| **scientific-writing** | Complex structures, grants | Part 12 | IMRAD+ templates, Specific Aims, literature review frameworks |
| **pubmed-integration** | Advanced PubMed queries | Part 1, Part 4 | MeSH terms, clinical queries, citation chaining |

### How to Invoke Integrated Skills

For specialized tasks beyond HPW's core functionality:

1. **Direct invocation**: State "Use the [skill-name] skill for [specific task]"
2. **Complementary workflow**: Use HPW for core manuscript writing + integrated skill for specialized functions
3. **Sequential process**: HPW for draft → integrated skill for enhancement → HPW for final polish

### Skill Selection Guide

- **Basic manuscript**: HPW alone sufficient
- **Systematic review**: HPW + literature-review + pubmed-integration
- **Grant proposal**: HPW + scientific-writing + citation-management
- **Journal submission**: HPW + peer-review + citation-management

---

*Part of OpenClaw Hematology Writing Suite*

