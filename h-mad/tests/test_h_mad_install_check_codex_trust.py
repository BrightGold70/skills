"""The install check could not see that codex would skip the h-mad gate.

Codex (0.166/0.167) runs a project hook only when its config holds a trust
record for it — `[hooks.state."<abs hooks.json>:<event_snake>:<group>:<hook>"]`
— or when `--dangerously-bypass-hook-trust` is passed. `hmad-dispatch exec
codex` now passes the flag (`_codex_hook_trust_arg`, 09c36baf/1d92ef9c); a codex
started by hand gets neither, and the Phase-5 gate silently does not run.
`h_mad_install_check.py` reported Claude and agy wiring and said nothing.

These tests pin an ADVISORY, not a verdict: one detail line per h-mad gate
entry, outcomes kept distinct, and the `INSTALL:` summary untouched. Shapes
measured 2026-11-08 on Hawui-Macmini: the record key for HemaSuite's gate was
`…/HemaSuite/.codex/hooks.json:pre_tool_use:0:0`, and it carried `trusted_hash`
with NO `enabled` key — so an absent `enabled` must not read as disabled. What
`trusted_hash` hashes is unknown, so a present record is never reported as
"enforced" — only as recorded, hash not verified.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_install_check.py"
DISPATCH = SCRIPTS / "hmad-dispatch.sh"
sys.path.insert(0, str(SCRIPTS))

GATE = "python3 $HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py"
HASH = "sha256:" + "0" * 64


def _hooks(repo: Path, commands_by_event: dict[str, list[list[str]]]) -> Path:
    """Write `<repo>/.codex/hooks.json`: event -> groups -> hook commands."""
    path = repo / ".codex" / "hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"hooks": {
        event: [{"matcher": "apply_patch|Bash",
                 "hooks": [{"type": "command", "command": c} for c in group]}
                for group in groups]
        for event, groups in commands_by_event.items()}}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _gate_hooks(repo: Path) -> Path:
    return _hooks(repo, {"PreToolUse": [[GATE]]})


def _key(hooks: Path, event: str = "pre_tool_use", g: int = 0, h: int = 0) -> str:
    return f"{hooks.resolve()}:{event}:{g}:{h}"


def _config(home: Path, records: dict[str, dict[str, object]] | None = None,
            raw: str | None = None) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    path = home / "config.toml"
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
        return path
    lines = ['model = "x"', "", "[hooks.state]", ""]
    for key, fields in (records or {}).items():
        lines.append(f'[hooks.state."{key}"]')
        for name, value in fields.items():
            rendered = ("true" if value is True else "false" if value is False
                        else json.dumps(value))
            lines.append(f"{name} = {rendered}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _check(hooks_files, config):
    import h_mad_install_check as mod
    return mod.check_codex_hook_trust(list(hooks_files), config)


def _only(lines, prefix):
    hits = [line for line in lines if line.startswith(prefix)]
    assert len(hits) == 1, f"expected exactly one {prefix!r} line, got {lines!r}"
    return hits[0]


# --- outcomes ---------------------------------------------------------------

def test_no_trust_record_reports_untrusted_with_the_key_it_looked_for(tmp_path):
    hooks = _gate_hooks(tmp_path / "repo")
    config = _config(tmp_path / "codex-home")
    lines = _check([hooks], config)
    line = _only(lines, "CODEX_HOOK_UNTRUSTED:")
    assert _key(hooks) in line
    assert "--dangerously-bypass-hook-trust" in line
    assert str(config) in line, "the line must name the config it read"
    assert not any(l.startswith("CODEX_HOOK_TRUST_RECORDED:") for l in lines)


def test_record_present_and_enabled_reports_recorded_hash_not_verified(tmp_path):
    hooks = _gate_hooks(tmp_path / "repo")
    config = _config(tmp_path / "codex-home",
                     {_key(hooks): {"enabled": True, "trusted_hash": HASH}})
    line = _only(_check([hooks], config), "CODEX_HOOK_TRUST_RECORDED:")
    assert _key(hooks) in line
    assert "hash not verified" in line
    assert "enforced" not in line.lower()


def test_record_without_enabled_key_is_recorded_not_disabled(tmp_path):
    """Measured shape: HemaSuite's record carries trusted_hash and no `enabled`."""
    hooks = _gate_hooks(tmp_path / "repo")
    config = _config(tmp_path / "codex-home", {_key(hooks): {"trusted_hash": HASH}})
    lines = _check([hooks], config)
    _only(lines, "CODEX_HOOK_TRUST_RECORDED:")
    assert not any(l.startswith("CODEX_HOOK_DISABLED:") for l in lines)


def test_record_explicitly_disabled_reports_disabled(tmp_path):
    hooks = _gate_hooks(tmp_path / "repo")
    config = _config(tmp_path / "codex-home",
                     {_key(hooks): {"enabled": False, "trusted_hash": HASH}})
    lines = _check([hooks], config)
    assert _key(hooks) in _only(lines, "CODEX_HOOK_DISABLED:")
    assert not any(l.startswith("CODEX_HOOK_TRUST_RECORDED:") for l in lines)


def test_a_record_for_another_path_does_not_count(tmp_path):
    """Trust is keyed by ABSOLUTE path: every worktree is a new, untrusted path."""
    hooks = _gate_hooks(tmp_path / "worktree")
    other = tmp_path / "main" / ".codex" / "hooks.json"
    config = _config(tmp_path / "codex-home",
                     {_key(other): {"enabled": True, "trusted_hash": HASH}})
    _only(_check([hooks], config), "CODEX_HOOK_UNTRUSTED:")


def test_the_gate_is_keyed_at_its_own_group_and_hook_index(tmp_path):
    hooks = _hooks(tmp_path / "repo", {"PreToolUse": [["echo other"], ["true", GATE]]})
    trusted_wrong = _config(tmp_path / "a",
                            {_key(hooks, g=0, h=0): {"enabled": True, "trusted_hash": HASH}})
    _only(_check([hooks], trusted_wrong), "CODEX_HOOK_UNTRUSTED:")
    trusted_right = _config(tmp_path / "b",
                            {_key(hooks, g=1, h=1): {"enabled": True, "trusted_hash": HASH}})
    assert _key(hooks, g=1, h=1) in _only(_check([hooks], trusted_right),
                                           "CODEX_HOOK_TRUST_RECORDED:")


# --- silence: not codex-wired, or not our hook --------------------------------

def test_no_codex_hooks_file_is_silent(tmp_path):
    config = _config(tmp_path / "codex-home")
    assert _check([tmp_path / "repo" / ".codex" / "hooks.json"], config) == []


def test_hooks_without_the_h_mad_gate_are_silent(tmp_path):
    hooks = _hooks(tmp_path / "repo", {"PreToolUse": [["echo mine"]],
                                       "Stop": [["echo bye"]]})
    assert _check([hooks], _config(tmp_path / "codex-home")) == []


# --- could-not-check is never "trusted" ---------------------------------------

@pytest.mark.parametrize("case", ["config-missing", "config-unparseable",
                                  "hooks-unparseable", "hooks-wrong-shape"])
def test_unreadable_inputs_report_unknown_never_recorded(tmp_path, case):
    repo = tmp_path / "repo"
    hooks = _gate_hooks(repo)
    config = _config(tmp_path / "codex-home",
                     {_key(hooks): {"enabled": True, "trusted_hash": HASH}})
    if case == "config-missing":
        config.unlink()
    elif case == "config-unparseable":
        config.write_text("[hooks.state\nnot toml = = =\n", encoding="utf-8")
    elif case == "hooks-unparseable":
        hooks.write_text("{not json", encoding="utf-8")
    elif case == "hooks-wrong-shape":
        hooks.write_text(json.dumps({"hooks": ["not", "a", "mapping"]}), encoding="utf-8")
    lines = _check([hooks], config)
    line = _only(lines, "CODEX_HOOK_TRUST_UNKNOWN:")
    assert "reason=" in line
    assert not any(l.startswith(("CODEX_HOOK_TRUST_RECORDED:", "CODEX_HOOK_UNTRUSTED:"))
                   for l in lines), "could-not-check must take neither verdict"


# --- the gate string has one meaning ------------------------------------------

def test_gate_command_matches_hmad_dispatch():
    """A second copy of the gate string: pinned equal so the two cannot drift."""
    import h_mad_install_check as mod
    shell = re.search(r'^GATE = "([^"]+)"$', DISPATCH.read_text(encoding="utf-8"), re.M)
    assert shell, "hmad-dispatch.sh no longer defines GATE"
    assert mod.CODEX_GATE_COMMAND == shell.group(1) == GATE


# --- through main(): advisory rides detail lines, verdict unchanged -----------

def _main(tmp_path, hermetic_env, config, hooks, *, extra_env=None, pass_config=True,
          pass_hooks=True):
    claude = tmp_path / "claude"
    (claude / "skills").mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, str(SCRIPT),
            "--skills-link", str(claude / "skills" / "h-mad"),
            "--hook-link", str(claude / "hooks" / "h-mad-tdd-gate.sh")]
    if pass_hooks:
        argv += ["--codex-hooks-json", str(hooks)]
    if pass_config:
        argv += ["--codex-config", str(config)]
    return subprocess.run(argv, capture_output=True, text=True, cwd=tmp_path,
                          env=hermetic_env(**(extra_env or {})), timeout=60.0)


def test_main_prints_the_advisory_and_leaves_the_summary_and_issue_count(tmp_path, hermetic_env):
    hooks = _gate_hooks(tmp_path / "repo")
    untrusted = _config(tmp_path / "home-a")
    trusted = _config(tmp_path / "home-b",
                      {_key(hooks): {"enabled": True, "trusted_hash": HASH}})
    a = _main(tmp_path, hermetic_env, untrusted, hooks)
    b = _main(tmp_path, hermetic_env, trusted, hooks)
    assert a.returncode == b.returncode == 0, (a.stderr, b.stderr)
    first_a, first_b = a.stdout.splitlines()[0], b.stdout.splitlines()[0]
    assert first_a.startswith("INSTALL: ")
    assert first_a == first_b, "an advisory must not change the INSTALL: summary or issues="
    assert any(l.startswith("CODEX_HOOK_UNTRUSTED:") for l in a.stdout.splitlines())
    assert any(l.startswith("CODEX_HOOK_TRUST_RECORDED:") for l in b.stdout.splitlines())


def test_main_defaults_the_config_to_codex_home(tmp_path, hermetic_env):
    """The live home on an Orca host is CODEX_HOME, not ~/.codex (measured 2026-11-08)."""
    hooks = _gate_hooks(tmp_path / "repo")
    home = tmp_path / "orca-codex-home"
    config = _config(home)
    proc = _main(tmp_path, hermetic_env, config, hooks, pass_config=False,
                 extra_env={"CODEX_HOME": str(home)})
    assert proc.returncode == 0, proc.stderr
    line = _only(proc.stdout.splitlines(), "CODEX_HOOK_UNTRUSTED:")
    assert str(config) in line


def test_main_reads_the_default_hooks_json_from_the_env_override(tmp_path, hermetic_env):
    """`HMAD_CODEX_HOOKS_JSON` replaces the git-toplevel default, the way
    `HMAD_AGENTS_SKILLS_DIR` replaces a host root: the suite runs from inside this
    repo, whose real `.codex/hooks.json` carries the gate, and a test that read it
    would print an advisory into every other test's exact output."""
    hooks = _gate_hooks(tmp_path / "repo")
    config = _config(tmp_path / "codex-home")
    proc = _main(tmp_path, hermetic_env, config, hooks, pass_hooks=False,
                 extra_env={"HMAD_CODEX_HOOKS_JSON": str(hooks)})
    assert proc.returncode == 0, proc.stderr
    assert _key(hooks) in _only(proc.stdout.splitlines(), "CODEX_HOOK_UNTRUSTED:")
