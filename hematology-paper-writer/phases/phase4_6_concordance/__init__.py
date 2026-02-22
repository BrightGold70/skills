"""
Phase 4.6: Concordance/Verification Module

Provides reference verification and concordance checking.
Delegates to tools/pubmed_verifier.py for core functionality.
"""

from tools.pubmed_verifier import (
    PubMedVerifier,
    BatchReferenceVerifier,
    verify_reference,
    verify_references,
)

__all__ = [
    "PubMedVerifier",
    "BatchReferenceVerifier",
    "verify_reference",
    "verify_references",
]
