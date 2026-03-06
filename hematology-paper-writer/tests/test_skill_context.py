"""
Tests for SkillContext — the cross-phase context persistence layer.

Covers: save, load, empty-on-missing, corrupt-recovery, unknown-key-dropping,
and round-trip fidelity.
"""

import json
import pytest
from pathlib import Path

from tools.skills._base import SkillContext


@pytest.fixture
def tmp_project(tmp_path):
    """Returns (project_name, project_dir) for a temporary project."""
    project_name = "test_aml_review"
    project_dir = tmp_path / "hpw_project"
    project_dir.mkdir()
    return project_name, project_dir


def context_path(project_name: str, project_dir: Path) -> Path:
    return project_dir / "project_notebooks" / f"{project_name}.skills_context.json"


class TestSkillContextSave:
    def test_save_creates_json(self, tmp_project):
        project_name, project_dir = tmp_project
        ctx = SkillContext(project_name=project_name)
        ctx.hypotheses = ["Azacitidine improves OS in R/R AML"]
        ctx.save(project_dir)

        path = context_path(project_name, project_dir)
        assert path.exists(), "JSON file should be created on save()"

    def test_save_creates_parent_directories(self, tmp_path):
        project_name = "nested_project"
        project_dir = tmp_path / "deep" / "nested"
        project_dir.mkdir(parents=True)
        ctx = SkillContext(project_name=project_name)
        ctx.save(project_dir)  # should not raise even if project_notebooks/ absent
        assert context_path(project_name, project_dir).exists()

    def test_save_serializes_all_fields(self, tmp_project):
        project_name, project_dir = tmp_project
        ctx = SkillContext(project_name=project_name)
        ctx.hypotheses = ["H1", "H2"]
        ctx.quality_scores = {"prisma": 0.92}
        ctx.journal_fit_score = 0.85
        ctx.save(project_dir)

        raw = json.loads(context_path(project_name, project_dir).read_text())
        assert raw["hypotheses"] == ["H1", "H2"]
        assert raw["quality_scores"] == {"prisma": 0.92}
        assert raw["journal_fit_score"] == 0.85


class TestSkillContextLoad:
    def test_load_returns_empty_on_missing_file(self, tmp_project):
        project_name, project_dir = tmp_project
        ctx = SkillContext.load(project_name, project_dir)
        assert ctx.project_name == project_name
        assert ctx.hypotheses == []
        assert ctx.quality_scores == {}

    def test_load_recovers_from_corrupt_json(self, tmp_project):
        project_name, project_dir = tmp_project
        path = context_path(project_name, project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{invalid json :::}")  # corrupt

        ctx = SkillContext.load(project_name, project_dir)  # must not raise
        assert ctx.project_name == project_name
        assert ctx.hypotheses == []

    def test_load_drops_unknown_keys(self, tmp_project):
        """Forward-compatibility: JSON with extra keys should not raise."""
        project_name, project_dir = tmp_project
        path = context_path(project_name, project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "project_name": project_name,
            "hypotheses": ["H1"],
            "future_field_not_in_dataclass": "some value",  # unknown key
        }
        path.write_text(json.dumps(data))

        ctx = SkillContext.load(project_name, project_dir)  # must not raise
        assert ctx.hypotheses == ["H1"]

    def test_load_recovers_from_empty_file(self, tmp_project):
        project_name, project_dir = tmp_project
        path = context_path(project_name, project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")  # empty file

        ctx = SkillContext.load(project_name, project_dir)  # must not raise
        assert ctx.project_name == project_name


class TestSkillContextRoundTrip:
    def test_round_trip_preserves_all_fields(self, tmp_project):
        project_name, project_dir = tmp_project
        original = SkillContext(project_name=project_name)
        original.hypotheses = ["H1", "H2"]
        original.research_gaps = ["Gap A"]
        original.study_design = {"type": "systematic_review", "population": "AML"}
        original.statistical_plan = {"methods": ["KM", "log-rank"]}
        original.journal_fit_score = 0.82
        original.draft_sections = {"introduction": "AML is..."}
        original.figure_descriptions = ["Figure 1: PRISMA flow"]
        original.prose_issues = ["Passive voice §2.3"]
        original.quality_scores = {"prisma_compliance": 0.94}
        original.review_comments = ["Expand discussion"]
        original.slide_outline = {"slides": [{"title": "Background", "bullets": ["AML"]}]}
        original.grant_sections = {"specific_aims": "We propose..."}

        original.save(project_dir)
        loaded = SkillContext.load(project_name, project_dir)

        assert loaded.hypotheses == original.hypotheses
        assert loaded.research_gaps == original.research_gaps
        assert loaded.study_design == original.study_design
        assert loaded.statistical_plan == original.statistical_plan
        assert loaded.journal_fit_score == original.journal_fit_score
        assert loaded.draft_sections == original.draft_sections
        assert loaded.figure_descriptions == original.figure_descriptions
        assert loaded.prose_issues == original.prose_issues
        assert loaded.quality_scores == original.quality_scores
        assert loaded.review_comments == original.review_comments
        assert loaded.slide_outline == original.slide_outline
        assert loaded.grant_sections == original.grant_sections
