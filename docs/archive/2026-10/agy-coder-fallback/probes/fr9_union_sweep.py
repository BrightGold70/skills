#!/usr/bin/env python3
"""AC-9.1: measure the line/joined union and bind each hit to a hand reading.

Working directory: repository root.
Invocation: python3 docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py
Control: python3 docs/03-analysis/probes/agy-coder-fallback/fr9_union_sweep.py --control
Use --root PATH to measure another tracked working tree. No files are changed.

Every tracked h-mad/ file gets the case-insensitive physical-line grep. Python
files also get each ast str constant (adjacent literals joined by ast) and each
tokenize COMMENT, with whitespace collapsed. Other files get their entire text
with whitespace collapsed, as the plan prescribes. All hits remain in the union,
including historical fixtures and deliberate mutation payloads. Parse/tokenize
failures are printed and counted by file, never silently skipped.

REVIEWED records hand readings at 3236ade63000759101b8d5de7e4bdc1558329b73.
The digests bind those readings to the bytes actually inspected: a changed,
additional or missing hit needs a fresh hand reading and fails this gate. They
are not expected census counts or a substitute for reading new content. The
control invalidates one review digest, exercising the normal FAIL path.
The sweep cannot identify prose assembled through runtime interpolation.
PASS and FAIL exit 0; unreadable input or failed git discovery exits 2.
"""

import argparse
import ast
import hashlib
import io
import os
import re
import subprocess
import sys
import tokenize
import warnings
from pathlib import Path


PATTERN = re.compile(
    r"missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError",
    re.IGNORECASE,
)
REVIEWED = {
    "h-mad/SKILL.md": (
        "f8413f73eb7d155d1b6a49bfa36ff446fbae1c63cf3424b7bc1ee139bf36308f",
        "RULE WITH CARVE-OUT: line 500 includes caller-created, callee-resolves, "
        "name-both and call-only wire-cut conditions.",
    ),
    "h-mad/references/codex-implementer-prompt.md": (
        "98cbbab1bb1e9b6fef835ec7f0d1e8d75f781bf883720c8904609d7c8711ae49",
        "RULE WITH CARVE-OUT: all three copies, lines 60, 68 and 72, carry "
        "the full three-sentence block individually.",
    ),
    "h-mad/references/failure-recovery.md": (
        "e08033f2e9ac2aa233486e740d889cdf1b27085f0764b37b10e1f2c9904030fe",
        "RULE WITH CARVE-OUT: the line 36 remedy contains the full block.",
    ),
    "h-mad/scripts/h_mad_assemble_tdd.py": (
        "ecb14c4aa31e42254c886869902b625f3b027daaecc6c08a5bd3e7068a798468",
        "RULE WITH CARVE-OUT: the joined wiring header at lines 477-483 "
        "contains the full block after its general prohibition.",
    ),
    "h-mad/tests/fixtures/codex-text-8-exec.log": (
        "cc0843bf8790c04f83c5fd4a0f06247f165b92abbb733873954200ac7252055b",
        "NO GENERAL RULE: line 974 describes one existing-caller recorder "
        "test's len(calls) assertion in captured output, not universal RED policy.",
    ),
    "h-mad/tests/mutation-specs/new_caller_carveout_copies.json": (
        "de2c68a37ae31c71117e5c54535989cb0a704062b60ace56d206a69d13848b3b",
        "MUTATION DATA: find/replace pairs deliberately damage individual "
        "carve-out sentences; these are negative controls, not operative rules.",
    ),
    "h-mad/tests/test_h_mad_agent_definitions.py": (
        "86b40df7c613ec0b7d80267e581f884ec74b50e4df30347801cbb90854c9b8f8",
        "NO BLANKET RULE: line 77 pins new-symbol import-shaped RED wording; "
        "it does not forbid the new-caller carve-out.",
    ),
    "h-mad/tests/test_h_mad_new_caller_carveout_copies.py": (
        "61f337263e106b5451506642ec76f3ea78267faf3c48725288d725a32ee3e66d",
        "RULE WITH CARVE-OUT: CANONICAL at lines 16-21 contains the full block; "
        "the six locators require each individual copy.",
    ),
    "h-mad/tests/test_h_mad_wire_pin_gate.py": (
        "c475e310a0802e46b390f5bacf62d8b6f3a985987c19a2baf135ceb0873a5112",
        "NO GENERAL RULE: lines 576-582 explain scaffolding for an existing "
        "caller's registration assertion; they prescribe no universal halt.",
    ),
    "h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py": (
        "a093daa2d47684990ca0a3911010baa877c7f279161153ee1b68825916785837",
        "RULE WITH CARVE-OUT: new_rule at lines 56-62 requires caller AND "
        "callee resolution; old_rule is explicitly Before FR-9 for comparison. "
        "Other hits are case keys, exception recognition and assertions.",
    ),
}


def collapse(text):
    return " ".join(text.split())


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=True,
    ).stdout


def readings(name, raw):
    """Return independent line/joined hits and all Python parse failures."""
    text = raw.decode("utf-8", errors="replace")
    hits = [("line", number, number, line)
            for number, line in enumerate(text.splitlines(), 1)
            if PATTERN.search(line)]
    errors = []
    if not name.endswith(".py"):
        if PATTERN.search(collapse(text)):
            hits.append(("text", 1, len(text.splitlines()),
                         "whitespace-collapsed whole-file text matches"))
        return hits, errors

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            encoding = tokenize.detect_encoding(io.BytesIO(raw).readline)[0]
            tree = ast.parse(raw.decode(encoding), filename=name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value = collapse(node.value)
                    if PATTERN.search(value):
                        hits.append(("string", node.lineno, node.end_lineno, value))
        except (SyntaxError, UnicodeError, LookupError, ValueError) as exc:
            errors.append(f"ast: {type(exc).__name__}: {exc}")
        try:
            for token in tokenize.tokenize(io.BytesIO(raw).readline):
                if token.type == tokenize.COMMENT:
                    value = collapse(token.string)
                    if PATTERN.search(value):
                        hits.append(("comment", token.start[0], token.end[0], value))
        except (SyntaxError, UnicodeError, LookupError, tokenize.TokenError) as exc:
            errors.append(f"tokenize: {type(exc).__name__}: {exc}")
    return sorted(hits, key=lambda hit: (hit[1], hit[0], hit[2], hit[3])), errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--control", action="store_true")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        head = git(root, "rev-parse", "HEAD").decode().strip()
        paths = [os.fsdecode(path) for path in
                 git(root, "ls-files", "-z", "--", "h-mad/").split(b"\0") if path]
        union, unparsed, digests = {}, {}, {}
        for name in paths:
            raw = (root / name).read_bytes()
            hits, errors = readings(name, raw)
            if hits:
                union[name] = hits
                digests[name] = hashlib.sha256(raw).hexdigest()
            if errors:
                unparsed[name] = errors
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"probe cannot run: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"HEAD: {head}")
    print(f"ROOT: {root}")
    print(f"REGEX: {PATTERN.pattern} (case-insensitive)")
    print(f"TRACKED: files={len(paths)} python={sum(p.endswith('.py') for p in paths)}")
    sets = {kind: {name for name, hits in union.items()
                   if any(hit[0] == kind for hit in hits)}
            for kind in ("line", "string", "comment", "text")}
    joined = sets["string"] | sets["comment"] | sets["text"]
    print(f"READING: line={len(sets['line'])} strings={len(sets['string'])} "
          f"comments={len(sets['comment'])} text={len(sets['text'])} "
          f"joined={len(joined)} union={len(union)} unparsed={len(unparsed)}")
    print(f"LINE-MINUS-JOINED: {sorted(sets['line'] - joined)!r}")
    print(f"JOINED-MINUS-LINE: {sorted(joined - sets['line'])!r}")
    reviewed = dict(REVIEWED)
    if args.control:
        name = "h-mad/SKILL.md"
        reviewed[name] = ("0" * 64, reviewed[name][1])
        print(f"CONTROL: invalidated hand-review digest for {name}")
    ok = not unparsed
    for name, hits in sorted(union.items()):
        print(f"UNION: {name}")
        for kind, start, end, value in hits:
            print(f"HIT[{kind}]: {name}:{start}-{end}: {value}")
        expected, reading = reviewed.get(name, (None, "UNREVIEWED: read by hand"))
        same = digests[name] == expected
        ok &= same
        print(f"REVIEW: {'OK' if same else 'NEEDS_HAND_READING'} "
              f"sha256={digests[name]} :: {reading}")
    for name in sorted(reviewed.keys() - union.keys()):
        ok = False
        print(f"REVIEW: MISSING_PREVIOUS_HIT {name}; repeat hand reading")
    for name, errors in sorted(unparsed.items()):
        for error in errors:
            print(f"UNPARSED: {name}: {error}")
    print("PROBE: " + ("PASS" if ok else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
