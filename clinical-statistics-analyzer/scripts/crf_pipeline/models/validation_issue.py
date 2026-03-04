"""Validation data models for CRF data quality checking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation problem found in a patient record."""

    record_id: str
    field: str
    severity: ValidationSeverity
    message: str
    rule_id: Optional[str] = None
    actual_value: Any = None
    expected_value: Any = None


@dataclass
class ValidationResult:
    """Aggregated validation results across a dataset."""

    total_records: int = 0
    valid_records: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(
            1 for i in self.issues if i.severity == ValidationSeverity.ERROR
        )

    @property
    def warning_count(self) -> int:
        return sum(
            1 for i in self.issues if i.severity == ValidationSeverity.WARNING
        )

    @property
    def completeness(self) -> float:
        """Percentage of valid records."""
        if self.total_records == 0:
            return 0.0
        return (self.valid_records / self.total_records) * 100.0
