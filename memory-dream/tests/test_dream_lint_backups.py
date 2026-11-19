"""dream_lint against REAL memory stores: the backups memory-dream writes before every edit.

Fixtures are written to exercise one rule each; real stores hold what nobody thought to
write — 300 notes of TOML headers, regex classes, nested fences, CRLF, aliases. These tests
run the lint over every backup under `~/.claude/memory-dream-backups` (or
`$MEMORY_DREAM_BACKUPS`) and check what real data can settle:

- every backup lints without a traceback, inside a time bound (the 2026-11-19 code-span
  regex backtracked exponentially on crafted input; real notes quote Markdown), with exit
  2 + UNREADABLE exactly when the backup holds no MEMORY.md (most backups are partial:
  only the files one edit touched);
- the lint is READ-ONLY on them, including `--fix-links` without `--apply` (contents AND mtimes;
  every run is on a temp copy, so a regression can never touch the real backups);
- the one full pre-dream snapshot keeps the calibration the hook checks were committed on:
  0 hook findings, 0 UNSAFE, 0 AMBIGUOUS (store-state counts such as orphans are not a
  property of the lint and are not pinned).

The backups are private and machine-local. Where none exist (another machine, CI) every
test SKIPS — "I could not check" and "the check passed" must not be spelled the same way.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "dream_lint.py"
ROOT = pathlib.Path(os.environ.get("MEMORY_DREAM_BACKUPS",
                                   pathlib.Path.home() / ".claude" / "memory-dream-backups"))
PRE_DREAM = "20261119-105940-judgment"     # full 299-file snapshot taken before the judgment pass
TIME_BOUND_S = 10.0


def backups() -> list[pathlib.Path]:
    return sorted(p for p in ROOT.iterdir() if p.is_dir()) if ROOT.is_dir() else []


pytestmark = pytest.mark.skipif(not backups(), reason=f"no memory-dream backups under {ROOT}")


def lint(path: pathlib.Path, *extra: str) -> tuple[subprocess.CompletedProcess, float]:
    t0 = time.monotonic()
    r = subprocess.run([sys.executable, str(SCRIPT), str(path), *extra],
                       capture_output=True, text=True, timeout=120)
    return r, time.monotonic() - t0


def tree_state(path: pathlib.Path) -> dict[str, tuple[str, int]]:
    """Every file's (sha256, mtime_ns): a rewrite with identical bytes still moves the mtime."""
    return {str(p.relative_to(path)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in sorted(path.rglob("*")) if p.is_file()}


@pytest.fixture
def copy_of(tmp_path):
    """Lint a COPY, never the backup itself: a lint that writes would otherwise damage the
    only undo for an unversioned store, and an earlier test's write would mask a later check."""
    def make(backup: pathlib.Path) -> pathlib.Path:
        dst = tmp_path / backup.name
        shutil.copytree(backup, dst, copy_function=shutil.copy2)
        return dst
    return make


def counts(stdout: str) -> dict[str, int]:
    return {k: int(v) for k, v in re.findall(r"\b([A-Za-z_]+)=(\d+)\b", stdout)}


@pytest.mark.parametrize("backup", backups(), ids=lambda p: p.name)
def test_every_backup_lints_cleanly(backup, copy_of):
    r, elapsed = lint(copy_of(backup))
    assert "Traceback" not in r.stderr, r.stderr
    assert elapsed < TIME_BOUND_S, f"{backup.name}: {elapsed:.1f}s"
    if (backup / "MEMORY.md").is_file():
        assert r.returncode in (0, 1), (r.returncode, r.stderr)
        assert re.search(r"^links total=\d+", r.stdout, re.M), r.stdout
    else:
        assert r.returncode == 2 and "UNREADABLE" in r.stderr, (r.returncode, r.stderr)


@pytest.mark.parametrize("backup", backups(), ids=lambda p: p.name)
def test_lint_never_writes_to_a_backup(backup, copy_of):
    work = copy_of(backup)
    before = tree_state(work)
    lint(work)
    lint(work, "--fix-links")            # the dry run prints a diff and must write nothing
    lint(work, "--verbose")
    assert tree_state(work) == before


def test_pre_dream_snapshot_keeps_its_calibration(copy_of):
    snap = ROOT / PRE_DREAM
    if not (snap / "MEMORY.md").is_file():
        pytest.skip(f"{PRE_DREAM} snapshot not on this machine")
    assert len(list(snap.glob("*.md"))) >= 200, "not the full snapshot"
    r, _ = lint(copy_of(snap))
    c = counts(r.stdout)
    assert c["hooks"] == 0, r.stdout
    assert c["UNSAFE"] == 0 and c["AMBIGUOUS"] == 0, r.stdout
    assert c["total"] == c["RESOLVED"] + c["FIXABLE"] + c["UNSAFE"] + c["AMBIGUOUS"] + c["DANGLING"]
