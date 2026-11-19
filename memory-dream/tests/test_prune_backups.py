"""Tests for memory-dream/scripts/prune_backups.py — retention that must never take the only undo."""
from __future__ import annotations

import datetime as dt
import pathlib
import subprocess
import sys

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import prune_backups as pb  # noqa: E402

SCRIPT = SCRIPTS / "prune_backups.py"
NOW = dt.datetime(2026, 12, 31, 12, 0, 0)


def partial(root, name, with_index=False):
    d = root / name
    d.mkdir()
    (d / "note.md").write_text("x")
    if with_index:                       # partial backups often hold the index they edited
        (d / "MEMORY.md").write_text("- [A](a.md) — x\n")
        (d / "MEMORY-ARCHIVE.md").write_text("- [B](b.md) — y\n")
    return d


def full(root, name):
    d = root / name
    d.mkdir()
    (d / "MEMORY.md").write_text("- [A](a.md) — x\n")
    (d / "MEMORY-ARCHIVE.md").write_text("- [B](./b.md#s) — y\n")
    (d / "a.md").write_text("a")
    (d / "b.md").write_text("b")
    return d


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "backups"
    r.mkdir()
    return r


def names(paths):
    return [p.name for p in paths]


def test_age_comes_from_the_name_and_the_cutoff_is_exclusive(root):
    partial(root, "20261101-120000-old")          # 60 days
    partial(root, "20261201-120000-edge")         # exactly 30 days: kept
    partial(root, "20261230-090000-new")
    p = pb.plan(root, 30, NOW)
    assert names(p["delete"]) == ["20261101-120000-old"]
    assert names(p["keep"]) == ["20261201-120000-edge", "20261230-090000-new"]


def test_newest_full_snapshot_is_protected_however_old(root):
    full(root, "20260901-000000-full-older")
    full(root, "20261001-000000-full-newest")
    partial(root, "20261101-000000-partial-with-index", with_index=True)
    p = pb.plan(root, 30, NOW)
    assert names(p["protected"]) == ["20261001-000000-full-newest"]
    assert "20260901-000000-full-older" in names(p["delete"])
    assert "20261101-000000-partial-with-index" in names(p["delete"])


def test_holding_memory_md_does_not_make_a_backup_full(root):
    assert not pb.is_full(partial(root, "20261101-000000-p", with_index=True))
    assert pb.is_full(full(root, "20261101-000001-f"))


def test_foreign_names_files_and_symlinks_are_ignored(root, tmp_path):
    (root / "notes").mkdir()
    (root / "20261101-000000.txt").write_text("a file with a backup-like name")
    outside = tmp_path / "20260101-000000-outside"
    outside.mkdir()
    (root / "20260101-000000-link").symlink_to(outside)
    p = pb.plan(root, 30, NOW)
    assert p["delete"] == [] and len(p["ignored"]) == 3


def test_dry_run_deletes_nothing_and_apply_deletes_only_the_plan(root, tmp_path):
    old = partial(root, "20261101-120000-old")
    keep = partial(root, "20261230-090000-new")
    outside = tmp_path / "20260101-000000-outside"
    outside.mkdir()
    (root / "20260101-000000-link").symlink_to(outside)
    base = [sys.executable, str(SCRIPT), "--root", str(root), "--now", NOW.isoformat()]
    r = subprocess.run(base, capture_output=True, text=True)
    assert "would_delete=1" in r.stdout and old.exists()
    r = subprocess.run(base + ["--apply"], capture_output=True, text=True)
    assert "deleted=1" in r.stdout and r.returncode == 0
    assert not old.exists() and keep.exists() and outside.exists() and (root / "20260101-000000-link").is_symlink()


def test_missing_root_and_bad_days(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path / "none")], capture_output=True, text=True)
    assert r.returncode == 0 and "PRUNE: NONE" in r.stdout
    r = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path), "--days", "0"], capture_output=True, text=True)
    assert r.returncode == 2


def test_symlink_to_a_sibling_backup_is_ignored(root):
    """Resolves INSIDE the root, so only the is_symlink guard stops it."""
    target = partial(root, "20261230-090000-new")
    (root / "20260101-000000-alias").symlink_to(target)
    p = pb.plan(root, 30, NOW)
    assert "20260101-000000-alias" in names(p["ignored"]) and p["delete"] == []
