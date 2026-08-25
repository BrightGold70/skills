"""Tests for `h_mad_version_history.py`.

The helper's whole value is the refusals, so most of these assert that a write
did NOT happen and that the reason was named. But a guard that refuses
everything kills every mutant and protects nothing, so the accept cases are
first-class here: `TestAccepts` proves a clean ascending bump actually lands,
lands in the right place, and lands exactly once.

The fixtures are verbatim corpus sections (see `fixtures/vh-*.md` headers), not
tidy ASCII. They carry the em-dashes, `↔`/`×`/`⇒`, backticked identifiers and
`v2.0/v1.0: superseded.` shorthand that real phase docs carry, because a tidy
fixture cannot fail the way the real corpus fails.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
REFERENCES = Path(__file__).resolve().parents[1] / "references"
sys.path.insert(0, str(SCRIPTS))

from h_mad_version_history import (  # noqa: E402
    Refusal,
    bump,
    classify_order,
    plan_insertion,
)

SCRIPT = SCRIPTS / "h_mad_version_history.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def stage(tmp_path: Path, fixture: str) -> Path:
    """Copy a fixture into a temp dir so a write cannot touch the checkout."""
    target = tmp_path / fixture
    target.write_text((FIXTURES / fixture).read_text())
    return target


def section_bullets(path: Path) -> list[str]:
    lines = path.read_text().split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.strip().lower() == "## version history")
    return [ln for ln in lines[start + 1:] if ln.startswith("- ")]


class TestAccepts:
    """The guard must let the good case through, not merely reject bad ones."""

    def test_ascending_section_gets_the_entry_at_the_end(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        before = section_bullets(doc)
        result = bump(doc, "v1.3", "Audit v3 fixes.")
        after = section_bullets(doc)

        assert result["placement"] == "append"
        assert after[:-1] == before
        assert after[-1] == "- v1.3: Audit v3 fixes."

    def test_descending_section_gets_the_entry_at_the_top(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-descending.md")
        before = section_bullets(doc)
        result = bump(doc, "v3.4", "Adds the thing.")
        after = section_bullets(doc)

        assert result["placement"] == "prepend"
        assert after[1:] == before
        assert after[0] == "- v3.4: Adds the thing."

    def test_the_rest_of_the_document_is_untouched(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        before = doc.read_text().split("\n")
        bump(doc, "v1.3", "Audit v3 fixes.")
        after = doc.read_text().split("\n")

        assert len(after) == len(before) + 1
        inserted = next(i for i, ln in enumerate(after) if ln.startswith("- v1.3:"))
        assert after[:inserted] + after[inserted + 1:] == before

    def test_an_empty_section_accepts_the_first_entry(self, tmp_path: Path) -> None:
        doc = tmp_path / "empty.md"
        doc.write_text("# Doc\n\n## Version History\n")
        bump(doc, "v1.0", "Initial draft.")
        assert section_bullets(doc) == ["- v1.0: Initial draft."]

    def test_dry_run_verifies_without_writing(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        before = doc.read_text()
        result = bump(doc, "v1.3", "Audit v3 fixes.", dry_run=True)

        assert result["placement"] == "append"
        assert doc.read_text() == before

    def test_a_rule_terminated_section_appends_above_the_rule(self, tmp_path: Path) -> None:
        """14 corpus sections end at `---` rather than at EOF or a header.

        The trailing content here is a BULLET list on purpose. With prose
        after the rule this test cannot discriminate: dropping the `---`
        terminator finds no further bullets, so the insertion point is
        unchanged and the mutant survives while looking covered. Measured
        over 2132 files, no real section has bullets after its rule -- so the
        fixture has to supply the case the corpus does not.
        """
        doc = tmp_path / "ruled.md"
        doc.write_text("## Version History\n- v1.0: First.\n\n---\n\n- Unrelated list item.\n")
        bump(doc, "v1.1", "Second.")
        lines = doc.read_text().split("\n")

        assert lines.index("- v1.1: Second.") < lines.index("---")
        assert lines.index("- Unrelated list item.") > lines.index("---")

    def test_a_header_terminated_section_appends_above_the_header(self, tmp_path: Path) -> None:
        doc = tmp_path / "headed.md"
        doc.write_text("## Version History\n- v1.0: First.\n\n## Next Steps\n\n- Do it.\n")
        bump(doc, "v1.1", "Second.")
        lines = doc.read_text().split("\n")

        assert lines.index("- v1.1: Second.") < lines.index("## Next Steps")
        assert "- Do it." in lines


class TestAnchorRefusals:
    """The drifted anchor is the silent no-op this script exists to end."""

    def test_a_missing_section_refuses(self, tmp_path: Path) -> None:
        doc = tmp_path / "no-section.md"
        doc.write_text("# Doc\n\n## Overview\n\nNothing here.\n")
        with pytest.raises(Refusal) as exc:
            bump(doc, "v1.0", "Anything.")
        assert exc.value.reason == "anchor_missing"

    def test_a_missing_section_writes_nothing(self, tmp_path: Path) -> None:
        doc = tmp_path / "no-section.md"
        doc.write_text("# Doc\n\n## Overview\n\nNothing here.\n")
        before = doc.read_text()
        with pytest.raises(Refusal):
            bump(doc, "v1.0", "Anything.")
        assert doc.read_text() == before

    def test_two_headers_refuse_rather_than_taking_the_first(self) -> None:
        doc = (
            "## Version History\n- v1.0: Template example.\n\n"
            "## Overview\n\nProse.\n\n"
            "## Version History\n- v2.0: The live log.\n"
        )
        with pytest.raises(Refusal) as exc:
            plan_insertion(doc, "v2.1", "Should never land.")
        assert exc.value.reason == "anchor_ambiguous"
        assert exc.value.detail == "matches=2"

    def test_indented_template_headers_are_not_live_sections(self) -> None:
        """`references/inline-protocols.md` carries 7 `## Version History`
        lines, and every one is indented inside a fenced protocol example.

        Measured 2026-08-25 over 2132 files: under the strict `^##` anchor no
        file in the corpus has more than one match, and 711 have exactly one.
        A looser anchor that stripped leading whitespace would find seven here
        and refuse a doc that is not actually ambiguous -- so this pins the
        strictness, not just the count.
        """
        source = REFERENCES / "inline-protocols.md"
        assert source.exists(), "the multi-header reference doc moved"
        text = source.read_text()
        assert text.count("## Version History") >= 7, "fixture premise moved"

        # The one unindented header is a real section, so this parses cleanly.
        _, _, placement = plan_insertion(text, "v9.9", "Probe only, never written.")
        assert placement in {"append", "prepend"}


class TestShapeRefusals:
    def test_a_table_section_refuses_rather_than_being_reformatted(
        self, tmp_path: Path
    ) -> None:
        doc = stage(tmp_path, "vh-table.md")
        before = doc.read_text()
        with pytest.raises(Refusal) as exc:
            bump(doc, "v0.2", "Phase 1.")
        assert exc.value.reason == "table_shape"
        assert doc.read_text() == before

    def test_an_unrecognised_shape_refuses(self, tmp_path: Path) -> None:
        doc = tmp_path / "prose.md"
        doc.write_text("## Version History\n\nThis doc has never been versioned.\n")
        with pytest.raises(Refusal) as exc:
            bump(doc, "v1.0", "Anything.")
        assert exc.value.reason == "unknown_shape"


class TestOrderRefusals:
    def test_the_real_unsorted_section_refuses(self, tmp_path: Path) -> None:
        """26 of 246 multi-entry corpus sections are unsorted.

        Appending blind puts v1.3 after v1.1 in a section reading 1.0/1.2/1.1,
        which is wrong in a way no assertion on the write itself can see.
        """
        doc = stage(tmp_path, "vh-mixed-order.md")
        before = doc.read_text()
        with pytest.raises(Refusal) as exc:
            bump(doc, "v1.3", "Audit v3 fixes.")
        assert exc.value.reason == "mixed_order"
        assert doc.read_text() == before

    @pytest.mark.parametrize(
        "versions,expected",
        [
            ([(1, 0), (1, 1), (1, 2)], "ascending"),
            ([(3, 3), (3, 2), (2, 0)], "descending"),
            ([(1, 0)], "ascending"),
            ([], "ascending"),
            ([(1, 0), (1, 0)], "ascending"),
            ([(1, 9), (1, 10)], "ascending"),
        ],
    )
    def test_order_classification(self, versions, expected) -> None:
        assert classify_order(versions) == expected

    def test_ten_sorts_after_nine_not_before(self, tmp_path: Path) -> None:
        """String comparison would call v1.10 < v1.9 and read the section as unsorted."""
        doc = tmp_path / "tens.md"
        doc.write_text("## Version History\n- v1.9: Nine.\n- v1.10: Ten.\n")
        result = bump(doc, "v1.11", "Eleven.")
        assert result["placement"] == "append"


class TestDuplicateRefusal:
    def test_the_same_version_twice_refuses(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        with pytest.raises(Refusal) as exc:
            bump(doc, "v1.2", "Re-run of the same cycle.")
        assert exc.value.reason == "duplicate_version"

    def test_a_re_run_cannot_append_twice(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        bump(doc, "v1.3", "Audit v3 fixes.")
        after_first = doc.read_text()
        with pytest.raises(Refusal):
            bump(doc, "v1.3", "Audit v3 fixes.")
        assert doc.read_text() == after_first


class TestArgumentRefusals:
    @pytest.mark.parametrize("version", ["1.3", "v1", "v1.3.1", "va.b", "", "v1.3 "])
    def test_a_malformed_version_refuses(self, tmp_path: Path, version: str) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        with pytest.raises(Refusal) as exc:
            bump(doc, version, "Anything.")
        assert exc.value.reason == "bad_version"

    def test_empty_text_refuses(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        with pytest.raises(Refusal) as exc:
            bump(doc, "v1.3", "   ")
        assert exc.value.reason == "empty_text"

    def test_multiline_text_refuses(self, tmp_path: Path) -> None:
        """A newline in the body would silently create a second list item."""
        doc = stage(tmp_path, "vh-ascending.md")
        with pytest.raises(Refusal) as exc:
            bump(doc, "v1.3", "First line.\n- v1.4: smuggled.")
        assert exc.value.reason == "multiline_text"

    def test_an_unreadable_path_refuses(self, tmp_path: Path) -> None:
        with pytest.raises(Refusal) as exc:
            bump(tmp_path / "absent.md", "v1.0", "Anything.")
        assert exc.value.reason == "unreadable"


class TestCli:
    def test_a_clean_bump_prints_ok_and_exits_zero(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        proc = run_cli(str(doc), "--version", "v1.3", "--text", "Audit v3 fixes.")

        assert proc.returncode == 0
        assert "VERSION-HISTORY: OK" in proc.stdout
        assert "version=v1.3" in proc.stdout
        assert "placement=append" in proc.stdout

    def test_a_refusal_exits_two_and_names_the_reason(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-mixed-order.md")
        proc = run_cli(str(doc), "--version", "v1.3", "--text", "Audit v3 fixes.")

        assert proc.returncode == 2
        assert "VERSION-HISTORY: REFUSED" in proc.stdout
        assert "reason=mixed_order" in proc.stdout

    def test_a_refusal_carries_no_line_number(self, tmp_path: Path) -> None:
        """A cannot-write must not be readable as a write that landed."""
        doc = stage(tmp_path, "vh-table.md")
        proc = run_cli(str(doc), "--version", "v0.2", "--text", "Phase 1.")

        assert proc.returncode == 2
        assert "line=" not in proc.stdout

    def test_unreadable_prints_its_own_verdict(self, tmp_path: Path) -> None:
        proc = run_cli(str(tmp_path / "absent.md"), "--version", "v1.0", "--text", "X.")

        assert proc.returncode == 2
        assert "VERSION-HISTORY: UNREADABLE" in proc.stdout
        assert "line=" not in proc.stdout

    def test_dry_run_prints_its_own_verb(self, tmp_path: Path) -> None:
        doc = stage(tmp_path, "vh-ascending.md")
        before = doc.read_text()
        proc = run_cli(str(doc), "--version", "v1.3", "--text", "X.", "--dry-run")

        assert proc.returncode == 0
        assert "VERSION-HISTORY: DRY-RUN" in proc.stdout
        assert doc.read_text() == before


class TestDocsPin:
    """Bidirectional: the token in the script must be the token in SKILL.md."""

    def test_the_token_is_registered_in_skill_md(self) -> None:
        skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text()
        assert "h_mad_version_history.py" in skill
        assert "VERSION-HISTORY: OK" in skill

    def test_every_refusal_reason_is_documented(self) -> None:
        script = SCRIPT.read_text()
        skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text()
        reasons = set(re.findall(r'Refusal\("([a-z_]+)"', script))
        assert reasons, "no refusal reasons found in the script"
        undocumented = sorted(r for r in reasons if r not in skill)
        assert not undocumented, f"undocumented refusal reasons: {undocumented}"
