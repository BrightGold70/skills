"""Fuzzy string matching utilities for CRF variable name resolution."""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from thefuzz import fuzz

    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logger.debug("thefuzz not installed; fuzzy matching disabled")


def is_available() -> bool:
    """Check if fuzzywuzzy is installed."""
    return FUZZY_AVAILABLE


def fuzzy_match(
    value: str,
    choices: List[str],
    threshold: int = 60,
) -> Tuple[Optional[str], int]:
    """Find the best fuzzy match for a value among choices.

    Args:
        value: String to match.
        choices: Candidate strings.
        threshold: Minimum score (0-100) to accept a match.

    Returns:
        (best_match, score) or (None, 0) if no match above threshold.
    """
    if not FUZZY_AVAILABLE:
        return None, 0

    if not value or not choices:
        return None, 0

    best_match = None
    best_score = 0

    for choice in choices:
        score = fuzz.ratio(value.lower().strip(), choice.lower().strip())
        if score > best_score:
            best_score = score
            best_match = choice

    if best_score >= threshold:
        return best_match, best_score

    return None, 0
