"""Repeat the Phase 4 discovery and canonicalisation prototype readings."""
from __future__ import annotations

import argparse
from collections import deque
from contextlib import contextmanager, redirect_stderr
from contextlib import redirect_stdout
from functools import wraps
from io import StringIO
import json
import os
from pathlib import Path
import re
import select
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

PARTS = ("fx", "fx2", "disc", "ev2", "proto2", "failclosed", "chain", "names", "arming")
SCRIPTS = Path(__file__).resolve().parents[4] / "h-mad/scripts"
STATE = Path("docs/.bkit-memory.json")
GIT_ENV = {key: value for key, value in os.environ.items()
           if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"}}
GIT_ENV["LC_ALL"] = "C"


def probe_main(function):
    """Publish a probe reading only after the measurement completes."""
    @wraps(function)
    def main(argv=None):
        output = StringIO()
        try:
            with redirect_stdout(output):
                result = function(argv)
        except SystemExit as error:
            result = 0 if error.code == 0 else 2
            if error.code not in (0, 2):
                print(f"probe exited: {error.code}", file=sys.stderr)
        except Exception as error:
            print(f"{function.__module__}: {error}", file=sys.stderr)
            return 2
        if result == 0:
            print(output.getvalue(), end="")
        return result
    return main


def git(root, *args, check=False, executable="git"):
    return subprocess.run([executable, "--no-optional-locks", "-C", str(root), *args],
                          capture_output=True, env=GIT_ENV, timeout=2, check=check)


class Oracle:
    """Prototype ignore stream and index/HEAD directory membership for one root."""

    def __init__(self, root, executable=None):
        self.root = root
        self.executable = executable or ("git-missing" if os.getenv("NOGIT") == "1" else "git")
        self.process = None
        self.buffer = b""
        self.content = None
        self.memo = {".": (False, False)}  # ignored, excluded
        self.wait = 0.0
        try:
            self.process = subprocess.Popen(
                [self.executable, "--no-optional-locks", "-C", str(root), "check-ignore",
                 "--no-index", "-v", "-n", "-z", "--stdin"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                bufsize=0, env=GIT_ENV,
            )
        except OSError:
            pass

    def close(self, failed=False):
        if self.process is None:
            return
        process, self.process = self.process, None
        if failed and process.poll() is None:
            process.kill()
        for stream in (process.stdin, process.stdout):
            try:
                stream.close()
            except OSError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def ready(self, stream, write=False):
        start = time.perf_counter()
        duration = max(0, 2 - self.wait)
        readable, writable, _ = select.select(
            [] if write else [stream], [stream] if write else [], [], duration,
        )
        self.wait += time.perf_counter() - start
        if not (readable or writable):
            raise TimeoutError("waiting for git check-ignore")

    def content_paths(self):
        try:
            index = git(self.root, "ls-files", "-z", check=True, executable=self.executable)
            head = git(self.root, "ls-tree", "-r", "-d", "-z", "--name-only", "HEAD",
                       executable=self.executable)
            if head.returncode:
                log = git(self.root, "log", "-1", "--format=", executable=self.executable)
                if b"does not have any commits yet" not in log.stderr:
                    return False
            paths = set(os.fsdecode(path) for path in head.stdout.split(b"\0") if path)
            for path in index.stdout.split(b"\0"):
                parent = Path(os.fsdecode(path)).parent
                while parent != Path(".") and str(parent) not in paths:
                    paths.add(str(parent))
                    parent = parent.parent
            return paths
        except (OSError, subprocess.SubprocessError):
            return False

    def has_content(self, relative):
        if self.content is False:
            return True
        if relative in self.content:
            return True
        folded = unicodedata.normalize("NFC", relative).casefold()
        for name in self.content:
            if unicodedata.normalize("NFC", name).casefold() == folded:
                try:
                    if (self.root / name).samefile(self.root / relative):
                        return True
                except OSError:
                    pass
        return False

    def query(self, names):
        pending = []
        for name in names:
            if name in self.memo:
                continue
            ignored, excluded = self.memo[os.path.dirname(name) or "."]
            if excluded:
                self.memo[name] = (True, True)
            elif ignored:
                self.memo[name] = (True, not self.has_content(name))
            else:
                pending.append(name)

        def read_field():
            while b"\0" not in self.buffer:
                self.ready(self.process.stdout)
                data = os.read(self.process.stdout.fileno(), 8192)
                if not data:
                    raise EOFError("git check-ignore ended before the batch was answered")
                self.buffer += data
            field, self.buffer = self.buffer.split(b"\0", 1)
            return field

        batch, size = [], 0
        for name in pending:
            word = os.fsencode(name) + b"/\0"
            if batch and (len(batch) == 64 or size + len(word) > 4096):
                self.exchange(batch, read_field)
                batch, size = [], 0
            batch.append((name, word))
            size += len(word)
        if batch:
            self.exchange(batch, read_field)

    def exchange(self, batch, read_field):
        answers = {}
        complete = False
        if self.process is not None:
            try:
                data = memoryview(b"".join(word for _, word in batch))
                while data:
                    self.ready(self.process.stdin, write=True)
                    data = data[os.write(self.process.stdin.fileno(), data):]
                for name, _ in batch:
                    _, _, pattern, _ = (read_field() for _ in range(4))
                    answers[name] = bool(pattern and not pattern.startswith(b"!"))
                complete = True
            except (OSError, EOFError):
                self.close(failed=True)
        if self.content is None and any(answers.values()):
            if complete:
                self.content = self.content_paths()
            else:
                answers.clear()
        for name, _ in batch:
            ignored = answers.get(name, False)
            self.memo[name] = (ignored, ignored and not self.has_content(name))


def discover(root, oracle=None):
    """List candidates breadth first, asking before listing each child."""
    files = []
    errors = 0
    queue = deque(["."])
    while queue:
        name = queue.popleft()
        path = root / name
        try:
            (path / STATE).lstat()
        except (FileNotFoundError, NotADirectoryError):
            pass
        except OSError:
            errors += 1
        else:
            if name == "." or not os.path.lexists(path / "docs/.git"):
                files.append(path / STATE)
        try:
            with os.scandir(path) as entries:
                children = [os.path.join(name, entry.name).removeprefix("./") for entry in entries
                            if entry.is_dir(follow_symlinks=False)
                            and entry.name not in {"tests", "fixtures"}
                            and not os.path.lexists(Path(entry.path) / ".git")]
        except OSError:
            errors += 1
            continue
        if oracle is not None:
            oracle.query(children)
            children = [child for child in children if not oracle.memo[child][1]]
        queue.extend(children)
    return files, errors


@contextmanager
def audit():
    events = {name: [] for name in ("os.scandir", "os.listdir", "open", "subprocess.Popen")}
    active = True
    first = []

    def record(event, args):
        if active and event in events:
            events[event].append(args[0])
            if not first and event != "open":
                first.append(event)

    sys.addaudithook(record)
    try:
        yield events, first
    finally:
        active = False


def scan(root, plain=False, read=False):
    with audit() as (events, first):
        oracle = None if plain else Oracle(root)
        try:
            files, errors = discover(root, oracle)
            live = read and any_live(files)
        finally:
            if oracle is not None:
                oracle.close()
    return files, errors, live, events, first, oracle.wait if oracle else 0.0


def any_live(files):
    from h_mad_target_identity import _state_status

    return "active" in [_state_status(path) for path in files]


def disc(args):
    elapsed, waits = [], []
    for _ in range(args.runs):
        start = time.perf_counter()
        files, errors, _, events, _, wait = scan(args.root, plain=args.mode == "plain")
        elapsed.append(round(time.perf_counter() - start, 6))
        waits.append(round(wait, 6))
    return (f"files={len(files)} errors={errors} listed={len(events['os.scandir'])} "
            f"processes={len(events['subprocess.Popen'])} seconds={elapsed!r} wait={waits!r}")


def ev2(args):
    from h_mad_target_identity import _state_status  # load before recording file opens

    files, errors, _, events, first, _ = scan(args.root, read=True)
    trees = [(args.root / tree).resolve() for tree in args.trees]

    def below(path):
        return isinstance(path, (str, bytes)) and any(
            Path(os.fsdecode(path)).absolute().is_relative_to(tree) for tree in trees
        )

    listed = sum(map(below, events["os.scandir"] + events["os.listdir"]))
    opened = sum(below(path) and Path(os.fsdecode(path)).name == STATE.name for path in events["open"])
    return (f"files={len(files)} errors={errors} first={first[0]} "
            f"processes={len(events['subprocess.Popen'])} excluded_listed={listed} excluded_state_opened={opened}")


def write_state(root, records=None):
    path = root / STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"orchestrator_state": records or {}}), encoding="utf-8")
    return path


def repo(root):
    root.mkdir()
    git(root, "init", "-q", check=True)
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "fixture", check=True)


def fx(args):
    shapes = {
        "f_wide": (2000, 10, 1, True), "f_trees": (2000, 10, 1, True),
        "f_subs": (2000, 10, 1, True), "f_nested": (2000, 10, 20, True),
        "f_small": (10, 1, 1, True), "f_none": (2000, 10, 1, True),
        "f_many": (10000, 2, 1, True), "f_nogit": (2000, 10, 1, False),
    }
    if args.layout:
        shapes = {args.layout: shapes[args.layout]}
    for name, (count, width, depth, under_git) in shapes.items():
        root = args.directory / name
        if under_git:
            repo(root)
        else:
            root.mkdir()
        write_state(root)
        for number in range(count):
            nested = Path(*(f"n{number // depth}-{index}" for index in range(number % depth)))
            folder = root / "content" / nested / f"d{number}"
            folder.mkdir(parents=True)
            for index in range(width):
                (folder / str(index)).touch()
        if name != "f_none":
            (root / ".gitignore").write_text("/excluded/\n/excluded-*/\n", encoding="utf-8")
            for index in range(100):
                folder = f"excluded-{index}/sub" if name == "f_trees" else f"excluded/sub{index}"
                if name != "f_nogit":
                    write_state(root / folder)
                if name in {"f_subs", "f_nogit"}:
                    write_state(root / f"sub{index}")
        (root / "docs/n.md").touch()
        (root / "src").mkdir()
        (root / "src/x.py").touch()
    return f"layouts={','.join(shapes)}"


def fx2(args):
    shapes = ("g_every", "g_deep", "g_nothing", "g_nogit")
    for name in shapes:
        root = args.directory / name
        if name == "g_nogit":
            root.mkdir()
        else:
            repo(root)
        (root / ".gitignore").write_text("/state/\n", encoding="utf-8")
        write_state(root)
        for index in range(100):
            child = root / "state" / f"child-{index}"
            (child / "a/b/c").mkdir(parents=True)
            if name == "g_every":
                write_state(child)
                write_state(child / "a/b/c")
        if name in ("g_deep", "g_nogit"):
            write_state(root / "state/child-0/a/b/c")
    return f"layouts={','.join(shapes)}"


def chain_files(root, target, oracles):
    parent = target.parent.resolve()
    if not parent.is_relative_to(root):
        return [root / STATE] if os.path.lexists(root / STATE) else []
    top, directory = root, root
    files = []
    candidates = (root, *(root.joinpath(*parent.relative_to(root).parts[:index])
                          for index in range(1, len(parent.relative_to(root).parts) + 1)))
    for directory in candidates:
        if os.path.lexists(directory / ".git"):
            top = directory
        state = directory / STATE
        if not os.path.lexists(state):
            continue
        if top != directory:
            if top not in oracles:
                oracles[top] = Oracle(top)
            oracle = oracles[top]
            relative = directory.relative_to(top)
            for index in range(1, len(relative.parts) + 1):
                oracle.query([str(Path(*relative.parts[:index]))])
            if oracle.memo[str(relative)][1]:
                continue
        files.append(state)
    return files


def chain(args):
    target = args.root / args.target
    with audit() as (events, _):
        oracles = {args.root: Oracle(args.root)}
        try:
            files, _ = discover(args.root, oracles[args.root])
            scanned = len(events["subprocess.Popen"])
            chains = []
            for _ in range(args.runs):
                own = oracles if args.mode == "shared" else {}
                try:
                    chains.append(len(chain_files(args.root, target, own)))
                finally:
                    if own is not oracles:
                        for oracle in own.values():
                            oracle.close()
        finally:
            for oracle in oracles.values():
                oracle.close()
    return (f"mode={args.mode} files={len(files)} chain_files={chains!r} "
            f"scan_processes={scanned} processes={len(events['subprocess.Popen'])}")


def canonical_sample(root, target, mode):
    from h_mad_target_identity import canonicalise, emit_canon, emit_doc_data

    with audit() as (events, _):
        identity = canonicalise(str(root), str(target))
        if mode != "current":
            oracle = Oracle(root)
            try:
                files, _ = discover(root, oracle)
                any_live(files)
            finally:
                oracle.close()
        if mode == "live":
            for directory in (root, identity.prefix or root):
                git(directory, "rev-parse", "--show-toplevel")
        emit_canon(identity)
        emit_doc_data(identity)
    print(len(events["subprocess.Popen"]))


def proto2(args):
    source = ("import runpy,sys; from pathlib import Path; "
              "probe=runpy.run_path(sys.argv[1]); sys.path.insert(0,str(probe['SCRIPTS'])); "
              "probe['canonical_sample'](Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])")
    times = {mode: [] for mode in ("current", "no-live", "live")}
    counts = {}
    for _ in range(args.runs):
        for mode in times:
            start = time.perf_counter()
            result = subprocess.run(
                [args.python, "-B", "-c", source, str(Path(__file__).resolve()),
                 str(args.root), str(args.target), mode],
                capture_output=True, text=True, timeout=30, check=True,
            )
            times[mode].append(time.perf_counter() - start)
            counts[mode] = int(result.stdout.splitlines()[-1])
    medians = {mode: statistics.median(samples) for mode, samples in times.items()}
    return " ".join(f"{mode}_ms={median * 1000:.3f} {mode}_git={counts[mode]}"
                    for mode, median in medians.items())


def target_names(root, raw):
    from h_mad_target_identity import canonical_directory, canonicalise

    path = root / raw
    pending = deque(path.parts[1:])
    place = Path(path.anchor)
    names = []
    for _ in range(40):
        while pending:
            part = pending.popleft()
            if part == "..":
                place = place.parent
                continue
            if part == ".":
                continue
            candidate = place / part
            if candidate.is_symlink():
                if ".." not in pending:
                    names.append(Path(canonical_directory(str(place))) / part / Path(*pending))
                link = candidate.readlink()
                if link.is_absolute():
                    place = Path(link.anchor)
                    pending.extendleft(reversed(link.parts[1:]))
                else:
                    pending.extendleft(reversed(link.parts))
                break
            place = candidate
        else:
            names.append(place)
            break
    identity = canonicalise(str(root), raw)
    if identity.target:
        target = Path(identity.target)
        names.append(target)
        names.extend(target.with_name(name) for name in identity.names)
    return tuple(dict.fromkeys(map(str, names)))


def folds_case(directory):
    device = directory.stat().st_dev
    for parent in (directory, *directory.parents):
        if parent.stat().st_dev != device:
            break
        for entry in parent.iterdir():
            swapped = entry.with_name(entry.name.swapcase())
            if swapped == entry:
                continue
            try:
                return swapped.samefile(entry)
            except FileNotFoundError:
                return False
    return None


def names(args):
    with tempfile.TemporaryDirectory(prefix="hmad-names-") as scratch:
        root = Path(scratch).resolve()
        (root / "nested/real").mkdir(parents=True)
        (root / "nested/.git").mkdir()
        (root / "123").mkdir()
        (root / "nested/Marker.py").touch()
        os.link(root / "nested/Marker.py", root / "nested/peer.py")
        for name, referent in (("alias", "nested/.git"), ("docs", "nested/real"),
                               ("dangling", "nested/absent"), ("indirect", "dangling"),
                               ("loop", "loop"), ("physical", "nested/real"),
                               ("hard-alias", "nested/peer.py")):
            (root / name).symlink_to(referent)
        targets = ("alias/HEAD", "docs/.bkit-memory.json", "indirect", "physical/../Marker.py",
                   "loop/file", "absent/parent/file", "nested/Marker.py", "nested/marker.py",
                   "nested/peer.py", "hard-alias", "123/absent", "docs")
        results = {target: len(target_names(root, target)) for target in targets}
    return (f"layouts={len(results)} name_counts={json.dumps(results, separators=(',', ':'))} "
            f"folds_case={folds_case(args.root)}")


ARMING_FIELDS = ("phase", "implementation_checkout", "phase5_stage")
MENTION = re.compile(r"(?<![a-z0-9_])(phase|implementation_checkout|phase5_stage)\s*=")
WRITER = SCRIPTS / "h_mad_state_write.py"


def bounded(argv):
    return (len(argv) >= 6 and argv[1:3] == ["run", "--timeout"] and argv[3].isdigit()
            and int(argv[3]) > 0 and argv[4] == "--")


def writer_name(tokens, root, cwd):
    from h_mad_target_identity import _command_path

    todo = list(tokens)
    seen = set()
    while todo:
        word = todo.pop()
        if word in seen:
            continue
        seen.add(word)
        cleaned = word.replace('"', '').replace("'", "")
        path = _command_path(cleaned, root, cwd)
        try:
            if path is not None and path.samefile(WRITER):
                return True
        except OSError:
            pass
        todo.extend(cleaned.split())
        try:
            todo.extend(shlex.split(word))
        except ValueError:
            pass
    return False


def probe_arming(argv, root, cwd):
    from h_mad_target_identity import _command_path, _safe_argv

    if _safe_argv(argv, root, cwd):
        while Path(argv[0]).name in {"hmad-dispatch", "hmad-dispatch.sh"} and bounded(argv):
            argv = argv[5:]
        if len(argv) < 2 or not Path(argv[0]).name.startswith("python"):
            return "none"
        if not writer_name([argv[1]], root, cwd):
            return "none"
        script = _command_path(argv[1], root, cwd)
        if script is None or not script.samefile(WRITER):
            return "none"
        keys = writer_keys(argv[2:])
        return "position" if keys.intersection(ARMING_FIELDS) else "none"
    text = " ".join(argv).replace('"', '').replace("'", "").casefold()
    return ("mention" if MENTION.search(text)
            and (WRITER.stem in text or writer_name(argv, root, cwd)) else "none")


def writer_keys(words):
    import h_mad_state_write as writer

    # At the baseline the parser belongs to main. Stop at its first call
    # after parse_args so classification cannot change the scratch store.
    class Parsed(Exception):
        pass

    with patch.object(writer, "_refuse_before_any_write", side_effect=Parsed) as parsed:
        try:
            with redirect_stderr(StringIO()):
                writer.main(words)
        except Parsed:
            args = parsed.call_args.args[0]
            values = [*args.set, *args.append]
            if all("=" in value for value in values):
                return {value.partition("=")[0].strip() for value in values}
        except SystemExit as error:
            if error.code != 2:
                raise
    return set()


def arming(args):
    from h_mad_target_identity import SIMPLE_SHELL_COMMAND, _argv_operator_allowed, _safe_argv

    counts = {route: 0 for route in ("position", "mention", "none")}
    with tempfile.TemporaryDirectory(prefix="hmad-arming-") as scratch:
        root = Path(scratch).resolve()
        state = write_state(root)
        (root / "nested").mkdir()
        (root / "nested/rename").symlink_to(WRITER)
        home = root / "home"
        home.mkdir()
        env = dict(PATH=os.defpath, HOME=str(home), TMPDIR=str(root), LC_ALL="C",
                   GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_CEILING_DIRECTORIES=str(root), PYTHONDONTWRITEBYTECODE="1")
        created = subprocess.run([sys.executable, str(WRITER), str(state), "--feature", "measure",
                                  "--create", "--started-ts", "2026-01-01T00:00:00Z"],
                                 env=env, cwd=root, capture_output=True, timeout=10, check=True)
        if b"STATE-WRITE: OK " not in created.stdout:
            raise ValueError("failed to initialize scratch store")
        initial = state.read_bytes()
        entry = ["python3", str(WRITER), str(state), "--feature", "measure"]
        commands = []
        for field in (*ARMING_FIELDS, "other", "prefix_phase", "phase_suffix"):
            assignment = field + "=step5"
            commands.extend((entry + ["--set", assignment], entry + ["--set=" + assignment],
                             ["grep", str(WRITER), assignment], ["git", "log", str(WRITER), assignment],
                             ["false", str(WRITER), assignment], ["false", "rename", assignment],
                             ["false", "rename", field, "=step5"],
                             ["false", "ordinary", assignment],
                             ["git", "show", assignment]))
        before = json.loads(initial)["orchestrator_state"]["measure"]
        changed = changed_hits = executed = writer_refusals = 0
        for argv in commands:
            command = shlex.join(argv)
            route = (probe_arming(argv, root, str(root / "nested"))
                     if SIMPLE_SHELL_COMMAND.fullmatch(command) else "none")
            counts[route] += 1
            state.write_bytes(initial)
            executable = sys.executable if argv[0] == "python3" else argv[0]
            result = subprocess.run([executable, *argv[1:]], cwd=root / "nested", env=env,
                                    stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
            executed += 1
            writer_refusals += int(argv[0] == "python3" and result.returncode == 2)
            after = json.loads(state.read_bytes())["orchestrator_state"]["measure"]
            if any(before.get(field) != after.get(field) for field in ARMING_FIELDS):
                changed += 1
                changed_hits += route != "none"
        cwd_cases = [(str(root / "nested"), True), (str(root), False), (None, False),
                     (str(root / "absent"), False), ("relative", False)]
        for cwd, expected in cwd_cases:
            hit = probe_arming(["false", "rename", "phase=step5"], root, cwd)
            if hit != ("mention" if expected else "none"):
                raise ValueError("relative writer identity differed from its command directory")
        wrapped = 0
        for verb in ("run", "send"):
            for number in ("1", "01", "0", "-1", "", "three", "000", "100"):
                for option in ("--timeout", "--out", "--timeout=1", ""):
                    for separator in ("--", "-", ""):
                        argv = [str(SCRIPTS.parent / "bin/hmad-dispatch"), verb, option, number,
                                separator, "git", "status"]
                        inner = argv[5:]
                        safe = bounded(argv) and _safe_argv(inner, root, str(root))
                        prefixes = [["git", "status"]]
                        operator = (bounded(argv) and number == str(int(number))
                                    and _argv_operator_allowed(inner, prefixes))
                        if _safe_argv(argv, root, str(root)) != safe:
                            raise ValueError("safe wrapper differs from the bounded form")
                        if _argv_operator_allowed(argv, prefixes) != operator:
                            raise ValueError("operator wrapper differs from the bounded form")
                        wrapped += 1
    return (f"commands={len(commands)} positions={counts['position']} "
            f"mentions={counts['mention']} controls={counts['none']} wrapper_cases={wrapped} "
            f"safe_comparisons={wrapped} operator_comparisons={wrapped} cwd_cases={len(cwd_cases)} "
            f"executed={executed} changed={changed} "
            f"changed_hits={changed_hits} writer_refusals={writer_refusals} "
            "historical_54=not-re-runnable reason=original-command-list-unavailable")


def failclosed(args):
    from xml.etree import ElementTree
    from differential import extract_old_tree

    revision = "5e36fac6"
    # Select the cases that actually build the three-function stub. Two
    # parametrized families also use the real hook for their other inputs.
    cases = {
        "judge": (
            "claude_gate_kind[judge-error]", "claude_gate_judge_timeout_stub",
            "judge_stub_is_judge_error", "state_stub_is_judge_error",
            "refusal_sites_use_the_chosen_form[malformed-judge]", "trap_member_refuses_in_form",
            "symlinked_hook_runs_its_own_trees_judge", "claude_canon_protocol_error_is_judge_error",
        ),
        "peers": ("hook_reads_authorship_from_the_state_line_not_the_environment",
                  "today_shape_state_line_is_judge_error", "unknown_author_field_is_judge_error"),
        "fallback_agent": ("state_stub_fallback_field_is_judge_error",
                           "state_stub_fallback_position_out_of_range_is_judge_error",
                           "state_stub_grok_fold_naming_a_non_grok_record_is_judge_error",
                           "state_stub_invalid_fold_naming_a_valid_record_is_judge_error",
                           "state_stub_agreeing_fold_refuses_its_own_kind"),
    }

    def change(source, before, after):
        if source.count(before) != 1:
            raise ValueError(f"expected one fixture anchor: {before!r}")
        return source.replace(before, after)

    with tempfile.TemporaryDirectory(prefix="hmad-failclosed-") as scratch:
        directory = Path(scratch).resolve()
        skill = extract_old_tree(directory / "tree", revision) / "h-mad"
        tests = skill / "tests"
        tests.mkdir()
        ids = []
        files = ["tdd_gate_support.py"]
        for suite, names in cases.items():
            filename = f"test_h_mad_tdd_gate_{suite}.py"
            files.append(filename)
            ids.extend(f"{filename}::test_{name}" for name in names)
        for filename in files:
            content = git(SCRIPTS.parent.parent, "show", f"{revision}:h-mad/tests/{filename}", check=True)
            (tests / filename).write_bytes(content.stdout)

        hook = skill / "hooks/h-mad-tdd-gate.sh"
        source = hook.read_text()
        home = directory / "home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("PYTEST_", "HMAD_", "CLAUDE", "CODEX", "GIT_"))}
        env.update(HOME=str(home), TMPDIR=str(directory), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        xml = directory / "results.xml"

        def observe(body, selected):
            hook.write_text(body)
            result = subprocess.run(
                [sys.executable, "-I", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                 "--junitxml", str(xml), *selected], cwd=tests, env=env,
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode not in (0, 1):
                raise ValueError(f"stub suite failed to run: {result.stdout[-1200:]} {result.stderr}")
            outcomes = {}
            for case in ElementTree.parse(xml).iter("testcase"):
                if case.find("error") is not None or case.find("skipped") is not None:
                    raise ValueError(f"unexpected test outcome: {case.attrib}")
                failure = case.find("failure")
                if failure is not None and "AssertionError" not in (failure.text or ""):
                    raise ValueError(f"stub fixture error: {failure.text}")
                outcomes[(case.get("classname"), case.get("name"))] = failure is None
            if not outcomes:
                raise ValueError("stub suite produced no cases")
            return outcomes

        baseline = observe(source, ids)
        if not all(baseline.values()):
            raise ValueError(f"baseline failed: {[k for k in baseline if not baseline[k]]}")
        if args.stub == "stub-edited":
            helper = tests / "test_h_mad_tdd_gate_judge.py"
            method = "\ndef emit_arming(root, raw, record):\n    print('arming none')\n"
            helper.write_text(change(helper.read_text(), "    return hook, tree",
                '    with identity.open("a") as stub:\n'
                f'        stub.write({method!r})\n'
                '    return hook, tree'))

        emit = ("import h_mad_target_identity as identity;"
                "getattr(identity,\"emit_arming\",lambda *a:print(\"arming missing\"))"
                "(sys.argv[2],sys.argv[3],i);emit_canon(i);")
        guarded = change(source, "emit_canon(i);", emit)
        guarded = change(guarded, "\nDOC_DATA_LINE=", '\nARMING=\n'
                         'if [[ "$CANON_RECORD" == *$\'\\n\'* ]]; then\n'
                         '  ARMING=${CANON_RECORD%%$\'\\n\'*}\n'
                         '  CANON_RECORD=${CANON_RECORD#*$\'\\n\'}\nfi\nDOC_DATA_LINE=')
        guarded = change(guarded, "_allow() { DECIDED=", '_allow() { '
                         '[ "${ARMING:-}" = "arming none" ] || _refuse arming-input "missing arming response"; DECIDED=')
        modes = {"allow": guarded}
        if args.mode == "fc":
            modes["head"] = change(guarded, "\n_read_canon\n",
                '\n[ "$ARMING" = "arming none" ] || _refuse arming-input "missing arming response"\n_read_canon\n')
            modes["required-import"] = change(source, "import canonicalise,emit_canon,emit_doc_data;",
                                              "import canonicalise,emit_canon,emit_doc_data,emit_arming;")
        fields = [f"cases={len(baseline)}", f"baseline={sum(baseline.values())}"]
        for mode, body in modes.items():
            observed = observe(body, ids)
            if observed.keys() != baseline.keys():
                raise ValueError("stub corpus changed between runs")
            fields.append(f"{mode}_changed={sum(not passed for passed in observed.values())}")
            if mode in ("allow", "required-import"):
                # Distinguish a reached refusal from an earlier missing import
                # yielding the same kind. Both controls still refuse the input.
                marked = change(body, 'if [ "$JRC" = 0 ] && [[ $JOUT =~ $JUDGE_ALLOW_RE ]];',
                                'if [ "$JRC" != 0 ] && [[ $JOUT =~ $JUDGE_ALLOW_RE ]]; then '
                                '_refuse arming-input "judge status control"; fi\n'
                                'if [ "$JRC" = 0 ] && [[ $JOUT =~ $JUDGE_ALLOW_RE ]];')
                marked = change(marked, '_refuse judge-error "invalid CANON header"',
                                '_refuse arming-input "invalid CANON header"')
                sample = [next(i for i in ids if i.endswith("::test_" + name))
                          for name in ("judge_stub_is_judge_error", "claude_canon_protocol_error_is_judge_error")]
                checks = observe(marked, sample)
                for label, needle in (("H4", "allow-rc1"), ("CANON1", "version-2")):
                    matching = [key for key in checks if needle in key[1]]
                    if len(matching) != 1:
                        raise ValueError(f"missing {label} protocol case")
                    key = matching[0]
                    fields.append(f"{mode}_{label}_detected={int(observed[key] != checks[key])}")
    return " ".join(fields + ["historical_38=not-re-runnable",
                              "reason=original-stub-case-selection-unavailable"])

def directory(value):
    path = Path(value).resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"expected a directory: {value}")
    return path


def positive(value):
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("expected a positive number of runs")
    return count


@probe_main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parts = parser.add_subparsers(dest="part", required=True)
    for part in PARTS:
        command = parts.add_parser(part)
        if part in {"fx", "fx2"}:
            command.add_argument("directory", type=directory, nargs="?", default=Path.cwd())
        elif part != "failclosed":
            command.add_argument("root", type=directory)
        if part == "fx":
            command.add_argument("--layout", choices=("f_wide", "f_trees", "f_subs", "f_nested", "f_small",
                                                       "f_none", "f_many", "f_nogit"))
        elif part == "disc":
            command.add_argument("runs", type=positive)
            command.add_argument("mode", nargs="?", choices=("plain",))
        elif part == "ev2":
            command.add_argument("trees", nargs="+")
        elif part == "proto2":
            command.add_argument("target", type=Path)
            command.add_argument("--runs", type=positive, default=21)
            command.add_argument("--python", default=sys.executable)
        elif part == "failclosed":
            command.add_argument("mode", choices=("fc", "allow"))
            command.add_argument("stub", nargs="?", choices=("stub-edited",))
        elif part == "chain":
            command.add_argument("target", type=Path)
            command.add_argument("mode", choices=("shared", "own"))
            command.add_argument("runs", type=positive)

    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        if error.code not in (0, 2):
            raise
        return int(error.code)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SCRIPTS))
    reading = globals()[args.part](args)
    print(f"DISCOVERY: part={args.part} {reading}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
