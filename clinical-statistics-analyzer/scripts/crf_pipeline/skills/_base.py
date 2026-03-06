"""
CSA Scientific Skills Integration — Foundation Layer

Provides CSASkillBase abstract class and CSASkillContext dataclass for
cross-hook context persistence. All 8 scientific skill classes inherit
from CSASkillBase.

Separate from HPW's tools/skills/_base.py — CSA context fields are
analysis-run-oriented (disease, key_statistics) vs HPW's manuscript-
phase-oriented (draft_sections, review_comments).
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Optional


@dataclass
class CSASkillContext:
    """
    Shared state container for CSA scientific skills.

    Persisted to: {output_dir}/data/{study_name}.csa_skills_context.json
    Each skill reads/writes only its own keys — no coupling between skills.
    key_statistics entries must use StatValue-compatible shape:
      {"value": float, "unit": str|None, "ci_lower": float|None,
       "ci_upper": float|None, "p_value": float|None}
    """

    study_name: str
    disease: str = "unknown"           # "aml" | "cml" | "mds" | "hct"

    # ── Pre-analysis (written before R scripts run) ──────────────────────────
    hypotheses: list = field(default_factory=list)          # list[str]
    statistical_plan: dict = field(default_factory=dict)    # see design §2.2
    assumption_warnings: list = field(default_factory=list) # list[str]

    # ── Post-analysis (written after R scripts; populates hpw_manifest) ──────
    # Written to data/*_stats.json; _write_hpw_manifest() picks up automatically
    key_statistics: dict = field(default_factory=dict)      # {key: StatValue-dict}
    interpretation_notes: list = field(default_factory=list)# list[str]
    methods_prose: str = ""

    # CSA-specific post-analysis
    eln_annotations: dict = field(default_factory=dict)     # {stat_key: str}
    protocol_gaps: list = field(default_factory=list)       # list[str]

    # ── Tracking ─────────────────────────────────────────────────────────────
    scripts_run: list = field(default_factory=list)         # list[str]

    def save(self, output_dir: Path) -> None:
        """Persist context to JSON. Creates data/ dir if needed."""
        path = Path(output_dir) / "data" / f"{self.study_name}.csa_skills_context.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, default=str))

    @classmethod
    def load(cls, study_name: str, output_dir: Path) -> "CSASkillContext":
        """
        Load context from JSON. Never raises — returns empty context on any failure.
        Forward-compatible: unknown keys in JSON are silently dropped.
        """
        path = Path(output_dir) / "data" / f"{study_name}.csa_skills_context.json"
        if not path.exists():
            return cls(study_name=study_name)
        try:
            data = json.loads(path.read_text())
            known_keys = {f.name for f in fields(cls)}
            filtered = {k: v for k, v in data.items() if k in known_keys}
            return cls(**filtered)
        except Exception:
            logging.getLogger(__name__).warning(
                "CSASkillContext: corrupt context at %s — starting fresh", path
            )
            return cls(study_name=study_name)


class CSASkillBase(ABC):
    """
    Abstract base for all 8 CSA scientific skill classes.

    Subclasses implement invoke() and domain-specific methods that
    read/write self.context. All methods must fail silently — log
    warnings and return empty/default values rather than raising.

    Usage pattern in skills_integration.py:
        ctx = CSASkillContext.load(study_name, output_dir)
        result = MySkill(context=ctx).my_method(...)
        ctx.save(output_dir)
    """

    def __init__(self, context: CSASkillContext) -> None:
        self.context = context
        self._log = logging.getLogger(self.__class__.__name__)

    def load_context(self, study_name: str, output_dir: Path) -> None:
        """Replace current context by loading from disk."""
        self.context = CSASkillContext.load(study_name, Path(output_dir))

    def save_context(self, output_dir: Path) -> None:
        """Persist current context to disk."""
        self.context.save(Path(output_dir))

    @abstractmethod
    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Primary entry point. Returns result string.
        Must never raise — catch all exceptions and return empty string.
        """
        ...
