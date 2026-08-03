"""The agy SKILL-reviewer prompt template is bundled and wired.

The skill already ships a spec reviewer (`agy-spec-reviewer-prompt.md`, Phase 5e)
and an architectural reviewer (`agy-architectural-reviewer-prompt.md`, 6a-prime).
Both are phase-gated and take an impl-plan task plus a Codex report as input, so
neither fits reviewing a *skill* — a doc+script family with no task and no report,
where the question is whether the instructions can be followed at all.

That review ran four times (handoff, h-mad, orca-cli, orchestration) off an ad-hoc
scratchpad prompt rebuilt each time. These tests pin the bundled template, the
three rules that carry its value, and its wiring into SKILL.md.

The `--help`-not-the-guide rule is the one worth stating twice: a review prompt
that names a vendor *guide* as ground truth manufactures false findings. One run
produced four separate "undocumented flag" findings and every one was a real flag
the guide had simply omitted — acting on them would have deleted working code.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEWER = REPO_ROOT / "h-mad" / "references" / "agy-skill-reviewer-prompt.md"
SKILL = REPO_ROOT / "h-mad" / "SKILL.md"


def _norm(text: str) -> str:
    """Collapse runs of whitespace so a literal survives reflow/indentation."""
    return " ".join(text.split())


def test_skill_reviewer_prompt_reference_exists() -> None:
    assert REVIEWER.is_file(), f"missing bundled skill-reviewer template: {REVIEWER}"


@pytest.mark.parametrize(
    "literal,why",
    [
        (
            "a flag's absence from the guide is not evidence the flag does not exist",
            "the false-finding class this template exists to prevent",
        ),
        (
            "Before reporting any flag, subcommand, or exit code as missing, unsupported, or "
            "renamed, run its `--help` and quote the real signature",
            "the runnable check, not just the warning — a rule without the means is improvised around",
        ),
        (
            "A finding you cannot classify is a finding you have not verified",
            "forces [OURS]/[UPSTREAM]/[USAGE] triage before effort is spent",
        ),
        (
            "Before claiming anything is MISSING, grep for it and say what you grepped",
            "reviews have asserted an absence for something present just outside their window",
        ),
        (
            "VERDICT: <CLEAN | NEEDS_WORK>",
            "the caller parses this line",
        ),
    ],
)
def test_the_load_bearing_instructions_are_present(literal: str, why: str) -> None:
    assert _norm(literal) in _norm(REVIEWER.read_text()), why


def test_every_ownership_class_is_defined() -> None:
    # Naming the classes without defining them leaves the reviewer to guess which
    # bucket a vendor-managed file falls in — the distinction that decides whether
    # a finding is work or merely information.
    text = _norm(REVIEWER.read_text())
    for cls in ("`[OURS]`", "`[UPSTREAM]`", "`[USAGE]`"):
        assert cls in text, f"{cls} is never defined in the template"


def test_the_template_is_wired_into_the_skill() -> None:
    text = _norm(SKILL.read_text())
    assert "## Reviewing a skill with agy" in text, "no SKILL.md section routes to the template"
    assert "references/agy-skill-reviewer-prompt.md" in text, (
        "a bundled template nothing references is a file, not a skill upgrade"
    )


def test_the_skill_states_the_exec_transport_and_why_a_stale_pin_is_irrelevant() -> None:
    # `exec` needs only the CLI on PATH. Without this, a `PREFLIGHT: FAIL` from an
    # unrelated stale pin reads as "cannot review" and the reviewer re-pins for
    # nothing — observed live.
    text = _norm(SKILL.read_text())
    assert "hmad-dispatch exec agy <prompt-file> --cd <repo> --out <report.md>" in text, (
        "the dispatch command itself must be in the skill, not only in the template"
    )
    assert "pane-independent" in text and "stale pin" in text, (
        "must say a stale pin does not block exec, or a FAIL preflight blocks the review"
    )


def test_the_skill_carries_the_help_not_guide_rule() -> None:
    # The rule has to reach SKILL.md too: the orchestrator writes the prompt, and a
    # prompt naming the guide as ground truth is what caused the false findings.
    text = _norm(SKILL.read_text())
    assert "Ground truth is the binary, not its documentation" in text
    assert "run `<cmd> --help` before reporting a flag as missing or unsupported" in text, (
        "the runnable check must be stated where the prompt is authored"
    )


def test_the_probe_instruction_is_bounded_to_read_only() -> None:
    # The template invites the reviewer to run `--help` probes, which the sibling
    # prompts never do (they end "Do NOT invoke any tool other than view_file").
    # Inviting execution without bounding it is what let the first live run write a
    # placeholder entry into the project's permanent learnings file — the reviewer
    # probed `learn.py add` to see what it did. A review that mutates the tree it
    # reviews is worse than one that reports the behaviour as unverified.
    text = _norm(REVIEWER.read_text())
    assert "**Probes must be read-only.**" in text, "the probe invitation is unbounded"
    assert "Do NOT run any subcommand that writes" in text, (
        "the prohibition must be explicit; 'read-only' alone reads as advisory"
    )
    assert "Do NOT modify any file in the target tree" in text, (
        "the closing constraint must forbid mutation, as the sibling prompts do"
    )
    assert "report it as unverified" in text, (
        "without a sanctioned alternative the reviewer improvises — the exact "
        "hazard-named-command-withheld shape this skill family keeps regressing into"
    )


def test_no_prompt_mentions_a_slot_bracketed_in_prose() -> None:
    # SKILL.md 7.2 makes a residual `<INLINE_` grep a MANDATORY pre-dispatch halt,
    # and records the bracketed-in-header case as "a live failure, not a
    # hypothetical". `<INLINE_*>` matches no real slot name, so substitution never
    # touches it and it survives into the dispatched prompt — where it either trips
    # that halt or, worse, is read by the agent as an unfilled template and the
    # whole axis silently discounted.
    #
    # Found by dogfooding this template: staging asserted no unfilled slots
    # remained and the header tripped it. All five reference prompts carried it.
    # Scoped to every prompt, not to this one — a one-file assertion is how the
    # `git add -N` fix landed at one of four sites and stayed green.
    offenders = []
    for path in sorted((REPO_ROOT / "h-mad" / "references").glob("*.md")):
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if "<INLINE_*>" in line:
                offenders.append(f"{path.name}:{i}")
    assert not offenders, (
        "prose must name a slot bare (`INLINE_*`); only a real slot is bracketed — "
        f"these survive substitution and reach the agent as raw tokens: {offenders}"
    )


def test_verify_every_finding_is_cross_referenced_not_restated() -> None:
    # Single-source contract: the verification discipline already has a section.
    # A second independent statement of it can drift from the first.
    text = _norm(SKILL.read_text())
    assert '§"Verifying a review finding before acting on it"' in text, (
        "the review section must point at the existing rule rather than restating it"
    )
