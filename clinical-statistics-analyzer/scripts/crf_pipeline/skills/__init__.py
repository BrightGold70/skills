"""
scripts/crf_pipeline/skills — CSA Scientific Skills Integration Layer

Re-exports CSASkillBase, CSASkillContext, and all 8 scientific skill classes.

Usage:
    from scripts.crf_pipeline.skills import (
        CSASkillContext, ROutputInterpreter, StatisticalAnalyst
    )
"""

from ._base import CSASkillBase, CSASkillContext

# Tier 1 — Pre-analysis skills
from .statistical_analyst import StatisticalAnalyst
from .hypothesis_generator import HypothesisGenerator
from .critical_thinker import CriticalThinker

# Tier 1 — Post-analysis skills
from .scientific_writer import ScientificWriter
from .content_researcher import ContentResearcher

# Tier 2 — CSA-specific skills
from .r_output_interpreter import ROutputInterpreter
from .eln_guideline_mapper import ELNGuidelineMapper
from .protocol_consistency import ProtocolConsistencyChecker

__all__ = [
    "CSASkillBase",
    "CSASkillContext",
    # Tier 1 pre
    "StatisticalAnalyst",
    "HypothesisGenerator",
    "CriticalThinker",
    # Tier 1 post
    "ScientificWriter",
    "ContentResearcher",
    # Tier 2
    "ROutputInterpreter",
    "ELNGuidelineMapper",
    "ProtocolConsistencyChecker",
]
