"""Cross-surface contracts for Grok detection and evidence counting."""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from grokfixtures import (
    agy_transcript,
    banner_then_f0,
    depth_line,
    f0_text,
    f_beat,
    f_deep,
    f_notools,
    f_shared,
    f_spaced,
    f_trunc,
    mixed_agy_f0,
    window_edge_log,
)
from test_hmad_dispatch import WRAPPER, run, run_fn


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_audit_cycle as audit_cycle  # noqa: E402
import h_mad_review_evidence as evidence  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_agent_env(monkeypatch):
    """Orchestrator exports must not change these transcript classifications."""
    for name in os.environ:
        if name.startswith("CLAUDE") or name == "HPW_AGENT_BACKEND":
            monkeypatch.delenv(name)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


def _log(tmp_path, text):
    path = tmp_path / "review [*] marker.ndjson"
    path.write_text(text, encoding="utf-8")
    return path


def _progress(log):
    result = run(["progress", str(log), "--lines", "400"])
    assert result.returncode == 0, f"progress must render the log: {result.stderr}"
    match = re.search(r"^\s*format: (agy-ndjson|grok-ndjson|codex-text)\b",
                      result.stdout, re.M)
    assert match, f"progress must print its format: {result.stdout}"
    return match.group(1)


def _measure(log):
    return audit_cycle.measure_effort(log)["shape"]


def _cli(log):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("CLAUDE") and key != "HPW_AGENT_BACKEND"}
    env["HMAD_STUB_HOSTILE"] = "all"
    return subprocess.run([sys.executable, str(SCRIPTS / "h_mad_review_evidence.py"),
                           str(log)], env=env, capture_output=True, text=True)


def _shell_grok_readers(log, pre=0):
    quoted = shlex.quote(str(log))
    result = run_fn(
        f'_grok_region_state {quoted} {pre}\n_grok_last_tool {quoted} {pre}',
        env={"HMAD_STUB_HOSTILE": "all"},
    )
    assert result.returncode == 0, f"Grok shell readers must run: {result.stderr}"
    lines = result.stdout.splitlines()
    assert lines and lines[0] in {"complete", "truncated"}, (
        f"_grok_region_state must return a completeness state: {result.stdout}"
    )
    assert len(lines) == 2, f"_grok_last_tool must print its count: {result.stdout}"
    match = re.fullmatch(r"(\d+) tool calls completed; last tool: .+", lines[1])
    assert match, f"_grok_last_tool must print N completed calls: {lines[1]}"
    return lines[0], int(match.group(1))


@pytest.mark.parametrize(
    "builder,expected_format,expected_shape",
    [
        (f0_text, "grok-ndjson", "grok"),
        (f_spaced, "grok-ndjson", "grok"),
        (f_trunc, "grok-ndjson", "grok-truncated"),
        (agy_transcript, "agy-ndjson", "parsed"),
        (lambda: "OpenAI Codex v0.145.0\nexec\n", "codex-text", "codex-text"),
        (mixed_agy_f0, "agy-ndjson", "parsed"),
        (banner_then_f0, "codex-text", "codex-text"),
        (window_edge_log, "grok-ndjson", "grok"),
    ],
    ids=["f0", "f_spaced", "f_trunc", "agy", "codex_banner", "mixed",
         "banner_then_f0", "window_edge"],
)
def test_format_agreement(tmp_path, builder, expected_format, expected_shape):
    log = _log(tmp_path, builder())
    shell_format = _progress(log)
    python_shape = _measure(log)
    assert shell_format == expected_format, "progress must retain the expected format"
    assert python_shape == expected_shape, "measure_effort must retain the expected shape"
    assert python_shape in {
        "agy-ndjson": {"parsed"},
        "grok-ndjson": {"grok", "grok-truncated"},
        "codex-text": {"codex-text", "unparseable"},
    }[shell_format], "progress and measure_effort must classify the same transcript compatibly"


def test_depth_bound_literals_agree():
    source = WRAPPER.read_text(encoding="utf-8")
    matches = re.findall(r"^_GROK_MAX_DEPTH=(\d+)$", source, re.M)
    assert len(matches) == 1, "hmad-dispatch must define one Grok depth literal"
    assert int(matches[0]) == evidence.GROK_MAX_DEPTH == 64, (
        "shell and Python Grok maximum depth must share the depth-64 contract"
    )


@pytest.mark.parametrize("depth,expected", [(64, True), (65, False)], ids=["64", "65"])
def test_depth_boundary_agrees_across_surfaces(tmp_path, depth, expected):
    text = depth_line(depth)
    shell_recognized = _progress(_log(tmp_path, text)) == "grok-ndjson"
    python_recognized = evidence.scan_grok(text) is not None
    assert shell_recognized == expected, f"progress must classify depth {depth} correctly"
    assert python_recognized == expected, f"scan_grok must classify depth {depth} correctly"
    assert shell_recognized == python_recognized, "Grok depth detection must agree"


@pytest.mark.parametrize("depth,complete,ok", [(64, True, 3), (65, False, 2)],
                         ids=["64", "65"])
def test_f_deep_readers_agree_with_scan_grok(tmp_path, depth, complete, ok):
    text = f_deep(depth)
    state, shell_ok = _shell_grok_readers(_log(tmp_path, text))
    counts = evidence.scan_grok(text)
    assert counts is not None, "scan_grok must recognize the F-DEEP region"
    assert (state == "complete") == counts["complete"] == complete, (
        f"_grok_region_state and scan_grok must agree on F-DEEP{depth} completeness"
    )
    assert shell_ok == counts["ok"] == ok, (
        f"_grok_last_tool and scan_grok must agree on F-DEEP{depth} completed calls"
    )


@pytest.mark.parametrize(
    "line,recognized",
    [('{"meta":1,"type":"text","data":"x"}\n', True),
     ('{"meta":1,"type":"bogus","data":"x"}\n', False)],
    ids=["key_order", "bogus"],
)
def test_key_order_detection_agrees(tmp_path, line, recognized):
    shell_recognized = _progress(_log(tmp_path, line)) == "grok-ndjson"
    python_recognized = evidence.scan_grok(line) is not None
    assert shell_recognized == recognized, "progress must honor AC-5.2b's type vocabulary"
    assert python_recognized == recognized, "scan_grok must honor AC-5.2b's type vocabulary"
    assert shell_recognized == python_recognized, "AC-5.2b detection must agree"


def test_banner_wins_on_all_three_surfaces(tmp_path):
    log = _log(tmp_path, banner_then_f0())
    assert _progress(log) == "codex-text", "progress must give the Codex banner priority"
    cli = _cli(log)
    assert cli.returncode == 2, "review evidence CLI must reject incomplete Codex text"
    assert cli.stdout.startswith("CODEXEVIDENCE:"), "CLI must use the Codex evidence reader"
    assert cli.stdout.endswith("EVIDENCE: UNREADABLE reason=unsupported_format\n"), (
        "CLI must preserve the Codex text verdict"
    )
    assert "format=grok" not in cli.stdout, "CLI must not claim Grok format after the banner"
    assert _measure(log) == "codex-text", "measure_effort must give the Codex banner priority"


def test_window_edge_cli_and_measure_effort_agree(tmp_path):
    log = _log(tmp_path, window_edge_log())
    cli = _cli(log)
    assert cli.returncode == 0, "CLI must accept completed Grok past the banner window"
    assert re.search(r"^EVIDENCE: PASS .*\bformat=grok\b", cli.stdout, re.M), (
        "CLI must print a Grok evidence line at the banner window edge"
    )
    assert _measure(log) == "grok", "measure_effort must agree with CLI at the banner window edge"


@pytest.mark.parametrize(
    "builder,pre,complete,ok",
    [(f0_text, 0, True, 2), (f_trunc, 0, False, 2),
     (f_notools, 0, True, 0), (f_shared, 110, False, 2),
     (f_beat, 0, True, 2)],
    ids=["f0", "f_trunc", "f_notools", "f_shared_region", "f_beat"],
)
def test_completeness_and_n_single_sourced(tmp_path, builder, pre, complete, ok):
    text = builder()
    region = "".join(text.splitlines(keepends=True)[pre:])
    state, shell_ok = _shell_grok_readers(_log(tmp_path, text), pre)
    counts = evidence.scan_grok(region)
    assert counts is not None, "scan_grok must recognize the selected Grok region"
    assert (state == "complete") == counts["complete"] == complete, (
        "_grok_region_state and scan_grok must agree on region completeness"
    )
    assert shell_ok == counts["ok"] == ok, (
        "_grok_last_tool and scan_grok must agree on region completed calls"
    )


def test_type_vocabulary_single_sourced():
    source = WRAPPER.read_text(encoding="utf-8")
    matches = re.findall(r"^_GROK_TYPES_RE='([^']+)'$", source, re.M)
    assert len(matches) == 1, "hmad-dispatch must define one Grok type vocabulary"
    shell_types = set(matches[0].split("|"))
    assert shell_types == evidence._GROK_TYPES == {
        "thought", "text", "available_commands", "tool_call", "tool_call_update",
        "usage", "end",
    }, "shell and Python must share the seven Grok event types"
