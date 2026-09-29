#!/usr/bin/env python3
"""Compare the committed runtime scripts with their pre-feature counterparts."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = Path("h-mad/scripts")
SCRIPT = {
    "budget": "h_mad_context_budget.py",
    "decision": "h_mad_resume_decision.py",
    "install-a": "h_mad_install_check.py",
    "install-b": "h_mad_install_check.py",
}
LINKS = tuple(
    Path.home() / root / name
    for root in (".agents/skills", ".gemini/config/skills")
    for name in ("h-mad", "handoff")
)


def clean_env(**settings: str) -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("CLAUDE")
        and key not in {"HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CONTEXT_WINDOW"}
    }
    env.update(settings)
    return env


def git(*args: str, timeout: float = 60.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, env=clean_env(),
        capture_output=True, text=True, timeout=timeout,
    )


def unreadable(reason: str) -> int:
    print(f"BYTE-IDENTITY: UNREADABLE reason={reason}")
    return 2


def turn(read: int) -> str:
    return json.dumps({
        "isSidechain": False, "type": "assistant",
        "message": {"usage": {
            "input_tokens": 10, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": read, "output_tokens": 999,
        }},
    }) + "\n"


def budget_cases(scratch: Path) -> list[tuple[str, list[str], dict[str, str]]]:
    home = scratch / "empty-home"
    home.mkdir()
    cases = []
    for name, used, extra in (
        ("ok-advisor", 1_000, []),
        ("deny-advisor", 525_732, []),
        ("run-ok", 790_000, ["--mode", "run"]),
        ("run-halt", 810_000, ["--mode", "run"]),
        ("window-zero", 1_000, ["--window", "0"]),
        ("missing-transcript", None, []),
        ("no-usage", None, []),
    ):
        transcript = scratch / f"{name}.jsonl"
        if used is not None:
            transcript.write_text(turn(used), encoding="utf-8")
        elif name == "no-usage":
            transcript.write_text('{"type":"user"}\n', encoding="utf-8")
        argv = ["--transcript", str(transcript), *extra]
        settings = {"HOME": str(home)} if name == "missing-transcript" else {}
        for suffix, host in (("unset", None), ("claude", "claude")):
            env = dict(settings)
            if host:
                env["HMAD_HOST"] = host
            cases.append((f"{name}-{suffix}", argv, env))
    return cases


def decision_cases(scratch: Path) -> list[tuple[str, list[str], dict[str, str]]]:
    now = "2026-09-29T00:00:00+00:00"
    cases = []
    for name in (
        "absent-file", "unreadable-file", "absent-feature",
        "foreign-owner-with-id", "foreign-owner-without-id", "halted",
        "complete", "lcp-4", "lcp-1",
    ):
        state = scratch / f"{name}.json"
        if name == "unreadable-file":
            state.write_text("{invalid", encoding="utf-8")
        elif name != "absent-file":
            record: dict[str, object] = {"last_completed_phase": 1}
            if name.startswith("foreign-owner"):
                record.update(owner_session_id="other", owner_heartbeat_ts=now)
            elif name == "halted":
                record["halt_reason"] = "probe"
            elif name == "complete":
                record["complete"] = True
            elif name == "lcp-4":
                record["last_completed_phase"] = 4
            feature = "other" if name == "absent-feature" else "probe"
            state.write_text(json.dumps({"orchestrator_state": {feature: record}}), encoding="utf-8")
        argv = ["--state", str(state), "--feature", "probe"]
        if name == "foreign-owner-with-id":
            argv += ["--session-id", "mine", "--now", now]
        for suffix, host in (("unset", None), ("claude", "claude")):
            cases.append((f"{name}-{suffix}", argv,
                          {"HMAD_HOST": host} if host else {}))
    return cases


def install_cases(scratch: Path, *, defaults: bool) -> list[tuple[str, list[str], dict[str, str]]]:
    cases = []
    for name in (
        "healthy", "stale-copy", "missing-hook", "split", "dangling",
        "absent-link", "sibling-copy", "sibling-other-checkout", "empty-path",
    ):
        root = scratch / name
        repo = root / "checkout"
        for skill_name in ("h-mad", "handoff"):
            skill = repo / skill_name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {skill_name}\n---\n", encoding="utf-8")
        hook_target = repo / "h-mad/hooks/h-mad-tdd-gate.sh"
        hook_target.parent.mkdir()
        hook_target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        other = root / "other-checkout/handoff"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("---\nname: handoff\n---\n", encoding="utf-8")
        link_dir = root / "links"
        link_dir.mkdir()
        skills = link_dir / "h-mad"
        skills.symlink_to(repo / "h-mad")
        hook = root / "hook"
        hook.symlink_to(hook_target)
        sibling = link_dir / "handoff"
        skill_arg, hook_arg = str(skills), str(hook)
        if name == "stale-copy":
            copy = root / "stale"
            copy.mkdir()
            (copy / "SKILL.md").write_text("stale\n", encoding="utf-8")
            skill_arg = str(copy)
        elif name == "missing-hook":
            hook_arg = str(root / "missing-hook")
        elif name == "split":
            split = root / "split-hook"
            split.symlink_to(other / "hook")
            hook_arg = str(split)
        elif name == "dangling":
            dangling = root / "dangling"
            dangling.symlink_to(root / "gone")
            skill_arg = str(dangling)
        elif name == "absent-link":
            skill_arg = str(root / "absent-link")
        elif name == "sibling-copy":
            sibling.mkdir()
            (sibling / "SKILL.md").write_text("stale\n", encoding="utf-8")
        elif name == "sibling-other-checkout":
            sibling.symlink_to(other)
        elif name == "empty-path":
            skill_arg = ""
        argv = ["--skills-link", skill_arg, "--hook-link", hook_arg, "--repo", str(repo)]
        settings = {} if defaults else {
            "HMAD_AGENTS_SKILLS_DIR": str(root / "absent-agents"),
            "HMAD_AGY_SKILLS_DIR": str(root / "absent-agy"),
        }
        cases.append((name, argv, settings))
    return cases


def collisions(scratch: Path) -> set[str]:
    names = git("ls-files", "*/SKILL.md")
    if names.returncode:
        raise RuntimeError("git ls-files failed")
    repo_names = sorted({line.split("/", 1)[0] for line in names.stdout.splitlines()
                         if line.count("/") == 1})
    root = Path.home() / ".gemini/config/skills"
    listed = sorted(p.name for p in root.iterdir())
    # P8's `comm -12` reading, with the same two sorted input streams.
    source_file, root_file = scratch / "repo-names", scratch / "agy-names"
    source_file.write_text("".join(f"{name}\n" for name in repo_names), encoding="utf-8")
    root_file.write_text("".join(f"{name}\n" for name in listed), encoding="utf-8")
    result = subprocess.run(
        ["comm", "-12", str(source_file), str(root_file)],
        env=clean_env(), capture_output=True, text=True, timeout=60.0,
    )
    if result.returncode:
        raise RuntimeError("comm -12 failed")
    return set(result.stdout.splitlines())


def closed_diff(old: str, new: str, old_rc: int, new_rc: int,
                collision_names: set[str]) -> bool:
    if old_rc != new_rc:
        return False
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    old_verdict = next((i for i, line in enumerate(old_lines) if line.startswith("INSTALL:")), None)
    new_verdict = next((i for i, line in enumerate(new_lines) if line.startswith("INSTALL:")), None)
    if old_verdict is None or new_verdict is None:
        return False
    if old_lines[old_verdict] != new_lines[new_verdict]:
        old_lines.pop(old_verdict)
        new_lines.pop(new_verdict)
        if old_lines[old_verdict:old_verdict + 1] == ["OK\n"]:
            old_lines.pop(old_verdict)
        if new_lines[new_verdict:new_verdict + 1] == ["OK\n"]:
            new_lines.pop(new_verdict)
    permitted = {str(path) for path in LINKS}
    filtered = []
    for line in new_lines:
        if line.startswith("SIBLING_"):
            match = re.match(r"^SIBLING_[A-Z_]+:(\S+)", line)
            if match and match.group(1) in permitted:
                continue
        if line.startswith("AGY_SIBLING_COLLISION:"):
            match = re.match(r"^AGY_SIBLING_COLLISION:(\S+) kind=", line)
            if match and Path(match.group(1)).parent == Path.home() / ".gemini/config/skills" \
                    and Path(match.group(1)).name in collision_names:
                continue
        filtered.append(line)
    return old_lines == filtered


def compare(name: str, argv: list[str], settings: dict[str, str], arm: str,
            base: Path, collision_names: set[str]) -> bool:
    outputs = []
    for tree in (base, ROOT):
        result = subprocess.run(
            [sys.executable, str(tree / SCRIPTS / SCRIPT[arm]), *argv],
            cwd=tree, env=clean_env(**settings), capture_output=True,
            timeout=60.0,
        )
        outputs.append(result)
    old, new = outputs
    if arm == "install-b":
        matches = closed_diff(old.stdout.decode(errors="replace"),
                              new.stdout.decode(errors="replace"),
                              old.returncode, new.returncode, collision_names)
    else:
        matches = old.returncode == new.returncode and old.stdout == new.stdout
    if matches:
        return True
    print(f"BYTE-IDENTITY: FAIL arm={arm} case={name}")
    print(f"exit codes: base={old.returncode} current={new.returncode}")
    print("".join(difflib.unified_diff(
        old.stdout.decode(errors="replace").splitlines(keepends=True),
        new.stdout.decode(errors="replace").splitlines(keepends=True),
        fromfile="base stdout", tofile="current stdout")), end="")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--arm", required=True, choices=tuple(SCRIPT))
    args = parser.parse_args()
    if args.arm == "install-b" and any(not path.is_symlink() for path in LINKS):
        return unreadable("links_absent")
    resolved = git("rev-parse", "--verify", f"{args.base}^{{commit}}")
    if resolved.returncode:
        return unreadable("bad_base")
    with tempfile.TemporaryDirectory(prefix="byte-identity-") as scratch_name:
        scratch = Path(scratch_name)
        base = scratch / "base"
        added = git("worktree", "add", "--detach", str(base), resolved.stdout.strip())
        if added.returncode:
            return unreadable("worktree_add_failed")
        try:
            fixtures = scratch / "fixtures"
            fixtures.mkdir()
            collision_names = collisions(fixtures) if args.arm == "install-b" else set()
            if args.arm == "budget":
                cases = budget_cases(fixtures)
            elif args.arm == "decision":
                cases = decision_cases(fixtures)
            else:
                cases = install_cases(fixtures, defaults=args.arm == "install-b")
                if args.arm == "install-b":
                    cases.append(("real-checkout", [
                        "--skills-link", str(Path.home() / ".claude/skills/h-mad"),
                        "--repo", "/Users/kimhawk/orca/skills",
                    ], {}))
            failed = next((False for name, argv, settings in cases
                           if not compare(name, argv, settings, args.arm, base, collision_names)), None)
        finally:
            git("worktree", "remove", "--force", str(base))
        listing = git("worktree", "list", "--porcelain")
        if listing.returncode or any(line == f"worktree {base}" for line in listing.stdout.splitlines()):
            return unreadable("worktree_left")
        if failed is not None:
            return 0
        print(f"BYTE-IDENTITY: PASS arm={args.arm} cases={len(cases)}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
