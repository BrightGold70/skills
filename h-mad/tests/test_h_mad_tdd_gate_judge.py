"""Caller-level RED for the Claude gate rewrite.

V-0: READING=E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b E1=present E2=absent EJ=absent E0=present claude=2.1.283 (Claude Code) scratch=/var/folders/7s/9n332lmj54511rf57fgf8pz40000gn/T//hmad-v0.3XE4dM
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tdd_gate_support import assert_case_insensitive, build_venv, dd7_cells, decision, detaching_sleeper, fake_venv, hook_form, sleeper, stop_detached, write_state


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
    identity = tree / "h-mad/scripts/h_mad_target_identity.py"
    identity.write_text(
        "import os\n"
        "def canonicalise(root, target):\n"
        " path = os.path.normpath(os.path.join(root, target))\n"
        " return (os.path.realpath(root), os.path.dirname(path), "
        "os.path.dirname(path), os.path.basename(path))\n"
        "def emit_canon(record):\n"
        " root, target, prefix, name = record\n"
        " print('CANON 1')\n"
        " for key, value in (('root', root), ('target', target), ('prefix', prefix)):\n"
        "  print(key + ' ' + value)\n"
        " print('unresolvable no')\n print('arm 0')\n print('component ')\n"
        " print('names 1')\n print('name ' + name)\n",
        encoding="utf-8",
    )
    return hook, tree


@pytest.mark.parametrize("kind", ["red-measured", "no-test-resolved", "test-missing", "venv-escapes-root",
                                  "pytest-missing", "pytest-error", "no-tests-ran", "no-summary",
                                  "test-passing", "timeout", "judge-timeout", "judge-error"])
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
    elif kind == "judge-timeout":
        pidfile = tmp_path / "detached.pid"
        detaching_sleeper(fake_venv(root / "hematology-paper-writer", "exit 0"), pidfile, 90,
                           parent_seconds=90)
    hook = _tree_b(tmp_path, judge_line="TDD-JUDGE: MAYBE")[0] if kind == "judge-error" else HOOK
    try:
        result = _gate(root, payload=_payload(str(root / target)), bin_dir=bin_dir, hook=hook,
                       timeout=120.0 if kind in ("timeout", "judge-timeout") else 60.0)
    finally:
        if kind == "judge-timeout":
            stop_detached(pidfile)
    _assert(result, "allow" if kind == "red-measured" else "deny",
            "" if kind == "red-measured" else kind, hook)


@pytest.mark.parametrize("depth", ["one-absent", "two-absent"])
def test_claude_absent_intermediate_dirs_judge_the_real_target(tmp_path, depth):
    root = _root(tmp_path)
    if depth == "one-absent":
        (root / "hematology-paper-writer").mkdir()
    target = "hematology-paper-writer/tools/x.py"
    result = _gate(root, payload=_payload(str(root / target)), bin_dir=_bin(tmp_path),
                   extra_env={"HMAD_CODEX_UNAVAILABLE": "1"})
    out = _assert(result, "deny", "test-missing")
    assert "hematology-paper-writer/tests/test_x.py" in out.reason, out


def test_claude_gate_judge_timeout_stub(tmp_path):
    root = _root(tmp_path)
    hook, _ = _tree_b(tmp_path, judge_line="TDD-JUDGE: DENY kind=judge-timeout reason=r", judge_rc=0)
    result = _gate(root, arg=str(root / TARGET), bin_dir=_bin(tmp_path), hook=hook)
    _assert(result, "deny", "judge-timeout", hook)


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



@pytest.mark.parametrize("spelling", ["as-on-disk", "mis-cased"])
def test_mode_000_project_dir_refuses(tmp_path, spelling):
    # Operator decisions D-2/D-3 (2026-09-30): a root that exists but cannot be
    # entered is refused whatever its spelling; the refusal does not depend on
    # the arm-2 component equalling the spelled root.
    root = _root(tmp_path, active=False).rename(tmp_path / "Proj")
    spelled = root if spelling == "as-on-disk" else root.with_name("proj")
    if spelling == "mis-cased":
        assert spelled.exists() and spelled.name not in os.listdir(tmp_path), "case-insensitive precondition"
    original_mode = root.stat().st_mode & 0o7777
    root.chmod(0)
    try:
        with pytest.raises(PermissionError):
            os.open(spelled, os.O_RDONLY)
        result = _gate(root, arg=str(spelled / "src/prod.py"), bin_dir=_bin(tmp_path), cwd=tmp_path,
                       extra_env={"CLAUDE_PROJECT_DIR": str(spelled)})
        out = _assert(result, "deny", "judge-error")
        assert "cannot be entered" in out.reason, out.reason
    finally:
        root.chmod(original_mode)

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


@pytest.mark.parametrize("cell", ["m4", "m5"])
def test_claude_symlinked_test_dir_denies(tmp_path, cell):
    root = _root(tmp_path)
    src = root / "src"
    src.mkdir()
    (root / "tests").symlink_to(src, target_is_directory=True)
    if cell == "m4":
        _file(root, "src/prod.py")
    _assert(_gate(root, arg=f"tests/{'prod' if cell == 'm4' else 'newmod'}.py",
                  bin_dir=_bin(tmp_path)), "deny", "no-test-resolved")


def test_claude_dotdot_after_symlink_denies(tmp_path):
    root = _root(tmp_path)
    _file(root, "src/prod.py")
    (root / "tests").mkdir()
    (root / "src/sub").mkdir()
    (root / "tests/l").symlink_to("../src/sub", target_is_directory=True)
    _assert(_gate(root, arg="tests/l/../prod.py", bin_dir=_bin(tmp_path)),
            "deny", "no-test-resolved")


def test_claude_symlinked_root_denies(tmp_path):
    physical = tmp_path / "R/real"
    _file(physical, "x.py")
    write_state(physical, {"feat": {"phase": "step5", "codex_status": "exhausted"}})
    spelled = tmp_path / "R/tests/link"
    spelled.parent.mkdir()
    spelled.symlink_to("../real", target_is_directory=True)
    assert "tests" in spelled.parts and spelled.resolve() == physical
    b = _bin(tmp_path)
    _assert(_gate(spelled, arg=str(spelled / "x.py"), bin_dir=b), "deny", "no-test-resolved")
    _assert(_gate(physical, arg=str(physical / "x.py"), bin_dir=b), "deny", "no-test-resolved")


def test_claude_symlinked_root_inside_tests_still_denies_production(tmp_path):
    physical = tmp_path / "tests/real"
    _file(physical, "x.py")
    write_state(physical, {"feat": {"phase": "step5", "codex_status": "exhausted"}})
    spelled = tmp_path / "tests/link"
    spelled.symlink_to("real", target_is_directory=True)
    assert spelled.resolve() == physical

    _assert(_gate(spelled, arg=str(spelled / "x.py"), bin_dir=_bin(tmp_path)),
            "deny", "no-test-resolved")


@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_claude_case_root_m8_denies(tmp_path, direction):
    assert_case_insensitive(tmp_path)
    disk, spelled = ("Case", "case") if direction == "forward" else ("case", "Case")
    root = tmp_path / disk / "tests/proj"
    _file(root, "src/prod.py")
    write_state(root, {"feat": {"phase": "step5", "codex_status": "exhausted"}})
    target = tmp_path / spelled / "tests/proj/src/prod.py"
    assert target.exists()
    _assert(_gate(root, arg=str(target), bin_dir=_bin(tmp_path)), "deny", "no-test-resolved")


def test_claude_case_directory_m9_denies(tmp_path):
    assert_case_insensitive(tmp_path)
    root = _root(tmp_path)
    disk = _file(root, "Tests/prod.py")
    assert (root / "tests/prod.py").samefile(disk)
    result = _gate(root, arg="tests/prod.py", bin_dir=_bin(tmp_path))
    _assert(result, "deny", "no-test-resolved")


@pytest.mark.parametrize("cell", ["m10", "m11"])
def test_claude_toward_allow_m10_m11(tmp_path, cell):
    root = _root(tmp_path)
    if cell == "m10":
        _file(root, "fixtures/helper.py")
        arg = "FIXTURES/helper.py"
        assert (root / arg).exists()
    else:
        _file(root, "tests/helper.py")
        (root / "src").mkdir()
        (root / "src/tl").symlink_to("../tests", target_is_directory=True)
        arg = "src/tl/helper.py"
    _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path)), "allow")


@pytest.mark.parametrize("shape", ["absent-leaf", "absent-parent"])
def test_claude_new_file_denies_without_judge_error(tmp_path, shape):
    root = _root(tmp_path)
    arg = "src/new.py" if shape == "absent-leaf" else "src/newpkg/mod.py"
    (root / "src").mkdir()
    out = _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path)), "deny")
    assert out.kind != "judge-error"


def test_claude_hard_link_alias_denies(tmp_path):
    root = _root(tmp_path)
    production = _file(root, "src/prod.py")
    alias = root / "src/test_prod.py"
    os.link(production, alias)
    assert production.stat().st_ino == alias.stat().st_ino
    _assert(_gate(root, arg="src/test_prod.py", bin_dir=_bin(tmp_path)),
            "deny", "no-test-resolved")


def test_claude_hardlink_mixed_names_judges_the_production_name(tmp_path):
    from test_h_mad_codex_tdd_gate_judge import _payload as codex_payload, _run as run_codex

    root = _root(tmp_path)
    target = "hematology-paper-writer/tools/test_a.py"
    alias = _file(root, target)
    production = root / "hematology-paper-writer/tools/z.py"
    os.link(alias, production)
    assert alias.stat().st_ino == production.stat().st_ino

    codex_decision, codex_reason, _ = run_codex(root, codex_payload(target))
    assert codex_decision == "deny", codex_reason
    assert "kind=test-missing" in codex_reason, codex_reason
    mapped_test = "hematology-paper-writer/tests/test_z.py"
    assert mapped_test in codex_reason, codex_reason

    claude = _assert(_gate(root, arg=target, bin_dir=_bin(tmp_path)),
                     codex_decision, "test-missing")
    assert mapped_test in claude.reason, claude.reason


@pytest.mark.parametrize("name,expected", [("lnk", "deny"), ("tests", "allow"), ("src", "deny")])
def test_claude_outside_root_symlink_keeps_raw_conjunct(tmp_path, name, expected):
    root = _root(tmp_path)
    outside = tmp_path / "out"
    (outside / "tests").mkdir(parents=True)
    (outside / "src").mkdir()
    (outside / "lnk").symlink_to("tests", target_is_directory=True)
    _assert(_gate(root, arg=str(outside / name / "x.py"), bin_dir=_bin(tmp_path)),
            expected, "no-test-resolved" if expected == "deny" else "")


def test_claude_fold_existing_leaf_denies(tmp_path):
    root = _root(tmp_path)
    _file(root, "src/prod.PY")
    _assert(_gate(root, arg="src/prod.PY", bin_dir=_bin(tmp_path)), "deny", "no-test-resolved")


@pytest.mark.parametrize("suffix", ["m3", "pY", "Py"])
def test_claude_fold_new_leaf_denies(tmp_path, suffix):
    root = _root(tmp_path)
    (root / "src").mkdir()
    ext = "PY" if suffix == "m3" else suffix
    _assert(_gate(root, arg=f"src/new.{ext}", bin_dir=_bin(tmp_path)), "deny", "no-test-resolved")


def test_claude_test_shaped_names_stay_exempt(tmp_path):
    root = _root(tmp_path)
    b = _bin(tmp_path)
    for name in ("test_x.PY", "x_test.pY", "conftest.Py"):
        _assert(_gate(root, arg=f"src/{name}", bin_dir=b), "allow")


def test_claude_trailing_space_is_not_folded(tmp_path):
    root = _root(tmp_path)
    _assert(_gate(root, arg="src/prod.py ", bin_dir=_bin(tmp_path)), "allow")


def _unresolvable(root: Path, cell: str) -> tuple[str, str]:
    if cell == "m12":
        (root / "src").mkdir()
        (root / "docs/d.md").symlink_to("../src/newprod.py")
        return "docs/d.md", str(root / "docs/d.md")
    if cell == "m13-leaf":
        (root / "src").mkdir()
        (root / "src/dang.py").symlink_to("nowhere/x.py")
        return "src/dang.py", str(root / "src/dang.py")
    if cell == "m13-intermediate":
        (root / "lnk").symlink_to("nowhere", target_is_directory=True)
        return "lnk/x.py", str(root / "lnk")
    (root / "src").mkdir()
    (root / "src/loopa.py").symlink_to("loopb.py")
    (root / "src/loopb.py").symlink_to("loopa.py")
    return "src/loopa.py", str(root / "src/loopa.py")


@pytest.mark.parametrize("cell", ["m12", "m13-leaf", "m13-intermediate", "m14"])
def test_claude_unresolvable_governed_is_judge_error(tmp_path, cell):
    root = _root(tmp_path)
    arg, component = _unresolvable(root, cell)
    out = _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path)), "deny", "judge-error")
    assert "arm=1" in out.reason and component in out.reason


def test_claude_unresolvable_step3_allows(tmp_path):
    root = _root(tmp_path, active=False)
    arg, _ = _unresolvable(root, "m13-leaf")
    _assert(_gate(root, arg=arg, bin_dir=_bin(tmp_path)), "allow")


def _unreadable_referent(root: Path, kind: str) -> tuple[Path, Path]:
    src = root / "src"
    src.mkdir()
    private = root / "private"
    private.mkdir()
    sealed = private / "sealed"
    if kind == "a":
        sealed.write_text("pass\n")
    else:
        sealed.mkdir()
    target = src / "link.py"
    target.symlink_to("../private/sealed", target_is_directory=kind == "b")
    sealed.chmod(0)
    return target, sealed


@pytest.mark.parametrize("kind", ["a", "b"])
def test_claude_unreadable_component_step5(tmp_path, kind):
    root = _root(tmp_path)
    target, sealed = _unreadable_referent(root, kind)
    try:
        with pytest.raises(PermissionError):
            os.open(target, os.O_RDONLY)
        out = _assert(_gate(root, arg=str(target), bin_dir=_bin(tmp_path)),
                      "deny", "judge-error")
        assert "arm=2" in out.reason and str(target) in out.reason
    finally:
        sealed.chmod(0o755)


@pytest.mark.parametrize("kind", ["a", "b"])
def test_claude_unreadable_component_step3_allows(tmp_path, kind):
    root = _root(tmp_path, active=False)
    target, sealed = _unreadable_referent(root, kind)
    try:
        with pytest.raises(PermissionError):
            os.open(target, os.O_RDONLY)
        _assert(_gate(root, arg=str(target), bin_dir=_bin(tmp_path)), "allow")
    finally:
        sealed.chmod(0o755)


@pytest.mark.parametrize("active", [True, False], ids=["active", "inactive"])
def test_claude_root_open_failure_refuses_only_when_governed(tmp_path, active):
    root = _root(tmp_path, active=active)
    b = _bin(tmp_path)
    root.chmod(0o311)
    try:
        with pytest.raises(PermissionError):
            os.open(root, os.O_RDONLY)
        out = _assert(_gate(root, arg="src/prod.py", bin_dir=b),
                      "deny" if active else "allow", "judge-error" if active else "")
        if active:
            assert "arm=2" in out.reason and str(root) in out.reason
    finally:
        root.chmod(0o755)


@pytest.mark.parametrize("variant", [
    "unknown-key", "missing-key", "second-header", "version-2", "arm-3",
    "unresolvable-maybe", "names-negative", "count-mismatch", "bad-pct",
    "directory-with-names", "file-with-zero-names",
])
def test_claude_canon_protocol_error_is_judge_error(tmp_path, variant):
    root = _root(tmp_path)
    target = _file(root, "src/file.py")
    if variant == "directory-with-names":
        target = root / "src/dir.py"
        target.mkdir()
        assert target.is_dir()
    else:
        assert target.is_file()
    b = _bin(tmp_path)
    hook, tree = _tree_b(tmp_path,
                         judge_line="TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x.py")
    fields = ["CANON 1", f"root {root}", f"target {target.parent}",
              f"prefix {target.parent}", "unresolvable no", "arm 0",
              "component ", "names 1", f"name {target.name}"]
    if variant == "unknown-key":
        fields.insert(1, "surprise x")
    elif variant == "missing-key":
        fields.remove("arm 0")
    elif variant == "second-header":
        fields.append("CANON 1")
    elif variant == "version-2":
        fields[0] = "CANON 2"
    elif variant == "arm-3":
        fields[5] = "arm 3"
    elif variant == "unresolvable-maybe":
        fields[4] = "unresolvable maybe"
    elif variant == "names-negative":
        fields[7] = "names -1"
    elif variant == "count-mismatch":
        fields[7] = "names 2"
    elif variant == "bad-pct":
        fields[-1] = "name bad%GG.py"
    elif variant == "directory-with-names":
        fields[2] = f"target {target}"
    else:
        fields[7] = "names 0"
        fields.pop()
    record = "\n".join(fields)
    (tree / "h-mad/scripts/h_mad_target_identity.py").write_text(
        "def canonicalise(*args, **kwargs):\n return None\n"
        f"def emit_canon(record):\n print({record!r})\n", encoding="utf-8")
    _assert(_gate(root, arg=str(target), bin_dir=b, hook=hook), "deny", "judge-error", hook)


def test_claude_gate_is_bash_3_2_clean(tmp_path):
    patterns = [
        (r"\b(local|declare|typeset)\s+-[a-zA-Z]*n\b", "local -n _out=$1"),
        (r"\b(local|declare|typeset)\s+-[a-zA-Z]*A\b", "declare -A m"),
        (r"\b(declare|typeset)\s+-[a-zA-Z]*g\b", "declare -g X=1"),
        (r"\b(mapfile|readarray)\b", "mapfile -t a < f"),
        (r"\$\{[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?(,|\^)", "${name,,}"),
    ]
    source = HOOK.read_text(encoding="utf-8")
    for index, (pattern, fixture) in enumerate(patterns):
        assert re.search(pattern, fixture), f"pattern {index} misses its positive fixture"
        assert all(not re.search(other, fixture) for j, (other, _) in enumerate(patterns)
                   if j != index), f"pattern {index} overlaps another fixture"
        assert not re.search(pattern, source), f"bash 3.2 forbidden construct: {fixture}"
    root = _root(tmp_path)
    (root / "src").mkdir()
    b = _bin(tmp_path)
    env = {"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()),
           "CLAUDE_PROJECT_DIR": str(root)}
    result = subprocess.run(["/bin/bash", str(HOOK), "src/new.py"], cwd=root, env=env,
                            stdin=subprocess.DEVNULL, text=True, capture_output=True,
                            timeout=60, check=False)
    out = _assert(result, "deny")
    assert out.kind != "judge-error"
    assert not any(word in result.stderr for word in
                   ("invalid option", "bad substitution", "command not found"))


def test_claude_single_pwd_p_is_the_h8_walk():
    lines = [line for line in HOOK.read_text(encoding="utf-8").splitlines() if "pwd -P" in line]
    assert len(lines) == 1 and "# M:H8" in lines[0]
