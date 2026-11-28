"""Observe the existing gate tests at the plan's census revision."""
from __future__ import annotations

import argparse
import errno
import json
import linecache
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from unittest.mock import patch

PROBES = Path(__file__).resolve().parent
sys.path.insert(0, str(PROBES))
from discovery_probe import probe_main


BASE = "b29173f1"
STATE = ".bkit-memory.json"
VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES")
HOOKS = {
    "h-mad-codex-tdd-gate.py": "codex",
    "h-mad-agy-tdd-gate.py": "agy",
    "h-mad-tdd-gate.sh": "claude",
}
TEST_TERMS = re.compile(r"tdd.gate|tdd_judge|target_identity|state_write|bkit_guard|bkit-memory")
ARMING_FIELD = re.compile(r"(?<![a-z0-9_])(phase|implementation_checkout|phase5_stage)\s*=")
SHELL_REFUSAL = re.compile(r"permits only explicit|through Bash|read-only, and H-MAD")
ROWS = (
    "D1", "D2", "D3", "D4", "D5", "D6-write", "D6-shell", "D6-referent", "D7",
    "lstat-undecidable", "root-unlistable", "git-shim", "replaced-run", "claude-stub",
    "agy-kinds", "shell-refusal",
)


def git(args, *, cwd, env=None, check=True):
    executable = os.environ.get("HMAD_CENSUS_GIT", "git")
    with subprocess.Popen([executable, *args], cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise
        if check and proc.returncode:
            raise subprocess.CalledProcessError(proc.returncode, args, stdout, stderr)
        return proc.returncode, stdout.strip()


def is_state(path):
    return path.name.casefold() == STATE and path.parent.name.casefold() == "docs"


def checkout(path):
    for directory in (path, *path.parents):
        try:
            (directory / ".git").lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        return directory
    return None


def state_candidates(root):
    # Walk independently of the hook's rglob, and inspect the joined names.
    # This also sees a docs symlink without recursing through directory links.
    for directory, subdirs, _ in os.walk(root):
        subdirs[:] = [name for name in subdirs if name != ".git"]
        parent = Path(directory)
        docs = {parent / "docs"}
        docs.update(parent / name for name in subdirs if name.casefold() == "docs")
        for location in docs:
            candidates = {location / STATE}
            try:
                candidates.update(path for path in location.iterdir() if path.name.casefold() == STATE)
            except OSError:
                pass
            yield from sorted(candidates)


class Census:
    def __init__(self, log):
        self.log = log

    def entry_mode(self, path, route):
        try:
            return path.lstat().st_mode
        except (FileNotFoundError, NotADirectoryError):
            return None
        except OSError as exc:
            if not isinstance(exc, PermissionError) and exc.errno != errno.ELOOP:
                raise
            self.log("lstat-undecidable", route)
            return None

    def presence(self, root, path, route):
        mode = self.entry_mode(path, route)
        if mode is None:
            return

        kinds = []
        if stat.S_ISLNK(mode):
            try:
                path.stat()
            except FileNotFoundError:
                kinds.append("dangling-link")
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    kinds.append("looping-link")
            else:
                kinds.append("file-link")
        elif stat.S_ISDIR(mode):
            kinds.append("directory-in-place")
        elif stat.S_ISFIFO(mode):
            kinds.append("fifo")
        elif stat.S_ISREG(mode):
            kinds.append("regular")
        if path.parent.is_symlink():
            kinds.append("docs-symlink")
        if path.parent.name != "docs":
            kinds.append("case-variant-docs")
        if path.name != STATE:
            kinds.append("case-variant-file")
        for kind in kinds:
            self.log("D4", kind, route)

        if path == root / "docs" / STATE:
            return
        nested = checkout(path.parent)
        if nested is not None and nested != checkout(root):
            self.log("D2", route)
        try:
            relative = path.relative_to(root)
        except ValueError:
            return
        if {"tests", "fixtures"}.intersection(relative.parts[:-2]):
            self.log("D3", route)
        project = relative.parent.parent
        if project != Path(".") and checkout(root) is not None:
            from discovery_probe import Oracle

            oracle = Oracle(root, executable=os.environ.get("HMAD_CENSUS_GIT", "git"))
            try:
                for directory in (*reversed(project.parents), project):
                    oracle.query([str(directory)])
                if oracle.memo[str(project)][1]:
                    self.log("D1", route)
            finally:
                oracle.close()

    def state_write(self, path, via):
        if path.is_symlink():
            self.log("D5", via)

    def write_target(self, host, root, path, identity=None):
        resolved = Path(os.path.realpath(path))
        targets = {path, resolved}
        if getattr(identity, "target", ""):
            actual = Path(identity.target)
            targets.update(actual.parent / name for name in identity.names)

        protected = {candidate for candidate in targets
                     if is_state(candidate) or ".git" in candidate.parts}
        if protected:
            if path in protected:
                self.log("D6-write", host, "name")
            if path != resolved and (path in protected or resolved in protected):
                self.log("D6-write", host, "symlink")

        try:
            target_root = checkout(resolved.parent)
            if protected and target_root is not None and target_root != checkout(root):
                self.log("D6-write", host, "other-checkout")
        except PermissionError:
            # Distinguish a refused project root from an inaccessible target inside it.
            try:
                with os.scandir(root):
                    pass
            except PermissionError as exc:
                self.root_error(host, exc)
                return
            self.log("lstat-undecidable", "target")
            target_root = None
        except OSError as exc:
            if exc.errno != errno.ELOOP:
                raise
            self.log("lstat-undecidable", "target")
            target_root = None

        for directory in {root, target_root} - {None}:
            for candidate in state_candidates(directory):
                if candidate in targets:
                    continue
                mode = self.entry_mode(candidate, "referent")
                if mode is not None and stat.S_ISLNK(mode) and Path(os.path.realpath(candidate)) == resolved:
                    self.log("D6-referent", host)
                    return

    def shell(self, host, command, root, cwd, safe):
        try:
            argv = shlex.split(command)
        except ValueError:
            return
        if not argv:
            return
        if len(argv) > 5 and Path(argv[0]).name == "hmad-dispatch" and argv[1] == "run":
            argv = argv[5:]
        if not argv:
            return
        if safe:
            index = int(Path(argv[0]).name.startswith("python"))
            if len(argv) > index + 1 and Path(argv[index]).name == "h_mad_state_write.py":
                target = (Path(cwd) if isinstance(cwd, str) and cwd else root) / argv[index + 1]
                if is_state(target) and any(ARMING_FIELD.match(arg) for arg in argv[index + 2:]):
                    self.log("D6-shell", host, "position")
            return
        text = " ".join(argv).replace("'", "").replace('"', "").casefold()
        if "h_mad_state_write" in text and ARMING_FIELD.search(text):
            self.log("D6-shell", host, "mention")

    def git_env(self, host, lookup=None):
        present = tuple(name for name in VARIABLES if name in os.environ)
        if present:
            details = ()
            if lookup is not None:
                clean = {key: value for key, value in os.environ.items() if key not in VARIABLES}
                args = ("rev-parse", "--show-toplevel")
                changed = git(args, cwd=lookup, check=False) != git(args, cwd=lookup, env=clean, check=False)
                details = ("changed" if changed else "equal",)
            for name in present:
                self.log("D7", name, host, *details)

    def root_lookup(self, host, directory, original_run):
        if subprocess.run is not original_run:
            self.log("replaced-run", host)
        if shutil.which("git") != os.environ.get("HMAD_CENSUS_GIT"):
            self.log("git-shim", host)
        self.log("git-root-lookup", host)
        self.git_env(host, directory)

    def root_error(self, host, error):
        if isinstance(error, PermissionError):
            self.log("root-unlistable", host)


def control(root):
    rows = []

    def log(row, *details):
        label = {"D6-write": "D6", "D6-shell": "D6", "D6-referent": "D6 referent"}.get(row, row)
        rows.append(" ".join(("CENSUS-CONTROL:", label, *details)))

    def case_detector(case):
        return Census(lambda row, *details: log(row, *details, case))

    detector = Census(log)
    git(("init", "-q"), cwd=root)
    (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    for name in ("ignored", "nested", "tests"):
        folder = root / name
        (folder / "docs").mkdir(parents=True)
        (folder / "docs" / STATE).touch()
    git(("init", "-q"), cwd=root / "nested")
    for route in ("scan", "chain"):
        for name in ("ignored", "nested", "tests"):
            detector.presence(root, root / name / "docs" / STATE, route)

    mixed = root / "mixed"
    mixed.mkdir()
    case_paths = {}
    for name in ("file-link", "dangling-link", "looping-link", "directory-in-place", "fifo",
                 "docs-symlink", "case-variant-docs", "case-variant-file"):
        path = mixed / name / ("DOCS" if name == "case-variant-docs" else "docs") / (
            STATE.upper() if name == "case-variant-file" else STATE)
        path.parent.parent.mkdir()
        if name != "docs-symlink":
            path.parent.mkdir()
        case_paths[name] = path
    ordinary = root / "ignored" / "docs" / STATE
    case_paths["file-link"].symlink_to(ordinary)
    case_paths["dangling-link"].symlink_to(root / "missing")
    case_paths["looping-link"].symlink_to(STATE)
    case_paths["directory-in-place"].mkdir()
    os.mkfifo(case_paths["fifo"])
    case_paths["docs-symlink"].parent.symlink_to(ordinary.parent)
    case_paths["case-variant-docs"].touch()
    case_paths["case-variant-file"].touch()
    for route in ("scan", "chain"):
        for path in case_paths.values():
            detector.presence(root, path, route)
        with patch.object(Path, "lstat", side_effect=PermissionError):
            detector.presence(root, ordinary, route)

    detector.state_write(case_paths["file-link"], "write")
    detector.state_write(case_paths["file-link"], "seed")
    referent = root / "note.txt"
    case_paths["file-link"].unlink()
    case_paths["file-link"].symlink_to(referent)
    alias = root / "alias"
    alias.symlink_to(ordinary)
    for host in ("codex", "agy", "claude"):
        for path in (ordinary, alias, root / "nested" / "docs" / STATE, referent):
            detector.write_target(host, root, path)
    for host in ("codex", "agy"):
        detector.shell(host, f"python3 h_mad_state_write.py '{ordinary}' --set phase=", root, None, True)
        detector.shell(host, "inspect 'h_mad_state_write.py phase='", root, None, False)

    drive_git_environment(detector, root)
    original_run = subprocess.run
    with patch.object(subprocess, "run"), patch.object(shutil, "which", return_value="git-shim"):
        detector.root_lookup("codex", root, original_run)
    detector.root_error("codex", PermissionError())
    listable = root / "listable"
    restricted = listable / "restricted"
    restricted.mkdir(parents=True)
    mode = stat.S_IMODE(restricted.stat().st_mode)
    restricted.chmod(0)
    try:
        case_detector("unsearchable-parent").write_target("codex", listable, restricted / "note.txt")
    finally:
        restricted.chmod(mode)

    docs = listable / "docs"
    docs.symlink_to(docs.name)
    case_detector("looping-docs").presence(listable, docs / STATE, "scan")

    for row, *details in observer_control(root):
        log(row, *details)
    for row, filename in source_hits("test_fixture.py", "GATE_KINDS\npermits only explicit"):
        log(row, filename)
    return sorted(set(rows))


def source_hits(filename, source):
    if "GATE_KINDS" in source:
        yield "agy-kinds", filename
    if SHELL_REFUSAL.search(source):
        yield "shell-refusal", filename


def observer_control(root):
    # Drive the same call/return tracing hooks used during the census. Install
    # the observer in a child so its tracing and Popen wrapper end there.
    fixtures = root / "observer-control"
    fixtures.mkdir()
    (fixtures / "h_mad_target_identity.py").write_text(
        "def canonicalise(root, target): return (root, target)\n")
    (fixtures / "h_mad_tdd_judge.py").write_text("def judge(target): return None\n")
    docs = fixtures / "docs"
    docs.mkdir()
    (docs / STATE).touch()
    (fixtures / "loop").symlink_to("loop")
    log = fixtures / "observations.jsonl"
    env = dict(os.environ, HMAD_CENSUS_LOG=str(log), PYTEST_CURRENT_TEST="control")
    driver = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[2]); "
        "from pin_census import install_observer; install_observer(); "
        "sys.path.insert(0, str(Path.cwd())); "
        "from h_mad_target_identity import canonicalise; from h_mad_tdd_judge import judge; "
        "canonicalise(Path.cwd(), 'note.txt'); canonicalise(Path.cwd(), 'loop/note.txt'); "
        "judge(Path.cwd() / 'docs/.bkit-memory.json')"
    )
    mode = stat.S_IMODE(docs.stat().st_mode)
    docs.chmod(0)
    try:
        subprocess.run([sys.executable, "-I", "-B", "-c", driver, "h-mad-tdd-gate.sh", str(PROBES)],
                       cwd=fixtures, env=env, check=True, capture_output=True, timeout=15)
    finally:
        docs.chmod(mode)
    for line in log.read_text().splitlines():
        row, _, *details = json.loads(line)
        if row == "observer-error":
            raise ValueError(f"observer control failed: {details}")
        yield row, *details


def drive_git_environment(detector, root):
    for name in VARIABLES:
        with patch.dict(os.environ, {name: str(root)}, clear=False):
            detector.git_env("codex", root)
            detector.git_env("agy", root)
            detector.git_env("codex-explicit")
            detector.git_env("claude")


def caller_host(frame):
    while frame is not None:
        name = Path(frame.f_code.co_filename).name
        if name in HOOKS:
            return HOOKS[name]
        if name == "<string>" and len(sys.argv) > 1 and Path(sys.argv[1]).name in HOOKS:
            return HOOKS[Path(sys.argv[1]).name]
        frame = frame.f_back
    return None


def install_observer():
    """Observe the baseline tests and the child Python hooks they execute."""
    log_path = Path(os.environ["HMAD_CENSUS_LOG"])
    original_run = subprocess.run
    instrumented = frozenset((*HOOKS, "h_mad_target_identity.py", "h_mad_tdd_judge.py",
                              "h_mad_state_write.py", "h_mad_bkit_guard.py"))
    original_popen = subprocess.Popen.__init__

    def instrumented_argument(arg):
        if not isinstance(arg, (str, os.PathLike)):
            return False
        try:
            command = Path(arg)
            return command.name in instrumented or (
                command.is_symlink() and command.resolve().name in instrumented)
        except (OSError, RuntimeError, ValueError, TypeError):
            # Arguments can be program text or names the filesystem cannot resolve.
            return False

    def observed_popen(child, args, *positional, **kwargs):
        # Several shell hook fixtures construct an environment from scratch.
        # Keep their choices and carry only the observer and running test ID.
        test = os.environ.get("PYTEST_CURRENT_TEST")
        if test and isinstance(args, (tuple, list)) and kwargs.get("env") is not None:
            if any(instrumented_argument(arg) for arg in args[:3]):
                env = dict(kwargs["env"])
                monitor = str(Path(__file__).parent)
                env["PYTHONPATH"] = os.pathsep.join(filter(None, (monitor, env.get("PYTHONPATH"))))
                for key in ("HMAD_CENSUS_LOG", "HMAD_CENSUS_GIT"):
                    env[key] = os.environ[key]
                env["PYTEST_CURRENT_TEST"] = test
                kwargs["env"] = env
        original_popen(child, args, *positional, **kwargs)

    subprocess.Popen.__init__ = observed_popen

    def log(row, *details):
        current = os.environ.get("PYTEST_CURRENT_TEST", "")
        if not current:
            return
        node = current.rsplit(" (", 1)[0]
        record = json.dumps([row, node, *details], ensure_ascii=True) + "\n"
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, record.encode())
        finally:
            os.close(fd)

    detector = Census(log)

    def scan(root):
        for candidate in state_candidates(root):
            detector.presence(root, candidate, "scan")

    def root_lookup(frame, event, arg):
        if event != "line":
            return root_lookup
        if linecache.getline(frame.f_code.co_filename, frame.f_lineno).strip() == "result = subprocess.run(":
            host = HOOKS[Path(frame.f_code.co_filename).name]
            directory = frame.f_locals["path"] if host == "codex" else Path.cwd().parent
            detector.root_lookup(host, directory, original_run)
        return root_lookup

    def after_canonicalise(frame, event, arg):
        if event == "return":
            host = caller_host(frame)
            if host is not None and arg is not None:
                values = frame.f_locals
                root = Path(values["root"])
                base = Path(values.get("base", values.get("cwd") or root))
                detector.write_target(host, root, base / values["target"], arg)
                if host == "claude" and not hasattr(arg, "target"):
                    log("claude-stub")
        return after_canonicalise

    def after_shell(frame, event, arg):
        if event == "return":
            host = caller_host(frame)
            if host is not None:
                values = frame.f_locals
                detector.shell(host, values["command"], values["root"], values["cwd"], arg)
        return after_shell

    def after_directory(frame, event, arg):
        if event == "exception" and isinstance(arg[1], OSError):
            caller = frame.f_back
            host = caller_host(caller)
            if host is not None and (caller.f_code.co_name == "_canonical_root"
                                     or caller.f_locals.get("spelled_root") == frame.f_locals["path"]):
                detector.root_error(host, arg[1])
        return after_directory

    def observe(frame, filename, name):
        values = frame.f_locals
        if filename == "h_mad_target_identity.py":
            if name == "_any_phase5_status":
                scan(Path(values["root"]))
            elif name == "_safe_shell_command" and values["root"] is not None:
                return after_shell
            elif name == "canonicalise":
                if caller_host(frame) == "claude":
                    detector.git_env("claude")
                return after_canonicalise
            elif name == "canonical_directory":
                return after_directory
        elif filename == "h_mad_tdd_judge.py":
            if name == "_state_at" and frame.f_back.f_code.co_name == "read_chain":
                detector.presence(Path(frame.f_back.f_locals["real_root"]), values["path"], "chain")
            elif name == "judge" and is_state(Path(values["target"])):
                log("D6-write", "judge", "name")
        elif filename == "h_mad_state_write.py" and name == "_atomic_write":
            detector.state_write(values["state_file"], "write")
        elif filename == "h_mad_bkit_guard.py" and name == "seed":
            detector.state_write(values["state_file"], "seed")
        elif filename == "h-mad-codex-tdd-gate.py" and name == "_project_root":
            explicit = os.environ.get("CODEX_PROJECT_DIR")
            if explicit and Path(explicit).expanduser().is_dir():
                detector.git_env("codex-explicit")
            return root_lookup
        elif filename == "h-mad-agy-tdd-gate.py" and name == "main":
            return root_lookup
        return None

    def traced_callback(callback):
        def traced(frame, event, arg):
            try:
                callback(frame, event, arg)
            except Exception as exc:
                log("observer-error", frame.f_code.co_name, type(exc).__name__)
            return traced
        return traced

    def trace(frame, event, arg):
        if event != "call" or "PYTEST_CURRENT_TEST" not in os.environ:
            return None
        filename = os.path.basename(frame.f_code.co_filename)
        if filename not in instrumented:
            return None
        try:
            callback = observe(frame, filename, frame.f_code.co_name)
            if callback is not None:
                frame.f_trace_lines = callback is root_lookup
                return traced_callback(callback)
        except Exception as exc:
            log("observer-error", frame.f_code.co_name, type(exc).__name__)
        return None

    sys.settrace(trace)


def reading(scratch):
    root = Path(__file__).resolve().parents[4]
    clone = scratch / "repo"
    observer = scratch / "monitor"
    observer.mkdir()
    for name in ("pin_census.py", "discovery_probe.py"):
        shutil.copyfile(PROBES / name, observer / name)
    (observer / "sitecustomize.py").write_text(
        "from pin_census import install_observer\ninstall_observer()\n", encoding="utf-8",
    )
    log = scratch / "hits.jsonl"
    test_home = scratch / "home"
    test_home.mkdir()
    env = {name: value for name, value in os.environ.items()
           if not name.startswith(("GIT_", "PYTEST_", "OPENCODE", "CLAUDE", "CODEX", "ORCA_"))}
    env.update({
        "HOME": str(test_home), "PYTHONPATH": str(observer), "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1", "HMAD_CENSUS_LOG": str(log),
        "HMAD_CENSUS_GIT": shutil.which("git") or "git",
    })
    git(("clone", "--quiet", "--no-hardlinks", "--no-checkout", str(root), str(clone)), cwd=scratch, env=env)
    git(("checkout", "--quiet", "--detach", BASE), cwd=clone, env=env)
    references = test_home / ".claude/skills/h-mad/references"
    references.mkdir(parents=True)
    shutil.copyfile(clone / "h-mad/references/inline-protocols.md", references / "inline-protocols.md")
    _, files = git(("ls-files", "-z", "h-mad/tests", "handoff"), cwd=clone, env=env)
    selected = []
    hits = set()
    for filename in files.split("\0"):
        path = Path(filename)
        if path.suffix != ".py" or not path.name.startswith("test_"):
            continue
        source = (clone / path).read_text(encoding="utf-8")
        if TEST_TERMS.search(source):
            selected.append(filename)
        hits.update(source_hits(filename, source))
    if not selected:
        raise ValueError("baseline test selection is empty")

    python = root / ".venv/bin/python"
    if not python.is_file():
        python = Path(sys.executable)
    result = subprocess.run([str(python), "-m", "pytest", "-q", *selected], cwd=clone, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=2400)
    if result.returncode:
        sys.stderr.write(result.stdout)
        raise RuntimeError(f"baseline tests exited {result.returncode}")
    if not log.exists():
        raise RuntimeError("baseline hooks did not reach the observer")
    hits.update(tuple(json.loads(line)) for line in log.read_text(encoding="utf-8").splitlines())
    errors = sorted(hit for hit in hits if hit[0] == "observer-error")
    if errors:
        raise RuntimeError(f"observer errors: {errors}")
    rows = [f"CENSUS: base={BASE} files={len(selected)}"]
    for row in (*ROWS, "git-root-lookup"):
        matches = sorted(hit[1:] for hit in hits if hit[0] == row)
        # Ordinary regular stores are the reference class in the D4 row.
        if row == "D4":
            matches = [hit for hit in matches if hit[1] != "regular"]
        rows.append(f"CENSUS: {row} hits={len(matches)}")
        rows.extend("CENSUS-HIT: " + " ".join((row, *hit)) for hit in matches)
    return rows


@probe_main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="hmad-census-") as directory:
        scratch = Path(directory).resolve()
        rows = control(scratch) if args.control else reading(scratch)
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
