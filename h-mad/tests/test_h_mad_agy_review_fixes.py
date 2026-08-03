"""Fixes from the 2026-08-03 agy review of the h-mad skill.

The review returned NEEDS_WORK with six findings, all verified against the files
before acting. Three of them share one shape, and it is the shape worth naming:
**the document diagnoses a hazard precisely and then withholds the command
needed to avoid it.** `git stash push` exits 0 on untracked paths (documented,
no safe alternative given); "presence is not enforcement" (documented in
invariants, never reaching the reviewer that needs it); a preconditions check
that emits no token while the caller is told to read one.

An agent that is handed a rule without the means to obey it does not stop — it
improvises. These tests pin the means, not just the rule.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = SKILL_DIR / "SKILL.md"
RECOVERY = SKILL_DIR / "references" / "failure-recovery.md"
SPEC_REVIEWER = SKILL_DIR / "references" / "agy-spec-reviewer-prompt.md"
BASE = SKILL_DIR / "invariants.base.md"
PRECONDITIONS = SKILL_DIR / "scripts" / "h_mad_do_preconditions.py"


def _norm(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _run(repo_root: Path, feature: str = "feat") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PRECONDITIONS), "--repo-root", str(repo_root),
         "--feature", feature],
        capture_output=True, text=True,
    )


# --- M1: preconditions must carry a token and exit 0 on a verdict ---------


def test_a_failing_precondition_is_a_verdict_not_an_exit_code(tmp_path: Path) -> None:
    # The violation this fixes: exiting 1 on a normal FAIL registers as a
    # PostToolUseFailure and leaks into coexisting plugins' error handling
    # (invariants.base.md §"Audit-gate signal discipline").
    proc = _run(tmp_path)
    assert proc.returncode == 0, (
        f"a normal FAIL verdict must exit 0, got {proc.returncode}: {proc.stderr}"
    )
    assert "PRECONDITION: FAIL" in proc.stdout, proc.stdout


def test_the_fail_token_carries_a_count_and_the_detail_lines(tmp_path: Path) -> None:
    proc = _run(tmp_path)
    assert "issues=" in proc.stdout, proc.stdout
    assert "MISSING:" in proc.stdout, "the detail lines say WHICH prerequisite is unmet"


def test_a_passing_precondition_prints_the_pass_token(tmp_path: Path) -> None:
    # Counter-direction: a check that only ever emits FAIL would satisfy the
    # test above forever.
    plan = tmp_path / "docs/01-plan/features"
    design = tmp_path / "docs/02-design/features"
    plan.mkdir(parents=True)
    design.mkdir(parents=True)
    (plan / "feat.plan.md").write_text("plan", encoding="utf-8")
    (design / "feat.design.md").write_text("design", encoding="utf-8")
    clean = "## Must-fix\n\nNone\n\n## Should-fix\n\n## Nit\n"
    (plan / "feat.plan.audit.v1.md").write_text(clean, encoding="utf-8")
    (design / "feat.design.audit.v1.md").write_text(clean, encoding="utf-8")
    proc = _run(tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "PRECONDITION: PASS" in proc.stdout, proc.stdout


def test_an_unreadable_repo_root_is_the_one_non_zero_case(tmp_path: Path) -> None:
    # Non-zero stays meaningful: reserved for "nothing was checked", never for a
    # verdict about the feature.
    proc = _run(tmp_path / "does-not-exist")
    assert proc.returncode == 2, proc.stdout
    assert "PRECONDITION: UNREADABLE" in proc.stdout, proc.stdout
    assert "PRECONDITION: FAIL" not in proc.stdout, (
        "a bad path must not be reported as a verdict about the feature"
    )


def test_skill_tells_the_caller_to_read_the_token() -> None:
    text = _norm(SKILL)
    assert "read its `PRECONDITION:` token, never `$?`" in text, (
        "the instruction that caused the violation was 'refuse if non-zero'"
    )
    assert "refuse if non-zero" not in text, "the exit-code instruction is still there"


# --- N1: the orchestrator must not train itself to branch on $? ------------


def test_the_pane_alive_check_does_not_chain_on_exit_codes() -> None:
    text = _norm(SKILL)
    assert "`hmad-dispatch alive codex` && `hmad-dispatch alive agy`" not in text, (
        "chaining on && branches on $?, the exact habit the signal-discipline "
        "invariant forbids — and `env` returns 0 even on PREFLIGHT: FAIL, so the "
        "chain reads a failure as success"
    )
    assert "requiring `PREFLIGHT: PASS`" in text, "no token-reading replacement was given"


# --- M2 / S1: recovery rows must be routable per transport and per agent ---


def test_the_5d_no_verdict_row_branches_by_transport() -> None:
    text = _norm(RECOVERY)
    assert "**exec path** (the DEFAULT transport)" in text, (
        "one blanket re-dispatch instruction is catastrophic on exec, where the "
        "work may already have landed and only the report was lost"
    )
    assert "do NOT re-dispatch" in text, "the dangerous action must be named as such"


def test_the_5e_no_verdict_row_covers_codex_not_just_agy() -> None:
    text = _norm(RECOVERY)
    assert "**codex GREEN dispatch**" in text, (
        "the row was scoped 5e/5e-review but its remedy only cleared agy — an "
        "operator following it re-dispatches the reviewer against an unimplemented tree"
    )
    assert text.count("`step5e:no_verdict:<module>`") >= 2, "the row was not split"


# --- S2: name the trap AND give the escape --------------------------------


def test_the_revert_sequence_makes_untracked_files_stashable() -> None:
    text = _norm(SKILL)
    # Assert the RUNNABLE line, not a mention. `git add -N` also appears in the
    # prose explaining it, so a bare substring check stays green while the actual
    # command is deleted from the block an agent copies — a mutation proved it.
    assert "git add -N -- <production-paths>" in text, (
        "without intent-to-add, `git stash push` stashes nothing and exits 0 on a "
        "new module — the revert silently no-ops and certifies GREEN"
    )
    assert "git stash push -- <production-paths>" in text, "the revert command itself is gone"
    assert "git stash pop" in text, "a revert with no documented restore loses the work"


def test_every_site_naming_the_stash_hazard_also_gives_the_fix() -> None:
    # The test above pins ONE site, and that is exactly how this regressed: the
    # `git add -N` fix was applied to SKILL.md's revert block while three other
    # places went on naming the hazard with no way to avoid it — including
    # codex-verifier-prompt.md, handed to an independent agent that cannot see
    # SKILL.md at all. A site-scoped assertion is a weak test: it stayed green
    # for all three. Enforce the invariant across every site instead.
    gaps = []
    for path in sorted(SKILL_DIR.rglob("*.md")):
        if "docs/handoffs" in str(path):
            continue
        lines = path.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines):
            if "stashes nothing" not in line:
                continue
            window = "\n".join(lines[max(0, i - 2):i + 6])
            # Only an actual INSTANCE of the hazard needs the fix beside it, and an
            # instance always names the command it is about. A doc that merely quotes
            # the phrase while teaching reviewers to hunt for this shape is not
            # committing it — `agy-skill-reviewer-prompt.md` lists "stashes nothing"
            # among the phrasings to grep for, and the first version of this guard
            # flagged it. Found only when the two branches were merged: the guard
            # lived on one, the prompt on the other, so neither side failed alone.
            if "git stash push" not in window:
                continue
            if "add -N" not in window:
                gaps.append(f"{path.relative_to(SKILL_DIR)}:{i + 1}")
    assert not gaps, (
        "these name the `git stash push` hazard without the `git add -N` fix that "
        f"avoids it — an agent given the rule and not the means improvises: {gaps}"
    )


def test_the_destructive_alternative_is_called_out() -> None:
    text = _norm(SKILL)
    assert "deletes** the new implementation" in text, (
        "git restore/checkout -- on uncommitted work is unrecoverable; the doc must "
        "say so or an agent reaches for the obvious command"
    )


# --- S3: the caveat must reach the reviewer that needs it ------------------


def test_the_spec_reviewer_is_told_presence_is_not_enforcement() -> None:
    text = _norm(SPEC_REVIEWER)
    assert "presence is not enforcement" in text.lower(), (
        "the spec review is diff-based, where a call site looks identical whether "
        "or not any test would fail when it is removed"
    )
    assert "wire-scoped revert" in text, (
        "the reviewer must know which downstream gate actually settles enforcement"
    )


def test_the_cited_invariant_exists() -> None:
    # A caveat citing a section that does not exist is a dangling reference.
    assert "## Connection enforcement" in _norm(BASE)


# --- the shared rule these fixes serve -------------------------------------


@pytest.mark.parametrize(
    "path,label",
    [(SKILL, "SKILL.md"), (BASE, "invariants.base.md")],
    ids=["skill", "invariants"],
)
def test_signal_discipline_is_still_stated_where_it_is_owned(path: Path, label: str) -> None:
    # The M1 and N1 fixes lean entirely on this rule. If it stops being stated in
    # the two files that own it — the invariant, and the phase steps that apply
    # it — the fixes read as arbitrary style choices and drift back out.
    #
    # Deliberately NOT asserted against failure-recovery.md: that file is a table
    # of halt routes and has no business restating the invariant. An earlier
    # draft of this test included it and failed, which is the test being wrong
    # rather than the doc.
    text = _norm(path)
    assert "never `$?`" in text or "exit 0" in text, (
        f"{label} no longer states the token-not-exit-code rule the fixes rely on"
    )
