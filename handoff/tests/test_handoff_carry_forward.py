"""Pins WRITE's obligation to carry the predecessor's open items forward.

The measured failure: a 15-item backlog that a session had explicitly taken over
decayed across 8 consecutive handoffs on one branch -- 9 mentions, then 2, 4, 1,
0, 0, 0, 0 -- and the doc a later READ loaded carried none of it. No hop deleted
15 items; each dropped a few, so a diff of any adjacent pair looked like ordinary
scope change and nothing raised anywhere.

The mechanism is that WRITE had no carry-forward step and no way to acquire one.
Its "Gather context" item 2 reads the **task tool**, which is session-scoped: a
session that never ran READ starts with an empty list, and its WRITE then
truthfully reports no pending todos while dropping everything a prior session
restored. Confirmed live twice -- `TaskList` returned "No tasks found" at the
start of the session that found this defect, and again at the start of the
session that fixed it, while items were nominally owned in both.

Verified before the fix: SKILL.md had ZERO matches for
`predecessor|carry.forward|previous handoff|prior handoff`, and zero for
`supersede` -- while `**Supersedes:**` was in live use in the chain that
truncated. An undefined field was the visible marker of the drop and the skill
could not see it.

The rule these tests pin is one sentence: **an item leaves the chain by being
finished or by being handed over, never by not being mentioned.**
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def _norm(text: str) -> str:
    return " ".join(text.split())


def _section(title: str, until: str) -> str:
    text = SKILL.read_text(encoding="utf-8")
    start = text.index(title)
    return text[start : text.index(until, start)]


class TestWriteHasACarryForwardStep:
    def test_the_skill_names_the_predecessor_at_all(self) -> None:
        """The bare precondition. Before the fix this count was zero -- WRITE had
        no vocabulary for the doc it continues, so it could not be told to read
        one."""
        text = _norm(SKILL.read_text(encoding="utf-8")).lower()
        assert "carry the predecessor" in text

    def test_gather_context_reads_the_predecessor_not_only_the_task_tool(self) -> None:
        """The task tool is session-scoped; the predecessor doc is not. A session
        that never ran READ has an empty list and a full backlog."""
        section = _norm(_section("## Gather context before drafting", "## Required template"))
        assert "predecessor" in section.lower()
        assert "handoff_paths.py" in section or "$HP" in section

    def test_the_rule_is_stated_as_an_obligation_not_a_suggestion(self) -> None:
        text = _norm(SKILL.read_text(encoding="utf-8"))
        assert (
            "An item leaves the chain by being finished or by being handed over, "
            "never by not being mentioned." in text
        )

    def test_an_unresolved_item_must_be_re_emitted_or_closed_with_a_reason(
        self,
    ) -> None:
        """Two exits, both explicit. Silence is not one of them."""
        section = _norm(
            _section(
                "### Carry the predecessor's open items forward",
                "## Writing guidance",
            )
        ).lower()
        assert "re-emit" in section
        assert "reason" in section

    def test_the_step_says_what_to_do_when_the_predecessor_cannot_be_read(
        self,
    ) -> None:
        """Fail closed, like every other gate in this skill: 'I could not read the
        predecessor' and 'the predecessor had no open items' must not take the
        same branch."""
        section = _norm(
            _section(
                "### Carry the predecessor's open items forward",
                "## Writing guidance",
            )
        ).lower()
        assert "could not" in section or "unreadable" in section


class TestSupersedesIsDefined:
    def test_the_field_is_no_longer_unspecified(self) -> None:
        """D3: `grep -c -i supersede SKILL.md` returned 0 while the field was
        truncating a live chain."""
        text = SKILL.read_text(encoding="utf-8").lower()
        assert text.count("supersede") > 0

    def test_the_template_carries_the_field(self) -> None:
        template = _section("## Required template", "## Writing guidance")
        assert "**Supersedes:**" in template

    def test_the_field_table_says_it_is_not_a_licence_to_drop(self) -> None:
        """The whole defect in one line: the field pointed at a predecessor and
        was read as permission to stop repeating it."""
        template = _norm(_section("## Required template", "## Writing guidance"))
        assert "pointer, not a licence to drop" in template

    def test_supersedes_points_at_the_doc_the_carry_forward_step_reads(self) -> None:
        section = _norm(
            _section(
                "### Carry the predecessor's open items forward",
                "## Writing guidance",
            )
        )
        assert "Supersedes:" in section


class TestAStampedBriefIsStillAPredecessor:
    """The hole D1's stamp opens in D2, scoped to exactly the items this whole
    task is about.

    A handover brief is filed under the SENDER's branch slug, so WRITE's
    branch-scoped predecessor lookup cannot see it -- the same construction as
    the READ defect. Sequence that loses it with no error: the taker stamps
    `**Taken-Over-By:**` (which removes the brief from `pending-handovers`),
    restores the todos into the session-scoped task tool, and the session ends
    before writing a handoff. The next session on the branch runs WRITE without
    READ: empty task list, no branch predecessor, so it writes a doc that owes
    nothing -- and nothing re-offers the brief either, because the stamp worked.
    """

    def test_a_stamped_brief_no_handoff_supersedes_is_a_source(
        self, tmp_path: Path
    ) -> None:
        import handoff_paths as hp

        d = tmp_path / "docs" / "handoffs"
        d.mkdir(parents=True)
        (d / "2026-08-30-other__inbound.md").write_text(
            "**Handover-From:** x · y · session a\n**Taken-Over-By:** me · session b\n",
            encoding="utf-8",
        )

        sources, unreadable = hp.carry_forward_sources("feature-41", start=tmp_path)

        assert [p.name for p in sources] == ["2026-08-30-other__inbound.md"]
        assert unreadable == []

    def test_once_a_handoff_supersedes_it_the_chain_owns_it(
        self, tmp_path: Path
    ) -> None:
        """The brief stops being a separate source when a handoff on the branch
        names it -- from then on the ordinary predecessor rule carries it."""
        import handoff_paths as hp

        d = tmp_path / "docs" / "handoffs"
        d.mkdir(parents=True)
        (d / "2026-08-30-other__inbound.md").write_text(
            "**Handover-From:** x · y · session a\n**Taken-Over-By:** me · session b\n",
            encoding="utf-8",
        )
        (d / "2026-09-01-feature-41__mine.md").write_text(
            "**Supersedes:** 2026-08-30-other__inbound.md\n", encoding="utf-8"
        )

        sources, _ = hp.carry_forward_sources("feature-41", start=tmp_path)

        assert [p.name for p in sources] == ["2026-09-01-feature-41__mine.md"]

    def test_the_branch_predecessor_is_still_a_source(self, tmp_path: Path) -> None:
        import handoff_paths as hp

        d = tmp_path / "docs" / "handoffs"
        d.mkdir(parents=True)
        (d / "2026-09-01-feature-41__mine.md").write_text("**Branch:** x\n", encoding="utf-8")

        sources, _ = hp.carry_forward_sources("feature-41", start=tmp_path)

        assert [p.name for p in sources] == ["2026-09-01-feature-41__mine.md"]

    def test_an_unreadable_doc_is_reported_not_treated_as_nothing_owed(
        self, tmp_path: Path
    ) -> None:
        import handoff_paths as hp

        d = tmp_path / "docs" / "handoffs"
        d.mkdir(parents=True)
        (d / "2026-08-31-other__broken.md").write_bytes(b"\xff\xfe\x00")

        _, unreadable = hp.carry_forward_sources("feature-41", start=tmp_path)

        assert [p.name for p in unreadable] == ["2026-08-31-other__broken.md"]

    def test_write_step_2b_uses_the_command(self) -> None:
        section = _norm(
            _section("## Gather context before drafting", "## Required template")
        )
        assert "carry-forward-sources" in section
