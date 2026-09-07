#!/usr/bin/env python3
"""H5 — is one shared sentence adopted VERBATIM by every sibling document?

The failure this closes is invisible to every audit leg by construction. Measured on
`#18 gateway-consolidation`: two authors independently corrected one shared fact in the
same cycle, one to **18** and one to **20**. Each document was internally consistent,
so a reviewer reading any single document found nothing, and a reviewer reading both
had no reason to diff one sentence out of thousands. Three of the last five cycles'
must-fixes there were propagation gaps of this shape.

The existing remedy is `doc-auditor` rule 7 — a cross-document reading by a reviewer,
in the NEXT cycle, after the divergence is committed. This runs before the commit and
answers mechanically: which siblings quote the design's sentence, and which do not.

**Whitespace normalisation is the whole difficulty, and getting it wrong in either
direction is fatal.** Documents hard-wrap at different columns, so one sentence is a
different byte string in each file; this repo has a measured case of a hard wrap hiding
a retired count from every single-line grep for 92 cycles. A byte comparison therefore
reports DIVERGED on documents that adopted the sentence perfectly — the calibration
error that gets a gate switched off (`docs/learnings.md`: detectors written as hard
fired 104/49/48 times on artifacts that had already passed). So both sides are
collapsed to single-spaced text before comparison. What is NOT normalised is the
sentence's own words: this is an adoption check, not a similarity score, and h-mad has
already refused fuzzy matching once by measurement (`h_mad_audit_gate.py`, where token
overlap scored the negative control ABOVE both true pairs).

Stdlib only, like every other h-mad script.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_WS = re.compile(r"\s+")
# Leading list/quote furniture, so a sentence quoted as a bullet still counts. Only
# the LEADING run is stripped and only these characters: anything more and the check
# starts silently accepting text that is not the sentence.
_FURNITURE = re.compile(r"^[\s>*\-+#|]*")


def normalize(text: str) -> str:
    """Collapse every whitespace run to one space, and strip the ends.

    A hard wrap, an indent and a bullet all change the bytes without changing the
    sentence. Newlines are collapsed FIRST — a per-line scan is the instrument that
    fails permissively here, returning a smaller number that reads as clean.
    """
    return _WS.sub(" ", text).strip()


def _needle(sentence: str) -> str:
    return normalize(_FURNITURE.sub("", sentence))


def check(sentence: str, docs: list[Path]) -> dict:
    """Which of `docs` quote `sentence` verbatim, modulo whitespace?

    An unreadable document is UNREADABLE, never "did not adopt": the two have
    opposite remedies, and reporting a missing file as a divergence sends someone
    to edit a document that is not there.
    """
    needle = _needle(sentence)
    if not needle:
        return {"verdict": "UNREADABLE", "reason": "empty_sentence"}
    if len(docs) < 2:
        return {"verdict": "UNREADABLE", "reason": f"not_two_docs:{len(docs)}"}

    adopted: list[str] = []
    missing: list[str] = []
    for path in docs:
        try:
            body = normalize(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            return {"verdict": "UNREADABLE",
                    "reason": f"doc:{exc.__class__.__name__.lower()}:{path.name}"}
        (adopted if needle in body else missing).append(str(path))

    if missing:
        return {"verdict": "DIVERGED", "adopted": adopted, "missing": missing}
    return {"verdict": "ADOPTED", "adopted": adopted, "missing": []}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Is one shared sentence adopted verbatim by every sibling document?"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sentence", help="the canonical sentence, inline")
    source.add_argument(
        "--sentence-file", type=Path,
        help="read the canonical sentence from a file — the design owns it, and "
             "retyping it into the command line is how it drifts",
    )
    parser.add_argument(
        "--doc", action="append", default=[], type=Path, metavar="PATH", required=True,
        help="a sibling document that should quote the sentence. Repeatable; at "
             "least two, because adoption is a relation between siblings",
    )
    args = parser.parse_args(argv)

    if args.sentence_file is not None:
        try:
            sentence = args.sentence_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            print("ADOPTION: UNREADABLE reason=sentence_file")
            return 2
    else:
        sentence = args.sentence

    result = check(sentence, args.doc)
    verdict = result["verdict"]

    if verdict == "UNREADABLE":
        print(f"ADOPTION: UNREADABLE reason={result['reason']}")
        print("  a document that could not be read has not been shown to diverge — "
              "the two have opposite remedies, so this is a cannot-judge.")
        return 2

    print(f"ADOPTION: {verdict} docs={len(args.doc)} "
          f"adopted={len(result['adopted'])} missing={len(result['missing'])}")
    for path in result["missing"]:
        print(f"  missing: {path}")
    if verdict == "DIVERGED":
        print("  each of those documents is internally consistent, which is why no "
              "single-document reviewer can see this — fix the sentence at its source "
              "and re-run before committing the cycle (#11/H5).")
    print(f"[H-MAD] adoption {verdict}")
    # A verdict exits 0, like every other h-mad gate: DIVERGED is an answer, not an
    # operational failure, and callers read the token rather than `$?`.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
