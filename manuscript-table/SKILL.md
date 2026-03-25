---
name: manuscript-table
description: Expert guidance for designing and drafting high-impact medical manuscript tables targeting NEJM, JAMA, The Lancet, and The BMJ. Use when creating baseline characteristics tables, outcome tables, safety/AE tables, PRISMA/CONSORT/STROBE/STARD systematic review tables, GRADE Summary of Findings, Risk of Bias 2.0, Phase 1/2/3 clinical trial tables (DLTs, PK/PD, CONSORT 2025), hematology-specific tables (AML/MDS/CML response criteria, BCR-ABL mutation tables, MRD endpoints, AOE tables), or converting narrative results into structured evidence displays.
---

# manuscript-table

## Core Rules (Always Apply)

1. **Standalone**: Title + table + footnotes must convey the full message without the text. Use PICO in titles (Population, Intervention, Comparator, Outcomes).
2. **No redundancy**: Tables must not repeat data already in text or figures.
3. **Bookshelf layout**: 3 horizontal lines only (top, under header, bottom). No vertical lines.
4. **Footnotes**: Alphabetical (a, b, c). Define all abbreviations, symbols, and statistical tests.
5. **Software**: Microsoft Word native table function — no images/screenshots, no manual spacing.

## Quick Reference: Journal-Specific Rules

| Rule | NEJM | JAMA | The Lancet | The BMJ |
| :--- | :--- | :--- | :--- | :--- |
| P-value format | ≥0.01→2dp, 0.01–0.001→3dp, <0.001→"P<0.001" | Exact values | Absolute values | Standardized |
| Units | Headers or leftmost col | Explicitly in headers | Defined per variable | SI units required |
| Orientation | Strictly portrait | Portrait preferred | Portrait/Landscape | Portrait, max 2 pages |
| Abbreviations | Footnotes (alphabetical) | Footnotes | Legend | Sparingly, defined |

> **Full journal rules**: See [references/journal-guidelines.md](references/journal-guidelines.md)

## Table Type Selection

| Study Type | Key Tables Required | Reference |
| :--- | :--- | :--- |
| Phase 1 trial | Dose-escalation + DLTs, PK parameters | [references/clinical-trials.md](references/clinical-trials.md) |
| Phase 2 trial | Efficacy signal (ORR/PFS), dose-ranging | [references/clinical-trials.md](references/clinical-trials.md) |
| Phase 3 / CONSORT 2025 | Table 1 (baseline), outcomes, safety/AEs | [references/clinical-trials.md](references/clinical-trials.md) |
| Systematic review | Characteristics of included studies, RoB 2.0 | [references/systematic-reviews.md](references/systematic-reviews.md) |
| Meta-analysis | GRADE SoF, effect measures (RR/OR/HR/SMD) | [references/systematic-reviews.md](references/systematic-reviews.md) |
| Narrative/clinical review | Study characteristics, inclusion/exclusion criteria | [references/systematic-reviews.md](references/systematic-reviews.md) |
| Observational (STROBE) | Baseline table with P-values, adjusted vs. crude | [references/reporting-guidelines.md](references/reporting-guidelines.md) |
| Diagnostic accuracy (STARD) | Sensitivity/specificity, ROC, LR | [references/reporting-guidelines.md](references/reporting-guidelines.md) |
| Genetic association (STREGA) | SNP table, MAF, HWE, GWAS threshold | [references/reporting-guidelines.md](references/reporting-guidelines.md) |
| AML / MDS trial | IWG response criteria (CR/CRi/CRp/HI), MRD | [references/hematology.md](references/hematology.md) |
| CML trial | BCR-ABL response (CCyR/MMR/MR4), mutation IC50 | [references/hematology.md](references/hematology.md) |
| Hematologic AEs | Neutropenia/thrombocytopenia grades, AOE sub-table | [references/hematology.md](references/hematology.md) |

> **Ready-to-use templates**: See [references/templates.md](references/templates.md)
> **Reporting guideline compliance** (CONSORT/STROBE/STARD/TIDieR): See [references/reporting-guidelines.md](references/reporting-guidelines.md)

## Statistical Reporting Hierarchy

- **P > 0.01** → two decimal places (P=0.54)
- **0.001 ≤ P ≤ 0.01** → three decimal places (P=0.006)
- **P < 0.001** → fixed (P<0.001)
- Label adjusted P-values; distinguish pre-specified vs post-hoc analyses.
- Odds ratios and hazard ratios: report to two significant digits.

## Workflow

1. **Select table type** from the table above; load the relevant reference file.
2. **Draft title** using PICO framework — be specific about population, timeframe, and outcome.
3. **Structure columns** — place primary outcome first; include N, effect estimate, 95% CI, P-value.
4. **Write footnotes** — define all symbols (*, †, ‡) and abbreviations alphabetically.
5. **Verify standalone test** — can a reader understand the key finding without reading the manuscript?
