import inspect
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import h_mad_cycle_counts as counts  # noqa: E402


def artifact(root: Path, relative: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return path


def test_audit_artifacts_maps_versions_and_skips_gaps(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    v1 = artifact(root, "01-plan/features/f.plan.audit.v1.md")
    v3 = artifact(root, "01-plan/features/f.plan.audit.v3.md")

    assert counts.audit_artifacts(root, "f", "plan") == {1: v1, 3: v3}
    assert counts.audit_cycles(root, "f") == {
        "plan": 3,
        "design": 0,
        "impl_plan": 0,
    }


def test_two_contiguous_plan_audits_derive_cycle_two(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "01-plan/features/f.plan.audit.v1.md")
    artifact(root, "01-plan/features/f.plan.audit.v2.md")

    assert counts.audit_cycles(root, "f")["plan"] == 2


def test_plan_and_impl_plan_audits_derive_expected_phase_dict(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "01-plan/features/f.plan.audit.v2.md")
    artifact(root, "02-design/features/f.impl-plan.audit.v1.md")

    assert counts.audit_cycles(root, "f") == {
        "plan": 2,
        "design": 0,
        "impl_plan": 1,
    }


def test_audit_cycles_discovers_all_phase_roots(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "01-plan/features/f.plan.audit.v2.md")
    artifact(root, "02-design/features/f.design.audit.v4.md")
    artifact(root, "02-design/features/f.impl-plan.audit.v1.md")

    assert counts.audit_cycles(root, "f") == {
        "plan": 2,
        "design": 4,
        "impl_plan": 1,
    }


def test_missing_phase_is_zero_and_latest_audit_is_highest(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    v2 = artifact(root, "01-plan/features/f.plan.audit.v2.md")

    assert counts.audit_artifacts(root, "f", "design") == {}
    assert counts.latest_audit_path(root, "f", "plan") == v2
    assert counts.latest_audit_path(root, "f", "design") is None


def test_archive_audits_are_included_and_can_be_disabled(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    live = artifact(root, "01-plan/features/f.plan.audit.v1.md")
    archived = artifact(root, "archive/2019-01/f/f.plan.audit.v3.md")

    assert counts.audit_artifacts(root, "f", "plan") == {1: live, 3: archived}
    assert counts.audit_cycles(root, "f")["plan"] == 3
    assert counts.audit_artifacts(root, "f", "plan", include_archive=False) == {1: live}
    assert counts.latest_audit_path(root, "f", "plan") == archived


def test_archived_audits_from_multiple_months_are_both_discovered(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    january = artifact(root, "archive/2019-01/f/f.plan.audit.v2.md")
    july = artifact(root, "archive/2026-07/f/f.plan.audit.v4.md")

    assert counts.audit_artifacts(root, "f", "plan") == {2: january, 4: july}
    assert counts.audit_cycles(root, "f")["plan"] == 4


def test_analysis_artifacts_and_iterate_cycles(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    v1 = artifact(root, "03-analysis/f.analysis.v1.md")
    v4 = artifact(root, "03-analysis/f.analysis.v4.md")
    archived = artifact(root, "archive/2026-07/f/f.analysis.v6.md")

    assert counts.analysis_artifacts(root, "f") == {1: v1, 4: v4, 6: archived}
    assert counts.iterate_cycles(root, "f") == 5
    assert counts.analysis_artifacts(root, "f", include_archive=False) == {1: v1, 4: v4}


def test_single_analysis_version_and_absence_both_have_zero_iterations(tmp_path: Path) -> None:
    root = tmp_path / "docs"

    assert counts.analysis_artifacts(root, "none") == {}
    assert counts.iterate_cycles(root, "none") == 0

    versioned = artifact(root, "03-analysis/one.analysis.v1.md")
    assert counts.analysis_artifacts(root, "one") == {1: versioned}
    assert counts.iterate_cycles(root, "one") == 0


def test_four_contiguous_analysis_versions_derive_three_iterations(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    paths = [artifact(root, f"03-analysis/f.analysis.v{version}.md") for version in range(1, 5)]

    assert counts.analysis_artifacts(root, "f") == {
        version: path for version, path in enumerate(paths, start=1)
    }
    assert counts.iterate_cycles(root, "f") == 3


def test_unversioned_analysis_is_not_an_artifact(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "03-analysis/f.analysis.md")

    assert counts.analysis_artifacts(root, "f") == {}
    assert counts.iterate_cycles(root, "f") == 0


def test_literal_feature_boundary_excludes_prefix_collisions(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "01-plan/features/feat-ab.plan.audit.v9.md")

    assert counts.audit_cycles(root, "feat") == {
        "plan": 0,
        "design": 0,
        "impl_plan": 0,
    }


def test_templates_are_never_searched(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "templates/audit-example.audit.v1.md")

    assert counts.audit_cycles(root, "audit-example") == {
        "plan": 0,
        "design": 0,
        "impl_plan": 0,
    }


def test_malformed_versions_are_ignored_without_raising(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    artifact(root, "01-plan/features/f.plan.audit.vX.md")
    artifact(root, "03-analysis/f.analysis.md")

    assert counts.audit_artifacts(root, "f", "plan") == {}
    assert counts.analysis_artifacts(root, "f") == {}


def test_case_sensitive_feature_filter_survives_case_insensitive_glob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "docs"
    wrong_case = root / "01-plan/features/Feat.plan.audit.v1.md"
    wrong_case.parent.mkdir(parents=True)

    original_glob = counts.Path.glob

    def fake_glob(path: Path, pattern: str):
        if path == root / "01-plan/features":
            return iter([wrong_case])
        return original_glob(path, pattern)

    monkeypatch.setattr(counts.Path, "glob", fake_glob)

    assert counts.audit_artifacts(root, "feat", "plan") == {}


def test_oserror_from_one_root_does_not_mask_other_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "docs"
    found = artifact(root, "02-design/features/f.design.audit.v2.md")
    original_glob = counts.Path.glob

    def flaky_glob(path: Path, pattern: str):
        if path == root / "01-plan/features":
            raise OSError("simulated unavailable root")
        return original_glob(path, pattern)

    monkeypatch.setattr(counts.Path, "glob", flaky_glob)

    assert counts.audit_artifacts(root, "f", "plan") == {}
    assert counts.audit_artifacts(root, "f", "design") == {2: found}


def test_public_derivations_delegate_to_artifact_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = {7: Path("sentinel.md")}
    docs_root = Path("explicit-docs-root")
    feature = "explicit-feature"
    audit_calls = []
    analysis_calls = []

    def fake_audits(root: Path, name: str, phase: str, *, include_archive: bool = True):
        audit_calls.append((root, name, phase, include_archive))
        return sentinel

    def fake_analysis(root: Path, name: str, *, include_archive: bool = True):
        analysis_calls.append((root, name, include_archive))
        return sentinel

    monkeypatch.setattr(counts, "audit_artifacts", fake_audits)
    monkeypatch.setattr(counts, "analysis_artifacts", fake_analysis)

    assert counts.audit_cycles(docs_root, feature) == {
        "plan": 7,
        "design": 7,
        "impl_plan": 7,
    }
    assert audit_calls == [
        (docs_root, feature, "plan", True),
        (docs_root, feature, "design", True),
        (docs_root, feature, "impl_plan", True),
    ]

    audit_calls.clear()
    assert counts.latest_audit_path(docs_root, feature, "plan") == sentinel[7]
    assert audit_calls == [(docs_root, feature, "plan", True)]

    assert counts.iterate_cycles(docs_root, feature) == 6
    assert analysis_calls == [(docs_root, feature, True)]


def test_derivation_helpers_contain_no_independent_glob_or_regex() -> None:
    for function in (counts.latest_audit_path, counts.audit_cycles, counts.iterate_cycles):
        source = inspect.getsource(function)
        for forbidden in (".glob(", "rglob", "fnmatch", "import glob", "glob.glob", "re.compile"):
            assert forbidden not in source


def test_module_is_stdlib_only_and_does_not_import_jsonschema() -> None:
    source = (SCRIPT_DIR / "h_mad_cycle_counts.py").read_text(encoding="utf-8")
    assert "import jsonschema" not in source

    # Asserting `"jsonschema" not in sys.modules` here would be an assertion about
    # global interpreter state, not about this module: any earlier test that touches
    # the state scripts imports jsonschema first, and this test then fails for a
    # reason that has nothing to do with the module under test. Ask a clean
    # interpreter instead -- that is the claim AC-NFR-1 actually makes, and the one
    # that matters, since telemetry must keep running under the bare `python3` the
    # state scripts cannot use.
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import h_mad_cycle_counts; "
            "print('jsonschema' in sys.modules)",
            str(SCRIPT_DIR),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip() == "False"


@pytest.mark.parametrize(
    ("feature", "expected"),
    [
        (
            "orca-git-native-checkpoints-and-merge-gate",
            {"plan": 2, "design": 2, "impl_plan": 1},
        ),
        (
            "worktree-parallel-multi-module-tdd",
            {"plan": 3, "design": 2, "impl_plan": 2},
        ),
        ("dispatch-resolve-verb", {"plan": 2, "design": 1, "impl_plan": 1}),
    ],
)
def test_live_repo_audit_cycles(feature: str, expected: dict[str, int]) -> None:
    assert counts.audit_cycles(REPO_ROOT / "docs", feature) == expected


def test_live_repo_features_without_analysis_map_empty() -> None:
    docs_root = REPO_ROOT / "docs"

    assert counts.analysis_artifacts(docs_root, "feature-with-no-analysis-files") == {}
    assert counts.analysis_artifacts(docs_root, "dispatch-resolve-verb") == {}
    assert counts.iterate_cycles(docs_root, "dispatch-resolve-verb") == 0
