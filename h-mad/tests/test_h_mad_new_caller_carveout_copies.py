"""Bind the six FR-9 surfaces to one block without letting copies mask each other."""

import ast
import re
from pathlib import Path

import pytest

from docsections import titled_section


SKILL_DIR = Path(__file__).resolve().parents[1]
PROMPT = SKILL_DIR / "references" / "codex-implementer-prompt.md"

# Verbatim spec FR-9's three-sentence block, with Markdown quote wrapping removed.
CANONICAL = (
    "A missing-symbol RED on the pin is valid **only** when the missing symbol is "
    "the caller the task creates, and the callee resolves at the RED base. "
    "The RED report must name both. GREEN must prove the wire by a wire-cut: "
    "delete the call only, keep the caller and the callee, and confirm the pin fails."
)

RED_ANCHOR = "1. For each FAILING test:"
WIRE_ANCHOR = "**If the dispatch carries a `WIRE:` / `WIRE-PIN:` line"
SKILL_ANCHOR = "**The third task shape is `wiring`, and counts cannot gate it.**"
RECOVERY_ANCHOR = "`step5d:red_wrong_reason:<module>`"
ASSEMBLER_ANCHOR = "The WIRE-PIN is this task's single load-bearing test."
GREEN_ANCHOR = "For GREEN phase (5e):"


def collapse(text):
    return " ".join(text.split())


def _only(spans, locator):
    assert len(spans) == 1, (
        f"{locator}: expected exactly one span, found {len(spans)}"
    )
    return spans[0]


def _paragraph(text, anchor, locator):
    return _only(
        [block for block in re.split(r"\n[ \t]*\n", text)
         if block.lstrip().startswith(anchor)],
        locator,
    )


def L1(text):
    return _only(
        re.findall(r"^1\. For each FAILING test:.*?(?=\n2\. )", text, re.M | re.S),
        "L1",
    )


def L2(text):
    return _paragraph(text, WIRE_ANCHOR, "L2")


def L3(text):
    section = titled_section(text, "Phase 5 (Implementation) sub-steps")
    return _paragraph(section, SKILL_ANCHOR, "L3")


def L4(text):
    cells = [re.split(r"(?<!\\)\|", line) for line in text.splitlines()]
    return _only(
        [row[4] for row in cells
         if len(row) >= 6 and row[3].strip() == RECOVERY_ANCHOR],
        "L4",
    )


def _assembler_copy_nodes(text):
    module = ast.parse(text)
    assemble = _only(
        [node for node in module.body
         if isinstance(node, ast.FunctionDef) and node.name == "assemble"],
        "L5 assemble",
    )
    return [node for node in ast.walk(assemble)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and ASSEMBLER_ANCHOR in node.value]


def L5(text):
    return _only(_assembler_copy_nodes(text), "L5").value


def L6(text):
    return _paragraph(text, GREEN_ANCHOR, "L6")


# IDs, source files, locators, and their structural anchors (not the missing block).
COPIES = [
    ("L1", PROMPT, L1, RED_ANCHOR),
    ("L2", PROMPT, L2, WIRE_ANCHOR),
    ("L3", SKILL_DIR / "SKILL.md", L3, SKILL_ANCHOR),
    ("L4", SKILL_DIR / "references" / "failure-recovery.md", L4, RECOVERY_ANCHOR),
    ("L5", SKILL_DIR / "scripts" / "h_mad_assemble_tdd.py", L5, ASSEMBLER_ANCHOR),
    ("L6", PROMPT, L6, GREEN_ANCHOR),
]


@pytest.mark.parametrize("name,path,locate,anchor", COPIES, ids=[c[0] for c in COPIES])
def test_copy_carries_the_canonical_block(name, path, locate, anchor):
    span = locate(path.read_text(encoding="utf-8"))
    count = collapse(span).count(collapse(CANONICAL))
    assert count == 1, (
        f"{name} ({path.relative_to(SKILL_DIR)}): expected exactly one complete "
        f"FR-9 canonical three-sentence new-caller carve-out block; found {count}"
    )


@pytest.mark.parametrize("name,path,locate,anchor", COPIES, ids=[c[0] for c in COPIES])
@pytest.mark.parametrize("cardinality", ["zero", "two"])
def test_locator_refuses_zero_or_many_spans(name, path, locate, anchor, cardinality):
    source = path.read_text(encoding="utf-8")
    span = locate(source)  # The unchanged source must first select exactly one span.
    if name == "L4":
        # Locate the row through the remedy cell that L4 actually returns.
        anchor = span.strip()
    assert anchor in span

    expected = 0 if cardinality == "zero" else 2
    if name == "L4":
        row = _only([line for line in source.splitlines() if anchor in line],
                    "L4 control")
        doctored = source.replace(
            row, "" if cardinality == "zero" else row + "\n" + row, 1,
        )
    elif cardinality == "zero":
        doctored = source.replace(anchor, "REMOVED FR-9 locator anchor")
    else:
        if name in ("L3", "L6"):
            # Duplicate the selected paragraph in place, keeping its context.
            assert source.count(span) == 1
            doctored = source.replace(span, span + "\n\n" + span, 1)
        elif name == "L5":
            # Keep one assemble() and two distinct str constants inside it.
            node = _only(_assembler_copy_nodes(source), "L5 control")
            literal = ast.get_source_segment(source, node)
            assert literal is not None and source.count(literal) == 1
            doctored = source.replace(literal, f"({literal} + {literal})", 1)
        else:
            doctored = source + "\n\n" + source

    with pytest.raises(
        AssertionError,
        match=re.escape(f"{name}: expected exactly one span, found {expected}"),
    ):
        locate(doctored)
