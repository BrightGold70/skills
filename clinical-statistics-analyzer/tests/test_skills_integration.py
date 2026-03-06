"""
tests/test_skills_integration.py

≥40 tests for the CSA scientific skills integration layer.
Covers: _base.py, ROutputInterpreter, pre-analysis skills,
post-analysis skills, and integration hooks.

Run with:
    pytest tests/test_skills_integration.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_output_dir(tmp_path: Path) -> Path:
    """Create a minimal CSA output dir structure."""
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    return tmp_path


def make_context(study_name="TEST", disease="aml"):
    from scripts.crf_pipeline.skills import CSASkillContext
    return CSASkillContext(study_name=study_name, disease=disease)


# ── §9.1 _base.py tests (10) ──────────────────────────────────────────────────

class TestCSASkillContext:

    def test_save_and_load_roundtrip(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        od = make_output_dir(tmp_path)
        ctx = CSASkillContext(study_name="STUDY1", disease="aml")
        ctx.hypotheses = ["H0: no effect", "H1: effect exists"]
        ctx.methods_prose = "Kaplan-Meier was used."
        ctx.save(od)

        loaded = CSASkillContext.load("STUDY1", od)
        assert loaded.study_name == "STUDY1"
        assert loaded.disease == "aml"
        assert loaded.hypotheses == ["H0: no effect", "H1: effect exists"]
        assert loaded.methods_prose == "Kaplan-Meier was used."

    def test_load_nonexistent_returns_empty(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        ctx = CSASkillContext.load("NONEXISTENT", tmp_path)
        assert ctx.study_name == "NONEXISTENT"
        assert ctx.hypotheses == []
        assert ctx.key_statistics == {}

    def test_load_nonexistent_does_not_raise(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        try:
            CSASkillContext.load("X", tmp_path)
        except Exception as exc:
            pytest.fail(f"load() raised unexpectedly: {exc}")

    def test_load_corrupt_json_returns_empty(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        od = make_output_dir(tmp_path)
        corrupt = od / "data" / "CORRUPT.csa_skills_context.json"
        corrupt.write_text("{ invalid json :::}")
        ctx = CSASkillContext.load("CORRUPT", od)
        assert ctx.key_statistics == {}

    def test_load_unknown_keys_dropped(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        od = make_output_dir(tmp_path)
        path = od / "data" / "FUTURE.csa_skills_context.json"
        data = {"study_name": "FUTURE", "disease": "cml", "future_field": "ignored"}
        path.write_text(json.dumps(data))
        ctx = CSASkillContext.load("FUTURE", od)
        assert ctx.study_name == "FUTURE"
        assert not hasattr(ctx, "future_field")

    def test_default_lists_are_not_none(self):
        from scripts.crf_pipeline.skills import CSASkillContext
        ctx = CSASkillContext(study_name="X")
        assert ctx.hypotheses is not None
        assert ctx.assumption_warnings is not None
        assert ctx.key_statistics is not None
        assert ctx.protocol_gaps is not None
        assert ctx.scripts_run is not None

    def test_default_methods_prose_is_empty_string(self):
        from scripts.crf_pipeline.skills import CSASkillContext
        ctx = CSASkillContext(study_name="X")
        assert ctx.methods_prose == ""

    def test_save_creates_data_subdir(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        ctx = CSASkillContext(study_name="S1", disease="hct")
        ctx.save(tmp_path)
        assert (tmp_path / "data" / "S1.csa_skills_context.json").exists()

    def test_context_disease_default(self):
        from scripts.crf_pipeline.skills import CSASkillContext
        ctx = CSASkillContext(study_name="X")
        assert ctx.disease == "unknown"

    def test_key_statistics_serialises_floats(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        od = make_output_dir(tmp_path)
        ctx = CSASkillContext(study_name="FLOAT", disease="aml")
        ctx.key_statistics = {"os_median_months": {"value": 18.4, "unit": "months"}}
        ctx.save(od)
        loaded = CSASkillContext.load("FLOAT", od)
        assert loaded.key_statistics["os_median_months"]["value"] == pytest.approx(18.4)


# ── §9.2 ROutputInterpreter tests (12) ───────────────────────────────────────

class TestROutputInterpreter:

    def _make_cox_csv(self, path: Path, hr=0.62, p=0.006):
        path.write_text(
            "variable,hr,hr_lower,hr_upper,p_value,n_events\n"
            f"OS,{hr},0.44,0.87,{p},45\n"
            "Age,1.02,0.99,1.05,0.12,45\n"
        )

    def _make_fg_csv(self, path: Path):
        path.write_text(
            "cause,shr,shr_lower,shr_upper,p_value\n"
            "GRFS,0.78,0.64,0.91,0.004\n"
            "aGVHD,0.55,0.42,0.71,0.001\n"
        )

    def _make_ss_csv(self, path: Path, n=120):
        path.write_text(
            "parameter,value\n"
            f"n_total,{n}\n"
            "alpha,0.05\n"
        )

    def test_cox_csv_extracts_os_hr(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        assert "os_hr" in ctx.key_statistics
        assert ctx.key_statistics["os_hr"]["value"] == pytest.approx(0.62)

    def test_cox_csv_includes_p_value(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv", hr=0.55, p=0.001)
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        assert ctx.key_statistics["os_hr"]["p_value"] == pytest.approx(0.001)

    def test_finegray_csv_extracts_grfs(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_fg_csv(od / "FineGray_GRFS.csv")
        ctx = make_context(disease="hct")
        ROutputInterpreter(context=ctx).interpret(od)
        assert "grfs_event_rate" in ctx.key_statistics

    def test_finegray_csv_extracts_agvhd(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_fg_csv(od / "FineGray_GVHD.csv")
        ctx = make_context(disease="hct")
        ROutputInterpreter(context=ctx).interpret(od)
        assert "agvhd_grade2_4_rate" in ctx.key_statistics

    def test_samplesize_csv_extracts_n_total(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_ss_csv(od / "SampleSize_AML.csv", n=87)
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        assert "n_total" in ctx.key_statistics
        assert ctx.key_statistics["n_total"]["value"] == 87

    def test_missing_csv_returns_empty_no_raise(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        ctx = make_context()
        try:
            ROutputInterpreter(context=ctx).interpret(od)
        except Exception as exc:
            pytest.fail(f"interpret() raised: {exc}")
        # key_statistics may be empty — that's fine
        assert isinstance(ctx.key_statistics, dict)

    def test_sidecar_json_written_to_data_dir(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        sidecars = list((od / "data").glob("*_stats.json"))
        assert len(sidecars) >= 1

    def test_sidecar_has_key_statistics_field(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        for sidecar in (od / "data").glob("*_stats.json"):
            data = json.loads(sidecar.read_text())
            assert "key_statistics" in data
            assert "disease_specific" in data
            assert "analysis_notes" in data

    def test_stat_value_has_value_field(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        for v in ctx.key_statistics.values():
            assert "value" in v

    def test_multiple_csvs_merged(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        self._make_ss_csv(od / "SampleSize_AML.csv")
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        assert "os_hr" in ctx.key_statistics
        assert "n_total" in ctx.key_statistics

    def test_disease_specific_is_empty_dict(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        ctx = make_context()
        ROutputInterpreter(context=ctx).interpret(od)
        for sidecar in (od / "data").glob("*_stats.json"):
            data = json.loads(sidecar.read_text())
            assert data["disease_specific"] == {}

    def test_interpret_updates_context_key_statistics(self, tmp_path):
        from scripts.crf_pipeline.skills import ROutputInterpreter
        od = make_output_dir(tmp_path)
        self._make_cox_csv(od / "Cox_OS_Analysis.csv")
        ctx = make_context()
        returned_ctx = ROutputInterpreter(context=ctx).interpret(od)
        assert returned_ctx is ctx
        assert len(ctx.key_statistics) > 0


# ── §9.3 Pre-analysis skills tests (8) ───────────────────────────────────────

class TestPreAnalysisSkills:

    def test_statistical_analyst_aml_includes_finegray(self):
        from scripts.crf_pipeline.skills import StatisticalAnalyst
        ctx = make_context(disease="aml")
        plan = StatisticalAnalyst(context=ctx).analyze(disease="aml")
        all_methods = " ".join(plan.get("methods", []))
        assert "Fine-Gray" in all_methods or "competing" in all_methods.lower()

    def test_statistical_analyst_hct_includes_nih2014(self):
        from scripts.crf_pipeline.skills import StatisticalAnalyst
        ctx = make_context(disease="hct")
        plan = StatisticalAnalyst(context=ctx).analyze(disease="hct")
        all_text = json.dumps(plan)
        assert "NIH 2014" in all_text or "Fine-Gray" in all_text

    def test_statistical_analyst_unknown_disease_returns_non_empty(self):
        from scripts.crf_pipeline.skills import StatisticalAnalyst
        ctx = make_context(disease="unknown")
        plan = StatisticalAnalyst(context=ctx).analyze(disease="xyz")
        assert isinstance(plan, dict)
        assert len(plan) > 0

    def test_hypothesis_generator_aml_returns_3_hypotheses(self):
        from scripts.crf_pipeline.skills import HypothesisGenerator
        ctx = make_context(disease="aml")
        hyps = HypothesisGenerator(context=ctx).generate(disease="aml", endpoint="OS")
        assert len(hyps) == 3

    def test_hypothesis_generator_cml_includes_mmr(self):
        from scripts.crf_pipeline.skills import HypothesisGenerator
        ctx = make_context(disease="cml")
        hyps = HypothesisGenerator(context=ctx).generate(disease="cml")
        combined = " ".join(hyps)
        assert "MMR" in combined or "molecular" in combined.lower()

    def test_critical_thinker_small_n_generates_warning(self):
        from scripts.crf_pipeline.skills import CriticalThinker
        ctx = make_context(disease="aml")
        warnings = CriticalThinker(context=ctx).check_assumptions(disease="aml", n=15)
        combined = " ".join(warnings)
        assert "small" in combined.lower() or "n=15" in combined

    def test_critical_thinker_hct_includes_competing_risks(self):
        from scripts.crf_pipeline.skills import CriticalThinker
        ctx = make_context(disease="hct")
        warnings = CriticalThinker(context=ctx).check_assumptions(disease="hct", n=80)
        combined = " ".join(warnings)
        assert "Fine-Gray" in combined or "competing" in combined.lower()

    def test_critical_thinker_no_warnings_returns_list(self):
        from scripts.crf_pipeline.skills import CriticalThinker
        ctx = make_context(disease="mds")
        try:
            warnings = CriticalThinker(context=ctx).check_assumptions(disease="mds", n=100)
        except Exception as exc:
            pytest.fail(f"check_assumptions raised: {exc}")
        assert isinstance(warnings, list)


# ── §9.4 Post-analysis skills tests (8) ──────────────────────────────────────

class TestPostAnalysisSkills:

    def test_scientific_writer_aml_contains_kaplan_meier(self):
        from scripts.crf_pipeline.skills import StatisticalAnalyst, ScientificWriter
        ctx = make_context(disease="aml")
        StatisticalAnalyst(context=ctx).analyze(disease="aml")
        prose = ScientificWriter(context=ctx).draft_methods()
        assert "Kaplan-Meier" in prose

    def test_scientific_writer_hct_contains_finegray(self):
        from scripts.crf_pipeline.skills import StatisticalAnalyst, ScientificWriter
        ctx = make_context(disease="hct")
        StatisticalAnalyst(context=ctx).analyze(disease="hct")
        prose = ScientificWriter(context=ctx).draft_methods()
        assert "Fine-Gray" in prose

    def test_eln_mapper_annotates_known_key(self):
        from scripts.crf_pipeline.skills import ELNGuidelineMapper
        ctx = make_context(disease="aml")
        ctx.key_statistics = {"eln_favorable_pct": {"value": 0.42}}
        ELNGuidelineMapper(context=ctx).map()
        assert "eln_favorable_pct" in ctx.eln_annotations

    def test_eln_mapper_no_matching_keys_does_not_raise(self):
        from scripts.crf_pipeline.skills import ELNGuidelineMapper
        ctx = make_context(disease="aml")
        ctx.key_statistics = {"custom_key": {"value": 1.0}}
        try:
            ELNGuidelineMapper(context=ctx).map()
        except Exception as exc:
            pytest.fail(f"map() raised: {exc}")
        assert ctx.eln_annotations == {}

    def test_protocol_checker_missing_endpoint_in_gaps(self, tmp_path):
        from scripts.crf_pipeline.skills import ProtocolConsistencyChecker
        ctx = make_context(disease="aml")
        ctx.key_statistics = {}  # empty — all endpoints missing
        spec = {"primary_endpoints": ["OS", "CR rate"], "secondary_endpoints": []}
        checker = ProtocolConsistencyChecker(context=ctx)
        gaps = checker.check(protocol_spec=spec)
        assert len(gaps) >= 1

    def test_protocol_checker_all_present_empty_gaps(self, tmp_path):
        from scripts.crf_pipeline.skills import ProtocolConsistencyChecker
        ctx = make_context(disease="aml")
        ctx.key_statistics = {
            "os_median_months": {"value": 18.4},
            "cr_rate": {"value": 0.65},
        }
        spec = {"primary_endpoints": ["OS", "CR rate"], "secondary_endpoints": []}
        checker = ProtocolConsistencyChecker(context=ctx)
        gaps = checker.check(protocol_spec=spec)
        assert gaps == []

    def test_content_researcher_returns_list(self):
        from scripts.crf_pipeline.skills import ContentResearcher
        ctx = make_context(disease="aml")
        ctx.key_statistics = {"os_median_months": {"value": 18.4}, "orr": {"value": 0.68}}
        refs = ContentResearcher(context=ctx).find_citations()
        assert isinstance(refs, list)
        assert len(refs) > 0

    def test_context_persisted_after_post_skills(self, tmp_path):
        from scripts.crf_pipeline.skills import (
            ELNGuidelineMapper, ScientificWriter, StatisticalAnalyst, CSASkillContext
        )
        od = make_output_dir(tmp_path)
        ctx = make_context(disease="cml")
        StatisticalAnalyst(context=ctx).analyze(disease="cml")
        ScientificWriter(context=ctx).draft_methods()
        ELNGuidelineMapper(context=ctx).map()
        ctx.save(od)
        loaded = CSASkillContext.load("TEST", od)
        assert loaded.methods_prose != ""


# ── §9.5 Integration hook tests (6) ──────────────────────────────────────────

class TestIntegrationHooks:

    def _make_mock_result(self, disease="aml"):
        """Minimal mock of AnalysisResult."""
        class _SR:
            def __init__(self, script, success=True):
                self.script = script
                self.success = success

        class _R:
            def __init__(self):
                self.disease = disease
                self.script_results = [_SR("02_table1.R"), _SR("04_survival.R")]
                self.status = "success"

        return _R()

    def test_post_analysis_writes_sidecar(self, tmp_path):
        from scripts.crf_pipeline.skills_integration import integrate_skills_post_analysis
        od = make_output_dir(tmp_path)
        # Write a Cox CSV for ROutputInterpreter to find
        (od / "Cox_OS_Analysis.csv").write_text(
            "variable,hr,hr_lower,hr_upper,p_value,n_events\nOS,0.62,0.44,0.87,0.006,45\n"
        )
        result = self._make_mock_result("aml")
        integrate_skills_post_analysis(result, od, "TEST")
        sidecars = list((od / "data").glob("*_stats.json"))
        assert len(sidecars) >= 1

    def test_post_analysis_corrupt_output_dir_no_raise(self, tmp_path):
        from scripts.crf_pipeline.skills_integration import integrate_skills_post_analysis
        result = self._make_mock_result("aml")
        try:
            integrate_skills_post_analysis(result, tmp_path / "nonexistent", "X")
        except Exception as exc:
            pytest.fail(f"integrate_skills_post_analysis raised: {exc}")

    def test_post_analysis_saves_context(self, tmp_path):
        from scripts.crf_pipeline.skills import CSASkillContext
        from scripts.crf_pipeline.skills_integration import integrate_skills_post_analysis
        od = make_output_dir(tmp_path)
        result = self._make_mock_result("cml")
        integrate_skills_post_analysis(result, od, "STUDY_CML")
        ctx_path = od / "data" / "STUDY_CML.csa_skills_context.json"
        assert ctx_path.exists()

    def test_pre_analysis_returns_context(self, tmp_path):
        from scripts.crf_pipeline.skills_integration import integrate_skills_pre_analysis
        od = make_output_dir(tmp_path)
        ctx = integrate_skills_pre_analysis(
            study_name="PRE_TEST", disease="aml", output_dir=od,
            primary_endpoint="OS", n_estimated=60
        )
        assert ctx is not None

    def test_pre_analysis_populates_hypotheses(self, tmp_path):
        from scripts.crf_pipeline.skills_integration import integrate_skills_pre_analysis
        od = make_output_dir(tmp_path)
        ctx = integrate_skills_pre_analysis(
            study_name="HYP_TEST", disease="hct", output_dir=od,
        )
        assert hasattr(ctx, "hypotheses")
        assert isinstance(ctx.hypotheses, list)

    def test_cli_hypothesis_help_exits_zero(self):
        """CLI subcommand --help returns exit code 0."""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "scripts.crf_pipeline", "hypothesis", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        assert "hypothesis" in result.stdout.lower() or "disease" in result.stdout.lower()
