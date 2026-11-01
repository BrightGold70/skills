"""The Phase-5 shell gate admits read-only `git`, and nothing that writes or executes.

Row "Phase-5 Codex gate refuses the read-only checks GREEN and the verifier are
told to run" (skill-candidates, recurrence 10): the 5e verifier was refused
`git diff`/`git show`, so it returned BLOCKED on ACs it could not measure
(spec-unchanged, scripts-unchanged, exact-diff) and the orchestrator measured
them by hand every time. Denylist agreed 2026-11-01: nine read verbs; nothing
before the verb (`-c alias.x=!sh` / `-c core.pager=` execute); and no
`--output`, `--ext-diff`, `--textconv` or `--filters`, nor any prefix git would
expand to one of them (git accepts unique abbreviations of long options).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

HMAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HMAD / "scripts"))
import h_mad_target_identity as identity  # noqa: E402


def _admits(command: str, tmp_path: Path) -> bool:
    return identity._safe_shell_command(command, tmp_path, str(tmp_path))


@pytest.mark.parametrize("command", [
    "git diff",
    "git diff --stat HEAD -- h-mad/scripts",
    "git show --stat abc123",
    "git log --oneline -5",
    "git status --short",
    "git rev-parse HEAD",
    "git ls-files h-mad/tests",
    "git merge-base HEAD main",
    "git cat-file -p HEAD:h-mad/SKILL.md",
    "git blame -L 1,20 h-mad/SKILL.md",
    "/usr/bin/git diff --name-only",
], ids=["diff", "diff-stat-path", "show", "log", "status", "rev-parse", "ls-files",
        "merge-base", "cat-file", "blame", "absolute-git"])
def test_read_only_git_is_admitted(command: str, tmp_path: Path) -> None:
    assert _admits(command, tmp_path), command


@pytest.mark.parametrize("command", [
    "git",
    "git checkout -- h-mad/scripts/x.py",
    "git commit -m x",
    "git stash",
    "git grep -O foo",
    "git -c core.pager=sh log",
    "git -c alias.d=!sh d",
    "git -C /tmp diff",
    "git --git-dir=/tmp/x log",
    "git -p log",
    "git diff --output=/tmp/x",
    "git diff --output /tmp/x",
    "git log --out=/tmp/x",
    "git diff --ext-diff",
    "git diff --ext",
    "git show --textconv HEAD",
    "git log --textc -p",
    "git cat-file --filters HEAD:x",
    "git cat-file --filt HEAD:x",
    "git diff --text",
], ids=["bare", "checkout", "commit", "stash", "grep-open-pager", "global-c-pager",
        "global-c-alias", "global-C", "global-git-dir", "global-paginate", "output-eq",
        "output-sep", "output-abbrev", "ext-diff", "ext-diff-abbrev", "textconv",
        "textconv-abbrev", "filters", "filters-abbrev", "text-is-a-textconv-prefix"])
def test_git_that_writes_or_executes_is_refused(command: str, tmp_path: Path) -> None:
    assert not _admits(command, tmp_path), command


def test_a_git_outside_the_trusted_bin_dirs_is_refused(tmp_path: Path) -> None:
    fake = tmp_path / "git"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    fake.chmod(0o755)
    assert not _admits(f"{fake} diff", tmp_path)


_GIT_LINE = re.compile(r"read-only `git` with exactly these verbs: (.+?)\.", re.S)


@pytest.mark.parametrize("template", [
    "references/codex-implementer-prompt.md",
    "references/codex-verifier-prompt.md",
    "audit-prompt.template.md",
])
def test_codex_prompts_name_exactly_the_git_verbs_the_gate_admits(template: str) -> None:
    text = (HMAD / template).read_text(encoding="utf-8")
    match = _GIT_LINE.search(text)
    assert match, f"{template} does not name the git verbs the gate admits"
    named = set(re.findall(r"`([a-z-]+)`", match.group(1)))
    assert named == identity.READ_ONLY_GIT_VERBS, named ^ identity.READ_ONLY_GIT_VERBS
    after = text[match.end():match.end() + 400]
    for option in identity.GIT_DENIED_OPTIONS:
        assert option in after, f"{template} must say {option} is refused"
