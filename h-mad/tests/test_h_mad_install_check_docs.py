"""A check nothing is obliged to run is advisory, and the install is the one
precondition that decides which copy of everything else runs.

`h_mad_install_check.py` can be correct and still change nothing: the defect it
closes (a stale *copy* at `~/.claude/skills/h-mad`, and an absent
`~/.claude/hooks/h-mad-tdd-gate.sh`) went unnoticed for 2.5 months precisely
because no step was required to look. Same shape as the `PREFLIGHT:` obligation
in `test_h_mad_preflight_docs.py`, one level further down: this one decides
*which* `h_mad_*.py` the later gates are even executing.

These tests assert the obligation exists in the protocol document. They cannot
assert an orchestrator performs it.

They also pin the coexisting-plugin entries in §"Known interactions", because
both of those hooks DENY rather than warn, and rediscovering that mid-Phase-7
costs a commit cycle.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_install_check.py"


def _section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _skill() -> str:
    return SKILL_MD.read_text()


def _bootstrap() -> str:
    return _section(_skill(), "## First-run auto-bootstrap", "## Decision routing")


def _interactions() -> str:
    return _section(
        _skill(), "## Known interactions (coexisting plugins)", "## State schema"
    )


# ── the obligation to run it ─────────────────────────────────────────────────

def test_bootstrap_mandates_the_install_check():
    assert "h_mad_install_check.py" in _bootstrap()


def test_bootstrap_names_the_token_to_read():
    assert "INSTALL:" in _bootstrap()


def test_bootstrap_forbids_branching_on_the_exit_code():
    """Both verdicts exit 0, so `$?` cannot discriminate them."""
    body = _bootstrap()
    assert "never `$?`" in body


def test_bootstrap_names_a_halt_reason_for_a_failed_install():
    assert "bootstrap:install_broken" in _bootstrap()


def test_bootstrap_refuses_to_proceed_on_fail():
    """Continuing past a broken install means later gates measure an unknown tree."""
    body = _bootstrap()
    assert "INSTALL: FAIL" in body
    assert "do not proceed" in body.lower()


def test_bootstrap_records_unreadable_as_a_cannot_judge():
    assert "INSTALL: UNREADABLE" in _bootstrap()


def test_bootstrap_records_the_self_staleness_limit():
    """A stale copy runs the stale checker, so PASS from an unknown vintage is weak.

    Asserted as a LITERAL sentence. The first version of this test matched the
    phrase "stale copy", which also occurs in the missing-checker rule below it —
    so it passed with the whole limitation deleted. Caught by mutation
    (`invariants.base.md` §"Test discrimination": a check that cannot fail is
    decoration), not by review or by a green run.
    """
    body = " ".join(_bootstrap().split())
    assert "It is a copy detecting its own staleness" in body
    assert "can only report divergences the old copy is new enough to know about" in body, (
        "the rule must state WHY a PASS from an unknown vintage is weak evidence"
    )


def test_bootstrap_gives_unreadable_its_own_halt_reason():
    """A bad invocation must not be recorded as a bad install."""
    body = " ".join(_bootstrap().split())
    assert "bootstrap:install_unreadable" in body
    assert "distinct from" in body


def test_every_detail_line_has_a_named_remedy():
    """A rule without an adjacent runnable remedy is 'hazard named, command
    withheld' — an agent handed a rule it cannot obey improvises."""
    body = _bootstrap()
    for token in (
        "SKILL_NOT_INSTALLED",
        "SKILL_NOT_SYMLINK",
        "SKILL_DANGLING",
        "SKILL_NOT_A_CHECKOUT",
        "HOOK_NOT_INSTALLED",
        "HOOK_DANGLING",
        "SPLIT_INSTALL",
        "SIBLING_NOT_SYMLINK",
        "SIBLING_DANGLING",
        "SIBLING_WRONG_CHECKOUT",
    ):
        assert token in body, f"{token} has no remedy named in the bootstrap protocol"
    # The two link-creating remedies must be runnable, not described.
    assert "ln -s <checkout> ~/.claude/skills/h-mad" in body
    assert "ln -s <checkout>/hooks/h-mad-tdd-gate.sh" in body


def test_bootstrap_treats_a_missing_checker_as_the_finding():
    """The commonest way for the script to be absent is an install that predates
    it — i.e. the exact stale copy the check exists for. Silence must not read
    as consent in the one place the original defect is most likely to sit."""
    body = " ".join(_bootstrap().split())
    assert "No `INSTALL:` line at all" in body
    assert "bootstrap:install_broken" in body


# ── the script must actually implement what the doc promises ─────────────────

def test_every_detail_line_named_in_the_docs_exists_in_the_script():
    """Docs and implementation drift apart silently; this pins them together."""
    script = SCRIPT.read_text()
    skill = _skill()
    for token in (
        "SKILL_NOT_SYMLINK",
        "SKILL_NOT_INSTALLED",
        "SKILL_DANGLING",
        "SKILL_NOT_A_CHECKOUT",
        "HOOK_NOT_INSTALLED",
        "HOOK_DANGLING",
        "SPLIT_INSTALL",
        "SIBLING_NOT_SYMLINK",
        "SIBLING_DANGLING",
        "SIBLING_WRONG_CHECKOUT",
    ):
        assert token in script, f"{token} documented but not implemented"
        assert token in skill, f"{token} implemented but not documented"


def test_helper_script_registry_lists_it():
    registry = _section(
        _skill(), "## Helper scripts", "## Working a `skill-monitoring` item"
    )
    assert "h_mad_install_check.py" in registry


# ── coexisting plugins that DENY (not warn) ──────────────────────────────────

def test_interactions_record_the_heredoc_commit_collision():
    body = _interactions()
    assert "ENH-310" in body
    assert "git commit -F" in body, "the remedy must be named, not just the problem"


def test_interactions_record_that_these_hooks_deny_rather_than_warn():
    body = _interactions()
    assert "deny" in body.lower()


def test_interactions_record_the_per_rule_retry_cost():
    """N flagged constructs in one file costs N refused writes, one rule at a time."""
    body = _interactions()
    assert "security-guidance" in body
    assert "first" in body.lower() and "retry" in body.lower()


def test_interactions_point_at_the_local_patches_and_upstream_reports():
    body = _interactions()
    assert "docs/patches/" in body
    assert "#145" in body and "#5085" in body


def test_interactions_warn_that_the_local_patches_are_volatile():
    """Both live in version-pinned plugin caches an update replaces wholesale."""
    body = _interactions()
    assert "verify" in body.lower()
