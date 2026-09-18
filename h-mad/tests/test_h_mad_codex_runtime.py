import json
import os
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _frontmatter() -> dict:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, raw, _ = text.split("---", 2)
    return yaml.safe_load(raw)


def test_frontmatter_is_valid_for_codex_skill_discovery():
    metadata = _frontmatter()
    assert metadata["name"] == "h-mad"
    assert "<" not in metadata["description"]
    assert ">" not in metadata["description"]


def test_entrypoint_routes_codex_to_native_runtime_adapter():
    entrypoint = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    adapter = (ROOT / "references" / "codex-runtime.md").read_text(encoding="utf-8")

    assert "references/codex-runtime.md" in entrypoint
    for phase in range(1, 8):
        assert f"Phase {phase}" in adapter
    for token in (
        "collaboration.spawn_agent",
        "fork_turns",
        "two independent",
        "RED",
        "GREEN",
        "90%",
        "100%",
        "HMAD_SKILL_ROOT",
    ):
        assert token in adapter
    for token in ("Agent(subagent_type:", "AskUserQuestion", "TodoWrite"):
        assert token not in adapter


def test_codex_tdd_hook_is_shipped_as_a_separate_host_adapter():
    hook = ROOT / "hooks" / "h-mad-codex-tdd-gate.py"
    assert hook.is_file()
    text = hook.read_text(encoding="utf-8")
    assert "apply_patch" in text
    assert "exec_command" in text
    assert "permissionDecision" in text
    assert ".agy" not in text


def test_codex_adapter_states_pytest_trust_boundary():
    adapter = (ROOT / "references" / "codex-runtime.md").read_text(encoding="utf-8")
    assert "workflow guard, not an OS security sandbox" in adapter
    assert "malicious test can mutate the worktree" in adapter
    assert "production paths mounted read-only" in adapter


def _active_project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / ".bkit-memory.json").write_text(
        json.dumps({"orchestrator_state": {"feature": {"phase": "step5"}}}),
        encoding="utf-8",
    )
    return tmp_path


def _run_hook(project: Path, payload: dict) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CODEX_PROJECT_DIR"] = str(project)
    return subprocess.run(
        [sys.executable, str(ROOT / "hooks" / "h-mad-codex-tdd-gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=project,
        env=env,
        check=False,
    )


def test_codex_hook_denies_apply_patch_without_a_red_test(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    })
    output = json.loads(result.stdout)
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "failing test" in decision["permissionDecisionReason"].lower()


def test_codex_hook_accepts_canonical_apply_patch_command_field(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "apply_patch",
        "tool_input": {"command": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    })
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_codex_hook_gates_apply_patch_move_destination(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "apply_patch",
        "tool_input": {
            "patch": (
                "*** Update File: tests/test_seed.py\n"
                "*** Move to: hematology-paper-writer/tools/production.py\n"
            )
        },
    })
    output = json.loads(result.stdout)
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "failing test" in decision["permissionDecisionReason"].lower()


def test_codex_hook_allows_apply_patch_when_derived_test_is_red(tmp_path):
    project = _active_project(tmp_path)
    prod = project / "hematology-paper-writer" / "tools" / "widget.py"
    test = project / "hematology-paper-writer" / "tests" / "test_widget.py"
    prod.parent.mkdir(parents=True)
    test.parent.mkdir(parents=True)
    prod.write_text("VALUE = 1\n", encoding="utf-8")
    test.write_text("def test_red():\n    assert False\n", encoding="utf-8")

    result = _run_hook(project, {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    })
    assert result.returncode == 0
    assert result.stdout.strip() in ("", "{}")


def test_codex_hook_denies_opaque_shell_mutation_during_phase5(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "Bash",
        "tool_input": {"cmd": "sed -i '' s/old/new/ hematology-paper-writer/tools/widget.py"},
    })
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "apply_patch" in output["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_hook_denies_interpreter_based_shell_write(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "Bash",
        "tool_input": {"command": "python3 -c \"open('widget.py','w').write('x')\""},
    })
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_codex_hook_allows_explicit_test_command(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "Bash",
        "tool_input": {"command": "python3.11 -m pytest -q tests/test_widget.py"},
    })
    assert result.returncode == 0
    assert result.stdout.strip() in ("", "{}")


def test_codex_hook_allows_trusted_simple_read_command(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "Bash",
        "tool_input": {"command": "ls -la"},
    })
    assert result.returncode == 0
    assert result.stdout.strip() in ("", "{}")


def test_codex_hook_allows_exact_safe_hmad_control_script(tmp_path):
    project = _active_project(tmp_path)
    script = ROOT / "scripts" / "h_mad_state_validate.py"
    result = _run_hook(project, {
        "tool_name": "Bash",
        "tool_input": {"command": f"python3 {script} docs/.bkit-memory.json"},
    })
    assert result.returncode == 0
    assert result.stdout.strip() in ("", "{}")


def test_codex_hook_allows_observational_hmad_dispatch_verb(tmp_path):
    project = _active_project(tmp_path)
    dispatch = ROOT / "bin" / "hmad-dispatch"
    result = _run_hook(project, {
        "tool_name": "Bash",
        "tool_input": {"command": f"{dispatch} env"},
    })
    assert result.returncode == 0
    assert result.stdout.strip() in ("", "{}")


def test_codex_hook_rejects_untrusted_executable_paths(tmp_path):
    project = _active_project(tmp_path)
    for command in (
        "/tmp/git status",
        "./hmad-dispatch",
        "python3 /tmp/h_mad_evil.py",
        "PATH=/tmp git status",
        "git status & /tmp/evil",
        "git status $(/tmp/evil)",
        "git status `/tmp/evil`",
        "git status =(/tmp/evil)",
        "git status *(e:'/tmp/evil':)",
        "git status ${PATH}",
        "rg --pre=/tmp/evil needle .",
        "rg --hostname-bin=/tmp/evil needle .",
        "git diff --ext-diff",
        "git show --textconv HEAD:file",
        "git status",
    ):
        result = _run_hook(project, {
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny", command


def test_codex_hook_rejects_privileged_hmad_scripts_and_dispatch_verbs(tmp_path):
    project = _active_project(tmp_path)
    scripts = ROOT / "scripts"
    dispatch = ROOT / "bin" / "hmad-dispatch"
    for command in (
        f"python3 {scripts / 'h_mad_doc_block_exec.py'} docs/spec.md",
        f"python3 {scripts / 'h_mad_phase7_integrate.py'} --apply",
        f"python3 {scripts / 'h_mad_mutation_harness.py'} tests/mutation-specs/x.json",
        f"python3 {scripts / 'h_mad_response_probe.py'} --help",
        f"python3 {scripts / 'h_mad_state_write.py'} /tmp/.bkit-memory.json --feature x --set phase=null",
        f"python3 {scripts / 'h_mad_assemble_tdd.py'} --out hematology-paper-writer/tools/escape.py",
        f"python3 {scripts / 'h_mad_wire_registry.py'} verify --python /tmp/evil",
        f"{dispatch} run --timeout 1 -- /tmp/evil",
        f"{dispatch} worktree-rm escape",
        f"{dispatch} exec agy docs/prompt.md --cd .",
        f"{dispatch} send agy docs/prompt.md",
        f"{dispatch} ask agy docs/prompt.md",
        f"{dispatch} dispatch agy docs/prompt.md",
        f"{dispatch} launch agy",
        f"{dispatch} audit-cycle --feature escape --phase impl-plan",
        f"{dispatch} task-create escape",
    ):
        result = _run_hook(project, {
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny", command


def test_codex_hook_rejects_mutating_variants_of_read_commands(tmp_path):
    project = _active_project(tmp_path)
    for command in ("git branch -D feature/x", "find . -fprint /tmp/escape"):
        result = _run_hook(project, {
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny", command


def test_codex_hook_scopes_nested_state_to_the_target_project(tmp_path):
    root = tmp_path
    nested = root / "nested"
    sibling = root / "sibling"
    _active_project(nested)
    (nested / "hematology-paper-writer" / "tools").mkdir(parents=True)
    (sibling / "hematology-paper-writer" / "tools").mkdir(parents=True)

    nested_result = _run_hook(root, {
        "tool_name": "apply_patch",
        "tool_input": {
            "patch": "*** Update File: nested/hematology-paper-writer/tools/widget.py\n"
        },
    })
    assert json.loads(nested_result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

    sibling_result = _run_hook(root, {
        "tool_name": "apply_patch",
        "tool_input": {
            "patch": "*** Update File: sibling/hematology-paper-writer/tools/widget.py\n"
        },
    })
    assert sibling_result.stdout.strip() in ("", "{}")


def test_codex_hook_rejects_pytest_no_tests_collected_as_red(tmp_path):
    project = _active_project(tmp_path)
    prod = project / "hematology-paper-writer" / "tools" / "widget.py"
    test = project / "hematology-paper-writer" / "tests" / "test_widget.py"
    prod.parent.mkdir(parents=True)
    test.parent.mkdir(parents=True)
    prod.write_text("VALUE = 1\n", encoding="utf-8")
    test.write_text("# no tests collected\n", encoding="utf-8")

    result = _run_hook(project, {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    })
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "exit 1" in output["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_hook_self_check_reports_machine_readable_pass():
    result = subprocess.run(
        [sys.executable, str(ROOT / "hooks" / "h-mad-codex-tdd-gate.py"), "--self-check"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "CODEX-TDD-GATE: PASS"


def test_codex_hook_resolves_git_root_from_nested_cwd(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _active_project(tmp_path)
    nested = tmp_path / "nested"
    nested.mkdir()
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    }
    env = os.environ.copy()
    env.pop("CODEX_PROJECT_DIR", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "hooks" / "h-mad-codex-tdd-gate.py")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=nested,
        env=env,
        check=False,
    )
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_codex_hook_rejects_unparseable_write_when_phase5_is_active(tmp_path):
    project = _active_project(tmp_path)
    result = _run_hook(project, {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "not a valid apply_patch payload"},
    })
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "identify" in output["hookSpecificOutput"]["permissionDecisionReason"]


def test_codex_hook_fails_closed_on_malformed_state(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / ".bkit-memory.json").write_text("{not-json", encoding="utf-8")
    result = _run_hook(tmp_path, {
        "tool_name": "apply_patch",
        "tool_input": {"command": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    })
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "state" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()


def test_codex_hook_is_noop_outside_phase5(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / ".bkit-memory.json").write_text(
        json.dumps({"orchestrator_state": {"feature": {"phase": None}}}),
        encoding="utf-8",
    )
    result = _run_hook(tmp_path, {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "*** Update File: hematology-paper-writer/tools/widget.py\n"},
    })
    assert result.returncode == 0
    assert result.stdout.strip() in ("", "{}")
