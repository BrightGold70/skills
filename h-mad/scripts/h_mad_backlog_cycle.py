#!/usr/bin/env python3
"""Drive one skill-candidate backlog row through RED -> GREEN -> land.

Replaces the hand-scripted chain (redfull.sh / cycle.sh / land.sh) that drove
ten rows on 2026-10-18 (row 2661). It composes the sibling tools by path and
reimplements none of them:

    red   --row <name> --paths <tests...>   [-- assemble_tdd args]
    green --row <name> --paths <files...>   [--mutation-spec S] [-- assemble_tdd args]
    land  --row <name> --status "<text>"    [--no-push]

Every commit is pathspec-scoped to the declared paths, so two cycles open in
one tree never sweep each other's files into a commit. Each subcommand's last
line is one verdict token; any refusal exits non-zero.
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSEMBLE = HERE / "h_mad_assemble_tdd.py"
CONSUMERS = HERE / "h_mad_doc_consumers.py"
HARNESS = HERE / "h_mad_mutation_harness.py"
CENSUS = HERE.parents[1] / "handoff" / "scripts" / "skill_candidates_census.py"
RECORDS = Path(".h-mad") / "backlog-cycles"


class Refused(Exception):
    """A precondition failed; the message is the reason token."""


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=check)


def tool(path: Path, *args: str) -> int:
    """Run a sibling tool, echo its output, return its rc."""
    result = subprocess.run([sys.executable, str(path), *args],
                            capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def repo_relative(repo: Path, path: str) -> str:
    """A --paths entry as typed (relative to cwd) -> repo-relative POSIX."""
    absolute = Path(os.path.normpath(Path.cwd().resolve() / path))
    try:
        return absolute.relative_to(repo.resolve()).as_posix()
    except ValueError:
        raise Refused(f"path-outside-repo path={path}") from None


def slug(row: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", row.lower()).strip("-")


def check_row(store: Path, row: str) -> None:
    """The row must name exactly one OPEN candidate, by the census's own parser."""
    spec = importlib.util.spec_from_file_location("census", CENSUS)
    census = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(census)
    matches = [c for c in census.open_candidates(store.read_text(encoding="utf-8"))
               if c[2] == row]
    if len(matches) != 1:
        raise Refused(f"{'no-match' if not matches else 'ambiguous'} row={row}")


def load(repo: Path, row: str) -> dict | None:
    path = repo / RECORDS / f"{slug(row)}.json"
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    for key in ("commits", "paths", "specs"):
        record.setdefault(key, [])
    return record


def save(repo: Path, record: dict) -> None:
    path = repo / RECORDS / f"{slug(record['row'])}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")


def check_claims(repo: Path, row: str, paths: list[str]) -> None:
    """Refuse a path another still-open cycle has declared."""
    directory = repo / RECORDS
    for other in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        if other.stem == slug(row):
            continue
        claimed = set(json.loads(other.read_text()).get("paths", []))
        for path in paths:
            if path in claimed:
                raise Refused(f"path-claimed-by={other.stem} path={path}")


def commit(repo: Path, paths: list[str], message: str) -> str:
    """Commit exactly `paths`; refuse any that did not change."""
    for path in paths:
        if not git(repo, "status", "--porcelain", "--", path).stdout.strip():
            raise Refused(f"nothing-to-commit path={path}")
    git(repo, "add", "--", *paths)
    git(repo, "commit", "-q", "-m", message, "--", *paths)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def dispatch(phase: str, passthrough: list[str], extra: list[str]) -> None:
    rc = tool(ASSEMBLE, "--phase", phase, *extra, *passthrough)
    if rc != 0:
        raise Refused(f"assemble-rc={rc}")


def cmd_red(repo: Path, args, passthrough: list[str]) -> str:
    check_row(args.store, args.row)
    if load(repo, args.row) is not None:
        raise Refused(f"cycle-active row={args.row}")
    paths = [repo_relative(repo, p) for p in args.paths]
    check_claims(repo, args.row, paths)
    dispatch("red", passthrough, [])
    sha = commit(repo, paths, f"test: RED — {args.row}")
    save(repo, {"row": args.row, "commits": [sha], "paths": paths, "specs": []})
    return f"CYCLE: RED committed={sha}"


def cmd_green(repo: Path, args, passthrough: list[str]) -> str:
    check_row(args.store, args.row)
    record = load(repo, args.row)
    if record is None:
        raise Refused(f"no-red row={args.row}")
    paths = [repo_relative(repo, p) for p in args.paths]
    check_claims(repo, args.row, paths)
    extra = ["--mutation-spec", args.mutation_spec] if args.mutation_spec else []
    dispatch("green", passthrough, extra)
    sha = commit(repo, paths, f"feat: GREEN — {args.row}")
    spec = [repo_relative(repo, args.mutation_spec)] if args.mutation_spec else []
    save(repo, {**record, "commits": [*record["commits"], sha],
                "paths": sorted({*record["paths"], *paths}),
                "specs": record["specs"] + spec})
    return f"CYCLE: GREEN committed={sha}"


def is_document(rel: str) -> bool:
    # Mirrors h_mad_doc_consumers._is_document; imported tools may be absent.
    return not rel.endswith(".py") and "tests" not in Path(rel).parts[:-1]


def cycle_files(repo: Path, commits: list[str]) -> list[str]:
    """Files this cycle's own commits touched that still exist.

    Only the recorded commits: the range red^..HEAD would also cover another
    open cycle's commits and run its consumers and specs.
    """
    files: set[str] = set()
    for sha in commits:
        if git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode:
            raise Refused(f"commit-missing sha={sha}")
        out = git(repo, "diff-tree", "-r", "--root", "--no-commit-id", "--name-only",
                  "-z", sha).stdout
        files.update(name for name in out.split("\0") if name)
    return sorted(rel for rel in files if (repo / rel).exists())


def run_consumers(repo: Path, changed: list[str]) -> None:
    docs = [rel for rel in changed if is_document(rel)]
    if not docs:
        # Not a result: no document changed, so there is nothing to run.
        print("CONSUMERS: SKIPPED reason=no-documents")
        return
    rc = tool(CONSUMERS, "--repo", str(repo), "--run", *docs)
    if rc != 0:
        raise Refused(f"consumers-rc={rc}")


def run_mutation(repo: Path, record: dict, changed: list[str]) -> None:
    specs = sorted({*record["specs"],
                    *(rel for rel in changed
                      if "mutation-specs" in Path(rel).parts and rel.endswith(".json"))})
    if not specs:
        print("MUTATION: SKIPPED reason=no-specs")
        return
    rc = tool(HARNESS, "--sweep", "--isolate", *[str(repo / s) for s in specs])
    if rc != 0:
        raise Refused(f"mutation-rc={rc}")


def apply_status(store: Path, row: str, status: str) -> None:
    def cell(text: str) -> str:
        return text.replace("|", r"\|")

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as table:
        table.write(f"| name | status |\n|---|---|\n| {cell(row)} | {cell(status)} |\n")
    try:
        rc = tool(CENSUS, "--apply", table.name, str(store))
    finally:
        Path(table.name).unlink()
    if rc != 0:
        raise Refused(f"census-rc={rc}")


def cmd_land(repo: Path, args, passthrough: list[str]) -> str:
    check_row(args.store, args.row)
    record = load(repo, args.row)
    if record is None:
        raise Refused(f"no-red row={args.row}")
    if len(record["commits"]) < 2:
        raise Refused(f"no-green row={args.row}")
    store_rel = repo_relative(repo, str(args.store))
    if git(repo, "status", "--porcelain", "--", store_rel).stdout.strip():
        # Committing the store would sweep unrelated edits into the LANDED commit.
        raise Refused(f"store-dirty path={store_rel}")
    head_bytes = args.store.read_bytes()
    changed = cycle_files(repo, record["commits"])
    run_consumers(repo, changed)
    run_mutation(repo, record, changed)
    before_apply = args.store.read_bytes()
    apply_status(args.store, args.row, args.status)
    stamped = args.store.read_bytes()
    try:
        sha = commit(repo, [store_rel], f"docs(candidates): LANDED — {args.row}")
    except subprocess.CalledProcessError:
        # Leave the row OPEN and the record in place, so a retry can land it.
        # From HEAD, not the index: commit() already staged the edit, and the
        # store was clean before it, so HEAD is exactly what was there — unless
        # another process edited the store after the dirty check.
        if before_apply == head_bytes and args.store.read_bytes() == stamped:
            git(repo, "checkout", "HEAD", "--", store_rel)
        else:
            if args.store.read_bytes() == stamped:
                args.store.write_bytes(before_apply)
            git(repo, "reset", "HEAD", "--", store_rel)
        raise
    (repo / RECORDS / f"{slug(args.row)}.json").unlink()
    if args.no_push:
        return f"CYCLE: LANDED committed={sha} pushed=no"
    push = git(repo, "push", check=False)
    if push.returncode != 0:
        sys.stderr.write(push.stderr)
        return f"PUSH: REJECTED rc={push.returncode} committed={sha}"
    return f"CYCLE: LANDED committed={sha} pushed=yes"


def parse(argv: list[str]):
    own, passthrough = (argv[:argv.index("--")], argv[argv.index("--") + 1:]) \
        if "--" in argv else (argv, [])
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("red", "green", "land"):
        p = sub.add_parser(name)
        p.add_argument("--row", required=True)
        p.add_argument("--store", type=Path, default=None)
        if name != "land":
            p.add_argument("--paths", nargs="+", required=True)
    sub.choices["green"].add_argument("--mutation-spec")
    sub.choices["land"].add_argument("--status", required=True)
    sub.choices["land"].add_argument("--no-push", action="store_true")
    return parser.parse_args(own), passthrough


def main(argv: list[str] | None = None) -> int:
    args, passthrough = parse(list(sys.argv[1:] if argv is None else argv))
    top = git(Path.cwd(), "rev-parse", "--show-toplevel", check=False)
    if top.returncode != 0:
        print("CYCLE: REFUSED reason=not-a-git-repo")
        return 2
    repo = Path(top.stdout.strip())
    args.store = (args.store or repo / "docs" / "skill-candidates.md").resolve()
    handler = {"red": cmd_red, "green": cmd_green, "land": cmd_land}[args.command]
    try:
        verdict = handler(repo, args, passthrough)
    except Refused as exc:
        print(f"CYCLE: REFUSED reason={exc}")
        return 2
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or "")
        tail = exc.cmd[exc.cmd.index("--") + 1:] if "--" in exc.cmd else []
        suffix = f" path={','.join(tail)}" if tail else ""
        print(f"CYCLE: REFUSED reason=git-failed command={' '.join(exc.cmd[3:5])}{suffix}")
        return 2
    print(verdict)
    return 1 if verdict.startswith("PUSH: REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())
