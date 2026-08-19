"""The census tool exists because three hand-written counts of this backlog were
wrong, so its own counting is what needs pinning.

Each fixture below is one trap that produced a real miscount, and each is written
so a naive counter gets a *different* number than the correct one — a fixture both
readings agree on would prove nothing.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skill_candidates_census.py"


def run(path: Path) -> str:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        capture_output=True, text=True, check=False,
    )
    assert r.returncode == 0, f"census failed: {r.stderr}"
    return r.stdout


def counts(out: str) -> dict[str, int]:
    line = out.splitlines()[0]
    d = {k: int(v) for k, v in re.findall(r"(\w+)=\s*(\d+)", line)}
    d["OPEN"] = int(re.search(r"OPEN\(yes\+maybe\)=\s*(\d+)", line).group(1))
    return d


def write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "skill-candidates.md"
    p.write_text("# Skill Candidates\n\n" + body, encoding="utf-8")
    return p


def test_no_arguments_refuses_instead_of_reporting_zero() -> None:
    # The tool's own instance of the class it measures: invoked wrong, it must not
    # print a clean zero census.
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode != 0
    assert "usage:" in (r.stderr + r.stdout)


@pytest.mark.parametrize(
    "row, expect_open, why",
    [
        (
            "- **a**: short row — candidate: yes\n",
            1,
            "the ordinary same-line case must still count",
        ),
        (
            "- **a**: a description long enough to wrap\n  onto a second line — candidate: yes\n",
            1,
            "a verdict on a continuation line is what a single-line grep misses",
        ),
        (
            "- **a**: done elsewhere — candidate: **SUPERSEDED** — `exec`\n",
            0,
            "the replacing convention closes the row",
        ),
        (
            "- **a**: still says yes — candidate: yes — **SUPERSEDED** — `exec`\n",
            0,
            "the APPENDING convention also closes it; a terminal marker outranks "
            "the candidate value or every mass-stamped row reads as open",
        ),
        (
            "- **a**: scout said no — candidate: no\n",
            0,
            "`no` is a verdict already given, not an undecided row",
        ),
        (
            "- **a** (recurrence, not a new row): seen again — candidate: yes\n",
            0,
            "a bump is a note on an existing row; counting it inflates the total",
        ),
        (
            "- **a** (no new recurrence): nothing this session\n",
            0,
            "a bump with no verdict at all is correct, not a hole to stamp",
        ),
        (
            "- **a** *(existing row, recurrence bumped)*: still candidate: yes in prose\n",
            0,
            "PROSE saying 'candidate: yes' inside a bump is exactly what scored a "
            "phantom third open row on 2026-08-20",
        ),
        (
            "- **a** (row ~354) — re-proved later\n",
            0,
            "a back-reference points at another row and is not itself a candidate",
        ),
        (
            "- **a** *(still open; partially eased — see note)*: candidate: yes\n",
            1,
            "a parenthetical that is NOT a bump marker must not be swallowed — "
            "over-excluding is the same defect facing the other way",
        ),
    ],
)
def test_one_row_one_trap(tmp_path: Path, row: str, expect_open: int, why: str) -> None:
    c = counts(run(write(tmp_path, row)))
    assert c["OPEN"] == expect_open, f"{why}\nrow: {row!r}\ngot: {c}"


def test_bump_rows_are_listed_so_the_exclusion_is_auditable(tmp_path: Path) -> None:
    # A silent exclusion is indistinguishable from a row that was never there.
    out = run(write(tmp_path, "- **a** (recurrence, not a new row): seen again\n"))
    assert "BUMP ROWS EXCLUDED (1)" in out
    assert "a" in out.split("BUMP ROWS EXCLUDED")[1]


def test_mixed_store_totals(tmp_path: Path) -> None:
    # All traps at once: 6 `- **` lines, 2 of them bumps, 1 closed by an appended
    # marker, 1 `no`. A row-count reads 6, a naive yes-grep reads 3; open is 2.
    p = write(tmp_path, "".join([
        "- **a**: wraps to the next line\n  — candidate: yes\n",
        "- **b**: candidate: maybe\n",
        "- **c**: candidate: yes — **SUPERSEDED** — `exec`\n",
        "- **d**: candidate: no\n",
        "- **a** (recurrence, not a new row): still candidate: yes in prose\n",
        "- **c** (row ~3) — re-proved\n",
    ]))
    c = counts(run(p))
    assert c["candidates"] == 4, f"bumps must not be candidates: {c}"
    assert c["OPEN"] == 2, f"open is a(yes) + b(maybe) only: {c}"
    assert c["no"] == 1 and c["SUPERSEDED"] == 1, c
    assert c.get("verdict", c.get("verdict-less", 0)) == 0
