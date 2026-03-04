"""PDF processor with auto-detection of scanned vs digital."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import CoordinateItem, DocumentProcessor, DocumentResult

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class PDFProcessor(DocumentProcessor):
    """PDF processor with auto-detection of scanned vs digital."""

    def __init__(self, ocr_lang: str = "eng+kor", ocr_dpi: int = 300):
        self.ocr_lang = ocr_lang
        self.ocr_dpi = ocr_dpi

    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".pdf"

    def is_scanned(self, file_path: str) -> bool:
        """True if extracted text < 100 chars (heuristic)."""
        if not PYMUPDF_AVAILABLE:
            return True
        try:
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return len(text.strip()) < 100
        except Exception as e:
            logger.error("Error checking if PDF is scanned: %s", e)
            return True

    def process(self, file_path: str, hospital: str = "") -> DocumentResult:
        """Process a single PDF. Routes to OCR or direct extraction."""
        scanned = self.is_scanned(file_path)
        result = DocumentResult(
            file_path=file_path,
            file_name=os.path.basename(file_path),
            hospital=hospital,
            is_scanned=scanned,
            text="",
            format="pdf",
        )

        try:
            if scanned:
                result.text = self._extract_text_ocr(file_path)
                result.text_with_coords = self._extract_coords_ocr(file_path)
            else:
                result.text = self._extract_text_digital(file_path)
                result.text_by_page = self._extract_text_by_page(file_path)
                result.text_with_coords = self._extract_coords_digital(file_path)
        except Exception as e:
            logger.error("Error processing PDF %s: %s", file_path, e)
            result.error = str(e)

        return result

    def process_directory(self, input_dir: str) -> List[DocumentResult]:
        """Walk subdirectories (hospital -> patient PDFs)."""
        results = []
        input_path = Path(input_dir)

        for hospital_dir in sorted(input_path.iterdir()):
            if not hospital_dir.is_dir():
                continue
            hospital_name = hospital_dir.name
            logger.info("Processing hospital: %s", hospital_name)

            for pdf_file in sorted(hospital_dir.glob("*.pdf")):
                logger.info("  Processing: %s", pdf_file.name)
                results.append(self.process(str(pdf_file), hospital=hospital_name))

        return results

    # --- Private helpers ---

    def _extract_text_digital(self, file_path: str) -> str:
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF required for text extraction")
        doc = fitz.open(file_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text

    def _extract_text_by_page(self, file_path: str) -> List[str]:
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF required for text extraction")
        doc = fitz.open(file_path)
        pages = [page.get_text() for page in doc]
        doc.close()
        return pages

    def _extract_coords_digital(self, file_path: str) -> List[CoordinateItem]:
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF required for coordinate extraction")
        items = []
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            items.append(CoordinateItem(
                                page=page_num + 1,
                                text=span.get("text", "").strip(),
                                x=bbox[0],
                                y=bbox[1],
                                width=bbox[2] - bbox[0],
                                height=bbox[3] - bbox[1],
                                font=span.get("font", ""),
                            ))
        doc.close()
        return items

    def _extract_text_ocr(self, file_path: str) -> str:
        if not (TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE):
            raise ImportError("pytesseract and pdf2image required for OCR")
        images = convert_from_path(file_path, dpi=self.ocr_dpi)
        parts = []
        for page_num, image in enumerate(images):
            text = pytesseract.image_to_string(image, lang=self.ocr_lang)
            parts.append(f"\n--- Page {page_num + 1} ---\n{text}")
        return "".join(parts)

    def _extract_coords_ocr(self, file_path: str) -> List[CoordinateItem]:
        if not (TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE):
            raise ImportError("pytesseract and pdf2image required for OCR")
        images = convert_from_path(file_path, dpi=self.ocr_dpi)
        items = []
        for page_num, image in enumerate(images):
            data = pytesseract.image_to_data(
                image, lang=self.ocr_lang,
                output_type=pytesseract.Output.DICT,
            )
            for i, text in enumerate(data["text"]):
                if text.strip():
                    items.append(CoordinateItem(
                        page=page_num + 1,
                        text=text.strip(),
                        x=data["left"][i],
                        y=data["top"][i],
                        width=data["width"][i],
                        height=data["height"][i],
                        conf=data["conf"][i],
                    ))
        return items
