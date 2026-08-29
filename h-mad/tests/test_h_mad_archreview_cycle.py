"""The 6a-prime loop was hand-assembled seven times in one session, and once more
while closing J43 in this one.

Seven mechanical steps, every one already prescribed by SKILL.md: rebuild the
prompt from `agy-architectural-reviewer-prompt.md`, substitute
feature/BASE/HEAD/diff/design, append the absolute-path instructions, re-stamp the
HEAD sha, dispatch `exec agy`, run the evidence gate on the log, extract
`ASSESSMENT:`. Two of them have no other home and are the two that get skipped:

  * **the BASE/HEAD stamp** — a stale sha silently reviews the PREVIOUS commit and
    reports cleanly, which is the J41 failure one level up; and
  * **the evidence gate** — `EVIDENCE: PASS tools=N` is the only thing separating a
    review that read from one that merely sounds like it did. Measured: a 6a-prime
    dispatch whose single `view_file` errored returned `READY_TO_MERGE` in 1510
    confident bytes, and rc, the extractor and the Phase-7 gate all took it.

Deliberately NOT modelled on `audit-cycle`, despite the candidate row asking for
"an audit-cycle for the architectural gate". That tool is a multi-pass verdict
COMBINER — it takes `--pass` specs of runs that already finished, fans out N
parallel passes, and rejects any phase outside plan/design/impl-plan. 6a-prime is
one reviewer re-run sequentially after fixes, emitting a word rather than finding
counts. Same name, different machine.

**This driver runs exactly one cycle and refuses to decide whether to run
another.** That judgement is the operator's: the seven-cycle run went to seven
because cycle 3 came back clean and cycle 4 then found a Critical vacuous pass. A
loop-until-clean driver would have stopped at three and shipped the defect.

Split into `stage` and `score` for the same reason `h_mad_assemble_tdd.py` stages
rather than dispatches: the dispatch is the side-effecting, agy-dependent,
minutes-long part, while assembly and scoring are pure and testable. Both halves
of the skip-prone pair land in the tested halves.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_archreview_cycle.py"

VALID_STATE = {
    "feature": "feat", "started_ts": "2026-08-28T00:00:00Z",
    "last_completed_phase": 5, "current_phase": 6, "phase": None,
    "audit_cycles": {"plan": 0, "design": 0, "impl_plan": 0},
    "iterate_cycles": 0, "halt_reason": None, "halt_ts": None,
}


def _state(tmp_path: Path) -> Path:
    p = tmp_path / "bkit.json"
    p.write_text(json.dumps({"orchestrator_state": {"feat": dict(VALID_STATE)}}),
                 encoding="utf-8")
    return p


def _log(tmp_path: Path, tools: int) -> Path:
    """A dispatch log carrying `tools` completed tool calls."""
    p = tmp_path / "run.log"
    # The shape `h_mad_review_evidence.scan` actually reads: a `step_update` whose
    # `step_type` is "tool" and whose `state` is DONE. Built from the real reader
    # rather than from memory of the log format — a fixture in the wrong shape
    # reports zero tools, which is indistinguishable from a review that read
    # nothing, and would have made every evidence assertion here vacuous.
    lines = []
    for i in range(tools):
        lines.append(json.dumps({
            "step_update": {"step_type": "tool", "state": "DONE", "name": f"view_file_{i}"},
        }))
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _review(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "review.md"
    p.write_text(body, encoding="utf-8")
    return p


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


class TestScoreRecordsOnlyAProvenReview:
    """The gate order is the contract: evidence BEFORE verdict, always."""

    def test_a_read_review_is_recorded_and_read_back(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 12)),
                      "--review", str(_review(tmp_path, "ok\nASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 0, result.stdout + result.stderr
        assert "ARCHREVIEW: READY_TO_MERGE" in result.stdout
        assert "tools=12" in result.stdout
        record = json.loads(state.read_text())["orchestrator_state"]["feat"]
        assert record["archreview"] == "READY_TO_MERGE"

    def test_a_review_that_read_nothing_is_refused_and_records_nothing(self, tmp_path):
        """The 1510-confident-bytes case. The verdict line says READY_TO_MERGE and
        it must not reach state — recording it is what made the defect survivable."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 0)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 2
        assert "ARCHREVIEW: NO_EVIDENCE" in result.stdout
        assert "step6a-prime:review_read_nothing" in result.stdout
        assert "archreview" not in json.loads(state.read_text())["orchestrator_state"]["feat"]

    def test_a_missing_verdict_is_refused_and_records_nothing(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 5)),
                      "--review", str(_review(tmp_path, "I looked at some files.\n")))

        assert result.returncode == 2
        assert "ARCHREVIEW: NO_VERDICT" in result.stdout
        assert "step6a-prime:no_verdict" in result.stdout
        assert "archreview" not in json.loads(state.read_text())["orchestrator_state"]["feat"]

    def test_a_failing_verdict_is_recorded_and_halts(self, tmp_path):
        """WITH_FIXES is a real verdict — it must be recorded, and it must halt."""
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 3)),
                      "--review", str(_review(tmp_path, "ASSESSMENT: WITH_FIXES\n")))

        assert result.returncode == 0, result.stdout
        assert "ARCHREVIEW: WITH_FIXES" in result.stdout
        assert "step6a-prime:architectural_review_failed" in result.stdout
        assert json.loads(state.read_text())["orchestrator_state"]["feat"]["archreview"] == "WITH_FIXES"

    def test_the_last_assessment_wins(self, tmp_path):
        """Same rule as every other extractor here: a log carries the prompt before
        the answer, so a first-match read returns the instruction's own echo."""
        state = _state(tmp_path)
        # BOTH lines must be line-anchored, or the regex sees one match and
        # first-vs-last is untestable. The first draft opened the echo with "emit",
        # which never matched — the mutation surviving is what exposed it, and a
        # tidy fixture is exactly how that hides.
        body = ("Instructions said:\n"
                "ASSESSMENT: READY_TO_MERGE\n"
                "...having actually read the diff...\n"
                "ASSESSMENT: WITH_FIXES\n")
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(_log(tmp_path, 4)),
                      "--review", str(_review(tmp_path, body)))

        assert "ARCHREVIEW: WITH_FIXES" in result.stdout, result.stdout

    def test_an_unreadable_log_is_a_cannot_judge_not_a_verdict(self, tmp_path):
        state = _state(tmp_path)
        result = _run("score", "--feature", "feat", "--state", str(state),
                      "--log", str(tmp_path / "nope.log"),
                      "--review", str(_review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")))

        assert result.returncode == 2
        assert "ARCHREVIEW: UNREADABLE" in result.stdout
        assert "READY_TO_MERGE" not in result.stdout

    def test_a_dropped_write_is_caught_by_the_readback(self, tmp_path):
        """`archreview` is not in the schema's `required`, so strict validation
        passes over a write that never landed. The read-back is the only check."""
        state = _state(tmp_path)
        log = _log(tmp_path, 4)
        review = _review(tmp_path, "ASSESSMENT: READY_TO_MERGE\n")
        # The DIRECTORY, not the file: the writer replaces atomically, and
        # `os.replace` needs only directory write permission — a read-only file is
        # still replaced. Simulating the drop the wrong way would have made this
        # test pass for a driver with no read-back at all.
        state.parent.chmod(0o555)
        try:
            result = _run("score", "--feature", "feat", "--state", str(state),
                          "--log", str(log), "--review", str(review))
            assert result.returncode == 2, result.stdout
            assert "ARCHREVIEW: NOT_RECORDED" in result.stdout
        finally:
            state.parent.chmod(0o755)


class TestStage:
    def _tpl(self, tmp_path):
        t = tmp_path / "tpl.md"
        t.write_text(
            "feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
            "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n"
            "summary <INLINE_PHASE_5_SUMMARY>\n", encoding="utf-8")
        return t

    def test_every_placeholder_is_substituted(self, tmp_path):
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / "p.txt"
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "aaa1111", "--head", "bbb2222",
                      "--design", str(design), "--diff-files", "a.py\nb.py",
                      "--summary", "did things", "--prompt", str(prompt))

        assert result.returncode == 0, result.stdout + result.stderr
        body = prompt.read_text(encoding="utf-8")
        assert "<INLINE_" not in body, body

    def test_an_unsubstituted_placeholder_is_refused(self, tmp_path):
        """A prompt shipped with a live `<INLINE_…>` in it asks the reviewer to
        review a placeholder, and it reads as a real prompt to everything else."""
        t = tmp_path / "tpl.md"
        t.write_text("feature <INLINE_FEATURE>\nmystery <INLINE_SOMETHING_ELSE>\n",
                     encoding="utf-8")
        design = tmp_path / "d.md"
        design.write_text("d\n", encoding="utf-8")
        result = _run("stage", "--feature", "feat", "--template", str(t),
                      "--base", "a", "--head", "b", "--design", str(design),
                      "--diff-files", "x.py", "--summary", "s",
                      "--prompt", str(tmp_path / "p.txt"))

        assert result.returncode == 2, result.stdout
        assert "ARCHREVIEW: UNSUBSTITUTED" in result.stdout
        assert "INLINE_SOMETHING_ELSE" in result.stdout

    def test_base_and_head_must_differ(self, tmp_path):
        """A stale stamp is the J41 failure one level up: BASE == HEAD reviews an
        empty diff and comes back clean, which reads exactly like a passing review."""
        design = tmp_path / "d.md"
        design.write_text("d\n", encoding="utf-8")
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "same", "--head", "same", "--design", str(design),
                      "--diff-files", "x.py", "--summary", "s",
                      "--prompt", str(tmp_path / "p.txt"))

        assert result.returncode == 2, result.stdout
        assert "ARCHREVIEW: DEGENERATE_RANGE" in result.stdout

    def test_the_printed_command_carries_the_log_the_score_step_needs(self, tmp_path):
        """`score` cannot run without `--log`, so staging must not print a dispatch
        that omits it — that is how the evidence gate gets skipped."""
        design = tmp_path / "d.md"
        design.write_text("d\n", encoding="utf-8")
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "aaa", "--head", "bbb", "--design", str(design),
                      "--diff-files", "x.py", "--summary", "s",
                      "--prompt", str(tmp_path / "p.txt"))

        assert "--log" in result.stdout
        assert "exec agy" in result.stdout


def test_it_refuses_to_decide_whether_to_run_another_cycle():
    """The one judgement this tool must never make.

    Asserted on the source because it is an absence, and an absence is exactly
    what nobody notices being added later. The seven-cycle run went to seven
    because cycle 3 was clean and cycle 4 then found a Critical vacuous pass; a
    loop-until-clean driver would have stopped at three and shipped it.
    """
    import ast

    # The AST, not the text: both `while`s in this file are prose in the module
    # docstring, and a grep over the source called them loops. Asserting on
    # executable structure is the only version of this that means anything.
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    loops = [n for n in ast.walk(tree) if isinstance(n, (ast.While, ast.For))]
    assert loops == [] or all(
        not isinstance(n, ast.While) for n in loops
    ), "no while-loop: one cycle per invocation, the operator decides on another"


class TestSummaryReachesTheReviewer:
    """#31 — `--summary` took a literal string while `--design` read a file.

    An operator who writes the Phase-5 summary to a file and passes
    `--summary /tmp/summary.md` gets the PATH substituted into the prompt, not
    the 35 lines they wrote. `--design` is `type=Path` and is `read_text()`;
    `--summary` was neither. The staging still reported STAGED, and the two
    architectural review legs ran without the context they were given.

    The tell was byte length: two stagings with DIFFERENT summary files produced
    prompts of identical size, because both substituted a path of equal length.
    """

    def _tpl(self, tmp_path):
        t = tmp_path / "tpl.md"
        t.write_text(
            "feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
            "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n"
            "summary <INLINE_PHASE_5_SUMMARY>\n", encoding="utf-8")
        return t

    def _stage(self, tmp_path, summary_arg, prompt_name="p.txt"):
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / prompt_name
        result = _run("stage", "--feature", "feat", "--template", str(self._tpl(tmp_path)),
                      "--base", "aaa1111", "--head", "bbb2222",
                      "--design", str(design), "--diff-files", "a.py",
                      "--summary", summary_arg, "--prompt", str(prompt))
        return result, prompt

    def test_a_summary_file_is_read_not_pasted_as_a_path(self, tmp_path):
        body_text = "Task 7 rewrote the transport guard and re-pinned the anchor.\n"
        summary = tmp_path / "phase5_summary.md"
        summary.write_text(body_text, encoding="utf-8")

        result, prompt = self._stage(tmp_path, str(summary))

        assert result.returncode == 0, result.stdout + result.stderr
        staged = prompt.read_text(encoding="utf-8")
        assert body_text.strip() in staged, (
            "the summary FILE's contents never reached the prompt — the path was "
            "substituted instead, so the reviewer read a filename"
        )
        assert str(summary) not in staged, "the path itself must not be pasted in"

    def test_two_different_summary_files_produce_different_prompts(self, tmp_path):
        """The byte-length tell: equal-length paths made distinct summaries look identical."""
        a = tmp_path / "sum_a.md"
        b = tmp_path / "sum_b.md"
        a.write_text("Alpha finding: the flush fires before the disclosure.\n", encoding="utf-8")
        b.write_text("Beta finding: the guard reads a different field entirely.\n", encoding="utf-8")

        _r1, p1 = self._stage(tmp_path, str(a), "p1.txt")
        _r2, p2 = self._stage(tmp_path, str(b), "p2.txt")

        assert p1.read_text(encoding="utf-8") != p2.read_text(encoding="utf-8")

    def test_an_inline_summary_string_still_works(self, tmp_path):
        """Back-compat: a literal summary that is not a path must still substitute."""
        result, prompt = self._stage(tmp_path, "did things inline")

        assert result.returncode == 0, result.stdout + result.stderr
        assert "did things inline" in prompt.read_text(encoding="utf-8")

    def test_a_missing_summary_file_is_a_staging_failure(self, tmp_path):
        """A path-shaped argument that does not exist must not be pasted as text."""
        result, prompt = self._stage(tmp_path, str(tmp_path / "does_not_exist.md"))

        assert result.returncode != 0, result.stdout + result.stderr
        assert not prompt.exists(), "a failed staging must not leave a prompt behind"

    def test_a_value_whose_slot_is_absent_is_a_staging_failure(self, tmp_path):
        """#31's other half: a required value with no slot reaches nobody.

        The existing guard catches the inverse — a slot left UNSUBSTITUTED. A
        template that simply lacks the slot leaves nothing behind, so it passed.
        """
        t = tmp_path / "no_summary_slot.md"
        t.write_text(
            "feature <INLINE_FEATURE>\nbase <INLINE_BASE_SHA>\nhead <INLINE_HEAD_SHA>\n"
            "files <INLINE_DIFF_FILES>\ndesign <INLINE_AUDITED_DESIGN>\n", encoding="utf-8")
        design = tmp_path / "d.md"
        design.write_text("the design\n", encoding="utf-8")
        prompt = tmp_path / "p.txt"

        result = _run("stage", "--feature", "feat", "--template", str(t),
                      "--base", "aaa1111", "--head", "bbb2222",
                      "--design", str(design), "--diff-files", "a.py",
                      "--summary", "did things", "--prompt", str(prompt))

        assert result.returncode != 0, result.stdout + result.stderr
        assert "INLINE_PHASE_5_SUMMARY" in (result.stdout + result.stderr)
