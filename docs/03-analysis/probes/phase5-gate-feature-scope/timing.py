"""Measure complete Phase 5 hook calls against an extracted baseline."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from discovery_probe import probe_main


HOOKS = {
    "codex": "h-mad-codex-tdd-gate.py",
    "agy": "h-mad-agy-tdd-gate.py",
    "claude": "h-mad-tdd-gate.sh",
}
STATE_FILE = Path("docs/.bkit-memory.json")
SECOND = "second-checkout"
TARGETS = ("document", "production", "state-file", "shell", SECOND)


class Reading(NamedTuple):
    hook: str
    target: str
    old_ms: float
    new_ms: float
    record: str = "none"
    old_git: int | None = None
    new_git: int | None = None

    @property
    def added_ms(self) -> float:
        return self.new_ms - self.old_ms


def _git(executable: str, root: Path, env: dict[str, str], *args: str) -> bytes:
    return subprocess.check_output([executable, *args], cwd=root, env=env, timeout=30)


def _scratch_checkouts(scratch: Path, git: str, env: dict[str, str]) -> tuple[Path, Path]:
    root, second = scratch / "repository", scratch / "second checkout"
    root.mkdir()
    _git(git, root, env, "init", "-q")
    (root / "docs").mkdir()
    (root / "docs/notes.md").write_text("# Timing fixture\n", encoding="utf-8")
    for i in range(2_000):
        directory = root / f"data-{i:04}"
        directory.mkdir()
        for j in range(10):
            (directory / f"sample-{j}").touch()
    _git(git, root, env, "add", ".")
    _git(git, root, env, "-c", "user.name=Timing", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "commit", "-qm", "timing fixture")
    _git(git, root, env, "worktree", "add", "-q", "--detach", str(second), "HEAD")
    return root, second


def _other_checkout(root: Path, git: str, env: dict[str, str]) -> Path:
    listing = _git(git, root, env, "worktree", "list", "--porcelain", "-z")
    for entry in listing.split(b"\0\0"):
        first, *fields = entry.split(b"\0")
        if not first.startswith(b"worktree ") or b"bare" in fields:
            continue
        candidate = Path(os.fsdecode(first[len(b"worktree "):])).resolve()
        if candidate != root and (candidate / ".git").exists():
            return candidate
    raise ValueError("--repo must have a second checkout available")


def _record_state(root: Path, identity) -> str:
    try:
        content = identity._read_regular_text(root / STATE_FILE)
    except FileNotFoundError:
        return "none"
    records = json.loads(content).get("orchestrator_state", {})
    return "live" if any(isinstance(row, dict) and row.get("phase") == "step5"
                         for row in records.values()) else "none"


def _bench(diff, hook: str, root: Path, target: str, value: Path, record: str,
           trees: tuple[Path, Path], runs: int, env: dict[str, str], scratch: Path) -> Reading:
    if target == "shell":
        payload = diff._shell_payload(f"{hook}-shell", "git status --short", str(root))
    else:
        surface = hook if hook == "claude" else f"{hook}-write"
        payload = diff._write_payload(surface, str(value))
    stdin = json.dumps(payload)
    cwd = root
    if hook == "agy":
        # The agy host starts the hook one level below the checkout root.
        cwd = next((path for path in (root / ".agents", root / "docs", root / ".git")
                    if path.is_dir() and not path.is_symlink()), None)
        if cwd is None:
            cwd = next((path for path in root.iterdir() if path.is_dir() and not path.is_symlink()), None)
        if cwd is None:
            raise ValueError("agy timing requires a subdirectory in the checkout")
    launcher = "/bin/bash" if hook == "claude" else sys.executable
    log = scratch / "git.log"

    def call(tree: Path, count: bool = False) -> float:
        package = tree / "h-mad"
        child_env = dict(env, CLAUDE_PROJECT_DIR=str(root), _TIMING_GIT_LOG=str(log))
        bins = [str(scratch / "bin"), str(package / "bin"), env.get("PATH", os.defpath)]
        if count:
            bins.insert(0, str(scratch / "count"))
        child_env["PATH"] = os.pathsep.join(bins)
        command = [launcher, str(package / "hooks" / HOOKS[hook])]
        start = time.perf_counter()
        result = subprocess.run(command, input=stdin, text=True, capture_output=True,
                                env=child_env, cwd=cwd, timeout=30)
        elapsed = (time.perf_counter() - start) * 1000
        outcome = diff._TEST_SUPPORT.host_decision(hook, result)
        if outcome.decision not in {"allow", "deny"}:
            raise ValueError(f"{hook} {target}: invalid hook answer {outcome.reason!r}")
        return elapsed

    old, new = [], []
    for _ in range(runs):
        old.append(call(trees[0]))
        new.append(call(trees[1]))
    counts = []
    for tree in trees:
        log.write_bytes(b"")
        call(tree, count=True)
        counts.append(log.read_bytes().count(b"\n"))
    return Reading(hook, target, statistics.median(old), statistics.median(new), record, *counts)


def _measure(args: argparse.Namespace, hooks: tuple[str, ...]) -> list[Reading]:
    # Keep probe caches and subprocess scratch files outside the measured checkout.
    sys.dont_write_bytecode = True
    import differential as diff

    sys.path.insert(0, str(diff.ROOT / "h-mad/scripts"))
    import h_mad_target_identity as identity

    with tempfile.TemporaryDirectory(prefix="phase5-timing-", dir="/tmp") as directory:
        scratch = Path(directory).resolve()
        env = diff._hook_environment(scratch, {})
        git = diff._TEST_SUPPORT.hook_git(env.get("PATH", os.defpath))
        home = scratch / "home"
        home.mkdir()
        env.update(HOME=str(home), TMPDIR=str(scratch), GIT_OPTIONAL_LOCKS="0",
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", _TIMING_GIT=git)
        bin_dir = scratch / "bin"
        bin_dir.mkdir()
        (bin_dir / "git").symlink_to(git)
        (bin_dir / "python3").symlink_to(Path(sys.executable).absolute())
        (scratch / "count").mkdir()
        diff._shell_shim(scratch / "count/git", 'printf ".\\n" >> "$_TIMING_GIT_LOG"\n'
                         'exec "$_TIMING_GIT" "$@"\n')

        trees = (args.old.resolve(strict=True), diff.ROOT)
        if args.repo is None:
            root, second = _scratch_checkouts(scratch, git, env)
            states = ("none", "live")
        else:
            root = args.repo.resolve(strict=True)
            top = _git(git, root, env, "rev-parse", "--show-toplevel")
            if Path(os.fsdecode(top.rstrip(b"\n"))).resolve() != root:
                raise ValueError("--repo must name a checkout root")
            second = _other_checkout(root, git, env)
            states = (_record_state(root, identity),)

        # Use a fresh prospective Python path so a live checkout cannot run an
        # existing test as a side effect of the read-only benchmark.
        production = f"{scratch.name}.py"
        targets = (("document", root / "docs/notes.md"),
                   ("production", root / production), ("state-file", root / STATE_FILE))
        readings = []
        for record in states:
            if args.repo is None and record == "live":
                diff._TEST_SUPPORT.write_state(root, {diff._fixture_feature(): {"phase": "step5"}})
            for hook in hooks:
                cases = targets if hook == "claude" else (*targets, ("shell", root))
                for target, value in cases:
                    readings.append(_bench(diff, hook, root, target, value, record,
                                           trees, args.runs, env, scratch))
        for hook in hooks:
            readings.append(_bench(diff, hook, root, SECOND, second / production, states[-1],
                                   trees, args.runs, env, scratch))
        return readings


def _samples(path: Path, hooks: tuple[str, ...]) -> list[Reading]:
    readings = []
    for row in json.loads(path.read_text(encoding="utf-8")):
        reading = Reading(**row)
        if (reading.hook not in HOOKS or reading.target not in TARGETS
                or reading.record not in {"none", "live"}
                or any(type(ms) not in {int, float} or not math.isfinite(ms) or ms < 0
                       for ms in (reading.old_ms, reading.new_ms))):
            raise ValueError("invalid timing sample")
        if reading.hook in hooks:
            readings.append(reading)
    return readings


def _number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _lines(readings: list[Reading], hooks: tuple[str, ...]) -> list[str]:
    bounded = [row for row in readings if row.target != SECOND]
    second = [row for row in readings if row.target == SECOND]
    if sorted(row.hook for row in second) != sorted(hooks):
        raise ValueError("expected one second-checkout sample per hook")
    max_added = max(row.added_ms for row in bounded)
    lines = [f"TIMING: max_added_ms={_number(max_added)} bound=300"]
    for row in (*bounded, *second):
        fields = (f"hook={row.hook} record={row.record} "
                  f"old_ms={_number(row.old_ms)} new_ms={_number(row.new_ms)}")
        if row.old_git is not None:
            fields += f" old_git={row.old_git} new_git={row.new_git}"
        if row.target == SECOND:
            lines.append(f"TIMING-SECOND-CHECKOUT: added_ms={_number(row.added_ms)} {fields}")
        else:
            lines.append(f"TIMING-CASE: target={row.target} {fields}")
    return lines


@probe_main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--hook", choices=HOOKS, action="append")
    parser.add_argument("--samples", type=Path)
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be positive")
    hooks = tuple(dict.fromkeys(args.hook or HOOKS))
    readings = _samples(args.samples, hooks) if args.samples else _measure(args, hooks)
    lines = _lines(readings, hooks)
    if args.samples is None:
        lines.append("TIMING-GIT: resolved toolchain git excludes host launcher overhead per git call")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
