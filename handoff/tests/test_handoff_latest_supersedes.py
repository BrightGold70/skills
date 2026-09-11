"""Pins that `find_latest` returns the END of the supersedes chain, not whichever
same-date file the filesystem happened to order last.

THE MEASURED FAILURE (2026-09-11, HemaSuite-wsg clone). A READ resume asked for
`latest --branch feature-18-gateway-consolidation` and got
`2026-09-09-…__tasks-19-20-shipped-21-retired-22-at-5e.md`. That doc is TWO HOPS
stale: `…__task22-shipped-t23-rescoped.md` supersedes it, and
`…__phase5-complete-t23-t24-t25.md` supersedes that. The resume therefore loaded
a document describing work (Task 22 "at 5e, uncommitted") that had since shipped,
and would have restored todos for tasks already closed.

WHY THE OLD TIE-BREAK COULD NOT WORK. `sorted_handoffs` orders same-date files by
mtime, on the reasoning that a same-day concurrency discriminant (`…-2.md`) sorts
lexically BEFORE the file it follows. That reasoning holds for files written by
successive sessions. It does not hold for files written by git: a clone, a
checkout or a merge materialises every file it touches inside the same instant,
in INDEX order, which is alphabetical. All four gateway docs above carried mtime
`2026-09-10 18:10:30` from one merge and were separated by ~0.1 ms in filename
order -- so mtime had stopped being a recency signal and was silently
re-encoding the filename sort. Any repo with two same-day handoffs on a branch is
exposed the moment it is cloned or merged.

THE FIX is to stop inferring recency and read the order the documents themselves
declare. `**Supersedes:**` is already parsed here for `carry_forward_sources`;
`find_latest` now skips any file another handoff retires.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import handoff_paths as hp  # noqa: E402


def doc(branch: str, supersedes: str = "none") -> str:
    return f"# Handoff\n\n**Branch:** `{branch}`\n**Supersedes:** {supersedes}\n"


def store(
    tmp_path: Path, files: dict[str, str], ages: dict[str, int] | None = None
) -> Path:
    """Write a store, optionally stamping each file's mtime.

    `ages` maps filename -> seconds OLD. Every test that cares about ordering
    passes it, and passes ages that CONTRADICT the supersedes chain -- the chain
    head is stamped oldest. That is the point: the pre-fix implementation
    tie-breaks on mtime, so contradicting ages force it to a deterministic wrong
    answer, and the test discriminates.

    Stamping identical mtimes instead does NOT discriminate. Equal keys leave
    Python's stable sort echoing the glob's own order, which is readdir order and
    therefore arbitrary -- the first draft of these tests did that and passed
    against the reverted implementation by luck of directory layout.
    """
    d = tmp_path / "docs" / "handoffs"
    d.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (d / name).write_text(text, encoding="utf-8")
    now = time.time()
    for name, age in (ages or {}).items():
        os.utime(d / name, (now - age, now - age))
    return d


BR = "feature-18"
A = f"2026-09-09-{BR}__aaa-oldest.md"
B = f"2026-09-09-{BR}__mmm-middle.md"
C = f"2026-09-09-{BR}__zzz-newest.md"


class TestSupersedesDecidesAmongSameDateFiles:
    def test_the_chain_head_wins_when_mtime_says_it_is_the_oldest(
        self, tmp_path: Path
    ) -> None:
        """A -> B -> C, with mtimes stamped in the OPPOSITE order to the chain.

        This is the real shape: git materialised all three in one instant in an
        order unrelated to when the sessions actually wrote them, so the newest
        document carries the oldest stamp. mtime therefore names B (or A), and
        only the chain names C.
        """
        store(
            tmp_path,
            {A: doc(BR), B: doc(BR, A), C: doc(BR, B)},
            ages={A: 100, B: 50, C: 900},
        )
        # The trap is armed: the pre-fix key would pick B.
        assert hp.sorted_handoffs(BR, start=tmp_path)[-1].name == B
        latest = hp.find_latest(BR, start=tmp_path)
        assert latest is not None and latest.name == C

    def test_it_walks_back_past_MORE_THAN_ONE_retired_doc(
        self, tmp_path: Path
    ) -> None:
        """The measured case was TWO hops stale, so one hop of skipping is not enough."""
        store(
            tmp_path,
            {A: doc(BR), B: doc(BR, A), C: doc(BR, B)},
            ages={A: 10, B: 20, C: 900},
        )
        # Both A and B outrank C on mtime, and both are retired.
        assert [p.name for p in hp.sorted_handoffs(BR, start=tmp_path)] == [C, B, A]
        assert hp.find_latest(BR, start=tmp_path).name == C

    def test_a_doc_retired_by_another_BRANCH_is_still_retired(
        self, tmp_path: Path
    ) -> None:
        """A `main` closeout absorbing a feature lane's last doc is the common shape.

        The retirement scan must cover the whole store; a branch-scoped scan
        cannot see the doc doing the retiring, so the retired doc would win.
        """
        early = f"2026-09-09-{BR}__feature-early.md"
        feature_last = f"2026-09-09-{BR}__feature-final.md"
        main_doc = "2026-09-10-main__absorbed-the-lane.md"
        store(
            tmp_path,
            {
                early: doc(BR),
                feature_last: doc(BR, early),
                main_doc: doc("main", feature_last),
            },
            ages={early: 900, feature_last: 10, main_doc: 800},
        )
        # Repo-wide: the main doc wins on DATE, the primary key, despite its
        # older mtime -- so the date rule is still in force.
        assert hp.find_latest(None, start=tmp_path).name == main_doc
        # Branch-filtered: every candidate on BR is retired -- `early` by
        # `feature_last`, and `feature_last` by a doc on ANOTHER branch, which a
        # branch-scoped retirement scan could not have seen. The fallback returns
        # the last rather than None: a store with handoffs never answers "none".
        assert hp.find_latest(BR, start=tmp_path) is not None


class TestTheFallbacksStayHonest:
    def test_an_empty_store_is_still_none(self, tmp_path: Path) -> None:
        store(tmp_path, {})
        assert hp.find_latest(None, start=tmp_path) is None

    def test_a_supersedes_cycle_does_not_empty_the_store(self, tmp_path: Path) -> None:
        """Corruption must degrade to the old answer, never to 'no handoffs exist'."""
        store(tmp_path, {A: doc(BR, C), C: doc(BR, A)}, ages={A: 100, C: 50})
        assert hp.find_latest(BR, start=tmp_path) is not None

    def test_an_unreadable_file_retires_nothing_and_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """The claim is that the scan survives undecodable bytes -- NOT an ordering.

        Asserting which file wins here is what broke the first draft: the binary
        file is unretired, so whether it or C is returned is decided purely by
        mtime, and pinning that would test the stamp rather than the fix.
        """
        store(tmp_path, {A: doc(BR), C: doc(BR, A)}, ages={A: 10, C: 900})
        binary = tmp_path / "docs" / "handoffs" / f"2026-09-09-{BR}__binary.md"
        binary.write_bytes(b"\xff\xfe\x00garbage")
        os.utime(binary, (time.time() - 5000, time.time() - 5000))
        latest = hp.find_latest(BR, start=tmp_path)
        # No exception, and A -- the one thing that IS retired -- is still refused,
        # even though its mtime makes it the newest of the three.
        assert latest is not None and latest.name != A

    def test_the_unretired_newest_is_unaffected(self, tmp_path: Path) -> None:
        """The ordinary case -- nothing supersedes anything -- must not change."""
        store(tmp_path, {A: doc(BR), C: doc(BR)}, ages={A: 900, C: 10})
        assert hp.find_latest(BR, start=tmp_path).name == C

    def test_date_still_outranks_the_chain(self, tmp_path: Path) -> None:
        """A later DATE wins even though the older file heads a chain.

        Guards against the fix quietly promoting `Supersedes` to the primary key.
        """
        early = f"2026-09-09-{BR}__early.md"
        older_head = f"2026-09-09-{BR}__heads-a-chain.md"
        next_day = f"2026-09-10-{BR}__next-day.md"
        store(
            tmp_path,
            {early: doc(BR), older_head: doc(BR, early), next_day: doc(BR)},
            ages={early: 900, older_head: 10, next_day: 800},
        )
        assert hp.find_latest(BR, start=tmp_path).name == next_day
