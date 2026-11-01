#!/usr/bin/env python3
"""Did a re-anchored mutation row keep its edit delta? Advisory, read-only.

Usage: h_mad_reanchor_diff.py --base <ref> <spec.json> [more...]

A row can stay ANCHORS_OK and ALL_CAUGHT while its mutant no longer breaks what
it used to (skill-candidates row 2816: codex rewrote
`emit-the-guards-only-for-wiring` that way on 2026-10-25). Rule, per the user's
ruling 2026-11-01: tokenize `find` and `replace` ignoring whitespace, diff them,
and compare with the same-named row at `--base`: the tokens added must match,
and one set of removed tokens must contain the other (`same_delta`). Widening
`find` for uniqueness keeps the delta; changing what the mutant breaks does not.

Prints `  reanchor-changed:` / `  reanchor-unjudged:` detail lines, then
`REANCHOR: SAME|CHANGED|UNJUDGED rows=N reanchored=R changed=C unjudged=U`.
A row with no same-named row at base, a spec absent at base and an unreadable
spec are UNJUDGED, never SAME. Exit 0 on every verdict; 2 on bad arguments.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def edit_delta(find: str, replace: str) -> tuple[Counter, Counter]:
    """(tokens removed, tokens added) going from `find` to `replace`."""
    old, new = _TOKEN_RE.findall(find), _TOKEN_RE.findall(replace)
    removed, added = Counter(), Counter()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag != "equal":
            removed.update(old[i1:i2])
            added.update(new[j1:j2])
    return removed, added


def same_delta(was: tuple[Counter, Counter], now: tuple[Counter, Counter]) -> bool:
    """Same tokens added, and one removed set contains the other.

    Not exact equality: a mutant that replaces a whole statement removes every
    token of it, so when the statement legitimately grows the removed set grows
    with it (calibration: `empty-argv-returns-clean`, a9e9a123). Exact equality
    flagged 7 of 10 real re-anchors; this flags the 2 from the known-bad
    2026-10-25 rewrite (user ruling 2026-11-01).
    """
    (was_removed, was_added), (now_removed, now_added) = was, now
    nested = not (was_removed - now_removed) or not (now_removed - was_removed)
    return was_added == now_added and nested


def _rows(text: str) -> dict[str, dict]:
    data = json.loads(text)
    rows = data.get("mutations") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError("no mutations list")
    return {row["name"]: row for row in rows if isinstance(row, dict) and isinstance(row.get("name"), str)}


def _base_text(spec: Path, base: str) -> str | None:
    top = subprocess.run(["git", "-C", str(spec.parent), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if top.returncode != 0:
        return None
    relative = spec.resolve().relative_to(Path(top.stdout.strip()).resolve()).as_posix()
    shown = subprocess.run(["git", "-C", top.stdout.strip(), "show", f"{base}:{relative}"],
                           capture_output=True, text=True)
    return shown.stdout if shown.returncode == 0 else None


def _shown(counter: Counter) -> str:
    return " ".join(sorted(counter.elements())) or "∅"


def judge(spec_arg: str, base: str) -> tuple[int, int, list[str], list[str]]:
    """(rows, reanchored, changed lines, unjudged lines) for one spec."""
    spec = Path(spec_arg)
    try:
        current = _rows(spec.read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError) as exc:
        return 0, 0, [], [f"{spec_arg} (unreadable: {type(exc).__name__})"]
    old_text = _base_text(spec, base)
    try:
        old = _rows(old_text) if old_text is not None else None
    except (ValueError, KeyError):
        old = None
    reanchored, changed, unjudged = 0, [], []
    for name, row in current.items():
        if old is None or name not in old:
            unjudged.append(f"{spec_arg} :: {name} (no row of that name at {base})")
            continue
        before = old[name]
        if (before.get("find"), before.get("replace")) == (row.get("find"), row.get("replace")):
            continue
        reanchored += 1
        was = edit_delta(str(before.get("find", "")), str(before.get("replace", "")))
        now = edit_delta(str(row.get("find", "")), str(row.get("replace", "")))
        if not same_delta(was, now):
            changed.append(f"{spec_arg} :: {name} now -[{_shown(now[0])}] +[{_shown(now[1])}], "
                           f"was -[{_shown(was[0])}] +[{_shown(was[1])}]")
    return len(current), reanchored, changed, unjudged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--base", required=True, help="git ref holding the rows before re-anchoring")
    parser.add_argument("specs", nargs="+")
    args = parser.parse_args(argv)
    rows = reanchored = 0
    changed: list[str] = []
    unjudged: list[str] = []
    for spec in args.specs:
        n, r, c, u = judge(spec, args.base)
        rows, reanchored = rows + n, reanchored + r
        changed, unjudged = changed + c, unjudged + u
    for line in changed:
        print(f"  reanchor-changed: {line}")
    for line in unjudged:
        print(f"  reanchor-unjudged: {line}")
    verdict = "CHANGED" if changed else "UNJUDGED" if unjudged else "SAME"
    print(f"REANCHOR: {verdict} rows={rows} reanchored={reanchored} "
          f"changed={len(changed)} unjudged={len(unjudged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
