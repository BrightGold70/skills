#!/usr/bin/env python3
"""Apply omc-codex-mcp-no-type to every installed OMC copy. Idempotent.

Exit 0: every target patched (or already patched). Exit 2: a target is missing,
or its emission line does not match exactly once. Nothing is written in that
case for that file, and the reason is printed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from targets import MARKER, ORIGINAL, targets  # noqa: E402


def main() -> int:
    paths = targets()
    if not paths:
        print("APPLY: UNREADABLE no installed OMC copy found")
        return 2
    rc = 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"APPLY: SKIP {path} unreadable ({exc})")
            rc = 2
            continue
        hits = ORIGINAL.findall(text)
        if not hits and MARKER in text:
            print(f"APPLY: ALREADY {path}")
            continue
        if len(hits) != 1:
            print(f"APPLY: REFUSED {path} emission line matched {len(hits)} times (want 1)")
            rc = 2
            continue
        backup = path.with_name(path.name + ".pre-omc-codex-mcp-no-type")
        if not backup.exists():
            backup.write_text(text, encoding="utf-8")
        path.write_text(ORIGINAL.sub(MARKER, text, count=1), encoding="utf-8")
        print(f"APPLY: PATCHED {path} (backup {backup.name})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
