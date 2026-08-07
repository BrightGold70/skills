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
    assert registry.collect(tmp_path, [Path("tests")]) == {"tests/test_a.py::test_one", "tests/test_b.py::test_two"}


def test_collect_raises_on_collection_failure_with_stderr_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Result:
        stdout = ""
        stderr = "Traceback\nModuleNotFoundError: No module named pytest\n"
        returncode = 1

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    with pytest.raises(registry.RegistryError) as excinfo:
        registry.collect(tmp_path, [Path("tests")])
    assert "exit code 1" in str(excinfo.value)
    assert "No module named pytest" in str(excinfo.value)


def test_collect_raises_on_collection_failure_with_stdout_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Result:
        stdout = "ERROR tests/test_broken.py\nInterrupted: 23 errors during collection\n"
        stderr = ""
        returncode = 2

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    with pytest.raises(registry.RegistryError) as excinfo:
        registry.collect(tmp_path, [Path("tests")])
    message = str(excinfo.value)
    assert "exit code 2" in message
    assert "Interrupted: 23 errors during collection" in message
    assert "stderr (last 20 lines): <empty>" in message


def test_collect_failure_includes_both_stdout_and_stderr_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Result:
        stdout = "ERROR tests/test_broken.py\n"
        stderr = "Traceback\nModuleNotFoundError: No module named broken_dependency\n"
        returncode = 2

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    with pytest.raises(registry.RegistryError) as excinfo:
        registry.collect(tmp_path, [Path("tests")])
    message = str(excinfo.value)
    assert "ERROR tests/test_broken.py" in message
    assert "No module named broken_dependency" in message


def test_collect_accepts_pytest_no_tests_exit_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        stdout = "no tests collected\n"
        stderr = ""
        returncode = 5

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    assert registry.collect(tmp_path, [Path("tests")]) == set()


def test_collect_emits_repo_relative_ids_from_a_real_throwaway_repo(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    test_path = repo / "h-mad" / "tests" / "test_wire.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_registered_wire():\n    assert True\n", encoding="utf-8")

    collected = registry.collect(repo, [Path("h-mad/tests")])

    assert "h-mad/tests/test_wire.py::test_registered_wire" in collected
    assert "tests/test_wire.py::test_registered_wire" not in collected


def test_run_pins_resolves_a_repo_relative_pin_in_a_real_throwaway_repo(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    test_path = repo / "h-mad" / "tests" / "test_wire.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_registered_wire():\n    assert True\n", encoding="utf-8")
    record = _entry(pin="h-mad/tests/test_wire.py::test_registered_wire")

    verified, broken = registry.run_pins([record], repo)

    assert [item["id"] for item in verified] == ["wire-1"]
    assert broken == []


def test_verify_marks_an_existing_registered_pin_verified_end_to_end(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    test_path = repo / "h-mad" / "tests" / "test_wire.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_registered_wire():\n    assert True\n", encoding="utf-8")
    record = _entry(pin="h-mad/tests/test_wire.py::test_registered_wire")
    registry_path = repo / ".h-mad" / "wires.jsonl"
    registry.register([record], registry_path)
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "registry")

    result = registry.verify(
        registry_path, "HEAD", repo, repo, [Path("h-mad/tests")]
    )

    assert result["verdict"] == "PASS"
    assert result["verified"] == 1
    assert result["missing"] == 0


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


def test_changed_files_uses_name_status_and_keeps_renames(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    for name, text in {
        "added.py": "x = 1\n", "deleted.py": "x = 1\n", "kept.py": "x = 2\n",
        "old.py": "x = 3\n" * 10,
    }.items():
        (repo / name).write_text(text, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "brandnew.py").write_text("x = 9\n", encoding="utf-8")
    (repo / "added.py").write_text("x = 4\n", encoding="utf-8")
    (repo / "deleted.py").unlink()
    (repo / "kept.py").write_text("x = 5\n", encoding="utf-8")
    (repo / "old.py").rename(repo / "new.py")
    (repo / "new.py").write_text("x = 3\n" * 10 + "y = 6\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "head")
    result = registry.changed_files(base, repo)
    assert (None, "brandnew.py") in result
    assert ("kept.py", "kept.py") in result
    assert ("old.py", "new.py") in result
    assert all(head != "deleted.py" for _, head in result)


def test_ast_targets_are_structural_and_ignore_reindenting() -> None:
    source = "import json\nfrom pkg import thing\n\ndef f():\n    return pkg.call(thing(x))\n"
    assert registry.ast_targets(source) == {"json", "pkg", "thing", "pkg.call"}
    wrapped = "import json\nfrom pkg import thing\n\ndef f():\n    return pkg.call(\n        thing(x)\n    )\n"
    assert registry.ast_targets(source) == registry.ast_targets(wrapped)


def test_challenge_without_boundaries_is_not_compared(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "module.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "module.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "head")
    result = registry.challenge(base, repo / "plan.md", repo / "boundaries.json", repo / "ack.md", repo)
    assert result["token"] == "WIRECHALLENGE: NOT_COMPARED reason=no_boundaries"


def test_challenge_reports_no_production_diff_as_not_compared(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "module.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_module.py").write_text("def test_old(): pass\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "tests" / "test_module.py").write_text(
        "import module\n\ndef test_new():\n    module.changed()\n", encoding="utf-8"
    )
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "head")
    boundaries = tmp_path / "boundaries.json"
    boundaries.write_text(json.dumps({"module.py": "engine"}), encoding="utf-8")

    result = registry.challenge(base, tmp_path / "plan.md", boundaries, tmp_path / "ack.md", repo)

    assert result["token"] == "WIRECHALLENGE: NOT_COMPARED reason=no_production_diff"
    assert "challenges=0" not in result["token"]


def test_challenge_exempts_a_wiring_claim_with_a_cross_boundary_call(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "caller.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "callee.py").write_text("def run(): pass\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "caller.py").write_text("import callee\n\ndef call():\n    callee.run()\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "head")
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Task 1: connect caller\n**Task shape**: `wiring`\n"
        "**Production file**: `caller.py`\n",
        encoding="utf-8",
    )
    boundaries = tmp_path / "boundaries.json"
    boundaries.write_text(json.dumps({"caller.py": "engine", "callee.py": "tools"}), encoding="utf-8")

    result = registry.challenge(base, plan, boundaries, tmp_path / "ack.md", repo)

    assert result["challenges"] == 0
    assert "challenges=0" in result["token"]
    assert result["unattributed"] == 0


def test_challenge_uses_base_path_for_a_renamed_file_ast_diff(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "old.py").write_text(
        "import callee\n\ndef call():\n    callee.existing()\n", encoding="utf-8"
    )
    (repo / "callee.py").write_text("def existing(): pass\ndef added(): pass\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "old.py").rename(repo / "new.py")
    (repo / "new.py").write_text(
        "import callee\n\ndef call():\n    callee.existing()\n    callee.added()\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "head")
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Task 1: add call\n**Task shape**: `new-behaviour`\n"
        "**Production file**: `new.py`\n",
        encoding="utf-8",
    )
    boundaries = tmp_path / "boundaries.json"
    boundaries.write_text(json.dumps({"new.py": "engine", "callee.py": "tools"}), encoding="utf-8")

    result = registry.challenge(base, plan, boundaries, tmp_path / "ack.md", repo)

    assert result["challenges"] == 1
    assert len(result["details"]) == 1
    assert "callee.added" in result["details"][0]


def test_challenge_ignores_test_file_cross_boundary_calls(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    (repo / "caller.py").write_text("def call(): pass\n", encoding="utf-8")
    (repo / "callee.py").write_text("def run(): pass\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_caller.py").write_text("def test_old(): pass\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "tests" / "test_caller.py").write_text(
        "import callee\n\ndef test_new():\n    callee.run()\n", encoding="utf-8"
    )
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "head")
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Task 1: test call\n**Task shape**: `new-behaviour`\n"
        "**Production file**: `tests/test_caller.py`\n",
        encoding="utf-8",
    )
    boundaries = tmp_path / "boundaries.json"
    boundaries.write_text(
        json.dumps({"tests/test_caller.py": "engine", "callee.py": "tools"}), encoding="utf-8"
    )

    result = registry.challenge(base, plan, boundaries, tmp_path / "ack.md", repo)

    assert result["challenges"] == 0
    assert result["unattributed"] == 0
    assert result["token"] == "WIRECHALLENGE: NOT_COMPARED reason=no_production_diff"


def test_challenge_cli_requires_base(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_wire_registry.py"
    result = subprocess.run([sys.executable, str(script), "challenge"], capture_output=True, text=True)
    assert result.returncode == 2


def test_challenge_cli_is_verdict_neutral(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_wire_registry.py"
    repo = _git_repo(tmp_path)
    (repo / "module.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-m", "base")
    result = subprocess.run([sys.executable, str(script), "challenge", "--base", "HEAD", "--repo", str(repo)], capture_output=True, text=True)
    assert result.returncode == 0


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


def _valid_registry(path: Path, *records: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_trackedness_reports_ignored_and_untracked_with_different_remedies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _git_repo(tmp_path)
    path = repo / ".h-mad" / "wires.jsonl"
    path.parent.mkdir()
    path.write_text("{}\n", encoding="utf-8")

    class Ignored:
        returncode = 0

    class Untracked:
        returncode = 1

    monkeypatch.setattr(
        registry.subprocess, "run",
        lambda command, *args, **kwargs: Ignored() if command[1] == "check-ignore" else Untracked(),
    )
    ignored, ignored_remedy = registry.trackedness(path, repo)
    monkeypatch.setattr(
        registry.subprocess, "run",
        lambda command, *args, **kwargs: Untracked(),
    )
    untracked, untracked_remedy = registry.trackedness(path, repo)
    assert not ignored and not untracked
    assert ignored_remedy != untracked_remedy
    assert "!.h-mad/wires.jsonl" in ignored_remedy
    assert "git add" in untracked_remedy


def test_absent_registry_is_pass_and_skips_trackedness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / ".h-mad" / "wires.jsonl"
    monkeypatch.setattr(registry, "trackedness", lambda *args: pytest.fail("trackedness called"))
    result = registry.verify(path, "HEAD", tmp_path, tmp_path)
    assert result["verdict"] == "PASS"
    assert result["registered"] == 0


@pytest.mark.parametrize("field", ["broken", "missing", "unverified_renames", "undeclared_removals"])
def test_each_failure_count_drives_fail_and_is_in_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path, _entry())
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [])
    monkeypatch.setattr(registry, "collect", lambda *args: set())
    if field == "broken":
        monkeypatch.setattr(registry, "collect", lambda *args: {"test_pin"})
        monkeypatch.setattr(registry, "run_pins", lambda *args: ([], [_entry()]))
    elif field == "missing":
        monkeypatch.setattr(registry, "run_pins", lambda *args: ([], []))
    elif field == "unverified_renames":
        renamed = _entry(status="removed", removal_provenance="renamed", removed_by_feature="x", successor_pin="gone")
        registry.load(path)
        path.write_text(json.dumps(renamed) + "\n", encoding="utf-8")
    else:
        base = _entry(id="old")
        monkeypatch.setattr(registry, "load_base", lambda *args: [base])
    result = registry.verify(path, "HEAD", tmp_path, tmp_path)
    assert result["verdict"] == "FAIL"
    assert result[field] > 0
    assert f"{field}={result[field]}" in result["token"]


def test_active_base_record_absent_at_head_is_an_undeclared_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path)
    active = _entry(id="active-base")
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [active])
    monkeypatch.setattr(registry, "collect", lambda *args: set())

    result = registry.verify(path, "HEAD", tmp_path, tmp_path)

    assert result["undeclared_removals"] == 1
    assert result["verdict"] == "FAIL"
    assert "step5f:undeclared_removal:active-base" in capsys.readouterr().out


def test_tombstoned_base_record_absent_at_head_is_not_an_undeclared_removal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path)
    tombstone = _entry(
        id="declared-tombstone", status="removed",
        removal_provenance="pinned-a-defect", removed_by_feature="fix",
    )
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [tombstone])
    monkeypatch.setattr(registry, "collect", lambda *args: set())

    result = registry.verify(path, "HEAD", tmp_path, tmp_path)

    output = capsys.readouterr().out
    assert result["undeclared_removals"] == 0
    assert result["verdict"] == "PASS"
    assert "step5f:" not in output
    assert "declared-tombstone" not in output


def test_only_active_record_drives_mixed_base_removal_count_and_halt_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path)
    active = _entry(id="active-base")
    tombstone = _entry(
        id="declared-tombstone", status="removed",
        removal_provenance="pinned-a-defect", removed_by_feature="fix",
    )
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [active, tombstone])
    monkeypatch.setattr(registry, "collect", lambda *args: set())

    result = registry.verify(path, "HEAD", tmp_path, tmp_path)

    output = capsys.readouterr().out
    assert result["undeclared_removals"] == 1
    assert [record["id"] for record in result["undeclared_removal_records"]] == ["active-base"]
    assert "step5f:undeclared_removal:active-base" in output
    assert "step5f:undeclared_removal:declared-tombstone" not in output


def test_untracked_broken_registry_keeps_counts_and_detail_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "wires.jsonl"
    bad = _entry(id="bad", pin="test_bad")
    _valid_registry(path, bad)
    monkeypatch.setattr(registry, "trackedness", lambda *args: (False, "git add wires.jsonl"))
    monkeypatch.setattr(registry, "load_base", lambda *args: [])
    monkeypatch.setattr(registry, "collect", lambda *args: {bad["pin"]})
    monkeypatch.setattr(registry, "run_pins", lambda *args: ([], [bad]))
    result = registry.verify(path, "HEAD", tmp_path, tmp_path)
    assert result["verdict"] == "UNTRACKED"
    assert result["registered"] == 1 and result["broken"] == 1
    assert "step5f:wire_regression:bad" in capsys.readouterr().out


@pytest.mark.parametrize("reason, record", [
    ("step5f:wire_regression:bad", _entry(id="bad")),
    ("step5f:wire_pin_missing:missing", _entry(id="missing", pin="gone")),
    ("step5f:undeclared_removal:removed", _entry(id="removed")),
    ("step5f:unverified_rename:renamed", _entry(id="renamed", status="removed", removal_provenance="renamed", removed_by_feature="x", successor_pin="gone")),
])
def test_fail_drivers_emit_named_halt_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], reason: str, record: dict
) -> None:
    path = tmp_path / "wires.jsonl"
    if record["id"] == "removed":
        _valid_registry(path)
    else:
        _valid_registry(path, record)
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "collect", lambda *args: set())
    monkeypatch.setattr(registry, "run_pins", lambda *args: ([], [record]) if record["id"] == "bad" else ([], []))
    monkeypatch.setattr(registry, "load_base", lambda *args: [record] if record["id"] == "removed" else [])
    registry.verify(path, "HEAD", tmp_path, tmp_path)
    assert reason in capsys.readouterr().out


def test_main_missing_base_is_exit_2_and_verdicts_are_exit_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _git_repo(tmp_path)
    path = repo / "wires.jsonl"
    assert registry.main(["verify", "--registry", str(path)]) == 2
    _valid_registry(path)
    _git(repo, "add", ".")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "registry")
    assert registry.main([
        "verify", "--registry", str(path), "--base", "HEAD", "--rootdir", str(tmp_path),
        "--repo", str(repo), "--testpath", ".",
    ]) == 0
    assert "WIREREG:" in capsys.readouterr().out


def test_main_collection_failure_is_cannot_judge_exit_2_not_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path, _entry())
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [])
    monkeypatch.setattr(
        registry.subprocess,
        "run",
        lambda *args, **kwargs: type(
            "Result", (), {
                "stdout": "",
                "stderr": "ModuleNotFoundError: No module named pytest\n",
                "returncode": 1,
            }
        )(),
    )

    exit_code = registry.main(
        ["verify", "--registry", str(path), "--base", "HEAD", "--rootdir", str(tmp_path), "--repo", str(tmp_path)]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "[H-MAD]" in output
    assert "WIREREG: FAIL" not in output
