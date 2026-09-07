#!/usr/bin/env python3
"""H7 — tag every must-fix with its ORIGIN, and measure the fix-introduced rate per cycle.

The hypothesis, verbatim from the `gateway-consolidation` audit ledger: "Measure the
fix-introduced rate every cycle instead of reconstructing it from memory at handoff."
That reconstruction is the part that failed. Phase 4 of `#18` ran 105 design cycles and
31 plan cycles, and the ledger's own summary of the tail could only say "at least **17 of
98** cycles carry a must-fix that an earlier cycle's fix created (seeded from recorded
evidence -- a lower bound; a blank cell in the table means *unclassified*, not *new*)".
A lower bound reconstructed at handoff is not a measurement, and it is the number the
whole audit-loop investigation turned on.

Tagged at the moment each must-fix is verified, the same corpus answers exactly: over the
152 records the prototype captured for cycles 98-103, **fix-introduced is 51** -- a third
of all must-fixes, and the largest single class. `author-self-caught` is 27 more: the same
class intercepted one step earlier by the revising author's own delta review, which is
what H4 automates. Neither number is recoverable from a cycle table after the fact.

**This script does not decide an origin.** Classifying a must-fix is a judgement about why
a defect exists -- whether the previous cycle's fix created it, whether the fix reached one
document and stopped -- and nothing here can see that. `append` records a judgement the
orchestrator has already made and refuses one that is malformed; `summary` aggregates.
That is also why there is no hook into `h_mad_audit_cycle.py`: the ledger says to "tag at
the moment the must-fix is verified, not at handoff", and the driver does not know that
moment.

**The vocabulary is fixed and is not re-derived here.** EIGHT origins, defined in the
ledger §"Per-cycle capture" and counted against it rather than from memory -- the first
draft of this docstring said nine. An unknown origin is the one hard error over content,
because a typo that silently becomes its own category is how this instrument would report
a falling fix-introduced rate that is really a spelling.

Note that `rejected` occurs **zero** times in the 152-record prototype, so the rule that
excludes it from the fix-introduced denominator has no coverage from real data and is
pinned by a synthetic fixture instead. That is worth saying out loud: "calibrated against
the real corpus" is a claim about the paths the corpus exercises, and this is not one.

Calibrated before it was wired, against the 152 records the prototype had already
captured: every hard rule below fires **zero** times on them. That is the bar a new
detector has to clear here -- every `h_mad_precheck_doc.py` detector first written as hard
fired 104 / 49 / 48 times on documents that had just passed 83 and 74 audit cycles.

Stdlib only, like every other h-mad script.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

# The nine origins, verbatim from the ledger's §"Per-cycle capture". Order is the
# ledger's, not alphabetical, so a reader diffing the two sees them line up.
ORIGINS = (
    "new-mechanism",
    "new-consistency",
    "fix-introduced",
    "propagation-gap",
    "instrument",
    "record-stale",
    "author-self-caught",
    "rejected",
)

# `by_cycle` names the cycle whose fix created this defect. For these two origins the
# record is not interpretable without it -- "fix-introduced" with no seed cycle is the
# unclassified blank the ledger warns reads as "new". Other origins MAY carry it
# (measured: 33 of the prototype's 152 do, `author-self-caught` most often, where it
# names the cycle whose fix the author caught themselves) and that is not an error.
BY_CYCLE_REQUIRED = ("fix-introduced", "propagation-gap")

# `caught_by` is optional and only meaningful on `author-self-caught`, where the ledger
# records who saw it. Not enforced: an absent value is "not recorded", which is honest.
CAUGHT_BY = ("self", "advisor", "orchestrator")

REQUIRED_KEYS = ("phase", "cycle", "leg", "item", "origin")


def validate(record: dict) -> list[str]:
    """Return a list of reasons this record is not interpretable. Empty means OK.

    Hard only where a wrong value would silently corrupt an aggregate. `severity`,
    `note` and any future key pass through untouched -- the prototype already carries
    two keys the schema block never mentioned, and rejecting them would have refused
    the very data this instrument was built from.
    """
    reasons = []
    for key in REQUIRED_KEYS:
        if key not in record:
            reasons.append(f"missing:{key}")

    origin = record.get("origin")
    if "origin" in record and origin not in ORIGINS:
        # Named, not summarised: a typo is only fixable if the output says what it was.
        reasons.append(f"unknown-origin:{origin!r}")

    if "cycle" in record and not isinstance(record["cycle"], int):
        reasons.append(f"cycle-not-int:{record['cycle']!r}")

    if origin in BY_CYCLE_REQUIRED and not isinstance(record.get("by_cycle"), int):
        reasons.append(f"by_cycle-required-for-{origin}:{record.get('by_cycle')!r}")

    vbe = record.get("verified_by_execution")
    if vbe is not None and not isinstance(vbe, bool):
        reasons.append(f"verified_by_execution-not-bool:{vbe!r}")

    return reasons


def read_sidecar(path: Path) -> tuple[list[dict], list[tuple[int, str]]]:
    """Return (records, problems). A problem is (line number, reason).

    A line that will not parse is reported with its number and never skipped silently:
    a sidecar that loses records to a bad write would otherwise report a *smaller*
    fix-introduced count, which reads as improvement.
    """
    records: list[dict] = []
    problems: list[tuple[int, str]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError as exc:
            problems.append((lineno, f"unparsable-json:{exc.__class__.__name__}"))
            continue
        if not isinstance(record, dict):
            problems.append((lineno, f"not-an-object:{type(record).__name__}"))
            continue
        for reason in validate(record):
            problems.append((lineno, reason))
        records.append(record)
    return records, problems


def aggregate(records: list[dict]) -> dict:
    """Counts the summary line is built from.

    `accepted` excludes `rejected` on purpose and the output states it: a false finding
    is not a defect, so counting it in the denominator would make a cycle that filed
    noise look like a cycle with a lower fix-introduced share.
    """
    by_origin = collections.Counter(r.get("origin") for r in records)
    rejected = by_origin.get("rejected", 0)
    accepted = len(records) - rejected
    fix_introduced = by_origin.get("fix-introduced", 0)
    self_caught = by_origin.get("author-self-caught", 0)

    per_cycle: dict[int, collections.Counter] = collections.defaultdict(
        collections.Counter)
    for record in records:
        cycle = record.get("cycle")
        if isinstance(cycle, int):
            per_cycle[cycle][record.get("origin")] += 1

    return {
        "n": len(records),
        "accepted": accepted,
        "rejected": rejected,
        "fix_introduced": fix_introduced,
        "self_caught": self_caught,
        "by_origin": by_origin,
        "per_cycle": per_cycle,
        "by_phase": collections.Counter(r.get("phase") for r in records),
        "by_leg": collections.Counter(r.get("leg") for r in records),
    }


def share(count: int, denominator: int) -> str:
    """A share is printed with its denominator or not at all."""
    if denominator <= 0:
        return "n/a"
    return f"{count}/{denominator} ({100.0 * count / denominator:.1f}%)"


def default_sidecar(docs_root: Path, feature: str) -> Path:
    return docs_root / "03-analysis" / f"{feature}.audit-origins.jsonl"


def resolve_sidecar(args: argparse.Namespace) -> Path | None:
    if args.sidecar:
        return args.sidecar
    if args.feature:
        return default_sidecar(args.docs_root, args.feature)
    return None


def cmd_append(args: argparse.Namespace) -> int:
    sidecar = resolve_sidecar(args)
    if sidecar is None:
        print("ORIGINS: UNREADABLE reason=no-sidecar")
        print("  pass --sidecar <path> or --feature <name>; nothing was written.")
        return 2

    record = {
        "phase": args.phase,
        "cycle": args.cycle,
        "leg": args.leg,
        "item": args.item[:args.item_chars],
        "origin": args.origin,
        "by_cycle": args.by_cycle,
        "verified_by_execution": args.verified_by_execution,
    }
    if args.caught_by:
        record["caught_by"] = args.caught_by
    if args.severity:
        record["severity"] = args.severity
    if args.note:
        record["note"] = args.note

    reasons = validate(record)
    if reasons:
        # Refused, not written. A malformed record in the sidecar is worse than a
        # missing one: it is counted by every later summary.
        print(f"ORIGINS: INVALID n=0 reasons={len(reasons)}")
        for reason in reasons:
            print(f"  {reason}")
        print("  nothing was appended.")
        print("[H-MAD] origins INVALID")
        return 1

    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with sidecar.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"ORIGINS: APPENDED cycle={args.cycle} origin={args.origin} "
          f"leg={args.leg} sidecar={sidecar}")
    print("[H-MAD] origins APPENDED")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    sidecar = resolve_sidecar(args)
    if sidecar is None:
        print("ORIGINS: UNREADABLE reason=no-sidecar")
        print("  pass --sidecar <path> or --feature <name>.")
        return 2
    if not sidecar.is_file():
        # Absent and empty are different answers, and only one of them is a measurement.
        print(f"ORIGINS: UNREADABLE reason=absent:{sidecar}")
        print("  no sidecar means NOTHING WAS TAGGED, which is not the same as a "
              "cycle run with no fix-introduced defects. Do not read it as zero.")
        return 2

    try:
        records, problems = read_sidecar(sidecar)
    except OSError as exc:
        print(f"ORIGINS: UNREADABLE reason=os:{exc.__class__.__name__}")
        return 2

    agg = aggregate(records)

    if args.per_cycle:
        for cycle in sorted(agg["per_cycle"]):
            counts = agg["per_cycle"][cycle]
            total = sum(counts.values())
            fixed = counts.get("fix-introduced", 0)
            caught = counts.get("author-self-caught", 0)
            parts = " ".join(f"{origin}={counts[origin]}"
                             for origin in ORIGINS if counts.get(origin))
            print(f"  cycle {cycle}: n={total} fix-introduced={fixed} "
                  f"self-caught={caught} | {parts}")

    if args.cell:
        # The `origins tagged` cell for a ledger table, printed for the OWNING lane to
        # paste. This script never edits another lane's ledger.
        for cycle in sorted(agg["per_cycle"]):
            counts = agg["per_cycle"][cycle]
            cell = ", ".join(f"{counts[origin]} {origin}"
                             for origin in ORIGINS if counts.get(origin))
            print(f"  | {cycle} | {cell} |")

    if problems:
        print(f"ORIGINS: INVALID n={agg['n']} problems={len(problems)} "
              f"fix-introduced={share(agg['fix_introduced'], agg['accepted'])}")
        for lineno, reason in problems[:args.max_problems]:
            print(f"  {sidecar}:{lineno}: {reason}")
        if len(problems) > args.max_problems:
            print(f"  … and {len(problems) - args.max_problems} more")
        print("  the counts above are over the records that DID parse, so they are a "
              "lower bound. Fix the lines named before citing them.")
        print("[H-MAD] origins INVALID")
        return 1

    print(f"ORIGINS: OK n={agg['n']} accepted={agg['accepted']} "
          f"rejected={agg['rejected']} "
          f"fix-introduced={share(agg['fix_introduced'], agg['accepted'])} "
          f"self-caught={share(agg['self_caught'], agg['accepted'])} "
          f"cycles={min(agg['per_cycle'], default=0)}-{max(agg['per_cycle'], default=0)}")
    for origin in ORIGINS:
        if agg["by_origin"].get(origin):
            print(f"  {origin}: {agg['by_origin'][origin]}")
    print("  the fix-introduced denominator EXCLUDES `rejected`: a false finding is not "
          "a defect, and counting it would lower the share of a cycle that filed noise.")
    print("[H-MAD] origins OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tag must-fixes with their origin and measure the "
                    "fix-introduced rate per cycle (H7)")
    parser.add_argument("--docs-root", type=Path, default=Path("docs"))
    parser.add_argument("--feature", help="resolves <docs-root>/03-analysis/"
                                          "<feature>.audit-origins.jsonl")
    parser.add_argument("--sidecar", type=Path, help="explicit sidecar path (wins)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ap = sub.add_parser("append", help="validate and append one must-fix record")
    ap.add_argument("--phase", required=True)
    ap.add_argument("--cycle", type=int, required=True)
    ap.add_argument("--leg", required=True)
    ap.add_argument("--item", required=True)
    ap.add_argument("--origin", required=True,
                    help="one of: " + " · ".join(ORIGINS))
    ap.add_argument("--by-cycle", type=int, default=None, dest="by_cycle",
                    help="the cycle whose fix created this; required for "
                         + "/".join(BY_CYCLE_REQUIRED))
    ap.add_argument("--caught-by", default=None, dest="caught_by",
                    choices=CAUGHT_BY)
    ap.add_argument("--severity", default=None)
    ap.add_argument("--note", default=None)
    ap.add_argument("--item-chars", type=int, default=80, dest="item_chars",
                    help="the ledger's schema truncates item to 80 chars")
    vbe = ap.add_mutually_exclusive_group()
    vbe.add_argument("--verified-by-execution", action="store_true", default=False,
                     dest="verified_by_execution")
    vbe.add_argument("--not-verified-by-execution", action="store_false",
                     dest="verified_by_execution")

    sp = sub.add_parser("summary", help="aggregate the sidecar")
    sp.add_argument("--per-cycle", action="store_true", dest="per_cycle",
                    help="one line per cycle — the trend H7 exists to show")
    sp.add_argument("--cell", action="store_true",
                    help="print the ledger's `origins tagged` cells to paste")
    sp.add_argument("--max-problems", type=int, default=20, dest="max_problems")

    args = parser.parse_args(argv)
    if args.cmd == "append":
        return cmd_append(args)
    return cmd_summary(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
