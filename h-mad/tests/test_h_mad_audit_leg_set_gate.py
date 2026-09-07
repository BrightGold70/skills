"""H3 — a clean streak counts only over an UNCHANGED leg set.

Measured on HemaSuite `#18 gateway-consolidation` and recorded in
`gateway-consolidation.audit-ledger.md`: Sigma-must tracked the LEG COUNT, not
document quality. The last 13 design cycles ran `3 3 7 5 3 5 4 3 8 4 7 12 6`
must-fixes, and every rise coincided with a leg being added or returning
(teammate c87, doc-auditor+crossdoc c92, codex c97). The two-consecutive-both-
clean exit was therefore RESET by new legs four times and never once approached
by the documents. 99 cycles, exit streak zero.

The defect is not that a leg was added. It is that adding one silently reset a
streak nobody was counting, so the loop could not distinguish "the documents got
worse" from "we started asking a new question". H3's remedy is to make the leg
set part of what a streak is measured OVER: two cycles close the exit gate only
if they asked the SAME question, and changing the question starts a new
baseline by construction -- two fresh cycles under the new set.

**Provably wrong only.** A stamp that records no leg set is NOT blocked. Every
stamp written before this field existed has none, and a gate that refuses them
would fire on cycles that were legitimately clean -- the calibration error this
repo has already paid for (`docs/learnings.md`: detectors written as hard fired
104/49/48 times on documents that had passed 74-83 cycles). Unrecorded is
reported as unrecorded, on the EXIT line and again at stamp time, which is what
keeps it from becoming prose an orchestrator can skip.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
    for line in out.splitlines():
        if line.startswith(prefix):
            return line
    return ""


class TestTheStampCarriesTheLegSet:
    def _stamped(self, tmp_path: Path, legs: list[str] | None) -> dict:
        audit = tmp_path / "f.design.audit.v1.md"
        audit.write_text(CLEAN, encoding="utf-8")
        doc = tmp_path / "f.design.md"
        doc.write_text("body\n", encoding="utf-8")
        argv = [str(audit), "--gated", str(doc)]
        for leg in legs or []:
            argv += ["--legs", leg]
        assert run(*argv).returncode == 0
        return json.loads(gate.stamp_path(audit).read_text(encoding="utf-8"))

    def test_the_legs_are_recorded_sorted_and_deduped(self, tmp_path: Path) -> None:
        """Order is not a leg-set change, and neither is naming one twice."""
        assert self._stamped(tmp_path, ["codex", "agy", "codex"])["legs"] == ["agy", "codex"]

    def test_an_unrecorded_leg_set_is_null_never_an_empty_list(self, tmp_path: Path) -> None:
        """`[]` would claim a cycle ran zero legs. It claims nothing instead."""
        assert self._stamped(tmp_path, None)["legs"] is None

    def test_stamping_without_legs_says_so_on_its_own_line(self, tmp_path: Path) -> None:
        """Non-skippable at the point of use, not only at the exit gate."""
        audit = tmp_path / "f.design.audit.v1.md"
        audit.write_text(CLEAN, encoding="utf-8")
        doc = tmp_path / "f.design.md"
        doc.write_text("body\n", encoding="utf-8")
        out = run(str(audit), "--gated", str(doc)).stdout
        assert "GATE-LEGS: unrecorded" in out

    def test_the_gate_line_is_untouched_by_the_leg_set(self, tmp_path: Path) -> None:
        """`h_mad_audit_cycle.GATE_RE` anchors on `should=N\\s*$`.

        A fifth field on line 1 makes every verdict un-parse — the same reason
        GATE-CLASS and SUITE are their own lines.
        """
        audit = tmp_path / "f.design.audit.v1.md"
        audit.write_text(CLEAN, encoding="utf-8")
        doc = tmp_path / "f.design.md"
        doc.write_text("body\n", encoding="utf-8")
        line = token(run(str(audit), "--gated", str(doc), "--legs", "codex").stdout, "GATE:")
        assert "legs" not in line


class TestTheExitGateRefusesAChangedLegSet:
    def _stamp(self, tmp_path: Path, name: str, legs, verdict: str = "PASS",
               suite: str = "PASS") -> Path:
        p = tmp_path / name
        payload = {"verdict": verdict, "files": {}, "suite": suite}
        if legs is not None:
            payload["legs"] = legs
        p.write_text(json.dumps(payload), encoding="utf-8")
        return p

    def test_two_cycles_on_the_same_leg_set_are_READY(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", ["agy", "codex"])
        b = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex"])
        out = run("x", "--exit-check", str(a), str(b))
        assert out.returncode == 0
        assert token(out.stdout, "EXIT:").startswith("EXIT: READY")

    def test_a_leg_added_between_the_two_cycles_BLOCKS(self, tmp_path: Path) -> None:
        """THE defect: c92 added doc-auditor+crossdoc and the streak silently reset."""
        a = self._stamp(tmp_path, "v1.gated.json", ["agy", "codex"])
        b = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex", "doc-auditor"])
        line = token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")
        assert "BLOCKED" in line
        assert "legs_changed:agy+codex|agy+codex+doc-auditor" in line

    def test_a_leg_dropped_between_the_two_cycles_BLOCKS(self, tmp_path: Path) -> None:
        """Removing a leg is the cheaper way to reach a clean streak, so it blocks too."""
        a = self._stamp(tmp_path, "v1.gated.json", ["agy", "codex"])
        b = self._stamp(tmp_path, "v2.gated.json", ["codex"])
        assert "legs_changed" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_leg_order_alone_is_not_a_change(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", ["codex", "agy"])
        b = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex"])
        assert "READY" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_two_fresh_cycles_under_the_new_set_close_the_gate(self, tmp_path: Path) -> None:
        """The declared new baseline — it falls out, no extra flag needed."""
        old = self._stamp(tmp_path, "v1.gated.json", ["agy", "codex"])
        a = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex", "doc-auditor"])
        b = self._stamp(tmp_path, "v3.gated.json", ["agy", "codex", "doc-auditor"])
        assert "READY" in token(
            run("x", "--exit-check", str(old), str(a), str(b)).stdout, "EXIT:")

    def test_an_unrecorded_leg_set_does_not_block(self, tmp_path: Path) -> None:
        """Provably wrong only. Every pre-H3 stamp has no legs and was not wrong."""
        a = self._stamp(tmp_path, "v1.gated.json", None)
        b = self._stamp(tmp_path, "v2.gated.json", None)
        out = run("x", "--exit-check", str(a), str(b))
        assert out.returncode == 0
        assert "READY" in token(out.stdout, "EXIT:")

    def test_a_mixed_recorded_and_unrecorded_pair_does_not_block(self, tmp_path: Path) -> None:
        """One cycle stamped before H3 and one after is a CANNOT-JUDGE, not a mismatch.

        The discriminating case for the comparison guard, and the reason the
        both-unrecorded test cannot stand in for it: with the guard removed,
        `None != ["agy","codex"]` is True and the pair blocks with a
        `legs_changed` naming a set that was never recorded. Two unrecorded
        cycles compare equal even without the guard, so that pair proves nothing
        about it — a mutation battery pointed there is killed by the wrong
        assertion.
        """
        a = self._stamp(tmp_path, "v1.gated.json", None)
        b = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex"])
        out = run("x", "--exit-check", str(a), str(b))
        assert out.returncode == 0
        assert "READY" in token(out.stdout, "EXIT:")
        assert "legs_changed" not in out.stdout

    def test_an_unrecorded_leg_set_is_REPORTED_on_the_exit_line(self, tmp_path: Path) -> None:
        """Not blocking is not the same as not saying — silence is how H3 becomes prose."""
        a = self._stamp(tmp_path, "v1.gated.json", None)
        b = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex"])
        assert "legs=unrecorded" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_a_recorded_streak_names_its_leg_set(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "v1.gated.json", ["agy", "codex"])
        b = self._stamp(tmp_path, "v2.gated.json", ["agy", "codex"])
        assert "legs=agy+codex" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_a_red_suite_still_outranks_the_leg_set(self, tmp_path: Path) -> None:
        """#91's refusal is not softened by adding a second one beside it."""
        a = self._stamp(tmp_path, "v1.gated.json", ["agy"], suite="PASS")
        b = self._stamp(tmp_path, "v2.gated.json", ["agy"], suite="FAIL")
        assert "suite_fail" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")


class TestDocumented:
    def test_the_skill_names_the_leg_set_flag(self) -> None:
        text = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        assert "--legs" in text
