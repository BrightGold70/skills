"""Caller-level RED for the Claude gate rewrite.

V-0: READING=E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b E1=present E2=absent EJ=absent E0=present claude=2.1.283 (Claude Code) scratch=/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T//hmad-v0.3XE4dM
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tdd_gate_support import build_venv, dd7_cells, decision, fake_venv, hook_form, sleeper, write_state


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"
CODEX_HOOK = HOOK.with_name("h-mad-codex-tdd-gate.py")
CHOSEN = re.search(r"CHOSEN=([ab]) ", __doc__).group(1)
HOSTILE_KEY = 'agent "q"\\newline\n[H-MAD:MARKER]%'
TARGET = "hematology-paper-writer/tools/w.py"
TEST = "hematology-paper-writer/tests/test_w.py"


def _file(root: Path, relative: str, body: str = "# governed production\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _root(tmp_path: Path, *, status: str | None = "exhausted", active: bool = True) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    records = {HOSTILE_KEY: {"phase": "step5", **({"codex_status": status} if status else {})}} if active else {"other": {"phase": "step3"}}
    write_state(root, records)
    return root


def _bin(tmp_path: Path, *, codex: bool = False, jq: bool = True) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name, source in (("python3", sys.executable), ("dirname", "/usr/bin/dirname"), ("basename", "/usr/bin/basename")):
        link = bin_dir / name
        if not link.exists():
            link.symlink_to(source)
    if jq and shutil.which("jq") and not (bin_dir / "jq").exists():
        (bin_dir / "jq").symlink_to(shutil.which("jq"))
    if codex:
        stub = bin_dir / "codex"
        stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)
    return bin_dir


def _payload(target: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": target}}


def _gate(root: Path, *, payload: dict | str | None = None, arg: str | None = None,
          bin_dir: Path, extra_env: dict | None = None, cwd: Path | None = None,
          hook: Path = HOOK, timeout: float = 60.0, path_tail: str = "/usr/bin:/bin"):
    env = {"PATH": f"{bin_dir}:{path_tail}", "HOME": str(Path.home()), "CLAUDE_PROJECT_DIR": str(root)}
    env.update(extra_env or {})
    kw = {"input": json.dumps(payload) if isinstance(payload, dict) else payload} if payload is not None else {"stdin": subprocess.DEVNULL}
    return subprocess.run([str(hook)] + ([arg] if arg is not None else []),
                          capture_output=True, text=True, cwd=cwd or root, env=env,
                          timeout=timeout, check=False, **kw)


def _out(result, hook: Path = HOOK):
    return decision(result, hook_form(hook))


def _assert(result, expected: str, kind: str = "", hook: Path = HOOK):
    out = _out(result, hook)
    assert out.decision == expected, f"expected {expected} {kind}, got {out}"
    if kind:
        assert out.kind == kind, f"expected kind={kind}, got {out}"
    return out


def _tree_b(tmp_path: Path, *, judge_line: str = "TDD-JUDGE: DENY kind=judge-error reason=stub",
            judge_rc: int = 0, state_line: str = "TDD-STATE: active codex-escape=yes blocker=0 records=1 fallback=none record=feat,exhausted,/x/docs/.bkit-memory.json,absent",
            state_rc: int = 0, marker: bool = False) -> tuple[Path, Path]:
    tree = tmp_path / "B"
    hook = tree / "h-mad/hooks/h-mad-tdd-gate.sh"
    hook.parent.mkdir(parents=True)
    shutil.copyfile(HOOK, hook)
    hook.chmod(0o755)
    judge = tree / "h-mad/scripts/h_mad_tdd_judge.py"
    judge.parent.mkdir(parents=True)
    judge.write_text(
        "import sys\nfrom pathlib import Path\n"
        f"verb=sys.argv[1]\n"
        f"if verb=='state':\n sys.stdout.write({state_line!r})\n sys.exit({state_rc})\n"
        + (f"Path({str(tree / 'marker')!r}).write_text('reached')\n" if marker else "")
        + f"sys.stdout.write({judge_line!r})\nsys.exit({judge_rc})\n",
        encoding="utf-8",
    )
    return hook, tree


@pytest.mark.parametrize("kind", ["red-measured", "no-test-resolved", "test-missing", "venv-escapes-root",
                                  "pytest-missing", "pytest-error", "no-tests-ran", "no-summary",
                                  "test-passing", "timeout", "judge-error"])
def test_claude_gate_kind(tmp_path, kind):
    root = _root(tmp_path)
    _file(root, TARGET)
    target = TARGET
    bin_dir = _bin(tmp_path)
    if kind != "test-missing":
        body = "def test_red():\n    assert False\n"
        body = {"pytest-error": "import module_that_does_not_exist_for_gate\n",
                "no-tests-ran": "# no tests collected\n",
                "test-passing": "def test_green():\n    assert True\n"}.get(kind, body)
        _file(root, TEST, body)
    if kind == "no-test-resolved":
        target = "tools/x.py"
        _file(root, target)
    elif kind == "venv-escapes-root":
        outside = tmp_path / "outside"
        fake_venv(outside, "exit 0")
        (root / "hematology-paper-writer/.venv").symlink_to(outside / ".venv", target_is_directory=True)
    elif kind == "pytest-missing":
        build_venv(root / "hematology-paper-writer/.venv", with_pytest=False)
    elif kind == "no-summary":
        fake_venv(root / "hematology-paper-writer", "exit 1")
    elif kind == "timeout":
        sleeper(fake_venv(root / "hematology-paper-writer", "exit 0"), tmp_path / "sleeper.pid", 90)
    hook = _tree_b(tmp_path, judge_line="TDD-JUDGE: MAYBE")[0] if kind == "judge-error" else HOOK
    result = _gate(root, payload=_payload(str(root / target)), bin_dir=bin_dir, hook=hook,
                   timeout=120.0 if kind == "timeout" else 60.0)
    _assert(result, "allow" if kind == "red-measured" else "deny",
            "" if kind == "red-measured" else kind, hook)


@pytest.mark.parametrize("variant,line,rc", [
    ("empty-line", "\n", 0), ("two-lines", "TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x\nTDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=y\n", 0),
    ("trailing-blank-line", "TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x\n\n", 0),
    ("maybe", "TDD-JUDGE: MAYBE\n", 0), ("unknown-kind", "TDD-JUDGE: DENY kind=bogus reason=x\n", 0),
    ("traceback-rc1", "Traceback: broken\n", 1),
    ("allow-rc1", "TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x\n", 1),
])
def test_judge_stub_is_judge_error(tmp_path, variant, line, rc):
    root = _root(tmp_path)
    hook, _ = _tree_b(tmp_path, judge_line=line, judge_rc=rc)
    result = _gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path), hook=hook)
    out = _assert(result, "deny", "judge-error", hook)
    assert out.rc != 1, variant


@pytest.mark.parametrize("variant,line,rc", [
    ("zero-lines", "", 0), ("two-lines", "TDD-STATE: none\nTDD-STATE: none\n", 0),
    ("trailing-blank-line", "TDD-STATE: none\n\n", 0),
    ("bad-value", "TDD-STATE: maybe\n", 0), ("none-rc1", "TDD-STATE: none\n", 1),
])
def test_state_stub_is_judge_error(tmp_path, variant, line, rc):
    root = _root(tmp_path)
    hook, _ = _tree_b(tmp_path, state_line=line, state_rc=rc)
    result = _gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path), hook=hook)
    _assert(result, "deny", "judge-error", hook)


def test_claude_code_payload_reaches_codex_authorship(tmp_path):
    root = _root(tmp_path, status=None)
    _assert(_gate(root, payload=_payload(str(root / TARGET)), bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


def test_stdin_target_beats_positional(tmp_path):
    root = _root(tmp_path, status=None)
    result = _gate(root, payload=_payload(str(root / TARGET)), arg=str(root / "tests/x.py"), bin_dir=_bin(tmp_path, codex=True))
    _assert(result, "deny", "codex-authorship")


def test_positional_alone_reaches_codex_authorship(tmp_path):
    root = _root(tmp_path, status=None)
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


@pytest.mark.parametrize("field", ["file_path", "path"], ids=["top-level-file-path", "top-level-path"])
def test_stdin_target_fields(tmp_path, field):
    root = _root(tmp_path, status=None)
    _assert(_gate(root, payload={field: str(root / TARGET)}, bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


def test_no_pytest_on_path_passing_test_is_refused(tmp_path):
    root = _root(tmp_path)
    _file(root, TARGET)
    _file(root, TEST, "def test_green():\n    assert True\n")
    out = _assert(_gate(root, payload=_payload(str(root / TARGET)), bin_dir=_bin(tmp_path), path_tail="/bin"), "deny")
    assert out.kind in {"pytest-missing", "test-passing"}, out


def test_new_production_file_with_passing_test_is_refused(tmp_path):
    root = _root(tmp_path)
    _file(root, TEST, "def test_green():\n    assert True\n")
    assert not (root / TARGET).exists()
    _assert(_gate(root, arg=TARGET, bin_dir=_bin(tmp_path)), "deny", "test-passing")


@pytest.mark.parametrize("site", ["codex-authorship", "judge-deny", "unreadable-state", "empty-target", "malformed-judge"])
def test_refusal_sites_use_the_chosen_form(tmp_path, site):
    root = _root(tmp_path, status=None if site == "codex-authorship" else "exhausted")
    hook = HOOK
    if site == "unreadable-state":
        (root / "docs/.bkit-memory.json").write_text("{not json", encoding="utf-8")
    elif site == "judge-deny":
        _file(root, TEST, "def test_green():\n    assert True\n")
    elif site == "malformed-judge":
        hook, _ = _tree_b(tmp_path, judge_line="TDD-JUDGE: MAYBE\n")
    result = _gate(root, arg=None if site == "empty-target" else str(root / TARGET),
                   payload={"tool_name": "Write", "tool_input": {}} if site == "empty-target" else None,
                   bin_dir=_bin(tmp_path, codex=site == "codex-authorship"), hook=hook)
    out = _assert(result, "deny", hook=hook)
    assert out.rc != 1 and hook_form(hook) == CHOSEN, out
    if CHOSEN == "b":
        assert isinstance(json.loads(result.stdout), dict) and result.stdout.count("hookSpecificOutput") == 1


def test_hook_has_no_exit_1():
    assert re.findall(r"^\s*exit 1\s*$", HOOK.read_text(encoding="utf-8"), re.M) == [], "hook still has exit 1 refusal sites"


def test_subproject_step5_under_root_step3_is_governed(tmp_path):
    root = _root(tmp_path, active=False)
    write_state(root / "hematology-paper-writer", {HOSTILE_KEY: {"phase": "step5", "codex_status": "exhausted"}})
    _file(root, TEST, "def test_green():\n    assert True\n")
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path)), "deny", "test-passing")


def test_unreadable_chain_refuses_production(tmp_path):
    root = _root(tmp_path)
    (root / "docs/.bkit-memory.json").write_text("{not json", encoding="utf-8")
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path)), "deny", "judge-error")


@pytest.mark.parametrize("target", ["docs/.bkit-memory.json", "tests/test_x.py", "notes.md"], ids=["state-file", "test-file", "doc"])
def test_exempt_write_on_unreadable_chain_is_allowed(tmp_path, target):
    root = _root(tmp_path)
    (root / "docs/.bkit-memory.json").write_text("{not json", encoding="utf-8")
    _assert(_gate(root, arg=str(root / target), bin_dir=_bin(tmp_path)), "allow")


@pytest.mark.parametrize("statuses", [("exhausted", None), (None, "exhausted")], ids=["exhausted-then-none", "none-then-exhausted"])
def test_codex_escape_needs_every_record(tmp_path, statuses):
    root = _root(tmp_path)
    write_state(root, {key: {"phase": "step5", **({"codex_status": status} if status else {})}
                       for key, status in zip(("a", "b"), statuses)})
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


@pytest.mark.parametrize("statuses", [("exhausted", "exhausted"), ("unavailable", "exhausted")], ids=["both-exhausted", "unavailable-and-exhausted"])
def test_codex_escape_all_declared_proceeds_to_judge(tmp_path, statuses):
    root = _root(tmp_path)
    write_state(root, {key: {"phase": "step5", "codex_status": status} for key, status in zip(("a", "b"), statuses)})
    _file(root, TEST, "def test_green():\n    assert True\n")
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path, codex=True)), "deny", "test-passing")


@pytest.mark.parametrize("variant", ["dangling-state-symlink", "missing-parent", "unsearchable-docs"])
def test_fast_path_defers(tmp_path, variant):
    root = _root(tmp_path)
    target = root / TARGET
    docs = root / "docs"
    if variant == "dangling-state-symlink":
        (docs / ".bkit-memory.json").unlink()
        (docs / ".bkit-memory.json").symlink_to("absent")
    elif variant == "missing-parent":
        (docs / ".bkit-memory.json").unlink()
        write_state(root / "hematology-paper-writer", {HOSTILE_KEY: {"phase": "step5", "codex_status": "exhausted"}})
        # impl-plan Task 8 item 17: the GREEN test is tests/test_x.py, the name the judge derives for newdir/x.py.
        _file(root, "hematology-paper-writer/tests/test_x.py", "def test_green():\n    assert True\n")
        target = root / "hematology-paper-writer/newdir/x.py"
    else:
        (docs / ".bkit-memory.json").unlink()
        substate = write_state(root / "hematology-paper-writer", {HOSTILE_KEY: {"phase": "step5"}})
        docs = substate.parent
        docs.chmod(0)
    try:
        result = _gate(root, arg=str(target), bin_dir=_bin(tmp_path))
    finally:
        if variant == "unsearchable-docs":
            docs.chmod(0o755)
    _assert(result, "deny", "test-passing" if variant == "missing-parent" else "judge-error")


def test_no_jq_on_path_still_judges(tmp_path):
    root = _root(tmp_path)
    _file(root, TEST, "def test_green():\n    assert True\n")
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path, jq=False), path_tail="/bin"), "deny", "test-passing")


@pytest.mark.parametrize("variant", ["active-root", "unreadable-root", "no-step5-root"])
def test_empty_target_rule(tmp_path, variant):
    root = _root(tmp_path, active=variant != "no-step5-root")
    if variant == "unreadable-root":
        (root / "docs/.bkit-memory.json").write_text("{not json", encoding="utf-8")
    result = _gate(root, payload={"tool_name": "Write", "tool_input": {}}, bin_dir=_bin(tmp_path))
    _assert(result, "allow" if variant == "no-step5-root" else "deny",
            "" if variant == "no-step5-root" else "judge-error")


@pytest.mark.parametrize("active", [True, False], ids=["active", "no-step5"])
def test_outside_root_target_is_governed_by_root(tmp_path, active):
    root = _root(tmp_path, status=None, active=active)
    result = _gate(root, arg=str(tmp_path / "sibling/x.py"), bin_dir=_bin(tmp_path, codex=True))
    _assert(result, "deny" if active else "allow", "codex-authorship" if active else "")


@pytest.mark.parametrize("name,target,expected", [
    ("tests-relative", "tests/x.py", "allow"), ("dot-tests-relative", "./tests/x.py", "allow"),
    ("fixtures-relative", "fixtures/x.py", "allow"), ("sub-relative", "sub/x.py", "deny"),
])
def test_relative_targets(tmp_path, name, target, expected):
    root = _root(tmp_path, status=None)
    b = _bin(tmp_path, codex=True)
    out = _assert(_gate(root, arg=target, bin_dir=b), expected, "codex-authorship" if expected == "deny" else "")
    if name == "sub-relative":
        absolute = _assert(_gate(root, arg=str(root / target), bin_dir=b), "deny", "codex-authorship")
        assert out.decision == absolute.decision


@pytest.mark.parametrize("target", ["tests/../x.py", "./tests/../x.py", "absolute"], ids=["relative", "dot-relative", "absolute"])
def test_traversal_target_is_gated(tmp_path, target):
    root = _root(tmp_path, status=None)
    arg = str(root / "tests/../x.py") if target == "absolute" else target
    _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


def test_dd7_differential_matches_the_published_cells(tmp_path):
    assert not {"tests", "fixtures"}.intersection(tmp_path.resolve().parts)
    observed = []
    for shape in ("repo", "tests/repo", "fixtures/repo"):
        root = tmp_path / shape
        root.mkdir(parents=True)
        b = _bin(root, codex=True)
        for cell in dd7_cells(root, shape):
            write_state(root, {HOSTILE_KEY: {"phase": "step5"}} if cell.state == "active" else {"other": {"phase": "step3"}})
            out = _out(_gate(root, arg=cell.target, bin_dir=b))
            assert out.decision == cell.expected, f"DD-7 {cell.name}: {out}"
            if out.decision == "deny":
                assert out.kind == "codex-authorship", f"DD-7 {cell.name}: {out}"
            observed.append(out.decision)
    assert len(observed) == 126 and observed.count("deny") == 18


def test_control_character_stdin_target_never_falls_back(tmp_path):
    root = _root(tmp_path)
    _assert(_gate(root, payload=_payload("a\nb.py"), arg=str(root / "tests/x.py"), bin_dir=_bin(tmp_path)), "deny", "judge-error")


def test_non_json_stdin_never_falls_back_to_positional(tmp_path):
    root = _root(tmp_path)
    _assert(_gate(root, payload="not json", arg=str(root / "tests/x.py"), bin_dir=_bin(tmp_path)), "deny", "judge-error")


def test_unenterable_project_dir_refuses(tmp_path):
    root = _root(tmp_path)
    result = _gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path), extra_env={"CLAUDE_PROJECT_DIR": str(tmp_path / "absent")})
    out = _assert(result, "deny", "judge-error")
    assert "CLAUDE_PROJECT_DIR" in out.reason


def test_codex_authorship_hint_names_blocker_key_and_state_file(tmp_path):
    root = tmp_path / "my proj"
    root.mkdir()
    state = write_state(root, {"a": {"phase": "step5", "codex_status": "exhausted"}, "b": {"phase": "step5"}})
    out = _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")
    assert "--feature b" in out.reason and str(state) in out.reason


@pytest.mark.parametrize("variant", ["traceback-rc1", "allow-rc1", "realpath-stub", "unset-variable"])
def test_trap_member_refuses_in_form(tmp_path, variant):
    root = _root(tmp_path, status=None if variant == "unset-variable" else "exhausted")
    line = "Traceback: broken\n" if variant == "traceback-rc1" else "TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x\n"
    hook, _ = _tree_b(tmp_path, judge_line=line, judge_rc=1)
    b = _bin(tmp_path, codex=variant == "unset-variable")
    if variant == "realpath-stub":
        shim = b / "python3"
        shim.unlink()
        shim.write_text("#!/bin/sh\ncase \"$*\" in *os.path.realpath*) exit 3 ;; esac\nexec " + sys.executable + " \"$@\"\n", encoding="utf-8")
        shim.chmod(0o755)
    elif variant == "unset-variable":
        source = hook.read_text(encoding="utf-8")
        assert source.count("_refuse() {") == 1
        hook.write_text(source.replace("_refuse() {", '_refuse() {\n  : "$HMAD_UNSET_PROBE_VAR"'), encoding="utf-8")
    result = _gate(root, arg=str(root / TARGET), bin_dir=b, hook=hook)
    out = _assert(result, "deny", "judge-error", hook)
    assert out.rc != 1


def test_symlinked_hook_runs_its_own_trees_judge(tmp_path):
    root = _root(tmp_path)
    hook, tree = _tree_b(tmp_path, judge_line="TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=tree-b.py\n", marker=True)
    link = tmp_path / "L/h-mad-tdd-gate.sh"
    link.parent.mkdir()
    link.symlink_to(hook)
    result = _gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path), hook=link)
    assert (tree / "marker").exists(), "symlinked hook did not call tree B judge"
    _assert(result, "allow", hook=link)


def test_hooks_reach_the_name_map_only_through_the_judge():
    assert "h_mad_derive_test_path.sh" not in HOOK.read_text(encoding="utf-8"), "Claude hook still owns name map"
    assert "h_mad_derive_test_path.sh" not in CODEX_HOOK.read_text(encoding="utf-8")


def test_claude_gate_keeps_no_private_state_reader():
    source = HOOK.read_text(encoding="utf-8")
    for token in ("orchestrator_state", "_resolve_state_file", "jq"):
        assert token not in source, f"Claude gate still owns private state reader: {token}"


def test_refusal_form_is_a_readonly_literal():
    source = HOOK.read_text(encoding="utf-8")
    assert len(re.findall(r"^readonly REFUSAL_FORM=[ab]$", source, re.M)) == 1, "missing readonly REFUSAL_FORM literal"
    assert hook_form(HOOK) == CHOSEN
    assert not re.search(r"REFUSAL_FORM=.*\$", source), "REFUSAL_FORM read from environment"


def test_state_without_step5_is_allowed(tmp_path):
    root = _root(tmp_path, active=False)
    _assert(_gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path, codex=True)), "allow")


@pytest.mark.parametrize("target", ["x.py", "absolute"], ids=["tests-root-relative", "tests-root-absolute"])
def test_root_under_a_test_directory_is_governed(tmp_path, target):
    root = tmp_path / "tests/repo"
    root.mkdir(parents=True)
    write_state(root, {HOSTILE_KEY: {"phase": "step5"}})
    arg = str(root / "x.py") if target == "absolute" else target
    _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


@pytest.mark.parametrize("target", ["../x.py", "traversal-absolute"], ids=["dotdot-relative", "traversal-absolute"])
def test_outside_root_exemption_needs_both_spellings(tmp_path, target):
    root = tmp_path / "tests/repo"
    root.mkdir(parents=True)
    write_state(root, {HOSTILE_KEY: {"phase": "step5"}})
    arg = str(tmp_path / "tests/../x.py") if target == "traversal-absolute" else target
    _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path, codex=True)), "deny", "codex-authorship")


def test_root_name_glob_characters_are_literal(tmp_path):
    root = tmp_path / "re[p]o"
    root.mkdir()
    write_state(root, {HOSTILE_KEY: {"phase": "step5"}})
    _assert(_gate(root, arg="tests/x.py", bin_dir=_bin(tmp_path, codex=True)), "allow")
