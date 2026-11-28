"""Git environment, state records and command-directory policy for Phase 5."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import Mock

import pytest

from tdd_gate_support import hook_git

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


@pytest.mark.parametrize("name", ["read_state", "checkout_of", "session_checkout"])
def test_path_parameters_accept_str_and_path(identity, name, state_path, hostile, request):
    if name in ("checkout_of", "session_checkout"):
        checkout_path = request.getfixturevalue("checkout_path")
        lookup = getattr(identity, name)
        _init_repo(checkout_path)
        top = identity.canonical_directory(str(checkout_path))
        for spelling in (str(checkout_path), checkout_path):
            result = lookup(spelling)
            assert (result.top, result.answered) == (top, True)
        return
    data = {"note": hostile}
    state_path.write_text(json.dumps(data), encoding="utf-8")
    reader = getattr(identity, name)
    result = reader(str(state_path))
    assert result == reader(state_path)
    assert (result.path, result.status, result.data) == (str(state_path), "read", data)


@pytest.fixture
def checkout_path(tmp_path, hostile, monkeypatch):
    for variable in GIT_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("LC_ALL", "C")
    monkeypatch.setenv("GIT_DISCOVERY_ACROSS_FILESYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    return tmp_path / (hostile.replace("/", "_") + "\r\n")


def _init_repo(path, bare=False):
    options = ["--bare"] if bare else []
    subprocess.run([hook_git(os.environ["PATH"]), "init", "-q", *options, str(path)],
                   check=True, capture_output=True, timeout=10)


def _git_shim(tmp_path, monkeypatch, action=""):
    """Log argv before forwarding to real git or applying the requested failure/delay."""
    real_git = hook_git(os.environ["PATH"])
    directory = tmp_path / "bin"
    directory.mkdir()
    log = tmp_path / "calls.jsonl"
    log.touch()
    shim = directory / "git"
    shim.write_text(
        f"#!{sys.executable}\nimport json, os, sys, time\n"
        f"with open({str(log)!r}, 'a') as calls:\n"
        "    print(json.dumps(sys.argv[1:]), file=calls)\n"
        f"{action}\nos.execv({real_git!r}, [{real_git!r}, *sys.argv[1:]])\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    monkeypatch.setenv("PATH", str(directory) + os.pathsep + os.environ["PATH"])
    return log


NO_REPO = "fatal: not a git repository (or any of the parent directories): .git"


@pytest.mark.parametrize("case", [
    "checkout", "no-work-tree", "message-alone", "no-entry-alone", "inside-valid-dot-git",
    "inside-damaged-dot-git", "bare-repository", "empty-dot-git-directory", "git-missing",
    "git-timeout",
])
def test_checkout_of(identity, checkout_path, tmp_path, monkeypatch, case):
    monkeypatch.setenv("LC_ALL", "C")
    lookup = identity.checkout_of
    root = checkout_path
    root.mkdir()
    path = root
    expected = (None, False)
    if case == "checkout":
        _init_repo(root)
        deepest = root / "child"
        deepest.mkdir()
        alias = tmp_path / "link"
        alias.symlink_to(deepest, target_is_directory=True)
        path = alias / "missing" / "leaf"
        expected = (identity.canonical_directory(str(root)), True)
        log = _git_shim(tmp_path, monkeypatch)
    elif case == "no-work-tree":
        expected = (None, True)
    elif case == "message-alone":
        path = root / "child"
        path.mkdir()
        entry = root / ".git"
        entry.symlink_to(root / "missing")
        _git_shim(tmp_path, monkeypatch, f"sys.stderr.write({NO_REPO!r} + '\\n'); sys.exit(128)")
        answer = lookup(path)
        assert (answer.top, answer.answered) == (None, False), "dangling ancestor .git counts"
        answer = lookup(root)
        assert (answer.top, answer.answered) == (None, False), "dangling .git in the queried directory counts"
        entry.unlink()
        original_lstat = os.lstat

        def lstat(path, *args, **kwargs):
            if os.fspath(path) == str(entry):
                raise PermissionError(path)
            return original_lstat(path, *args, **kwargs)

        monkeypatch.setattr(os, "lstat", lstat)
    elif case == "no-entry-alone":
        # A substring match and a full match at the wrong exit status both fail.
        action = (f"print({NO_REPO!r}, file=sys.stderr)\n"
                  "if os.environ.get('SECOND_EXIT'):\n    sys.exit(1)\n"
                  "print('additional diagnostic', file=sys.stderr)\nsys.exit(128)")
        monkeypatch.delenv("SECOND_EXIT", raising=False)
        _git_shim(tmp_path, monkeypatch, action)
        answer = lookup(path)
        assert (answer.top, answer.answered) == (None, False), "the whole diagnostic must match"
        monkeypatch.setenv("SECOND_EXIT", "1")
    elif case == "inside-valid-dot-git":
        _init_repo(root)
        path = root / ".git" / "objects"
        expected = (identity.canonical_directory(str(root)), True)
    elif case == "inside-damaged-dot-git":
        path = root / ".git" / "objects"
        path.mkdir(parents=True)
    elif case == "bare-repository":
        _init_repo(root, bare=True)
    elif case == "empty-dot-git-directory":
        _init_repo(root)
        path = root / "child"
        (path / ".git").mkdir(parents=True)
        expected = (identity.canonical_directory(str(root)), True)
    elif case == "git-missing":
        _init_repo(root)
        monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    elif case == "git-timeout":
        _init_repo(root)
        log = _git_shim(tmp_path, monkeypatch, "time.sleep(6)")
        run = Mock(wraps=subprocess.run)
        monkeypatch.setattr(subprocess, "run", run)
    started = time.monotonic()
    answer = lookup(path)
    elapsed = time.monotonic() - started
    assert (answer.top, answer.answered) == expected, case
    if case == "checkout":
        args, = map(json.loads, log.read_text().splitlines())
        assert "--no-optional-locks" in args
        assert args[args.index("-C") + 1] == identity.canonical_directory(str(deepest))
        assert args[-2:] == ["rev-parse", "--show-toplevel"]
        canonical = identity.canonical_directory
        refused = []

        def refuse_top(directory):
            if os.fspath(directory) == expected[0]:
                refused.append(directory)
                raise PermissionError(directory)
            return canonical(directory)

        monkeypatch.setattr(identity, "canonical_directory", refuse_top)
        answer = lookup(path)
        assert refused and (answer.top, answer.answered) == (None, False), "git top must be canonicalisable"
    if case == "git-timeout":
        assert run.call_args.kwargs["timeout"] == 2
        assert log.stat().st_size and 1.5 <= elapsed < 4, "git lookup must use its 2 s budget"


@pytest.mark.parametrize("case", ["canonicalisable", "refused-top-level-root"])
def test_session_checkout(identity, checkout_path, tmp_path, monkeypatch, case):
    lookup = identity.session_checkout
    _init_repo(checkout_path)
    if case == "canonicalisable":
        child = checkout_path / "child"
        child.mkdir()
        result = lookup(child)
        assert (result.top, result.answered) == (identity.canonical_directory(str(checkout_path)), True)
    else:
        log = _git_shim(tmp_path, monkeypatch)
        monkeypatch.setattr(identity, "canonical_directory", Mock(side_effect=PermissionError))
        result = lookup(checkout_path)
        assert (result.top, result.answered) == (None, False)
        assert log.read_bytes() == b"", "a refused session root must start zero git calls"


RECORDED_CASES = [
    ("absent", "field-absent"), ("null", "field-absent"), ("not-string", "field-invalid"),
    ("empty", "field-invalid"), ("relative", "field-invalid"), ("not-encodable", "field-invalid"),
    ("missing", "path-missing"), ("through-a-file", "path-missing"), ("stat-error", "checkout-unreadable"),
    ("regular-file", "not-a-checkout"), ("mode-000-file", "not-a-checkout"), ("fifo", "not-a-checkout"),
    ("canonical-refuses", "checkout-unreadable"), ("git-cannot-answer", "checkout-unreadable"),
    ("bare-repository", "checkout-unreadable"), ("no-work-tree", "not-a-checkout"),
    ("sub-directory", "not-a-checkout"), ("inside-dot-git", "not-a-checkout"),
    ("usable", ""), ("equals-session-no-git", ""),
]


def _record_fifo(identity, path):
    # A separate interpreter bounds even a blocking open. Its audit hook sees
    # builtins.open, io.open and os.open and reports any attempt on the FIFO.
    script = """
import json, os, sys
sys.path.insert(0, sys.argv[1])
from h_mad_target_identity import recorded_checkout
fifo = sys.argv[2]
def watch(event, args):
    if event == 'open' and args[0] in (fifo, os.fsencode(fifo)):
        sys.exit('recorded_checkout opened the FIFO')
sys.addaudithook(watch)
print(json.dumps(recorded_checkout(fifo)))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(Path(identity.__file__).parent), str(path)],
        capture_output=True, text=True, check=True, timeout=1,
    )
    return tuple(json.loads(result.stdout))


@pytest.mark.parametrize("case, reason", RECORDED_CASES, ids=[case for case, _ in RECORDED_CASES])
def test_recorded_checkout_reason(identity, checkout_path, tmp_path, monkeypatch, hostile, case, reason):
    lookup = identity.recorded_checkout
    path = checkout_path
    value = str(path)
    if case in ("absent", "null"):
        record = {} if case == "absent" else {"implementation_checkout": None}
        value = record.get("implementation_checkout")
    elif case in ("not-string", "empty", "relative", "not-encodable"):
        value = {"not-string": [hostile], "empty": "", "relative": path.name,
                 "not-encodable": str(path) + "\0"}[case]
    elif case == "through-a-file":
        path.touch()
        value = str(path / "child")
    elif case == "stat-error":
        path.symlink_to(path.name)  # ELOOP, even for a privileged test runner
    elif case in ("regular-file", "mode-000-file"):
        path.touch()
        if case == "mode-000-file":
            path.chmod(0)
    elif case == "fifo":
        os.mkfifo(path)
        log = _git_shim(tmp_path, monkeypatch)
        assert _record_fifo(identity, path) == (None, reason)
        assert log.read_bytes() == b"", "recorded_checkout must reject the FIFO before asking git"
        return
    elif case == "canonical-refuses":
        _init_repo(path)
        monkeypatch.setattr(identity, "canonical_directory", Mock(side_effect=PermissionError))
    elif case == "git-cannot-answer":
        _init_repo(path)
        _git_shim(tmp_path, monkeypatch, "sys.exit(3)")
    elif case == "bare-repository":
        _init_repo(path, bare=True)
    elif case == "no-work-tree":
        path.mkdir()
    elif case in ("sub-directory", "inside-dot-git"):
        _init_repo(path)
        child = path / (".git/objects" if case == "inside-dot-git" else "child")
        child.mkdir(exist_ok=True)
        value = str(child)
    elif case in ("usable", "equals-session-no-git"):
        _init_repo(path)
        alias = tmp_path / "link"
        alias.symlink_to(path, target_is_directory=True)
        top = identity.canonical_directory(str(path))
        if case == "equals-session-no-git":
            session = identity.Checkout(top, True)
            log = _git_shim(tmp_path, monkeypatch)
            result = lookup(str(alias), session)
            assert log.read_bytes() == b"", "a known session checkout must start zero git calls"
            child = path / "child"
            child.mkdir()
            assert lookup(str(child), session) == (None, "not-a-checkout")
            assert log.stat().st_size, "a different directory must be checked with git"
        else:
            result = lookup(str(alias))
        canonical, detail = result
        assert isinstance(detail, str)
        assert (canonical, detail) == (top, reason)
        return
    assert lookup(value) == (None, reason), case


@pytest.mark.parametrize("name", ["recorded_checkout"])
def test_raw_inputs_are_not_paths(identity, checkout_path, name):
    lookup = getattr(identity, name)
    _init_repo(checkout_path)
    assert lookup(str(checkout_path))[0] == identity.canonical_directory(str(checkout_path))
    assert lookup(checkout_path) == (None, "field-invalid")
