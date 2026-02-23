# Plan: HPW Skill Improvements

## Overview
Enhance the Hematology Paper Writer (HPW) skill by formally integrating `statistical-analysis`, `pubmed-integration`, and `citation-management` into goal-oriented workflow recipes.

## Goals
- Provide distinct, actionable recipes for different manuscript types.
- Deepen the integration of statistical analysis and literature reviews directly within HPW's drafting workflow.
- Maintain the strict academic rigor, reference integrity, and clinical accuracy core to HPW.

## User Stories
- As a researcher, I want a recipe for an AI-assisted meta-analysis so that I can seamlessly move from identifying PMIDs to quantitative synthesis and finally manuscript drafting.
- As a clinician, I want a recipe for a clinical trial report so that I can run assumption checks and calculate primary endpoints before drafting a CONSORT-compliant manuscript.
- As an author, I want a recipe for a comprehensive narrative review so that I can aggressively cite a deeply researched corpus and structure a compelling argument.

## Success Criteria
- [ ] Goal-Oriented Workflow Recipes section added to the HPW `SKILL.md`.
- [ ] Recipes successfully reference `pubmed-integration`, `statistical-analysis`, and `citation-management`.
- [ ] Recipes are logical, sequential, and align with HPW's core principles.

## Implementation Approach
1. Draft a design document detailing the 3 proposed workflow recipes: Meta-Analysis, Clinical Trial, and Narrative Review.
2. Get user approval for the proposed approach.
3. Update the `SKILL.md` file of `hematology-paper-writer` to embed the precise workflows as "Part 19: Goal-Oriented Workflow Recipes".

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Recipes become too complex | Medium | Keep recipes explicitly phased and high-level in the `SKILL.md` rather than scripting every CLI command. |
| Overlap with existing HPW steps | Low | Ensure recipes clearly demarcate where external skills end and HPW native drafting begins. |

## Timeline
Estimated effort: 1 implementation session.
Milestones:
1. Design document created and approved.
2. HPW `SKILL.md` updated with Recipe 1, 2, and 3.
