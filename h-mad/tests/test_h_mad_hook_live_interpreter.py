"""Smoke the two TDD gate hooks under the interpreter they are really launched with.

Skill-candidates row "hook-tests-run-under-the-wrong-interpreter": the test
support drives the hooks with `sys.executable` (3.11 here) while the live
launch resolves `python3` from PATH (3.15 here). `Path.resolve()` on a symlink
loop raises on 3.12 and earlier and returns on 3.13 and later, so a test could
pass for the wrong reason. This file launches the hooks the way a host does and
lets PATH decide:

  * `h-mad-agy-tdd-gate.py` is executable; it is EXECed directly, so its
    `#!/usr/bin/env python3` shebang picks the interpreter.
  * `h-mad-codex-tdd-gate.py` is mode 100644 in git, and the docs launch it as
    `python3 <path>` (codex-runtime.md), so PATH's `python3` picks it there.

Every payload needs no pytest in the hook's interpreter. A PATH shim named
`python3` logs each launch and then execs the real PATH `python3`: the control
test reads that log, so "the interpreter under test is the PATH one" is
measured, not assumed. The file skips, naming the interpreter, when `python3`
is absent or is `sys.executable`, since the run would then prove nothing new.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tdd_gate_support import hermetic_env, write_state

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
CODEX_GATE = HOOKS / "h-mad-codex-tdd-gate.py"
AGY_GATE = HOOKS / "h-mad-agy-tdd-gate.py"
LIVE = shutil.which("python3")


def _skip_reason() -> str | None:
    if LIVE is None:
        return ("`python3` is not on PATH, so there is no live-hook interpreter to test "
                f"(sys.executable={sys.executable})")
    if os.path.realpath(LIVE) == os.path.realpath(sys.executable):
        return (f"PATH `python3` ({LIVE}) is sys.executable ({sys.executable}): this run "
                "would repeat the suite's interpreter and prove nothing new")
    return None


needs_live = pytest.mark.skipif(_skip_reason() is not None, reason=_skip_reason() or "")

PRODUCTION = "hematology-paper-writer/tools/w.py"
TEST = "hematology-paper-writer/tests/test_w.py"
LOOP = "hematology-paper-writer/tools/loop/x.py"
HOOKS_UNDER_TEST = ("codex", "agy")


def _root(tmp_path: Path) -> Path:
    """An active step-5 feature in a hostile-named repository, with a symlink loop."""
    root = tmp_path / "repo Ω [*] 'q'"
    root.mkdir()
    env = {k: v for k, v in hermetic_env().items() if not k.startswith("GIT_")}
    subprocess.run(["git", "init", "--quiet", str(root)], check=True, env=env,
                   capture_output=True, timeout=30)
    (root / ".agents").mkdir()
    write_state(root, {"feat": {"phase": "step5"}})
    tools = root / "hematology-paper-writer" / "tools"
    tools.mkdir(parents=True)
    os.symlink("loop", tools / "loop")  # a self-referential link: resolve() hits ELOOP
    return root


def _shim(tmp_path: Path) -> tuple[Path, Path]:
    """A PATH-first `python3` that records each launch, then runs the real PATH one."""
    bin_dir, log = tmp_path / "shimbin", tmp_path / "launches.log"
    bin_dir.mkdir()
    shim = bin_dir / "python3"
    shim.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$0" >> "{log}"\nexec "{LIVE}" "$@"\n',
                    encoding="utf-8")
    shim.chmod(0o755)
    return bin_dir, log


def _launch(which: str, root: Path, bin_dir: Path, target: str) -> subprocess.CompletedProcess:
    base = hermetic_env(HMAD_STUB_HOSTILE="all", PYTHONPATH="", PYTHONNOUSERSITE="1")
    env = {k: v for k, v in base.items() if not k.startswith("GIT_")}
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    if which == "codex":
        env["CODEX_PROJECT_DIR"] = str(root)
        argv = [str(CODEX_GATE)] if os.access(CODEX_GATE, os.X_OK) else ["python3", str(CODEX_GATE)]
        payload = {"tool_name": "apply_patch", "tool_input": {"patch": f"*** Update File: {target}\n"}}
        cwd = root
    else:
        argv = [str(AGY_GATE)]  # executed directly: the shebang decides
        payload = {"toolCall": {"name": "write_to_file", "args": {"TargetFile": target}}}
        cwd = root / ".agents"
    return subprocess.run(argv, input=json.dumps(payload), capture_output=True, text=True,
                          cwd=cwd, env=env, timeout=120, check=False)


def _decide(which: str, proc: subprocess.CompletedProcess) -> tuple[str, str]:
    """(allow|deny|invalid, reason) from the hook's own output contract."""
    out = proc.stdout.strip()
    if proc.returncode != 0:
        return "invalid", f"rc={proc.returncode} stdout={out!r} stderr={proc.stderr!r}"
    if which == "codex" and out in ("", "{}"):
        return "allow", ""
    try:
        obj = json.loads(out)
        if which == "codex":
            body = obj["hookSpecificOutput"]
            return ("deny", body["permissionDecisionReason"]) \
                if body["permissionDecision"] == "deny" else ("invalid", out)
        if obj["decision"] == "allow":
            return "allow", ""
        if obj["decision"] == "deny":
            return "deny", obj["reason"]
    except (ValueError, KeyError, TypeError):
        pass
    return "invalid", f"stdout={out!r} stderr={proc.stderr!r}"


def _live_version() -> str:
    out = subprocess.run([LIVE, "--version"], capture_output=True, text=True, check=False)
    return (out.stdout + out.stderr).strip()


@needs_live
@pytest.mark.parametrize("which", HOOKS_UNDER_TEST)
def test_the_hook_runs_under_path_python3_not_sys_executable(tmp_path: Path, which: str) -> None:
    """Positive control: the launch went through PATH's `python3`, once."""
    root = _root(tmp_path)
    bin_dir, log = _shim(tmp_path)

    verdict, reason = _decide(which, _launch(which, root, bin_dir, TEST))

    launches = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    message = (f"{which} hook: expected one launch through the PATH shim over {LIVE} "
               f"({_live_version()}), not sys.executable {sys.executable}; got {launches}")
    assert launches == [str(bin_dir / "python3")], message
    assert verdict == "allow", f"{message}; decision {verdict}: {reason}"


@needs_live
@pytest.mark.parametrize("which", HOOKS_UNDER_TEST)
def test_a_test_file_write_is_allowed_under_the_live_interpreter(tmp_path: Path, which: str) -> None:
    root = _root(tmp_path)
    bin_dir, _ = _shim(tmp_path)

    verdict, reason = _decide(which, _launch(which, root, bin_dir, TEST))

    assert verdict == "allow", f"{which} under {LIVE} ({_live_version()}): {reason}"


@needs_live
@pytest.mark.parametrize("which", HOOKS_UNDER_TEST)
def test_a_production_write_with_no_failing_test_is_denied_under_the_live_interpreter(
        tmp_path: Path, which: str) -> None:
    root = _root(tmp_path)
    bin_dir, _ = _shim(tmp_path)

    verdict, reason = _decide(which, _launch(which, root, bin_dir, PRODUCTION))

    assert verdict == "deny", f"{which} under {LIVE} ({_live_version()}): {verdict} {reason}"
    assert "failing test before " + PRODUCTION in reason, reason


@needs_live
@pytest.mark.parametrize("which", HOOKS_UNDER_TEST)
def test_a_symlink_loop_target_is_denied_as_unresolvable_not_crashed_or_allowed(
        tmp_path: Path, which: str) -> None:
    """The version-sensitive case: `Path.resolve()` raises on a loop before 3.13, returns after.

    Whichever the live interpreter does, the public payload must end in a clean
    deny that names the target unresolvable; an allow, a traceback or a non-zero
    exit means the hook's answer depends on the interpreter version.
    """
    root = _root(tmp_path)
    bin_dir, _ = _shim(tmp_path)

    verdict, reason = _decide(which, _launch(which, root, bin_dir, LOOP))

    detail = f"{which} under {LIVE} ({_live_version()}): {verdict} {reason}"
    assert verdict == "deny", detail
    assert "unresolvable" in reason, detail
    assert "Traceback" not in reason and "RuntimeError" not in reason, detail


def _run_this_file(tmp_path: Path, path_dirs: list[Path]) -> subprocess.CompletedProcess:
    env = {**hermetic_env(), "PATH": os.pathsep.join(str(d) for d in path_dirs),
           "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rs", "-q",
         "-k", "test_a_test_file_write_is_allowed or test_the_hook_runs_under",
         str(Path(__file__).resolve())],
        capture_output=True, text=True, env=env, cwd=tmp_path, timeout=300, check=False)


def test_the_live_tests_skip_naming_the_interpreter_when_python3_is_sys_executable(
        tmp_path: Path) -> None:
    """Otherwise the live-interpreter run would repeat the suite's own and prove nothing."""
    bin_dir = tmp_path / "samebin"
    bin_dir.mkdir()
    os.symlink(sys.executable, bin_dir / "python3")

    proc = _run_this_file(tmp_path, [bin_dir, Path("/usr/bin"), Path("/bin")])

    out = proc.stdout + proc.stderr
    assert "4 skipped" in out and "passed" not in out, out
    assert f"is sys.executable ({sys.executable})" in out, out


def test_the_live_tests_skip_naming_the_interpreter_when_python3_is_absent(
        tmp_path: Path) -> None:
    empty = tmp_path / "emptybin"
    empty.mkdir()

    proc = _run_this_file(tmp_path, [empty])

    out = proc.stdout + proc.stderr
    assert "4 skipped" in out and "passed" not in out, out
    assert "`python3` is not on PATH" in out and sys.executable in out, out
