"""Classify the exact H-MAD host declaration."""

import os
from collections.abc import Mapping


HOST_ENV = "HMAD_HOST"
NON_CLAUDE_HOSTS = ("codex", "agy", "grok")


def classify_host(environ: Mapping[str, str] | None = None) -> tuple[str, str | None]:
    """Return the host class and unmodified declaration value."""
    env = os.environ if environ is None else environ
    value = env.get(HOST_ENV)
    if value is None or value in ("", "claude"):
        return ("claude", value)
    if value in NON_CLAUDE_HOSTS:
        return ("declared", value)
    return ("unknown", value)
