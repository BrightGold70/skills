# Plan: HPW Scientific Skills Integration

**Feature:** `hpw-scientific-skills-integration`
**Phase:** Plan
**Created:** 2026-03-05
**Status:** Planning
**Design doc:** `docs/plans/2026-03-05-hpw-scientific-skills-integration-design.md`

---

## 1. Overview

Integrate all 12 scientific OpenCode skills into the `hematology-paper-writer` as explicit Python classes in `tools/skills/`, with cross-phase context persistence via `SkillContext`. Each HPW phase module explicitly imports and calls the relevant skill class(es). Context is threaded across phases through a JSON-persisted `SkillContext` dataclass, enabling hypotheses from Phase 1 to inform quality checks in Phase 5 without re-derivation.

---

## 2. Proposals in Scope

| # | Component | Effort | Impact |
|---|-----------|--------|--------|
| 1 | `tools/skills/_base.py` — `SkillBase` + `SkillContext` | Small | High |
| 2 | `PhaseManager` — `skills_context_path` field | Small | High |
| 3 | 12 skill classes in `tools/skills/` | Large | High |
| 4 | Phase module updates (10 phases) | Medium | High |
| 5 | 4 new CLI commands in `cli.py` | Small | Medium |
| 6 | SKILL.md Part 19 — Scientific Skills Integration | Small | Medium |
| 7 | Test suite (4 test files) | Medium | High |

---

## 3. Proposal Details & Requirements

### Proposal #1 — Foundation: `SkillBase` + `SkillContext`

**File:** `tools/skills/_base.py`

**Requirements:**
- `SkillContext` dataclass with fields for all 12 skill output types:
  `hypotheses`, `research_gaps`, `study_design`, `statistical_plan`,
  `draft_sections`, `figure_descriptions`, `quality_scores`,
  `review_comments`, `slide_outline`, `grant_sections`, `prose_issues`,
  `journal_fit_score`, `update_log`
- `SkillContext.save(project_dir)` → writes to `project_notebooks/{project}.skills_context.json`
- `SkillContext.load(project_name, project_dir)` → reads JSON or returns empty context
- `SkillContext.load()` validates schema; corrupt/missing file → returns `SkillContext(project_name)` (no exception)
- `SkillBase` abstract base class with `load_context()`, `save_context()`, `invoke(prompt, **kwargs) → str`
- No external dependencies — stdlib only (`dataclasses`, `json`, `pathlib`)

**Deliverable:** `tools/skills/_base.py`

---

### Proposal #2 — PhaseManager Integration

**File:** `phases/phase_manager.py`

**Requirements:**
- Add `skills_context_path: str | None = None` to `ManuscriptMetadata`
- On phase transition, persist `skills_context_path` to the existing phase JSON state
- No breaking changes to existing phase serialization

**Deliverable:** Updated `phases/phase_manager.py`

---

### Proposal #3 — 12 Skill Classes

**Directory:** `tools/skills/`

| File | Class | Source Skill | HPW Phases |
|------|-------|--------------|------------|
| `hypothesis_generator.py` | `HypothesisGenerator` | `hypothesis-generation` | 1, 2 |
| `scientific_brainstormer.py` | `ScientificBrainstormer` | `scientific-brainstorming` | 1, Part 16 |
| `research_lookup.py` | `ResearchLookup` | `research-lookup` | 1, 4 |
| `statistical_analyst.py` | `StatisticalAnalyst` | `statistical-analysis` | 2, 4, 5 |
| `scientific_writer.py` | `ScientificWriter` | `scientific-writing` | 4, 4.5 |
| `critical_thinker.py` | `CriticalThinker` | `scientific-critical-thinking` | 3, 4.7, 5, 8 |
| `scientific_visualizer.py` | `ScientificVisualizer` | `scientific-visualization` | 4 |
| `scientific_schematist.py` | `ScientificSchematist` | `scientific-schematics` | 2 |
| `academic_writer.py` | `AcademicWriter` | `academic-research-writer` | 4 |
| `slide_generator.py` | `SlideGenerator` | `scientific-slides` | 9 |
| `grant_writer.py` | `GrantWriter` | `research-grants` | standalone |
| `peer_reviewer.py` | `PeerReviewer` | `peer-review` | 8 |
| `content_researcher.py` | `ContentResearcher` | `content-research-writer` | 1, 4 |

**Requirements per class:**
- Inherits `SkillBase`
- Constructor accepts `context: SkillContext`
- Primary method (e.g., `generate()`, `evaluate()`, `review()`) returns typed output and writes to `context`
- Fails silently (logs warning, returns empty result) — never raises to caller

**Deliverable:** 12 Python files + `tools/skills/__init__.py` (re-exports all classes)

---

### Proposal #4 — Phase Module Updates

**Files:** 10 phase modules across `phases/`

**Requirements:**
- Each phase that uses skills loads `SkillContext` at start, saves at end
- Pattern:
  ```python
  ctx = SkillContext.load(self.project_name, self.project_dir)
  result = SkillClass(context=ctx).method(...)
  ctx.save(self.project_dir)
  ```
- Skill invocation is opt-in: guarded by `if self.use_scientific_skills:` (default `True`)
- No changes to phase public API

**Phases to update:** Phase 1, 2, 3, 4, 4.5, 4.7, 5, 8, 9, and standalone grant command

**Deliverable:** Updated phase modules (10 files)

---

### Proposal #5 — New CLI Commands

**File:** `cli.py`

**New subcommands:**

| Command | Class | Description |
|---------|-------|-------------|
| `hpw hypothesis <topic>` | `HypothesisGenerator` | Generate research hypotheses |
| `hpw brainstorm <topic> [--method scamper]` | `ScientificBrainstormer` | Brainstorm research directions |
| `hpw visualize-figure <eps_path>` | `ScientificVisualizer` | Generate figure description from .eps |
| `hpw grant-draft <opportunity>` | `GrantWriter` | Draft grant application sections |

**Requirements:**
- Each command loads `SkillContext` from `--project` flag (or CWD default)
- Output written to stdout + saved to context
- `--no-context` flag to skip context persistence for standalone use

**Deliverable:** Updated `cli.py`

---

### Proposal #6 — SKILL.md Part 19

**File:** `SKILL.md`

**Requirements:**
- Add Part 19: "Scientific Skills Integration"
- Document all 12 skill classes with: purpose, HPW phase, primary method, example
- Document `SkillContext` threading model (one diagram)
- Document 4 new CLI commands
- Update Table of Contents

**Deliverable:** Updated `SKILL.md`

---

### Proposal #7 — Test Suite

**Directory:** `tests/`

| File | Coverage |
|------|----------|
| `test_skill_context.py` | `SkillContext` save/load/corrupt recovery/schema validation |
| `test_hypothesis_generator.py` | `HypothesisGenerator.generate()` with mocked responses |
| `test_critical_thinker.py` | `CriticalThinker.evaluate()` with mocked responses |
| `test_skill_integration.py` | End-to-end: Phase 1 hypothesis → Phase 5 quality check context flow |

**Requirements:**
- Mocked LLM responses (consistent with existing `conftest.py`)
- All tests pass with `pytest tests/` from HPW root
- Minimum 4 test files, ≥20 test functions total

**Deliverable:** 4 new test files

---

## 4. Implementation Order

```
Week 1 — Foundation (no phase changes yet):
  Proposal #1: _base.py (SkillBase + SkillContext)
  Proposal #2: PhaseManager integration
  Proposal #7 (partial): test_skill_context.py

Week 2 — Core manuscript skills (Phase 1-4):
  Proposal #3: hypothesis_generator.py, scientific_brainstormer.py,
               research_lookup.py, statistical_analyst.py, scientific_writer.py
  Proposal #4: Phase 1, 2, 4 updates

Week 3 — Quality/review skills (Phase 4.7, 5, 8):
  Proposal #3: critical_thinker.py, peer_reviewer.py, academic_writer.py
  Proposal #4: Phase 3, 4.5, 4.7, 5, 8 updates
  Proposal #7 (partial): test_hypothesis_generator.py, test_critical_thinker.py

Week 4 — Output/visualization/standalone:
  Proposal #3: scientific_visualizer.py, scientific_schematist.py,
               slide_generator.py, grant_writer.py, content_researcher.py
  Proposal #4: Phase 9, standalone grant updates
  Proposal #5: CLI commands
  Proposal #6: SKILL.md Part 19

Week 5 — Integration tests + polish:
  Proposal #7 (complete): test_skill_integration.py
  tools/skills/__init__.py finalized
  SKILL.md Part 19 finalized
```

---

## 5. Risk Assessment

| Proposal | Risk | Mitigation |
|----------|------|------------|
| #1 `_base.py` | Low — pure stdlib | Schema validation on load; no breaking surface |
| #2 PhaseManager | Low-Medium — touches metadata | Add field as Optional with default None; backward-compatible |
| #3 12 skill classes | Medium — large volume | Implement in batches by phase tier; fail-silent pattern |
| #4 Phase updates | Medium — 10 files | Guard with `use_scientific_skills` flag; additive only |
| #5 CLI commands | Low — additive subcommands | New subparsers don't affect existing commands |
| #6 SKILL.md | Low — doc only | New Part 19 appended; no existing parts modified |
| #7 Tests | Low | Mock all LLM calls; isolate skill logic from I/O |

---

## 6. Success Criteria

| Proposal | Done When |
|----------|-----------|
| #1 | `test_skill_context.py` passes: save/load/corrupt recovery all verified |
| #2 | `ManuscriptMetadata.skills_context_path` persists across phase transitions |
| #3 | All 12 skill classes have unit tests passing |
| #4 | Phase 1 invokes `HypothesisGenerator`; context written to JSON |
| #5 | `hpw hypothesis "AML salvage"` produces output and saves to context |
| #6 | Part 19 appears in SKILL.md ToC with all 12 classes documented |
| #7 | `pytest tests/` passes with ≥20 test functions across 4 test files |

---

## 7. Dependencies

- Builds on existing `tools/statistical_bridge.py` pattern (context passing)
- Builds on existing `tools/notebooklm_integration.py` pattern (silent fail)
- Requires `phases/phase_manager.py` update before phase module updates (#2 before #4)
- `tools/skills/__init__.py` requires all 12 classes before finalization
