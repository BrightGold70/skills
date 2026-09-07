"""#91 — the Phase 3/4 audit cycle never ran the project test suite.

Measured on HemaSuite `#18 gateway-consolidation`: a dual-surface design audit ran
95 cycles without meeting its exit gate while a repo test enforcing the AUDIT
LOOP'S OWN invariant stayed red for the entire life of the feature. Before this,
`h_mad_audit_gate.py` had zero occurrences of `subprocess|pytest|check_call|
os.system` — a document scorer with no execution path — and SKILL.md ran pytest
only at 5e and 5f.

Two decisions are pinned here.

**Gate-level, not protocol-level.** The 5f precedent is protocol-level, but
nothing counts the streak (`grep -in 'streak|consecutive'` over `scripts/` returns
nothing), so "a red suite blocks the exit" written as prose is an instruction an
orchestrator can skip — which is what 91 cycles already demonstrated.

**A red suite blocks the EXIT, not each cycle.** Blocking every cycle makes an
audit hostage to an unrelated flaky test, and `docs/skill-candidates.md:1277`
records two pytest runs over one working tree producing 6 and 3 failures in
different sets, and 0 when the file ran alone.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
SCRIPT = SCRIPTS / "h_mad_audit_gate.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_audit_gate as gate  # noqa: E402

CLEAN = """# Audit

## Summary
Fine.

## Must-fix
- None

## Should-fix
- None

## Nit
- None
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def token(out: str, prefix: str) -> str:
    lines = [l for l in out.splitlines() if l.startswith(prefix)]
    assert len(lines) == 1, f"expected one {prefix} line, got {lines!r}"
    return lines[0]


def fake_suite(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    p.chmod(0o755)
    return p


class TestTheGateNowExecutes:
    """It had no execution path at all; that was the defect."""

    def test_the_script_can_run_a_suite(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        assert "subprocess.run" in text, (
            "the gate is a document scorer again — 95 cycles ran past a red test "
            "because nothing here executed anything")

    def test_a_green_suite_is_reported_on_its_own_line(self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "green.sh", 'echo "12 passed in 0.1s"')
        result = run(str(audit), "--project-tests", str(tmp_path),
                     "--suite-cmd", str(sh))
        assert result.returncode == 0, result.stderr
        assert token(result.stdout, "SUITE:") == "SUITE: PASS passed=12 failed=0"
        assert token(result.stdout, "GATE:").startswith("GATE: PASS")

    def test_the_suite_line_is_separate_from_the_gate_line(self, tmp_path: Path) -> None:
        """`h_mad_audit_cycle.GATE_RE` anchors on `should=N\\s*$`, so anything woven
        into the GATE line makes every verdict un-parse. Same reason GATE-CLASS is
        its own line."""
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "green.sh", 'echo "3 passed in 0.1s"')
        out = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout
        assert "suite" not in token(out, "GATE:").lower()

    def test_without_the_flag_nothing_runs_and_the_output_is_unchanged(
            self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        out = run(str(audit)).stdout
        assert "SUITE:" not in out, "every existing caller must be unaffected"


class TestARedSuiteDoesNotHostageTheCycle:
    def test_a_failing_suite_leaves_the_cycle_verdict_alone(self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "red.sh", 'echo "1 failed, 11 passed in 0.2s"; exit 1')
        result = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh))
        assert token(result.stdout, "SUITE:") == "SUITE: FAIL passed=11 failed=1"
        assert token(result.stdout, "GATE:").startswith("GATE: PASS"), (
            "the document is clean; a flaky unrelated test must not make it dirty")


class TestTheSuiteVerdictIsScoredOnTheSummary:
    """Never on the exit code: a skipped selection and a killed run both exit 0."""

    def test_a_zero_exit_with_a_red_summary_is_FAIL(self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "liar.sh", 'echo "2 failed, 5 passed in 0.1s"; exit 0')
        out = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout
        assert "SUITE: FAIL" in out

    def test_no_summary_is_UNREADABLE_not_PASS_and_not_FAIL(self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "silent.sh", 'echo "collected 0 items"; exit 0')
        out = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout
        assert token(out, "SUITE:") == "SUITE: UNREADABLE reason=no_summary"

    def test_an_empty_selection_is_not_a_pass(self, tmp_path: Path) -> None:
        """`pytest -k` collecting nothing exits 0 — this repo has been fooled.

        The summary PARSES here (`0 passed`), which is what makes this
        discriminating: a stub printing only "no tests ran" never reaches the
        verdict logic at all, so it exercised nothing and a mutant that dropped
        the guard survived it.
        """
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "empty.sh", 'echo "0 passed in 0.01s"; exit 0')
        out = run(str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout
        assert token(out, "SUITE:") == "SUITE: UNREADABLE reason=no_tests_ran"

    def test_a_run_that_says_only_no_tests_ran_is_also_refused(self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        sh = fake_suite(tmp_path, "silent2.sh", 'echo "no tests ran in 0.01s"; exit 5')
        assert "SUITE: PASS" not in run(
            str(audit), "--project-tests", str(tmp_path), "--suite-cmd", str(sh)).stdout

    def test_a_missing_command_is_UNREADABLE(self, tmp_path: Path) -> None:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        out = run(str(audit), "--project-tests", str(tmp_path),
                  "--suite-cmd", str(tmp_path / "nope.sh")).stdout
        assert token(out, "SUITE:").startswith("SUITE: UNREADABLE")


class TestTheStampCarriesTheSuite:
    def _stamped(self, tmp_path: Path, body: str | None) -> dict:
        audit = tmp_path / "f.plan.audit.v1.codex.md"
        audit.write_text(CLEAN, encoding="utf-8")
        gated = tmp_path / "f.plan.md"
        gated.write_text("doc\n", encoding="utf-8")
        argv = [str(audit), "--gated", str(gated)]
        if body is not None:
            argv += ["--project-tests", str(tmp_path),
                     "--suite-cmd", str(fake_suite(tmp_path, "s.sh", body))]
        assert run(*argv).returncode == 0
        return json.loads(gate.stamp_path(audit).read_text(encoding="utf-8"))

    def test_a_measured_green_suite_is_recorded(self, tmp_path: Path) -> None:
        assert self._stamped(tmp_path, 'echo "9 passed in 0.1s"')["suite"] == "PASS"

    def test_a_measured_red_suite_is_recorded(self, tmp_path: Path) -> None:
        assert self._stamped(tmp_path, 'echo "1 failed, 8 passed"; exit 1')["suite"] == "FAIL"

    def test_an_unmeasured_suite_is_null_never_PASS(self, tmp_path: Path) -> None:
        """A cycle that never ran the suite has not shown it green."""
        assert self._stamped(tmp_path, None)["suite"] is None


class TestTheExitGateIsWhatRefuses:
    def _stamp(self, tmp_path: Path, name: str, verdict: str, suite) -> Path:
        # REAL grammar (see test_h_mad_audit_leg_set_gate.py): a cycle emits one
        # stamp per leg, and `vN.gated.json` cannot express that.
        n = re.match(r"v(\d+)\.gated\.json$", name)
        p = tmp_path / (f"f.design.audit.v{n.group(1)}.codex.md.gated.json" if n else name)
        p.write_text(json.dumps({"verdict": verdict, "files": {}, "suite": suite}),
                     encoding="utf-8")
        return p

    def test_two_clean_green_cycles_are_READY(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", "PASS", "PASS")
        b = self._stamp(tmp_path, "v2.gated.json", "PASS", "PASS")
        out = run("x", "--exit-check", str(a), str(b))
        assert out.returncode == 0
        assert token(out.stdout, "EXIT:").startswith("EXIT: READY")

    def test_a_red_suite_in_either_cycle_blocks(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", "PASS", "PASS")
        b = self._stamp(tmp_path, "v2.gated.json", "PASS", "FAIL")
        assert "BLOCKED reason=suite_fail:f.design.audit.v2.codex.md.gated.json" in token(
            run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_an_unmeasured_suite_blocks_too(self, tmp_path: Path) -> None:
        """Silence is not a pass — the whole defect in one assertion."""
        a = self._stamp(tmp_path, "v1.gated.json", "PASS", "PASS")
        b = self._stamp(tmp_path, "v2.gated.json", "PASS", None)
        assert "suite_unmeasured" in token(
            run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_only_the_last_two_cycles_count(self, tmp_path: Path) -> None:
        old = self._stamp(tmp_path, "v1.gated.json", "PASS", "FAIL")
        a = self._stamp(tmp_path, "v2.gated.json", "PASS", "PASS")
        b = self._stamp(tmp_path, "v3.gated.json", "PASS", "PASS")
        assert "READY" in token(run("x", "--exit-check", str(old), str(a), str(b)).stdout, "EXIT:")

    def test_a_dirty_cycle_blocks(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", "PASS", "PASS")
        b = self._stamp(tmp_path, "v2.gated.json", "FAIL", "PASS")
        assert "not_clean" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_one_cycle_is_not_a_streak(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", "PASS", "PASS")
        assert "not_two_cycles:1" in token(run("x", "--exit-check", str(a)).stdout, "EXIT:")

    def test_an_unreadable_stamp_is_a_cannot_judge_at_exit_2(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", "PASS", "PASS")
        b = tmp_path / "v2.gated.json"
        b.write_text("{not json", encoding="utf-8")
        result = run("x", "--exit-check", str(a), str(b))
        assert result.returncode == 2
        assert "UNREADABLE" in token(result.stdout, "EXIT:")


class TestDocumented:
    def test_the_skill_routes_phases_3_and_4_through_the_suite_run(self) -> None:
        text = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        assert "--project-tests" in text
        assert "--exit-check" in text
