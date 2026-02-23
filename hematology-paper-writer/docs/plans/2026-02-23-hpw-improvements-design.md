# Manuscript Design: Hematology Paper Writer (HPW) V2 Integration Recipes

## Core Contribution
The HPW skill is enhanced with distinct, goal-oriented "recipes" that weave powerful open-source data and literature processing tools directly into its existing manuscript generation workflow.

## Feature Overview

We will introduce a new section inside the `hematology-paper-writer` SKILL.md called **"Part 19: Goal-Oriented Workflow Recipes."** This section outlines exactly how to combine external skills sequentially to achieve specific manuscript types in Hematology.

---

## Recipe 1: The AI-Assisted Meta-Analysis

**Focus:** Systematic identification of literature, quantitative pooling, and structured manuscript drafting.

1. **Phase 1: Literature Discovery (`pubmed-integration` + `literature-review`)**
   - Execute an advanced MeSH query or PICO query using `pubmed-integration`.
   - Filter for Randomized Controlled Trials and export PMIDs.
2. **Phase 2: Quantitative Synthesis (`statistical-analysis`)**
   - Provide the extracted data from the PMIDs to the agent.
   - Invoke `statistical-analysis` to perform fixed/random-effects calculations, heterogeneity tests (I²), and prepare Forest Plot inputs.
3. **Phase 3: Manuscript Generation (`hematology-paper-writer`)**
   - Use HPW's Systematic Review Drafter combining the PRISMA checklist template.
   - Mandate prose-only formatting, ensuring all pooled results from Phase 2 are cited in the text narrative.
4. **Phase 4: Verification and Formatting (`citation-management`)**
   - Auto-format the final bibliography converting PMIDs to strict Vancouver or APA style based on target journal.

---

## Recipe 2: The Clinical Trial / Cohort Report

**Focus:** Transforming raw clinical/observational data into a CONSORT-compliant manuscript.

1. **Phase 1: Exploratory & Confirmatory Data Analysis (`statistical-analysis`)**
   - Read the study dataset (e.g., CSV/Excel) of patient characteristics and outcomes.
   - Run assumption checks (normality, variance) via `statistical-analysis`.
   - Calculate primary endpoints (e.g., Log-rank test for Survival, T-tests, Cox regression for Hazard Ratios).
2. **Phase 2: Trial Manuscript Drafting (`hematology-paper-writer`)**
   - Pass the verified statistics to HPW's Clinical Trial Drafter.
   - Ensure the structure strictly adheres to the CONSORT guidelines (Methods -> Statistical Analysis subsection, Participant flow).
3. **Phase 3: Baseline Consistency Check (`notebooklm` / `pubmed-integration`)**
   - Query NotebookLM or PubMed to check if the survival statistics reported deviate significantly from the latest hematological standards (e.g., ELN 2025).

---

## Recipe 3: The Comprehensive Narrative Review

**Focus:** Synthesizing large volumes of recent literature into an authoritative, narrative-driven review article.

1. **Phase 1: The Deep Dive Search (`pubmed-database` / `pubmed-integration`)**
   - Start by querying PubMed using the `pubmed-integration` skill for the past 5 years of review articles and landmark studies on the target topic (e.g., "novel mutations in myeloproliferative neoplasms").
   - Extract the abstracts and compile the foundational knowledge base.
2. **Phase 2: Argument Structuring (`scientific-writing` + HPW)**
   - Utilize HPW's Plan-Outline workflow (Farquhar method) combined with the thematic synthesis frameworks from `scientific-writing` to build a coherent narrative arc (Current landscape -> Knowledge Gap -> Recent Innovations -> Future Directions).
3. **Phase 3: Deep Drafting (`hematology-paper-writer` + `citation-management`)**
   - Draft the manuscript paragraph by paragraph.
   - **Critical Citation Density:** Every claim synthesized from Phase 1 must be aggressively cited to prevent plagiarism concerns, using `citation-management` to track the cascading list of Vancouver-style references.
4. **Phase 4: The Prose Polish**
   - Execute HPW's AI Pattern Removal guidelines to ensure the review reads professionally without "superficial -ing analyses" or "significance inflation."
