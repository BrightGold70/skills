"""Committed mutation specs must keep their anchors current."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_mutation_harness  # noqa: E402
from h_mad_mutation_harness import classify_spec_file, precheck_spec  # noqa: E402


def _own_committed_mutation_specs(project_root: Path) -> tuple[list[Path], list[str]]:
    specs_dir = project_root / "tests" / "mutation-specs"
    spec_paths = []
    skipped = []
    for candidate in sorted(specs_dir.glob("*.json")):
        kind, detail = classify_spec_file(candidate)
        if kind == "spec":
            spec_paths.append(candidate)
        else:
            skipped.append(f"{candidate}: classifier={kind!r} detail={detail!r}")
    assert spec_paths, f"found no committed mutation specs in {specs_dir}"
    return spec_paths, skipped


def _committed_spec_drift_messages(spec_paths: list[Path], skipped: list[str]) -> list[str]:
    failures = [f"skipped committed mutation spec: {entry}" for entry in skipped]
    for spec_path in spec_paths:
        try:
            spec = h_mad_mutation_harness._load_spec(spec_path)
            root = h_mad_mutation_harness._resolve_root(spec, spec_path)
            result = precheck_spec(spec_path)
        except h_mad_mutation_harness.SpecError as exc:
            failures.append(f"{spec_path.name}: spec failed to load ({exc})")
            continue

        for entry in result["drifted"]:
            failures.append(
                f"{spec_path.name} root {root}: {entry['name']}: "
                f"anchor matched {entry['hits']} times in {entry['file']}, "
                "expected exactly 1"
            )
        for entry in result["unreadable"]:
            failures.append(f"{spec_path.name} root {root}: {entry}")
    return failures


def test_committed_mutation_specs_are_not_drifted() -> None:
    """Sweeps this project's own tests/mutation-specs/."""
    project_root = Path(__file__).resolve().parents[1]
    spec_paths, skipped = _own_committed_mutation_specs(project_root)

    failures = _committed_spec_drift_messages(spec_paths, skipped)

    assert not failures, (
        "committed mutation specs have drifted anchors:\n" + "\n".join(failures)
    )
