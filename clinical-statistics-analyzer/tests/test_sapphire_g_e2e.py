"""End-to-end tests using anonymized SAPPHIRE-G AML data (27 patients).

Validates the full pipeline: parse → transform → R-ready CSV, verifying
that SPSS value labels, binary numeric columns, and column mappings
all produce correct output matching published manuscript values.
"""

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from scripts.crf_pipeline.transformers.column_mapper import ColumnMapper
from scripts.crf_pipeline.transformers.date_calculator import DateCalculator
from scripts.crf_pipeline.transformers.value_recoder import ValueRecoder

FIXTURES = Path(__file__).parent / "fixtures"
MOCK_CSV = FIXTURES / "sapphire_g_mock.csv"
EXPECTED_JSON = FIXTURES / "sapphire_g_expected.json"

# Use the SAPPHIRE-G study config (in fixtures for isolation from main AML config)
SAPPHIRE_CONFIG = FIXTURES / "sapphire_g_aml_fields.json"


def _load_config():
    """Load the AML fields config."""
    with open(SAPPHIRE_CONFIG, encoding="utf-8") as f:
        return json.load(f)


def _load_expected():
    """Load expected values."""
    with open(EXPECTED_JSON, encoding="utf-8") as f:
        return json.load(f)


def _run_transform(df, config):
    """Run the full transform chain on a DataFrame."""
    date_calc = DateCalculator()
    value_recoder = ValueRecoder()
    column_mapper = ColumnMapper()

    df = date_calc.transform(df, config)
    df = value_recoder.transform(df, config)
    df = column_mapper.transform(df, config)
    return df


class TestSapphireGTransform:
    """Test the data transformation pipeline with SAPPHIRE-G mock data."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.df = pd.read_csv(MOCK_CSV)
        self.config = _load_config()
        self.expected = _load_expected()
        self.transformed = _run_transform(self.df.copy(), self.config)

    def test_row_count(self):
        """Verify no rows are lost during transformation."""
        assert len(self.transformed) == self.expected["n_patients"]

    def test_essential_columns_present(self):
        """FR-01: Transform creates both labeled and numeric columns."""
        expected_cols = self.expected["transform_checks"]["columns_present"]
        actual_cols = self.transformed.columns.tolist()
        missing = [c for c in expected_cols if c not in actual_cols]
        assert missing == [], f"Missing columns: {missing}"

    def test_sex_distribution(self):
        """Verify Sex column has correct label distribution."""
        if "Sex" not in self.transformed.columns:
            pytest.skip("Sex column not in transformed data")
        dist = self.transformed["Sex"].value_counts().to_dict()
        expected_dist = self.expected["transform_checks"]["sex_distribution"]
        for label, count in expected_dist.items():
            assert dist.get(label, 0) == count, (
                f"Sex={label}: expected {count}, got {dist.get(label, 0)}"
            )

    def test_treatment_distribution(self):
        """Verify Treatment column has correct label distribution."""
        if "Treatment" not in self.transformed.columns:
            pytest.skip("Treatment column not in transformed data")
        dist = self.transformed["Treatment"].value_counts().to_dict()
        expected_dist = self.expected["transform_checks"]["treatment_distribution"]
        for label, count in expected_dist.items():
            assert dist.get(label, 0) == count, (
                f"Treatment={label}: expected {count}, got {dist.get(label, 0)}"
            )

    def test_response_numeric_column_exists(self):
        """FR-01: Binary _numeric columns are created for response variables."""
        for col in ["Response_numeric", "CR_numeric", "cCR_numeric"]:
            assert col in self.transformed.columns, f"Missing binary column: {col}"

    def test_response_numeric_values(self):
        """FR-01: _numeric columns contain only 0, 1, or NaN."""
        for col in ["Response_numeric", "CR_numeric", "cCR_numeric"]:
            if col not in self.transformed.columns:
                continue
            valid_vals = {0.0, 1.0}
            actual_vals = set(self.transformed[col].dropna().unique())
            assert actual_vals.issubset(valid_vals), (
                f"{col} has invalid values: {actual_vals - valid_vals}"
            )

    def test_response_counts_match_manuscript(self):
        """Verify ORR, CR, cCR counts match manuscript values."""
        expected_counts = self.expected["transform_checks"]["response_counts"]

        if "Response_numeric" in self.transformed.columns:
            orr_count = int(self.transformed["Response_numeric"].sum())
            assert orr_count == expected_counts["ORR"], (
                f"ORR: expected {expected_counts['ORR']}, got {orr_count}"
            )

        if "CR_numeric" in self.transformed.columns:
            cr_count = int(self.transformed["CR_numeric"].sum())
            assert cr_count == expected_counts["CR"], (
                f"CR: expected {expected_counts['CR']}, got {cr_count}"
            )

        if "cCR_numeric" in self.transformed.columns:
            ccr_count = int(self.transformed["cCR_numeric"].sum())
            assert ccr_count == expected_counts["cCR"], (
                f"cCR: expected {expected_counts['cCR']}, got {ccr_count}"
            )

    def test_os_status_derived(self):
        """Verify OS_status is correctly derived from alive column."""
        if "OS_status" not in self.transformed.columns:
            pytest.skip("OS_status not in transformed data")
        # alive=1 → OS_status=0 (alive), alive=2 → OS_status=1 (dead)
        valid_vals = {0, 1, 0.0, 1.0}
        actual_vals = set(self.transformed["OS_status"].dropna().unique())
        assert actual_vals.issubset(valid_vals), (
            f"OS_status has invalid values: {actual_vals}"
        )

    def test_age_group_derived(self):
        """Verify Age_group is correctly binned."""
        if "Age_group" not in self.transformed.columns:
            pytest.skip("Age_group not in transformed data")
        valid_groups = {"<60", ">=60"}
        actual_groups = set(self.transformed["Age_group"].dropna().astype(str).unique())
        assert actual_groups.issubset(valid_groups), (
            f"Unexpected Age_group values: {actual_groups - valid_groups}"
        )


class TestValueRecoderSPSSLabels:
    """Unit tests for the SPSS label application in ValueRecoder."""

    def test_binary_numeric_creation(self):
        """_apply_spss_labels creates _numeric column for binary outcomes."""
        df = pd.DataFrame({"ORR": [1.0, 2.0, 1.0, 2.0, 1.0]})
        config = {
            "spss_value_mapping": {
                "ORR": {"1.0": "ORR", "2.0": "Non-ORR"}
            },
            "column_mapping": {},
        }
        recoder = ValueRecoder()
        result = recoder._apply_spss_labels(df, config)
        assert "ORR_numeric" in result.columns
        assert list(result["ORR_numeric"]) == [1.0, 0.0, 1.0, 0.0, 1.0]
        assert list(result["ORR"]) == ["ORR", "Non-ORR", "ORR", "Non-ORR", "ORR"]

    def test_non_binary_no_numeric(self):
        """_apply_spss_labels does NOT create _numeric for >2 categories."""
        df = pd.DataFrame({"Sal1": [1.0, 2.0, 0.0]})
        config = {
            "spss_value_mapping": {
                "Sal1": {"0.0": "Unknown", "1.0": "ICT", "2.0": "LIT"}
            },
            "column_mapping": {},
        }
        recoder = ValueRecoder()
        result = recoder._apply_spss_labels(df, config)
        assert "Sal1_numeric" not in result.columns
        assert list(result["Sal1"]) == ["ICT", "LIT", "Unknown"]

    def test_positive_keyword_detection(self):
        """Positive keyword correctly identifies the '1' value for binary coding."""
        df = pd.DataFrame({"CR": [1.0, 2.0, 1.0]})
        config = {
            "spss_value_mapping": {
                "CR": {"1.0": "CR", "2.0": "Non-CR"}
            },
            "column_mapping": {},
        }
        recoder = ValueRecoder()
        result = recoder._apply_spss_labels(df, config)
        assert "CR_numeric" in result.columns
        assert list(result["CR_numeric"]) == [1.0, 0.0, 1.0]

    def test_mapped_column_name(self):
        """Labels applied to R-mapped column name when present."""
        df = pd.DataFrame({"Response": [1.0, 2.0]})
        config = {
            "spss_value_mapping": {
                "ORR": {"1.0": "ORR", "2.0": "Non-ORR"}
            },
            "column_mapping": {"ORR": "Response"},
        }
        recoder = ValueRecoder()
        result = recoder._apply_spss_labels(df, config)
        assert "Response_numeric" in result.columns
        assert result["Response"].tolist() == ["ORR", "Non-ORR"]


class TestOrchestratorResolveArgs:
    """Unit tests for the enhanced _resolve_args with template variables."""

    def test_template_variable_substitution(self):
        """Template vars {outcome_var}, {disease} are resolved from profile defaults."""
        from scripts.crf_pipeline.orchestrator import AnalysisOrchestrator

        config_dir = str(
            Path(__file__).parent.parent / "scripts" / "crf_pipeline" / "config"
        )
        # Use a temp output dir
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            orch = AnalysisOrchestrator(
                config_dir=config_dir,
                disease="aml",
                output_dir=tmp,
            )

            args = ["{dataset}", "{outcome_var}", "--disease", "{disease}"]
            resolved = orch._resolve_args(args, "/tmp/test.csv")

            assert resolved[0] == "/tmp/test.csv"
            assert resolved[1] == "Response_numeric"  # AML default
            assert resolved[2] == "--disease"
            assert resolved[3] == "aml"

    def test_overrides_take_precedence(self):
        """Variant overrides replace profile defaults."""
        from scripts.crf_pipeline.orchestrator import AnalysisOrchestrator

        config_dir = str(
            Path(__file__).parent.parent / "scripts" / "crf_pipeline" / "config"
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            orch = AnalysisOrchestrator(
                config_dir=config_dir,
                disease="aml",
                output_dir=tmp,
            )

            args = ["{dataset}", "{time_var}", "{status_var}", "--disease", "{disease}"]
            overrides = {"time_var": "PFS_months", "status_var": "PFS_status"}
            resolved = orch._resolve_args(args, "/tmp/test.csv", overrides=overrides)

            assert resolved[1] == "PFS_months"
            assert resolved[2] == "PFS_status"
