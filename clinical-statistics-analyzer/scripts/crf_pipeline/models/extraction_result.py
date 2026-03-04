"""ExtractionResult dataclass for per-field extraction output."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ExtractionResult:
    """Result of extracting a single field from a document."""

    variable: str              # SPSS variable name
    value: Any                 # Extracted value (typed: int, float, str, date str)
    raw_value: Optional[str]   # Original text before type conversion
    confidence: float          # 0.0 - 1.0
    method: str                # "regex" | "template" | "llm" | "ocr" | "manual"
    source_file: str           # File path
    source_page: Optional[int] # Page number (1-indexed), None for DOCX
    error: Optional[str] = None  # Error message if extraction failed

    @property
    def needs_review(self) -> bool:
        """Flag for human review if confidence < 0.5 or extraction failed."""
        return self.confidence < 0.5 or self.error is not None
