"""Pins the locator for inbound handovers that READ check 2 can never reach.

READ Step 1 checks the branch's own newest handoff (check 2) before the repo-wide
newest (check 3), and check 3 is the only place that knows about
`**Handover-From:**`. It is gated "Use when this branch has none", so a branch
that HAS its own handoff -- the common case -- never reaches the exception. The
remedy for an inbound-handover bug had been placed in the branch that only runs
when the other branch fails.

Reproduced live 2026-09-01 on /Users/kimhawk/orca/HemaSuite (on
feature/41-headless-nlm-auth-gating): `latest --branch feature-41-…` and bare
`latest` return the SAME file, and 9 briefs in that store carry
`**Handover-From:**` with none of them reachable.

So the scan runs IN ADDITION to check 2, and needs a way to tell a brief that was
already taken over from one that was not. The two markers that exist today both
fail at this: the `taken over:` worktree comment is worktree-scoped, and the
advisory claim lives in a gitignored, machine-local `.bkit-memory.json`. Neither
travels with the doc, and the doc store is what the locator reads. The marker is
therefore written INTO the brief -- `**Taken-Over-By:**`, stamped by Step 3.5.

Fail-closed throughout: a file that cannot be read is an UNREADABLE report and a
non-zero exit, never an absence. "I could not check" and "there is nothing" must
not take the same branch -- that asymmetry is the whole subject of this defect.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import handoff_paths as hp  # noqa: E402


HANDOVER = "# Brief\n\n**Handover-From:** other-repo · other-branch · session abc\n"
TAKEN = HANDOVER + "**Taken-Over-By:** skills · session def · 2026-09-01\n"
PLAIN = "# Brief\n\n**Branch:** main\n\nOrdinary session handoff.\n"


def store(tmp_path: Path, files: dict[str, str]) -> Path:
    d = tmp_path / "docs" / "handoffs"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (d / name).write_text(text, encoding="utf-8")
    return d


class TestPendingHandoversAreFound:
    def test_an_unstamped_brief_is_pending(self, tmp_path: Path) -> None:
        store(tmp_path, {"2026-08-30-other__inbound.md": HANDOVER})

        pending, unreadable = hp.pending_handovers(start=tmp_path)

        assert [p.name for p in pending] == ["2026-08-30-other__inbound.md"]
        assert unreadable == []

    def test_a_stamped_brief_is_not_pending(self, tmp_path: Path) -> None:
        store(tmp_path, {"2026-08-30-other__inbound.md": TAKEN})

        assert hp.pending_handovers(start=tmp_path) == ([], [])

    def test_an_ordinary_handoff_is_not_a_handover(self, tmp_path: Path) -> None:
        store(tmp_path, {"2026-08-30-main__ordinary.md": PLAIN})

        assert hp.pending_handovers(start=tmp_path) == ([], [])

    def test_a_branch_with_its_own_handoff_still_sees_the_inbound_brief(
        self, tmp_path: Path
    ) -> None:
        """The defect itself: check 2 hits, so check 3 never runs. This scan is
        not a fallback to check 2 and must not be shadowed by it."""
        store(
            tmp_path,
            {
                "2026-08-30-other__inbound.md": HANDOVER,
                "2026-09-01-feature-41__own-work.md": PLAIN,
            },
        )

        assert hp.find_latest("feature-41", start=tmp_path) is not None
        assert [p.name for p in hp.pending_handovers(start=tmp_path)[0]] == [
            "2026-08-30-other__inbound.md"
        ]

    def test_oldest_first_so_the_longest_dropped_brief_surfaces_first(
        self, tmp_path: Path
    ) -> None:
        store(
            tmp_path,
            {
                "2026-09-01-b__later.md": HANDOVER,
                "2026-08-03-a__earlier.md": HANDOVER,
            },
        )

        pending, _ = hp.pending_handovers(start=tmp_path)

        assert [p.name for p in pending] == [
            "2026-08-03-a__earlier.md",
            "2026-09-01-b__later.md",
        ]

    def test_the_marker_must_be_the_bolded_field_not_a_mention(
        self, tmp_path: Path
    ) -> None:
        """Briefs discuss handovers in prose constantly -- this very repo's do.
        Matching a bare mention would make every retrospective a pending queue."""
        store(
            tmp_path,
            {
                "2026-08-30-main__prose.md": (
                    "# Brief\n\nWe discussed Handover-From: semantics at length.\n"
                ),
            },
        )

        assert hp.pending_handovers(start=tmp_path) == ([], [])

    def test_a_missing_store_is_empty_not_an_error(self, tmp_path: Path) -> None:
        assert hp.pending_handovers(start=tmp_path) == ([], [])


class TestAnUnreadableBriefIsNotAnAbsence:
    def test_undecodable_bytes_are_reported_not_skipped(self, tmp_path: Path) -> None:
        d = store(tmp_path, {"2026-08-30-other__inbound.md": HANDOVER})
        (d / "2026-08-31-other__broken.md").write_bytes(b"\xff\xfe\x00 not utf-8")

        pending, unreadable = hp.pending_handovers(start=tmp_path)

        assert [p.name for p in pending] == ["2026-08-30-other__inbound.md"]
        assert [p.name for p in unreadable] == ["2026-08-31-other__broken.md"]


class TestTheCLIContract:
    def _run(self, tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "handoff_paths.py"), *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

    def test_pending_handovers_prints_one_path_per_line(self, tmp_path: Path) -> None:
        store(tmp_path, {"2026-08-30-other__inbound.md": HANDOVER})

        result = self._run(tmp_path, "pending-handovers")

        assert result.returncode == 0
        assert result.stdout.strip().endswith("2026-08-30-other__inbound.md")

    def test_no_pending_handovers_exits_1_like_latest(self, tmp_path: Path) -> None:
        """Same contract as `latest`: nothing found is exit 1 with empty stdout,
        which a caller can distinguish from the exit 2 below."""
        store(tmp_path, {"2026-08-30-main__ordinary.md": PLAIN})

        result = self._run(tmp_path, "pending-handovers")

        assert result.returncode == 1
        assert result.stdout.strip() == ""

    def test_an_unreadable_brief_exits_2_and_names_the_file(
        self, tmp_path: Path
    ) -> None:
        """The fail-closed rung. Exit 2 says 'I could not check', which must never
        be read as 'there is nothing to take over'."""
        d = store(tmp_path, {"2026-08-30-main__ordinary.md": PLAIN})
        (d / "2026-08-31-other__broken.md").write_bytes(b"\xff\xfe\x00")

        result = self._run(tmp_path, "pending-handovers")

        assert result.returncode == 2
        assert "UNREADABLE:" in result.stderr
        assert "2026-08-31-other__broken.md" in result.stderr

    def test_unreadable_does_not_suppress_the_briefs_that_did_read(
        self, tmp_path: Path
    ) -> None:
        d = store(tmp_path, {"2026-08-30-other__inbound.md": HANDOVER})
        (d / "2026-08-31-other__broken.md").write_bytes(b"\xff\xfe\x00")

        result = self._run(tmp_path, "pending-handovers")

        assert result.returncode == 2
        assert "2026-08-30-other__inbound.md" in result.stdout
        assert "UNREADABLE:" in result.stderr


class TestTheSkillDocumentsTheMechanism:
    SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"

    def test_step_1_runs_the_scan_in_addition_to_check_2(self) -> None:
        text = self.SKILL.read_text(encoding="utf-8")
        assert "pending-handovers" in text
        # The gate that made the old exception unreachable must be gone from the
        # Handover-From path -- a reachable remedy is the entire fix.
        locate = text[text.index("### Step 1: Locate the doc") :]
        locate = locate[: locate.index("### Step 2: Read it")]
        assert "pending-handovers" in locate
        assert "in addition to" in locate.lower()

    def test_step_3_5_stamps_the_marker_the_scan_filters_on(self) -> None:
        text = self.SKILL.read_text(encoding="utf-8")
        step = text[text.index("### Step 3.5: Take over handed-over work") :]
        step = step[: step.index("### Step 3.6")]
        assert "**Taken-Over-By:**" in step

    def test_the_marker_is_defined_in_the_template(self) -> None:
        """The defect this repo also carries as D3: an undefined field doing
        load-bearing work. A marker the locator filters on must be specified."""
        text = self.SKILL.read_text(encoding="utf-8")
        assert "Taken-Over-By" in text[text.index("## Required template") :]
