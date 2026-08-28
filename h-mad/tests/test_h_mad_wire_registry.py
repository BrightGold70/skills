"""RED tests for the Phase-5d wire registry schema and runtime read-back."""

import json
import ast
import re
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


def _section(text: str, heading: str) -> str:
    """Return a named Markdown section, bounded by the next same/higher heading."""
    match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)
    assert match, f"missing section {heading!r}"
    level = len(match.group("marks"))
    end = re.search(rf"(?m)^#{{1,{level}}} ", text[match.end():])
    body_end = match.end() + end.start() if end else len(text)
    return text[match.end():body_end]


def _skill_text() -> str:
    return (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def _emitted_halt_reasons() -> set[str]:
    source = (SCRIPTS / "h_mad_wire_registry.py").read_text(encoding="utf-8")
    ast.parse(source)  # Ensure extraction is against valid executable source.
    # The three pin-bearing reasons emit one line PER offending pin, so they
    # interpolate `{label}` from pin_labels(); the other two still name the
    # record as a whole. Both placeholders canonicalise to the same shape --
    # the `#<pin>` suffix a multi-pin record adds is documented as prose, not
    # as a separate token, so this set comparison stays exact.
    emitted = set(re.findall(
        r"step5f:(?:wire_regression|wire_pin_missing|wire_pin_ambiguous):\{label\}"
        r"|step5f:(?:undeclared_removal|unverified_rename):\{_record_label\(record\)\}"
        r"|step5f:registry_untracked",
        source,
    ))
    return {
        value.replace("{_record_label(record)}", "<feature>::<id>").replace("{label}", "<feature>::<id>")
        for value in emitted
    }


def _documented_halt_reasons(text: str) -> set[str]:
    return set(re.findall(r"step5f:(?:wire_regression|wire_pin_missing|wire_pin_ambiguous|undeclared_removal|unverified_rename):<feature>::<id>|step5f:registry_untracked", text))


def test_skill_phase5b_documents_featured_wire_registration_and_executable_flags() -> None:
    phase5 = _section(_skill_text(), "Phase 5 (Implementation) sub-steps")
    line = next(line for line in phase5.splitlines() if "h_mad_wire_pin_gate.py" in line)
    assert "--feature <feature>" in line
    assert ".h-mad/wires.jsonl" in phase5
    assert "auto-register" in phase5 and "passing `wiring`" in phase5

    gate = ast.parse((SCRIPTS / "h_mad_wire_pin_gate.py").read_text(encoding="utf-8"))
    flags = {
        option.value
        for node in ast.walk(gate)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        for option in node.args
        if isinstance(option, ast.Constant) and isinstance(option.value, str) and option.value.startswith("--")
    }
    assert "--feature" in flags


def test_skill_phase5f_documents_reverification_and_warning_only_challenge() -> None:
    phase5 = _section(_skill_text(), "Phase 5 (Implementation) sub-steps")
    assert "h_mad_wire_registry.py verify --base <5c sha>" in phase5
    assert "challenge" in phase5
    assert "--rootdir" in phase5 and "--testpath" in phase5
    assert "--testpath <project-test-root>" in phase5
    assert "collectable test root" in phase5
    assert "warning-only" in phase5 and "verdict-neutral" in phase5


def test_skill_documents_exactly_all_registry_halt_reasons() -> None:
    assert _documented_halt_reasons(_skill_text()) == _emitted_halt_reasons()


def test_skill_inventory_lists_wire_registry_helper() -> None:
    inventory = _section(_skill_text(), "Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)")
    assert "h_mad_wire_registry.py" in inventory


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
    resolving, missing, ambiguous, unverified = registry.partition(
        records, {"tests/test_wire.py::test_present"}
    )
    assert [record["id"] for record in resolving] == ["wire-1"]
    assert resolving[0]["pin"] == "test_present"
    assert resolving[0]["node_id"] == "tests/test_wire.py::test_present"
    assert [record["id"] for record in missing] == ["wire-2"]
    assert ambiguous == []
    assert unverified == []


def test_partition_does_not_report_removed_pin_as_missing() -> None:
    tombstone = _entry(
        status="removed", removal_provenance="pinned-a-defect", removed_by_feature="fix"
    )
    assert registry.partition([tombstone], set()) == ([], [], [], [])


def test_partition_resolves_present_rename_and_unverifies_absent_rename() -> None:
    present = _entry(
        id="old-present", status="removed", removal_provenance="renamed",
        removed_by_feature="rename", successor_pin="test_new",
    )
    absent = _entry(
        id="old-absent", status="removed", removal_provenance="renamed",
        removed_by_feature="rename", successor_pin="test_gone",
    )
    resolving, missing, ambiguous, unverified = registry.partition(
        [present, absent], {"tests/test_wire.py::test_new"}
    )
    assert [(record["id"], record["pin"]) for record in resolving] == [("old-present", "test_new")]
    assert resolving[0]["node_id"] == "tests/test_wire.py::test_new"
    assert missing == []
    assert ambiguous == []
    assert [record["id"] for record in unverified] == ["old-absent"]


def test_partition_is_pure_without_subprocess_or_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: pytest.fail("subprocess"))
    records = [_entry(pin="test_present")]
    resolving = registry.partition(records, {"tests/test_wire.py::test_present"})[0]
    assert [record["id"] for record in resolving] == ["wire-1"]


def test_partition_reports_ambiguous_active_pin_without_resolving_or_missing() -> None:
    record = _entry(pin="test_same_name")
    resolving, missing, ambiguous, unverified = registry.partition(
        [record],
        {
            "tests/test_alpha.py::test_same_name",
            "tests/test_beta.py::test_same_name",
        },
    )
    assert resolving == []
    assert missing == []
    assert [item["id"] for item in ambiguous] == ["wire-1"]
    assert unverified == []


def test_partition_renamed_tombstone_reports_ambiguous_successor_pin() -> None:
    record = _entry(
        id="old-ambiguous", status="removed", removal_provenance="renamed",
        removed_by_feature="rename", successor_pin="test_new_name",
    )
    resolving, missing, ambiguous, unverified = registry.partition(
        [record],
        {
            "tests/test_alpha.py::test_new_name",
            "tests/test_beta.py::test_new_name",
        },
    )
    assert resolving == []
    assert missing == []
    assert [item["id"] for item in ambiguous] == ["old-ambiguous"]
    assert unverified == []


def test_partition_does_not_resolve_pin_that_is_suffix_of_longer_test_name() -> None:
    record = _entry(pin="test_foo")
    resolving, missing, ambiguous, unverified = registry.partition(
        [record], {"tests/test_wire.py::test_foo_bar"}
    )
    assert resolving == []
    assert [item["id"] for item in missing] == ["wire-1"]
    assert ambiguous == []
    assert unverified == []


def test_partition_requires_the_node_id_segment_delimiter() -> None:
    record = _entry(pin="wire")
    resolving, missing, ambiguous, unverified = registry.partition(
        [record], {"h-mad/tests/test_wire.py::test_wire"}
    )
    assert resolving == []
    assert [item["id"] for item in missing] == ["wire-1"]
    assert ambiguous == []
    assert unverified == []


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


def test_collect_then_partition_resolves_bare_registered_pin_in_real_throwaway_repo(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    test_path = repo / "h-mad" / "tests" / "test_wire.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_registered_wire():\n    assert True\n", encoding="utf-8")

    collected = registry.collect(repo, [Path("h-mad/tests")])
    resolving, missing, ambiguous, unverified = registry.partition(
        [_entry(pin="test_registered_wire")], collected
    )

    assert [record["id"] for record in resolving] == ["wire-1"]
    assert resolving[0]["node_id"] == "h-mad/tests/test_wire.py::test_registered_wire"
    assert missing == []
    assert ambiguous == []
    assert unverified == []


def test_run_pins_resolves_a_repo_relative_pin_in_a_real_throwaway_repo(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    test_path = repo / "h-mad" / "tests" / "test_wire.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_registered_wire():\n    assert True\n", encoding="utf-8")
    record = _entry(pin="h-mad/tests/test_wire.py::test_registered_wire")

    verified, broken = registry.run_pins([record], repo)

    assert [item["id"] for item in verified] == ["wire-1"]
    assert broken == []


def test_run_pins_invokes_pytest_with_resolved_node_id_not_bare_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []

    class Result:
        stdout = "PASSED tests/test_wire.py::test_registered_wire\n"
        returncode = 0

    def fake_run(command: list[str], *args: object, **kwargs: object) -> Result:
        seen.append(command)
        return Result()

    monkeypatch.setattr(registry.subprocess, "run", fake_run)
    record = _entry(
        pin="test_registered_wire",
        node_id="tests/test_wire.py::test_registered_wire",
    )

    verified, broken = registry.run_pins([record], tmp_path)

    assert seen == [[
        sys.executable, "-m", "pytest", "-q", "-rA", "-vv",
        "tests/test_wire.py::test_registered_wire",
    ]]
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


def test_verify_reports_ambiguous_pin_in_token_driver_and_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "wires.jsonl"
    record = _entry(id="ambiguous", pin="test_same_name")
    _valid_registry(path, record)
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [])
    monkeypatch.setattr(
        registry,
        "collect",
        lambda *args: {
            "tests/test_alpha.py::test_same_name",
            "tests/test_beta.py::test_same_name",
        },
    )
    monkeypatch.setattr(registry, "run_pins", lambda *args: ([], []))

    result = registry.verify(path, "HEAD", tmp_path, tmp_path, [Path("tests")])

    assert result["verdict"] == "FAIL"
    assert result["ambiguous"] == 1
    assert "ambiguous=1" in result["token"]
    assert "step5f:wire_pin_ambiguous:regression-provenance-ledger::ambiguous" in capsys.readouterr().out


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


def test_run_pins_fails_closed_for_a_pin_absent_from_pytest_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Result:
        stdout = ""
        returncode = 0

    monkeypatch.setattr(registry.subprocess, "run", lambda *args, **kwargs: Result())
    record = _entry(pin="tests/test_unknown.py::test_unknown")
    assert registry.run_pins([record], tmp_path) == ([], [record])
    output = capsys.readouterr().out
    assert "ABSENT FROM PYTEST OUTPUT" in output
    assert "INTERNAL INCONSISTENCY" not in output


def test_run_pins_fails_closed_for_real_error_skip_and_xfail_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _git_repo(tmp_path)
    test_path = repo / "tests" / "test_wire.py"
    test_path.parent.mkdir()
    test_path.write_text(
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def exploding_fixture():\n"
        "    raise RuntimeError('setup exploded')\n\n"
        "def test_error(exploding_fixture):\n"
        "    assert False\n\n"
        "@pytest.mark.skip(reason='deliberately skipped')\n"
        "def test_skipped():\n"
        "    assert False\n\n"
        "@pytest.mark.xfail(reason='deliberately expected failure')\n"
        "def test_xfailed():\n"
        "    assert False\n",
        encoding="utf-8",
    )
    records = [
        _entry(id="error", pin="tests/test_wire.py::test_error"),
        _entry(id="skipped", pin="tests/test_wire.py::test_skipped"),
        _entry(id="xfailed", pin="tests/test_wire.py::test_xfailed"),
    ]

    verified, broken = registry.run_pins(records, repo)

    assert verified == []
    assert [record["id"] for record in broken] == ["error", "skipped", "xfailed"]
    output = capsys.readouterr().out
    assert "ERROR" in output and records[0]["pin"] in output
    assert "SKIPPED" in output and records[1]["pin"] in output
    assert "XFAIL" in output and records[2]["pin"] in output

    registry_path = repo / "wires.jsonl"
    _valid_registry(registry_path, *records)
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [])
    result = registry.verify(registry_path, "HEAD", repo, repo, [Path("tests")])
    assert result["verdict"] == "FAIL"
    output = capsys.readouterr().out
    assert all(f"step5f:wire_regression:{registry._record_label(record)}" in output for record in records)


def test_register_cli_writes_requested_record(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "custom" / "wires.jsonl"
    assert registry.main([
        "register", "--registry", str(path), "--id", "cli-wire",
        "--caller", "engine.run", "--callee", "tools.measure",
        "--pin", "tests/test_wire.py::test_wire", "--feature", "feature-x",
    ]) == 0
    stored = registry.load(path)
    assert stored[0]["id"] == "cli-wire"
    assert stored[0]["owning_feature"] == "feature-x"
    assert "registered=1" in capsys.readouterr().out


def test_register_cli_requires_all_record_fields(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        registry.main(["register", "--registry", str(tmp_path / "wires.jsonl")])
    assert exc.value.code == 2


def test_verify_uses_custom_registry_path_for_base_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _git_repo(tmp_path)
    path = repo / "custom" / "wires.jsonl"
    _valid_registry(path, _entry())
    _git(repo, "add", ".")
    base = _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "registry")
    seen: list[str] = []

    def fake_load_base(sha: str, base_path: str, base_repo: Path) -> list[dict]:
        seen.append(base_path)
        return []

    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", fake_load_base)
    monkeypatch.setattr(registry, "collect", lambda *args: set())
    monkeypatch.setattr(registry, "run_pins", lambda *args: ([], []))

    registry.verify(path, base, repo, repo, [Path("tests")])

    assert seen == ["custom/wires.jsonl"]


def test_verify_threads_selected_python_to_collect_and_run_pins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path, _entry(pin="test_registered_wire"))
    monkeypatch.setattr(registry, "trackedness", lambda *args: (True, None))
    monkeypatch.setattr(registry, "load_base", lambda *args: [])
    calls: list[tuple[str, Path, tuple[Path, ...], str]] = []

    def fake_collect(rootdir: Path, testpaths: tuple[Path, ...], python: str = sys.executable) -> set[str]:
        calls.append(("collect", rootdir, tuple(testpaths), python))
        return {"tests/test_wire.py::test_registered_wire"}

    def fake_run_pins(records: list[dict], rootdir: Path, python: str = sys.executable) -> tuple[list[dict], list[dict]]:
        calls.append(("run_pins", rootdir, tuple(), python))
        return records, []

    monkeypatch.setattr(registry, "collect", fake_collect)
    monkeypatch.setattr(registry, "run_pins", fake_run_pins)

    result = registry.verify(
        path, "HEAD", tmp_path, tmp_path, [Path("tests")], python="/opt/project/python"
    )

    assert result["verdict"] == "PASS"
    assert calls == [
        ("collect", tmp_path, (Path("tests"),), "/opt/project/python"),
        ("run_pins", tmp_path, tuple(), "/opt/project/python"),
    ]


def test_collect_and_run_pins_use_selected_python_and_collect_error_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []

    class CollectFailure:
        stdout = ""
        stderr = "ModuleNotFoundError: No module named pytest\n"
        returncode = 1

    class RunSuccess:
        stdout = "PASSED tests/test_wire.py::test_registered_wire\n"
        stderr = ""
        returncode = 0

    def collect_fails(command: list[str], *args: object, **kwargs: object) -> CollectFailure:
        seen.append(command)
        return CollectFailure()

    monkeypatch.setattr(registry.subprocess, "run", collect_fails)
    with pytest.raises(registry.RegistryError) as excinfo:
        registry.collect(tmp_path, [Path("tests")], python="/opt/project/python")
    assert seen[0][:3] == ["/opt/project/python", "-m", "pytest"]
    assert "/opt/project/python" in str(excinfo.value)

    def run_succeeds(command: list[str], *args: object, **kwargs: object) -> RunSuccess:
        seen.append(command)
        return RunSuccess()

    monkeypatch.setattr(registry.subprocess, "run", run_succeeds)
    verified, broken = registry.run_pins(
        [_entry(pin="test_registered_wire", node_id="tests/test_wire.py::test_registered_wire")],
        tmp_path,
        python="/opt/project/python",
    )
    assert seen[1][:3] == ["/opt/project/python", "-m", "pytest"]
    assert [record["id"] for record in verified] == ["wire-1"]
    assert broken == []


def test_main_verify_accepts_python_option_and_threads_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "wires.jsonl"
    _valid_registry(path)
    seen: list[str] = []

    def fake_verify(*args: object, **kwargs: object) -> dict:
        seen.append(str(kwargs["python"]))
        return {
            "verdict": "PASS",
            "registered": 0,
            "verified": 0,
            "broken": 0,
            "missing": 0,
            "ambiguous": 0,
            "unverified_renames": 0,
            "undeclared_removals": 0,
            "token": "WIREREG: PASS registered=0 verified=0 broken=0 missing=0 ambiguous=0 unverified_renames=0 undeclared_removals=0",
            "remedy": None,
        }

    monkeypatch.setattr(registry, "verify", fake_verify)

    assert registry.main([
        "verify", "--registry", str(path), "--base", "HEAD", "--rootdir", str(tmp_path),
        "--repo", str(tmp_path), "--python", "/opt/project/python",
    ]) == 0
    assert seen == ["/opt/project/python"]


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
    assert "step5f:undeclared_removal:regression-provenance-ledger::active-base" in capsys.readouterr().out


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
    assert "step5f:undeclared_removal:regression-provenance-ledger::active-base" in output
    assert "step5f:undeclared_removal:regression-provenance-ledger::declared-tombstone" not in output


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
    assert "step5f:wire_regression:regression-provenance-ledger::bad" in capsys.readouterr().out


@pytest.mark.parametrize("reason, record", [
    ("step5f:wire_regression:regression-provenance-ledger::bad", _entry(id="bad")),
    ("step5f:wire_pin_missing:regression-provenance-ledger::missing", _entry(id="missing", pin="gone")),
    ("step5f:undeclared_removal:regression-provenance-ledger::removed", _entry(id="removed")),
    ("step5f:unverified_rename:regression-provenance-ledger::renamed", _entry(id="renamed", status="removed", removal_provenance="renamed", removed_by_feature="x", successor_pin="gone")),
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


class TestFeatureScopedKey:
    """J43 — `id` is `"Task N"`, and every impl-plan numbers tasks from 1.

    Keyed on the bare `id`, `register` upserts one feature's wire over another's
    and `compare` then keys on the same bare `id`, so the successor MASKS the
    eviction: `step5f:undeclared_removal` structurally cannot fire for it. The
    record schema requires `status`/`removal_provenance`/`removed_by_feature`
    for a *declared* removal — the entire apparatus the upsert walked around.

    Measured over the full history of this repo's `.h-mad/wires.jsonl` before the
    fix: 7 distinct `(owning_feature, id)` pairs ever registered, 6 at HEAD, and
    the missing one — `audit-cycle-verb :: Task 4` — was invisible to `compare`
    because `anchor-precheck-phase-5e-wiring :: Task 4` occupied its id. The loss
    was also unrestorable: re-registering it evicted the successor, because the
    registry could hold exactly one `"Task 4"` across all features, ever.
    """

    def test_same_id_under_a_different_feature_does_not_evict(self, tmp_path: Path) -> None:
        path = tmp_path / "wires.jsonl"
        registry.register([_entry(id="Task 4", owning_feature="feature-a")], path)
        result = registry.register([_entry(id="Task 4", owning_feature="feature-b")], path)
        assert len(result) == 2
        assert {(r["owning_feature"], r["id"]) for r in result} == {
            ("feature-a", "Task 4"), ("feature-b", "Task 4"),
        }

    def test_same_id_under_the_same_feature_still_updates_in_place(self, tmp_path: Path) -> None:
        """The accept direction. Mutation testing only proves the reject one, and
        a key that never matches would pass every test above while turning the
        registry into an append-only log of stale duplicates."""
        path = tmp_path / "wires.jsonl"
        registry.register([_entry(id="Task 4", owning_feature="feature-a")], path)
        result = registry.register(
            [_entry(id="Task 4", owning_feature="feature-a", callee="tools.other")], path
        )
        assert len(result) == 1
        assert result[0]["callee"] == "tools.other"

    def test_the_evicted_record_is_restorable_alongside_its_successor(self, tmp_path: Path) -> None:
        """The property that made the original loss permanent, not just silent."""
        path = tmp_path / "wires.jsonl"
        registry.register([_entry(id="Task 4", owning_feature="successor")], path)
        result = registry.register([_entry(id="Task 4", owning_feature="evicted")], path)
        assert len(result) == 2

    def test_compare_reports_a_removal_masked_by_the_same_id_at_head(self) -> None:
        base = _entry(id="Task 4", owning_feature="feature-a")
        head = _entry(id="Task 4", owning_feature="feature-b")
        assert registry.compare([base], [head]) == [base]

    def test_compare_does_not_report_a_record_still_present_under_its_own_feature(self) -> None:
        record = _entry(id="Task 4", owning_feature="feature-a")
        other = _entry(id="Task 4", owning_feature="feature-b")
        assert registry.compare([record], [record, other]) == []

    def test_halt_reason_names_the_feature_so_two_removals_are_distinguishable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """Once two features may each own a `Task 4`, a halt reason carrying only
        the bare id names neither of them."""
        assert registry._record_label(_entry(id="Task 4", owning_feature="feature-a")) == (
            "feature-a::Task 4"
        )
        assert registry._record_label(_entry(id="Task 4", owning_feature="feature-b")) == (
            "feature-b::Task 4"
        )


def test_live_registry_still_holds_the_wire_that_was_silently_evicted() -> None:
    """J43's measured casualty, pinned so a re-eviction is a test failure.

    A later feature may legitimately retire this wire — but only by declaring it
    with a tombstone, which is exactly the path the id-keyed upsert bypassed.
    """
    live = Path(__file__).resolve().parents[2] / ".h-mad" / "wires.jsonl"
    records = [json.loads(line) for line in live.read_text(encoding="utf-8").splitlines() if line.strip()]
    matching = [
        r for r in records
        if r["owning_feature"] == "audit-cycle-verb" and r["id"] == "Task 4"
    ]
    assert matching, "audit-cycle-verb::Task 4 is absent — it was evicted, not declared removed"
    assert matching[0]["pin"] == "test_fail_in_either_pass_fails_cycle"


class TestMultiPin:
    """A wiring task with N call sites needs N pins on ONE record.

    Before this, the registry keyed one row per task id and matched `pin`
    exactly with no list form, so a task wiring three sites could only register
    site 1; sites 2 and 3 were enforced by ACs and the wire-scoped revert, never
    by the registry. `pin` now takes a string (unchanged) or a list.
    """

    def test_a_list_pin_validates(self) -> None:
        record = _entry(pin=["test_site_one", "test_site_two"], registered_ts="t")
        assert registry.validate_record(record) is record

    def test_a_string_pin_still_validates(self) -> None:
        assert registry.validate_record(_entry(pin="test_site_one", registered_ts="t"))

    def test_an_empty_pin_list_is_rejected(self) -> None:
        with pytest.raises(registry.RegistryError, match="pin"):
            registry.validate_record(_entry(pin=[], registered_ts="t"))

    def test_a_non_string_pin_element_is_rejected(self) -> None:
        with pytest.raises(registry.RegistryError, match="pin"):
            registry.validate_record(_entry(pin=["test_ok", 7], registered_ts="t"))

    def test_a_duplicate_pin_is_rejected(self) -> None:
        with pytest.raises(registry.RegistryError, match="pin"):
            registry.validate_record(_entry(pin=["test_same", "test_same"], registered_ts="t"))

    def test_every_pin_must_resolve_for_the_record_to_resolve(self) -> None:
        record = _entry(pin=["test_site_one", "test_site_two"])
        collected = {"t/a.py::test_site_one", "t/b.py::test_site_two"}
        resolving, missing, ambiguous, _ = registry.partition([record], collected)
        assert len(resolving) == 1, (missing, ambiguous)
        assert resolving[0]["node_ids"] == [
            "t/a.py::test_site_one", "t/b.py::test_site_two"
        ]

    def test_one_unresolved_pin_makes_the_whole_record_missing(self) -> None:
        record = _entry(pin=["test_site_one", "test_site_two"])
        resolving, missing, ambiguous, _ = registry.partition(
            [record], {"t/a.py::test_site_one"}
        )
        assert not resolving, "a record is only as verified as its weakest pin"
        assert len(missing) == 1 and not ambiguous

    def test_an_ambiguous_pin_outranks_a_missing_sibling(self) -> None:
        record = _entry(pin=["test_gone", "test_dup"])
        collected = {"t/a.py::test_dup", "t/b.py::test_dup"}
        resolving, missing, ambiguous, _ = registry.partition([record], collected)
        assert not resolving
        assert len(ambiguous) == 1 and not missing, (
            "a pin naming more than one test is the stronger defect: it must be "
            "qualified before the record can be judged at all"
        )

    def test_a_halt_reason_names_the_offending_pin_on_a_multi_pin_record(
        self, tmp_path: Path
    ) -> None:
        """The J43 lesson, one level down: two failures on one record must differ.

        `<feature>::<id>` alone would emit the same line twice and the author
        could not tell which site broke.
        """
        record = _entry(pin=["test_gone_one", "test_gone_two"], id="Task 4")
        _, missing, _, _ = registry.partition([record], set())
        assert len(missing) == 1
        labels = registry.pin_labels(missing[0], registry.unresolved_pins(missing[0], set()))
        assert labels == [
            "regression-provenance-ledger::Task 4#test_gone_one",
            "regression-provenance-ledger::Task 4#test_gone_two",
        ], labels

    def test_a_single_pin_label_is_unchanged(self) -> None:
        """Every existing halt-reason string must stay byte-identical."""
        record = _entry(pin="test_gone", id="Task 4")
        labels = registry.pin_labels(record, ["test_gone"])
        assert labels == ["regression-provenance-ledger::Task 4"], labels

    def test_register_stores_one_pin_as_a_bare_string(self, tmp_path: Path) -> None:
        """The on-disk shape of a single-pin record must not change."""
        path = tmp_path / "wires.jsonl"
        registry.register([_entry(pin="test_only")], path)
        assert json.loads(path.read_text().splitlines()[0])["pin"] == "test_only"

    def test_register_round_trips_a_list_pin(self, tmp_path: Path) -> None:
        path = tmp_path / "wires.jsonl"
        registry.register([_entry(pin=["test_a", "test_b"])], path)
        assert json.loads(path.read_text().splitlines()[0])["pin"] == ["test_a", "test_b"]

    def test_cli_register_accepts_a_repeated_pin_flag(self, tmp_path: Path) -> None:
        path = tmp_path / "wires.jsonl"
        rc = registry.main([
            "register", "--registry", str(path), "--id", "Task 4",
            "--caller", "a.b", "--callee", "c.d",
            "--pin", "test_a", "--pin", "test_b", "--feature", "f",
        ])
        assert rc == 0
        assert json.loads(path.read_text().splitlines()[0])["pin"] == ["test_a", "test_b"]

    def test_cli_register_with_one_pin_still_stores_a_string(self, tmp_path: Path) -> None:
        path = tmp_path / "wires.jsonl"
        registry.main([
            "register", "--registry", str(path), "--id", "Task 4",
            "--caller", "a.b", "--callee", "c.d", "--pin", "test_a", "--feature", "f",
        ])
        assert json.loads(path.read_text().splitlines()[0])["pin"] == "test_a"

    def test_a_renamed_tombstone_takes_a_list_successor(self) -> None:
        record = _entry(
            pin=["test_old_one", "test_old_two"], status="removed",
            removal_provenance="renamed", removed_by_feature="f",
            successor_pin=["test_new_one", "test_new_two"], registered_ts="t",
        )
        assert registry.validate_record(record) is record
        collected = {"t/a.py::test_new_one", "t/b.py::test_new_two"}
        resolving, _, _, unverified = registry.partition([record], collected)
        assert len(resolving) == 1 and not unverified


def test_skill_documents_the_multi_pin_contract() -> None:
    """The list form and its `#<pin>` halt-reason suffix must be findable in SKILL.md."""
    phase5 = _section(_skill_text(), "Phase 5 (Implementation) sub-steps")
    assert "may be a single test or a LIST" in phase5
    assert "step5f:wire_pin_missing:<feature>::<id>#<pin>" in phase5
    assert "EVERY pin passes" in phase5
    assert "Ambiguity outranks absence" in phase5


def test_run_pins_breaks_a_record_when_only_one_of_its_pins_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wire is only as verified as its weakest site.

    Site 1 passing while site 2 regresses must NOT read as a verified wire --
    that is precisely the blindness one pin per record left in place.
    """
    class Result:
        stdout = (
            "PASSED t/a.py::test_site_one\n"
            "FAILED t/b.py::test_site_two\n"
        )
        returncode = 1

    monkeypatch.setattr(registry.subprocess, "run", lambda *a, **k: Result())
    record = _entry(
        pin=["test_site_one", "test_site_two"],
        node_ids=["t/a.py::test_site_one", "t/b.py::test_site_two"],
    )

    verified, broken = registry.run_pins([record], tmp_path)

    assert verified == [] and len(broken) == 1
    assert broken[0]["broken_pins"] == ["t/b.py::test_site_two"], (
        "only the failing site is named, so the author is not sent to re-check "
        "a site that passed"
    )


def test_run_pins_verifies_a_record_only_when_every_pin_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Result:
        stdout = (
            "PASSED t/a.py::test_site_one\n"
            "PASSED t/b.py::test_site_two\n"
        )
        returncode = 0

    monkeypatch.setattr(registry.subprocess, "run", lambda *a, **k: Result())
    record = _entry(
        pin=["test_site_one", "test_site_two"],
        node_ids=["t/a.py::test_site_one", "t/b.py::test_site_two"],
    )

    verified, broken = registry.run_pins([record], tmp_path)
    assert len(verified) == 1 and broken == []
