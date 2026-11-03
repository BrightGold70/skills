"""READ does not set a caveman level; it follows the one the user configured.

Measured 2026-11-03 on the first live `/handoff read` after the split: Step 0b
ran `Skill(skill: "caveman:caveman", args: "ultra")`, and the very next prompt
carried `CAVEMAN MODE ACTIVE (lite)` again. The caveman plugin keeps its level
in one machine-wide flag (`~/.claude/.caveman-active`) that only a prompt the
user types (`/caveman <level>`) or SessionStart writes; a model-invoked Skill
call writes nothing, so the per-turn hook restores the old level. Writing the
flag from READ would switch every concurrent session on the machine. Operator
decision 2026-11-03: drop the escalation.
"""
from __future__ import annotations

import re
from pathlib import Path

READ_MODE = Path(__file__).resolve().parents[1] / "references" / "read-mode.md"


def _step_0b() -> str:
    text = READ_MODE.read_text(encoding="utf-8")
    m = re.search(r"^### Step 0b:.*?(?=^### )", text, re.M | re.S)
    assert m, "read-mode.md has no Step 0b section"
    return m.group(0)


def test_read_never_invokes_the_caveman_skill() -> None:
    text = READ_MODE.read_text(encoding="utf-8")
    assert not re.search(r"Skill\(\s*skill:\s*\"caveman", text), (
        "READ must not invoke the caveman skill: a model-invoked level lasts one turn, "
        "and the plugin's per-turn hook restores the user's configured level"
    )


def test_step_0b_names_the_flag_and_the_supported_route() -> None:
    flat = " ".join(_step_0b().split())
    assert "machine-wide flag, `.caveman-active`" in flat, (
        "Step 0b must name the machine-wide flag it defers to"
    )
    assert "`/caveman ultra`" in flat, "Step 0b must name the user-typed route to a terser level"
