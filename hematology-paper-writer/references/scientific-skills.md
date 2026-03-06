# Scientific Skills Integration Reference

13 cross-phase skill classes in `tools/skills/`. Load this file when using `hpw hypothesis`, `hpw brainstorm`, `hpw visualize-figure`, `hpw grant-draft`, or any other scientific skill CLI command.

---

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
| Clonal Haematopoiesis | CHIP/CCUS defined (top-level) | Not a top-level ICC category |

---

## Part 20: Scientific Skills Integration

### Overview

HPW exposes 13 scientific skill classes in `tools/skills/`, each wrapping
skill logic as a fail-silent Python class with cross-phase state persistence
via `SkillContext` (JSON at `project_notebooks/{project}.skills_context.json`).

### Skill Classes

| Class | Phase | Purpose |
|-------|-------|---------|
| `HypothesisGenerator` | 1 | Generates testable hypotheses + null hypotheses |
| `ScientificBrainstormer` | 1 | SCAMPER / Six Thinking Hats brainstorming |
| `ResearchLookup` | 1 | PubMed literature retrieval |
| `ContentResearcher` | 1/3 | Literature gap identification and synthesis |
| `StatisticalAnalyst` | 2 | Study design and statistical planning |
| `ScientificSchematist` | 2/4 | ASCII study design schematics |
| `ScientificWriter` | 4 | IMRaD section prose templates |
| `AcademicWriter` | 4/4.5 | Prose transformation, language upgrade |
| `ScientificVisualizer` | 4/9 | Figure legend templates |
| `CriticalThinker` | 5/8 | Logical fallacy and methodology evaluation |
| `PeerReviewer` | 8 | Structured reviewer-style comments |
| `SlideGenerator` | 9 | Conference presentation outlines |
| `GrantWriter` | 9 | NIH grant section templates |

### Phase Integration Functions

Each phase module has an additive `integrate_skills_phaseN()` at file end:

| Phase file | Function | Skills |
|-----------|----------|--------|
| `phase1_topic/topic_development.py` | `integrate_skills_phase1()` | HypothesisGenerator, ScientificBrainstormer, ResearchLookup |
| `phase2_research/study_design_manager.py` | `integrate_skills_phase2()` | StatisticalAnalyst |
| `phase3_journal/journal_strategy_manager.py` | `integrate_skills_phase3()` | ContentResearcher |
| `phase4_5_updating/manuscript_updater.py` | `integrate_skills_phase4_5()` | AcademicWriter |
| `phase4_7_prose/prose_verifier.py` | `integrate_skills_phase4_7()` | CriticalThinker |
| `phase5_quality/__init__.py` | `integrate_skills_phase5()` | CriticalThinker |
| `phase8_peerreview/peer_review_manager.py` | `integrate_skills_phase8()` | PeerReviewer, CriticalThinker |
| `phase9_publication/publication_manager.py` | `integrate_skills_phase9()` | SlideGenerator |

### Tests

```
tests/test_skill_context.py        8 tests — SkillContext save/load/recover
tests/test_hypothesis_generator.py 19 tests — HypothesisGenerator, null hypotheses
tests/test_critical_thinker.py     29 tests — CriticalThinker, PeerReviewer, AcademicWriter
tests/test_skill_integration.py     8 tests — cross-phase context flow

Total: 113 tests  (~0.1s)
Run: python -m pytest tests/ -q
```
