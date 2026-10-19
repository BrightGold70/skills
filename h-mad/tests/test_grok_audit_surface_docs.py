"""Pins for the Grok audit surface's exclusions and operator documentation."""

from pathlib import Path
import re
import subprocess

from docsections import titled_section


REPO = Path(__file__).resolve().parents[2]
EXCLUSIONS = REPO / "docs/03-analysis/probes/grok-audit-surface/exclusions.txt"
SKILL_MD = REPO / "h-mad/SKILL.md"


def test_exclusion_list_holds_the_required_entries() -> None:
    assert EXCLUSIONS.is_file(), (
        "the declared exclusion list must exist and hold exactly D5's six entries "
        f"in order: {EXCLUSIONS}"
    )
    entries = [
        line.strip()
        for line in EXCLUSIONS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert entries == [
        "dir docs/archive/2026-09/audit-report-docs-copy",
        "dir docs/archive/2026-09/tdd-gate-fail-opens",
        "dir docs/archive/2026-10/agy-coder-fallback",
        "dir docs/03-analysis/probes/grok-audit-surface",
        "dir docs/03-analysis/agy-coder-fallback.authoring",
        "name-contains grok-audit-surface",
    ], "the declared exclusion list must hold exactly D5's six entries in order"


def test_teammate_section_names_hmad_dispatch_audit_cycle() -> None:
    section = " ".join(
        titled_section(
            SKILL_MD.read_text(encoding="utf-8"),
            "Teammate audit leg — when codex is unavailable",
        ).split()
    )
    command = (
        "`hmad-dispatch audit-cycle --feature <feature> --phase <phase> "
        "--cycle <N> --project-root <root> --passes 2 --surfaces agy,grok`"
    )
    assert section.count(command) == 1, (
        "the teammate section must name exactly once the complete hmad-dispatch "
        "audit-cycle command with feature, phase, cycle, project root, two passes, "
        "and agy,grok surfaces"
    )


def test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "h-mad/*.md"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = [path for path in tracked.split("\0") if path]
    assert "h-mad/SKILL.md" in paths, "the tracked Markdown scan must include SKILL.md"
    pattern = re.compile(r"h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces")
    occurrences = []
    for path in paths:
        text = (REPO / path).read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            occurrences.append(f"{path}:{line}: {match.group(0)}")
    assert not occurrences, (
        "tracked h-mad Markdown must never pair h_mad_audit_cycle.py with "
        "--surfaces; use hmad-dispatch audit-cycle instead:\n"
        + "\n".join(occurrences)
    )


def test_never_do_legs_bullet_states_the_first_gate_leg_set() -> None:
    section = titled_section(
        SKILL_MD.read_text(encoding="utf-8"), "What you NEVER do"
    )
    bullets = [" ".join(bullet.split()) for bullet in re.split(r"(?m)^- ", section)]
    legs_bullets = [
        bullet
        for bullet in bullets
        if bullet.startswith("**Name the reviewer legs with `--legs`")
    ]
    assert len(legs_bullets) == 1, (
        "What you NEVER do must contain exactly one reviewer --legs bullet"
    )
    sentence = (
        "The first gate and the revisions run different leg sets by design, "
        "so the streak, when it is reached, is among revision cycles."
    )
    assert legs_bullets[0].endswith(sentence), (
        "the reviewer --legs bullet must append the explanation that the first "
        "gate uses a different leg set and the streak is among revision cycles"
    )
