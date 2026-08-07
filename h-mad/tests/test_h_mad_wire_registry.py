"""RED tests for the Phase-5d wire registry schema and runtime read-back."""

import json
import subprocess
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


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _commit_registry(repo: Path, records: list[dict]) -> str:
    path = repo / ".h-mad" / "wires.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "registry")
    return _git(repo, "rev-parse", "HEAD")


def _git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    return repo


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


def test_partition_separates_resolving_and_missing_active_records() -> None:
    records = [_entry(pin="test_present"), _entry(id="wire-2", pin="test_absent")]
    resolving, missing, unverified = registry.partition(records, {"test_present"})
    assert [record["id"] for record in resolving] == ["wire-1"]
    assert [record["id"] for record in missing] == ["wire-2"]
    assert unverified == []


def test_partition_does_not_report_removed_pin_as_missing() -> None:
    tombstone = _entry(
        status="removed", removal_provenance="pinned-a-defect", removed_by_feature="fix"
    )
    assert registry.partition([tombstone], set()) == ([], [], [])


def test_partition_resolves_present_rename_and_unverifies_absent_rename() -> None:
    present = _entry(
        id="old-present", status="removed", removal_provenance="renamed",
        removed_by_feature="rename", successor_pin="test_new",
    )
    absent = _entry(
        id="old-absent", status="removed", removal_provenance="renamed",
        removed_by_feature="rename", successor_pin="test_gone",
    )
    resolving, missing, unverified = registry.partition([present, absent], {"test_new"})
    assert [(record["id"], record["pin"]) for record in resolving] == [("old-present", "test_new")]
    assert missing == []
    assert [record["id"] for record in unverified] == ["old-absent"]


def test_partition_is_pure_without_subprocess_or_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: pytest.fail("subprocess"))
    records = [_entry(pin="test_present")]
    assert registry.partition(records, {"test_present"})[0] == records


def test_collect_returns_pytest_node_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        stdout = "tests/test_a.py::test_one\ntests/test_b.py::test_two\n2 tests collected\n"
        returncode = 0

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    assert registry.collect(tmp_path) == {"tests/test_a.py::test_one", "tests/test_b.py::test_two"}


def test_run_pins_empty_does_not_spawn_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: pytest.fail("spawned"))
    assert registry.run_pins([], tmp_path) == ([], [])


def test_run_pins_attributes_failed_pin_and_owning_feature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Result:
        stdout = "PASSED tests/test_ok.py::test_ok\nFAILED tests/test_bad.py::test_bad - assert False\n"
        returncode = 1

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    good = _entry(id="good", pin="tests/test_ok.py::test_ok")
    bad = _entry(id="bad", pin="tests/test_bad.py::test_bad", owning_feature="feature-x")
    verified, broken = registry.run_pins([good, bad], tmp_path)
    assert [record["id"] for record in verified] == ["good"]
    assert [record["id"] for record in broken] == ["bad"]
    assert "feature-x" in capsys.readouterr().out


def test_run_pins_reports_unclassified_pin_as_internal_inconsistency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Result:
        stdout = ""
        returncode = 0

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    record = _entry(pin="tests/test_unknown.py::test_unknown")
    assert registry.run_pins([record], tmp_path) == ([], [])
    assert "INTERNAL INCONSISTENCY" in capsys.readouterr().out


def test_git_show_reads_a_path_at_a_valid_commit(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    sha = _commit_registry(repo, [_entry()])
    assert registry.git_show(sha, ".h-mad/wires.jsonl", repo) == (
        json.dumps(_entry()) + "\n"
    )


def test_git_show_rejects_an_invalid_sha(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    _commit_registry(repo, [_entry()])
    with pytest.raises(registry.RegistryError, match="invalid.*SHA|commit"):
        registry.git_show("not-a-commit", ".h-mad/wires.jsonl", repo)


def test_load_base_treats_a_path_absent_at_a_valid_commit_as_empty(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    sha = _commit_registry(repo, [])
    (repo / ".h-mad" / "wires.jsonl").unlink()
    _git(repo, "add", "-u")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "remove registry")
    assert registry.load_base(sha, ".h-mad/missing.jsonl", repo) == []


def test_compare_returns_the_base_record_for_an_undeclared_removal() -> None:
    removed = _entry(id="wire-removed", owning_feature="feature-owner")
    assert registry.compare([removed], []) == [removed]


def test_compare_is_pure_and_does_not_call_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: pytest.fail("git"))
    record = _entry(id="wire-removed")
    assert registry.compare([record], []) == [record]


def test_compare_does_not_report_a_tombstoned_id_present_at_head() -> None:
    tombstone = _entry(
        id="wire-removed", status="removed", removal_provenance="pinned-a-defect",
        removed_by_feature="fix",
    )
    assert registry.compare([tombstone], [tombstone]) == []
