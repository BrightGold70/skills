# Plan: HPW Recipe 3 Structural Upgrade (Section Chaining + Full-Text)

## Overview
Update the Hematology Paper Writer (HPW) "Recipe 3: The Comprehensive Narrative Review" to enforce submission-quality rigor. The current single-pass generation relying only on PubMed abstracts produces shallow results without proper academic structure. The new protocol will strictly mandate NotebookLM integration for deep full-text context and explicit section-by-section drafting.

## Goals
- Enforce mandatory full-text literature ingestion via NotebookLM prior to manuscript drafting.
- Forbid single-pass full-text generation in favor of a strict, user-approved section-by-section drafting loop.
- Elevate the output to submission quality by explicitly demanding exact p-values, mechanistic context, and zero generalized fluff.

## User Stories
- As a medical researcher, I want my generated narrative reviews to automatically adopt standard academic sections (Abstract, Introduction, Methods, Evidence Review, Discussion) and possess the depth of full-text papers so that the draft is structurally sound and submission-ready.

## Success Criteria
- [ ] `SKILL.md` is updated to include the NotebookLM halt-and-ingest prerequisite for Recipe 3.
- [ ] `SKILL.md` is updated to define the "Section-by-Section Sequencing" protocol.
- [ ] Explicit instructions defining "submission quality" are added to the Recipe 3 definition.

## Implementation Approach
1. Modify the Recipe 3 subsection in `/Users/kimhawk/.agents/skills/hematology-paper-writer/SKILL.md`.
2. Add a critical requirement block explicitly defining expected quality.
3. Replace the "Deep Drafting" step with "Mandatory Full-Text Integration" and "Section-by-Section Sequencing".
4. Ensure the Farquhar structuring is mapped to standard academic headers.

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| User friction from manual PDF uploads | Medium | Clearly explain in the prompt *why* this step is required to achieve submission-quality depth and avoid hallucination. |
| AI losing context between sections | Low | Enforce that the AI queries NotebookLM for the specific context of the current section before drafting it. |

## Timeline
Estimated effort: 1-2 agent interactions to update `SKILL.md` and complete the PDCA cycle.
