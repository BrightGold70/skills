"""Audit-cycle contracts for measured Grok logs and their verdict routes."""

import importlib
import re
import sys
from pathlib import Path

import pytest

from grokfixtures import (
    agy_transcript,
    banner_then_f0,
    deep_line_200k,
    f0_text,
    f0_with_completed,
    f_trunc,
    mixed_agy_f0,
)
from test_h_mad_audit_cycle import audit_cycle, pass_result


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_review_evidence as ev  # noqa: E402


def _measure(tmp_path: Path, text: str) -> dict:
    log = tmp_path / "review.ndjson"
    log.write_text(text, encoding="utf-8")
    return audit_cycle().measure_effort(log)


def _combine(effort: dict) -> tuple[str, str | None]:
    return audit_cycle().combine([pass_result(index=1, effort=effort)])


def test_measure_effort_reads_f0_as_grok(tmp_path):
    effort = _measure(tmp_path, f0_text())
    assert effort == {
        "readable": True,
        "shape": "grok",
        "agy_events": 0,
        "tools": 2,
        "ok": 2,
        "unresolved": 0,
        "thinking": 121,
        "stop_reason": "end_turn",
    }, "measure_effort must propagate scan_grok's completed F0 counts without a failed key"


def test_measure_effort_reads_f_trunc_as_grok_truncated(tmp_path):
    effort = _measure(tmp_path, f_trunc())
    assert effort == {"readable": True, "shape": "grok-truncated", "agy_events": 0}, (
        "measure_effort must withhold counts from a Grok stream with no end event"
    )


def test_combine_scores_f0_against_the_floor(tmp_path):
    effort = _measure(tmp_path, f0_text())
    assert _combine(effort) == ("UNVERIFIED", "low_evidence:p1"), (
        "combine must score F0's two completed Grok calls against the delivery floor"
    )


def test_combine_passes_three_completed_calls(tmp_path):
    effort = _measure(tmp_path, f0_with_completed(3))
    assert _combine(effort) == ("PASS", None), (
        "combine must certify a Grok pass with three completed calls"
    )


def test_combine_f_trunc_is_unmeasurable(tmp_path):
    effort = _measure(tmp_path, f_trunc())
    assert _combine(effort) == ("UNVERIFIED", "low_evidence_unmeasurable:p1"), (
        "combine must refuse an incomplete Grok stream as unmeasurable"
    )


def test_combine_routes_hand_built_grok_truncated_to_unmeasurable():
    effort = {"readable": True, "shape": "grok-truncated", "agy_events": 0}
    assert _combine(effort) == ("UNVERIFIED", "low_evidence_unmeasurable:p1"), (
        "combine must route grok-truncated before the delivery-floor check"
    )


@pytest.mark.parametrize(
    "shape,effort,expected",
    [
        ("missing", {"readable": False, "shape": "missing"},
         ("UNVERIFIED", "low_evidence_unmeasurable:p1")),
        ("empty", {"readable": False, "shape": "empty"},
         ("UNVERIFIED", "low_evidence:p1")),
        ("parsed", {"readable": True, "shape": "parsed", "ok": 0},
         ("UNVERIFIED", "low_evidence:p1")),
        ("grok", {"readable": True, "shape": "grok", "ok": 0},
         ("UNVERIFIED", "low_evidence:p1")),
        ("grok-truncated", {"readable": True, "shape": "grok-truncated"},
         ("UNVERIFIED", "low_evidence_unmeasurable:p1")),
        ("codex-text", {"readable": True, "shape": "codex-text"},
         ("PASS", None)),
        ("unparseable", {"readable": True, "shape": "unparseable"},
         ("UNVERIFIED", "low_evidence_unmeasurable:p1")),
        ("unknown", {"readable": True, "shape": "bogus", "ok": 0},
         ("UNVERIFIED", "shape_unrouted:p1")),
    ],
    ids=["missing", "empty", "parsed", "grok", "grok-truncated", "codex-text",
         "unparseable", "unknown"],
)
def test_combine_routes_every_shape(shape, effort, expected):
    assert _combine(effort) == expected, f"combine must route {shape} to {expected}"


def test_effort_items_render_grok_and_grok_truncated():
    ac = audit_cycle()
    grok = {"readable": True, "shape": "grok", "agy_events": 0,
            "tools": 2, "ok": 2, "unresolved": 0, "thinking": 121,
            "stop_reason": "end_turn"}
    truncated = {"readable": True, "shape": "grok-truncated", "agy_events": 0}
    try:
        lines = ac._effort_items([
            pass_result(index=1, effort=grok),
            pass_result(index=2, effort=truncated),
        ])
    except KeyError as exc:
        pytest.fail(f"_effort_items must render Grok's unresolved count without a failed key: {exc}")
    assert lines[0].startswith(
        "p1 tools=2 ok=2 unresolved=0 thinking=121 format=grok low-evidence ("
    ), "_effort_items must render measured Grok counts and the floor suffix"
    assert lines[1] == (
        "p2 not measured (grok log truncated — no end event; counts withheld)"
    ), "_effort_items must not print counts for a truncated Grok stream"


def test_measure_effort_mixed_agy_f0_is_parsed(tmp_path):
    agy = _measure(tmp_path, agy_transcript())
    mixed = _measure(tmp_path, mixed_agy_f0())
    assert mixed == agy, "measure_effort must keep agy precedence over Grok events"
    assert mixed["shape"] == "parsed", "measure_effort must classify mixed agy/F0 as parsed"


def test_measure_effort_banner_then_f0_is_codex_text(tmp_path):
    effort = _measure(tmp_path, banner_then_f0())
    assert effort["shape"] == "codex-text", (
        "measure_effort must give the head Codex banner precedence over Grok events"
    )
    assert effort["agy_events"] == 0


def test_codex_banner_pattern_is_single_sourced():
    header_pattern = ev._CODEX_HEADER_RE
    ac = audit_cycle()
    re.purge()
    reloaded = importlib.reload(ac)
    assert reloaded._CODEX_BANNER is header_pattern, (
        "audit_cycle must share review_evidence's Codex banner pattern object"
    )


def test_measure_effort_survives_a_200k_deep_line(tmp_path):
    baseline = _measure(tmp_path, f0_text())
    deep = tmp_path / "deep.ndjson"
    deep.write_text(deep_line_200k() + f0_text(), encoding="utf-8")
    try:
        actual = audit_cycle().measure_effort(deep)
    except RecursionError:
        pytest.fail("measure_effort() raised RecursionError on a 200,000-deep line")
    assert actual == baseline, "measure_effort must preserve F0 after a deep line"
    assert actual["shape"] == "grok", "measure_effort must still classify F0 as Grok"
