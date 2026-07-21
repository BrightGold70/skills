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


class TestPreflightHalt:
    def test_skill_md_defines_the_halt(self):
        assert HALT in skill()

    def test_halt_has_a_recovery_route(self):
        """Every halt reason needs an entry, or the operator gets a token and
        no way forward."""
        assert HALT in recovery()

    def test_preflight_checks_the_pane_before_dispatching(self):
        """Mirrors 5d: confirm alive, refuse if missing."""
        s = skill()
        idx = s.find("**6a-prime**")
        assert idx != -1
        section = s[idx : idx + 1600]
        assert "alive" in section.lower()

    def test_names_unresolved_as_the_trigger(self):
        """`UNRESOLVED` is what `hmad-dispatch env` actually prints."""
        s = skill()
        idx = s.find("**6a-prime**")
        assert "UNRESOLVED" in s[idx : idx + 1600]


class TestSkipIsRecorded:
    def test_state_records_a_skipped_review(self):
        s = skill()
        assert "SKIPPED_NO_PANE" in s

    def test_skip_surfaces_in_the_phase_7_report(self):
        """A closure report that omits this lets a feature ship looking
        reviewed when it was not."""
        p = protocols()
        start = p.index("## Phase 7")
        section = p[start:]
        assert "SKIPPED_NO_PANE" in section or "architectural review" in section.lower()

    def test_skipping_is_explicitly_not_a_pass(self):
        s = skill()
        idx = s.find("**6a-prime**")
        section = s[idx : idx + 1600].lower()
        assert "not" in section and (
            "ready_to_merge" in section or "pass" in section
        )


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
