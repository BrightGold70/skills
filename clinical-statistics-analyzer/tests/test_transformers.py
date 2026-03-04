"""Tests for data transformers (column_mapper, date_calculator, value_recoder)."""

import numpy as np
import pandas as pd
import pytest

from scripts.crf_pipeline.transformers.column_mapper import ColumnMapper
from scripts.crf_pipeline.transformers.date_calculator import DateCalculator, _parse_dates
from scripts.crf_pipeline.transformers.value_recoder import ValueRecoder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_crf_df():
    """DataFrame mimicking CRF pipeline output with original variable names."""
    return pd.DataFrame({
        "case_no": ["AML-001", "AML-002", "AML-003"],
        "age": [55, 68, 42],
        "gender": ["Male", "Female", "Male"],
        "alive": [1, 2, 1],
        "induction_date": ["2025-01-15", "2025-02-01", "2025-03-10"],
        "date_death": [None, "2025-08-15", None],
        "date_last_fu": ["2025-12-01", "2025-08-15", "2025-11-20"],
        "relapse_date": [None, "2025-06-01", None],
        "FLT3ITD": ["Positive", "Negative", "Positive"],
        "NPM1": ["Negative", "Positive", "Negative"],
        "induction_ct": ["AD 45", "AD 90", "AI"],
        "cr_achieved": ["CR", "NR", "CR"],
    })


@pytest.fixture
def aml_config():
    """Merged AML config with column_mapping and derived_columns."""
    return {
        "column_mapping": {
            "case_no": "Patient_ID",
            "age": "Age",
            "gender": "Sex",
            "induction_ct": "Treatment",
            "cr_achieved": "Response",
            "FLT3ITD": "FLT3_ITD",
            "NPM1": "NPM1_mut",
            "induction_date": "Treatment_Start_Date",
        },
        "derived_columns": {
            "OS_months": {
                "type": "date_diff_months",
                "from": "induction_date",
                "to": "date_death",
                "censor": "date_last_fu",
            },
            "PFS_months": {
                "type": "date_diff_months",
                "from": "induction_date",
                "to": "relapse_date",
                "censor": "date_last_fu",
            },
            "OS_status": {
                "type": "recode",
                "source": "alive",
                "mapping": {"1": 0, "2": 1},
            },
            "Age_group": {
                "type": "bin",
                "source": "age",
                "bins": [0, 60, 200],
                "labels": ["<60", ">=60"],
            },
        },
    }


# ---------------------------------------------------------------------------
# ColumnMapper tests
# ---------------------------------------------------------------------------

class TestColumnMapper:
    def test_basic_rename(self, sample_crf_df, aml_config):
        mapper = ColumnMapper()
        result = mapper.transform(sample_crf_df.copy(), aml_config)

        assert "Patient_ID" in result.columns
        assert "Age" in result.columns
        assert "Sex" in result.columns
        assert "Treatment" in result.columns
        assert "FLT3_ITD" in result.columns
        # Original names should be gone
        assert "case_no" not in result.columns
        assert "FLT3ITD" not in result.columns

    def test_preserves_unmapped_columns(self, sample_crf_df, aml_config):
        mapper = ColumnMapper()
        result = mapper.transform(sample_crf_df.copy(), aml_config)

        # Columns not in mapping should remain
        assert "alive" in result.columns
        assert "date_last_fu" in result.columns

    def test_empty_mapping(self, sample_crf_df):
        mapper = ColumnMapper()
        config = {"column_mapping": {}}
        result = mapper.transform(sample_crf_df.copy(), config)
        assert list(result.columns) == list(sample_crf_df.columns)

    def test_no_mapping_key(self, sample_crf_df):
        mapper = ColumnMapper()
        result = mapper.transform(sample_crf_df.copy(), {})
        assert list(result.columns) == list(sample_crf_df.columns)

    def test_mapping_with_missing_columns(self, sample_crf_df):
        mapper = ColumnMapper()
        config = {"column_mapping": {"nonexistent": "NewName", "age": "Age"}}
        result = mapper.transform(sample_crf_df.copy(), config)
        assert "Age" in result.columns
        assert "nonexistent" not in result.columns
        assert "NewName" not in result.columns

    def test_data_values_preserved(self, sample_crf_df, aml_config):
        mapper = ColumnMapper()
        result = mapper.transform(sample_crf_df.copy(), aml_config)
        assert list(result["Patient_ID"]) == ["AML-001", "AML-002", "AML-003"]
        assert list(result["Age"]) == [55, 68, 42]


# ---------------------------------------------------------------------------
# DateCalculator tests
# ---------------------------------------------------------------------------

class TestDateCalculator:
    def test_date_diff_months(self, sample_crf_df, aml_config):
        calc = DateCalculator()
        result = calc.transform(sample_crf_df.copy(), aml_config)

        assert "OS_months" in result.columns
        assert "PFS_months" in result.columns

        # Patient 2 died: 2025-02-01 → 2025-08-15 ≈ 6.4 months
        os_months_p2 = result.loc[1, "OS_months"]
        assert 6.0 < os_months_p2 < 7.0

        # Patient 1 censored: 2025-01-15 → 2025-12-01 ≈ 10.5 months
        os_months_p1 = result.loc[0, "OS_months"]
        assert 10.0 < os_months_p1 < 11.0

    def test_date_diff_with_censor(self, sample_crf_df, aml_config):
        calc = DateCalculator()
        result = calc.transform(sample_crf_df.copy(), aml_config)

        # Patient 2 relapsed: 2025-02-01 → 2025-06-01 ≈ 3.9 months
        pfs_p2 = result.loc[1, "PFS_months"]
        assert 3.5 < pfs_p2 < 4.5

        # Patient 1 no relapse, censored: 2025-01-15 → 2025-12-01 ≈ 10.5 months
        pfs_p1 = result.loc[0, "PFS_months"]
        assert 10.0 < pfs_p1 < 11.0

    def test_missing_from_column(self):
        calc = DateCalculator()
        df = pd.DataFrame({"date_death": ["2025-08-01"]})
        config = {
            "derived_columns": {
                "OS_months": {
                    "type": "date_diff_months",
                    "from": "nonexistent",
                    "to": "date_death",
                }
            }
        }
        result = calc.transform(df, config)
        assert "OS_months" not in result.columns

    def test_various_date_formats(self):
        df = pd.DataFrame({
            "start": ["15/01/2025", "01/02/2025"],
            "end": ["15/07/2025", "01/08/2025"],
        })
        parsed = _parse_dates(df["start"])
        assert parsed.notna().all()

    def test_empty_config(self, sample_crf_df):
        calc = DateCalculator()
        result = calc.transform(sample_crf_df.copy(), {})
        assert list(result.columns) == list(sample_crf_df.columns)

    def test_skips_non_date_diff_types(self, sample_crf_df):
        calc = DateCalculator()
        config = {
            "derived_columns": {
                "OS_status": {"type": "recode", "source": "alive", "mapping": {"1": 0}},
            }
        }
        result = calc.transform(sample_crf_df.copy(), config)
        assert "OS_status" not in result.columns  # recode is not handled by DateCalculator


# ---------------------------------------------------------------------------
# ValueRecoder tests
# ---------------------------------------------------------------------------

class TestValueRecoder:
    def test_recode_alive_to_os_status(self, sample_crf_df, aml_config):
        recoder = ValueRecoder()
        result = recoder.transform(sample_crf_df.copy(), aml_config)

        assert "OS_status" in result.columns
        # alive=1 → OS_status=0, alive=2 → OS_status=1
        assert list(result["OS_status"]) == [0, 1, 0]

    def test_bin_age_group(self, sample_crf_df, aml_config):
        recoder = ValueRecoder()
        result = recoder.transform(sample_crf_df.copy(), aml_config)

        assert "Age_group" in result.columns
        # 55 → <60, 68 → >=60, 42 → <60
        assert str(result.loc[0, "Age_group"]) == "<60"
        assert str(result.loc[1, "Age_group"]) == ">=60"
        assert str(result.loc[2, "Age_group"]) == "<60"

    def test_recode_missing_source(self):
        recoder = ValueRecoder()
        df = pd.DataFrame({"x": [1, 2, 3]})
        config = {
            "derived_columns": {
                "Y": {"type": "recode", "source": "nonexistent", "mapping": {"1": "a"}},
            }
        }
        result = recoder.transform(df, config)
        assert "Y" not in result.columns

    def test_bin_missing_source(self):
        recoder = ValueRecoder()
        df = pd.DataFrame({"x": [1, 2, 3]})
        config = {
            "derived_columns": {
                "Group": {"type": "bin", "source": "nonexistent", "bins": [0, 5], "labels": ["low"]},
            }
        }
        result = recoder.transform(df, config)
        assert "Group" not in result.columns

    def test_recode_string_and_numeric_keys(self):
        recoder = ValueRecoder()
        df = pd.DataFrame({"status": [1, 2, "Alive", "Dead"]})
        config = {
            "derived_columns": {
                "OS_status": {
                    "type": "recode",
                    "source": "status",
                    "mapping": {"1": 0, "2": 1, "Alive": 0, "Dead": 1},
                }
            }
        }
        result = recoder.transform(df, config)
        assert list(result["OS_status"]) == [0, 1, 0, 1]

    def test_empty_config(self, sample_crf_df):
        recoder = ValueRecoder()
        result = recoder.transform(sample_crf_df.copy(), {})
        assert list(result.columns) == list(sample_crf_df.columns)


# ---------------------------------------------------------------------------
# Integration: full transform chain
# ---------------------------------------------------------------------------

class TestTransformChain:
    """Test the full transform chain: derive → rename."""

    def test_full_transform_order(self, sample_crf_df, aml_config):
        """Derived columns use original names, then column_mapper renames."""
        calc = DateCalculator()
        recoder = ValueRecoder()
        mapper = ColumnMapper()

        # Step 1: Derive (uses original CRF names)
        df = calc.transform(sample_crf_df.copy(), aml_config)
        df = recoder.transform(df, aml_config)

        # Derived columns should exist with R-ready names
        assert "OS_months" in df.columns
        assert "OS_status" in df.columns
        assert "Age_group" in df.columns

        # Original columns still present
        assert "case_no" in df.columns
        assert "age" in df.columns

        # Step 2: Rename (CRF → R names)
        df = mapper.transform(df, aml_config)

        # Renamed columns
        assert "Patient_ID" in df.columns
        assert "Age" in df.columns
        assert "Treatment" in df.columns

        # Derived columns still present
        assert "OS_months" in df.columns
        assert "OS_status" in df.columns

        # Original CRF names gone (those in mapping)
        assert "case_no" not in df.columns
        assert "induction_ct" not in df.columns

    def test_r_ready_output_has_expected_columns(self, sample_crf_df, aml_config):
        """The final DataFrame should have all columns R scripts expect."""
        calc = DateCalculator()
        recoder = ValueRecoder()
        mapper = ColumnMapper()

        df = calc.transform(sample_crf_df.copy(), aml_config)
        df = recoder.transform(df, aml_config)
        df = mapper.transform(df, aml_config)

        # Key columns for R analysis scripts
        expected = ["Patient_ID", "Age", "Sex", "Treatment", "OS_months", "OS_status"]
        for col in expected:
            assert col in df.columns, f"Missing expected column: {col}"
