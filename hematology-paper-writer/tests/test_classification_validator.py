"""
Tests for ClassificationValidator — hpw-classification-validator feature.

Covers: AML WHO/ICC classification, ELN 2022 risk, WHO/ICC discordance,
CML ELN 2025 milestones, acute/chronic GVHD grading, prose generation,
manifest write, SkillContext round-trip.

27 tests targeting the design spec success criteria.
"""

import json
import pytest
from pathlib import Path

from tools.skills._base import SkillContext
from tools.skills.classification_validator import (
    AMLClassificationResult,
    ClassificationValidator,
    CMLMilestoneResult,
    GVHDResult,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_project(tmp_path):
    """Returns (project_name, project_dir) for a temporary HPW project."""
    name = "test_classification_project"
    project_dir = tmp_path / "hpw_project"
    project_dir.mkdir()
    return name, project_dir


@pytest.fixture
def validator(tmp_project):
    """Returns a ClassificationValidator with an empty SkillContext."""
    name, project_dir = tmp_project
    ctx = SkillContext(project_name=name)
    return ClassificationValidator(context=ctx)


# ── AML Classification — WHO 2022 / ICC 2022 ──────────────────────────────────

class TestAMLClassification:
    def test_cbf_t8_21_favorable(self, validator):
        """t(8;21) → AML with RUNX1::RUNX1T1, ELN Favorable (test 1)."""
        result = validator.classify_aml({
            "blasts_pct": 35,
            "cytogenetics": "t(8;21)",
        })
        assert result.who_2022 == "AML with RUNX1::RUNX1T1"
        assert result.icc_2022 == "AML with RUNX1::RUNX1T1"
        assert result.eln_2022_risk == "Favorable"
        assert result.is_concordant

    def test_apl_pml_rara(self, validator):
        """t(15;17) → APL with PML::RARA, concordant (test 2)."""
        result = validator.classify_aml({
            "blasts_pct": 40,
            "cytogenetics": "t(15;17)",
        })
        assert result.who_2022 == "APL with PML::RARA"
        assert result.icc_2022 == "APL with PML::RARA"
        assert result.is_concordant

    def test_npm1_flt3_itd_low_favorable(self, validator):
        """NPM1+/FLT3-ITD(low AR=0.3) → ELN Favorable (test 3)."""
        result = validator.classify_aml({
            "blasts_pct": 30,
            "cytogenetics": "normal",
            "npm1": True,
            "flt3_itd": True,
            "flt3_itd_allelic_ratio": 0.3,
        })
        assert result.who_2022 == "AML with NPM1 mutation"
        assert result.eln_2022_risk == "Favorable"

    def test_npm1_flt3_itd_high_intermediate(self, validator):
        """NPM1+/FLT3-ITD(high AR=0.7) → ELN Intermediate (test 4)."""
        result = validator.classify_aml({
            "blasts_pct": 30,
            "cytogenetics": "normal",
            "npm1": True,
            "flt3_itd": True,
            "flt3_itd_allelic_ratio": 0.7,
        })
        assert result.eln_2022_risk == "Intermediate"
        # High AR (≥0.5) means NPM1 is NOT favorable — no NPM1 factor added
        assert not any("Favorable" in f for f in result.eln_factors)

    def test_tp53_high_blasts_adverse(self, validator):
        """TP53+ blasts 25% → WHO='AML with TP53 mutation', ELN Adverse (test 5)."""
        result = validator.classify_aml({
            "blasts_pct": 25,
            "cytogenetics": "normal",
            "tp53": True,
        })
        assert result.who_2022 == "AML with TP53 mutation"
        assert result.icc_2022 == "AML with TP53 mutation"
        assert result.eln_2022_risk == "Adverse"
        assert "TP53" in " ".join(result.eln_factors)

    def test_tp53_low_blasts_who_icc_discordance(self, validator):
        """TP53+ blasts 15% → ICC='MDS/AML', discordant (test 6 — key divergence)."""
        result = validator.classify_aml({
            "blasts_pct": 15,
            "cytogenetics": "normal",
            "tp53": True,
        })
        assert result.icc_2022 == "MDS/AML"
        assert not result.is_concordant
        assert "TP53" in result.discordance_reason or "10–19%" in result.discordance_reason

    def test_asxl1_adverse(self, validator):
        """ASXL1+ normal karyotype → ELN Adverse (test 7)."""
        result = validator.classify_aml({
            "blasts_pct": 25,
            "cytogenetics": "normal",
            "asxl1": True,
        })
        assert result.eln_2022_risk == "Adverse"
        assert any("ASXL1" in f for f in result.eln_factors)

    def test_aml_nos_concordant(self, validator):
        """Blasts 22%, no markers → WHO=ICC='AML NOS', concordant (test 8)."""
        result = validator.classify_aml({
            "blasts_pct": 22,
            "cytogenetics": "normal",
        })
        assert result.who_2022 == "AML NOS"
        assert result.icc_2022 == "AML NOS"
        assert result.is_concordant

    def test_therapy_related_aml(self, validator):
        """therapy_related flag → 'AML, therapy-related' (WHO and ICC)."""
        result = validator.classify_aml({
            "blasts_pct": 20,
            "therapy_related": True,
        })
        assert result.who_2022 == "AML, therapy-related"
        assert result.icc_2022 == "AML, therapy-related"
        assert result.is_concordant

    def test_npm1_low_blasts_icc_excluded(self, validator):
        """NPM1+ blasts 8% → ICC does not classify as AML (blasts <10%) (test from spec)."""
        result = validator.classify_aml({
            "blasts_pct": 8,
            "cytogenetics": "normal",
            "npm1": True,
        })
        # WHO gives AML with NPM1; ICC cannot because blasts <10%
        assert result.who_2022 == "AML with NPM1 mutation"
        assert result.icc_2022 != "AML with NPM1 mutation"
        assert not result.is_concordant


# ── Cohort-Level Discordance ───────────────────────────────────────────────────

class TestDiscordanceReport:
    def test_all_concordant(self, validator):
        """All concordant results → discordant_n=0 (test 9)."""
        results = [
            AMLClassificationResult(
                who_2022="AML NOS", icc_2022="AML NOS",
                eln_2022_risk="Intermediate", is_concordant=True,
            )
            for _ in range(5)
        ]
        report = validator.compare_who_icc(results)
        assert report.discordant_n == 0
        assert report.concordance_rate == 1.0

    def test_mixed_cohort_discordant_pairs(self, validator):
        """Mixed cohort includes TP53 discordant pair (test 10)."""
        concordant = [
            AMLClassificationResult(
                who_2022="AML NOS", icc_2022="AML NOS",
                eln_2022_risk="Intermediate", is_concordant=True,
            )
        ] * 8
        discordant = [
            AMLClassificationResult(
                who_2022="AML with TP53 mutation",
                icc_2022="MDS/AML",
                eln_2022_risk="Adverse",
                is_concordant=False,
                discordance_reason="TP53 mutation with blasts 15% (10–19%): ICC classifies as MDS/AML",
            )
        ] * 2
        report = validator.compare_who_icc(concordant + discordant)
        assert report.discordant_n == 2
        assert report.total_n == 10
        assert abs(report.concordance_rate - 0.8) < 0.01
        tp53_pair = next(
            (p for p in report.discordant_pairs if "TP53" in p["who"]), None
        )
        assert tp53_pair is not None

    def test_empty_cohort(self, validator):
        """Empty input → concordance_rate=1.0, no crash."""
        report = validator.compare_who_icc([])
        assert report.total_n == 0
        assert report.concordance_rate == 1.0


# ── CML Milestone Assessment ───────────────────────────────────────────────────

class TestCMLMilestone:
    def test_3month_optimal(self, validator):
        """BCR::ABL1 8% at 3m with CHR → Optimal (test 11)."""
        result = validator.classify_cml_milestone({
            "months": 3, "bcr_abl_is": 8.0, "achieved_chr": True,
        })
        assert result.status == "Optimal"

    def test_6month_warning(self, validator):
        """BCR::ABL1 5% at 6m → Warning (test 12)."""
        result = validator.classify_cml_milestone({
            "months": 6, "bcr_abl_is": 5.0, "achieved_chr": True,
        })
        assert result.status == "Warning"

    def test_12month_optimal_mr3(self, validator):
        """BCR::ABL1 0.05% at 12m → Optimal (MR3 achieved) (test 13)."""
        result = validator.classify_cml_milestone({
            "months": 12, "bcr_abl_is": 0.05, "achieved_chr": True,
        })
        assert result.status == "Optimal"
        assert result.threshold_optimal == 0.1

    def test_12month_warning(self, validator):
        """BCR::ABL1 0.5% at 12m → Warning (test 14)."""
        result = validator.classify_cml_milestone({
            "months": 12, "bcr_abl_is": 0.5, "achieved_chr": True,
        })
        assert result.status == "Warning"

    def test_no_chr_is_failure(self, validator):
        """No CHR at 3m regardless of BCR::ABL1 → Failure (test 15)."""
        result = validator.classify_cml_milestone({
            "months": 3, "bcr_abl_is": 5.0, "achieved_chr": False,
        })
        assert result.status == "Failure"

    def test_recommendation_not_empty(self, validator):
        """Failure status includes non-empty recommendation."""
        result = validator.classify_cml_milestone({
            "months": 12, "bcr_abl_is": 5.0, "achieved_chr": True,
        })
        assert result.status == "Failure"
        assert len(result.recommendation) > 0


# ── GVHD Grading ──────────────────────────────────────────────────────────────

class TestGVHDGrading:
    def test_acute_grade_i(self, validator):
        """Skin stage 2, liver/gut 0 → Acute Grade I (test 16)."""
        result = validator.classify_gvhd({
            "type": "acute", "skin_stage": 2, "liver_stage": 0, "gut_stage": 0,
        })
        assert result.gvhd_type == "acute"
        assert result.grade == "I"

    def test_acute_grade_iii(self, validator):
        """Skin stage 3, gut stage 3 → Acute Grade III (test 17)."""
        result = validator.classify_gvhd({
            "type": "acute", "skin_stage": 3, "liver_stage": 0, "gut_stage": 3,
        })
        assert result.grade == "III"

    def test_acute_grade_iv(self, validator):
        """Gut stage 4 → Acute Grade IV (test 18)."""
        result = validator.classify_gvhd({
            "type": "acute", "skin_stage": 0, "liver_stage": 0, "gut_stage": 4,
        })
        assert result.grade == "IV"
        assert result.overall_score == 4

    def test_chronic_mild(self, validator):
        """1 organ score 1, lung 0 → Chronic Mild (test 19)."""
        result = validator.classify_gvhd({
            "type": "chronic", "skin_score": 1,
        })
        assert result.gvhd_type == "chronic"
        assert result.grade == "Mild"

    def test_chronic_severe_lung(self, validator):
        """Lung score 3 → Chronic Severe (test 20)."""
        result = validator.classify_gvhd({
            "type": "chronic", "lung_score": 3,
        })
        assert result.grade == "Severe"
        assert result.overall_score == 3

    def test_chronic_no_gvhd(self, validator):
        """All scores 0 → Chronic grade 'None'."""
        result = validator.classify_gvhd({"type": "chronic"})
        assert result.grade == "None"


# ── Prose Generation ───────────────────────────────────────────────────────────

class TestProseGeneration:
    def test_aml_methods_contains_required_terms(self, validator):
        """AML methods paragraph contains WHO, ICC, ELN keywords (test 21)."""
        para = validator.generate_methods_paragraph("AML")
        assert "WHO" in para
        assert "ICC" in para
        assert "ELN" in para
        assert "2022" in para

    def test_cml_methods_contains_bcr_abl1(self, validator):
        """CML methods paragraph contains BCR::ABL1 and ELN 2025 (test 22)."""
        para = validator.generate_methods_paragraph("CML")
        assert "BCR::ABL1" in para
        assert "2025" in para

    def test_hct_methods_contains_nih(self, validator):
        """HCT methods paragraph contains NIH and GVHD."""
        para = validator.generate_methods_paragraph("HCT")
        assert "NIH" in para
        assert "GVHD" in para.upper() or "graft" in para.lower()

    def test_methods_persisted_to_context(self, validator):
        """generate_methods_paragraph writes to draft_sections."""
        validator.generate_methods_paragraph("AML")
        assert "methods_classification_aml" in validator.context.draft_sections

    def test_results_table_three_rows(self, validator):
        """generate_results_table with 3 results → 3 data rows (test 23)."""
        results = [
            AMLClassificationResult(
                who_2022="AML NOS", icc_2022="AML NOS",
                eln_2022_risk="Intermediate", is_concordant=True,
            )
            for _ in range(3)
        ]
        table = validator.generate_results_table(results)
        # Header + separator + 3 data rows = 5 lines
        lines = [l for l in table.split("\n") if l.strip()]
        assert len(lines) == 5

    def test_results_table_empty(self, validator):
        """generate_results_table with empty list → empty string."""
        assert validator.generate_results_table([]) == ""


# ── Manifest Write ────────────────────────────────────────────────────────────

class TestManifestWrite:
    def test_creates_classification_summary_block(self, tmp_path, validator):
        """write_to_manifest creates manifest with classification_summary (test 24)."""
        manifest_path = tmp_path / "hpw_manifest.json"
        validator.write_to_manifest(manifest_path, summary={"disease": "AML", "n_patients": 50})
        data = json.loads(manifest_path.read_text())
        assert "classification_summary" in data
        assert data["classification_summary"]["disease"] == "AML"

    def test_merges_into_existing_manifest(self, tmp_path, validator):
        """write_to_manifest preserves existing keys (test 25)."""
        manifest_path = tmp_path / "hpw_manifest.json"
        existing = {"schema_version": "1.0", "tables": [{"id": "t1"}]}
        manifest_path.write_text(json.dumps(existing))

        validator.write_to_manifest(manifest_path, summary={"disease": "CML"})
        data = json.loads(manifest_path.read_text())
        assert "tables" in data                   # existing key preserved
        assert "classification_summary" in data    # new key added

    def test_creates_parent_dir_if_missing(self, tmp_path, validator):
        """write_to_manifest creates missing parent directories."""
        manifest_path = tmp_path / "subdir" / "nested" / "hpw_manifest.json"
        validator.write_to_manifest(manifest_path, summary={"disease": "HCT"})
        assert manifest_path.exists()


# ── invoke() Safety ───────────────────────────────────────────────────────────

class TestInvokeSafety:
    def test_invoke_never_raises(self, validator):
        """invoke() returns a string and never raises on empty input (test 26)."""
        result = validator.invoke("")
        assert isinstance(result, str)

    def test_invoke_truncates_long_prompt(self, validator):
        """invoke() truncates prompt to 200 chars."""
        long_prompt = "x" * 500
        result = validator.invoke(long_prompt)
        assert len(result) < 300


# ── SkillContext Round-Trip ────────────────────────────────────────────────────

class TestSkillContextRoundTrip:
    def test_classification_result_saved_and_loaded(self, tmp_project):
        """classification_result field persists across save/load (test 27)."""
        name, project_dir = tmp_project
        ctx = SkillContext(project_name=name)
        ctx.classification_result = {"disease": "AML", "n_patients": 120}
        ctx.save(project_dir)

        loaded = SkillContext.load(name, project_dir)
        assert loaded.classification_result["disease"] == "AML"
        assert loaded.classification_result["n_patients"] == 120

    def test_context_persisted_after_classify_aml(self, tmp_project):
        """classify_aml result is stored in context.classification_result."""
        name, project_dir = tmp_project
        ctx = SkillContext(project_name=name)
        v = ClassificationValidator(context=ctx)
        v.classify_aml({
            "blasts_pct": 30, "cytogenetics": "t(8;21)",
        })
        assert "last_aml" in ctx.classification_result
        assert ctx.classification_result["last_aml"]["who_2022"] == "AML with RUNX1::RUNX1T1"


# ── Nomenclature Check ────────────────────────────────────────────────────────

class TestNomenclatureCheck:
    def test_flags_bcr_abl_hyphen(self, validator):
        """BCR-ABL1 triggers BCR::ABL1 notation issue."""
        issues = validator.check_classification_nomenclature(
            "BCR-ABL1 was measured at 3 months."
        )
        assert any("BCR::ABL1" in i for i in issues)

    def test_no_issues_correct_text(self, validator):
        """Clean text with correct notation returns no nomenclature issues."""
        clean = (
            "BCR::ABL1 IS levels were assessed per ELN 2025 recommendations. "
            "Patients were classified per WHO 2022 (Khoury et al.) and ICC 2022."
        )
        issues = validator.check_classification_nomenclature(clean)
        # Should not flag BCR::ABL1 double-colon notation
        assert not any("BCR::ABL1" in i and "use" in i for i in issues)
