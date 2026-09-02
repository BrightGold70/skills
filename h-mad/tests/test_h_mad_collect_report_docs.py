"""RED docs pins for the collect-report/codex-leg documentation.

These tests intentionally pin the operator-facing docs only. Phase 5d must not
modify the production docs; GREEN adds the section and registry entries these
assertions describe.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
SKILL_MD = SKILL_DIR / "SKILL.md"
ORCHESTRATION_MODE = SKILL_DIR / "references" / "orchestration-mode.md"
SCRIPT_DIR = SKILL_DIR / "scripts"

sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_audit_gate import is_transport_path  # noqa: E402


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
