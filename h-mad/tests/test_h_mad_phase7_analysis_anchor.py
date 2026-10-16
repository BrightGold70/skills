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
    # Phase 7 also requires the per-cycle artifact telemetry counts (analysis_unversioned).
    (docs / "03-analysis" / "demo.analysis.v1.md").write_text(PASSING, encoding="utf-8")
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


def feature_worktree(root: Path, *, analysis: str = PASSING) -> Path:
    """A feature worktree holding the Phase-6 artifacts; returns its docs/ dir.

    Before 7f merges, the state file is main's while the analysis, its v<N>
    versions and any parked mutation spec exist only in the feature worktree.
    HemaSuite #101 got `BLOCKED` from the CLI for that reason and closed Phase 7
    through a hand-written `check(record, analysis, docs_root=<worktree>/docs)`.
    """
    docs = root / "docs"
    (docs / "03-analysis").mkdir(parents=True, exist_ok=True)
    (docs / "03-analysis" / "demo.analysis.md").write_text(analysis, encoding="utf-8")
    (docs / "03-analysis" / "demo.analysis.v1.md").write_text(analysis, encoding="utf-8")
    return docs


def main_checkout(root: Path) -> Path:
    """Main's state file with the record and NO Phase-6 artifacts."""
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    state = docs / ".bkit-memory.json"
    state.write_text(json.dumps({"orchestrator_state": {"demo": RECORD}}), encoding="utf-8")
    return state


def park_spec(docs: Path, *, restored: bool) -> None:
    pending = docs / "03-analysis" / "demo.pending-mutation-specs"
    pending.mkdir(parents=True, exist_ok=True)
    (pending / "guards.json.pending").write_text("{}", encoding="utf-8")
    live = docs.parent / "tests" / "mutation-specs"
    live.mkdir(parents=True, exist_ok=True)
    if restored:
        (live / "guards.json").write_text("{}", encoding="utf-8")


class TestDocsRootFlag:
    def test_without_the_flag_main_state_blocks_on_artifacts_only_the_worktree_has(
        self, tmp_path: Path
    ) -> None:
        state = main_checkout(tmp_path / "main")
        feature_worktree(tmp_path / "wt")
        proc = run(tmp_path, state)
        assert proc.returncode == 0, proc.stderr
        assert "PHASE7: BLOCKED" in proc.stdout
        assert "analysis_missing" in proc.stdout

    def test_the_flag_reads_the_worktrees_analysis_and_versions(self, tmp_path: Path) -> None:
        state = main_checkout(tmp_path / "main")
        docs = feature_worktree(tmp_path / "wt")
        proc = run(tmp_path, state, "--docs-root", str(docs))
        assert proc.returncode == 0, proc.stderr
        assert "PHASE7: READY blockers=0" in proc.stdout, proc.stdout

    def test_the_versioned_check_follows_the_flag_not_the_state_file(
        self, tmp_path: Path
    ) -> None:
        """Main holds a passing analysis but no v<N>; the worktree holds both."""
        state = main_checkout(tmp_path / "main")
        (state.parent / "03-analysis").mkdir()
        (state.parent / "03-analysis" / "demo.analysis.md").write_text(PASSING, encoding="utf-8")
        docs = feature_worktree(tmp_path / "wt")
        without = run(tmp_path, state)
        assert "analysis_unversioned" in without.stdout, without.stdout
        with_flag = run(tmp_path, state, "--docs-root", str(docs))
        assert "PHASE7: READY blockers=0" in with_flag.stdout, with_flag.stdout

    def test_a_parked_spec_restored_in_the_worktree_is_seen_as_restored(
        self, tmp_path: Path
    ) -> None:
        state = main_checkout(tmp_path / "main")
        docs = feature_worktree(tmp_path / "wt")
        park_spec(docs, restored=True)
        proc = run(tmp_path, state, "--docs-root", str(docs))
        assert "PHASE7: READY blockers=0" in proc.stdout, proc.stdout

    def test_a_parked_spec_never_restored_in_the_worktree_still_blocks(
        self, tmp_path: Path
    ) -> None:
        state = main_checkout(tmp_path / "main")
        docs = feature_worktree(tmp_path / "wt")
        park_spec(docs, restored=False)
        proc = run(tmp_path, state, "--docs-root", str(docs))
        assert "pending_mutation_spec_not_restored" in proc.stdout, proc.stdout

    def test_an_explicit_analysis_still_wins_over_the_flag(self, tmp_path: Path) -> None:
        state = main_checkout(tmp_path / "main")
        docs = feature_worktree(tmp_path / "wt")
        low = tmp_path / "low.analysis.md"
        low.write_text("# Analysis\n\n## Match Rate: 40%\n", encoding="utf-8")
        proc = run(tmp_path, state, "--docs-root", str(docs), "--analysis", str(low))
        assert "match_rate_below_threshold" in proc.stdout or "BLOCKED" in proc.stdout
        assert "PHASE7: READY" not in proc.stdout

    def test_a_docs_root_that_is_not_a_directory_is_an_operational_error(
        self, tmp_path: Path
    ) -> None:
        """A typo must not read as "no analysis here" — that is a verdict about
        artifacts the gate never looked at."""
        state = main_checkout(tmp_path / "main")
        proc = run(tmp_path, state, "--docs-root", str(tmp_path / "absent" / "docs"))
        assert proc.returncode == 2, proc.stdout
        assert "PHASE7:" not in proc.stdout
        assert "--docs-root" in proc.stderr
