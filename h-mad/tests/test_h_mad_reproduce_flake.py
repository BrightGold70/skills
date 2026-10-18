"""Row 2508: reproduce a flake across SIGINT disposition and machine load.

Only the CLI is prescribed, so tests execute the script rather than inventing
an internal API. Production loading happens at test execution, never collection.
The small pytest double makes matrix/timeout tests fast; one real pytest test
independently proves that bg actually inherits SIG_IGN. The driver observes real
subprocesses and bounds cpu_count to two, without replacing load helpers.
"""

import ast
import json
import os
import re
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "h_mad_reproduce_flake.py"
CELLS = {f"{disposition}-{load}" for disposition in ("fg", "bg")
         for load in ("idle", "cpu", "fork")}

DRIVER = r'''
import json, os, runpy, subprocess, sys
script, trace, *args = sys.argv[1:]
os.cpu_count = lambda: 2
original_popen = subprocess.Popen
original_killpg = os.killpg
children = []
def record(event):
    with open(trace, "a") as stream:
        stream.write(json.dumps(event) + "\n")
def popen(*args, **kwargs):
    child = original_popen(*args, **kwargs)
    argv = kwargs.get("args", args[0] if args else [])
    record({"event": "spawn", "pid": child.pid,
            "argv": list(map(str, argv)) if not isinstance(argv, str) else [argv],
            "pgid": os.getpgid(child.pid),
            "live_before": [item.pid for item in children if item.poll() is None]})
    children.append(child)
    communicate = child.communicate
    def observed_communicate(*args, **kwargs):
        record({"event": "timeout", "pid": child.pid, "seconds": kwargs.get("timeout")})
        return communicate(*args, **kwargs)
    child.communicate = observed_communicate
    wait = child.wait
    def observed_wait(*args, **kwargs):
        record({"event": "timeout", "pid": child.pid,
                "seconds": kwargs.get("timeout", args[0] if args else None)})
        return wait(*args, **kwargs)
    child.wait = observed_wait
    return child
def killpg(pgid, sig):
    record({"event": "killpg", "pgid": pgid, "signal": int(sig)})
    return original_killpg(pgid, sig)
subprocess.Popen = popen
os.killpg = killpg
sys.argv = [script, *args]
runpy.run_path(script, run_name="__main__")
'''

FAKE_PYTEST = r'''
import json, os, pathlib, signal, sys, time
args = sys.argv[1:]
if "--version" in args:
    print("pytest 8.0.0")
    raise SystemExit(0)
if "--collect-only" in args or "--co" in args:
    if os.environ.get("FLAKE_TEST_MODE") == "empty":
        print("no tests collected in 0.00s")
        raise SystemExit(5)
    print("test_target.py::test_target\n\n1 test collected in 0.00s")
    raise SystemExit(0)
mode = os.environ.get("FLAKE_TEST_MODE", "pass")
if mode == "empty":
    print("no tests ran in 0.00s")
    raise SystemExit(5)
trace = pathlib.Path(os.environ["FLAKE_TEST_RUNS"])
lock = trace.with_suffix(".lock")
def _holder_alive():
    try:
        os.kill(int(lock.read_text() or "0"), 0)
    except (ValueError, ProcessLookupError, FileNotFoundError):
        return False
    except PermissionError:
        return True
    return True
# Like the real suite lock, a lock left by a killed holder is stale and taken over.
try:
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
except FileExistsError:
    if _holder_alive():
        print("OVERLAPPING_PYTEST")
        raise SystemExit(7)
    lock.unlink(missing_ok=True)
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
os.write(fd, str(os.getpid()).encode())
os.close(fd)
with trace.open("a") as stream:
    stream.write(json.dumps({"argv": args, "cwd": os.getcwd(),
                             "pid": os.getpid(), "event": "start"}) + "\n")
try:
    print("target stdout marker", flush=True)
    print("target stderr marker", file=sys.stderr, flush=True)
    if mode == "interrupt":
        os.kill(os.getppid(), signal.SIGINT)
        time.sleep(0.1)
    if mode == "sleep":
        pathlib.Path(os.environ["FLAKE_TEST_READY"]).write_text(str(os.getpid()))
        time.sleep(20)
    time.sleep(0.025)
    count = sum(json.loads(line)["event"] == "start" for line in trace.read_text().splitlines())
    failed = mode == "fail" or (mode == "alternate" and count % 2 == 1)
    if failed:
        print("FAILED test_target.py::test_target - AssertionError: deliberate")
    print("1 failed in 0.03s" if failed else "1 passed in 0.03s")
finally:
    with trace.open("a") as stream:
        stream.write(json.dumps({"event": "end", "pid": os.getpid()}) + "\n")
    lock.unlink(missing_ok=True)
raise SystemExit(1 if failed else 0)
'''


def _sandbox(tmp_path, mode="pass", real_pytest=False):
    work = tmp_path / "work"
    work.mkdir()
    (work / "test_target.py").write_text("def test_target():\n    assert True\n")
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER)
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               FLAKE_TEST_MODE=mode, FLAKE_TEST_RUNS=str(tmp_path / "runs.jsonl"),
               FLAKE_TEST_READY=str(tmp_path / "ready"), TMPDIR=str(tmp_path))
    # Scratch pytest sessions must not inherit this repository's lock/config.
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"):
        env.pop(name, None)
    if not real_pytest:
        package = tmp_path / "packages" / "pytest"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "__main__.py").write_text(FAKE_PYTEST)
        # Audit runs inside exec'd Python load helpers too; this proves the
        # fork load repeatedly launches the specified executable.
        (package.parent / "sitecustomize.py").write_text(textwrap.dedent(f"""\
            import json, sys
            def audit(event, args):
                if event in ('subprocess.Popen', 'os.posix_spawn', 'os.exec'):
                    if str(args[0]) == '/usr/bin/true':
                        with open({str(tmp_path / 'true.jsonl')!r}, 'a') as stream:
                            stream.write(json.dumps({{'executable': str(args[0])}}) + '\\n')
            sys.addaudithook(audit)
            """))
        env["PYTHONPATH"] = str(package.parent)
    return work, driver, env


def _command(tmp_path, driver, work, *, cells="fg-idle", runs=1,
             timeout=10, log_dir=True, python=True):
    argv = [sys.executable, str(driver), str(SCRIPT), str(tmp_path / "spawn.jsonl"),
            "test_target.py::test_target", "--cwd", str(work)]
    if python:
        argv += ["--python", sys.executable]
    if runs is not None:
        argv += ["--runs", str(runs)]
    if cells is not None:
        argv += ["--cells", cells]
    if timeout is not None:
        argv += ["--timeout", str(timeout)]
    if log_dir:
        argv += ["--log-dir", str(tmp_path / "logs")]
    return argv


def _run(tmp_path, *, mode="pass", real_pytest=False, **options):
    work, driver, env = _sandbox(tmp_path, mode, real_pytest)
    result = subprocess.run(_command(tmp_path, driver, work, **options),
                            env=env, capture_output=True, text=True, timeout=15)
    return result


def _rows(result):
    return re.findall(r"^FLAKE: (\S+) fails=(\d+)/(\d+)$", result.stdout, re.M)


def _verdict(result, expected):
    lines = result.stdout.strip().splitlines()
    assert lines and lines[-1].startswith(f"FLAKE-VERDICT: {expected}"), result.stdout + result.stderr
    return lines[-1]


def _events(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def _helpers(tmp_path):
    # Availability probes and pytest runs are not load generators.
    return [event for event in _events(tmp_path / "spawn.jsonl")
            if event["event"] == "spawn" and
            not any("pytest" in arg for arg in event["argv"])]


def _assert_helpers_reaped(tmp_path, *, required=True):
    helpers = _helpers(tmp_path)
    if required:
        assert helpers, "the requested load never started a helper"
    for helper in helpers:
        with pytest.raises(ProcessLookupError):
            os.kill(helper["pid"], 0)
    kills = [event for event in _events(tmp_path / "spawn.jsonl") if event["event"] == "killpg"]
    if helpers:
        assert kills, "load helpers must be stopped as process groups"
        assert {helper["pgid"] for helper in helpers} <= {event["pgid"] for event in kills}


def test_help_exposes_the_prescribed_cli(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                            capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    for option in ("nodeid", "--python", "--runs", "--cwd", "--log-dir", "--timeout", "--cells"):
        assert option in result.stdout


def test_defaults_cover_all_six_cells_with_five_runs(tmp_path):
    result = _run(tmp_path, cells=None, runs=None, timeout=None, python=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert {(cell, int(fails), int(runs)) for cell, fails, runs in _rows(result)} == {
        (cell, 0, 5) for cell in CELLS}
    assert len(_rows(result)) == 6
    assert _verdict(result, "NOT_REPRODUCED") == "FLAKE-VERDICT: NOT_REPRODUCED runs=30"
    timeouts = [event["seconds"] for event in _events(tmp_path / "spawn.jsonl")
                if event["event"] == "timeout" and event["seconds"] is not None]
    assert any(299 <= value <= 300 for value in timeouts), timeouts
    _assert_helpers_reaped(tmp_path)


def test_cells_option_runs_only_the_selected_cells(tmp_path):
    result = _run(tmp_path, cells="fg-idle,bg-cpu")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(result) == [("fg-idle", "0", "1"), ("bg-cpu", "0", "1")]
    assert _verdict(result, "NOT_REPRODUCED") == "FLAKE-VERDICT: NOT_REPRODUCED runs=2"
    _assert_helpers_reaped(tmp_path)


def test_real_pytest_fails_only_when_bg_inherits_sigint_ignored(tmp_path):
    work, driver, env = _sandbox(tmp_path, real_pytest=True)
    (work / "test_target.py").write_text(textwrap.dedent("""\
        import signal
        def test_target():
            assert signal.getsignal(signal.SIGINT) != signal.SIG_IGN, 'real-bg-disposition'
        """))
    result = subprocess.run(_command(tmp_path, driver, work, cells="fg-idle,bg-idle"),
                            env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(result) == [("fg-idle", "0", "1"), ("bg-idle", "1", "1")]
    assert _verdict(result, "REPRODUCED") == (
        f"FLAKE-VERDICT: REPRODUCED cells=bg-idle logs={tmp_path / 'logs'}")
    logs = list((tmp_path / "logs").glob("*.log"))
    assert len(logs) == 1 and logs[0].name.startswith("bg-idle-")
    assert "real-bg-disposition" in logs[0].read_text()


def test_runs_are_serial_use_requested_python_cwd_and_exact_pytest_selection(tmp_path):
    work, driver, env = _sandbox(tmp_path)
    # The executable wrapper makes --python observable, even if sys.executable
    # happens to be the reproducer's default interpreter.
    python = tmp_path / "selected-python"
    python.write_text(f"#!{sys.executable}\nimport os, sys\n"
                      f"open({str(tmp_path / 'selected')!r}, 'a').write('used\\n')\n"
                      f"os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\n")
    python.chmod(0o755)
    argv = _command(tmp_path, driver, work, runs=3, cells="fg-idle,bg-idle")
    argv[argv.index("--python") + 1] = str(python)
    result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "selected").is_file(), "--python was ignored"
    events = _events(tmp_path / "runs.jsonl")
    starts = [event for event in events if event["event"] == "start"]
    # An executing probe, rather than --collect-only, may add one initial run.
    assert len(starts) in (6, 7), events
    assert [event["event"] for event in events] == ["start", "end"] * len(starts)
    for event in starts[-6:]:
        assert event["argv"] == ["test_target.py::test_target", "-q", "-p", "no:cacheprovider"]
        assert Path(event["cwd"]).resolve() == work.resolve()
    assert _rows(result) == [("fg-idle", "0", "3"), ("bg-idle", "0", "3")]


def test_only_failed_runs_keep_combined_stdout_and_stderr_logs(tmp_path):
    result = _run(tmp_path, mode="alternate", runs=2, cells="fg-idle,bg-idle")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(result) == [("fg-idle", "1", "2"), ("bg-idle", "1", "2")]
    assert _verdict(result, "REPRODUCED") == (
        f"FLAKE-VERDICT: REPRODUCED cells=fg-idle,bg-idle logs={tmp_path / 'logs'}")
    logs = list((tmp_path / "logs").glob("*.log"))
    assert len(logs) == 2
    assert {re.sub(r"-\d+\.log$", "", path.name) for path in logs} == {"fg-idle", "bg-idle"}
    for path in logs:
        assert re.fullmatch(r"(?:fg|bg)-idle-\d+\.log", path.name)
        assert "target stdout marker" in path.read_text()
        assert "target stderr marker" in path.read_text()


def test_each_failed_repeat_gets_a_distinct_indexed_log(tmp_path):
    result = _run(tmp_path, mode="fail", runs=2)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(result) == [("fg-idle", "2", "2")]
    logs = sorted((tmp_path / "logs").glob("fg-idle-*.log"))
    assert len(logs) == 2
    indices = sorted(int(path.stem.rsplit("-", 1)[1]) for path in logs)
    assert indices in ([0, 1], [1, 2])


def test_passing_runs_leave_no_logs(tmp_path):
    result = _run(tmp_path, runs=2)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _verdict(result, "NOT_REPRODUCED") == "FLAKE-VERDICT: NOT_REPRODUCED runs=2"
    assert not list((tmp_path / "logs").glob("*.log"))


def test_default_log_directory_is_new_and_printed(tmp_path):
    result = _run(tmp_path, mode="fail", log_dir=False)
    assert result.returncode == 0, result.stdout + result.stderr
    line = _verdict(result, "REPRODUCED")
    match = re.fullmatch(r"FLAKE-VERDICT: REPRODUCED cells=fg-idle logs=(.+)", line)
    assert match, line
    directory = Path(match[1])
    assert directory.is_dir() and directory.resolve().is_relative_to(tmp_path.resolve())
    assert directory.name not in {"work", "packages"}
    assert len(list(directory.glob("fg-idle-*.log"))) == 1


@pytest.mark.parametrize("cell,helper_count", [("fg-idle", 0), ("fg-cpu", 2), ("bg-cpu", 2),
                                              ("fg-fork", 1), ("bg-fork", 1)])
def test_load_starts_the_required_helpers_and_reaps_their_groups(tmp_path, cell, helper_count):
    result = _run(tmp_path, cells=cell)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(result) == [(cell, "0", "1")]
    helpers = _helpers(tmp_path)
    # /usr/bin/true invocations made in the parent are fork-load work, not
    # additional persistent generators. Normally they run inside the helper.
    generators = [event for event in helpers if event["argv"][0] != "/usr/bin/true"]
    assert len(generators) == helper_count, helpers
    runs = [event for event in _events(tmp_path / "spawn.jsonl")
            if event["event"] == "spawn" and "-m" in event["argv"]
            and "pytest" in event["argv"] and "--collect-only" not in event["argv"]
            and "--co" not in event["argv"]]
    assert runs, "no measured pytest process was started"
    assert {event["pid"] for event in generators} <= set(runs[-1]["live_before"]), (
        "load must stay alive while pytest runs", generators, runs)
    if cell.endswith("fork"):
        assert len(_events(tmp_path / "true.jsonl")) >= 2, "fork load must repeatedly spawn /usr/bin/true"
    _assert_helpers_reaped(tmp_path, required=bool(helper_count))


@pytest.mark.parametrize("mode", ["fail", "interrupt", "empty"])
@pytest.mark.parametrize("load", ["cpu", "fork"])
def test_load_helpers_are_reaped_on_failure_interruption_and_empty_probe(tmp_path, mode, load):
    result = _run(tmp_path, mode=mode, cells=f"bg-{load}")
    if mode == "fail":
        assert result.returncode == 0, result.stdout + result.stderr
        _verdict(result, "REPRODUCED")
    else:
        assert result.returncode == 2, result.stdout + result.stderr
        assert "reason=" in _verdict(result, "UNREADABLE")
    # A collection probe may happen before creating any load.
    _assert_helpers_reaped(tmp_path, required=mode != "empty")


def test_timeout_is_per_run_keeps_output_and_cleans_up_load(tmp_path):
    started = time.monotonic()
    result = _run(tmp_path, mode="sleep", cells="bg-cpu", runs=2, timeout=0.3)
    assert time.monotonic() - started < 5, "--timeout was ignored"
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(result) == [("bg-cpu", "2", "2")]
    _verdict(result, "REPRODUCED")
    logs = list((tmp_path / "logs").glob("bg-cpu-*.log"))
    assert len(logs) == 2
    for path in logs:
        assert "target stdout marker" in path.read_text()
        assert "target stderr marker" in path.read_text()
    _assert_helpers_reaped(tmp_path)


def test_missing_pytest_is_unreadable_instead_of_a_reproduced_failure(tmp_path):
    work, driver, env = _sandbox(tmp_path)
    (tmp_path / "packages" / "pytest" / "__init__.py").write_text(
        "raise ModuleNotFoundError(\"No module named 'pytest'\")\n")
    result = subprocess.run(_command(tmp_path, driver, work), env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "reason=" in _verdict(result, "UNREADABLE")
    assert not _rows(result)
    assert not (tmp_path / "runs.jsonl").exists()


def test_nodeid_collecting_nothing_is_unreadable(tmp_path):
    result = _run(tmp_path, mode="empty")
    assert result.returncode == 2, result.stdout + result.stderr
    # The collection probe must refuse it, not a later per-run exit-code check.
    assert "reason=collection_failed" in _verdict(result, "UNREADABLE")
    assert not _rows(result)
    assert not list((tmp_path / "logs").glob("*.log"))


def test_interrupted_run_is_unreadable(tmp_path):
    result = _run(tmp_path, mode="interrupt")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "reason=" in _verdict(result, "UNREADABLE")
    _assert_helpers_reaped(tmp_path, required=False)


def test_script_imports_only_stdlib_and_local_helpers():
    # Read inside the test: an absent new module must fail a node, not collection.
    tree = ast.parse(SCRIPT.read_text())
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".")[0])
    local = {path.stem for path in (ROOT / "scripts").glob("*.py")}
    assert imports <= sys.stdlib_module_names | local | {"__future__", ""}


def test_skill_scripts_list_names_tokens_and_when_to_prefer_the_reproducer():
    text = (ROOT / "SKILL.md").read_text()
    inventory = text.split("## Helper scripts", 1)[1].split("\n## ", 1)[0]
    bullets = re.findall(r"^- .*?(?=\n- |\n### |\Z)", inventory, re.M | re.S)
    entries = [bullet for bullet in bullets if "`h_mad_reproduce_flake.py`" in bullet]
    assert len(entries) == 1, "add one reproducer bullet to the helper scripts list"
    for literal in ("FLAKE:", "FLAKE-VERDICT:", "REPRODUCED", "NOT_REPRODUCED", "UNREADABLE",
                    "h_mad_failure_diff.py", "--repeat"):
        assert literal in entries[0], literal
    assert "load" in entries[0].lower() and "signal" in entries[0].lower()
