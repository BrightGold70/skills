"""Field extractor abstract base class."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.extraction_result import ExtractionResult
from ..models.field_definition import FieldDefinition
from ..processors.base import CoordinateItem


class FieldExtractorBase(ABC):
    """Base class for field extraction strategies."""

    @abstractmethod
    def extract(self, field: FieldDefinition,
                text: str,
                coords: Optional[List[CoordinateItem]] = None,
                source_file: str = "",
                source_page: Optional[int] = None) -> ExtractionResult:
        """Extract a single field value from document content."""

    @abstractmethod
    def can_extract(self, field: FieldDefinition) -> bool:
        """Return True if this extractor supports the given field."""
