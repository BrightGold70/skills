"""Canonical filesystem identity and policy shared by both H-MAD TDD write gates."""
from __future__ import annotations

import fcntl
from functools import cache
from importlib import import_module
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import sys
from typing import Any, NamedTuple


PY_SUFFIXES = (".py", ".pY", ".Py", ".PY")


class Identity(NamedTuple):
    root: str
    target: str
    prefix: str
    names: tuple[str, ...]
    unresolvable: bool
    arm: int
    component: str


def _path_from_fd(fd: int, fallback: str) -> str:
    if not hasattr(fcntl, "F_GETPATH"):
        return os.path.realpath(fallback)
    path = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))
    return os.fsdecode(path.rstrip(b"\0"))


def canonical_directory(path: str) -> str:
    fd = os.open(path, os.O_RDONLY)
    try:
        return _path_from_fd(fd, path)
    finally:
        os.close(fd)


def _on_disk_component(component: str) -> str:
    try:
        info = os.stat(component)
        parent = os.path.dirname(component)
        with os.scandir(parent) as entries:
            names = sorted(
                entry.name for entry in entries
                if not entry.is_symlink()
                and (entry_info := entry.stat(follow_symlinks=False)).st_dev == info.st_dev
                and entry_info.st_ino == info.st_ino
            )
        if names:
            component = os.path.join(parent, names[0])
    except OSError:
        pass
    return component


def canonicalise(root: str, target: str, cwd: str | None = None) -> Identity:
    spelled_root = os.path.abspath(root)
    try:
        canonical_root = canonical_directory(spelled_root)
    except OSError:
        return Identity(spelled_root, "", spelled_root, (), True, 2,
                        _on_disk_component(spelled_root))

    if not target:
        return Identity(canonical_root, "", canonical_root, (), False, 0, "")

    base = canonical_root
    if cwd and not os.path.isabs(target):
        resolved_cwd = os.path.realpath(cwd)
        if (os.path.isdir(resolved_cwd)
                and os.path.commonpath((canonical_root, resolved_cwd)) == canonical_root):
            try:
                base = canonical_directory(cwd)
            except OSError:
                base = resolved_cwd

    spelled_target = os.path.join(base, target)
    current = os.path.sep
    deepest_directory = current
    deepest_directory_index = -1
    referent_stat = None
    absent = False
    components = spelled_target.split(os.path.sep)
    for index, part in enumerate(components):
        if not part or part == ".":  # M:TI10 a kept `.` would make the next `..` strip only itself
            continue
        if part == "..":
            try:
                if stat.S_ISLNK(os.lstat(current).st_mode):
                    current = os.path.dirname(canonical_directory(current))
                else:
                    # N-1: an existing non-symlink directory's spelled parent is
                    # its physical parent; opening it would refuse an x-only one.
                    current = os.path.dirname(current)
            except OSError:
                return Identity(canonical_root, "", current, (), True, 2,
                                _on_disk_component(current))
        else:
            current = os.path.join(current, part)
        try:
            os.lstat(current)
        except OSError:
            absent = True
            break
        try:
            referent_stat = os.stat(current)
        except FileNotFoundError:  # M:TI4
            try:
                prefix = canonical_directory(deepest_directory)
            except OSError:
                return Identity(canonical_root, "", deepest_directory, (), True, 2,
                                _on_disk_component(deepest_directory))
            return Identity(canonical_root, "", prefix, (), True, 1, current)
        except OSError:  # M:TI5
            try:
                prefix = canonical_directory(deepest_directory)
            except OSError:
                return Identity(canonical_root, "", deepest_directory, (), True, 2,
                                _on_disk_component(deepest_directory))
            return Identity(canonical_root, "", prefix, (), True, 1, current)
        if stat.S_ISDIR(referent_stat.st_mode):
            deepest_directory = current
            deepest_directory_index = index

    if absent:
        try:
            prefix = canonical_directory(deepest_directory)
        except OSError:
            return Identity(canonical_root, "", deepest_directory, (), True, 2,
                            _on_disk_component(deepest_directory))
        canonical_target = os.path.normpath(
            os.path.join(prefix, *components[deepest_directory_index + 1:]))
        return Identity(canonical_root, canonical_target, prefix,
                        (os.path.basename(canonical_target),), False, 0, "")

    if referent_stat is None:
        referent_stat = os.stat(current)

    if stat.S_ISDIR(referent_stat.st_mode):
        try:
            canonical_target = canonical_directory(current)
        except OSError:
            return Identity(canonical_root, "", current, (), True, 2,
                            _on_disk_component(current))
        return Identity(canonical_root, canonical_target, canonical_target, (), False, 0, "")

    referent_path = current
    if stat.S_ISLNK(os.lstat(current).st_mode):
        try:
            fd = os.open(current, os.O_RDONLY)
            try:
                referent_path = _path_from_fd(fd, current)
                referent_stat = os.fstat(fd)
            finally:
                os.close(fd)
        except OSError:
            return Identity(canonical_root, "", current, (), True, 2,
                            _on_disk_component(current))

    parent = os.path.dirname(referent_path)
    try:
        prefix = canonical_directory(parent)
    except OSError:
        return Identity(canonical_root, "", parent, (), True, 2,
                        _on_disk_component(parent))
    try:
        with os.scandir(prefix) as entries:
            matching = []
            for entry in entries:
                if entry.is_symlink():
                    continue
                info = entry.stat(follow_symlinks=False)
                if (info.st_dev, info.st_ino) == (referent_stat.st_dev,
                                                   referent_stat.st_ino):
                    matching.append(entry.name)
            names = tuple(sorted(matching))
    except OSError:
        return Identity(canonical_root, "", prefix, (), True, 2,
                        _on_disk_component(parent))
    if not names:
        return Identity(canonical_root, "", prefix, (), True, 2,
                        _on_disk_component(parent))
    return Identity(canonical_root, os.path.join(prefix, names[0]), prefix,
                    names, False, 0, "")


def fold_py_suffix(name: str) -> str:
    for suffix in PY_SUFFIXES:
        if name.endswith(suffix):
            return name[:-len(suffix)] + ".py"
    return name


def _encode_field(value: str) -> str:
    return "".join(
        chr(byte) if (48 <= byte <= 57 or 65 <= byte <= 90
                      or 97 <= byte <= 122 or byte in b"/-._")
        else f"%{byte:02X}"
        for byte in os.fsencode(value)
    )


def emit_canon(identity: Identity) -> None:
    print("CANON 1")
    print("root " + _encode_field(identity.root))
    print("target " + _encode_field(identity.target))
    print("prefix " + _encode_field(identity.prefix))
    print("unresolvable " + ("yes" if identity.unresolvable else "no"))
    print("arm " + str(identity.arm))
    print("component " + _encode_field(identity.component))
    print("names " + str(len(identity.names)))
    for name in identity.names:
        print("name " + _encode_field(name))


SIMPLE_SHELL_COMMAND = re.compile(r"[A-Za-z0-9_./:@%+=,'\" \t-]+")
READ_ONLY_COMMANDS = {"cat", "grep", "head", "jq", "ls", "pwd", "shasum", "tail", "wc"}
SAFE_DISPATCH_VERBS = {
    "alive", "await", "clear", "collect-report", "env", "file-diff", "gate-create",
    "gate-resolve", "gate-wait", "interrupt", "notify", "pin", "pin-agents",
    "progress", "read", "report-wait", "resolve", "resolved-model", "verify", "wait",
    "worktree-comment", "worktree-current", "worktree-list", "worktree-ps",
}
SAFE_HMAD_SCRIPT_OPTIONS = {
    "h_mad_assemble_tdd.py": {
        "--effort", "--expect-fail", "--expect-pass", "--feature", "--guard", "--impl-plan",
        "--log", "--model", "--module", "--out", "--phase", "--project-root", "--prompt",
        "--report-file", "--sandbox", "--task", "--template", "--test-path", "--timeout",
    },
    "h_mad_baseline_sha.py": {"--branch", "--repo", "--trunk"},
    "h_mad_context_budget.py": {"--ceiling", "--cwd", "--host", "--mode", "--transcript", "--window"},
    "h_mad_do_preconditions.py": {"--feature", "--repo-root"},
    "h_mad_extract_verdict.py": {"--after-marker", "--allowed", "--feature", "--key", "--phase"},
    "h_mad_identifier_sweep.py": {"--allow", "--include-history", "--root"},
    "h_mad_mutation_harness.py": {"--check-anchors"},
    "h_mad_resume_decision.py": {
        "--state", "--feature", "--host", "--session-id", "--now", "--session-id-from-git-dir",
    },
    "h_mad_state_validate.py": {"--feature", "--strict-only"},
    "h_mad_state_write.py": {
        "--beat", "--claim", "--create", "--drop-undeclared", "--feature", "--force",
        "--release", "--session-id", "--set", "--started-ts",
    },
    "h_mad_wire_pin_gate.py": {"--feature", "--registry"},
    "h_mad_wire_registry.py": {
        "--ack", "--ack-file", "--base", "--boundaries", "--impl-plan", "--registry",
        "--repo", "--rootdir", "--testpath",
    },
}
TEMP_OUTPUT_OPTIONS = {"--log", "--out", "--prompt", "--report-file"}
# Operator-declared argv prefixes admitted through Bash during step5, for work
# unrelated to the feature (a manuscript run). Codex may not write this file
# while step5 is active, or a worker could grant itself any command.
SHELL_ALLOW_FILE = ".h-mad/phase5-shell-allow"
TRUSTED_BIN_DIRS = {
    Path("/bin"),
    Path("/usr/bin"),
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
    Path(sys.executable).resolve().parent,
}
MALFORMED_WORKDIR = object()  # a workdir codex sent that is not a string


def _read_regular_text(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):  # M:G4
            raise OSError("not a regular file")
        chunks = []
        while chunk := os.read(descriptor, 65536):
            chunks.append(chunk)
        return b"".join(chunks).decode("utf-8")
    finally:
        os.close(descriptor)


def _state_status(state_file: Path) -> str:
    try:
        text = _read_regular_text(state_file)
        state = json.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "unknown"
    records = state.get("orchestrator_state", {})
    if not isinstance(records, dict):
        return "unknown"
    active = any(
        isinstance(value, dict) and value.get("phase") == "step5"
        for value in records.values()
    )
    return "active" if active else "inactive"


def _any_phase5_status(root: Path) -> str:
    statuses = [_state_status(path) for path in root.rglob("docs/.bkit-memory.json")]
    if "active" in statuses:
        return "active"
    if "unknown" in statuses:
        return "unknown"
    return "inactive"


def _payload_cwd_base(root: Path, cwd: Any) -> Path:
    if isinstance(cwd, str) and cwd:  # M:G1
        candidate = Path(cwd).expanduser().resolve()
        if candidate.is_dir() and (candidate == root or root in candidate.parents):  # M:G7
            return candidate
    return root


def _is_production_python(relative: str) -> bool:
    path = Path(fold_py_suffix(relative))
    name = path.name
    if path.suffix != ".py":
        return False
    if name.startswith("test_") or name.endswith("_test.py") or name.startswith("conftest"):
        return False
    # docs/ first-component rule (same rule as the Claude gate's M:H-DOCS case):
    # `relative` is the kernel-canonical path relative to the project root, so a .py
    # under the root's own docs/ tree (committed probes, readings scripts) is not
    # production. Only the FIRST component counts: src/docs/foo.py and a top-level
    # docs.py stay gated. Residual: anything the project places under its root
    # docs/ is ungated, including an importable package it chose to put there; a
    # docs/ spelling whose symlinks resolve outside docs/ is judged by its target.
    if path.parts[:1] == ("docs",):  # M:G-DOCS
        return False
    return "tests" not in path.parts and "fixtures" not in path.parts


def _trusted_executable(token: str) -> Path | None:
    if "/" in token:
        candidate = Path(token).expanduser()
    else:
        found = shutil.which(token)
        if not found:
            return None
        candidate = Path(found)
    resolved = candidate.resolve()
    hmad_dispatch = (Path(__file__).resolve().parents[1] / "bin" / "hmad-dispatch").resolve()
    if resolved == hmad_dispatch:
        return resolved
    return resolved if candidate.parent in TRUSTED_BIN_DIRS else None


def _cwd_escapes_root(root: Path, cwd: object) -> bool:
    """A named cwd that does not resolve inside the root (absent, outside, `..`-escaped).

    `_payload_cwd_base` falls such a cwd back to the root, which is right for judging
    a write target and wrong for a relative interpreter: the command runs in the
    named directory, so resolving its token under the root would vouch for a venv
    the command never executes.
    """
    if cwd is MALFORMED_WORKDIR:
        return True
    if not isinstance(cwd, str) or not cwd:
        return False
    return _payload_cwd_base(root, cwd) == root and Path(cwd).expanduser().resolve() != root


def _contained_venv_executable(token: str, root: Path, cwd: object) -> Path | None:
    if "/" not in token:
        return None
    if not os.path.isabs(os.path.expanduser(token)) and _cwd_escapes_root(root, cwd):  # M:F2-ESCAPE
        return None
    path = Path(os.path.normpath(os.path.join(str(_payload_cwd_base(root, cwd)), os.path.expanduser(token))))  # M:G10
    if not (path.name.startswith("python") and path.parent.name == "bin" and path.parent.parent.name == ".venv"):
        return None
    if not path.is_file():
        return None
    if not _load_judge().venv_contained(path.parent.parent.parent, root):  # M:G6
        return None
    return path  # M:G3


def _path_within(path: str, parent: Path) -> bool:
    candidate = Path(path).expanduser()
    candidate = candidate.resolve() if candidate.is_absolute() else (Path.cwd() / candidate).resolve()
    try:
        candidate.relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _option_value(args: list[str], option: str) -> str | None:
    for index, token in enumerate(args):
        if token == option and index + 1 < len(args):
            return args[index + 1]
        if token.startswith(option + "="):
            return token.split("=", 1)[1]
    return None


def _safe_hmad_script(script: Path, args: list[str], root: Path) -> bool:
    allowed_options = SAFE_HMAD_SCRIPT_OPTIONS.get(script.name)
    if allowed_options is None:
        return False
    for token in args:
        if token.startswith("--") and token.split("=", 1)[0] not in allowed_options:
            return False
        if token.startswith("-") and not token.startswith("--"):
            return False

    if script.name == "h_mad_state_write.py":
        return bool(args) and not args[0].startswith("-") and Path(args[0]).name == ".bkit-memory.json" \
            and _path_within(args[0], root / "docs")
    if script.name == "h_mad_wire_pin_gate.py":
        if not args or args[0].startswith("-") or not args[0].endswith(".impl-plan.md"):
            return False
        registry = _option_value(args, "--registry")
        return _path_within(args[0], root) and (registry is None or _path_within(registry, root / ".h-mad"))
    if script.name == "h_mad_mutation_harness.py":
        # Only the read-only anchor check: a full run writes mutants into
        # production code. Every spec it reads must be inside the project.
        specs = [token for token in args if not token.startswith("-")]
        return ("--check-anchors" in args and bool(specs)  # M:CX-MUT-ANCHORS
                and all(_path_within(spec, root) for spec in specs))
    if script.name == "h_mad_wire_registry.py":
        return bool(args) and args[0] in {"challenge", "verify"}
    if script.name == "h_mad_assemble_tdd.py":
        return all(
            (value := _option_value(args, option)) is None or _path_within(value, Path("/tmp"))
            for option in TEMP_OUTPUT_OPTIONS
        )
    return True


def _safe_shell_command(command: str, root: Path | None = None, cwd: object = None) -> bool:
    # The command will ultimately be evaluated by the user's shell.  Accept a
    # deliberately small lexical subset instead of trying to enumerate every
    # execution primitive supported by bash/zsh (for example, zsh's `=(...)`
    # and executable glob qualifiers).  Complex read commands can be split or
    # run outside an active H-MAD step5 gate.
    if not command or SIMPLE_SHELL_COMMAND.fullmatch(command) is None:
        return False
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    return _safe_argv(argv, root, cwd)


def _shell_allowance(root: Path) -> list[list[str]] | str:
    """The operator's declared prefixes, or why they cannot be trusted."""
    try:
        text = _read_regular_text(root / SHELL_ALLOW_FILE)
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as exc:
        return f"{SHELL_ALLOW_FILE} is unreadable ({exc})"
    prefixes = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            return f"{SHELL_ALLOW_FILE}:{number} cannot be parsed ({exc})"  # M:SA-PARSE
        prefixes.append(tokens)
    return prefixes


def _operator_allowed(command: str, prefixes: list[list[str]]) -> bool:
    if SIMPLE_SHELL_COMMAND.fullmatch(command) is None:  # M:SA-LEXICAL
        return False
    try:
        argv = shlex.split(command)
    except ValueError:
        return False
    return _argv_operator_allowed(argv, prefixes)


def _argv_operator_allowed(argv: list[str], prefixes: list[list[str]]) -> bool:
    if not argv or shutil.which(argv[0]) is None:  # M:SA-RESOLVE
        return False
    if any(argv[:len(prefix)] == prefix for prefix in prefixes):  # M:SA-PREFIX
        return True
    # `hmad-dispatch run --timeout N -- <cmd>` runs <cmd> under a timeout: admit it
    # when <cmd> itself is declared, so one allow line covers both spellings (row
    # 2756). Only h-mad's own wrapper, in exactly the shape `_safe_argv` admits.
    hmad_dispatch = (Path(__file__).resolve().parents[1] / "bin" / "hmad-dispatch").resolve()
    return (_trusted_executable(argv[0]) == hmad_dispatch  # M:SA-RUN-WRAPPER
            and len(argv) >= 6 and argv[1:3] == ["run", "--timeout"]
            # No leading zero: bash reads `08` as bad octal and the wrapper dies.
            and argv[3].isdigit() and argv[3] == str(int(argv[3])) and int(argv[3]) >= 1
            and argv[4:5] == ["--"]  # M:SA-RUN-SHAPE
            and _argv_operator_allowed(argv[5:], prefixes))  # M:SA-RUN-INNER


def _is_shell_allowance(root: Path, resolved: Identity) -> bool:
    parent = Path(resolved.target).parent
    for candidate in (Path(resolved.target), *(parent / name for name in resolved.names)):
        if candidate.relative_to(root).as_posix().casefold() == SHELL_ALLOW_FILE:  # M:SA-FOLD
            return True
    return False


def _safe_argv(argv: list[str], root: Path | None, cwd: object) -> bool:
    if not argv:
        return False
    if "=" in argv[0] and not argv[0].startswith(("/", ".")):
        return False
    resolved_executable = (_contained_venv_executable(argv[0], root, cwd) if root is not None else None) or _trusted_executable(argv[0])  # M:G9
    if resolved_executable is None:
        return False
    executable = resolved_executable.name
    if executable in {"pytest", "py.test"}:
        return True
    if executable.startswith("python") and len(argv) >= 3 and argv[1:3] == ["-m", "pytest"]:
        return True
    if executable in READ_ONLY_COMMANDS:
        return True
    if executable in {"hmad-dispatch", "hmad-dispatch.sh"}:
        expected = (Path(__file__).resolve().parents[1] / "bin" / "hmad-dispatch").resolve()
        if resolved_executable != expected or len(argv) < 2:
            return False
        if argv[1] == "run":  # M:CX-RUN
            # `run --timeout <s> -- <cmd...>` executes <cmd>: admit it only in
            # exactly that shape and only when <cmd> is itself trusted.
            return (len(argv) >= 6 and argv[2] == "--timeout" and argv[3].isdigit()
                    and int(argv[3]) > 0 and argv[4] == "--"
                    and _safe_argv(argv[5:], root, cwd))  # M:CX-RUN-INNER
        return argv[1] in SAFE_DISPATCH_VERBS
    if executable.startswith("python") and len(argv) >= 2:
        script = Path(os.path.expandvars(argv[1])).expanduser()
        script = script.resolve() if script.is_absolute() else (Path.cwd() / script).resolve()
        scripts_root = (Path(__file__).resolve().parents[1] / "scripts").resolve()
        try:
            script.relative_to(scripts_root)
        except ValueError:
            return False
        return _safe_hmad_script(script, argv[2:], root or Path.cwd())
    return False


@cache
def _load_judge() -> Any:
    scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module("h_mad_tdd_judge")
