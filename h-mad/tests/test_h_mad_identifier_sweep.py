"""Post-edit identifier sweep: after the LAST edit of a rename, what still names the old thing?

The argument for a tool is one measured failure, not a preference. `a311385`
renamed `hooks/h-mad-advisor-gate.sh` to `-warn.sh` and shipped three stale
references to a file the same commit deletes; the sweep had been *started* by
hand mid-work — two context-budget docstrings were noticed — and then never
finished, because more edits followed. It failed once in three tries.

The mechanical half is the grep-and-classify loop plus a hit list diffed
against an allowlist of files that legitimately explain the old name. The half
that must stay with a human is deciding whether a given hit is explanation or
leftover, which is why the allowlist is an input and never inferred.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SWEEP = SCRIPTS / "h_mad_identifier_sweep.py"

sys.path.insert(0, str(SCRIPTS))
from h_mad_identifier_sweep import classify_surface, sweep  # noqa: E402


def _tree(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


# --- the verdicts ---------------------------------------------------------


def test_no_remaining_reference_is_clean(tmp_path: Path) -> None:
    _tree(tmp_path, {"a.py": "x = 1\n", "docs/b.md": "nothing here\n"})

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert result["verdict"] == "CLEAN", result
    assert result["leftover"] == []


def test_a_remaining_reference_is_a_leftover_with_its_location(tmp_path: Path) -> None:
    _tree(tmp_path, {"a.py": "x = 1\ncall(old_name)\n"})

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert result["verdict"] == "LEFTOVERS", result
    hit = result["leftover"][0]
    assert hit["path"] == "a.py"
    assert hit["line"] == 2, "a hit without a line number is a manual re-grep"
    assert "old_name" in hit["text"]


def test_an_allowlisted_file_is_reported_but_not_a_leftover(tmp_path: Path) -> None:
    """The new script's own header explains the old name on purpose.

    Allowed hits stay visible — silently dropping them would let the allowlist
    grow into a place where real leftovers hide.
    """
    _tree(tmp_path, {
        "new.py": "# replaces old_name, which never fired\n",
        "stale.md": "run old_name to check\n",
    })

    result = sweep(tmp_path, ["old_name"], allow=["new.py"])

    assert result["verdict"] == "LEFTOVERS", result
    assert [h["path"] for h in result["leftover"]] == ["stale.md"]
    assert [h["path"] for h in result["allowed"]] == ["new.py"]


def test_every_hit_allowlisted_is_clean(tmp_path: Path) -> None:
    _tree(tmp_path, {"new.py": "# replaces old_name\n"})

    result = sweep(tmp_path, ["old_name"], allow=["new.py"])

    assert result["verdict"] == "CLEAN", result
    assert result["allowed"], "an allowed hit must still be reported"


# --- surfaces -------------------------------------------------------------


def test_each_surface_is_named_so_the_reader_knows_what_they_are_looking_at() -> None:
    """The row lists the surfaces because they are checked and missed unevenly."""
    assert classify_surface("h-mad/tests/mutation-specs/x.json", '"find": "old"') == "mutation-anchor"
    assert classify_surface("h-mad/tests/test_x.py", "assert old") == "test"
    assert classify_surface("docs/x.md", "prose about old") == "doc"
    assert classify_surface("scripts/x.py", "    # old was removed") == "comment"
    assert classify_surface("scripts/x.py", "    call(old)") == "code"


def test_a_mutation_spec_anchor_is_classified_as_such(tmp_path: Path) -> None:
    """The surface the row calls the one most often missed."""
    _tree(tmp_path, {
        "tests/mutation-specs/s.json": '{"find": "old_name", "replace": "x"}\n',
    })

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert result["leftover"][0]["surface"] == "mutation-anchor", result


# --- the stem, and the false positive it would cause ----------------------


def test_the_stem_of_a_filename_is_reported_separately_not_as_a_leftover(
    tmp_path: Path,
) -> None:
    """Renaming `foo.sh` leaves prose saying "foo" — related, not the same claim.

    Folding stem hits into `leftover` would flood the verdict with prose that
    names a concept rather than a file; dropping them entirely re-creates the
    miss this sweep exists to catch. They are reported as their own class.
    """
    _tree(tmp_path, {
        "docs/a.md": "the advisor-gate approach is gone\n",
        "docs/b.md": "run advisor-gate.sh nightly\n",
    })

    result = sweep(tmp_path, ["advisor-gate.sh"], allow=[])

    assert [h["path"] for h in result["leftover"]] == ["docs/b.md"]
    assert [h["path"] for h in result["related"]] == ["docs/a.md"]
    assert result["verdict"] == "LEFTOVERS"


def test_a_stem_hit_alone_does_not_make_the_verdict_dirty(tmp_path: Path) -> None:
    _tree(tmp_path, {"docs/a.md": "the advisor-gate approach is gone\n"})

    result = sweep(tmp_path, ["advisor-gate.sh"], allow=[])

    assert result["verdict"] == "CLEAN", result
    assert result["related"], "the stem hit must still be printed for the reader"


def test_an_identifier_with_no_extension_has_no_stem_pass(tmp_path: Path) -> None:
    """An empty stem is `""`, and `"" in line` is true of every line there is.

    The tree deliberately carries lines that do NOT contain the identifier: the
    first version of this test had only the matching line, so the stem branch
    was never reached and a mutation making the stem match everything survived.
    A fixture that cannot reach the branch cannot discriminate it.
    """
    _tree(tmp_path, {
        "a.py": "old_name\n",
        "b.py": "nothing to do with it\nnor this line\n",
    })

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert len(result["leftover"]) == 1
    assert result["related"] == [], "an extensionless identifier must have no stem pass"


# --- what must not be searched -------------------------------------------


def test_git_and_bytecode_are_not_searched(tmp_path: Path) -> None:
    """A hit inside `.git` or a `.pyc` is not a reference anyone can fix."""
    _tree(tmp_path, {
        ".git/COMMIT_EDITMSG": "removed old_name\n",
        "pkg/__pycache__/x.cpython-311.pyc": "old_name\n",
        "keep.py": "fine\n",
    })

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert result["verdict"] == "CLEAN", result


def test_an_unreadable_file_is_skipped_rather_than_crashing_the_sweep(
    tmp_path: Path,
) -> None:
    _tree(tmp_path, {"good.md": "old_name\n"})
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00old_name")

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert [h["path"] for h in result["leftover"]] == ["good.md"]


# --- several identifiers in one pass --------------------------------------


def test_several_identifiers_are_swept_in_one_pass(tmp_path: Path) -> None:
    """A rename usually removes more than one name, and two passes is where
    the human version stops after the first."""
    _tree(tmp_path, {"a.py": "one_old\n", "b.py": "two_old\n"})

    result = sweep(tmp_path, ["one_old", "two_old"], allow=[])

    assert {h["identifier"] for h in result["leftover"]} == {"one_old", "two_old"}


# --- CLI ------------------------------------------------------------------


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SWEEP), *args],
                          capture_output=True, text=True)


def test_cli_prints_the_token_and_exits_2_on_a_leftover(tmp_path: Path) -> None:
    _tree(tmp_path, {"a.py": "old_name\n"})

    proc = _cli("old_name", "--root", str(tmp_path))

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "SWEEP: LEFTOVERS" in proc.stdout, proc.stdout
    assert "a.py:1" in proc.stdout, proc.stdout
    assert "[H-MAD]" in proc.stdout, proc.stdout


def test_cli_exits_0_when_clean(tmp_path: Path) -> None:
    _tree(tmp_path, {"a.py": "fine\n"})

    proc = _cli("old_name", "--root", str(tmp_path))

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SWEEP: CLEAN" in proc.stdout, proc.stdout


def test_cli_says_the_judgement_is_not_its_own(tmp_path: Path) -> None:
    """Leftover means "still names the old thing", not "wrong" — the reader
    decides which hits are explanation. A tool that implied a verdict on that
    would train people to delete correct prose."""
    _tree(tmp_path, {"a.py": "old_name\n"})

    proc = _cli("old_name", "--root", str(tmp_path))

    assert "explanation" in proc.stdout, proc.stdout


def test_cli_reports_an_unreadable_root_as_a_cannot_judge(tmp_path: Path) -> None:
    proc = _cli("old_name", "--root", str(tmp_path / "nope"))

    assert proc.returncode == 2
    assert "SWEEP: UNREADABLE" in proc.stdout, proc.stdout
    assert "LEFTOVERS" not in proc.stdout, "a cannot-judge must not read as a finding"


def test_cli_refuses_an_empty_identifier(tmp_path: Path) -> None:
    """An empty needle matches every line of every file — a sweep that reports
    everything is indistinguishable from one that reports nothing."""
    proc = _cli("", "--root", str(tmp_path))

    assert proc.returncode != 0
    assert "empty" in (proc.stdout + proc.stderr).lower()


def test_the_skill_documents_the_sweep() -> None:
    skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "h_mad_identifier_sweep.py" in skill, "a tool nobody is told to run is a tool nobody runs"
    assert "SWEEP:" in skill, "the token is undocumented"
    assert "the LAST edit" in skill, (
        "the timing IS the property — a sweep run mid-work is the failure it replaces"
    )


# --- what live fire found that tmp_path fixtures could not ----------------
#
# Measured 2026-08-26, first real run over this repo: 26 hits, 14 of them lines
# of `.bkit/audit/*.jsonl` machine log and 5 more in handoff docs that are
# historical records by definition. Neither is editable, and together they
# outnumbered the four hits a reader would act on. The excerpt was truncated at
# 160 characters from the START of the line, so on a 900-character JSON log line
# the printed text did not contain the identifier at all.


def test_append_only_history_is_counted_not_listed_as_a_leftover(tmp_path: Path) -> None:
    """Handoffs and archives are historical records — READ mode forbids editing
    them. Flagging them trains the reader to skim the leftover list."""
    _tree(tmp_path, {
        "docs/handoffs/2026-01-01-x.md": "we removed old_name today\n",
        "docs/archive/old/plan.md": "old_name was the design\n",
        "live.py": "old_name\n",
    })

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert [h["path"] for h in result["leftover"]] == ["live.py"]
    assert len(result["history"]) == 2, result


def test_history_hits_are_still_counted_so_the_suppression_is_visible(
    tmp_path: Path,
) -> None:
    """A silent skip and an empty tree print the same thing."""
    _tree(tmp_path, {"docs/handoffs/x.md": "old_name\n"})

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert result["verdict"] == "CLEAN", result
    assert len(result["history"]) == 1


def test_include_history_promotes_them_to_leftovers(tmp_path: Path) -> None:
    _tree(tmp_path, {"docs/handoffs/x.md": "old_name\n"})

    result = sweep(tmp_path, ["old_name"], allow=[], include_history=True)

    assert result["verdict"] == "LEFTOVERS", result
    assert [h["path"] for h in result["leftover"]] == ["docs/handoffs/x.md"]


def test_machine_log_directories_are_not_searched_at_all(tmp_path: Path) -> None:
    """`.bkit`/`.omc` are append-only tool state, not references anyone edits."""
    _tree(tmp_path, {".bkit/audit/2026-08-23.jsonl": '{"cmd":"old_name"}\n'})

    result = sweep(tmp_path, ["old_name"], allow=[], include_history=True)

    assert result["verdict"] == "CLEAN", result
    assert result["history"] == []


def test_the_excerpt_contains_the_identifier_on_a_very_long_line(
    tmp_path: Path,
) -> None:
    """Truncating from the start of the line prints an excerpt that does not
    contain the thing being swept for — the one guarantee the excerpt owes."""
    _tree(tmp_path, {"log.py": "x" * 800 + "old_name" + "y" * 800 + "\n"})

    result = sweep(tmp_path, ["old_name"], allow=[])

    assert "old_name" in result["leftover"][0]["text"], result["leftover"][0]["text"]
    assert len(result["leftover"][0]["text"]) < 300, "the excerpt must stay one line"


def test_cli_include_history_actually_reaches_the_sweep(tmp_path: Path) -> None:
    """The flag is wired, not merely parsed.

    Found by mutation: `--include-history` could be dropped on the way from
    argparse into `sweep()` and every test still passed, because they all called
    `sweep()` directly. A flag that parses and does nothing is worse than an
    absent one — it answers the reader's question with a lie.
    """
    _tree(tmp_path, {"docs/handoffs/x.md": "old_name\n"})

    quiet = _cli("old_name", "--root", str(tmp_path))
    loud = _cli("old_name", "--root", str(tmp_path), "--include-history")

    assert quiet.returncode == 0 and "SWEEP: CLEAN" in quiet.stdout, quiet.stdout
    assert loud.returncode == 2, loud.stdout + loud.stderr
    assert "leftover: docs/handoffs/x.md:1" in loud.stdout, loud.stdout


def test_cli_says_how_many_historical_hits_it_suppressed(tmp_path: Path) -> None:
    """A suppression nobody can see is the same defect as a silent skip."""
    _tree(tmp_path, {"docs/handoffs/x.md": "old_name\n"})

    proc = _cli("old_name", "--root", str(tmp_path))

    assert "history:" in proc.stdout, proc.stdout
    assert "--include-history" in proc.stdout, "the reader must be told how to see them"
