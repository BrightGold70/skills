"""Exhaustive search behind the design's `13,104 (text, pair) cases` and `194` figures.

Subject: doc-block-exec, §Detailed Design > Substitution. The design claims, over the
alphabet {a, b}, all texts of length 2..7 and all non-substring key pairs of length 2 and 3,
that neither span scan ever missed a case where a key occurs and fires zero times, and that
the lookahead form refuses 194 cases the bare form does not. This file IS that search; the
design cites it by this committed path and publishes the output below.

Every figure the design states is printed here and none is hardcoded: the corpus sizes, the
pair split and both refusal sets are derived in this file and printed on the CASES line, so a
reader who re-runs it re-derives the design's numbers rather than reading them back.

Run: python3 docs/03-analysis/probes/doc-block-exec/substitution_independence_search.2026-09-06.51a2b6f7.py
Measured 2026-09-06 on python 3.11.8 (the supported interpreter) at repo sha 0021c77;
the search reads no file and no tree, so its output is a property of the interpreter alone.
"""

import itertools
import re
import sys

ALPHABET = "ab"
TEXT_LENGTHS = range(2, 8)  # length 2 through 7 inclusive
KEY_LENGTHS = (2, 3)


def texts():
    for n in TEXT_LENGTHS:
        for t in itertools.product(ALPHABET, repeat=n):
            yield "".join(t)


def keys():
    for n in KEY_LENGTHS:
        for k in itertools.product(ALPHABET, repeat=n):
            yield "".join(k)


def scan(text, subs, lookahead):
    """The design's span scan, both enumerations, on the ORIGINAL text.

    lookahead=True  -- OVERLAPPING occurrences: one zero-width hit per starting position.
    lookahead=False -- the narrower form this section prescribed before v1.110.
    Returns the sorted (offset, a, b) triples the refusal would render, one per key pair,
    carrying the SMALLEST index the pair shares anywhere in the text.
    """
    if lookahead:
        spans = [(m.start(), m.start() + len(k), k)
                 for k in subs for m in re.finditer(r"(?=" + re.escape(k) + r")", text)]
    else:
        spans = [(m.start(), m.end(), k)
                 for k in subs for m in re.finditer(re.escape(k), text)]
    first = {}
    for a in spans:
        for b in spans:
            if a[2] < b[2] and a[0] < b[1] and b[0] < a[1]:
                p, o = (a[2], b[2]), max(a[0], b[0])
                first[p] = min(first.get(p, o), o)
    return sorted((o, p[0], p[1]) for p, o in first.items())


def fires(text, subs):
    """Run the real single-pass replacement and record how many times each key fired."""
    counted = {k: 0 for k in subs}
    re.sub("|".join(map(re.escape, subs)),
           lambda m: (counted.__setitem__(m.group(0), counted[m.group(0)] + 1),
                      subs[m.group(0)])[1],
           text)
    return counted


def main():
    all_keys = sorted(keys())
    all_pairs = list(itertools.combinations(all_keys, 2))
    substring_pairs = [(a, b) for a, b in all_pairs if a in b or b in a]
    pairs = [(a, b) for a, b in all_pairs if (a, b) not in set(substring_pairs)]
    corpus = list(texts())

    cases = 0
    lookahead_only = 0
    bare_only = 0
    missed_by_lookahead = 0   # a key occurs, fires zero times, and the scan does not refuse
    missed_by_bare = 0
    witness_lookahead = witness_bare = None

    for text in corpus:
        for a, b in pairs:
            subs = {a: "X", b: "Y"}
            cases += 1
            look = bool(scan(text, subs, True))
            bare = bool(scan(text, subs, False))
            if look and not bare:
                lookahead_only += 1
            if bare and not look:
                bare_only += 1
            counted = fires(text, subs)
            silent = any(k in text and counted[k] == 0 for k in subs)
            if silent and not look:
                missed_by_lookahead += 1
                witness_lookahead = witness_lookahead or (text, a, b)
            if silent and not bare:
                missed_by_bare += 1
                witness_bare = witness_bare or (text, a, b)

    print("python %s" % sys.version.split()[0])
    print("CORPUS texts=%d (lengths %d..%d over {%s}) keys=%d pairs=%d "
          "substring_pairs=%d non_substring_pairs=%d"
          % (len(corpus), min(TEXT_LENGTHS), max(TEXT_LENGTHS), ",".join(ALPHABET),
             len(all_keys), len(all_pairs), len(substring_pairs), len(pairs)))
    print("CASES cases=%d lookahead_only=%d bare_only=%d "
          "missed_by_lookahead=%d missed_by_bare=%d"
          % (cases, lookahead_only, bare_only, missed_by_lookahead, missed_by_bare))
    print("WITNESS missed_by_lookahead=%r missed_by_bare=%r"
          % (witness_lookahead, witness_bare))
    # The two fixtures the design names, run inside the same search so the corpus and the
    # canonical examples cannot drift apart.
    for text, subs in (("abc", {"ab": "X", "bc": "Y"}), ("aaab", {"aa": "X", "ab": "Y"})):
        print("FIXTURE %-6r bare=%s lookahead=%s"
              % (text, scan(text, subs, False), scan(text, subs, True)))


if __name__ == "__main__":
    main()
