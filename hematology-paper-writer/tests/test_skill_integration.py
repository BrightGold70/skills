"""
Cross-phase SkillContext integration tests.

Verifies that skills from different phases share and accumulate state
correctly via a single SkillContext instance persisted to disk.
"""

import pytest
from pathlib import Path

from tools.skills._base import SkillContext
from tools.skills.hypothesis_generator import HypothesisGenerator
from tools.skills.statistical_analyst import StatisticalAnalyst
from tools.skills.scientific_writer import ScientificWriter
from tools.skills.critical_thinker import CriticalThinker
from tools.skills.peer_reviewer import PeerReviewer
from tools.skills.academic_writer import AcademicWriter
from tools.skills.scientific_visualizer import ScientificVisualizer
from tools.skills.slide_generator import SlideGenerator
from tools.skills.content_researcher import ContentResearcher


class TestPhase1To2ContextFlow:
    """Phase 1 (hypotheses) → Phase 2 (stats plan) share same context."""

    def test_hypotheses_flow_to_phase2(self, tmp_path):
        ctx = SkillContext(project_name="flow_test")

        HypothesisGenerator(context=ctx).generate(
            topic="venetoclax in AML", disease="aml", n=2
        )
        assert len(ctx.hypotheses) == 2

        StatisticalAnalyst(context=ctx).analyze(
            data_description="AML cohort n=120",
            study_type="cohort",
            primary_endpoint="OS",
            sample_size=120,
        )
        assert ctx.statistical_plan != {}

        ctx.save(tmp_path)
        loaded = SkillContext.load("flow_test", tmp_path)
        assert len(loaded.hypotheses) == 2
        assert loaded.statistical_plan != {}

    def test_context_accumulates_across_phases(self, tmp_path):
        ctx = SkillContext(project_name="accumulate_test")

        # Phase 1
        HypothesisGenerator(context=ctx).generate(topic="asciminib CML", disease="cml", n=1)
        ContentResearcher(context=ctx).identify_gaps(topic="asciminib", disease="cml")
        assert len(ctx.hypotheses) >= 1
        assert len(ctx.research_gaps) >= 1

        # Phase 2
        StatisticalAnalyst(context=ctx).analyze(
            data_description="CML cohort", study_type="cohort",
            primary_endpoint="MMR", sample_size=80,
        )

        # Phase 4: write section
        ScientificWriter(context=ctx).write_section(
            "results", disease="CML", n="80", primary_endpoint="MMR",
            primary_result="achieved in 65%", ci="58–72%", p_value="<0.001",
        )
        assert "results" in ctx.draft_sections

        ctx.save(tmp_path)
        loaded = SkillContext.load("accumulate_test", tmp_path)
        assert "results" in loaded.draft_sections
        assert len(loaded.hypotheses) >= 1


class TestPhase4To8ContextFlow:
    """Phase 4 (draft) → Phase 5 (quality) → Phase 8 (peer review) flow."""

    def test_quality_and_review_share_context(self, tmp_path):
        ctx = SkillContext(project_name="quality_review_test")

        # Phase 4: draft
        text = (
            "Patients with AML were enrolled. The CR rate was 45% (95% CI, 38–52%). "
            "Limitations of this study include its retrospective design."
        )
        AcademicWriter(context=ctx).transform_to_prose(
            "• CR rate 45%\n• retrospective design", section="results"
        )

        # Phase 5: quality
        result = CriticalThinker(context=ctx).evaluate(
            text=text, study_type="retrospective", focus="all"
        )
        assert "critical_thinking" in ctx.quality_scores
        assert result["score"] >= 0.0

        # Phase 8: peer review
        PeerReviewer(context=ctx).review(
            text=text, journal="Blood", study_type="retrospective"
        )

        ctx.save(tmp_path)
        loaded = SkillContext.load("quality_review_test", tmp_path)
        assert "critical_thinking" in loaded.quality_scores
        assert isinstance(loaded.review_comments, list)

    def test_reviewer_response_from_saved_context(self, tmp_path):
        ctx = SkillContext(project_name="response_test")
        PeerReviewer(context=ctx).review(
            text="Methods were applied. No sample size calculation was provided.",
        )
        ctx.save(tmp_path)

        loaded = SkillContext.load("response_test", tmp_path)
        ctx2 = loaded
        responses = PeerReviewer(context=ctx2).generate_response_points()
        assert isinstance(responses, list)
        assert len(responses) > 0


class TestVisualizationAndDisseminationFlow:
    """Phase 4/9: figures + slides accumulate across skill calls."""

    def test_figure_descriptions_accumulate(self, tmp_path):
        ctx = SkillContext(project_name="viz_test")

        ScientificVisualizer(context=ctx).describe_figure(
            "kaplan_meier",
            title="Overall Survival",
            n_patients="120",
            disease="AML",
            treatment="venetoclax + azacitidine",
            endpoint="OS",
        )
        ScientificVisualizer(context=ctx).describe_figure(
            "waterfall",
            title="Best Response",
            n_patients="120",
            endpoint="BM blast reduction",
        )

        assert len(ctx.figure_descriptions) == 2

        ctx.save(tmp_path)
        loaded = SkillContext.load("viz_test", tmp_path)
        assert len(loaded.figure_descriptions) == 2

    def test_slide_outline_written_to_context(self, tmp_path):
        ctx = SkillContext(project_name="slides_test")

        outline = SlideGenerator(context=ctx).generate_outline(
            format="oral_10min",
            title="Novel AML Study",
            authors="Kim et al.",
            conference="ASH",
            year="2026",
            primary_endpoint="CR rate",
            primary_result="45%",
            ci="38–52%",
            conclusion_statement=(
                "Venetoclax + azacitidine demonstrates high CR rate in elderly AML."
            ),
        )

        assert len(outline) == 9  # oral_10min has 9 slides
        assert ctx.slide_outline is not None
        assert len(ctx.slide_outline) == 9

        ctx.save(tmp_path)
        loaded = SkillContext.load("slides_test", tmp_path)
        assert len(loaded.slide_outline) == 9
        assert loaded.slide_outline[0]["title"] == "Title Slide"
