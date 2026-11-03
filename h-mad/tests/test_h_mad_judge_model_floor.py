"""Row 2934 fix direction (3): judge roles never resolve below Opus.

A cheaper DOER's mistake surfaces as a red gate (TDD gate, mutation harness,
failure-diff). A cheaper JUDGE's mistake does not: an auditor or reviewer that
misses a real finding reports a clean verdict, and nothing downstream re-checks
a clean verdict. So the effort and model tiering of row 2934 stops at the
judges: `doc-auditor`, `change-reviewer`, and the spec/plan/design authors,
whose documents the rest of a run is measured against. `implplan-author` is
deliberately absent; the row names it as the one author worth an A/B below
Opus.

Two ways a judge could resolve lower, both pinned here:
  * its frontmatter `model:` — a lower tier, or `inherit`, which follows the
    parent session's model and so can be anything;
  * a prescribed `Agent(subagent_type: "<judge>", model: …)` in SKILL.md or a
    reference, which overrides the frontmatter for that dispatch.

Not reachable from the repository: `CLAUDE_CODE_SUBAGENT_MODEL` in the
environment overrides every subagent's model. That is an operator setting and
is stated in SKILL.md §"Helper work" rather than tested.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from skill_corpus import doc_text

SKILL_DIR = Path(__file__).resolve().parents[1]
AGENTS = SKILL_DIR / "agents"
JUDGES = ("doc-auditor", "change-reviewer", "spec-author", "plan-author", "design-author")
# Fable sits above Opus. An alias or a full model id of either family passes.
AT_LEAST_OPUS = re.compile(r"^(opus|fable|claude-(opus|fable)-[0-9a-z.-]+)$")
PRESCRIPTION = re.compile(r'Agent\(subagent_type: "(?P<role>[^"]+)"')


def _frontmatter(path: Path) -> dict[str, str]:
    head = path.read_text(encoding="utf-8").split("---", 2)[1]
    return {k.strip(): v.strip() for k, v in
            (line.split(":", 1) for line in head.strip().splitlines() if ":" in line)}


def _call_text(text: str, start: int) -> str:
    """The `Agent(...)` call starting at `start`, to its matching close paren.

    Quoted strings are skipped, because a prompt routinely contains parentheses.
    An unterminated call returns the rest of the text, so a malformed
    prescription is scanned rather than skipped.
    """
    depth, i, quote = 0, start, None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch == '"':
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]


def _corpus() -> dict[str, str]:
    docs = {"SKILL.md": doc_text(SKILL_DIR / "SKILL.md")}
    for p in sorted((SKILL_DIR / "references").glob("*.md")):
        docs[f"references/{p.name}"] = p.read_text(encoding="utf-8")
    return docs


@pytest.mark.parametrize("role", JUDGES)
def test_a_judge_pins_at_least_opus_in_its_frontmatter(role: str) -> None:
    model = _frontmatter(AGENTS / f"{role}.md").get("model", "")
    assert AT_LEAST_OPUS.match(model), (
        f"{role} pins model {model!r}; a judge below Opus turns real findings into clean verdicts"
    )


def test_inherit_is_not_a_floor() -> None:
    """`inherit` follows the parent session, which may be anything."""
    assert not AT_LEAST_OPUS.match("inherit")
    assert not AT_LEAST_OPUS.match("sonnet")
    assert not AT_LEAST_OPUS.match("claude-sonnet-5-5")
    assert AT_LEAST_OPUS.match("claude-opus-5-5") and AT_LEAST_OPUS.match("fable")


def test_no_prescribed_judge_dispatch_lowers_the_model() -> None:
    seen, low = 0, []
    for name, text in _corpus().items():
        for m in PRESCRIPTION.finditer(text):
            if m.group("role") not in JUDGES:
                continue
            seen += 1
            for model in re.findall(r'\bmodel:\s*"([^"]*)"', _call_text(text, m.start())):
                if not AT_LEAST_OPUS.match(model):
                    low.append(f"{name}: {m.group('role')} model={model!r}")
    assert seen >= 3, f"found only {seen} judge prescriptions; the census pattern is stale"
    assert not low, f"a prescribed judge dispatch lowers the model: {low}"


def test_the_call_scanner_reads_past_parentheses_inside_the_prompt() -> None:
    """Positive control: a `model:` after a prompt containing ')' is still found."""
    text = 'Agent(subagent_type: "doc-auditor", prompt: "see f(x) and (y)", model: "sonnet")'
    assert 'model: "sonnet"' in _call_text(text, 0)
