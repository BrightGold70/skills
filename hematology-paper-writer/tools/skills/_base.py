"""
Scientific Skills Integration — Foundation Layer
Provides SkillBase abstract class and SkillContext dataclass for cross-phase
context persistence. All 12 scientific skill classes inherit from SkillBase.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Optional


@dataclass
class SkillContext:
    """
    Shared state container threaded across HPW phases.

    Persisted to: project_notebooks/{project_name}.skills_context.json
    Each skill class reads/writes only its own keys — no coupling between skills.
    """

    project_name: str

    # Phase 1 — Topic Selection
    hypotheses: list = field(default_factory=list)          # list[str]
    research_gaps: list = field(default_factory=list)       # list[str]

    # Phase 2 — Research Design
    study_design: dict = field(default_factory=dict)        # {type, population, diagram}
    statistical_plan: dict = field(default_factory=dict)    # {primary_endpoint, methods, assumptions}

    # Phase 3 — Journal Strategy
    journal_fit_score: Optional[float] = None

    # Phase 4 — Manuscript Prep
    draft_sections: dict = field(default_factory=dict)      # {section_name: prose_text}
    figure_descriptions: list = field(default_factory=list) # list[str]

    # Phase 4.5 — Updating
    update_log: list = field(default_factory=list)          # list[str]

    # Phase 4.7 / 5 — Prose Verification / Quality
    prose_issues: list = field(default_factory=list)        # list[str]
    quality_scores: dict = field(default_factory=dict)      # {check_name: float}

    # Phase 8 — Peer Review
    review_comments: list = field(default_factory=list)     # list[str]

    # Phase 9 — Publication
    slide_outline: dict = field(default_factory=dict)       # {slides: [{title, bullets}]}

    # Standalone — Grant Writing
    grant_sections: dict = field(default_factory=dict)      # {section_name: prose_text}

    # Phase 4 — Classification Validation (hpw-classification-validator)
    classification_result: dict = field(default_factory=dict)
    # Keys populated by ClassificationValidator:
    #   disease, n_patients, last_aml (AMLClassificationResult dict),
    #   concordance_report (DiscordanceReport dict),
    #   who_2022_counts, icc_2022_counts, eln2022_risk_counts,
    #   cml_milestones {Nm: CMLMilestoneResult dict},
    #   gvhd_grades {acute: {grade: n}, chronic: {grade: n}}

    def save(self, project_dir: Path) -> None:
        """Persist context to JSON. Creates project_notebooks/ if needed."""
        path = Path(project_dir) / "project_notebooks" / f"{self.project_name}.skills_context.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, default=str))

    @classmethod
    def load(cls, project_name: str, project_dir: Path) -> "SkillContext":
        """
        Load context from JSON. Never raises — returns empty context on any failure.
        Forward-compatible: unknown keys in JSON are silently dropped.
        """
        path = Path(project_dir) / "project_notebooks" / f"{project_name}.skills_context.json"
        if not path.exists():
            return cls(project_name=project_name)
        try:
            data = json.loads(path.read_text())
            known_keys = {f.name for f in fields(cls)}
            filtered = {k: v for k, v in data.items() if k in known_keys}
            return cls(**filtered)
        except Exception:
            logging.getLogger(__name__).warning(
                "SkillContext: corrupt or unreadable context at %s — starting fresh", path
            )
            return cls(project_name=project_name)


class SkillBase(ABC):
    """
    Abstract base for all 12 scientific skill classes.

    Subclasses implement invoke() and one or more domain-specific methods
    that read/write self.context. All methods must fail silently — log
    warnings and return empty/default values rather than raising.

    Usage pattern in phase modules:
        ctx = SkillContext.load(project_name, project_dir)
        result = MySkill(context=ctx).my_method(...)
        ctx.save(project_dir)
    """

    def __init__(self, context: SkillContext) -> None:
        self.context = context
        self._log = logging.getLogger(self.__class__.__name__)

    def load_context(self, project_name: str, project_dir: Path) -> None:
        """Replace current context by loading from disk."""
        self.context = SkillContext.load(project_name, Path(project_dir))

    def save_context(self, project_dir: Path) -> None:
        """Persist current context to disk."""
        self.context.save(Path(project_dir))

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Primary LLM-mediated operation. Returns result string.
        Must never raise — catch all exceptions and return empty string.
        """
        ...
