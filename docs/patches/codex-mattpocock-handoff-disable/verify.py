#!/usr/bin/env python3
"""Verify every Codex config still disables the INSTALLED Matt Pocock `handoff` skill.

The disable is a `[[skills.config]]` entry naming the skill's SKILL.md by absolute path, and
that path carries the plugin version (`.../mattpocock-skills/1.3.2/...`). A plugin update
installs a new version folder and deletes the old one, so the entry silently stops matching
and the duplicate handoff loads again. This check names the path to repoint to.

Configs checked: ~/.codex/config.toml, $CODEX_HOME/config.toml, and every Orca codex-account
config. Each config is judged against the plugin copies under ITS OWN Codex home
(`<config dir>/plugins/cache/...`); an Orca account's `home/plugins` is normally a symlink to
~/.codex/plugins, but a real directory there is checked on its own. A config only needs the
entry when it enables the plugin and its home has a handoff copy installed. Project-level
.codex/config.toml files are not checked: Codex ignores `skills.config` there.

Exit 0: every config that enables the plugin disables every installed handoff copy
        (or the plugin, or its handoff skill, is not installed).
Exit 1: a disable is missing or stale; repoint it per README.md.
Exit 2: could not judge (no Codex config found, a config unreadable). That is not a pass.
"""
import os
import sys
import tomllib
from pathlib import Path

PLUGIN_KEY = "mattpocock-skills@mattpocock"


def plugin_root(codex_home: Path) -> Path:
    return codex_home / "plugins/cache/mattpocock/mattpocock-skills"


def installed_handoffs(codex_home: Path) -> list[Path]:
    root = plugin_root(codex_home)
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("*/skills/*/handoff/SKILL.md") if p.is_file())


def config_paths(home: Path) -> list[Path]:
    found = [home / ".codex/config.toml"]
    if os.environ.get("CODEX_HOME"):
        found.append(Path(os.environ["CODEX_HOME"]) / "config.toml")
    found += sorted((home / "Library/Application Support/orca/codex-accounts").glob("*/home/config.toml"))
    seen, out = set(), []
    for p in found:
        key = os.path.realpath(p)
        if key not in seen and p.is_file():
            seen.add(key)
            out.append(p)
    return out


def norm(p: str) -> str:
    return os.path.realpath(os.path.expanduser(p))


def table(d, key) -> dict:
    v = d.get(key, {})
    return v if isinstance(v, dict) else {}


def main() -> int:
    home = Path.home()
    configs = config_paths(home)
    if not configs:
        print("VERIFY: UNREADABLE no Codex config.toml found")
        return 2

    problems, unreadable, versions, pinned = [], [], set(), 0
    for cfg in configs:
        try:
            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            unreadable.append(f"{cfg} ({type(exc).__name__})")
            continue
        plugin = table(data, "plugins").get(PLUGIN_KEY)
        if not isinstance(plugin, dict) or plugin.get("enabled", True) is not True:
            continue
        handoffs = installed_handoffs(cfg.parent)
        entries = table(data, "skills").get("config", [])
        if not isinstance(entries, list):
            entries = []
        entries = [e for e in entries if isinstance(e, dict) and isinstance(e.get("path"), str)]
        disabled = {norm(e["path"]) for e in entries if e.get("enabled") is False}
        stale = [e["path"] for e in entries
                 if e.get("enabled") is False and "/mattpocock-skills/" in e["path"]
                 and e["path"].endswith("/handoff/SKILL.md") and not Path(norm(e["path"])).exists()]
        missing = [h for h in handoffs if norm(str(h)) not in disabled]
        pinned += bool(handoffs)
        if missing:
            versions |= {h.relative_to(plugin_root(cfg.parent)).parts[0] for h in missing}
            line = f"PROBLEM {cfg}: no enabled=false entry for " + ", ".join(map(str, missing))
            if stale:
                line += "; stale entry: " + ", ".join(stale)
            problems.append(line)

    for line in problems:
        print(line)
    for u in unreadable:
        print(f"UNREADABLE {u}")
    if problems:
        print(f"VERIFY: STALE Matt Pocock handoff disable in {len(problems)} Codex config(s); "
              f"installed {', '.join(sorted(versions))}; repoint per README")
        return 1
    if unreadable:
        print(f"VERIFY: UNREADABLE {len(unreadable)} Codex config(s)")
        return 2
    if not pinned:
        print("VERIFY: OK no Codex config enables an installed Matt Pocock handoff")
        return 0
    print(f"VERIFY: OK {pinned} Codex config(s) disable every installed Matt Pocock handoff")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # the hook reads exit 1 as "patch missing"; an unexpected error is not that
        print(f"VERIFY: UNREADABLE unexpected {type(exc).__name__}: {exc}")
        sys.exit(2)
