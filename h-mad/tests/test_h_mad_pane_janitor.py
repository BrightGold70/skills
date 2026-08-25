"""Tests for `h_mad_pane_janitor.py`.

This tool closes things, so most of these assert that it did NOT close
something. The one that matters most is `test_the_callers_own_pane_is_never_a
_candidate`: the failure the row records is closing the operator's own agent
session, and the panes are indistinguishable by title, so nothing but the
self-handle lookup stands between the janitor and that.

The stub models the real CLI's shape as measured on a live install, including
the two defaulting behaviours that are footguns: `terminal show` with no
`--terminal` returns the CALLER's pane, and `terminal close` accepts no handle
at all — in which case it would close the caller's pane too. The stub records
every argv, so a close emitted without an explicit handle is visible rather
than merely unlikely.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "h_mad_pane_janitor.py"

WT = "/repo/work"
OTHER_WT = "/repo/sibling"
SELF = "term_self"

STUB = r'''#!/usr/bin/env python3
import json, os, sys
state = json.load(open(os.environ["STUB_STATE"]))
with open(os.environ["STUB_CAPTURE"], "a") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\n")
args = [a for a in sys.argv[1:] if a != "--json"]

def emit(result):
    print(json.dumps({"ok": True, "result": result}))
    raise SystemExit(0)

def fail(code):
    print(json.dumps({"ok": False, "error": {"code": code}}))
    raise SystemExit(0)

# Scoped per command on purpose. A global knob trips on the FIRST orca call --
# `terminal show` inside self_handle -- so a test claiming to exercise a
# `worker-list` payload failure never reaches worker-list at all.
if state.get("deny") == " ".join(args[:2]):
    fail("run_required")
if args[:2] == ["terminal", "list"]:
    emit({"terminals": state["terminals"]})
if args[:2] == ["terminal", "show"]:
    if state.get("no_self"):
        emit({"terminal": {}})
    # No --terminal means "the caller's own pane" -- the real defaulting.
    handle = args[3] if len(args) > 3 and args[2] == "--terminal" else state["self"]
    for t in state["terminals"]:
        if t["handle"] == handle:
            emit({"terminal": t})
    emit({"terminal": {"handle": handle}})
if args[:2] == ["terminal", "close"]:
    emit({"closed": True})
if args[:2] == ["orchestration", "worker-list"]:
    emit({"workers": state.get("workers", [])})
if args[:2] == ["orchestration", "task-update"]:
    if state.get("settle_fails"):
        fail("dispatch_not_found")
    emit({"updated": True})
fail("unknown_command")
'''


def pane(handle: str, worktree: str = WT, title: str = "worker") -> dict:
    return {"handle": handle, "worktreePath": worktree, "title": title}


@pytest.fixture()
def env(tmp_path: Path):
    stub = tmp_path / "orca-stub"
    stub.write_text(STUB, encoding="utf-8")
    stub.chmod(0o755)
    state_file = tmp_path / "state.json"
    capture = tmp_path / "capture.txt"
    capture.write_text("", encoding="utf-8")

    class Env:
        def __init__(self) -> None:
            self.stub, self.state_file, self.capture = stub, state_file, capture

        def set(self, _self: str = SELF, **state) -> None:
            state["self"] = _self
            state_file.write_text(json.dumps(state), encoding="utf-8")

        def run(self, *args: str) -> subprocess.CompletedProcess[str]:
            import os
            environ = dict(os.environ,
                           STUB_STATE=str(state_file), STUB_CAPTURE=str(capture))
            return subprocess.run(
                [sys.executable, str(SCRIPT), *args, "--orca", str(stub)],
                capture_output=True, text=True, env=environ)

        def calls(self) -> list[str]:
            return [ln for ln in capture.read_text().splitlines() if ln.strip()]

    return Env()


def baseline_file(tmp_path: Path, handles: list[str], worktree: str = WT) -> Path:
    target = tmp_path / "baseline.json"
    target.write_text(json.dumps(
        {"worktree": worktree, "self": SELF, "handles": handles}), encoding="utf-8")
    return target


class TestSnapshot:
    def test_it_records_only_the_named_worktree(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF), pane("term_a"), pane("term_x", OTHER_WT)])
        out = tmp_path / "snap.json"
        proc = env.run("snapshot", "--worktree", WT, "--out", str(out))

        assert proc.returncode == 0, proc.stdout + proc.stderr
        snapshot = json.loads(out.read_text())
        assert snapshot["handles"] == sorted([SELF, "term_a"])
        assert snapshot["self"] == SELF

    def test_snapshot_closes_nothing(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF), pane("term_a")])
        env.run("snapshot", "--worktree", WT, "--out", str(tmp_path / "s.json"))
        assert not any("close" in c for c in env.calls())


class TestCandidateSelection:
    def test_a_pane_absent_from_the_baseline_is_a_candidate(
        self, env, tmp_path: Path
    ) -> None:
        env.set(terminals=[pane(SELF), pane("term_old"), pane("term_new")])
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF, "term_old"])))

        assert "JANITOR: PLANNED candidates=1" in proc.stdout
        assert "term_new" in proc.stdout

    def test_the_callers_own_pane_is_never_a_candidate(
        self, env, tmp_path: Path
    ) -> None:
        """The recorded failure: closing the operator's own agent session.

        The baseline here carries NEITHER the caller's handle NOR a `self`
        key — a hand-written or pre-self baseline — so the LIVE lookup is the
        only thing left. An earlier version of this test used `baseline_file`,
        which always writes `self`, and a mutation deleting the live exclusion
        survived it: the baseline was quietly doing the work the test claimed
        to be checking.
        """
        env.set(terminals=[pane(SELF, title="worker"), pane("term_new")])
        stale = tmp_path / "stale.json"
        stale.write_text(json.dumps({"worktree": WT, "handles": []}), encoding="utf-8")
        proc = env.run("plan", "--baseline", str(stale))

        assert SELF not in proc.stdout
        assert "candidates=1" in proc.stdout

    def test_the_caller_is_excluded_even_when_it_moved_panes(
        self, env, tmp_path: Path
    ) -> None:
        """The janitor may run from a different pane than took the snapshot."""
        env.set("term_moved", terminals=[pane("term_moved"), pane("term_new")])
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF])))

        assert "term_moved" not in proc.stdout
        assert "term_new" in proc.stdout

    def test_panes_in_another_worktree_are_never_candidates(
        self, env, tmp_path: Path
    ) -> None:
        """A concurrent agent session in a sibling worktree was live for real."""
        env.set(terminals=[pane(SELF), pane("term_sibling", OTHER_WT, "HemaSuite")])
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF])))

        assert "JANITOR: NOTHING" in proc.stdout
        assert "term_sibling" not in proc.stdout

    def test_nothing_to_do_is_its_own_verdict(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF), pane("term_old")])
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF, "term_old"])))
        assert "JANITOR: NOTHING candidates=0" in proc.stdout
        assert proc.returncode == 0


class TestDryRunIsTheDefault:
    def test_plan_closes_nothing(self, env, tmp_path: Path) -> None:
        # The pane needs a worker row, or positive identification keeps it out
        # of the target set and the dry-run branch is never reached -- the test
        # would then pass for the wrong reason. Caught by a mutation that had
        # been killed before the identification change and survived after it.
        env.set(terminals=[pane(SELF), pane("term_new")], workers=[{"agentTerminalHandle": "term_new", "taskId": "t", "dispatchStatus": "completed"}])
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF])))

        assert "JANITOR: PLANNED" in proc.stdout
        assert not any("terminal close" in c for c in env.calls())
        assert "dry run" in proc.stdout

    def test_clean_without_apply_closes_nothing(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF), pane("term_new")], workers=[{"agentTerminalHandle": "term_new", "taskId": "t", "dispatchStatus": "completed"}])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])))

        assert "JANITOR: PLANNED" in proc.stdout
        assert not any("terminal close" in c for c in env.calls())

    def test_a_dry_run_never_reports_work_as_done(self, env, tmp_path: Path) -> None:
        """`PLANNED ... closed=1` reads as a pane that was closed.

        Same failure shape as a cannot-judge carrying a count: the verdict word
        says one thing and the fields say another, and the fields are what an
        operator skims. A dry run reports `would_close`/`would_settle`.
        """
        env.set(
            terminals=[pane(SELF), pane("term_new")],
            workers=[{"agentTerminalHandle": "term_new", "taskId": "task_1",
                      "dispatchStatus": "running"}],
        )
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF])))

        assert "would_close=1" in proc.stdout
        assert "would_settle=1" in proc.stdout
        assert "closed=1" not in proc.stdout
        assert "settled=1" not in proc.stdout
        assert "would close:" in proc.stdout

    def test_clean_with_apply_closes(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF), pane("term_new")],
                workers=[{"agentTerminalHandle": "term_new", "taskId": "t",
                          "dispatchStatus": "completed"}])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "JANITOR: CLEANED candidates=1" in proc.stdout
        assert "closed=1" in proc.stdout
        assert any("terminal close --terminal term_new" in c for c in env.calls())


class TestTheCloseIsAlwaysExplicit:
    def test_no_close_is_ever_emitted_without_a_handle(
        self, env, tmp_path: Path
    ) -> None:
        """`orca terminal close` with no `--terminal` closes the CALLER's pane.

        Verified on a live install: `--terminal` is optional. So a bare close
        is not a cosmetic slip, it is the destructive bug this tool exists to
        avoid, and it must be impossible rather than merely unlikely.
        """
        env.set(terminals=[pane(SELF), pane("term_a"), pane("term_b")],
                workers=[{"agentTerminalHandle": h, "taskId": "t",
                          "dispatchStatus": "completed"} for h in ("term_a", "term_b")])
        env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        closes = [c for c in env.calls() if c.startswith("terminal close")]
        assert closes, "expected at least one close"
        for call in closes:
            assert "--terminal" in call, f"bare close would kill the caller: {call!r}"


class TestDispatchSettling:
    def test_an_unsettled_dispatch_is_settled_before_its_pane_closes(
        self, env, tmp_path: Path
    ) -> None:
        env.set(
            terminals=[pane(SELF), pane("term_new")],
            workers=[{"agentTerminalHandle": "term_new", "taskId": "task_1",
                      "dispatchStatus": "running"}],
        )
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "settled=1" in proc.stdout
        calls = env.calls()
        settle = next(i for i, c in enumerate(calls) if "task-update" in c)
        close = next(i for i, c in enumerate(calls) if c.startswith("terminal close"))
        assert settle < close, "closing before settling wedges the terminal permanently"

    def test_an_already_settled_dispatch_is_not_re_settled(
        self, env, tmp_path: Path
    ) -> None:
        env.set(
            terminals=[pane(SELF), pane("term_new")],
            workers=[{"agentTerminalHandle": "term_new", "taskId": "task_1",
                      "dispatchStatus": "completed"}],
        )
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "settled=0" in proc.stdout
        assert "closed=1" in proc.stdout
        assert not any("task-update" in c for c in env.calls())

    def test_a_failed_settle_leaves_the_pane_open(self, env, tmp_path: Path) -> None:
        """A wedged terminal you can still see beats one you cannot."""
        env.set(
            terminals=[pane(SELF), pane("term_new")],
            workers=[{"agentTerminalHandle": "term_new", "taskId": "task_1",
                      "dispatchStatus": "running"}],
            settle_fails=True,
        )
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "closed=0" in proc.stdout
        assert "skipped=1" in proc.stdout
        assert "settle failed" in proc.stdout
        assert not any(c.startswith("terminal close") for c in env.calls())

    def test_a_pane_with_no_worker_row_needs_no_settle(
        self, env, tmp_path: Path
    ) -> None:
        env.set(terminals=[pane(SELF), pane("term_plain")], workers=[])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])),
                       "--apply", "--include-unidentified")

        assert "settled=0 closed=1" in proc.stdout
        assert not any("task-update" in c for c in env.calls())


class TestRefusals:
    def test_it_refuses_when_it_cannot_identify_itself(
        self, env, tmp_path: Path
    ) -> None:
        env.set(terminals=[pane("term_a")], no_self=True)
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [])))

        assert proc.returncode == 2
        assert "REFUSED reason=cannot_identify_self" in proc.stdout
        assert not any("close" in c for c in env.calls())

    def test_a_missing_baseline_refuses(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF)])
        proc = env.run("plan", "--baseline", str(tmp_path / "absent.json"))

        assert proc.returncode == 2
        assert "reason=baseline_unreadable" in proc.stdout

    def test_a_malformed_baseline_refuses(self, env, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text('{"worktree": "/repo/work"}', encoding="utf-8")
        env.set(terminals=[pane(SELF)])
        proc = env.run("plan", "--baseline", str(bad))

        assert proc.returncode == 2
        assert "reason=baseline_malformed" in proc.stdout

    def test_too_many_candidates_refuses_rather_than_acting(
        self, env, tmp_path: Path
    ) -> None:
        """A baseline taken against the wrong worktree makes every pane a candidate."""
        env.set(terminals=[pane(SELF)] + [pane(f"term_{i}") for i in range(12)])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert proc.returncode == 2
        assert "reason=too_many_candidates" in proc.stdout
        assert not any("close" in c for c in env.calls())

    def test_the_cap_can_be_raised_deliberately(self, env, tmp_path: Path) -> None:
        env.set(terminals=[pane(SELF)] + [pane(f"term_{i}") for i in range(12)])
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF])),
                       "--max", "20")

        assert proc.returncode == 0
        assert "candidates=12" in proc.stdout

    def test_an_orca_that_answers_not_ok_refuses(self, env, tmp_path: Path) -> None:
        """Distinct from a launch failure: the CLI ran and said no.

        `worker-list` answers `run_required` when no Run is bound, which is a
        real response on a real install — treating a not-ok payload as an empty
        result would read "no workers" and close panes without settling them.
        """
        env.set(terminals=[pane(SELF), pane("term_new")], deny="terminal show")
        proc = env.run("plan", "--baseline", str(baseline_file(tmp_path, [SELF])))

        assert proc.returncode == 2
        assert "reason=orca_error" in proc.stdout
        assert not any("close" in c for c in env.calls())

    def test_an_orca_that_cannot_run_refuses(self, tmp_path: Path) -> None:
        base = tmp_path / "b.json"
        base.write_text(json.dumps({"worktree": WT, "handles": []}), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "plan", "--baseline", str(base),
             "--orca", str(tmp_path / "no-such-orca")],
            capture_output=True, text=True)

        assert proc.returncode == 2
        assert "reason=orca_unavailable" in proc.stdout


class TestDocsPin:
    def test_the_token_is_registered_in_skill_md(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text()
        assert "h_mad_pane_janitor.py" in skill
        assert "JANITOR: PLANNED" in skill

    def test_every_refusal_reason_is_documented(self) -> None:
        import re
        script = SCRIPT.read_text()
        skill = (SKILL_DIR / "SKILL.md").read_text()
        reasons = set(re.findall(r'Refusal\(\s*"([a-z_]+)"', script))
        assert reasons, "no refusal reasons found in the script"
        undocumented = sorted(r for r in reasons if r not in skill)
        assert not undocumented, f"undocumented refusal reasons: {undocumented}"


class TestPositiveIdentification:
    """Subtraction alone cannot tell the probe's panes from the operator's.

    Surfaced by an adversarial review of the shipped tool: an operator who opens
    a pane in this worktree AFTER the snapshot — to tail a log while the probe
    runs — produces a delta indistinguishable from a probe pane. Neither guard
    that existed saw it: `--max` only bounds how many get closed, and the
    self-handle protects the one shell the janitor runs in, not the operator's
    other tabs.
    """

    def test_a_pane_with_no_worker_row_is_left_alone_by_default(
        self, env, tmp_path: Path
    ) -> None:
        env.set(terminals=[pane(SELF), pane("term_operator", title="tail -f")], workers=[])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "unidentified=1" in proc.stdout
        assert "closed=0" in proc.stdout
        assert not any("terminal close" in c for c in env.calls())

    def test_an_unidentified_pane_is_always_named_never_silent(
        self, env, tmp_path: Path
    ) -> None:
        """Silence is what made `--max 10` insufficient: it bounded the damage
        at nine panes without ever saying which."""
        env.set(terminals=[pane(SELF), pane("term_operator", title="tail -f")], workers=[])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "UNIDENTIFIED (1)" in proc.stdout
        assert "term_operator" in proc.stdout
        assert "--include-unidentified" in proc.stdout

    def test_the_operators_pane_survives_beside_a_real_probe_pane(
        self, env, tmp_path: Path
    ) -> None:
        """The scenario in full: both appear in the delta, only one is the probe's."""
        env.set(
            terminals=[pane(SELF), pane("term_probe"), pane("term_operator", title="tail -f")],
            workers=[{"agentTerminalHandle": "term_probe", "taskId": "t",
                      "dispatchStatus": "completed"}],
        )
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert "identified=1 unidentified=1" in proc.stdout
        closes = [c for c in env.calls() if c.startswith("terminal close")]
        assert closes == ["terminal close --terminal term_probe --json"], closes

    def test_include_unidentified_closes_them_deliberately(
        self, env, tmp_path: Path
    ) -> None:
        """The live-verified path: a pane made by `terminal create` has no worker
        row, so the escape hatch has to exist — behind an explicit flag."""
        env.set(terminals=[pane(SELF), pane("term_plain")], workers=[])
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])),
                       "--apply", "--include-unidentified")

        assert "closed=1" in proc.stdout
        assert any("terminal close --terminal term_plain" in c for c in env.calls())


class TestTheDenyKnobIsScoped:
    """A global failure knob trips on the first call and proves nothing later."""

    def test_a_worker_list_payload_failure_refuses(self, env, tmp_path: Path) -> None:
        """This is what `test_an_orca_that_answers_not_ok_refuses` CLAIMED to test.

        `worker-list` answers `run_required` when no Run is bound. Treating a
        not-ok payload as an empty result would read "no workers", mark every
        candidate unidentified, and — before this — close them unsettled.
        """
        env.set(terminals=[pane(SELF), pane("term_new")],
                deny="orchestration worker-list")
        proc = env.run("clean", "--baseline", str(baseline_file(tmp_path, [SELF])), "--apply")

        assert proc.returncode == 2
        assert "reason=orca_error" in proc.stdout
        assert "worker-list" in proc.stdout
        assert not any("terminal close" in c for c in env.calls())
