"""RED tests for Grok review evidence and the two agy scan robustness fixes."""

import sys
from pathlib import Path

import pytest

from grokfixtures import (
    agy_transcript,
    banner_then_f0,
    deep_line_200k,
    depth_line,
    f0_text,
    f_notools,
    f_trunc,
    window_edge_log,
)


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_review_evidence as ev  # noqa: E402
import h_mad_archreview_cycle as ar  # noqa: E402


def test_scan_grok_counts_f0():
    assert ev.scan_grok(f0_text()) == {
        "tools": 2,
        "ok": 2,
        "unresolved": 0,
        "thinking": 121,
        "complete": True,
        "stop_reason": "end_turn",
    }, "scan_grok must count F0's parsed tool calls, reasoning, and end event"


def test_scan_grok_counts_f_notools():
    result = ev.scan_grok(f_notools())
    assert result is not None, "scan_grok must recognize Grok events without completed calls"
    assert (result["tools"], result["ok"], result["unresolved"], result["complete"]) == (
        2, 0, 2, True
    ), "scan_grok must leave both unfinished tool calls unresolved"


def test_scan_grok_marks_f_trunc_incomplete():
    result = ev.scan_grok(f_trunc())
    assert result is not None, "scan_grok must recognize a truncated Grok stream"
    assert (result["tools"], result["ok"], result["complete"], result["stop_reason"]) == (
        2, 2, False, None
    ), "scan_grok must not invent an end event for a truncated stream"


@pytest.mark.parametrize(
    "log_text",
    [agy_transcript(), "OpenAI Codex v0.145.0\nexec\n", "", '{"type":"bogus"}\n'],
    ids=["agy", "codex_banner", "empty", "bogus_type"],
)
def test_scan_grok_is_none_without_a_grok_event(log_text):
    assert ev.scan_grok(log_text) is None, "scan_grok must reject logs without a known Grok type"


def test_scan_grok_ok_ignores_a_completed_substring_in_text():
    decoy = '{"type":"text","data":"\\"status\\":\\"completed\\""}\n'
    result = ev.scan_grok(f0_text() + decoy)
    assert result is not None, "scan_grok must recognize F0 alongside a text decoy"
    assert result["ok"] == 2, "scan_grok must count completed updates, not text substrings"


def test_scan_grok_survives_malformed_type_lines():
    malformed = ''.join(
        f'{{"type":{value}}}\n' for value in ("[]", "{}", "1", "null")
    )
    lines = f0_text().splitlines(keepends=True)
    noisy = malformed + deep_line_200k() + ''.join(lines[:1]) + deep_line_200k() + ''.join(lines[1:])
    baseline = ev.scan_grok(f0_text())
    assert baseline is not None, "scan_grok must recognize F0 before malformed-line comparison"
    assert ev.scan_grok(noisy) == baseline, (
        "scan_grok must skip malformed types and deep lines without losing later Grok events"
    )


@pytest.mark.parametrize("depth, recognized", [(64, True), (65, False)], ids=["64", "65"])
def test_scan_grok_depth_boundary(depth, recognized):
    assert (ev.scan_grok(depth_line(depth)) is not None) is recognized, (
        f"scan_grok must {'accept' if recognized else 'reject'} depth {depth}"
    )


def test_scan_grok_key_order_and_bogus_type():
    assert ev.scan_grok('{"meta":1,"type":"text","data":"x"}\n') is not None, (
        "scan_grok must recognize a Grok type regardless of JSON key order"
    )
    assert ev.scan_grok('{"meta":1,"type":"bogus","data":"x"}\n') is None, (
        "scan_grok must reject an unknown type regardless of JSON key order"
    )


def test_codex_banner_in_head_window_edge():
    assert ev.CODEX_BANNER_HEAD == 4096, "the Codex banner window must be 4096 characters"
    assert ev.codex_banner_in_head(window_edge_log()) is False, (
        "codex_banner_in_head must ignore a banner beyond the first 4096 characters"
    )
    assert ev.codex_banner_in_head(banner_then_f0()) is True, (
        "codex_banner_in_head must recognize a banner at the start of a log"
    )


def test_scan_unchanged_on_f0():
    result = ev.scan(f0_text())
    assert result["agy_events"] == 0, "scan must not classify F0 Grok events as agy"
    assert result["tools"] == 0, "scan must not count F0 Grok calls as agy tools"


def test_scan_survives_a_200k_deep_line():
    expected = ev.scan(f0_text())
    try:
        actual = ev.scan(deep_line_200k() + f0_text())
    except RecursionError:
        pytest.fail("scan() raised RecursionError on a 200,000-deep line")
    assert actual == expected, "scan must skip a deep line and preserve later evidence"


def test_archreview_evidence_counts_survive_a_200k_deep_line():
    expected = ev.scan(f0_text())
    try:
        actual = ar._evidence_counts(deep_line_200k() + f0_text())
    except RecursionError:
        pytest.fail("_evidence_counts raised RecursionError on a 200,000-deep line")
    assert actual == expected, "_evidence_counts must preserve later evidence after a deep line"


def test_scan_survives_an_unhashable_event_value():
    expected = ev.scan(f0_text())
    try:
        actual = ev.scan('{"event":[]}\n' + f0_text())
    except TypeError:
        pytest.fail("scan() raised TypeError on an unhashable event value")
    assert actual == expected, "scan must skip an unhashable event value and preserve F0 counts"
