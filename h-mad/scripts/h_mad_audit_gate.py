#!/usr/bin/env python3
"""h_mad_audit_gate.py - classify H-MAD audit files for blocking findings."""
from __future__ import annotations

import argparse
import subprocess
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
# bullet is `build`; an unknown value is `build`; and a MUST-FIX bullet tagged
# `build` OR an unknown value cannot be cleared by the `## Acknowledged-not-fixed`
# sidecar at all (`ack_refused` counts those). Should-fix bullets of any class
# stay deferrable through the sidecar, as they always were. Only untagged bullets
# keep the pre-class ack behaviour, because every sidecar written before the tag
# existed is untagged.
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


def _section_detail(content: list[str], acknowledged: set[str], *,
                    refuse_build_ack: bool = True) -> dict:
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
        if acked and (cls == "measurement" or cls is None or not refuse_build_ack):
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

    # Only a MUST-FIX tagged build (or unknown) is refused by the sidecar: a
    # build-class must is what 5d/5e would implement wrongly. A should-fix of
    # any class has always been deferrable through the sidecar (SKILL.md, the
    # Phase 3 / 5b exit clauses), and the class does not change that.
    detail = {key: _section_detail(content, acknowledged_items,
                                   refuse_build_ack=(key == "must_count"))
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


# --- the project suite (#91) ---------------------------------------------------
#
# Measured on HemaSuite `#18 gateway-consolidation`: a dual-surface design audit
# ran 95 cycles without meeting its exit gate while a repo test enforcing the
# AUDIT LOOP'S OWN invariant stayed red for the entire life of the feature. This
# file had ZERO occurrences of `subprocess|pytest|check_call|os.system` — a
# document scorer with no execution path — and SKILL.md ran pytest only at 5e and
# 5f. Phases 3 and 4 had no suite run in the protocol and none here.
#
# A red suite BLOCKS THE EXIT, not each cycle. Blocking every cycle makes an audit
# hostage to an unrelated flaky test, and this repo has the receipt:
# `docs/skill-candidates.md:1277` records two pytest runs over one working tree
# producing 6 and 3 failures in DIFFERENT sets, and 0 when the file ran alone. So
# the per-cycle `GATE:` verdict is untouched and the streak is what refuses.
SUITE_UNMEASURED = None


def run_suite(test_root: Path, command: list[str] | None = None,
              timeout: int = 3600) -> dict:
    """Run the project suite once. Returns a verdict dict; raises nothing.

    The test root is NAMED, never inferred: `SKILL.md` step 5f already documents
    why an unscoped pytest from a repository root collects sibling-project import
    mismatches, and HemaSuite carries two suites under a monorepo root.
    """
    argv = command or [sys.executable, "-m", "pytest", str(test_root), "-q"]
    try:
        run = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"verdict": "UNREADABLE", "reason": f"timeout_after_{timeout}s"}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"verdict": "UNREADABLE", "reason": exc.__class__.__name__.lower()}
    tail = (run.stdout or "") + (run.stderr or "")
    summary = _suite_summary(tail)
    if summary is None:
        # No parseable summary line: pytest did not get far enough to report.
        # That is a cannot-judge, NOT a failure — and never a pass. Reading a
        # missing summary as either is how a run that collected nothing scores.
        return {"verdict": "UNREADABLE", "reason": "no_summary", "rc": run.returncode}
    passed, failed = summary
    if passed == 0 and failed == 0:
        # A run that collected nothing MEASURED nothing, and it exits 0. `pytest -k`
        # with a selection that matches no test is the standing example in this
        # repo. Neither PASS (it showed nothing green) nor FAIL (nothing was
        # broken) — the third answer is the honest one.
        return {"verdict": "UNREADABLE", "reason": "no_tests_ran", "rc": run.returncode}
    verdict = "PASS" if failed == 0 and passed > 0 else "FAIL"
    return {"verdict": verdict, "passed": passed, "failed": failed, "rc": run.returncode}


_SUITE_RE = re.compile(r"(?:(\d+) failed[,.]? )?(?:(\d+) passed)")


def _suite_summary(text: str) -> tuple[int, int] | None:
    """`(passed, failed)` from pytest's own summary line, or None.

    Scored on the SUMMARY, never on the exit code: this repo has been fooled by
    rc in both directions — a skipped selection and a killed run both exit 0.
    """
    best = None
    for match in _SUITE_RE.finditer(text):
        failed, passed = match.group(1), match.group(2)
        if passed is None and failed is None:
            continue
        best = (int(passed or 0), int(failed or 0))
    return best


def stamp_path(audit_file: Path) -> Path:
    return audit_file.with_name(audit_file.name + STAMP_SUFFIX)


# The alternation order does NOT matter here, though it looks like it should: the
# feature group is non-greedy and the alternation is tried at a position fixed by
# the preceding `\.`, so `plan` cannot match inside `impl-plan`. Measured both
# orders on `doc-block.impl-plan.audit.v20.codex.md.gated.json` — identical parse.
# `impl-plan` is listed first anyway, for readers who expect the longest-first rule
# that WOULD be load-bearing if the group were greedy or unanchored.
_STAMP_NAME_RE = re.compile(
    r"^(?P<feature>.+?)\.(?P<phase>impl-plan|design|plan)\.audit\.v(?P<cycle>\d+)"
    r"\.(?P<leg>[^.]+)\.md" + re.escape(STAMP_SUFFIX) + r"$"
)


def cycle_of(stamp: Path) -> tuple[str, str, int] | None:
    """`(feature, phase, cycle)` from a stamp's name, or None if it is not in the grammar.

    A cycle emits one stamp PER LEG, so "the last two stamps" is not "two cycles".
    Measured 2026-09-07 over the real archive: of 17 cycles carrying stamps, **8
    have two**, and same-cycle legs sort ADJACENTLY — so a glob hands `exit_check`
    two legs of ONE cycle. Executed against the shipped gate, the real pair
    `doc-block-exec.design.audit.v20.codex` + `…v20.p1` returned `EXIT: READY`:
    the exit gate certified a two-consecutive-clean-cycle streak from one cycle.

    None is a CANNOT-JUDGE and its caller must refuse, never pass. A stamp whose
    cycle cannot be established could be a second leg of a cycle already counted,
    and treating it as its own cycle is the defect this closes.
    """
    m = _STAMP_NAME_RE.match(stamp.name)
    if m is None:
        return None
    return m.group("feature"), m.group("phase"), int(m.group("cycle"))


def _leg_key(legs) -> list[str]:
    """The comparable form of a leg set: sorted, deduped, whitespace-stripped.

    Order is not a leg-set change and neither is naming a leg twice, so both are
    normalised away before anything is compared. Without this the gate would
    refuse a streak for the order the orchestrator happened to type its flags in.
    """
    return sorted({str(name).strip() for name in legs if str(name).strip()})


def exit_check(stamps: list[Path]) -> dict:
    """Are the last two cycles eligible to close the exit gate?

    The enforcement point for #91, and the reason this is gate-level rather than
    protocol-level: nothing counts the streak. `grep -in 'streak|consecutive'`
    over `scripts/` returns nothing, so the two-consecutive-both-clean rule lives
    only in SKILL prose — and an instruction an orchestrator can skip is exactly
    what 91 cycles of a red suite already demonstrated.

    A cycle whose suite was RED or UNMEASURED cannot contribute to the streak.
    Unmeasured is refused for the same reason a missing summary is: a cycle that
    never ran the suite has not shown it green, and treating silence as a pass is
    the defect this closes.

    **H3 — the streak is measured over a leg set, not over cycles alone.** On
    HemaSuite `#18 gateway-consolidation` Σmust tracked the LEG COUNT rather than
    document quality: the 13 design cycles ending at c99 ran
    `3 3 7 5 3 5 4 3 8 4 7 12 6`, and every rise coincided with a leg added or
    returning (teammate c87, doc-auditor+crossdoc c92, codex c97). Re-derive the
    series from the ledger rather than reading that window as current; it has
    grown since. The exit streak was reset by new legs four times and never
    approached by the documents — zero at c99 when measured, still zero at c104.
    Two cycles therefore close the gate only if they asked the same question; a
    changed set starts a new baseline by construction, since two fresh cycles
    under it agree with each other.

    An UNRECORDED leg set does **not** block. Every stamp written before the
    field existed has none and was not thereby wrong, and a detector that fires
    on artifacts which legitimately passed is the calibration error this repo has
    already paid for. It is reported instead — `legs=unrecorded` on the EXIT
    line, and `GATE-LEGS: unrecorded` at stamp time — because not-blocking and
    not-saying are different things, and only the second turns H3 back into prose.
    """
    # Group by CYCLE first: a cycle emits one stamp per leg, so counting stamps
    # counts legs. Fail closed on a name outside the grammar — an unplaceable
    # stamp may be a second leg of a cycle already counted.
    grouped: dict[tuple[str, str, int], list[Path]] = {}
    for path in stamps:
        key = cycle_of(path)
        if key is None:
            return {"verdict": "UNREADABLE", "reason": f"stamp_name:{path.name}"}
        grouped.setdefault(key, []).append(path)

    # Numeric on the cycle number, never lexical: `v10` sorts before `v9` as text,
    # which would silently consider the wrong pair.
    order = sorted(grouped, key=lambda k: (k[0], k[1], k[2]))
    if len(order) < 2:
        return {"verdict": "BLOCKED", "reason": f"not_two_cycles:{len(order)}"}
    considered_keys = order[-2:]
    considered = [grouped[k][0] for k in considered_keys]

    leg_sets: list[list[str] | None] = []
    for key in considered_keys:
        # EVERY leg of a counted cycle must be clean — a cycle is not clean per-leg.
        cycle_legs: list[list[str] | None] = []
        for path in sorted(grouped[key]):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                return {"verdict": "UNREADABLE",
                        "reason": f"stamp:{exc.__class__.__name__.lower()}:{path.name}"}
            if data.get("verdict") != "PASS":
                return {"verdict": "BLOCKED", "reason": f"not_clean:{path.name}"}
            suite = data.get("suite")
            if suite is None:
                return {"verdict": "BLOCKED", "reason": f"suite_unmeasured:{path.name}"}
            if suite != "PASS":
                return {"verdict": "BLOCKED", "reason": f"suite_{suite.lower()}:{path.name}"}
            recorded = data.get("legs")
            cycle_legs.append(None if recorded is None else _leg_key(recorded))
        # The legs of one cycle must agree about what that cycle ran. Disagreement
        # is a cannot-judge, not a set to pick a winner from.
        distinct = {tuple(v) if v is not None else None for v in cycle_legs}
        if len(distinct) > 1:
            return {"verdict": "BLOCKED",
                    "reason": f"legs_disagree:{key[1]}.v{key[2]}"}
        leg_sets.append(cycle_legs[0])

    # Compared only when BOTH cycles recorded one: a mismatch against a cycle
    # that recorded nothing is not a mismatch, it is a cannot-judge.
    first, second = leg_sets
    legs: list[str] | None = None
    if first is not None and second is not None:
        if first != second:
            return {"verdict": "BLOCKED",
                    "reason": f"legs_changed:{'+'.join(first) or '-'}"
                              f"|{'+'.join(second) or '-'}"}
        legs = first
    return {"verdict": "READY", "cycles": [p.name for p in considered], "legs": legs}


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
        "--project-tests", type=Path, metavar="TEST_ROOT",
        help="run the project suite at TEST_ROOT and report it as its own `SUITE:` "
             "line, recording the result in the stamp (#91). A scoped root, never "
             "the repository root: an unscoped pytest collects sibling-project "
             "import mismatches (SKILL.md 5f).",
    )
    parser.add_argument(
        "--suite-cmd", help="override the suite command (default: pytest <root> -q)",
    )
    parser.add_argument(
        "--suite-result", choices=("PASS", "FAIL", "UNREADABLE"), metavar="VERDICT",
        help="record a suite verdict measured ONCE for the whole cycle instead of "
             "running one here. The cycle driver calls this gate once per LEG, and "
             "running the suite per leg is minutes each and the design "
             "`audit_suite_gate.json` already rejects. Mutually exclusive with "
             "--project-tests: two sources for one field is how they disagree.",
    )
    parser.add_argument(
        "--legs", action="append", default=[], metavar="NAME",
        help="a reviewer leg this cycle ran (`codex`, `agy`, `doc-auditor`, …); "
             "recorded in the stamp on PASS. Repeatable. Two cycles close the "
             "exit gate only over the SAME leg set (#11/H3): adding or dropping "
             "a leg starts a new baseline instead of silently resetting a streak "
             "nobody was counting.",
    )
    parser.add_argument(
        "--exit-check", nargs="+", type=Path, metavar="STAMP",
        help="read the cycle stamps and report whether the exit gate may close. "
             "A cycle whose suite was red or unmeasured cannot contribute, and a "
             "leg set that changed between the two cycles blocks it (#11/H3).",
    )
    parser.add_argument(
        "--verify-stamp", action="store_true",
        help="re-hash what a previous PASS recorded and report CURRENT / STALE / UNSTAMPED",
    )
    args = parser.parse_args(argv)

    if args.exit_check:
        result = exit_check(sorted(args.exit_check))
        detail = result.get("reason") or ",".join(result.get("cycles", []))
        line = (f"EXIT: {result['verdict']} "
                f"{'reason' if result.get('reason') else 'cycles'}={detail}")
        if result["verdict"] == "READY":
            # Reported on every READY, recorded or not. A streak that closed over
            # an unknown leg set is still a fact the reader needs (#11/H3).
            line += f" legs={'+'.join(result['legs']) if result.get('legs') else 'unrecorded'}"
        print(line)
        reason = str(result.get("reason", ""))
        if result["verdict"] == "UNREADABLE" and reason.startswith("stamp_name"):
            print("  that stamp's name is outside the audit grammar "
                  "(`<feature>.<phase>.audit.v<N>.<leg>.md.gated.json`), so which CYCLE "
                  "it belongs to cannot be established — and an unplaceable stamp may be "
                  "a second leg of a cycle already counted. A cannot-judge, never a pass.")
        elif result["verdict"] == "BLOCKED":
            if reason.startswith("legs_changed"):
                print("  the two cycles ran different reviewer legs, so the streak "
                      "measures two different questions. Σmust tracked the leg count "
                      "on #18 and the exit was reset four times by legs, never "
                      "approached by the documents (#11/H3). Run two cycles under "
                      "the new set — that IS the new baseline.")
            elif reason.startswith("legs_disagree"):
                print("  two legs of the SAME cycle disagree about which legs that cycle "
                      "ran. There is no winner to pick between them — re-stamp the cycle "
                      "with one leg set (#11/H3).")
            elif reason.startswith("not_two_cycles"):
                print("  a streak is two CYCLES, not two stamps — a cycle emits one stamp "
                      "per leg. Measured 2026-09-07: 8 of 17 archived cycles carry two "
                      "stamps, they sort adjacently, and the real pair "
                      "`design.audit.v20.codex`+`…v20.p1` returned READY before this. "
                      "Gate another cycle, do not add another leg.")
            else:
                print("  a cycle whose suite was red or unmeasured cannot close the exit "
                      "gate; the per-cycle verdicts are untouched (#91).")
        return 2 if result["verdict"] == "UNREADABLE" else 0

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

    if args.suite_result and args.project_tests is not None:
        print("ERROR: --suite-result and --project-tests are mutually exclusive — "
              "one field, one source", file=sys.stderr)
        return 2

    suite = SUITE_UNMEASURED
    if args.suite_result:
        # Measured once for the cycle by the driver and forwarded here. `source=cycle`
        # so a reader can never mistake a recorded verdict for one this call measured.
        suite = args.suite_result
        print(f"SUITE: {suite} source=cycle")
    elif args.project_tests is not None:
        command = args.suite_cmd.split() if args.suite_cmd else None
        outcome = run_suite(args.project_tests, command)
        suite = outcome["verdict"]
        if suite == "UNREADABLE":
            print(f"SUITE: UNREADABLE reason={outcome['reason']}")
        else:
            print(f"SUITE: {suite} passed={outcome['passed']} failed={outcome['failed']}")

    # Declared ABOVE `stamped` deliberately: `audit_suite_gate.json` anchors the
    # red-suite-hostage row on `stamped = ""` immediately followed by the `if`,
    # and splitting that pair drifts a neighbouring feature's mutation spec.
    legs_line: str | None = None
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
        # `None`, never `[]`: argparse cannot distinguish "no --legs" from an
        # explicitly empty one, and `[]` would CLAIM the cycle ran zero legs.
        # Claiming nothing is the honest record, and the exit gate reads it as a
        # cannot-judge rather than as a mismatch (#11/H3).
        # `or None`, not `if args.legs`: `--legs ""` makes the list TRUTHY and
        # `_leg_key` then strips it back to `[]`, which stamped a recorded-empty
        # set while `GATE-LEGS:` printed `unrecorded` — two surfaces disagreeing
        # about the same cycle. Normalise after the strip, not before it.
        legs = _leg_key(args.legs) or None
        stamp_path(args.audit_file).write_text(
            json.dumps({"verdict": verdict, "files": files, "suite": suite,
                        "legs": legs}, indent=1) + "\n",
            encoding="utf-8",
        )
        stamped = f" gated={len(files)}"
        # Deferred, not printed here: the emission order is GATE -> GATE-CLASS ->
        # GATE-LEGS, and this block runs BEFORE the verdict line. Printing in
        # place put GATE-LEGS above GATE and falsified the order this file's own
        # registry entry documents — caught by executing the CLI, not by reading it.
        legs_line = '+'.join(legs) if legs else 'unrecorded'

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
    # Line 3, on a stamped PASS only. Its own line for the same reason as
    # GATE-CLASS and SUITE: `h_mad_audit_cycle.GATE_RE` anchors on `should=N\s*$`,
    # so anything woven into line 1 un-parses every verdict. An orchestrator that
    # never names its legs is told so each cycle, at the point of use, rather
    # than once at the exit gate — which is what keeps H3 from being prose.
    if legs_line is not None:
        print(f"GATE-LEGS: {legs_line}")
    print(f"[H-MAD] {feature} gate {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
