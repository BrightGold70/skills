"""Run the committed FR-9 probe against isolated repositories, never this tree."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


HMAD = Path(__file__).resolve().parents[1]
DRIVER = (HMAD.parent / "docs/03-analysis/probes"
          / "gate-non-py-production-files/fr9_drive.py")
HOOK = "h-mad/hooks/h-mad-tdd-gate.sh"
PLAN = "docs/01-plan/features/exec-missing-report-recovery.impl-plan.md"
HOSTILE = 'agent "quoted" \\\n## H-MAD-MARKER *?[] Ω\nkind=forged'
CASES = (
    ("no-before-side", "fixture", "before"),
    ("dirty-hooks", "fixture", "after"),
    ("hook-outside-tree", "fixture", "after"),
    ("hook-blob-mismatch", "fixture", "after"),
    ("authorship-line", "fixture", "after"),
    ("missing-base", "replay", "after"),
    ("base-is-head", "replay", "after"),
    ("plan-absent-at-base", "replay", "after"),
    ("plan-blob-mismatch", "replay", "after"),
)


def _git(root: Path, env: dict[str, str], *args: str,
         check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, env=env, capture_output=True,
        text=True, timeout=15, check=check,
    )


def _commit(root: Path, env: dict[str, str]) -> str:
    _git(root, env, "add", "--all")
    _git(root, env, "commit", "--quiet", "-m", HOSTILE)
    return _git(root, env, "rev-parse", "HEAD").stdout.strip()


def _refusal_repo(tmp_path: Path, reason: str) -> tuple[Path, dict[str, str]]:
    # Hostile operator-chosen paths deliberately avoid [], and : because pytest
    # and the probe's venv also use scratch paths as filesystem locations.
    root = tmp_path / "repo Ω 'quoted%H-MAD-MARKER"
    root.mkdir()
    home = tmp_path / "empty-home"
    home.mkdir()
    temp = tmp_path / "temp"
    temp.mkdir()
    env = {name: value for name, value in os.environ.items()
           if not name.startswith("GIT_")}
    env.update(
        HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
        TMPDIR=str(temp), LANG="en_US.UTF-8", HMAD_STUB_HOSTILE="all",
        GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="FR9 fixture",
        GIT_AUTHOR_EMAIL="fr9@example.invalid", GIT_COMMITTER_NAME="FR9 fixture",
        GIT_COMMITTER_EMAIL="fr9@example.invalid",
    )
    _git(root, env, "init", "--quiet")
    _git(root, env, "config", "core.autocrlf", "false")
    _git(root, env, "config", "commit.gpgsign", "false")
    for name in ("hooks", "scripts"):
        shutil.copytree(HMAD / name, root / "h-mad" / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    hook = root / HOOK
    if reason == "hook-outside-tree":
        outside = tmp_path / "outside Ω 'quoted-hook.sh"
        outside.write_bytes(hook.read_bytes())
        hook.unlink()
        hook.symlink_to(outside)
    elif reason == "authorship-line":
        (root / "h-mad/scripts/h_mad_tdd_judge.py").write_text(
            "import sys\n"
            "if sys.argv[1] == 'implementer':\n"
            "    print('TDD-IMPLEMENTER: codex chosen=codex switch=none')\n",
            encoding="utf-8",
        )
    elif reason == "plan-blob-mismatch":
        plan = root / PLAN
        plan.parent.mkdir(parents=True)
        plan.write_bytes(("# Replay plan\n" + HOSTILE + "\n").replace(
            "\n", "\r\n").encode("utf-8"))

    base = _commit(root, env)
    if reason in {"plan-absent-at-base", "plan-blob-mismatch"}:
        plan = root / PLAN
        if reason == "plan-absent-at-base":
            plan.parent.mkdir(parents=True)
            plan.write_text("# Added after base\n" + HOSTILE + "\n", encoding="utf-8")
        else:
            (root / "later.txt").write_text(HOSTILE + "\n", encoding="utf-8")
        head = _commit(root, env)
        assert head != base, f"{reason}: fixture must put the base before HEAD"
        _git(root, env, "update-ref", "refs/remotes/origin/main", base)
        assert _git(root, env, "merge-base", "HEAD", "origin/main").stdout.strip() == base
        at_base = _git(root, env, "cat-file", "blob", f"{base}:{PLAN}", check=False)
        if reason == "plan-absent-at-base":
            assert at_base.returncode == 128, "plan-absent-at-base: absent blob precondition"
            _git(root, env, "cat-file", "-e", f"HEAD:{PLAN}")
        else:
            _git(root, env, "config", "core.autocrlf", "true")
            # Byte copying must preserve CRLF. Hash from the source repo: the
            # replay repo lacks this local config and cannot expose this defect.
            copy = tmp_path / "plan-copy.md"
            copy.write_bytes(subprocess.run(
                ["git", "cat-file", "blob", f"{base}:{PLAN}"], cwd=root, env=env,
                capture_output=True, timeout=15, check=True,
            ).stdout)
            assert b"\r\n" in copy.read_bytes(), "plan-blob-mismatch: preserve base CRLF"
            blob = _git(root, env, "rev-parse", f"{base}:{PLAN}").stdout.strip()
            hashed = _git(root, env, "hash-object", str(copy)).stdout.strip()
            assert hashed != blob, "plan-blob-mismatch: source repo must normalise the copy"
    elif reason == "base-is-head":
        _git(root, env, "update-ref", "refs/remotes/origin/main", base)
        assert _git(root, env, "merge-base", "HEAD", "origin/main").stdout.strip() == base
    elif reason == "missing-base":
        assert _git(root, env, "rev-parse", "--verify", "refs/remotes/origin/main",
                    check=False).returncode != 0, "missing-base: origin/main must be absent"

    if reason in {"dirty-hooks", "hook-blob-mismatch"}:
        hook.write_bytes(hook.read_bytes() + b"\n# uncommitted fixture change\n")
        if reason == "hook-blob-mismatch":
            _git(root, env, "update-index", "--assume-unchanged", HOOK)
            assert (_git(root, env, "hash-object", HOOK).stdout.strip()
                    != _git(root, env, "rev-parse", f"HEAD:{HOOK}").stdout.strip()), (
                "hook-blob-mismatch: hidden edit must differ from the committed blob"
            )
    status = _git(root, env, "status", "--porcelain", "--", "h-mad").stdout
    assert bool(status) == (reason == "dirty-hooks"), (
        f"{reason}: hook dirtiness must reach the intended refusal, got {status!r}"
    )
    if reason == "hook-outside-tree":
        assert hook.is_symlink() and not hook.resolve().is_relative_to(root.resolve()), (
            "hook-outside-tree: the clean committed symlink must escape the tested tree"
        )
    return root, env


@pytest.mark.parametrize("reason,scenario,side", CASES, ids=[case[0] for case in CASES])
def test_fr9_driver_refuses(tmp_path, reason, scenario, side):
    root, env = _refusal_repo(tmp_path, reason)
    proc = subprocess.run(
        [sys.executable, "-I", str(DRIVER), "--scenario", scenario,
         "--side", side, "--host", "claude", "--out",
         str(tmp_path / "evidence Ω 'quoted%H-MAD-MARKER")],
        cwd=root, env=env, capture_output=True, text=True, timeout=120, check=False,
    )
    expected = f"FR9-DRIVE: UNREADABLE {reason}"
    assert expected in proc.stdout.splitlines(), (
        f"{reason}: driver.main must print its exact refusal token {expected!r}; "
        f"rc={proc.returncode}, stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
    assert proc.returncode == 2, (
        f"{reason}: driver.main must refuse with exit 2, got {proc.returncode}; "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
