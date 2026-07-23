import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import h_mad_telemetry as telemetry  # noqa: E402


def make_state(path: Path, feature: str = "f", **feature_fields) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "orchestrator_state": {
            feature: {
                "started_ts": "2026-07-23T00:00:00Z",
                "last_completed_phase": 6,
                "audit_cycles": {"plan": 0, "design": 0, "impl_plan": 0},
                "iterate_cycles": 0,
                "halt_reason": None,
                **feature_fields,
            }
        }
    }
    path.write_text(json.dumps(state), encoding="utf-8")
    return path


def make_row(feature: str = "f", **fields) -> dict:
    return {
        "feature": feature,
        "last_completed_phase": 6,
        "audit_cycles": {"plan": 0, "design": 0, "impl_plan": 0},
        "iterate_cycles": 0,
        "halt_reason": None,
        **fields,
    }


def add_artifact(docs_root: Path, relative: str) -> Path:
    path = docs_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return path


def row_prefix(
    feature: str,
    phase: int,
    plan: int,
    design: int,
    impl_plan: int,
    iterate: int,
) -> str:
    return (
        f"{feature:<30}{phase:>5}"
        f"{plan:>7}{design:>7}{impl_plan:>7}{iterate:>6}"
    )


def test_record_derives_counts_and_defaults_docs_root_to_docs_state_parent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs_root = tmp_path / "docs"
    state_path = make_state(docs_root / ".bkit-memory.json")
    out_path = tmp_path / "telemetry.jsonl"
    add_artifact(docs_root, "01-plan/features/f.plan.audit.v2.md")
    add_artifact(docs_root, "03-analysis/f.analysis.v3.md")

    assert telemetry.main(
        [
            "record",
            "--feature",
            "f",
            "--state",
            str(state_path),
            "--out",
            str(out_path),
        ]
    ) == 0
    captured = capsys.readouterr()
    recorded = json.loads(out_path.read_text(encoding="utf-8"))

    assert recorded["audit_cycles"] == {"plan": 2, "design": 0, "impl_plan": 0}
    assert recorded["iterate_cycles"] == 2
    assert "audit_cycles={'plan': 2" in captured.out


def test_record_without_artifacts_records_zero_counts(tmp_path: Path) -> None:
    state_path = make_state(
        tmp_path / "docs" / ".bkit-memory.json",
        audit_cycles={"plan": 8, "design": 7, "impl_plan": 6},
        iterate_cycles=5,
    )
    out_path = tmp_path / "telemetry.jsonl"

    assert telemetry.main(
        [
            "record",
            "--feature",
            "f",
            "--state",
            str(state_path),
            "--out",
            str(out_path),
        ]
    ) == 0
    recorded = json.loads(out_path.read_text(encoding="utf-8"))

    assert recorded["audit_cycles"] == {"plan": 0, "design": 0, "impl_plan": 0}
    assert recorded["iterate_cycles"] == 0


@pytest.mark.parametrize("case", ["missing", "malformed", "absent"])
def test_record_error_paths_keep_codes_with_docs_root_flag(
    tmp_path: Path, case: str, capsys: pytest.CaptureFixture[str]
) -> None:
    state_path = tmp_path / "docs" / ".bkit-memory.json"
    if case == "malformed":
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text("{not-json", encoding="utf-8")
    elif case == "absent":
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"orchestrator_state": {}}), encoding="utf-8")

    expected = 3 if case in {"missing", "malformed"} else 2
    assert telemetry.main(
        [
            "record",
            "--feature",
            "f",
            "--state",
            str(state_path),
            "--out",
            str(tmp_path / "telemetry.jsonl"),
            "--docs-root",
            str(tmp_path / "docs"),
        ]
    ) == expected
    stderr = capsys.readouterr().err
    if case == "missing":
        assert "state file not found" in stderr
        assert "malformed state file" not in stderr
    elif case == "malformed":
        assert "malformed state file" in stderr
        assert "state file not found" not in stderr
    else:
        assert "feature 'f' not found in state" in stderr


def test_summary_uses_empty_mapping_fallback_not_zero_derived_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs_root = tmp_path / "docs"
    add_artifact(docs_root, "02-design/features/f.design.audit.v1.md")
    add_artifact(docs_root, "03-analysis/f.analysis.v1.md")
    input_path = tmp_path / "telemetry.jsonl"
    input_path.write_text(
        json.dumps(
            make_row(
                audit_cycles={"plan": 4, "design": 0, "impl_plan": 0},
                iterate_cycles=3,
            )
        )
        + "\n",
        encoding="utf-8",
    )

    assert telemetry.main(
        ["summary", "--input", str(input_path), "--docs-root", str(docs_root)]
    ) == 0
    captured = capsys.readouterr()

    assert row_prefix("f", 6, 0, 1, 0, 0) in captured.out
    assert row_prefix("f", 6, 4, 1, 0, 3) not in captured.out


def test_summary_displays_derived_counts_over_stored_zero_counts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs_root = tmp_path / "docs"
    add_artifact(docs_root, "01-plan/features/f.plan.audit.v2.md")
    add_artifact(docs_root, "03-analysis/f.analysis.v2.md")
    input_path = tmp_path / "telemetry.jsonl"
    input_path.write_text(json.dumps(make_row()) + "\n", encoding="utf-8")

    # --docs-root is required here: without it summary resolves Path("docs") relative
    # to cwd (the repo root under pytest), not to this tmp tree, so the artifacts above
    # would not be found and the stored-value fallback would correctly fire instead.
    assert telemetry.main(
        ["summary", "--input", str(input_path), "--docs-root", str(docs_root)]
    ) == 0
    captured = capsys.readouterr()

    assert row_prefix("f", 6, 2, 0, 0, 1) in captured.out


def test_summary_falls_back_to_stored_counts_when_no_artifacts_exist(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs_root = tmp_path / "chosen-docs"
    input_path = tmp_path / "telemetry.jsonl"
    input_path.write_text(
        json.dumps(
            make_row(
                audit_cycles={"plan": 4, "design": 0, "impl_plan": 0},
                iterate_cycles=0,
            )
        )
        + "\n",
        encoding="utf-8",
    )

    assert telemetry.main(
        ["summary", "--input", str(input_path), "--docs-root", str(docs_root)]
    ) == 0
    captured = capsys.readouterr()

    assert row_prefix("f", 6, 4, 0, 0, 0) in captured.out


def test_summary_derivation_does_not_modify_input_bytes_and_warns_on_derived_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs_root = tmp_path / "docs"
    add_artifact(docs_root, "01-plan/features/f.plan.audit.v4.md")
    input_path = tmp_path / "telemetry.jsonl"
    input_path.write_bytes((json.dumps(make_row()) + "\n").encode("utf-8"))
    before = input_path.read_bytes()

    # See the note in test_summary_displays_derived_counts_over_stored_zero_counts:
    # --docs-root must be explicit or the tmp artifacts are not the ones searched.
    assert telemetry.main(
        ["summary", "--input", str(input_path), "--docs-root", str(docs_root)]
    ) == 0
    captured = capsys.readouterr()

    assert input_path.read_bytes() == before
    assert row_prefix("f", 6, 4, 0, 0, 0) in captured.out
    assert "WARN: 1 feature(s) hit audit_cycles > 3" in captured.out


def test_summary_docs_root_flag_is_used_and_existing_flags_remain_accepted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    selected_root = tmp_path / "selected-docs"
    ignored_root = tmp_path / "ignored-docs"
    add_artifact(selected_root, "01-plan/features/f.plan.audit.v3.md")
    add_artifact(ignored_root, "01-plan/features/f.plan.audit.v9.md")
    input_path = tmp_path / "telemetry.jsonl"
    input_path.write_text(json.dumps(make_row()) + "\n", encoding="utf-8")

    assert telemetry.main(
        [
            "summary",
            "--input",
            str(input_path),
            "--limit",
            "20",
            "--docs-root",
            str(selected_root),
        ]
    ) == 0
    captured = capsys.readouterr()

    assert row_prefix("f", 6, 3, 0, 0, 0) in captured.out


def test_record_and_summary_use_documented_default_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    docs_root = tmp_path / "docs"
    make_state(docs_root / ".bkit-memory.json")
    add_artifact(docs_root, "01-plan/features/f.plan.audit.v2.md")

    assert telemetry.main(["record", "--feature", "f"]) == 0
    default_output = tmp_path / ".h-mad" / "telemetry.jsonl"
    assert default_output.is_file()
    recorded = json.loads(default_output.read_text(encoding="utf-8"))
    assert recorded["audit_cycles"]["plan"] == 2

    assert telemetry.main(["summary"]) == 0
    captured = capsys.readouterr()
    assert row_prefix("f", 6, 2, 0, 0, 0) in captured.out
