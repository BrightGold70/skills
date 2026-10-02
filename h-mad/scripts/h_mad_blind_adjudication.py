#!/usr/bin/env python3
"""Blinded adjudication set with positive AND negative controls.

When one lane's verdicts contradict another's, the question is not "who is
right" but "does this lane over-call?". Mix the disputed calls with known
positives and known negatives, shuffle, blind, and hand the payload to
independent readers; keep the key aside. Negative controls coming back clean
exonerate the METHOD; positives recovered show the reader can see a real
call; only then does the disputed tally mean anything.

    build  --corpus C.jsonl --disputed a,b --positives p,q --negatives n,m
           --seed N --out DIR [--strip FIELD ...]
        -> DIR/payload.jsonl  (shuffled, re-keyed item-001.., no id, no tag)
        -> DIR/key.json       {item: {orig_id, tag}}

    score  --key DIR/key.json --verdicts V.jsonl
        verdict rows: {"item": "item-001", "verdict": "upheld" | "rejected"}
        prints  disputed upheld=a/b
                positives recovered=c/d
                negatives clean=e/f
                ADJUDICATION: VALID | CONTROLS-FAILED | INCOMPLETE

Stdlib only. Exit 0 only on VALID.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

TAGS = ("disputed", "positive", "negative")
VERDICTS = ("upheld", "rejected")


def _ids(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


def _refuse(msg: str) -> int:
    print(f"REFUSED: {msg}", file=sys.stderr)
    return 2


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{n}: row is not a JSON object")
        rows.append(row)
    return rows


def cmd_build(args: argparse.Namespace) -> int:
    lists = {
        "disputed": _ids(args.disputed),
        "positive": _ids(args.positives),
        "negative": _ids(args.negatives),
    }
    if not lists["disputed"]:
        return _refuse("--disputed is empty")
    if not lists["positive"]:
        return _refuse("--positives is empty: positive controls are mandatory")
    if not lists["negative"]:
        return _refuse("--negatives is empty: negative controls are mandatory")

    tag_of: dict[str, str] = {}
    for tag in TAGS:
        for oid in lists[tag]:
            if oid in tag_of:
                return _refuse(f"id {oid!r} appears in both {tag_of[oid]} and {tag}")
            tag_of[oid] = tag

    try:
        corpus = _load_jsonl(Path(args.corpus))
    except (OSError, ValueError) as exc:
        return _refuse(f"cannot read corpus: {exc}")
    by_id: dict[str, dict] = {}
    for row in corpus:
        if "id" in row:
            by_id[str(row["id"])] = row
    missing = [oid for oid in tag_of if oid not in by_id]
    if missing:
        return _refuse(f"ids not in corpus: {', '.join(missing)}")

    order = [oid for tag in TAGS for oid in lists[tag]]
    random.Random(args.seed).shuffle(order)

    strip = {"id", "tag", *(args.strip or [])}
    width = max(3, len(str(len(order))))
    payload, key = [], {}
    for n, oid in enumerate(order, 1):
        item = f"item-{n:0{width}d}"
        row = {"item": item}
        row.update({k: v for k, v in by_id[oid].items() if k not in strip})
        payload.append(row)
        key[item] = {"orig_id": oid, "tag": tag_of[oid]}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "payload.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in payload),
        encoding="utf-8")
    (out / "key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    counts = " ".join(f"{t}={len(lists[t])}" for t in TAGS)
    print(f"BUILT: items={len(order)} {counts} seed={args.seed} out={out}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    try:
        key = json.loads(Path(args.key).read_text(encoding="utf-8"))
        rows = _load_jsonl(Path(args.verdicts))
    except (OSError, ValueError) as exc:
        print(f"ADJUDICATION: INCOMPLETE reason=unreadable: {exc}")
        return 1

    problems: list[str] = []
    verdict: dict[str, str] = {}
    for row in rows:
        item, v = row.get("item"), row.get("verdict")
        if item not in key:
            problems.append(f"verdict for unknown item {item!r}")
        elif v not in VERDICTS:
            problems.append(f"item {item}: verdict {v!r} not in {'|'.join(VERDICTS)}")
        elif item in verdict and verdict[item] != v:
            problems.append(f"item {item}: conflicting verdicts")
        else:
            verdict[item] = v
    for item in key:
        if item not in verdict:
            problems.append(f"no verdict for {item}")

    tally = {t: [0, 0] for t in TAGS}
    for item, entry in key.items():
        tag = entry["tag"]
        if tag not in tally:
            problems.append(f"key item {item}: unknown tag {tag!r}")
            continue
        tally[tag][1] += 1
        v = verdict.get(item)
        if tag == "negative":
            hit = v == "rejected"
        else:
            hit = v == "upheld"
        tally[tag][0] += int(hit)

    print(f"disputed upheld={tally['disputed'][0]}/{tally['disputed'][1]}")
    print(f"positives recovered={tally['positive'][0]}/{tally['positive'][1]}")
    print(f"negatives clean={tally['negative'][0]}/{tally['negative'][1]}")
    for p in problems:
        print(f"  problem: {p}")
    if problems:
        print("ADJUDICATION: INCOMPLETE")
        return 1
    pos_ok = tally["positive"][0] == tally["positive"][1]
    neg_ok = tally["negative"][0] == tally["negative"][1]
    if pos_ok and neg_ok:
        print("ADJUDICATION: VALID")
        return 0
    print("ADJUDICATION: CONTROLS-FAILED")
    return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="emit a blinded payload and its key")
    b.add_argument("--corpus", required=True, help="JSONL; each row an object with an 'id'")
    b.add_argument("--disputed", required=True, help="comma-separated ids under dispute")
    b.add_argument("--positives", required=True, help="comma-separated known positives (mandatory)")
    b.add_argument("--negatives", required=True, help="comma-separated known negatives (mandatory)")
    b.add_argument("--seed", required=True, type=int, help="shuffle seed")
    b.add_argument("--out", required=True, help="output directory")
    b.add_argument("--strip", action="append", default=[],
                   help="extra field to drop from payload rows (repeatable); 'id' and 'tag' always go")
    b.set_defaults(func=cmd_build)

    s = sub.add_parser(
        "score", help="score reader verdicts against the key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Verdict rows are JSONL: {\"item\": \"item-001\", \"verdict\": V}\n"
            "  V = upheld   the reader says the call stands (a real finding)\n"
            "  V = rejected the reader says the call does not stand\n"
            "A positive is recovered when upheld; a negative is clean when rejected.\n"
            "VALID needs every positive recovered AND every negative clean.\n"
            "A key item with no verdict, a verdict for an unknown item, or any\n"
            "other verdict word -> ADJUDICATION: INCOMPLETE (fail closed)."
        ))
    s.add_argument("--key", required=True, help="key.json from build")
    s.add_argument("--verdicts", required=True, help="reader verdicts JSONL")
    s.set_defaults(func=cmd_score)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
