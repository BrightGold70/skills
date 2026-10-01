#!/usr/bin/env python3
"""Codex PreToolUse gate for H-MAD Phase 5.

The Claude hook cannot be reused: it treats any hooked production write as
Claude self-authoring and it cannot see apply_patch targets. This adapter parses
Codex hook payloads, gates recognized Python writes, and refuses opaque shell
mutations while a feature is in step5. It is a workflow guard, not an OS
sandbox: pytest and the exact H-MAD control allowlist are trusted code.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
from functools import cache
from importlib import import_module
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from h_mad_target_identity import Identity


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
TRUSTED_BIN_DIRS = {
    Path("/bin"),
    Path("/usr/bin"),
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
    Path(sys.executable).resolve().parent,
}


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


def _payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _canonical_root(path: Path) -> Path | Identity:
    identity = _load_identity()
    try:
        return Path(identity.canonical_directory(str(path)))
    except OSError:
        return identity.Identity(str(path), "", str(path), (), True, 2, identity._on_disk_component(str(path)))


def _project_root(payload: dict[str, Any]) -> Path | Identity:
    explicit = os.environ.get("CODEX_PROJECT_DIR")
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_dir():
            return _canonical_root(path)

    for candidate in (payload.get("project_dir"), payload.get("cwd"), os.getcwd()):
        if not candidate:
            continue
        path = Path(str(candidate)).expanduser()
        if not path.is_dir():
            continue
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _canonical_root(Path(result.stdout.strip()).expanduser())
        return _canonical_root(path)
    return _canonical_root(Path.cwd())


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


class TargetParse(NamedTuple):
    tool: str
    paths: list[str]
    command: str
    bad_header: str


def _patch_header_paths(patch: str) -> tuple[list[str], str]:
    markers = (
        "*** Add File: ", "*** Update File: ",
        "*** Delete File: ", "*** Move to: ",
    )
    paths: list[str] = []
    bad_header = ""
    for line in patch.split("\n"):
        start, end = 0, len(line)
        while start < end and line[start].isspace() and not "\x1c" <= line[start] <= "\x1f":
            start += 1
        while end > start and line[end - 1].isspace() and not "\x1c" <= line[end - 1] <= "\x1f":
            end -= 1
        header = line[start:end]
        for marker in markers:
            if header == marker[:-1]:
                if not bad_header:
                    bad_header = header
                break
            if header.startswith(marker):
                path = header[len(marker):]
                if not path or any(ord(char) < 0x20 or ord(char) == 0x7f for char in path):
                    if not bad_header:
                        bad_header = header
                else:
                    paths.append(path)
                break
    return paths, bad_header


def _targets(payload: dict[str, Any]) -> TargetParse:
    tool = str(payload.get("tool_name") or "")
    raw = payload.get("tool_input")
    args = raw if isinstance(raw, dict) else {}
    if tool in {"Write", "Edit"}:
        path = str(args.get("file_path") or args.get("path") or "")
        return TargetParse(tool, [path] if path else [], "", "")
    if tool == "apply_patch":
        patch = str(args.get("patch") or args.get("command") or "")
        paths, bad_header = _patch_header_paths(patch)
        return TargetParse(tool, paths, "", bad_header)
    if tool in {"exec_command", "shell_command", "shell", "Bash", "Shell"}:
        command = str(args.get("cmd") or args.get("command") or "")
        return TargetParse(tool, [], command, "")
    return TargetParse(tool, [], "", "")


def _payload_cwd_base(root: Path, cwd: Any) -> Path:
    if isinstance(cwd, str) and cwd:  # M:G1
        candidate = Path(cwd).expanduser().resolve()
        if candidate.is_dir() and (candidate == root or root in candidate.parents):  # M:G7
            return candidate
    return root


def _relative_target(root: Path, raw: str, cwd: Any = None) -> Identity | None:
    identity = _load_identity()
    try:
        base = _payload_cwd_base(root, cwd)
    except RuntimeError:
        base = root
    if isinstance(cwd, str) and cwd and base != root:
        try:
            base = Path(identity.canonical_directory(str(Path(cwd).expanduser())))
            try:
                base = _payload_cwd_base(root, str(base))
            except RuntimeError:
                base = root
        except OSError:
            try:
                base = _payload_cwd_base(root, cwd)
            except RuntimeError:
                base = root
    resolved = identity.canonicalise(str(root), str(Path(raw).expanduser()), str(base))
    if resolved.unresolvable:
        return resolved
    try:
        Path(resolved.target).relative_to(root)
    except ValueError:
        return None
    return resolved


def _is_production_python(relative: str) -> bool:
    path = Path(_load_identity().fold_py_suffix(relative))
    name = path.name
    if path.suffix != ".py":
        return False
    if name.startswith("test_") or name.endswith("_test.py") or name.startswith("conftest"):
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


def _contained_venv_executable(token: str, root: Path, cwd: object) -> Path | None:
    if "/" not in token:
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


@cache
def _load_identity() -> Any:
    scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module("h_mad_target_identity")


def main() -> int:
    if sys.argv[1:] == ["--self-check"]:
        if any(_patch_header_paths(patch) != (["src/prod.py"], "") for patch in (
            "*** Update File: src/prod.py\n",
            "*** Update File: src/prod.py \n",
            "  *** Update File: src/prod.py\n",
        )):
            print("CODEX-TDD-GATE: FAIL parser", file=sys.stderr)
            return 2
        unsafe = (
            "python3 -c \"open('x','w').write('x')\"",
            "git status =(/tmp/evil)",
            "rg --pre=/tmp/evil needle .",
            "git diff --ext-diff",
        )
        if any(_safe_shell_command(command) for command in unsafe):
            print("CODEX-TDD-GATE: FAIL shell-policy", file=sys.stderr)
            return 2
        print("CODEX-TDD-GATE: PASS")
        return 0

    try:
        return _main_guarded()
    except Exception as exc:  # M:G2
        return _deny(f"H-MAD Phase 5 gate raised {type(exc).__name__}: {exc}; refusing fail-closed. kind=judge-error")


def _main_guarded() -> int:

    payload = _payload()
    root = _project_root(payload)
    if not isinstance(root, Path):
        if not os.access(root.root, os.X_OK):  # M:CX-ROOT-ENTER (D-2: rglob sees no state under it)
            return _deny(f"H-MAD project root cannot be entered ({root.component}); refusing fail-closed. kind=judge-error")
        try:
            phase5_status = _any_phase5_status(Path(root.component))
        except OSError:
            phase5_status = "unknown"
        if phase5_status in {"active", "unknown"}:
            return _deny(f"H-MAD Phase 5 root is unreadable ({root.component}); refusing fail-closed. kind=judge-error")
        return 0
    tool, targets, command, bad_header = _targets(payload)
    phase5_status = _any_phase5_status(root)

    if bad_header and phase5_status in {"active", "unknown"}:
        return _deny(f"H-MAD Phase 5 patch has a bad header {bad_header!r}; refusing fail-closed. kind=judge-error")

    if command and phase5_status == "unknown":
        return _deny("H-MAD state is unreadable; refusing shell execution fail-closed.")
    if command and phase5_status == "active" and not _safe_shell_command(command, root, payload.get("cwd")):
        return _deny(
            "H-MAD Phase 5 permits only explicit test, read-only, and H-MAD control commands "
            "through Bash. Use apply_patch for writes so the Codex TDD gate can verify a "
            "failing test first."
        )

    if tool in {"Write", "Edit", "apply_patch"} and not targets and phase5_status in {"active", "unknown"}:
        return _deny("H-MAD Phase 5 could not identify this write target; refusing fail-closed.")

    for raw in targets:  # M:G5
        resolved = _relative_target(root, raw, payload.get("cwd"))
        if resolved is None:
            if phase5_status in {"active", "unknown"}:
                return _deny("H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.")
            continue
        if resolved.unresolvable:
            if phase5_status in {"active", "unknown"}:
                return _deny(f"H-MAD Phase 5 target is unresolvable ({resolved.component}); refusing fail-closed. kind=judge-error")
            continue
        production = []
        for name in resolved.names:
            absolute = Path(resolved.target).parent / name
            relative = absolute.relative_to(root).as_posix()
            if _is_production_python(relative):
                production.append((name, absolute, relative))
        if not production:
            continue
        _, absolute, relative = min(production)
        judge = _load_judge()
        chain = judge.read_chain(root, absolute)  # M:W5A
        if chain.value == "unreadable":
            return _deny(f"H-MAD state governing this write is unreadable ({chain.error_file}: {chain.error}); refusing fail-closed. kind=judge-error")
        if chain.value != "active":
            continue
        verdict = judge.judge(root, absolute, chain.records)  # M:W1
        if verdict.decision != "ALLOW":
            return _deny(f"H-MAD Phase 5 requires a failing test before {relative}: kind={verdict.kind}; {verdict.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
