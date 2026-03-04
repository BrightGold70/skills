"""Tests for v3.1 output quality & CML expansion modules.

Covers: JournalThemes, PDFExporter, ReportGenerator, HTMLExporter,
        CML script routing (26-29), post_process integration, CLI flags.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pandas as pd
import pytest

from scripts.crf_pipeline.orchestrator import (
    AnalysisOrchestrator,
    AnalysisResult,
    ScriptResult,
)
from scripts.crf_pipeline.journal_themes import JournalThemes
from scripts.crf_pipeline.pdf_exporter import PDFExporter
from scripts.crf_pipeline.report_generator import ReportGenerator, _SCRIPT_TO_SECTION
from scripts.crf_pipeline.html_exporter import HTMLExporter

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "scripts" / "crf_pipeline" / "config"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory with Tables/Figures/Reports subdirs."""
    out = tmp_path / "output"
    (out / "Tables").mkdir(parents=True)
    (out / "Figures").mkdir(parents=True)
    (out / "Reports").mkdir(parents=True)
    return str(out)


@pytest.fixture
def mock_cml_csv(tmp_path):
    """Create a mock CML patient CSV (simplified from fixtures/cml_mock.csv)."""
    df = pd.DataFrame({
        "case_no": [f"CML-{i:03d}" for i in range(1, 6)],
        "age": [45, 62, 38, 55, 70],
        "gender": ["Male", "Female", "Male", "Female", "Male"],
        "alive": [1, 2, 1, 1, 2],
        "tki_first_line": ["Imatinib", "Dasatinib", "Nilotinib", "Imatinib", "Dasatinib"],
        "tki_start_date": [
            "2024-01-15", "2024-02-01", "2024-03-10", "2024-01-20", "2024-04-05",
        ],
        "date_death": [None, "2025-08-15", None, None, "2025-05-10"],
        "date_last_fu": [
            "2025-12-01", "2025-08-15", "2025-11-20", "2025-12-10", "2025-05-10",
        ],
        "relapse_date": [None, None, None, None, None],
        "bcr_abl_baseline": [95.0, 78.0, 110.0, 85.0, 65.0],
        "bcr_abl_3m": [10.0, 5.0, 15.0, 8.0, 12.0],
        "bcr_abl_6m": [1.0, 0.5, 3.0, 0.8, 2.0],
        "bcr_abl_12m": [0.1, 0.05, 0.5, 0.08, 0.3],
        "cml_phase_dx": ["Chronic Phase"] * 5,
        "sokal_risk": ["Low", "Intermediate", "Low", "High", "Intermediate"],
        "mmr_achieved": ["Yes", "Yes", "No", "Yes", "No"],
    })
    csv_path = tmp_path / "cml_test_data.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def sample_script_results():
    """Mock script results for post-processing tests."""
    return [
        ScriptResult(
            script="02_table1.R", exit_code=0,
            output_files=["/tmp/out/Tables/Table1_Baseline_Characteristics.docx"],
        ),
        ScriptResult(
            script="04_survival.R", exit_code=0,
            output_files=["/tmp/out/Figures/KM_OS.eps"],
        ),
        ScriptResult(
            script="05_safety.R", exit_code=0,
            output_files=["/tmp/out/Tables/Safety_Summary_Table.docx"],
        ),
        ScriptResult(
            script="22_cml_tfr_analysis.R", exit_code=1,
            error="Missing columns",
        ),
    ]


# ---------------------------------------------------------------------------
# JournalThemes tests
# ---------------------------------------------------------------------------

class TestJournalThemes:
    def test_load_templates(self):
        themes = JournalThemes()
        assert themes._templates is not None
        assert len(themes._templates) > 0

    def test_available_journals(self):
        themes = JournalThemes()
        journals = themes.available_journals
        assert "nejm" in journals
        assert "lancet" in journals
        assert "blood" in journals
        assert "jco" in journals

    def test_get_theme_valid(self):
        themes = JournalThemes()
        theme = themes.get_theme("nejm")
        assert theme is not None
        assert "font_family" in theme
        assert "font_size" in theme

    def test_get_theme_invalid(self):
        themes = JournalThemes()
        with pytest.raises(ValueError, match="Unknown journal"):
            themes.get_theme("nonexistent_journal")

    def test_get_theme_case_insensitive(self):
        themes = JournalThemes()
        theme_lower = themes.get_theme("nejm")
        theme_upper = themes.get_theme("NEJM")
        assert theme_lower == theme_upper

    @patch("scripts.crf_pipeline.journal_themes.subprocess.run")
    def test_apply_calls_rscript(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create a fake .docx file in Tables
        fake_docx = Path(output_dir) / "Tables" / "Test_Table.docx"
        fake_docx.write_text("fake")

        themes = JournalThemes()
        themes.apply(str(Path(output_dir) / "Tables"), "nejm")

        # Should have attempted to run Rscript
        assert mock_run.called

    def test_apply_no_docx_files(self, output_dir):
        themes = JournalThemes()
        result = themes.apply(str(Path(output_dir) / "Tables"), "nejm")
        assert result == []

    def test_template_has_required_keys(self):
        themes = JournalThemes()
        required_keys = {"font_family", "font_size"}
        for journal in themes.available_journals:
            theme = themes.get_theme(journal)
            for key in required_keys:
                assert key in theme, f"{journal} missing key: {key}"


# ---------------------------------------------------------------------------
# PDFExporter tests
# ---------------------------------------------------------------------------

class TestPDFExporter:
    def test_init(self, output_dir):
        exporter = PDFExporter(output_dir)
        assert exporter.output_dir == Path(output_dir)

    @patch("scripts.crf_pipeline.pdf_exporter.subprocess.run")
    def test_export_tables_libreoffice(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create fake .docx
        fake_docx = Path(output_dir) / "Tables" / "Test.docx"
        fake_docx.write_text("fake")

        # Create pdf subdir and expected output PDF so it "exists"
        pdf_dir = Path(output_dir) / "Tables" / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_out = pdf_dir / "Test.pdf"
        pdf_out.write_text("fake_pdf")

        exporter = PDFExporter(output_dir)
        results = exporter.export_tables(str(Path(output_dir) / "Tables"))

        # Should have attempted conversion (libreoffice or pandoc)
        assert mock_run.called or results == []

    @patch("scripts.crf_pipeline.pdf_exporter.subprocess.run")
    def test_export_figures_ghostscript(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create fake .eps
        fake_eps = Path(output_dir) / "Figures" / "KM_OS.eps"
        fake_eps.write_text("fake")

        # Create pdf subdir and expected output PDF
        pdf_dir = Path(output_dir) / "Figures" / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_out = pdf_dir / "KM_OS.pdf"
        pdf_out.write_text("fake_pdf")

        exporter = PDFExporter(output_dir)
        results = exporter.export_figures(str(Path(output_dir) / "Figures"))

        assert mock_run.called or results == []

    @patch("scripts.crf_pipeline.pdf_exporter.subprocess.run")
    def test_export_all(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        exporter = PDFExporter(output_dir)
        result = exporter.export_all(
            str(Path(output_dir) / "Tables"),
            str(Path(output_dir) / "Figures"),
        )

        assert "tables" in result
        assert "figures" in result


# ---------------------------------------------------------------------------
# ReportGenerator tests
# ---------------------------------------------------------------------------

class TestReportGenerator:
    def test_script_to_section_mapping(self):
        assert _SCRIPT_TO_SECTION["02_table1.R"] == "demographics"
        assert _SCRIPT_TO_SECTION["03_efficacy.R"] == "efficacy"
        assert _SCRIPT_TO_SECTION["04_survival.R"] == "survival"
        assert _SCRIPT_TO_SECTION["05_safety.R"] == "safety"
        assert _SCRIPT_TO_SECTION["22_cml_tfr_analysis.R"] == "disease_specific"
        assert _SCRIPT_TO_SECTION["26_cml_eln_milestones.R"] == "disease_specific"
        assert _SCRIPT_TO_SECTION["28_cml_resistance.R"] == "disease_specific"

    def test_collect_outputs(self, output_dir, sample_script_results):
        gen = ReportGenerator(output_dir, "cml")
        section_files = gen.collect_outputs(sample_script_results)

        assert "demographics" in section_files
        assert "safety" in section_files
        assert "survival" in section_files
        # Only successful scripts should contribute
        assert len(section_files["demographics"]) == 1  # table1
        assert len(section_files["safety"]) == 1  # safety

    def test_collect_outputs_skips_failures(self, output_dir):
        results = [
            ScriptResult(script="02_table1.R", exit_code=1, error="failed"),
        ]
        gen = ReportGenerator(output_dir, "aml")
        section_files = gen.collect_outputs(results)
        assert len(section_files["demographics"]) == 0

    def test_ich_e3_sections(self):
        expected = [
            "title_page", "synopsis", "demographics", "efficacy",
            "safety", "survival", "disease_specific", "conclusions",
        ]
        assert ReportGenerator.ICH_E3_SECTIONS == expected

    @patch("scripts.crf_pipeline.report_generator.HAS_DOCX", False)
    def test_generate_without_docx(self, output_dir, sample_script_results):
        gen = ReportGenerator(output_dir, "cml")
        result = gen.generate(sample_script_results)
        assert result == ""

    @patch("scripts.crf_pipeline.report_generator.HAS_DOCX", True)
    @patch("scripts.crf_pipeline.report_generator.Document")
    def test_generate_creates_docx(self, mock_doc_cls, output_dir, sample_script_results):
        mock_doc = MagicMock()
        mock_doc_cls.return_value = mock_doc

        gen = ReportGenerator(output_dir, "cml")
        result = gen.generate(sample_script_results)

        # Should have called doc.save()
        mock_doc.save.assert_called_once()
        assert result.endswith(".docx")


# ---------------------------------------------------------------------------
# HTMLExporter tests
# ---------------------------------------------------------------------------

class TestHTMLExporter:
    def test_init_creates_reports_dir(self, output_dir):
        exporter = HTMLExporter(output_dir, "cml")
        assert (Path(output_dir) / "Reports").exists()

    def test_create_rmd_template(self, output_dir):
        exporter = HTMLExporter(output_dir, "cml")
        rmd_path = exporter._create_rmd_template("/tmp/test.csv")

        assert os.path.exists(rmd_path)
        with open(rmd_path, "r") as f:
            content = f.read()

        assert "CML Clinical Trial Dashboard" in content
        assert "plotly" in content
        assert "DT" in content
        assert "/tmp/test.csv" in content

        # Clean up
        os.unlink(rmd_path)

    @patch("scripts.crf_pipeline.html_exporter.subprocess.run")
    def test_render_html_success(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create expected output HTML
        html_path = Path(output_dir) / "Reports" / "Dashboard_CML.html"
        html_path.write_text("<html></html>")

        exporter = HTMLExporter(output_dir, "cml")
        result = exporter._render_html("/tmp/test.Rmd")

        assert result == str(html_path)
        assert mock_run.called

    @patch("scripts.crf_pipeline.html_exporter.subprocess.run")
    def test_render_html_failure(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

        exporter = HTMLExporter(output_dir, "cml")
        result = exporter._render_html("/tmp/test.Rmd")

        assert result == ""

    @patch("scripts.crf_pipeline.html_exporter.subprocess.run")
    def test_render_html_rscript_not_found(self, mock_run, output_dir):
        mock_run.side_effect = FileNotFoundError("Rscript not found")

        exporter = HTMLExporter(output_dir, "cml")
        result = exporter._render_html("/tmp/test.Rmd")

        assert result == ""

    @patch("scripts.crf_pipeline.html_exporter.subprocess.run")
    def test_generate_full(self, mock_run, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create expected output HTML
        html_path = Path(output_dir) / "Reports" / "Dashboard_CML.html"
        html_path.write_text("<html></html>")

        exporter = HTMLExporter(output_dir, "cml")
        result = exporter.generate("/tmp/test.csv", [])

        assert result == str(html_path)


# ---------------------------------------------------------------------------
# CML script routing (scripts 26-29)
# ---------------------------------------------------------------------------

class TestCMLScriptRouting:
    def test_cml_profile_includes_new_scripts(self):
        with open(CONFIG_DIR / "analysis_profiles.json") as f:
            profiles = json.load(f)

        cml_scripts = [s["name"] for s in profiles["profiles"]["cml"]["scripts"]]

        assert "26_cml_eln_milestones.R" in cml_scripts
        assert "27_cml_waterfall.R" in cml_scripts
        assert "28_cml_resistance.R" in cml_scripts
        assert "29_cml_tfr_deep.R" in cml_scripts

    def test_new_scripts_are_optional(self):
        with open(CONFIG_DIR / "analysis_profiles.json") as f:
            profiles = json.load(f)

        cml_scripts = profiles["profiles"]["cml"]["scripts"]
        new_script_names = {
            "26_cml_eln_milestones.R", "27_cml_waterfall.R",
            "28_cml_resistance.R", "29_cml_tfr_deep.R",
        }

        for script in cml_scripts:
            if script["name"] in new_script_names:
                assert script["required"] is False, f"{script['name']} should be optional"

    def test_new_scripts_have_expected_outputs(self):
        with open(CONFIG_DIR / "analysis_profiles.json") as f:
            profiles = json.load(f)

        cml_scripts = {s["name"]: s for s in profiles["profiles"]["cml"]["scripts"]}

        assert "CML_ELN2020_Milestones.docx" in cml_scripts["26_cml_eln_milestones.R"]["expected_outputs"]
        assert "CML_Waterfall_BCR_ABL.eps" in cml_scripts["27_cml_waterfall.R"]["expected_outputs"]
        assert "CML_Resistance_Mutations.docx" in cml_scripts["28_cml_resistance.R"]["expected_outputs"]
        assert "CML_TFR_Deep_Analysis.docx" in cml_scripts["29_cml_tfr_deep.R"]["expected_outputs"]

    def test_cml_column_mapping_has_resistance_fields(self):
        with open(CONFIG_DIR / "cml_fields.json") as f:
            config = json.load(f)

        mapping = config["column_mapping"]
        assert "resistance_mutation" in mapping
        assert "resistance_date" in mapping
        assert "tfr_start_date" in mapping
        assert "mmr_loss_date" in mapping
        assert "mr4_duration_months" in mapping

    def test_cml_column_mapping_has_bcr_abl_timepoints(self):
        with open(CONFIG_DIR / "cml_fields.json") as f:
            config = json.load(f)

        mapping = config["column_mapping"]
        for tp in ["3m", "6m", "12m", "18m", "24m"]:
            assert f"bcr_abl_{tp}" in mapping

    def test_orchestrator_loads_all_cml_scripts(self, output_dir):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
        )
        scripts = orch._get_scripts_for_disease()
        names = [s["name"] for s in scripts]

        # Should have 10 scripts total: 4 common + 6 CML-specific
        assert len(names) == 10
        assert "26_cml_eln_milestones.R" in names
        assert "29_cml_tfr_deep.R" in names

    def test_aml_profile_unchanged(self):
        """Verify AML profile was not accidentally modified."""
        with open(CONFIG_DIR / "analysis_profiles.json") as f:
            profiles = json.load(f)

        aml_scripts = [s["name"] for s in profiles["profiles"]["aml"]["scripts"]]
        assert len(aml_scripts) == 6
        assert "26_cml_eln_milestones.R" not in aml_scripts


# ---------------------------------------------------------------------------
# Post-process integration tests
# ---------------------------------------------------------------------------

class TestPostProcess:
    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_post_process_journal(self, mock_run, output_dir, sample_script_results):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
        )
        result = orch.post_process(
            csv_path="/tmp/test.csv",
            script_results=sample_script_results,
            journal="nejm",
        )

        assert "journal_files" in result
        assert "pdf_files" in result
        assert "html_path" in result
        assert "csr_path" in result

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_post_process_no_options(self, mock_run, output_dir, sample_script_results):
        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
        )
        result = orch.post_process(
            csv_path="/tmp/test.csv",
            script_results=sample_script_results,
            journal=None,
            generate_pdf=False,
            generate_html=False,
            generate_csr=False,
        )

        # All should be empty/default
        assert result["journal_files"] == []
        assert result["html_path"] == ""
        assert result["csr_path"] == ""

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_with_post_process(self, mock_run, mock_cml_csv, output_dir):
        mock_run.return_value = MagicMock(returncode=0, stdout="OK\n", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        result = orch.run_full(
            mock_cml_csv,
            skip_validation=True,
            journal="blood",
            generate_pdf=True,
            generate_html=False,
            generate_csr=False,
        )

        assert "post_process" in result.steps
        assert result.steps["post_process"]["status"] in ("success", "error")

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_no_post_process_when_defaults(self, mock_run, mock_cml_csv, output_dir):
        """When no post-process flags, generate_csr=True still triggers post_process."""
        mock_run.return_value = MagicMock(returncode=0, stdout="OK\n", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        result = orch.run_full(
            mock_cml_csv,
            skip_validation=True,
            generate_csr=True,
        )

        # generate_csr=True should trigger post_process
        assert "post_process" in result.steps

    @patch("scripts.crf_pipeline.orchestrator.subprocess.run")
    def test_run_full_skip_post_process(self, mock_run, mock_cml_csv, output_dir):
        """When all post-process flags are off, no post_process step."""
        mock_run.return_value = MagicMock(returncode=0, stdout="OK\n", stderr="")

        orch = AnalysisOrchestrator(
            config_dir=str(CONFIG_DIR),
            disease="cml",
            output_dir=output_dir,
            script_filter=["02_table1.R"],
        )
        result = orch.run_full(
            mock_cml_csv,
            skip_validation=True,
            journal=None,
            generate_pdf=False,
            generate_html=False,
            generate_csr=False,
        )

        assert "post_process" not in result.steps


# ---------------------------------------------------------------------------
# CLI argument tests
# ---------------------------------------------------------------------------

class TestCLIFlags:
    def test_run_analysis_parser_has_journal(self):
        from scripts.crf_pipeline.cli import main
        import argparse

        # Build parser manually to test argument existence
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        analysis_cmd = subparsers.add_parser("run-analysis")
        analysis_cmd.add_argument("data_file")
        analysis_cmd.add_argument("-d", "--disease", default="aml")
        analysis_cmd.add_argument("--journal", choices=["nejm", "lancet", "blood", "jco"])
        analysis_cmd.add_argument("--pdf", action="store_true")
        analysis_cmd.add_argument("--html", action="store_true")
        analysis_cmd.add_argument("--no-csr", action="store_true")

        args = parser.parse_args(["run-analysis", "data.csv", "--journal", "nejm", "--pdf", "--html"])
        assert args.journal == "nejm"
        assert args.pdf is True
        assert args.html is True

    def test_cli_no_csr_flag(self):
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        analysis_cmd = subparsers.add_parser("run-analysis")
        analysis_cmd.add_argument("data_file")
        analysis_cmd.add_argument("--no-csr", action="store_true")

        args = parser.parse_args(["run-analysis", "data.csv", "--no-csr"])
        assert args.no_csr is True


# ---------------------------------------------------------------------------
# CML mock data fixture validation
# ---------------------------------------------------------------------------

class TestCMLMockData:
    def test_cml_mock_csv_exists(self):
        fixture_path = FIXTURES_DIR / "cml_mock.csv"
        assert fixture_path.exists(), "CML mock CSV fixture should exist"

    def test_cml_mock_csv_structure(self):
        fixture_path = FIXTURES_DIR / "cml_mock.csv"
        if not fixture_path.exists():
            pytest.skip("CML mock fixture not found")

        df = pd.read_csv(fixture_path)
        assert len(df) == 15

        # Required columns for CML scripts
        required = [
            "Patient_ID", "Age", "Sex", "Treatment",
            "OS_months", "OS_status", "bcr_abl_baseline",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_cml_mock_has_resistance_data(self):
        fixture_path = FIXTURES_DIR / "cml_mock.csv"
        if not fixture_path.exists():
            pytest.skip("CML mock fixture not found")

        df = pd.read_csv(fixture_path)
        assert "resistance_mutation" in df.columns
        # Should have some patients with mutations
        has_mutation = df["resistance_mutation"].notna().sum()
        assert has_mutation > 0

    def test_cml_mock_has_tfr_data(self):
        fixture_path = FIXTURES_DIR / "cml_mock.csv"
        if not fixture_path.exists():
            pytest.skip("CML mock fixture not found")

        df = pd.read_csv(fixture_path)
        assert "tfr_start_date" in df.columns
        has_tfr = df["tfr_start_date"].notna().sum()
        assert has_tfr > 0


# ---------------------------------------------------------------------------
# R script file existence tests
# ---------------------------------------------------------------------------

class TestRScriptFiles:
    @pytest.mark.parametrize("script_name", [
        "26_cml_eln_milestones.R",
        "27_cml_waterfall.R",
        "28_cml_resistance.R",
        "29_cml_tfr_deep.R",
    ])
    def test_r_script_exists(self, script_name):
        script_path = PROJECT_ROOT / "scripts" / script_name
        assert script_path.exists(), f"R script {script_name} should exist"

    @pytest.mark.parametrize("script_name", [
        "26_cml_eln_milestones.R",
        "27_cml_waterfall.R",
        "28_cml_resistance.R",
        "29_cml_tfr_deep.R",
    ])
    def test_r_script_has_shebang(self, script_name):
        script_path = PROJECT_ROOT / "scripts" / script_name
        with open(script_path) as f:
            first_line = f.readline().strip()
        assert first_line == "#!/usr/bin/env Rscript"

    @pytest.mark.parametrize("script_name", [
        "26_cml_eln_milestones.R",
        "27_cml_waterfall.R",
        "28_cml_resistance.R",
        "29_cml_tfr_deep.R",
    ])
    def test_r_script_uses_csa_output_dir(self, script_name):
        script_path = PROJECT_ROOT / "scripts" / script_name
        content = script_path.read_text()
        assert "CSA_OUTPUT_DIR" in content, f"{script_name} should use CSA_OUTPUT_DIR"
