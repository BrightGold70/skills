#!/usr/bin/env python3
"""Verify Codex is offered exactly one `handoff` skill: this repo's.

Three independent checks, any of which fails the verify:

0. MISSING: ~/.agents/skills/handoff exists and resolves to this repo's handoff/, whose
   SKILL.md is named `handoff`. Without it Codex has no handoff at all.
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

--fix repoints each stale pin to the installed copy (or adds the pin), editing only the `path`
line or appending one block, with a timestamped backup; then re-runs the check. It never deletes
a duplicate skill, never overrides an entry that explicitly enables the handoff, and refuses a
stale path it cannot place unambiguously.
Exit 2: could not judge (no Codex config found, a config unreadable). That is not a pass.
"""
import errno
import os
import re
import shutil
import stat
import sys
import time
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


def missing_handoff(home: Path, unreadable: list[str]) -> str | None:
    """Why Codex would get NO repo handoff, or None. The repo's handoff reaches Codex (both the
    plain and the Orca CODEX_HOME) through one link, ~/.agents/skills/handoff -> <repo>/handoff.
    Decided with lstat/stat so that a permission error is "could not judge" (appended to
    unreadable), never "absent": pathlib's exists() swallows it on 3.15 but raises on 3.11."""
    link, repo = home / ".agents/skills/handoff", repo_handoff()
    relink = f"run: ln -sfn {repo} {link}"
    try:
        st = os.lstat(link)
    except FileNotFoundError:
        mk = "" if link.parent.is_dir() else f"mkdir -p {link.parent} && "
        return f"{link} is absent; run: {mk}ln -s {repo} {link}"
    except OSError as exc:
        unreadable.append(f"{link} ({type(exc).__name__})")
        return None
    if stat.S_ISLNK(st.st_mode):
        try:
            os.stat(link)
        except (FileNotFoundError, NotADirectoryError) as exc:
            return f"{link} is a dangling link to {os.readlink(link)}; {relink}"
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                return f"{link} is a link loop; {relink}"
            unreadable.append(f"{link} ({type(exc).__name__})")
            return None
        if os.path.realpath(link) != repo:
            return f"{link} links to {os.path.realpath(link)}, not {repo}; {relink}"
    elif os.path.realpath(link) != repo:   # not a link itself; fine if reached through a linked parent
        kind = "folder" if stat.S_ISDIR(st.st_mode) else "file"
        return f"{link} is a real {kind}, not a link to {repo}; move it away, then ln -s {repo} {link}"
    md = Path(repo) / "SKILL.md"
    try:
        name = skill_name(read_raw(md))
    except (OSError, UnicodeDecodeError):
        return f"{md} is missing or unreadable (is the repo on a branch without handoff/?)"
    if name != "handoff":
        return f"{md} is named {name!r}, not 'handoff'"
    return None


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


def check(home: Path) -> tuple[int, list[str], list[dict]]:
    """Run both checks. Returns (exit code, output lines, one repair plan per config whose pin
    is missing or stale)."""
    problems, unreadable, versions, pinned, plans = [], [], set(), 0, []
    dupes = duplicate_handoffs(home, unreadable)
    missing_link = missing_handoff(home, unreadable)
    if missing_link:
        # The link itself (its target, or a folder in its place) is MISSING's to repair; reporting
        # it again as a duplicate would tell the user to delete what the link points at.
        here = os.path.realpath(home / ".agents/skills/handoff")
        dupes = [d for d in dupes if d.split(" (reached via ")[0] != here]
    configs = config_paths(home)
    if not configs and not dupes and not missing_link:
        return 2, [f"UNREADABLE {u}" for u in unreadable] + ["VERIFY: UNREADABLE no Codex config.toml found"], []
    for cfg in configs:
        try:
            text = read_raw(cfg)
            data = tomllib.loads(text)
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
        not_disabled = {norm(e["path"]) for e in entries if e.get("enabled") is not False}
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
            plans.append({"cfg": cfg, "text": text, "stale": stale, "missing": missing,
                          "explicitly_enabled": [h for h in missing if norm(str(h)) in not_disabled]})

    lines = [f"PROBLEM missing repo handoff: {missing_link}"] if missing_link else []
    lines += problems
    lines += [f"PROBLEM duplicate handoff skill: {d} (delete it per README)" for d in dupes]
    lines += [f"UNREADABLE {u}" for u in unreadable]
    parts = ["MISSING the repo handoff link (Codex has no handoff)"] if missing_link else []
    if problems:
        parts.append(f"STALE Matt Pocock handoff pin in {len(problems)} Codex config(s); "
                     f"installed {', '.join(sorted(versions))}; run verify.py --fix")
    if dupes:
        parts.append(f"DUPLICATE {len(dupes)} extra handoff skill(s) in Codex homes; delete per README")
    if parts:
        return 1, lines + ["VERIFY: " + "; ".join(parts)], plans
    if unreadable:
        return 2, lines + [f"VERIFY: UNREADABLE {len(unreadable)} item(s); see UNREADABLE lines"], plans
    if not pinned:
        return 0, lines + ["VERIFY: OK no Codex config enables an installed Matt Pocock handoff"], plans
    return 0, lines + [f"VERIFY: OK {pinned} Codex config(s) disable every installed Matt Pocock handoff"], plans


PATH_LINE = re.compile(r"""^(?P<lead>[ \t]*path[ \t]*=[ \t]*)(?P<q>["'])(?P<p>[^"'\n]*)(?P=q)""", re.M)


def toml_basic(s: str) -> str:
    """Body of a TOML basic ("...") string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def read_raw(path: Path) -> str:
    """Text with line endings untouched (no universal-newline translation): CRLF stays CRLF."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def current_text(path: Path) -> str:
    """Re-read just before replacing: a seam so a test can play Codex writing meanwhile."""
    return read_raw(path)


def plan_text(plan: dict) -> tuple[str | None, list[str]]:
    """New config text for one plan, or (None, reasons) when it cannot be done safely."""
    # Pin the resolved path: under Orca, Codex named the skill by its ~/.codex/... realpath
    # (measured 2026-11-10), not via the account's plugins symlink.
    text = plan["text"]
    todo = [os.path.realpath(h) for h in plan["missing"] if h not in plan["explicitly_enabled"]]
    reasons = [f"{h} is explicitly enabled there; not overriding it" for h in plan["explicitly_enabled"]]
    if reasons:
        return None, reasons
    for old in plan["stale"]:
        if not todo:
            break
        sites = [m for m in PATH_LINE.finditer(text) if m.group("p") == old]
        if text.count(old) != 1:
            return None, [f"stale path {old} appears {text.count(old)} time(s); edit it by hand"]
        if len(sites) != 1:
            return None, [f"stale path {old} is not on a plain `path = \"...\"` line "
                          "(inline table, or a quote in the path); edit it by hand"]
        m = sites[0]
        new = todo.pop(0)
        body = toml_basic(new) if m.group("q") == '"' else new   # a literal ('...') string has no escapes
        text = text[:m.start("p")] + body + text[m.end("p"):]
    nl = "\r\n" if "\r\n" in text else "\n"
    for h in todo:
        block = ("\n# Disable the Matt Pocock handoff; this repo-owned handoff skill replaces it.\n"
                 f'[[skills.config]]\npath = "{toml_basic(h)}"\nenabled = false\n')
        text += ("" if text.endswith("\n") else nl) + block.replace("\n", nl)
    try:
        tomllib.loads(text)   # e.g. a "'" in a path that sits in a literal ('...') string
    except tomllib.TOMLDecodeError as exc:
        return None, [f"the edit would not parse ({exc}); edit it by hand"]
    return text, []


def apply_fix(plan: dict) -> str:
    cfg = plan["cfg"]
    if cfg.is_symlink():
        # os.replace onto the link would swap it for a plain file and leave the managed target
        # (dotfiles, a sync tool) stale, while every later check reads the detached copy as OK.
        return (f"NOT FIXED {cfg}: it is a symlink to {os.path.realpath(cfg)}; "
                "fix the pin there by hand (the tool that manages it owns that file)")
    new, reasons = plan_text(plan)
    if new is None:
        return f"NOT FIXED {cfg}: " + "; ".join(reasons)
    stamp, n = time.strftime("%Y%m%d%H%M%S"), 0
    backup = cfg.with_name(f"{cfg.name}.bak-handoff-{stamp}")
    while backup.exists():   # two fixes in one second must not overwrite the first backup
        n += 1
        backup = cfg.with_name(f"{cfg.name}.bak-handoff-{stamp}-{n}")
    mode = stat.S_IMODE(cfg.stat().st_mode)
    tmp = cfg.with_name(f".{cfg.name}.handoff-fix-{os.getpid()}")
    replaced = created = False
    try:
        # Created at the config's mode (never wider, even for an instant); O_EXCL refuses a
        # leftover or planted temp instead of following it.
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        created = True
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        os.chmod(tmp, mode)
        shutil.copy2(cfg, backup)
        # Compare LAST, right before the replace: a Codex write after this point is the only
        # window left, and it is as short as one rename.
        if current_text(cfg) != plan["text"]:
            backup.unlink()
            return f"NOT FIXED {cfg}: it changed while fixing (Codex wrote it?); re-run --fix"
        os.replace(tmp, cfg)
        replaced = True
    finally:
        if not replaced:   # nothing was written: drop the temp, and the backup if it is redundant
            if created:   # never remove a temp this run did not make
                tmp.unlink(missing_ok=True)
            if backup.exists() and current_text_safe(cfg) == current_text_safe(backup):
                backup.unlink()
    return f"FIXED {cfg}: " + ", ".join(os.path.realpath(h) for h in plan["missing"]) + f" (backup {backup.name})"


def current_text_safe(path: Path) -> str | None:
    try:
        return read_raw(path)
    except (OSError, UnicodeDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    unknown = [a for a in args if a != "--fix"]
    if unknown:
        print(f"usage: verify.py [--fix]   (unknown: {' '.join(unknown)})")
        return 2
    home = Path.home()
    rc, lines, plans = check(home)
    if "--fix" in args and plans:
        for plan in plans:
            print(apply_fix(plan))
        rc, lines, _ = check(home)
    for line in lines:
        print(line)
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # the hook reads exit 1 as "patch missing"; an unexpected error is not that
        print(f"VERIFY: UNREADABLE unexpected {type(exc).__name__}: {exc}")
        sys.exit(2)
