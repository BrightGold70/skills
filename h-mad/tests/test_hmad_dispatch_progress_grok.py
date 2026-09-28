"""Public progress and auto-log contracts for Grok streaming JSON."""

import json
import os
import subprocess

import pytest

from grokfixtures import (
    agy_init_f0,
    banner_then_f0,
    depth_line,
    f0_text,
    f_deep,
    f_spaced,
    farm_env,
    usr_bin_farm,
    window_edge_log,
)
from test_hmad_dispatch import WRAPPER, _bindir, run


HOSTILE_PROMPT = (
    "# [agent](https://example.invalid/a*[?]) **review**\n"
    "line with 'quotes', $(), `ticks`, and [glob*]\n"
    "===HMAD-DISPATCH-BOUNDARY=== inside the request\n"
)


@pytest.fixture(autouse=True)
def _clean_caller_env(monkeypatch):
    """Keep orchestration's CLAUDE* and backend exports out of subprocesses."""
    for name in os.environ:
        if name.startswith("CLAUDE") or name == "HPW_AGENT_BACKEND":
            monkeypatch.delenv(name)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


def _log(tmp_path, stream):
    path = tmp_path / "run [*] marker.ndjson"
    path.write_text(stream, encoding="utf-8")
    return path


def _progress(tmp_path, stream, *, env=None):
    log = _log(tmp_path, stream)
    result = run(["progress", str(log), "--lines", "400"], env=env)
    assert result.returncode == 0, f"progress must render the log: {result.stderr}"
    return result


def _farm_progress(tmp_path, stream):
    log = _log(tmp_path, stream)
    farm = usr_bin_farm(tmp_path, absent=("jq",), stubs=())
    env = farm_env(farm, HMAD_STUB_HOSTILE="all", HMAD_SUBSTRATE="none")
    jq = subprocess.run(["bash", "-c", "command -v jq"], env=env,
                        text=True, capture_output=True)
    assert jq.returncode != 0, "the isolated PATH must omit jq"
    result = subprocess.run(["bash", str(WRAPPER), "progress", str(log),
                             "--lines", "400"], env=env, text=True,
                            capture_output=True, timeout=30)
    assert result.returncode == 0, f"progress without jq must return: {result.stderr}"
    return result


def test_progress_f0_is_grok_ndjson(tmp_path):
    result = _progress(tmp_path, f0_text())
    assert "format: grok-ndjson" in result.stdout, (
        "progress must classify the F0 Grok stream as grok-ndjson"
    )


def test_progress_f_spaced_is_grok_ndjson(tmp_path):
    result = _progress(tmp_path, f_spaced())
    assert "format: grok-ndjson" in result.stdout, (
        "progress must classify spaced Grok JSON as grok-ndjson"
    )


def test_progress_agy_init_plus_f0_is_agy_ndjson(tmp_path):
    result = _progress(tmp_path, agy_init_f0())
    assert "format: agy-ndjson" in result.stdout, (
        "progress must give an agy init event precedence over Grok events"
    )


def test_progress_f0_renders_counts_without_delta_text(tmp_path):
    result = _progress(tmp_path, f0_text())
    lines = result.stdout.splitlines()
    tool_lines = [line for line in lines
                  if "tool read_file " in line or "tool search_replace " in line]
    assert sum(" pending" in line for line in tool_lines) == 2, (
        "progress must render both pending F0 tool calls"
    )
    assert sum(" completed" in line for line in tool_lines) == 2, (
        "progress must render both completed F0 tool calls by name"
    )
    assert len(tool_lines) == 4, "progress must render exactly four F0 tool lines"
    for name in ("read_file", "search_replace"):
        for status in ("pending", "completed"):
            assert sum(f"tool {name} {status}" in line for line in tool_lines) == 1, (
                f"progress must render one {status} line for {name}"
            )
    assert sum("END stopReason=end_turn turns=3" in line for line in lines) == 1, (
        "progress must render the F0 end event once"
    )
    assert sum("turn usage" in line for line in lines) == 3, (
        "progress must render all three F0 usage events"
    )
    events = [json.loads(line) for line in f0_text().splitlines()]
    deltas = {event["data"].strip() for event in events
              if event["type"] in {"thought", "text"} and event["data"].strip()}
    assert not any(line.strip() in deltas for line in lines), (
        "progress must never print a thought or text delta as a digest line"
    )
    text_runs = []
    current = ""
    for event in events:
        if event["type"] == "text":
            current += event["data"]
        elif current:
            text_runs.append(current)
            current = ""
    if current:
        text_runs.append(current)
    assert len(text_runs) == 2, "F0 must contain two text runs for the privacy check"
    assert all(segment not in result.stdout for segment in text_runs), (
        "progress must never leak either F0 text segment"
    )


def test_progress_key_order_line_is_grok_ndjson(tmp_path):
    result = _progress(tmp_path, '{"meta":1,"type":"text","data":"x"}\n')
    assert "format: grok-ndjson" in result.stdout, (
        "progress must find a Grok type when type is not the first JSON key"
    )


def test_progress_bogus_type_line_is_codex_text(tmp_path):
    result = _progress(tmp_path, '{"meta":1,"type":"bogus","data":"x"}\n')
    assert "format: codex-text" in result.stdout, (
        "progress must reject a JSON type outside Grok's event vocabulary"
    )


def test_progress_key_order_line_on_the_fallback_route(tmp_path):
    result = _farm_progress(tmp_path, '{"meta":1,"type":"text","data":"x"}\n')
    assert "format: grok-ndjson" in result.stdout, (
        "progress must recognize key-order Grok JSON without jq"
    )


def test_progress_without_jq_cannot_render(tmp_path):
    result = _farm_progress(tmp_path, f0_text())
    assert "format: grok-ndjson" in result.stdout, (
        "progress must classify F0 through the no-jq fallback"
    )
    assert "  (grok stream — jq not on PATH, cannot render)" in result.stdout, (
        "progress must explain why a Grok stream cannot render without jq"
    )


def test_progress_with_failing_jq_cannot_render(tmp_path):
    bindir = _bindir(tmp_path, [])
    jq = bindir / "jq"
    if jq.exists() or jq.is_symlink():
        jq.unlink()
    jq.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
    jq.chmod(0o755)
    result = _progress(tmp_path, f0_text(), env={"_BINDIR": str(bindir)})
    assert "  (grok stream — jq failed, cannot render)" in result.stdout, (
        "progress must report a failing jq without showing a partial Grok digest"
    )
    assert "  · " not in result.stdout, (
        "progress must discard every rendered line when jq fails"
    )


def test_progress_banner_then_f0_is_codex_text(tmp_path):
    result = _progress(tmp_path, banner_then_f0())
    assert "format: codex-text" in result.stdout, (
        "progress must let a leading Codex banner override Grok events"
    )


@pytest.mark.parametrize("depth,expected", [(64, "grok-ndjson"),
                                            (65, "codex-text")], ids=["64", "65"])
def test_progress_depth_boundary(tmp_path, depth, expected):
    result = _progress(tmp_path, depth_line(depth))
    assert f"format: {expected}" in result.stdout, (
        f"progress must classify depth-{depth} JSON as {expected}"
    )


def test_progress_f_deep65_prints_no_deep_end(tmp_path):
    result = _progress(tmp_path, f_deep(65))
    assert "END stopReason=deep" not in result.stdout, (
        "progress must not render a depth-65 end event"
    )


def test_exec_grok_auto_log_is_rendered_as_the_digest(tmp_path):
    prompt = tmp_path / "prompt [*] marker.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    stream = tmp_path / "stream [*] marker.ndjson"
    stream.write_text(f0_text(), encoding="utf-8")
    bindir = _bindir(tmp_path, ["grok"])
    result = run(["exec", "grok", str(prompt), "--cd", str(tmp_path)],
                 env={"_BINDIR": str(bindir), "HMAD_STUB_HOSTILE": "all",
                      "HMAD_STUB_GROK_STREAM": str(stream)})
    assert result.returncode == 0, f"exec grok must complete: {result.stderr}"
    assert "END stopReason=end_turn" in result.stderr, (
        "exec grok without --log must render its auto-log as a progress digest"
    )
    assert not any(line.startswith('{"type":"') for line in result.stderr.splitlines()), (
        "exec grok auto-log must not dump raw NDJSON to stderr"
    )


def test_window_edge_log_is_grok_ndjson(tmp_path):
    result = _progress(tmp_path, window_edge_log())
    assert "format: grok-ndjson" in result.stdout, (
        "progress must ignore a Codex banner starting at byte 4096"
    )
