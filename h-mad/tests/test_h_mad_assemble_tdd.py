"""Tests for `h_mad_assemble_tdd.py`.

The assembler's job is to make five recorded hand-assembly mistakes
unrepeatable, so most of these assert the emitted command or a refusal. But a
gate that refuses everything ships nothing, so `TestAssembles` pins that a
well-formed RED and GREEN actually stage a prompt with the slots filled and the
phase stamped.

Fixtures are cut from the real HemaSuite impl-plan corpus, including a `wiring`
task with its WIRE/WIRE-PIN lines — the shape whose counts cannot gate it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from h_mad_assemble_tdd import (  # noqa: E402
    Halt,
    assemble,
    command_block,
    interpreter_has_pytest,
    task_body,
)

SCRIPT = SCRIPTS / "h_mad_assemble_tdd.py"
TEMPLATE = SKILL_DIR / "references" / "codex-implementer-prompt.md"

# A real interpreter that has pytest — this one, since it is running these tests.
PYTHON = sys.executable

PLAN = """# Feature impl-plan

## Task 1: gate-mechanism

- **Task shape**: new-behaviour
**Production**: `protocol/crf_gating.py`

### A sub-heading inside the task body

More task detail that must not be truncated.

## Task 2: seam-wiring

- **Task shape**: wiring (connects the resolver to the composer)
- **WIRE**: `crf_engine.build` -> `crf_composer.compose`
- **WIRE-PIN**: `test_composer_receives_the_resolved_ctx`

Body of the wiring task.

## Task 3: unpinned-wiring

- **Task shape**: wiring

Body with no pin at all.
"""


@pytest.fixture()
def plan(tmp_path: Path) -> Path:
    target = tmp_path / "feature.impl-plan.md"
    target.write_text(PLAN, encoding="utf-8")
    return target


def call(plan: Path, tmp_path: Path, **kw):
    args = dict(
        feature="feat", task_id="Task 1", phase="red", impl_plan=plan,
        project_root=tmp_path, module="mod", test_path="tests/test_mod.py",
        python=PYTHON, expect_fail=3, expect_pass=1, guards=[],
        report_file="", template=TEMPLATE,
    )
    args.update(kw)
    return assemble(**args)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


class TestTaskSlicing:
    def test_a_task_body_is_not_truncated_at_its_own_sub_heading(self) -> None:
        body = task_body(PLAN, "Task 1")
        assert "A sub-heading inside the task body" in body
        assert "must not be truncated" in body

    def test_a_task_body_stops_at_the_next_task(self) -> None:
        body = task_body(PLAN, "Task 1")
        assert "seam-wiring" not in body

    def test_the_last_task_runs_to_the_end_of_the_file(self) -> None:
        assert "Body with no pin at all." in task_body(PLAN, "Task 3")

    def test_an_unknown_task_halts(self) -> None:
        with pytest.raises(Halt) as exc:
            task_body(PLAN, "Task 9")
        assert exc.value.reason == "task_not_found"


class TestAssembles:
    def test_a_well_formed_red_fills_every_slot(self, plan: Path, tmp_path: Path) -> None:
        filled, meta = call(plan, tmp_path)
        assert meta["task"] == "Task 1"
        assert "<INLINE_" not in filled
        assert "<REPORT_FILE_PATH>" not in filled

    def test_the_phase_is_stamped_because_the_template_carries_both(
        self, plan: Path, tmp_path: Path
    ) -> None:
        red, _ = call(plan, tmp_path, phase="red")
        green, _ = call(plan, tmp_path, phase="green")
        assert "PHASE 5d (RED)" in red and "PHASE 5e (GREEN)" not in red
        assert "PHASE 5e (GREEN)" in green and "PHASE 5d (RED)" not in green

    def test_the_stated_counts_reach_the_prompt(self, plan: Path, tmp_path: Path) -> None:
        filled, _ = call(plan, tmp_path, expect_fail=5, expect_pass=2)
        assert "5 failing, 2 passing" in filled

    def test_guards_are_named_so_an_immediate_pass_is_not_manufactured_away(
        self, plan: Path, tmp_path: Path
    ) -> None:
        filled, _ = call(plan, tmp_path, guards=["test_a", "test_b"])
        assert "test_a, test_b" in filled
        assert "do NOT manufacture" in filled

    def test_no_guards_says_so_rather_than_omitting_the_line(
        self, plan: Path, tmp_path: Path
    ) -> None:
        filled, _ = call(plan, tmp_path, guards=[])
        assert "**Regression guards:** none in this task." in filled

    def test_a_green_dispatch_needs_no_counts(self, plan: Path, tmp_path: Path) -> None:
        filled, _ = call(plan, tmp_path, phase="green", expect_fail=None, expect_pass=None)
        assert "PHASE 5e (GREEN)" in filled


class TestWiringShape:
    def test_a_wiring_task_carries_its_wire_and_pin(self, plan: Path, tmp_path: Path) -> None:
        filled, meta = call(plan, tmp_path, task_id="Task 2",
                            expect_fail=None, expect_pass=None)
        assert meta["shape"] == "wiring"
        assert "test_composer_receives_the_resolved_ctx" in filled
        assert "crf_composer.compose" in filled

    def test_a_wiring_task_is_not_refused_for_missing_counts(
        self, plan: Path, tmp_path: Path
    ) -> None:
        """Counts cannot gate a wiring task — the RED split is identical either way."""
        filled, _ = call(plan, tmp_path, task_id="Task 2",
                         expect_fail=None, expect_pass=None)
        # Asserted against the emitted LINE, not the bare word: the shipped
        # template's own prose contains "instead of failing, and a hang…".
        assert "**Expected after this dispatch:**" not in filled
        assert "**Regression guards" not in filled

    def test_a_wiring_task_without_a_pin_halts(self, plan: Path, tmp_path: Path) -> None:
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, task_id="Task 3", expect_fail=None, expect_pass=None)
        assert exc.value.reason == "no_wire_pin"

    def test_the_pin_is_told_what_its_red_must_be(self, plan: Path, tmp_path: Path) -> None:
        filled, _ = call(plan, tmp_path, task_id="Task 2",
                         expect_fail=None, expect_pass=None)
        assert "never a missing" in filled


class TestTheFiveRecordedMistakes:
    """One test per hand-assembly mistake the row records."""

    def test_1_the_model_is_pinned_because_the_default_cannot_execute_tools(
        self, tmp_path: Path
    ) -> None:
        block = command_block(
            feature="f", module="m", phase="red", prompt=tmp_path / "p.txt",
            out=tmp_path / "o", log=tmp_path / "l", timeout=900, model="gpt-5.5",
            python=PYTHON, test_path="tests/t.py", project_root=tmp_path,
        )
        assert "--model gpt-5.5" in block

    def test_2_an_interpreter_without_pytest_is_refused_with_a_suggestion(
        self, plan: Path, tmp_path: Path
    ) -> None:
        fake = tmp_path / "python-no-pytest"
        fake.write_text('#!/bin/sh\nexit 1\n', encoding="utf-8")
        fake.chmod(0o755)
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, python=str(fake))
        assert exc.value.reason == "interpreter_has_no_pytest"
        assert "try " in exc.value.detail

    def test_3_the_prompt_is_passed_as_a_path_not_inline(self, tmp_path: Path) -> None:
        prompt = tmp_path / "p.txt"
        block = command_block(
            feature="f", module="m", phase="red", prompt=prompt,
            out=tmp_path / "o", log=tmp_path / "l", timeout=900, model="gpt-5.5",
            python=PYTHON, test_path="tests/t.py", project_root=tmp_path,
        )
        assert f"exec codex {prompt}" in block

    def test_4_a_read_only_sandbox_is_refused_for_a_run_that_executes_pytest(
        self, plan: Path, tmp_path: Path
    ) -> None:
        proc = run_cli(
            "--feature", "f", "--task", "Task 1", "--phase", "red",
            "--project-root", str(tmp_path), "--module", "m",
            "--test-path", "tests/t.py", "--impl-plan", str(plan),
            "--expect-fail", "3", "--expect-pass", "1",
            "--python", PYTHON, "--sandbox", "read-only",
        )
        assert proc.returncode == 2
        assert "HALT sandbox_read_only" in proc.stdout
        assert "tempdir" in proc.stdout

    def test_5_the_scoped_test_path_is_stated_and_bounded(
        self, plan: Path, tmp_path: Path
    ) -> None:
        filled, _ = call(plan, tmp_path, test_path="tests/test_mod.py")
        assert "pytest tests/test_mod.py -v" in filled
        assert "Do not widen it" in filled


class TestJudgementIsNotAutomated:
    def test_a_red_without_counts_is_refused_not_defaulted(
        self, plan: Path, tmp_path: Path
    ) -> None:
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, expect_fail=None, expect_pass=None)
        assert exc.value.reason == "counts_required"

    @pytest.mark.parametrize("missing", ["expect_fail", "expect_pass"])
    def test_half_the_counts_is_still_refused(
        self, plan: Path, tmp_path: Path, missing: str
    ) -> None:
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, **{missing: None})
        assert exc.value.reason == "counts_required"

    def test_zero_is_a_stated_count_not_an_absent_one(
        self, plan: Path, tmp_path: Path
    ) -> None:
        """`--expect-pass 0` must not be read as "not given" — 0 is a real answer."""
        filled, _ = call(plan, tmp_path, expect_fail=0, expect_pass=0)
        assert "0 failing, 0 passing" in filled


class TestPreflight:
    def test_a_template_with_an_unknown_slot_halts(
        self, plan: Path, tmp_path: Path
    ) -> None:
        bad = tmp_path / "bad-template.md"
        bad.write_text("<INLINE_TASK_FROM_IMPL_PLAN>\n<INLINE_SOMETHING_ELSE>\n",
                       encoding="utf-8")
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, template=bad)
        assert exc.value.reason == "residual_slots"
        assert "INLINE_SOMETHING_ELSE" in exc.value.detail

    def test_bare_prose_mentions_of_a_slot_are_not_residuals(
        self, plan: Path, tmp_path: Path
    ) -> None:
        """Prose names a slot bare; only a real slot is bracketed.

        The shipped template's own header says "with `INLINE_*` placeholders
        substituted". A preflight that matched bare names would refuse every
        assembly against the real template.
        """
        filled, _ = call(plan, tmp_path)
        assert "`INLINE_*` placeholders substituted" in filled

    def test_an_unreadable_impl_plan_halts(self, tmp_path: Path) -> None:
        with pytest.raises(Halt) as exc:
            call(tmp_path / "absent.md", tmp_path)
        assert exc.value.reason == "impl_plan_unreadable"


class TestCli:
    def test_a_clean_assembly_prints_pass_and_the_command_block(
        self, plan: Path, tmp_path: Path
    ) -> None:
        prompt = tmp_path / "prompt.txt"
        proc = run_cli(
            "--feature", "f", "--task", "Task 1", "--phase", "red",
            "--project-root", str(tmp_path), "--module", "m",
            "--test-path", "tests/t.py", "--impl-plan", str(plan),
            "--expect-fail", "3", "--expect-pass", "1",
            "--python", PYTHON, "--prompt", str(prompt),
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "ASSEMBLE-TDD: PASS" in proc.stdout
        assert "hmad-dispatch exec codex" in proc.stdout
        assert "h_mad_extract_verdict.py" in proc.stdout
        assert "--key STATUS" in proc.stdout
        assert prompt.exists()

    def test_the_block_re_runs_the_tests_independently_of_the_verdict(
        self, plan: Path, tmp_path: Path
    ) -> None:
        proc = run_cli(
            "--feature", "f", "--task", "Task 1", "--phase", "red",
            "--project-root", str(tmp_path), "--module", "m",
            "--test-path", "tests/t.py", "--impl-plan", str(plan),
            "--expect-fail", "3", "--expect-pass", "1", "--python", PYTHON,
        )
        assert "Re-run the tests yourself" in proc.stdout
        assert f"{PYTHON} -m pytest tests/t.py -v" in proc.stdout

    def test_a_halt_exits_two_and_writes_no_prompt(
        self, plan: Path, tmp_path: Path
    ) -> None:
        prompt = tmp_path / "prompt.txt"
        proc = run_cli(
            "--feature", "f", "--task", "Task 9", "--phase", "red",
            "--project-root", str(tmp_path), "--module", "m",
            "--test-path", "tests/t.py", "--impl-plan", str(plan),
            "--expect-fail", "3", "--expect-pass", "1",
            "--python", PYTHON, "--prompt", str(prompt),
        )
        assert proc.returncode == 2
        assert "HALT task_not_found" in proc.stdout
        assert not prompt.exists()

    def test_the_dispatch_is_backgrounded_and_polled_never_tailed(
        self, plan: Path, tmp_path: Path
    ) -> None:
        """A foreground exec prints nothing until exit; `tail -f` never returns."""
        proc = run_cli(
            "--feature", "f", "--task", "Task 1", "--phase", "red",
            "--project-root", str(tmp_path), "--module", "m",
            "--test-path", "tests/t.py", "--impl-plan", str(plan),
            "--expect-fail", "3", "--expect-pass", "1", "--python", PYTHON,
        )
        assert "--timeout 900 &" in proc.stdout
        assert "hmad-dispatch progress" in proc.stdout
        assert "tail -f" not in proc.stdout

    def test_the_hmad_marker_is_emitted(self, plan: Path, tmp_path: Path) -> None:
        proc = run_cli(
            "--feature", "f", "--task", "Task 1", "--phase", "red",
            "--project-root", str(tmp_path), "--module", "m",
            "--test-path", "tests/t.py", "--impl-plan", str(plan),
            "--expect-fail", "3", "--expect-pass", "1", "--python", PYTHON,
        )
        assert "[H-MAD] f tdd-assemble red Task 1" in proc.stdout


class TestRealCorpus:
    def test_the_shipped_template_assembles_without_residual_slots(
        self, plan: Path, tmp_path: Path
    ) -> None:
        filled, _ = call(plan, tmp_path, template=TEMPLATE)
        assert "<INLINE_" not in filled
        assert "<REPORT_FILE_PATH>" not in filled
        assert "STATUS: <DONE" in filled, "the report contract must survive assembly"

    def test_the_report_file_slot_is_filled_when_given(
        self, plan: Path, tmp_path: Path
    ) -> None:
        filled, _ = call(plan, tmp_path, report_file="/tmp/report.md")
        assert "/tmp/report.md" in filled

    def test_this_interpreter_has_pytest(self) -> None:
        """Guards the probe itself: a detector that always returns False would
        make every `interpreter_has_no_pytest` refusal vacuous."""
        assert interpreter_has_pytest(PYTHON)


class TestDocsPin:
    def test_the_token_is_registered_in_skill_md(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text()
        assert "h_mad_assemble_tdd.py" in skill
        assert "ASSEMBLE-TDD: PASS" in skill

    def test_every_halt_reason_is_documented(self) -> None:
        import re as _re
        script = SCRIPT.read_text()
        skill = (SKILL_DIR / "SKILL.md").read_text()
        reasons = set(_re.findall(r'Halt\(\s*"([a-z_]+)"', script))
        assert reasons, "no halt reasons found in the script"
        undocumented = sorted(r for r in reasons if r not in skill)
        assert not undocumented, f"undocumented halt reasons: {undocumented}"


class TestSurfacedByReview:
    """Findings from an adversarial review of the shipped assembler."""

    def test_a_typod_slot_is_still_a_residual(self, plan: Path, tmp_path: Path) -> None:
        """`<INLINE_MODULE-NAME>` evaded an `[A-Z_]+` pattern completely.

        A raw slot reaching the agent reads as an unfilled template and is
        silently discounted, so the one thing the preflight must not do is miss
        a slot because it was misspelled.
        """
        bad = tmp_path / "typo-template.md"
        bad.write_text("<INLINE_TASK_FROM_IMPL_PLAN>\n<INLINE_MODULE-NAME>\n", encoding="utf-8")
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, template=bad)
        assert exc.value.reason == "residual_slots"
        assert "INLINE_MODULE-NAME" in exc.value.detail

    def test_a_lowercase_slot_is_still_a_residual(self, plan: Path, tmp_path: Path) -> None:
        bad = tmp_path / "lower-template.md"
        bad.write_text("<INLINE_TASK_FROM_IMPL_PLAN>\n<INLINE_feature>\n", encoding="utf-8")
        with pytest.raises(Halt) as exc:
            call(plan, tmp_path, template=bad)
        assert exc.value.reason == "residual_slots"

    def test_a_path_with_spaces_is_quoted_in_the_block(self, tmp_path: Path) -> None:
        """Raw interpolation splits a spaced path into two shell arguments."""
        block = command_block(
            feature="f", module="m", phase="red", prompt=tmp_path / "p.txt",
            out=tmp_path / "o", log=tmp_path / "l", timeout=900, model="gpt-5.5",
            python="/opt/my python/bin/python3", test_path="tests/a b.py",
            project_root=tmp_path,
        )
        assert "'/opt/my python/bin/python3'" in block
        assert "'tests/a b.py'" in block

    def test_the_block_halts_when_the_dispatch_fails(self, tmp_path: Path) -> None:
        """Otherwise it reads a missing --out file and runs pytest anyway,
        turning a dispatch that never ran into a verdict-shaped nothing."""
        block = command_block(
            feature="f", module="m", phase="red", prompt=tmp_path / "p.txt",
            out=tmp_path / "o", log=tmp_path / "l", timeout=900, model="gpt-5.5",
            python=PYTHON, test_path="tests/t.py", project_root=tmp_path,
        )
        guard = 'if [ "$rc" -ne 0 ]; then'
        assert guard in block
        assert block.index(guard) < block.index("h_mad_extract_verdict.py")
