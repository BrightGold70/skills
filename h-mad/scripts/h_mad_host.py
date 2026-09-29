"""Classify the exact H-MAD host declaration."""

import os
from collections.abc import Mapping


HOST_ENV = "HMAD_HOST"
NON_CLAUDE_HOSTS = ("codex", "agy", "grok")


def classify_host(
    environ: Mapping[str, str] | None = None, *, explicit_host: str | None = None
) -> tuple[str, str | None]:
    """Return the host class and value; an explicit host outranks the environment."""
    env = os.environ if environ is None else environ
    value = env.get(HOST_ENV)
    if explicit_host is not None:
        value = explicit_host
        if value == "claude":
            return ("claude", value)
        if value in NON_CLAUDE_HOSTS:
            return ("declared", value)
        return ("unknown", value)
    if value is None or value in ("", "claude"):
        return ("claude", value)
    if value in NON_CLAUDE_HOSTS:
        return ("declared", value)
    return ("unknown", value)
