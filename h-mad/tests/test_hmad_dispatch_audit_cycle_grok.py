"""Audit-cycle wiring contracts for the Grok surface."""

import os

import pytest

from test_hmad_dispatch_audit_cycle import (
    _dispatch_artifacts_by_pass,
    dispatch_args,
    project_with_docs,
    read_jsonl,
    run_with_cmd_exec_stub,
)


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
