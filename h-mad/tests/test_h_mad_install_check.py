"""SKILL.md asserts the install shape as a fact. Nothing ever checked it.

§"Editing this skill while a run is in flight" states that `~/.claude/skills/h-mad`
**is a symlink into this repository**, and the whole coupled-suites warning follows
from that. It was prose. On 2026-08-09 the live install turned out to be a plain
directory copied 2.5 months earlier: 11KB SKILL.md against the checkout's 99KB,
7 scripts against 25. The skill loaded, ran, and reported itself as v2.2 — the
frontmatter is byte-identical between the two, so nothing downstream could tell.

The second half is worse because it is silent in the other direction. Two test
files (`test_h_mad_tdd_gate_codex.py`, `test_h_mad_tdd_gate_state_resolution.py`)
hard-code `~/.claude/hooks/h-mad-tdd-gate.sh`, and `references/codex-implementer-prompt.md`
tells the implementer that is where the armed gate lives. That path did not exist
at all. `settings.json` happened to arm the gate through the *skills* path, so the
gate worked while the tests and the Codex-facing contract pointed at nothing.

`hmad-dispatch env` preflights the agent substrate thoroughly and the skill's own
installation not at all. `bin/hmad-dispatch` resolves symlinks, but only to locate
itself on PATH — it never asserts the shape.

This check makes the install shape checkable instead of merely documented. It reads
paths; it repairs nothing.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_install_check.py"
sys.path.insert(0, str(SCRIPTS))


def _run(skills_link: Path, hook_link: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--skills-link", str(skills_link),
            "--hook-link", str(hook_link),
        ],
        capture_output=True, text=True,
    )


def _token(proc: subprocess.CompletedProcess) -> str:
    for line in proc.stdout.splitlines():
        if line.startswith("INSTALL:"):
            return line.strip()
    return ""


def _checkout(root: Path, name: str = "checkout") -> Path:
    """A directory shaped like an h-mad checkout."""
    co = root / name
    (co / "hooks").mkdir(parents=True)
    (co / "scripts").mkdir(parents=True)
    (co / "SKILL.md").write_text("---\nname: h-mad\n---\n")
    (co / "hooks" / "h-mad-tdd-gate.sh").write_text("#!/bin/bash\nexit 0\n")
    return co


def _healthy(root: Path) -> tuple[Path, Path]:
    co = _checkout(root)
    skills_link = root / "skills-h-mad"
    hook_link = root / "hooks-h-mad-tdd-gate.sh"
    skills_link.symlink_to(co)
    hook_link.symlink_to(co / "hooks" / "h-mad-tdd-gate.sh")
    return skills_link, hook_link


# ── the healthy shape ────────────────────────────────────────────────────────

def test_correct_symlink_install_passes(tmp_path):
    skills_link, hook_link = _healthy(tmp_path)
    proc = _run(skills_link, hook_link)
    assert _token(proc) == "INSTALL: PASS"
    assert proc.returncode == 0


# ── the two defects actually observed on 2026-08-09 ──────────────────────────

def test_stale_copy_instead_of_symlink_is_caught(tmp_path):
    """The real failure: a plain directory that loads fine and silently drifts."""
    co = _checkout(tmp_path)
    stale = tmp_path / "skills-h-mad"
    stale.mkdir()
    (stale / "SKILL.md").write_text("---\nname: h-mad\n---\n")
    hook_link = tmp_path / "hooks-h-mad-tdd-gate.sh"
    hook_link.symlink_to(co / "hooks" / "h-mad-tdd-gate.sh")

    proc = _run(stale, hook_link)
    assert _token(proc).startswith("INSTALL: FAIL")
    assert "SKILL_NOT_SYMLINK:" in proc.stdout


def test_missing_hook_link_is_caught(tmp_path):
    """The silent half: tests and the Codex prompt point at a path nothing creates."""
    co = _checkout(tmp_path)
    skills_link = tmp_path / "skills-h-mad"
    skills_link.symlink_to(co)
    absent_hook = tmp_path / "hooks-h-mad-tdd-gate.sh"

    proc = _run(skills_link, absent_hook)
    assert _token(proc).startswith("INSTALL: FAIL")
    assert "HOOK_NOT_INSTALLED:" in proc.stdout


def test_the_exact_observed_state_reports_both_issues(tmp_path):
    """Stale copy AND absent hook — the install as found on 2026-08-09."""
    stale = tmp_path / "skills-h-mad"
    stale.mkdir()
    (stale / "SKILL.md").write_text("---\nname: h-mad\n---\n")
    absent_hook = tmp_path / "hooks-h-mad-tdd-gate.sh"

    proc = _run(stale, absent_hook)
    assert _token(proc) == "INSTALL: FAIL issues=2"


# ── shapes that are wrong in less obvious ways ───────────────────────────────

def test_split_install_across_two_checkouts_is_caught(tmp_path):
    """Both links are symlinks, but into DIFFERENT checkouts.

    Individually each link looks correct, so a per-link check passes while the
    gate the operator runs and the gate the tests exercise are different files.
    """
    a = _checkout(tmp_path, "checkout-a")
    b = _checkout(tmp_path, "checkout-b")
    skills_link = tmp_path / "skills-h-mad"
    hook_link = tmp_path / "hooks-h-mad-tdd-gate.sh"
    skills_link.symlink_to(a)
    hook_link.symlink_to(b / "hooks" / "h-mad-tdd-gate.sh")

    proc = _run(skills_link, hook_link)
    assert _token(proc).startswith("INSTALL: FAIL")
    assert "SPLIT_INSTALL:" in proc.stdout


def test_dangling_skills_symlink_is_caught(tmp_path):
    co = _checkout(tmp_path)
    skills_link = tmp_path / "skills-h-mad"
    skills_link.symlink_to(tmp_path / "does-not-exist")
    hook_link = tmp_path / "hooks-h-mad-tdd-gate.sh"
    hook_link.symlink_to(co / "hooks" / "h-mad-tdd-gate.sh")

    proc = _run(skills_link, hook_link)
    assert _token(proc).startswith("INSTALL: FAIL")
    assert "SKILL_DANGLING:" in proc.stdout


def test_absent_skills_link_is_caught(tmp_path):
    co = _checkout(tmp_path)
    hook_link = tmp_path / "hooks-h-mad-tdd-gate.sh"
    hook_link.symlink_to(co / "hooks" / "h-mad-tdd-gate.sh")

    proc = _run(tmp_path / "skills-h-mad", hook_link)
    assert _token(proc).startswith("INSTALL: FAIL")
    assert "SKILL_NOT_INSTALLED:" in proc.stdout


def test_symlink_to_a_directory_that_is_not_a_checkout_is_caught(tmp_path):
    """A symlink is necessary but not sufficient — it must point at h-mad."""
    notco = tmp_path / "somewhere-else"
    notco.mkdir()
    skills_link = tmp_path / "skills-h-mad"
    skills_link.symlink_to(notco)
    co = _checkout(tmp_path)
    hook_link = tmp_path / "hooks-h-mad-tdd-gate.sh"
    hook_link.symlink_to(co / "hooks" / "h-mad-tdd-gate.sh")

    proc = _run(skills_link, hook_link)
    assert _token(proc).startswith("INSTALL: FAIL")
    assert "SKILL_NOT_A_CHECKOUT:" in proc.stdout


# ── signal discipline (invariants.base.md §"Audit-gate signal discipline") ───

def test_fail_exits_zero_because_it_is_a_verdict(tmp_path):
    """A non-zero exit registers as a PostToolUseFailure and leaks into
    coexisting plugins' error handling. FAIL is a verdict, not an error."""
    stale = tmp_path / "skills-h-mad"
    stale.mkdir()
    (stale / "SKILL.md").write_text("x")
    proc = _run(stale, tmp_path / "absent")
    assert _token(proc).startswith("INSTALL: FAIL")
    assert proc.returncode == 0


def test_token_is_the_only_verdict_surface_on_stdout(tmp_path):
    """Callers read the token, never `$?` — so stdout must carry exactly one."""
    skills_link, hook_link = _healthy(tmp_path)
    proc = _run(skills_link, hook_link)
    tokens = [l for l in proc.stdout.splitlines() if l.startswith("INSTALL:")]
    assert len(tokens) == 1


def test_pass_and_fail_are_distinguishable_without_the_exit_code(tmp_path):
    """Both verdicts exit 0, so the token must be the discriminator."""
    good_s, good_h = _healthy(tmp_path / "good")
    (tmp_path / "bad").mkdir()
    bad_s = tmp_path / "bad" / "skills-h-mad"
    bad_s.mkdir()
    good = _run(good_s, good_h)
    bad = _run(bad_s, tmp_path / "bad" / "absent")
    assert good.returncode == bad.returncode == 0
    assert _token(good) != _token(bad)


def test_unreadable_is_a_cannot_judge_and_exits_two(tmp_path):
    """Nothing could be checked -> no verdict exists. Distinct from FAIL."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--skills-link", "", "--hook-link", ""],
        capture_output=True, text=True,
    )
    assert _token(proc) == "INSTALL: UNREADABLE"
    assert proc.returncode == 2


# ── the defaults must be the real install paths ──────────────────────────────

def test_defaults_target_the_documented_install_paths():
    """The check is worthless if its defaults drift from what SKILL.md asserts."""
    import h_mad_install_check as ic

    assert ic.DEFAULT_SKILLS_LINK == Path.home() / ".claude" / "skills" / "h-mad"
    assert ic.DEFAULT_HOOK_LINK == (
        Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"
    )


def test_hook_link_default_matches_what_the_gate_tests_hardcode():
    """Both gate suites resolve HOOK the same way; if this default drifts from
    them the check would pass while those suites fail."""
    import h_mad_install_check as ic

    hardcoded = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"
    assert ic.DEFAULT_HOOK_LINK == hardcoded
