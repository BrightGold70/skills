"""FR-10 documentation pins for resolved Phase 5 implementer authorship."""

import json
import os
from pathlib import Path
import re
import subprocess

from docsections import titled_section


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
AGY_RUNTIME = ROOT / "references" / "agy-runtime.md"
PHASE5_HEADING = "Codex authors Phase 5 — enforced, not just instructed"
EXEC_HEADING = "Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot"
STAGING_ANCHOR = "- **Stage the implementer.**"


def _section(path: Path, heading: str) -> str:
    return titled_section(path.read_text(encoding="utf-8"), heading)


def _staging_bullet() -> str:
    text = SKILL.read_text(encoding="utf-8")
    assert text.count(STAGING_ANCHOR) == 1, (
        "SKILL.md must contain exactly one '- **Stage the implementer.**' bullet "
        "with the resolver command and fail-closed dispatch branches"
    )
    # Same paragraph split as test_h_mad_tdd_gate_docs._skill_gate_bullet.
    return text.split(STAGING_ANCHOR, 1)[1].split("\n\n", 1)[0]


def record_failed_branch_refuses_dispatch(bullet: str) -> bool:
    """Check the record-failure branch before reading the later switch fields."""
    start = bullet.find("record=failed")
    switch = bullet.find("switch=none")
    if start < 0 or switch <= start:
        return False
    span = " ".join(bullet[start:switch].split())
    return all(
        token in span.lower()
        for token in (
            "do not dispatch", "halt", "step5:implementer_switch_unrecorded",
            "[h-mad]", "first",
        )
    )


def test_phase5_authorship_section_names_the_resolver_and_agy_authorship():
    section = _section(SKILL, PHASE5_HEADING)
    for token in (
        "h_mad_tdd_judge.py implementer", "agy-authorship", "implementer-invalid",
        "FR-2", "FR-3", "codex", "agy",
        "Phase 5 implementation is **Codex's job**",
    ):
        assert token in section, f"Phase 5 authorship must document {token!r}"


def test_phase5_authorship_section_states_the_agy_upgrade_trigger():
    section = " ".join(_section(SKILL, PHASE5_HEADING).split())
    assert re.search(r"agy\s+upgrade", section, re.IGNORECASE), (
        "Phase 5 authorship must require re-verification after any agy upgrade"
    )
    for token in ("FR-8", "step 2", "step 2a", "class-(a)", "inventory"):
        assert token in section, f"agy upgrade trigger must name {token!r}"
    assert re.search(r"re[- ]?run", section, re.IGNORECASE), (
        "agy upgrade trigger must require re-running FR-8 steps 2 and 2a"
    )
    assert re.search(r"re[- ]?take", section, re.IGNORECASE), (
        "agy upgrade trigger must require re-taking the class-(a) inventory"
    )


def test_exit_code_dispatch_section_lists_exec_agy_as_an_implementer():
    section = _section(SKILL, EXEC_HEADING)
    assert any("exec agy" in line and "implement" in line.lower()
               for line in section.splitlines()), (
        "exit-code dispatch must name exec agy as an implementer on the same line"
    )
    assert "TDD-IMPLEMENTER:" in section, (
        "exit-code dispatch must stage authorship using the TDD-IMPLEMENTER: token"
    )


def test_teammate_bullet_separates_audit_selection_from_authorship():
    text = SKILL.read_text(encoding="utf-8")
    anchor = "- **It does not license Claude to write Phase 5 production code"
    assert text.count(anchor) == 1, "expected one teammate Phase 5 authorship bullet"
    bullet = text.split(anchor, 1)[1].split("\n\n", 1)[0]
    for token in ("h_mad_tdd_judge.py implementer", "agy-authorship",
                  "ACTIVE", "every", "unavailable", "exhausted"):
        assert token in bullet, f"teammate audit/authorship bullet must state {token!r}"


def test_agy_runtime_tdd_gate_names_the_agy_gate_and_keeps_the_halt():
    section = _section(AGY_RUNTIME, "The TDD gate")
    for token in ("h-mad-agy-tdd-gate.py", "AGY-GATE:",
                  "step5:agy_tdd_hook_unverified", "halt"):
        assert token in section, f"agy TDD gate contract must document {token!r}"


def test_agy_runtime_sessionstart_claim_is_rechecked_and_stamped():
    hooks = _section(AGY_RUNTIME, "Hooks")
    mapping = _section(AGY_RUNTIME, "Construct mapping")
    rows = [line for line in mapping.splitlines()
            if line.startswith("| `hook-event` |")]
    assert len(rows) == 1, "Construct mapping must have one hook-event row"
    for surface, text in (("Hooks", hooks), ("hook-event row", rows[0])):
        plain = text.replace("`", "").replace("**", "")
        assert "SessionStart" in plain, f"{surface} must document SessionStart"
        assert not re.search(r"\bno\s+SessionStart\b", plain, re.IGNORECASE), (
            f"{surface} must remove the obsolete 'no SessionStart' claim"
        )
        assert "1.4.0" in text, (
            f"{surface} must stamp the SessionStart re-check against installed agy 1.4.0"
        )


def test_staging_step_runs_the_verb_with_record_and_names_every_branch():
    bullet = _staging_bullet()
    normalized = " ".join(bullet.split())
    command = ('python3 ~/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py '
               'implementer --root . --feature "$FEATURE" --record')
    assert command in normalized, "implementer staging must run the resolver with --record"
    assert re.search(r"[^.!?]*\bnever\b[^.!?]*\$\?", normalized, re.IGNORECASE), (
        "implementer staging must say in one sentence to read the token, never $?"
    )
    for token in (
        "TDD-IMPLEMENTER:", "record=failed", "switch=none", "switch=codex->agy",
        "switch=agy->codex", "reason=", "switch=peers-out", "invalid field=",
        "no-record", "unreadable", "h_mad_assemble_tdd.py --agent", "codex", "agy",
        "step5:implementer_invalid", "step5:implementer_unresolved", "[H-MAD]",
    ):
        assert token in bullet, f"implementer staging must document branch/contract {token!r}"
    for requirement in (r"before\s+every\s+5d\s+and\s+5e", r"project\s+root",
                        r"always\s+exits?\s+0"):
        assert re.search(requirement, normalized, re.IGNORECASE), (
            f"implementer staging must state {requirement!r}"
        )


def test_staging_step_halts_on_record_failed_before_any_dispatch():
    assert record_failed_branch_refuses_dispatch(_staging_bullet()), (
        "record=failed must first forbid dispatch, halt step5:implementer_switch_unrecorded, "
        "and print its [H-MAD] marker before switch=none is read"
    )


def test_record_failed_check_rejects_a_procedure_that_dispatches():
    # Model agent-authored procedure text with the shared hostile input knob.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("HMAD_STUB_")}
    env["HMAD_STUB_HOSTILE"] = "all"
    result = subprocess.run(
        ["bash", str(ROOT / "tests" / "stubs" / "orca"), "worktree", "set"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"hostile procedure fixture failed: {result.stderr}"
    payload = json.loads(result.stdout)["result"]["worktree"]["comment"]
    halt = ("Check this branch first: do not dispatch. Halt "
            "step5:implementer_switch_unrecorded and print "
            "[H-MAD] <feature> halt step5:implementer_switch_unrecorded.")
    valid = (f"{STAGING_ANCHOR} {payload}\n"
             f"record=failed: {halt}\n"
             "switch=none: stage the resolved peer and dispatch.")
    assert record_failed_branch_refuses_dispatch(valid), (
        "record-failure checker must accept a correctly ordered halt with hostile text"
    )
    controls = {
        "dispatches after failed record": valid.replace(
            halt, "stage the resolved peer and dispatch.", 1),
        "halt sentence deleted": valid.replace(halt, "", 1),
        "halt without marker": valid.replace("[H-MAD]", "", 1),
        "record failure after switch fields": (
            f"{STAGING_ANCHOR} {payload}\n"
            f"switch=none: stage the peer. record=failed: {halt}"
        ),
    }
    for defect, doctored in controls.items():
        assert not record_failed_branch_refuses_dispatch(doctored), (
            f"record-failure checker must reject a procedure that {defect}"
        )
