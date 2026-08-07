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

    WIREPIN: PASS tasks=3 wiring=1 unpinned=0 mislabeled=0        exit 0
    WIREPIN: FAIL tasks=3 wiring=2 unpinned=1 mislabeled=0        exit 0
    WIREPIN: UNSHAPED tasks=2 wiring=0 unpinned=0 mislabeled=0    exit 2
    WIREPIN: UNREADABLE                                           exit 2

`mislabeled` is on the summary line because a demotion FAILs with `wiring=0
unpinned=0`: every count a reader would check reads clean, and a FAIL whose
summary shows nothing wrong invites "the gate is broken" over "the plan is".

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

import h_mad_wire_registry

# A task header, in the conventions shipped plans actually use:
#   `## Task 3: wire_bad`     `## Task 1 — wire_bad`
#   `## Task 0 (B9 gate): x`  `## M1 — TRIAL_FAMILY frozenset`   `### M5 — route`
# The id must be `Task <n>` or a module-style `M<n>`/`T<n>`: a looser pattern
# swallows prose headings ("## Module layout") and reports phantom unshaped
# tasks, which would FAIL every plan rather than judging it.
#
# The id must also START WITH A DIGIT. "Task" followed by any word swallows
# `## Task decomposition` and `## Task outline` — both real, both in plans with no
# task headers at all, so each turns a true `tasks=0` into `tasks=1`. That used to
# be cosmetic; now that `tasks=0` selects the operator's remedy it is load-bearing.
# Every id in the shipped corpus is digit-led (`0`, `4.a`, `6.1.5`, `7b`, `13.6`).
_TASK_RE = re.compile(
    r"^\s*#{2,3}\s+"
    r"(?:Task\s+(?P<num>\d[^\s:(–—]*)|(?P<mod>[MT]\d+))"
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

# Cuts a qualifier — `wiring (connects X to Y)`, `new-behaviour — pure helpers` —
# off the value. `_SHAPE_RE`'s word boundary already tolerates a trailing qualifier
# on its own, so this exists for one narrow job: the `|` test below must see the
# shape WITHOUT its qualifier, or `wiring (engine | tools seam)` reads as an unedited
# `new-behaviour | refactor | wiring` template and halts correct work. That is also
# why the cut runs BEFORE the `|` test, not after.
#
# An ASCII hyphen is deliberately NOT a terminator: `new-behaviour` contains one.
_SHAPE_QUALIFIER_RE = re.compile(r"[(,;–—].*$", re.DOTALL)

# The shape's only job is to decide whether the wiring obligation applies, so it is
# matched against a closed set and anything else reads as UNDECLARED. Trimming
# qualifiers alone cannot be the whole rule: it leaves every unrecognised word
# (`wire`, `connection`, `not-wiring`) meaning "declared something, therefore not
# wiring" — a silent PASS on precisely the task this gate exists to catch. Fail
# closed: an unrecognised value is a hiding place, exactly like a missing one.
# The set is the template's own alternation (`references/inline-protocols.md` §Phase 5a).
_SHAPE_RE = re.compile(r"^(new-behaviours?|new-behaviors?|refactor|wiring)(?![\w-])", re.IGNORECASE)

# WIRE values come from human-authored plans and the shipped template uses a
# Unicode right arrow. Keep the allowlist explicit and longest-first so `-->`
# is consumed as one token rather than as `-` followed by `->`.
_WIRE_ARROW_RE = re.compile("|".join(
    re.escape(arrow) for arrow in ("-->", "->", "=>", "→", "⟶", "➜", "➔")
))


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
    """The task's shape, or None when nothing recognisable was chosen.

    The template line offers `new-behaviour | refactor | wiring`; left unedited it
    declares nothing, and must not be read as a shape — least of all as a shape
    that happens to exclude `wiring`.

    The qualifier is cut first, so the alternation check that follows sees the same
    text a reader would call "the shape": a qualifier containing a `|` must not make
    a real, pinned shape read as an unedited template and halt correct work.
    """
    text = _SHAPE_QUALIFIER_RE.sub("", _clean(value)).strip()
    if "|" in text:
        return None
    match = _SHAPE_RE.match(text)
    return match.group(1).lower() if match else None


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
                # What the plan actually said, kept only so an unrecognised value
                # can be quoted back: "add the field" is the wrong remedy for a
                # field that is present and misspelled.
                "shape_raw": None,
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
            if _is_real_value(value):
                current["shape_raw"] = _clean(value)
        elif label == "wire-pin":
            current["pin"] = value
        elif label == "wire":
            current["wire"] = value
    return tasks


def _unshaped_entry(task: dict) -> str:
    """How an unshaped task is reported — blank and unrecognised need different fixes."""
    if task["shape_raw"]:
        return (
            f"{task['id']} ({task['name']}): declares `{task['shape_raw']}`, which is "
            "not `new-behaviour`, `refactor` or `wiring`"
        )
    return task["id"]


def check(plan_path: Path) -> dict:
    """Classify an impl-plan. Raises OSError if the plan cannot be read."""
    tasks = _parse_tasks(plan_path.read_text(encoding="utf-8"))

    if not any(task["shape"] for task in tasks):
        return {
            "verdict": "UNSHAPED",
            "tasks": len(tasks),
            "wiring": 0,
            "unpinned": [],
            "unshaped": [_unshaped_entry(task) for task in tasks],
            "mislabeled": [],
        }

    # The plan is shape-aware, so a task with no shape is a hiding place for a
    # wiring task — precisely what this gate exists to close. An unrecognised shape
    # word lands here too: it hides a wiring task just as effectively as a blank.
    unshaped = [_unshaped_entry(task) for task in tasks if not task["shape"]]

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

    # The other hiding place, and the cheaper one to reach: not an absent shape but
    # a *wrong* one. Closing only the absent case leaves a wiring task one edited
    # word away from a PASS. WIRE and WIRE-PIN are "`wiring` shape only" per the
    # impl-plan template, so a task carrying either under another shape contradicts
    # itself — and the filled-in field is the evidence, while the shape word is only
    # the label. Trust the evidence.
    #
    # `_is_real_value` is what keeps this usable: the template ships both lines on
    # every task, so an unfilled or placeholder value must read as "declared
    # nothing" rather than as a wire, or the guard fails every plan generated from
    # the template — refusing correct work, which is worse than the hole it closes.
    mislabeled = []
    for task in tasks:
        if not task["shape"] or task["shape"] == "wiring":
            continue
        present = [
            label
            for label, value in (("WIRE", task["wire"]), ("WIRE-PIN", task["pin"]))
            if _is_real_value(value)
        ]
        if present:
            mislabeled.append(
                f"{task['id']} ({task['name']}): declares `{task['shape']}` "
                f"but carries {', '.join(present)}"
            )

    verdict = "FAIL" if (unpinned or unshaped or mislabeled) else "PASS"
    return {
        "verdict": verdict,
        "tasks": len(tasks),
        "wiring": len(wiring),
        "unpinned": unpinned,
        "unshaped": unshaped,
        "mislabeled": mislabeled,
    }


def _register_wiring_tasks(
    tasks: list[dict], registry: Path, feature: str
) -> tuple[int, int]:
    """Register real wires from wiring tasks as one registry batch.

    Returns ``(registered, skipped)``. Registration is deliberately independent
    of the gate verdict, but a malformed WIRE must be visible rather than being
    mistaken for a plan with nothing to register.
    """
    entries = []
    skipped = 0
    for task in tasks:
        if task["shape"] != "wiring":
            continue
        wire = task["wire"]
        pin = task["pin"]
        if not _is_real_value(wire) or not _is_real_value(pin):
            skipped += 1
            continue
        match = _WIRE_ARROW_RE.search(wire)
        if match is None:
            skipped += 1
            print(
                f"  registration skipped: {task['id']} ({task['name']}): "
                f"WIRE has no recognised arrow: {wire!r}"
            )
            continue
        caller, callee = wire.replace("`", "").split(match.group(0), 1)
        caller, callee = caller.strip(), callee.strip()
        pin = pin.replace("`", "").strip()
        if not caller or not callee or not pin:
            skipped += 1
            continue
        entries.append(
            {
                "kind": "wire",
                "id": task["id"],
                "caller": caller,
                "callee": callee,
                "pin": pin,
                "owning_feature": feature,
            }
        )
    if entries:
        h_mad_wire_registry.register(entries, registry)
    return len(entries), skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="H-MAD Phase-5b wire-pin gate")
    parser.add_argument("impl_plan", type=Path)
    parser.add_argument("--feature")
    parser.add_argument(
        "--registry", type=Path, default=Path(h_mad_wire_registry.DEFAULT_REGISTRY)
    )
    args = parser.parse_args(argv)
    # The legacy human-facing marker still uses the conventional filename stem when
    # no feature flag is supplied. Registry ownership below never uses this value.
    display_feature = args.feature or args.impl_plan.name.split(".")[0] or "unknown"

    try:
        result = check(args.impl_plan)
    except OSError as exc:
        # The caller's contract is "read the `WIREPIN:` token, never `$?`", so a
        # failure announced on stderr alone is silence to anyone obeying it: no
        # token is what "the gate never ran" also looks like. Emit one.
        #
        # Deliberately WITHOUT the `tasks=`/`wiring=` fields every other verdict
        # carries. Those are counts of a parse that did not happen, and `tasks=` is
        # no longer cosmetic — it selects the operator's remedy (`tasks=0` routes to
        # `impl_plan_no_tasks`). Printing `tasks=0` here would fabricate the field
        # the router keys on and hand a wrong-path error the no-tasks remedy, which
        # is the misrouting the tasks=0 split exists to prevent. Absent counts also
        # make the token self-evidently a different shape from a real verdict.
        print(f"ERROR: {exc}", file=sys.stderr)
        print("WIREPIN: UNREADABLE")
        print(
            "  the plan could not be read, so nothing was judged — this is an "
            "operational error, not a verdict about the plan's contents. Check the "
            "path exists and is a readable file (halt `step5b:impl_plan_unreadable`)."
        )
        print(f"[H-MAD] {display_feature} wirepin UNREADABLE")
        return 2

    print(
        f"WIREPIN: {result['verdict']} tasks={result['tasks']} "
        f"wiring={result['wiring']} unpinned={len(result['unpinned'])} "
        f"mislabeled={len(result['mislabeled'])}"
    )
    for item in result["unpinned"]:
        print(f"  unpinned: {item}")
    for item in result["unshaped"]:
        print(f"  unshaped: {item}")
    for item in result["mislabeled"]:
        print(f"  mislabeled: {item}")
    if result["verdict"] == "PASS":
        if args.feature:
            tasks = _parse_tasks(args.impl_plan.read_text(encoding="utf-8"))
            registered, skipped = _register_wiring_tasks(tasks, args.registry, args.feature)
            print(f"  registration: registered={registered} skipped={skipped}")
        else:
            print("  registration skipped: --feature is required")
    if result["verdict"] == "UNSHAPED":
        # Same halt, two different plans behind it. `tasks=0` is not a missing
        # field — it is a plan the parser could not see a task in, and handing that
        # operator "add the **Task shape** field" sends them to edit a file that has
        # nothing to add it to.
        if result["tasks"] == 0:
            print(
                "  no task was found — this plan cannot be judged. The parser saw no "
                "`## Task <n>` or `## M<n>` header, so the shape field is not what is "
                "missing: check this is the impl-plan (not the design or a legacy "
                "`.plan.md`) and that its task headers follow that convention."
            )
        else:
            print(
                "  no task declares a **Task shape** — this plan cannot be judged. "
                "A wiring task here would ship its connection untested through every "
                "later gate; add the field (see references/inline-protocols.md §Phase 5a)."
            )
    print(f"[H-MAD] {display_feature} wirepin {result['verdict']}")
    return 2 if result["verdict"] == "UNSHAPED" else 0


if __name__ == "__main__":
    sys.exit(main())
