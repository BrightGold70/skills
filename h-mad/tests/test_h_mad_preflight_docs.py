"""Mandated reads: a verdict token nothing is obliged to read is still advisory.

`env` gained `PREFLIGHT: PASS|FAIL` and `h_mad_assemble_audit.py` already emitted
`ASSEMBLE: PASS|HALT`, but a token only changes behaviour if some step must consume
it. That is the whole defect this feature exists to close, one level up: the
`STALE`/`CONFLICT:` lines were correct and printed, and a dispatch still walked
into a rotated handle because no step was required to look.

These tests assert the obligation exists in the protocol documents. They cannot
assert that an orchestrator performs it — that gap is deliberate and recorded as a
carry item; Wave 3's dogfood run is what exercises it.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"
ORCH_MD = REPO_ROOT / "h-mad" / "references" / "orchestration-mode.md"
SUBS_MD = REPO_ROOT / "h-mad" / "references" / "agent-substrate.md"


def _section(text: str, start: str, end: str) -> str:
    """The slice of `text` from heading `start` up to heading `end`."""
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _phase5_preflight() -> str:
    """The Phase-5 substrate-preflight block of SKILL.md."""
    return _section(SKILL_MD.read_text(encoding="utf-8"),
                    "## Phase 5 (Implementation) sub-steps",
                    "## Phase 5 parallel fanout")


def _audit_assembly() -> str:
    return _section(SKILL_MD.read_text(encoding="utf-8"),
                    "## Audit prompt assembly",
                    "## Putting `hmad-dispatch` on PATH")


class TestPhase5MandatesReadingPreflight:
    def test_asserts_preflight_pass_before_first_dispatch(self):
        """AC-4.1."""
        s = _phase5_preflight()
        assert "PREFLIGHT: PASS" in s
        assert "before the first" in s.lower()

    def test_requires_reasserting_after_a_repin(self):
        """AC-4.2: handles rotate, so one assertion at the top of a run is not enough."""
        s = _phase5_preflight().lower()
        assert "re-assert" in s or "reassert" in s
        assert "re-pin" in s or "repin" in s

    def test_names_the_halt(self):
        """AC-4.3."""
        assert "preflight_failed" in _phase5_preflight()

    def test_says_read_the_token_not_the_exit_code(self):
        """AC-4.4: env exits 0 on both verdicts, so `$?` cannot carry the verdict."""
        s = _phase5_preflight()
        assert "token" in s.lower()
        assert "$?" in s


class TestAuditAssemblyMandatesReadingAssemble:
    def test_asserts_assemble_pass_before_dispatch(self):
        """AC-5.1."""
        s = _audit_assembly()
        assert "ASSEMBLE: PASS" in s
        assert "assert" in s.lower()

    def test_states_halt_is_a_verdict_not_a_tool_failure(self):
        """AC-5.2."""
        s = _audit_assembly()
        assert "ASSEMBLE: HALT" in s
        low = s.lower()
        assert "verdict" in low
        assert "exit" in low and "0" in s


class TestAutomationPrecheckGatesOnTheToken:
    def test_bare_env_precheck_is_gone(self):
        """AC-7.1: `--precheck "hmad-dispatch env"` gates on the EXIT CODE, which is
        0 even for a stale pin — the automation-shaped instance of this whole bug."""
        assert '--precheck "hmad-dispatch env"' not in ORCH_MD.read_text(encoding="utf-8")

    def test_precheck_tests_for_the_verdict(self):
        """AC-7.1."""
        t = ORCH_MD.read_text(encoding="utf-8")
        assert "PREFLIGHT: PASS" in t
        assert "--precheck" in t


class TestSubstrateReferenceDocumentsTheToken:
    def test_env_row_mentions_preflight(self):
        """AC-7.2."""
        t = SUBS_MD.read_text(encoding="utf-8")
        row = next(ln for ln in t.splitlines()
                   if ln.startswith("| `hmad-dispatch env`"))
        assert "PREFLIGHT" in row
