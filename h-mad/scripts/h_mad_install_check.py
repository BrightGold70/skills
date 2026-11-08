#!/usr/bin/env python3
"""h_mad_install_check.py — verify the skill's own installation shape.

SKILL.md §"Editing this skill while a run is in flight" asserts that
`~/.claude/skills/h-mad` **is a symlink into this repository**, and the
coupled-suites warning depends on it. That was prose until now: a live install
was found to be a plain directory copied 2.5 months earlier, running happily
because the frontmatter is byte-identical between checkout and copy.

Two links make up a correct install, and each fails silently in its own way:

  ~/.claude/skills/h-mad          -> <checkout>
  ~/.claude/hooks/h-mad-tdd-gate.sh -> <checkout>/hooks/h-mad-tdd-gate.sh

A stale *copy* of the first keeps loading while drifting arbitrarily far from
the checkout. An absent second breaks `test_h_mad_tdd_gate_codex.py`,
`test_h_mad_tdd_gate_state_resolution.py` and the contract
`references/codex-implementer-prompt.md` states to the implementer — while the
gate still appears to work, because `settings.json` may arm it through the
*skills* path instead.

Verdicts, printed as a canonical token:

    INSTALL: PASS                             exit 0
    INSTALL: FAIL issues=2                    exit 0
    INSTALL: UNREADABLE                       exit 2

followed by detail lines naming what is wrong.

After them come codex hook-trust advisories, never counted in `issues=`. Codex
runs a project hook only with a `[hooks.state."<abs hooks.json>:<event>:<group>:
<hook>"]` record in `$CODEX_HOME/config.toml` (default `~/.codex`) or with
`--dangerously-bypass-hook-trust`, which `hmad-dispatch exec` passes and a
hand-started codex does not. For each h-mad gate entry in
`<git toplevel>/.codex/hooks.json` (`--codex-hooks-json`, env
`HMAD_CODEX_HOOKS_JSON`; config `--codex-config`) one line prints:
`CODEX_HOOK_UNTRUSTED:` (no record), `CODEX_HOOK_DISABLED:` (`enabled = false`),
`CODEX_HOOK_TRUST_RECORDED: … (hash not verified)`, or `CODEX_HOOK_TRUST_UNKNOWN:
… reason=` when either file cannot be read. A record is never reported as
enforced: what `trusted_hash` covers is unknown.

`FAIL` exits 0 because it is a **verdict**, not an operational error
(`invariants.base.md` §"Audit-gate signal discipline"): a non-zero exit
registers as a Claude Code `PostToolUseFailure` and leaks into coexisting
plugins' error handling. Non-zero is reserved for the one genuine operational
error — no path to check, so no verdict exists.

This check reads paths. It repairs nothing: a wrong install is an operator
decision to fix, and silently relinking someone's `~/.claude` is precisely the
kind of action a preflight must not take.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path

DEFAULT_SKILLS_LINK = Path.home() / ".claude" / "skills" / "h-mad"
DEFAULT_HOOK_LINK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"

#: Marks a resolved directory as an h-mad checkout rather than any other target.
CHECKOUT_MARKER = "SKILL.md"

#: Where the hook link must land inside the checkout.
HOOK_RELPATH = ("hooks", "h-mad-tdd-gate.sh")

AGENTS_SKILLS_ENV = "HMAD_AGENTS_SKILLS_DIR"
AGY_SKILLS_ENV = "HMAD_AGY_SKILLS_DIR"
AGY_INSTALLED_NAMES = ("h-mad", "handoff")
SIBLING_KINDS = ("NOT_SYMLINK", "DANGLING", "WRONG_CHECKOUT")

#: The h-mad codex gate's hooks.json command. A second copy of `GATE` in
#: `hmad-dispatch.sh` (`_codex_hook_trust_arg`); a test pins the two equal.
CODEX_GATE_COMMAND = "python3 $HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py"
CODEX_HOOKS_ENV = "HMAD_CODEX_HOOKS_JSON"


def default_host_roots(environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    env = os.environ if environ is None else environ
    home = Path.home()
    agents = env[AGENTS_SKILLS_ENV] if AGENTS_SKILLS_ENV in env else str(home / ".agents" / "skills")
    agy = env[AGY_SKILLS_ENV] if AGY_SKILLS_ENV in env else str(home / ".gemini" / "config" / "skills")
    return agents, agy


def _check_skills_link(skills_link: Path) -> tuple[list[str], Path | None]:
    """Returns (issues, resolved_checkout_or_None)."""
    issues: list[str] = []

    if skills_link.is_symlink():
        target = skills_link.resolve()
        if not target.exists():
            issues.append(f"SKILL_DANGLING:{skills_link} -> {target}")
            return issues, None
        if not (target / CHECKOUT_MARKER).is_file():
            issues.append(f"SKILL_NOT_A_CHECKOUT:{skills_link} -> {target}")
            return issues, None
        return issues, target

    if not skills_link.exists():
        issues.append(f"SKILL_NOT_INSTALLED:{skills_link}")
        return issues, None

    # Exists, resolves, loads — and is a copy. The observed failure: it keeps
    # working while drifting, so nothing downstream reports it.
    issues.append(f"SKILL_NOT_SYMLINK:{skills_link}")
    if not (skills_link / CHECKOUT_MARKER).is_file():
        issues.append(f"SKILL_NOT_A_CHECKOUT:{skills_link}")
    return issues, None


def _check_hook_link(hook_link: Path) -> tuple[list[str], Path | None]:
    """Returns (issues, resolved_hook_or_None)."""
    issues: list[str] = []

    if not hook_link.exists():
        if hook_link.is_symlink():
            issues.append(f"HOOK_DANGLING:{hook_link} -> {hook_link.resolve()}")
        else:
            issues.append(f"HOOK_NOT_INSTALLED:{hook_link}")
        return issues, None

    return issues, hook_link.resolve()


def check_siblings(repo: Path, skills_dir: Path) -> list[str]:
    """Issues with the OTHER skills this checkout ships; empty means healthy.

    h-mad checked its own two links and nothing else. Measured 2026-08-28:
    `~/.claude/skills/h-mad` was a correct symlink while
    `~/.claude/skills/handoff` was a plain directory copied 68 days earlier.
    The copy is what a session actually loads, so a fix committed to the
    checkout a week before was invisible at runtime and the skill behaved as
    its June self — the same silent drift this script was written for, one
    directory over, where its check could not see it.

    A skill that is simply NOT installed is not an issue: not every skill in a
    checkout is one the operator wants loaded. Only a present-but-wrong install
    is reported, because only that one loads while lying about its contents.
    """
    issues: list[str] = []
    # When the checkout IS the skills directory, every skill dir is its own
    # install and there is nothing to compare — comparing anyway reports each
    # one as a copy of itself.
    try:
        if repo.resolve() == skills_dir.resolve():
            return issues
    except OSError:
        return issues
    for skill_md in sorted(repo.glob("*/" + CHECKOUT_MARKER)):
        name = skill_md.parent.name
        link = skills_dir / name
        if not link.is_symlink() and not link.exists():
            continue
        expected = (repo / name).resolve()
        if not link.is_symlink():
            issues.append(f"SIBLING_NOT_SYMLINK:{link} (expected -> {expected})")
            continue
        target = link.resolve()
        if not target.exists():
            issues.append(f"SIBLING_DANGLING:{link} -> {target}")
        elif target != expected:
            issues.append(f"SIBLING_WRONG_CHECKOUT:{link} -> {target} (expected {expected})")
    return issues


def checkout_skill_names(repo: Path) -> list[str]:
    return [p.parent.name for p in sorted(Path(repo).glob("*/" + CHECKOUT_MARKER))]


def split_agy_root(
    lines: Iterable[str], skills_dir: Path, names: Iterable[str], installed: Iterable[str]
) -> tuple[list[str], list[str]]:
    installed_set = set(installed)
    issues: list[str] = []
    details: list[str] = []
    for line in lines:
        owner = next(((name, kind) for name in names for kind in SIBLING_KINDS
                      if line.startswith(f"SIBLING_{kind}:{skills_dir / name} ")), None)
        if owner is None or owner[0] in installed_set:
            issues.append(line)
        else:
            details.append(f"AGY_SIBLING_COLLISION:{skills_dir / owner[0]} kind={owner[1]}")
    return issues, details


def lock_pinned_names(skills_dir: Path) -> set[str]:
    lock_file = skills_dir.parent / ".skill-lock.json"
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    skills = data.get("skills") if isinstance(data, Mapping) else None
    return {str(k) for k in skills} if isinstance(skills, Mapping) else set()


def split_agents_root(
    lines: Iterable[str], skills_dir: Path, names: Iterable[str], pinned: Iterable[str]
) -> tuple[list[str], list[str]]:
    name_list = list(names)
    must_symlink = (set(name_list) - set(pinned)) | set(AGY_INSTALLED_NAMES)
    issues, agy_details = split_agy_root(lines, skills_dir, name_list, must_symlink)
    return issues, [
        d.replace("AGY_SIBLING_COLLISION:", "AGENTS_SIBLING_COLLISION:", 1)
        for d in agy_details
    ]


def _hook_commands(node: object) -> Iterable[str]:
    if isinstance(node, Mapping):
        if node.get("enabled") is False:  # M:AH-DISABLED a switched-off hook never runs
            return
        command = node.get("command")
        if isinstance(command, str):
            yield command
        for value in node.values():
            yield from _hook_commands(value)
    elif isinstance(node, list):
        for value in node:
            yield from _hook_commands(value)


def check_agy_hook_targets(hooks_files: Iterable[Path], agy_root: Path) -> list[str]:
    """Hook commands that name a missing file under the agy skills root.

    An absent agy root adds no sibling line, which is right for an operator who
    never installed agy — and wrong when a live `hooks.json` runs a gate from
    under it. Measured 2026-10-18: `.agents/hooks.json` armed
    `~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py`, the root was
    absent, the hook exited 2 on every tool call, and `INSTALL:` said nothing.
    """
    issues: list[str] = []
    for hooks_file in hooks_files:
        try:
            data = json.loads(Path(hooks_file).read_text(encoding="utf-8"))
            commands = list(_hook_commands(data))
        except (OSError, ValueError, RecursionError):  # M:AH-UNREADABLE no verdict is worse than a skip
            continue
        for command in commands:
            try:
                tokens = shlex.split(command)
            except ValueError:
                continue
            for token in tokens:
                # Hook commands run through a shell: `$HOME` and `${HOME}` name the root too.
                target = Path(os.path.expandvars(os.path.expanduser(token)))  # M:AH-ENVVARS
                if not target.is_relative_to(agy_root):
                    continue
                if not target.exists():
                    issues.append(f"AGY_HOOK_TARGET_MISSING:{target}")
    return issues


def _snake(event: str) -> str:
    """`PreToolUse` -> `pre_tool_use`, the spelling codex uses in a trust key."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()


def _codex_gate_positions(hooks_json: Path) -> list[tuple[str, int, int]]:
    """(event, group index, hook index) of every h-mad gate entry.

    Raises ValueError naming the reason when the file is not the shape codex
    reads, so a malformed file is UNKNOWN rather than silently gate-free."""
    try:
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError("hooks-unreadable") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("hooks-unparseable") from exc
    events = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(events, dict):
        raise ValueError("hooks-shape")
    positions = []
    for event, groups in events.items():
        if not isinstance(groups, list):
            raise ValueError("hooks-shape")
        for gi, group in enumerate(groups):
            hooks = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(hooks, list):
                raise ValueError("hooks-shape")
            for hi, hook in enumerate(hooks):
                if isinstance(hook, dict) and hook.get("command") == CODEX_GATE_COMMAND:  # M:CT-GATE-ONLY
                    positions.append((event, gi, hi))
    return positions


def _codex_trust_records(codex_config: Path) -> dict[str, object]:
    """`[hooks.state]` of a codex config; ValueError(reason) when unreadable."""
    try:
        with codex_config.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ValueError("config-missing") from exc
    except OSError as exc:
        raise ValueError("config-unreadable") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError("config-unparseable") from exc
    state = data.get("hooks", {})
    state = state.get("state", {}) if isinstance(state, dict) else None
    if not isinstance(state, dict):
        raise ValueError("config-shape")
    return state


def check_codex_hook_trust(hooks_files: Iterable[Path], codex_config: Path) -> list[str]:
    """Advisory lines: does codex hold a trust record for each h-mad gate entry?

    Codex runs a project hook only with a `[hooks.state."<abs hooks.json>:<event>:
    <group>:<hook>"]` record or `--dangerously-bypass-hook-trust`, which
    `hmad-dispatch exec` passes and a hand-started codex does not. What the
    record's `trusted_hash` covers is unknown, so a present record is reported as
    recorded, never as enforced. Could-not-check is UNKNOWN, never either answer.
    """
    lines: list[str] = []
    records: dict[str, object] | None = None
    for hooks_json in (Path(p) for p in hooks_files):
        if not hooks_json.exists():
            continue  # codex is not wired in this project
        try:
            positions = _codex_gate_positions(hooks_json)
        except ValueError as exc:
            lines.append(f"CODEX_HOOK_TRUST_UNKNOWN:{hooks_json} reason={exc}")
            continue
        if not positions:
            continue
        if records is None:
            try:
                records = _codex_trust_records(codex_config)
            except ValueError as exc:  # M:CT-UNKNOWN
                lines.append(f"CODEX_HOOK_TRUST_UNKNOWN:{codex_config} reason={exc}")
                return lines
        for event, gi, hi in positions:
            key = f"{hooks_json.resolve()}:{_snake(event)}:{gi}:{hi}"
            record = records.get(key)
            if not isinstance(record, dict):  # M:CT-ABSENT
                lines.append(
                    f"CODEX_HOOK_UNTRUSTED:{key} config={codex_config} — a codex started "
                    "by hand skips the h-mad gate here; hmad-dispatch exec passes "
                    "--dangerously-bypass-hook-trust")
            elif record.get("enabled") is False:  # M:CT-DISABLED absent `enabled` is not off
                lines.append(f"CODEX_HOOK_DISABLED:{key} config={codex_config}")
            else:
                lines.append(
                    f"CODEX_HOOK_TRUST_RECORDED:{key} config={codex_config} (hash not verified)")
    return lines


def default_codex_config(environ: Mapping[str, str] | None = None) -> Path:
    """`$CODEX_HOME/config.toml`, else `~/.codex/config.toml`. On an Orca host
    CODEX_HOME is a per-account home and `~/.codex` is stale."""
    env = os.environ if environ is None else environ
    home = env.get("CODEX_HOME") or str(Path.home() / ".codex")
    return Path(home).expanduser() / "config.toml"


def default_codex_hooks_json(cwd: Path | None = None) -> Path:
    """`<git toplevel>/.codex/hooks.json`, the derivation `_codex_hook_trust_arg` uses.
    `$HMAD_CODEX_HOOKS_JSON` replaces it, as `HMAD_AGENTS_SKILLS_DIR` replaces a
    host root, so the suite never reads this repo's own gate file."""
    override = os.environ.get(CODEX_HOOKS_ENV)
    if override:  # M:CT-HOOKS-ENV
        return Path(override)
    here = Path.cwd() if cwd is None else cwd
    try:
        top = subprocess.run(["git", "-C", str(here), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        top = ""
    return Path(top or here) / ".codex" / "hooks.json"


def check(
    skills_link: Path, hook_link: Path, repo: Path | None = None, *,
    agents_skills_dir: Path | str | None = None,
    agy_skills_dir: Path | str | None = None,
    details: list[str] | None = None,
    hooks_files: Iterable[Path] = (),
) -> list[str]:
    """All issues with the install shape; empty means healthy."""
    skill_issues, checkout = _check_skills_link(skills_link)
    hook_issues, hook_target = _check_hook_link(hook_link)
    issues = skill_issues + hook_issues

    # Split install: each link is individually plausible but they resolve into
    # different checkouts, so the gate the operator arms and the gate the suites
    # exercise are different files. Only checkable when both sides resolved.
    if checkout is not None and hook_target is not None:
        expected = checkout.joinpath(*HOOK_RELPATH)
        if hook_target != expected:
            issues.append(f"SPLIT_INSTALL:skills={checkout} hook={hook_target}")

    # A correct h-mad link vouches for nothing but h-mad, so the neighbours are
    # checked too. The sibling root is one level UP from what the link resolves
    # to: `~/.claude/skills/h-mad` points at the repo's `h-mad` SUBDIRECTORY,
    # and the other skills are its siblings there. Deriving it from `checkout`
    # itself globbed h-mad's own subfolders, matched no SKILL.md, and reported
    # PASS over a genuinely stale copy — measured against the live install.
    sibling_repo = Path(repo) if repo is not None else (
        checkout.parent if checkout is not None else None
    )
    if sibling_repo is not None:
        issues += check_siblings(sibling_repo, skills_link.parent)
        if agents_skills_dir is not None:
            agents_root = Path(agents_skills_dir).expanduser()
            agents_issues, agents_details = split_agents_root(
                check_siblings(sibling_repo, agents_root), agents_root,
                checkout_skill_names(sibling_repo), lock_pinned_names(agents_root))
            issues += agents_issues
            if details is not None:
                details.extend(sorted(agents_details))
        if agy_skills_dir is not None:
            agy_root = Path(agy_skills_dir).expanduser()
            agy_issues, agy_details = split_agy_root(
                check_siblings(sibling_repo, agy_root), agy_root,
                checkout_skill_names(sibling_repo), AGY_INSTALLED_NAMES)
            issues += agy_issues
            if details is not None:
                details.extend(sorted(agy_details))

    if agy_skills_dir is not None:
        issues += check_agy_hook_targets(hooks_files, Path(os.path.expanduser(agy_skills_dir)))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="verify the h-mad install shape (two symlinks)"
    )
    parser.add_argument("--skills-link", default=str(DEFAULT_SKILLS_LINK))
    parser.add_argument("--hook-link", default=str(DEFAULT_HOOK_LINK))
    parser.add_argument(
        "--repo",
        default=None,
        help="checkout whose sibling skills to check; defaults to whatever "
             "--skills-link resolves to",
    )
    parser.add_argument("--agents-skills-dir", default=None)
    parser.add_argument("--agy-skills-dir", default=None)
    parser.add_argument(
        "--hooks-json",
        action="append",
        default=None,
        help="hooks.json whose commands may run from the agy skills root; "
             "repeatable; defaults to the project's .agents/hooks.json plus "
             "agy's global hooks.json beside the agy skills root",
    )
    parser.add_argument(
        "--codex-hooks-json",
        action="append",
        default=None,
        help="codex hooks.json whose h-mad gate trust to report; repeatable; "
             "defaults to <git toplevel>/.codex/hooks.json",
    )
    parser.add_argument(
        "--codex-config",
        default=None,
        help="codex config holding [hooks.state]; defaults to "
             "$CODEX_HOME/config.toml, else ~/.codex/config.toml",
    )
    args = parser.parse_args()

    # The one genuine operational error: no path to check, so there is no
    # verdict about any install. Reporting FAIL here would blame an install
    # that was never examined.
    if not args.skills_link.strip() or not args.hook_link.strip():
        print(
            "ERROR: --skills-link and --hook-link must both name a path",
            file=sys.stderr,
        )
        print("INSTALL: UNREADABLE")
        print(
            "  nothing was checked, so this is not a verdict about the install "
            "— pass both paths."
        )
        return 2

    default_agents, default_agy = default_host_roots()
    agents_dir = args.agents_skills_dir if args.agents_skills_dir is not None else default_agents
    agy_dir = args.agy_skills_dir if args.agy_skills_dir is not None else default_agy
    if not agents_dir.strip() or not agy_dir.strip():
        print("ERROR: --agents-skills-dir and --agy-skills-dir must name a path", file=sys.stderr)
        print("INSTALL: UNREADABLE")
        print("  nothing was checked, so this is not a verdict about the install — pass a path for each skill root.")
        return 2
    details: list[str] = []

    issues = check(
        Path(args.skills_link),
        Path(args.hook_link),
        Path(args.repo) if args.repo else None,
        agents_skills_dir=agents_dir,
        agy_skills_dir=agy_dir,
        details=details,
        # The project's hooks, and agy's GLOBAL hooks beside its skills root
        # (`~/.gemini/config/hooks.json`; 2026-10-31 residual). Derived from the skills
        # root, so a test that redirects that root never reads the real home.
        hooks_files=[Path(p) for p in (args.hooks_json or [
            Path.cwd() / ".agents" / "hooks.json",
            Path(agy_dir).expanduser().parent / "hooks.json",  # M:AH-GLOBAL-HOOKS
        ])],
    )

    if issues:
        print(f"INSTALL: FAIL issues={len(issues)}")
        for line in issues:
            print(line)
    else:
        print("INSTALL: PASS")
        print("OK")
    for line in details:
        print(line)
    # Advisory only: printed after the verdict and never counted in `issues=`,
    # because the summary line is read by substring and the gap is accepted.
    codex_config = Path(args.codex_config) if args.codex_config else default_codex_config()
    codex_hooks = [Path(p) for p in args.codex_hooks_json] if args.codex_hooks_json \
        else [default_codex_hooks_json()]
    for line in check_codex_hook_trust(codex_hooks, codex_config):  # M:CT-MAIN-WIRE
        print(line)
    # Exit 0 on either verdict; the caller reads the token, never `$?`.
    return 0


if __name__ == "__main__":
    sys.exit(main())
