"""Deterministic regex-based field extraction."""

import logging
import re
from typing import Dict, List, Optional

from ..models.extraction_result import ExtractionResult
from ..models.field_definition import FieldDefinition
from ..processors.base import CoordinateItem
from .base import FieldExtractorBase

logger = logging.getLogger(__name__)


class RegexExtractor(FieldExtractorBase):
    """Deterministic regex-based extraction. Confidence: 0.90 on match."""

    def __init__(self, spss_mapping: Optional[Dict] = None):
        self.spss_mapping = spss_mapping or {}

    def extract(self, field: FieldDefinition,
                text: str,
                coords: Optional[List[CoordinateItem]] = None,
                source_file: str = "",
                source_page: Optional[int] = None) -> ExtractionResult:
        """Try field.patterns in order, then auto-generated bilingual patterns."""
        patterns = list(field.patterns)
        if not patterns:
            patterns = self._create_patterns_from_field(field)

        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw_value = match.group(1) if match.groups() else match.group(0)
                    value = self._convert_value(field, raw_value)
                    return ExtractionResult(
                        variable=field.variable,
                        value=value,
                        raw_value=raw_value,
                        confidence=0.90,
                        method="regex",
                        source_file=source_file,
                        source_page=source_page,
                    )
            except re.error as e:
                logger.warning("Invalid regex pattern '%s': %s", pattern, e)

        return ExtractionResult(
            variable=field.variable,
            value=None,
            raw_value=None,
            confidence=0.0,
            method="regex",
            source_file=source_file,
            source_page=source_page,
            error="No pattern matched",
        )

    def can_extract(self, field: FieldDefinition) -> bool:
        """True for all fields (always attempted as first strategy)."""
        return True

    def _create_patterns_from_field(self, field: FieldDefinition) -> List[str]:
        """Auto-generate regex patterns from field name (bilingual)."""
        name = field.crf_field
        escaped = re.escape(name)
        return [
            rf"{escaped}\s*:?\s*(.+?)(?:\s*$|\s{{2,}})",
        ]

    def _convert_value(self, field: FieldDefinition, raw_value: str):
        """Convert raw string to typed value based on field definition."""
        raw_value = raw_value.strip()

        if field.sps_code and field.variable in self.spss_mapping:
            mapping = self.spss_mapping[field.variable]
            if raw_value in mapping:
                return mapping[raw_value]

        if field.field_type == "numeric":
            try:
                if "." in raw_value:
                    return float(raw_value)
                return int(raw_value)
            except ValueError:
                return raw_value

        return raw_value
