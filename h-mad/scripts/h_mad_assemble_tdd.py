#!/usr/bin/env python3
"""h_mad_assemble_tdd.py — stage a Phase-5d/5e Codex dispatch, or refuse.

The 5d/5e loop is mechanical and identical per task: cut §"Task N" out of the
impl-plan, fill the implementer template's `INLINE_*` slots, dispatch
`exec codex` backgrounded, read the `STATUS:` token, then re-run pytest
INDEPENDENTLY rather than trusting the verdict. Hand-assembling it 20+ times
across two sessions produced five distinct mistakes, and every one is an
invocation default rather than a judgement:

  1. Omitting `--model gpt-5.5`. The config default cannot execute tools at all,
     and — this is the trap — it fails as a well-formed `STATUS: BLOCKED`, not
     as an error. `exec` injects no model of its own (`hmad-dispatch.sh` only
     forwards `--model` when given), so the default has to live here.
  2. A bare `python3`, which on this machine is 3.14 and has no pytest. The
     independent re-run then errors instead of measuring.
  3. Passing the prompt inline when `exec` takes a FILE PATH — `no such prompt
     file: <the whole prompt>`, rc=2, nothing runs.
  4. `--sandbox read-only` on a run that executes pytest, which kills pytest's
     tempdir so the pass measures nothing.
  5. An unscoped `pytest`, which collects the sibling project and dies with
     pre-existing errors that have nothing to do with the task.

So this stages the prompt and prints the exact command block. It does NOT
dispatch: the dispatch/poll/wait loop is SKILL.md's §"Exit-code dispatch for
5d/5e", and a driver that dispatches either blocks blind for the timeout or
re-implements `progress`.

What it refuses to guess is the judgement the candidate row explicitly carves
out: which tests are regression guards, and how many are expected to fail. A
RED without stated counts is refused rather than defaulted, because "guard
changed" and "test weakened" are otherwise indistinguishable, and a default
would quietly pick one.

    ASSEMBLE-TDD: PASS <promptfile> <bytes>B phase=<red|green> task=<id> shape=<s>
    ASSEMBLE-TDD: HALT <reason>

exit 0 on PASS, 2 on any HALT. Stdlib-only.
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The task splitter is shared with the wire-pin gate on purpose. Re-deriving a
# parser is how `h_mad_do_preconditions.py` and the audit gate drifted into
# disagreeing verdicts on the same file (#39).
from h_mad_wire_pin_gate import _TASK_RE, _parse_tasks  # noqa: E402

TOKEN = "ASSEMBLE-TDD"
TEMPLATE = SKILL_DIR / "references" / "codex-implementer-prompt.md"
DEFAULT_MODEL = "gpt-5.5"

# Only a real slot is bracketed; prose refers to a slot by bare name. A raw
# `<INLINE_…>` reaching the agent reads as an unfilled template and is silently
# discounted (SKILL.md §"Audit prompt assembly").
RESIDUAL = re.compile(r"<INLINE_[A-Z_]+>|<REPORT_FILE_PATH>")


class Halt(Exception):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def task_body(text: str, task_id: str) -> str:
    """The impl-plan lines for `task_id`, bounded on the same header regex.

    Bounded on the shared `_TASK_RE` rather than on a blank line or a fixed
    heading level, so a task whose body contains its own sub-headings is not
    truncated at the first one.
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if _TASK_RE.match(ln)]
    wanted = task_id.strip().lower()
    for position, index in enumerate(starts):
        header = _TASK_RE.match(lines[index])
        assert header is not None  # `starts` was built from the same match
        num, mod = header.group("num"), header.group("mod")
        found = (mod.upper() if mod else f"Task {num.strip()}").lower()
        if found != wanted:
            continue
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        return "\n".join(lines[index:end]).rstrip()
    raise Halt("task_not_found", f"task={task_id}")


def interpreter_has_pytest(python: str) -> bool:
    try:
        return subprocess.run(
            [python, "-c", "import pytest"], capture_output=True
        ).returncode == 0
    except OSError:
        return False


def find_interpreters_with_pytest() -> list[str]:
    """Candidates to suggest when the chosen interpreter has no pytest."""
    return [
        candidate
        for candidate in (
            sys.executable, "python3.13", "python3.12", "python3.11",
            "/opt/homebrew/bin/python3", "/usr/bin/python3",
        )
        if candidate and interpreter_has_pytest(candidate)
    ]


def assemble(
    *,
    feature: str,
    task_id: str,
    phase: str,
    impl_plan: Path,
    project_root: Path,
    module: str,
    test_path: str,
    python: str,
    expect_fail: int | None,
    expect_pass: int | None,
    guards: list[str],
    report_file: str,
    template: Path,
) -> tuple[str, dict]:
    try:
        plan_text = impl_plan.read_text(encoding="utf-8")
    except OSError as exc:
        raise Halt("impl_plan_unreadable", f"{impl_plan}: {exc}") from None
    try:
        template_text = template.read_text(encoding="utf-8")
    except OSError as exc:
        raise Halt("template_unreadable", f"{template}: {exc}") from None

    tasks = {t["id"].lower(): t for t in _parse_tasks(plan_text)}
    meta = tasks.get(task_id.strip().lower())
    if meta is None:
        raise Halt("task_not_found", f"task={task_id}")
    body = task_body(plan_text, task_id)
    shape = meta["shape"] or "undeclared"

    # A wiring task ships a connection, and counts cannot gate it — the RED/GREEN
    # split returns identically whether or not the wire exists. Its pin is the
    # single load-bearing test, so its absence is the halt instead.
    if shape == "wiring":
        if not meta["pin"]:
            raise Halt("no_wire_pin", f"task={task_id}")
    elif phase == "red" and (expect_fail is None or expect_pass is None):
        raise Halt(
            "counts_required",
            "5d requires --expect-fail and --expect-pass; a default would decide "
            "whether an immediate pass is a guard or a weakened test",
        )

    if not interpreter_has_pytest(python):
        suggestions = find_interpreters_with_pytest()
        raise Halt(
            "interpreter_has_no_pytest",
            f"{python} cannot import pytest"
            + (f"; try {suggestions[0]}" if suggestions else ""),
        )

    # The phase is stamped because the template carries BOTH the RED and the
    # GREEN instructions and nothing in it says which one applies today.
    directive = {
        "red": "**THIS DISPATCH IS PHASE 5d (RED).** Write failing tests only. "
               "Do not modify production code.",
        "green": "**THIS DISPATCH IS PHASE 5e (GREEN).** Make the failing tests "
                 "pass with minimal production code. Do not weaken a test.",
    }[phase]

    lines = [directive, "", body, ""]
    if shape == "wiring":
        lines.append(f"**Task shape:** wiring — WIRE: {meta['wire']} · WIRE-PIN: {meta['pin']}")
        lines.append(
            "The WIRE-PIN is this task's single load-bearing test. Its RED must be "
            "an assertion about the CALLER's observable behaviour, never a missing "
            "symbol."
        )
    else:
        lines.append(
            f"**Expected after this dispatch:** {expect_fail} failing, {expect_pass} passing."
        )
        if guards:
            lines.append(
                "**Regression guards (must pass from the first run — do NOT manufacture "
                "a failure):** " + ", ".join(guards)
            )
        else:
            lines.append("**Regression guards:** none in this task.")
    lines.append("")
    lines.append(f"**Run the tests as:** `{python} -m pytest {test_path} -v`")
    lines.append(
        "That path is the scope. Do not widen it — an unscoped run collects the "
        "sibling project and dies on pre-existing errors."
    )

    filled = (
        template_text
        .replace("<INLINE_MODULE_NAME>", module)
        .replace("<INLINE_FEATURE_SLUG>", feature)
        .replace("<INLINE_FEATURE>", feature)
        .replace("<INLINE_TASK_FROM_IMPL_PLAN>", "\n".join(lines))
        .replace("<INLINE_REPO_ROOT>", str(project_root))
        .replace("<REPORT_FILE_PATH>", report_file)
    )

    residual = sorted(set(RESIDUAL.findall(filled)))
    if residual:
        raise Halt("residual_slots", ", ".join(residual))

    return filled, {"shape": shape, "task": meta["id"], "pin": meta["pin"]}


def command_block(
    *, feature: str, module: str, phase: str, prompt: Path, out: Path,
    log: Path, timeout: int, model: str, python: str, test_path: str,
    project_root: Path,
) -> str:
    key = "STATUS"
    step = "5d" if phase == "red" else "5e"
    q = shlex.quote
    return "\n".join([
        f"hmad-dispatch exec codex {q(str(prompt))} --model {model} \\",
        f"  --cd {q(str(project_root))} \\",
        f"  --out {q(str(out))} --log {q(str(log))} --timeout {timeout} &",
        "dispatch_pid=$!",
        f"hmad-dispatch progress {q(str(log))} --pid $dispatch_pid",
        "wait $dispatch_pid; rc=$?",
        f"python3 {q(str(SKILL_DIR / 'scripts' / 'h_mad_extract_verdict.py'))} \\",
        f"  {q(str(out))} --key {key} --feature {q(feature)} --phase {step}",
        "# The verdict says what the agent claims. Re-run the tests yourself:",
        f"{python} -m pytest {test_path} -v",
    ])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage a Phase-5d/5e Codex dispatch")
    ap.add_argument("--feature", required=True)
    ap.add_argument("--task", required=True, help='e.g. "Task 3" or "M2"')
    ap.add_argument("--phase", required=True, choices=("red", "green"))
    ap.add_argument("--project-root", required=True, type=Path)
    ap.add_argument("--module", required=True)
    ap.add_argument("--test-path", required=True,
                    help="scoped pytest path — an unscoped run measures the wrong tree")
    ap.add_argument("--impl-plan", type=Path,
                    help="default: <project-root>/docs/01-plan/features/<feature>.impl-plan.md")
    ap.add_argument("--python", default=sys.executable,
                    help="interpreter for the independent re-run; refused if it has no pytest")
    ap.add_argument("--expect-fail", type=int)
    ap.add_argument("--expect-pass", type=int)
    ap.add_argument("--guard", action="append", default=[],
                    help="a regression guard that must pass from the first run; repeatable")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--log", type=Path)
    ap.add_argument("--prompt", type=Path)
    ap.add_argument("--report-file", default="")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--sandbox", help="passed through; read-only is refused for a phase that runs pytest")
    ap.add_argument("--template", type=Path, default=TEMPLATE)
    args = ap.parse_args(argv)

    slug = f"{args.feature}_{args.module}_{args.phase}"
    impl_plan = args.impl_plan or (
        args.project_root / "docs" / "01-plan" / "features" / f"{args.feature}.impl-plan.md"
    )
    prompt = args.prompt or Path(f"/tmp/h_mad_{slug}.txt")
    out = args.out or Path(f"/tmp/exec_{slug}.out")
    log = args.log or Path(f"/tmp/exec_{slug}.log")

    try:
        if args.sandbox == "read-only":
            raise Halt(
                "sandbox_read_only",
                "this dispatch runs pytest, and a read-only sandbox kills pytest's "
                "tempdir — the run then passes without measuring anything",
            )
        filled, meta = assemble(
            feature=args.feature, task_id=args.task, phase=args.phase,
            impl_plan=impl_plan, project_root=args.project_root, module=args.module,
            test_path=args.test_path, python=args.python,
            expect_fail=args.expect_fail, expect_pass=args.expect_pass,
            guards=args.guard, report_file=args.report_file, template=args.template,
        )
    except Halt as exc:
        print(f"{TOKEN}: HALT {exc.reason}")
        if exc.detail:
            print(f"  {exc.detail}")
        return 2

    try:
        prompt.write_text(filled, encoding="utf-8")
    except OSError as exc:
        print(f"{TOKEN}: HALT prompt_unwritable")
        print(f"  {prompt}: {exc}")
        return 2

    size = len(filled.encode("utf-8"))
    print(
        f"{TOKEN}: PASS {prompt} {size}B phase={args.phase} "
        f"task={meta['task']} shape={meta['shape']}"
    )
    print(command_block(
        feature=args.feature, module=args.module, phase=args.phase, prompt=prompt,
        out=out, log=log, timeout=args.timeout, model=args.model,
        python=args.python, test_path=args.test_path, project_root=args.project_root,
    ))
    print(f"[H-MAD] {args.feature} tdd-assemble {args.phase} {meta['task']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
