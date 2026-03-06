"""
Tests for CriticalThinker, PeerReviewer, and AcademicWriter skill classes.

Covers: evaluate(), identify_limitations(), review(), generate_response_points(),
        transform_to_prose(), upgrade_language(), check_passive_voice().
"""

import pytest
from unittest.mock import patch
from pathlib import Path

from tools.skills._base import SkillContext
from tools.skills.critical_thinker import CriticalThinker
from tools.skills.peer_reviewer import PeerReviewer
from tools.skills.academic_writer import AcademicWriter


@pytest.fixture
def ctx():
    return SkillContext(project_name="test_project")


@pytest.fixture
def thinker(ctx):
    return CriticalThinker(context=ctx)


@pytest.fixture
def reviewer(ctx):
    return PeerReviewer(context=ctx)


@pytest.fixture
def writer(ctx):
    return AcademicWriter(context=ctx)


# ── CriticalThinker ──────────────────────────────────────────────────────────

class TestCriticalThinkerEvaluate:
    def test_evaluate_returns_dict(self, thinker):
        result = thinker.evaluate(text="AML patients were treated.", study_type="cohort")
        assert isinstance(result, dict)
        assert "fallacies" in result
        assert "weaknesses" in result
        assert "score" in result

    def test_evaluate_updates_context(self, thinker, ctx):
        thinker.evaluate(text="We analyzed all patients.", study_type="cohort")
        assert "critical_thinking" in ctx.quality_scores

    def test_evaluate_score_is_float(self, thinker):
        result = thinker.evaluate(text="Sample text.", study_type="rct")
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 100.0

    def test_evaluate_detects_fallacy_trigger(self, thinker):
        result = thinker.evaluate(
            text="All patients responded to treatment.", study_type="cohort"
        )
        fallacy_types = [f["type"] for f in result["fallacies"]]
        assert "overgeneralization" in fallacy_types

    def test_evaluate_focus_fallacies_only(self, thinker):
        result = thinker.evaluate(text="all patients.", study_type="cohort", focus="fallacies")
        assert "fallacies" in result
        assert result["weaknesses"] == []

    def test_evaluate_silent_on_error(self, ctx):
        thinker = CriticalThinker(context=ctx)
        with patch("tools.skills.critical_thinker._FALLACY_TRIGGERS", None):
            result = thinker.evaluate(text="test", study_type="cohort")
        assert result == {}

    def test_identify_limitations_by_study_type(self, thinker):
        lims = thinker.identify_limitations("retrospective")
        assert isinstance(lims, list)
        assert len(lims) > 0
        assert any("bias" in l.lower() for l in lims)

    def test_identify_limitations_detects_single_center(self, thinker):
        lims = thinker.identify_limitations("cohort", text="This single-center study enrolled patients.")
        assert any("single-center" in l.lower() or "single" in l.lower() for l in lims)

    def test_reviewer_questions_all(self, thinker):
        questions = thinker.generate_reviewer_questions("all")
        assert isinstance(questions, list)
        assert len(questions) > 4

    def test_reviewer_questions_domain(self, thinker):
        questions = thinker.generate_reviewer_questions("statistical_rigor")
        assert isinstance(questions, list)
        assert len(questions) > 0
        # At least one question must reference statistical concepts
        combined = " ".join(questions).lower()
        assert any(kw in combined for kw in ("statistic", "sample", "p-value", "confidence", "pre-specified"))


# ── PeerReviewer ─────────────────────────────────────────────────────────────

class TestPeerReviewerReview:
    def test_review_returns_list(self, reviewer):
        result = reviewer.review(text="Methods section text.", journal="Blood")
        assert isinstance(result, list)

    def test_review_updates_context(self, reviewer, ctx):
        reviewer.review(
            text="Patients were enrolled. Methods were unclear.",
            journal="Blood",
        )
        assert isinstance(ctx.review_comments, list)

    def test_review_detects_missing_sample_size(self, reviewer):
        comments = reviewer.review(
            text="We enrolled patients and analyzed outcomes.",
            study_type="cohort",
        )
        issues = [c["issue"] for c in comments]
        assert any("sample size" in i for i in issues)

    def test_review_silent_on_error(self, ctx):
        rev = PeerReviewer(context=ctx)
        with patch("tools.skills.peer_reviewer._COMMENT_TEMPLATES", None):
            result = rev.review(text="test")
        assert result == []

    def test_generate_response_points_from_context(self, reviewer, ctx):
        ctx.review_comments = [
            {"priority": "major", "issue": "sample size"},
            {"priority": "minor", "issue": "CI reporting"},
        ]
        points = reviewer.generate_response_points()
        assert len(points) == 2
        assert "sample size" in points[0]

    def test_summarize_review_empty(self, reviewer):
        summary = reviewer.summarize_review()
        assert summary["total"] == 0
        assert summary["recommendation"] == "accept"

    def test_summarize_review_recommendation(self, reviewer, ctx):
        ctx.review_comments = [
            {"priority": "critical", "issue": "fatal flaw"},
        ]
        summary = reviewer.summarize_review()
        assert summary["recommendation"] == "reject"


# ── AcademicWriter ───────────────────────────────────────────────────────────

class TestAcademicWriter:
    def test_transform_to_prose_returns_string(self, writer):
        result = writer.transform_to_prose(
            "• Venetoclax used in AML\n• Response assessed by ELN 2022",
            section="results",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_transform_writes_to_context(self, writer, ctx):
        writer.transform_to_prose("• Drug administered IV", section="methods")
        assert "methods" in ctx.draft_sections

    def test_upgrade_language_replaces_informal(self, writer):
        text = "We showed that the drug found to improve outcomes."
        upgraded = writer.upgrade_language(text)
        assert "demonstrated" in upgraded or "identified" in upgraded

    def test_upgrade_language_returns_string_on_empty(self, writer):
        assert writer.upgrade_language("") == ""

    def test_check_passive_voice_finds_violations(self, writer):
        result = writer.check_passive_voice("We analyzed samples from 120 patients.")
        assert result["violations"] > 0
        assert not result["passed"]

    def test_check_passive_voice_clean_text(self, writer):
        result = writer.check_passive_voice("Samples were analyzed from 120 patients.")
        assert result["passed"]

    def test_get_transition_returns_string(self, writer):
        phrase = writer.get_transition("conclusion")
        assert isinstance(phrase, str)
        assert len(phrase) > 0

    def test_get_transition_unknown_type_returns_empty(self, writer):
        phrase = writer.get_transition("nonexistent_type")
        assert phrase == ""

    def test_transform_silent_on_error(self, ctx):
        w = AcademicWriter(context=ctx)
        with patch("tools.skills.academic_writer._ACADEMIC_VERB_UPGRADES", None):
            result = w.transform_to_prose("• test item")
        assert result == ""
