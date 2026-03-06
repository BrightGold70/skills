# Design: HPW Scientific Skills Integration

**Date:** 2026-03-05
**Feature:** `hpw-scientific-skills-integration`
**Status:** Approved

---

## Overview

Integrate all 12 scientific OpenCode skills into the `hematology-paper-writer` (HPW) as explicit Python classes in `tools/skills/`, with cross-phase context threading via a `SkillContext` dataclass persisted to JSON.

**Integration type:** C2 — extract scientific skill SKILL.md logic into Python classes
**Scope:** All 12 available scientific skills
**Invocation:** A — explicit per-phase imports

---

## Section 1: Architecture

### Directory Structure

```
tools/
  skills/
    __init__.py               # re-exports all 12 classes
    _base.py                  # SkillBase + SkillContext (shared state)
    hypothesis_generator.py   # Phase 1, 2
    scientific_brainstormer.py # Phase 1, Part 16
    research_lookup.py        # Phase 1, 4
    statistical_analyst.py    # Phase 2, 4
    scientific_writer.py      # Phase 4, 4.5
    critical_thinker.py       # Phase 4.7, 5, 8
    scientific_visualizer.py  # Phase 4 (figure descriptions)
    scientific_schematist.py  # Phase 2 (study design diagrams)
    academic_writer.py        # Phase 4 (parallel drafter)
    slide_generator.py        # Phase 9
    grant_writer.py           # standalone
    peer_reviewer.py          # Phase 8
    content_researcher.py     # Phase 1, 4
```

### Key Classes

- **`SkillContext`** — JSON-serializable dataclass persisted to `project_notebooks/{project}.skills_context.json`. Threaded through phases via `PhaseManager`.
- **`SkillBase`** — abstract base with `load_context()`, `save_context()`, `invoke(prompt, **kwargs) → str`.
- **12 skill classes** — thin Python implementations of each scientific skill's SKILL.md logic.

---

## Section 2: Phase-to-Skill Mapping

| HPW Phase | Skill Classes Invoked | Context Keys Written |
|-----------|----------------------|----------------------|
| 1 — Topic Selection | `HypothesisGenerator`, `ScientificBrainstormer`, `ResearchLookup` | `hypotheses[]`, `research_gaps[]` |
| 2 — Research Design | `HypothesisGenerator`, `StatisticalAnalyst`, `ScientificSchematist` | `study_design`, `statistical_plan` |
| 3 — Journal Strategy | `CriticalThinker` | `journal_fit_score` |
| 4 — Manuscript Prep | `ScientificWriter`, `AcademicWriter`, `StatisticalAnalyst`, `ScientificVisualizer`, `ContentResearcher` | `draft_sections{}`, `figure_descriptions[]` |
| 4.5 — Updating | `ScientificWriter`, `ResearchLookup` | `update_log[]` |
| 4.7 — Prose Verification | `CriticalThinker`, `ScientificWriter` | `prose_issues[]` |
| 5 — Quality | `CriticalThinker`, `StatisticalAnalyst` | `quality_scores{}` |
| 8 — Peer Review | `PeerReviewer`, `CriticalThinker` | `review_comments[]` |
| 9 — Publication | `SlideGenerator` | `slide_outline` |
| standalone | `GrantWriter` | `grant_sections{}` |

### New CLI Commands

```bash
hpw hypothesis "AML salvage therapy" --phase 1
hpw brainstorm "research topic" --method scamper
hpw visualize-figure figure.eps --context
hpw grant-draft "funding opportunity"
```

---

## Section 3: SkillContext Data Flow

### SkillContext Schema (`_base.py`)

```python
@dataclass
class SkillContext:
    project_name: str
    hypotheses: list[str] = field(default_factory=list)
    research_gaps: list[str] = field(default_factory=list)
    study_design: dict = field(default_factory=dict)
    statistical_plan: dict = field(default_factory=dict)
    draft_sections: dict = field(default_factory=dict)
    figure_descriptions: list[str] = field(default_factory=list)
    quality_scores: dict = field(default_factory=dict)
    review_comments: list[str] = field(default_factory=list)
    slide_outline: dict = field(default_factory=dict)
    grant_sections: dict = field(default_factory=dict)
    prose_issues: list[str] = field(default_factory=list)
    journal_fit_score: float | None = None
    update_log: list[str] = field(default_factory=list)

    def save(self, project_dir: Path) -> None:
        path = project_dir / "project_notebooks" / f"{self.project_name}.skills_context.json"
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, project_name: str, project_dir: Path) -> "SkillContext":
        path = project_dir / "project_notebooks" / f"{project_name}.skills_context.json"
        return cls(**json.loads(path.read_text())) if path.exists() else cls(project_name)
```

### PhaseManager Integration

`ManuscriptMetadata` gains one field:

```python
skills_context_path: str | None = None
```

Each phase that uses skills follows this pattern:

```python
ctx = SkillContext.load(self.project_name, self.project_dir)
gen = HypothesisGenerator(context=ctx)
hypotheses = gen.generate(topic=self.topic)
ctx.save(self.project_dir)
```

Context flows forward: hypotheses from Phase 1 are available to `CriticalThinker` in Phase 5 without re-derivation. Each skill only reads/writes its own keys — no coupling between skill classes.

---

## Section 4: Testing & Error Handling

### Test Files

```
tests/
  test_skill_context.py        # SkillContext save/load/merge
  test_hypothesis_generator.py # HypothesisGenerator.generate()
  test_critical_thinker.py     # CriticalThinker.evaluate()
  test_skill_integration.py    # end-to-end Phase 1 → Phase 5 context flow
```

Each skill class tested in isolation with `pytest` + mocked LLM responses, consistent with existing `conftest.py` pattern.

### Error Handling Principles

1. **Graceful degradation** — if a skill class fails, the phase continues without it; skill output is always additive, never blocking
2. **Context corruption guard** — `SkillContext.load()` validates schema on load; corrupt/missing context falls back to empty `SkillContext` (same pattern as `NotebookLMIntegration.ask()` silent fail)
3. **No new dependencies** — skill classes use only stdlib (`dataclasses`, `json`, `pathlib`)

### SKILL.md Update

Add Part 19: "Scientific Skills Integration" documenting all 12 classes, CLI commands, and context threading model.

---

## Implementation Order

```
Week 1 — Foundation:
  _base.py (SkillBase + SkillContext)
  PhaseManager integration (skills_context_path field)
  test_skill_context.py

Week 2 — Core manuscript skills (Phase 1-4):
  hypothesis_generator.py
  scientific_brainstormer.py
  research_lookup.py
  statistical_analyst.py
  scientific_writer.py

Week 3 — Quality/review skills (Phase 4.7, 5, 8):
  critical_thinker.py
  peer_reviewer.py
  academic_writer.py

Week 4 — Output/visualization/standalone:
  scientific_visualizer.py
  scientific_schematist.py
  slide_generator.py
  grant_writer.py
  content_researcher.py
  SKILL.md Part 19 + CLI commands

Week 5 — Integration tests + docs:
  test_skill_integration.py
  SKILL.md Part 19 finalized
```

---

## Success Criteria

| Item | Done When |
|------|-----------|
| `SkillBase` + `SkillContext` | `test_skill_context.py` passes (save/load/corrupt recovery) |
| All 12 skill classes | Each has unit test passing |
| PhaseManager integration | `ManuscriptMetadata.skills_context_path` persisted across sessions |
| Context threading | Phase 1 hypothesis available in Phase 5 quality check (integration test) |
| CLI commands | `hpw hypothesis`, `hpw brainstorm`, `hpw visualize-figure`, `hpw grant-draft` functional |
| SKILL.md Part 19 | All 12 classes documented with usage examples |
