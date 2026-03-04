"""Unit tests for QualityReporter with confidence breakdown."""

import pytest

from crf_pipeline.models.extraction_result import ExtractionResult
from crf_pipeline.models.patient_record import PatientRecord
from crf_pipeline.models.validation_issue import (
    ValidationIssue, ValidationResult, ValidationSeverity,
)
from crf_pipeline.validators.quality_reporter import QualityReporter


def _make_record(fields: dict, case_no: str = "T-001") -> PatientRecord:
    """Create PatientRecord with given field data.

    fields: {variable: (value, confidence, method)}
    """
    record = PatientRecord(
        case_no=case_no,
        hospital="Test",
        source_file="test.pdf",
        disease="aml",
    )
    for var, (val, conf, method) in fields.items():
        record.results[var] = ExtractionResult(
            variable=var, value=val, raw_value=str(val) if val else None,
            confidence=conf, method=method,
            source_file="test.pdf", source_page=None,
        )
    return record


@pytest.fixture
def reporter():
    return QualityReporter()


@pytest.fixture
def sample_records():
    return [
        _make_record({
            "age": (65, 0.9, "regex"),
            "gender": (1, 0.9, "regex"),
            "wbc1": (45.2, 0.9, "regex"),
            "cause_death": ("relapse", 0.7, "llm"),
            "name": ("K.H.", 0.3, "ocr"),  # Low confidence
        }, case_no="T-001"),
        _make_record({
            "age": (55, 0.9, "regex"),
            "gender": (2, 0.9, "regex"),
            "wbc1": (12.0, 0.7, "template"),
            "cause_death": (None, 0.0, "none"),  # Failed
        }, case_no="T-002"),
    ]


@pytest.fixture
def sample_validation():
    result = ValidationResult(total_records=2, valid_records=1)
    result.issues = [
        ValidationIssue(
            record_id="T-002", field="case_no",
            severity=ValidationSeverity.ERROR,
            message="Required field 'case_no' is missing",
            rule_id="REQUIRED",
        ),
        ValidationIssue(
            record_id="T-001", field="gender",
            severity=ValidationSeverity.WARNING,
            message="gender='Unknown' not in allowed values",
            rule_id="CATEGORICAL",
        ),
    ]
    return result


class TestReportGeneration:
    def test_report_is_markdown(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert report.startswith("# CRF Data Quality Report")
        assert "## Summary" in report

    def test_summary_section(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "Total records" in report
        assert "Valid records" in report

    def test_confidence_section(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "Extraction Confidence" in report
        assert "Mean confidence" in report

    def test_method_breakdown(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "By Extraction Method" in report
        assert "regex" in report

    def test_section_breakdown(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "By Section" in report

    def test_confidence_distribution(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "Confidence Distribution" in report
        assert "0.8-1.0" in report

    def test_review_fields_listed(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "Fields Needing Review" in report
        # T-001 "name" has confidence 0.3 < 0.5, and T-002 "cause_death" has 0.0
        assert "name" in report

    def test_validation_issues(self, reporter, sample_validation, sample_records):
        report = reporter.generate_report(sample_validation, sample_records)
        assert "Validation Issues" in report
        assert "Errors" in report
        assert "REQUIRED" in report

    def test_empty_records(self, reporter):
        validation = ValidationResult(total_records=0)
        report = reporter.generate_report(validation, [])
        assert "Total records" in report
        assert "0" in report


class TestConfidenceByMethod:
    def test_groups_by_method(self, sample_records):
        stats = QualityReporter._confidence_by_method(sample_records)
        assert "regex" in stats
        assert stats["regex"]["count"] > 0
        assert 0.0 <= stats["regex"]["mean"] <= 1.0

    def test_counts_low_confidence(self, sample_records):
        stats = QualityReporter._confidence_by_method(sample_records)
        # "none" method has confidence 0.0
        if "none" in stats:
            assert stats["none"]["low"] > 0


class TestConfidenceBySection:
    def test_groups_by_section(self, sample_records):
        stats = QualityReporter._confidence_by_section(sample_records)
        # age and gender should be in demographics or known section
        assert len(stats) > 0
