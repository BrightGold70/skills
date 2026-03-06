# Design: HPW WHO/ICC Classification References Integration

**Feature**: `hpw-who-icc-references-integration`
**Phase**: Design
**Created**: 2026-03-06
**Plan**: `docs/01-plan/features/hpw-who-icc-references-integration.plan.md`

---

## Implementation Overview

Two text edits to two files. No new files, no code changes.

| # | File | Change |
|---|------|--------|
| 1 | `hematology-paper-writer/SKILL.md` | Append 2 rows to Reference Files table |
| 2 | `hematology-paper-writer/references/scientific-skills.md` | Append new section after the intro block |

---

## Edit 1: `hematology-paper-writer/SKILL.md`

### Location

The Reference Files table currently ends with this row (line ~101):

```
| `references/scientific-skills.md` | Using the 13 scientific skill classes (`HypothesisGenerator`, `StatisticalAnalyst`, etc.) |
```

### Exact text to insert AFTER that row

```markdown
| `references/2022_WHO_MyeloidClassificationDefinition.md` | WHO 2022 diagnostic criteria for all myeloid entities (AML blast thresholds, MDS, MPN, CML, CHIP). Load when writing disease classification or definition sections, verifying entity names, blast percentages, or molecular criteria per WHO 2022. |
| `references/2022_ICC_MyeloidClassificationDefinition.md` | ICC 2022 diagnostic criteria. Load alongside the WHO file when documenting WHO vs ICC divergence: CML accelerated phase (ICC-only), AML with NPM1 blast threshold (any% WHO vs ≥10% ICC), or MDS naming ("Neoplasms" WHO vs "Syndromes" ICC). |
```

### Result: full Reference Files table after edit

```markdown
## Reference Files

Load these on demand based on the task:

| File | Load When |
|------|-----------|
| `references/writing-standards.md` | Drafting manuscripts; web search integration; document type templates (systematic review, RCT, case report, etc.) |
| `references/citations.md` | Formatting references; verifying citations; Vancouver style details |
| `references/quality-workflow.md` | QA checklist; source discovery; end-to-end workflow examples |
| `references/advanced-workflows.md` | Review simulation; Farquhar abstract method; brainstorming; prose polish; reader testing; goal-oriented recipes |
| `references/scientific-skills.md` | Using the 13 scientific skill classes (`HypothesisGenerator`, `StatisticalAnalyst`, etc.) |
| `references/2022_WHO_MyeloidClassificationDefinition.md` | WHO 2022 diagnostic criteria for all myeloid entities (AML blast thresholds, MDS, MPN, CML, CHIP). Load when writing disease classification or definition sections, verifying entity names, blast percentages, or molecular criteria per WHO 2022. |
| `references/2022_ICC_MyeloidClassificationDefinition.md` | ICC 2022 diagnostic criteria. Load alongside the WHO file when documenting WHO vs ICC divergence: CML accelerated phase (ICC-only), AML with NPM1 blast threshold (any% WHO vs ≥10% ICC), or MDS naming ("Neoplasms" WHO vs "Syndromes" ICC). |
```

---

## Edit 2: `hematology-paper-writer/references/scientific-skills.md`

### Location

Current file structure (59 lines):

```
# Scientific Skills Integration Reference

13 cross-phase skill classes in `tools/skills/`. Load this file when using `hpw hypothesis`, `hpw brainstorm`, `hpw visualize-figure`, `hpw grant-draft`, or any other scientific skill CLI command.

---

## Part 20: Scientific Skills Integration
...
```

### Exact text to insert BETWEEN the `---` separator and `## Part 20`

```markdown
## Classification Reference Files

The `ClassificationValidator` skill class derives its logic from two authoritative sources.
Load these files when:
- Extending or debugging the validator for new entities
- Verifying that `ClassificationValidator` output matches official criteria
- Writing manuscript sections that require precise WHO 2022 **or** ICC 2022 diagnostic language

| File | System | Key Content |
|------|--------|-------------|
| `../2022_WHO_MyeloidClassificationDefinition.md` | WHO 2022 | AML (any blast% for gene-defined entities), MDS as "Neoplasms", no CML Accelerated Phase |
| `../2022_ICC_MyeloidClassificationDefinition.md` | ICC 2022 | AML NPM1 requires ≥10% blasts, CML AP defined (10–19% blasts or ACA), MDS as "Syndromes" |

**Load both files when any of these divergences apply to the manuscript:**

| Divergence | WHO 2022 | ICC 2022 |
|------------|----------|----------|
| CML Accelerated Phase | Not recognized | 10–19% blasts or additional clonal cytogenetic abnormality (ACA) in Ph+ cells |
| AML with NPM1 mutation | Any blast % | ≥10% blasts in BM/PB |
| MDS category name | "Myelodysplastic Neoplasms" | "Myelodysplastic Syndromes" |
| Clonal Haematopoiesis | CHIP/CCUS defined | Not a top-level ICC category |

---

```

### Result: beginning of scientific-skills.md after edit

```markdown
# Scientific Skills Integration Reference

13 cross-phase skill classes in `tools/skills/`. Load this file when using `hpw hypothesis`, `hpw brainstorm`, `hpw visualize-figure`, `hpw grant-draft`, or any other scientific skill CLI command.

---

## Classification Reference Files

The `ClassificationValidator` skill class derives its logic from two authoritative sources.
...divergence table...

---

## Part 20: Scientific Skills Integration
...
```

---

## Acceptance Criteria

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 1 | Both WHO/ICC rows appear in SKILL.md Reference Files table | `grep "WHO_Myeloid" SKILL.md` |
| 2 | scientific-skills.md has Classification Reference Files section | `grep "Classification Reference" references/scientific-skills.md` |
| 3 | Divergence table present in scientific-skills.md | `grep "CML Accelerated" references/scientific-skills.md` |
| 4 | SKILL.md line count ≤ 110 (minimal bloat) | `wc -l SKILL.md` |
| 5 | scientific-skills.md line count ≤ 95 (was 59 + ~30 new lines) | `wc -l references/scientific-skills.md` |

---

## Implementation Order

1. Edit `SKILL.md` — append 2 rows (1 Edit call)
2. Edit `references/scientific-skills.md` — insert section before `## Part 20` (1 Edit call)
3. Verify with grep checks above
