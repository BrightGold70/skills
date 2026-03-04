"""Temporal/date logic validator extracted from ValidationEngine (09_validate.py)."""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..models.validation_issue import ValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


class TemporalValidator:
    """
    Validates temporal/date logic in clinical trial DataFrames.

    Checks for:
    - Date sequence violations (e.g., diagnosis before treatment)
    - Future dates
    - Age/birth date consistency
    - Visit order violations per patient
    """

    DEFAULT_DATE_SEQUENCES: List[Tuple[str, str, str]] = [
        ("diagnosis_date", "treatment_start_date", "Diagnosis must precede treatment"),
        ("treatment_start_date", "response_date", "Treatment must precede response"),
        ("response_date", "relapse_date", "Response must precede relapse"),
        ("diagnosis_date", "death_date", "Diagnosis must precede death"),
        ("treatment_start_date", "death_date", "Treatment must precede death"),
    ]

    def __init__(
        self,
        date_sequences: Optional[List[Tuple[str, str, str]]] = None,
        protocol_spec: Optional[Dict] = None,
    ) -> None:
        """
        Initialize the temporal validator.

        Args:
            date_sequences: List of (earlier_col_pattern, later_col_pattern, description)
                tuples to validate. If None, DEFAULT_DATE_SEQUENCES is used.
            protocol_spec: Parsed protocol specification (reserved for future use).
        """
        self.date_sequences = date_sequences if date_sequences is not None else list(self.DEFAULT_DATE_SEQUENCES)
        self.protocol_spec = protocol_spec or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, data: pd.DataFrame) -> List[ValidationIssue]:
        """
        Run all temporal validations on a DataFrame.

        Replicates ValidationEngine._validate_temporal_logic() behaviour:
        - Detects future dates in any column whose name contains 'date' or 'dt'
        - Checks screening → baseline ordering when those columns exist
        - Checks visit order per patient
        - Checks age/birth date consistency
        - Checks DEFAULT_DATE_SEQUENCES (or caller-supplied sequences)

        Args:
            data: DataFrame containing patient data.

        Returns:
            List of ValidationIssue instances (may be empty).
        """
        issues: List[ValidationIssue] = []

        # --- column-level date checks (mirrors original loop) ---
        date_cols = [
            col for col in data.columns
            if "date" in col.lower() or "dt" in col.lower()
        ]

        for col in date_cols:
            try:
                date_series = pd.to_datetime(data[col], errors="coerce")

                # Future date check
                future_mask = date_series > pd.Timestamp.now()
                future_count = int(future_mask.sum())
                if future_count > 0:
                    logger.debug("Column '%s' has %d future date(s)", col, future_count)
                    issues.append(ValidationIssue(
                        record_id="dataset",
                        field=col,
                        severity=ValidationSeverity.WARNING,
                        message=f"Column '{col}' has {future_count} future date(s)",
                        rule_id="TEMPORAL_FUTURE",
                        actual_value=future_count,
                    ))

                # Screening → baseline sequence check
                if "screening" in col.lower():
                    baseline_col = self._find_column(
                        data.columns, ["baseline", "day1", "day 1"]
                    )
                    if baseline_col:
                        issues.extend(
                            self.validate_date_sequence(
                                data, col, baseline_col,
                                "Screening must precede baseline",
                            )
                        )

                # Visit order check
                if "visit" in col.lower():
                    issues.extend(self.validate_visit_order(data, col))

            except Exception as exc:  # noqa: BLE001
                logger.debug("Skipping temporal check on column '%s': %s", col, exc)

        # --- age / birth date consistency ---
        birth_col = self._find_column(data.columns, ["birth", "dob", "birthdate", "birth_dt"])
        age_col = self._find_column(data.columns, ["age"])

        if birth_col and age_col:
            try:
                birth_dates = pd.to_datetime(data[birth_col], errors="coerce")
                today = pd.Timestamp.now()
                calculated_age = ((today - birth_dates).dt.days / 365.25).round()
                age_diff = (calculated_age - data[age_col]).abs()
                inconsistent_count = int((age_diff > 1).sum())

                if inconsistent_count > 0:
                    logger.debug(
                        "Age/birth inconsistency in %d record(s)", inconsistent_count
                    )
                    issues.append(ValidationIssue(
                        record_id="dataset",
                        field=f"{birth_col}, {age_col}",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"Age and birth date inconsistent in "
                            f"{inconsistent_count} record(s)"
                        ),
                        rule_id="TEMPORAL_AGE_CONSISTENCY",
                        actual_value=inconsistent_count,
                    ))
            except Exception as exc:  # noqa: BLE001
                logger.debug("Age consistency check failed: %s", exc)

        # --- protocol date sequences ---
        for earlier_pattern, later_pattern, description in self.date_sequences:
            earlier_col = self._find_column(data.columns, [earlier_pattern])
            later_col = self._find_column(data.columns, [later_pattern])
            if earlier_col and later_col:
                issues.extend(
                    self.validate_date_sequence(data, earlier_col, later_col, description)
                )

        return issues

    def validate_date_sequence(
        self,
        data: pd.DataFrame,
        earlier_col: str,
        later_col: str,
        description: str,
    ) -> List[ValidationIssue]:
        """
        Validate that dates in *later_col* are not before dates in *earlier_col*.

        Replicates ValidationEngine._validate_date_sequence().

        Args:
            data: DataFrame containing patient data.
            earlier_col: Column that should contain the earlier date.
            later_col: Column that should contain the later date.
            description: Human-readable description of the expected ordering.

        Returns:
            List of ValidationIssue instances (empty when no violations found).
        """
        issues: List[ValidationIssue] = []
        try:
            dates_earlier = pd.to_datetime(data[earlier_col], errors="coerce")
            dates_later = pd.to_datetime(data[later_col], errors="coerce")

            violation_mask = dates_later < dates_earlier
            violation_count = int(violation_mask.sum())

            if violation_count > 0:
                logger.debug(
                    "Date sequence violation (%s → %s): %d record(s)",
                    earlier_col, later_col, violation_count,
                )
                issues.append(ValidationIssue(
                    record_id="dataset",
                    field=f"{earlier_col}, {later_col}",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"{description}: '{later_col}' is before '{earlier_col}' "
                        f"in {violation_count} record(s)"
                    ),
                    rule_id="TEMPORAL_SEQUENCE",
                    actual_value=violation_count,
                    expected_value=f"{earlier_col} <= {later_col}",
                ))
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "Date sequence check failed (%s, %s): %s",
                earlier_col, later_col, exc,
            )

        return issues

    def validate_visit_order(
        self,
        data: pd.DataFrame,
        visit_col: str,
    ) -> List[ValidationIssue]:
        """
        Validate that visit dates are in ascending order per patient.

        Replicates ValidationEngine._validate_visit_order().

        Args:
            data: DataFrame containing patient data.
            visit_col: Name of the visit label/type column (used for error reporting).

        Returns:
            List of ValidationIssue instances (empty when no violations found).
        """
        issues: List[ValidationIssue] = []

        patient_col = self._find_column(
            data.columns, ["subject_id", "patient_id", "patient", "scrno"]
        )
        if not patient_col:
            logger.debug("validate_visit_order: no patient ID column found, skipping")
            return issues

        date_col = self._find_column(
            data.columns, ["visit_date", "visitdt", "visit_date"]
        )
        if not date_col:
            logger.debug("validate_visit_order: no visit date column found, skipping")
            return issues

        try:
            dates = pd.to_datetime(data[date_col], errors="coerce")

            for patient, group in data.groupby(patient_col):
                patient_dates = dates[group.index]
                if not patient_dates.is_monotonic_increasing:
                    violations = int((patient_dates.diff().dt.total_seconds() < 0).sum())
                    logger.debug(
                        "Patient %s has %d visit order violation(s)",
                        patient, violations,
                    )
                    issues.append(ValidationIssue(
                        record_id=str(patient),
                        field=visit_col,
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"Patient {patient} has {violations} visit date "
                            f"sequence violation(s)"
                        ),
                        rule_id="TEMPORAL_VISIT_ORDER",
                        actual_value=violations,
                    ))
        except Exception as exc:  # noqa: BLE001
            logger.debug("Visit order check failed: %s", exc)

        return issues

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_column(columns, patterns: List[str]) -> Optional[str]:
        """
        Return the first column name whose lowercase form contains any pattern.

        Replicates ValidationEngine._find_column().

        Args:
            columns: Iterable of column names.
            patterns: Substrings to search for (case-insensitive).

        Returns:
            Matching column name, or None if no match found.
        """
        for col in columns:
            col_lower = col.lower()
            for pattern in patterns:
                if pattern.lower() in col_lower:
                    return col
        return None

