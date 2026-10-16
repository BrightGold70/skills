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
import subprocess
import sys
from functools import cache
from importlib import import_module
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from h_mad_target_identity import Identity


_POLICY_IMPORT_ERROR = None
try:
    scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from h_mad_target_identity import (
        SIMPLE_SHELL_COMMAND,
        READ_ONLY_COMMANDS,
        SAFE_DISPATCH_VERBS,
        SAFE_HMAD_SCRIPT_OPTIONS,
        TEMP_OUTPUT_OPTIONS,
        SHELL_ALLOW_FILE,
        TRUSTED_BIN_DIRS,
        MALFORMED_WORKDIR,
        _contained_venv_executable,
        _cwd_escapes_root,
        _load_judge,
        _option_value,
        _path_within,
        _payload_cwd_base,
        _safe_argv,
        _safe_hmad_script,
        _safe_shell_command,
        _trusted_executable,
        _shell_allowance,
        _operator_allowed,
        _is_shell_allowance,
        _read_regular_text,
        _state_status,
        _any_phase5_status,
        _is_production_python,
    )
except Exception as exc:
    _POLICY_IMPORT_ERROR = exc


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


def _tmp_report_target(raw: str, cwd: Any) -> bool:
    """An out-of-root write the gate admits: under /tmp and not Python.

    `/tmp` is where the orchestrator stages `<REPORT_FILE_PATH>` and the root this
    gate already trusts for `h_mad_assemble_tdd.py --report-file`. A `.py` in any
    case spelling stays refused, so codex cannot write production code into
    another checkout that happens to live under /tmp.
    """
    path = Path(raw).expanduser()
    if not path.is_absolute():
        base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else Path.cwd()
        path = base / path
    resolved = path.resolve()
    if Path(_load_identity().fold_py_suffix(resolved.name)).suffix == ".py":
        return False
    return _path_within(str(resolved), Path("/tmp"))  # M:G-TMP


def _command_cwd(payload: dict[str, Any]) -> object:
    """The directory the shell command runs in, which is not always the session's.

    codex puts its SESSION cwd at the payload's top level and the shell call's own
    directory in `tool_input.workdir` (exec_command, shell, shell_command). F2: a
    codex launched with `--cd <repo>` ran `.venv/bin/python -m pytest` with workdir
    `<repo>/hematology-paper-writer`; judged against the session cwd the token named
    a venv that does not exist, and a contained interpreter was refused -- while the
    inverse (session cwd in a sub-project, workdir elsewhere) admitted a venv the
    command would never run. A relative workdir is relative to the session cwd.
    """
    session = payload.get("cwd")
    raw = payload.get("tool_input")
    workdir = raw.get("workdir") if isinstance(raw, dict) else None  # M:F2-WORKDIR
    if workdir is not None and not isinstance(workdir, str):  # M:F2-MALFORMED
        # Present but unreadable (0, a list, a dict): the command's directory is
        # unknown, which is not the same as "the session's". Fail closed.
        return MALFORMED_WORKDIR
    if not workdir:
        return session
    path = Path(workdir).expanduser()
    if not path.is_absolute():
        path = (Path(session).expanduser() if isinstance(session, str) and session else Path.cwd()) / path
    return str(path)


@cache
def _load_identity() -> Any:
    scripts = str(Path(__file__).resolve().parents[1] / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return import_module("h_mad_target_identity")


def main() -> int:
    if sys.argv[1:] == ["--self-check"]:
        if _POLICY_IMPORT_ERROR is not None:
            print("CODEX-TDD-GATE: FAIL policy-import", file=sys.stderr)
            return 2
        if any(_patch_header_paths(patch) != (["src/prod.py"], "") for patch in (
            "*** Update File: src/prod.py\n",
            "*** Update File: src/prod.py \n",
            "  *** Update File: src/prod.py\n",
        )):
            print("CODEX-TDD-GATE: FAIL parser")
            return 0
        unsafe = (
            "python3 -c \"open('x','w').write('x')\"",
            "git status =(/tmp/evil)",
            "rg --pre=/tmp/evil needle .",
            "git diff --ext-diff",
        )
        if any(_safe_shell_command(command) for command in unsafe):
            print("CODEX-TDD-GATE: FAIL shell-policy")
            return 0
        print("CODEX-TDD-GATE: PASS")
        return 0

    try:
        return _main_guarded()
    except Exception as exc:  # M:G2
        return _deny(f"H-MAD Phase 5 gate raised {type(exc).__name__}: {exc}; refusing fail-closed. kind=judge-error")


def _main_guarded() -> int:
    if _POLICY_IMPORT_ERROR is not None:
        raise _POLICY_IMPORT_ERROR

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
    if command and phase5_status == "active" and not _safe_shell_command(command, root, _command_cwd(payload)):  # M:F2-WIRE
        allowance = _shell_allowance(root)
        if isinstance(allowance, str):
            return _deny(f"H-MAD Phase 5 shell allowance {allowance}; refusing fail-closed.")
        if not _operator_allowed(command, allowance):  # M:SA-WIRE
            return _deny(
                "H-MAD Phase 5 permits only explicit test, read-only, and H-MAD control commands "
                "through Bash. Use apply_patch for writes so the Codex TDD gate can verify a "
                f"failing test first. The operator may admit unrelated work by listing its "
                f"command prefix in {SHELL_ALLOW_FILE}."
            )

    if tool in {"Write", "Edit", "apply_patch"} and not targets and phase5_status in {"active", "unknown"}:
        return _deny("H-MAD Phase 5 could not identify this write target; refusing fail-closed.")

    for raw in targets:  # M:G5
        resolved = _relative_target(root, raw, payload.get("cwd"))
        if resolved is None:
            if _tmp_report_target(raw, payload.get("cwd")):
                continue
            if phase5_status in {"active", "unknown"}:
                return _deny("H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.")
            continue
        if resolved.unresolvable:
            if phase5_status in {"active", "unknown"}:
                return _deny(f"H-MAD Phase 5 target is unresolvable ({resolved.component}); refusing fail-closed. kind=judge-error")
            continue
        if phase5_status in {"active", "unknown"} and _is_shell_allowance(root, resolved):  # M:SA-GUARD
            return _deny(f"H-MAD Phase 5 forbids codex writing {SHELL_ALLOW_FILE}; only the operator declares allowances.")
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
