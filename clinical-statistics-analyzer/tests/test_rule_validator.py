"""Unit tests for RuleValidator."""

import pytest

from crf_pipeline.models.patient_record import PatientRecord
from crf_pipeline.models.extraction_result import ExtractionResult
from crf_pipeline.models.validation_issue import ValidationSeverity
from crf_pipeline.validators.rule_validator import RuleValidator


@pytest.fixture
def shared_rules(validation_rules):
    """Use real validation_rules.json."""
    return validation_rules


@pytest.fixture
def validator(shared_rules):
    """RuleValidator with shared rules, no disease override."""
    return RuleValidator(shared_rules)


@pytest.fixture
def aml_validator(shared_rules):
    """RuleValidator with AML-specific rules."""
    return RuleValidator(shared_rules, disease="aml")


@pytest.fixture
def hct_validator(shared_rules):
    """RuleValidator with HCT-specific rules."""
    return RuleValidator(shared_rules, disease="hct")


def _make_record(data: dict) -> PatientRecord:
    """Create a PatientRecord from flat data dict."""
    record = PatientRecord(
        case_no=data.get("case_no", "TEST-001"),
        hospital="Test Hospital",
        source_file="test.pdf",
        disease="aml",
    )
    for var, val in data.items():
        record.results[var] = ExtractionResult(
            variable=var,
            value=val,
            raw_value=str(val) if val is not None else None,
            confidence=0.9,
            method="regex",
            source_file="test.pdf",
            source_page=None,
        )
    return record


class TestCR001_CRAchievedDate:
    """CR achieved → CR date must be present."""

    def test_cr_yes_with_date_passes(self, validator):
        record = _make_record({
            "case_no": "T-001", "age": "65", "gender": "Male", "alive": "Alive",
            "cr_achieved": "Yes", "cr_date": "2025-02-28",
        })
        issues = validator.validate_record(record)
        cr001_issues = [i for i in issues if i.rule_id == "CR001"]
        assert len(cr001_issues) == 0

    def test_cr_yes_without_date_error(self, validator):
        record = _make_record({
            "case_no": "T-001", "age": "65", "gender": "Male", "alive": "Alive",
            "cr_achieved": "Yes", "cr_date": None,
        })
        issues = validator.validate_record(record)
        cr001_issues = [i for i in issues if i.rule_id == "CR001"]
        assert len(cr001_issues) == 1
        assert cr001_issues[0].severity == ValidationSeverity.ERROR

    def test_cr_no_without_date_passes(self, validator):
        record = _make_record({
            "case_no": "T-001", "age": "65", "gender": "Male", "alive": "Alive",
            "cr_achieved": "No",
        })
        issues = validator.validate_record(record)
        cr001_issues = [i for i in issues if i.rule_id == "CR001"]
        assert len(cr001_issues) == 0


class TestCR002_DeathDate:
    """Dead → death date must be present."""

    def test_dead_without_date_error(self, validator):
        record = _make_record({
            "case_no": "T-002", "age": "65", "gender": "Male",
            "alive": "Dead", "date_death": None,
        })
        issues = validator.validate_record(record)
        cr002 = [i for i in issues if i.rule_id == "CR002"]
        assert len(cr002) == 1

    def test_dead_with_date_passes(self, validator):
        record = _make_record({
            "case_no": "T-002", "age": "65", "gender": "Male",
            "alive": "Dead", "date_death": "2025-06-15",
        })
        issues = validator.validate_record(record)
        cr002 = [i for i in issues if i.rule_id == "CR002"]
        assert len(cr002) == 0


class TestCR003_PediatricWarning:
    """Age < 18 → warning."""

    def test_age_under_18_warning(self, validator):
        record = _make_record({
            "case_no": "T-003", "age": "15", "gender": "Male", "alive": "Alive",
        })
        issues = validator.validate_record(record)
        cr003 = [i for i in issues if i.rule_id == "CR003"]
        assert len(cr003) == 1
        assert cr003[0].severity == ValidationSeverity.WARNING

    def test_age_18_no_warning(self, validator):
        record = _make_record({
            "case_no": "T-003", "age": "18", "gender": "Male", "alive": "Alive",
        })
        issues = validator.validate_record(record)
        cr003 = [i for i in issues if i.rule_id == "CR003"]
        assert len(cr003) == 0


class TestCR004_DeathAfterDiagnosis:
    """Death date must be after diagnosis date."""

    def test_death_before_diagnosis_error(self, validator):
        record = _make_record({
            "case_no": "T-004", "age": "65", "gender": "Male", "alive": "Dead",
            "date_death": "2024-12-01", "reg_date": "2025-01-15",
        })
        issues = validator.validate_record(record)
        cr004 = [i for i in issues if i.rule_id == "CR004"]
        assert len(cr004) == 1

    def test_death_after_diagnosis_passes(self, validator):
        record = _make_record({
            "case_no": "T-004", "age": "65", "gender": "Male", "alive": "Dead",
            "date_death": "2025-06-15", "reg_date": "2025-01-15",
        })
        issues = validator.validate_record(record)
        cr004 = [i for i in issues if i.rule_id == "CR004"]
        assert len(cr004) == 0


class TestCR005_CRAfterInduction:
    """CR date must be after induction date."""

    def test_cr_before_induction_error(self, validator):
        record = _make_record({
            "case_no": "T-005", "age": "65", "gender": "Male", "alive": "Alive",
            "cr_achieved": "Yes",
            "cr_date": "2025-01-10", "induction_date": "2025-01-20",
        })
        issues = validator.validate_record(record)
        cr005 = [i for i in issues if i.rule_id == "CR005"]
        assert len(cr005) == 1

    def test_cr_after_induction_passes(self, validator):
        record = _make_record({
            "case_no": "T-005", "age": "65", "gender": "Male", "alive": "Alive",
            "cr_achieved": "Yes",
            "cr_date": "2025-02-28", "induction_date": "2025-01-20",
        })
        issues = validator.validate_record(record)
        cr005 = [i for i in issues if i.rule_id == "CR005"]
        assert len(cr005) == 0


class TestCR006_HCTAfterCR:
    """HCT date must be after CR date."""

    def test_hct_before_cr_error(self, validator):
        record = _make_record({
            "case_no": "T-006", "age": "65", "gender": "Male", "alive": "Alive",
            "hct_date": "2025-01-01", "cr_date": "2025-02-28",
        })
        issues = validator.validate_record(record)
        cr006 = [i for i in issues if i.rule_id == "CR006"]
        assert len(cr006) == 1


class TestCR007_RelapseAfterCR:
    """Relapse date must be after CR date."""

    def test_relapse_before_cr_error(self, validator):
        record = _make_record({
            "case_no": "T-007", "age": "65", "gender": "Male", "alive": "Alive",
            "relapse_date": "2025-01-01", "cr_date": "2025-02-28",
        })
        issues = validator.validate_record(record)
        cr007 = [i for i in issues if i.rule_id == "CR007"]
        assert len(cr007) == 1


class TestDiseaseSpecificRules:
    """Test disease-specific validation rules."""

    def test_aml_blast_required(self, aml_validator):
        record = _make_record({
            "case_no": "T-AML", "age": "65", "gender": "Male", "alive": "Alive",
            # blast1 missing
        })
        issues = aml_validator.validate_record(record)
        aml_r01 = [i for i in issues if i.rule_id == "AML-R01"]
        assert len(aml_r01) == 1

    def test_aml_blast_present_passes(self, aml_validator):
        record = _make_record({
            "case_no": "T-AML", "age": "65", "gender": "Male", "alive": "Alive",
            "blast1": "75",
        })
        issues = aml_validator.validate_record(record)
        aml_r01 = [i for i in issues if i.rule_id == "AML-R01"]
        assert len(aml_r01) == 0

    def test_hct_conditioning_required(self, hct_validator):
        record = _make_record({
            "case_no": "T-HCT", "age": "50", "gender": "Male", "alive": "Alive",
            # conditioning missing
        })
        issues = hct_validator.validate_record(record)
        hct_r01 = [i for i in issues if i.rule_id == "HCT-R01"]
        assert len(hct_r01) == 1

    def test_hct_engraft_after_hct(self, hct_validator):
        record = _make_record({
            "case_no": "T-HCT", "age": "50", "gender": "Male", "alive": "Alive",
            "conditioning": "Bu/Cy",
            "donor_type": "MSD",
            "engraft_anc_date": "2025-01-01",  # Before HCT
            "hct_date": "2025-02-01",
        })
        issues = hct_validator.validate_record(record)
        hct_r03 = [i for i in issues if i.rule_id == "HCT-R03"]
        assert len(hct_r03) == 1


class TestValidDatasetPasses:
    """Valid complete record should produce no errors."""

    def test_valid_record_no_errors(self, validator, sample_patient_data):
        record = _make_record(sample_patient_data)
        issues = validator.validate_record(record)
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0

    def test_validate_dataset(self, validator, sample_patient_data):
        records = [_make_record(sample_patient_data)]
        result = validator.validate_dataset(records)
        assert result.total_records == 1
        assert result.valid_records == 1


class TestRequiredFields:
    """Test required field checks."""

    def test_missing_required_field_error(self, validator):
        record = _make_record({
            "age": "65", "gender": "Male", "alive": "Alive",
            # case_no missing (required)
        })
        issues = validator.validate_record(record)
        required_issues = [i for i in issues if i.rule_id == "REQUIRED"]
        assert any(i.field == "case_no" for i in required_issues)


class TestRangeChecks:
    """Test numeric range validation."""

    def test_age_out_of_range(self, validator):
        record = _make_record({
            "case_no": "T-R", "age": "150", "gender": "Male", "alive": "Alive",
        })
        issues = validator.validate_record(record)
        range_issues = [i for i in issues if i.rule_id == "RANGE" and i.field == "age"]
        assert len(range_issues) == 1

    def test_age_in_range(self, validator):
        record = _make_record({
            "case_no": "T-R", "age": "65", "gender": "Male", "alive": "Alive",
        })
        issues = validator.validate_record(record)
        range_issues = [i for i in issues if i.rule_id == "RANGE" and i.field == "age"]
        assert len(range_issues) == 0


class TestCategoricalChecks:
    """Test categorical value validation."""

    def test_invalid_gender_warning(self, validator):
        record = _make_record({
            "case_no": "T-C", "age": "65", "gender": "Unknown", "alive": "Alive",
        })
        issues = validator.validate_record(record)
        cat_issues = [i for i in issues if i.rule_id == "CATEGORICAL" and i.field == "gender"]
        assert len(cat_issues) == 1
        assert cat_issues[0].severity == ValidationSeverity.WARNING
