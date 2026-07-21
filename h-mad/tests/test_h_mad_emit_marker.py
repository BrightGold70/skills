"""Tests for h_mad_emit_marker.sh — the [H-MAD] marker writer.

Markers are the greppable progress stream for a run, so a malformed one
corrupts anything parsing that stream after the fact. These tests pin the
output shape and the argument contract.
"""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_emit_marker.sh"


def emit(*args):
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestDocumentedForm:
    """phase-table.md documents: emit_marker.sh <feature> <N> <decision>"""

    def test_bare_phase_number(self):
        r = emit("myfeat", "2", "gate_passed")
        assert r.returncode == 0
        assert r.stdout.strip() == "[H-MAD] myfeat phase2 gate_passed"

    def test_multiword_decision_is_preserved(self):
        r = emit("myfeat", "5", "spec drafted")
        assert r.stdout.strip() == "[H-MAD] myfeat phase5 spec drafted"

    def test_sub_step_phase_label(self):
        r = emit("myfeat", "5d", "red_not_all_failing")
        assert r.stdout.strip() == "[H-MAD] myfeat phase5d red_not_all_failing"


class TestPhasePrefixIsIdempotent:
    """Regression: a caller passing an already-prefixed phase produced
    `phasephase2`. Prefixing must not double."""

    def test_already_prefixed_is_not_doubled(self):
        r = emit("myfeat", "phase2", "gate_passed")
        assert r.returncode == 0
        assert "phasephase" not in r.stdout
        assert r.stdout.strip() == "[H-MAD] myfeat phase2 gate_passed"

    def test_already_prefixed_sub_step(self):
        r = emit("myfeat", "phase6a-prime", "architectural_review_failed")
        assert "phasephase" not in r.stdout
        assert r.stdout.strip() == (
            "[H-MAD] myfeat phase6a-prime architectural_review_failed"
        )


class TestArgumentContract:
    """Regression: a missing decision silently became `?`, emitting a
    malformed marker into the stream instead of failing."""

    @pytest.mark.parametrize(
        "args",
        [
            (),
            ("myfeat",),
            ("myfeat", "2"),
        ],
        ids=["no-args", "feature-only", "no-decision"],
    )
    def test_missing_args_fail_loudly(self, args):
        r = emit(*args)
        assert r.returncode == 2, f"expected exit 2 for {args!r}"
        assert r.stdout.strip() == "", "must not emit a partial marker"
        assert "usage" in r.stderr.lower()

    def test_never_emits_the_question_mark_placeholder(self):
        """The exact wild garble: `[H-MAD] <feature> phasephase2 spec drafted ?`
        came from a 2-arg call whose phase carried the description."""
        r = emit("myfeat", "phase2 spec drafted")
        assert r.returncode == 2
        assert r.stdout.strip() == ""

    def test_extra_args_rejected(self):
        r = emit("myfeat", "2", "gate_passed", "stray")
        assert r.returncode == 2
        assert r.stdout.strip() == ""

    def test_empty_string_args_rejected(self):
        r = emit("myfeat", "", "gate_passed")
        assert r.returncode == 2
        assert r.stdout.strip() == ""
