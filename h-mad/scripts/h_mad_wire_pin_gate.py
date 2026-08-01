#!/usr/bin/env python3
"""h_mad_wire_pin_gate.py — Phase-5b gate: no `wiring` task without a WIRE-PIN.

A wiring task's deliverable is a **connection**, and every Phase-5 gate after 5b is
scoped to the **callee** (`invariants.base.md` §"Connection enforcement"): 5d's RED
goes red because the callee is absent, 5e's revert test removes caller *and* callee
so its RED split returns identically for a wired and an unwired build, the
anti-gaming audit finds a callee-scoped unit test perfectly discriminating, and
6a-prime sees a call site that is present. Presence is not enforcement.

The impl-plan is therefore the last document where the obligation can be required
mechanically, and this gate is the requirement.

Verdicts, printed as a canonical token:

    WIREPIN: PASS tasks=3 wiring=1 unpinned=0        exit 0
    WIREPIN: FAIL tasks=3 wiring=2 unpinned=1        exit 0
    WIREPIN: UNSHAPED tasks=2 wiring=0 unpinned=0    exit 2

`UNSHAPED` means no task declares a shape, so the plan cannot be judged — the same
discipline as the audit gate refusing to score an extract with no Must-fix section:
"cannot judge" must never read as "nothing to fix". Exit 0 is reserved for a real
verdict (§"Audit-gate signal discipline"), so callers read the token, never `$?`.

Stdlib only: consumer suites invoke h-mad scripts with a bare `python3`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A task header, in the conventions shipped plans actually use:
#   `## Task 3: wire_bad`     `## Task 1 — wire_bad`
#   `## Task 0 (B9 gate): x`  `## M1 — TRIAL_FAMILY frozenset`   `### M5 — route`
# The id must be `Task <n>` or a module-style `M<n>`/`T<n>`: a looser pattern
# swallows prose headings ("## Module layout") and reports phantom unshaped
# tasks, which would FAIL every plan rather than judging it.
_TASK_RE = re.compile(
    r"^\s*#{2,3}\s+"
    r"(?:Task\s+(?P<num>[^\s:(–—-]+)|(?P<mod>[MT]\d+))"
    r"\s*(?:\([^)]*\))?"  # `(B9 gate, pre-code, non-test)` qualifies the id
    r"\s*(?:[:–—-]\s*(?P<name>.*))?$",
    re.IGNORECASE,
)

# `**WIRE-PIN** (`wiring` shape only): `test_x``  — the parenthetical qualifier in
# the impl-plan template is part of the label, not of the value.
_FIELD_RE = re.compile(
    r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(Task\s+shape|WIRE-PIN|WIRE)\s*\*{0,2}"
    r"\s*(?:\([^)]*\))?\s*\*{0,2}\s*:\s*(.*)$",
    re.IGNORECASE,
)

# Values that look filled in and are not. `<...>` is the template placeholder the
# generator is supposed to replace; the rest are the ways a generator says nothing.
_FILLER = {"tbd", "n/a", "na", "none", "-", "--", "todo", "?", "x"}


def _clean(value: str) -> str:
    """Strip markdown decoration so a value is judged on its content."""
    return value.replace("`", "").replace("*", "").replace("_", "").strip()


def _is_real_value(value: str | None) -> bool:
    """True iff the field carries something a human actually filled in."""
    if value is None:
        return False
    text = _clean(value)
    if not text or text.lower() in _FILLER:
        return False
    # An unreplaced template placeholder: `<test id that fails when ...>`.
    if text.startswith("<") and text.endswith(">"):
        return False
    return True


def _declared_shape(value: str) -> str | None:
    """The task's shape, or None when nothing was actually chosen.

    The template line offers `new-behaviour | refactor | wiring`; left unedited it
    declares nothing, and must not be read as a shape — least of all as a shape
    that happens to exclude `wiring`.
    """
    text = _clean(value)
    if "|" in text:
        return None
    text = text.lower()
    return text or None


def _parse_tasks(text: str) -> list[dict]:
    tasks: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        header = _TASK_RE.match(line)
        if header:
            num, mod = header.group("num"), header.group("mod")
            current = {
                "id": mod.upper() if mod else f"Task {num.strip()}",
                "name": (header.group("name") or "").strip(),
                "shape": None,
                "wire": None,
                "pin": None,
            }
            tasks.append(current)
            continue
        if current is None:
            continue
        field = _FIELD_RE.match(line)
        if not field:
            continue
        label = " ".join(field.group(1).split()).lower()
        value = field.group(2)
        if label == "task shape":
            current["shape"] = _declared_shape(value)
        elif label == "wire-pin":
            current["pin"] = value
        elif label == "wire":
            current["wire"] = value
    return tasks


def check(plan_path: Path) -> dict:
    """Classify an impl-plan. Raises OSError if the plan cannot be read."""
    tasks = _parse_tasks(plan_path.read_text(encoding="utf-8"))

    if not any(task["shape"] for task in tasks):
        return {
            "verdict": "UNSHAPED",
            "tasks": len(tasks),
            "wiring": 0,
            "unpinned": [],
            "unshaped": [task["id"] for task in tasks],
        }

    # The plan is shape-aware, so a task with no shape is a hiding place for a
    # wiring task — precisely what this gate exists to close.
    unshaped = [task["id"] for task in tasks if not task["shape"]]

    wiring = [task for task in tasks if task["shape"] == "wiring"]
    unpinned = []
    for task in wiring:
        missing = [
            label
            for label, value in (("WIRE", task["wire"]), ("WIRE-PIN", task["pin"]))
            if not _is_real_value(value)
        ]
        if missing:
            unpinned.append(f"{task['id']} ({task['name']}): missing {', '.join(missing)}")

    verdict = "FAIL" if (unpinned or unshaped) else "PASS"
    return {
        "verdict": verdict,
        "tasks": len(tasks),
        "wiring": len(wiring),
        "unpinned": unpinned,
        "unshaped": unshaped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H-MAD Phase-5b wire-pin gate")
    parser.add_argument("impl_plan", type=Path)
    args = parser.parse_args(argv)

    try:
        result = check(args.impl_plan)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # "<feature>.impl-plan.md" -> "<feature>" (project-agnostic, same as the audit gate).
    feature = args.impl_plan.name.split(".")[0] or "unknown"

    print(
        f"WIREPIN: {result['verdict']} tasks={result['tasks']} "
        f"wiring={result['wiring']} unpinned={len(result['unpinned'])}"
    )
    for item in result["unpinned"]:
        print(f"  unpinned: {item}")
    for item in result["unshaped"]:
        print(f"  unshaped: {item}")
    if result["verdict"] == "UNSHAPED":
        print(
            "  no task declares a **Task shape** — this plan cannot be judged. "
            "A wiring task here would ship its connection untested through every "
            "later gate; add the field (see references/inline-protocols.md §Phase 5a)."
        )
    print(f"[H-MAD] {feature} wirepin {result['verdict']}")
    return 2 if result["verdict"] == "UNSHAPED" else 0


if __name__ == "__main__":
    sys.exit(main())
