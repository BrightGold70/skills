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
CODEX_MD = REPO_ROOT / "h-mad" / "references" / "codex-implementer-prompt.md"


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

    def test_precheck_also_requires_agents_to_be_resolved(self):
        """6a-prime finding 2: PREFLIGHT: PASS means "nothing is broken", not
        "ready to dispatch" — UNRESOLVED is deliberately not a failure. An
        automation gating on the verdict alone would preflight green with no
        agents pinned, then fail downstream."""
        t = ORCH_MD.read_text(encoding="utf-8")
        assert "UNRESOLVED" in t
        assert "ready to dispatch" in t


class TestSubstrateReferenceDocumentsTheToken:
    def test_env_row_mentions_preflight(self):
        """AC-7.2."""
        t = SUBS_MD.read_text(encoding="utf-8")
        row = next(ln for ln in t.splitlines()
                   if ln.startswith("| `hmad-dispatch env`"))
        assert "PREFLIGHT" in row


def test_skill_states_send_refuses_without_receipt() -> None:
    """AC-9.1: dispatch enforcement is provided by the wrapper, not a read mandate."""
    s = _phase5_preflight().lower()
    assert "send" in s
    assert "refuse" in s or "refuses" in s
    for token in ("preflight_not_run", "preflight_expired",
                  "preflight_handles_rotated", "preflight_agent_conflict"):
        assert token in s


def test_skill_documents_each_refusal_reason_and_recovery() -> None:
    """AC-9.2: every shipped refusal token has an actionable recovery."""
    s = _phase5_preflight().lower()
    recoveries = {
        "preflight_not_run": ("hmad-dispatch env", "run"),
        "preflight_expired": ("hmad-dispatch env", "run"),
        "preflight_handles_rotated": ("re-pin", "hmad-dispatch env"),
        "preflight_agent_conflict": ("pin", "hmad-dispatch env"),
    }
    for token, steps in recoveries.items():
        assert token in s
        assert all(step in s for step in steps)


def test_agent_substrate_documents_receipt_and_env_vars() -> None:
    """AC-9.3: the substrate reference describes receipt control knobs."""
    t = SUBS_MD.read_text(encoding="utf-8")
    low = t.lower()
    assert "receipt" in low
    assert "verdict=pass" in low
    assert "fingerprint" in low
    assert "ttl" in low
    for var in ("HMAD_PREFLIGHT_RECEIPT_FILE", "HMAD_PREFLIGHT_TTL_SEC",
                "HMAD_SKIP_PREFLIGHT"):
        assert var in t


def test_skill_frontmatter_still_valid() -> None:
    """AC-9.4: preserve a parseable manifest with non-empty required fields."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    end = text.find("\n---\n", 4)
    assert end != -1
    frontmatter = text[4:end]
    fields = dict(line.split(":", 1) for line in frontmatter.splitlines()
                  if ":" in line)
    assert fields.get("name", "").strip()
    assert fields.get("description", "").strip()


def test_skill_documents_worktree_rm_guards() -> None:
    """AC-9.1, AC-9.3: the guard and both reason tokens are documented."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "worktree_has_uncommitted_work" in text
    assert "worktree_has_unmerged_commits" in text
    # The verb-behaviour table must say worktree-rm can refuse, not merely that
    # it removes — a reader who only sees the happy path will not pass --force
    # when they mean to discard, and will read a refusal as a bug.
    assert "refuses" in text.lower()
    assert "--force" in text


def test_orchestration_mode_documents_task_id_on_both_paths() -> None:
    """AC-9.2: the two dispatch paths are no longer one sequence."""
    text = ORCH_MD.read_text(encoding="utf-8")
    assert "worktree_task" in text, "the task-id marker must be documented"
    # J14: the old prose ran worktree-create --prompt-file and task-create into a
    # single semicolon-joined instruction. Assert the task-id is described as
    # available from the --prompt-file path, which is what made await/gate-create
    # unusable there.
    assert "--prompt-file" in text
    assert "gate-create" in text


def test_codex_prompt_requires_a_named_concern() -> None:
    """AC-8.1, AC-8.2: the obligation and its consequence are both stated."""
    text = CODEX_MD.read_text(encoding="utf-8")
    assert "DONE_WITH_CONCERNS" in text
    lowered = text.lower()
    assert "at least one concern" in lowered
    assert "report `done`" in lowered or "report done" in lowered
    # The consequence must be visible to the agent, not only to the orchestrator:
    # an obligation with no stated penalty reads as advice.
    assert "reject" in lowered


def test_fanout_teardown_documents_the_base_override() -> None:
    """The guard is correct but obstructive without `--base <feature-branch>`.

    A module worktree branches from the FEATURE branch, while the default
    comparison base resolves to origin/HEAD -> main. Every commit on the feature
    is therefore "not in main", so teardown refuses for as long as the feature is
    unmerged. Measured live during this feature: a freshly created module
    worktree reported 7 commits ahead of main and 1 ahead of its real base.

    A guard that always refuses trains the operator to reach for --force, which
    is exactly the reflex J15 exists to prevent — so the override has to be
    documented in both places an orchestrator would look.
    """
    for doc in (SKILL_MD, ORCH_MD):
        text = doc.read_text(encoding="utf-8")
        # Anchor on the LITERAL instruction form. Asserting only that "--base"
        # and "feature branch" appear somewhere passes vacuously: both files
        # already carry `--base <ref>` in a verb table and "feature branch" in
        # unrelated prose, so that version of this test stayed green with the
        # guidance deleted. Verified by mutation.
        assert "--base <feature-branch>" in text, (
            f"{doc.name} must tell the caller to pass the FEATURE branch to "
            "worktree-rm on fanout teardown, not merely that --base exists"
        )
        # And the instruction must sit with the verb it governs.
        assert "worktree-rm" in text
