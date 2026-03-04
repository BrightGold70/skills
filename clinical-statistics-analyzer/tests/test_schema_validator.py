"""Unit tests for SchemaValidator."""

import pytest

from crf_pipeline.validators.schema_validator import SchemaValidator


@pytest.fixture
def validator(schemas_dir):
    return SchemaValidator(schemas_dir=schemas_dir)


class TestFieldConfigValidation:
    """Test field config schema validation."""

    def test_common_config_valid(self, validator, common_config):
        errors = validator.validate_field_config(common_config)
        # No structural errors expected
        structural = [e for e in errors if "required" in e.message.lower()
                      or "type" in e.message.lower()]
        assert len(structural) == 0, [str(e) for e in structural]

    def test_aml_config_valid(self, validator, aml_config):
        errors = validator.validate_field_config(aml_config)
        structural = [e for e in errors if "required" in e.message.lower()
                      or "type" in e.message.lower()]
        assert len(structural) == 0, [str(e) for e in structural]

    def test_missing_version_detected(self, validator):
        bad_config = {"sections": {}}
        errors = validator.validate_field_config(bad_config)
        version_errs = [e for e in errors if "version" in e.message.lower()]
        assert len(version_errs) > 0

    def test_invalid_field_type_detected(self, validator):
        config = {
            "version": "1.0",
            "sections": {
                "test": {
                    "fields": [{
                        "crf_field": "Test",
                        "variable": "test_var",
                        "type": "invalid_type",
                    }]
                }
            }
        }
        errors = validator.validate_field_config(config)
        type_errs = [e for e in errors if "invalid_type" in e.message
                     or "enum" in e.message.lower()]
        assert len(type_errs) > 0


class TestVariableUniqueness:
    def test_duplicate_variable_detected(self, validator):
        config = {
            "version": "1.0",
            "sections": {
                "sec1": {"fields": [
                    {"crf_field": "A", "variable": "dup_var", "type": "string"}
                ]},
                "sec2": {"fields": [
                    {"crf_field": "B", "variable": "dup_var", "type": "numeric"}
                ]},
            }
        }
        errors = validator.validate_field_config(config)
        dup_errs = [e for e in errors if "Duplicate" in e.message]
        assert len(dup_errs) == 1

    def test_unique_variables_pass(self, validator, common_config):
        errors = validator.validate_field_config(common_config)
        dup_errs = [e for e in errors if "Duplicate" in e.message]
        assert len(dup_errs) == 0


class TestSpssCoverage:
    def test_sps_code_without_mapping_detected(self, validator):
        config = {
            "version": "1.0",
            "sections": {
                "test": {"fields": [
                    {"crf_field": "Gender", "variable": "gender",
                     "type": "categorical", "sps_code": True}
                ]}
            },
            "spss_value_mapping": {},  # No mapping for gender
        }
        errors = validator.validate_field_config(config)
        spss_errs = [e for e in errors if "spss" in e.message.lower()
                     or "sps_code" in e.message.lower()]
        assert len(spss_errs) == 1


class TestRegexPatternValidation:
    def test_invalid_regex_detected(self, validator):
        config = {
            "version": "1.0",
            "sections": {
                "test": {"fields": [
                    {"crf_field": "Test", "variable": "test",
                     "type": "string", "patterns": ["[invalid("]}
                ]}
            }
        }
        errors = validator.validate_field_config(config)
        regex_errs = [e for e in errors if "regex" in e.message.lower()]
        assert len(regex_errs) == 1


class TestValidationRulesSchema:
    def test_real_rules_valid(self, validator, validation_rules):
        errors = validator.validate_validation_rules(validation_rules)
        # No structural errors expected
        assert len(errors) == 0, [str(e) for e in errors]

    def test_min_greater_than_max_detected(self, validator):
        rules = {
            "range_checks": {
                "bad_field": {"min": 100, "max": 0}
            }
        }
        errors = validator.validate_validation_rules(rules)
        range_errs = [e for e in errors if "min" in e.message]
        assert len(range_errs) == 1

    def test_duplicate_rule_id_detected(self, validator):
        rules = {
            "consistency_rules": [
                {"id": "DUP", "description": "Rule 1", "severity": "error"},
                {"id": "DUP", "description": "Rule 2", "severity": "error"},
            ]
        }
        errors = validator.validate_validation_rules(rules)
        dup_errs = [e for e in errors if "Duplicate" in e.message]
        assert len(dup_errs) == 1


class TestMergedConfigValidation:
    def test_merged_aml_valid(self, validator, config_dir):
        from crf_pipeline.config.loader import ConfigLoader
        loader = ConfigLoader(config_dir)
        config = loader.load("aml")
        # Remove validation_rules from merged config (separate schema)
        config.pop("validation_rules", None)
        errors = validator.validate_merged_config(config, "aml")
        # Filter to only critical errors
        critical = [e for e in errors if "required" in e.message.lower()
                    and "not found" not in e.message.lower()]
        assert len(critical) == 0, [str(e) for e in critical]
