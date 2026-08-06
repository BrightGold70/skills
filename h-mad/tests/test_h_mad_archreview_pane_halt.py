"""6a-prime must halt when no reviewer pane resolves, never skip silently.

5d refuses and halts on a missing pane (`step5d:no_<agent>_pane`). 6a-prime had
no equivalent instruction, so with `agy -> UNRESOLVED` — the normal state in any
session not started beside a reviewer — the step was simply passed over and the
run continued to 6a.

That is the worst step to lose without noticing. 6a-prime is the only pass
positioned to catch design-level problems: drift between design and spec, an
exception hierarchy that does not scale, a gate placed at the wrong altitude.
Both a document-reading audit and a code-reading gap analysis miss those by
construction.

A skipped review must also survive into Phase 7, or a feature closes with the
reader believing an architectural review happened.
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
RECOVERY = SKILL_DIR / "references" / "failure-recovery.md"
PROTOCOLS = SKILL_DIR / "references" / "inline-protocols.md"

HALT = "step6a-prime:no_reviewer_pane"


def skill() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def recovery() -> str:
    return RECOVERY.read_text(encoding="utf-8")


def protocols() -> str:
    return PROTOCOLS.read_text(encoding="utf-8")


def section_6a_prime() -> str:
    """The §6a-prime bullet, sliced at its real boundary.

    These tests used a magic `s[idx : idx + 1600]` window. The bullet is now
    1707 characters, so the last 107 sat outside every assertion — and the ban
    on prescribing `h_mad_state_validate.py` passed only because the sentence
    mentioning it fell past the cliff. The nearest required phrase had 76
    characters of margin, so any added sentence would have silently pushed a
    guard out of scope and broken it for an unrelated reason.
    """
    s = skill()
    start = s.find("**6a-prime**")
    assert start != -1, "§6a-prime bullet not found"
    end = s.find("- **6a**", start)
    assert end != -1, "§6a-prime bullet has no terminating `- **6a**`"
    return s[start:end]


class TestPreflightHalt:
    def test_skill_md_defines_the_halt(self):
        assert HALT in skill()

    def test_halt_has_a_recovery_route(self):
        """Every halt reason needs an entry, or the operator gets a token and
        no way forward."""
        assert HALT in recovery()

    def test_preflight_requires_the_agy_cli_not_a_pane(self):
        """The preflight checks for the executable, not a resolved reviewer pane."""
        section = section_6a_prime()
        assert "command -v agy" in section
        # Assert the OLD prescription is gone, rather than banning the substring
        # "resolved pane": the sibling test requires the section to say it does
        # NOT require a resolved pane, and a blanket ban would contradict it —
        # making the two tests mutually unsatisfiable and GREEN unreachable.
        assert "hmad-dispatch alive agy" not in section
        assert "alive agy" not in section

    def test_names_cli_absence_as_the_trigger(self):
        """The retained halt is now for an unavailable `agy` CLI."""
        section = section_6a_prime()
        assert "the `agy` CLI is absent" in section


class TestSkipIsRecorded:
    def test_state_records_the_operator_override(self):
        section = section_6a_prime()
        assert "SKIPPED_OPERATOR_OVERRIDE" in section

    def test_skip_surfaces_in_the_phase_7_report(self):
        """A closure report that omits this lets a feature ship looking
        reviewed when it was not."""
        p = protocols()
        start = p.index("## Phase 7")
        section = p[start:]
        assert "SKIPPED_NO_PANE" in section or "architectural review" in section.lower()

    def test_phase_7_skip_blocks_and_headless_review_satisfies_gate(self):
        s = skill()
        start = s.index("7. **Closure (autonomous)**")
        end = s.index("\n## Phase 5", start)
        section = s[start:end]
        assert (
            "A `SKIPPED_NO_PANE` archreview **blocks** the gate — "
            "a headless `exec agy` review satisfies the gate."
        ) in section

    def test_skipping_is_explicitly_not_a_pass(self):
        # NB: do NOT .lower() the section — the asserted phrase carries the
        # upper-case enum value, so a lowercased haystack can never match it and
        # the test would fail even with the sentence present verbatim.
        section = section_6a_prime()
        assert "`SKIPPED_OPERATOR_OVERRIDE` is not a pass" in section

    def test_exec_agy_satisfies_the_gate_without_a_resolved_pane(self):
        section = section_6a_prime()
        assert "`exec agy` satisfies the gate" in section
        assert "does not require a resolved pane" in section

    def test_no_pane_is_not_the_ordinary_skip_response(self):
        section = section_6a_prime()
        assert "SKIPPED_OPERATOR_OVERRIDE" in section
        assert "SKIPPED_NO_PANE" not in section

    def test_state_writes_extracted_assessment_to_archreview(self):
        section = section_6a_prime()
        assert (
            "write the extracted `ASSESSMENT:` into "
            "`orchestrator_state[<feature>].archreview`" in section
        )

    def test_state_write_is_verified_by_readback_comparison(self):
        section = section_6a_prime()
        assert (
            "read `orchestrator_state[<feature>].archreview` back and compare it "
            "to the value written" in section
        )
        # Assert the validator is NOT PRESCRIBED, rather than banning the string.
        # The section legitimately names it in order to warn against it, and a
        # blanket ban forbade the warning as well as the mistake — it passed only
        # because that sentence happened to fall outside the old 1600-char window.
        assert "do not rely on h_mad_state_validate.py --strict-only" in section

    def test_extraction_capture_is_line_scoped(self):
        """The extractor prints its `[H-MAD]` marker to STDOUT, so the obvious
        `$(...)` capture yields two lines and the writer refuses the value.

        Observed live on this feature's own 6a-prime: the write was rejected and
        the read-back reported `None`. This section is the first consumer that
        captures the extractor's output instead of reading it by eye, so the
        instruction has to say so or it walks the reader into the trap.
        """
        section = section_6a_prime()
        assert "prints its `[H-MAD]` marker to stdout" in section
        assert "sed -n 's/^ASSESSMENT: //p'" in section


class TestExistingHaltsIntact:
    """The two verdict-driven halts must survive this change."""

    def test_review_failed_halt_still_present(self):
        assert "step6a-prime:architectural_review_failed" in skill()
        assert "step6a-prime:architectural_review_failed" in recovery()

    def test_no_verdict_halt_still_present(self):
        assert "step6a-prime:no_verdict" in skill()
        assert "step6a-prime:no_verdict" in recovery()


class TestSchemaAcceptsTheKey:
    """SKILL.md tells the orchestrator to write `archreview`. The strict schema
    sets additionalProperties:false, so the key has to be declared or every
    record following that instruction fails --strict-only validation. This is
    the invent-a-key drift the two-tier validator exists to prevent."""

    def test_archreview_is_a_declared_property(self):
        import json

        schema = json.loads(
            (SKILL_DIR / "scripts" / "h_mad_state_schema.json").read_text()
        )
        assert "archreview" in schema["properties"]

    def test_skipped_no_pane_is_an_allowed_value(self):
        import json

        schema = json.loads(
            (SKILL_DIR / "scripts" / "h_mad_state_schema.json").read_text()
        )
        assert "SKIPPED_NO_PANE" in schema["properties"]["archreview"]["enum"]

    def test_a_record_carrying_it_validates_strict(self):
        import json
        import sys

        sys.path.insert(0, str(SKILL_DIR / "scripts"))
        import h_mad_state_validate as sv

        record = {
            "feature": "f",
            "started_ts": "2026-07-22T00:00:00Z",
            "last_completed_phase": 6,
            "current_phase": 6,
            "phase": None,
            "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 1},
            "iterate_cycles": 0,
            "halt_reason": None,
            "halt_ts": None,
            "archreview": "SKIPPED_NO_PANE",
        }
        assert sv.classify(record) == "strict"
