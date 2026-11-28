"""Git environment, state records and command-directory policy for Phase 5."""
import importlib
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest


PACKAGE = Path(__file__).resolve().parents[1]
GIT_VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES")


@pytest.fixture
def identity(monkeypatch):
    monkeypatch.syspath_prepend(str(PACKAGE / "scripts"))
    return importlib.import_module("h_mad_target_identity")


@pytest.fixture(scope="module")
def hostile():
    result = subprocess.run(
        [str(PACKAGE / "tests/stubs/orca"), "worktree", "set", "comment", "fixture"],
        env={"PATH": os.environ["PATH"], "HMAD_STUB_HOSTILE": "all"},
        capture_output=True, text=True, check=True, timeout=10,
    )
    return json.loads(result.stdout)["result"]["worktree"]["comment"]


@pytest.fixture
def state_path(tmp_path, hostile):
    return tmp_path / (hostile.replace("/", "_") + ".json")


@pytest.mark.parametrize("variable", GIT_VARIABLES)
def test_git_environment_drops_the_four_variables(identity, monkeypatch, variable, hostile):
    monkeypatch.setenv(variable, hostile)
    assert variable not in identity.git_environment()


def test_git_environment_sets_lc_all_c(identity, monkeypatch):
    monkeypatch.setenv("LC_ALL", "POSIX")
    assert identity.git_environment()["LC_ALL"] == "C"


def test_git_environment_leaves_os_environ_alone(identity, monkeypatch, hostile):
    for variable in GIT_VARIABLES:
        monkeypatch.setenv(variable, hostile)
    monkeypatch.setenv("LC_ALL", "POSIX")
    monkeypatch.setenv("HMAD_TEST_VALUE", hostile)
    before = dict(os.environ)
    env = identity.git_environment()
    expected = {key: value for key, value in before.items() if key not in GIT_VARIABLES}
    expected["LC_ALL"] = "C"
    assert env == expected
    env.pop("HMAD_TEST_VALUE")
    assert dict(os.environ) == before


@pytest.mark.parametrize("case", [
    "read", "absent", "unreadable-fifo", "unreadable-unparsable", "not-object",
])
def test_read_state_status(identity, state_path, hostile, case):
    if case == "read":
        data = {"orchestrator_state": {hostile: {"phase": "step5"}}}
        state_path.write_text(json.dumps(data), encoding="utf-8")
        read = identity.read_state(state_path)
        assert (read.path, read.status, read.data) == (str(state_path), "read", data)
        assert read.exception is None
    elif case == "absent":
        read = identity.read_state(state_path)
        assert read.status == "absent"
        assert read.exception is None
        link = state_path.with_suffix(".link")
        link.symlink_to(state_path)
        read = identity.read_state(link)
        assert (read.status, read.error, read.exception) == ("unreadable", "FileNotFoundError", None)
    elif case == "unreadable-fifo":
        os.mkfifo(state_path)
        for path in (state_path, state_path.parent):
            read = identity.read_state(path)
            assert (read.status, read.error, read.exception) == ("unreadable", "not-a-regular-file", None)
    elif case == "unreadable-unparsable":
        deep = state_path.with_suffix(".deep")
        deep.write_text("[" * 1_000_000 + "]" * 1_000_000, encoding="utf-8")
        state_path.write_text(hostile, encoding="utf-8")
        read = identity.read_state(state_path)
        assert (read.status, read.error, read.exception) == ("unreadable", "JSONDecodeError", None)
        read = identity.read_state(deep)
        assert (read.status, read.error) == ("unreadable", "RecursionError")
        assert isinstance(read.exception, RecursionError)
    else:
        malformed = state_path.with_suffix(".map")
        malformed.write_text(json.dumps({"orchestrator_state": [hostile]}), encoding="utf-8")
        state_path.write_text(json.dumps([hostile]), encoding="utf-8")
        read = identity.read_state(state_path)
        assert (read.status, read.error) == ("not-object", "not-an-object")
        assert isinstance(read.exception, AttributeError)
        read = identity.read_state(malformed)
        assert (read.status, read.error, read.exception) == ("not-object", "not-an-object", None)


@pytest.mark.parametrize("case", [
    "step5", "other-phase", "record-not-object", "orchestrator-state-not-object",
])
def test_live_records(identity, state_path, hostile, case):
    first = {"phase": "step5", "note": hostile}
    second = {"phase": "step5", "phase5_stage": "planning"}
    states = {
        "step5": {"z" + hostile: first, "a" + hostile: second},
        "other-phase": {hostile: {"phase": "step4"}},
        "record-not-object": {hostile: [hostile]},
        "orchestrator-state-not-object": [hostile],
    }[case]
    state_path.write_text(json.dumps({"orchestrator_state": states}), encoding="utf-8")
    records = identity.live_records(identity.read_state(state_path))
    if case == "step5":
        assert records == (
            identity.LiveRecord("z" + hostile, str(state_path), first),
            identity.LiveRecord("a" + hostile, str(state_path), second),
        )
    else:
        assert records == ()


@pytest.mark.parametrize("case, gates", [
    ("absent", True), ("null", True), ("planning", False), ("implementing", True),
    ("unknown-string", True), ("non-string", True),
], ids=["absent", "null", "planning", "implementing", "unknown-string", "non-string"])
def test_stage_gates_shell(identity, state_path, hostile, case, gates):
    data = {"phase": "step5"}
    if case != "absent":
        data["phase5_stage"] = {"null": None, "unknown-string": hostile, "non-string": [hostile]}.get(case, case)
    assert identity.stage_gates_shell(identity.LiveRecord(hostile, str(state_path), data)) is gates


def test_every_stage_is_true(identity, state_path, hostile):
    for fields in ({}, {"phase5_stage": "planning"}, {"phase5_stage": hostile}):
        assert identity.every_stage(identity.LiveRecord(hostile, str(state_path), fields)) is True


@pytest.mark.parametrize("case", ["absent", "null", "empty", "number", "list", "object", "string", "decode-raises"])
def test_command_directory(identity, hostile, case):
    key = "Cwd"
    decoded, absent = object(), object()
    decode = Mock(return_value=decoded)
    values = {"null": None, "empty": "", "number": 7, "list": [hostile],
              "object": {"path": hostile}, "string": hostile, "decode-raises": hostile}
    args = {key: values[case]} if case in values else {"workdir": hostile}
    if case == "decode-raises":
        decode.side_effect = RuntimeError(hostile)
    directory = identity.command_directory(args, key, decode, absent)
    if case in ("string", "decode-raises"):
        decode.assert_called_once_with()
    else:
        decode.assert_not_called()
    expected = {"absent": absent, "string": decoded}.get(case, identity.MALFORMED_WORKDIR)
    assert directory is expected


def test_status_is_compared_by_value(identity, hostile):
    assert identity.INACTIVE == identity.Status("inactive", ())
    assert (identity.INACTIVE.value, identity.INACTIVE.applied) == ("inactive", ())
    entries = (hostile, "second")
    for value in ("active", "unknown"):
        status = identity.Status(value, entries)
        assert status.value == value
        assert status.applied == entries


@pytest.mark.parametrize("name", ["read_state"])
def test_path_parameters_accept_str_and_path(identity, name, state_path, hostile):
    data = {"note": hostile}
    state_path.write_text(json.dumps(data), encoding="utf-8")
    reader = getattr(identity, name)
    result = reader(str(state_path))
    assert result == reader(state_path)
    assert (result.path, result.status, result.data) == (str(state_path), "read", data)
