#!/usr/bin/env python3
"""h_mad_doc_shape_check.py — verify a generated phase document's shape.

`invariants.base.md` §"Doc-template superset compliance" makes it a violation for
an h-mad-generated plan/design/report to fail the external doc-structure
validator it is a superset of (today: bkit PDCA `lib/pdca/template-validator.js`).
The templates in `references/inline-protocols.md` satisfy that contract, and
`tests/test_h_mad_doc_templates.py` holds them to it — but the *authored body* of
a real document is not the template, and it can break compliance two ways:

1.  A section gets dropped, renamed, or demoted below `##` while drafting.
2.  The body mentions a **plan-plus escalation literal**. The external validator
    reclassifies a `plan` as `plan-plus` on a *substring of the content*, which
    demands a strictly larger section list the h-mad plan template does not carry.
    A plan documenting this very coexistence is exactly the document that trips
    it — the literals are unremarkable prose.

This check is the guard for both, and it is **standalone**: the tables below are
h-mad's own copy, so the check runs with no other plugin installed
(§"Standalone / no plugin dependency"). Mirroring an external contract is the
"verdict computed in more than one place" hazard §"Single-source verdicts" names,
so the mirror is not trusted on inspection: `test_h_mad_doc_shape_check.py`
diffs every table *and* the escalation literals against the live validator source
when it is present, and fails on drift.

Signalling follows the house pattern (the Thrust-A lesson): the verdict is an
explicit stdout token and a computed verdict exits 0, so a legitimate FAIL is not
reported by the harness as a tool error. Exit 2 is reserved for an operational
error — an unreadable path, which is what a typo'd argument looks like.

Usage:
    h_mad_doc_shape_check.py <doc-path> [<doc-path> ...]

Output, one line per path:
    DOC-SHAPE: PASS path=<p> type=<plan|design|report|prd>
    DOC-SHAPE: FAIL path=<p> type=<t> missing=<a,b> triggers=<x,y>
    DOC-SHAPE: SKIP path=<p> type=none

SKIP is a real verdict, not a failure: h-mad's brainstorm, spec, impl-plan and
audit documents are deliberately outside the external validator's detection, so
they have no superset contract to meet.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- Mirror of the external validator's contract -----------------------------
# Kept in declaration order so a drift diff against the live source is a plain
# list comparison rather than a set comparison that would hide a reordering.

REQUIRED_SECTIONS: dict[str, list[str]] = {
    "plan": [
        "Executive Summary",
        "Overview",
        "Scope",
        "Requirements",
        "Success Criteria",
        "Risks and Mitigation",
        "Architecture Considerations",
        "Convention Prerequisites",
        "Next Steps",
        "Version History",
    ],
    "plan-plus": [
        "Executive Summary",
        "User Intent Discovery",
        "Alternatives Explored",
        "YAGNI Review",
        "Scope",
        "Requirements",
        "Success Criteria",
        "Risks and Mitigation",
        "Architecture Considerations",
        "Convention Prerequisites",
        "Next Steps",
        "Brainstorming Log",
        "Version History",
    ],
    "design": [
        "Executive Summary",
        "Overview",
        "Architecture",
        "Detailed Design",
        "Implementation Order",
        "Test Plan",
        "Version History",
    ],
    "report": [
        "Executive Summary",
        "Version History",
    ],
    "prd": [
        "Executive Summary",
        "Opportunity Discovery",
        "Value Proposition",
        "Market Research",
        "Go-To-Market",
        "Product Requirements",
        "Attribution",
    ],
}

# The validator tests these with JavaScript `String.prototype.includes`, which is
# case-SENSITIVE. `plan-plus` and `Plan-Plus` are therefore two distinct triggers
# and both must be listed; `plan plus` and `intent discovery` are not triggers at
# all. Matching must stay exact-literal — lowercasing either side here would
# reject prose the external validator accepts.
PLAN_PLUS_TRIGGERS: list[str] = [
    "Plan-Plus",
    "Plan Plus",
    "plan-plus",
    "Brainstorming-Enhanced",
    "Intent Discovery",
]

# `(docs-path fragment, filename fragment, type)`, matched as substrings in this
# order — the validator uses `includes`, not a directory equality test, so a
# document under `docs/01-plan/features/` is detected just as one directly under
# `docs/01-plan/` is.
_DETECTION_RULES: list[tuple[str, str, str]] = [
    ("docs/00-pm/", ".prd.md", "prd"),
    ("docs/01-plan/", ".plan.md", "plan"),
    ("docs/02-design/", ".design.md", "design"),
    ("docs/04-report/", ".report.md", "report"),
]

# `## ` headings, tolerating a leading section number ("## 3.1 Scope").
_SECTION_RE = re.compile(r"^##\s+(?:\d+[\.\d]*\s+)?(.+)$", re.MULTILINE)


def detect_doc_type(file_path: str) -> str | None:
    """The document type an external validator would assign, or None."""
    path = str(file_path).replace("\\", "/")
    if not path.endswith(".md"):
        return None
    for dir_fragment, name_fragment, doc_type in _DETECTION_RULES:
        if dir_fragment in path and name_fragment in path:
            return doc_type
    return None


def extract_sections(content: str) -> list[str]:
    return [match.group(1).strip() for match in _SECTION_RE.finditer(content)]


def found_plan_plus_triggers(content: str) -> list[str]:
    """Escalation literals present in `content`, in declaration order."""
    return [trigger for trigger in PLAN_PLUS_TRIGGERS if trigger in content]


def missing_sections(doc_type: str, content: str) -> list[str]:
    """Required sections with no `##` heading containing them, case-insensitively."""
    actual = [heading.lower() for heading in extract_sections(content)]
    return [
        required
        for required in REQUIRED_SECTIONS.get(doc_type, [])
        if not any(required.lower() in heading for heading in actual)
    ]


def check_document(file_path: str, content: str) -> dict:
    """Verdict for one document.

    A `plan` whose body carries an escalation literal is reported as FAIL against
    its *unescalated* type rather than re-scored against `plan-plus`: the h-mad
    template cannot satisfy plan-plus, so the actionable defect is the literal,
    and naming it beats listing the three extra sections it demands.
    """
    doc_type = detect_doc_type(file_path)
    if doc_type is None:
        return {"path": file_path, "type": None, "verdict": "SKIP",
                "missing": [], "triggers": []}

    triggers = found_plan_plus_triggers(content) if doc_type == "plan" else []
    missing = missing_sections(doc_type, content)
    verdict = "FAIL" if (missing or triggers) else "PASS"
    return {"path": file_path, "type": doc_type, "verdict": verdict,
            "missing": missing, "triggers": triggers}


def format_result(result: dict) -> str:
    if result["verdict"] == "SKIP":
        return f"DOC-SHAPE: SKIP path={result['path']} type=none"
    line = f"DOC-SHAPE: {result['verdict']} path={result['path']} type={result['type']}"
    if result["verdict"] == "PASS":
        return line
    return (
        f"{line} missing={','.join(result['missing']) or '-'}"
        f" triggers={','.join(result['triggers']) or '-'}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated phase documents against the doc-superset contract.",
    )
    parser.add_argument("paths", nargs="+", help="document paths to check")
    args = parser.parse_args(argv)

    # Read every path before emitting a verdict: an unreadable path is an
    # operational error, and half a verdict stream is worse than none.
    documents: list[tuple[str, str]] = []
    for raw in args.paths:
        path = Path(raw)
        try:
            documents.append((raw, path.read_text(encoding="utf-8")))
        except OSError as exc:
            print(f"h_mad_doc_shape_check: cannot read {raw}: {exc}", file=sys.stderr)
            return 2

    for raw, content in documents:
        print(format_result(check_document(raw, content)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
