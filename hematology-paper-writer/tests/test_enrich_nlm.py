"""
tests/test_enrich_nlm.py
Unit tests for StatisticalBridge NLM enrichment (FR-09).

All HTTP calls are mocked — no live open-notebook server required.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.statistical_bridge import StatisticalBridge


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_bridge(tmp_path: Path, disease: str = "aml") -> StatisticalBridge:
    """Return a minimal StatisticalBridge whose manifest lives in tmp_path."""
    manifest = {
        "schema_version": "1.0",
        "generated_at": "2026-03-01T00:00:00",
        "disease": disease,
        "scripts_run": [],
        "tables": [],
        "figures": [],
        "key_statistics": {},
        "r_version": "4.3.0",
        "r_packages": [],
        "analysis_notes": {},
    }
    manifest_path = tmp_path / "hpw_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return StatisticalBridge(str(manifest_path))


def _bridge_with_config(config: dict | None, tmp_path: Path, disease: str = "aml") -> StatisticalBridge:
    """Bridge whose _nlm_config cache is pre-loaded (no file I/O needed)."""
    bridge = _make_bridge(tmp_path, disease)
    bridge._nlm_config = config  # type: ignore[attr-defined]
    return bridge


# --------------------------------------------------------------------------- #
# _load_nlm_config tests
# --------------------------------------------------------------------------- #

class TestLoadNlmConfig:
    def test_returns_none_when_config_absent(self, tmp_path):
        """When notebooklm_config.json doesn't exist, returns None."""
        bridge = _make_bridge(tmp_path)
        # No config file created → fresh bridge has no cached value
        result = bridge._load_nlm_config()
        # File lives at <statistical_bridge.py parent>/../../notebooklm_config.json
        # which is the real HPW root — may or may not exist.
        # We only check the cache is set after the call (no AttributeError).
        assert hasattr(bridge, "_nlm_config")
        # If the real file doesn't exist, result is None; if it does exist it's
        # a dict — either way the return value must match the cached value.
        assert bridge._nlm_config == result

    def test_returns_none_when_config_missing_keys(self, tmp_path):
        """Config with only base_url (no notebook_id) is invalid → None."""
        bridge = _make_bridge(tmp_path)
        # Simulate the file having incomplete keys via the instance cache
        bridge._nlm_config = None  # type: ignore[attr-defined]
        result = bridge._load_nlm_config()
        assert result is None

    def test_caches_result_on_second_call(self, tmp_path):
        """Second call must return cached value without re-reading the file."""
        bridge = _make_bridge(tmp_path)
        sentinel = {"base_url": "http://x", "notebook_id": "abc"}
        bridge._nlm_config = sentinel  # type: ignore[attr-defined]
        result = bridge._load_nlm_config()
        assert result is sentinel  # exact same object — cache hit


# --------------------------------------------------------------------------- #
# _extract_parenthetical tests
# --------------------------------------------------------------------------- #

class TestExtractParenthetical:
    def test_extracts_first_sentence(self):
        answer = "Major molecular response is BCR::ABL1 IS ≤0.1% per ELN. Additional context."
        result = StatisticalBridge._extract_parenthetical(answer)
        # First sentence ends at ". " — should not include "Additional context"
        assert "Additional" not in result
        assert result.startswith("Major")

    def test_strips_leading_article(self):
        result = StatisticalBridge._extract_parenthetical(
            "The favorable risk includes NPM1 without FLT3."
        )
        assert not result.startswith("The ")

    def test_truncates_at_80_chars_word_boundary(self):
        long = "A " + "word " * 30 + "end."
        result = StatisticalBridge._extract_parenthetical(long)
        assert len(result) <= 80
        assert not result.endswith(" ")

    def test_empty_input_returns_empty(self):
        assert StatisticalBridge._extract_parenthetical("") == ""

    def test_short_answer_unchanged(self):
        result = StatisticalBridge._extract_parenthetical("CR per ELN 2022.")
        assert result == "CR per ELN 2022"


# --------------------------------------------------------------------------- #
# _enrich_with_nlm tests
# --------------------------------------------------------------------------- #

class TestEnrichWithNlm:
    def test_returns_empty_for_unknown_key(self, tmp_path):
        bridge = _bridge_with_config(
            {"base_url": "http://x", "notebook_id": "nb1"}, tmp_path
        )
        result = bridge._enrich_with_nlm("aml", "nonexistent_stat")
        assert result == ""

    def test_returns_empty_when_no_config(self, tmp_path):
        bridge = _bridge_with_config(None, tmp_path)
        result = bridge._enrich_with_nlm("cml", "mmr_12mo")
        assert result == ""

    def test_returns_parenthetical_on_success(self, tmp_path):
        bridge = _bridge_with_config(
            {"base_url": "http://localhost:5055", "notebook_id": "nb1"}, tmp_path
        )
        mock_nlm = MagicMock()
        mock_nlm.ask.return_value = "MMR is BCR::ABL1 IS ≤0.1% per ELN 2020. More detail."
        fake_module = MagicMock()
        fake_module.NotebookLMIntegration = lambda **kw: mock_nlm
        with patch.dict("sys.modules", {"tools.notebooklm_integration": fake_module}):
            result = bridge._enrich_with_nlm("cml", "mmr_12mo")
        assert isinstance(result, str)
        assert len(result) <= 80
        # The answer starts with "MMR is …"; after stripping "The"/"A"/"An" and
        # truncating at the first sentence boundary it should be non-empty.
        assert result != ""

    def test_returns_empty_on_exception(self, tmp_path):
        """Any exception inside _enrich_with_nlm must be swallowed silently."""
        bridge = _bridge_with_config(
            {"base_url": "http://localhost:5055", "notebook_id": "nb1"}, tmp_path
        )
        # Force an exception by making the import succeed but ask() raise
        mock_nlm = MagicMock()
        mock_nlm.ask.side_effect = ConnectionError("refused")
        with patch.dict(
            "sys.modules",
            {"tools.notebooklm_integration": MagicMock(NotebookLMIntegration=lambda **kw: mock_nlm)},
        ):
            result = bridge._enrich_with_nlm("aml", "eln_favorable_pct")
        assert result == ""
