"""Tests for `h_mad_doc_shape_check.py`.

Two jobs. The first is the ordinary one: the checker computes the verdict h-mad
needs (missing superset sections, plan-plus escalation literals) and signals it
the way the house pattern requires.

The second is the reason the checker is allowed to exist at all. It is a Python
mirror of an external JavaScript contract, which is precisely the "verdict
computed in more than one place" hazard `invariants.base.md` §"Single-source
verdicts" names. The mitigation is that the mirror is never trusted on
inspection: when the live bkit validator is installed, `TestMirrorFidelity`
diffs the section tables, the escalation literals, and the *verdicts themselves*
over a corpus, and fails on any drift. Those tests skip when the validator is
absent — a skip, never a silent pass, because §"Standalone / no plugin
dependency" forbids requiring it at runtime.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
MODULE_PATH = SCRIPT_DIR / "h_mad_doc_shape_check.py"

sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_doc_shape_check import (  # noqa: E402
    PLAN_PLUS_TRIGGERS,
    REQUIRED_SECTIONS,
    check_document,
    detect_doc_type,
    extract_sections,
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


def run_check(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), *[str(p) for p in paths]],
        check=False,
        capture_output=True,
        text=True,
    )


def compliant(doc_type: str, extra_body: str = "") -> str:
    body = "\n\n".join(f"## {section}\nPlaceholder." for section in REQUIRED_SECTIONS[doc_type])
    return f"# Example\n\n{body}\n\n{extra_body}"


def write_doc(tmp_path: Path, relative: str, content: str) -> Path:
    doc = tmp_path / relative
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(content, encoding="utf-8")
    return doc


class TestDetection:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("docs/01-plan/features/x.plan.md", "plan"),
            ("docs/01-plan/x.plan.md", "plan"),
            ("docs/02-design/features/x.design.md", "design"),
            ("docs/04-report/features/x.report.md", "report"),
            ("docs/00-pm/x.prd.md", "prd"),
        ],
    )
    def test_validated_paths_are_detected(self, path: str, expected: str) -> None:
        assert detect_doc_type(path) == expected

    @pytest.mark.parametrize(
        "path",
        [
            # The four h-mad document shapes that deliberately escape detection.
            "docs/01-plan/features/x-brainstorm.md",
            "docs/01-plan/features/x.spec.md",
            "docs/01-plan/features/x.impl-plan.md",
            "docs/01-plan/features/x.plan.audit.v1.md",
            # Right filename, wrong directory — the validator needs both.
            "docs/notes/x.plan.md",
            "notes.txt",
        ],
    )
    def test_unvalidated_paths_are_not_detected(self, path: str) -> None:
        assert detect_doc_type(path) is None

    def test_impl_plan_is_not_mistaken_for_a_plan(self) -> None:
        """`.impl-plan.md` contains `-plan.md`, not `.plan.md`."""
        assert detect_doc_type("docs/01-plan/features/x.impl-plan.md") is None


class TestSectionExtraction:
    def test_numbered_headings_are_accepted(self) -> None:
        assert extract_sections("## 3.1 Scope\n") == ["Scope"]

    def test_other_heading_levels_are_ignored(self) -> None:
        assert extract_sections("# Scope\n### Scope\n") == []


class TestVerdicts:
    def test_compliant_plan_passes(self) -> None:
        result = check_document("docs/01-plan/features/x.plan.md", compliant("plan"))
        assert result["verdict"] == "PASS"

    def test_missing_section_fails_and_is_named(self) -> None:
        content = compliant("plan").replace("## Convention Prerequisites", "## Conventions")
        result = check_document("docs/01-plan/features/x.plan.md", content)
        assert result["verdict"] == "FAIL"
        assert result["missing"] == ["Convention Prerequisites"]

    def test_undetected_path_skips(self) -> None:
        result = check_document("docs/01-plan/features/x.spec.md", "# nothing here\n")
        assert result["verdict"] == "SKIP"
        assert result["type"] is None

    @pytest.mark.parametrize("trigger", PLAN_PLUS_TRIGGERS)
    def test_each_escalation_literal_fails_an_otherwise_compliant_plan(self, trigger: str) -> None:
        content = compliant("plan", extra_body=f"Prose mentioning {trigger} in passing.")
        result = check_document("docs/01-plan/features/x.plan.md", content)
        assert result["verdict"] == "FAIL", f"{trigger!r} did not escalate"
        assert result["triggers"] == [trigger]

    @pytest.mark.parametrize("near_miss", ["plan plus", "intent discovery", "PLAN-PLUS"])
    def test_case_variants_that_are_not_triggers_do_not_fail(self, near_miss: str) -> None:
        """The external check is case-sensitive; over-matching would reject valid prose."""
        content = compliant("plan", extra_body=f"Prose mentioning {near_miss} in passing.")
        assert check_document("docs/01-plan/features/x.plan.md", content)["verdict"] == "PASS"

    @pytest.mark.parametrize("doc_type", ["design", "report"])
    def test_escalation_literals_only_apply_to_plans(self, doc_type: str) -> None:
        """`isPlanPlus` refines `plan` only — a design may discuss the literals freely."""
        content = compliant(doc_type, extra_body="Discussion of Plan-Plus and Intent Discovery.")
        path = f"docs/0{'2' if doc_type == 'design' else '4'}-{doc_type}/features/x.{doc_type}.md"
        assert check_document(path, content)["verdict"] == "PASS"


class TestCli:
    def test_fail_exits_zero_with_a_verdict_token(self, tmp_path: Path) -> None:
        """A legitimate FAIL must not read as a tool error (the Thrust-A lesson)."""
        doc = write_doc(tmp_path, "docs/01-plan/features/x.plan.md", "# Empty\n")
        result = run_check(doc)
        assert result.returncode == 0, result.stderr
        assert result.stdout.startswith("DOC-SHAPE: FAIL ")

    def test_pass_exits_zero(self, tmp_path: Path) -> None:
        doc = write_doc(tmp_path, "docs/01-plan/features/x.plan.md", compliant("plan"))
        result = run_check(doc)
        assert result.returncode == 0, result.stderr
        assert "DOC-SHAPE: PASS " in result.stdout

    def test_unreadable_path_is_an_operational_error(self, tmp_path: Path) -> None:
        result = run_check(tmp_path / "docs/01-plan/features/absent.plan.md")
        assert result.returncode == 2
        assert "DOC-SHAPE:" not in result.stdout

    def test_one_unreadable_path_emits_no_partial_verdict_stream(self, tmp_path: Path) -> None:
        good = write_doc(tmp_path, "docs/01-plan/features/a.plan.md", compliant("plan"))
        result = run_check(good, tmp_path / "docs/01-plan/features/absent.plan.md")
        assert result.returncode == 2
        assert result.stdout == ""

    def test_every_path_gets_a_line(self, tmp_path: Path) -> None:
        a = write_doc(tmp_path, "docs/01-plan/features/a.plan.md", compliant("plan"))
        b = write_doc(tmp_path, "docs/01-plan/features/b.spec.md", "# spec\n")
        result = run_check(a, b)
        assert result.returncode == 0, result.stderr
        assert len([ln for ln in result.stdout.splitlines() if ln.startswith("DOC-SHAPE:")]) == 2


# --- Mirror fidelity ---------------------------------------------------------


def _require_validator() -> None:
    if not shutil.which("node"):
        pytest.skip("node is unavailable")
    if not VALIDATOR.is_file():
        pytest.skip("bkit template validator is unavailable")


def _live_required_sections() -> dict[str, list[str]]:
    script = (
        f"const v = require({json.dumps(str(VALIDATOR))});"
        "process.stdout.write(JSON.stringify(v.REQUIRED_SECTIONS));"
    )
    out = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def _live_trigger_literals() -> list[str]:
    """The literals `isPlanPlus` tests, read from the validator source.

    Read from source rather than probed with a fixed list on purpose: a probe can
    only confirm the literals we already know, so it cannot see bkit adding a
    sixth one — which is the drift that would silently escalate an h-mad plan.
    """
    source = VALIDATOR.read_text(encoding="utf-8")
    body = re.search(r"function isPlanPlus\s*\([^)]*\)\s*\{(.*?)\n\}", source, re.DOTALL)
    assert body, "could not locate isPlanPlus in the validator source"
    return re.findall(r"content\.includes\(\s*'([^']*)'\s*\)", body.group(1))


def _live_verdict(doc_path: Path) -> dict:
    script = "\n".join(
        [
            f"const v = require({json.dumps(str(VALIDATOR))});",
            "const fs = require('fs');",
            f"const p = {json.dumps(str(doc_path))};",
            "process.stdout.write(JSON.stringify(v.validateDocument(p, fs.readFileSync(p, 'utf8'))));",
        ]
    )
    out = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


class TestMirrorFidelity:
    @pytest.mark.parametrize("doc_type", sorted(REQUIRED_SECTIONS))
    def test_required_sections_match_the_live_validator(self, doc_type: str) -> None:
        _require_validator()
        live = _live_required_sections()
        assert doc_type in live, f"{doc_type} no longer exists in the live validator"
        assert REQUIRED_SECTIONS[doc_type] == live[doc_type], (
            f"the {doc_type} section table drifted from the live validator; update "
            "h_mad_doc_shape_check.py AND the inline-protocols template together"
        )

    def test_no_live_document_type_is_unmirrored(self) -> None:
        _require_validator()
        assert set(_live_required_sections()) == set(REQUIRED_SECTIONS)

    def test_escalation_literals_match_the_live_validator(self) -> None:
        _require_validator()
        assert sorted(PLAN_PLUS_TRIGGERS) == sorted(_live_trigger_literals())


    @pytest.mark.parametrize(
        ("relative", "content_key"),
        [
            ("docs/01-plan/features/x.plan.md", "plan-compliant"),
            ("docs/01-plan/features/x.plan.md", "plan-missing"),
            ("docs/01-plan/features/x.plan.md", "plan-near-miss"),
            ("docs/02-design/features/x.design.md", "design-compliant"),
            ("docs/02-design/features/x.design.md", "design-missing"),
            ("docs/04-report/features/x.report.md", "report-compliant"),
            ("docs/01-plan/features/x.spec.md", "undetected"),
            ("docs/01-plan/features/x.impl-plan.md", "undetected"),
            ("docs/01-plan/features/x.plan.audit.v1.md", "undetected"),
        ],
    )
    def test_verdicts_agree_with_the_live_validator(
        self, tmp_path: Path, relative: str, content_key: str
    ) -> None:
        """Differential test: table equality alone would miss detection or regex drift."""
        _require_validator()
        contents = {
            "plan-compliant": compliant("plan"),
            "plan-missing": compliant("plan").replace("## Next Steps", "## Follow-ups"),
            "plan-near-miss": compliant("plan", "Prose mentioning plan plus in passing."),
            "design-compliant": compliant("design"),
            "design-missing": compliant("design").replace("## Test Plan", "## Testing"),
            "report-compliant": compliant("report"),
            "undetected": "# Not a validated document\n\n## Whatever\n",
        }
        doc = write_doc(tmp_path, relative, contents[content_key])

        live = _live_verdict(doc)
        mine = check_document(str(doc), contents[content_key])

        assert (mine["type"] is None) == (live["type"] is None), (
            f"detection diverged for {relative}: mine={mine['type']} live={live['type']}"
        )
        if live["type"] is None:
            assert mine["verdict"] == "SKIP"
            return
        assert mine["type"] == live["type"]
        assert (mine["verdict"] == "PASS") == live["valid"], (
            f"verdict diverged for {content_key}: mine={mine['verdict']} live={live}"
        )
        assert mine["missing"] == live["missing"]

    def test_an_escalating_plan_is_rejected_by_both(self, tmp_path: Path) -> None:
        """The one case where the two disagree by design, pinned so it stays deliberate.

        The live validator re-scores the document as `plan-plus` and reports the
        three extra sections as missing; this checker keeps the type `plan` and
        reports the literal instead. Both say "not valid" — only the explanation
        differs, and naming the literal is the actionable one.
        """
        _require_validator()
        content = compliant("plan", "Prose mentioning Plan-Plus in passing.")
        doc = write_doc(tmp_path, "docs/01-plan/features/x.plan.md", content)

        live = _live_verdict(doc)
        mine = check_document(str(doc), content)

        assert live["type"] == "plan-plus" and live["valid"] is False
        assert mine["type"] == "plan" and mine["verdict"] == "FAIL"
        assert mine["triggers"] == ["Plan-Plus"]

def test_escalation_literals_are_pinned_without_the_validator() -> None:
    """The portable half of the trigger guard.

    Every other check on this list needs the external validator installed and
    skips without it — so on a validator-less machine, silently dropping a
    literal (which is how the lowercase `plan-plus` went missing from the old
    hardcoded copy in `test_h_mad_doc_templates.py`) removes a parametrize case
    and leaves the suite green. This pin is not a second source of truth: when
    the literals legitimately change, `TestMirrorFidelity` fires first and this
    assertion is updated to match, loudly.
    """
    assert set(PLAN_PLUS_TRIGGERS) == {
        "Plan-Plus",
        "Plan Plus",
        "plan-plus",
        "Brainstorming-Enhanced",
        "Intent Discovery",
    }
