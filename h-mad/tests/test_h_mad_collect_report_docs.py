"""RED docs pins for the collect-report/codex-leg documentation.

These tests intentionally pin the operator-facing docs only. Phase 5d must not
modify the production docs; GREEN adds the section and registry entries these
assertions describe.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
SKILL_MD = SKILL_DIR / "SKILL.md"
ORCHESTRATION_MODE = SKILL_DIR / "references" / "orchestration-mode.md"
SCRIPT_DIR = SKILL_DIR / "scripts"

sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_audit_gate import is_transport_path  # noqa: E402
import h_mad_doc_block_exec as dbe  # noqa: E402


SECOND_SURFACE_HEADING = "## Second surface — the codex leg"
HELPER_HEADING = "## Helper scripts"
PATH_HEADING = "## Putting `hmad-dispatch` on PATH"


def _skill_doc() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _orchestration_doc() -> str:
    return ORCHESTRATION_MODE.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    """Return the section from heading ``start`` up to heading ``end``."""
    start_index = text.find(start)
    assert start_index != -1, f"document must contain section start `{start}`"
    end_index = text.find(end, start_index + len(start))
    assert end_index != -1, f"document must contain section end `{end}` after `{start}`"
    return text[start_index:end_index]


def _second_surface() -> str:
    return _section(_skill_doc(), SECOND_SURFACE_HEADING, HELPER_HEADING)


def _audit_prompt_assembly() -> str:
    return _section(_skill_doc(), "## Audit prompt assembly", PATH_HEADING)


def _report_capture_step() -> str:
    section = _audit_prompt_assembly()
    start = section.find("9. Capture the report.")
    assert start != -1, "Audit prompt assembly must contain step 9 report capture"
    end = section.find("\n10.", start)
    assert end != -1, "Audit prompt assembly step 9 must end before step 10"
    return section[start:end]


def _helper_registry() -> str:
    return _section(_skill_doc(), HELPER_HEADING, "## Working a `skill-monitoring` item")


def _helper_entry(script_name: str) -> str:
    registry = _helper_registry()
    match = re.search(rf"^- `{re.escape(script_name)}`.*?(?=\n- `|\Z)", registry, re.M | re.S)
    assert match, f"helper registry must list `{script_name}`"
    return match.group(0)


def _instantiate_rp_literal(literal: str) -> Path:
    path_text = (
        literal.removeprefix("RP=")
        .replace("<feature>", "f")
        .replace("<phase>", "plan")
        .replace("<N>", "3")
    )
    return Path(path_text)


def test_existing_6_6_report_file_literal_is_a_transport_path() -> None:
    step = _section(_audit_prompt_assembly(), "6.6.", "\n7.")
    match = re.search(r"RP=/tmp/audit_<feature>_<phase>_cycle<N>\.report\.md", step)

    assert match, "SKILL.md step 6.6 must keep the existing report-file RP literal"
    assert is_transport_path(_instantiate_rp_literal(match.group(0))), (
        "step 6.6 RP literal must satisfy the audit transport filename grammar"
    )


def test_skill_mentions_collect_report_at_least_twice() -> None:
    count = _skill_doc().count("collect-report")

    assert count >= 2, (
        "SKILL.md must mention `collect-report` at least twice for the codex-leg docs"
    )


def test_second_surface_section_is_between_path_setup_and_helper_registry_with_ordered_flow() -> None:
    doc = _skill_doc()
    path_index = doc.find(PATH_HEADING)
    section_index = doc.find(SECOND_SURFACE_HEADING)
    helper_index = doc.find(HELPER_HEADING)

    assert path_index != -1, "SKILL.md must keep the hmad-dispatch PATH section"
    assert section_index != -1, "SKILL.md must add `Second surface — the codex leg`"
    assert helper_index != -1, "SKILL.md must keep the helper scripts registry"
    assert path_index < section_index < helper_index, (
        "`Second surface — the codex leg` must sit after PATH setup and before helper scripts"
    )

    section = _second_surface()
    ordered_terms = [
        "exec codex",
        "collect-report",
        "report_not_collected",
        "h_mad_audit_gate.py",
    ]
    positions = [section.find(term) for term in ordered_terms]
    assert all(position != -1 for position in positions), (
        "Second surface must document exec codex, collect-report, "
        "report_not_collected, and h_mad_audit_gate.py"
    )
    assert positions == sorted(positions), (
        "Second surface flow must order `exec codex` before `collect-report` "
        "before `report_not_collected` before `h_mad_audit_gate.py`"
    )
    assert "collect-report --surface codex" in section, (
        "Second surface must invoke `collect-report --surface codex`"
    )
    assert (
        "[H-MAD] <feature> <phase> halted reason=report_not_collected" in section
    ), "Second surface must name the report_not_collected halt marker"

    gate_line = next(
        (line for line in section.splitlines() if "h_mad_audit_gate.py" in line),
        "",
    )
    assert gate_line, "Second surface must include an h_mad_audit_gate.py gate line"
    assert "$RP" not in gate_line, (
        "Second surface gate line must gate the printed docs path, never `$RP`"
    )


def test_second_surface_codex_report_file_literal_is_a_transport_path() -> None:
    doc = _skill_doc()
    section = (
        _second_surface()
        if SECOND_SURFACE_HEADING in doc and HELPER_HEADING in doc
        else ""
    )
    match = re.search(r"RP=/tmp/audit_<feature>_<phase>_cycle<N>_codex\.report\.md", section)

    assert match, (
        "Second surface must define the `_codex` report-file RP literal for exec codex"
    )
    assert is_transport_path(_instantiate_rp_literal(match.group(0))), (
        "Second surface `_codex` RP literal must satisfy the transport filename grammar"
    )


def test_helper_registry_describes_collect_report_contract() -> None:
    entry = _helper_entry("h_mad_collect_report.py")

    for required in ("COLLECT: OK|MISSING|CONFLICT", "exit 0", "2", "--force", "readback"):
        assert required in entry, (
            f"h_mad_collect_report.py registry entry must document `{required}`"
        )


def test_orchestration_mode_lists_collect_report_next_to_report_wait() -> None:
    lines = _orchestration_doc().splitlines()
    report_wait_indices = [
        index for index, line in enumerate(lines) if "`report-wait " in line or "| `report-wait" in line
    ]
    collect_indices = [
        index for index, line in enumerate(lines) if "`collect-report " in line or "| `collect-report" in line
    ]

    assert report_wait_indices, "orchestration verb table must keep a `report-wait` row"
    assert collect_indices, "orchestration verb table must add a `collect-report` row"
    assert min(
        abs(report_wait - collect)
        for report_wait in report_wait_indices
        for collect in collect_indices
    ) <= 2, "`collect-report` row must be adjacent to the `report-wait` row"


def test_step_9_warns_to_gate_docs_path_never_transport_path() -> None:
    step = _report_capture_step()
    sentence = (
        "The gate refuses a path named like a transport file (`audit_*.report.md`) "
        "— gate the docs path, never `$RP`."
    )

    assert sentence in step, (
        "Audit prompt assembly step 9 must warn to gate the docs path, never `$RP`"
    )


def test_audit_cycle_paragraph_points_to_second_surface() -> None:
    section = _audit_prompt_assembly()
    start = section.find("`audit-cycle` runs exactly one cycle")
    assert start != -1, "Audit prompt assembly must keep the audit-cycle paragraph"
    end = section.find("\n\n", start)
    paragraph = section[start:] if end == -1 else section[start:end]

    assert "Second surface" in paragraph, (
        "audit-cycle paragraph must point readers to the Second surface codex leg"
    )


def test_second_surface_gate_path_is_not_phase_hardcoded() -> None:
    """The section advertises `--phase plan|design|impl-plan`, so no example may
    hardcode one phase's audit directory: `collect-report` writes a design audit
    to `docs/02-design/features/`, and an operator following a `01-plan` literal
    for a design cycle would gate a path that does not exist.
    """
    section = _second_surface()

    assert "--phase plan|design|impl-plan" in section or "plan|design|impl-plan" in section, (
        "Second surface must keep advertising every phase it supports"
    )

    offenders = [
        line
        for line in section.splitlines()
        if "<phase>" in line
        and ("docs/01-plan/features" in line or "docs/02-design/features" in line)
    ]
    assert not offenders, (
        "Second surface must not pair a `<phase>` placeholder with a hardcoded "
        "phase directory — collect-report chooses the directory from --phase. "
        f"Offending lines: {offenders}"
    )


def test_second_surface_gates_the_path_printed_by_collect_report() -> None:
    """`COLLECT: OK` prints `path=<the collected docs path>`; the recipe must
    take the gate target from that line rather than reconstructing it.
    """
    section = _second_surface()

    assert "path=" in section, (
        "Second surface must show that `COLLECT: OK` prints the collected path"
    )

    gate_line = next(
        (line for line in section.splitlines() if "h_mad_audit_gate.py" in line),
        "",
    )
    assert gate_line, "Second surface must include an h_mad_audit_gate.py gate line"

    gated = gate_line.split("h_mad_audit_gate.py", 1)[1].strip()
    assert gated.startswith('"$') or gated.startswith("$"), (
        "the gate must run on a shell variable holding the path collect-report "
        f"printed, not on a reconstructed literal; got: {gate_line!r}"
    )


def _gate_block() -> dbe.Block:
    section = _second_surface()
    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
    _gating = [b for b in blocks if "h_mad_audit_gate.py" in b]
    assert _gating, "Second surface must contain a bash block that runs the gate"
    assert len(_gating) == 1, f"expected exactly one gating bash block, got {len(_gating)}"
    return dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")


def _gate_bash_block() -> str:
    return _gate_block().text


def _run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult:
    import subprocess

    collector = SCRIPT_DIR / "h_mad_collect_report.py"
    gate = SCRIPT_DIR / "h_mad_audit_gate.py"
    block = _gate_block()
    # the doc addresses the installed skill; point the snippet at this tree
    subbed = dbe.Block(
        text=block.text.replace(
            "~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py", shlex.quote(str(gate))
        ),
        shell=block.shell,
        lineno=block.lineno,
        info=block.info,
    )
    # quote every interpolated path: the harness must not be the thing that
    # breaks on whitespace, or it measures itself instead of the recipe
    q = shlex.quote
    preamble = (
        f'COLLECT_OUT=$({q(sys.executable)} {q(str(collector))} --surface codex '
        f'--feature f --phase {phase} --cycle {cycle} '
        f'--report {q(str(report))} --project-root {q(str(root))})\n'
    )
    p = subprocess.run(["bash", "-c", preamble + subbed.text], capture_output=True, text=True, timeout=60.0)
    return dbe.RunResult(rc=p.returncode, stdout=p.stdout, stderr=p.stderr, shell=subbed.shell)


def test_gate_block_resolves_through_doc_block_exec(monkeypatch) -> None:
    """The gate consumer must delegate both extraction and cardinality policy."""
    real_extract = dbe.extract
    real_select = dbe.select
    extract_calls = []
    select_calls = []

    def spy_extract(*args, **kwargs):
        result = real_extract(*args, **kwargs)
        extract_calls.append((args, kwargs, result))
        return result

    def spy_select(*args, **kwargs):
        result = real_select(*args, **kwargs)
        select_calls.append((args, kwargs, result))
        return result

    monkeypatch.setattr(dbe, "extract", spy_extract)
    monkeypatch.setattr(dbe, "select", spy_select)

    block = _gate_block()

    assert len(extract_calls) == 1, "_gate_block must call dbe.extract exactly once"
    args, kwargs, extracted = extract_calls[0]
    assert args == (SKILL_MD, SECOND_SURFACE_HEADING) and kwargs == {}
    assert len(select_calls) == 1, "_gate_block must call dbe.select exactly once"
    args, kwargs, selected = select_calls[0]
    assert args[0] is extracted and kwargs.get("index") is None, (
        "dbe.select must receive dbe.extract's list with its no-index policy"
    )
    assert selected is block, "_gate_block must return the block dbe.select selected"


def test_recipe_runs_through_run_block(monkeypatch, tmp_path: Path) -> None:
    """The documented recipe must delegate substitution and execution together."""
    real_substitute = dbe.substitute
    substitute_calls = []
    run_calls = []

    def spy_substitute(*args, **kwargs):
        result = real_substitute(*args, **kwargs)
        substitute_calls.append((args, kwargs, result))
        return result

    def spy_run(block, **kwargs):
        run_calls.append((block, kwargs))
        return dbe.RunResult(rc=0, stdout="", stderr="", shell="strict")

    monkeypatch.setattr(dbe, "substitute", spy_substitute)
    monkeypatch.setattr(dbe, "run_block", spy_run)

    result = _run_recipe(phase="plan", cycle=3, report=tmp_path / "r.md", root=tmp_path)

    assert len(substitute_calls) == 1, "_run_recipe must call dbe.substitute exactly once"
    args, kwargs, subbed = substitute_calls[0]
    assert args[0].text == _gate_bash_block() and kwargs == {}
    assert args[1] == {
        "~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(
            str(SCRIPT_DIR / "h_mad_audit_gate.py")
        )
    }
    assert len(run_calls) == 1, "_run_recipe must call dbe.run_block exactly once"
    block, kwargs = run_calls[0]
    assert block is subbed[0], "dbe.run_block must receive dbe.substitute's returned Block"
    assert "COLLECT_OUT=$(" in kwargs["preamble"] and kwargs["timeout"] == 60.0
    assert result == dbe.RunResult(rc=0, stdout="", stderr="", shell="strict")


def test_gate_block_refuses_an_untagged_recipe(monkeypatch) -> None:
    monkeypatch.setattr(dbe, "extract", lambda *_args, **_kwargs: [])

    try:
        _gate_block()
    except dbe.BlockNotFound:
        pass
    else:
        raise AssertionError("_gate_block must refuse an untagged recipe through dbe.BlockNotFound")


def test_exec_block_scan_performs_no_execution(monkeypatch) -> None:
    run_calls = []
    subprocess_calls = []
    real_subprocess_run = dbe.subprocess.run

    def spy_run(block, **kwargs):
        run_calls.append((block, kwargs))
        return None

    def spy_subprocess_run(*args, **kwargs):
        subprocess_calls.append((args, kwargs))
        return real_subprocess_run(*args, **kwargs)

    monkeypatch.setattr(dbe, "run_block", spy_run)
    monkeypatch.setattr(dbe.subprocess, "run", spy_subprocess_run)

    test_exec_codex_dispatch_carries_out_log_and_timeout()

    assert run_calls == [], "the exec-codex documentation scan must never execute its selected block"
    assert subprocess_calls == [], "the documentation scan must not invoke subprocess.run"


def test_consumer_calls_the_helper_module_qualified() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden = "from h_mad_doc_block_exec " + "import"
    assert forbidden not in source, (
        "the consumer must call the helper through the dbe module alias"
    )


def test_only_the_exec_scan_hand_rolls_extraction() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    needle = 're.findall(r"' + "```bash"
    assert source.count(needle) == 1, (
        "only test_exec_codex_dispatch_carries_out_log_and_timeout may hand-roll bash extraction"
    )


def test_gate_block_guards_on_the_collect_token_before_gating() -> None:
    """The prose says anything but `COLLECT: OK` is a halt. The runnable example
    must implement that, not merely sit beneath the sentence.
    """
    block = _gate_bash_block()

    gate_index = block.index("h_mad_audit_gate.py")
    before = block[:gate_index]

    assert "COLLECT: OK" in before, (
        "the gate block must test for the `COLLECT: OK` token before gating"
    )
    assert "report_not_collected" in before, (
        "the gate block must name the report_not_collected halt before gating"
    )


def test_documented_gate_recipe_halts_instead_of_gating_an_empty_path(
    tmp_path: Path,
) -> None:
    """Execute the documented snippet for real.

    `COLLECT: MISSING` also prints a `path=` field, so a naive parse yields an
    empty variable and the gate is then run on `""` — which fails with an
    operational error and no halt marker, exactly the delivery failure the
    section says to halt on.
    """
    # a root with a space: this machine's own codex home is under
    # "Application Support", so whitespace in a project root is ordinary.
    root = tmp_path / "pro j"
    (root / "docs/01-plan/features").mkdir(parents=True)
    (root / "dispatch").mkdir()

    # delivered: the gate must run on the collected path and pass
    report = root / "dispatch" / "audit_f_plan_cycle3_codex.report.md"
    report.write_text("## Must-fix\n\nNone\n\n## Should-fix\n\nNone\n", encoding="utf-8")
    report.with_suffix(report.suffix + ".done").write_text("", encoding="utf-8")

    ok = _run_recipe(phase="plan", cycle=3, report=report, root=root)
    assert "GATE: PASS" in ok.stdout, (
        f"delivered report must reach the gate; stdout={ok.stdout!r} stderr={ok.stderr!r}"
    )

    # undelivered: MISSING must halt, never gate an empty path
    missing = _run_recipe(phase="plan", cycle=9, report=root / "absent.report.md", root=root)
    combined = missing.stdout + missing.stderr

    assert "GATE:" not in combined, (
        "an undelivered report must not reach the gate at all; "
        f"stdout={missing.stdout!r} stderr={missing.stderr!r}"
    )
    assert "Is a directory" not in combined, (
        "the recipe must not gate an empty path and crash; "
        f"stdout={missing.stdout!r} stderr={missing.stderr!r}"
    )
    assert "report_not_collected" in combined, (
        "the recipe must emit the report_not_collected halt marker; "
        f"stdout={missing.stdout!r} stderr={missing.stderr!r}"
    )


def test_gate_block_does_not_exit_the_operators_shell() -> None:
    """The section is a paste-along recipe. A bare `exit` in it terminates an
    interactive shell when the halt branch is taken, so the block must branch
    around the gate instead of exiting.
    """
    block = _gate_bash_block()

    offenders = [
        line
        for line in block.splitlines()
        if re.match(r"\s*exit\b", line)
    ]
    assert not offenders, (
        "the gate block must not `exit` — it would kill an interactive shell; "
        f"offending lines: {offenders}"
    )


def test_second_surface_documents_the_out_fallback_rung() -> None:
    """6a-prime cycle 2: the `--out` fallback is the recipe's recovery path.

    The whole feature exists because report-file delivery sometimes fails —
    measured 1 of 18 passes — and `collect-report` arms an `--out` rung for
    exactly that case. A recipe that never mentions it leaves an operator with
    no documented recovery when the marker never arrives.
    """
    section = _second_surface()

    collect_line = next(
        (line for line in section.splitlines() if "collect-report" in line and "--report" in line),
        "",
    )
    assert collect_line or "--out" in section, "section must invoke collect-report"
    assert "--out" in section, (
        "the Second surface recipe must document collect-report's `--out` "
        "fallback rung; without it the documented flow has no recovery when "
        "report-file delivery fails"
    )


def test_exec_codex_dispatch_carries_out_log_and_timeout() -> None:
    """6a-prime cycle 2: SKILL.md's own rule is 'pass --log on every exec dispatch'.

    A bare `exec codex` is the blind-dispatch failure this skill documents at
    length: no transcript to poll, no captured response, no watchdog bound.
    """
    section = _second_surface()

    exec_block = next(
        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
        "",
    )
    assert exec_block, "Second surface must dispatch the codex leg via exec"

    for flag in ("--out", "--log", "--timeout"):
        assert flag in exec_block, (
            f"the exec codex dispatch must carry `{flag}` — SKILL.md requires "
            "--log on every exec dispatch, and a verdict needs a captured --out"
        )


def test_codex_prompt_path_does_not_collide_with_the_agy_leg() -> None:
    """6a-prime cycle 2: the two legs must not share one staged prompt file.

    Step 7 stages the agy prompt at `/tmp/audit_<feature>_<phase>_cycle<N>.txt`,
    which is also `h_mad_assemble_audit.py`'s default `--out`. A codex leg that
    reads or writes that same path races the agy leg of the same cycle.
    """
    section = _second_surface()

    agy_path = "/tmp/audit_<feature>_<phase>_cycle<N>.txt"
    offenders = [line for line in section.splitlines() if agy_path in line]
    assert not offenders, (
        "the codex leg must use its own staged prompt path (the `_codex` form), "
        f"not the agy leg's; offending lines: {offenders}"
    )
