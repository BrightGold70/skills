import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
INLINE_PROTOCOLS = REPO_ROOT / "h-mad" / "references" / "inline-protocols.md"

sys.path.insert(0, str(SCRIPT_DIR))

# Single-sourced from the checker (`invariants.base.md` §"Single-source
# verdicts"). A second hardcoded copy here would be free to drift from both the
# checker and the live validator while every test stayed green — and it had
# already drifted: the local trigger list was missing the lowercase `plan-plus`
# literal, which the external check tests case-sensitively as a distinct string.
# `test_h_mad_doc_shape_check.py::TestMirrorFidelity` holds the imported tables
# to the live validator.
from h_mad_doc_shape_check import (  # noqa: E402
    PLAN_PLUS_TRIGGERS as TRIGGER_LITERALS,
    REQUIRED_SECTIONS as BKIT_REQUIRED,
)

VALIDATOR = (
    Path.home()
    / ".claude"
    / "plugins"
    / "marketplaces"
    / "bkit-marketplace"
    / "lib"
    / "pdca"
    / "template-validator.js"
)

PHASE_TYPES = {
    "1": "brainstorm",
    "2": "spec",
    "3": "plan",
    "4": "design",
    "5a": "impl-plan",
    "6": "analysis",
    "7": "report",
}


PRIOR_HMAD_HEADINGS = {
    "plan": [
        "Overview",
        "Goals",
        "Implementation Strategy",
        "Deliverables",
        "Risks",
        "Success Criteria",
        "Out-of-Scope",
    ],
    "design": [
        "Architecture Overview",
        "Components Changed / Added",
        "Data Model / Schema Changes",
        "API / Interface Changes",
        "Error Handling Strategy",
        "Test Strategy",
        "Invariant Compliance",
    ],
    "report": [
        "Summary",
        "Metrics",
        "What Went Well",
        "What To Improve Next Time",
        "Carry Items",
    ],
}


def _phase_segment(text: str, phase: str) -> str:
    pattern = rf"^## Phase {re.escape(phase)}\b.*?(?=^## Phase |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    assert match, f"missing Phase {phase} section"
    return match.group(0)


def _first_template_block(segment: str) -> str:
    match = re.search(
        r"^\s*(?P<fence>`{3,4})markdown\s*\n(?P<body>.*?)(?m:^\s*(?P=fence)\s*$)",
        segment,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match, "missing first markdown template block"
    return match.group("body")


def _template_blocks() -> dict[str, str]:
    text = INLINE_PROTOCOLS.read_text(encoding="utf-8")
    return {
        doc_type: _first_template_block(_phase_segment(text, phase))
        for phase, doc_type in PHASE_TYPES.items()
    }


def _headings(block: str) -> list[str]:
    headings = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            headings.append(stripped.removeprefix("##").strip())
    return headings


def _has_heading_substring(headings: list[str], expected: str) -> bool:
    expected_lower = expected.lower()
    return any(expected_lower in heading.lower() for heading in headings)


@pytest.mark.parametrize("doc_type", ["plan", "design", "report"])
def test_bkit_validated_templates_have_required_superset_headings(doc_type: str) -> None:
    headings = _headings(_template_blocks()[doc_type])

    for required in BKIT_REQUIRED[doc_type]:
        assert _has_heading_substring(headings, required), (
            f"{doc_type} template missing bkit heading containing {required!r}"
        )

    for prior in PRIOR_HMAD_HEADINGS[doc_type]:
        assert _has_heading_substring(headings, prior), (
            f"{doc_type} template dropped prior H-MAD heading containing {prior!r}"
        )


def test_template_blocks_do_not_contain_plan_plus_trigger_literals() -> None:
    for doc_type, block in _template_blocks().items():
        for literal in TRIGGER_LITERALS:
            assert literal not in block, f"{doc_type} template contains trigger literal {literal!r}"


@pytest.mark.parametrize(
    ("doc_type", "relative_path"),
    [
        ("plan", "docs/01-plan/features/example.plan.md"),
        ("design", "docs/02-design/features/example.design.md"),
        ("report", "docs/04-report/features/example.report.md"),
    ],
)
def test_bkit_validator_accepts_plan_design_report_templates(
    tmp_path: Path, doc_type: str, relative_path: str
) -> None:
    if not shutil.which("node"):
        pytest.skip("node is unavailable")
    if not VALIDATOR.is_file():
        pytest.skip("bkit template validator is unavailable")

    doc_path = tmp_path / relative_path
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    content = "# Example\n\n" + "\n\n".join(
        f"## {heading}\nPlaceholder." for heading in _headings(_template_blocks()[doc_type])
    )
    doc_path.write_text(content, encoding="utf-8")

    script = "\n".join(
        [
            f"const validator = require({json.dumps(str(VALIDATOR))});",
            f"const fs = require('fs');",
            f"const filePath = {json.dumps(str(doc_path))};",
            "const result = validator.validateDocument(filePath, fs.readFileSync(filePath, 'utf8'));",
            "if (!result.valid) { console.error(JSON.stringify(result)); process.exit(1); }",
        ]
    )
    result = subprocess.run(
        ["node", "-e", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
