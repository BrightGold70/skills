#!/usr/bin/env python3
"""Pre-dispatch precheck for an H-MAD phase document (#20).

Refute the premises a `grep` can refute BEFORE the audit prompt is assembled.
A share of every first audit cycle's findings are claims about the tree that were
already false when the document was written, and each one costs a full dual-surface
cycle — two dispatches, ~4 minutes wall — to discover and a second to fix.

Verdict token, never `$?`::

    PRECHECK: PASS issues=0
    PRECHECK: FAIL issues=7
    PRECHECK: UNREADABLE reason=<r>

`PASS`/`FAIL` are measured outcomes and exit 0. Only an operational error — the
document cannot be read, the phase is not one this tool knows — exits 2. That is
the same signal discipline `h_mad_audit_gate.py` and `h_mad_install_check.py` use,
and it exists because a non-zero exit registers as a `PostToolUseFailure` and leaks
into coexisting plugins.

**It reports; it does not fix.** Every detail line names one hit and the reader
decides. Deliberate hits are passed back with `--allow`, which is an INPUT and is
never inferred — the same rule `h_mad_identifier_sweep.py` states, for the same
reason: a checker that learns to forgive its own false positives stops measuring.

Detectors, and the measured class each closes:

``PATH:``        **advisory only.** A cited repo file that does not exist. Filed as a
                 hard finding this produced 104 hits on a design document that had
                 passed 83 audit cycles — every one a file the document's own
                 component table marks ``| new |``. A planning document's job
                 includes naming files the feature will create, so absence is the
                 normal case and only a reader can tell it from a stale citation.
``SYMBOL:``      **advisory only.** ``path:name`` where the file exists but defines
                 no such name — which a planning document does legitimately, for a
                 symbol the feature will add.

**What is HARD is only what is provably wrong**: an unfilled slot, a pin past
end-of-file, a pin into a file that has changed since the document's own provenance
commit, and a provenance sha that names no commit here. Everything else is triage
output. That split was not chosen, it was MEASURED — every detector filed as hard on
first cut fired dozens of times on documents that had passed 74 and 83 audit cycles,
and a gate that fails a clean document is not a gate.
``PLACEHOLDER:`` ``TBD``/``TODO``/``FIXME`` anywhere. The slot forms — ``key=…`` and
                 a bare ``<name>`` — are scored on the **impl-plan only**, which is
                 where the author contract puts them and where an unfilled value is a
                 defect: an unresolved ``timeout=…`` is a finding, an explicit
                 ``timeout=60.0`` is a contract. A design or plan uses exactly that
                 notation to DECLARE a grammar (``leftover: "<path>"``,
                 ``DOCBLOCK: <VERDICT>``), so scored there it produced 48 hits on a
                 design document that had passed 83 cycles and every one was a
                 declaration.
``LINEPIN:``     a line number written into a document. For ``design`` and ``plan``
                 this is a hard finding outright — both author contracts say never
                 write one, because they go stale silently (measured three times in
                 one session on one file: ``:1804`` → ``:1887`` → ``:1897``). For
                 ``impl-plan``, where pins are permitted, only a pin past end-of-file
                 is hard.
``UNKNOWNSHA:``  a provenance commit that names no commit in this repository —
                 mistyped, or carried in from another checkout. Hard: it cannot
                 have been measured at.
``STALESHA:``    **advisory only.** A provenance commit that is behind ``HEAD``.
                 Filed as hard this fires on every correctly-provenanced measurement
                 in the tree, since a document is written at one commit and HEAD then
                 moves; only a reader knows whether the measured thing has changed.
``COUNT:``       **advisory only, verdict-neutral.** A stated count beside the length
                 of the nearest list. The heuristic is unproven, and an unproven
                 heuristic never blocks an operator — the rule
                 ``h_mad_wire_registry.py challenge`` already follows.

Acceptance corpus is real, not tidy: ``doc-block-exec.impl-plan.md`` at ``f6345c4``,
the document impl-plan cycle 33 reviewed, whose top must-fix was six stale line pins.
Its control is today's revision, which carries none. See
``h-mad/tests/test_h_mad_precheck_doc.py``.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PHASES = ("plan", "design", "impl-plan", "spec")

#: Phases whose author contract forbids writing a line number at all.
NO_LINE_PINS = ("design", "plan", "spec")

HARD_KINDS = ("PLACEHOLDER", "LINEPIN", "PINDRIFT", "UNKNOWNSHA")

# A backticked span. Every detector reads inside backticks rather than free prose:
# an author states a path, a pin or a slot as code, and free prose is where the
# false positives live.
#
# The ``` run is stripped BEFORE pairing. Prose in these documents routinely says
# "the section holds four ```bash fences, opening at `:1809`, `:1822` …" — and a
# naive pairing consumes the triple as an opening delimiter, which shifts every
# subsequent pair by one and silently drops the real spans. Measured on the c33
# corpus: five of that cycle's six stale line pins live on exactly such a line, and
# a first cut of this detector found ONE of the six while reporting no error.
_TRIPLE = re.compile(r"``+")
_CODE = re.compile(r"`([^`\n]{1,200})`")


def _spans(line: str) -> list[str]:
    return _CODE.findall(_TRIPLE.sub(" ", line))

# `some/path.py`, `docs/x.md`, optionally followed by `:<line>` or `:<symbol>`.
_PATHISH = re.compile(
    r"^(?P<path>[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]{1,6})"
    r"(?::(?P<tail>\d+(?:-\d+)?|[A-Za-z_][A-Za-z0-9_]*))?$"
)

# A bare `:1809` — five of the c33 corpus's six stale pins were written this way,
# attached to a path named earlier in the sentence.
_BARE_PIN = re.compile(r"^:(?P<line>\d{2,6})(?:-\d{2,6})?$")

# TBD/TODO/FIXME are findings anywhere. `…` is a finding only INSIDE a code span:
# in prose it is an ordinary ellipsis, and these documents use it on nearly every
# page. Measured: counted in prose it contributed the bulk of 49 hits on a plan
# that had passed 74 audit cycles.
_PLACEHOLDER = re.compile(r"(?:\bTBD\b|\bTODO\b|\bFIXME\b)")
# `…` counts only as an ASSIGNED VALUE — `timeout=…`, `key: …`. That is the
# unfilled-argument shape the impl-plan corpus actually carried. Elsewhere in a code
# span it is ordinary elision (`from h_mad_doc_block_exec import …`,
# `…::test_a_missing_heading_fails_loudly`), a documentation idiom this tree uses
# throughout; counted as a slot it produced 22 hits on a plan that had passed 74
# audit cycles and every one was elision.
_SLOT_IN_CODE = re.compile(r"[=:]\s*…\s*$|[=:]\s*…[,)\s]")

# `<lowercase-slot>` inside a code span — an unfilled template slot. A documented
# CLI usage line (`--feature <feature>`) is the legitimate form, so a span that
# also carries a flag or a command is exempt.
_ANGLE_SLOT = re.compile(r"<[a-z][a-z0-9_\- ]*>")

# A span carrying `<slot>` is an unfilled slot ONLY when the slot is the whole of
# it. These documents state grammars and usage lines constantly — a pytest node id
# `tests/x.py::<name>`, an output grammar `DOCBLOCK: <VERDICT> (<key>=<bare>|…)`, a
# constructor `LaunchFailed("reap", <the TimeoutExpired>, pgid=<n>)` — and every one
# is a contract, not a hole. Measured: without this exemption the detector produced
# 31 hits on a design document that had passed 83 cycles, and all of them were
# grammar. So a span containing a separator, a call, a flag, a path or an uppercase
# token is exempt.
_GRAMMAR = re.compile(r"(?:::|[|()\[\]{}]|--|/|\.py|\.md|[A-Z]{2,}|\s\w+\s)")

_SHA_CLAIM = re.compile(
    r"(?:verified|measured|re-measured|pinned|base|at HEAD|at commit)\b[^.]{0,120}?"
    r"`(?P<sha>[0-9a-f]{7,40})`",
    re.IGNORECASE | re.DOTALL,
)

_COUNT_CLAIM = re.compile(
    r"\b(?:the\s+)?(?P<n>\d{1,3})\s+(?:[a-z][a-z\-]{2,14}\s+){0,2}(?P<noun>tests|rows|sites|files|names|mutations|"
    r"tasks|verbs|classes|subclasses|fields|slots|cases|surfaces)\b",
    re.IGNORECASE,
)


class Unreadable(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _head_sha(root: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root), capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _changed_since(root: Path, sha: str, rel: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", f"{sha}..HEAD", "--", rel],
            cwd=str(root), capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return False  # cannot check → cannot judge → say nothing
    if r.returncode != 0:
        return False
    return bool(r.stdout.strip())


def _is_commit(root: Path, sha: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "cat-file", "-t", sha],
            cwd=str(root), capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return True  # cannot check → cannot judge → say nothing
    return r.returncode == 0 and r.stdout.strip() == "commit"


def _newest_commit(root: Path, shas: list[str]) -> str | None:
    """The one of `shas` that is nearest HEAD. A document accretes provenance over
    revisions; only the newest bounds what could have drifted since."""
    best, best_n = None, None
    for s in dict.fromkeys(shas):
        try:
            r = subprocess.run(
                ["git", "rev-list", "--count", f"{s}..HEAD"],
                cwd=str(root), capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode != 0:
            continue
        try:
            n = int(r.stdout.strip())
        except ValueError:
            continue
        if best_n is None or n < best_n:
            best, best_n = s, n
    return best


def _line_count(p: Path) -> int | None:
    try:
        with p.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return None


def _defines(p: Path, name: str) -> bool:
    """Does `p` define `name`? Deliberately generous — this must not manufacture
    findings. A def, a class, a module-level binding, a dict key or a CLI flag all
    count, because a document legitimately cites any of them."""
    try:
        text = p.read_text(errors="replace")
    except OSError:
        return True  # cannot read it → cannot judge it → say nothing
    pat = re.compile(
        r"(?:^\s*(?:async\s+)?def\s+%(n)s\b"
        r"|^\s*class\s+%(n)s\b"
        r"|^\s*%(n)s\s*[:=]"
        r"|[\"']%(n)s[\"']"
        r"|--%(n)s\b)" % {"n": re.escape(name)},
        re.MULTILINE,
    )
    return bool(pat.search(text))


def _list_length_after(lines: list[str], idx: int) -> int | None:
    """Length of the first markdown list beginning within 3 lines after `idx`."""
    i = idx + 1
    scanned = 0
    while i < len(lines) and scanned < 3 and not lines[i].strip():
        i += 1
        scanned += 1
    if i >= len(lines) or not re.match(r"^\s*[-*]\s+\S", lines[i]):
        return None
    n = 0
    while i < len(lines) and re.match(r"^\s*[-*]\s+\S", lines[i]):
        n += 1
        i += 1
    return n


def scan(doc: Path, phase: str, root: Path, allow: list[str] | None = None):
    """Return `(findings, advisories, allowed)`.

    `findings` move the verdict; `advisories` never do.
    """
    allow = list(allow or [])
    try:
        text = doc.read_text(errors="replace")
    except OSError as exc:
        raise Unreadable(f"document_unreadable") from exc

    lines = text.splitlines()
    findings: list[tuple[str, int, str]] = []
    advisories: list[tuple[str, int, str]] = []
    allowed: list[str] = []

    def allowed_by(span: str) -> bool:
        return any(a in span for a in allow)

    head = _head_sha(root)

    # The document's own provenance: the newest commit it claims to have measured
    # at. It is what a line pin is checkable AGAINST — without one, drift is not
    # evaluable and every pin is an advisory rather than a finding.
    prov = None
    if head:
        cands = [m.group("sha") for m in _SHA_CLAIM.finditer(text)]
        cands = [c for c in cands if _is_commit(root, c)]
        if cands:
            prov = _newest_commit(root, cands)

    in_fence = False
    for lineno, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence

        # --- placeholders: prose and fences alike -------------------------
        for m in _PLACEHOLDER.finditer(line):
            span = m.group(0)
            if allowed_by(line) or allowed_by(span):
                allowed.append(f"PLACEHOLDER {span} L{lineno}")
                continue
            findings.append(("PLACEHOLDER", lineno, f"{span} — unresolved slot"))

        for span in _spans(line):
            if allowed_by(span):
                allowed.append(f"span `{span}` L{lineno}")
                continue

            if phase == "impl-plan" and _SLOT_IN_CODE.search(span):
                findings.append(("PLACEHOLDER", lineno, f"`{span}` — unresolved slot"))
                continue

            # --- angle slots ---------------------------------------------
            if phase == "impl-plan" and _ANGLE_SLOT.search(span) and not _GRAMMAR.search(span):
                findings.append(("PLACEHOLDER", lineno, f"`{span}` — unfilled slot"))
                continue

            # --- bare `:NNNN` line pins ----------------------------------
            bare = _BARE_PIN.match(span)
            if bare:
                advisories.append(
                    ("LINEPIN", lineno, f"`{span}` — bare line pin, unanchored to any file")
                )
                continue

            m = _PATHISH.match(span)
            if not m:
                continue
            rel = m.group("path")
            tail = m.group("tail")
            target = root / rel

            if not target.exists():
                # ADVISORY, never a finding. A planning document's job includes
                # naming files the feature will CREATE, so "does not exist" is the
                # normal case rather than a defect. Measured: this detector, filed
                # as hard, produced 104 hits on a design document that had passed
                # 83 audit cycles — every one of them a file its own component
                # table marks `| new |`. A gate that fires on a clean document is
                # not a gate.
                advisories.append(("PATH", lineno, f"`{rel}` does not exist yet — new, or stale?"))
                continue

            if tail is None:
                continue

            if tail.isdigit() or "-" in tail:
                first = int(tail.split("-")[0])
                n = _line_count(target)
                if n is not None and first > n:
                    # HARD: provably wrong, no judgement involved.
                    findings.append(
                        ("LINEPIN", lineno, f"`{rel}:{tail}` past_eof — the file has {n} lines")
                    )
                elif prov and _changed_since(root, prov, rel):
                    # HARD: the document pins a line in a file that has been edited
                    # since the commit the document says it measured at. This is the
                    # c33 defect exactly — six SKILL.md pins, stale by 93 lines,
                    # measured at a commit that had moved.
                    findings.append(
                        ("PINDRIFT", lineno,
                         f"`{rel}:{tail}` — `{rel}` changed since the document's provenance `{prov[:7]}`")
                    )
                else:
                    # Cannot judge: no provenance sha to measure drift against.
                    # Reported, never scored — "I could not check" is not "it is fine".
                    advisories.append(
                        ("LINEPIN", lineno, f"`{rel}:{tail}` — line pin with no provenance commit to check it against")
                    )
                continue

            if target.suffix == ".py" and not _defines(target, tail):
                # ADVISORY, for the same reason PATH is: a planning document names
                # symbols the feature will ADD to files that already exist. Measured:
                # today's impl-plan cites `_gate_block` in an existing test module,
                # which Task 5 creates — a correct citation that a hard rule would
                # score as a defect, failing a document that had just passed a
                # gating audit round.
                advisories.append(("SYMBOL", lineno, f"`{rel}` defines no `{tail}` yet — new, or stale?"))

        # --- advisory counts ---------------------------------------------
        if not in_fence:
            for m in _COUNT_CLAIM.finditer(line):
                got = _list_length_after(lines, lineno - 1)
                if got is None or got == int(m.group("n")):
                    continue
                advisories.append(
                    ("COUNT", lineno,
                     f"states {m.group('n')} {m.group('noun')} beside a list of {got} — verify")
                )

    # --- provenance shas, over the WHOLE text -----------------------------
    # Scanned across newlines on purpose: a wrapped paragraph routinely puts the
    # trigger phrase on one line and the sha on the next, and the c33 corpus's
    # stale pin is exactly that shape. A line-scoped scan found zero of one.
    if head:
        for m in _SHA_CLAIM.finditer(text):
            sha = m.group("sha")
            lineno = text.count("\n", 0, m.start("sha")) + 1
            if allowed_by(sha):
                allowed.append(f"STALESHA {sha} L{lineno}")
                continue
            if head.startswith(sha):
                continue
            if not _is_commit(root, sha):
                # HARD. A sha that names no commit in this repository cannot have
                # been measured at. Mistyped, or from another checkout.
                findings.append(
                    ("UNKNOWNSHA", lineno, f"`{sha}` is not a commit in this repository")
                )
            else:
                # ADVISORY. Older-than-HEAD is the NORMAL condition of every written
                # measurement — the document was written at some commit and HEAD moved.
                # Filed as hard it fires on every correctly-provenanced measurement in
                # the tree, which is the opposite of what a provenance rule wants. Only
                # a reader knows whether the measured thing has since changed.
                advisories.append(
                    ("STALESHA", lineno,
                     f"`{sha}` is behind HEAD ({head[:7]}) — re-measure if what it measured has changed")
                )

    findings.sort(key=lambda f: (f[1], f[0]))
    advisories.sort(key=lambda f: (f[1], f[0]))
    return findings, advisories, allowed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="H-MAD phase-document pre-dispatch precheck")
    ap.add_argument("document")
    ap.add_argument("--phase", required=True, choices=PHASES)
    ap.add_argument("--root", default=".", help="repository root; cited paths resolve here")
    ap.add_argument("--allow", action="append", default=[],
                    help="a substring whose hits are deliberate. An INPUT, never inferred. Repeatable.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    doc = Path(args.document)
    root = Path(args.root).resolve()

    try:
        findings, advisories, allowed = scan(doc, args.phase, root, args.allow)
    except Unreadable as exc:
        print(f"PRECHECK: UNREADABLE reason={exc.reason}")
        print(f"[H-MAD] precheck {doc} unreadable")
        return 2

    verdict = "FAIL" if findings else "PASS"

    if args.json:
        print(json.dumps({
            "verdict": verdict,
            "issues": len(findings),
            "findings": [{"kind": k, "line": n, "detail": d} for k, n, d in findings],
            "advisories": [{"kind": k, "line": n, "detail": d} for k, n, d in advisories],
            "allowed": allowed,
        }, indent=2))
        return 0

    print(f"PRECHECK: {verdict} issues={len(findings)}")
    for kind, lineno, detail in findings:
        print(f"{kind}: L{lineno} {detail}")
    for kind, lineno, detail in advisories:
        print(f"{kind}: L{lineno} {detail}   (advisory — does not move the verdict)")
    for a in allowed:
        print(f"ALLOWED: {a}")
    print(f"[H-MAD] precheck {doc.name} {verdict} issues={len(findings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
