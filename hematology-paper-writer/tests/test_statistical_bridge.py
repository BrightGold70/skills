"""Tests for StatisticalBridge — CSA→HPW manifest consumption layer."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from tools.statistical_bridge import (
    ManifestError,
    ManifestVersionError,
    StatisticalBridge,
    StatValue,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _write_manifest(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "hpw_manifest.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _aml_manifest(tmp_path: Path, **overrides) -> dict:
    """Minimal valid AML manifest with all sidecar stats populated."""
    base = {
        "schema_version": "1.0",
        "disease": "aml",
        "generated_at": "2026-03-01T00:00:00",
        "r_version": "4.4.0",
        "r_packages": ["survival", "flextable", "officer", "ggplot2"],
        "scripts_run": [
            "02_table1.R", "03_efficacy.R", "04_survival.R", "05_safety.R",
            "20_aml_eln_risk.R", "21_aml_composite_response.R", "25_aml_phase1_boin.R",
        ],
        "key_statistics": {
            "n_total": 120,
            "orr": {"value": 72.5, "unit": "percent", "ci_lower": 63.6, "ci_upper": 80.1},
            "cr_rate": {"value": 55.0, "unit": "percent"},
            "ccr_rate": {"value": 68.3, "unit": "percent", "ci_lower": 59.0, "ci_upper": 76.6},
            "os_median_months": {"value": 18.4, "ci_lower": 14.2, "ci_upper": 22.6},
            "os_hr": {"value": 0.62, "ci_lower": 0.41, "ci_upper": 0.94, "p_value": 0.024},
            "pfs_median_months": {"value": 12.1, "ci_lower": 9.8, "ci_upper": 14.9},
            "ae_grade3plus_rate": {"value": 48.3, "unit": "percent"},
            "follow_up_median_months": {"value": 24.0},
            # ELN 2022
            "eln_favorable_pct": {"value": 38.3, "unit": "percent"},
            "eln_intermediate_pct": {"value": 25.0, "unit": "percent"},
            "eln_adverse_pct": {"value": 36.7, "unit": "percent"},
            # BOIN
            "target_dlt_rate": {"value": 0.25},
            "lambda_e": {"value": 0.2367},
            "lambda_d": {"value": 0.2933},
            "n_doses": {"value": 6},
            "n_simulated_trials": {"value": 1000},
        },
        "analysis_notes": {
            "survival_model": "Cox proportional hazards",
            "competing_risks": "Fine-Gray subdistribution hazard",
        },
        "study_context": {
            "study_name": "SAPPHIRE-G",
            "protocol_id": "SGPG-2024-001",
            "trial_phase": "Phase 2",
            "sponsor": "Test Pharma",
            "data_cutoff": "2025-12-31",
        },
        "tables": [
            {"id": "T1", "label": "Table 1. Baseline characteristics",
             "path": "Tables/Table1.docx", "type": "table1", "source_script": "02_table1.R"},
            {"id": "T2", "label": "Table 2. Efficacy outcomes",
             "path": "Tables/Efficacy.docx", "type": "efficacy", "source_script": "03_efficacy.R"},
        ],
        "figures": [
            {"id": "F1", "label": "Figure 1. Overall survival",
             "path": "Figures/KM_OS.eps", "type": "km_os", "source_script": "04_survival.R"},
        ],
    }
    base.update(overrides)
    return base


@pytest.fixture
def aml_bridge(tmp_path):
    data = _aml_manifest(tmp_path)
    p = _write_manifest(tmp_path, data)
    return StatisticalBridge(p)


def _cml_manifest(tmp_path: Path) -> dict:
    return {
        "schema_version": "1.0",
        "disease": "cml",
        "generated_at": "2026-03-01T00:00:00",
        "r_version": "4.4.0",
        "r_packages": ["survival", "flextable"],
        "scripts_run": ["02_table1.R", "04_survival.R", "22_cml_tfr_analysis.R", "23_cml_scores.R"],
        "key_statistics": {
            "n_total": 85,
            "mmr_12mo": {"value": 72.9, "unit": "percent"},
            "tfr_12mo": {"value": 55.3, "unit": "percent"},
            "tfr_24mo": {"value": 48.1, "unit": "percent"},
            "sokal_high_pct": {"value": 22.4, "unit": "percent"},
            "os_median_months": {"value": 48.0},
            "ae_grade3plus_rate": {"value": 31.8, "unit": "percent"},
        },
        "analysis_notes": {},
        "tables": [],
        "figures": [],
    }


def _hct_manifest(tmp_path: Path) -> dict:
    return {
        "schema_version": "1.0",
        "disease": "hct",
        "generated_at": "2026-03-01T00:00:00",
        "r_version": "4.4.0",
        "r_packages": ["survival", "cmprsk"],
        "scripts_run": ["02_table1.R", "04_survival.R", "24_hct_gvhd_analysis.R"],
        "key_statistics": {
            "n_total": 60,
            "agvhd_grade2_4_rate": {"value": 34.0, "unit": "percent"},
            "cgvhd_any_rate": {"value": 28.0, "unit": "percent"},
            "grfs_event_rate": {"value": 55.0, "unit": "percent"},
            "neutrophil_engraftment_rate": {"value": 98.3, "unit": "percent"},
            "median_neutrophil_engraftment_days": {"value": 14.0},
            "os_median_months": {"value": 36.0},
            "ae_grade3plus_rate": {"value": 41.7, "unit": "percent"},
        },
        "analysis_notes": {},
        "tables": [],
        "figures": [],
    }


# ── Load / schema validation ───────────────────────────────────────────────────

class TestLoad:
    def test_loads_valid_manifest(self, aml_bridge):
        assert aml_bridge.is_available

    def test_raises_missing_file(self, tmp_path):
        with pytest.raises(ManifestError, match="not found"):
            StatisticalBridge(tmp_path / "missing.json")

    def test_raises_invalid_json(self, tmp_path):
        p = tmp_path / "hpw_manifest.json"
        p.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ManifestError, match="Invalid JSON"):
            StatisticalBridge(p)

    def test_raises_wrong_schema_version(self, tmp_path):
        data = _aml_manifest(tmp_path, schema_version="2.0")
        p = _write_manifest(tmp_path, data)
        with pytest.raises(ManifestVersionError):
            StatisticalBridge(p)

    def test_from_env_returns_none_without_env(self, monkeypatch):
        monkeypatch.delenv("CSA_OUTPUT_DIR", raising=False)
        assert StatisticalBridge.from_env() is None

    def test_from_env_loads_manifest(self, tmp_path, monkeypatch):
        data = _aml_manifest(tmp_path)
        _write_manifest(tmp_path, data)
        monkeypatch.setenv("CSA_OUTPUT_DIR", str(tmp_path))
        bridge = StatisticalBridge.from_env()
        assert bridge is not None
        assert bridge.disease == "aml"


# ── Properties ────────────────────────────────────────────────────────────────

class TestProperties:
    def test_disease(self, aml_bridge):
        assert aml_bridge.disease == "aml"

    def test_scripts_run(self, aml_bridge):
        assert "02_table1.R" in aml_bridge.scripts_run
        assert "20_aml_eln_risk.R" in aml_bridge.scripts_run

    def test_study_context(self, aml_bridge):
        ctx = aml_bridge.study_context
        assert ctx["study_name"] == "SAPPHIRE-G"
        assert ctx["trial_phase"] == "Phase 2"

    def test_study_name_property(self, aml_bridge):
        assert aml_bridge.study_name == "SAPPHIRE-G"

    def test_trial_phase_property(self, aml_bridge):
        assert aml_bridge.trial_phase == "Phase 2"

    def test_study_name_empty_when_absent(self, tmp_path):
        data = _aml_manifest(tmp_path)
        del data["study_context"]
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        assert bridge.study_name == ""
        assert bridge.trial_phase == ""

    def test_study_context_empty_when_absent(self, tmp_path):
        data = _aml_manifest(tmp_path)
        del data["study_context"]
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        assert bridge.study_context == {}


# ── get_stat / format_stat ────────────────────────────────────────────────────

class TestGetStat:
    def test_scalar_stat(self, aml_bridge):
        sv = aml_bridge.get_stat("n_total")
        assert sv is not None
        assert sv.value == 120

    def test_dict_stat_with_ci(self, aml_bridge):
        sv = aml_bridge.get_stat("orr")
        assert sv.value == 72.5
        assert sv.ci_lower == 63.6
        assert sv.unit == "percent"

    def test_missing_stat_returns_none(self, aml_bridge):
        assert aml_bridge.get_stat("nonexistent_key") is None

    def test_format_stat_standard(self, aml_bridge):
        s = aml_bridge.format_stat("orr")
        assert "72.5%" in s
        assert "95% CI" in s

    def test_format_stat_hr(self, aml_bridge):
        s = aml_bridge.format_stat("os_hr", "hr")
        assert "HR 0.62" in s
        assert "p = 0.024" in s

    def test_format_stat_missing_returns_placeholder(self, aml_bridge):
        s = aml_bridge.format_stat("absent_key")
        assert s == "[DATA UNAVAILABLE]"

    def test_fmt_opt_returns_empty_when_absent(self, aml_bridge):
        s = aml_bridge._fmt_opt("absent_key")
        assert s == ""

    def test_fmt_opt_returns_value_when_present(self, aml_bridge):
        s = aml_bridge._fmt_opt("orr")
        assert "72.5%" in s


# ── References ────────────────────────────────────────────────────────────────

class TestReferences:
    def test_table_refs(self, aml_bridge):
        tables = aml_bridge.get_table_references()
        assert len(tables) == 2
        assert tables[0].type == "table1"
        assert tables[0].source_script == "02_table1.R"

    def test_figure_refs(self, aml_bridge):
        figs = aml_bridge.get_figure_references()
        assert len(figs) == 1
        assert figs[0].type == "km_os"


# ── Prose generation ──────────────────────────────────────────────────────────

class TestProseGeneration:
    def test_methods_paragraph_contains_r_version(self, aml_bridge):
        para = aml_bridge.generate_methods_paragraph()
        assert "R version 4.4.0" in para

    def test_methods_paragraph_mentions_kaplan_meier(self, aml_bridge):
        para = aml_bridge.generate_methods_paragraph()
        assert "Kaplan" in para

    def test_methods_paragraph_mentions_fine_gray(self, aml_bridge):
        para = aml_bridge.generate_methods_paragraph()
        assert "Fine" in para

    def test_results_baseline_section(self, aml_bridge):
        prose = aml_bridge.generate_results_prose()
        assert "baseline" in prose
        assert "120" in prose["baseline"]

    def test_results_efficacy_section(self, aml_bridge):
        prose = aml_bridge.generate_results_prose()
        assert "efficacy" in prose
        assert "72.5%" in prose["efficacy"]

    def test_results_aml_eln_risk(self, aml_bridge):
        prose = aml_bridge.generate_results_prose()
        assert "aml_eln_risk" in prose
        assert "ELN 2022" in prose["aml_eln_risk"]
        assert "adverse-risk" in prose["aml_eln_risk"]

    def test_results_aml_composite_response_ccr(self, aml_bridge):
        prose = aml_bridge.generate_results_prose()
        assert "aml_composite_response" in prose
        assert "cCR" in prose["aml_composite_response"]
        assert "68.3%" in prose["aml_composite_response"]

    def test_results_aml_composite_response_boin(self, aml_bridge):
        prose = aml_bridge.generate_results_prose()
        assert "aml_composite_response" in prose
        assert "BOIN" in prose["aml_composite_response"]

    def test_results_cml_molecular(self, tmp_path):
        data = _cml_manifest(tmp_path)
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        prose = bridge.generate_results_prose()
        assert "cml_molecular" in prose
        assert "MMR" in prose["cml_molecular"]

    def test_results_cml_tfr(self, tmp_path):
        data = _cml_manifest(tmp_path)
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        prose = bridge.generate_results_prose()
        assert "cml_tfr" in prose
        assert "TFR" in prose["cml_tfr"]

    def test_results_cml_scores(self, tmp_path):
        data = _cml_manifest(tmp_path)
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        prose = bridge.generate_results_prose()
        assert "cml_scores" in prose
        assert "Sokal" in prose["cml_scores"]

    def test_results_hct_gvhd(self, tmp_path):
        data = _hct_manifest(tmp_path)
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        prose = bridge.generate_results_prose()
        assert "hct_gvhd" in prose
        assert "GVHD" in prose["hct_gvhd"]
        assert "GRFS" in prose["hct_gvhd"]
        assert "engraftment" in prose["hct_gvhd"]

    def test_no_aml_keys_when_wrong_disease(self, tmp_path):
        data = _cml_manifest(tmp_path)
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        prose = bridge.generate_results_prose()
        assert "aml_eln_risk" not in prose
        assert "aml_composite_response" not in prose


# ── Abstract statistics ────────────────────────────────────────────────────────

class TestAbstractStatistics:
    def test_aml_abstract_includes_ccr(self, aml_bridge):
        abstract = aml_bridge.get_abstract_statistics()
        assert "ccr_rate" in abstract
        assert isinstance(abstract["ccr_rate"], StatValue)

    def test_aml_abstract_includes_eln_adverse(self, aml_bridge):
        abstract = aml_bridge.get_abstract_statistics()
        assert "eln_adverse_pct" in abstract

    def test_abstract_only_present_keys(self, tmp_path):
        data = _aml_manifest(tmp_path)
        del data["key_statistics"]["ccr_rate"]
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        abstract = bridge.get_abstract_statistics()
        assert "ccr_rate" not in abstract  # absent, not placeholder


# ── Schema validation (M2) ────────────────────────────────────────────────────

class TestSchemaValidation:
    def test_validate_completeness_all_present(self, aml_bridge):
        missing = aml_bridge.validate_stats_completeness()
        assert missing == []

    def test_validate_completeness_missing_key(self, tmp_path):
        data = _aml_manifest(tmp_path)
        del data["key_statistics"]["ae_grade3plus_rate"]
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        missing = bridge.validate_stats_completeness()
        assert "ae_grade3plus_rate" in missing

    def test_validate_completeness_multiple_missing(self, tmp_path):
        data = _aml_manifest(tmp_path)
        del data["key_statistics"]["orr"]
        del data["key_statistics"]["os_median_months"]
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        missing = bridge.validate_stats_completeness()
        assert "orr" in missing
        assert "os_median_months" in missing

    def test_validate_completeness_unknown_disease(self, tmp_path):
        data = _aml_manifest(tmp_path)
        data["study_context"]["disease"] = "unknown_disease"
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        # Unknown disease has no required stats → always complete
        assert bridge.validate_stats_completeness() == []

    def test_get_ds_stat_reads_disease_specific(self, tmp_path):
        data = _aml_manifest(tmp_path)
        data["disease_specific"] = {"aml": {"eln_favorable_pct": 35.0}}
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        sv = bridge._get_ds_stat("aml", "eln_favorable_pct")
        assert sv is not None
        assert sv.value == 35.0

    def test_get_ds_stat_fallback_to_key_statistics(self, aml_bridge):
        # "orr" is in key_statistics but not in disease_specific
        sv = aml_bridge._get_ds_stat("aml", "orr")
        assert sv is not None
        assert sv.value == 72.5

    def test_get_ds_stat_returns_none_when_absent(self, aml_bridge):
        sv = aml_bridge._get_ds_stat("aml", "nonexistent_stat_xyz")
        assert sv is None

    def test_get_ds_stat_dict_value(self, tmp_path):
        data = _aml_manifest(tmp_path)
        data["disease_specific"] = {
            "aml": {"ccr_rate": {"value": 68.3, "ci_lower": 55.0, "ci_upper": 79.7}}
        }
        p = _write_manifest(tmp_path, data)
        bridge = StatisticalBridge(p)
        sv = bridge._get_ds_stat("aml", "ccr_rate")
        assert sv is not None
        assert sv.value == 68.3
        assert sv.ci_lower == 55.0


# ── Verification ──────────────────────────────────────────────────────────────

class TestVerification:
    def test_exact_match_no_issues(self, aml_bridge):
        text = "The ORR was 72.5% and OS was 18.4 months."
        issues = aml_bridge.verify_manuscript_statistics(text)
        assert issues == []

    def test_rounding_discrepancy_flagged(self, aml_bridge):
        text = "The ORR was 71.8% in this analysis."
        issues = aml_bridge.verify_manuscript_statistics(text, strictness="warn")
        assert len(issues) == 1
        assert issues[0].severity == "warning"

    def test_off_strictness_returns_empty(self, aml_bridge):
        text = "The ORR was 10.0%."
        issues = aml_bridge.verify_manuscript_statistics(text, strictness="off")
        assert issues == []
