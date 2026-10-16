"""FR-4 Task 5: agy gate contract, activity, and classes (a) and (d)."""
from __future__ import annotations

import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from tdd_gate_support import hermetic_env, write_state


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "h-mad/hooks/h-mad-agy-tdd-gate.py"
SCRIPTS = ROOT / "h-mad/scripts"
INVENTORY = ROOT / "docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log"
CLASS_A = frozenset({
    "view_file", "list_dir", "grep_search", "find_by_name", "command_status",
    "read_url_content", "search_web", "ask_question", "finish", "wait", "wait_5_seconds",
})
CLASS_B = frozenset({
    "write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit",
})
GATE_KINDS = frozenset({
    "judge-error", "tool-not-admitted", "target-outside-root", "allowance-file-write", "shell-not-admitted",
})
HOSTILE = 'agent "q"\\\n## [H-MAD:MARKER] *?[] Ω\nkind=forged'


@pytest.fixture(autouse=True)
def hostile_stub_input(monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    monkeypatch.syspath_prepend(str(SCRIPTS))


def _env():
    env = hermetic_env(HMAD_STUB_HOSTILE="all", PYTHONPATH="", PYTHONNOUSERSITE="1")
    # A dispatched worker can inherit git's worktree overrides. Fixtures must
    # discover their own repositories, including the deliberately missing one.
    for name in tuple(env):
        if name.startswith("GIT_"):
            env.pop(name)
    return env


def _root(tmp_path: Path, status: str) -> Path:
    root = tmp_path / "repo Ω [*] 'q'"
    root.mkdir()
    process = subprocess.run(
        ["git", "init", "--quiet", str(root)], env=_env(),
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert process.returncode == 0, f"git fixture could not initialise: {process.stderr}"
    (root / ".agents").mkdir()
    if status == "unknown":
        state = root / "docs/.bkit-memory.json"
        state.parent.mkdir()
        state.write_text(HOSTILE, encoding="utf-8")
    else:
        assert status in {"active", "inactive"}
        write_state(root, {HOSTILE: {"phase": "step5" if status == "active" else "step4"}})
    return root.resolve()


def _payload(name="call_mcp_tool", **extra):
    return {"toolCall": {"name": name, "args": {"message": HOSTILE}}, **extra}


def _load_gate(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("agy_gate_task5_test", GATE)
    assert spec and spec.loader, "the agy gate must be loadable by its production path"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _one_decision(stdout: str, rc: int, *, stderr: str = "") -> dict:
    assert rc == 0, f"gate must exit 0 and emit one JSON object; rc={rc}, stderr={stderr!r}"
    try:
        decision = json.loads(stdout)
    except ValueError as exc:
        raise AssertionError(f"gate must print exactly one JSON object; stdout={stdout!r}") from exc
    assert isinstance(decision, dict), f"gate output must be one JSON object: {decision!r}"
    assert decision.get("decision") in {"allow", "deny"}, f"invalid gate decision: {decision!r}"
    if decision["decision"] == "allow":
        assert decision == {"decision": "allow"}, "allow must use the FR-4 payload contract"
    else:
        assert set(decision) == {"decision", "reason"}, "deny must use the FR-4 payload contract"
        reason = decision["reason"]
        assert isinstance(reason, str), "every deny must carry a string reason"
        assert reason.count("kind=") == 1, f"every deny must carry exactly one kind= token: {reason!r}"
        tokens = re.findall(r"kind=([^\s]+)", reason)
        assert len(tokens) == 1, f"every deny must carry exactly one kind= token: {reason!r}"
        assert re.search(r"(?:^|\s)kind=" + re.escape(tokens[0]) + r"\Z", reason), (
            f"the one kind= token must end the deny reason: {reason!r}"
        )
        judge = importlib.import_module("h_mad_tdd_judge")
        assert tokens[0] in GATE_KINDS | judge.KINDS, f"deny kind must be in the closed set: {reason!r}"
    return decision


def _decide(root: Path, payload, cwd: Path | None = None) -> dict:
    process = subprocess.run(
        [sys.executable, str(GATE)], cwd=cwd if cwd is not None else root / ".agents",
        input=payload if isinstance(payload, str) else json.dumps(payload),
        env=_env(), capture_output=True, text=True, timeout=10, check=False,
    )
    return _one_decision(process.stdout, process.returncode, stderr=process.stderr)


def _expect(decision: dict, verdict: str, kind: str | None = None):
    assert decision["decision"] == verdict, f"expected {verdict}, got {decision!r}"
    if kind is not None:
        assert decision["reason"].endswith(f" kind={kind}"), (
            f"deny row must end with kind={kind}: {decision!r}"
        )


@pytest.mark.parametrize("payload", [
    HOSTILE,
    [HOSTILE],
    {"toolCall": [HOSTILE]},
    {"toolCall": {"name": [HOSTILE]}},
], ids=["not-json", "json-array", "toolcall-not-object", "name-not-str"])
def test_every_exit_prints_one_json_object(tmp_path, payload):
    root = _root(tmp_path, "active")
    _expect(_decide(root, payload), "deny", "judge-error")


@pytest.mark.parametrize("name", sorted(CLASS_A), ids=sorted(CLASS_A))
def test_class_a_allowed_before_state_is_read(tmp_path, name):
    outside = tmp_path / "outside Ω [*]"
    outside.mkdir()
    (outside / ".agents").mkdir()
    (outside / "docs").mkdir()
    (outside / "docs/.bkit-memory.json").write_text(HOSTILE, encoding="utf-8")
    _expect(_decide(outside, _payload(name, workspacePaths=["/elsewhere"])), "allow")


@pytest.mark.parametrize("status,name,verdict,kind", [
    ("inactive", "call_mcp_tool", "allow", None),
    ("active", "brand_new_tool", "deny", "tool-not-admitted"),
], ids=["call_mcp_tool-inactive", "unlisted-name-active"])
def test_unknown_tool_is_class_d(tmp_path, status, name, verdict, kind):
    root = _root(tmp_path, status)
    _expect(_decide(root, _payload(name)), verdict, kind)


@pytest.mark.parametrize("status,names_root,verdict,kind", [
    ("unknown", False, "deny", "judge-error"),
    ("inactive", False, "allow", None),
    ("active", True, "deny", "tool-not-admitted"),
], ids=["unknown-denies", "inactive-stands-down", "naming-root-passes"])
def test_workspace_paths_cross_check(tmp_path, status, names_root, verdict, kind):
    root = _root(tmp_path, status)
    paths = [str(root)] if names_root else ["/elsewhere"]
    _expect(_decide(root, _payload(workspacePaths=paths)), verdict, kind)


@pytest.mark.parametrize("row,kind", [
    ("malformed-payload", "judge-error"),
    ("root-unresolvable", "judge-error"),
    ("exception-after-step-2", "judge-error"),
    ("workspace-paths", "judge-error"),
    ("class-d-active", "tool-not-admitted"),
    ("class-d-unknown", "judge-error"),
], ids=["malformed-payload", "root-unresolvable", "exception-after-step-2",
        "workspace-paths", "class-d-active", "class-d-unknown"])
def test_deny_row_kind(tmp_path, monkeypatch, capsys, row, kind):
    root = _root(tmp_path, "unknown" if row == "class-d-unknown" else "active")
    if row == "exception-after-step-2":
        gate = _load_gate(monkeypatch)
        policy = importlib.import_module("h_mad_target_identity")
        visits = []

        def fail_status(resolved_root):
            visits.append(Path(resolved_root))
            assert Path(resolved_root) == root, "activity scan must receive the canonical git root"
            assert Path.cwd() == root, "gate must chdir to the root before reading activity"
            raise RuntimeError(HOSTILE)

        # Patch both the source module and a possible existing binding: imports
        # performed inside main's guarded try must still see the injected fault.
        monkeypatch.setattr(policy, "_any_phase5_status", fail_status)
        monkeypatch.setattr(gate, "_any_phase5_status", fail_status, raising=False)
        monkeypatch.chdir(root / ".agents")
        chdirs = []
        original_chdir = os.chdir

        def record_chdir(path):
            chdirs.append(Path(path))
            original_chdir(path)

        monkeypatch.setattr(os, "chdir", record_chdir)
        monkeypatch.setattr(sys, "argv", [str(GATE)])
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_payload())))
        rc = gate.main()
        captured = capsys.readouterr()
        decision = _one_decision(captured.out, rc, stderr=captured.err)
        assert visits == [root], "main must call the shared activity predicate exactly once"
        assert chdirs == [root], "main must chdir to the canonical git root exactly once"
    elif row == "root-unresolvable":
        outside = tmp_path / "outside"
        outside.mkdir()
        decision = _decide(root, _payload(), cwd=outside)
    elif row == "malformed-payload":
        decision = _decide(root, {"toolCall": HOSTILE})
    elif row == "workspace-paths":
        decision = _decide(root, _payload(workspacePaths=["/elsewhere"]))
    else:
        decision = _decide(root, _payload())
    _expect(decision, "deny", kind)


def test_self_check_passes(tmp_path):
    process = subprocess.run(
        [sys.executable, str(GATE), "--self-check"], cwd=tmp_path,
        env=_env(), capture_output=True, text=True, timeout=30, check=False,
    )
    assert process.stdout == "AGY-TDD-GATE: PASS\n", "all four self-checks must produce exactly the PASS line"
    assert process.returncode == 0, "a successful self-check must exit 0"


def test_self_check_fails_on_a_policy_import_failure(tmp_path):
    copied_gate = tmp_path / "hooks" / GATE.name
    copied_gate.parent.mkdir()
    shutil.copyfile(GATE, copied_gate)
    # Keep the real judge and its dependencies; only identity/policy is absent.
    scripts = tmp_path / "scripts"
    shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("h_mad_target_identity.py", "__pycache__"))
    assert (scripts / "h_mad_tdd_judge.py").is_file(), "import-failure fixture must include the real judge"
    assert not (scripts / "h_mad_target_identity.py").exists()
    process = subprocess.run(
        [sys.executable, "-I", str(copied_gate), "--self-check"], cwd=tmp_path,
        env=_env(), capture_output=True, text=True, timeout=30, check=False,
    )
    assert process.stdout == "AGY-TDD-GATE: FAIL policy-import\n", (
        "missing identity/policy must print exactly the policy-import operational failure line"
    )
    assert process.returncode == 2, "a self-check that could not import policy must exit 2"


def test_classification_table_is_the_recorded_inventory(monkeypatch):
    gate = _load_gate(monkeypatch)
    with INVENTORY.open(encoding="utf-8") as stream:
        first_init = next(event for line in stream if line.strip()
                          if (event := json.loads(line)).get("event") == "init")
    names = first_init["init"]["tools"]
    recorded = set(names)
    assert len(names) == len(recorded) == 58, "the recorded first init must contain 58 distinct tool names"
    assert gate.CLASS_A == CLASS_A, "CLASS_A must contain exactly the 11 FR-4 read-only names"
    assert gate.CLASS_B == CLASS_B, "CLASS_B must contain exactly the five FR-4 path-write names"
    assert isinstance(gate.CLASS_A, frozenset) and isinstance(gate.CLASS_B, frozenset)
    assert gate.PATH_KEYS == {"write_to_file": ("TargetFile",)}, "path keys must stay limited to the observed contract"
    assert gate.GATE_KINDS == GATE_KINDS, "gate deny kinds must match FR-4's five-name closed set"
    assert isinstance(gate.GATE_KINDS, frozenset)
    admitted = CLASS_A | CLASS_B | {"run_command"}
    assert admitted <= recorded, "every class (a), (b), and (c) name must occur in the recorded inventory"
    remainder = recorded - admitted
    assert len(remainder) == 41, "the inventory remainder must contain exactly 41 class-(d) tools"
    for label, members in (("a", CLASS_A), ("b", CLASS_B), ("c", {"run_command"}), ("d", remainder)):
        for name in members:
            assert gate.classify_tool(name) == label, f"{name!r} must be classified as {label}"
    assert gate.classify_tool("brand_new_tool") == "d", "unlisted tools must default to class (d)"
    assert gate.classify_tool("VIEW_FILE") == "d", "tool names must be matched case-sensitively"


@pytest.mark.parametrize("failure", ["classification", "shell-policy"])
def test_self_check_policy_fail_is_a_verdict_with_exit_0(monkeypatch, capsys, failure):
    gate = _load_gate(monkeypatch)
    policy = importlib.import_module("h_mad_target_identity")
    judge = importlib.import_module("h_mad_tdd_judge")
    assert judge.JUDGE_BUDGET_S > 0, "verdict fixture must have a readable judge budget"
    if failure == "classification":
        monkeypatch.setattr(gate, "CLASS_A", gate.CLASS_A - {"view_file"})
    else:
        monkeypatch.setattr(policy, "_safe_shell_command", lambda *args, **kwargs: True)
        monkeypatch.setattr(gate, "_safe_shell_command", lambda *args, **kwargs: True, raising=False)
    monkeypatch.setattr(sys, "argv", [str(GATE), "--self-check"])
    rc = gate.main()
    captured = capsys.readouterr()
    assert captured.out == f"AGY-TDD-GATE: FAIL {failure}\n", (
        f"{failure} self-check must print exactly its FAIL verdict line on stdout"
    )
    assert rc == 0, f"{failure} self-check is a verdict FAIL and must exit 0, never 2"
