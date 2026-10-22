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
def test_exec_grok_bullet_states_the_strict_contract():
    from pathlib import Path

    from test_grok_fallback_docs import titled_section

    skill = Path(__file__).parents[1] / "SKILL.md"
    lines = titled_section(
        skill.read_text(),
        "Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot",
    ).splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if "**`exec grok`** — an explicit RED/GREEN implementer fallback" in line
    )
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].lstrip().startswith("- **")
        ),
        len(lines),
    )
    bullet = " ".join(" ".join(lines[start:end]).split())
    expected = (
        "From FR-11, `exec grok` always runs `--sandbox strict`: a weaker or unknown "
        "`--sandbox` value exits 2 unless `--allow-weaker-sandbox` is also given, "
        "which is recorded in `<log>.profile`, and `GROK_SANDBOX` is removed from "
        "grok's environment. In a git work tree it stages its prompt and `TMPDIR` "
        "under `<top level>/.h-mad/tmp/` and exits 2, launching nothing, when `--cd` "
        "is below the top level, when the repository does not ignore `.h-mad/tmp/`, "
        "or when `git rev-parse` fails for a reason other than \"not a git repository\"; "
        "outside a work tree it uses `<cd>/.tmp/`."
    )
    assert expected in bullet, "exec grok bullet must state the verbatim FR-11 strict contract"


def test_agent_substrate_grok_row_states_the_strict_default():
    from pathlib import Path

    from test_grok_fallback_docs import titled_section

    substrate = Path(__file__).parents[1] / "references" / "agent-substrate.md"
    section = titled_section(
        substrate.read_text(), "Agent Dispatch Substrate (cmux | orca)"
    )
    row = next(line for line in section.splitlines() if "GROK_SANDBOX" in line)
    row = " ".join(row.split())
    expected = (
        "`--sandbox` defaults to `strict`; a weaker or unknown profile exits 2 unless "
        "`--allow-weaker-sandbox` is given, and the effective profile is recorded in "
        "`<log>.profile`. `GROK_SANDBOX` is removed from the child. The prompt and "
        "`TMPDIR` are staged under `<top level>/.h-mad/tmp/` in a git work tree, or "
        "`<cd>/.tmp/` outside one, and `exec` refuses a `--cd` below the top level, "
        "an unignored `.h-mad/tmp/`, and a `git rev-parse` failure other than "
        "\"not a git repository\"."
    )
    assert "[--sandbox <profile>] [--allow-weaker-sandbox]" in row, (
        "agent-substrate exec grok command must expose the strict-default override"
    )
    assert expected in row, "agent-substrate exec grok row must state the verbatim FR-11 contract"
