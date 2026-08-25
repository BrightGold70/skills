#!/usr/bin/env python3
"""Post-edit identifier sweep: what still names the thing you just removed?

After the LAST edit of a rename or removal, re-grep the old identifier across
every surface — code, comments, docs prose, tests, mutation-spec anchors — and
require each remaining hit to be a deliberate explanation rather than a
leftover.

The timing is the whole property. `a311385` renamed `hooks/h-mad-advisor-gate.sh`
to `-warn.sh` and shipped three stale references to a file the same commit
deletes. The sweep had been started by hand mid-work: two context-budget
docstrings were noticed, the docs pins and the mutation spec were visited, and
then more edits followed and nobody came back. Run once at the end, it costs a
second; run during, it is unreliable in exactly the way that produced the
defect.

What this does NOT do is decide whether a hit is explanation or leftover. That
judgement stays with the reader, which is why the allowlist is an input and is
never inferred: a tool that guessed would eventually delete correct prose, and
the reader would stop reading its output.

Stdlib only, like every other h-mad script — the bare-`python3` callers have no
site-packages.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Nothing here is a reference a human can fix, and each one is large enough to
# dominate the report if it were searched.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache",
             ".pytest_cache", ".ruff_cache", "dist", "build", ".h-mad",
             # Append-only tool state: machine logs nobody edits by hand. On the
             # first live run these were 14 of 26 hits and outnumbered the four
             # a reader would act on.
             ".bkit", ".omc"}

# Records that are historical BY DEFINITION — a handoff is a snapshot of a past
# session, and READ mode forbids rewriting one. Their hits are counted, never
# listed as leftovers, unless the caller asks for them.
HISTORY_PREFIXES = (("docs", "handoffs"), ("docs", "archive"))

COMMENT_PREFIXES = ("#", "//", "*", "<!--")

EXCERPT = 160


def classify_surface(rel_path: str, line: str) -> str:
    """Which surface a hit is on. The row lists these because they are missed unevenly.

    Mutation-spec anchors come first: a drifted anchor mutates nothing, so its
    spec REFUSES rather than failing, and that is the surface a hand sweep skips
    most often.
    """
    parts = Path(rel_path).parts
    name = Path(rel_path).name
    if "mutation-specs" in parts:
        return "mutation-anchor"
    if name.startswith("test_") or name.endswith("_test.py") or "tests" in parts:
        return "test"
    if name.endswith((".md", ".markdown", ".rst", ".txt")):
        return "doc"
    if line.strip().startswith(COMMENT_PREFIXES):
        return "comment"
    return "code"


def _files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _is_history(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    return any(parts[: len(prefix)] == prefix for prefix in HISTORY_PREFIXES)


def _excerpt(line: str, needle: str) -> str:
    """One line of context CENTRED on the match, not truncated from the left.

    Measured: a 900-character JSON log line truncated at 160 from the start
    printed an excerpt that did not contain the identifier at all — the one
    thing an excerpt owes its reader.
    """
    stripped = line.strip()
    if len(stripped) <= EXCERPT:
        return stripped
    at = stripped.find(needle)
    if at < 0:
        return stripped[:EXCERPT] + "…"
    start = max(0, at - EXCERPT // 2)
    end = min(len(stripped), start + EXCERPT)
    return ("…" if start else "") + stripped[start:end] + ("…" if end < len(stripped) else "")


def _stem_of(identifier: str) -> str:
    """`advisor-gate.sh` -> `advisor-gate`. Empty when there is no extension.

    Prose that names the concept after the file is gone is a real signal and a
    real source of noise, so it is reported in its own class rather than folded
    into the verdict either way.
    """
    suffix = Path(identifier).suffix
    return identifier[: -len(suffix)] if suffix and len(suffix) < len(identifier) else ""


def sweep(
    root: Path,
    identifiers: list[str],
    allow: list[str],
    include_history: bool = False,
) -> dict:
    """Grep `identifiers` under `root`, split into leftover / allowed / related / history.

    `allow` holds root-relative paths whose hits are deliberate explanations.
    They are still reported — dropping them silently would turn the allowlist
    into a place real leftovers could hide, and a silent skip is
    indistinguishable from an empty tree.
    """
    root = Path(root)
    allowed_paths = {str(Path(a)) for a in allow}
    stems = {i: _stem_of(i) for i in identifiers}

    result = {
        "root": str(root),
        "identifiers": list(identifiers),
        "leftover": [],
        "allowed": [],
        "related": [],
        "history": [],
    }

    for path in _files(root):
        rel = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # A binary blob is not a reference anyone edits; skipping it beats
            # aborting a sweep whose other findings are real.
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for identifier in identifiers:
                hit = {
                    "identifier": identifier,
                    "path": rel,
                    "line": lineno,
                    "text": _excerpt(line, identifier),
                    "surface": classify_surface(rel, line),
                }
                if identifier in line:
                    if rel in allowed_paths:
                        result["allowed"].append(hit)
                    elif _is_history(rel) and not include_history:
                        result["history"].append(hit)
                    else:
                        result["leftover"].append(hit)
                elif stems[identifier] and stems[identifier] in line:
                    result["related"].append(hit)

    # Only `leftover` moves the verdict. `related` is prose naming the concept
    # rather than the file, and calling that a finding would flood the report
    # the sweep exists to keep readable.
    result["verdict"] = "LEFTOVERS" if result["leftover"] else "CLEAN"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-grep a removed identifier across every surface, after the last edit"
    )
    parser.add_argument("identifier", nargs="+", help="the old name(s) that were removed or renamed")
    parser.add_argument("--root", type=Path, default=Path("."), help="tree to sweep (default: cwd)")
    parser.add_argument(
        "--allow", action="append", default=[], metavar="PATH",
        help="root-relative path whose hits explain the old name on purpose; repeatable",
    )
    parser.add_argument(
        "--include-history", action="store_true",
        help="treat docs/handoffs and docs/archive hits as leftovers too "
             "(they are counted, never listed, by default)",
    )
    args = parser.parse_args(argv)

    empty = [i for i in args.identifier if not i.strip()]
    if empty:
        # An empty needle is in every line of every file. A sweep that reports
        # everything is exactly as useful as one that reports nothing, and looks
        # far more thorough.
        parser.error("identifier must not be empty")

    if not args.root.is_dir():
        print(f"ERROR: not a directory: {args.root}", file=sys.stderr)
        print("SWEEP: UNREADABLE")
        print(
            "  nothing was searched, so this is a cannot-judge and not a clean "
            "sweep (halt `identifier_sweep:root_unreadable`)."
        )
        print("[H-MAD] identifier-sweep UNREADABLE")
        return 2

    result = sweep(args.root, args.identifier, args.allow, args.include_history)
    verdict = result["verdict"]

    print(
        f"SWEEP: {verdict} identifiers={len(result['identifiers'])} "
        f"leftover={len(result['leftover'])} allowed={len(result['allowed'])} "
        f"related={len(result['related'])} history={len(result['history'])}"
    )
    for hit in result["leftover"]:
        print(f"  leftover: {hit['path']}:{hit['line']} [{hit['surface']}] {hit['text']}")
    for hit in result["allowed"]:
        print(f"  allowed:  {hit['path']}:{hit['line']} [{hit['surface']}] {hit['text']}")
    for hit in result["related"]:
        print(f"  related:  {hit['path']}:{hit['line']} [{hit['surface']}] {hit['text']}")
    if result["history"]:
        # Counted, not listed. A handoff is a record of a session that already
        # happened; rewriting one to match today is how a snapshot stops being
        # evidence. `--include-history` lists them when that is what you want.
        paths = sorted({h["path"] for h in result["history"]})
        print(
            f"  history:  {len(result['history'])} hit(s) in "
            f"{len(paths)} historical record(s) — not listed; "
            f"re-run with --include-history to see them"
        )

    if verdict == "LEFTOVERS":
        print(
            "  each leftover still names the old thing. Whether that is an "
            "explanation or a stale reference is YOUR call — pass the deliberate "
            "ones with --allow rather than editing them away."
        )
    print(f"[H-MAD] identifier-sweep {verdict}")
    return 0 if verdict == "CLEAN" else 2


if __name__ == "__main__":
    sys.exit(main())
