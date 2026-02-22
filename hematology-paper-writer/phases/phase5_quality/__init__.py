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
