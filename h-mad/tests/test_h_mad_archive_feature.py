"""`h_mad_archive_feature.py` archives a closed feature COMPLETELY, or says it did not.

Skill-candidates row "a closure check that the archive is COMPLETE": Phase 7c was four
`mv docs/…/${FEATURE}* … 2>/dev/null || true` lines. For doc-block-exec it moved 6 of
641 files, leaving the originals live; a merged feature's impl-plan kept gating live
code and an unrelated commit turned the suite red weeks later. The glob also never
reached `docs/03-analysis/probes/<feature>/`, and `${FEATURE}*` matches every sibling
feature sharing the prefix (`pin-agents` takes `pin-agents-tail-banner.*`).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_archive_feature.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

FEATURE_FILES = [
    "docs/01-plan/features/foo.plan.md",
    "docs/01-plan/features/foo.spec.md",
    "docs/01-plan/features/foo.plan.audit.v1.md",
    "docs/01-plan/features/foo-brainstorm.md",
    "docs/02-design/features/foo.design.md",
    "docs/03-analysis/foo.analysis.md",
    "docs/03-analysis/probes/foo/reading.md",
    "docs/04-report/features/foo.report.md",
]
SIBLINGS = ["docs/01-plan/features/foo-bar.plan.md", "docs/03-analysis/probes/foo-bar/x.md"]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, env=ENV,
                          capture_output=True, text=True).stdout


def _repo(tmp_path: Path, untracked: tuple[str, ...] = ()) -> Path:
    repo = tmp_path / "repo"
    for rel in FEATURE_FILES + SIBLINGS:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"{rel}\n", encoding="utf-8")
    _git(repo, "init", "-q")
    for rel in untracked:
        (repo / rel).rename(repo / (rel + ".tmp"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    for rel in untracked:
        (repo / (rel + ".tmp")).rename(repo / rel)
    return repo


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--feature", "foo",
                           "--month", "2026-10", *args], capture_output=True, text=True)


def _token(out: str) -> str:
    return next((l for l in out.splitlines() if l.startswith("ARCHIVE:")), "")


def test_apply_moves_every_feature_file_and_reports_complete(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    proc = _run(repo, "--apply")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _token(proc.stdout) == f"ARCHIVE: COMPLETE moved={len(FEATURE_FILES)}", proc.stdout
    dest = repo / "docs/archive/2026-10/foo"
    for rel in FEATURE_FILES:
        assert not (repo / rel).exists(), rel
    assert (dest / "foo.plan.md").exists()
    assert (dest / "foo-brainstorm.md").exists()
    assert (dest / "probes" / "reading.md").exists(), "the probes dir is part of the feature"


def test_a_sibling_sharing_the_prefix_is_never_taken(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    _run(repo, "--apply")

    for rel in SIBLINGS:
        assert (repo / rel).exists(), f"{rel} belongs to foo-bar, not foo"


def test_tracked_files_move_with_git_so_history_follows(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    _run(repo, "--apply")

    staged = _git(repo, "diff", "--cached", "--name-status", "-M")
    assert "R100\tdocs/01-plan/features/foo.plan.md\tdocs/archive/2026-10/foo/foo.plan.md" in staged, staged


def test_an_untracked_feature_file_is_moved_too(tmp_path: Path) -> None:
    repo = _repo(tmp_path, untracked=("docs/03-analysis/foo.analysis.md",))

    proc = _run(repo, "--apply")

    assert _token(proc.stdout).startswith("ARCHIVE: COMPLETE"), proc.stdout
    assert (repo / "docs/archive/2026-10/foo/foo.analysis.md").exists()


def test_default_is_a_dry_run(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    proc = _run(repo)

    assert _token(proc.stdout) == f"ARCHIVE: PLAN would_move={len(FEATURE_FILES)}", proc.stdout
    assert all((repo / rel).exists() for rel in FEATURE_FILES), "a dry run moved files"


def test_an_existing_archive_file_is_never_overwritten(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    dest = repo / "docs/archive/2026-10/foo"
    dest.mkdir(parents=True)
    (dest / "foo.plan.md").write_text("already archived, different\n", encoding="utf-8")

    proc = _run(repo, "--apply")

    assert proc.returncode == 2, proc.stdout
    assert _token(proc.stdout).startswith("ARCHIVE: INCOMPLETE"), proc.stdout
    assert "COLLISION: docs/01-plan/features/foo.plan.md" in proc.stdout, proc.stdout
    assert (dest / "foo.plan.md").read_text(encoding="utf-8") == "already archived, different\n"
    assert (repo / "docs/01-plan/features/foo.plan.md").exists()


def test_check_reports_what_was_left_live(tmp_path: Path) -> None:
    """The doc-block-exec shape: the archive exists, the originals are still live."""
    repo = _repo(tmp_path)

    proc = _run(repo, "--check")

    assert proc.returncode == 2, proc.stdout
    assert _token(proc.stdout) == f"ARCHIVE: INCOMPLETE left={len(FEATURE_FILES)}", proc.stdout
    assert "LEFT: docs/03-analysis/probes/foo/reading.md" in proc.stdout, proc.stdout


def test_check_after_apply_is_complete(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _run(repo, "--apply")

    proc = _run(repo, "--check")

    assert proc.returncode == 0, proc.stdout
    assert _token(proc.stdout) == "ARCHIVE: COMPLETE left=0", proc.stdout


def test_a_feature_name_matching_nothing_is_not_complete(tmp_path: Path) -> None:
    """A typo'd name archives nothing; 'COMPLETE moved=0' would certify it."""
    repo = _repo(tmp_path)

    proc = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--feature", "fooo",
                           "--month", "2026-10", "--apply"], capture_output=True, text=True)

    assert proc.returncode == 2, proc.stdout
    assert _token(proc.stdout) == "ARCHIVE: NOTHING feature=fooo", proc.stdout


def test_a_probes_dir_that_live_code_reads_is_kept_not_moved(tmp_path: Path) -> None:
    """Calibrated on this repo: `multi-host-runtime`'s probes are read by
    `h-mad/tests/test_host_runtime_docs.py`. Archiving them breaks the suite, so a
    probes dir that tracked code outside it names is KEPT, and not counted as left."""
    repo = _repo(tmp_path)
    test = repo / "skill" / "tests" / "test_reads_probes.py"
    test.parent.mkdir(parents=True)
    test.write_text('P = ROOT / "docs/03-analysis/probes/foo" / "reading.md"\n', encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "a live reader")

    proc = _run(repo, "--apply")

    assert proc.returncode == 0, proc.stdout
    assert _token(proc.stdout) == f"ARCHIVE: COMPLETE moved={len(FEATURE_FILES) - 1}", proc.stdout
    assert "KEPT: docs/03-analysis/probes/foo — read by skill/tests/test_reads_probes.py" in proc.stdout
    assert (repo / "docs/03-analysis/probes/foo/reading.md").exists()
    check = _run(repo, "--check")
    assert _token(check.stdout) == "ARCHIVE: COMPLETE left=0", check.stdout


def test_a_sibling_probe_naming_its_own_dir_does_not_keep_ours(tmp_path: Path) -> None:
    """`probes/foo-bar/` contains the string `probes/foo`; that is not a reader of foo."""
    repo = _repo(tmp_path)
    sib = repo / "docs/03-analysis/probes/foo-bar/run.py"
    sib.write_text('OUT = "docs/03-analysis/probes/foo-bar/out.txt"\n', encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "sibling probe")

    proc = _run(repo, "--apply")

    assert "KEPT:" not in proc.stdout, proc.stdout
    assert _token(proc.stdout) == f"ARCHIVE: COMPLETE moved={len(FEATURE_FILES)}", proc.stdout
