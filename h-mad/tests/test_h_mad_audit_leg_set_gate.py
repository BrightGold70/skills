"""H3 — a clean streak counts only over an UNCHANGED leg set.

Measured on HemaSuite `#18 gateway-consolidation` and recorded in
`gateway-consolidation.audit-ledger.md`: Sigma-must tracked the LEG COUNT, not
document quality. The 13 design cycles ending at c99 ran `3 3 7 5 3 5 4 3 8 4 7 12 6`
must-fixes, and every rise coincided with a leg being added or returning
(teammate c87, doc-auditor+crossdoc c92, codex c97). The two-consecutive-both-
clean exit was therefore RESET by new legs four times and never once approached
by the documents. Zero at c99 when this was measured, still zero at c104; the
series has grown since, so re-derive it from the ledger rather than reading the
window above as current.

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
import re
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

    def test_a_leg_set_that_strips_to_nothing_is_also_null(self, tmp_path: Path) -> None:
        """`--legs ""` makes argparse's list TRUTHY, and the strip empties it again.

        Guarding on `args.legs` rather than on the normalised result stamped
        `[]` — a RECORDED empty set — while `GATE-LEGS:` printed `unrecorded`,
        so the stamp and the line disagreed about the same cycle. `[]` then
        compares unequal to any real set and blocks with `legs_changed:-|agy`.
        """
        assert self._stamped(tmp_path, ["", "  "])["legs"] is None

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
        # REAL grammar, not `v1.gated.json`: the tidy fixture is exactly what let a
        # same-cycle leg pair read as a two-cycle streak for as long as it did.
        n = re.match(r"v(\d+)\.gated\.json$", name)
        p = tmp_path / (f"f.design.audit.v{n.group(1)}.codex.md.gated.json" if n else name)
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


class TestAStreakIsTwoCyclesNotTwoStamps:
    """A cycle emits one stamp PER LEG, so "the last two stamps" is not "two cycles".

    Measured 2026-09-07 on real archived artifacts: of 17 cycles carrying stamps,
    **8 have two**, and same-cycle legs sort ADJACENTLY, so a glob feeds
    `--exit-check` two legs of ONE cycle. Executed against the shipped gate, the
    pair `doc-block-exec.design.audit.v20.codex` + `…v20.p1` returned
    `EXIT: READY … legs=agy+codex` — the exit gate certified a two-consecutive-
    clean-cycle streak from a single cycle.

    H3 made it read WORSE rather than catching it: both legs of one cycle carry the
    same declared leg set, so the leg check passes and lends false confidence.

    Neither existing gate could see this. The offline fixtures were named
    `v1.gated.json` / `v2.gated.json` — synthetic, distinct-by-construction — and
    the field tracer used v43 and v44, distinct by construction too. Tidy fixtures
    hiding a defect class, which is why the fixtures below carry the REAL grammar.
    """

    def _stamp(self, tmp_path: Path, feature: str, phase: str, cycle: int, leg: str,
               legs=("agy", "codex"), verdict: str = "PASS", suite: str = "PASS") -> Path:
        p = tmp_path / f"{feature}.{phase}.audit.v{cycle}.{leg}.md.gated.json"
        payload = {"verdict": verdict, "files": {}, "suite": suite}
        if legs is not None:
            payload["legs"] = list(legs)
        p.write_text(json.dumps(payload), encoding="utf-8")
        return p

    def test_two_legs_of_ONE_cycle_are_not_a_streak(self, tmp_path: Path) -> None:
        """THE defect, reproduced from the real archived pair."""
        a = self._stamp(tmp_path, "doc-block-exec", "design", 20, "codex")
        b = self._stamp(tmp_path, "doc-block-exec", "design", 20, "p1")
        line = token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")
        assert "BLOCKED" in line
        assert "not_two_cycles:1" in line

    def test_two_distinct_cycles_are_a_streak(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "doc-block-exec", "design", 20, "codex")
        b = self._stamp(tmp_path, "doc-block-exec", "design", 21, "codex")
        out = run("x", "--exit-check", str(a), str(b))
        assert out.returncode == 0
        assert "READY" in token(out.stdout, "EXIT:")

    def test_every_leg_of_a_counted_cycle_must_be_clean(self, tmp_path: Path) -> None:
        """One dirty leg makes the whole cycle dirty — a cycle is not clean per-leg."""
        a = self._stamp(tmp_path, "f", "design", 20, "codex")
        b = self._stamp(tmp_path, "f", "design", 21, "codex")
        self._stamp(tmp_path, "f", "design", 21, "p1", verdict="FAIL")
        line = token(run("x", "--exit-check", str(a), str(b),
                         str(tmp_path / "f.design.audit.v21.p1.md.gated.json")).stdout, "EXIT:")
        assert "BLOCKED" in line and "not_clean" in line

    def test_a_red_suite_on_any_leg_of_a_cycle_blocks(self, tmp_path: Path) -> None:
        a = self._stamp(tmp_path, "f", "design", 20, "codex")
        b = self._stamp(tmp_path, "f", "design", 21, "codex")
        c = self._stamp(tmp_path, "f", "design", 21, "p1", suite="FAIL")
        assert "suite_fail" in token(
            run("x", "--exit-check", str(a), str(b), str(c)).stdout, "EXIT:")

    def test_a_name_outside_the_grammar_is_UNREADABLE_never_a_pass(self, tmp_path: Path) -> None:
        """Fail closed: a stamp whose cycle cannot be established is a cannot-judge.

        `A.json` is exactly what the 2026-09-07 field tracer wrote, and it is why
        that run could not have caught this.
        """
        a = self._stamp(tmp_path, "f", "design", 20, "codex")
        b = tmp_path / "A.json"
        b.write_text(json.dumps({"verdict": "PASS", "files": {}, "suite": "PASS",
                                 "legs": ["agy", "codex"]}), encoding="utf-8")
        result = run("x", "--exit-check", str(a), str(b))
        assert result.returncode == 2
        assert "UNREADABLE" in token(result.stdout, "EXIT:")

    def test_impl_plan_parses_as_one_phase_not_plan(self, tmp_path: Path) -> None:
        """`impl-plan` must win the alternation, or the feature absorbs `impl`."""
        a = self._stamp(tmp_path, "f", "impl-plan", 20, "codex")
        b = self._stamp(tmp_path, "f", "impl-plan", 21, "codex")
        assert "READY" in token(run("x", "--exit-check", str(a), str(b)).stdout, "EXIT:")

    def test_the_two_NEWEST_cycles_count_not_the_first_two(self, tmp_path: Path) -> None:
        """v9 vs v10 must order numerically; lexically `v10` sorts before `v9`."""
        self._stamp(tmp_path, "f", "design", 8, "codex", verdict="FAIL")
        a = self._stamp(tmp_path, "f", "design", 9, "codex")
        b = self._stamp(tmp_path, "f", "design", 10, "codex")
        old = tmp_path / "f.design.audit.v8.codex.md.gated.json"
        assert "READY" in token(
            run("x", "--exit-check", str(old), str(a), str(b)).stdout, "EXIT:")

    def test_legs_must_agree_across_the_legs_of_one_cycle(self, tmp_path: Path) -> None:
        """Two stamps of one cycle declaring different leg sets is a cannot-judge."""
        self._stamp(tmp_path, "f", "design", 20, "codex")
        self._stamp(tmp_path, "f", "design", 21, "codex", legs=("agy", "codex"))
        self._stamp(tmp_path, "f", "design", 21, "p1", legs=("codex",))
        out = run("x", "--exit-check", *[str(p) for p in sorted(tmp_path.glob("*.gated.json"))])
        assert "legs_disagree" in token(out.stdout, "EXIT:")
