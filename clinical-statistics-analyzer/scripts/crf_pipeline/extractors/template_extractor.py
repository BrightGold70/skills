"""Coordinate-based extraction using label proximity."""

import logging
from typing import Dict, List, Optional

from ..models.extraction_result import ExtractionResult
from ..models.field_definition import FieldDefinition
from ..processors.base import CoordinateItem
from .base import FieldExtractorBase

logger = logging.getLogger(__name__)


class TemplateExtractor(FieldExtractorBase):
    """Coordinate-based extraction using label proximity. Confidence: 0.70."""

    def __init__(self, spss_mapping: Optional[Dict] = None,
                 proximity_threshold: float = 50.0):
        self.spss_mapping = spss_mapping or {}
        self.proximity_threshold = proximity_threshold

    def extract(self, field: FieldDefinition,
                text: str,
                coords: Optional[List[CoordinateItem]] = None,
                source_file: str = "",
                source_page: Optional[int] = None) -> ExtractionResult:
        """Find field label in coordinates, read adjacent text items."""
        if not coords:
            return ExtractionResult(
                variable=field.variable,
                value=None,
                raw_value=None,
                confidence=0.0,
                method="template",
                source_file=source_file,
                source_page=source_page,
                error="No coordinates available",
            )

        label = field.crf_field.lower()
        label_items = [
            c for c in coords
            if label in c.text.lower() or field.variable.lower() in c.text.lower()
        ]

        if not label_items:
            return ExtractionResult(
                variable=field.variable,
                value=None,
                raw_value=None,
                confidence=0.0,
                method="template",
                source_file=source_file,
                source_page=source_page,
                error="Label not found in coordinates",
            )

        label_item = label_items[0]
        value_item = self._find_adjacent_value(label_item, coords)

        if value_item is None:
            return ExtractionResult(
                variable=field.variable,
                value=None,
                raw_value=None,
                confidence=0.0,
                method="template",
                source_file=source_file,
                source_page=source_page,
                error="No adjacent value found",
            )

        raw_value = value_item.text.strip()
        value = raw_value

        if field.sps_code and field.variable in self.spss_mapping:
            mapping = self.spss_mapping[field.variable]
            if raw_value in mapping:
                value = mapping[raw_value]

        return ExtractionResult(
            variable=field.variable,
            value=value,
            raw_value=raw_value,
            confidence=0.70,
            method="template",
            source_file=source_file,
            source_page=source_page,
        )

    def can_extract(self, field: FieldDefinition) -> bool:
        """True if extraction_method is 'template'."""
        return field.extraction_method == "template"

    def _find_adjacent_value(self, label: CoordinateItem,
                             coords: List[CoordinateItem]) -> Optional[CoordinateItem]:
        """Find the closest text item to the right or below the label."""
        candidates = []
        for item in coords:
            if item is label or not item.text.strip():
                continue
            if item.page != label.page:
                continue
            dx = item.x - (label.x + label.width)
            dy = item.y - label.y

            # Right of label (same row)
            if 0 < dx < self.proximity_threshold and abs(dy) < label.height:
                candidates.append((dx, item))
            # Below label (same column)
            elif abs(item.x - label.x) < self.proximity_threshold and 0 < dy < self.proximity_threshold:
                candidates.append((dy + 1000, item))  # Prefer right over below

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
