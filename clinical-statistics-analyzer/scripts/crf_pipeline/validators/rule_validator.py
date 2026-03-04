"""Rule-based validator implementing CR001-CR007 consistency checks."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.patient_record import PatientRecord
from ..models.validation_issue import (
    ValidationIssue, ValidationResult, ValidationSeverity,
)

logger = logging.getLogger(__name__)

DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
    "%m-%d-%Y", "%m/%d/%Y", "%Y.%m.%d", "%d.%m.%Y",
]


class RuleValidator:
    """Validates extracted records against consistency and range rules."""

    def __init__(self, validation_rules: Dict, disease: str = ""):
        self.range_checks = validation_rules.get("range_checks", {})
        self.consistency_rules = validation_rules.get("consistency_rules", [])
        self.required_fields = validation_rules.get("required_fields", [])
        self.categorical_values = validation_rules.get("categorical_values", {})
        self.disease = disease

        # Add disease-specific rules to consistency rules
        disease_rules = validation_rules.get("disease_specific_rules", {})
        if disease and disease in disease_rules:
            self.consistency_rules = list(self.consistency_rules) + disease_rules[disease]

    def validate_record(self, record: PatientRecord) -> List[ValidationIssue]:
        """Run all validation checks on a single patient record."""
        issues = []
        data = record.to_flat_dict()
        record_id = record.case_no or record.source_file

        issues.extend(self._check_required(record_id, data))
        issues.extend(self._check_ranges(record_id, data))
        issues.extend(self._check_categorical(record_id, data))
        issues.extend(self._check_consistency(record_id, data))

        return issues

    def validate_dataset(self, records: List[PatientRecord]) -> ValidationResult:
        """Validate all records, aggregate results."""
        result = ValidationResult(total_records=len(records))
        for record in records:
            issues = self.validate_record(record)
            result.issues.extend(issues)
            errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
            if not errors:
                result.valid_records += 1
        return result

    def _check_required(self, record_id: str, data: Dict) -> List[ValidationIssue]:
        issues = []
        for field in self.required_fields:
            if field not in data or data[field] is None or data[field] == "":
                issues.append(ValidationIssue(
                    record_id=record_id, field=field,
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field}' is missing",
                    rule_id="REQUIRED",
                ))
        return issues

    def _check_ranges(self, record_id: str, data: Dict) -> List[ValidationIssue]:
        issues = []
        for field, spec in self.range_checks.items():
            value = data.get(field)
            if value is None:
                continue
            try:
                num_val = float(value)
                if num_val < spec["min"] or num_val > spec["max"]:
                    issues.append(ValidationIssue(
                        record_id=record_id, field=field,
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"{field}={num_val} out of range "
                            f"[{spec['min']}, {spec['max']}] {spec.get('unit', '')}"
                        ),
                        rule_id="RANGE",
                        actual_value=num_val,
                        expected_value=f"{spec['min']}-{spec['max']}",
                    ))
            except (ValueError, TypeError):
                pass
        return issues

    def _check_categorical(self, record_id: str, data: Dict) -> List[ValidationIssue]:
        issues = []
        for field, allowed in self.categorical_values.items():
            value = data.get(field)
            if value is None:
                continue
            if str(value) not in [str(v) for v in allowed]:
                issues.append(ValidationIssue(
                    record_id=record_id, field=field,
                    severity=ValidationSeverity.WARNING,
                    message=f"{field}='{value}' not in allowed values",
                    rule_id="CATEGORICAL",
                    actual_value=value,
                    expected_value=str(allowed),
                ))
        return issues

    def _check_consistency(self, record_id: str, data: Dict) -> List[ValidationIssue]:
        """Dispatch consistency rules CR001-CR007."""
        issues = []
        for rule in self.consistency_rules:
            issue = self._check_consistency_rule(rule, record_id, data)
            if issue:
                issues.append(issue)
        return issues

    def _check_consistency_rule(self, rule: Dict, record_id: str,
                                data: Dict) -> Optional[ValidationIssue]:
        rule_id = rule["id"]
        severity = ValidationSeverity(rule.get("severity", "error"))

        if rule_id == "CR001":
            cr = data.get("cr_achieved")
            if cr in ("Yes", "CR") and not data.get("cr_date"):
                return ValidationIssue(
                    record_id=record_id, field="cr_date",
                    severity=severity, message=rule["description"],
                    rule_id=rule_id,
                )

        elif rule_id == "CR002":
            alive = data.get("alive")
            if alive in ("Dead", "\uc0ac\ub9dd") and not data.get("date_death"):
                return ValidationIssue(
                    record_id=record_id, field="date_death",
                    severity=severity, message=rule["description"],
                    rule_id=rule_id,
                )

        elif rule_id == "CR003":
            age = data.get("age")
            if age is not None:
                try:
                    if float(age) < 18:
                        return ValidationIssue(
                            record_id=record_id, field="age",
                            severity=ValidationSeverity.WARNING,
                            message=rule["description"],
                            rule_id=rule_id, actual_value=age,
                        )
                except (ValueError, TypeError):
                    pass

        elif rule_id == "CR004":
            return self._check_date_order(
                record_id, data, "date_death", "reg_date", rule
            )

        elif rule_id == "CR005":
            return self._check_date_order(
                record_id, data, "cr_date", "induction_date", rule
            )

        elif rule_id == "CR006":
            return self._check_date_order(
                record_id, data, "hct_date", "cr_date", rule
            )

        elif rule_id == "CR007":
            return self._check_date_order(
                record_id, data, "relapse_date", "cr_date", rule
            )

        else:
            # Handle disease-specific rules generically
            return self._check_generic_rule(rule, record_id, data)

        return None

    def _check_generic_rule(self, rule: Dict, record_id: str,
                            data: Dict) -> Optional[ValidationIssue]:
        """Handle disease-specific rules (AML-R*, CML-R*, MDS-R*, HCT-R*)."""
        rule_id = rule["id"]
        severity = ValidationSeverity(rule.get("severity", "error"))
        condition = rule.get("condition")
        require = rule.get("require")

        # Check condition first (if present)
        if condition:
            if not self._eval_condition(condition, data):
                return None

        # Check requirement
        if require:
            # Date ordering: "field_a >= field_b"
            if ">=" in require:
                parts = require.split(">=")
                if len(parts) == 2:
                    later = parts[0].strip()
                    earlier = parts[1].strip()
                    return self._check_date_order(
                        record_id, data, later, earlier, rule
                    )

            # Required field: "field is not null"
            if "is not null" in require:
                field = require.replace("is not null", "").strip()
                if not data.get(field):
                    return ValidationIssue(
                        record_id=record_id, field=field,
                        severity=severity, message=rule["description"],
                        rule_id=rule_id,
                    )

        # Condition-only rule (warning when condition is true, no require)
        elif condition and not require:
            return ValidationIssue(
                record_id=record_id, field="",
                severity=severity, message=rule["description"],
                rule_id=rule_id,
            )

        return None

    @staticmethod
    def _eval_condition(condition: str, data: Dict) -> bool:
        """Simple condition evaluator for rule conditions."""
        # "field is not null"
        if "is not null" in condition:
            field = condition.replace("is not null", "").strip()
            return data.get(field) is not None

        # "field in [...]" (already handled by CR001/CR002)
        # For simple cases, just check if the field is truthy
        return True

    def _check_date_order(self, record_id: str, data: Dict,
                          later_field: str, earlier_field: str,
                          rule: Dict) -> Optional[ValidationIssue]:
        later = self._parse_date(data.get(later_field))
        earlier = self._parse_date(data.get(earlier_field))
        if later and earlier and later < earlier:
            return ValidationIssue(
                record_id=record_id, field=later_field,
                severity=ValidationSeverity(rule.get("severity", "error")),
                message=rule["description"],
                rule_id=rule["id"],
                actual_value=str(data.get(later_field)),
                expected_value=f">= {data.get(earlier_field)}",
            )
        return None

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None
