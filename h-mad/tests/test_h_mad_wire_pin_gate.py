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


# --- the second hiding place: a wrong shape, not a missing one -------------
#
# Closing "no shape declared" leaves "wrong shape declared" open, and the second
# is cheaper to reach: one word changes in a generated plan and the gate believes
# it. The template says WIRE/WIRE-PIN are "`wiring` shape only", so a task that
# carries either while declaring another shape contradicts itself. Trust the
# evidence in the plan over the label on it.


@pytest.mark.parametrize("shape", ["new-behaviour", "refactor"])
def test_wire_field_under_a_non_wiring_shape_is_a_mislabel(tmp_path: Path, shape: str) -> None:
    result = check(_plan(tmp_path, _task(1, shape=shape, pin=None)))
    assert result["verdict"] == "FAIL", f"a WIRE under `{shape}` was accepted: {result}"
    assert "Task 1" in " ".join(result["mislabeled"]), result


@pytest.mark.parametrize("shape", ["new-behaviour", "refactor"])
def test_wire_pin_field_under_a_non_wiring_shape_is_a_mislabel(tmp_path: Path, shape: str) -> None:
    # Either field alone is enough: a plan that names a pin has admitted the task
    # wires something, whatever the shape line says.
    result = check(_plan(tmp_path, _task(1, shape=shape, wire=None)))
    assert result["verdict"] == "FAIL", f"a WIRE-PIN under `{shape}` was accepted: {result}"
    assert "Task 1" in " ".join(result["mislabeled"]), result


def test_a_demoted_wiring_task_does_not_pass(tmp_path: Path) -> None:
    # The concrete mutation: take a correctly-pinned wiring task and change only
    # the shape word. Before this guard the gate returned PASS with wiring=0.
    body = _task(1, "wire_ok") + _task(2, "wire_demoted", shape="new-behaviour")
    result = check(_plan(tmp_path, body))
    assert result["verdict"] == "FAIL", result
    joined = " ".join(result["mislabeled"])
    assert "Task 2" in joined and "Task 1" not in joined, joined


@pytest.mark.parametrize("value", ["TBD", "N/A", "none", "-", "<caller/path.py>:<symbol>"])
def test_an_unfilled_wire_template_under_a_non_wiring_shape_is_not_a_mislabel(
    tmp_path: Path, value: str
) -> None:
    # The counter-direction, and the one that decides whether this guard is usable:
    # the impl-plan template ships WIRE/WIRE-PIN lines on every task. A refactor
    # task that simply left them unfilled has declared nothing and must still PASS,
    # or the guard fails every plan written from the template.
    result = check(_plan(tmp_path, _task(1, shape="refactor", wire=value, pin=value)))
    assert result["verdict"] == "PASS", f"unfilled `{value}` read as a real wire: {result}"
    assert result["mislabeled"] == [], result


def test_mislabel_is_reported_by_the_cli(tmp_path: Path) -> None:
    plan = _plan(tmp_path, _task(1, shape="new-behaviour"))
    proc = subprocess.run(
        [sys.executable, str(GATE), str(plan)], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
    assert "WIREPIN: FAIL" in proc.stdout, proc.stdout
    assert "mislabeled: Task 1" in proc.stdout, proc.stdout


def test_summary_line_carries_the_mislabel_count(tmp_path: Path) -> None:
    # A demotion FAILs with `wiring=0 unpinned=0`: every count on the summary line
    # reads clean, so a reader who stops at the token sees a FAIL with nothing wrong
    # and concludes the gate is broken rather than the plan. The count has to be on
    # the line that carries the verdict.
    plan = _plan(tmp_path, _task(1, shape="new-behaviour"))
    proc = subprocess.run(
        [sys.executable, str(GATE), str(plan)], capture_output=True, text=True
    )
    summary = next(l for l in proc.stdout.splitlines() if l.startswith("WIREPIN:"))
    assert "mislabeled=1" in summary, summary


def test_summary_line_reports_zero_mislabels_on_a_pass(tmp_path: Path) -> None:
    # The counter-direction: the field must be a real count, not a constant that
    # happens to read right on the failing case.
    plan = _plan(tmp_path, _task(1, "wire_ok"))
    proc = subprocess.run(
        [sys.executable, str(GATE), str(plan)], capture_output=True, text=True
    )
    summary = next(l for l in proc.stdout.splitlines() if l.startswith("WIREPIN:"))
    assert "WIREPIN: PASS" in summary and "mislabeled=0" in summary, summary


# --- tolerance: the field must survive how a generator writes it ----------


@pytest.mark.parametrize(
    "line",
    [
        "**Task shape**: `wiring`",
        "**Task shape**: wiring",
        "**Task Shape**: WIRING",
        "- **Task shape**: `wiring`",
        "**Task shape**: `wiring` (connects the finalizer to the shadow measurer)",
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


# --- tolerance: a parenthetical qualifies the shape, it is not part of it -----
#
# The template already allows a parenthetical on the LABEL (`**WIRE-PIN** (`wiring`
# shape only):`), so a generator writing one on the VALUE is the natural next step.
# Read literally it makes `wiring (connects X to Y)` a shape that is not `wiring`,
# which lands the task in `mislabeled` — the gate accusing a correctly-shaped,
# correctly-pinned wiring task of contradicting itself, and sending the operator to
# fix a label that was already right.


def _qualified(n: int, shape_line: str, wired: bool = True) -> str:
    """A task whose **Task shape** line is written verbatim, qualifier and all."""
    out = [f"## Task {n}: mod\n", f"**Task shape**: {shape_line}\n"]
    if wired:
        out.append("**WIRE**: `a.py:f` -> `b.g`\n**WIRE-PIN**: `test_f_calls_g`\n")
    return "".join(out) + "\n"


@pytest.mark.parametrize(
    "shape_line,why",
    [
        ("`wiring` (connects the finalizer to the measurer)", "plain parenthetical"),
        ("`wiring` (connects `finalize()` to `measure()`)", "nested parens — call syntax is the natural way to name a connection"),
        ("`wiring` (connects the engine to tools", "unbalanced paren, e.g. a qualifier wrapped onto the next line"),
        ("`wiring` (a) (b)", "two trailing parentheticals"),
        ("`wiring` — connects the finalizer to the measurer", "em-dash prose: the house style in shipped plans"),
        ("`wiring`, but see the note below", "comma-led aside"),
        ("`wiring` - connects a to b", "ascii hyphen, spaced"),
    ],
)
def test_a_qualified_wiring_shape_is_still_wiring(
    tmp_path: Path, shape_line: str, why: str
) -> None:
    result = check(_plan(tmp_path, _qualified(1, shape_line)))
    assert result["wiring"] == 1, f"qualifier read as part of the shape ({why}): {result}"
    assert result["verdict"] == "PASS", result
    assert result["mislabeled"] == [], "a pinned wiring task was called a mislabel"


def test_a_qualified_non_wiring_shape_still_catches_a_mislabel(tmp_path: Path) -> None:
    # The counter-direction: reading past the qualifier must not become a way to
    # launder a demotion past the mislabel check.
    result = check(_plan(tmp_path, _qualified(1, "`refactor` (no new call sites)")))
    assert result["verdict"] == "FAIL", result
    # Assert on the message the operator is routed by, not on an incidental
    # substring: the pre-fix message contained "refactor" too, so a looser
    # assertion here passes against the very bug this file pins.
    assert "declares `refactor` but carries" in result["mislabeled"][0], result


@pytest.mark.parametrize(
    "shape_line,why",
    [
        ("`connection`", "a plausible synonym that is not one of the three"),
        ("`wire`", "an abbreviation of the real thing"),
        ("`not-wiring` (wiring)", "a near-miss whose qualifier mentions the real shape"),
        ("`integration`", "an invented shape word"),
    ],
)
def test_an_unrecognised_shape_word_is_not_a_free_pass(
    tmp_path: Path, shape_line: str, why: str
) -> None:
    # Fail-closed. The shape field's only job is to decide whether the wiring
    # obligation applies, so a word the gate does not recognise must never be read
    # as "declared something, therefore not wiring" — that is a silent PASS on
    # exactly the task this gate exists to catch. Unrecognised reads as undeclared.
    body = _qualified(1, "`wiring`") + _qualified(2, shape_line, wired=False)
    result = check(_plan(tmp_path, body))
    assert result["verdict"] == "FAIL", f"unrecognised shape passed ({why}): {result}"
    assert "Task 2" in " ".join(result["unshaped"]), result


def test_an_unrecognised_shape_says_what_was_declared(tmp_path: Path) -> None:
    # "no shape declared" and "a shape I don't recognise" get the same verdict but
    # need different remedies — the operator must not be told to add a field that
    # is already there.
    body = _qualified(1, "`wiring`") + _qualified(2, "`connection`", wired=False)
    result = check(_plan(tmp_path, body))
    entry = next(e for e in result["unshaped"] if "Task 2" in e)
    assert "connection" in entry, f"the unrecognised value is not shown: {entry}"


@pytest.mark.parametrize(
    "shape_line",
    [
        "`new-behaviour` — pure helpers, fully testable unwired; no call site is created here",
        "`new-behaviour` (a generator plus a committed fixture)",
        "`refactor`, no behaviour change",
    ],
)
def test_a_qualified_non_wiring_shape_is_recognised_not_rejected(
    tmp_path: Path, shape_line: str
) -> None:
    # Lifted from shipped plans. Fail-closed must not become fail-on-everything:
    # these are correctly-shaped non-wiring tasks and must PASS without a pin.
    result = check(_plan(tmp_path, _qualified(1, shape_line, wired=False)))
    assert result["verdict"] == "PASS", f"a real shipped shape line was refused: {result}"
    assert result["unshaped"] == [], result


def test_a_qualifier_containing_a_pipe_does_not_read_as_an_unedited_template(
    tmp_path: Path,
) -> None:
    # Ordering, not decoration: the alternation check is how an unedited template
    # (`new-behaviour | refactor | wiring`) is recognised as declaring nothing. Run
    # it before the qualifier is stripped and any qualifier carrying a `|` drags a
    # real, pinned shape into UNSHAPED — a halt on correct work.
    result = check(_plan(tmp_path, _qualified(1, "`wiring` (engine | tools seam)")))
    assert result["verdict"] == "PASS", result
    assert result["wiring"] == 1, f"qualifier read as a template alternation: {result}"


def test_an_unedited_template_alternation_still_declares_nothing(tmp_path: Path) -> None:
    # The counter-direction for that ordering: stripping first must not defeat the
    # alternation check on the case it exists for.
    body = _qualified(1, "`new-behaviour` | `refactor` | `wiring`")
    assert check(_plan(tmp_path, body))["verdict"] == "UNSHAPED"


def test_a_shape_that_is_only_a_parenthetical_declares_nothing(tmp_path: Path) -> None:
    # Strip the qualifier and nothing is left: that is "declared nothing", not a
    # shape — and on a shape-aware plan it is the hiding place the gate exists for.
    body = _task(1) + _qualified(2, "(see above)", wired=False)
    result = check(_plan(tmp_path, body))
    assert result["verdict"] == "FAIL", result
    assert "Task 2" in " ".join(result["unshaped"]), result


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
        # Real ids swept from the shipped corpus. Tightening the id group to stop
        # counting prose headings must not start dropping these.
        ("## Task 0: mod", "zero is a real id — a pre-code gate task"),
        ("## Task 4.a: mod", "dotted-alpha id"),
        ("## Task 6.1.5: mod", "multi-level dotted id"),
        ("## Task 7b: mod", "digit-then-letter id"),
        ("## Task 13.6 — mod", "dotted id, em-dash form"),
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
        # These begin with the literal word "Task", so a parser that accepts any
        # word as the id counts them. Both are lifted from shipped plans, and both
        # sit in files with no real task headers at all — so each turns a true
        # `tasks=0` into `tasks=1` and routes the operator to the wrong remedy.
        "## Task decomposition",
        "## Task outline",
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


def test_an_unreadable_plan_emits_a_token_on_stdout(tmp_path: Path) -> None:
    # SKILL.md's contract is "read the `WIREPIN:` token, never `$?`". A caller that
    # obeys it sees stdout only — so an error that prints to stderr alone is
    # indistinguishable from the gate never having run. Both look like no token.
    # That silence is worst in exactly the case the tasks=0 story is about: being
    # pointed at the wrong file.
    proc = _run(str(tmp_path / "nope.md"))
    assert "WIREPIN: UNREADABLE" in proc.stdout, (
        f"an unreadable plan produced no token for a token-reading caller: {proc.stdout!r}"
    )
    assert proc.returncode == 2, "cannot-read is not a verdict"


def test_the_unreadable_token_carries_no_counts(tmp_path: Path) -> None:
    # The load-bearing half. `tasks=` now SELECTS the operator's remedy (SKILL.md
    # §5b: tasks=0 -> impl_plan_no_tasks). A plan that could not be read has no
    # counts to report, so printing `tasks=0` would fabricate the one field the
    # router keys on and hand a wrong-path error the no-tasks remedy — the exact
    # misrouting the tasks=0 split was written to stop.
    proc = _run(str(tmp_path / "nope.md"))
    assert "tasks=" not in proc.stdout, (
        f"UNREADABLE fabricated a count the remedy router keys on: {proc.stdout!r}"
    )


def test_the_unreadable_path_keeps_its_stderr_diagnostic(tmp_path: Path) -> None:
    # The token says the class of failure; only the exception says which file and
    # why. Emitting the token must not cost the operator the detail.
    proc = _run(str(tmp_path / "nope.md"))
    assert "ERROR:" in proc.stderr, proc.stderr
    assert "nope.md" in proc.stderr, proc.stderr


def test_unreadable_is_reached_by_more_than_a_missing_file(tmp_path: Path) -> None:
    # A directory handed to the gate raises IsADirectoryError, not FileNotFoundError.
    # The token is about "could not read this plan", not about one errno.
    target = tmp_path / "a-directory.impl-plan.md"
    target.mkdir()
    proc = _run(str(target))
    assert "WIREPIN: UNREADABLE" in proc.stdout, proc.stdout
    assert proc.returncode == 2


def test_unreadable_emits_the_hmad_marker_like_every_other_verdict(tmp_path: Path) -> None:
    # Log scrapers key on the `[H-MAD] <feature> wirepin <verdict>` line. Omitting it
    # on the error path makes an errored run invisible to the same scan that sees
    # every PASS and FAIL.
    proc = _run(str(tmp_path / "nope.md"))
    assert "[H-MAD] nope wirepin UNREADABLE" in proc.stdout, proc.stdout


def test_cli_unshaped_is_not_a_pass(tmp_path: Path) -> None:
    plan = _plan(tmp_path, _task(1, shape=None, wire=None, pin=None))
    proc = _run(str(plan))
    assert "WIREPIN: UNSHAPED" in proc.stdout, proc.stdout
    assert proc.returncode == 2, "cannot-judge must not exit 0 alongside real verdicts"


def test_a_plan_with_no_tasks_is_told_no_task_was_found(tmp_path: Path) -> None:
    # `tasks=0` reaches UNSHAPED through the same branch as "shaped plan, no shapes"
    # and inherits its remedy — "add the **Task shape** field" — which sends the
    # operator to add a field to a file the parser found no tasks in. Same halt,
    # wrong instruction: the verdict is right, the sentence after it is not.
    plan = _plan(tmp_path, "## Executive Summary\nA legacy plan, no task headers.\n")
    proc = _run(str(plan))
    assert "WIREPIN: UNSHAPED tasks=0" in proc.stdout, proc.stdout
    assert "no task was found" in proc.stdout, proc.stdout
    assert "declares a **Task shape**" not in proc.stdout, (
        f"tasks=0 was handed the shape-field remedy: {proc.stdout}"
    )


def test_a_shaped_plan_with_no_shapes_still_gets_the_shape_remedy(tmp_path: Path) -> None:
    # The counter-direction: the new message must be reached by `tasks=0` only, not
    # substituted for the one case where "add the field" is the right instruction.
    plan = _plan(tmp_path, _task(1, shape=None, wire=None, pin=None))
    proc = _run(str(plan))
    assert "WIREPIN: UNSHAPED tasks=1" in proc.stdout, proc.stdout
    assert "declares a **Task shape**" in proc.stdout, proc.stdout
    assert "no task was found" not in proc.stdout, proc.stdout


def test_gate_is_stdlib_only() -> None:
    # Consumer suites invoke h-mad scripts with a bare `python3` that has no venv.
    source = GATE.read_text(encoding="utf-8")
    for banned in ("import yaml", "import requests", "from pydantic", "import jsonschema"):
        assert banned not in source, f"{banned} would break the bare-python3 callers"
