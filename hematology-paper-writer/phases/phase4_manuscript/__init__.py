"""
Phase 4: Manuscript Preparation Module

Provides manuscript drafting and generation capabilities.
Delegates to tools/systematic_review_workflow.py for core functionality.
"""

from tools.systematic_review_workflow import (
    SystematicReviewWorkflow,
    SystematicReviewResult,
)

__all__ = [
    "SystematicReviewWorkflow",
    "SystematicReviewResult",
]
