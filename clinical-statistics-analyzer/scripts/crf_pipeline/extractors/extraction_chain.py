"""Cascading extraction strategy across multiple extractors."""

import logging
from typing import List, Optional

from ..models.extraction_result import ExtractionResult
from ..models.field_definition import FieldDefinition
from ..processors.base import DocumentResult
from .base import FieldExtractorBase
from .llm_extractor import LLMExtractor
from .ocr_postprocessor import OCRPostprocessor

logger = logging.getLogger(__name__)


class ExtractionChain:
    """Orchestrates cascading extraction strategy across multiple extractors."""

    def __init__(self, extractors: List[FieldExtractorBase],
                 ocr_postprocessor: Optional[OCRPostprocessor] = None,
                 min_confidence: float = 0.5):
        self.extractors = extractors
        self.ocr_postprocessor = ocr_postprocessor
        self.min_confidence = min_confidence

    def extract_field(self, field: FieldDefinition,
                      doc_result: DocumentResult) -> ExtractionResult:
        """Try each extractor in order until one returns confidence >= min_confidence."""
        text = doc_result.text
        if self.ocr_postprocessor and doc_result.is_scanned:
            text = self.ocr_postprocessor.clean(text)

        best_result = None

        for extractor in self.extractors:
            if not extractor.can_extract(field):
                continue

            result = extractor.extract(
                field=field,
                text=text,
                coords=doc_result.text_with_coords or None,
                source_file=doc_result.file_path,
                source_page=None,
            )

            if result.confidence >= self.min_confidence:
                return result

            if best_result is None or result.confidence > best_result.confidence:
                best_result = result

        if best_result is not None:
            return best_result

        return ExtractionResult(
            variable=field.variable,
            value=None,
            raw_value=None,
            confidence=0.0,
            method="none",
            source_file=doc_result.file_path,
            source_page=None,
            error="All extractors failed",
        )

    def extract_all(self, fields: List[FieldDefinition],
                    doc_result: DocumentResult) -> List[ExtractionResult]:
        """Extract all fields from a document.

        LLM fields are batched for cost efficiency.
        """
        text = doc_result.text
        if self.ocr_postprocessor and doc_result.is_scanned:
            text = self.ocr_postprocessor.clean(text)

        results = []
        llm_fields = []

        for field in fields:
            # Try non-LLM extractors first
            result = self._try_non_llm(field, text, doc_result)
            if result.confidence >= self.min_confidence:
                results.append(result)
            elif field.extraction_method == "llm":
                llm_fields.append(field)
                results.append(None)  # Placeholder
            else:
                # Still try LLM as last resort
                llm_fields.append(field)
                results.append(None)

        # Batch LLM extraction
        if llm_fields:
            llm_extractor = self._get_llm_extractor()
            if llm_extractor:
                batch_results = llm_extractor.extract_batch(
                    llm_fields, text, source_file=doc_result.file_path
                )
                batch_idx = 0
                for i, r in enumerate(results):
                    if r is None:
                        results[i] = batch_results[batch_idx]
                        batch_idx += 1

        # Fill any remaining None placeholders
        for i, r in enumerate(results):
            if r is None:
                results[i] = ExtractionResult(
                    variable=fields[i].variable,
                    value=None, raw_value=None, confidence=0.0,
                    method="none", source_file=doc_result.file_path,
                    source_page=None, error="No extractor succeeded",
                )

        return results

    def _try_non_llm(self, field: FieldDefinition, text: str,
                     doc_result: DocumentResult) -> ExtractionResult:
        """Try non-LLM extractors in order."""
        best = None
        for extractor in self.extractors:
            if isinstance(extractor, LLMExtractor):
                continue
            if not extractor.can_extract(field):
                continue
            result = extractor.extract(
                field=field, text=text,
                coords=doc_result.text_with_coords or None,
                source_file=doc_result.file_path, source_page=None,
            )
            if result.confidence >= self.min_confidence:
                return result
            if best is None or result.confidence > best.confidence:
                best = result

        return best or ExtractionResult(
            variable=field.variable, value=None, raw_value=None,
            confidence=0.0, method="none",
            source_file=doc_result.file_path, source_page=None,
        )

    def _get_llm_extractor(self) -> Optional[LLMExtractor]:
        for ext in self.extractors:
            if isinstance(ext, LLMExtractor):
                return ext
        return None
