"""
Hematology Journal Specifications Package
Provides journal formatting and submission guidelines for hematology manuscripts.
"""

from .journal_loader import (
    load_specs,
    get_required_sections,
    format_reference,
    check_compliance,
    get_journal_list,
    compare_journals,
    Manuscript,
)

__all__ = [
    'load_specs',
    'get_required_sections',
    'format_reference',
    'check_compliance',
    'get_journal_list',
    'compare_journals',
    'Manuscript',
]
