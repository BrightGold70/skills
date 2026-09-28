"""Shared test support for codex-tdd-gate-defects (not collected: no test_ prefix)."""
from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DROPPED_ENV = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CODEX_UNAVAILABLE", "CODEX_PROJECT_DIR")


def hermetic_env(**extra: str) -> dict[str, str]:
    """os.environ minus every CLAUDE* name and DROPPED_ENV, then `extra`."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE") and k not in DROPPED_ENV}  # M:E1
    env.update(extra)
    return env


def write_state(directory: Path, records: dict) -> Path:
    path = directory / "docs" / ".bkit-memory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"orchestrator_state": records}), encoding="utf-8")
    return path


def write_plan(state_dir: Path, key: str, text: str) -> Path:
    path = state_dir / "docs" / "01-plan" / "features" / f"{key}.impl-plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build_venv(dest: Path, *, with_pytest: bool) -> Path:
    argv = [sys.executable, "-m", "venv", "--without-pip"]
    if with_pytest:
        argv.append("--system-site-packages")
    argv.append(str(dest))
    subprocess.run(argv, check=True, stdin=subprocess.DEVNULL, timeout=60.0, env=hermetic_env())
    python = dest / "bin" / "python"
    probe = subprocess.run(
        [str(python), "-c", "import pytest"], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=60.0, env=hermetic_env(), check=False,
    )
    if with_pytest:
        assert probe.returncode == 0, (
            "builder's base interpreter has no pytest; run the suite under a base "
            "interpreter (sys.prefix == sys.base_prefix): " + probe.stderr
        )
    else:
        assert probe.returncode != 0, "isolated venv unexpectedly has pytest"
    return python


def _shell_script(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def fake_venv(directory: Path, sh_body: str) -> Path:
    venv = directory / ".venv"
    venv.mkdir(parents=True, exist_ok=True)
    (venv / "pyvenv.cfg").write_text("home = fixture\n", encoding="utf-8")
    return _shell_script(venv / "bin" / "python", sh_body)


def marker_shim(python: Path, marker: Path) -> Path:
    return _shell_script(
        python,
        f"printf '%s\\n' \"$0\" >> {shlex.quote(str(marker))}\n"
        f"exec {shlex.quote(sys.executable)} \"$@\"",
    )


def sleeper(path: Path, pidfile: Path, seconds: int) -> Path:
    return _shell_script(path, f"sleep {int(seconds)} &\necho $! > {shlex.quote(str(pidfile))}\nwait")


@dataclass(frozen=True)
class CorpusRow:
    name: str
    root: Path
    cwd: Path
    command: str
    expected_new: str


def shell_corpus(tmp: Path, scripts_dir: Path) -> list[CorpusRow]:
    """Build the 251-cell shell-policy differential from one real venv tree."""
    def argv_for(root: Path) -> tuple[tuple[str, str, bool], ...]:
        return (
            ("pytest", "-m pytest tests/test_x.py", True),
            ("c-write", '-c "open(\'x\',\'w\')"', False),
            ("pip", "-m pip install x", False),
            ("script", "script.py", False),
            ("semicolon", "-m pytest tests/test_x.py; touch y", False),
            ("state-write", f"{scripts_dir}/h_mad_state_write.py {root}/docs/.bkit-memory.json --set x=y", True),
        )

    base = tmp / "base" / "root"
    project = base / "hematology-paper-writer"
    project.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(base)], check=True, stdin=subprocess.DEVNULL,
                   timeout=30.0, env=hermetic_env())
    write_state(base, {'agent "q"\\newline\n[H-MAD:MARKER]%': {"phase": "step5"}})
    test = project / "tests" / "test_x.py"
    test.parent.mkdir()
    test.write_text("def test_red():\n    assert False\n", encoding="utf-8")
    build_venv(project / ".venv", with_pytest=True)
    _shell_script(project / ".venv" / "bin" / "python-evil", "exit 0")
    outside = tmp / "outside-venv"
    build_venv(outside, with_pytest=True)

    rows: list[CorpusRow] = []
    states = ("contained", "venv-symlink-out", "bin-symlink-out", "cfg-missing", "cfg-symlink")
    for state in states:
        root = tmp / state / "root"
        root.parent.mkdir()
        shutil.copytree(base, root, symlinks=True)
        sub = root / "hematology-paper-writer"
        venv = sub / ".venv"
        (root / "sibling").mkdir()
        if state == "venv-symlink-out":
            shutil.rmtree(venv)
            venv.symlink_to(outside, target_is_directory=True)
            assert not os.path.realpath(venv).startswith(str(root) + os.sep)
        elif state == "bin-symlink-out":
            shutil.rmtree(venv / "bin")
            (venv / "bin").symlink_to(outside / "bin", target_is_directory=True)
            assert not os.path.realpath(venv / "bin").startswith(str(root) + os.sep)
        elif state == "cfg-missing":
            (venv / "pyvenv.cfg").unlink()
            assert not os.path.lexists(venv / "pyvenv.cfg")
        elif state == "cfg-symlink":
            cfg = venv / "pyvenv.cfg"
            cfg.unlink()
            real = sub / "cfg-real"
            real.write_text("home=inside\n", encoding="utf-8")
            cfg.symlink_to(real)
            assert cfg.is_symlink() and not stat.S_ISREG(cfg.lstat().st_mode)

        versioned = f"python{sys.version_info.major}.{sys.version_info.minor}"
        spellings = (
            ("absolute", str(venv / "bin/python"), root, True),
            ("root-prefix", "hematology-paper-writer/.venv/bin/python", root, True),
            ("sub-cwd", ".venv/bin/python", sub, True),
            ("sub-dot", "./.venv/bin/python", sub, True),
            ("sibling", "../hematology-paper-writer/.venv/bin/python", root / "sibling", True),
            ("doubled", "hematology-paper-writer/.venv/bin/python", sub, False),
            ("versioned", f".venv/bin/{versioned}", sub, True),
            ("python-evil", ".venv/bin/python-evil", sub, True),
        )
        for spelling, token, cwd, resolves in spellings:
            for args_name, args, allowed_argv in argv_for(root):
                allow = state == "contained" and resolves and allowed_argv
                rows.append(CorpusRow(f"{state}/{spelling}/{args_name}", root, cwd,
                                      f"{token} {args}", "allow" if allow else "deny"))

    root = tmp / "contained" / "root"
    sub = root / "hematology-paper-writer"
    for args_name, args, _ in argv_for(root):
        rows.append(CorpusRow(f"outside/{args_name}", root, sub,
                              f"{outside}/bin/python {args}", "deny"))
    for name, token, args, expected in (
        ("usr-python-pytest", "/usr/bin/python3", "-m pytest tests/test_x.py", "allow"),
        ("usr-python-state-write", "/usr/bin/python3",
         f"{scripts_dir}/h_mad_state_write.py {root}/docs/.bkit-memory.json --set x=y", "allow"),
        ("other-venv", "venv/bin/python", "-m pytest tests/test_x.py", "deny"),
        ("venv-pytest", ".venv/bin/pytest", "tests/test_x.py", "deny"),
        ("bare-python-pytest", "python3", "-m pytest tests/test_x.py", "allow"),
    ):
        rows.append(CorpusRow(f"control/{name}", root, sub, f"{token} {args}", expected))
    assert len(rows) == 251
    assert sum(row.expected_new == "allow" for row in rows) == 17
    assert len({row.name for row in rows}) == len(rows)
    return rows
