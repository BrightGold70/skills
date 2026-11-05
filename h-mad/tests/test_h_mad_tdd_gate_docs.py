"""Documentation pins for the Phase 5 TDD gate's shipped contract."""

import subprocess
from pathlib import Path

import pytest

from docsections import titled_section
from tdd_gate_support import hook_form
from skill_corpus import doc_text  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
CODEX_RUNTIME = ROOT / "references" / "codex-runtime.md"
SKILL = ROOT / "SKILL.md"
AGY_RUNTIME = ROOT / "references" / "agy-runtime.md"
IMPLEMENTER_PROMPT = ROOT / "references" / "codex-implementer-prompt.md"
DERIVE_SCRIPT = ROOT / "scripts" / "h_mad_derive_test_path.sh"
HOOK = ROOT / "hooks" / "h-mad-tdd-gate.sh"


def _hook_block(text: str) -> str:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("Hook: ")]
    assert len(starts) == 1, f"expected one 'Hook: ' line, found {len(starts)}"  # M:D1
    start = starts[0]
    end = start + 1
    while end < len(lines) and lines[end].startswith("- "):
        end += 1
    return "\n".join(lines[start:end])


def _skill_gate_bullet(text: str) -> str:
    anchor = "- **It does not license Claude to write Phase 5 production code"
    assert text.count(anchor) == 1, "expected one Claude Phase 5 gate bullet"
    return text.split(anchor, 1)[1].split("\n\n", 1)[0]


def test_trust_boundary_states_the_venv_rule():
    section = titled_section(CODEX_RUNTIME.read_text(encoding="utf-8"), "Trust boundary")
    for token in ("nearest", ".venv", ".venv/bin", "realpath", "pyvenv.cfg",
                  "regular", "venv-escapes-root", "summary line"):
        assert token in section, f"Trust boundary must state {token!r}"


def test_helper_scripts_registers_the_judge():
    section = titled_section(
        doc_text(SKILL),
        "Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)",
    )
    for token in ("h_mad_tdd_judge.py", "state", "judge", "TDD-STATE:",
                  "TDD-JUDGE:", "judge-error", "copied", "symlinked", "TDD-LISTING:",
                  "listing"):
        assert token in section, f"Helper scripts must describe {token!r}"


def test_tdd_gate_section_names_the_chosen_form():
    section = titled_section(AGY_RUNTIME.read_text(encoding="utf-8"), "The TDD gate")
    form = hook_form(HOOK)
    assert form in ("a", "b"), f"hook must declare one refusal form, got {form!r}"
    if form == "a":
        assert "rc 2" in section and "stderr" in section, "form a must document rc 2 on stderr"
    else:
        assert "permissionDecision" in section and "rc 0" in section, (
            "form b must document permissionDecision JSON deny on rc 0"
        )
        assert "exit-code protocol" not in section, "form b must remove the old exit-code wording"


def test_hook_line_names_both_gates():
    hook_line = _hook_block(IMPLEMENTER_PROMPT.read_text(encoding="utf-8")).splitlines()[0]
    for token in ("h-mad-codex-tdd-gate.py", "apply_patch", "shell",
                  "h-mad-tdd-gate.sh", "Write", "Edit"):
        assert token in hook_line, f"Hook line must name {token!r}"
    assert "<" not in hook_line and ">" not in hook_line, "Hook line must have no slot"


def test_hook_bullets_state_the_shipped_rule():
    bullets = "\n".join(_hook_block(IMPLEMENTER_PROMPT.read_text(encoding="utf-8")).splitlines()[1:])
    for token in ("impl-plan", "name map", "summary", "N failed", "test_*.py",
                  "*_test.py", "conftest*.py", ".md", ".yaml", ".yml", ".json",
                  ".toml", ".txt", ".rst", ".cfg", ".ini", "Production file", ".sh"):
        assert token in bullets, f"Hook bullets must state {token!r}"
    assert "<" not in bullets and ">" not in bullets, "Hook bullets must have no slot"


def test_skill_gate_bullet_states_the_every_record_rule():
    bullet = _skill_gate_bullet(doc_text(SKILL))
    for token in ("ACTIVE", "every", "unavailable", "exhausted"):
        assert token in bullet, f"Phase 5 gate bullet must state {token!r} for every record"


def test_derive_script_header_names_the_judge():
    header = "\n".join(DERIVE_SCRIPT.read_text(encoding="utf-8").splitlines()[:5])
    assert "Used by h_mad_tdd_judge.py" in header, "derive script header must name the judge"


@pytest.mark.parametrize("locator", ("trust-boundary", "helper-scripts", "tdd-gate", "hook-line"))
def test_locators_fail_loudly(locator):
    if locator == "trust-boundary":
        text = CODEX_RUNTIME.read_text(encoding="utf-8")
        doctored = text.replace("### Trust boundary", "### Renamed boundary", 1)
        assert doctored != text
        with pytest.raises(AssertionError):
            titled_section(doctored, "Trust boundary")
    elif locator == "helper-scripts":
        text = doc_text(SKILL)
        doctored = text.replace("## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)",
                                "## Renamed helper scripts", 1)
        assert doctored != text
        with pytest.raises(AssertionError):
            titled_section(doctored, "Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)")
    elif locator == "tdd-gate":
        text = AGY_RUNTIME.read_text(encoding="utf-8")
        doctored = text.replace("## The TDD gate", "## Renamed TDD gate", 1)
        assert doctored != text
        with pytest.raises(AssertionError):
            titled_section(doctored, "The TDD gate")
    else:
        text = IMPLEMENTER_PROMPT.read_text(encoding="utf-8")
        doctored = text.replace("Hook: ", "Renamed hook: ", 1)
        assert doctored != text
        with pytest.raises(AssertionError):
            _hook_block(doctored)


def test_skill_states_the_docs_first_component_rule():
    text = doc_text(SKILL)
    anchor = "The gates judge production `.py`, and a code-like file such as a `.sh` script or an extensionless launcher when a Task's **Production file** line lists it; test files, docs, doc/data files (`.md` `.yaml` `.yml` `.json` `.toml` `.txt` `.rst` `.cfg` `.ini`, listed or not) and unlisted code-like files are allowed."
    assert text.count(anchor) == 1, "expected one gate-scope line in SKILL.md"
    paragraph = text.split(anchor, 1)[1].split("\n\n", 1)[0]
    for token in ("FIRST component", "relative to the project root", "`docs`",
                  "`src/docs/foo.py`", "All three gates"):
        assert token in paragraph, f"gate-scope line must state {token!r}"


@pytest.mark.parametrize("branch", (
    pytest.param("production-Python", id="production-python"),
    pytest.param(r"a .\.py. suffix in any case", id="suffix-in-any-case"),
    pytest.param("never gated", id="never-gated"),
    pytest.param("only production", id="only-production"),
    pytest.param(r"production-.\.py.", id="production-dot-py"),
    pytest.param("markdown / yaml", id="markdown-yaml"),
    pytest.param("Both gates", id="both-gates"),
    pytest.param("neither gate", id="neither-gate"),
))
def test_gate_prose_has_no_retired_phrasing(branch):
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "grep", "-n", "-E", branch, "--",
         "h-mad/SKILL.md", "h-mad/references", "h-mad/agents", "h-mad/invariants.base.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, (
        f"gate prose must have no retired phrasing {branch!r}; "
        f"git grep returned {result.returncode}\n{result.stdout}{result.stderr}"
    )
    assert result.stdout == "", f"gate prose must have no retired phrasing {branch!r}"
