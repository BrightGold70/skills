"""FR-4 Tasks 5–6: agy gate contract, activity, and classes (a), (b), and (d)."""
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

from tdd_gate_support import hermetic_env, write_plan, write_state


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


def _root(tmp_path: Path, status: str, *, name="repo Ω [*] 'q'") -> Path:
    root = tmp_path / name
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


def _expect(decision: dict, verdict: str, kind: str | None = None, *, because="gate contract"):
    assert decision["decision"] == verdict, f"{because}: expected {verdict}, got {decision!r}"
    if kind is not None:
        assert decision["reason"].endswith(f" kind={kind}"), (
            f"{because}: deny row must end with kind={kind}: {decision!r}"
        )


def _write_payload(target, **extra):
    payload = _payload("write_to_file", **extra)
    payload["toolCall"]["args"]["TargetFile"] = target
    return payload


def _production_with_test(root: Path, *, relative="src/widget.py", failing=False) -> Path:
    production = root / relative
    production.parent.mkdir(parents=True, exist_ok=True)
    production.write_text(f"message = {HOSTILE!r}\n", encoding="utf-8")
    test = root / "tests/test_subject.py"
    test.parent.mkdir()
    test.write_text(
        f"def test_subject():\n    assert {not failing!r}, {HOSTILE!r}\n", encoding="utf-8",
    )
    measured = subprocess.run(
        [sys.executable, "-m", "pytest", str(test), "-x", "-q", "--no-header"],
        cwd=root, env=_env(), capture_output=True, text=True, timeout=10, check=False,
    )
    summary = "1 failed" if failing else "1 passed"
    assert summary in measured.stdout, (
        f"production fixture must measure {summary}: stdout={measured.stdout!r}, stderr={measured.stderr!r}"
    )
    write_plan(root, HOSTILE, (
        "## Task 1: production write\n"
        f"**Production file**: `{relative}`\n"
        "**Test file**: `tests/test_subject.py`\n\n" + HOSTILE + "\n"
    ))
    return production


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
    ("class-b-no-target", "judge-error"),
    ("t2-unresolvable", "judge-error"),
    ("t2a-directory", "judge-error"),
    ("t4-outside-root", "target-outside-root"),
    ("t5-allowance-file", "allowance-file-write"),
    ("t7-chain-unreadable", "judge-error"),
    ("t7-judge-non-allow", "test-passing"),
], ids=["malformed-payload", "root-unresolvable", "exception-after-step-2",
        "workspace-paths", "class-d-active", "class-d-unknown", "class-b-no-target",
        "t2-unresolvable", "t2a-directory", "t4-outside-root", "t5-allowance-file",
        "t7-chain-unreadable", "t7-judge-non-allow"])
def test_deny_row_kind(tmp_path, monkeypatch, capsys, row, kind):
    root = _root(tmp_path, "unknown" if row == "class-d-unknown" else "active",
                 name="repo Ω *? 'q'" if row == "t7-judge-non-allow" else "repo Ω [*] 'q'")
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
    elif row == "class-b-no-target":
        decision = _decide(root, _payload("write_to_file"))
    elif row == "t2-unresolvable":
        target = root / "dangling Ω [*].py"
        target.symlink_to(root / "absent Ω [*].py")
        identity = importlib.import_module("h_mad_target_identity")
        resolved = identity.canonicalise(str(root), str(target), str(root))
        assert resolved.unresolvable, "T2 fixture must have an unresolvable target identity"
        decision = _decide(root, _write_payload(str(target)))
    elif row == "t2a-directory":
        decision = _decide(root, _write_payload("."))
    elif row == "t4-outside-root":
        decision = _decide(root, _write_payload(str(tmp_path / "outside Ω [*].PY")))
    elif row == "t5-allowance-file":
        decision = _decide(root, _write_payload(".h-mad/phase5-shell-allow"))
    elif row == "t7-chain-unreadable":
        package = root / "package Ω [*]"
        docs = write_state(package, {HOSTILE: {"phase": "step5"}}).parent
        target = package / "worker.py"
        target.write_text(f"message = {HOSTILE!r}\n", encoding="utf-8")
        try:
            docs.chmod(0)
            decision = _decide(root, _write_payload(str(target)))
        finally:
            docs.chmod(0o755)
    elif row == "t7-judge-non-allow":
        target = _production_with_test(root)
        decision = _decide(root, _write_payload(str(target)))
    else:
        decision = _decide(root, _payload())
    _expect(decision, "deny", kind, because=f"FR-4 deny row {row}")


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


@pytest.mark.parametrize("status,args", [
    ("unknown", {}),
    ("inactive", {}),
    ("active", {"TargetFile": ""}),
    ("unknown", {"TargetFile": ""}),
    ("inactive", {"TargetFile": ""}),
    ("active", {"TargetFile": None}),
    ("active", {"TargetFile": 5}),
    ("active", {"TargetFile": ["x"]}),
    ("inactive", {"TargetFile": 5}),
    ("inactive", {"TargetFile": ["x"]}),
], ids=["no-key-unknown", "no-key-inactive", "empty-active", "empty-unknown", "empty-inactive",
        "null-active", "number-active", "list-active", "number-inactive", "list-inactive"])
def test_class_b_no_target(tmp_path, status, args):
    root = _root(tmp_path, status)
    payload = _payload("write_to_file")
    payload["toolCall"]["args"].update(args)
    _expect(
        _decide(root, payload), "allow" if status == "inactive" else "deny",
        None if status == "inactive" else "judge-error",
        because=f"class (b) no non-empty string target under {status}: {args!r}",
    )


@pytest.mark.parametrize("name", [
    "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit",
])
def test_class_b_tools_without_a_recorded_key_deny_under_active(tmp_path, name):
    root = _root(tmp_path, "active")
    payload = _payload(name)
    # Neither another tool's observed key nor plausible unrecorded aliases count.
    payload["toolCall"]["args"].update({
        "TargetFile": "tests/test_subject.py", "file_path": "docs/report.txt", "path": HOSTILE,
    })
    _expect(_decide(root, payload), "deny", "judge-error",
            because=f"class (b) {name} has no recorded path key")


def test_production_py_with_failing_test_allows(tmp_path):
    # Pytest treats [] in an explicit test path as node parametrization syntax.
    # Keep hostile glob characters, quotes and Unicode without that reserved pair.
    root = _root(tmp_path, "active", name="repo Ω *? 'q'")
    _production_with_test(root, failing=True)
    # Relative paths must start at the git root, although the handler runs in .agents/.
    _expect(_decide(root, _write_payload("src/widget.py")), "allow",
            because="T1 uses root as base and T7 allows a production .py with a failing test")


@pytest.mark.parametrize("status,suffix,artifact,verdict,kind", [
    ("active", ".txt", "directory", "allow", None),
    ("active", ".PY", "directory", "deny", "target-outside-root"),
    ("inactive", ".txt", 5, "allow", None),
], ids=["non-py-allowed", "py-denied", "non-str-inactive"])
def test_artifact_directory_path(tmp_path, status, suffix, artifact, verdict, kind):
    root = _root(tmp_path, status)
    # /private/var/... on macOS is outside both the root and /tmp (including its alias).
    directory = tmp_path / "artifact Ω [*]"
    directory.mkdir()
    identity = importlib.import_module("h_mad_target_identity")
    assert not identity._path_within(str(directory), Path("/tmp")), (
        "artifactDirectoryPath fixture must be outside /tmp to isolate the artifact allowance"
    )
    target = directory / f"agent Ω [*]{suffix}"
    target.write_text(HOSTILE, encoding="utf-8")
    adp = str(directory) if artifact == "directory" else artifact
    _expect(_decide(root, _write_payload(str(target), artifactDirectoryPath=adp)), verdict, kind,
            because=f"T4 artifactDirectoryPath={adp!r}, suffix={suffix}, status={status}")


def test_tmp_non_py_write_allowed_under_active(tmp_path):
    root = _root(tmp_path, "active")
    # A missing leaf is enough; the gate judges the proposed write and creates nothing.
    target = f"/tmp/hmad-agy-{tmp_path.name}-Ω [*].txt"
    _expect(_decide(root, _write_payload(target)), "allow",
            because="T3 containment precedes T5 allowance check so T4 admits /tmp non-.py writes")


def test_hardlinked_production_name_is_judged(tmp_path):
    root = _root(tmp_path, "active", name="repo Ω *? 'q'")
    production = _production_with_test(root, relative="src/z.py")
    alias = root / "src/test_a.py"
    os.link(production, alias)
    identity = importlib.import_module("h_mad_target_identity")
    resolved = identity.canonicalise(str(root), str(alias), str(root))
    assert resolved.names == ("test_a.py", "z.py"), "T6 fixture must include both hard-link names"
    assert Path(resolved.target) == alias, "T6 target-only mutant must see the test-file spelling"
    _expect(_decide(root, _write_payload("src/test_a.py")), "deny", "test-passing",
            because="T6 judges every hard-link name and T7 passes through the judge's kind")


def test_unsearchable_chain_denies_although_the_scan_is_inactive(tmp_path):
    root = _root(tmp_path, "inactive")
    package = root / "package Ω [*]"
    docs = write_state(package, {HOSTILE: {"phase": "step5"}}).parent
    target = package / "worker.py"
    target.write_text(f"message = {HOSTILE!r}\n", encoding="utf-8")
    identity = importlib.import_module("h_mad_target_identity")
    judge = importlib.import_module("h_mad_tdd_judge")
    try:
        docs.chmod(0)
        assert identity._any_phase5_status(root) == "inactive", "rglob scan must miss the chmod 000 docs/"
        assert judge.read_chain(root, target).value == "unreadable", "T7 chain must detect the hidden state"
        _expect(_decide(root, _write_payload(str(target))), "deny", "judge-error",
                because="T6–T7 run under inactive and T7 refuses an unreadable chain")
    finally:
        docs.chmod(0o755)


def test_out_of_root_py_denies_under_unknown(tmp_path):
    root = _root(tmp_path, "unknown")
    _expect(_decide(root, _write_payload(str(tmp_path / "outside Ω [*].py"))),
            "deny", "target-outside-root",
            because="T4 outside-root .py refusal applies under unknown with its specific kind")


@pytest.mark.parametrize("target,status", [
    (".", "active"), (".", "unknown"), (".", "inactive"),
    ("src/", "active"), ("src/", "unknown"), ("src/", "inactive"),
], ids=["dot-active", "dot-unknown", "dot-inactive", "src-active", "src-unknown", "src-inactive"])
def test_class_b_directory_target(tmp_path, target, status):
    root = _root(tmp_path, status)
    (root / "src").mkdir()
    assert (root / target).is_dir(), "OD-2 fixture must name an existing directory"
    _expect(_decide(root, _write_payload(target)), "allow" if status == "inactive" else "deny",
            None if status == "inactive" else "judge-error",
            because=f"OD-2 T2a directory target {target!r} under {status}")
