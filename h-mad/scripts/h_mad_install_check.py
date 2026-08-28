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
import sys
from pathlib import Path

DEFAULT_SKILLS_LINK = Path.home() / ".claude" / "skills" / "h-mad"
DEFAULT_HOOK_LINK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"

#: Marks a resolved directory as an h-mad checkout rather than any other target.
CHECKOUT_MARKER = "SKILL.md"

#: Where the hook link must land inside the checkout.
HOOK_RELPATH = ("hooks", "h-mad-tdd-gate.sh")


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


def check(skills_link: Path, hook_link: Path, repo: Path | None = None) -> list[str]:
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

    issues = check(
        Path(args.skills_link),
        Path(args.hook_link),
        Path(args.repo) if args.repo else None,
    )

    if issues:
        print(f"INSTALL: FAIL issues={len(issues)}")
        for line in issues:
            print(line)
    else:
        print("INSTALL: PASS")
        print("OK")
    # Exit 0 on either verdict; the caller reads the token, never `$?`.
    return 0


if __name__ == "__main__":
    sys.exit(main())
