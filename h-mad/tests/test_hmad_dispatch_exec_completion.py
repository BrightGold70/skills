"""`exec agy` lingers after its `result` event — wait on the SIGNAL, not the pid.

Taken-over brief `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`
(Handover-From HemaSuite, Taken-Over-By skills 2026-09-03, never started). Measured
during 29 dual-surface design audits: twice, `hmad-dispatch exec agy … --timeout 1800`
kept running the FULL 30 minutes after agy had finished. The `--log` ends with the
`{"event":"result",…}` JSON and the `<report>.done` marker exists within ~4 minutes,
but the wrapper waits on the PID, so the caller pays the whole timeout and gets
`rc=124` — which a coordinator reads as "no verdict" and re-dispatches work already on
disk. Codex on the same runner exits normally every time.

**Completion signal is not process exit.** That is the whole finding, and it is the
same shape `h_mad_collect_report.py` already handles from the other side: the report is
delivered while the producer's state says otherwise.

The real defect is intermittent — 2 of 29, the 18th and 29th of identical dispatches —
so it is not reproducible on demand. It is deterministically SIMULABLE, which is what
these tests do: a fake child that emits the terminal event and then sleeps stands in
for agy lingering, and the control that omits the signal proves the flag is what
changed the outcome rather than the fixture being fast.
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "hmad-dispatch.sh"

RESULT_LINE = '{"event":"result","result":{"response":"done"}}'


def _function(name: str) -> str:
    source = SCRIPT.read_text()
    starts = list(re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\(\) \{", source))
    for i, match in enumerate(starts):
        if match.group(1) == name:
            end = starts[i + 1].start() if i + 1 < len(starts) else len(source)
            return source[match.start():end]
    return ""


# NOTE ON TIMING ASSERTIONS. Only UPPER bounds are asserted, and only with wide
# margin (a 30s deadline against `< 10s`). A lower bound is flaky AND redundant:
# bash's `SECONDS` is an integer sampled once, so `deadline = SECONDS + 3` gives an
# effective wait anywhere in ~2.0-3.0s -- measured 2.449s on a 3s deadline, failing
# 2 runs in 3 against `>= 2.5`. It is redundant because `rc == 124` already proves
# the run reached the deadline rather than the completion path, which is the property
# under test. A flaky gate is worse than none: it trains its reader to ignore red.
def _run_exec(args: str, tmp_path: Path) -> tuple[int, float]:
    """Call `_exec_run` with `args`; return (rc, wall-clock seconds)."""
    body = _function("_exec_run")
    helper = _function("_exec_completed")
    assert body, "could not extract _exec_run"
    assert helper, "could not extract _exec_completed"
    script = f"{helper}\n{body}\n_exec_run {args}\n"
    start = time.monotonic()
    proc = subprocess.run(["bash", "-c", script], cwd=str(tmp_path),
                          capture_output=True, text=True)
    return proc.returncode, time.monotonic() - start


def _lingering_agent(tmp_path: Path, log: Path, *, emit: bool, sleep: int = 30) -> str:
    """A child that (optionally) emits the terminal event, then refuses to exit."""
    agent = tmp_path / "fake_agent.sh"
    emit_line = f'printf "%s\\n" {RESULT_LINE!r} >> {str(log)!r}' if emit else ":"
    agent.write_text(f"#!/bin/sh\n{emit_line}\nsleep {sleep}\n", encoding="utf-8")
    agent.chmod(0o755)
    return str(agent)


class TestCompletionSignalEndsTheWait:
    def test_a_result_event_stops_the_wait_long_before_the_deadline(
        self, tmp_path: Path
    ) -> None:
        """THE defect: 30 minutes of waiting after the work was done."""
        log = tmp_path / "t.log"
        log.write_text("", encoding="utf-8")
        agent = _lingering_agent(tmp_path, log, emit=True)
        rc, elapsed = _run_exec(
            f"--complete-log {log} 30 {agent}", tmp_path)
        assert rc == 0, f"a completed turn must not report the timeout convention (rc={rc})"
        assert elapsed < 10, f"waited {elapsed:.1f}s after the result event"

    def test_WITHOUT_the_flag_the_same_child_burns_the_whole_deadline(
        self, tmp_path: Path
    ) -> None:
        """The control. Without it, a fast pass proves the fixture, not the fix."""
        log = tmp_path / "t.log"
        log.write_text("", encoding="utf-8")
        agent = _lingering_agent(tmp_path, log, emit=True, sleep=30)
        rc, elapsed = _run_exec(f"3 {agent}", tmp_path)
        assert rc == 124, f"expected the timeout convention, got {rc}"

    def test_a_done_marker_also_stops_the_wait(self, tmp_path: Path) -> None:
        """The report-file transport's own completion signal, when one is known."""
        marker = tmp_path / "r.report.md.done"
        agent = tmp_path / "a.sh"
        agent.write_text(f"#!/bin/sh\n: > {str(marker)!r}\nsleep 30\n", encoding="utf-8")
        agent.chmod(0o755)
        rc, elapsed = _run_exec(f"--complete-marker {marker} 30 {agent}", tmp_path)
        assert rc == 0
        assert elapsed < 10


class TestTheCeilingAndTheOrdinaryPathsAreUNCHANGED:
    def test_no_signal_still_times_out_at_the_deadline(self, tmp_path: Path) -> None:
        """`--timeout` remains the ceiling for the no-signal case."""
        log = tmp_path / "t.log"
        log.write_text("", encoding="utf-8")
        agent = _lingering_agent(tmp_path, log, emit=False, sleep=30)
        rc, elapsed = _run_exec(f"--complete-log {log} 3 {agent}", tmp_path)
        assert rc == 124

    def test_a_child_that_exits_normally_keeps_its_own_rc(self, tmp_path: Path) -> None:
        log = tmp_path / "t.log"
        log.write_text("", encoding="utf-8")
        agent = tmp_path / "a.sh"
        agent.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
        agent.chmod(0o755)
        rc, _ = _run_exec(f"--complete-log {log} 30 {agent}", tmp_path)
        assert rc == 7, "the child's own exit code must survive"

    def test_a_missing_log_is_not_a_completion_signal(self, tmp_path: Path) -> None:
        """An absent file must not read as "the event is there" — fail closed."""
        agent = _lingering_agent(tmp_path, tmp_path / "nope.log", emit=False, sleep=30)
        rc, elapsed = _run_exec(
            f"--complete-log {tmp_path}/nope.log 3 {agent}", tmp_path)
        assert rc == 124

    def test_an_unrelated_event_is_not_a_completion_signal(self, tmp_path: Path) -> None:
        """`step_update` is mid-turn. Matching any event would end every wait at once."""
        log = tmp_path / "t.log"
        log.write_text('{"event":"step_update","n":1}\n', encoding="utf-8")
        agent = _lingering_agent(tmp_path, log, emit=False, sleep=30)
        rc, elapsed = _run_exec(f"--complete-log {log} 3 {agent}", tmp_path)
        assert rc == 124, "a mid-turn event ended the wait"

    def test_a_PREVIOUS_passs_result_event_does_not_end_this_wait(
        self, tmp_path: Path
    ) -> None:
        """The log is APPENDED to across passes, so the check must be run-scoped.

        Caught by the existing suite, not by these tests: an unscoped grep saw the
        previous pass's `result` and killed the new child on its first poll —
        `test_verb_passes_one` fell to `dispatch_count == 0`. A dispatcher that
        never dispatches is strictly worse than the linger this replaces.
        """
        log = tmp_path / "t.log"
        log.write_text(RESULT_LINE + "\n", encoding="utf-8")  # the previous pass
        agent = _lingering_agent(tmp_path, log, emit=False, sleep=30)
        rc, _ = _run_exec(
            f"--complete-log {log} --complete-after 1 3 {agent}", tmp_path)
        assert rc == 124, "a previous pass's result event ended this run's wait"
