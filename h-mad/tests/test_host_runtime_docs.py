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
HOST_ADAPTERS = (ADAPTER_ID, "h-mad-agy", "h-mad-grok")
BASE_SHA = "52a78ca8"
REFUSAL_FORM_AT_BASE = "b"


def _refusal_form_at_base() -> str:
    shown = subprocess.run(
        ["git", "show", f"{BASE_SHA}:h-mad/hooks/h-mad-tdd-gate.sh"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True, timeout=60.0,
    ).stdout
    assert 'readonly REFUSAL_FORM=b' in shown
    assert '"permissionDecision":"deny"' in shown
    assert 'exit 2  # M:H5A' in shown
    assert 'tool_input.get(\'file_path\')' in shown
    assert 'toolInput' not in shown
    return "b"


REFUSAL_TOKEN = {"exit1": "exit 1", "a": "exit 2", "b": "permissionDecision"}[REFUSAL_FORM_AT_BASE]


def test_refusal_form_pin_matches_rebased_base() -> None:
    assert _refusal_form_at_base() == REFUSAL_FORM_AT_BASE


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
        if not ADAPTERS[adapter_id].is_file():
            raise LookupError(f"adapter absent: {ADAPTERS[adapter_id]}")
        return _section(ADAPTERS[adapter_id].read_text(encoding="utf-8"), heading)
    except (FileNotFoundError, LookupError) as exc:
        pytest.fail(f"{adapter_id} {property_name}: {exc}")


def _row(adapter_id: str, construct_id: str, property_name: str) -> host_parity.Row:
    _required_section(adapter_id, "## Construct mapping", property_name)
    text = ADAPTERS[adapter_id].read_text(encoding="utf-8")
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
        ("h-mad-grok", "status", "not-applicable"),
        ("h-mad-grok", "hmad-dispatch-exec", "hmad-dispatch exec"),
        ("h-mad-grok", "spawn-subagent", "spawn_subagent"),
    ],
    ids=[
        "h-mad-codex-status", "h-mad-codex-hmad-dispatch-exec", "h-mad-codex-spawn-agent", "h-mad-codex-fork-turns",
        "h-mad-agy-status", "h-mad-agy-hmad-dispatch-exec", "h-mad-agy-invoke-subagent",
        "h-mad-grok-status", "h-mad-grok-hmad-dispatch-exec", "h-mad-grok-spawn-subagent",
    ],
)
def test_advisor_row(adapter_id: str, property_name: str, expected: str) -> None:
    row = _row(adapter_id, "advisor", f"advisor {property_name}")
    if property_name == "status":
        assert row.status == expected, f"advisor must be not-applicable on {adapter_id}"
    else:
        assert expected in row.mapping, f"advisor mapping must contain {expected}"
    if adapter_id == "h-mad-grok" and property_name == "spawn-subagent":
        roles = _required_section(adapter_id, "## Author and reviewer roles", "author and reviewer roles")
        for token in ("spawn_subagent", "prompt", "get_command_or_subagent_output", "git status --short"):
            assert token in roles, f"grok Author and reviewer roles must state {token}"


@pytest.mark.parametrize(
    "adapter_id,token",
    [(adapter_id, token) for adapter_id in HOST_ADAPTERS for token in (
        ("uuid.uuid4()", "owned_elsewhere", "GROK_SESSION_ID", "hook processes")
        if adapter_id == "h-mad-grok" else ("uuid.uuid4()", "owned_elsewhere")
    )],
    ids=[f"{adapter_id}-{suffix}" for adapter_id in HOST_ADAPTERS for suffix in (
        ("uuid4", "owned-elsewhere", "grok-session-id", "hook-processes")
        if adapter_id == "h-mad-grok" else ("uuid4", "owned-elsewhere")
    )],
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


@pytest.mark.parametrize("adapter_id", (*HOST_ADAPTERS, "handoff-codex", "handoff-agy", "handoff-grok"), ids=(*HOST_ADAPTERS, "handoff-codex", "handoff-agy", "handoff-grok"))
def test_not_applicable_rows_state_a_reason(adapter_id: str) -> None:
    _required_section(adapter_id, "## Construct mapping", "not-applicable rows state a reason")
    table = host_parity.adapter_table(ADAPTERS[adapter_id].read_text(encoding="utf-8"))
    assert table.problems == [], f"Construct mapping table must parse: {table.problems}"
    rows = [row for row in table.rows if row.status == "not-applicable"]
    assert rows, "Construct mapping must include at least one not-applicable row"
    if adapter_id == "handoff-grok":
        settings = _row(adapter_id, "claude-settings", "claude-settings not-applicable")
        assert settings.status == "not-applicable", "handoff-grok claude-settings must be not-applicable"
        assert "todo_write" in settings.mapping, "handoff-grok claude-settings must explain that todo_write needs no settings opt-in"
    for row in rows:
        mapping = re.sub(r"`[^`]*`", " ", row.mapping).strip()
        assert len(re.findall(r"[A-Za-z]{2,}", mapping)) >= 3, f"{row.id} not-applicable mapping needs a reason of at least three words"
        assert re.fullmatch(r"(?i)(?:n/?a|not[- ]applicable|none)\.?", mapping) is None, f"{row.id} needs more than a status word"
        assert row.mapping != row.source, f"{row.id} reason must differ from source"


@pytest.mark.parametrize(
    "adapter_id,case,field,token",
    [
        ("handoff-codex", "status", "status", "not-applicable"),
        ("handoff-codex", "notepad", "mapping", ".omc/notepad.md"),
        ("handoff-codex", "update-plan", "mapping", "update_plan"),
        ("handoff-agy", "status", "status", "not-applicable"),
        ("handoff-agy", "manage-task", "mapping", "manage_task"),
        ("handoff-agy", "notepad", "mapping", ".omc/notepad.md"),
        ("handoff-grok", "status", "status", "mapped"),
        ("handoff-grok", "todo-write", "mapping", "todo_write"),
        ("handoff-grok", "ctrl-t", "mapping", "Ctrl+T"),
    ],
    ids=[
        "handoff-codex-status", "handoff-codex-notepad", "handoff-codex-update-plan",
        "handoff-agy-status", "handoff-agy-manage-task", "handoff-agy-notepad",
        "handoff-grok-status", "handoff-grok-todo-write", "handoff-grok-ctrl-t",
    ],
)
def test_task_tools_row(adapter_id: str, case: str, field: str, token: str) -> None:
    row = _row(adapter_id, "task-tools", f"task-tools {case}")
    assert token in getattr(row, field), f"{adapter_id} task-tools {case} must state {token}"
    if case == "update-plan":
        assert "lead" in row.mapping.lower(), "handoff-codex task-tools must identify update_plan as a lead"
    if adapter_id == "handoff-grok" and case == "todo-write":
        tools = _required_section(adapter_id, "## grok tool mapping", "grok tool mapping")
        for name in ("todo_write", "Ctrl+T", "spawn_subagent", "HANDOFF_SKILL_ROOT", "loaded skill path"):
            assert name in tools, f"handoff-grok grok tool mapping must state {name}"


@pytest.mark.parametrize(
    "adapter_id,token",
    [(adapter_id, token) for adapter_id in HOST_ADAPTERS for token in (
        ("CTXBUDGET: UNKNOWN reason=host_unsupported", "80%", "substitute: none", "/context", "not an orchestrator gate")
        if adapter_id == "h-mad-grok" else ("CTXBUDGET: UNKNOWN reason=host_unsupported", "80%", "substitute: none")
    )],
    ids=[f"{adapter_id}-{suffix}" for adapter_id in HOST_ADAPTERS for suffix in (
        ("unknown", "80pct", "substitute-none", "slash-context", "not-a-gate")
        if adapter_id == "h-mad-grok" else ("unknown", "80pct", "substitute-none")
    )],
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
    )] + [("h-mad-agy", case) for case in ("gemini-h-mad", "gemini-handoff", "ln-s", "never-overwritten")]
    + [("h-mad-grok", case) for case in (
        "agents-h-mad", "agents-handoff", "ln-s", "never-overwritten", "codex-hooks-json", "does-not-re-arm",
    )],
    ids=[f"{ADAPTER_ID}-{case}" for case in (
        "agents-h-mad", "agents-handoff", "ln-s", "never-overwritten", "codex-hooks-json", "does-not-re-arm",
    )] + [f"h-mad-agy-{case}" for case in ("gemini-h-mad", "gemini-handoff", "ln-s", "never-overwritten")]
    + [f"h-mad-grok-{case}" for case in (
        "agents-h-mad", "agents-handoff", "ln-s", "never-overwritten", "codex-hooks-json", "does-not-re-arm",
    )],
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


@pytest.mark.parametrize(
    "case,token",
    [
        ("grok-session-id", "GROK_SESSION_ID"),
        ("smoke-condition", "only after the live smoke records it present in the orchestrator's shell"),
    ],
    ids=["grok-session-id", "smoke-condition"],
)
def test_grok_session_id_condition(case: str, token: str) -> None:
    section = _claims("h-mad-grok", f"session id condition {case}")
    assert token in section, f"grok session id condition {case} must state {token}"


@pytest.mark.parametrize(
    "adapter_id,case,token",
    [
        ("h-mad-grok", "version", "1.0.41"),
        ("h-mad-grok", "compat-skills", "compat.claude.skills"),
        ("h-mad-grok", "compat-hooks", "compat.claude.hooks"),
        ("handoff-grok", "version", "1.0.41"),
        ("handoff-grok", "compat-skills", "compat.claude.skills"),
    ],
    ids=["h-mad-grok-version", "h-mad-grok-compat-skills", "h-mad-grok-compat-hooks", "handoff-grok-version", "handoff-grok-compat-skills"],
)
def test_version_and_compatibility(adapter_id: str, case: str, token: str) -> None:
    section = _required_section(adapter_id, "## Version and compatibility", f"version and compatibility {case}")
    assert token in section, f"grok Version and compatibility must state {token}"
    if case == "version":
        assert "grok inspect" in section, "grok Version and compatibility must name the verification command"
        text = ADAPTERS[adapter_id].read_text(encoding="utf-8")
        if adapter_id == "handoff-grok":
            headings = (
                "# grok runtime adapter", "## Version and compatibility", "## Resolve the skill package",
                "## grok tool mapping", "## Mode routing", "## Construct mapping", "## Safety invariants",
            )
        else:
            headings = (
                "# grok runtime adapter", "## Version and compatibility", "## Package and project roots",
                "## Install", "## Project trust", "## Hooks", "## The TDD gate",
                "## Author and reviewer roles", "## Context budget and claims", "## Memory index",
                "## Construct mapping", "## What does not change",
            )
        positions = [text.find(heading + "\n") for heading in headings]
        assert -1 not in positions and positions == sorted(positions), "grok adapter must have every required section in order"
    elif case == "compat-skills":
        if adapter_id == "handoff-grok":
            roots = _required_section(adapter_id, "## Resolve the skill package", "resolve the skill package")
            for root in ("HANDOFF_SKILL_ROOT", "loaded skill path"):
                assert root in roots, f"handoff-grok Resolve the skill package must state {root}"
        else:
            roots = _required_section(adapter_id, "## Package and project roots", "package and project roots")
            for root in ("HMAD_SKILL_ROOT", "~/.claude/skills/h-mad", "~/.agents/skills/h-mad"):
                assert root in roots, f"grok Package and project roots must state {root}"
    else:
        trust = _required_section("h-mad-grok", "## Project trust", "project trust")
        assert "/hooks-trust" in trust and "--trust" in trust, "grok Project trust must name both trust controls"


@pytest.mark.parametrize(
    "case,token",
    [
        ("halt-token", "step5:grok_tdd_hook_unverified"),
        ("tool-input", "toolInput"),
        ("fails-open", "fails open"),
        ("pytest", "pytest"),
        ("reason-i", REFUSAL_TOKEN),
    ],
    ids=["halt-token", "tool-input", "fails-open", "pytest", "reason-i"],
)
def test_tdd_gate_section(case: str, token: str) -> None:
    section = _required_section("h-mad-grok", "## The TDD gate", f"TDD gate {case}")
    assert token in section, f"grok TDD gate {case} must state {token}"
    if case == "reason-i":
        assert "exit 1" not in section, "grok gate reason must not describe the pre-rebase refusal"


@pytest.mark.parametrize(
    "case,field,token",
    [
        ("status", "status", "not-applicable"),
        ("grok-memory", "mapping", "~/.grok/memory"),
        ("memory-index-script", "mapping", "h_mad_check_memory_index.py"),
    ],
    ids=["status", "grok-memory", "memory-index-script"],
)
def test_claude_projects_store_row(case: str, field: str, token: str) -> None:
    row = _row("h-mad-grok", "claude-projects-store", f"claude-projects-store {case}")
    assert token in getattr(row, field), f"grok claude-projects-store {case} must state {token}"
    if case == "memory-index-script":
        section = _required_section("h-mad-grok", "## Memory index", "memory index")
        assert "~/.grok/memory" in section, "grok Memory index must name its own store"
        assert "h_mad_check_memory_index.py" in section, "grok Memory index must name the checker"


@pytest.mark.parametrize("adapter_id", ["h-mad-grok", "handoff-grok"], ids=["h-mad-grok", "handoff-grok"])
def test_grok_source_cells_format(adapter_id: str) -> None:
    _required_section(adapter_id, "## Construct mapping", "grok source cells format")
    table = host_parity.adapter_table(ADAPTERS[adapter_id].read_text(encoding="utf-8"))
    assert table.problems == [], f"{adapter_id} Construct mapping problems: {table.problems}"
    assert table.rows, f"{adapter_id} Construct mapping must have at least one row"
    for row in table.rows:
        assert (
            re.search(r"\b\d\d-[a-z-]+\.md\b", row.source)
            or row.source == "grok inspect"
            or row.source.startswith("observed:")
        ), f"{adapter_id} {row.id} source must cite a grok chapter, grok inspect, or observed evidence"


@pytest.mark.parametrize(
    "case,token",
    [("hook-name", "h-mad-advisor-warn.sh"), ("ctxbudget", "CTXBUDGET"), ("ignore", "ignore")],
    ids=["hook-name", "ctxbudget", "ignore"],
)
def test_hooks_section_advisor_warn_note(case: str, token: str) -> None:
    section = _required_section("h-mad-grok", "## Hooks", f"advisor warn note {case}")
    assert token in section, f"grok Hooks advisor warn note {case} must state {token}"
    if case == "hook-name":
        assert "a 5 s handler limit, after which the handler fails open" in section, "grok Hooks must state the 5 s fail-open handler limit"


@pytest.mark.parametrize(
    "skill,host",
    [(skill, host) for skill in ("h-mad", "handoff") for host in ("codex", "agy", "grok")],
    ids=[f"{skill}-{host}" for skill in ("h-mad", "handoff") for host in ("codex", "agy", "grok")],
)
def test_host_runtime_names_every_adapter(skill: str, host: str) -> None:
    section = _section((REPO_ROOT / skill / "SKILL.md").read_text(encoding="utf-8"), "## Host runtime")
    adapter = f"references/{host}-runtime.md"
    assert adapter in section, f"{skill} Host runtime must name {adapter}"


@pytest.mark.parametrize("case", ("renamed", "doubled"), ids=("renamed", "doubled"))
def test_host_runtime_locator_fails_loudly(case: str) -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    heading = "## Host runtime"
    assert text.count(heading + "\n") == 1, "fixture requires one Host runtime heading"
    changed = text.replace(heading + "\n", "## Runtime hosts\n", 1) if case == "renamed" else text + "\n" + heading + "\n"
    with pytest.raises(LookupError, match="heading absent" if case == "renamed" else "heading doubled"):
        _section(changed, heading)


@pytest.mark.parametrize("case,token", (("hmad-host", "HMAD_HOST"), ("session-id", "--session-id")), ids=("hmad-host", "session-id"))
def test_cannot_judge_row_names_host_cause(case: str, token: str) -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, '## Decision routing (for `/h-mad "<feature>"`)')
    rows = [line for line in section.splitlines() if line.startswith("| `cannot_judge` |")]
    assert len(rows) == 1, "Decision routing must have exactly one cannot_judge row"
    assert token in rows[0], f"cannot_judge row must name {token} as a host cause ({case})"


@pytest.mark.parametrize(
    "case,token",
    (
        ("agents-root", "~/.agents/skills"),
        ("agy-root", "~/.gemini/config/skills"),
        ("agents-env", "HMAD_AGENTS_SKILLS_DIR"),
        ("agy-env", "HMAD_AGY_SKILLS_DIR"),
    ),
    ids=("agents-root", "agy-root", "agents-env", "agy-env"),
)
def test_bootstrap_install_check_names_host_roots(case: str, token: str) -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## First-run auto-bootstrap")
    assert token in section, f"First-run auto-bootstrap must name {case}: {token}"


@pytest.mark.parametrize(
    "case,root",
    (("agents", "~/.agents/skills"), ("agy", "~/.gemini/config/skills")),
    ids=("agents", "agy"),
)
def test_sibling_remedy_names_every_root(case: str, root: str) -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## First-run auto-bootstrap")
    rows = [line for line in section.splitlines() if line.startswith("| `SIBLING_NOT_SYMLINK` |")]
    assert len(rows) == 1, "First-run auto-bootstrap needs exactly one SIBLING_NOT_SYMLINK remedy"
    assert root in rows[0], f"SIBLING_NOT_SYMLINK remedy must name {case} root {root}"


def test_agy_collision_row_present() -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## First-run auto-bootstrap")
    rows = [line for line in section.splitlines() if line.startswith("| `AGY_SIBLING_COLLISION` |")]
    assert len(rows) == 1, "First-run auto-bootstrap needs exactly one AGY_SIBLING_COLLISION row"


@pytest.mark.parametrize(
    "case,token",
    (("agents-option", "--agents-skills-dir"), ("agy-option", "--agy-skills-dir"), ("agy-collision", "AGY_SIBLING_COLLISION:")),
    ids=("agents-option", "agy-option", "agy-collision"),
)
def test_helper_registry_install_check_line(case: str, token: str) -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)")
    lines = [line for line in section.splitlines() if line.startswith("- `h_mad_install_check.py` —")]
    assert len(lines) == 1, "Helper scripts needs exactly one install-check entry"
    assert token in lines[0], f"install-check registry line must name {case}: {token}"


@pytest.mark.parametrize(
    "case,token",
    (("host-unsupported", "host_unsupported"), ("unknown-host", "unknown_host")),
    ids=("host-unsupported", "unknown-host"),
)
def test_helper_registry_budget_line(case: str, token: str) -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)")
    lines = [line for line in section.splitlines() if line.startswith("- `h_mad_context_budget.py` —")]
    assert len(lines) == 1, "Helper scripts needs exactly one context-budget entry"
    assert token in lines[0], f"context-budget registry line must name {case}: {token}"


def test_helper_registry_lists_h_mad_host() -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)")
    lines = [line for line in section.splitlines() if line.startswith("- `h_mad_host.py` —")]
    assert len(lines) == 1, "Helper scripts needs exactly one h_mad_host.py entry"
    assert "HMAD_HOST" in lines[0], "h_mad_host.py registry line must name HMAD_HOST"


def test_remedy_count_sentence_names_the_eleventh_row() -> None:
    text = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    section = _section(text, "## First-run auto-bootstrap")
    lines = [line for line in section.splitlines() if "all ten have one" in line]
    assert len(lines) == 1, "First-run auto-bootstrap needs exactly one remedy-count sentence"
    assert "the eleventh row, `AGY_SIBLING_COLLISION`" in lines[0], "remedy-count sentence must name the eleventh AGY_SIBLING_COLLISION row"
