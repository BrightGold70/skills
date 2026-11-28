"""Phase 5 scope differential at the old-tree boundary (Task 1)."""
from __future__ import annotations

import ast
import errno
import hashlib
import importlib
import importlib.machinery
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import venv
from unittest import mock

import pytest

import tdd_gate_support as support


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "docs/03-analysis/probes/phase5-gate-feature-scope/differential.py"
BASE = "7a3cca48"
SURFACES = ("codex-shell", "codex-write", "agy-shell", "agy-write", "claude")
INTERPRETERS = ("py3.9", "py3.11", "py3.12", "py3.13", "py3.14", "py3.15")
ALL_CLASSES = frozenset(("D1", "D2", "D3", "D4", "D5", "D6", "D7"))
PRESENCE = ("regular", "file-link", "dangling-link", "looping-link", "directory-in-place",
            "docs-symlink", "case-variant-docs", "case-variant-file")
VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES")


def differential():
    with mock.patch.object(sys, "path", [str(PROBE.parent), *sys.path]):
        module = importlib.import_module("differential")
    assert Path(module.__file__).resolve() == PROBE, "must load this worktree's oracle"
    return module


def interpreter(module, name):
    paths = module.resolve_interpreters()
    assert name in paths, f"resolver omitted interpreter or named skip {name}"
    if paths[name] is None:
        pytest.skip(f"launcher unavailable for {name}")
    return paths[name]


def named(module, name, surface):
    rows = [s for s in module.crossed_corpus() if s.name == name and s.surface == surface]
    assert len(rows) == 1, f"expected one {surface} corpus case named {name!r}"
    return rows[0]


@pytest.fixture(autouse=True)
def scratch_environment(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    for variable in (*VARIABLES, "CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        monkeypatch.delenv(variable, raising=False)


def test_supported_interpreters_are_the_parametrised_set(tmp_path, request, monkeypatch, capsys):
    module = differential()
    resolved = module.resolve_interpreters()
    assert set(resolved) == set(INTERPRETERS), f"pytest interpreter matrix differs: {resolved}"
    present = {key: Path(path).resolve() for key, path in resolved.items() if path is not None}
    assert len(set(present.values())) == len(present), "one interpreter per executable identity"
    for key, path in present.items():
        version = subprocess.check_output(
            [str(path), "-c", "import sys; print('py%d.%d' % sys.version_info[:2])"],
            text=True, timeout=10, env=support.hermetic_env(),
        ).strip()
        assert key.split("-")[0] == version, f"{key} runs {version} at {path}"

    usage = subprocess.run([sys.executable, str(PROBE), "--bad-option"], cwd=ROOT,
                           env=support.hermetic_env(), capture_output=True, timeout=15)
    assert (usage.returncode, usage.stdout) == (2, b""), "bad option must be a silent usage exit"
    # Exercise the no-option path with a bounded corpus. The matrix below runs every row.
    row = named(module, "excluded-alone", "codex-shell")
    monkeypatch.setattr(module, "crossed_corpus", lambda: (row,))
    monkeypatch.setattr(module, "resolve_interpreters", lambda: {"py3.11": sys.executable})
    monkeypatch.setattr(sys, "argv", [str(PROBE)])
    # The harness loads the decoder by path. Observe its actual returns even when
    # that import has a different module name from the one pytest uses here.
    seen = set()
    admission_seen = set()
    seen_before_first = []
    hook_verdicts = []
    decoder_verdicts = []
    decoder_file = Path(support.__file__).resolve()
    real_run_hook = module.run_hook

    def record_run_hook(tree, case, python):
        verdict = real_run_hook(tree, case, python)
        hook_verdicts.append((case.spec.name, tree, case.spec.call, verdict))
        if case.spec.name == "admission-control":
            side = "new" if Path(tree).resolve() == ROOT.resolve() else "old"
            cmd = (
                case.spec.call["toolCall"]["args"]["CommandLine"]
                if case.spec.surface == "agy-shell"
                else case.spec.call["tool_input"]["cmd"]
            )
            admission_seen.add((case.spec.surface, side, verdict.decision, cmd))
        return verdict

    monkeypatch.setattr(module, "run_hook", record_run_hook)

    def record_decoder(frame, event, outcome):
        if (event == "return" and frame.f_code.co_name == "host_decision" and outcome is not None
                and Path(frame.f_code.co_filename).resolve() == decoder_file):
            host = frame.f_locals["host"]
            result = frame.f_locals["result"]
            seen.add((host, outcome.decision))
            decoder_verdicts.append((host, outcome, result.stdout, result.stderr))

    def verdict_details(hook_count=None, decoder_count=None):
        return (f"hook verdicts={hook_verdicts[:hook_count]!r}\n"
                f"decoder outcomes with stdout and stderr={decoder_verdicts[:decoder_count]!r}")

    calibrated = set(itertools.product(("claude", "codex", "agy"), ("allow", "deny", "invalid")))
    expected_admission = set(itertools.product(
        ("codex-shell", "agy-shell"), ("old", "new"), ("allow", "deny"),
        ("true", "hmad-dispatch run --timeout 60 -- true"),
    ))
    expected = module.expected_verdict
    compared = []

    def after_decoder_controls(*args, **kwargs):
        assert calibrated <= seen, (
            f"missing baseline decoder controls before first twin: {calibrated - seen}\n{verdict_details()}"
        )
        seen_before_first.append((set(seen), set(admission_seen), len(hook_verdicts), len(decoder_verdicts)))
        compared.append(True)
        return expected(*args, **kwargs)

    monkeypatch.setattr(module, "expected_verdict", after_decoder_controls)
    capsys.readouterr()
    old_profile = sys.getprofile()
    try:
        sys.setprofile(record_decoder)
        assert module.main() == 0, f"{capsys.readouterr()!r}\n{verdict_details()}"
    finally:
        sys.setprofile(old_profile)
    assert calibrated <= seen, f"missing baseline decoder controls: {calibrated - seen}\n{verdict_details()}"
    assert compared, f"the CLI must compare the selected corpus row\n{verdict_details()}"
    result = capsys.readouterr()
    assert re.fullmatch(r"DIFFERENTIAL: PASS cases=[1-9][0-9]*\n", result.out), (
        f"{result!r}\n{verdict_details()}"
    )

    def wrong_twin(spec, interpreter, changes, scratch, legacy_raise_lifted=False):
        return expected(spec, interpreter, changes ^ {"D1"}, scratch, legacy_raise_lifted)

    monkeypatch.setattr(module, "expected_verdict", wrong_twin)
    assert module.main() == 0, (
        f"DIFFERENTIAL: FAIL is a normal verdict token and must exit 0: {capsys.readouterr()!r}\n"
        f"{verdict_details()}"
    )
    result = capsys.readouterr()
    assert result.out == f"DIFFERENTIAL: FAIL case={row.name}\n", f"{result!r}\n{verdict_details()}"

    assert expected_admission <= seen_before_first[0][1], (
        f"missing admission controls in main() before first twin: {expected_admission - seen_before_first[0][1]}\n"
        f"{verdict_details(*seen_before_first[0][2:])}"
    )

    assert hasattr(module, "ensure_preconditions"), (
        "differential probe must expose ensure_preconditions for the pytest corpus path"
    )
    seen.clear()
    admission_seen.clear()
    seen_before_first.clear()
    compared.clear()
    hook_verdicts.clear()
    decoder_verdicts.clear()
    monkeypatch.setattr(module, "_PRECONDITIONS_VERIFIED", set())
    monkeypatch.setattr(module, "expected_verdict", after_decoder_controls)
    monkeypatch.setattr(sys.modules[__name__], "_assert_surface_coverage", lambda rows, surface: None)
    old_profile = sys.getprofile()
    try:
        sys.setprofile(record_decoder)
        test_crossed_corpus(tmp_path / "pytest-precond", request, monkeypatch, "py3.11", "codex-shell")
    finally:
        sys.setprofile(old_profile)
    assert compared, f"test_crossed_corpus must compare the selected corpus row\n{verdict_details()}"
    assert calibrated <= seen_before_first[0][0], (
        f"test_crossed_corpus missing decoder controls before first twin: {calibrated - seen_before_first[0][0]}\n"
        f"{verdict_details(*seen_before_first[0][2:])}"
    )
    assert expected_admission <= seen_before_first[0][1], (
        f"test_crossed_corpus missing admission controls before first twin: "
        f"{expected_admission - seen_before_first[0][1]}\n{verdict_details(*seen_before_first[0][2:])}"
    )
    admission_seen.clear()
    module.ensure_preconditions(sys.executable)
    assert not admission_seen, f"ensure_preconditions must cache verified interpreters\n{verdict_details()}"


@pytest.mark.parametrize("shape", ("alias-collapses", "same-version-two-executables",
                                   "missing-launcher"))
def test_interpreter_resolution(shape, tmp_path, monkeypatch):
    module = differential()
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    if shape == "missing-launcher":
        name = "python3.98765"
        assert shutil.which(name) is None
        result = module.resolve_interpreters([name])
        assert len(result) == 1 and list(result.values()) == [None], result
        assert "98765" in next(iter(result)), "skip must identify the absent launcher"
        return

    def executable(label):
        dest = tmp_path / label
        venv.EnvBuilder(with_pip=False, symlinks=False).create(dest)
        return dest / "bin/python"

    first = executable("first installation")
    second = first if shape == "alias-collapses" else executable("second installation")
    names = ("first-python", "second-python")
    for name, target in zip(names, (first, second)):
        # Each launcher execs the installation it names, preserving its sys.executable.
        launcher = tmp_path / name
        launcher.write_text(f'#!/bin/sh\nexec "{target}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
    result = module.resolve_interpreters(names)
    expected = {"py3.11": first.resolve()}
    if shape == "same-version-two-executables":
        assert not first.samefile(second)
        expected["py3.11-2"] = second.resolve()
    assert {key: Path(path).resolve() for key, path in result.items()} == expected


def shell_case(module, root, host, command):
    if host == "codex":
        payload = {"tool_name": "exec_command", "tool_input": {"cmd": command, "workdir": "."}}
    else:
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": command, "Cwd": "."}}}
    spec = module.CaseSpec("admission-control", host + "-shell", (), "other", payload, {})
    return module.Case(spec, root, frozenset())


def live_root(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    env = _decoder_environment(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, env=env, check=True, timeout=10)
    feature = _decoder_hostile_text(env)
    assert "\n" in feature and "[" in feature
    support.write_state(root, {feature: {"phase": "step5"}})
    (root / ".agents").mkdir()
    (root / ".h-mad").mkdir()
    return root


@pytest.mark.parametrize("side", ("old", "new"))
def test_baseline_extraction_resolves_own_wrapper(side, tmp_path, monkeypatch):
    module = differential()
    commit = BASE if side == "old" else "HEAD"
    tree = module.extract_old_tree(tmp_path / side, commit)
    assert tree.resolve().is_relative_to(tmp_path.resolve())
    for file in ("bin/hmad-dispatch", "scripts/h_mad_tdd_judge.py",
                 "hooks/h-mad-tdd-gate.sh", "hooks/h-mad-codex-tdd-gate.py",
                 "hooks/h-mad-agy-tdd-gate.py"):
        path = "h-mad/" + file
        expected = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT, timeout=10)
        assert (tree / path).read_bytes() == expected, f"{side} must extract its own {file}"
    if side == "old":
        with pytest.raises((ValueError, RuntimeError, subprocess.CalledProcessError)):
            module.extract_old_tree(tmp_path / "missing", "0" * 40)

    case = shell_case(module, live_root(tmp_path), "codex", "pwd")
    wrapper = tree / "h-mad/bin/hmad-dispatch"
    assert os.access(wrapper, os.X_OK)
    verdict = module.run_hook(tree, case, sys.executable)
    assert verdict.decision == "allow", f"{side} wrapper control: {verdict!r}"
    # Make PATH offer a runnable foreign wrapper after the scratch tree's own bin.
    foreign = tmp_path / "foreign-bin"
    foreign.mkdir()
    wrapper.rename(foreign / wrapper.name)
    monkeypatch.setenv("PATH", str(foreign) + os.pathsep + os.environ["PATH"])
    with pytest.raises((AssertionError, RuntimeError, ValueError, FileNotFoundError),
                       match=r"(?i)hmad-dispatch|wrapper"):
        module.run_hook(tree, case, sys.executable)


@pytest.mark.parametrize(("ident", "host"), tuple(itertools.product(INTERPRETERS, ("codex", "agy"))),
                         ids=[f"{i}-{h}" for i in INTERPRETERS for h in ("codex", "agy")])
def test_admission_control(ident, host, tmp_path):
    module = differential()
    python = interpreter(module, ident)
    baseline = module.extract_old_tree(tmp_path / "baseline")
    root = live_root(tmp_path)
    allowance = root / ".h-mad/phase5-shell-allow"
    command = "true"
    for declared in (True, False):
        allowance.write_text(command + "\n" if declared else "", encoding="utf-8")
        for spelling in (command, "hmad-dispatch run --timeout 60 -- " + command):
            case = shell_case(module, root, host, spelling)
            for tree in (baseline, ROOT):
                # Neither side gets a developer-tool cache warmed by fixture setup.
                env = {"TMPDIR": tempfile.mkdtemp(dir=tmp_path)}
                cold_case = case._replace(spec=case.spec._replace(env=env))
                verdict = module.run_hook(tree, cold_case, python)
                context = f"{ident} {host} {tree}: {spelling!r}, declared={declared}"
                assert verdict.decision == ("allow" if declared else "deny"), (
                    f"{context}: {verdict!r}"
                )
                if not declared:
                    assert verdict.kind == ("" if host == "codex" else "shell-not-admitted"), (
                        f"{context}: {verdict!r}"
                    )


def test_oracle_imports_no_tree_module(tmp_path, monkeypatch):
    loader = importlib.machinery.SourceFileLoader
    load = loader.exec_module

    def check_origin(self, module):
        path = Path(self.path).resolve()
        assert path.parent.parts[-2:] not in {("h-mad", "hooks"), ("h-mad", "scripts")}, (
            f"oracle loaded a tree module by path: {path}"
        )
        return load(self, module)

    monkeypatch.delitem(sys.modules, "differential", raising=False)
    monkeypatch.setattr(loader, "exec_module", check_origin)
    module = differential()
    names = {path.stem for folder in ("scripts", "hooks")
             for path in (ROOT / "h-mad" / folder).rglob("*.py")}
    for node in ast.walk(ast.parse(PROBE.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            parts = [part for alias in node.names for part in alias.name.split(".")]
        elif isinstance(node, ast.ImportFrom):
            parts = (node.module or "").split(".") + [alias.name for alias in node.names]
        else:
            continue
        assert not names.intersection(parts), f"oracle imports tree module at line {node.lineno}"

    # Observe which tree actually answers the oracle, including its forwarded interpreter.
    row = named(module, "excluded-alone", "codex-shell")
    real_run = module.run_hook
    calls = []
    trees = []

    def old_side_only(tree, case, python):
        hook = Path(tree) / "h-mad/hooks/h-mad-codex-tdd-gate.py"
        assert hook.resolve().is_relative_to(tmp_path.resolve()), f"oracle ran {hook}"
        old_hook = subprocess.check_output(
            ["git", "show", f"{BASE}:h-mad/hooks/{hook.name}"], cwd=ROOT, timeout=10)
        assert hook.read_bytes() == old_hook
        assert python == sys.executable
        calls.append(case.spec.surface)
        trees.append(Path(tree).resolve())
        return real_run(tree, case, python)

    monkeypatch.setattr(module, "run_hook", old_side_only)
    result = module.expected_verdict(row, sys.executable, frozenset(), tmp_path / "oracle", False)
    assert calls and set(calls) == {row.surface}, "old hook must supply the oracle answer"
    assert result.decision == "deny", f"excluded live copy still gates the baseline shell: {result!r}"

    # A sibling directory named 'baseline' extracted from another commit or holding
    # altered bytes must never be adopted by _oracle_baseline.
    head_decoy = module.extract_old_tree(tmp_path / "head-case/baseline", "HEAD")
    trees.clear()
    head_verdict = module.expected_verdict(
        row, sys.executable, frozenset(), tmp_path / "head-case/oracle", False,
    )
    assert trees and head_decoy.resolve() not in trees, (
        "oracle adopted a sibling baseline directory extracted from HEAD instead of 7a3cca48"
    )
    assert head_verdict.decision == "deny", f"HEAD decoy control: {head_verdict!r}"

    tampered = module.extract_old_tree(tmp_path / "tampered-case/baseline", BASE)
    (tampered / "h-mad/hooks/h-mad-codex-tdd-gate.py").write_bytes(
        b"#!/usr/bin/env python3\nraise SystemExit(0)\n"
    )
    trees.clear()
    tampered_verdict = module.expected_verdict(
        row, sys.executable, frozenset(), tmp_path / "tampered-case/oracle", False,
    )
    assert trees and tampered.resolve() not in trees, (
        "oracle adopted a tampered baseline directory without verifying 7a3cca48 content"
    )
    assert tampered_verdict.decision == "deny", f"tampered baseline control: {tampered_verdict!r}"

    genuine = module.extract_old_tree(tmp_path / "genuine-case/baseline", BASE)
    trees.clear()
    genuine_verdict = module.expected_verdict(
        row, sys.executable, frozenset(), tmp_path / "genuine-case/oracle", False,
    )
    assert trees == [genuine.resolve()], "oracle must adopt a verified 7a3cca48 baseline extraction"
    assert genuine_verdict.decision == "deny", f"verified baseline control: {genuine_verdict!r}"


# Host decoder controls


def _decoder_baseline(destination, env):
    destination.mkdir()
    archive = subprocess.run(
        ["git", "archive", BASE, "h-mad/hooks", "h-mad/scripts", "h-mad/bin"],
        cwd=ROOT, env=env, capture_output=True, check=True, timeout=30,
    )
    subprocess.run(
        ["tar", "-xf", "-", "-C", str(destination)],
        input=archive.stdout, env=env, capture_output=True, check=True, timeout=30,
    )
    return destination / "h-mad"


def _decoder_environment(tmp_path):
    return {
        name: value
        for name, value in support.hermetic_env(
            HOME=str(tmp_path / "home"), HMAD_STUB_HOSTILE="all", PYTHONPATH="", PYTHONNOUSERSITE="1",
            PYTHONDONTWRITEBYTECODE="1",
        ).items()
        if not name.startswith("GIT_")
        and (not name.startswith("HMAD_STUB_") or name == "HMAD_STUB_HOSTILE")
    }


def _decoder_hostile_text(env):
    result = subprocess.run(
        [str(ROOT / "h-mad/tests/stubs/orca"), "worktree", "set", "comment", "fixture"],
        env=env, capture_output=True, check=True, text=True, timeout=10,
    )
    return json.loads(result.stdout)["result"]["worktree"]["comment"]


def _decoder_control(package, tmp_path, host, control, env, hostile):
    root = tmp_path.resolve() / "repo"
    root.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--quiet", str(root)],
        env=env, capture_output=True, check=True, timeout=10,
    )
    (root / ".agents").mkdir()
    subject = root / "shared" / f"{hostile.replace('/', '∕')}.py"
    subject.parent.mkdir()
    subject.touch()
    if control in ("malformed-state", "kindless"):
        support.write_state(root, {}).write_text(hostile, encoding="utf-8")
    elif control in ("judge-error", "production"):
        support.write_state(root, {hostile: {"phase": "step5"}})

    write = {"tool_name": "Write", "tool_input": {"file_path": str(subject)}}
    shell = {"tool_name": "exec_command", "tool_input": {"cmd": "pwd", "workdir": str(root)}}
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    (shim_dir / "git").symlink_to(support.hook_git(env["PATH"]))
    (shim_dir / "python3").symlink_to(sys.executable)
    hook = package / "hooks" / f"h-mad-{host}-tdd-gate.py"
    cwd = root
    if host == "claude":
        launcher = "bash"
        argv = [launcher, str(package / "hooks/h-mad-tdd-gate.sh")]
        env = dict(env, CLAUDE_PROJECT_DIR=str(root))
        payload = write
    elif host == "codex":
        launcher = "python3"
        argv = [launcher, str(hook)]
        env = dict(env, CODEX_PROJECT_DIR=str(root))
        if control == "judge-error":
            payload = {
                "tool_name": "apply_patch",
                "tool_input": {"patch": f"*** Add File: kind=operand\t{hostile}"},
            }
        else:
            payload = write if control == "production" else shell
    else:
        launcher = "python3"
        argv = [str(hook)]
        cwd = root / ".agents"
        tool, args = (
            ("write_to_file", {"TargetFile": str(subject)}) if control == "production"
            else ("run_command", {"CommandLine": "pwd", "Cwd": str(root)})
        )
        payload = {"toolCall": {"name": tool, "args": args}}

    if control == "malformed":
        shim = shim_dir / launcher
        if shim.is_symlink():
            shim.unlink()
        shim.write_text("#!/bin/sh\nprintf '%s\\n' 'broken hook answer {'\n", encoding="utf-8")
        shim.chmod(0o755)
    env = dict(env, PATH=os.pathsep.join((str(package / "bin"), str(shim_dir), env["PATH"])))
    return subprocess.run(
        argv, cwd=cwd, env=env, input=json.dumps(payload), capture_output=True,
        check=False, text=True, timeout=15,
    )


@pytest.mark.parametrize(
    "host, answer",
    [
        pytest.param(host, answer, id=f"{host}-{answer}")
        for host in ("claude", "codex", "agy")
        for answer in ("allow", "deny", "malformed")
    ],
)
def test_host_decoder_controls(tmp_path, host, answer):
    env = _decoder_environment(tmp_path)
    package = _decoder_baseline(tmp_path / "baseline", env)
    hostile = _decoder_hostile_text(env)
    if answer == "deny":
        controls = {
            "claude": (("malformed-state", "judge-error", "BLOCK kind=judge-error:"),),
            "codex": (
                ("judge-error", "judge-error", "kind=judge-error"),
                ("production", "test-missing", "kind=test-missing;"),
                ("kindless", "", "H-MAD state is unreadable"),
            ),
            "agy": (("production", "test-missing", "kind=test-missing"),),
        }[host]
    else:
        controls = ((answer, "", ""),)
    expected_decision = "invalid" if answer == "malformed" else answer
    raw_controls = []
    for control, kind, reason_fragment in controls:
        result = _decoder_control(package, tmp_path / control, host, control, env, hostile)
        if answer == "malformed":
            assert result.stdout == "broken hook answer {\n" and result.returncode == 0, (
                f"{host} malformed launcher control: {result!r}"
            )
        if host == "agy" and answer == "allow":
            assert json.loads(result.stdout) == {"decision": "allow"}, f"agy allow control: {result!r}"
        if reason_fragment:
            assert reason_fragment in result.stdout, f"{host} {control} baseline: {result!r}"
        raw_controls.append((control, kind, reason_fragment, result))

    for control, kind, reason_fragment, result in raw_controls:
        outcome = support.host_decision(host, result)
        details = (f"{host} {control}: {outcome!r}, "
                   f"stdout={result.stdout!r}, stderr={result.stderr!r}")
        assert (outcome.decision, outcome.kind) == (expected_decision, kind), (
            f"decoder expected {(expected_decision, kind)!r}, got {details}"
        )
        if reason_fragment:
            assert reason_fragment in outcome.reason, details
        if host == "codex" and control == "judge-error":
            assert "kind=operand" in outcome.reason, details
            assert outcome.reason.endswith("kind=judge-error"), details
        if host == "codex" and control == "kindless":
            assert "kind=" not in outcome.reason, details


# Typed oracle controls

TYPED_CROSSES = {
    "excluded-alone": ("codex-shell", "allow", ""),
    "excluded-beside-live-root": ("codex-shell", "deny", ""),
    "nested-beside-live-root": ("codex-shell", "deny", ""),
    "nested-target-inside": ("codex-write", "deny", "test-missing"),
    "nested-in-excluded-tree": ("codex-write", "deny", "test-missing"),
    "nested-below-fixtures": ("codex-write", "deny", ""),
    "variable-beside-live-root": ("codex-shell", "deny", ""),
}
ISOLATED_CONTROLS = {
    "D1-control": "allow",
    "D2-control": "allow",
    "D3-control": "allow",
    "D4-control": "deny",
}


@pytest.mark.parametrize(
    "name", (*ISOLATED_CONTROLS, *(f"presence-{kind}" for kind in PRESENCE), *TYPED_CROSSES),
)
def test_oracle_typed_verdicts(name, tmp_path):
    module = differential()
    paths = module.resolve_interpreters()
    assert set(INTERPRETERS) <= paths.keys(), "oracle controls require explicit interpreter ids"
    available = {key: paths[key] for key in INTERPRETERS if paths[key] is not None}
    if not available:
        pytest.skip("no supported interpreter launcher is available for typed oracle verdicts")

    isolated = name in ISOLATED_CONTROLS
    is_presence_control = name.startswith("presence-")
    surface, decision, kind = TYPED_CROSSES.get(
        name, ("codex-shell", ISOLATED_CONTROLS.get(name, "deny"), ""),
    )
    spec = named(module, name, surface)
    if is_presence_control and name.startswith("presence-case-variant-"):
        lower = tmp_path / "caseprobe"
        lower.touch()
        if not (tmp_path / "CASEPROBE").exists():
            decision = "allow"

    if name == "presence-docs-symlink":
        initial = module.build_case(spec, tmp_path / "symlink-original")
        assert stat.S_ISLNK((initial.root / "docs").lstat().st_mode), (
            "docs-symlink control must start with a symlink"
        )
        expected_bytes = (initial.root / "docs/.bkit-memory.json").read_bytes()
        twin = module.build_twin(spec, tmp_path / "symlink-twin", ALL_CLASSES, False)
        docs = twin.root / "docs"
        memory = docs / ".bkit-memory.json"
        assert "docs" in os.listdir(twin.root) and stat.S_ISDIR(docs.lstat().st_mode), (
            "D4 must canonicalize symlinked docs to a real directory"
        )
        assert ".bkit-memory.json" in os.listdir(docs) and stat.S_ISREG(memory.lstat().st_mode), (
            "D4 must put the state in a canonical regular file"
        )
        assert memory.read_bytes() == expected_bytes, "D4 must preserve readable state text"

    if isolated:
        label = name.split("-", 1)[0]
        neighbour_spec = named(module, f"{label}-neighbour", surface)
        original = module.build_case(spec, tmp_path / "original")
        neighbour = module.build_case(neighbour_spec, tmp_path / "neighbour")
        assert original.labels == frozenset({label}), f"{name} must isolate {label}"
        assert not neighbour.labels, f"{neighbour_spec.name} must sit outside D1 through D7"
        old_tree = module.extract_old_tree(tmp_path / "baseline")
        changed = False
        comparisons = {}

    for python_id, executable in available.items():
        scratch = tmp_path / python_id
        scratch.mkdir()
        verdict = module.expected_verdict(spec, executable, ALL_CLASSES, scratch)
        assert (verdict.decision, verdict.kind) == (decision, kind), (
            f"{name} on {python_id} requires {(decision, kind)}, got {verdict!r}"
        )
        if name == "nested-target-inside":
            for variant in ("nested-in-excluded-tree", "nested-below-fixtures"):
                variant_surface, variant_decision, variant_kind = TYPED_CROSSES[variant]
                variant_scratch = tmp_path / f"{python_id}-{variant}"
                variant_scratch.mkdir()
                nested = module.expected_verdict(
                    named(module, variant, variant_surface), executable, ALL_CLASSES,
                    variant_scratch,
                )
                assert (nested.decision, nested.kind) == (variant_decision, variant_kind), (
                    f"{variant} on {python_id} must retain the nested root after outer filtering: {nested!r}"
                )
        if isolated:
            baseline = module.run_hook(old_tree, original, executable)
            assert baseline.decision in {"allow", "deny"}, f"{name} baseline is malformed: {baseline!r}"
            comparisons[python_id] = (baseline, verdict)
            changed |= baseline.decision != verdict.decision
            neighbour_scratch = scratch / "neighbour-oracle"
            neighbour_scratch.mkdir()
            unchanged = module.expected_verdict(
                neighbour_spec, executable, ALL_CLASSES, neighbour_scratch,
            )
            before = module.run_hook(old_tree, neighbour, executable)
            assert (before.decision, before.kind) == (unchanged.decision, unchanged.kind) == (
                "deny", "",
            ), (f"{neighbour_spec.name} on {python_id} must retain its kindless refusal: "
                f"baseline={before!r}, twin={unchanged!r}")

    if isolated:
        assert changed, (
            f"{name} must change the baseline decision on a supported interpreter: {comparisons!r}"
        )


# Corpus coverage and comparison

STATE_PATH = Path("docs/.bkit-memory.json")
MALFORMED_SHAPES = (
    "inaccessible-docs", "unparsable-json", "invalid-utf8", "deep-json", "fifo",
    "directory-in-place", "not-object", "state-not-object",
    "dangling-link", "looping-link",
)
ORDINARY_STATES = ("absent", "inactive", "live", "unreadable")
STATE_LOCATIONS = ("root", "subproject")
SHELL_OPERATIONS = ("safe", "allowance", "refused")
WRITE_OPERATIONS = ("test", "document", "production", "listed")
TARGET_LOCATIONS = ("inside", "outside", "tmp")


def _assert_surface_coverage(rows, surface):
    """Matrix rows use cross-<state>-<state location>-<call> identifiers."""
    names = [spec.name for spec in rows]
    assert len(names) == len(set(names)), f"{surface}: duplicate corpus case name"
    if surface.endswith("-shell"):
        calls = SHELL_OPERATIONS
    else:
        calls = tuple(f"{op}-{where}" for op, where in
                      itertools.product(WRITE_OPERATIONS, TARGET_LOCATIONS))
    required = {
        f"cross-{state}-{location}-{call}"
        for state, location, call in itertools.product(ORDINARY_STATES, STATE_LOCATIONS, calls)
    }
    required.update(f"presence-{shape}" for shape in PRESENCE)
    required.update(f"malformed-{shape}-{neighbour}" for shape, neighbour in
                    itertools.product(MALFORMED_SHAPES, ("alone", "beside-live")))
    required.update(("excluded-not-object", "excluded-object-not-live"))
    if surface.endswith("-shell"):
        required.add("mention-unknown-program")
    assert required <= set(names), f"{surface}: missing corpus cells {sorted(required - set(names))}"

    # Codex exercises its explicit and inferred root routes for each variable.
    explicit_roots = (False, True) if surface.startswith("codex-") else (False,)
    for variable, explicit in itertools.product(VARIABLES, explicit_roots):
        assert any(
            set(VARIABLES).intersection(spec.env) == {variable}
            and ("CODEX_PROJECT_DIR" in spec.env) == explicit
            for spec in rows
        ), f"{surface}: missing one-variable fixture {variable} (explicit root={explicit})"


def _git_call_recorder(scratch, monkeypatch):
    git = support.hook_git(os.environ["PATH"])
    assert git, "differential fixtures require git"
    log = scratch / "git-calls.jsonl"
    git_shim = scratch / "git"
    git_shim.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        f"with open({str(log)!r}, 'a', encoding='utf-8') as log:\n"
        "    log.write(json.dumps([os.getcwd(), sys.argv[1:]]) + '\\n')\n"
        f"os.execv({git!r}, [{git!r}, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    git_shim.chmod(0o755)
    monkeypatch.setenv("PATH", str(scratch) + os.pathsep + os.environ.get("PATH", ""))
    return git, log


def _assert_git_fixture_effect(case, git, log, variables):
    assert log.is_file(), f"{case.spec.name}: git process evidence was not retained"
    variable, = variables
    clean = support.hermetic_env(LC_ALL="C")
    for name in VARIABLES:
        clean.pop(name, None)
    with_variable = dict(clean, **{variable: str(case.root / case.spec.env[variable])})
    questions = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    inferred = case.spec.surface.startswith("agy-") or (
        case.spec.surface.startswith("codex-") and "CODEX_PROJECT_DIR" not in case.spec.env
    )
    for cwd, args in questions:
        # A streaming question needs its input to be replayable.
        if "--stdin" in args or (inferred and "--show-toplevel" not in args):
            continue
        answers = []
        for env in (clean, with_variable):
            result = subprocess.run(
                [git, *args], cwd=cwd, env=env, capture_output=True, text=True,
                timeout=10, check=False,
            )
            answers.append((result.returncode, result.stdout.strip()))
        if answers[0] != answers[1]:
            return
    pytest.fail(f"{case.spec.name}: {variable} did not change an observed git answer")


def _legacy_records(state_path):
    records = json.loads(state_path.read_text(encoding="utf-8"))["orchestrator_state"]
    assert isinstance(records, dict), f"{state_path}: expected legacy records"
    for record in records.values():
        assert {"implementation_checkout", "phase5_stage"}.isdisjoint(record), (
            f"{state_path}: differential fixtures must use legacy records"
        )
    return records.values()


MALFORMED_STORE_PROBE = """
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
try:
    parsed = json.loads(path.read_text(encoding="utf-8"))
except UnicodeDecodeError:
    print(json.dumps(["invalid-utf8", False, False]))
    raise SystemExit(0)
except json.JSONDecodeError:
    print(json.dumps(["unparsable-json", False, False]))
    raise SystemExit(0)
except RecursionError:
    print(json.dumps(["deep-json", False, False]))
    raise SystemExit(0)

if not isinstance(parsed, dict):
    print(json.dumps(["not-object", False, False]))
    raise SystemExit(0)

records = parsed.get("orchestrator_state", {})
if not isinstance(records, dict):
    print(json.dumps(["state-not-object", False, False]))
    raise SystemExit(0)

active = False
has_new = False
for value in records.values():
    if isinstance(value, dict):
        has_new |= not {"phase5_stage", "implementation_checkout"}.isdisjoint(value)
        active |= value.get("phase") == "step5"
print(json.dumps(["object", active, has_new]))
"""


def _check_malformed_store(path, python):
    mode = path.lstat().st_mode
    if stat.S_ISFIFO(mode):
        return "fifo", False
    if stat.S_ISDIR(mode):
        return "directory-in-place", False
    if stat.S_ISLNK(mode):
        try:
            path.stat()
        except FileNotFoundError:
            return "dangling-link", False
        except OSError as exc:
            assert exc.errno == errno.ELOOP, f"{path}: unexpected link error"
            return "looping-link", False
    assert path.is_file(), f"{path}: unexpected state file type"
    probe = subprocess.run(
        [str(python), "-I", "-c", MALFORMED_STORE_PROBE, str(path)],
        capture_output=True, text=True, timeout=10, check=True,
    )
    kind, active, has_new = json.loads(probe.stdout)
    assert not has_new, f"{path}: differential fixtures must use legacy records"
    return kind, active


def _check_malformed_case(case, python):
    name = case.spec.name.removeprefix("malformed-")
    beside_live = name.endswith("-beside-live")
    shape = name.removesuffix("-beside-live" if beside_live else "-alone")
    stores = []
    for parent, directories, files in os.walk(case.root):
        docs = Path(parent) / "docs"
        if "docs" in directories and stat.S_IMODE(docs.lstat().st_mode) == 0:
            stores.append(("inaccessible-docs", False))
            directories.remove("docs")
        if Path(parent).name == "docs" and STATE_PATH.name in directories + files:
            stores.append(_check_malformed_store(Path(parent) / STATE_PATH.name, python))
    assert sorted(stores) == sorted([(shape, False)] + ([("object", True)] if beside_live else [])), (
        f"{case.spec.name}: malformed state and live neighbour must match their on-disk kinds: {stores}"
    )


def _assert_ordinary_case(case):
    _, state, location, call = case.spec.name.split("-", 3)
    stores = tuple(case.root.rglob(str(STATE_PATH)))
    if state == "absent":
        assert not stores, f"{case.spec.name}: absent state fixture contains stores"
    else:
        assert len(stores) == 1, f"{case.spec.name}: expected one state file"
        in_root = stores[0] == case.root / STATE_PATH
        assert in_root == (location == "root"), f"{case.spec.name}: misplaced state file"
        if state in {"inactive", "live"}:
            active = any(record.get("phase") == "step5" for record in _legacy_records(stores[0]))
            assert active == (state == "live"), f"{case.spec.name}: wrong state activity"
        else:
            with pytest.raises((OSError, UnicodeDecodeError, json.JSONDecodeError)):
                json.loads(stores[0].read_text(encoding="utf-8"))

    payload = case.spec.call
    agy = case.spec.surface.startswith("agy-")
    inputs = payload["toolCall"]["args"] if agy else payload["tool_input"]
    if case.spec.surface.endswith("-shell"):
        command = inputs["CommandLine" if agy else "cmd"]
        allowance = case.root / ".h-mad/phase5-shell-allow"
        listed = allowance.is_file() and command in allowance.read_text(encoding="utf-8").splitlines()
        assert listed == (call == "allowance"), f"{case.spec.name}: wrong shell allowance"
        if call == "safe":
            assert command.split()[0] in {"pwd", "ls", "cat", "grep", "head", "tail", "wc"}, (
                f"{case.spec.name}: expected an ordinary safe command"
            )
    else:
        operation, target_location = call.rsplit("-", 1)
        raw_target = Path(inputs["TargetFile" if agy else "file_path"])
        assert not raw_target.is_absolute(), f"{case.spec.name}: call must be relative to the fixture"
        target = (case.root / raw_target).resolve()
        assert target.is_relative_to(case.root.resolve()) == (target_location == "inside"), (
            f"{case.spec.name}: target is in the wrong location"
        )
        if target_location == "tmp":
            assert target.is_relative_to(Path("/tmp").resolve()), (
                f"{case.spec.name}: expected a target under /tmp"
            )
        if operation in {"test", "production"}:
            assert target.suffix == ".py", f"{case.spec.name}: expected a Python target"
            assert target.name.startswith("test_") == (operation == "test"), (
                f"{case.spec.name}: wrong target file role"
            )


INACCESSIBLE_LSTAT_PROBE = """
import os
import sys

for path in sys.argv[1:]:
    try:
        os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        pass
    except OSError:
        continue
    raise SystemExit(f"lstat must raise an OSError other than absence for {path}")
"""


def _inaccessible_docs(scratch):
    """See the private record."""
    result = []
    for current, dirs, _ in os.walk(scratch, followlinks=False):
        docs = Path(current) / "docs"
        if "docs" in dirs and stat.S_IMODE(docs.lstat().st_mode) == 0:
            result.append(docs)
            dirs.remove("docs")
    return result


def _assert_case_verdict(spec, expected, observed):
    assert expected.decision in {"allow", "deny"}, f"{spec.name}: invalid baseline {expected!r}"
    assert (observed.decision, observed.kind) == (expected.decision, expected.kind), (
        f"{spec.name}: expected {expected!r}, observed {observed!r}"
    )


def _norm_path(value):
    return os.path.normpath(os.fsdecode(os.fspath(value)))


def _collect_build_checks(lstat, popen):
    lstat_paths = {
        _norm_path(call.args[0]) for call in lstat.call_args_list
        if call.args and isinstance(call.args[0], (str, bytes, os.PathLike))
    }
    git_calls = []
    for call in popen.call_args_list:
        if not call.args or not isinstance(call.args[0], (list, tuple)) or not call.args[0]:
            continue
        argv = [os.fsdecode(os.fspath(part)) for part in call.args[0]]
        if Path(argv[0]).name != "git":
            continue
        raw_cwd = call.kwargs.get("cwd")
        cwd = _norm_path(raw_cwd) if raw_cwd is not None else None
        git_calls.append((argv, cwd, call.kwargs.get("env")))
    return lstat_paths, git_calls


def _assert_kind_checked(case, kind, lstat_paths, git_calls):
    family, *parts = kind.split(":")
    if family == "state":
        folder, shape = parts
        project = case.root if folder in {"root", "."} else case.root / folder
        docs = project / ("Docs" if shape == "case-variant-docs" else "docs")
        target = docs / (STATE_PATH.name.upper() if shape == "case-variant-file" else STATE_PATH.name)
        assert _norm_path(target) in lstat_paths, (
            f"{case.spec.name}: missing direct lstat check on {target} for {kind!r}"
        )
        if shape == "docs-symlink":
            assert _norm_path(docs) in lstat_paths, (
                f"{case.spec.name}: missing direct lstat check on {docs} for {kind!r}"
            )
        return
    if family == "call":
        operation, *locations = parts
        session = case.root / "sub" if "session:sub" in case.spec.kinds else case.root
        if case.spec.surface.endswith("-shell"):
            allowance = _norm_path(session / ".h-mad/phase5-shell-allow")
            assert allowance in lstat_paths, (
                f"{case.spec.name}: missing direct lstat check on {allowance} for {kind!r}"
            )
            return
        if locations == ["tmp"]:
            expected = _norm_path(case.root.parent / "tmp")
        else:
            raw = (
                case.spec.call["toolCall"]["args"]["TargetFile"]
                if case.spec.surface == "agy-write"
                else case.spec.call["tool_input"]["file_path"]
            )
            expected = _norm_path(case.root / raw)
        assert expected in lstat_paths, (
            f"{case.spec.name}: missing direct lstat check on {expected} for {kind!r}"
        )
        if operation == "listed":
            _, state_folder, _ = next(k for k in case.spec.kinds if k.startswith("state:")).split(":")
            plan_project = case.root if state_folder in {"root", "."} else case.root / state_folder
            plan_dir = _norm_path(plan_project / "docs/01-plan/features") + os.sep
            assert any(p.startswith(plan_dir) and p.endswith(".impl-plan.md") for p in lstat_paths), (
                f"{case.spec.name}: missing direct lstat check on impl-plan for {kind!r}"
            )
        return
    if family in {"checkout", "session"}:
        rel, = parts
        expected = _norm_path(case.root / rel)
        assert any(
            "rev-parse" in argv[1:] and "--show-toplevel" in argv[1:]
            and (
                cwd == expected
                or ("-C" in argv and argv.index("-C") + 1 < len(argv)
                    and _norm_path(argv[argv.index("-C") + 1]) == expected)
            )
            for argv, cwd, _ in git_calls
        ), f"{case.spec.name}: missing direct git rev-parse check on {expected} for {kind!r}"
        return
    if family == "variable":
        variable, = parts
        expected_val = _norm_path(case.root / case.spec.env[variable])
        assert any(
            "rev-parse" in argv[1:] and "--show-toplevel" in argv[1:]
            and env is not None and variable in env and _norm_path(env[variable]) == expected_val
            for argv, _, env in git_calls
        ), f"{case.spec.name}: missing direct git variable check on {variable} for {kind!r}"
        return
    pytest.fail(f"{case.spec.name}: unhandled builder kind {kind!r}")


def test_builder_checks_each_kind(tmp_path):
    module = differential()
    for name, expected_labels in (
        ("D1-control", {"D1"}), ("D2-control", {"D2"}), ("D3-control", {"D3"}),
        ("presence-regular", set()), ("presence-docs-symlink", {"D4"}),
    ):
        spec = named(module, name, "codex-shell")
        with mock.patch("os.lstat", wraps=os.lstat) as lstat, mock.patch(
            "subprocess.Popen", wraps=subprocess.Popen,
        ) as popen:
            case = module.build_case(spec, tmp_path / name)
        assert case.spec == spec, f"{name}: builder lost the case specification"
        assert case.labels == expected_labels, f"{name}: labels must describe fixture facts"
        lstat_paths, git_calls = _collect_build_checks(lstat, popen)
        for kind in spec.kinds:
            _assert_kind_checked(case, kind, lstat_paths, git_calls)
        if name in {"D1-control", "D2-control"}:
            expected_command = "check-ignore" if name == "D1-control" else "rev-parse"
            assert any(expected_command in argv[1:] for argv, _, _ in git_calls), (
                f"{name}: builder did not verify the kind with git {expected_command}"
            )

    # Visit a representative of every declared kind on both shell and write surfaces,
    # verifying each kind's own direct filesystem or git check on its path.
    available_pythons = {
        ident: path for ident, path in module.resolve_interpreters().items() if path is not None
    }
    observed = set()
    for index, spec in enumerate(module.crossed_corpus()):
        is_shell = spec.surface.endswith("-shell")
        keys = {
            (is_shell, kind) if kind in {"call:scope", "call:variable"} else kind
            for kind in spec.kinds
        }
        additional = keys - observed
        if not additional:
            continue
        inaccessible = any(kind.endswith(":inaccessible-docs") for kind in spec.kinds)
        if os.geteuid() == 0 and inaccessible:
            continue
        scratch = tmp_path / f"kind-{index}"
        try:
            with mock.patch("os.lstat", wraps=os.lstat) as lstat, mock.patch(
                "subprocess.Popen", wraps=subprocess.Popen,
            ) as popen:
                case = module.build_case(spec, scratch)
            lstat_paths, git_calls = _collect_build_checks(lstat, popen)
            for kind in spec.kinds:
                _assert_kind_checked(case, kind, lstat_paths, git_calls)
            if "state:root:deep-json" in spec.kinds:
                for ident, exe in available_pythons.items():
                    observed_shape, _ = _check_malformed_store(case.root / STATE_PATH, exe)
                    assert observed_shape == "deep-json", (
                        f"deep-json fixture parsed as {observed_shape!r} instead of raising "
                        f"RecursionError under {ident}"
                    )
            observed.update(additional)
        finally:
            if inaccessible:
                for docs in _inaccessible_docs(scratch):
                    docs.chmod(0o755)
    assert observed, "corpus must declare builder kinds"


def test_twin_is_built_not_copied(tmp_path):
    module = differential()
    spec = named(module, "presence-regular", "codex-shell")
    original = module.build_case(spec, tmp_path / "original")
    original_file = original.root / STATE_PATH
    original_text = original_file.read_bytes()
    original_file.write_bytes(b"fixture was changed after the first build")
    with mock.patch.object(module, "build_case", wraps=module.build_case) as rebuild:
        twin = module.build_twin(spec, tmp_path / "twin", frozenset(), False)

    rebuild.assert_called_once()
    assert rebuild.call_args.args[0] == spec, "twin must pass the original spec to the builder"
    assert twin.root != original.root, "twin needs its own fixture root"
    assert twin.spec == spec and twin.labels == original.labels, "empty changes preserve the case"
    assert (twin.root / STATE_PATH).read_bytes() == original_text, (
        "twin must reconstruct the original content from the spec"
    )

    # D1, D2 and D3 removals must apply by rule to any store in an excluded,
    # nested-checkout or tests/fixtures directory, not only to _SCOPED_LAYOUTS.
    refused_call = {"tool_name": "exec_command", "tool_input": {"cmd": "false", "workdir": "."}}
    for custom_name, store_rel, extra_kinds, expected_label in (
        ("custom-excluded", "excluded/pkg", (), "D1"),
        ("custom-nested", "vendor/nested", ("checkout:vendor/nested",), "D2"),
        ("custom-fixtures", "tests/fixtures/pkg", (), "D3"),
    ):
        assert custom_name not in module._SCOPED_LAYOUTS
        custom_spec = module.CaseSpec(
            custom_name, "codex-shell",
            (f"state:{store_rel}:live", *extra_kinds, "call:refused"),
            "other", refused_call, {},
        )
        built = module.build_case(custom_spec, tmp_path / f"{custom_name}-orig")
        assert (built.root / store_rel / STATE_PATH).is_file()
        assert built.labels == frozenset({expected_label}), (
            f"{custom_name}: expected label {expected_label}, got {built.labels}"
        )
        scoped_twin = module.build_twin(
            custom_spec, tmp_path / f"{custom_name}-twin", ALL_CLASSES, False,
        )
        assert not os.path.lexists(scoped_twin.root / store_rel / STATE_PATH), (
            f"{custom_name}: {expected_label} removal did not apply outside _SCOPED_LAYOUTS"
        )


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("interpreter_id", INTERPRETERS)
def test_crossed_corpus(tmp_path, request, monkeypatch, interpreter_id, surface):
    module = differential()
    python = interpreter(module, interpreter_id)
    old_tree = module.extract_old_tree(tmp_path / "baseline")
    rows = [spec for spec in module.crossed_corpus() if spec.surface == surface]
    _assert_surface_coverage(rows, surface)
    module.ensure_preconditions(python, old_tree)
    for index, spec in enumerate(rows):
        inaccessible = spec.name.startswith("malformed-inaccessible-docs-")
        if inaccessible and os.geteuid() == 0:
            request.node.user_properties.append((
                "skipped-corpus-case", f"{spec.name}: lstat must raise an OSError other than absence",
            ))
            continue
        scratch = tmp_path / f"cell-{index}"
        scratch.mkdir()
        assert spec.branch in {"arming", "other"}, f"{spec.name}: invalid branch"
        changes = module.CHANGES_IN_FORCE[(surface, spec.branch)]
        lifted = surface == "claude" or surface in module.LEGACY_RAISE_LIFTED
        try:
            case = module.build_case(spec, scratch / "actual")
            assert case.labels <= ALL_CLASSES, f"{spec.name}: invalid differential labels"
            if spec.name.startswith("cross-"):
                _assert_ordinary_case(case)
            if spec.name.startswith("malformed-"):
                _check_malformed_case(case, python)
            if spec.name == "mention-unknown-program":
                assert spec.branch == "arming" and "D6" in case.labels, (
                    f"{spec.name}: arming mention must be labelled D6"
                )
                required = module.expected_verdict(
                    spec, python, ALL_CLASSES, scratch / "mention-required", lifted,
                )
                assert required.decision == "deny", f"{spec.name}: FR-5 mention must be refused: {required!r}"
            if inaccessible:
                directories = _inaccessible_docs(scratch)
                assert directories, f"{spec.name}: missing inaccessible-docs fixture"
                probe = subprocess.run(
                    [python, "-I", "-c", INACCESSIBLE_LSTAT_PROBE,
                     *(str(docs / STATE_PATH.name) for docs in directories)],
                    capture_output=True, text=True, timeout=10, check=False,
                )
                assert probe.returncode == 0, f"{spec.name}: {probe.stderr}"

            expected = module.expected_verdict(spec, python, changes, scratch / "expected", lifted)
            variables = set(VARIABLES).intersection(spec.env)
            if variables:
                with monkeypatch.context() as environment:
                    git, log = _git_call_recorder(scratch, environment)
                    baseline = module.run_hook(old_tree, case, python)
                    actual = module.run_hook(ROOT, case, python)
                if baseline.git_processes or actual.git_processes:
                    _assert_git_fixture_effect(case, git, log, variables)
            else:
                actual = module.run_hook(ROOT, case, python)
            _assert_case_verdict(spec, expected, actual)
            if not case.labels and changes:
                baseline = module.run_hook(old_tree, case, python)
                _assert_case_verdict(spec, baseline, actual)
            if surface == "codex-shell" and spec.name == "excluded-alone":
                wrong = module.expected_verdict(
                    spec, python, changes ^ {"D1"}, scratch / "wrong-twin", lifted,
                )
                assert wrong.decision in {"allow", "deny"} and wrong.decision != actual.decision, (
                    f"{spec.name}: detector requires a well-formed opposite decision: "
                    f"wrong twin={wrong!r}, current={actual!r}"
                )
                with pytest.raises(AssertionError, match=re.escape(spec.name)):
                    _assert_case_verdict(spec, wrong, actual)
        finally:
            if inaccessible:
                for docs in _inaccessible_docs(scratch):
                    docs.chmod(0o755)


# Measurement probe CLIs


def _probe_cli(tmp_path, name, *args):
    path = PROBE.with_name(name + ".py")
    return subprocess.run(
        [sys.executable, "-I", "-B", str(path), *map(str, args)], cwd=tmp_path,
        env=_decoder_environment(tmp_path), capture_output=True, text=True, timeout=180,
    )


def _reading(tmp_path, name, *args):
    result = _probe_cli(tmp_path, name, *args)
    assert result.returncode == 0, f"{name} must return a reading for {args!r}: {result.stderr}"
    return result.stdout.splitlines()


@pytest.mark.parametrize("name", ("discovery_probe", "timing", "pin_census", "mixtures"))
def test_probe_usage_error_exits_2_with_empty_stdout(name, tmp_path, capsys, monkeypatch):
    result = _probe_cli(tmp_path, name, "--unknown-option")
    assert PROBE.with_name(name + ".py").is_file(), f"{name} usage handler missing: {result.stderr}"
    assert (result.returncode, result.stdout) == (2, ""), f"{name} usage error: {result!r}"
    if name == "timing":
        samples = tmp_path / "samples.json"
        samples.write_text("[]", encoding="utf-8")
        result = _probe_cli(tmp_path, name, "--samples", samples)
        assert (result.returncode, result.stdout) == (2, ""), "--samples still requires --old"
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(
                shutil, "which", return_value="/usr/bin/git"), mock.patch.object(
                subprocess, "check_output", return_value="\n"):
            with pytest.raises(FileNotFoundError, match="git"):
                support.hook_git(os.defpath)
    probe = _load_probe(name)
    if name == "pin_census":
        _check_observed_baseline(probe, tmp_path)
    assert probe.main(["--unknown-option"]) == 2
    assert capsys.readouterr().out == ""

    def broken_parser(*args, **kwargs):
        print("partial reading")
        raise KeyError("measurement unavailable")

    monkeypatch.setattr(probe.argparse.ArgumentParser, "parse_args", broken_parser)
    assert probe.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "measurement unavailable" in captured.err

    def interrupted_parser(*args, **kwargs):
        raise SystemExit(1)

    monkeypatch.setattr(probe.argparse.ArgumentParser, "parse_args", interrupted_parser)
    assert probe.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err


def _load_probe(name):
    spec = importlib.util.spec_from_file_location(name, PROBE.with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_observed_baseline(probe, scratch):
    nodes = [
        "h-mad/tests/test_h_mad_wire_pin_gate.py::TestRegistrationWire::test_template_wire_arrow_registers",
        "h-mad/tests/test_hmad_dispatch_exec.py::test_ac_5_6_exec_run_consumes_heartbeat_context_without_child_argv",
        "h-mad/tests/test_hmad_dispatch_exec.py::test_ac_5_8_exec_run_does_not_implicitly_read_heartbeat_env",
    ]
    classes = {
        "root-unlistable": [
            f"test_h_mad_tdd_gate_judge.py::test_mode_000_project_dir_refuses[{variant}]"
            for variant in ("as-on-disk", "mis-cased")
        ],
        "lstat-undecidable": [
            "test_h_mad_agy_tdd_gate.py::test_deny_row_kind[t7-chain-unreadable]",
            "test_h_mad_agy_tdd_gate.py::test_unsearchable_chain_denies_although_the_scan_is_inactive",
            "test_h_mad_codex_tdd_gate_judge.py::test_unsearchable_docs_on_the_chain_denies_although_the_scan_is_inactive",
            "test_h_mad_tdd_gate_judge.py::test_fast_path_defers[unsearchable-docs]",
            *(f"test_h_mad_agy_tdd_gate_differential.py::test_target_differential[chmod000-chain-{status}]"
              for status in ("active", "inactive", "unknown")),
            *("test_h_mad_hook_live_interpreter.py::"
              f"test_a_symlink_loop_target_is_denied_as_unresolvable_not_crashed_or_allowed[{host}]"
              for host in ("codex", "agy")),
        ],
    }
    nodes.extend("h-mad/tests/" + case for cases in classes.values() for case in cases)
    run = subprocess.run

    def select_nodes(argv, **kwargs):
        if argv[1:4] != ["-m", "pytest", "-q"]:
            return run(argv, **kwargs)
        assert all(node.split("::")[0] in argv[4:] for node in nodes)
        result = run([*argv[:4], *nodes], **kwargs)
        assert result.returncode == 0, "\n".join(result.stdout.splitlines()[-6:])
        assert f"{len(nodes)} passed" in result.stdout
        return result

    with mock.patch.object(probe.subprocess, "run", select_nodes):
        directory = scratch / "baseline"
        directory.mkdir()
        rows = probe.reading(directory)
    hits = {
        label: {line.split()[2] for line in rows if line.startswith(f"CENSUS-HIT: {label} ")}
        for label in classes
    }
    for label, cases in classes.items():
        assert {"h-mad/tests/" + case for case in cases} <= hits[label]
    overlap = hits["root-unlistable"] & hits["lstat-undecidable"]
    assert not overlap, f"baseline IDs observed in both census classes: {sorted(overlap)}"


@pytest.mark.parametrize("part", (
    "fx", "fx2", "disc", "ev2", "proto2", "failclosed", "chain", "names", "arming",
))
def test_discovery_probe_part_reads(part, tmp_path):
    root = live_root(tmp_path)
    subject = Path("sub") / "docs" / "n.md"
    (root / subject).parent.mkdir(parents=True)
    (root / subject).write_text(_decoder_hostile_text(_decoder_environment(tmp_path)), encoding="utf-8")
    support.write_state(root / "sub", {})
    args = {
        "fx": (), "fx2": (), "disc": (root, 1), "ev2": (root, "sub"),
        "proto2": (root, subject), "failclosed": ("fc",), "chain": (root, subject, "shared", 1),
        "names": (root,), "arming": (root,),
    }
    lines = _reading(tmp_path, "discovery_probe", part, *args[part])
    assert len(lines) == 1 and lines[0].strip(), f"{part} must print one reading: {lines!r}"
    keys = {
        "fx": "layouts", "fx2": "layouts", "disc": "files errors listed processes seconds wait",
        "ev2": "files errors first processes excluded_listed excluded_state_opened",
        "proto2": "current_ms current_git no-live_ms no-live_git live_ms live_git",
        "chain": "mode files chain_files scan_processes processes",
        "names": "layouts name_counts folds_case",
        "arming": "commands positions mentions controls wrapper_cases",
        "failclosed": "cases baseline head_changed allow_changed required-import_changed",
    }
    assert lines[0].startswith(f"DISCOVERY: part={part} "), lines
    fields = set(re.findall(r"(?:^| )([\w-]+)=\S", lines[0]))
    assert set(keys[part].split()) <= fields, lines
    if part == "failclosed":
        expected = {"cases=44", "baseline=44", "allow_changed=2", "historical_38=not-re-runnable",
                    "allow_H4_detected=1", "allow_CANON1_detected=1",
                    "required-import_H4_detected=0", "required-import_CANON1_detected=0"}
        assert expected <= set(lines[0].split()), lines
        edited = _reading(tmp_path, "discovery_probe", part, "allow", "stub-edited")
        assert "allow_changed=0" in edited[0].split(), edited
    if part == "arming":
        for field in ("commands=54", "executed=54", "safe_comparisons=192", "operator_comparisons=192",
                      "cwd_cases=5", "historical_54=not-re-runnable"):
            assert field in lines[0].split(), lines
        values = dict(word.split("=", 1) for word in lines[0].split() if "=" in word)
        assert int(values["changed"]) > 0 and values["changed"] == values["changed_hits"], lines
    if part in ("fx", "fx2"):
        assert any(
            not path.is_relative_to(root) for path in tmp_path.rglob(".bkit-memory.json")
        ), f"{part} must build its scratch layout"


def test_pin_census_control_logs_every_class(tmp_path, monkeypatch):
    lines = _reading(tmp_path, "pin_census", "--control")
    for case, route in (("unsearchable-parent", "target"), ("looping-docs", "scan")):
        assert [line for line in lines if line.endswith(" " + case)] == [
            f"CENSUS-CONTROL: lstat-undecidable {route} {case}"
        ], case
    assert "CENSUS-CONTROL: lstat-undecidable target" in lines
    assert "CENSUS-CONTROL: lstat-undecidable scan" in lines
    # Each line names the detector and the particular control that reached it.
    hits = {frozenset(re.findall(r"[\w-]+", line)) for line in lines}
    expected = [(label,) for label in ("D1", "D2", "D3", "D5")]
    expected.extend(itertools.product(("D4",), (*PRESENCE, "fifo"), ("scan", "chain")))
    expected.extend(itertools.product(("D6",), ("codex", "agy", "claude"),
                                      ("name", "symlink", "other-checkout")))
    expected.extend(itertools.product(("D6",), ("referent",), ("codex", "agy", "claude")))
    expected.extend(itertools.product(("D6",), ("codex", "agy"), ("position", "mention")))
    expected.extend(itertools.product(("D7",), VARIABLES, ("codex", "agy", "codex-explicit", "claude")))
    expected.extend([("lstat-undecidable",), ("root-unlistable",), ("git-shim",), ("replaced-run",)])
    expected.extend([("lstat-undecidable", "scan"), ("lstat-undecidable", "chain"),
                     ("lstat-undecidable", "target"), ("lstat-undecidable", "referent")])
    expected.extend([("claude-stub",), ("D6", "judge", "name"), ("agy-kinds",),
                     ("shell-refusal",), ("git-root-lookup",)])
    missing = [row for row in expected if not any(set(row) <= hit for hit in hits)]

    probe = _load_probe("pin_census")
    root = tmp_path / "d1"
    root.mkdir()

    def git(*args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    git("init", "-q")
    (root / ".gitignore").write_text(".bkit-memory.json\nignored/\nindexed/\ncommitted/\n")
    for folder in ("ordinary", "ignored/nested", "indexed", "committed"):
        support.write_state(root / folder, {})
    for folder in ("committed", "indexed"):
        (root / folder / "marker").touch()
        git("add", "-f", f"{folder}/marker")
        if folder == "committed":
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
            git("rm", "--cached", "committed/marker")
    shim = tmp_path / "observed-bin"
    shim.mkdir()
    (shim / "git").write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$0.calls"\nexit 1\n')
    (shim / "git").chmod(0o755)
    monkeypatch.setenv("HMAD_CENSUS_GIT", shutil.which("git"))
    import discovery_probe
    monkeypatch.setitem(discovery_probe.GIT_ENV, "PATH", str(shim))
    fields = ("phase", "implementation_checkout", "phase5_stage", "phase5_checkout",
              "autonomous_entry_ts", "xphase", "0phase", "_phase", "éphase")
    field_hits = []
    for field in fields:
        rows = []
        probe.Census(lambda *row: rows.append(row)).shell(
            "codex", f"inspect 'h_mad_state_write.py {field} ='", root, None, False)
        if rows:
            field_hits.append(field)
    assert field_hits == ["phase", "implementation_checkout", "phase5_stage", "éphase"]
    for folder in ("ordinary", "ignored/nested", "indexed", "committed"):
        rows = []
        probe.Census(lambda *row: rows.append(row)).presence(
            root, root / folder / "docs" / probe.STATE, "scan")
        assert (("D1", "scan") in rows) == (folder == "ignored/nested"), (folder, rows)
    calls = shim / "git.calls"
    assert not calls.exists(), calls.read_text()
    detector = probe.Census(lambda *row: pytest.fail(f"unexpected classification: {row}"))
    with mock.patch.object(Path, "lstat", side_effect=OSError(errno.EIO, "read error")):
        with pytest.raises(OSError, match="read error"):
            detector.presence(root, root / "docs" / probe.STATE, "scan")
        with pytest.raises(OSError, match="read error"):
            detector.write_target("codex", root, root / "note.txt")
    assert not missing, f"census control omitted detector hits {missing!r}: {lines!r}"


def _timing_checkouts(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    env = _decoder_environment(tmp_path)

    def git(*args):
        subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True, timeout=20)

    git("init", "-q")
    hostile = _decoder_hostile_text(env)
    (root / "src").mkdir()
    (root / "src/x.py").write_text("pass\n", encoding="utf-8")
    support.write_state(root, {})
    (root / "docs/n.md").write_text(hostile, encoding="utf-8")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
    second = tmp_path / "second checkout"
    git("worktree", "add", "-q", "--detach", str(second), "HEAD")
    return root, second


def _file_hashes(*checkouts):
    return {
        (checkout.name, path.relative_to(checkout)): hashlib.sha256(path.read_bytes()).hexdigest()
        for checkout in checkouts for path in checkout.rglob("*") if path.is_file()
    }


def _assert_timing_cases(lines, hooks, record):
    bias = "TIMING-GIT: resolved toolchain git excludes host launcher overhead per git call"
    assert lines.count(bias) == 1, lines
    summary = [line for line in lines if line.startswith("TIMING:")]
    assert len(summary) == 1, lines
    assert re.fullmatch(r"TIMING: max_added_ms=-?\d+(?:\.\d+)? bound=300", summary[0]), lines
    second = [line for line in lines if line.startswith("TIMING-SECOND-CHECKOUT:")]
    assert len(second) == len(hooks), f"one second-checkout reading per hook: {second}"
    expected = {(hook, target) for hook in hooks for target in ("document", "production", "state-file")}
    expected.update((hook, "shell") for hook in hooks if hook in ("codex", "agy"))
    observed = []
    for line in lines:
        if line in second or line in summary or line == bias:
            continue
        fields = dict(field.split("=", 1) for field in line.split() if "=" in field)
        observed.append((fields["hook"], fields["target"]))
        assert all(float(fields[key]) >= 0 for key in ("old_ms", "new_ms")), line
        if fields["target"] == "shell":
            assert fields.get("record") == record, f"shell must name the measured root state: {line}"
    assert sorted(observed) == sorted(expected), f"wrong bounded hook cases: {lines}"
    for hook in hooks:
        assert sum(f"hook={hook}" in line.split() for line in second) == 1, second


@pytest.mark.parametrize("mode", ("every-hook", "one-hook", "second-checkout-apart"))
def test_timing_probe_prints_its_token(mode, tmp_path):
    if mode == "second-checkout-apart":
        samples = tmp_path / "medians.json"
        samples.write_text(json.dumps([
            {"hook": "claude", "target": target, "old_ms": old, "new_ms": new}
            for target, old, new in (("document", 10, 12), ("production", 30, 47),
                                     ("state-file", 60, 59), ("second-checkout", 4, 991))
        ]), encoding="utf-8")
        lines = _reading(tmp_path, "timing", "--old", tmp_path / "absent",
                         "--hook", "claude", "--samples", samples)
        assert "TIMING: max_added_ms=17 bound=300" in lines, f"largest bounded delta must be 17: {lines}"
        second = [line for line in lines if line.startswith("TIMING-SECOND-CHECKOUT:")]
        assert len(second) == 1 and "added_ms=987" in second[0].split(), second
        assert all("987" not in line for line in lines if line not in second), lines
        return

    old = differential().extract_old_tree(tmp_path / "baseline")
    root, second = _timing_checkouts(tmp_path)
    hooks = ("codex", "agy", "claude") if mode == "every-hook" else ("claude",)
    selection = () if mode == "every-hook" else ("--hook", "claude")
    for record in (("none", "live") if mode == "every-hook" else ("none",)):
        if record == "live":
            key = _decoder_hostile_text(_decoder_environment(tmp_path))
            support.write_state(root, {key: {"phase": "step5", "fixture": "timing read-only"}})
        before = _file_hashes(root, second)
        lines = _reading(tmp_path, "timing", "--old", old, "--repo", root, "--runs", 1, *selection)
        assert _file_hashes(root, second) == before, "--repo timing changed checkout files"
        _assert_timing_cases(lines, hooks, record)
    if mode == "one-hook":
        probe = _load_probe("timing")
        observed = []

        def record_case(diff, hook, session, target, value, *unused):
            if target == probe.SECOND:
                observed.append((session, value.parent))

        args = mock.Mock(old=old, repo=root, runs=1)
        with mock.patch.object(probe, "_bench", record_case):
            probe._measure(args, hooks)
        assert observed == [(root.resolve(), second.resolve())]


@pytest.mark.parametrize("mode", ("identical-trees-pass", "failing-mixture-named", "every-mixture-run"))
def test_mixtures_probe(mode, tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    log = tmp_path / "observations.jsonl"
    # The two versions agree on their own revision. Only a newer value with
    # the older reader accepts the 'compare' case. 'observe' always refuses.
    for tree, revision in ((old, 0), (new, int(mode != "identical-trees-pass"))):
        tree.mkdir()
        (tree / "value.json").write_text(json.dumps(revision), encoding="utf-8")
        (tree / "entry.py").write_text(
            "import json, sys\nfrom pathlib import Path\n"
            f"reader = {revision}\n"
            "value = json.loads(Path(__file__).with_name('value.json').read_text())\n"
            f"with Path({str(log)!r}).open('a') as output:\n"
            "    home = Path.home()\n"
            "    local_home = home.is_dir() and home.is_relative_to(Path.cwd().parent)\n"
            "    print(json.dumps([reader, value, sys.argv[2], local_home]), file=output)\n"
            "sys.exit(0 if sys.argv[1] == 'compare' and value > reader else 1)\n",
            encoding="utf-8",
        )
    hostile = _decoder_hostile_text(_decoder_environment(tmp_path))
    case = "compare" if mode == "failing-mixture-named" else "observe"
    definition = tmp_path / "set.json"
    definition.write_text(json.dumps({
        "name": "toy", "files": ["entry.py", "value.json"], "entry": [sys.executable, "entry.py"],
        "corpus": [{"name": case, "argv": [case, hostile]}],
    }), encoding="utf-8")
    lines = _reading(tmp_path, "mixtures", "--old", old, "--new", new, "--set-file", definition)
    if mode == "failing-mixture-named":
        assert lines == ["MIXTURES: FAIL set=toy mixture=value.json case=compare"], lines
    else:
        assert len(lines) == 1, lines
        assert re.fullmatch(r"MIXTURES: PASS set=toy mixtures=4 cases=[1-9]\d*", lines[0]), lines
    observed = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert observed and all(payload == hostile for _, _, payload, _ in observed), observed
    assert all(local_home for _, _, _, local_home in observed), "each mixture needs its own scratch HOME"
    if mode == "every-mixture-run":
        combinations = {(reader, value) for reader, value, _, _ in observed}
        assert combinations == set(itertools.product(range(2), repeat=2)), (
            f"the entry must run on all four reader/value combinations: {observed!r}"
        )
    if mode == "identical-trees-pass":
        baseline = differential().extract_old_tree(tmp_path / "baseline")
        lines = _reading(tmp_path, "mixtures", "--old", baseline, "--new", ROOT, "--set", "staging")
        assert lines == ["MIXTURES: PASS set=staging mixtures=4 cases=24"], lines
        probe = _load_probe("mixtures")
        args = mock.Mock(old=baseline, new=ROOT, set="staging", set_file=None)
        with mock.patch.object(probe, "_staging", return_value={"review-live-complete": False}):
            assert probe._measure(args, tmp_path) == "MIXTURES: FAIL set=staging mixture=none case=review-live-complete"
        for label, tree in (("old", baseline), ("new", ROOT)):
            work = tmp_path / f"writes-{label}"
            (work / "home").mkdir(parents=True)
            rows = probe._writes(tree, work, pure=True)
            accepted = ("create", "set", "append", "claim", "beat", "release", "drop", "switch")
            refused = ("create-invalid", "set-unknown", "append-type", "claim-owner",
                       "beat-owner", "release-owner", "drop-absent", "switch-extra")
            assert rows == {f"{form}-{op}": op in accepted for form in ("regular", "symlink")
                            for op in (*accepted, *refused)}
    if mode == "every-mixture-run":
        _check_mixture_readings(tmp_path)
    if mode == "failing-mixture-named":
        _check_pure_mixture_answers(tmp_path)


def _check_mixture_readings(tmp_path):
    probe = _load_probe("mixtures")
    diff = differential()
    work = tmp_path / "gate-work"
    work.mkdir()
    (work / "home").mkdir()
    run = subprocess.run
    homes = []

    def observe_hook(argv, **kwargs):
        if len(argv) > 1 and Path(argv[1]).name in {
                "h-mad-codex-tdd-gate.py", "h-mad-agy-tdd-gate.py", "h-mad-tdd-gate.sh"}:
            env = kwargs["env"]
            homes.append(Path(env["HOME"]))
            assert homes[-1].is_dir() and homes[-1].is_relative_to(work)
            assert all(key not in env for key in VARIABLES)
        return run(argv, **kwargs)

    with mock.patch.object(subprocess, "run", observe_hook):
        gates = probe._gates(ROOT, work)
    assert len(homes) == len(gates) == 10
    expected_gates = {case: case.endswith(("-document", "-safe")) for case in gates}
    errors = {case: value for case, value in gates.items() if value != expected_gates[case]}
    work = tmp_path / "invalid-gate"
    work.mkdir()
    with mock.patch.object(diff, "run_hook", return_value=diff.Verdict("invalid", "", 0)):
        invalid = probe._gates(ROOT, work)
    errors.update({case: value for case, value in invalid.items() if value is not None})

    def staging(args, root, home, **env):
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0)
        prompt = root / "prompt.txt"
        stdout = ""
        if root.name.startswith("green-"):
            stdout = "ASSEMBLE-TDD: PASS fixture\nASSEMBLE-TDD: HALT task_not_found\n"
        if root.name == "green-live-complete":
            stdout = "ASSEMBLE-TDD: PASS\n"
        if root.name.startswith("gate-"):
            prompt.symlink_to("missing")
        if root.name.startswith("review-"):
            Path(str(prompt) + ".assembled").touch()
        if root.name.startswith(("gate-", "review-")):
            stdout = "ASSEMBLE-TDD: HALT task_not_found\n"
        return subprocess.CompletedProcess(args, int("absent" in root.name), stdout, "ImportError")

    work = tmp_path / "stage-work"
    with mock.patch.object(probe, "_command", staging):
        stages = probe._staging(ROOT, work)
    for case, actual in stages.items():
        expected = False if case.startswith("red-") else None
        if actual is not expected:
            errors[case] = actual
    assert not errors, errors


def _check_pure_mixture_answers(tmp_path):
    probe = _load_probe("mixtures")
    tree = tmp_path / "mixture-input"
    for folder in ("scripts", "hooks", "references", "bin"):
        (tree / "h-mad" / folder).mkdir(parents=True)
    (tree / probe.WRITER).touch()
    problems = []
    for group, case, wrong in (
            ("writes", "regular-create", False), ("writes", "symlink-drop-absent", True),
            ("gates", "codex-shell-refused", True), ("gates", "claude-document", False),
            ("staging", "green-live-missing-task", True)):
        args = mock.Mock(old=tree, new=tree, set=group, set_file=None)
        with mock.patch.dict(probe.FILES, {group: (probe.WRITER,)}), mock.patch.object(
                probe, "_" + group, return_value={case: wrong}):
            line = probe._measure(args, tmp_path)
        if line != f"MIXTURES: FAIL set={group} mixture=none case={case}":
            problems.append((case, line))

    token = "TDD-IMPLEMENTER: agy chosen=codex switch=codex->agy reason=status"
    versions = (probe.WRITER, probe.JUDGE)
    new = tmp_path / "mixture-new"
    (tree / probe.JUDGE).write_text("old")
    shutil.copytree(tree, new)
    for file in versions:
        (new / file).write_text("new")
    args = mock.Mock(old=tree, new=new, set="writes", set_file=None)

    def write(argv, root, home, **env):
        case = root.name.split("-", 1)[1]
        source = argv[1].parents[2]
        mixed = (source / probe.JUDGE).read_text() != (source / probe.WRITER).read_text()
        path = root / "docs/.bkit-memory.json"
        if mixed and case == "set-unknown":
            if scenario == "missing-store":
                path.unlink()
            if scenario == "bare-ok":
                return subprocess.CompletedProcess(argv, 1, "STATE-WRITE: OK\n", "")
        if case.startswith("switch"):
            if mixed and case == "switch" and scenario == "partial-record":
                path.write_text("{}")
                return subprocess.CompletedProcess(argv, 0, token + "\n", "")
            if mixed and scenario == "record-failed":
                return subprocess.CompletedProcess(argv, 0, "fixture starting\n" + token + " record=failed\n", "")
            if case == "switch" and (not mixed or scenario == "changed-field"):
                data = json.loads(path.read_bytes())
                if mixed:
                    data["orchestrator_state"]["fixture"]["agy_status"] = "unavailable"
                data["orchestrator_state"]["fixture"]["implementer_switch"] = dict(
                    ts="now", reason="status", **{"from": "codex", "to": "agy"})
                path.write_text(json.dumps(data))
                return subprocess.CompletedProcess(argv, 0, token + "\n", "")
            if case == "switch-extra" and not mixed and scenario != "pure-error":
                return subprocess.CompletedProcess(argv, 0, token + " record=failed\n", "")
            stdout = "fixture starting\n" if mixed else ""
            return subprocess.CompletedProcess(argv, 1, stdout, "ImportError: fixture unavailable\n")
        stdout = "STATE-WRITE: OK feature=fixture" if "-" not in case else ""
        return subprocess.CompletedProcess(argv, 0, stdout, "")

    (tree / probe.WRITER).write_text("old")
    with mock.patch.dict(probe.FILES, {"writes": versions}), mock.patch.object(probe, "_command", write):
        success = "MIXTURES: PASS set=writes mixtures=4 cases=32"
        mixed_failure = f"MIXTURES: FAIL set=writes mixture={probe.WRITER} case=regular-"
        for scenario, expected in (
                ("pure-error", "MIXTURES: FAIL set=writes mixture=none case=regular-switch-extra"),
                ("exception", success), ("record-failed", success),
                ("partial-record", mixed_failure + "switch"),
                ("changed-field", mixed_failure + "switch"),
                ("missing-store", mixed_failure + "set-unknown"),
                ("bare-ok", mixed_failure + "set-unknown")):
            try:
                line = probe._measure(args, tmp_path)
            except (KeyError, OSError) as exc:
                line = type(exc).__name__
            if line != expected:
                problems.append((scenario, expected, line))
    assert not problems, problems
