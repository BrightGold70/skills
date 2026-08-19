#!/usr/bin/env python3
"""Verify h-mad's hooks are actually WIRED, not merely installed.

`h_mad_install_check.py` proves the two symlinks resolve. It cannot prove any
settings file references them, and an unwired hook is invisible in exactly the way
a passing one is: nothing errors, nothing warns, and every write or `advisor()` call
sails through as if approved. SKILL.md has named this hole since the TDD gate
shipped ("an absent hook link still leaves the gate armed whenever settings.json
points at the skills path instead"); the advisor gate made it two hooks.

The check is deliberately a SEPARATE verdict token from `INSTALL:`. A wiring result
depends on enumerating settings sources this script cannot be certain it has seen
(managed policy, `--settings`, a plugin's own hooks, a project root it was not
pointed at), and `INSTALL: FAIL` halts bootstrap. A false halt that no local edit
can clear is worse than a missed check, so wiring reports beside the install verdict
rather than inside it.

Three ways a naive version reports the wrong thing:

  1. matching on the literal path. The live wiring is
     `bash $HOME/.claude/skills/h-mad/hooks/h-mad-advisor-gate.sh` -- an unexpanded
     env var, inside a longer command. Compare on the basename and expand before
     touching the filesystem.
  2. treating "referenced" as "wired". An entry can name the hook under a matcher
     that cannot match the tool it must gate: `Write` alone never fires for `Edit`,
     and the hook then stands down on half its surface, silently.
  3. calling a missing settings file "not wired". That is a cannot-judge -- nothing
     was read -- and it is the single most likely false FAIL on a machine that keeps
     its hooks somewhere this script does not know about.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

#: hook basename -> tool names its matcher must be able to fire on.
REQUIRED_HOOKS: dict[str, tuple[str, ...]] = {
    "h-mad-tdd-gate.sh": ("Write", "Edit"),
    "h-mad-advisor-gate.sh": ("advisor",),
}

MATCH_ALL = ("*", "", "**")


def settings_sources(project_root: Path | None) -> list[Path]:
    """Every settings file this check knows to look in, most-global first.

    Two resolutions that are easy to omit and both produce a false NOT_WIRED on a
    correctly wired machine:

      * `CLAUDE_CONFIG_DIR` relocates the whole config tree, so `~/.claude` is not
        always the user scope;
      * project settings are found by walking UP from the working directory, so a
        repo whose `.claude/` sits above the directory the check was pointed at is
        wired by a file this list would never contain.

    Missing a source can only ever under-report wiring, which is why the CLI treats
    "read nothing" as a cannot-judge rather than a verdict.
    """
    config = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    home = Path(_expand(config)) if config else Path.home() / ".claude"
    out = [home / "settings.json", home / "settings.local.json"]
    if project_root is not None:
        seen = set()
        for d in (project_root, *project_root.parents):
            c = d / ".claude"
            if c in seen:
                continue
            seen.add(c)
            out += [c / "settings.json", c / "settings.local.json"]
    return out


def _expand(text: str) -> str:
    return os.path.expanduser(os.path.expandvars(text))


def _referenced_path(command: str, basename: str) -> str | None:
    """The token inside `command` that names `basename`, expanded.

    The command is a shell line, not a path: `bash $HOME/.claude/.../x.sh --flag`.
    Splitting on whitespace and taking the token that ends with the basename is
    enough for every wiring shape h-mad documents, and returning None (rather than
    guessing) keeps an exotic one from being reported as a stale path it is not.
    """
    for token in command.replace('"', " ").replace("'", " ").split():
        if token.endswith(basename):
            return _expand(token)
    return None


def _matcher_fires(matcher: str, tool: str) -> bool:
    if matcher in MATCH_ALL:
        return True
    try:
        return re.search(matcher, tool) is not None
    except re.error:
        # An invalid pattern is not a match; it is also not this check's job to
        # explain regex. Reported as a wrong matcher, which is what it behaves as.
        return False


def check(project_root: Path | None = None,
          sources: list[Path] | None = None) -> tuple[list[str], bool]:
    """Returns (issues, read_anything). Empty issues + read_anything means wired."""
    paths = sources if sources is not None else settings_sources(project_root)

    entries: list[tuple[str, str]] = []   # (matcher, command)
    read_anything = False
    for path in paths:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        read_anything = True
        if not isinstance(data, dict):
            continue
        pre = (data.get("hooks") or {}).get("PreToolUse") or []
        if not isinstance(pre, list):
            continue
        for entry in pre:
            if not isinstance(entry, dict):
                continue
            matcher = entry.get("matcher")
            matcher = matcher if isinstance(matcher, str) else ""
            for hook in entry.get("hooks") or []:
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    entries.append((matcher, hook["command"]))

    if not read_anything:
        return [], False

    issues: list[str] = []
    for basename, tools in REQUIRED_HOOKS.items():
        hits = [(m, c) for m, c in entries if basename in c]
        if not hits:
            issues.append(f"HOOK_NOT_WIRED:{basename}")
            continue

        # Wired more than once is fine — the harness runs each. The hook counts as
        # correctly wired if ANY entry covers a tool; report per uncovered tool so a
        # `Write`-only matcher cannot pass on the strength of gating half its surface.
        uncovered = [t for t in tools
                     if not any(_matcher_fires(m, t) for m, _ in hits)]
        if uncovered:
            shown = "|".join(sorted({m or "<empty>" for m, _ in hits}))
            issues.append(
                f"HOOK_WIRED_WRONG_MATCHER:{basename} matcher={shown} "
                f"uncovered={','.join(uncovered)}")

        # A command naming a path that does not exist is wired to nothing. Only
        # reported when a path token was actually identified.
        for _, command in hits:
            target = _referenced_path(command, basename)
            if target is not None and not Path(target).exists():
                issues.append(f"HOOK_WIRED_STALE_PATH:{basename} -> {target}")

    return issues, True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="verify h-mad hooks are wired")
    ap.add_argument("--project-root", default=os.getcwd())
    args = ap.parse_args(argv)

    root = Path(args.project_root).expanduser()
    issues, read_anything = check(root if str(root).strip() else None)

    if not read_anything:
        print("ERROR: no readable settings file among "
              + ", ".join(str(p) for p in settings_sources(root)), file=sys.stderr)
        # No `issues=` count, for the same reason `WIREPIN: UNREADABLE` carries none:
        # a shape that can be parsed by a count that was never measured, will be.
        print("WIRING: UNKNOWN reason=no_settings")
        return 2

    if issues:
        print(f"WIRING: FAIL issues={len(issues)}")
        for line in issues:
            print(line)
        return 0

    print("WIRING: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
