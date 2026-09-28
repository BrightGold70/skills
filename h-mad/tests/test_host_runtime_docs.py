"""Executable and section-scoped contracts for host runtime adapters."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import host_parity


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = {
    f"{skill}-{host}": REPO_ROOT / skill / "references" / f"{host}-runtime.md"
    for skill in ("h-mad", "handoff")
    for host in ("codex", "agy", "grok")
}
sys.path.insert(0, str(REPO_ROOT / "h-mad" / "scripts"))
from h_mad_doc_block_exec import AmbiguousHeading, _fence_events, fence_aware_end, find_heading  # noqa: E402


SID_READ = '"$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"'
ADAPTER_ID = "h-mad-codex"
HOST_ADAPTERS = (ADAPTER_ID, "h-mad-agy")


def _section(text: str, heading: str) -> str:
    try:
        found = find_heading(text, heading)
    except AmbiguousHeading:
        raise LookupError(f"heading doubled: {heading}")  # M:L2
    if found is None:
        raise LookupError(f"heading absent: {heading}")  # M:L1
    start, level = found
    return text[start:fence_aware_end(text, start, level)]


def _fenced_lines(section: str) -> list[str]:
    return [section[e.start:e.end].rstrip("\r\n") for e in _fence_events(section) if e.kind == "body"]


def _required_section(adapter_id: str, heading: str, property_name: str) -> str:
    try:
        return _section(ADAPTERS[adapter_id].read_text(encoding="utf-8"), heading)
    except LookupError as exc:
        pytest.fail(f"{adapter_id} {property_name}: {exc}")


def _row(adapter_id: str, construct_id: str, property_name: str) -> host_parity.Row:
    text = ADAPTERS[adapter_id].read_text(encoding="utf-8")
    _required_section(adapter_id, "## Construct mapping", property_name)
    table = host_parity.adapter_table(text)
    assert table.problems == [], f"{adapter_id} Construct mapping problems: {table.problems}"
    rows = [row for row in table.rows if row.id == construct_id]
    assert len(rows) == 1, f"{adapter_id} Construct mapping needs exactly one {construct_id} row"
    return rows[0]


def _claims(adapter_id: str, property_name: str) -> str:
    return _required_section(adapter_id, "## Context budget and claims", property_name)


@pytest.mark.parametrize(
    "adapter_id,property_name,expected",
    [
        (ADAPTER_ID, "status", "not-applicable"),
        (ADAPTER_ID, "hmad-dispatch-exec", "hmad-dispatch exec"),
        (ADAPTER_ID, "spawn-agent", "collaboration.spawn_agent"),
        (ADAPTER_ID, "fork-turns", "fork_turns"),
        ("h-mad-agy", "status", "not-applicable"),
        ("h-mad-agy", "hmad-dispatch-exec", "hmad-dispatch exec"),
        ("h-mad-agy", "invoke-subagent", "invoke_subagent"),
    ],
    ids=[
        "h-mad-codex-status", "h-mad-codex-hmad-dispatch-exec", "h-mad-codex-spawn-agent", "h-mad-codex-fork-turns",
        "h-mad-agy-status", "h-mad-agy-hmad-dispatch-exec", "h-mad-agy-invoke-subagent",
    ],
)
def test_advisor_row(adapter_id: str, property_name: str, expected: str) -> None:
    row = _row(adapter_id, "advisor", f"advisor {property_name}")
    if property_name == "status":
        assert row.status == expected, f"advisor must be not-applicable on {adapter_id}"
    else:
        assert expected in row.mapping, f"advisor mapping must contain {expected}"


@pytest.mark.parametrize(
    "adapter_id,token",
    [(adapter_id, token) for adapter_id in HOST_ADAPTERS for token in ("uuid.uuid4()", "owned_elsewhere")],
    ids=[f"{adapter_id}-{suffix}" for adapter_id in HOST_ADAPTERS for suffix in ("uuid4", "owned-elsewhere")],
)
def test_session_id_env_row(adapter_id: str, token: str) -> None:
    assert token in _row(adapter_id, "session-id-env", f"session-id-env {token}").mapping, f"{adapter_id} session-id-env mapping must contain {token}"


@pytest.mark.parametrize(
    "adapter_id,case",
    [(adapter_id, case) for adapter_id in HOST_ADAPTERS for case in (
        "create-claim", "claim", "beat", "set", "release", "oracle", "mint",
        "oracle-first", "no-dollar-sid", "prose-once-at-bootstrap", "prose-never-deleted",
    )],
    ids=[f"{adapter_id}-{case}" for adapter_id in HOST_ADAPTERS for case in (
        "create-claim", "claim", "beat", "set", "release", "oracle", "mint",
        "oracle-first", "no-dollar-sid", "prose-once-at-bootstrap", "prose-never-deleted",
    )],
)
def test_claims_section_fenced_lines(adapter_id: str, case: str) -> None:
    section = _claims(adapter_id, case)
    lines = _fenced_lines(section)
    state_lines = [line for line in lines if "h_mad_state_write.py" in line]
    oracle_lines = [line for line in lines if "h_mad_resume_decision.py" in line]
    conditions = {
        "create-claim": lambda line: "--create --claim " + SID_READ in line,
        "claim": lambda line: "--claim " + SID_READ in line and "--create" not in line,
        "beat": lambda line: "--beat" in line and "--session-id " + SID_READ in line,
        "set": lambda line: "--set" in line and "--session-id " + SID_READ in line,
        "release": lambda line: "--release" in line and "--session-id " + SID_READ in line,
        "oracle": lambda line: "h_mad_resume_decision.py" in line and "--session-id " + SID_READ in line,
        "mint": lambda line: all(token in line for token in ("set -C", "uuid.uuid4()", "h-mad-session-id.<feature>", "SID: NOT_MINTED")),
    }
    if case in conditions:
        assert any(conditions[case](line) for line in lines), f"{case} needs its own fenced command with full session-id read"
    elif case == "oracle-first":
        assert oracle_lines and state_lines, "oracle-first requires oracle and state-write commands"
        assert lines.index(oracle_lines[0]) < min(lines.index(line) for line in state_lines), "resume oracle must precede every state write"
    elif case == "no-dollar-sid":
        assert not any("$SID" in line for line in lines), "fenced commands must not rely on $SID across invocations"
        assert any(SID_READ in line for line in lines), "fenced commands must read the session id from its file"
    elif case == "prose-once-at-bootstrap":
        assert "once at bootstrap" in section, "mint procedure must say once at bootstrap"
    else:
        assert "never deleted or reused without the operator" in section, "session id file must require operator action before deletion or reuse"


@pytest.mark.parametrize("adapter_id", HOST_ADAPTERS, ids=HOST_ADAPTERS)
def test_claims_lines_execute_across_invocations(adapter_id: str, tmp_path: Path, hermetic_env) -> None:
    lines = _fenced_lines(_claims(adapter_id, "claims lines execute across invocations"))
    mint = next((line for line in lines if "SID: MINTED" in line and "SID: NOT_MINTED" in line), None)
    create = next((line for line in lines if "--create --claim " + SID_READ in line), None)
    oracle = next((line for line in lines if "h_mad_resume_decision.py" in line and "--session-id " + SID_READ in line), None)
    assert mint and create and oracle, "mint, create-claim and resume-oracle fenced lines are required"

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True, text=True, check=True, timeout=60.0)
    (repo / "docs").mkdir()
    state_path = repo / "docs" / ".bkit-memory.json"
    state_path.write_text("{}", encoding="utf-8")
    empty_home = tmp_path / "home"
    empty_home.mkdir()
    env = hermetic_env(HMAD_SKILL_ROOT=str(REPO_ROOT / "h-mad"), HOME=str(empty_home))

    def run(line: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-c", line.replace("<feature>", "fixture-feature")],
            cwd=repo, env=env, capture_output=True, text=True, timeout=60.0,
        )

    first = run(mint)
    assert first.returncode == 0 and "SID: MINTED" in first.stdout, f"mint must succeed: {first.stdout} {first.stderr}"
    sid_file = repo / ".git" / "h-mad-session-id.fixture-feature"
    original = sid_file.read_bytes()
    second = run(mint)
    assert second.returncode == 0 and "SID: NOT_MINTED" in second.stdout, f"second mint must refuse overwrite: {second.stdout} {second.stderr}"
    assert sid_file.read_bytes() == original, "second mint must preserve original session id bytes"

    claimed = run(create)
    assert claimed.returncode == 0, f"create-claim must run with the minted id: {claimed.stdout} {claimed.stderr}"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["orchestrator_state"]["fixture-feature"]["owner_session_id"] == original.decode().strip(), "create-claim must use the file's session id"

    decision = run(oracle)
    assert decision.returncode == 0, f"resume oracle must run with the minted id: {decision.stdout} {decision.stderr}"
    assert "cannot_judge" not in decision.stdout and "owned_elsewhere" not in decision.stdout, "owner's resume oracle must not reject its own claim"
    control = run(oracle.replace(SID_READ, '""'))
    assert "cannot_judge" in control.stdout, "oracle without the file's session id must report cannot_judge"


@pytest.mark.parametrize("adapter_id", HOST_ADAPTERS, ids=HOST_ADAPTERS)
def test_not_applicable_rows_state_a_reason(adapter_id: str) -> None:
    _required_section(adapter_id, "## Construct mapping", "not-applicable rows state a reason")
    table = host_parity.adapter_table(ADAPTERS[adapter_id].read_text(encoding="utf-8"))
    assert table.problems == [], f"Construct mapping table must parse: {table.problems}"
    rows = [row for row in table.rows if row.status == "not-applicable"]
    assert rows, "Construct mapping must include at least one not-applicable row"
    for row in rows:
        mapping = re.sub(r"`[^`]*`", " ", row.mapping).strip()
        assert len(re.findall(r"[A-Za-z]{2,}", mapping)) >= 3, f"{row.id} not-applicable mapping needs a reason of at least three words"
        assert re.fullmatch(r"(?i)(?:n/?a|not[- ]applicable|none)\.?", mapping) is None, f"{row.id} needs more than a status word"
        assert row.mapping != row.source, f"{row.id} reason must differ from source"


@pytest.mark.parametrize(
    "adapter_id,token",
    [(adapter_id, token) for adapter_id in HOST_ADAPTERS for token in (
        "CTXBUDGET: UNKNOWN reason=host_unsupported", "80%", "substitute: none",
    )],
    ids=[f"{adapter_id}-{suffix}" for adapter_id in HOST_ADAPTERS for suffix in ("unknown", "80pct", "substitute-none")],
)
def test_context_budget_section(adapter_id: str, token: str) -> None:
    assert token in _claims(adapter_id, f"context budget {token}"), f"{adapter_id} Context budget and claims must state {token}"


@pytest.mark.parametrize("adapter_id", HOST_ADAPTERS, ids=HOST_ADAPTERS)
def test_budget_line_runs_and_reports_host(adapter_id: str, tmp_path: Path, hermetic_env) -> None:
    section = _claims(adapter_id, "budget line runs and reports host")
    host = adapter_id.removeprefix("h-mad-")
    pattern = re.compile(rf'^HMAD_HOST={host} python3 "\$HMAD_SKILL_ROOT/scripts/h_mad_context_budget\.py"$')
    lines = [line for line in _fenced_lines(section) if pattern.fullmatch(line)]
    assert len(lines) == 1, f"Context budget and claims needs exactly one fenced {host} budget command"
    empty_home = tmp_path / "home"
    empty_home.mkdir()
    result = subprocess.run(
        ["bash", "-c", lines[0]],
        env=hermetic_env(HMAD_SKILL_ROOT=str(REPO_ROOT / "h-mad"), HOME=str(empty_home)),
        capture_output=True, text=True, timeout=60.0,
    )
    # host_unsupported is a cannot-judge: h_mad_context_budget.py exits 2 for it (design, impl-plan Task 5).
    assert result.returncode == 2, f"{host} budget command must report host_unsupported with rc 2: {result.stderr}"
    assert result.stdout.strip() == f"CTXBUDGET: UNKNOWN reason=host_unsupported host={host}", f"{host} budget must report unsupported host"


@pytest.mark.parametrize(
    "adapter_id,case",
    [(ADAPTER_ID, case) for case in (
        "agents-h-mad", "agents-handoff", "ln-s", "never-overwritten", "codex-hooks-json", "does-not-re-arm",
    )] + [("h-mad-agy", case) for case in ("gemini-h-mad", "gemini-handoff", "ln-s", "never-overwritten")],
    ids=[f"{ADAPTER_ID}-{case}" for case in (
        "agents-h-mad", "agents-handoff", "ln-s", "never-overwritten", "codex-hooks-json", "does-not-re-arm",
    )] + [f"h-mad-agy-{case}" for case in ("gemini-h-mad", "gemini-handoff", "ln-s", "never-overwritten")],
)
def test_install_section(adapter_id: str, case: str) -> None:
    section = _required_section(adapter_id, "## Install", f"install {case}")
    lines = _fenced_lines(section)
    if case == "agents-h-mad":
        assert "ln -s /path/to/checkout/h-mad ~/.agents/skills/h-mad" in lines, "Install must fence the h-mad symlink command"
    elif case == "agents-handoff":
        assert "ln -s /path/to/checkout/handoff ~/.agents/skills/handoff" in lines, "Install must fence the handoff symlink command"
    elif case == "gemini-h-mad":
        assert "ln -s /path/to/checkout/h-mad ~/.gemini/config/skills/h-mad" in lines, "Install must fence the agy h-mad symlink command"
    elif case == "gemini-handoff":
        assert "ln -s /path/to/checkout/handoff ~/.gemini/config/skills/handoff" in lines, "Install must fence the agy handoff symlink command"
    elif case == "ln-s":
        assert sum(line.startswith("ln -s ") for line in lines) == 2, "Install must provide both ln -s commands"
        if adapter_id == "h-mad-agy":
            assert 'python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py" --agy-skills-dir ~/.gemini/config/skills' in lines, "agy Install must fence its host-specific checker"
    elif case == "never-overwritten":
        assert "an existing non-symlink at either path is an operator decision and is never overwritten" in section, "Install must protect existing non-symlinks"
    elif case == "codex-hooks-json":
        assert ".codex/hooks.json" in section and '{"hooks": {}}' in section, "Install must describe the tracked empty Codex hooks file"
    else:
        assert "does not re-arm" in section, "Install must explain that linking does not re-arm the Codex TDD gate"
        assert 'python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py" --agents-skills-dir ~/.agents/skills' in section, "Install must include the host-specific checker"
