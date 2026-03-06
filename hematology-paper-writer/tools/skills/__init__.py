"""
tools/skills — Scientific Skills Integration Layer

Re-exports SkillBase, SkillContext, and all 12 scientific skill classes.
"""

from ._base import SkillBase, SkillContext

# Week 2 — Core manuscript skills
from .hypothesis_generator import HypothesisGenerator
from .scientific_brainstormer import ScientificBrainstormer
from .research_lookup import ResearchLookup
from .statistical_analyst import StatisticalAnalyst
from .scientific_writer import ScientificWriter

# Week 3 — Critical analysis and writing skills
from .critical_thinker import CriticalThinker
from .peer_reviewer import PeerReviewer
from .academic_writer import AcademicWriter

# Week 4 — Visualization, dissemination, and grant skills
from .scientific_visualizer import ScientificVisualizer
from .scientific_schematist import ScientificSchematist
from .slide_generator import SlideGenerator
from .grant_writer import GrantWriter
from .content_researcher import ContentResearcher

# Classification validation (hpw-classification-validator)
from .classification_validator import ClassificationValidator

__all__ = [
    "SkillBase",
    "SkillContext",
    # Week 2
    "HypothesisGenerator",
    "ScientificBrainstormer",
    "ResearchLookup",
    "StatisticalAnalyst",
    "ScientificWriter",
    # Week 3
    "CriticalThinker",
    "PeerReviewer",
    "AcademicWriter",
    # Week 4
    "ScientificVisualizer",
    "ScientificSchematist",
    "SlideGenerator",
    "GrantWriter",
    "ContentResearcher",
    # Classification validation
    "ClassificationValidator",
]
