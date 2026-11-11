"""Shared target list and patterns for the omc-codex-mcp-no-type patch."""
import json
import os
import re
from pathlib import Path

MARKER = "/* omc-codex-mcp-no-type: codex ignores mcp_servers.*.type (OMC #4899) */"

# The one line in renderCodexServerBlock() that writes `type = "..."` into the
# managed Codex block. The bundled cli.cjs renames the parameter to `entry2`.
ORIGINAL = re.compile(r"lines\.push\(`type = \$\{renderTomlString\((entry2?)\.type\)\}`\);")

RELATIVE = ("dist/installer/mcp-registry.js", "bridge/cli.cjs")


ROOTS_ENV = "OMC_PATCH_ROOTS"
NPM_ENV = "OMC_NPM_ROOT"
NPM_DEFAULT = "/opt/homebrew/lib/node_modules/oh-my-claude-sisyphus"


def roots() -> list[Path]:
    """Every installed OMC copy that runs: the active plugin cache and the global npm CLI.

    `OMC_PATCH_ROOTS` (os.pathsep-separated) replaces the lookup entirely, with no
    fallback, so tests can point apply/verify at fixture roots and never at the host.
    `OMC_NPM_ROOT` replaces only the npm CLI path (empty: no npm copy), so a test can
    drive the real installed_plugins.json lookup under a fixture HOME.
    """
    override = os.environ.get(ROOTS_ENV)
    if override is not None:
        return [Path(p) for p in override.split(os.pathsep) if p]
    found: list[Path] = []
    installed = Path.home() / ".claude/plugins/installed_plugins.json"
    try:
        plugins = json.loads(installed.read_text())["plugins"]
    except (OSError, ValueError, KeyError):
        plugins = {}
    for key, entries in plugins.items():
        if key.startswith("oh-my-claudecode@"):
            for entry in entries:
                if entry.get("installPath"):
                    found.append(Path(entry["installPath"]))
    npm_path = os.environ.get(NPM_ENV, NPM_DEFAULT)
    if npm_path and Path(npm_path).is_dir():
        found.append(Path(npm_path))
    return found


def targets() -> list[Path]:
    return [root / rel for root in roots() for rel in RELATIVE]
