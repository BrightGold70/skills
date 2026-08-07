"""RED tests for the Phase-5d wire registry schema and runtime read-back."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import h_mad_wire_registry as registry  # noqa: E402


def _entry(**overrides: object) -> dict:
    record = {
        "kind": "wire",
        "id": "wire-1",
        "caller": "engine.run",
        "callee": "tools.measure",
        "pin": "test_run_calls_measure",
        "owning_feature": "regression-provenance-ledger",
    }
    record.update(overrides)
    return record


@pytest.mark.parametrize("field", ["kind", "id", "caller", "callee", "pin", "owning_feature"])
def test_register_rejects_a_record_missing_required_field(tmp_path: Path, field: str) -> None:
    record = _entry()
    del record[field]
    with pytest.raises(registry.RegistryError, match=field):
        registry.register([record], tmp_path / "wires.jsonl")


def test_register_rejects_counter_kind(tmp_path: Path) -> None:
    with pytest.raises(registry.RegistryError, match="kind"):
        registry.register([_entry(kind="counter")], tmp_path / "wires.jsonl")


def test_register_generates_registered_timestamp_and_ignores_supplied_value(
    tmp_path: Path,
) -> None:
    path = tmp_path / "wires.jsonl"
    result = registry.register([_entry(registered_ts="forged")], path)
    assert result[0]["registered_ts"] != "forged"
    assert result[0]["registered_ts"]
    assert registry.load(path)[0]["registered_ts"] == result[0]["registered_ts"]


def test_register_updates_a_duplicate_id_in_place(tmp_path: Path) -> None:
    path = tmp_path / "wires.jsonl"
    registry.register([_entry()], path)
    result = registry.register([_entry(callee="tools.other")], path)
    assert len(result) == 1
    assert result[0]["callee"] == "tools.other"


def test_load_rejects_malformed_json_with_one_based_line_number(tmp_path: Path) -> None:
    path = tmp_path / "wires.jsonl"
    path.write_text('{"kind":"wire"}\nnot-json\n', encoding="utf-8")
    with pytest.raises(registry.RegistryError, match=r"line 2"):
        registry.load(path)


def test_removed_tombstone_requires_removal_provenance(tmp_path: Path) -> None:
    with pytest.raises(registry.RegistryError, match="removal_provenance"):
        registry.register([_entry(status="removed")], tmp_path / "wires.jsonl")


def test_superseded_tombstone_requires_superseding_feature(tmp_path: Path) -> None:
    with pytest.raises(registry.RegistryError, match="superseding_feature"):
        registry.register(
            [_entry(status="removed", removal_provenance="superseded", removed_by_feature="fix")],
            tmp_path / "wires.jsonl",
        )


def test_any_tombstone_requires_removed_by_feature(tmp_path: Path) -> None:
    with pytest.raises(registry.RegistryError, match="removed_by_feature"):
        registry.register(
            [_entry(status="removed", removal_provenance="pinned-a-defect")],
            tmp_path / "wires.jsonl",
        )


def test_renamed_tombstone_requires_successor_pin(tmp_path: Path) -> None:
    with pytest.raises(registry.RegistryError, match="successor_pin"):
        registry.register(
            [_entry(status="removed", removal_provenance="renamed", removed_by_feature="rename")],
            tmp_path / "wires.jsonl",
        )


def test_register_runtime_readback_rejects_a_silent_write_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "write_text", lambda self, *args, **kwargs: None)
    with pytest.raises(registry.RegistryError, match="read-back|mismatch"):
        registry.register([_entry()], tmp_path / "wires.jsonl")


def test_wire_registry_guard_fires_on_a_deliberate_live_file_leak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import conftest

    target = tmp_path / "wires.jsonl"
    monkeypatch.setattr(conftest, "_live_wire_registry_file", lambda: target)
    guard = conftest._protect_live_wire_registry.__wrapped__()
    next(guard)
    target.write_text("leak\n", encoding="utf-8")
    with pytest.raises(pytest.fail.Exception, match="live wire registry"):
        next(guard)
    assert not target.exists()


def test_wire_registry_guard_mutation_is_caught_by_harness(tmp_path: Path) -> None:
    # The explicit root keeps the real conftest mutation target and pytest cwd
    # unambiguous. The baseline command runs only this passing guard test, not
    # the intentionally RED registry tests.
    from h_mad_mutation_harness import run_spec
    import json

    root = Path(__file__).resolve().parents[2]
    spec = tmp_path / "mutations.json"
    spec.write_text(json.dumps({
        "root": str(root),
        "command": [
            sys.executable, "-m", "pytest", "h-mad/tests/test_h_mad_wire_registry.py::"
            "test_wire_registry_guard_fires_on_a_deliberate_live_file_leak", "-q",
        ],
        "mutations": [{
            "name": "make wire registry guard permissive",
            "file": "h-mad/tests/conftest.py",
            "find": "    # J18 guard mutation anchor.\n    if after == before:",
            "replace": "    # J18 guard mutation anchor.\n    if True:",
        }],
    }), encoding="utf-8")
    result = run_spec(spec)
    assert result["verdict"] == "ALL_CAUGHT", result
