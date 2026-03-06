# Plan: HPW WHO/ICC Classification References Integration

**Feature**: `hpw-who-icc-references-integration`
**Phase**: Plan
**Created**: 2026-03-06

---

## Overview

Two curated reference files already exist in the HPW skill's `references/` directory but are not wired into the skill:

- `references/2022_WHO_MyeloidClassificationDefinition.md` — 113 lines, WHO 2022 full myeloid classification with diagnostic criteria
- `references/2022_ICC_MyeloidClassificationDefinition.md` — 96 lines, ICC 2022 full myeloid classification with diagnostic criteria

These files serve as ground truth for myeloid disease classification, preventing hallucinated blast thresholds, molecular criteria, and entity names. They also encode clinically meaningful divergences between the two systems (e.g., CML accelerated phase, NPM1 blast thresholds, MDS naming).

## Problem Statement

Currently Claude cannot discover these files because:
1. They are **not referenced in `SKILL.md`** — no "load when" trigger defined
2. They are **not linked from `references/scientific-skills.md`** — disconnected from the `ClassificationValidator` they underpin

Without explicit references, Claude will either ignore the files entirely or hallucinate classification criteria instead of loading authoritative content.

## Goals

### Path 1: Add to SKILL.md Reference Files table
Add both files to the existing "Reference Files" table in `SKILL.md` with precise trigger conditions.

**Acceptance Criteria**:
- Both files appear in the Reference Files table
- Trigger condition is specific enough to load them only when classification/nomenclature context is needed (avoid unnecessary loading for e.g. pure literature search tasks)
- Trigger mentions: AML/MDS/MPN classification, WHO vs ICC divergence, blast thresholds, diagnostic criteria

### Path 2: Link from references/scientific-skills.md
Add a section in `scientific-skills.md` that declares these files as the authoritative source for the `ClassificationValidator` skill class.

**Acceptance Criteria**:
- `scientific-skills.md` references both files with clear context
- Explains the WHO vs ICC divergence cases where both files should be loaded together
- Notes that the `ClassificationValidator` programmatic logic is derived from these criteria

## Non-Goals

- Do NOT modify the content of the WHO/ICC files themselves
- Do NOT move them to CSA (ELN 2022 risk ≠ WHO/ICC classification)
- Do NOT merge them into a single file (independent loading is preferable)
- Do NOT add divergence comparison tables to SKILL.md (too detailed; belongs in scientific-skills.md)

## Key WHO vs ICC Divergence Cases

These divergences are the main reason both files are needed:

| Entity | WHO 2022 | ICC 2022 | Clinical Impact |
|--------|----------|----------|-----------------|
| CML Accelerated Phase | **Not recognized** | 10–19% blasts or ACA in Ph+ cells | Staging differences in CML manuscripts |
| AML with NPM1 mutation | Any blast % | ≥10% blasts | Changes AML diagnosis threshold |
| AML with biallelic TP53 | ≥10% blasts | ≥10% blasts | Same threshold, different naming |
| MDS naming | "Myelodysplastic **Neoplasms**" | "Myelodysplastic **Syndromes**" | Nomenclature in abstracts/titles |
| AML blast threshold (general) | ≥20% | ≥20% (but gene-defined AML lower) | Context-dependent |

## Implementation Steps

1. **Edit `SKILL.md`** — add 2 rows to the Reference Files table
2. **Edit `references/scientific-skills.md`** — add a "Classification Reference Files" section before or after the existing skill class list

## Files to Modify

| File | Change |
|------|--------|
| `hematology-paper-writer/SKILL.md` | Add 2 rows to Reference Files table |
| `hematology-paper-writer/references/scientific-skills.md` | Add classification reference section |

## Success Metrics

- Claude loads WHO or ICC file when asked about myeloid disease classification
- Claude loads both files when comparing WHO vs ICC
- Claude invokes classification validator with reference context when using `hpw hypothesis` or similar commands
- No hallucinated blast thresholds or entity names when classification reference is loaded
