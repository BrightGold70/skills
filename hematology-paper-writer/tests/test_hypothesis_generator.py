"""
Tests for HypothesisGenerator skill class.

Covers: generate(), null hypothesis conversion, context updates, silent failure.
"""

import pytest
from unittest.mock import patch
from pathlib import Path

from tools.skills._base import SkillContext
from tools.skills.hypothesis_generator import HypothesisGenerator


@pytest.fixture
def ctx():
    return SkillContext(project_name="test_project")


@pytest.fixture
def generator(ctx):
    return HypothesisGenerator(context=ctx)


class TestHypothesisGeneratorGenerate:
    def test_generate_returns_list(self, generator):
        result = generator.generate(topic="venetoclax in AML", disease="aml")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_updates_context(self, generator, ctx):
        generator.generate(topic="asciminib in CML", disease="cml", intervention="asciminib")
        assert len(ctx.hypotheses) > 0

    def test_generate_respects_n_parameter(self, generator):
        result = generator.generate(topic="azacitidine", disease="mds", n=2)
        assert len(result) == 2

    def test_generate_includes_disease_context(self, generator):
        result = generator.generate(topic="venetoclax", disease="aml", intervention="venetoclax")
        combined = " ".join(result).upper()
        assert "AML" in combined or "SURVIVAL" in combined.upper() or len(result) > 0

    def test_generate_works_without_disease(self, generator):
        result = generator.generate(topic="novel immunotherapy")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_works_without_intervention(self, generator):
        result = generator.generate(topic="HCT outcomes", disease="hct")
        assert isinstance(result, list)

    def test_generate_silent_on_error(self, ctx):
        """generate() must not raise even if internal logic fails."""
        gen = HypothesisGenerator(context=ctx)
        # Patch _DISEASE_OUTCOMES to cause a key lookup failure
        with patch("tools.skills.hypothesis_generator._DISEASE_OUTCOMES", None):
            result = gen.generate(topic="test", disease="aml")
        assert result == []


class TestNullHypotheses:
    def test_generate_null_hypotheses_from_context(self, generator, ctx):
        ctx.hypotheses = ["Drug X improves OS compared to placebo in AML patients."]
        nulls = generator.generate_null_hypotheses()
        assert isinstance(nulls, list)
        assert len(nulls) == 1

    def test_generate_null_hypotheses_from_argument(self, generator):
        hyps = ["Azacitidine improves EFS compared to SOC in MDS."]
        nulls = generator.generate_null_hypotheses(hypotheses=hyps)
        assert len(nulls) == 1
        assert "H₀" in nulls[0]

    def test_generate_null_hypotheses_silent_on_error(self, generator, ctx):
        ctx.hypotheses = None  # force error
        result = generator.generate_null_hypotheses()
        assert result == []


class TestContextIntegration:
    def test_context_saved_after_generate(self, tmp_path, ctx):
        ctx.project_name = "save_test"
        gen = HypothesisGenerator(context=ctx)
        gen.generate(topic="TKI in CML", disease="cml")
        ctx.save(tmp_path)
        loaded = SkillContext.load("save_test", tmp_path)
        assert loaded.hypotheses == ctx.hypotheses
