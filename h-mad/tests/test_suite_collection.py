"""Every directory holding tests must be collected by a bare `pytest`.

Measured 2026-09-01: the suite was habitually invoked as
`pytest h-mad/tests handoff/tests`, which excluded the 110 tests living in
`handoff/scripts/` beside the scripts they pin. One of them had been RED since
2026-08-31, and every "full suite passed" claim in that window — including a
handoff document's own closing verification, and several made while shipping
other work — was true of the paths named and silently blind to the rest.

That is the worst shape a coverage gap can take: not a failing gate, but a
passing one that was never asked the question. The repair is `testpaths`, and
this test is what stops a new test directory from being added outside it.

`testpaths` applies only when pytest is given no path arguments, so an explicit
install-path run (`pytest ~/.claude/skills/h-mad/tests/`) is unaffected.

**Discrimination, verified once by hand rather than by a committed spec.**
Restoring the exact pre-fix line (`testpaths = h-mad/tests handoff/tests`) makes
the test below fail — measured 2026-09-01 through the mutation harness, which
reported ALL_CAUGHT. The spec was then DELETED rather than kept: `pytest.ini`
lives at the repository root, so a spec targeting it needs a `root` that escapes
this skill, and `test_every_committed_spec_resolves_within_its_own_skill` refuses
that — an installed skill must carry specs it can still resolve. That portability
rule outranks the convenience of a committed mutant, so the result is recorded
here instead: the guard was proven, not assumed.
"""

from __future__ import annotations

import configparser
import subprocess
from pathlib import Path

import pytest


def _repo_root() -> Path | None:
    """Resolved through git, because this skill is INSTALLED as a symlink and
    `parents[2]` from the install path is `~/.claude/skills`, not the repo."""
    try:
        out = subprocess.run(
            ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None
    return Path(out) if out else None


def test_no_declared_skill_has_a_test_directory_left_out() -> None:
    """Completeness WITHIN each skill that testpaths already covers.

    Deliberately not "every test directory in the repo": this checkout also
    vendors three independent projects (`clinical-statistics-analyzer`,
    `hemasuite`, `hematology-paper-writer`) with their own dependency sets, and
    pulling those into the default run would make a bare `pytest` require
    everything they import. That is a decision for their owners, not a
    side effect of fixing a collection gap.

    The measured failure was narrower and this is its exact shape: `handoff/tests`
    was declared while `handoff/scripts` — same skill, 110 tests, one of them red —
    was not. So for every skill already declared, every directory under it holding
    test files must be declared too.
    """
    root = _repo_root()
    if root is None:
        pytest.skip("not inside a git checkout — nothing to assert about repo config")
    ini = root / "pytest.ini"
    assert ini.is_file(), (
        "pytest.ini is gone: a bare `pytest` then collects by rootdir discovery and "
        "the habitual two-path invocation silently excludes whole directories again"
    )
    cfg = configparser.ConfigParser()
    cfg.read(ini, encoding="utf-8")
    declared = {p.strip() for p in cfg["pytest"]["testpaths"].split() if p.strip()}
    assert declared, "testpaths is empty"

    skills = {d.split("/", 1)[0] for d in declared}
    missing = sorted(
        str(path.parent.relative_to(root))
        for skill in skills
        for path in (root / skill).rglob("test_*.py")
        if ".git" not in path.parts
        and str(path.parent.relative_to(root)) not in declared
    )
    assert not missing, (
        "these directories belong to a skill already in testpaths but would not be "
        f"collected by a bare `pytest`: {missing}. Add them to pytest.ini."
    )
