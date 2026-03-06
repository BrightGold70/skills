# Design: HPW Scientific Skills Integration

**Feature:** `hpw-scientific-skills-integration`
**Phase:** Design
**Created:** 2026-03-05
**Plan reference:** `docs/01-plan/features/hpw-scientific-skills-integration.plan.md`
**Design reference:** `docs/plans/2026-03-05-hpw-scientific-skills-integration-design.md`

---

## Architecture Overview

Introduce a `tools/skills/` layer into HPW that extracts the logic of 12 OpenCode scientific skills into thin Python classes. Each class inherits `SkillBase`, reads/writes a shared `SkillContext` dataclass, and is explicitly imported by the HPW phase module that needs it. Context persists across phases via `project_notebooks/{project}.skills_context.json`.

```
phases/
  phase1_topic/       → imports HypothesisGenerator, ScientificBrainstormer, ResearchLookup
  phase2_research/    → imports HypothesisGenerator, StatisticalAnalyst, ScientificSchematist
  phase3_journal/     → imports CriticalThinker
  phase4_manuscript/  → imports ScientificWriter, AcademicWriter, StatisticalAnalyst,
                                ScientificVisualizer, ContentResearcher
  phase4_5_updating/  → imports ScientificWriter, ResearchLookup
  phase4_7_prose/     → imports CriticalThinker, ScientificWriter
  phase5_quality/     → imports CriticalThinker, StatisticalAnalyst
  phase8_peerreview/  → imports PeerReviewer, CriticalThinker
  phase9_publication/ → imports SlideGenerator
  cli.py (standalone) → imports GrantWriter
        ↓ (all phases)
tools/skills/
  _base.py            ← SkillBase (abstract) + SkillContext (dataclass)
  12 skill classes    ← thin Python implementations
        ↓
project_notebooks/{project}.skills_context.json  ← persisted cross-phase state
```

---

## Components

### `tools/skills/_base.py` — Foundation

**`SkillContext` dataclass** — the shared state container:

```python
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import logging

@dataclass
class SkillContext:
    project_name: str
    # Phase 1 outputs
    hypotheses: list[str] = field(default_factory=list)
    research_gaps: list[str] = field(default_factory=list)
    # Phase 2 outputs
    study_design: dict = field(default_factory=dict)
    statistical_plan: dict = field(default_factory=dict)
    # Phase 3 outputs
    journal_fit_score: float | None = None
    # Phase 4 outputs
    draft_sections: dict = field(default_factory=dict)
    figure_descriptions: list[str] = field(default_factory=list)
    update_log: list[str] = field(default_factory=list)
    # Phase 4.7 / 5 outputs
    prose_issues: list[str] = field(default_factory=list)
    quality_scores: dict = field(default_factory=dict)
    # Phase 8 outputs
    review_comments: list[str] = field(default_factory=list)
    # Phase 9 outputs
    slide_outline: dict = field(default_factory=dict)
    # Standalone
    grant_sections: dict = field(default_factory=dict)

    def save(self, project_dir: Path) -> None:
        path = project_dir / "project_notebooks" / f"{self.project_name}.skills_context.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, project_name: str, project_dir: Path) -> "SkillContext":
        path = project_dir / "project_notebooks" / f"{project_name}.skills_context.json"
        if not path.exists():
            return cls(project_name=project_name)
        try:
            data = json.loads(path.read_text())
            # Drop unknown keys for forward-compatibility
            known = {f.name for f in fields(cls)}
            return cls(**{k: v for k, v in data.items() if k in known})
        except Exception:
            logging.warning("SkillContext: corrupt context file, starting fresh")
            return cls(project_name=project_name)
```

**`SkillBase` abstract class:**

```python
from abc import ABC, abstractmethod

class SkillBase(ABC):
    def __init__(self, context: SkillContext):
        self.context = context
        self._log = logging.getLogger(self.__class__.__name__)

    def load_context(self, project_name: str, project_dir: Path) -> None:
        self.context = SkillContext.load(project_name, project_dir)

    def save_context(self, project_dir: Path) -> None:
        self.context.save(project_dir)

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """Primary method. Returns result string. Never raises."""
        ...
```

---

### 12 Skill Classes — API Signatures

All classes inherit `SkillBase`. All primary methods return typed results and silently update `self.context`. Errors are caught and logged; empty/default values returned on failure.

| Class | File | Primary Method | Returns | Updates Context |
|-------|------|----------------|---------|-----------------|
| `HypothesisGenerator` | `hypothesis_generator.py` | `generate(topic: str, disease: str) -> list[str]` | list of hypotheses | `context.hypotheses` |
| `ScientificBrainstormer` | `scientific_brainstormer.py` | `brainstorm(topic: str, method: str = "free") -> list[str]` | list of ideas | `context.research_gaps` |
| `ResearchLookup` | `research_lookup.py` | `lookup(query: str, max_results: int = 10) -> list[dict]` | list of {title, pmid, summary} | `context.research_gaps` |
| `StatisticalAnalyst` | `statistical_analyst.py` | `analyze(data_description: str, study_type: str) -> dict` | {methods, assumptions, tests} | `context.statistical_plan` |
| `ScientificWriter` | `scientific_writer.py` | `write_section(section: str, outline: str, style: str = "academic") -> str` | prose text | `context.draft_sections[section]` |
| `CriticalThinker` | `critical_thinker.py` | `evaluate(text: str, criteria: list[str]) -> list[str]` | list of issues/comments | `context.prose_issues` or `context.quality_scores` |
| `ScientificVisualizer` | `scientific_visualizer.py` | `describe_figure(figure_path: str, context_hint: str = "") -> str` | figure legend text | `context.figure_descriptions` |
| `ScientificSchematist` | `scientific_schematist.py` | `generate_diagram(study_design: dict) -> str` | mermaid/text diagram | `context.study_design["diagram"]` |
| `AcademicWriter` | `academic_writer.py` | `draft(topic: str, section: str, references: list[str]) -> str` | prose text | `context.draft_sections[section]` |
| `SlideGenerator` | `slide_generator.py` | `generate_outline(manuscript_summary: str, n_slides: int = 15) -> dict` | {slides: [{title, bullets}]} | `context.slide_outline` |
| `GrantWriter` | `grant_writer.py` | `draft_section(opportunity: str, section: str) -> str` | grant prose | `context.grant_sections[section]` |
| `PeerReviewer` | `peer_reviewer.py` | `review(manuscript_text: str, journal: str) -> list[str]` | list of reviewer comments | `context.review_comments` |
| `ContentResearcher` | `content_researcher.py` | `research(topic: str, depth: str = "standard") -> dict` | {summary, key_points, sources} | `context.research_gaps` |

**`tools/skills/__init__.py`** re-exports all:

```python
from .hypothesis_generator import HypothesisGenerator
from .scientific_brainstormer import ScientificBrainstormer
from .research_lookup import ResearchLookup
from .statistical_analyst import StatisticalAnalyst
from .scientific_writer import ScientificWriter
from .critical_thinker import CriticalThinker
from .scientific_visualizer import ScientificVisualizer
from .scientific_schematist import ScientificSchematist
from .academic_writer import AcademicWriter
from .slide_generator import SlideGenerator
from .grant_writer import GrantWriter
from .peer_reviewer import PeerReviewer
from .content_researcher import ContentResearcher
from ._base import SkillBase, SkillContext

__all__ = [
    "SkillBase", "SkillContext",
    "HypothesisGenerator", "ScientificBrainstormer", "ResearchLookup",
    "StatisticalAnalyst", "ScientificWriter", "CriticalThinker",
    "ScientificVisualizer", "ScientificSchematist", "AcademicWriter",
    "SlideGenerator", "GrantWriter", "PeerReviewer", "ContentResearcher",
]
```

---

## Data Models

### `SkillContext` JSON Schema

Persisted at `project_notebooks/{project_name}.skills_context.json`:

```json
{
  "project_name": "aml_salvage_review",
  "hypotheses": ["Azacitidine improves OS in R/R AML vs placebo"],
  "research_gaps": ["No head-to-head comparison of venetoclax combinations"],
  "study_design": {
    "type": "systematic_review",
    "population": "R/R AML patients",
    "diagram": "graph TD\n  A[Screen] --> B[Include]"
  },
  "statistical_plan": {
    "primary_endpoint": "OS",
    "methods": ["Kaplan-Meier", "log-rank"],
    "assumptions": ["proportional hazards"]
  },
  "journal_fit_score": 0.82,
  "draft_sections": {
    "introduction": "AML is...",
    "methods": "We searched PubMed..."
  },
  "figure_descriptions": ["Figure 1: PRISMA flow diagram showing..."],
  "update_log": [],
  "prose_issues": ["Passive voice in Methods §2.3"],
  "quality_scores": {"prisma_compliance": 0.94},
  "review_comments": ["Expand discussion of venetoclax resistance mechanisms"],
  "slide_outline": {},
  "grant_sections": {}
}
```

### `ManuscriptMetadata` extension (`phases/phase_manager.py`)

```python
@dataclass
class ManuscriptMetadata:
    # ... existing fields ...
    skills_context_path: str | None = None  # NEW — relative path to .skills_context.json
```

---

## API Specifications — Phase Integration Points

### Phase invocation pattern (all phases)

```python
# At start of each phase method that uses skills:
from tools.skills import SkillContext, HypothesisGenerator  # etc.

ctx = SkillContext.load(self.project_name, Path(self.project_dir))
skill = HypothesisGenerator(context=ctx)
result = skill.generate(topic=self.topic, disease=self.disease)
ctx.save(Path(self.project_dir))
# result is also in ctx.hypotheses for downstream phases
```

### Phase 1 — `phase1_topic/`

```python
from tools.skills import HypothesisGenerator, ScientificBrainstormer, ResearchLookup

# TopicDevelopmentManager.develop_topic():
ctx = SkillContext.load(...)
ctx.hypotheses = HypothesisGenerator(ctx).generate(topic, disease)
ctx.research_gaps += ScientificBrainstormer(ctx).brainstorm(topic)
ctx.research_gaps += [r["summary"] for r in ResearchLookup(ctx).lookup(topic)]
ctx.save(...)
```

### Phase 5 — `phase5_quality/` (reads Phase 1 context)

```python
from tools.skills import CriticalThinker, StatisticalAnalyst, SkillContext

ctx = SkillContext.load(...)
# ctx.hypotheses already populated from Phase 1 — used to validate manuscript alignment
thinker = CriticalThinker(ctx)
ctx.quality_scores = thinker.evaluate(manuscript_text, criteria=["hypothesis_alignment", "prisma"])
ctx.save(...)
```

### New CLI Commands (`cli.py`)

```python
# hpw hypothesis <topic> [--disease <disease>] [--project <name>]
def cmd_hypothesis(args):
    ctx = SkillContext.load(args.project, get_project_dir(args.project))
    result = HypothesisGenerator(ctx).generate(args.topic, args.disease or "")
    if not args.no_context:
        ctx.save(get_project_dir(args.project))
    print("\n".join(result))

# hpw brainstorm <topic> [--method scamper|six-hats|free] [--project <name>]
# hpw visualize-figure <eps_path> [--project <name>]
# hpw grant-draft <opportunity> [--section specific-aims|significance|approach]
```

---

## Security Considerations

- `SkillContext` JSON may contain clinical research data — files inherit project directory permissions (Dropbox-managed)
- No patient-level data should be written to `SkillContext`; all fields store analysis outputs, not raw patient records
- `SkillContext.load()` uses `known = {f.name for f in fields(cls)}` key filtering to prevent injection of arbitrary keys from corrupt/malicious JSON

---

## Testing Strategy

### Test Files

**`tests/test_skill_context.py`** — `SkillContext` contract tests:
- `test_save_creates_json()` — file written to correct path
- `test_load_returns_empty_on_missing()` — no file → `SkillContext(project_name)`
- `test_load_recovers_from_corrupt_json()` — invalid JSON → empty context, no exception
- `test_load_drops_unknown_keys()` — forward-compatibility with future schema fields
- `test_round_trip()` — save then load preserves all fields

**`tests/test_hypothesis_generator.py`** — representative skill unit test:
- `test_generate_returns_list()` — result is `list[str]`, non-empty
- `test_generate_updates_context()` — `ctx.hypotheses` populated after call
- `test_generate_silent_on_error()` — exception in impl → empty list, no raise
- `test_context_saved_after_generate()` — `ctx.save()` called

**`tests/test_critical_thinker.py`**:
- `test_evaluate_returns_issues()` — issues list non-empty for flawed text
- `test_evaluate_updates_prose_issues()` — `ctx.prose_issues` populated
- `test_evaluate_updates_quality_scores()` — scores dict populated when `criteria` includes scoring keys

**`tests/test_skill_integration.py`** — cross-phase context threading:
- `test_phase1_to_phase5_context_flow()` — hypotheses written in Phase 1 mock → readable in Phase 5 mock
- `test_context_persists_across_skill_instances()` — two different skill instances share same JSON
- `test_multiple_phases_accumulate_context()` — Phase 1 + Phase 4 + Phase 5 all write; all keys present

### Mocking strategy

```python
# conftest.py addition
@pytest.fixture
def mock_skill_response(monkeypatch):
    """Patches SkillBase.invoke to return deterministic test data."""
    def _fake_invoke(self, prompt, **kwargs):
        return f"mocked response for: {prompt[:50]}"
    monkeypatch.setattr(SkillBase, "invoke", _fake_invoke)
```

All 12 skill classes tested against this fixture; primary method tests use `mock_skill_response` to avoid LLM calls.

---

## Implementation Order

```
Week 1:
  tools/skills/_base.py
  phases/phase_manager.py  (+skills_context_path)
  tests/test_skill_context.py

Week 2:
  hypothesis_generator.py, scientific_brainstormer.py,
  research_lookup.py, statistical_analyst.py, scientific_writer.py
  Phase 1, 2, 4 module updates
  tests/test_hypothesis_generator.py

Week 3:
  critical_thinker.py, peer_reviewer.py, academic_writer.py
  Phase 3, 4.5, 4.7, 5, 8 module updates
  tests/test_critical_thinker.py

Week 4:
  scientific_visualizer.py, scientific_schematist.py,
  slide_generator.py, grant_writer.py, content_researcher.py
  Phase 9, standalone grant CLI
  tools/skills/__init__.py (finalized)
  cli.py (4 new subcommands)

Week 5:
  tests/test_skill_integration.py
  SKILL.md Part 19
  Full pytest run → target 100% pass rate
```
