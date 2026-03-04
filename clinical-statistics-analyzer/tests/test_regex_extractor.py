"""Unit tests for RegexExtractor."""

import pytest

from crf_pipeline.extractors.regex_extractor import RegexExtractor
from crf_pipeline.models.field_definition import FieldDefinition


@pytest.fixture
def extractor():
    return RegexExtractor(spss_mapping={
        "gender": {"Male": 1, "Female": 2, "M": 1, "F": 2},
        "alive": {"Alive": 1, "Dead": 2},
    })


def _make_field(variable, crf_field, field_type="string",
                patterns=None, sps_code=False, values=None):
    return FieldDefinition(
        variable=variable,
        crf_field=crf_field,
        field_type=field_type,
        extraction_method="regex",
        section="test",
        sps_code=sps_code,
        patterns=patterns or [],
        values=values or [],
    )


class TestRegexExtraction:
    """Test regex matching and value extraction."""

    def test_age_english(self, extractor, sample_document_text):
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"Age[:\s]*(\d+)"])
        result = extractor.extract(field, sample_document_text)
        assert result.value == 65
        assert result.confidence == 0.90
        assert result.method == "regex"

    def test_age_korean(self, extractor):
        text = "나이: 55세"
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"나이[:\s]*(\d+)"])
        result = extractor.extract(field, text)
        assert result.value == 55

    def test_wbc_numeric(self, extractor, sample_document_text):
        field = _make_field("wbc1", "WBC at diagnosis", "numeric",
                            patterns=[r"WBC[:\s]*(\d+\.?\d*)"])
        result = extractor.extract(field, sample_document_text)
        assert result.value == 45.2

    def test_case_number(self, extractor, sample_document_text):
        field = _make_field("case_no", "Case number", "string",
                            patterns=[r"Case Number[:\s]*([A-Z]+-\d{3})"])
        result = extractor.extract(field, sample_document_text)
        assert result.value == "SAPH-001"

    def test_multiple_patterns_first_wins(self, extractor):
        text = "Patient Age: 70 years"
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"does_not_match", r"Age[:\s]*(\d+)"])
        result = extractor.extract(field, text)
        assert result.value == 70

    def test_no_match_returns_zero_confidence(self, extractor):
        field = _make_field("age", "Age", "numeric",
                            patterns=[r"ZZZZZ_NO_MATCH"])
        result = extractor.extract(field, "Some random text")
        assert result.value is None
        assert result.confidence == 0.0
        assert result.error is not None

    def test_spss_mapping(self, extractor, sample_document_text):
        field = _make_field("gender", "Gender", "categorical",
                            patterns=[r"Gender[:\s]*(Male|Female)"],
                            sps_code=True)
        result = extractor.extract(field, sample_document_text)
        assert result.value == 1  # Male → 1

    def test_auto_pattern_from_field_name(self, extractor):
        text = "Hemoglobin: 9.5"
        field = _make_field("hb1", "Hemoglobin", "numeric")
        result = extractor.extract(field, text)
        # Auto-generated pattern from "Hemoglobin"
        assert result.value is not None

    def test_invalid_regex_handled(self, extractor):
        field = _make_field("test", "Test", patterns=[r"[invalid("])
        result = extractor.extract(field, "test text")
        # Should not raise, returns no match
        assert result.confidence == 0.0


class TestCanExtract:
    def test_always_true(self, extractor):
        field = _make_field("any", "Any field")
        assert extractor.can_extract(field) is True


class TestValueConversion:
    def test_integer_conversion(self, extractor):
        field = _make_field("age", "Age", "numeric", patterns=[r"(\d+)"])
        result = extractor.extract(field, "65")
        assert result.value == 65
        assert isinstance(result.value, int)

    def test_float_conversion(self, extractor):
        field = _make_field("wbc1", "WBC", "numeric", patterns=[r"(\d+\.\d+)"])
        result = extractor.extract(field, "45.2")
        assert result.value == 45.2
        assert isinstance(result.value, float)

    def test_string_preserved(self, extractor):
        field = _make_field("name", "Name", "string", patterns=[r"Name[:\s]*(\S+)"])
        result = extractor.extract(field, "Name: Kim")
        assert result.value == "Kim"
        assert isinstance(result.value, str)
