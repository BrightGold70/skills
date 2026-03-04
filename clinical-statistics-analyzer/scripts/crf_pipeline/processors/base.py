"""Document processor abstract base class and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class CoordinateItem:
    """Text item with position information."""

    page: int           # 1-indexed
    text: str
    x: float
    y: float
    width: float
    height: float
    font: Optional[str] = None
    conf: Optional[int] = None  # OCR confidence (tesseract)


@dataclass
class DocumentResult:
    """Output from document processing."""

    file_path: str
    file_name: str
    hospital: str
    is_scanned: bool
    text: str                                          # Full extracted text
    text_by_page: List[str] = field(default_factory=list)  # Per-page text
    text_with_coords: List[CoordinateItem] = field(default_factory=list)
    format: str = "pdf"                                # "pdf" | "docx" | "xlsx"
    error: Optional[str] = None


class DocumentProcessor(ABC):
    """Base class for document processors."""

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Return True if this processor handles the given file type."""

    @abstractmethod
    def process(self, file_path: str, hospital: str = "") -> DocumentResult:
        """Extract text and metadata from a document."""

    @abstractmethod
    def process_directory(self, input_dir: str) -> List[DocumentResult]:
        """Process all supported files in a directory tree.

        Subdirectories are treated as hospital identifiers.
        """
