"""Pins for the Grok audit surface's declared documentation exclusions."""

from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
EXCLUSIONS = REPO / "docs/03-analysis/probes/grok-audit-surface/exclusions.txt"


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
