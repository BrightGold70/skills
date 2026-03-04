"""Tests for the analysis orchestrator."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from scripts.crf_pipeline.orchestrator import (
    AnalysisOrchestrator,
    AnalysisResult,
    ScriptResult,
)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "scripts" / "crf_pipeline" / "config"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


@pytest.fixture
def mock_aml_csv(tmp_path):
    """Create a mock AML patient data CSV file."""
    df = pd.DataFrame({
        "case_no": ["AML-001", "AML-002", "AML-003", "AML-004", "AML-005"],
        "age": [55, 68, 42, 71, 33],
        "gender": ["Male", "Female", "Male", "Female", "Male"],
        "alive": [1, 2, 1, 2, 1],
        "induction_date": [
            "2025-01-15", "2025-02-01", "2025-03-10", "2025-01-20", "2025-04-05",
        ],
        "date_death": [None, "2025-08-15", None, "2025-05-10", None],
        "date_last_fu": [
            "2025-12-01", "2025-08-15", "2025-11-20", "2025-05-10", "2025-12-15",
        ],
        "relapse_date": [None, "2025-06-01", None, None, "2025-09-01"],
        "FLT3ITD": ["Positive", "Negative", "Positive", "Negative", "Positive"],
        "NPM1": ["Negative", "Positive", "Negative", "Negative", "Positive"],
        "induction_ct": ["AD 45", "AD 90", "AI", "AD 45", "AD 90"],
        "cr_achieved": ["CR", "NR", "CR", "NR", "CR"],
        "wbc1": [45.2, 12.1, 88.5, 3.2, 120.0],
        "hb1": [8.5, 10.2, 7.1, 9.8, 6.5],
        "plt1": [45, 120, 22, 85, 15],
        "blast1": [75, 30, 90, 45, 85],
        "perf1": [80, 70, 90, 60, 100],
        "ECOG1": [1, 2, 0, 2, 0],
    })
    csv_path = tmp_path / "aml_test_data.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return str(out)


# ---------------------------------------------------------------------------
# AnalysisOrchestrator.transform() tests
# ---------------------------------------------------------------------------

class TestOrchestratorTransform:
    def test_transform_produces_csv(self, mock_aml_csv, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
        )
        csv_path = orch.transform(mock_aml_csv)

        assert os.path.exists(csv_path)
        assert csv_path.endswith(".csv")

        df = pd.read_csv(csv_path)
        assert len(df) == 5

    def test_transform_renames_columns(self, mock_aml_csv, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
        )
        csv_path = orch.transform(mock_aml_csv)
        df = pd.read_csv(csv_path)

        # Check renamed columns
        assert "Patient_ID" in df.columns
        assert "Age" in df.columns
        assert "Sex" in df.columns
        assert "Treatment" in df.columns

    def test_transform_creates_derived_columns(self, mock_aml_csv, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
        )
        csv_path = orch.transform(mock_aml_csv)
        df = pd.read_csv(csv_path)

        # Check derived columns
        assert "OS_months" in df.columns
        assert "OS_status" in df.columns
        assert "Age_group" in df.columns

        # Verify OS_status values (alive=1→0, alive=2→1)
        assert df.loc[0, "OS_status"] == 0  # alive=1
        assert df.loc[1, "OS_status"] == 1  # alive=2

    def test_transform_os_months_values(self, mock_aml_csv, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
        )
        csv_path = orch.transform(mock_aml_csv)
        df = pd.read_csv(csv_path)

        # Patient 2: 2025-02-01 → 2025-08-15 ≈ 6.4 months
        assert 6.0 < df.loc[1, "OS_months"] < 7.0

        # All OS_months should be positive
        assert (df["OS_months"].dropna() > 0).all()


# ---------------------------------------------------------------------------
# Script routing tests
# ---------------------------------------------------------------------------

class TestScriptRouting:
    def test_aml_scripts_loaded(self, mock_aml_csv, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
        )
        scripts = orch._get_scripts_for_disease()
        script_names = [s["name"] for s in scripts]

        assert "02_table1.R" in script_names
        assert "05_safety.R" in script_names
        assert "03_efficacy.R" in script_names
        assert "04_survival.R" in script_names
        assert "20_aml_eln_risk.R" in script_names
        assert "21_aml_composite_response.R" in script_names

    def test_cml_scripts_loaded(self, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
        )
        scripts = orch._get_scripts_for_disease()
        script_names = [s["name"] for s in scripts]

        assert "22_cml_tfr_analysis.R" in script_names
        assert "23_cml_scores.R" in script_names
        # Should NOT contain AML-specific scripts
        assert "20_aml_eln_risk.R" not in script_names

    def test_hct_scripts_loaded(self, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="hct",
            output_dir=output_dir,
        )
        scripts = orch._get_scripts_for_disease()
        script_names = [s["name"] for s in scripts]

        assert "24_hct_gvhd_analysis.R" in script_names
        assert "20_aml_eln_risk.R" not in script_names

    def test_script_filter(self, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R", "04_survival.R"],
        )
        scripts = orch._get_scripts_for_disease()
        script_names = [s["name"] for s in scripts]

        assert script_names == ["02_table1.R", "04_survival.R"]


# ---------------------------------------------------------------------------
# R script execution tests (mocked subprocess)
# ---------------------------------------------------------------------------

class TestScriptExecution:
    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_scripts_success(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Script completed successfully\n",
            stderr="",
        )

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        csv_path = orch.transform(mock_aml_csv)
        results = orch.run_scripts(csv_path)

        assert len(results) == 1
        assert results[0].success
        assert results[0].script == "02_table1.R"

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_scripts_failure(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: package 'table1' not found",
        )

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        csv_path = orch.transform(mock_aml_csv)
        results = orch.run_scripts(csv_path)

        assert len(results) == 1
        assert not results[0].success
        assert "table1" in results[0].error

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_scripts_sets_env(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        csv_path = orch.transform(mock_aml_csv)
        orch.run_scripts(csv_path)

        # Check that CSA_OUTPUT_DIR was set in the env
        call_kwargs = mock_run.call_args
        env = call_kwargs.kwargs.get("env") or call_kwargs[1].get("env", {})
        assert env.get("CSA_OUTPUT_DIR") == output_dir

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_resolve_args_replaces_dataset(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["03_efficacy.R"],
        )
        csv_path = orch.transform(mock_aml_csv)
        orch.run_scripts(csv_path)

        # The {dataset} placeholder should be replaced with the actual CSV path
        call_args = mock_run.call_args[0][0]  # First positional arg (cmd list)
        assert csv_path in call_args


# ---------------------------------------------------------------------------
# Full pipeline (run_full) tests
# ---------------------------------------------------------------------------

class TestRunFull:
    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_success(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="OK\n", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        result = orch.run_full(mock_aml_csv, skip_validation=True)

        assert result.status in ("success", "partial")
        assert result.transformed_csv.endswith(".csv")
        assert result.steps["parse"]["status"] == "success"
        assert result.steps["validate"]["status"] == "skipped"
        assert result.steps["transform"]["status"] == "success"

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_partial_failure(self, mock_run, mock_aml_csv, output_dir):
        # First script succeeds, second fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="OK\n", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="Error in script"),
        ]

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R", "05_safety.R"],
        )
        result = orch.run_full(mock_aml_csv, skip_validation=True)

        assert result.status == "partial"
        assert result.successful_scripts == 1
        assert result.failed_scripts == 1

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_saves_summary(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        orch.run_full(mock_aml_csv, skip_validation=True)

        summary_path = Path(output_dir) / "analysis_summary.json"
        assert summary_path.exists()

        with open(summary_path) as f:
            summary = json.load(f)
        assert summary["disease"] == "aml"
        assert "steps" in summary

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_with_validation(self, mock_run, mock_aml_csv, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="aml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        result = orch.run_full(mock_aml_csv, skip_validation=False)

        assert result.steps["validate"]["status"] in ("success", "error")


# ---------------------------------------------------------------------------
# AnalysisResult tests
# ---------------------------------------------------------------------------

class TestAnalysisResult:
    def test_to_dict(self):
        result = AnalysisResult(
            status="success",
            disease="aml",
            total_scripts=2,
            successful_scripts=2,
            failed_scripts=0,
            elapsed_time=15.5,
        )
        d = result.to_dict()
        assert d["status"] == "success"
        assert d["disease"] == "aml"
        assert d["elapsed_time"] == 15.5

    def test_script_result_success(self):
        sr = ScriptResult(script="02_table1.R", exit_code=0)
        assert sr.success

    def test_script_result_failure(self):
        sr = ScriptResult(script="02_table1.R", exit_code=1, error="Missing package")
        assert not sr.success
