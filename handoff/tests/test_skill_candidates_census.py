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


def test_no_arguments_usage_names_every_flag_help_names() -> None:
    # Row 2878: the bare-invocation usage line omitted `--apply` and `--rev`, so
    # the stamp verb that already existed was rebuilt by hand four times and
    # triaged as missing twice. The error path is what a caller actually sees.
    bare = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    helped = subprocess.run([sys.executable, str(SCRIPT), "-h"], capture_output=True, text=True)
    flags = set(re.findall(r"--[a-z-]+", helped.stdout))
    assert {"--list-open", "--rev", "--apply"} <= flags, helped.stdout
    missing = sorted(f for f in flags if f not in bare.stderr)
    assert not missing, f"bare usage omits {missing}: {bare.stderr!r}"


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
            "- **a** (*already open above, recurrence raised*): seen again — candidate: yes\n",
            0,
            "HemaSuite's bump spelling (hpw:253 bidirectional-cross-doc-check) was "
            "double-counted as a live candidate",
        ),
        (
            "- **a**: the regex misses `(*already open above, recurrence raised*)` "
            "— candidate: yes\n",
            1,
            "a row that QUOTES the marker mid-tail is a real candidate (hpw:276); "
            "the marker only counts directly after the name",
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


# --- DECLINED carries its triage bucket -----------------------------------
#
# `DECLINED` means two different things in this file: "idea rejected" and
# "useful, but no tool will be built". The header documents that, and a reader
# who skims the marker without the note misreads 15 rows. Measured 2026-08-26:
# 20 of 23 markers already carried a `(triage: ...)` qualifier, so the fix is to
# finish the convention and count it — NOT to invent a fourth vocabulary word,
# which would cost a rewrite of every existing row and lose their history.


def test_declined_split_is_counted(tmp_path) -> None:
    doc = tmp_path / "c.md"
    doc.write_text(
        "- **a**: x — candidate: **DECLINED** (triage: useful, not codable) — r\n"
        "- **b**: x — candidate: **DECLINED** (triage: not useful) — r\n"
        "- **c**: x — candidate: **DECLINED** (triage: useful, not codable) — r\n",
        encoding="utf-8",
    )

    out = run(doc)

    assert "DECLINED=3" in out, out
    assert "useful-not-codable=2" in out, out
    assert "not-useful=1" in out, out


def test_an_unqualified_declined_is_reported_not_absorbed(tmp_path) -> None:
    """The whole point: an unqualified marker is exactly the one a reader
    misreads, so it must be visible rather than folded into either bucket."""
    doc = tmp_path / "c.md"
    doc.write_text(
        "- **a**: x — candidate: **DECLINED** (triage: not useful) — r\n"
        "- **b**: x — candidate: **DECLINED** — no bucket named\n",
        encoding="utf-8",
    )

    out = run(doc)

    assert "unqualified=1" in out, out
    assert "not-useful=1" in out, out


def test_the_live_backlog_has_no_unqualified_declined() -> None:
    """Regression pin on the real file, not a fixture.

    Finishing the convention is only worth anything if it stays finished; a new
    bare `DECLINED` re-creates the ambiguity this row was filed against.
    """
    out = run(SCRIPT.resolve().parents[2] / "docs" / "skill-candidates.md")

    assert "unqualified=0" in out, out


# --- the non-J historical log stays out of the open count -----------------
#
# docs/skill-monitoring.md carries 46 `J` entries under a `Status:` lifecycle
# and 33 older F/G/H/A/V/P rows that predate it. Read in full on 2026-08-26:
# none is live open work — F1-F13 have their own FIXED table, F14-F18/G/H/A
# record resolution inline, G5/H5/V1 are notes rather than work, P1 was
# declined. The standing temptation is to "fix" the coverage gap by widening
# the parser, which would reclassify all 33 as open in one commit.


def test_the_non_j_rows_are_reported_but_never_parsed_as_entries() -> None:
    out = run(SCRIPT.resolve().parents[2] / "docs" / "skill-monitoring.md")

    # Bumped 46 -> 48 for J50/J51 (2026-10-12), 48 -> 50 for J52/J53 (2026-10-15), 50 -> 53
    # for J54-J56 (2026-10-18). Real entries move both numbers together; the historical gap
    # the pin exists for stays exactly 33 (86 - 53).
    assert "J-entries=   53" in out or "J-entries=53" in out, out
    assert "parsed=53 row-shaped=86" in out, out


def test_widening_the_parser_would_be_visible_here() -> None:
    """A regression pin with teeth: if a later change makes the reader absorb
    the 33, `parsed` moves off 53 and this fails. The count is the guard — the
    coverage line alone would still print, just with different numbers."""
    out = run(SCRIPT.resolve().parents[2] / "docs" / "skill-monitoring.md")

    # 0 -> 2 for J52/J53 (2026-10-15), 2 -> 4 for J54-J56 (2026-10-18; J56 FIXED, two
    # MONITORING). Lower it when an open entry is closed.
    open_line = [l for l in out.splitlines() if "J-entries" in l][0]
    assert "OPEN(MONITORING+PLANNED)=   4" in open_line, open_line


def test_the_coverage_gap_names_what_it_is(tmp_path) -> None:
    """An unexplained `33 ROW-SHAPED LINES NOT PARSED` reads as a defect and
    invites exactly the parser-widening the file forbids. It must say why."""
    out = run(SCRIPT.resolve().parents[2] / "docs" / "skill-monitoring.md")

    assert "historical" in out.lower(), out


def test_importing_the_module_runs_nothing() -> None:
    """The friction that keeps producing ad-hoc parsers, pinned.

    Before the `__main__` guard, module top level WAS the CLI: importing to
    reuse `rows()`/`ROW`/`TERM`/`CAND` — the only reader with tests — printed a
    census to stdout and then `sys.exit`ed with a usage error unless the caller
    set `sys.argv` first. Three sessions wrote their own parser instead and all
    three miscounted (270/101 against 316/125; two more on 2026-08-28). A bare
    import must be silent and must not raise.
    """
    r = subprocess.run(
        [sys.executable, "-c", "import skill_candidates_census"],
        cwd=SCRIPT.parent, capture_output=True, text=True,
    )

    assert r.returncode == 0, r.stderr
    assert r.stdout == "", f"import printed to stdout: {r.stdout!r}"
    assert r.stderr == "", f"import printed to stderr: {r.stderr!r}"


def test_the_documented_import_api_is_actually_importable() -> None:
    """Naming the symbols in a docstring is worthless if they move. A caller
    following the scout's instruction needs exactly these."""
    probe = (
        "import skill_candidates_census as m;"
        "assert callable(m.rows) and callable(m.main);"
        "assert m.ROW.pattern and m.TERM.pattern and m.CAND.pattern;"
        "assert m.OPEN == ('yes', 'maybe');"
        "print('ok')"
    )
    r = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=SCRIPT.parent, capture_output=True, text=True,
    )

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ok"


def test_main_is_callable_in_process_and_returns_an_exit_code(tmp_path) -> None:
    """`main(argv)` is the half that makes the guard useful — without it the
    only way to run a census is to shell out, which is what a caller wanting
    the numbers in-process was avoiding."""
    store = write(tmp_path, "- **a**: row — candidate: yes\n")
    probe = (
        "import sys, io, skill_candidates_census as m;"
        "buf = io.StringIO(); old = sys.stdout; sys.stdout = buf;"
        f"rc = m.main([{str(store)!r}]);"
        "sys.stdout = old;"
        "print(rc, 'OPEN(yes+maybe)=' in buf.getvalue())"
    )
    r = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=SCRIPT.parent, capture_output=True, text=True,
    )

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "0 True", r.stdout


def test_no_arguments_still_refuses_after_the_guard() -> None:
    """The pre-existing refusal must survive the refactor in BOTH surfaces:
    the CLI (already pinned above) and the in-process entry point, which is new
    and could easily have been written to return 0 on an empty argv."""
    r = subprocess.run(
        [sys.executable, "-c",
         "import skill_candidates_census as m; print(m.main([]))"],
        cwd=SCRIPT.parent, capture_output=True, text=True,
    )

    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "1", r.stdout
    assert "usage:" in r.stderr


# --- a WRAPPED bold name, and a coverage check that can disagree with the reader ---

def test_a_row_whose_bold_name_wraps_is_still_a_row(tmp_path: Path) -> None:
    """`ROW` needed the closing `**` on one line, so a row whose NAME wrapped was
    not a row at all: not counted, not censused, in no bucket.

    Measured 2026-09-07 on the live store — a row was appended (git diff: 18 lines
    inserted) and the census read `candidates=201` before and after. Two rows
    already in that file had never been counted by any run.
    """
    p = write(tmp_path, "- **a name long enough that it wraps before\n"
                        "  its closing bold**: body — candidate: yes\n")
    c = counts(run(p))
    assert c["candidates"] == 1, run(p)
    assert c["OPEN"] == 1


def test_the_wrapped_name_is_normalised_not_left_with_its_newline(tmp_path: Path) -> None:
    """Assert the parsed NAME, not the printed column spacing — an `or` chain over
    three paddings tests the formatter, not the fix."""
    p = write(tmp_path, "- **wrapped\n  name**: body — candidate: yes\n")
    sys.path.insert(0, str(SCRIPT.parent))
    import skill_candidates_census as m

    (lineno, body), = m.rows(str(p))
    name, tail = m.row_name(body)
    assert name == "wrapped name", name
    assert "\n" not in name
    assert tail.startswith(": body"), tail


def test_the_tail_that_BUMP_reads_is_the_closing_line_only(tmp_path: Path) -> None:
    """A bump marker is a first-line annotation. Widening the tail to the whole row
    makes `BUMP` search the body, which silently reclassifies a real terminal row.

    This is not hypothetical: the first version of the wrap fix returned the whole
    remainder as the tail, and a LANDED row three lines down became a bump — the
    LANDED total stayed put and looked correct while one row had moved buckets.
    """
    p = write(tmp_path, "- **a**: body — candidate: yes\n"
                        "  — **LANDED 2026-09-07.** and here the prose happens to say\n"
                        "  no new recurrence, which is NOT a bump marker for this row\n")
    c = counts(run(p))
    assert c.get("LANDED") == 1, run(p)
    assert "1 bump rows excluded" not in run(p)


def test_coverage_DISAGREES_when_a_bold_name_never_closes(tmp_path: Path) -> None:
    """The load-bearing half. COVERAGE used to be computed with the same `ROW`
    regex as the reader, so an unparsed row was missing from BOTH sides and the
    ratio stayed a reassuring `N/N`. A coverage metric derived from the pattern it
    audits can only ever report agreement with itself.
    """
    p = write(tmp_path, "- **a**: fine — candidate: yes\n"
                        "- **this name never closes its bold at all\n"
                        "  and neither does this line\n")
    out = run(p)
    assert "never closes" in out, out
    c = counts(out)
    assert c["candidates"] == 1, out
    # The point of the whole change: parsed < row-shaped, and the check SAYS so.
    parsed, rowish = re.search(r"parsed=(\d+) row-shaped=(\d+)", out).groups()
    assert int(parsed) < int(rowish), out
    assert "ROW-SHAPED LINES NOT PARSED" in out, out


# --- `--list-open` ---------------------------------------------------------
#
# Nothing named the rows behind the OPEN number, so every session that wanted to
# reconcile the backlog re-derived the set with an ad-hoc grep — and this file has
# been measured wrong that way twice (a row whose bolded name WRAPPED was counted
# by neither the reader nor the coverage check, leaving a reassuring 207/207). The
# listing therefore comes from the SAME row objects the counter consumes, and the
# script asserts the two agree rather than trusting that they do.

def run_flag(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, check=False,
    )


def _store(tmp_path: Path) -> Path:
    p = tmp_path / "skill-candidates.md"
    p.write_text(
        "# Skill Candidates\n\n"
        "- **an open one**: body — recurrence: 1 — candidate: yes\n"
        "- **a maybe one**: body — recurrence: 1 — candidate: maybe\n"
        "- **a landed one**: body — candidate: yes\n"
        "  — **LANDED 2026-09-14** somewhere\n"
        "- **a declined one**: body — candidate: yes\n"
        "  — **DECLINED 2026-09-14 (triage: not useful)** because\n"
        "- **a no one**: body — recurrence: 1 — candidate: no\n",
        encoding="utf-8",
    )
    return p


class TestListOpen:
    def test_it_names_every_open_row_and_no_other(self, tmp_path: Path) -> None:
        out = run_flag("--list-open", str(_store(tmp_path))).stdout
        assert "an open one" in out
        assert "a maybe one" in out
        assert "a landed one" not in out
        assert "a declined one" not in out
        assert "a no one" not in out

    def test_the_listing_and_the_count_cannot_disagree(self, tmp_path: Path) -> None:
        """The script asserts this itself; this pins that it still does."""
        r = run_flag("--list-open", str(_store(tmp_path)))
        assert r.returncode == 0, r.stderr
        assert "OPEN rows in" in r.stdout
        listed = [l for l in r.stdout.splitlines() if l.startswith("    ") and ":" in l]
        assert len(listed) == 2, r.stdout

    def test_each_row_carries_its_line_number_and_verdict(self, tmp_path: Path) -> None:
        """A backlog row you cannot jump to is one nobody reconciles."""
        out = run_flag("--list-open", str(_store(tmp_path))).stdout
        assert ":3" in out and "yes" in out
        assert ":4" in out and "maybe" in out

    def test_the_default_output_is_unchanged(self, tmp_path: Path) -> None:
        """The summary line is parsed by other consumers; this is add-only."""
        store = _store(tmp_path)
        plain = run_flag(str(store)).stdout
        assert "OPEN rows in" not in plain
        flagged = run_flag("--list-open", str(store)).stdout
        for line in plain.splitlines():
            assert line in flagged, f"default line vanished under the flag: {line!r}"

    def test_the_flag_is_not_mistaken_for_a_path(self, tmp_path: Path) -> None:
        r = run_flag("--list-open")
        assert r.returncode == 1
        assert "usage:" in r.stderr and "--list-open" in r.stderr


# --- committed reads and insert-only reconciliation ------------------------

@pytest.fixture
def committed_store(tmp_path: Path) -> tuple[Path, str]:
    # Nest the store so REF:path must be relative to the git root, not its cwd.
    docs = tmp_path / "docs"
    docs.mkdir()
    store = _store(docs)
    for args in (
        ["init", "-q"],
        ["add", "docs/skill-candidates.md"],
        ["-c", "user.name=Census Test", "-c", "user.email=census@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
         "commit", "-qm", "fixture"],
    ):
        r = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, check=False,
        )
        assert r.returncode == 0, r.stderr
    ref = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return store, ref


def reconciliation_table(tmp_path: Path, *rows: tuple[str, str]) -> Path:
    table = tmp_path / "reconcile.md"
    table.write_text(
        "| open-line | status-line |\n| --- | --- |\n"
        + "".join(f"| {name} | {status} |\n" for name, status in rows),
        encoding="utf-8",
    )
    return table


@pytest.mark.parametrize("ref_kind", ["HEAD", "commit"])
def test_rev_reads_committed_content_despite_dirty_worktree(
    committed_store: tuple[Path, str], ref_kind: str,
) -> None:
    store, commit = committed_store
    expected = run(store)
    before = store.read_bytes()
    store.write_text(
        "# Skill Candidates\n\n- **working tree only**: candidate: no\n",
        encoding="utf-8",
    )
    dirty = store.read_bytes()
    assert dirty != before
    assert counts(run(store))["OPEN"] == 0

    r = run_flag("--rev", commit if ref_kind == "commit" else "HEAD", str(store))

    assert r.returncode == 0, r.stderr
    assert r.stdout == expected  # Includes verdict totals AND coverage.
    assert r.stderr == ""
    assert store.read_bytes() == dirty


def test_rev_combines_with_list_open_using_committed_names_and_line_numbers(
    committed_store: tuple[Path, str],
) -> None:
    store, ref = committed_store
    expected = run_flag("--list-open", str(store)).stdout
    store.write_text(
        "# Skill Candidates\n\n\n\n- **uncommitted open row**: candidate: yes\n",
        encoding="utf-8",
    )

    r = run_flag("--list-open", "--rev", ref, str(store))

    assert r.returncode == 0, r.stderr
    assert r.stdout == expected
    assert "an open one" in r.stdout and "a maybe one" in r.stdout
    assert "uncommitted open row" not in r.stdout


@pytest.mark.parametrize("failure", ["bad-ref", "uncommitted-path"])
def test_rev_unreadable_blob_exits_two_with_git_diagnostic_and_no_fallback(
    committed_store: tuple[Path, str], failure: str,
) -> None:
    store, ref = committed_store
    if failure == "bad-ref":
        ref = "census-ref-that-does-not-exist"
    else:
        store = store.with_name("untracked-candidates.md")
        store.write_text("- **working tree fallback**: candidate: yes\n", encoding="utf-8")
    # Match git's own diagnostic rather than pinning version-specific wording.
    git_result = subprocess.run(
        ["git", "-C", str(store.parent), "show", f"{ref}:docs/{store.name}"],
        capture_output=True, text=True, check=False,
    )
    assert git_result.returncode != 0
    before = store.read_bytes()

    r = run_flag("--rev", ref, str(store))

    assert r.returncode == 2, r.stderr
    assert r.stderr.strip() == (
        f"census: cannot read {store} at {ref}: {git_result.stderr.splitlines()[0]}"
    )
    assert r.stdout == ""
    assert store.read_bytes() == before


def test_apply_counts_lines_by_newline_only_past_unicode_separators(
    committed_store: tuple[Path, str], tmp_path: Path,
) -> None:
    # Rows are numbered by "\n"; str.splitlines also breaks on U+2028/U+2029,
    # which put the live store's row-2661 status two lines above its row.
    store, _ = committed_store
    head = "# Skill Candidates\n\n- **quoted row**: shows ` ` and ` ` — candidate: no\n\n"
    row = "- **target row**: description — candidate: yes\n"
    store.write_text(head + row, encoding="utf-8")
    table = reconciliation_table(tmp_path, ("target row", "**LANDED** done"))

    r = run_flag("--apply", str(table), str(store))

    assert r.returncode == 0, r.stderr
    assert "APPLY: inserted=1 OPEN 1→0" in r.stdout.splitlines()
    assert store.read_text(encoding="utf-8") == head + row + "  — **LANDED** done\n"


@pytest.mark.parametrize(
    "following",
    ["- **next row**: candidate: maybe\n", "## Next section\n", "\nA note outside the row.\n", ""],
    ids=["next-row", "heading", "blank", "eof"],
)
def test_apply_inserts_after_last_continuation_before_row_boundary(
    committed_store: tuple[Path, str], tmp_path: Path, following: str,
) -> None:
    store, _ = committed_store
    prefix = (
        "# Skill Candidates\n\n"
        "- **wrapped candidate**: description\n"
        "  — candidate: yes\n"
        "  final continuation that must stay ahead of the insertion\n"
    )
    store.write_text(prefix + following, encoding="utf-8")
    table = reconciliation_table(tmp_path, ("wrapped candidate", "reviewed; still open"))
    table_before = table.read_bytes()

    r = run_flag("--apply", str(table), str(store))

    assert r.returncode == 0, r.stderr
    assert store.read_bytes() == (
        prefix + "  — reviewed; still open\n" + following
    ).encode("utf-8")
    assert table.read_bytes() == table_before


def test_apply_reports_insertions_and_census_open_delta_for_all_table_rows(
    committed_store: tuple[Path, str], tmp_path: Path,
) -> None:
    store, _ = committed_store
    before = store.read_text(encoding="utf-8")
    table = reconciliation_table(
        tmp_path,
        ("a maybe one", "reviewed; remains a maybe"),
        ("an open one", "**LANDED 2026-10-18** shipped"),
    )

    r = run_flag("--apply", str(table), str(store))

    assert r.returncode == 0, r.stderr
    assert "APPLY: inserted=2 OPEN 2→1" in r.stdout.splitlines()
    expected = before.replace(
        "- **a maybe one**:",
        "  — **LANDED 2026-10-18** shipped\n- **a maybe one**:",
    ).replace(
        "- **a landed one**:",
        "  — reviewed; remains a maybe\n- **a landed one**:",
    )
    assert store.read_text(encoding="utf-8") == expected
    assert counts(run(store))["OPEN"] == 1


def test_apply_unescapes_pipes_in_both_cells_before_matching_and_inserting(
    committed_store: tuple[Path, str], tmp_path: Path,
) -> None:
    store, _ = committed_store
    write(store.parent, "- **tool | tree**: candidate: yes\n")
    before = store.read_text(encoding="utf-8")
    table = reconciliation_table(
        tmp_path, (r"tool \| tree", r"**LANDED 2026-10-18** `src/a \| src/b`"),
    )

    r = run_flag("--apply", str(table), str(store))

    assert r.returncode == 0, r.stderr
    assert store.read_text(encoding="utf-8") == (
        before + "  — **LANDED 2026-10-18** `src/a | src/b`\n"
    )
    assert "APPLY: inserted=1 OPEN 1→0" in r.stdout.splitlines()


@pytest.mark.parametrize("name", ["absent row", "a landed one", "a no one", "bump only"])
def test_apply_no_match_refuses_entire_table_without_writing(
    committed_store: tuple[Path, str], tmp_path: Path, name: str,
) -> None:
    store, _ = committed_store
    with store.open("a", encoding="utf-8") as stream:
        stream.write("- **bump only** (recurrence, not a new row): candidate: yes\n")
    table = reconciliation_table(
        tmp_path,
        ("an open one", "**LANDED 2026-10-18** must not be partially applied"),
        (name, "**LANDED 2026-10-18** invalid target"),
    )
    before, table_before = store.read_bytes(), table.read_bytes()

    r = run_flag("--apply", str(table), str(store))

    assert store.read_bytes() == before
    assert table.read_bytes() == table_before
    assert r.returncode == 2, r.stderr
    assert f"APPLY: REFUSED reason=no-match line={name}" in r.stdout.splitlines()
    assert "APPLY: inserted=" not in r.stdout


@pytest.mark.parametrize("second_verdict", ["yes", "maybe"])
def test_apply_ambiguous_open_name_refuses_whole_table_without_writing(
    committed_store: tuple[Path, str], tmp_path: Path, second_verdict: str,
) -> None:
    store, _ = committed_store
    write(
        store.parent,
        "- **unique row**: candidate: yes\n"
        "- **same name**: candidate: yes\n"
        f"- **same name**: candidate: {second_verdict}\n",
    )
    table = reconciliation_table(
        tmp_path,
        ("unique row", "**LANDED 2026-10-18** must not be partially applied"),
        ("same name", "**LANDED 2026-10-18** ambiguous"),
    )
    before, table_before = store.read_bytes(), table.read_bytes()

    r = run_flag("--apply", str(table), str(store))

    assert store.read_bytes() == before
    assert table.read_bytes() == table_before
    assert r.returncode == 2, r.stderr
    assert "APPLY: REFUSED reason=ambiguous line=same name" in r.stdout.splitlines()
    assert "APPLY: inserted=" not in r.stdout


def test_apply_matches_normalized_open_name_and_ignores_closed_duplicate(
    committed_store: tuple[Path, str], tmp_path: Path,
) -> None:
    store, _ = committed_store
    prefix = "# Skill Candidates\n\n- **same\n  name**: candidate: maybe\n"
    closed = "- **same name**: candidate: yes — **LANDED 2026-10-17** done\n"
    store.write_text(prefix + closed, encoding="utf-8")
    table = reconciliation_table(tmp_path, ("same name", "reviewed; remains open"))

    r = run_flag("--apply", str(table), str(store))

    assert r.returncode == 0, r.stderr
    assert store.read_text(encoding="utf-8") == (
        prefix + "  — reviewed; remains open\n" + closed
    )
    assert "APPLY: inserted=1 OPEN 1→1" in r.stdout.splitlines()


@pytest.mark.parametrize("rev_first", [True, False])
def test_apply_rejects_rev_combination_as_usage_error_without_writing(
    committed_store: tuple[Path, str], tmp_path: Path, rev_first: bool,
) -> None:
    store, ref = committed_store
    table = reconciliation_table(tmp_path, ("an open one", "**LANDED 2026-10-18** done"))
    before, table_before = store.read_bytes(), table.read_bytes()
    options = (["--rev", ref, "--apply", str(table)] if rev_first
               else ["--apply", str(table), "--rev", ref])

    r = run_flag(*options, str(store))

    assert store.read_bytes() == before
    assert table.read_bytes() == table_before
    assert r.returncode == 1, r.stderr
    assert "usage:" in r.stderr
    assert "--rev" in r.stderr and "--apply" in r.stderr


@pytest.mark.parametrize("store_count", [0, 2])
def test_apply_requires_exactly_one_store_and_writes_nothing_on_usage_error(
    committed_store: tuple[Path, str], tmp_path: Path, store_count: int,
) -> None:
    store, _ = committed_store
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    other = _store(other_dir)
    table = reconciliation_table(tmp_path, ("an open one", "**LANDED 2026-10-18** done"))
    before = {p: p.read_bytes() for p in (store, other, table)}
    paths = [str(store), str(other)] if store_count == 2 else []

    r = run_flag("--apply", str(table), *paths)

    assert {p: p.read_bytes() for p in before} == before
    assert r.returncode == 1, r.stderr
    assert "usage:" in r.stderr and "--apply" in r.stderr


def test_apply_landed_status_removes_only_that_row_from_open_listing(
    committed_store: tuple[Path, str], tmp_path: Path,
) -> None:
    store, _ = committed_store
    before = counts(run(store))
    table = reconciliation_table(tmp_path, ("an open one", "**LANDED 2026-10-18** shipped"))

    applied = run_flag("--apply", str(table), str(store))

    assert applied.returncode == 0, applied.stderr
    listed = run_flag("--list-open", str(store))
    assert listed.returncode == 0, listed.stderr
    after = counts(listed.stdout)
    assert after["OPEN"] == before["OPEN"] - 1
    assert after["LANDED"] == before["LANDED"] + 1
    assert after["candidates"] == before["candidates"]
    assert "an open one" not in listed.stdout
    assert "a maybe one" in listed.stdout
    assert "APPLY: inserted=1 OPEN 2→1" in applied.stdout.splitlines()


# --- malformed reconciliation tables: refuse the whole apply (spec 2026-10-18) ---


@pytest.mark.parametrize(
    "malformed",
    [
        pytest.param("| a maybe one | reviewed | still open |", id="unescaped-status-pipe"),
        pytest.param("| a maybe | one | reviewed |", id="unescaped-name-pipe"),
        pytest.param("| a maybe one |", id="one-cell"),
        pytest.param("|", id="zero-cells"),
        pytest.param("| a maybe one | reviewed | |", id="empty-extra-cell"),
        pytest.param("| a maybe one", id="missing-closing-pipe"),
        pytest.param(
            r"| a maybe one | reviewed \| quoted | unescaped |",
            id="escaped-pipe-does-not-hide-extra-cell",
        ),
    ],
)
@pytest.mark.parametrize("malformed_first", [True, False], ids=["before-valid", "after-valid"])
def test_apply_malformed_row_refuses_whole_table_with_physical_line_number(
    tmp_path: Path, malformed: str, malformed_first: bool,
) -> None:
    """Spec 1: neither an earlier nor a later valid row may be applied."""
    store = _store(tmp_path)
    valid = "| an open one | **LANDED 2026-10-18** must not be applied |"
    data = [malformed, valid] if malformed_first else [valid, malformed]
    # Prose, header, separator and blank lines all count toward the diagnostic's
    # physical line number; none is a data row.
    lines = ["# Reconciliation", "", "| open-line | status-line |", "| --- | --- |", ""]
    lines.extend(data)
    table = tmp_path / "reconcile.md"
    table.write_text("\n".join(lines) + "\n", encoding="utf-8")
    before = {p: p.read_bytes() for p in (store, table)}
    expected_line = 6 if malformed_first else 7

    result = run_flag("--apply", str(table), str(store))

    assert {p: p.read_bytes() for p in before} == before, "refusal must be atomic"
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"APPLY: REFUSED reason=malformed-row line={expected_line}"
    ]
    assert result.stderr == ""


def test_apply_only_malformed_data_row_is_not_a_successful_noop(tmp_path: Path) -> None:
    """Spec 1: reproduce the silent inserted=0 success reported in the defect."""
    store = _store(tmp_path)
    table = reconciliation_table(tmp_path, ("an open one", "reviewed | still open | extra"))
    before = {p: p.read_bytes() for p in (store, table)}

    result = run_flag("--apply", str(table), str(store))

    assert {p: p.read_bytes() for p in before} == before
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["APPLY: REFUSED reason=malformed-row line=3"]
    assert result.stderr == ""


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("", id="empty-file"),
        pytest.param(" \n\t\n", id="whitespace-only"),
        pytest.param("# Reconciliation\n\nNo decisions yet.\n", id="prose-only"),
        pytest.param("| open-line | status-line |\n", id="header-only"),
        pytest.param("| open-line | status-line |\n| --- | --- |\n", id="header-and-separator"),
        pytest.param(
            "# Reconciliation\n\n| open-line | status-line |\n| :--- | ---: |\n\n",
            id="header-and-aligned-separator-with-prose",
        ),
    ],
)
def test_apply_zero_data_rows_refuses_empty_table_without_writing(
    tmp_path: Path, text: str,
) -> None:
    """Spec 2: empty input must not be reported as a successful no-op."""
    store = _store(tmp_path)
    table = tmp_path / "reconcile.md"
    table.write_text(text, encoding="utf-8")
    before = {p: p.read_bytes() for p in (store, table)}

    result = run_flag("--apply", str(table), str(store))

    assert {p: p.read_bytes() for p in before} == before
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["APPLY: REFUSED reason=empty-table"]
    assert result.stderr == ""


@pytest.mark.parametrize("separator", ["| --- | --- |", "| :--- | ---: |"])
def test_apply_valid_table_guard_preserves_escaped_cells_and_all_insertions(
    tmp_path: Path, separator: str,
) -> None:
    """Spec 3 — existing-behavior guard (expected PASS during RED)."""
    store = write(
        tmp_path,
        "- **tool | tree**: candidate: yes\n"
        "- **another**: candidate: maybe\n",
    )
    table = tmp_path / "reconcile.md"
    table.write_text(
        "# Reconciliation\n\n| open-line | status-line |\n"
        + separator + "\n\n"
        + r"| tool \| tree | **LANDED 2026-10-18** src/a \| src/b \| src/c |" + "\n"
        + "| another | reviewed; remains open |\n",
        encoding="utf-8",
    )
    table_before = table.read_bytes()

    result = run_flag("--apply", str(table), str(store))

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["APPLY: inserted=2 OPEN 2→1"]
    assert result.stderr == ""
    assert store.read_bytes() == (
        "# Skill Candidates\n\n"
        "- **tool | tree**: candidate: yes\n"
        "  — **LANDED 2026-10-18** src/a | src/b | src/c\n"
        "- **another**: candidate: maybe\n"
        "  — reviewed; remains open\n"
    ).encode("utf-8")
    assert table.read_bytes() == table_before


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_flag_prints_usage_and_exits_zero_without_opening_flag_as_path(
    flag: str,
) -> None:
    """Row 39: --help/-h must print usage and exit 0, not raise FileNotFoundError."""
    result = run_flag(flag)
    assert result.returncode == 0, f"{flag} must exit 0: {result.stderr}"
    assert "usage: skill_candidates_census.py" in result.stdout, result.stdout
    assert "--list-open" in result.stdout and "--apply" in result.stdout, result.stdout
    assert result.stderr == "", result.stderr

