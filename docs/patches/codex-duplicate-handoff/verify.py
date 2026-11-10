#!/usr/bin/env python3
"""Verify Codex is offered exactly one `handoff` skill: this repo's.

Two independent checks, either of which fails the verify:

1. STALE: every Codex config still disables the INSTALLED Matt Pocock `handoff` skill.
2. DUPLICATE: no skill named `handoff` exists, at any depth, under the `skills/` of a Codex home
   (~/.codex, $CODEX_HOME, each Orca codex account's home) or under ~/.agents/skills, unless it
   resolves to this repo's handoff/ (the expected ~/.agents/skills/handoff link does). The Orca account copy ("Handoff for Codex", removed 2026-11-10) was
   probably installed by OMX setup and comes back if that re-runs.

Check 1 detail:

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
Exit 1: a disable is missing or stale, or a duplicate handoff skill exists; fix per README.md.
Exit 2: could not judge (no Codex config found, a config unreadable). That is not a pass.
"""
import os
import re
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


def codex_homes(home: Path) -> list[Path]:
    found = [home / ".codex"]
    if os.environ.get("CODEX_HOME"):
        found.append(Path(os.environ["CODEX_HOME"]))
    found += sorted((home / "Library/Application Support/orca/codex-accounts").glob("*/home"))
    seen, out = set(), []
    for p in found:
        key = os.path.realpath(p)
        if key not in seen and p.is_dir():
            seen.add(key)
            out.append(p)
    return out


NAME_LINE = re.compile(r"""^["']?name["']?[ \t]*:\s*(.*?)\s*$""")   # top-level key only


def skill_name(text: str) -> str | None:
    """Top-level frontmatter `name`, tolerant of forms YAML reads the same way: a BOM, CRLF, a
    quoted key, space before the colon, a trailing comment, quotes, a folded/literal block
    scalar. Indented lines (nested keys, block-scalar text) never match."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return None
        m = NAME_LINE.match(line)
        if not m:
            continue
        value = re.sub(r"\s+#.*$", "", m.group(1)).strip()
        if value[:1] in (">", "|"):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            value = nxt.strip()
        return value.strip("'\"").strip()
    return None


def repo_handoff() -> str:
    override = os.environ.get("HANDOFF_REPO_DIR")   # tests only; production is this repo's handoff/
    return os.path.realpath(override or Path(__file__).resolve().parents[3] / "handoff")


MAX_DEPTH = 2   # skills/<a>/SKILL.md and skills/<a>/<b>/SKILL.md: covers .system/<x> and one vendor
                # level, not templates deep inside a skill (.system/skill-creator/assets/...), and
                # bounds the walk when a skill folder links to a big tree.


def skill_files(root: Path, unreadable: list[str]) -> list[Path]:
    """SKILL.md files up to MAX_DEPTH folders below root, following symlinked dirs; an unlistable
    dir is unreadable. A real folder is walked again only when reached SHALLOWER than before:
    marking it seen at its first (possibly deep, via a link) visit would hide its own children,
    which the depth cap stops at the deeper visit. Loops terminate: depth only shrinks."""
    out, seen = [], {}

    def err(exc: OSError) -> None:
        unreadable.append(f"{exc.filename} ({type(exc).__name__})")

    for dirpath, dirnames, filenames in os.walk(root, onerror=err, followlinks=True):
        real = os.path.realpath(dirpath)
        depth = len(Path(dirpath).relative_to(root).parts)
        if seen.get(real, MAX_DEPTH + 1) <= depth:
            dirnames[:] = []
            continue
        seen[real] = depth
        dirnames.sort()
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        if "SKILL.md" in filenames and Path(dirpath) != root:
            out.append(Path(dirpath) / "SKILL.md")
    return out


def duplicate_handoffs(home: Path, unreadable: list[str]) -> list[str]:
    allowed = repo_handoff()
    roots = [ch / "skills" for ch in codex_homes(home)] + [home / ".agents/skills"]
    dupes, seen = [], set()
    for root in roots:
        if not root.is_dir():
            continue
        for md in skill_files(root, unreadable):
            try:
                name = skill_name(md.read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                unreadable.append(f"{md} ({type(exc).__name__})")
                continue
            real = os.path.realpath(md.parent)
            if name == "handoff" and real != allowed and real not in seen:   # one report per real copy
                seen.add(real)
                dupes.append(real if real == str(md.parent) else f"{real} (reached via {md.parent})")
    return dupes


def norm(p: str) -> str:
    return os.path.realpath(os.path.expanduser(p))


def table(d, key) -> dict:
    v = d.get(key, {})
    return v if isinstance(v, dict) else {}


def main() -> int:
    home = Path.home()
    problems, unreadable, versions, pinned = [], [], set(), 0
    dupes = duplicate_handoffs(home, unreadable)
    configs = config_paths(home)
    if not configs and not dupes:
        for u in unreadable:
            print(f"UNREADABLE {u}")
        print("VERIFY: UNREADABLE no Codex config.toml found")
        return 2
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
    for d in dupes:
        print(f"PROBLEM duplicate handoff skill: {d} (delete it per README)")
    for u in unreadable:
        print(f"UNREADABLE {u}")
    parts = []
    if problems:
        parts.append(f"STALE Matt Pocock handoff disable in {len(problems)} Codex config(s); "
                     f"installed {', '.join(sorted(versions))}")
    if dupes:
        parts.append(f"DUPLICATE {len(dupes)} extra handoff skill(s) in Codex homes")
    if parts:
        print("VERIFY: " + "; ".join(parts) + "; fix per README")
        return 1
    if unreadable:
        print(f"VERIFY: UNREADABLE {len(unreadable)} item(s); see UNREADABLE lines")
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
