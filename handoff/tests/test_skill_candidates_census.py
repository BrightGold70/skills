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


# --- the J registry (`docs/skill-monitoring.md`) ---------------------------
#
# The failure these pin is worse than a miscount. This script read a 1946-line
# registry carrying 46 entries as `candidates=3 OPEN=0` -- not an error, not an
# empty result, but a CLEAN backlog, which is the one answer nothing prompts you
# to re-check. `rows()` ends a row on any line starting with `|`, and that file
# is full of pipe tables.

MONITORING_HEADER = """# Skill Monitoring — bugs & improvement points (standing)

**Lifecycle** — every `J` entry ends with exactly one machine-readable status line.

| word | meaning |
|---|---|
| `MONITORING` | tracked, still unfixed — the only word that means open work |
| `PLANNED` | scheduled, not yet started |
| `FIXED` | remedied in code |

## Entries
"""


def monitoring(tmp_path: Path, body: str) -> Path:
    target = tmp_path / "skill-monitoring.md"
    target.write_text(MONITORING_HEADER + body, encoding="utf-8")
    return target


def test_a_pipe_table_registry_is_no_longer_read_as_three_candidates(tmp_path: Path) -> None:
    """The regression. A summary pipe table must not eat the entries below it."""
    path = monitoring(tmp_path, """
| J | sev | status |
|---|---|---|
| J1 | 🔴 | **FIXED** |

- 🔴 **J1 — a real entry.** Body. Status: `FIXED`
- 🟡 **J2 — another.** Body. Status: `MONITORING`
""")
    out = run(path)
    assert "J-entries=    2" in out, out
    assert "OPEN(MONITORING+PLANNED)=   1" in out, out
    assert "candidates=" not in out.split("COVERAGE")[0], "must not be read as a candidate store"


def test_monitoring_is_the_word_that_means_open(tmp_path: Path) -> None:
    path = monitoring(tmp_path, """
- 🔴 **J1 — fixed one.** Status: `FIXED`
- 🟡 **J2 — open one.** Status: `MONITORING`
- 🟢 **J3 — scheduled.** Status: `PLANNED`
""")
    out = run(path)
    assert "OPEN(MONITORING+PLANNED)=   2" in out, out


def test_the_status_is_read_not_inferred_from_severity(tmp_path: Path) -> None:
    """The leading emoji is SEVERITY. A red entry can be fixed."""
    path = monitoring(tmp_path, "- 🔴 **J1 — red but done.** Status: `FIXED`\n")
    out = run(path)
    assert "FIXED=1" in out
    assert "OPEN(MONITORING+PLANNED)=   0" in out


def test_prose_containing_a_status_word_does_not_decide_an_entry(tmp_path: Path) -> None:
    """A census once reported J18 open because a note after it said MONITORING.

    Two backticked statuses in one entry is a quotation, not a verdict, so the
    reader refuses to pick rather than taking the first.
    """
    path = monitoring(tmp_path, """
- 🔴 **J1 — done, with a note.** Status: `FIXED`

  Note: see the `MONITORING` lifecycle word, quoted here as Status: `MONITORING`.
""")
    out = run(path)
    assert "OPEN(MONITORING+PLANNED)=   0" in out, out
    assert "no single machine-readable status" in out, out


def test_an_undocumented_status_word_is_flagged(tmp_path: Path) -> None:
    """Used-vs-documented is diffed against the file's OWN vocabulary table."""
    path = monitoring(tmp_path, "- 🔴 **J1 — invented word.** Status: `MOSTLYFIXED`\n")
    out = run(path)
    assert "used but NOT documented" in out
    assert "MOSTLYFIXED" in out


# --- the coverage line: what the count did NOT read ------------------------


def test_coverage_flags_an_entry_shape_the_reader_missed(tmp_path: Path) -> None:
    """The generalisable guard. The bug was never "pipe tables are unsupported",
    it was "an unsupported shape reads as an empty backlog"."""
    path = monitoring(tmp_path, """
- 🔴 **J1 — parsed normally.** Status: `FIXED`
- 🟡 **J2 : written with a colon instead of a dash.** Status: `FIXED`
""")
    out = run(path)
    assert "ROW-SHAPED LINES NOT PARSED" in out, out


def test_coverage_does_not_cry_wolf_on_the_deliberate_numbering_gaps(
    tmp_path: Path
) -> None:
    """This file's own header discusses the deliberate J31-J33 gaps.

    Measuring coverage against J-ids mentioned ANYWHERE reported three phantom
    misses on the real file — the self-pollution failure in reverse. A guard
    that fires on the header is worse than no guard.
    """
    path = monitoring(tmp_path, """
Numbering gaps (J31–J33) are deliberate and must stay; J32 is referenced from commits.

- 🔴 **J1 — the only entry.** Status: `FIXED`
""")
    out = run(path)
    assert "ROW-SHAPED LINES NOT PARSED" not in out, out
    assert "deliberate gaps): J31, J32, J33" in out, out


def test_a_monitoring_only_run_prints_no_candidates_total(tmp_path: Path) -> None:
    """`TOTAL candidates=0` for a J registry is the same false-clean shape."""
    path = monitoring(tmp_path, "- 🔴 **J1 — one.** Status: `FIXED`\n")
    out = run(path)
    assert "TOTAL candidates=" not in out, out


def test_a_candidate_store_still_reports_its_coverage(tmp_path: Path) -> None:
    path = tmp_path / "skill-candidates.md"
    path.write_text("- **a**: x — candidate: yes\n", encoding="utf-8")
    out = run(path)
    assert "COVERAGE" in out
    assert "skill-candidates.md: parsed=1 row-shaped=1" in out, out


def test_routing_needs_both_the_title_and_a_j_row(tmp_path: Path) -> None:
    """A candidates file that merely mentions a J-id must not route to the J reader."""
    path = tmp_path / "skill-candidates.md"
    # The discriminating case is not a J-id MENTION -- that never matched the J
    # row shape anyway, so an earlier version of this test passed with the title
    # check deleted. It is a candidates store QUOTING a J entry verbatim, which
    # this backlog does. Without the title check that file routes to the J
    # reader and every real candidate row disappears.
    path.write_text(
        "- **a**: relates to J1 — candidate: yes\n"
        "- 🔴 **J1 — quoted verbatim from the monitoring registry.** Status: `FIXED`\n",
        encoding="utf-8")
    out = run(path)
    assert "J-entries=" not in out, out
    assert "OPEN(yes+maybe)=   1" in out, out


# --- surfaced by an adversarial review of the shipped fix -------------------


def test_a_bold_closed_id_is_still_an_entry(tmp_path: Path) -> None:
    """`- 🔴 **J1** — title` is as real as `- 🔴 **J1 — title`.

    Seven entries in the real file use the bold-closed shape.
    """
    path = monitoring(tmp_path, "- 🔴 **J1** — closed bold. Status: `MONITORING`\n")
    out = run(path)
    assert "J-entries=    1" in out, out
    assert "OPEN(MONITORING+PLANNED)=   1" in out, out


def test_coverage_counts_entries_of_any_prefix_not_just_j(tmp_path: Path) -> None:
    """Hardcoding `J` in the denominator rigs the guard to hide its own gap.

    The real file carries 33 F/G/H/A/V/P finding rows beside its 46 J entries.
    They are not the standing registry and carry no `Status:` line, so they are
    not open work — but a coverage line that filters them out of its own
    denominator reports clean while dropping them, which is the guard covering
    up exactly what it exists to expose.
    """
    path = monitoring(tmp_path, """
- 🔴 **J1 — a real entry.** Status: `FIXED`
- 🔴 **F1 — a finding row from some review.** No status line.
- 🟡 **G2** — another shape entirely.
""")
    out = run(path)
    assert "parsed=1 row-shaped=3" in out, out
    assert "2 ROW-SHAPED LINES NOT PARSED" in out, out


def test_routing_survives_a_blank_first_line(tmp_path: Path) -> None:
    """Pinning the title to line 0 sends the registry to the CANDIDATE reader.

    It then hits the pipe table and reports `TOTAL candidates=0` — precisely the
    catastrophic false-clean this routing was written to prevent, reintroduced
    by a leading blank line or YAML frontmatter.
    """
    path = tmp_path / "skill-monitoring.md"
    path.write_text("\n---\ntitle: registry\n---\n" + MONITORING_HEADER
                    + "- 🔴 **J1 — one.** Status: `MONITORING`\n", encoding="utf-8")
    out = run(path)
    assert "J-entries=    1" in out, out
    assert "TOTAL candidates=" not in out, out


def test_an_empty_registry_is_still_a_registry(tmp_path: Path) -> None:
    """"No entries yet" must not be the thing that misroutes the file."""
    path = monitoring(tmp_path, "\nNo entries have been filed yet.\n")
    out = run(path)
    assert "J-entries=    0" in out, out
    assert "TOTAL candidates=" not in out, out
