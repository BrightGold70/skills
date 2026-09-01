"""Pins the surface-suffixed audit blind spot and the arbitrary pick it exposes.

`_VERSION_RE` was `\\.v(\\d+)(?:\\.p\\d+)?\\.md$`, which cannot match an audit named
for the surface that produced it (`<feature>.design.audit.v26.codex.md`). Those
files are inside the `*.audit.v*.md` glob already; only the regex rejected them,
so `latest_audit_path` returned an older cycle and `h_mad_do_preconditions`
printed `PRECONDITION: PASS` off a stale report. Measured on HemaSuite
2026-09-01: 30 of 343 design audits, 54 of 480 impl-plan audits and 14 of 297
plan audits were invisible -- and the brief that reported this defect had counted
only two of those three phases.

Two directions, both silent, which is why each gets its own pin:

- **Too narrow** is the original defect: a real audit is unseen and a stale one
  gates.
- **Too wide** is its mirror: `…v26.codex.draft.md` is not an audit report, and
  admitting it hands `_audit_issue` a file with no gate headings at exactly the
  moment the operator is told the gate passed.

The suffix grammar is taken from the corpus, not invented: over 1120 real audit
files the token after `.v<N>` is one of `''`, `.p1`, `.p2`, `.p3`, `.codex`,
`.agy`, `.claude` -- always exactly one token, and a pass index NEVER co-occurs
with a surface name. So the rule is "one optional discriminator", not "a pass
index and a surface".

The third pin is the defect the widening would otherwise introduce. 256 of 763
`(feature, phase, version)` groups already hold more than one file, and
`root.glob()` yields in filesystem order, so keying `artifacts[version] = path`
picks arbitrarily among them. That was tolerable while the collisions were
`.p1`/`.p2` -- two halves of one audit -- and is not tolerable now that
`.codex` and `.agy` at the same cycle are two DIFFERENT auditors which, in this
project's own record, routinely disagree. Gating on whichever one the filesystem
happened to list first is "gate on one audit pass" wearing a green verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import h_mad_cycle_counts as counts  # noqa: E402
from h_mad_do_preconditions import check  # noqa: E402


CLEAN = "# Audit\n\n## Must-fix\n\nNone\n\n## Should-fix\n\nNone\n"
DIRTY = "# Audit\n\n## Must-fix\n\n- The resolver is duplicated.\n\n## Should-fix\n\nNone\n"


def artifact(root: Path, relative: str, text: str = "") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestSurfaceSuffixedAuditsAreDiscovered:
    def test_a_surface_suffixed_audit_is_seen(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        found = artifact(root, "02-design/features/f.design.audit.v26.codex.md")

        assert counts.audit_artifacts(root, "f", "design") == {26: found}

    def test_the_surface_set_is_open(self, tmp_path: Path) -> None:
        """A closed `(codex|agy|claude)` alternation re-creates this defect on the
        fourth surface, silently and for exactly the same reason."""
        root = tmp_path / "docs"
        artifact(root, "01-plan/features/f.plan.audit.v1.gemini.md")
        artifact(root, "01-plan/features/f.plan.audit.v2.some-new-surface.md")

        assert sorted(counts.audit_artifacts(root, "f", "plan")) == [1, 2]

    def test_a_surface_suffixed_audit_wins_the_latest_over_an_older_bare_one(
        self, tmp_path: Path
    ) -> None:
        """The measured consequence: `latest_audit_path` returned the stale file."""
        root = tmp_path / "docs"
        artifact(root, "02-design/features/f.design.audit.v18.md")
        newest = artifact(root, "02-design/features/f.design.audit.v26.codex.md")

        assert counts.latest_audit_path(root, "f", "design") == newest

    def test_a_pass_index_still_matches(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        found = artifact(root, "01-plan/features/f.plan.audit.v4.p2.md")

        assert counts.audit_artifacts(root, "f", "plan") == {4: found}

    def test_analysis_files_share_the_widened_grammar(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        artifact(root, "03-analysis/f.analysis.v3.codex.md")

        assert sorted(counts.analysis_artifacts(root, "f")) == [3]


class TestTheWideningStopsWhereTheGrammarDoes:
    """Too wide is as silent as too narrow -- these are the mirror pins."""

    @pytest.mark.parametrize(
        "name",
        [
            "f.plan.audit.v3.codex.draft.md",  # two tokens: not the grammar
            "f.plan.audit.vX.md",  # no version at all
            "f.plan.audit.v3..md",  # empty token
            "f.plan.audit.v3.md.bak",  # not a markdown file
            "f.plan.audit.v3-codex.md",  # token not dot-separated
        ],
    )
    def test_a_non_audit_shape_is_not_admitted(self, tmp_path: Path, name: str) -> None:
        root = tmp_path / "docs"
        artifact(root, f"01-plan/features/{name}")

        assert counts.audit_artifacts(root, "f", "plan") == {}


class TestEveryAuditAtTheLatestCycleIsVisible:
    def test_two_surfaces_at_one_cycle_are_both_kept(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        agy = artifact(root, "01-plan/features/f.plan.audit.v29.agy.md")
        codex = artifact(root, "01-plan/features/f.plan.audit.v29.codex.md")

        assert counts.latest_audit_paths(root, "f", "plan") == [agy, codex]

    def test_the_single_path_accessor_is_deterministic_under_glob_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`root.glob()` yields in filesystem order. Two runs over one tree must
        not disagree about which audit gated the phase."""
        root = tmp_path / "docs"
        agy = artifact(root, "01-plan/features/f.plan.audit.v29.agy.md")
        codex = artifact(root, "01-plan/features/f.plan.audit.v29.codex.md")

        original_glob = counts.Path.glob

        def reversed_glob(path: Path, pattern: str):
            return iter(sorted(original_glob(path, pattern), reverse=True))

        monkeypatch.setattr(counts.Path, "glob", reversed_glob)

        assert counts.audit_artifacts(root, "f", "plan") == {29: agy}
        assert counts.latest_audit_paths(root, "f", "plan") == [agy, codex]


class TestAnArchivedCopyIsTheSameAudit:
    """Archiving copies rather than moves, so most cycles exist twice under one
    filename. Counting them as two audits doubles every finding a caller reports
    and makes a one-auditor cycle look like a two-auditor one."""

    def test_the_live_and_archived_copy_collapse_to_one(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        live = artifact(root, "01-plan/features/f.plan.audit.v2.md")
        artifact(root, "archive/2026-07/f/f.plan.audit.v2.md")

        assert counts.latest_audit_paths(root, "f", "plan") == [live]
        assert counts.audit_artifacts(root, "f", "plan") == {2: live}

    def test_an_archive_only_cycle_is_still_found(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        artifact(root, "01-plan/features/f.plan.audit.v1.md")
        archived = artifact(root, "archive/2026-07/f/f.plan.audit.v3.md")

        assert counts.latest_audit_paths(root, "f", "plan") == [archived]

    def test_two_surfaces_survive_the_collapse(self, tmp_path: Path) -> None:
        """The collapse keys on filename, so it must not fold distinct surfaces."""
        root = tmp_path / "docs"
        agy = artifact(root, "01-plan/features/f.plan.audit.v5.agy.md")
        codex = artifact(root, "01-plan/features/f.plan.audit.v5.codex.md")
        artifact(root, "archive/2026-07/f/f.plan.audit.v5.agy.md")

        assert counts.latest_audit_paths(root, "f", "plan") == [agy, codex]


class TestThePhaseGateReadsEverySurface:
    def _feature(self, tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        (repo / "docs/01-plan/features").mkdir(parents=True)
        (repo / "docs/02-design/features").mkdir(parents=True)
        (repo / "docs/01-plan/features/f.plan.md").write_text("plan", encoding="utf-8")
        (repo / "docs/02-design/features/f.design.md").write_text("design", encoding="utf-8")
        return repo

    def test_a_dirty_second_surface_at_the_same_cycle_fails_the_gate(
        self, tmp_path: Path
    ) -> None:
        """The false PASS this whole file exists for. Two auditors ran cycle 29;
        one found nothing and one found a blocker. Reading either alone is a
        coin flip, and one face of it clears the gate."""
        repo = self._feature(tmp_path)
        d = repo / "docs/02-design/features"
        (d / "f.design.audit.v29.agy.md").write_text(CLEAN, encoding="utf-8")
        (d / "f.design.audit.v29.codex.md").write_text(DIRTY, encoding="utf-8")
        (repo / "docs/01-plan/features/f.plan.audit.v1.md").write_text(
            CLEAN, encoding="utf-8"
        )

        rc, issues = check(repo, "f")

        assert rc == 1
        assert any(i.startswith("DIRTY:") and "codex" in i for i in issues)

    def test_two_clean_surfaces_still_pass(self, tmp_path: Path) -> None:
        repo = self._feature(tmp_path)
        d = repo / "docs/02-design/features"
        (d / "f.design.audit.v29.agy.md").write_text(CLEAN, encoding="utf-8")
        (d / "f.design.audit.v29.codex.md").write_text(CLEAN, encoding="utf-8")
        (repo / "docs/01-plan/features/f.plan.audit.v1.md").write_text(
            CLEAN, encoding="utf-8"
        )

        assert check(repo, "f") == (0, ["OK"])

    def test_an_unscoreable_second_surface_is_reported_not_skipped(
        self, tmp_path: Path
    ) -> None:
        repo = self._feature(tmp_path)
        d = repo / "docs/02-design/features"
        (d / "f.design.audit.v29.agy.md").write_text(CLEAN, encoding="utf-8")
        (d / "f.design.audit.v29.codex.md").write_text(
            "# Audit\n\nProse with no headings.\n", encoding="utf-8"
        )
        (repo / "docs/01-plan/features/f.plan.audit.v1.md").write_text(
            CLEAN, encoding="utf-8"
        )

        rc, issues = check(repo, "f")

        assert rc == 1
        assert any(i.startswith("INVALID:") and "codex" in i for i in issues)


class TestThePhaseNameTheRestOfHMadUses:
    """`PHASE_SEGMENTS` keys `impl_plan`; every other h-mad surface spells the
    phase `impl-plan` (`h_mad_assemble_audit.PHASES`, `h_mad_audit_cycle`'s
    `--phase` choices). `audit_artifacts` answered `{}` for the spelling the
    codebase itself uses -- an empty result that reads as "no audits were run"."""

    def test_the_dashed_spelling_finds_the_same_audits(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        found = artifact(root, "01-plan/features/f.impl-plan.audit.v2.md")

        assert counts.audit_artifacts(root, "f", "impl-plan") == {2: found}
        assert counts.audit_artifacts(root, "f", "impl_plan") == {2: found}
        assert counts.latest_audit_path(root, "f", "impl-plan") == found

    def test_a_genuinely_unknown_phase_is_still_empty(self, tmp_path: Path) -> None:
        root = tmp_path / "docs"
        artifact(root, "01-plan/features/f.plan.audit.v1.md")

        assert counts.audit_artifacts(root, "f", "not-a-phase") == {}
        assert counts.latest_audit_path(root, "f", "not-a-phase") is None
