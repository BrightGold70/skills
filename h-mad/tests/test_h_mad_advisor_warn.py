"""The advisor warning is the mechanical half of the context-budget rule.

It replaces `h-mad-advisor-gate.sh`, which was a PreToolUse hook with matcher
`advisor` and which — proven twice with the marker at line 1 — never fired once
(J44). The reason is structural, not a typo in the matcher: `advisor` is a
`server_tool_use` executed server-side and never enters local tool dispatch, so
no tool-scoped hook event can attach to it. `TestTheDeadGateIsGone`
below is the guard against re-deriving that fix from the old prose.

So this is an ADVISORY, not a gate. It rides PostToolUse — the event whose firing
rate tracks the risk, since tool results are what grow a transcript — and injects
the budget verdict as `additionalContext`, reaching the model during the
orientation window in which it decides whether to call the advisor.

Every test here is about a way the advisory is WORSE than no advisory:

  * speaking when it cannot measure. A warning emitted on a cannot-judge trains
    the reader to ignore it, and then the real one lands on deaf ears.
  * speaking on every tool call. This hook exists to prevent context bloat; a
    warning that reprints 30x a minute IS context bloat.
  * staying silent because its own throttle broke. Every failure path must fall
    through to emitting — one extra warning costs two lines, a missed one costs
    the run.
  * matching `HALT` as well as `DENY`. `--mode run`'s ceiling is worded HALT on
    purpose (J45); collapsing the two makes a dying run look like an over-budget
    advisor call.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "h-mad" / "hooks" / "h-mad-advisor-warn.sh"
GATE = REPO_ROOT / "h-mad" / "hooks" / "h-mad-advisor-gate.sh"
BUDGET = REPO_ROOT / "h-mad" / "scripts" / "h_mad_context_budget.py"


def _turn(read):
    return json.dumps({
        "isSidechain": False,
        "message": {"usage": {"input_tokens": 0,
                              "cache_creation_input_tokens": 0,
                              "cache_read_input_tokens": read}},
    })


def _transcript(tmp_path, read, name="session.jsonl"):
    p = tmp_path / name
    p.write_text(_turn(read) + "\n")
    return p


def _run(payload, tmp_path, **env):
    """Hermetic: no ambient session may leak in and decide the verdict."""
    e = dict(os.environ)
    for leak in ("CLAUDE_TRANSCRIPT_PATH", "CLAUDE_CODE_SESSION_ID",
                 "HMAD_CONTEXT_WINDOW", "HMAD_CONTEXT_CEILING",
                 "HMAD_ADVISOR_WARN_INTERVAL"):
        e.pop(leak, None)
    e["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir(exist_ok=True)
    # Per-test stamp dir, or one test's throttle silences the next.
    stamps = tmp_path / "stamps"
    stamps.mkdir(exist_ok=True)
    e["TMPDIR"] = str(stamps)
    e["HMAD_CONTEXT_BUDGET_SCRIPT"] = str(BUDGET)
    e.update({k: str(v) for k, v in env.items()})
    return subprocess.run(["bash", str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, env=e)


def _context(result):
    """The injected text, or None when the hook said nothing."""
    if not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout
    return payload["hookSpecificOutput"]["additionalContext"]


def _code(path: Path) -> str:
    """The hook's executable lines, comments stripped.

    The header deliberately NAMES what it removed — `{"matcher": "advisor"}` and
    `HMAD_ADVISOR_OVERRIDE` — because the reason they are gone is the whole
    finding. Asserting against the raw file would forbid the explanation and push
    the next reader to re-derive J44 from scratch.
    """
    return "\n".join(ln for ln in path.read_text(encoding="utf-8").splitlines()
                      if not ln.lstrip().startswith("#"))


def _payload(tmp_path, read, *, session="s1", name="session.jsonl"):
    return {"tool_name": "Bash", "session_id": session,
            "transcript_path": str(_transcript(tmp_path, read, name))}


class TestItWarnsAboveTheCeiling:
    def test_emits_injected_context_above_the_ceiling(self, tmp_path):
        r = _run(_payload(tmp_path, 525_742), tmp_path)

        assert r.returncode == 0, r.stderr
        ctx = _context(r)
        assert ctx is not None and "Context budget" in ctx

    def test_the_output_is_the_documented_hook_json_shape(self, tmp_path):
        """Plain stdout also injects on 2.1.241, but the documented contract is
        `hookSpecificOutput` + `hookEventName`; drifting off it is how a hook
        starts being treated as plain text with no warning."""
        r = _run(_payload(tmp_path, 525_742), tmp_path)

        payload = json.loads(r.stdout)
        assert payload["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        assert payload["hookSpecificOutput"]["additionalContext"]

    def test_the_warning_names_the_substitutes(self, tmp_path):
        """A budget warning that names no cheaper route is a warning the reader
        can only obey by doing nothing."""
        ctx = _context(_run(_payload(tmp_path, 525_742), tmp_path))

        assert ctx is not None
        assert "exec agy" in ctx
        assert "fork" in ctx

    def test_the_warning_names_the_assumed_window(self, tmp_path):
        """The window is a guess from an env default. If the model's window is
        smaller the percentage is wrong, and the reader must see why."""
        ctx = _context(_run(_payload(tmp_path, 525_742), tmp_path))

        assert ctx is not None
        assert "1000000" in ctx
        assert "HMAD_CONTEXT_WINDOW" in ctx

    def test_it_is_advisory_only_and_never_blocks(self, tmp_path):
        """PostToolUse cannot deny a call that already happened, and this hook
        must not pretend otherwise: a non-zero exit or a `decision: block` would
        turn a budget note into a broken tool."""
        r = _run(_payload(tmp_path, 525_742), tmp_path)

        assert r.returncode == 0
        assert "block" not in r.stdout.lower()
        assert "continue" not in r.stdout


class TestItStaysSilentWhenItCannotMeasure:
    def test_silent_below_the_ceiling(self, tmp_path):
        r = _run(_payload(tmp_path, 100_000), tmp_path)

        assert r.returncode == 0
        assert _context(r) is None

    def test_a_cannot_judge_is_silent(self, tmp_path):
        """The budget script exits 2 on UNKNOWN. Reading the rc rather than the
        token would make a fresh session — the one the ladder tells you to call
        the advisor from — warn on every single tool call."""
        r = _run({"tool_name": "Bash", "session_id": "s1",
                  "transcript_path": str(tmp_path / "nope.jsonl")}, tmp_path)

        assert r.returncode == 0
        assert _context(r) is None

    def test_a_transcript_with_no_usage_yet_is_silent(self, tmp_path):
        p = tmp_path / "fresh.jsonl"
        p.write_text(json.dumps({"type": "user", "message": {}}) + "\n")

        r = _run({"tool_name": "Bash", "session_id": "s1",
                  "transcript_path": str(p)}, tmp_path)

        assert r.returncode == 0
        assert _context(r) is None

    def test_malformed_payload_is_silent(self, tmp_path):
        e = dict(os.environ)
        e["HOME"] = str(tmp_path)
        e["TMPDIR"] = str(tmp_path)
        e["HMAD_CONTEXT_BUDGET_SCRIPT"] = str(BUDGET)

        r = subprocess.run(["bash", str(HOOK)], input="{not json",
                           capture_output=True, text=True, env=e)

        assert r.returncode == 0
        assert not r.stdout.strip()

    def test_missing_budget_script_is_silent(self, tmp_path):
        r = _run(_payload(tmp_path, 525_742), tmp_path,
                 HMAD_CONTEXT_BUDGET_SCRIPT=str(tmp_path / "gone.py"))

        assert r.returncode == 0
        assert _context(r) is None

    def test_a_run_mode_halt_is_not_an_advisor_deny(self, tmp_path):
        """J45: `--mode run` says HALT at 80% and `--mode advisor` says DENY at
        45%, worded apart so one cannot be read as the other. A checker emitting
        only HALT must leave this hook silent."""
        fake = tmp_path / "halt.py"
        fake.write_text(
            "print('CTXBUDGET: HALT used=900000 window=1000000 pct=90.0 "
            "projected=1800000 ceiling=80 mode=run')\n"
        )

        r = _run(_payload(tmp_path, 525_742), tmp_path,
                 HMAD_CONTEXT_BUDGET_SCRIPT=str(fake))

        assert r.returncode == 0
        assert _context(r) is None


class TestItIsTunable:
    def test_the_ceiling_is_configurable(self, tmp_path):
        """A hardcoded 45 is wrong for anyone running a different budget, and the
        wrongness is silent: the warning simply never arrives."""
        below_default = _payload(tmp_path, 300_000)   # 30% — silent at ceiling 45

        assert _context(_run(below_default, tmp_path)) is None
        assert _context(_run(below_default, tmp_path,
                             HMAD_CONTEXT_CEILING=20)) is not None

    def test_the_window_is_configurable(self, tmp_path):
        """The 1M default is a guess. On a smaller-window model an unconfigurable
        window is wrong in the PERMISSIVE direction — it under-reports usage."""
        payload = _payload(tmp_path, 300_000)

        assert _context(_run(payload, tmp_path)) is None
        ctx = _run(payload, tmp_path, HMAD_CONTEXT_WINDOW=500_000)
        assert _context(ctx) is not None
        assert "500000" in _context(ctx), "the warning must name the window it used"


class TestItBoundsItsOwnRepetition:
    def test_a_second_call_within_the_interval_is_silent(self, tmp_path):
        first = _run(_payload(tmp_path, 525_742), tmp_path)
        second = _run(_payload(tmp_path, 525_742), tmp_path)

        assert _context(first) is not None
        assert _context(second) is None, "the warning reprinted inside its interval"

    def test_a_zero_interval_always_speaks(self, tmp_path):
        """The throttle must be tunable to off, or a long over-budget stretch
        gets exactly one warning and then silence that reads as recovery."""
        first = _run(_payload(tmp_path, 525_742), tmp_path,
                     HMAD_ADVISOR_WARN_INTERVAL=0)
        second = _run(_payload(tmp_path, 525_742), tmp_path,
                      HMAD_ADVISOR_WARN_INTERVAL=0)

        assert _context(first) is not None
        assert _context(second) is not None

    def test_two_sessions_do_not_silence_each_other(self, tmp_path):
        a = _run(_payload(tmp_path, 525_742, session="alpha", name="a.jsonl"), tmp_path)
        b = _run(_payload(tmp_path, 525_742, session="beta", name="b.jsonl"), tmp_path)

        assert _context(a) is not None
        assert _context(b) is not None, "one session's stamp silenced another's"

    def test_a_corrupt_stamp_falls_through_to_warning(self, tmp_path):
        """Fail toward SPEAKING. A throttle that cannot read its own stamp must
        not conclude 'already warned' — one extra warning costs two lines."""
        _run(_payload(tmp_path, 525_742), tmp_path)
        stamp = next((tmp_path / "stamps").glob("h-mad-advisor-warn.*.stamp"))
        stamp.write_text("not-a-timestamp\n")

        again = _run(_payload(tmp_path, 525_742), tmp_path)

        assert _context(again) is not None

    @pytest.mark.parametrize("session", ["../escape", "a/b", "../../pwn"])
    def test_a_hostile_session_id_builds_no_stamp_path(self, tmp_path, session):
        """The stamp path is built from a payload field. A session_id carrying a
        separator must not become a write outside the stamp dir; refusing the stamp
        (and so warning every time) is the safe direction.

        The parent directory the UNGUARDED path would need is created first, and it
        is computed the same way the hook computes it. Without that step the write
        fails because the parent does not exist, the test passes, and it has proved
        nothing about the guard — which is exactly what it did on the first attempt
        (the mutation harness caught it: `hostile-session-id-builds-a-path` survived
        against the earlier version of this test)."""
        stamps = tmp_path / "stamps"
        stamps.mkdir(exist_ok=True)
        escaped = Path(f"{stamps}/h-mad-advisor-warn.{session}.stamp")
        escaped.parent.mkdir(parents=True, exist_ok=True)
        before = {q.resolve() for q in stamps.rglob("*") if q.is_file()}

        r = _run(_payload(tmp_path, 525_742, session=session), tmp_path)

        assert r.returncode == 0
        assert _context(r) is not None, "refusing a stamp must not mean staying silent"
        assert not escaped.exists(), f"wrote through a hostile session_id to {escaped}"
        after = {q.resolve() for q in stamps.rglob("*") if q.is_file()}
        assert after == before, f"unexpected file(s): {sorted(after - before)}"

    def test_an_absent_session_id_still_throttles(self, tmp_path):
        """A missing `session_id` is not hostile — the payload parser substitutes
        the `-` sentinel, which carries no separator, so it is a usable stamp key.
        Refusing it would make the advisory reprint on every tool call in any
        session the harness does not name."""
        payload = {"tool_name": "Bash",
                   "transcript_path": str(_transcript(tmp_path, 525_742))}

        assert _context(_run(payload, tmp_path)) is not None
        assert _context(_run(payload, tmp_path)) is None, "no throttle without a session_id"


class TestTheDeadGateIsGone:
    def test_the_pretooluse_gate_script_is_removed(self):
        """It could never fire. Leaving it on disk leaves something for an
        install to re-wire, and its own header still documents the PreToolUse
        registration as the way to install it."""
        assert not GATE.exists()

    def test_the_install_snippet_registers_postooluse_not_pretooluse(self):
        """The one line an operator copies must not recreate J44."""
        text = HOOK.read_text(encoding="utf-8")
        snippet = text.split("Install as a", 1)[1].split("#\n", 1)[0]

        assert "PostToolUse" in snippet
        assert '"matcher": "*"' in snippet
        assert "PreToolUse" not in snippet

    def test_the_root_cause_travels_with_the_fix(self):
        """Without it, the next reader sees an advisory where a gate would do and
        'improves' it back into a PreToolUse matcher that cannot fire."""
        text = HOOK.read_text(encoding="utf-8")

        assert "server_tool_use" in text
        assert "J44" in text

    def test_the_advisory_has_no_override_env_var(self):
        """The gate needed `HMAD_ADVISOR_OVERRIDE` because it could refuse. An
        advisory that ships an escape hatch is telling the reader it blocks."""
        assert "HMAD_ADVISOR_OVERRIDE" not in _code(HOOK)
