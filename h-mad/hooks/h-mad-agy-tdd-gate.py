#!/usr/bin/env python3
"""Fail-closed Phase 5 gate for agy's tool-call hook contract."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time


CLASS_A: frozenset[str] = frozenset({
    "view_file", "list_dir", "grep_search", "find_by_name", "command_status",
    "read_url_content", "search_web", "ask_question", "finish", "wait", "wait_5_seconds",
    # Executed by agy but absent from its advertised init inventory.
    "read_file",
})
CLASS_B: frozenset[str] = frozenset({
    "write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit",
    # Executed by agy 1.4.12 but absent from its advertised init inventory.
    "write_file", "edit_file",
})
PATH_KEYS: dict[str, tuple[str, ...]] = {
    "write_to_file": ("TargetFile",), "replace_file_content": ("TargetFile",),
    "write_file": ("Path",), "edit_file": ("Path",),
}
GATE_KINDS: frozenset[str] = frozenset({
    "judge-error", "tool-not-admitted", "target-outside-root", "allowance-file-write", "shell-not-admitted",
})


def classify_tool(name: str) -> str:
    if name in CLASS_A:
        return "a"
    if name in CLASS_B:
        return "b"
    if name == "run_command":
        return "c"
    return "d"


def _payload() -> object:
    """Read to EOF within two seconds; support in-memory callers as well."""
    try:
        fd = sys.stdin.fileno()
    except io.UnsupportedOperation:
        return json.loads(sys.stdin.read())
    if os.isatty(fd):
        raise ValueError("hook input must be JSON")
    chunks = []
    deadline = time.monotonic() + 2.0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
            raise TimeoutError("hook input timed out")
        chunk = os.read(fd, 65536)
        if not chunk:
            return json.loads(b"".join(chunks))
        chunks.append(chunk)


def main() -> int:
    self_check = sys.argv[1:] == ["--self-check"]
    check_result = "AGY-TDD-GATE: FAIL policy-import"
    decision = None
    try:
        if not self_check:
            payload = _payload()
            if not isinstance(payload, dict):
                raise ValueError("hook payload must be an object")
            call = payload.get("toolCall")
            if not isinstance(call, dict) or not isinstance(call.get("name"), str):
                raise ValueError("toolCall must name a tool")
            tool_class = classify_tool(call["name"])
            if tool_class == "a":
                decision = {"decision": "allow"}
                return 0

        # Import failures belong to the guarded decision, never to module startup.
        scripts = str(Path(__file__).resolve().parents[1] / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import h_mad_tdd_judge as judge
        import h_mad_target_identity as identity
        from h_mad_target_identity import (
            SHELL_ALLOW_FILE,
            MALFORMED_WORKDIR,
            _any_phase5_status,
            _is_production_python,
            _is_shell_allowance,
            _operator_allowed,
            _path_within,
            _safe_shell_command,
            _shell_allowance,
        )
        judge.JUDGE_BUDGET_S

        if self_check:
            if classify_tool("view_file") != "a" or classify_tool("call_mcp_tool") != "d":
                check_result = "AGY-TDD-GATE: FAIL classification"
                return 0
            if _safe_shell_command("python3 -c \"open('x','w').write('x')\""):
                check_result = "AGY-TDD-GATE: FAIL shell-policy"
                return 0
            check_result = "AGY-TDD-GATE: PASS"
            return 0

        result = subprocess.run(
            ["git", "-C", str(Path.cwd().parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=2,
        )
        root = Path(identity.canonical_directory(result.stdout.strip()))
        os.chdir(root)
        adp = payload.get("artifactDirectoryPath")
        artifact = Path(adp) if isinstance(adp, str) and adp else None
        phase5_status = _any_phase5_status(root)
        workspace_paths = payload.get("workspacePaths")
        if phase5_status in {"active", "unknown"} and isinstance(workspace_paths, list):
            if not any(isinstance(path, str) and _path_within(path, root) for path in workspace_paths):
                decision = {"decision": "deny", "reason": "Workspace paths do not name the root. kind=judge-error"}
                return 0

        if tool_class == "b":
            args = call.get("args")
            if not isinstance(args, dict):
                args = {}
            targets = [args[key] for key in PATH_KEYS.get(call["name"], ())
                       if key in args and isinstance(args[key], str) and args[key]]
            if not targets:
                if phase5_status in {"active", "unknown"}:
                    decision = {"decision": "deny", "reason": "Write has no recognised string target. kind=judge-error"}
                else:
                    decision = {"decision": "allow"}
                return 0

            for raw in targets:
                # T1–T2: resolve from the root before examining the identity.
                resolved = identity.canonicalise(str(root), str(Path(raw).expanduser()), str(root))
                if resolved.unresolvable:
                    if phase5_status in {"active", "unknown"}:
                        detail = repr(resolved.component).replace("kind=", "kind:")
                        decision = {"decision": "deny", "reason": f"Write target is unresolvable ({detail}). kind=judge-error"}
                        return 0
                    continue
                # T2a: an existing directory has no file names for T6 to judge.
                if Path(resolved.target).is_dir():
                    if phase5_status in {"active", "unknown"}:
                        detail = repr(resolved.target).replace("kind=", "kind:")
                        decision = {"decision": "deny", "reason": f"Write target is a directory ({detail}). kind=judge-error"}
                        return 0
                    continue
                # T3–T4: containment must precede the allowance-file helper.
                try:
                    Path(resolved.target).relative_to(root)
                except ValueError:
                    outside_allowed = (
                        not any(Path(identity.fold_py_suffix(name)).suffix == ".py" for name in resolved.names)
                        and (_path_within(resolved.target, Path("/tmp"))
                             or (artifact is not None and _path_within(resolved.target, artifact)))
                    )
                    if not outside_allowed and phase5_status in {"active", "unknown"}:
                        decision = {"decision": "deny", "reason": "Write target is outside the root. kind=target-outside-root"}
                        return 0
                    continue
                # T5: only the operator may declare shell allowances.
                if phase5_status in {"active", "unknown"} and _is_shell_allowance(root, resolved):
                    decision = {"decision": "deny", "reason": "Writing the shell allowance file is forbidden. kind=allowance-file-write"}
                    return 0
                # T6–T7: the chain is authoritative even after an inactive scan.
                production = []
                for name in resolved.names:
                    absolute = Path(resolved.target).parent / name
                    relative = absolute.relative_to(root).as_posix()
                    if _is_production_python(relative):
                        production.append((name, absolute, relative))
                if not production:
                    continue
                _, absolute, relative = min(production)
                chain = judge.read_chain(root, absolute)
                if chain.value == "unreadable":
                    detail = f"{chain.error_file}: {chain.error}".replace("kind=", "kind:")
                    decision = {"decision": "deny", "reason": f"State governing the write is unreadable ({detail}). kind=judge-error"}
                    return 0
                if chain.value != "active":
                    continue
                verdict = judge.judge(root, absolute, chain.records)
                if verdict.decision != "ALLOW":
                    detail = f"{relative}: {verdict.reason}".replace("kind=", "kind:")
                    decision = {"decision": "deny", "reason": f"Phase 5 requires a failing test before {detail} kind={verdict.kind}"}
                    return 0
            decision = {"decision": "allow"}
            return 0

        if tool_class == "c":
            args = call.get("args")
            if not isinstance(args, dict):
                args = {}
            command = args.get("CommandLine")
            if not isinstance(command, str):
                if phase5_status in {"active", "unknown"}:
                    decision = {"decision": "deny", "reason": "Shell call has no string CommandLine. kind=judge-error"}
                else:
                    decision = {"decision": "allow"}
                return 0
            if phase5_status == "unknown":
                decision = {"decision": "deny", "reason": "State governing shell execution is unreadable. kind=judge-error"}
                return 0
            if phase5_status == "active":
                workdir = args.get("Cwd")
                if workdir is not None and not isinstance(workdir, str):
                    cwd = MALFORMED_WORKDIR
                elif not workdir:
                    cwd = str(root)
                else:
                    path = Path(workdir).expanduser()
                    cwd = str(root / path if not path.is_absolute() else path)
                try:
                    if isinstance(cwd, str) and Path(cwd).is_dir():
                        os.chdir(cwd)
                except OSError:
                    pass
                if not _safe_shell_command(command, root, cwd):
                    allowance = _shell_allowance(root)
                    if isinstance(allowance, str):
                        decision = {"decision": "deny", "reason": "Shell allowance is unreadable or unparsable. kind=judge-error"}
                        return 0
                    if not _operator_allowed(command, allowance):
                        decision = {
                            "decision": "deny",
                            "reason": "Phase 5 permits only explicit test, read-only, and H-MAD control commands. "
                                      f"Use {', '.join(sorted(CLASS_B))} for writes so the TDD gate can verify a failing test. "
                                      f"The operator may list command prefixes in {SHELL_ALLOW_FILE}. kind=shell-not-admitted",
                        }
                        return 0
            decision = {"decision": "allow"}
            return 0

        if phase5_status == "inactive":
            decision = {"decision": "allow"}
        elif phase5_status == "active":
            decision = {"decision": "deny", "reason": "Tool is not admitted during Phase 5. kind=tool-not-admitted"}
        # Unknown activity leaves the finally's fail-closed decision in force.
    except Exception:
        if self_check:
            return 2
    finally:
        if self_check:
            print(check_result)
        else:
            if decision is None:
                decision = {"decision": "deny", "reason": "Gate could not reach a judgement. kind=judge-error"}
            print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
