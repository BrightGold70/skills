#!/usr/bin/env python3
"""h_mad_audit_gate.py - classify H-MAD audit files for blocking findings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# Suffix of the sidecar a passing gate writes beside the audit file. Kept next to
# the audit rather than in orchestrator state because the pairing IS the claim:
# this verdict was about this content, and the two must travel together.
STAMP_SUFFIX = ".gated.json"


TRANSPORT_RE = re.compile(r"^audit_[^.]+\.report\.md$")


def is_transport_path(path: Path) -> bool:
    """True iff path.name matches TRANSPORT_RE."""
    return bool(TRANSPORT_RE.match(path.name))


BLOCKING_SECTIONS = {
    "## Must-fix": "must_count",
    "## Should-fix": "should_count",
}


# Bullet markers a reviewer may emit. agy (Antigravity/Gemini) renders `• `, other
# tools `* `; the template asks for `- `. A trailing space is REQUIRED so markdown
# emphasis lines placed under a section (`**Note:** …`, `*(no issues)*`) are not
# miscounted as findings — those start with `*` but not `* `. Leading whitespace is
# stripped before matching because the Gemini TUI indents every captured line ~2
# spaces, which previously hid `## Must-fix` from a column-0 match and silently
# scored a real finding as PASS.
_BULLET_MARKERS = ("- ", "* ", "• ")


def _bullet_remainder(stripped: str) -> str | None:
    """Return the text after a bullet marker, or None if not a bullet line."""
    for mark in _BULLET_MARKERS:
        if stripped.startswith(mark):
            return stripped[len(mark):].strip()
    return None


# Formatting a reviewer may wrap the empty-section sentinel in. agy writes
# `None.` with a trailing period; markdown emphasis (`**None**`, `_None_`,
# `` `None` ``) is the same class. Every one of these is the single word None
# dressed up, and a bare `==` comparison misses all of them -- the section then
# falls through the fail-safe branch below and MANUFACTURES a phantom finding
# (D-2, observed live: `Must-fix: None.` scored `GATE: FAIL must=1`).
_SENTINEL_TRIM = " \t.*_`"


def _is_none_sentinel(payload: str) -> bool:
    """True iff `payload` is the empty-section sentinel `None`, however dressed.

    Trims surrounding whitespace, trailing punctuation and markdown emphasis
    before comparing. It is a full-string comparison after trimming, never a
    prefix match, so a real finding that merely BEGINS with the word None
    ("None of the ACs pin the emitter — …") still counts as a finding.
    """
    return payload.strip(_SENTINEL_TRIM).lower() == "none"


def _payload(line: str) -> str:
    """The finding text of a content line: its bullet remainder, or the line itself.

    Lets `- None` and `None` both read as the empty-section sentinel, and lets a
    non-bulleted finding (prose / `1.` numbered / `> blockquote`) still be seen as
    content rather than silently ignored.
    """
    stripped = line.strip()
    remainder = _bullet_remainder(stripped)
    return remainder if remainder is not None else stripped


# --- finding CLASS -------------------------------------------------------------
#
# A reviewer classifies each Must-fix / Should-fix bullet on a CONTINUATION line,
# the same shape as `quote:` — never a `- ` bullet, which would be a second finding:
#
#     - <issue> — <why>
#       class: build | measurement
#
# The operational test is one sentence, stated identically in the template, in
# agents/doc-auditor.md and in SKILL.md: "would the code or tests a 5d/5e
# implementer writes differ if this finding were fixed?" — yes is `build`, no is
# `measurement`. Measured on doc-block-exec (18 gating rounds, 98 design cycles):
# by r18 the union held 15 musts and 9 of them were the documents' own
# self-measurement layer — a ledger row the audit report landing MOVES, a
# trip-wire stamp, "eight" over a ten-member list, a self-count of 4 that reads
# 5. Real findings, none of which changes what an implementer writes, and a gate
# that scores them like a false timeout semantics cannot converge on a document
# that publishes numbers about a tree it moves.
#
# It fails CLOSED in every direction the reviewer can get wrong: an untagged
# bullet is `build`; an unknown value is `build`; and a bullet tagged `build` OR
# an unknown value cannot be cleared by the `## Acknowledged-not-fixed` sidecar
# at all (`ack_refused` counts those). Only untagged bullets keep the pre-class
# ack behaviour, because every sidecar written before the tag existed is untagged.
_CLASS_RE = re.compile(r"^class\s*:\s*([a-z]+)$")
CLASSES = ("build", "measurement")


def _class_of(line: str) -> str | None:
    """`build` / `measurement` / an unknown word from a `class:` continuation line, else None.

    Only a NON-bullet line qualifies (a `- class: x` line is a finding, per the
    `quote:` rule). Spelling is canonicalised — emphasis, backticks, case,
    trailing punctuation — never fuzzed: `class: cosmetic` returns "cosmetic",
    which the counter treats as untagged (build).
    """
    stripped = line.strip()
    if _bullet_remainder(stripped) is not None:
        return None
    s = _ACK_STRIP.sub("", stripped)
    s = _ACK_WS.sub(" ", s).strip().strip(" .;,").lower()
    m = _CLASS_RE.match(s)
    return m.group(1) if m else None


_ACK_KEY_RE = re.compile(r"^\[([A-Za-z0-9][A-Za-z0-9 ._:/-]{0,60})\]\s*")
_ACK_STRIP = re.compile(r"[`*_~]")
_ACK_WS = re.compile(r"\s+")


def _ack_normalize(payload: str) -> str:
    """Canonical form of a finding/ack bullet for comparison.

    A CANONICALISATION, never a similarity: it removes formatting the reviewer did
    not mean to change — markdown emphasis, backticks, line-wrap whitespace, case,
    trailing punctuation — and nothing else. Two texts that differ in a word still
    differ here, which is the property that makes it safe (#15).
    """
    s = _ACK_STRIP.sub("", payload)
    s = _ACK_WS.sub(" ", s).strip()
    s = s.strip(" .;,:—-")
    return s.lower()


def _ack_key(payload: str) -> str | None:
    """A leading `[key]` tag, lowercased, or None.

    The rewording-immune half. An operator who writes
    `- [ac-1.4 teardown-leak] <text>` in the sidecar acknowledges THAT finding
    however the next cycle's reviewer rephrases it, and two findings that share a
    topic but not a key are never conflated — which is exactly the case fuzzy
    matching gets wrong below.
    """
    m = _ACK_KEY_RE.match(payload.strip())
    return m.group(1).strip().lower() if m else None


def _is_acknowledged(payload: str, acknowledged: set[str]) -> bool:
    """Is this finding covered by the `## Acknowledged-not-fixed` sidecar?

    Three ways, in order of strength, and NO fuzzy text similarity. That omission
    is measured, not squeamish. On the real 7-bullet sidecar of HemaSuite's
    `gateway-consolidation.plan.audit.v18` — which accreted 7 bullets over ~3
    underlying findings, with items 1/4 and 2/5 as re-worded duplicates and items
    6/7 as two genuinely DIFFERENT AC-1.4 process-group leaks — token-overlap
    scores the negative control ABOVE both true pairs:

        positive 1~4  jaccard 0.089
        positive 2~5  jaccard 0.158
        NEGATIVE 6~7  jaccard 0.180   <-- higher than either pair

    So the ordering is inverted: every threshold that pairs the re-worded
    duplicates collapses the two distinct leaks FIRST, and a collapsed ack
    silently clears a real finding. Same shape as the refused evidence check
    (#27): the rule that would help does not discriminate, and the one that
    discriminates is vacuous. Softening therefore stops at canonicalisation plus
    an explicit operator key.
    """
    if payload in acknowledged:
        return True
    norm = _ack_normalize(payload)
    if any(norm == _ack_normalize(a) for a in acknowledged):
        return True
    key = _ack_key(payload)
    if key is not None and any(_ack_key(a) == key for a in acknowledged):
        return True
    return False


def _count_section_findings(content: list[str], acknowledged: set[str]) -> int:
    """Findings in one blocking section — the count alone (see `_section_detail`)."""
    return _section_detail(content, acknowledged)["count"]


def _section_detail(content: list[str], acknowledged: set[str]) -> dict:
    """Findings in one blocking section's non-blank content lines, by class.

    Returns ``{"count", "build", "measurement", "untagged", "ack_refused"}``.

    A section is CLEAN (0) iff every line's payload is the `None` sentinel — this
    covers an empty section, `None`, a stray `- None`, and punctuated/emphasised
    forms like `None.` or `**None**` (see `_is_none_sentinel`). Otherwise it has
    findings. When the section carries `-`/`*`/`•` bullets we count them (so a
    wrapped multi-line bullet counts once, not once per line), and a `class:`
    continuation line under a bullet classifies THAT bullet (`_class_of`). When
    it carries non-`None` content but NO bullet — a prose, numbered, or
    blockquote finding a reviewer wrote off-template — we count 1 rather than 0,
    so such a finding fails the gate (fail-safe) instead of being silently
    missed (F14).

    A bullet that is acknowledged in the `## Acknowledged-not-fixed` sidecar is
    cleared when it is tagged `class: measurement` or carries no tag — UNLESS the
    reviewer tagged it `class: build` or an unknown value, in which case it is
    counted anyway and reported under `ack_refused`: a build-class must is what
    5d/5e would implement wrongly, and no sidecar clears that. A section whose
    bullets were ALL cleared is CLEAN, and must not fall into the off-template
    fail-safe below: both cases leave no countable bullet, but only the
    bulletless one is an unscored finding. Conflating them capped the escape at
    one bullet per section (a 2-bullet section scored 1 with both bullets
    acknowledged), so no multi-finding gate could ever be cleared.
    """
    zero = {"count": 0, "build": 0, "measurement": 0, "untagged": 0, "ack_refused": 0}
    payloads = [_payload(line) for line in content]
    if all(_is_none_sentinel(p) for p in payloads):
        return zero

    # Group into (payload, class) per bullet; continuation lines classify the
    # bullet they follow. Lines before any bullet are prose (off-template).
    findings: list[tuple[str, str | None]] = []
    target: int | None = None          # index of the bullet a `class:` line classifies
    for line, payload in zip(content, payloads):
        if _bullet_remainder(line.strip()) is not None:
            if payload and not _is_none_sentinel(payload):
                findings.append((payload, None))
                target = len(findings) - 1
            else:
                # A `- None` sentinel bullet ends the previous bullet's span: a
                # `class:` line after it classifies nothing (review m1 — otherwise
                # it downgraded the PREVIOUS finding, the fail-open direction).
                target = None
            continue
        cls = _class_of(line)
        if cls is not None and target is not None:
            text_, _old = findings[target]
            findings[target] = (text_, cls)

    if not findings:
        # Non-None content with no countable bullet → at least one off-template finding.
        joined = " ".join(p for p in payloads if p)
        if _is_acknowledged(joined, acknowledged):
            return zero
        return {"count": 1, "build": 1, "measurement": 0, "untagged": 1, "ack_refused": 0}

    out = dict(zero)
    for payload, cls in findings:
        acked = _is_acknowledged(payload, acknowledged)
        # Only two shapes clear through the sidecar: an explicit `measurement`,
        # and an UNTAGGED bullet (every sidecar written before the tag existed is
        # untagged, so that is the back-compat surface). An explicit `build` is
        # refused, and so is an UNKNOWN value: it can only occur in a report
        # written after the tag existed, so refusing it costs no back-compat and
        # closes the hole a typo'd `class: buidl` would otherwise open (review M1).
        if acked and (cls == "measurement" or cls is None):
            continue                      # cleared by the sidecar
        if acked:
            out["ack_refused"] += 1       # build or unknown: the sidecar cannot clear it
        out["count"] += 1
        if cls == "measurement":
            out["measurement"] += 1
        else:
            out["build"] += 1
            if cls not in CLASSES:
                out["untagged"] += 1
    return out


def has_gate_sections(text: str) -> bool:
    """True iff BOTH `## Must-fix` and `## Should-fix` headers are present.

    An extract that lacks them is not a clean audit — it is no audit at all (an
    empty/garbled scrape). The gate must refuse to score it rather than report
    the absent findings as zero findings.
    """
    seen = {line.strip() for line in text.splitlines()}
    return all(section in seen for section in BLOCKING_SECTIONS)


def classify_detail(text: str, acknowledged: set[str] | None = None) -> dict:
    """`classify()` plus the per-class breakdown of both blocking sections.

    Keys: verdict, must_count, should_count, must_build, must_measurement,
    must_untagged, should_build, should_measurement, should_untagged, ack_refused.
    The verdict is unchanged by the class — a measurement-class must still FAILS
    the gate; what the class changes is which findings the sidecar may clear and
    which the orchestrator may carry past a round (SKILL.md, Phase 3 / 5b exit).
    """
    acknowledged_items = acknowledged or set()
    section_content: dict[str, list[str]] = {key: [] for key in BLOCKING_SECTIONS.values()}
    current_count_key: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped in BLOCKING_SECTIONS:
            current_count_key = BLOCKING_SECTIONS[stripped]
            continue
        if stripped.startswith("## "):
            current_count_key = None
            continue
        if current_count_key and stripped:
            section_content[current_count_key].append(line)

    detail = {key: _section_detail(content, acknowledged_items)
              for key, content in section_content.items()}
    must, should = detail["must_count"], detail["should_count"]
    verdict = "FAIL" if must["count"] or should["count"] else "PASS"
    return {
        "verdict": verdict,
        "must_count": must["count"],
        "should_count": should["count"],
        "must_build": must["build"],
        "must_measurement": must["measurement"],
        "must_untagged": must["untagged"],
        "should_build": should["build"],
        "should_measurement": should["measurement"],
        "should_untagged": should["untagged"],
        "ack_refused": must["ack_refused"] + should["ack_refused"],
    }


def classify(text: str, acknowledged: set[str] | None = None) -> dict:
    """Count findings in Must-fix/Should-fix (indent-, marker- and prose-tolerant).

    A finding is a `-`/`*`/`•` bullet, OR — fail-safe — any non-`None` content in a
    blocking section that carries no bullet (prose / numbered / blockquote), so an
    off-template finding fails the gate rather than being silently missed.
    Returns exactly ``verdict`` / ``must_count`` / ``should_count`` (every
    existing caller reads those three); `classify_detail()` adds the classes.
    """
    d = classify_detail(text, acknowledged)
    return {"verdict": d["verdict"], "must_count": d["must_count"], "should_count": d["should_count"]}


def _acknowledged_from_text(text: str) -> set[str]:
    acknowledged: set[str] = set()
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Acknowledged-not-fixed":
            in_section = True
            continue
        if stripped.startswith("## "):
            in_section = False
            continue
        if in_section:
            item = _bullet_remainder(stripped)
            if item:
                acknowledged.add(item)
    return acknowledged


def _read_ack_file(path: Path) -> set[str]:
    acknowledged: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if stripped:
            acknowledged.add(stripped)
    return acknowledged


def _digest(path: Path) -> str:
    """Content hash of one gated file. Raises OSError if it cannot be read."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp_path(audit_file: Path) -> Path:
    return audit_file.with_name(audit_file.name + STAMP_SUFFIX)


def verify_stamp(audit_file: Path) -> dict:
    """Is the recorded verdict still about the content on disk?

    The gate reads the audit file and never the document the audit judged, so a
    PASS outlives every later edit to the thing it passed. Measured: a design
    audited clean twice produced 9 findings on the next cycle, 4 of them created
    by the edits that fixed the previous cycle.

    `UNSTAMPED` is a cannot-judge, never `CURRENT`: nothing was recorded, so
    nothing was compared, and reporting that as current is the same lie as an
    empty scrape reading as "no findings".
    """
    path = stamp_path(audit_file)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"verdict": "UNSTAMPED", "changed": [], "checked": 0}

    files = record.get("files") or {}
    changed = []
    for rel, recorded in sorted(files.items()):
        target = audit_file.parent / rel
        try:
            current = _digest(target)
        except OSError:
            # Deleted or unreadable. The verdict was about content that is no
            # longer there, which is a change, not a cannot-judge.
            changed.append(f"{rel} (unreadable)")
            continue
        if current != recorded:
            changed.append(rel)

    return {
        "verdict": "STALE" if changed else "CURRENT",
        "changed": changed,
        "checked": len(files),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the audit gate CLI."""
    parser = argparse.ArgumentParser(description="H-MAD audit gate")
    parser.add_argument("audit_file", type=Path)
    parser.add_argument("--ack-file", type=Path)
    parser.add_argument("--must-only", action="store_true")
    parser.add_argument(
        "--gated", action="append", default=[], type=Path, metavar="PATH",
        help="a document this audit judged; recorded beside the verdict on PASS. "
             "Repeatable — a cycle that gates a design and an impl-plan must name both",
    )
    parser.add_argument(
        "--verify-stamp", action="store_true",
        help="re-hash what a previous PASS recorded and report CURRENT / STALE / UNSTAMPED",
    )
    args = parser.parse_args(argv)

    if args.verify_stamp:
        result = verify_stamp(args.audit_file)
        verdict = result["verdict"]
        print(f"GATESTAMP: {verdict} checked={result['checked']} changed={len(result['changed'])}")
        for rel in result["changed"]:
            print(f"  changed: {rel}")
        if verdict == "STALE":
            print(
                "  the PASS was about content that has since moved — the edits that "
                "fixed the last cycle are themselves ungated. Re-audit before "
                "relying on it (halt `audit_gate:verdict_stale`)."
            )
        elif verdict == "UNSTAMPED":
            print(
                "  nothing was recorded, so nothing was compared — a cannot-judge, "
                "not a clean readback. Re-run the gate with --gated."
            )
        print(f"[H-MAD] {args.audit_file.name.split('.')[0] or 'unknown'} gatestamp {verdict}")
        return 0 if verdict == "CURRENT" else 2

    feature = args.audit_file.name.split(".")[0] or "unknown"
    if is_transport_path(args.audit_file):
        print("GATE: INVALID must=0 should=0")
        print(
            f"[H-MAD] {feature} gate INVALID "
            "(transport file — collect it into docs first: h_mad_collect_report.py)"
        )
        return 2

    try:
        text = args.audit_file.read_text(encoding="utf-8")
        acknowledged = _acknowledged_from_text(text)
        if args.ack_file:
            acknowledged.update(_read_ack_file(args.ack_file))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # An input lacking the mandatory `## Must-fix`/`## Should-fix` sections is not
    # a clean audit — it is an empty or garbled scrape (e.g. the reviewer emitted
    # nothing and the extractor wrote an empty file). Scoring it would report the
    # missing findings as zero findings. Refuse with a distinct token + non-zero
    # exit (an operational error, not a verdict), so "no report" can never read as
    # "no findings". Signal discipline holds: exit 0 is reserved for PASS/FAIL.
    if not has_gate_sections(text):
        print("GATE: INVALID must=0 should=0")
        print(f"[H-MAD] {feature} gate INVALID (missing Must-fix/Should-fix sections)")
        return 2

    result = classify_detail(text, acknowledged)
    verdict = "FAIL" if result["must_count"] or (result["should_count"] and not args.must_only) else "PASS"

    stamped = ""
    if args.gated and verdict == "PASS":
        # Hash everything BEFORE writing anything: a stamp covering three files
        # of which one was unreadable would record a verdict over content the
        # gate never saw, and the readback would then compare that fiction to
        # reality and report CURRENT.
        files = {}
        for path in args.gated:
            try:
                files[os.path.relpath(path, args.audit_file.parent)] = _digest(path)
            except OSError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                print("GATE: UNSTAMPABLE must=0 should=0")
                print(
                    "  a gated file could not be read, so nothing was recorded — "
                    "an operational error, not a verdict about the audit."
                )
                print(f"[H-MAD] {feature} gate UNSTAMPABLE")
                return 2
        stamp_path(args.audit_file).write_text(
            json.dumps({"verdict": verdict, "files": files}, indent=1) + "\n",
            encoding="utf-8",
        )
        stamped = f" gated={len(files)}"

    # The first line is what every existing caller reads, so the stamp count is
    # appended rather than woven in, and is absent entirely without --gated.
    print(f"GATE: {verdict} must={result['must_count']} should={result['should_count']}{stamped}")
    # Line 2 is the class breakdown over BOTH blocking sections. It is a second
    # line rather than fields woven into line 1: `h_mad_audit_cycle.GATE_RE`
    # anchors on `should=N\s*$`, so it already refuses a `--gated` line 1 (latent —
    # the cycle driver never passes `--gated`), and adding more there would make
    # every verdict un-parse. It is printed on PASS and FAIL only; the INVALID and
    # UNSTAMPABLE early returns above carry no class line, and a consumer must
    # never read its absence as `build=0`.
    print(
        "GATE-CLASS: "
        f"build={result['must_build'] + result['should_build']} "
        f"measurement={result['must_measurement'] + result['should_measurement']} "
        f"untagged={result['must_untagged'] + result['should_untagged']} "
        f"ack_refused={result['ack_refused']}"
    )
    print(f"[H-MAD] {feature} gate {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
