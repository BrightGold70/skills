"""Shared test support for codex-tdd-gate-defects (not collected: no test_ prefix)."""
from __future__ import annotations

import os

DROPPED_ENV = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CODEX_UNAVAILABLE", "CODEX_PROJECT_DIR")


def hermetic_env(**extra: str) -> dict[str, str]:
    """os.environ minus every CLAUDE* name and DROPPED_ENV, then `extra`."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE") and k not in DROPPED_ENV}  # M:E1
    env.update(extra)
    return env
