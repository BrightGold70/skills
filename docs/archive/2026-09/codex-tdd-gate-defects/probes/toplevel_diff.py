#!/usr/bin/env python3
"""Report changed or removed top-level statements in existing test modules."""

import argparse
import ast
import os
from pathlib import Path
import subprocess
import sys


TEST_ROOTS = ("h-mad/tests", "handoff/tests", "handoff/scripts")


def git(repo, *args, check=True):
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("CLAUDE") and key not in ("HPW_AGENT_BACKEND", "HMAD_HOST")
    }
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        env=env,
    )


def version(repo, ref, path):
    result = git(repo, "show", "{}:{}".format(ref, path), check=False)
    return result.stdout.decode("utf-8") if result.returncode == 0 else None


def targets(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in targets(item)]
    return []


def statements(source):
    if source is None:
        return {}
    found = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            key = node.name
        elif isinstance(node, ast.Assign):
            key = ",".join(name for target in node.targets for name in targets(target))
        elif isinstance(node, ast.AnnAssign):
            key = ",".join(targets(node.target))
        else:
            continue
        if key:
            found[key] = ast.get_source_segment(source, node)
    return found


def sibling_imports(source):
    if source is None:
        return set()
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".", 1)[0])
            elif node.level == 1:
                found.update(alias.name for alias in node.names)
    return found


def file_set(repo, base, head):
    diff = git(
        repo, "diff", "--diff-filter=M", "--name-only", base, head,
        "--", *TEST_ROOTS,
    ).stdout.decode("utf-8")
    modified = {path for path in diff.splitlines() if path.endswith(".py")}
    selected = set(modified)
    for path in modified:
        directory = Path(path).parent
        for parent in (directory, *directory.parents):
            if str(parent) == ".":
                break
            conftest = (parent / "conftest.py").as_posix()
            if version(repo, base, conftest) is not None:
                selected.add(conftest)
        imports = sibling_imports(version(repo, base, path))
        imports.update(sibling_imports(version(repo, head, path)))
        for name in imports:
            sibling = (directory / (name + ".py")).as_posix()
            if version(repo, base, sibling) is not None:
                selected.add(sibling)
    return sorted(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", type=Path)
    args = parser.parse_args()
    if args.repo is None:
        probe_dir = Path(__file__).resolve().parent
        root = git(probe_dir, "rev-parse", "--show-toplevel", check=False)
        if root.returncode:
            print("TOPDIFF: UNREADABLE reason=repo", file=sys.stderr)
            return 2
        args.repo = Path(root.stdout.decode("utf-8").strip())
    for ref in (args.base, args.head):
        if git(args.repo, "rev-parse", "--verify", "{}^{{commit}}".format(ref), check=False).returncode:
            print("TOPDIFF: UNREADABLE reason=bad_sha")
            return 2
    try:
        files = file_set(args.repo, args.base, args.head)
        changed = removed = 0
        for path in files:
            before = statements(version(args.repo, args.base, path))
            after = statements(version(args.repo, args.head, path))
            for key, segment in before.items():
                if key not in after:
                    print("TOPDIFF: removed {}::{}".format(path, key))
                    removed += 1
                elif segment != after[key]:
                    print("TOPDIFF: changed {}::{}".format(path, key))
                    changed += 1
    except (subprocess.CalledProcessError, UnicodeError, SyntaxError) as exc:
        print("TOPDIFF: UNREADABLE reason=read_error detail={}".format(exc), file=sys.stderr)
        return 2
    print("TOPDIFF: DONE files={} changed={} removed={}".format(len(files), changed, removed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
