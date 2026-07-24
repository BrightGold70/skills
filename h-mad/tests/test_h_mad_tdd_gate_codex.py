"""Codex-authorship enforcement in the Phase-5 TDD gate hook.

The hook already enforces test-first ORDER (a red test must exist before a prod
write). It did NOT enforce Codex AUTHORSHIP: Codex writes via its own process
(subprocess/pane), so its writes never reach this PreToolUse hook — only Claude's
Write/Edit does. Therefore a prod-code write arriving at the hook during step5 is
Claude self-implementing. When Codex is available, that must be blocked and
redirected to a dispatch; the only escape is an AUDITABLE declaration that Codex
is unavailable (state `codex_status=exhausted|unavailable`, or the
`HMAD_CODEX_UNAVAILABLE` env override), never silent self-authoring.
"""
from __future__ import annotations

import json
import shutil
import stat
import subprocess
from pathlib import Path

HOOK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"

_STATE_STEP5 = {
    "version": 1,
    "features": {},
    "orchestrator_state": {
        "feat": {
            "feature": "feat", "current_phase": 5, "phase": "step5",
            "last_completed_phase": 4, "halt_reason": None,
        }
    },
}


def _project(tmp_path: Path, *, codex_status: str | None = None) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    state = json.loads(json.dumps(_STATE_STEP5))
    if codex_status is not None:
        state["orchestrator_state"]["feat"]["codex_status"] = codex_status
    (docs / ".bkit-memory.json").write_text(json.dumps(state))
    return tmp_path


def _bin(tmp_path: Path, *, codex: bool) -> Path:
    """An isolated bin: real jq always, a `codex` stub only when codex=True."""
    b = tmp_path / "bin"
    b.mkdir(exist_ok=True)
    jq = shutil.which("jq")
    if jq:
        (b / "jq").symlink_to(jq)
    if codex:
        cx = b / "codex"
        cx.write_text("#!/bin/bash\nexit 0\n")
        cx.chmod(cx.stat().st_mode | stat.S_IEXEC)
    return b


def _run(tmp_path: Path, target: str, *, codex: bool, env_extra=None,
         codex_status: str | None = None) -> subprocess.CompletedProcess:
    proj = _project(tmp_path, codex_status=codex_status)
    b = _bin(tmp_path, codex=codex)
    env = {"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()),
           "CLAUDE_PROJECT_DIR": str(proj)}
    if env_extra:
        env.update(env_extra)
    return subprocess.run([str(HOOK), target], capture_output=True, text=True,
                          check=False, env=env)


PROD = "hematology-paper-writer/tools/widget.py"


def test_blocks_claude_prod_write_when_codex_available(tmp_path):
    # The core enforcement: Codex on PATH, no unavailable declaration -> a prod
    # write reaching the hook is Claude self-authoring -> BLOCK, name the dispatch.
    r = _run(tmp_path, PROD, codex=True)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "codex" in r.stderr.lower()
    assert "dispatch" in r.stderr.lower(), "the block must tell Claude to dispatch"


def test_state_codex_status_exhausted_allows_fallback(tmp_path):
    # Auditable fallback: state records Codex is exhausted -> Claude may author.
    # (Falls through to the TDD-order gate; the path is unknown to derive, so that
    # gate blocks with its OWN reason — the codex gate must NOT be what fires.)
    r = _run(tmp_path, PROD, codex=True, codex_status="exhausted")
    assert "must be authored by codex" not in r.stderr.lower(), \
        "codex gate fired despite an exhausted declaration"


def test_env_override_allows_fallback(tmp_path):
    r = _run(tmp_path, PROD, codex=True, env_extra={"HMAD_CODEX_UNAVAILABLE": "1"})
    assert "must be authored by codex" not in r.stderr.lower()


def test_codex_absent_does_not_trigger_codex_gate(tmp_path):
    # No codex on PATH -> can't dispatch -> the codex gate must not fire.
    r = _run(tmp_path, PROD, codex=False)
    assert "must be authored by codex" not in r.stderr.lower()


def test_test_file_allowed_even_with_codex_available(tmp_path):
    # Claude MUST still be able to write the RED test itself; only prod is gated.
    r = _run(tmp_path, "hematology-paper-writer/tests/test_widget.py", codex=True)
    assert r.returncode == 0, r.stderr


def test_non_step5_ignores_codex_gate(tmp_path):
    # phase=null -> no gate at all.
    docs = tmp_path / "docs"; docs.mkdir(parents=True)
    (docs / ".bkit-memory.json").write_text(json.dumps({
        "version": 1, "features": {},
        "orchestrator_state": {"feat": {"feature": "feat", "phase": None}},
    }))
    b = _bin(tmp_path, codex=True)
    r = subprocess.run([str(HOOK), PROD], capture_output=True, text=True, check=False,
                       env={"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()),
                            "CLAUDE_PROJECT_DIR": str(tmp_path)})
    assert r.returncode == 0, r.stderr
