"""Pins the analysis path to the state file, not to the process CWD.

`main()` built the default as `Path("docs/03-analysis") / f"{feature}.analysis.md"`
-- a RELATIVE path, resolved against wherever the process happened to be started.
The state file argument already names the project tree the feature belongs to, so
CWD is never the right anchor: H-MAD is routinely driven from a monorepo root
against a sub-project's state file, which is HemaSuite's entire layout
(`hematology-paper-writer/docs/.bkit-memory.json`).

Filed 2026-08-18 and still reproducing on 2026-09-01, 14 days later. Identical
state, identical files, only the CWD differs:

    cd /Users/kimhawk/orca/HemaSuite
    ... hematology-paper-writer/docs/.bkit-memory.json --feature synopsis-authoritative-registry
    -> PHASE7: BLOCKED blockers=1 / analysis_missing

    cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
    ... docs/.bkit-memory.json --feature synopsis-authoritative-registry
    -> PHASE7: READY blockers=0

**Both directions, and only one of them is safe.** The observed failure was a
false BLOCKED, which is loud and costs a re-run. Its mirror is not: start the
process in any tree that happens to have a file at the same relative path and the
gate reports **READY on someone else's analysis** -- a Phase-7 close granted on
evidence belonging to a different feature, in a different project, with nothing in
the output saying so. That direction gets the decoy test below, because a fix
verified only against the safe direction would score a CWD-anchored default as
working.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_phase7_preconditions.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import h_mad_phase7_preconditions as p7  # noqa: E402

RECORD = {
    "feature": "demo",
    "started_ts": "2026-07-22T00:00:00Z",
    "last_completed_phase": 6,
    "current_phase": 7,
    "phase": None,
    "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 1},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
    "archreview": "READY_TO_MERGE",
}
PASSING = "# Analysis: demo\n\n## Match Rate: 96%\n\n## Verdict\nAdvance.\n"


def project(root: Path, *, analysis: str | None = PASSING) -> Path:
    """A sub-project holding its own docs/ tree; returns the state file path."""
    docs = root / "docs"
    (docs / "03-analysis").mkdir(parents=True, exist_ok=True)
    state = docs / ".bkit-memory.json"
    state.write_text(json.dumps({"orchestrator_state": {"demo": RECORD}}), encoding="utf-8")
    if analysis is not None:
        (docs / "03-analysis" / "demo.analysis.md").write_text(analysis, encoding="utf-8")
    return state


def run(cwd: Path, state: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(state), "--feature", "demo", *extra],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class TestTheVerdictDoesNotDependOnWhereYouStand:
    def test_from_inside_the_sub_project(self, tmp_path: Path) -> None:
        """Control. The fixture must be able to produce READY at all, or the
        monorepo-root assertion below would pass for the wrong reason."""
        sub = tmp_path / "sub"
        state = project(sub)

        result = run(sub, Path("docs/.bkit-memory.json"))

        assert "PHASE7: READY" in result.stdout, result.stdout
        assert state.is_file()

    def test_from_the_monorepo_root(self, tmp_path: Path) -> None:
        """The reported defect. Same state, same files, different CWD."""
        sub = tmp_path / "sub"
        project(sub)

        result = run(tmp_path, Path("sub/docs/.bkit-memory.json"))

        assert "PHASE7: READY" in result.stdout, result.stdout
        assert "analysis_missing" not in result.stdout

    def test_from_an_unrelated_directory(self, tmp_path: Path) -> None:
        """An absolute state path from anywhere at all must still resolve."""
        sub = tmp_path / "sub"
        state = project(sub)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        result = run(elsewhere, state)

        assert "PHASE7: READY" in result.stdout, result.stdout


class TestTheUnsafeDirection:
    """A false BLOCKED costs a re-run. A false READY closes a phase on another
    feature's evidence and says nothing."""

    def test_a_decoy_analysis_in_the_cwd_is_not_read(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        state = project(sub, analysis=None)  # the REAL analysis does not exist
        decoy = tmp_path / "docs" / "03-analysis"
        decoy.mkdir(parents=True)
        (decoy / "demo.analysis.md").write_text(PASSING, encoding="utf-8")

        result = run(tmp_path, state)

        assert "PHASE7: BLOCKED" in result.stdout, result.stdout
        assert "analysis_missing" in result.stdout
        # And it must name the path it actually looked at, or the operator goes
        # hunting for a file that is present in front of them.
        assert str(sub / "docs" / "03-analysis") in result.stdout

    def test_a_decoy_does_not_override_the_real_failing_analysis(
        self, tmp_path: Path
    ) -> None:
        """The subtler shape: both files exist and disagree. Reading the wrong one
        turns a real 12% into a passing 96% with no missing-file signal at all."""
        sub = tmp_path / "sub"
        state = project(sub, analysis="# Analysis: demo\n\n## Match Rate: 12%\n")
        decoy = tmp_path / "docs" / "03-analysis"
        decoy.mkdir(parents=True)
        (decoy / "demo.analysis.md").write_text(PASSING, encoding="utf-8")

        result = run(tmp_path, state)

        assert "PHASE7: BLOCKED" in result.stdout, result.stdout
        assert "match_rate" in result.stdout


class TestTheExplicitOverrideStillWins:
    def test_analysis_flag_beats_the_derived_default(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        state = project(sub, analysis="# Analysis: demo\n\n## Match Rate: 12%\n")
        chosen = tmp_path / "hand-picked.md"
        chosen.write_text(PASSING, encoding="utf-8")

        result = run(tmp_path, state, "--analysis", str(chosen))

        assert "PHASE7: READY" in result.stdout, result.stdout

    def test_a_relative_analysis_flag_is_still_the_users_own_cwd_choice(
        self, tmp_path: Path
    ) -> None:
        """Anchoring the DEFAULT must not silently re-root an explicit path the
        user typed -- that would be a second surprise in the opposite direction."""
        sub = tmp_path / "sub"
        state = project(sub, analysis=None)
        (tmp_path / "mine.md").write_text(PASSING, encoding="utf-8")

        result = run(tmp_path, state, "--analysis", "mine.md")

        assert "PHASE7: READY" in result.stdout, result.stdout


class TestTheAnchorHelper:
    def test_a_state_file_in_docs_anchors_to_that_docs(self, tmp_path: Path) -> None:
        state = tmp_path / "sub" / "docs" / ".bkit-memory.json"
        assert p7.resolve_analysis_path(None, state, "demo") == (
            tmp_path / "sub" / "docs" / "03-analysis" / "demo.analysis.md"
        )

    def test_a_state_file_outside_docs_still_never_uses_the_cwd(
        self, tmp_path: Path
    ) -> None:
        """The fallback is where the CWD dependency would survive a partial fix.
        `Path("docs")` here is relative and reintroduces the whole defect for any
        layout that does not keep state inside docs/."""
        state = tmp_path / "proj" / ".bkit-memory.json"
        got = p7.resolve_analysis_path(None, state, "demo")

        assert got.is_absolute() or not str(got).startswith("docs/")
        assert got == tmp_path / "proj" / "docs" / "03-analysis" / "demo.analysis.md"

    def test_an_explicit_path_is_returned_untouched(self, tmp_path: Path) -> None:
        state = tmp_path / "docs" / ".bkit-memory.json"
        assert p7.resolve_analysis_path(Path("mine.md"), state, "demo") == Path("mine.md")
