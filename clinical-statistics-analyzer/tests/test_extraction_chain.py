"""Integration tests for ExtractionChain cascading strategy."""

import pytest

from crf_pipeline.extractors.extraction_chain import ExtractionChain
from crf_pipeline.extractors.regex_extractor import RegexExtractor
from crf_pipeline.extractors.template_extractor import TemplateExtractor
from crf_pipeline.models.extraction_result import ExtractionResult
from crf_pipeline.models.field_definition import FieldDefinition
from crf_pipeline.processors.base import DocumentResult


@pytest.fixture
def doc_result(sample_document_text):
    """DocumentResult with sample text."""
    return DocumentResult(
        file_path="test.pdf",
        file_name="test.pdf",
        hospital="Test Hospital",
        is_scanned=False,
        text=sample_document_text,
    )


@pytest.fixture
def chain():
    """ExtractionChain with regex and template extractors."""
    return ExtractionChain(
        extractors=[
            RegexExtractor(),
            TemplateExtractor(),
        ],
        min_confidence=0.5,
    )


def _make_field(variable, crf_field, field_type="string",
                extraction_method="regex", patterns=None):
    return FieldDefinition(
        variable=variable,
        crf_field=crf_field,
        field_type=field_type,
        extraction_method=extraction_method,
        section="test",
        patterns=patterns or [],
    )


class TestCascadingExtraction:
    """Test extraction chain cascading behavior."""

    def test_regex_success_skips_template(self, chain, doc_result):
        """If regex succeeds with high confidence, template is not needed."""
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"Age[:\s]*(\d+)"])
        result = chain.extract_field(field, doc_result)
        assert result.value is not None
        assert result.confidence >= 0.5
        assert result.method == "regex"

    def test_no_match_returns_best(self, chain, doc_result):
        """If no extractor meets threshold, return best result."""
        field = _make_field("nonexistent", "Nonexistent Field",
                            patterns=[r"ZZZZZ_NO_MATCH"])
        result = chain.extract_field(field, doc_result)
        assert result.confidence < 0.5

    def test_all_fail_returns_zero_confidence(self, chain, doc_result):
        """If all extractors fail, return confidence 0."""
        field = _make_field("xyz", "XYZ Field", extraction_method="template",
                            patterns=[r"ZZZZZ"])
        result = chain.extract_field(field, doc_result)
        assert result.confidence == 0.0


class TestExtractAll:
    """Test batch extraction of multiple fields."""

    def test_extracts_multiple_fields(self, chain, doc_result):
        fields = [
            _make_field("age", "Age", "numeric", patterns=[r"Age[:\s]*(\d+)"]),
            _make_field("wbc1", "WBC", "numeric", patterns=[r"WBC[:\s]*(\d+\.?\d*)"]),
            _make_field("case_no", "Case number", "string",
                        patterns=[r"Case Number[:\s]*([A-Z]+-\d{3})"]),
        ]
        results = chain.extract_all(fields, doc_result)
        assert len(results) == 3
        # All should have values
        for r in results:
            assert isinstance(r, ExtractionResult)
            assert r.variable in ("age", "wbc1", "case_no")

    def test_no_none_in_results(self, chain, doc_result):
        """extract_all should never return None placeholders."""
        fields = [
            _make_field("age", "Age", "numeric", patterns=[r"Age[:\s]*(\d+)"]),
            _make_field("missing", "Missing", patterns=[r"ZZZZZ"]),
        ]
        results = chain.extract_all(fields, doc_result)
        assert None not in results
        assert all(isinstance(r, ExtractionResult) for r in results)


class TestMinConfidenceThreshold:
    """Test min_confidence threshold behavior."""

    def test_high_threshold_cascades(self, doc_result):
        chain = ExtractionChain(
            extractors=[RegexExtractor()],
            min_confidence=0.95,  # Higher than regex's 0.90
        )
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"Age[:\s]*(\d+)"])
        result = chain.extract_field(field, doc_result)
        # Regex returns 0.90 which is < 0.95, so best_result returned
        assert result.confidence == 0.90

    def test_low_threshold_accepts(self, doc_result):
        chain = ExtractionChain(
            extractors=[RegexExtractor()],
            min_confidence=0.5,
        )
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"Age[:\s]*(\d+)"])
        result = chain.extract_field(field, doc_result)
        assert result.confidence == 0.90
        assert result.value == 65
