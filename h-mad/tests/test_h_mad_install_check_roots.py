"""Host skill roots are checked by the install-check CLI without changing its API default."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_install_check.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_install_check as ic


def _checkout(root: Path, names=("h-mad", "handoff", "debugger")) -> Path:
    repo = root / "checkout"
    for name in names:
        skill = repo / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    hook = repo / "h-mad" / "hooks" / "h-mad-tdd-gate.sh"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\n", encoding="utf-8")
    return repo


def _install(tmp_path: Path, names=("h-mad", "handoff", "debugger")):
    repo = _checkout(tmp_path, names)
    claude = tmp_path / "claude-skills"
    claude.mkdir()
    (claude / "h-mad").symlink_to(repo / "h-mad")
    hook = tmp_path / "hooks" / "h-mad-tdd-gate.sh"
    hook.parent.mkdir()
    hook.symlink_to(repo / "h-mad" / "hooks" / "h-mad-tdd-gate.sh")
    return repo, claude, hook


def _state(root: Path, repo: Path, name: str, state: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    link = root / name
    if state == "absent":
        return
    if state == "correct":
        link.symlink_to(repo / name)
    elif state == "copy":
        link.mkdir()
        (link / "SKILL.md").write_text("stale copy\n", encoding="utf-8")
    elif state == "dangling":
        link.symlink_to(root / "missing" / name)
    elif state == "other-checkout":
        other = root.parent / "other-checkout" / name
        other.mkdir(parents=True, exist_ok=True)
        (other / "SKILL.md").write_text("different checkout\n", encoding="utf-8")
        link.symlink_to(other)
    else:
        raise AssertionError(f"unknown state: {state}")


def _run(repo, claude, hook, hermetic_env, *, agents=None, agy=None, extra_env=None):
    argv = [sys.executable, str(SCRIPT), "--skills-link", str(claude / "h-mad"),
            "--hook-link", str(hook), "--repo", str(repo)]
    if agents is not None:
        argv += ["--agents-skills-dir", str(agents)]
    if agy is not None:
        argv += ["--agy-skills-dir", str(agy)]
    return subprocess.run(argv, capture_output=True, text=True,
                          env=hermetic_env(**(extra_env or {})), timeout=60.0)


def _lines(proc):
    return proc.stdout.splitlines()


@pytest.mark.parametrize("state", ["correct", "copy", "dangling", "other-checkout", "absent"])
def test_agents_root(tmp_path, hermetic_env, state):
    repo, claude, hook = _install(tmp_path)
    agents = tmp_path / "agents-skills"
    _state(agents, repo, "handoff", "correct")
    _state(agents, repo, "h-mad", state)
    proc = _run(repo, claude, hook, hermetic_env, agents=agents,
                agy=tmp_path / "absent-agy")
    kinds = {"copy": "NOT_SYMLINK", "dangling": "DANGLING",
             "other-checkout": "WRONG_CHECKOUT"}
    if state in kinds:
        assert f"SIBLING_{kinds[state]}:{agents / 'h-mad'} " in proc.stdout
        assert _lines(proc)[:1] == ["INSTALL: FAIL issues=1"]
    else:
        assert _lines(proc) == ["INSTALL: PASS", "OK"]
    assert f"SIBLING_NOT_SYMLINK:{agents / 'handoff'}" not in proc.stdout
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("root", ["agents", "agy"])
def test_empty_root_option_is_unreadable(tmp_path, hermetic_env, root):
    repo, claude, hook = _install(tmp_path)
    agents = "" if root == "agents" else tmp_path / "absent-agents"
    agy = "" if root == "agy" else tmp_path / "absent-agy"
    proc = _run(repo, claude, hook, hermetic_env, agents=agents, agy=agy)
    assert _lines(proc)[:1] == ["INSTALL: UNREADABLE"]
    assert proc.returncode == 2


@pytest.mark.parametrize("root", ["agents", "agy"])
def test_empty_env_override_is_unreadable(tmp_path, hermetic_env, root):
    repo, claude, hook = _install(tmp_path)
    key = "HMAD_AGENTS_SKILLS_DIR" if root == "agents" else "HMAD_AGY_SKILLS_DIR"
    proc = _run(repo, claude, hook, hermetic_env, extra_env={key: ""})
    assert _lines(proc)[:1] == ["INSTALL: UNREADABLE"]
    assert proc.returncode == 2


@pytest.mark.parametrize("root", ["agents", "agy"])
def test_explicit_option_beats_env_override(tmp_path, hermetic_env, root):
    repo, claude, hook = _install(tmp_path)
    option_root = tmp_path / "option-root"
    env_root = tmp_path / "env-root"
    _state(option_root, repo, "h-mad", "copy")
    _state(env_root, repo, "h-mad", "correct")
    key = "HMAD_AGENTS_SKILLS_DIR" if root == "agents" else "HMAD_AGY_SKILLS_DIR"
    proc = _run(repo, claude, hook, hermetic_env,
                agents=option_root if root == "agents" else tmp_path / "absent-agents",
                agy=option_root if root == "agy" else tmp_path / "absent-agy",
                extra_env={key: str(env_root)})
    assert f"SIBLING_NOT_SYMLINK:{option_root / 'h-mad'} " in proc.stdout
    assert str(env_root / "h-mad") not in proc.stdout
    assert _lines(proc)[:1] == ["INSTALL: FAIL issues=1"]


@pytest.mark.parametrize("case,name,state,kind,detail", [
    pytest.param("h-mad-correct", "h-mad", "correct", None, False, id="h-mad-correct"),
    pytest.param("h-mad-copy", "h-mad", "copy", "NOT_SYMLINK", False, id="h-mad-copy"),
    pytest.param("h-mad-dangling", "h-mad", "dangling", "DANGLING", False, id="h-mad-dangling"),
    pytest.param("h-mad-other-checkout", "h-mad", "other-checkout", "WRONG_CHECKOUT", False,
                 id="h-mad-other-checkout"),
    pytest.param("handoff-copy", "handoff", "copy", "NOT_SYMLINK", False, id="handoff-copy"),
    pytest.param("handoff-dangling", "handoff", "dangling", "DANGLING", False,
                 id="handoff-dangling"),
    pytest.param("handoff-other-checkout", "handoff", "other-checkout", "WRONG_CHECKOUT", False,
                 id="handoff-other-checkout"),
    pytest.param("both-absent", None, "absent", None, False, id="both-absent"),
    pytest.param("debugger-copy", "debugger", "copy", "NOT_SYMLINK", True,
                 id="debugger-copy"),
    pytest.param("debugger-dangling", "debugger", "dangling", "DANGLING", True,
                 id="debugger-dangling"),
    pytest.param("debugger-other-checkout", "debugger", "other-checkout", "WRONG_CHECKOUT", True,
                 id="debugger-other-checkout"),
    pytest.param("h-mad-copy-plus-debugger-copy", "h-mad", "copy", "NOT_SYMLINK", False,
                 id="h-mad-copy-plus-debugger-copy"),
])
def test_agy_root_cell(tmp_path, hermetic_env, case, name, state, kind, detail):
    repo, claude, hook = _install(tmp_path)
    agy = tmp_path / "agy-skills"
    if name is not None:
        _state(agy, repo, name, state)
    if case == "h-mad-copy-plus-debugger-copy":
        _state(agy, repo, "debugger", "copy")
    proc = _run(repo, claude, hook, hermetic_env,
                agents=tmp_path / "absent-agents", agy=agy)
    lines = _lines(proc)
    if case == "h-mad-copy-plus-debugger-copy":
        assert lines[:1] == ["INSTALL: FAIL issues=1"]
        assert sum(line.startswith("SIBLING_") for line in lines) == 1
        assert f"SIBLING_NOT_SYMLINK:{agy / 'h-mad'} " in proc.stdout
        assert lines[-1] == f"AGY_SIBLING_COLLISION:{agy / 'debugger'} kind=NOT_SYMLINK"
    elif detail:
        assert lines == ["INSTALL: PASS", "OK",
                         f"AGY_SIBLING_COLLISION:{agy / name} kind={kind}"]
        assert not any(line.startswith("SIBLING_") for line in lines)
    elif kind is not None:
        assert lines[:1] == ["INSTALL: FAIL issues=1"]
        assert f"SIBLING_{kind}:{agy / name} " in proc.stdout
        assert not any(line.startswith("AGY_SIBLING_COLLISION:") for line in lines)
    else:
        assert lines == ["INSTALL: PASS", "OK"]
    assert proc.returncode == 0, proc.stderr


def test_claude_root_debugger_copy_still_fails(tmp_path, hermetic_env):
    repo, claude, hook = _install(tmp_path)
    _state(claude, repo, "debugger", "copy")
    proc = _run(repo, claude, hook, hermetic_env,
                agents=tmp_path / "absent-agents", agy=tmp_path / "absent-agy")
    assert f"SIBLING_NOT_SYMLINK:{claude / 'debugger'} " in proc.stdout
    assert _lines(proc)[:1] == ["INSTALL: FAIL issues=1"]
    assert "AGY_SIBLING_COLLISION:" not in proc.stdout


def test_absent_roots_add_no_line(tmp_path, hermetic_env):
    repo, claude, hook = _install(tmp_path)
    agents = tmp_path / "absent-agents"
    agy = tmp_path / "absent-agy"
    proc = _run(repo, claude, hook, hermetic_env, agents=agents, agy=agy)
    assert _lines(proc) == ["INSTALL: PASS", "OK"]
    assert str(agents) not in proc.stdout and str(agy) not in proc.stdout


@pytest.mark.parametrize("root", ["agents", "agy"])
def test_env_override_is_read(tmp_path, hermetic_env, root):
    repo, claude, hook = _install(tmp_path)
    env_root = tmp_path / "env-root"
    _state(env_root, repo, "h-mad", "copy")
    key = "HMAD_AGENTS_SKILLS_DIR" if root == "agents" else "HMAD_AGY_SKILLS_DIR"
    proc = _run(repo, claude, hook, hermetic_env, extra_env={key: str(env_root)})
    assert f"SIBLING_NOT_SYMLINK:{env_root / 'h-mad'} " in proc.stdout
    assert _lines(proc)[:1] == ["INSTALL: FAIL issues=1"]


def test_default_roots_resolve_to_documented_paths():
    assert ic.default_host_roots({}) == (
        str(Path.home() / ".agents" / "skills"),
        str(Path.home() / ".gemini" / "config" / "skills"),
    )


def test_detail_lines_sorted_and_after_verdict(tmp_path, hermetic_env):
    repo, claude, hook = _install(tmp_path, ("h-mad", "handoff", "debugger", "zeta"))
    agy = tmp_path / "agy-skills"
    _state(agy, repo, "zeta", "copy")
    _state(agy, repo, "debugger", "copy")
    proc = _run(repo, claude, hook, hermetic_env,
                agents=tmp_path / "absent-agents", agy=agy)
    assert _lines(proc) == [
        "INSTALL: PASS", "OK",
        f"AGY_SIBLING_COLLISION:{agy / 'debugger'} kind=NOT_SYMLINK",
        f"AGY_SIBLING_COLLISION:{agy / 'zeta'} kind=NOT_SYMLINK",
    ]


def test_check_without_root_keywords_reads_no_new_root(tmp_path, monkeypatch):
    repo, claude, hook = _install(tmp_path)
    agents = tmp_path / "agents-skills"
    agy = tmp_path / "agy-skills"
    _state(agents, repo, "h-mad", "copy")
    _state(agy, repo, "h-mad", "copy")
    monkeypatch.setenv("HMAD_AGENTS_SKILLS_DIR", str(agents))
    monkeypatch.setenv("HMAD_AGY_SKILLS_DIR", str(agy))
    assert ic.check(claude / "h-mad", hook, repo) == []


def test_unattributable_sibling_line_stays_an_issue():
    line = "SIBLING_NOT_SYMLINK:/elsewhere/x (expected -> /y)"
    issues, details = ic.split_agy_root([line], Path("/agy"), ["h-mad"],
                                         ("h-mad", "handoff"))
    assert issues == [line]
    assert details == []


def test_checkout_names_agree_with_check_siblings(tmp_path):
    repo = _checkout(tmp_path, ("h-mad", "handoff", "debugger"))
    root = tmp_path / "copies"
    for name in ("h-mad", "handoff", "debugger"):
        _state(root, repo, name, "copy")
    issue_names = {line.split(":", 1)[1].split(" ", 1)[0].rsplit("/", 1)[1]
                   for line in ic.check_siblings(repo, root)}
    assert issue_names == set(ic.checkout_skill_names(repo))


def test_split_prefix_does_not_capture_a_longer_name(tmp_path, hermetic_env):
    repo, claude, hook = _install(tmp_path, ("h-mad", "handoff", "h-mad-x"))
    agy = tmp_path / "agy-skills"
    _state(agy, repo, "h-mad-x", "copy")
    proc = _run(repo, claude, hook, hermetic_env,
                agents=tmp_path / "absent-agents", agy=agy)
    assert _lines(proc) == ["INSTALL: PASS", "OK",
                            f"AGY_SIBLING_COLLISION:{agy / 'h-mad-x'} kind=NOT_SYMLINK"]
