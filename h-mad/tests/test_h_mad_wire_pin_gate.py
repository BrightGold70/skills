"""Phase-5b gate: a `wiring` task may not reach 5d without a WIRE-PIN.

A wiring task's deliverable is a connection, and every downstream Phase-5 gate is
scoped to the callee (`invariants.base.md` §"Connection enforcement"). The
impl-plan is therefore the LAST document where the obligation can be required
mechanically: after 5b nothing can tell a wired build from an unwired one.

The gate reads an impl-plan and refuses a `wiring`-shaped task whose WIRE-PIN is
absent, still a template placeholder, or a filler value.

Signal discipline (`invariants.base.md` §"Audit-gate signal discipline"): exit 0
carries a verdict (PASS/FAIL) and non-zero is reserved for an operational error —
so the caller reads the token, never `$?`.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
GATE = SCRIPTS / "h_mad_wire_pin_gate.py"

sys.path.insert(0, str(SCRIPTS))
from h_mad_wire_pin_gate import check  # noqa: E402


HEADER = "# Implementation Plan: demo\n\n## Executive Summary\nDemo.\n\n"


def _task(
    n: int,
    name: str = "mod",
    shape: str | None = "wiring",
    wire: str | None = "`engine/run.py:dispatch` -> `tools.shadow.measure`",
    pin: str | None = "`test_run_calls_measure`",
) -> str:
    out = [f"## Task {n}: {name}\n"]
    out.append("**Production file**: `engine/run.py`\n")
    out.append("**Test file**: `tests/test_run.py`\n")
    if shape is not None:
        out.append(f"**Task shape**: `{shape}`\n")
    if wire is not None:
        out.append(f"**WIRE**: {wire}\n")
    if pin is not None:
        out.append(f"**WIRE-PIN**: {pin}\n")
    out.append("\n**Acceptance Criteria**:\n- [ ] AC-1.1: something testable\n\n")
    return "".join(out)


def _plan(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "demo.impl-plan.md"
    path.write_text(HEADER + body, encoding="utf-8")
    return path


# --- the refusal ---------------------------------------------------------


def test_wiring_task_with_a_real_pin_passes(tmp_path: Path) -> None:
    result = check(_plan(tmp_path, _task(1)))
    assert result["verdict"] == "PASS", result
    assert result["wiring"] == 1
    assert result["unpinned"] == []


@pytest.mark.parametrize(
    "pin,why",
    [
        (None, "no WIRE-PIN line at all"),
        ("<test id that fails when ONLY the wire is removed, callee intact>", "template placeholder"),
        ("TBD", "filler"),
        ("N/A", "filler"),
        ("None", "filler"),
        ("", "empty value"),
        ("   ", "whitespace-only value"),
    ],
)
def test_wiring_task_without_a_real_pin_fails(tmp_path: Path, pin: str | None, why: str) -> None:
    result = check(_plan(tmp_path, _task(1, pin=pin)))
    assert result["verdict"] == "FAIL", f"{why} was accepted as a pin: {result}"
    assert "Task 1" in " ".join(result["unpinned"]), result


def test_wiring_task_without_a_wire_fails(tmp_path: Path) -> None:
    # WIRE names what to revert; without it the 5e wire-scoped revert has no target.
    result = check(_plan(tmp_path, _task(1, wire=None)))
    assert result["verdict"] == "FAIL", result


# --- the negative case: the guard must NOT fire when it should not --------
#
# A refusal test that only ever observes refusals passes forever against a guard
# that refuses unconditionally. These pin the other direction.


@pytest.mark.parametrize("shape", ["new-behaviour", "refactor"])
def test_non_wiring_task_needs_no_pin(tmp_path: Path, shape: str) -> None:
    result = check(_plan(tmp_path, _task(1, shape=shape, wire=None, pin=None)))
    assert result["verdict"] == "PASS", f"gate over-fired on a {shape} task: {result}"
    assert result["wiring"] == 0


def test_mixed_plan_reports_only_the_unpinned_wiring_task(tmp_path: Path) -> None:
    body = (
        _task(1, "parser", shape="new-behaviour", wire=None, pin=None)
        + _task(2, "wire_ok")
        + _task(3, "wire_bad", pin=None)
    )
    result = check(_plan(tmp_path, body))
    assert result["verdict"] == "FAIL"
    assert result["tasks"] == 3 and result["wiring"] == 2
    joined = " ".join(result["unpinned"])
    assert "Task 3" in joined and "Task 2" not in joined, joined


# --- the hiding place ----------------------------------------------------


def test_undeclared_shape_in_a_shape_aware_plan_fails(tmp_path: Path) -> None:
    # If any task declares a shape the plan is shape-aware, so an undeclared task
    # is a hiding place for a wiring task — the one thing this gate exists to stop.
    body = _task(1) + _task(2, "legacy", shape=None, wire=None, pin=None)
    result = check(_plan(tmp_path, body))
    assert result["verdict"] == "FAIL", result
    assert "Task 2" in " ".join(result["unshaped"]), result


def test_plan_with_no_shapes_at_all_is_unshaped_not_pass(tmp_path: Path) -> None:
    # "cannot judge" must never read as "nothing to fix" — same discipline as the
    # audit gate refusing to score an extract with no Must-fix/Should-fix sections.
    body = _task(1, shape=None, wire=None, pin=None) + _task(2, "other", shape=None, wire=None, pin=None)
    result = check(_plan(tmp_path, body))
    assert result["verdict"] == "UNSHAPED", result


# --- tolerance: the field must survive how a generator writes it ----------


@pytest.mark.parametrize(
    "line",
    [
        "**Task shape**: `wiring`",
        "**Task shape**: wiring",
        "**Task Shape**: WIRING",
        "- **Task shape**: `wiring`",
        "**Task shape**: `new-behaviour` | `refactor` | `wiring`",  # template left unedited
    ],
)
def test_shape_line_recognised(tmp_path: Path, line: str) -> None:
    body = f"## Task 1: mod\n{line}\n**WIRE**: `a.py:f` -> `b.g`\n**WIRE-PIN**: `test_f_calls_g`\n"
    result = check(_plan(tmp_path, body))
    if "|" in line:
        # An unedited template alternation declares nothing — it must not read as
        # a shape, and it must not read as PASS either.
        assert result["verdict"] == "UNSHAPED", result
    else:
        assert result["wiring"] == 1, f"shape line not recognised: {line!r} -> {result}"


# --- tolerance: the task header must survive how a plan is actually written --
#
# Dogfooding the gate against ~50 shipped impl-plans returned `tasks=0` for
# several of them: the parser required the literal word "Task" AND a colon, and
# real plans use an em-dash, a parenthetical qualifier, or module-style `M<N>`
# headers. A plan the parser cannot see reports UNSHAPED, so a *shaped* plan in
# those conventions would be refused for declaring nothing — a false halt on
# correct work, and the reason this tolerance is pinned rather than assumed.


@pytest.mark.parametrize(
    "header,why",
    [
        ("## Task 1: mod", "colon form"),
        ("## Task 1 — mod", "em-dash form, seen in shipped plans"),
        ("## Task 0 (B9 gate, pre-code, non-test): mod", "parenthetical qualifier before the colon"),
        ("## M1 — mod", "module-style id, the dominant convention in shipped plans"),
        ("### M5 — mod", "h3 module-style id"),
        ("### Task 2: mod", "h3 colon form"),
    ],
)
def test_task_header_conventions_are_parsed(tmp_path: Path, header: str, why: str) -> None:
    body = f"{header}\n**Task shape**: `wiring`\n**WIRE**: `a.py:f` -> `b.g`\n**WIRE-PIN**: `test_f_calls_g`\n"
    result = check(_plan(tmp_path, body))
    assert result["tasks"] == 1, f"header not parsed ({why}): {header!r} -> {result}"
    assert result["verdict"] == "PASS", result


@pytest.mark.parametrize(
    "header",
    [
        "## Executive Summary",
        "## Acceptance Criteria",
        "## Module layout",
        "## Testing strategy",
        "### Migration notes",
        # Single-word headings are the discriminating cases: a multi-word heading
        # is rejected by the trailing `$` alone, so a parser relaxed to accept any
        # word as an id still passes those. These are lifted verbatim from shipped
        # plans and are the ones such a relaxation actually swallows.
        "## Scope",
        "## Rollback",
        "## Verification",
        "### RED",
        "### GREEN",
    ],
)
def test_prose_headings_are_not_mistaken_for_tasks(tmp_path: Path, header: str) -> None:
    # A parser loose enough to swallow prose headings would report phantom
    # unshaped "tasks" and FAIL every plan — the guard has to discriminate, not
    # merely match more.
    body = f"## Task 1: mod\n**Task shape**: `refactor`\n\n{header}\nSome prose.\n"
    result = check(_plan(tmp_path, body))
    assert result["tasks"] == 1, f"{header!r} was parsed as a task -> {result}"
    assert result["verdict"] == "PASS", result


# --- CLI contract --------------------------------------------------------


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), *args], capture_output=True, text=True
    )


def test_cli_prints_canonical_token_and_exits_zero_on_a_verdict(tmp_path: Path) -> None:
    plan = _plan(tmp_path, _task(1, pin=None))
    proc = _run(str(plan))
    assert proc.returncode == 0, f"a FAIL verdict must exit 0: {proc.stderr}"
    assert "WIREPIN: FAIL" in proc.stdout, proc.stdout
    assert "tasks=1" in proc.stdout and "wiring=1" in proc.stdout, proc.stdout
    assert "[H-MAD] demo wirepin FAIL" in proc.stdout, proc.stdout


def test_cli_pass_token(tmp_path: Path) -> None:
    proc = _run(str(_plan(tmp_path, _task(1))))
    assert proc.returncode == 0
    assert "WIREPIN: PASS" in proc.stdout, proc.stdout


def test_cli_missing_file_is_an_operational_error(tmp_path: Path) -> None:
    proc = _run(str(tmp_path / "nope.md"))
    assert proc.returncode == 2, "a missing plan is an operational error, not a verdict"
    assert "WIREPIN: PASS" not in proc.stdout


def test_cli_unshaped_is_not_a_pass(tmp_path: Path) -> None:
    plan = _plan(tmp_path, _task(1, shape=None, wire=None, pin=None))
    proc = _run(str(plan))
    assert "WIREPIN: UNSHAPED" in proc.stdout, proc.stdout
    assert proc.returncode == 2, "cannot-judge must not exit 0 alongside real verdicts"


def test_gate_is_stdlib_only() -> None:
    # Consumer suites invoke h-mad scripts with a bare `python3` that has no venv.
    source = GATE.read_text(encoding="utf-8")
    for banned in ("import yaml", "import requests", "from pydantic", "import jsonschema"):
        assert banned not in source, f"{banned} would break the bare-python3 callers"
