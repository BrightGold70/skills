#!/usr/bin/env python3
"""Name the tests that PARSE a document you are about to commit.

A doc-derived test lives next to the CONSUMER of a document, never next to the
document, so editing `h-mad/SKILL.md` gives no hint that
`h-mad/tests/test_h_mad_context_budget_docs.py` parses one of its sections. Twice
a commit was pushed on a green targeted slice and was red in the full suite on a
guard in a third file (skill-candidates row "name the tests that PARSE a
document you are about to edit").

Usage:
  h_mad_doc_consumers.py [--repo DIR] [--staged] [PATH ...]

Prints, per document, `CONSUMERS: <doc> n=<K>` followed by the test files, then
one `RUN: python3 -m pytest -q <files>` line covering them all (omitted when
there are none). Exit 0 always: this NAMES tests, it decides nothing.

A test counts as a consumer when its source contains the document's basename
AND either lives in the same top-level directory as the document or also names
that directory. Over-reporting is the safe direction here: an extra file in the
RUN line costs seconds, a missing one is the defect this exists for. `.py`
files and test files themselves are not documents and are skipped.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("paths", nargs="*", help="repo-relative documents")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--staged", action="store_true",
                    help="use the documents staged for commit")
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
        return 0

    union: list[str] = []
    for doc in docs:
        hits = consumers(repo, doc, tests)
        print(f"CONSUMERS: {doc} n={len(hits)}")
        for rel in hits:
            print(f"  {rel}")
            if rel not in union:
                union.append(rel)
    if union:
        print("RUN: python3 -m pytest -q " + " ".join(sorted(union)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
