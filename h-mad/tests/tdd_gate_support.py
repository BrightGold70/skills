"""Shared test support for codex-tdd-gate-defects (not collected: no test_ prefix)."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
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
