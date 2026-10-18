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
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


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
    return json.loads(path.read_text()) if path.exists() else None


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
    check_claims(repo, args.row, args.paths)
    dispatch("red", passthrough, [])
    sha = commit(repo, args.paths, f"test: RED — {args.row}")
    save(repo, {"row": args.row, "red_commit": sha, "paths": args.paths, "specs": []})
    return f"CYCLE: RED committed={sha}"


def cmd_green(repo: Path, args, passthrough: list[str]) -> str:
    check_row(args.store, args.row)
    record = load(repo, args.row)
    if record is None:
        raise Refused(f"no-red row={args.row}")
    check_claims(repo, args.row, args.paths)
    extra = ["--mutation-spec", args.mutation_spec] if args.mutation_spec else []
    dispatch("green", passthrough, extra)
    sha = commit(repo, args.paths, f"feat: GREEN — {args.row}")
    specs = record["specs"] + ([args.mutation_spec] if args.mutation_spec else [])
    save(repo, {**record, "paths": sorted({*record["paths"], *args.paths}),
                "specs": specs})
    return f"CYCLE: GREEN committed={sha}"


def is_document(rel: str) -> bool:
    # Mirrors h_mad_doc_consumers._is_document; imported tools may be absent.
    return not rel.endswith(".py") and "tests" not in Path(rel).parts[:-1]


def changed_since(repo: Path, red_commit: str) -> list[str]:
    parent = git(repo, "rev-parse", "--verify", "--quiet", f"{red_commit}^", check=False)
    base = parent.stdout.strip() or EMPTY_TREE
    return git(repo, "diff", "--name-only", base, "HEAD").stdout.split()


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
    changed = changed_since(repo, record["red_commit"])
    run_consumers(repo, changed)
    run_mutation(repo, record, changed)
    apply_status(args.store, args.row, args.status)
    store_rel = args.store.resolve().relative_to(repo).as_posix()
    sha = commit(repo, [store_rel], f"docs(candidates): LANDED — {args.row}")
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
    print(verdict)
    return 1 if verdict.startswith("PUSH: REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())
