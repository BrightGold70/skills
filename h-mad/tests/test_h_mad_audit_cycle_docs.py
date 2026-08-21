"""RED docs pins for the audit-cycle verb.

The verb already exists in the dispatch/helper layer. These tests pin the
operator-facing contract in SKILL.md so the next documentation edit cannot omit
the token, the single-cycle boundary, the legacy hand-run path, or the measured
report transport caveat.
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
SKILL_MD = SKILL_DIR / "SKILL.md"
AUDIT_CYCLE = SKILL_DIR / "scripts" / "h_mad_audit_cycle.py"


EXPECTED_FRONTMATTER = (
    "name: h-mad\n"
    "description: Orchestrate the 7-phase H-MAD (Hawk Multi-Agents Development) workflow "
    "end-to-end. Standalone \u2014 no external skill dependencies (spec-kit, b-mad, or pdca). "
    "All phase protocols are built-in. Project-agnostic; splices project-specific Axis B "
    "invariants from `<PROJECT_ROOT>/.h-mad/invariants.md` into audit prompts at dispatch "
    "time. Use when user invokes /h-mad \"<feature>\", /h-mad do \"<feature>\", /h-mad "
    "status, or /h-mad reset \"<feature>\"."
)


def _skill_doc() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    """Return the section from heading ``start`` up to heading ``end``."""
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _audit_prompt_assembly() -> str:
    return _section(
        _skill_doc(),
        "## Audit prompt assembly",
        "## Putting `hmad-dispatch` on PATH",
    )


def _report_transport_step() -> str:
    section = _audit_prompt_assembly()
    start = section.index("6.6.")
    end = section.index("\n7.", start)
    return section[start:end]


def _helper_registry() -> str:
    return _section(
        _skill_doc(),
        "## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)",
        "## Working a `skill-monitoring` item",
    )


def _frontmatter() -> str:
    text = _skill_doc()
    assert text.startswith("---\n"), "SKILL.md frontmatter must start the file"
    end = text.find("\n---\n", 4)
    assert end != -1, "SKILL.md frontmatter must have a closing delimiter"
    return text[4:end]


def _squash(text: str) -> str:
    return " ".join(text.split())


def test_docs_token_pinned():
    """AUDITCYCLE: appears in h_mad_audit_cycle.py <=> it appears in SKILL.md."""
    script_has_token = "AUDITCYCLE:" in AUDIT_CYCLE.read_text(encoding="utf-8")
    docs_has_token = "AUDITCYCLE:" in _skill_doc()

    assert (
        not script_has_token or docs_has_token
    ), "AUDITCYCLE token present in h_mad_audit_cycle.py but missing from SKILL.md"
    assert (
        not docs_has_token or script_has_token
    ), "AUDITCYCLE token present in SKILL.md but missing from h_mad_audit_cycle.py"
    assert (
        script_has_token and docs_has_token
    ), "AUDITCYCLE token must remain present on both sides of the docs/helper pin"


def test_audit_prompt_assembly_leads_with_audit_cycle_and_keeps_hand_run_steps():
    section = _audit_prompt_assembly()
    command_index = section.find("hmad-dispatch audit-cycle")
    hand_run_index = section.find("The steps below")

    assert (
        command_index != -1
    ), "Audit prompt assembly must present `hmad-dispatch audit-cycle` as the cycle entrypoint"
    assert hand_run_index != -1, "Audit prompt assembly must retain the hand-run debugging path"
    assert (
        command_index < hand_run_index
    ), "`hmad-dispatch audit-cycle` must lead the hand-run debugging steps"

    for hand_run_detail in (
        "<INLINE_TARGET_DOC>",
        "<AUDIT_SENTINEL>",
        "hmad-dispatch send agy",
        "h_mad_extract_report.py",
        "h_mad_audit_gate.py",
    ):
        assert (
            hand_run_detail in section[hand_run_index:]
        ), f"hand-run audit prompt assembly steps dropped `{hand_run_detail}`"


def test_helper_registry_lists_audit_cycle_verdict_token():
    registry = _helper_registry()
    audit_cycle_line = next(
        (
            line
            for line in registry.splitlines()
            if "h_mad_audit_cycle.py" in line
        ),
        "",
    )

    assert (
        audit_cycle_line
    ), "helper registry must list `h_mad_audit_cycle.py` alongside verdict helpers"
    assert (
        "AUDITCYCLE:" in audit_cycle_line
    ), "h_mad_audit_cycle.py registry entry must carry the `AUDITCYCLE:` token"
    for neighbouring_token in ("GATE:", "WIREPIN:", "CTXBUDGET:"):
        assert (
            neighbouring_token in registry
        ), f"helper registry lost neighbouring verdict token `{neighbouring_token}`"


def test_audit_cycle_intro_states_one_cycle_and_orchestrator_owned_revision_loop():
    section = _audit_prompt_assembly()
    command_index = section.find("hmad-dispatch audit-cycle")
    assert (
        command_index != -1
    ), "audit-cycle introduction must be adjacent to `hmad-dispatch audit-cycle`"

    intro = _squash(section[command_index : command_index + 900].lower())
    assert (
        "one cycle" in intro or "single cycle" in intro or "exactly one" in intro
    ), "`audit-cycle` introduction must say the verb runs exactly one cycle"
    assert (
        "revision loop" in intro and "orchestrator" in intro
    ), "`audit-cycle` introduction must say the revision loop remains the orchestrator's"


def test_report_file_transport_records_delivery_measurement_and_out_fallback():
    step = _squash(_report_transport_step().lower())

    assert (
        "measure" in step or "measured" in step
    ), "SKILL.md step 6.6 must record the measured report-file delivery result"
    assert (
        "report file" in step or "report-file" in step
    ), "SKILL.md step 6.6 must name report-file delivery in the measurement"
    assert (
        "cycle 7" in step and "pass 1" in step
    ), "SKILL.md step 6.6 must identify the report-file miss that required fallback"
    assert (
        "--out" in step and "always" in step and "fallback" in step
    ), "SKILL.md step 6.6 must state the `--out` fallback is always armed"


def test_skill_frontmatter_identity_survives_audit_cycle_docs_update():
    # Regression guard: this must pass in RED and GREEN unless docs edits corrupt the manifest.
    frontmatter = _frontmatter()
    assert frontmatter == EXPECTED_FRONTMATTER

    fields = dict(
        line.split(":", 1) for line in frontmatter.splitlines() if ":" in line
    )
    assert fields.get("name", "").strip() == "h-mad"
    assert fields.get("description", "").strip()
