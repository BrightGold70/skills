"""Pin the two evidence-semantics rules that a wrong accessor makes invisible.

Both rules exist because an *absent* measurement and a *zero* measurement render
identically, so nothing in a run reports that they were violated:

  1. Every raw `orca … --json` payload is enveloped under `.result`. Reading a
     bare top-level key yields empty, and empty-from-a-wrong-path cannot be told
     apart from a genuinely empty result. Measured 2026-08-20 — a parser read a
     top-level `terminals` key and reported `terminals: 0` for a lane that had
     been used minutes earlier.
  2. A delivery surface reporting `accepted` / `bytesWritten` / `input_accepted`
     confirms the bytes were handed to a terminal, never that the receiving agent
     consumed them.

Guidance is the only enforcement either rule has: no gate can fire on a count
that was never taken. So the guidance itself is what gets pinned, the same way
`test_h_mad_claim_staleness.py` pins the `--force` wording. Literals are
whitespace-normalised so a markdown reflow cannot break them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_ROOT / "references"
CANONICAL = REFERENCES / "agent-substrate.md"
SECTION = "The `.result` envelope"


def _norm(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _require(haystack: str, literal: str, why: str, where: str) -> None:
    assert " ".join(literal.split()) in haystack, f"{where} dropped guidance: {why}"


# --- rule 1: the .result envelope ------------------------------------------


def test_canonical_envelope_rule_is_stated_once_in_agent_substrate() -> None:
    doc = _norm(CANONICAL)
    for literal, why in [
        (
            "Every raw `orca … --json` payload is enveloped under `.result`.",
            "the envelope is the fact every wrong accessor gets wrong",
        ),
        (
            "empty-from-a-wrong-path is indistinguishable from a genuinely empty result",
            "without the indistinguishability, a zero still reads as evidence",
        ),
        (
            "existence and content are two columns, never one",
            "the two-column framing is the reusable half of the rule",
        ),
        (
            "jq -e '.result.terminals'",
            "the rule is unusable without the assertion that implements it",
        ),
    ]:
        _require(doc, literal, why, "agent-substrate.md")


def test_wrapper_unwrap_is_documented_so_paths_are_not_copied_across_surfaces() -> None:
    # The trap is not knowing the envelope exists; it is that `hmad-dispatch`
    # strips it, so a top-level path copied off wrapper docs onto a raw `orca`
    # call silently measures nothing.
    _require(
        _norm(CANONICAL),
        "`hmad-dispatch` unwraps the envelope for you.",
        "mixing wrapper paths with raw paths is the documented way into the trap",
        "agent-substrate.md",
    )


def test_hmad_dispatch_guards_the_container_before_iterating_worktrees() -> None:
    # agent-substrate.md cites this line as the reference implementation. If the
    # guard is ever dropped, the doc starts pointing at a pattern that no longer
    # exists in the code it names.
    shell = (SKILL_ROOT / "scripts" / "hmad-dispatch.sh").read_text(encoding="utf-8")
    assert "jq -e '.result.worktrees'" in shell, (
        "hmad-dispatch.sh dropped the container assertion that agent-substrate.md "
        "cites as the reference implementation of the envelope rule"
    )


def test_per_path_restatements_point_at_the_canonical_section() -> None:
    # A fourth local copy of this rule is the failure mode, not the fix: a class
    # fixed in one place and restated in three goes stale in the restatements.
    _require(
        _norm(SKILL_ROOT / "SKILL.md"),
        f"stated once in `references/agent-substrate.md` §\"{SECTION}",
        "the tail[] note must defer to the canonical rule, not re-state it",
        "SKILL.md",
    )


# --- rule 2: handed to the terminal != consumed by the agent ----------------


def test_delivery_surfaces_are_documented_as_acceptance_not_action() -> None:
    doc = _norm(REFERENCES / "orchestration-mode.md")
    for literal, why in [
        (
            "`accepted: true` / `bytesWritten: <n>` from `orca terminal send` is the same class",
            "terminal send is the surface the other two rules did not cover",
        ),
        (
            "`bytesWritten` in particular measures your payload, not their behaviour",
            "a byte count reads as delivery proof unless this is said outright",
        ),
        (
            "rules out only the **stale-pin** failure",
            "`connected: true` is the near-miss that looks like pickup proof",
        ),
        (
            "none confirms *consumed by the agent*",
            "the three surfaces must be named as one class so they cannot drift",
        ),
    ]:
        _require(doc, literal, why, "orchestration-mode.md")


# --- the sibling skill (present in this repo; h-mad stays standalone) -------


def _handoff_skill() -> str:
    path = SKILL_ROOT.parent / "handoff" / "SKILL.md"
    if not path.is_file():
        pytest.skip("handoff skill not installed alongside h-mad")
    return _norm(path)


def test_handoff_refuses_to_overwrite_a_comment_it_could_not_read() -> None:
    # The destructive instance: "comment is empty" and "I could not read the
    # comment" are the same value and imply opposite actions, and the wrong one
    # clobbers a human's note.
    doc = _handoff_skill()
    for literal, why in [
        (
            "refusing to overwrite",
            "an unreadable comment must skip the stamp, not replace the field",
        ),
        (
            "only NOW is empty meaningful",
            "emptiness is only evidence after the container is proven present",
        ),
    ]:
        _require(doc, literal, why, "handoff/SKILL.md")


def test_handoff_does_not_report_a_send_as_a_pickup() -> None:
    _require(
        _handoff_skill(),
        "**A successful send is not a pickup.**",
        "HANDOVER hands off and stops watching, so the send response is the "
        "only thing a sender sees and must not be reported as acceptance by the receiver",
        "handoff/SKILL.md",
    )
