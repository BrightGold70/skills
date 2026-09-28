"""Host construct parity: registry, Markdown tables, coverage, and branch controls."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

import host_parity
from test_h_mad_doc_block_exec import recognition_sites


REPO_ROOT = Path(__file__).resolve().parents[2]
ADVISOR_ROW = "| `advisor` | not-applicable | no advisor tool on this host | observed: fixture |"
CLAUDE_ROW = "| `claude-md` | mapped | the host project rules file | observed: fixture |"
HEADER = "| construct | status | mapping | source |"
DELIMITER = "|---|---|---|---|"
HOSTS = ("codex", "agy", "grok")

SEED_IDS = (
    "subagent-call", "skill-call", "advisor", "send-message", "hook-event",
    "task-tools", "tool-search", "session-id-env", "claude-config-dir",
    "skill-root-env", "todo-tools-optin", "claude-md", "claude-skills-dir",
    "claude-agents-dir", "claude-hooks-dir", "claude-settings",
    "claude-handoffs-dir", "claude-projects-store", "claude-homunculus",
    "claude-home-bare", "session-reset-command", "skill-slash-invocation",
)
RETIRED_IDS: dict[str, str] = {}

# These 54 examples are literal host spellings, maintained independently of
# the registry regexes and the branch expander.
BRANCH_SAMPLES = {
    "subagent-call": ["Agent(", "subagent_type"],
    "skill-call": ["Skill("],
    "advisor": ["advisor()"],
    "send-message": ["SendMessage"],
    "hook-event": ["PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "SessionStart", "Stop-hook"],
    "task-tools": ["TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "TodoWrite"],
    "tool-search": ["ToolSearch"],
    "session-id-env": ["CLAUDE_CODE_SESSION_ID"],
    "claude-config-dir": ["CLAUDE_CONFIG_DIR"],
    "skill-root-env": ["CLAUDE_SKILLS_ROOT"],
    "todo-tools-optin": ["CLAUDE_CODE_ENABLE_TODO_TOOLS"],
    "claude-md": ["CLAUDE.md"],
    "claude-skills-dir": ["~/.claude/skills", "$HOME/.claude/skills", "${HOME}/.claude/skills"],
    "claude-agents-dir": ["~/.claude/agents", "$HOME/.claude/agents", "${HOME}/.claude/agents"],
    "claude-hooks-dir": ["~/.claude/hooks", "$HOME/.claude/hooks", "${HOME}/.claude/hooks"],
    "claude-settings": [
        "~/.claude/settings.json", "~/.claude/settings.local.json",
        "$HOME/.claude/settings.json", "$HOME/.claude/settings.local.json",
        "${HOME}/.claude/settings.json", "${HOME}/.claude/settings.local.json",
    ],
    "claude-handoffs-dir": ["~/.claude/handoffs", "$HOME/.claude/handoffs", "${HOME}/.claude/handoffs"],
    "claude-projects-store": ["~/.claude/projects", "$HOME/.claude/projects", "${HOME}/.claude/projects", "MEMORY.md"],
    "claude-homunculus": ["~/.claude/homunculus", "$HOME/.claude/homunculus", "${HOME}/.claude/homunculus"],
    "claude-home-bare": ["~/.claude", "$HOME/.claude", "${HOME}/.claude"],
    "session-reset-command": ["`/clear", "`/compact"],
    "skill-slash-invocation": ["`/h-mad", "`/handoff"],
}

AXIS_TOKENS = {
    "A1": "Foobar(",
    "A2": "`FooBar`",
    "A3": "CLAUDE_FOO",
    "A4-tilde": "~/.claude/foo",
    "A4-home": "$HOME/.claude/foo",
    "A4-home-braced": "${HOME}/.claude/foo",
}
SUFFIXES = ("Error", "Exception", "Warning", "Expired", "Exit", "Interrupt")


def _missing_seed_ids(registry_ids, seed_ids, retired) -> list[str]:
    return [i for i in seed_ids if i not in registry_ids and not retired.get(i)]


def _registry(paths):
    return json.loads(paths.registry.read_text(encoding="utf-8"))


def _write_registry(paths, data):
    paths.registry.write_text(json.dumps(data), encoding="utf-8")


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture prerequisite absent: {old!r} in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _adapter(paths, skill="h-mad", host="codex") -> Path:
    path = paths.root / skill / "references" / f"{host}-runtime.md"
    assert path in paths.adapters
    return path


def _baseline(tmp_path: Path) -> host_parity.ParityPaths:
    registry = tmp_path / "h-mad" / "references" / "host-constructs.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"constructs": [
        {"id": "advisor", "pattern": r"\badvisor\(\)", "skills": ["h-mad"], "description": "Calls the advisor tool."},
        {"id": "claude-md", "pattern": r"\bCLAUDE\.md\b", "skills": ["h-mad", "handoff"], "description": "Names the project rules file."},
    ]}), encoding="utf-8")
    skills = {
        "h-mad": tmp_path / "h-mad" / "SKILL.md",
        "handoff": tmp_path / "handoff" / "SKILL.md",
    }
    for path in skills.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    skills["h-mad"].write_text("# h\n\nCall advisor() before CLAUDE.md is read.\n", encoding="utf-8")
    skills["handoff"].write_text("# f\n\nRead CLAUDE.md first.\n", encoding="utf-8")
    adapters = {}
    for skill in skills:
        for host in HOSTS:
            path = tmp_path / skill / "references" / f"{host}-runtime.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            rows = [ADVISOR_ROW, CLAUDE_ROW] if skill == "h-mad" else [CLAUDE_ROW]
            path.write_text("\n".join(["# A", "", "## Construct mapping", "", HEADER, DELIMITER, *rows, ""]), encoding="utf-8")
            adapters[path] = skill
    return host_parity.ParityPaths(tmp_path, registry, skills, adapters)


def _pairs(result):
    return {(f.kind, f.reason) for f in result.failures}


def _lines(result):
    return [f.line() for f in result.failures]


def _h_mad_unregistered(result, paths):
    target = str(paths.skills["h-mad"].relative_to(paths.root))
    return [f for f in result.failures if f.kind == "UNREGISTERED" and f.file == target]


def _empty_registry_with_token(tmp_path, token):
    paths = _baseline(tmp_path)
    _write_registry(paths, {"constructs": []})
    paths.skills["h-mad"].write_text(token + "\n", encoding="utf-8")
    return paths


@pytest.fixture(scope="module")
def live_result():
    return host_parity.check(host_parity.live_paths(REPO_ROOT))


def test_live_registry_and_skill_files_are_clean(live_result):
    assert "registry" in live_result.stages
    allowed = {"h-mad/references/host-constructs.json", "h-mad/SKILL.md", "handoff/SKILL.md"}
    allowed.update(f"{skill}/references/{host}-runtime.md" for skill in ("h-mad", "handoff") for host in HOSTS)
    assert all(f.file in allowed for f in live_result.failures), _lines(live_result)
    assert not [f.line() for f in live_result.failures if f.file in {"h-mad/references/host-constructs.json", "h-mad/SKILL.md", "handoff/SKILL.md"}], _lines(live_result)


@pytest.mark.parametrize("skill,host", [(skill, host) for skill in ("h-mad", "handoff") for host in HOSTS], ids=[f"{skill}-{host}" for skill in ("h-mad", "handoff") for host in HOSTS])
def test_live_adapter_is_clean(live_result, skill, host):
    assert "adapter" in live_result.stages, "registry unreadable; adapter not checked"
    target = f"{skill}/references/{host}-runtime.md"
    assert not [f.line() for f in live_result.failures if f.file == target], "\n".join(_lines(live_result))


def test_clean_baseline_yields_nothing(tmp_path):
    assert _lines(host_parity.check(_baseline(tmp_path))) == []


KIND_CASES = [
    ("ru-missing-file", "REGISTRY_UNREADABLE", "missing_file"),
    ("ru-invalid-json", "REGISTRY_UNREADABLE", "invalid_json"),
    ("ru-not-object", "REGISTRY_UNREADABLE", "not_object"),
    ("ru-no-constructs", "REGISTRY_UNREADABLE", "no_constructs"),
    ("ru-constructs-not-array", "REGISTRY_UNREADABLE", "constructs_not_array"),
    ("ru-element-not-object", "REGISTRY_UNREADABLE", "element_not_object"),
    ("ru-missing-key-id", "REGISTRY_UNREADABLE", "missing_key:id"),
    ("ru-missing-key-pattern", "REGISTRY_UNREADABLE", "missing_key:pattern"),
    ("ru-missing-key-skills", "REGISTRY_UNREADABLE", "missing_key:skills"),
    ("ru-missing-key-description", "REGISTRY_UNREADABLE", "missing_key:description"),
    ("ru-extra-key", "REGISTRY_UNREADABLE", "extra_key:notes"),
    ("ru-bad-id", "REGISTRY_UNREADABLE", "bad_id"),
    ("ru-empty-description", "REGISTRY_UNREADABLE", "empty_description"),
    ("ru-empty-skills", "REGISTRY_UNREADABLE", "empty_skills"),
    ("ru-bad-skill", "REGISTRY_UNREADABLE", "bad_skill"),
    ("duplicate-id", "DUPLICATE_ID", None),
    ("bad-pattern", "BAD_PATTERN", None),
    ("stale-entry", "STALE_ENTRY", None),
    ("undeclared-skill", "UNDECLARED_SKILL", None),
    ("unregistered", "UNREGISTERED", None),
    ("tm-no-heading", "TABLE_MISSING", "no_heading"),
    ("tm-no-table", "TABLE_MISSING", "no_table"),
    ("tm-heading-twice", "TABLE_MISSING", "heading_twice"),
    ("tmal-header", "TABLE_MALFORMED", "header"),
    ("tmal-cell-count", "TABLE_MALFORMED", "cell_count"),
    ("row-missing", "ROW_MISSING", None),
    ("row-unknown-id", "ROW_UNKNOWN_ID", None),
    ("row-wrong-skill", "ROW_WRONG_SKILL", None),
    ("row-duplicate", "ROW_DUPLICATE", None),
    ("status-invalid", "STATUS_INVALID", None),
    ("ce-mapping-no-alnum", "CELL_EMPTY", "mapping:no_alnum"),
    ("ce-mapping-tbd", "CELL_EMPTY", "mapping:tbd"),
    ("ce-mapping-todo", "CELL_EMPTY", "mapping:todo"),
    ("ce-source-no-alnum", "CELL_EMPTY", "source:no_alnum"),
    ("ce-source-tbd", "CELL_EMPTY", "source:tbd"),
    ("ce-source-todo", "CELL_EMPTY", "source:todo"),
    ("split-bad-pattern-non-str", "BAD_PATTERN", None),
    ("split-bad-id-non-str", "REGISTRY_UNREADABLE", "bad_id"),
    ("split-bad-skill-non-list", "REGISTRY_UNREADABLE", "bad_skill"),
    ("split-bad-skill-duplicate-name", "REGISTRY_UNREADABLE", "bad_skill"),
    ("split-empty-description-non-str", "REGISTRY_UNREADABLE", "empty_description"),
    ("split-header-bad-delimiter", "TABLE_MALFORMED", "header"),
]


def _apply_kind_edit(paths, case):
    advisor = _adapter(paths)
    handoff = _adapter(paths, "handoff")
    if case == "ru-missing-file":
        paths.registry.unlink()
        return
    if case == "ru-invalid-json":
        paths.registry.write_text('{"constructs": [', encoding="utf-8")
        return
    if case == "ru-not-object":
        paths.registry.write_text("[]", encoding="utf-8")
        return
    if case == "ru-no-constructs":
        _write_registry(paths, {"entries": []})
        return
    if case == "ru-constructs-not-array":
        _write_registry(paths, {"constructs": {}})
        return
    registry_cases = {
        "ru-element-not-object", "ru-missing-key-id", "ru-missing-key-pattern",
        "ru-missing-key-skills", "ru-missing-key-description", "ru-extra-key",
        "ru-bad-id", "ru-empty-description", "ru-empty-skills", "ru-bad-skill",
        "duplicate-id", "bad-pattern", "split-bad-pattern-non-str",
        "split-bad-id-non-str", "split-bad-skill-non-list",
        "split-bad-skill-duplicate-name", "split-empty-description-non-str",
    }
    if case in registry_cases:
        data = _registry(paths)
        entries = data["constructs"]
        entry = entries[0]
        if case == "ru-element-not-object":
            entries[1] = "claude-md"
        elif case.startswith("ru-missing-key-"):
            del entry[case.removeprefix("ru-missing-key-")]
        elif case == "ru-extra-key":
            entry["notes"] = "x"
        elif case == "ru-bad-id":
            entry["id"] = "Advisor"
        elif case == "ru-empty-description":
            entry["description"] = ""
        elif case == "ru-empty-skills":
            entry["skills"] = []
        elif case == "ru-bad-skill":
            entry["skills"] = ["h-mad", "grok"]
        elif case == "duplicate-id":
            entries.append(entries[1].copy())
        elif case == "bad-pattern":
            entry["pattern"] = "("
        elif case == "split-bad-pattern-non-str":
            entry["pattern"] = 5
        elif case == "split-bad-id-non-str":
            entry["id"] = 7
        elif case == "split-bad-skill-non-list":
            entry["skills"] = {"h-mad": True}
        elif case == "split-bad-skill-duplicate-name":
            entry["skills"] = ["h-mad", "h-mad"]
        elif case == "split-empty-description-non-str":
            entry["description"] = 7
        _write_registry(paths, data)
        return
    if case == "stale-entry":
        _replace(paths.skills["h-mad"], "advisor()", "the tool")
    elif case == "undeclared-skill":
        with paths.skills["handoff"].open("a", encoding="utf-8") as stream:
            stream.write("Call advisor().\n")
    elif case == "unregistered":
        with paths.skills["h-mad"].open("a", encoding="utf-8") as stream:
            stream.write("Use `FooBar`.\n")
    elif case == "tm-no-heading":
        _replace(advisor, "## Construct mapping", "## Constructs")
    elif case == "tm-no-table":
        advisor.write_text("# A\n\n## Construct mapping\n\nThere is prose, but no table.\n", encoding="utf-8")
    elif case == "tm-heading-twice":
        with advisor.open("a", encoding="utf-8") as stream:
            stream.write("\n## Construct mapping\n\nThe second heading.\n")
    elif case == "tmal-header":
        _replace(advisor, HEADER, HEADER.replace("status", "state"))
    elif case == "tmal-cell-count":
        _replace(advisor, ADVISOR_ROW, "| `advisor` | not-applicable | no advisor tool |")
    elif case == "row-missing":
        _replace(advisor, ADVISOR_ROW + "\n", "advisor here, advisor again, advisor a third time.\n")
    elif case == "row-unknown-id":
        with advisor.open("a", encoding="utf-8") as stream:
            stream.write("| `zeta-thing` | mapped | a map | observed: fixture |\n")
    elif case == "row-wrong-skill":
        with handoff.open("a", encoding="utf-8") as stream:
            stream.write(ADVISOR_ROW + "\n")
    elif case == "row-duplicate":
        with advisor.open("a", encoding="utf-8") as stream:
            stream.write(CLAUDE_ROW + "\n")
    elif case == "status-invalid":
        _replace(advisor, ADVISOR_ROW, ADVISOR_ROW.replace("not-applicable", "maybe"))
    elif case.startswith("ce-"):
        _, cell, value = case.split("-", 2)
        value = {"no-alnum": "—", "tbd": "TbD", "todo": "ToDo"}[value]
        cells = ADVISOR_ROW.split(" | ")
        cells[2 if cell == "mapping" else 3] = value
        _replace(advisor, ADVISOR_ROW, " | ".join(cells))
    elif case == "split-header-bad-delimiter":
        _replace(advisor, DELIMITER, "|---|---|x|---|")
    else:
        raise AssertionError(f"unhandled fixture {case}")


@pytest.mark.parametrize("case,kind,reason", KIND_CASES, ids=[case for case, _, _ in KIND_CASES])
def test_kind_fixture_reports_exactly_its_pair(tmp_path, case, kind, reason):
    paths = _baseline(tmp_path)
    _apply_kind_edit(paths, case)
    result = host_parity.check(paths)
    assert _pairs(result) == {(kind, reason)}, f"{case}: expected {(kind, reason)}; got {_lines(result)}"
    assert all(line.startswith("PARITY ") and " file=" in line and " id=" in line for line in _lines(result)), _lines(result)
    if reason is not None:
        assert all(f"reason={reason}" in line for line in _lines(result)), _lines(result)
    if case == "unregistered":
        assert any("token=`FooBar`" in line for line in _lines(result)), _lines(result)
    if case == "tmal-cell-count":
        assert any("id=advisor" in line for line in _lines(result)), _lines(result)
    if case == "row-missing":
        assert any("id=advisor" in line for line in _lines(result)), _lines(result)


@pytest.mark.parametrize("rule", list("abcde"))
def test_suppression_rule_leaves_one_pair(tmp_path, rule):
    paths = _baseline(tmp_path)
    adapter = _adapter(paths)
    if rule == "a":
        _apply_kind_edit(paths, "ru-extra-key")
        _apply_kind_edit(paths, "tm-no-heading")
        expected = ("REGISTRY_UNREADABLE", "extra_key:notes")
    elif rule == "b":
        _apply_kind_edit(paths, "bad-pattern")
        _apply_kind_edit(paths, "unregistered")
        expected = ("BAD_PATTERN", None)
    elif rule == "c":
        _apply_kind_edit(paths, "duplicate-id")
        _replace(_adapter(paths, "handoff"), CLAUDE_ROW + "\n", "")
        expected = ("DUPLICATE_ID", None)
    elif rule == "d":
        _apply_kind_edit(paths, "tmal-header")
        _replace(adapter, ADVISOR_ROW, ADVISOR_ROW.replace("not-applicable", "maybe"))
        expected = ("TABLE_MALFORMED", "header")
    else:
        _replace(adapter, ADVISOR_ROW, "| `advisor` | not-applicable | no advisor tool | observed: fixture | extra |")
        expected = ("TABLE_MALFORMED", "cell_count")
    result = host_parity.check(paths)
    assert _pairs(result) == {expected}, f"suppression {rule}: {_lines(result)}"
    if rule == "e":
        assert any("id=advisor" in line for line in _lines(result)), _lines(result)


def test_absent_adapter_file_reads_as_no_heading(tmp_path):
    paths = _baseline(tmp_path)
    _adapter(paths).unlink()
    result = host_parity.check(paths)
    assert _pairs(result) == {("TABLE_MISSING", "no_heading")}, _lines(result)


@pytest.mark.parametrize("axis", AXIS_TOKENS)
def test_catch_all_axis_alone_reports_its_fixture(tmp_path, axis):
    token = AXIS_TOKENS[axis]
    paths = _empty_registry_with_token(tmp_path, token)
    if axis.startswith("A4-"):
        branch = host_parity.A4_BRANCHES[axis.removeprefix("A4-").replace("-", "_")]
        axes = {"A4": host_parity.a4_pattern([branch])}
    else:
        axes = {axis: host_parity.CATCH_ALL_AXES[axis]}
    assert any(f.token == token for f in _h_mad_unregistered(host_parity.check(paths, axes=axes), paths)), axis


@pytest.mark.parametrize("axis", ["A1", "A2", "A3", "A4", "A4-tilde", "A4-home", "A4-home-braced"])
def test_removing_an_axis_or_branch_clears_its_fixture(tmp_path, axis):
    if axis.startswith("A4-"):
        paths = _empty_registry_with_token(tmp_path, "\n".join(AXIS_TOKENS[f"A4-{name.replace('_', '-')}"] for name in host_parity.A4_BRANCHES))
        axes = {"A4": host_parity.a4_pattern(value for name, value in host_parity.A4_BRANCHES.items() if name.replace("_", "-") != axis.removeprefix("A4-"))}
        got = {f.token for f in _h_mad_unregistered(host_parity.check(paths, axes=axes), paths)}
        assert AXIS_TOKENS[axis] not in got, got
        assert {value for key, value in AXIS_TOKENS.items() if key.startswith("A4-") and key != axis} <= got, got
    else:
        token = AXIS_TOKENS["A4-tilde"] if axis == "A4" else AXIS_TOKENS[axis]
        paths = _empty_registry_with_token(tmp_path, token)
        axes = {key: value for key, value in host_parity.CATCH_ALL_AXES.items() if key != axis}
        assert _h_mad_unregistered(host_parity.check(paths, axes=axes), paths) == [], axis


@pytest.mark.parametrize("axis", AXIS_TOKENS)
def test_default_axes_report_each_fixture(tmp_path, axis):
    token = AXIS_TOKENS[axis]
    paths = _empty_registry_with_token(tmp_path, token)
    assert any(f.token == token for f in _h_mad_unregistered(host_parity.check(paths), paths)), axis


@pytest.mark.parametrize("suffix", SUFFIXES)
def test_exclusion_suffix_hides_its_fixture(tmp_path, suffix):
    paths = _empty_registry_with_token(tmp_path, f"`Foo{suffix}`")
    assert _h_mad_unregistered(host_parity.check(paths, axes={"A2": host_parity.CATCH_ALL_AXES["A2"]}), paths) == []


@pytest.mark.parametrize("suffix", SUFFIXES)
def test_removed_exclusion_suffix_reports_its_fixture(tmp_path, suffix):
    token = f"`Foo{suffix}`"
    paths = _empty_registry_with_token(tmp_path, token)
    exclusions = [name for name in host_parity.EXCLUSION_SUFFIXES if name != suffix]
    result = host_parity.check(paths, axes={"A2": host_parity.CATCH_ALL_AXES["A2"]}, exclusion_suffixes=exclusions)
    assert any(f.token == token for f in _h_mad_unregistered(result, paths)), _lines(result)


def test_unregistered_teamcreate_then_registered_passes(tmp_path):
    paths = _baseline(tmp_path)
    with paths.skills["h-mad"].open("a", encoding="utf-8") as stream:
        stream.write("Use `TeamCreate`.\n")
    result = host_parity.check(paths)
    assert any(f.kind == "UNREGISTERED" and f.token == "`TeamCreate`" for f in result.failures), _lines(result)
    data = _registry(paths)
    data["constructs"].append({"id": "team-create", "pattern": r"\bTeamCreate\b", "skills": ["h-mad"], "description": "Names the team creation tool."})
    _write_registry(paths, data)
    for host in HOSTS:
        with _adapter(paths, host=host).open("a", encoding="utf-8") as stream:
            stream.write("| `team-create` | mapped | a team tool | observed: fixture |\n")
    assert _lines(host_parity.check(paths)) == []


def test_fenced_pipe_table_is_not_the_table(tmp_path):
    paths = _baseline(tmp_path)
    fenced = "```markdown\n" + HEADER + "\n" + DELIMITER + "\n| `zeta-thing` | mapped | a map | observed: fixture |\n```\n\n"
    _replace(_adapter(paths), HEADER, fenced + HEADER)
    assert _lines(host_parity.check(paths)) == []


def test_registry_holds_every_seed_id():
    registry = host_parity.live_paths(REPO_ROOT).registry
    assert registry.is_file(), f"registry file absent: {registry}"
    ids = [entry["id"] for entry in json.loads(registry.read_text(encoding="utf-8"))["constructs"]]
    assert _missing_seed_ids(ids, SEED_IDS, RETIRED_IDS) == [], "registry lacks seed ids without retirement reasons"


@pytest.mark.parametrize("construct_id", BRANCH_SAMPLES, ids=list(BRANCH_SAMPLES))
def test_registry_branch_samples(construct_id):
    registry = host_parity.live_paths(REPO_ROOT).registry
    assert registry.is_file(), f"registry file absent: {registry}"
    entries = {entry["id"]: entry for entry in json.loads(registry.read_text(encoding="utf-8"))["constructs"]}
    assert construct_id in entries, f"registry lacks branch sample id {construct_id}"
    pattern = entries[construct_id]["pattern"]
    branches = host_parity.expand_branches(pattern)
    samples = BRANCH_SAMPLES[construct_id]
    assert len(samples) == len(branches), f"{construct_id}: sample count {len(samples)} != branch count {len(branches)}"
    for sample in samples:
        assert sum(bool(re.search(branch, sample)) for branch in branches) == 1, f"{construct_id}: {sample!r} must match exactly one branch"
        assert re.search(pattern, sample), f"{construct_id}: full pattern misses {sample!r}"


@pytest.mark.parametrize("shape", ["(?:a|b)+", "a{2}", "(a"], ids=["group-plus", "atom-brace", "unbalanced"])
def test_branch_expander_refuses_unsupported_shapes(shape):
    with pytest.raises(host_parity.UnsupportedPattern):
        host_parity.expand_branches(shape)


def _stubs(tmp_path):
    directory = tmp_path / "bin"
    directory.mkdir()
    markers = {}
    for name in HOSTS:
        marker = tmp_path / f"{name}.called"
        script = directory / name
        script.write_text(f"#!/bin/sh\n: > '{marker}'\nexit 99\n", encoding="utf-8")
        script.chmod(0o755)
        markers[name] = marker
    return directory, markers


def test_gate_runs_no_host_cli(tmp_path, monkeypatch):
    stub_dir, markers = _stubs(tmp_path)
    monkeypatch.setenv("CLAUDE_ZZZ_PROBE", "1")
    monkeypatch.setenv("PATH", str(stub_dir))
    host_parity.check(host_parity.live_paths(REPO_ROOT))
    assert not [name for name, marker in markers.items() if marker.exists()], "parity gate launched a host CLI"


@pytest.mark.parametrize("name", HOSTS)
def test_host_cli_stub_control_fires(tmp_path, monkeypatch, name):
    stub_dir, markers = _stubs(tmp_path)
    monkeypatch.setenv("CLAUDE_ZZZ_PROBE", "1")
    result = subprocess.run([name], env={"PATH": str(stub_dir)}, timeout=60.0)
    assert result.returncode == 99, f"{name} stub did not execute"
    assert markers[name].exists(), f"{name} stub failed to write its marker"


def test_host_parity_has_no_direct_launcher_import():
    source = Path(host_parity.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in source, "host_parity must not import a direct process launcher"
    assert "os.system" not in source and "os.popen" not in source, "host_parity must not call a shell launcher"


@pytest.mark.parametrize("retired,expected", [
    ({"advisor": "fixture reason"}, [],),
    ({"advisor": ""}, ["advisor"],),
    ({}, ["advisor"],),
], ids=["retired-with-reason", "retired-empty-reason", "absent-not-retired"])
def test_seed_check_honours_retirement(retired, expected):
    assert _missing_seed_ids(["claude-md"], ["advisor", "claude-md"], retired) == expected


def test_host_parity_has_no_fence_scanner():
    assert recognition_sites("def f(t):\n    return t.startswith('#')\n") == {"f"}, "fence scanner guard must recognize a real scanner"
    source = Path(host_parity.__file__).read_text(encoding="utf-8")
    assert recognition_sites(source) == set(), "host_parity must reuse the shared fence scanner"


def test_expand_branches_optional_group_adds_empty_alternative():
    assert sorted(host_parity.expand_branches("x(?:y)?z")) == ["xyz", "xz"], "optional group must contribute its empty branch"
