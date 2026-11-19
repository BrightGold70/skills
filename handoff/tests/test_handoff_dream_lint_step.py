"""WRITE's memory-dream report step: pinned to the script it runs, not just to its wording.

`references/auto-memories.md` tells every closeout to run `memory-dream/scripts/dream_lint.py`
read-only, copy its `links` / `orphans` / `last_dream` lines into Open Items on exit 1, report
exit 2 as unreadable (never "clean"), suggest the `memory-dream` skill past 7 days, and never
`--apply`. That instruction is prose; a test that only checked the prose mentions dream_lint
would stay green while the command pointed at a moved script or the exit codes changed meaning
underneath it. So this pins four things, each against the other side of the contract:

1. the step is reachable (SKILL.md routes WRITE to auto-memories.md) and its command resolves
   to a real script in this repo;
2. the exit codes the step branches on are the ones the script actually returns, and the
   lines it says to copy are lines the script actually prints;
3. the step forbids `--apply` and the judgment pass, so a closeout never edits the shared store;
4. its staleness threshold equals memory-dream's own "due" threshold.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "handoff" / "SKILL.md"
AUTO = REPO / "handoff" / "references" / "auto-memories.md"
DREAM_SKILL = REPO / "memory-dream" / "SKILL.md"
COMMAND = re.compile(r'python3 "\$\{CLAUDE_SKILLS_ROOT:-\$HOME/\.claude/skills\}/(?P<rel>[^"]+)" <memory-dir>')


def _step() -> str:
    text = AUTO.read_text(encoding="utf-8")
    m = re.search(r"\*\*Then run the mechanical dream report\*\*.*?(?=\n\*\*How to apply:\*\*)", text, re.S)
    assert m, "auto-memories.md has no 'mechanical dream report' step"
    return m.group(0)


def _script() -> Path:
    m = COMMAND.search(_step())
    assert m, "the step's dream_lint command is missing or reshaped"
    return REPO / m.group("rel")


def _store(tmp: Path, body: str) -> Path:
    (tmp / "MEMORY.md").write_text("- [A](a.md) — x\n", encoding="utf-8")
    (tmp / "a.md").write_text(f"---\nname: a\ndescription: d\nmetadata:\n  type: feedback\n---\n{body}",
                              encoding="utf-8")
    return tmp


def _run(store: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(_script()), str(store)], capture_output=True, text=True)


def test_write_routes_to_the_auto_memories_reference():
    assert "references/auto-memories.md" in SKILL.read_text(encoding="utf-8")


def test_the_command_resolves_to_the_real_script():
    script = _script()
    assert script == REPO / "memory-dream" / "scripts" / "dream_lint.py"
    assert script.is_file()


def test_exit_codes_and_printed_lines_match_what_the_step_branches_on(tmp_path):
    step = _step()
    assert "when it exits 1" in step and "Exit 2 means the store could not be read" in step
    (tmp_path / "clean").mkdir()
    clean = _run(_store(tmp_path / "clean", "self [[a]]\n"))
    assert clean.returncode == 0, clean.stdout + clean.stderr
    for name in ("links", "orphans", "last_dream"):          # the lines the step says to copy
        assert f"`{name}`" in step
        assert re.search(rf"^{name}[ =]", clean.stdout, re.M), (name, clean.stdout)
    (tmp_path / "finding").mkdir()
    store = _store(tmp_path / "finding", "see [[A]]\n")
    (store / "orphan.md").write_text("nobody links me\n", encoding="utf-8")
    assert _run(store).returncode == 1
    (tmp_path / "empty").mkdir()
    bad = _run(tmp_path / "empty")
    assert bad.returncode == 2 and "UNREADABLE" in bad.stderr


def test_write_never_applies_or_judges():
    step = _step()
    assert re.search(r"Do \*\*not\*\* run `--apply` or the judgment pass from WRITE", step)
    assert not re.search(r"--fix-links|--apply --backup-dir", step.replace("Do **not** run `--apply`", ""))


def test_staleness_threshold_matches_memory_dream():
    step_days = re.search(r"`last_dream` is `never` or over (\d+) days", _step())
    dream_days = re.search(r"A full dream is due when it reads over (\d+) days", DREAM_SKILL.read_text(encoding="utf-8"))
    assert step_days and dream_days
    assert step_days.group(1) == dream_days.group(1)
    assert "`memory-dream`" in _step() and "**Suggested-Skills:**" in _step()
