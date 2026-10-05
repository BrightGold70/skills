#!/usr/bin/env python3
"""Name the tests that PARSE a document you are about to commit.

A doc-derived test lives next to the CONSUMER of a document, never next to the
document, so editing `h-mad/SKILL.md` gives no hint that
`h-mad/tests/test_h_mad_context_budget_docs.py` parses one of its sections. Twice
a commit was pushed on a green targeted slice and was red in the full suite on a
guard in a third file (skill-candidates row "name the tests that PARSE a
document you are about to edit").

Usage:
  h_mad_doc_consumers.py [--repo DIR] [--staged] [--run [--timeout S]] [PATH ...]

Prints, per document, `CONSUMERS: <doc> n=<K>` followed by the test files, then
one `RUN: python3 -m pytest -q <files>` line covering them all (omitted when
there are none). Without `--run`, exit 0 always: this NAMES tests, it decides
nothing.

`--run` prints the same lines, then EXECUTES that RUN line's own file list as
`<this interpreter> -m pytest -q <files>` from the repo toplevel. "This
interpreter" is the one running the script (`sys.executable`; through the
shebang that is the `python3` on PATH), named on a `RUN-WITH:` line, so a
missing pytest is `UNREADABLE`, never a spawned interpreter that errors.
pytest's own output streams to stderr as it runs (a SKILL.md run is ~77 files
and several minutes); stdout keeps the lines above and ends with one verdict
token. Read the token, not `$?`:

    CONSUMERS-RUN: PASS files=<k> passed=<n>                        exit 0
    CONSUMERS-RUN: FAIL files=<k> failed=<n>   (+ FAILED/ERROR ids) exit 1
    CONSUMERS-RUN: NONE   (documents exist, nothing reads them)     exit 0
    CONSUMERS-RUN: UNREADABLE reason=<r>                            exit 2
      pytest-missing | no-summary | unknown-docs | timeout | interrupted
      | incomplete rc=<n> summary="<pytest summary>"
        (nothing failed, but pytest exited non-zero or nothing passed)

Fail closed: no pytest, no summary line, a run that passed nothing or exited
non-zero without a failure, `--timeout` (default 1800 s), Ctrl-C, no document,
a missing document, a path that is absolute or leaves the repo (give
repo-relative paths), or a git failure is UNREADABLE, never PASS or NONE.

A test counts as a consumer when its source contains the document's basename
AND either lives in the same top-level directory as the document or also names
that directory. Over-reporting is the safe direction here: an extra file in the
RUN line costs seconds, a missing one is the defect this exists for. `.py`
files and test files themselves are not documents and are skipped.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import re
import subprocess
import sys
import threading
from pathlib import Path

# pytest's last line: `2 passed in 0.01s`, `1 failed, 3 passed, 1 warning in
# 9.12s (0:00:09)`, `no tests ran in 0.00s`, optionally framed by `=`.
_SUMMARY = re.compile(r"^=*\s*(no tests ran|\d+ \w+(?:, \d+ \w+)*) in \d+(?:\.\d+)?s"
                      r"(?: \([\d:]+\))?\s*=*$")


def _git(repo: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(repo), "-c", "core.quotePath=false", *args],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return [line for line in out.stdout.split("\0") if line]


def _is_document(rel: str) -> bool:
    parts = Path(rel).parts
    return not rel.endswith(".py") and "tests" not in parts[:-1]


def _test_files(repo: Path) -> list[str]:
    return sorted(rel for rel in _git(repo, "ls-files", "-z", "--", "*.py")
                  if "tests" in Path(rel).parts[:-1])


def consumers(repo: Path, doc: str, tests: list[str]) -> list[str]:
    base = Path(doc).name
    top = Path(doc).parts[0] if len(Path(doc).parts) > 1 else ""
    found = []
    for rel in tests:
        try:
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if base not in text:
            continue
        if not top or Path(rel).parts[0] == top or top in text:
            found.append(rel)
    return found


def run_consumers(repo: Path, files: list[str], timeout: float) -> int:
    """Execute exactly `files` (the RUN line's list) and print one verdict token."""
    if importlib.util.find_spec("pytest") is None:
        print("CONSUMERS-RUN: UNREADABLE reason=pytest-missing")
        return 2
    print(f"RUN-WITH: {sys.executable} (Python {platform.python_version()})", flush=True)
    lines: list[str] = []
    expired: list[bool] = []
    try:
        proc = subprocess.Popen([sys.executable, "-m", "pytest", "-q", *files],
                                cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace")
    except OSError:
        print("CONSUMERS-RUN: UNREADABLE reason=no-summary")
        return 2
    timer = threading.Timer(timeout, lambda: (expired.append(True), proc.kill()))
    timer.start()
    try:
        for line in proc.stdout:
            sys.stderr.write(line)  # progress as it happens; stdout stays the verdict
            lines.append(line.rstrip("\n"))
        rc = proc.wait()
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
        print("CONSUMERS-RUN: UNREADABLE reason=interrupted")
        return 2
    finally:
        timer.cancel()
    if expired:
        print(f"CONSUMERS-RUN: UNREADABLE reason=timeout after={timeout:g}s")
        return 2
    summary = None
    for line in lines:
        match = _SUMMARY.match(line.strip())
        if match:
            summary = match.group(1)
    if summary is None:
        print("CONSUMERS-RUN: UNREADABLE reason=no-summary")
        for line in lines[-15:]:
            print(f"  {line}")
        return 2
    counts = {name.rstrip("s"): int(n) for n, name in re.findall(r"(\d+) (\w+)", summary)}
    failed = counts.get("failed", 0) + counts.get("error", 0)
    passed = counts.get("passed", 0)
    if failed:
        print(f"CONSUMERS-RUN: FAIL files={len(files)} failed={failed}")
        for line in lines:
            if line.startswith(("FAILED ", "ERROR ")):
                print(f"  {line.split(' - ', 1)[0]}")
        return 1
    if rc != 0 or not passed:
        print(f'CONSUMERS-RUN: UNREADABLE reason=incomplete rc={rc} summary="{summary}"')
        return 2
    print(f"CONSUMERS-RUN: PASS files={len(files)} passed={passed}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("paths", nargs="*", help="repo-relative documents")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--staged", action="store_true",
                    help="use the documents staged for commit")
    ap.add_argument("--run", action="store_true",
                    help="execute the RUN line and print a CONSUMERS-RUN verdict token")
    ap.add_argument("--timeout", type=float, default=1800.0,
                    help="seconds before --run stops pytest and reports UNREADABLE (default 1800)")
    args = ap.parse_args(argv)

    try:
        repo = Path(_git(args.repo, "rev-parse", "--show-toplevel")[0].strip())
        docs = list(args.paths)
        if args.staged:
            docs += _git(repo, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
        docs = sorted({d for d in docs if _is_document(d)})
        tests = _test_files(repo) if docs else []
    except (RuntimeError, IndexError) as exc:
        print(f"CONSUMERS: UNKNOWN — {exc}")
        if args.run:
            print("CONSUMERS-RUN: UNREADABLE reason=unknown-docs")
            return 2
        return 0
    # An absolute path or one leaving the repo names ANOTHER copy of the document
    # (another worktree's), while the consumers would run against this repo's.
    missing = [d for d in docs if Path(d).is_absolute()
               or os.path.normpath(d).split(os.sep)[0] == ".."
               or not (repo / d).is_file()]
    if args.run and (not docs or missing):
        print("CONSUMERS-RUN: UNREADABLE reason=unknown-docs"
              + (" missing=" + ",".join(missing) if missing else " no-documents"))
        return 2

    union: list[str] = []
    for doc in docs:
        hits = consumers(repo, doc, tests)
        print(f"CONSUMERS: {doc} n={len(hits)}")
        for rel in hits:
            print(f"  {rel}")
            if rel not in union:
                union.append(rel)
    files = sorted(union)
    if files:
        print("RUN: python3 -m pytest -q " + " ".join(files))
    if args.run:
        if not files:
            print("CONSUMERS-RUN: NONE")
            return 0
        return run_consumers(repo, files, args.timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
