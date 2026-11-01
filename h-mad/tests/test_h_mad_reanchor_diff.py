"""A re-anchored mutation row must keep the same edit delta (row 2816).

A row can stay ANCHORS_OK and ALL_CAUGHT while its mutant no longer breaks what
it used to: codex rewrote `emit-the-guards-only-for-wiring` that way on
2026-10-25. The rule (user ruling 2026-11-01): tokenize `find` and `replace`
ignoring whitespace, diff them, and require the same tokens added, with one
removed set containing the other, as the row's version at `--base`. Widening `find` for
uniqueness keeps the delta; changing what the mutant breaks does not. A row with
no same-named row at base is cannot-judge, never OK. Advisory: exit 0, and the
summary word is new to this tool, so no hook parses it.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_reanchor_diff.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _row(name: str, find: str, replace: str) -> dict:
    return {"name": name, "file": "x.py", "find": find, "replace": replace,
            "test": "tests/test_x.py::test_x"}


def _repo(tmp_path: Path, rows: list[dict]) -> Path:
    repo = tmp_path / "repo"
    (repo / "specs").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _write(repo, rows)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _write(repo: Path, rows: list[dict]) -> Path:
    spec = repo / "specs" / "s.json"
    spec.write_text(json.dumps({"command": ["true"], "mutations": rows}), encoding="utf-8")
    return spec


def _run(repo: Path, *specs: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--base", "HEAD", *specs],
                          cwd=repo, capture_output=True, text=True)


GUARD = _row("drop-guard", "    if not ok:\n        return False", "    if False:\n        return False")


def test_widening_find_for_uniqueness_keeps_the_delta(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [GUARD])
    _write(repo, [_row("drop-guard", "def f():\n    if not ok:\n        return False",
                       "def f():\n    if False:\n        return False")])
    proc = _run(repo, "specs/s.json")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == "REANCHOR: SAME rows=1 reanchored=1 changed=0 unjudged=0", proc.stdout


def test_whitespace_only_reflow_keeps_the_delta(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [GUARD])
    _write(repo, [_row("drop-guard", "        if not ok:\n            return False",
                       "        if False:\n            return False")])
    assert "REANCHOR: SAME" in _run(repo, "specs/s.json").stdout


def test_a_rewrite_that_breaks_something_else_is_changed(tmp_path: Path) -> None:
    # The 2026-10-25 shape: anchors still valid, mutant now breaks a different guard.
    repo = _repo(tmp_path, [GUARD])
    _write(repo, [_row("drop-guard", "    if not ok:\n        return False",
                       "    if not ok:\n        return True")])
    proc = _run(repo, "specs/s.json")
    assert proc.returncode == 0, "advisory: a changed delta never fails the run"
    assert proc.stdout.splitlines()[-1] == "REANCHOR: CHANGED rows=1 reanchored=1 changed=1 unjudged=0", proc.stdout
    assert "  reanchor-changed: specs/s.json :: drop-guard" in proc.stdout, proc.stdout


def test_a_row_with_no_same_named_row_at_base_is_unjudged(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [GUARD])
    _write(repo, [_row("drop-guard-renamed", GUARD["find"], GUARD["replace"])])
    proc = _run(repo, "specs/s.json")
    assert proc.stdout.splitlines()[-1] == "REANCHOR: UNJUDGED rows=1 reanchored=0 changed=0 unjudged=1", proc.stdout
    assert "  reanchor-unjudged: specs/s.json :: drop-guard-renamed (no row of that name at HEAD)" in proc.stdout


def test_a_spec_absent_at_base_is_unjudged_not_ok(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [GUARD])
    (repo / "specs" / "new.json").write_text(json.dumps({"mutations": [GUARD]}), encoding="utf-8")
    proc = _run(repo, "specs/new.json")
    assert "REANCHOR: UNJUDGED" in proc.stdout.splitlines()[-1], proc.stdout


def test_an_unreadable_spec_is_unjudged_not_ok(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [GUARD])
    (repo / "specs" / "s.json").write_text("{not json", encoding="utf-8")
    proc = _run(repo, "specs/s.json")
    assert proc.returncode == 0
    assert "REANCHOR: UNJUDGED" in proc.stdout.splitlines()[-1], proc.stdout


def test_an_untouched_row_is_not_counted_as_reanchored(tmp_path: Path) -> None:
    other = _row("other", "a = 1", "a = 2")
    repo = _repo(tmp_path, [GUARD, other])
    _write(repo, [GUARD, _row("other", "b = 1\na = 1", "b = 1\na = 2")])
    assert _run(repo, "specs/s.json").stdout.splitlines()[-1] == (
        "REANCHOR: SAME rows=2 reanchored=1 changed=0 unjudged=0")


def test_bad_arguments_exit_two(tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(SCRIPT), "specs/s.json"], cwd=tmp_path,
                          capture_output=True, text=True)
    assert proc.returncode == 2


def test_a_deleted_statement_that_grew_keeps_the_delta(tmp_path: Path) -> None:
    # Calibration (a9e9a123, `empty-argv-returns-clean`): the mutant replaces a whole
    # statement, and the statement grew, so the removed tokens grew with it. Same
    # added tokens and nested removed tokens is a legitimate re-anchor (user ruling).
    repo = _repo(tmp_path, [_row("drop-usage", 'print("usage: x [--a]")', "0")])
    _write(repo, [_row("drop-usage", 'print("usage: x [--a] [--b]")', "0")])
    assert _run(repo, "specs/s.json").stdout.splitlines()[-1] == (
        "REANCHOR: SAME rows=1 reanchored=1 changed=0 unjudged=0")


def test_removing_unrelated_tokens_is_changed(tmp_path: Path) -> None:
    # Neither removed set contains the other: the mutant now deletes something else.
    repo = _repo(tmp_path, [_row("drop-a", "a = check(x)", "a = True")])
    _write(repo, [_row("drop-a", "b = probe(y)", "b = True")])
    assert "REANCHOR: CHANGED" in _run(repo, "specs/s.json").stdout


def test_same_removed_tokens_but_a_different_replacement_is_changed(tmp_path: Path) -> None:
    # Only the added tokens differ: `x = True` became `x = None`.
    repo = _repo(tmp_path, [_row("stub-check", "x = check(a)", "x = True")])
    _write(repo, [_row("stub-check", "x = check(a)", "x = None")])
    assert "REANCHOR: CHANGED" in _run(repo, "specs/s.json").stdout


def test_spacing_inside_the_edited_region_is_ignored(tmp_path: Path) -> None:
    repo = _repo(tmp_path, [_row("swap-args", "f(a,b)", "f(b,a)")])
    _write(repo, [_row("swap-args", "f(a, b)", "f(b, a)")])
    assert "REANCHOR: SAME" in _run(repo, "specs/s.json").stdout
