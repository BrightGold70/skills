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
})
CLASS_B: frozenset[str] = frozenset({
    "write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit",
})
PATH_KEYS: dict[str, tuple[str, ...]] = {"write_to_file": ("TargetFile",)}
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
        phase5_status = _any_phase5_status(root)
        workspace_paths = payload.get("workspacePaths")
        if phase5_status in {"active", "unknown"} and isinstance(workspace_paths, list):
            if not any(isinstance(path, str) and _path_within(path, root) for path in workspace_paths):
                decision = {"decision": "deny", "reason": "Workspace paths do not name the root. kind=judge-error"}
                return 0

        # Tasks 6 and 7 replace this conservative rule for classes (b) and (c).
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
