"""
Phase 5: Quality Analysis Module

Provides manuscript quality assessment and compliance checking.
Delegates to tools/quality_analyzer.py for core functionality.
"""

from tools.quality_analyzer import (
    ManuscriptQualityAnalyzer,
    QualityReport,
    QualityScore,
    QualityCategory,
)

__all__ = [
    "ManuscriptQualityAnalyzer",
    "QualityReport",
    "QualityScore",
    "QualityCategory",
]


# ── Scientific Skills Integration (additive, opt-in) ──────────────────────────

def integrate_skills_phase5(
    project_name: str,
    project_dir,
    text: str = "",
    study_type: str = "cohort",
) -> None:
    """
    Invoke scientific skills for Phase 5 (Quality Analysis).

    Runs CriticalThinker (full evaluation) and persists quality scores to
    SkillContext. Fails silently on any error.

    Args:
        project_name: Manuscript project name
        project_dir: Project directory (Path or str)
        text: Manuscript text to evaluate
        study_type: rct | cohort | retrospective | case_series | systematic_review
    """
    try:
        from pathlib import Path
        from tools.skills import SkillContext, CriticalThinker

        ctx = SkillContext.load(project_name, Path(project_dir))

        if text:
            CriticalThinker(context=ctx).evaluate(
                text=text,
                study_type=study_type,
                focus="all",
            )

        ctx.save(Path(project_dir))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Phase 5 skill integration failed: %s", exc)
