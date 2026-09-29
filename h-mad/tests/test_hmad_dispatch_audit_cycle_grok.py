"""Audit-cycle wiring contracts for the Grok surface."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_hmad_dispatch_audit_cycle import (
    _dispatch_artifacts_by_pass,
    dispatch_args,
    project_with_docs,
    read_jsonl,
    run_with_cmd_exec_stub,
)


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import h_mad_audit_cycle as audit_cycle  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_caller_env(monkeypatch):
    """Keep ambient Claude and backend settings out of dispatch subprocesses."""
    for name in tuple(os.environ):
        if name.startswith("CLAUDE") or name == "HPW_AGENT_BACKEND":
            monkeypatch.delenv(name)


def test_audit_cycle_dispatches_the_grok_pass_through_exec_grok(tmp_path):
    root = project_with_docs(tmp_path)
    result, trace = run_with_cmd_exec_stub(
        tmp_path,
        dispatch_args(root=root, passes="2") + ["--surfaces", "agy,grok"],
    )

    starts = [row for row in read_jsonl(trace) if row["kind"] == "cmd_exec_start"]
    assert len(starts) == 2, (
        "audit-cycle must call _cmd_exec for both agy and grok passes; "
        f"got {starts!r}; stderr: {result.stderr}"
    )
    starts_by_pass = sorted(starts, key=lambda row: row["argv"][1])
    assert [row["argv"][:1] for row in starts_by_pass] == [["agy"], ["grok"]], (
        "audit-cycle must pass grok to _cmd_exec for pass 2"
    )
    artifacts = _dispatch_artifacts_by_pass(starts)
    assert artifacts[1]["log"] and artifacts[2]["log"], (
        "each audit-cycle _cmd_exec pass must receive --log"
    )
    assert artifacts[1]["log"] != artifacts[2]["log"], (
        "agy and grok audit-cycle passes must receive different --log paths"
    )
    assert result.returncode == 0, result.stderr


def test_audit_cycle_unknown_surface_names_agy_codex_grok(tmp_path):
    root = project_with_docs(tmp_path)
    result, _trace = run_with_cmd_exec_stub(
        tmp_path,
        dispatch_args(root=root, passes="2") + ["--surfaces", "agy,gpt"],
    )

    assert result.returncode == 2, result.stderr
    assert "(agy|codex|grok)" in result.stderr, (
        "audit-cycle unknown-surface error must name agy|codex|grok: "
        f"{result.stderr}"
    )


def test_audit_cycle_clears_stale_grok_log_before_truncated_retry(tmp_path):
    feature = f"grok-stale-{tmp_path.name}"
    root = project_with_docs(tmp_path, feature=feature)
    log = Path(f"/tmp/audit_{feature}_plan_cycle7_p1.log")
    old_pass = (
        '{"type":"tool_call","toolCallId":"read-1"}\n'
        '{"type":"tool_call_update","toolCallId":"read-1","status":"completed"}\n'
        '{"type":"end","stopReason":"end_turn"}\n'
    )
    log.write_text(old_pass, encoding="utf-8")
    try:
        result, trace = run_with_cmd_exec_stub(
            tmp_path,
            dispatch_args(feature=feature, root=root, passes="1")
            + ["--surfaces", "grok"],
            env={"HMAD_STUB_RETRY_LOG_TEXT": '{"type":"thought","data":"retry"}\n'},
        )
        assert result.returncode == 0, result.stderr
        starts = [row for row in read_jsonl(trace) if row["kind"] == "cmd_exec_start"]
        assert len(starts) == 1
        assert starts[0]["log_existed"] is False, "stale log must be gone before dispatch"
        assert log.read_text(encoding="utf-8") == '{"type":"thought","data":"retry"}\n'

        env = {key: value for key, value in os.environ.items()
               if not key.startswith("CLAUDE") and key != "HPW_AGENT_BACKEND"}
        evidence = subprocess.run(
            [sys.executable, str(SCRIPTS / "h_mad_review_evidence.py"), str(log)],
            input="", capture_output=True, text=True, env=env, timeout=10,
        )
        assert evidence.returncode == 2, evidence.stderr
        assert "EVIDENCE: UNREADABLE reason=truncated_no_end" in evidence.stdout
        assert audit_cycle.measure_effort(log)["shape"] == "grok-truncated"
    finally:
        log.unlink(missing_ok=True)
