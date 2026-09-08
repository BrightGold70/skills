"""The author DONE-line gate — taken-over brief, 2026-09-08.

An author's `DONE` line has carried `path=`, `lines=` and `sha256=` in five live
dispatches (`spec-author` x1, `design-author` x2, `implplan-author` x1,
`plan-author` x1), and the orchestrator verified all five with
`shasum -a 256 "$F" | awk '{print $1}'` gated `|| exit 1` before committing. Five
for five matched. But the protocol lived only in hand-written dispatch prompts:
measured at `6f00f8c`, `grep -ciE 'sha256|line-count|lines='` over the five agent
definitions returned **0 for all five**, and `SKILL.md` held **zero** occurrences
of either string. A rule in a prompt is advice.

The gate this file covers must discriminate in BOTH directions, which is the whole
point — a battery that only proves the reject path lets a guard that refuses
everything score as a kill (`invariants.base.md` §"Test discrimination", and the
`nlm-cli-version-pin` finding: a wrong-catcher ships as ALL_CAUGHT without
per-mutation `test` keys). So every refusal below has a matching acceptance, and
the acceptance uses a REAL digest computed by the same command the agent files
name.

Three verdicts, and the partition is load-bearing rather than cosmetic:

  * `FAIL` refutes the author's claim.
  * `UNREADABLE` says the gate could not judge — routing it as a refutation sends
    the orchestrator to re-ask the author about a problem that is its own.
  * A MISSING artifact is `FAIL`, not `UNREADABLE`: the author asserted a file
    with that digest exists, so absence refutes the assertion.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "h_mad_done_gate.py"
AGENTS = SKILL_DIR / "agents"
SKILL = SKILL_DIR / "SKILL.md"

AUTHORS = ["spec-author", "plan-author", "design-author", "implplan-author"]
ALL_AGENTS = AUTHORS + ["doc-auditor"]


def _norm(path: Path) -> str:
    """Collapse whitespace so a literal survives reflow/indentation."""
    return " ".join(path.read_text(encoding="utf-8").split())


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
        capture_output=True, text=True,
    )


def _doc(repo: Path, rel: str = "docs/f.spec.md", body: str = "alpha\nbeta\n") -> tuple[str, int]:
    """Write `rel` and return `(sha256, wc -l)` for it."""
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    data = target.read_bytes()
    return hashlib.sha256(data).hexdigest(), data.count(b"\n")


def _done(sha: str, lines: int, path: str = "docs/f.spec.md",
          role: str = "SPEC-AUTHOR", version: str = "v1.3") -> str:
    return f"{role}: DONE version={version} path={path} lines={lines} sha256={sha}"


# --- acceptance: the gate must PASS a truthful report ---------------------------


def test_a_truthful_done_line_passes(tmp_path: Path) -> None:
    """Without this, every refusal below is satisfied by a gate that refuses all."""
    sha, lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line", _done(sha, lines))
    assert r.returncode == 0, r.stdout
    assert r.stdout.startswith("DONEGATE: PASS "), r.stdout
    assert f"sha256={sha}" in r.stdout
    assert "lines_check=ok" in r.stdout


def test_the_digest_matches_the_command_the_agent_files_name(tmp_path: Path) -> None:
    """`shasum -a 256 | awk '{print $1}'` and `wc -l` are what the agents prescribe.

    If the gate re-derived by any other route the author and the orchestrator would
    be measuring two different things, and a mismatch would mean nothing.
    """
    sha, lines = _doc(tmp_path, body="one\ntwo\nthree\n")
    doc = tmp_path / "docs/f.spec.md"
    shelled = subprocess.run(
        f"shasum -a 256 {doc} | awk '{{print $1}}'",
        shell=True, capture_output=True, text=True, check=True).stdout.strip()
    wc = subprocess.run(f"wc -l < {doc}", shell=True, capture_output=True,
                        text=True, check=True).stdout.strip()
    assert shelled == sha
    assert int(wc) == lines
    assert _run(tmp_path, "--done-line", _done(sha, lines)).returncode == 0


def test_every_role_token_is_accepted(tmp_path: Path) -> None:
    """Five agents emit this line; a gate anchored on one role silently skips four."""
    sha, lines = _doc(tmp_path)
    for role in ("SPEC-AUTHOR", "PLAN-AUTHOR", "DESIGN-AUTHOR",
                 "IMPLPLAN-AUTHOR", "DOC-AUDITOR"):
        r = _run(tmp_path, "--done-line", _done(sha, lines, role=role))
        assert r.returncode == 0, (role, r.stdout)


def test_the_implplan_extra_fields_do_not_displace_the_digest(tmp_path: Path) -> None:
    """`IMPLPLAN-AUTHOR` carries `tasks=`/`wiring=`/`mutation_rows=` before `path=`."""
    sha, lines = _doc(tmp_path, rel="docs/f.impl-plan.md")
    line = (f"IMPLPLAN-AUTHOR: DONE version=v1.7 tasks=9 wiring=2 mutation_rows=14 "
            f"path=docs/f.impl-plan.md lines={lines} sha256={sha}")
    r = _run(tmp_path, "--done-line", line)
    assert r.returncode == 0, r.stdout
    assert "path=docs/f.impl-plan.md" in r.stdout


# --- refusal: the mutation that matters ----------------------------------------


def test_a_wrong_sha_is_refused(tmp_path: Path) -> None:
    """THE mutation the brief names: a DONE line whose sha is not the file's.

    This is what a post-DONE dispatch produces — the author resumed from its
    transcript and wrote again, so the digest describes a file that no longer
    exists. Accepting it commits an artifact nobody verified.
    """
    sha, lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line", _done("0" * 64, lines))
    assert r.returncode == 1, r.stdout
    assert "DONEGATE: FAIL reason=sha_mismatch" in r.stdout
    # Both values, so the halt says what actually differs rather than that it did.
    assert f"actual={sha}" in r.stdout
    assert "reported=" + "0" * 64 in r.stdout


def test_a_sha_that_is_not_a_sha_is_refused(tmp_path: Path) -> None:
    """A truncated or placeholder digest must not fall through to a byte compare."""
    _sha, lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line", _done("deadbeef", lines))
    assert r.returncode == 1
    assert "reason=malformed_sha" in r.stdout


def test_a_missing_sha_field_is_refused(tmp_path: Path) -> None:
    """The pre-fix DONE line — `version=v1.N` alone — must not read as a pass."""
    _sha, lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line",
             f"SPEC-AUTHOR: DONE version=v1.3 path=docs/f.spec.md lines={lines}")
    assert r.returncode == 1
    assert "reason=no_sha_field" in r.stdout


def test_a_missing_path_field_is_refused(tmp_path: Path) -> None:
    sha, _lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line", f"SPEC-AUTHOR: DONE version=v1.3 sha256={sha}")
    assert r.returncode == 1
    assert "reason=no_path_field" in r.stdout


def test_a_valid_digest_of_the_WRONG_file_is_refused(tmp_path: Path) -> None:
    """The likelier mistake, and the one only `--expect-path` can see.

    An author that hashes the wrong file reports a digest that verifies perfectly
    against the file it named. Every byte-level check passes; only comparing
    `path=` with the document the orchestrator dispatched for catches it.
    """
    _want, _ = _doc(tmp_path, rel="docs/f.spec.md")
    other_sha, other_lines = _doc(tmp_path, rel="docs/f.plan.md", body="x\n")
    line = _done(other_sha, other_lines, path="docs/f.plan.md")
    # Without the expectation the report is internally consistent and passes.
    assert _run(tmp_path, "--done-line", line).returncode == 0
    r = _run(tmp_path, "--expect-path", "docs/f.spec.md", "--done-line", line)
    assert r.returncode == 1, r.stdout
    assert "reason=path_mismatch" in r.stdout


def test_expect_path_accepts_a_different_spelling_of_the_same_file(tmp_path: Path) -> None:
    """`./docs/f.spec.md` and `docs/f.spec.md` are one file; refusing that is noise."""
    sha, lines = _doc(tmp_path)
    r = _run(tmp_path, "--expect-path", "./docs/f.spec.md",
             "--done-line", _done(sha, lines))
    assert r.returncode == 0, r.stdout


def test_an_absent_artifact_is_FAIL_not_UNREADABLE(tmp_path: Path) -> None:
    """The author asserted the file exists; absence refutes it, and rc must say so.

    `UNREADABLE` (2) would route the orchestrator to fix its own inputs instead of
    re-asking the author, which is the cannot-judge/refutation confusion that
    `invariants.base.md` §"Audit-gate signal discipline" exists to prevent.
    """
    sha, lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line", _done(sha, lines, path="docs/gone.md"))
    assert r.returncode == 1, r.stdout
    assert "DONEGATE: FAIL reason=artifact_absent" in r.stdout


def test_a_done_line_that_is_not_first_is_refused(tmp_path: Path) -> None:
    """DONE-first is rule 4's contract; a gate that scans anywhere re-opens it.

    Four r17 reports were truncated before a trailing DONE and read as unfinished.
    A trailing DONE that survives truncation once says nothing about the next one.
    """
    sha, lines = _doc(tmp_path)
    msg = tmp_path / "msg.txt"
    msg.write_text("here is my report\n" + _done(sha, lines) + "\n", encoding="utf-8")
    r = _run(tmp_path, "--message-file", str(msg))
    assert r.returncode == 1, r.stdout
    assert "reason=done_line_not_first" in r.stdout


def test_a_message_with_no_done_line_is_refused(tmp_path: Path) -> None:
    _doc(tmp_path)
    msg = tmp_path / "msg.txt"
    msg.write_text("I finished the document.\n", encoding="utf-8")
    r = _run(tmp_path, "--message-file", str(msg))
    assert r.returncode == 1
    assert "reason=no_done_line" in r.stdout


def test_a_done_quoted_inside_a_report_body_is_not_the_contract_line(tmp_path: Path) -> None:
    """`DONE_RE` is anchored at line start for this: prose about a DONE is not one."""
    sha, lines = _doc(tmp_path)
    msg = tmp_path / "msg.txt"
    msg.write_text(f"the previous SPEC-AUTHOR: DONE version=v1.2 was stale\n"
                   f"{_done(sha, lines)}\n", encoding="utf-8")
    r = _run(tmp_path, "--message-file", str(msg))
    assert r.returncode == 1, r.stdout
    assert "reason=done_line_not_first" in r.stdout


# --- lines: reported, never gating ---------------------------------------------


def test_a_wrong_line_count_does_not_gate(tmp_path: Path) -> None:
    """`wc -l` counts newlines, so a units trap must not be able to fail a build.

    A matching sha already proves the bytes are identical, which is the whole
    claim; a lines disagreement means the author miscounted.
    """
    sha, _lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line", _done(sha, 999))
    assert r.returncode == 0, r.stdout
    assert "DONEGATE: PASS" in r.stdout
    assert "lines_check=disagree" in r.stdout


def test_an_absent_line_count_is_reported_as_absent_not_as_agreement(tmp_path: Path) -> None:
    """`absent` and `ok` must not spell the same thing — one of them is unmeasured."""
    sha, _lines = _doc(tmp_path)
    r = _run(tmp_path, "--done-line",
             f"SPEC-AUTHOR: DONE version=v1.3 path=docs/f.spec.md sha256={sha}")
    assert r.returncode == 0
    assert "lines_check=absent" in r.stdout


def test_a_file_with_no_trailing_newline_is_counted_the_way_wc_counts(tmp_path: Path) -> None:
    """The trap itself, pinned: the author's `wc -l` and the gate must agree."""
    sha, lines = _doc(tmp_path, body="alpha\nbeta")
    assert lines == 1  # two lines of text, one newline — this is the trap
    r = _run(tmp_path, "--done-line", _done(sha, lines))
    assert "lines_check=ok" in r.stdout, r.stdout


# --- cannot-judge --------------------------------------------------------------


def test_a_missing_message_file_is_UNREADABLE(tmp_path: Path) -> None:
    _doc(tmp_path)
    r = _run(tmp_path, "--message-file", str(tmp_path / "nope.txt"))
    assert r.returncode == 2, r.stdout
    assert "DONEGATE: UNREADABLE reason=message_file_unreadable" in r.stdout


def test_an_empty_message_file_is_UNREADABLE_not_a_missing_done_line(tmp_path: Path) -> None:
    """An empty `$RP` beside a DONE is a cannot-judge (rule 5); so is an empty message."""
    _doc(tmp_path)
    msg = tmp_path / "msg.txt"
    msg.write_text("   \n\n", encoding="utf-8")
    r = _run(tmp_path, "--message-file", str(msg))
    assert r.returncode == 2, r.stdout
    assert "reason=message_file_empty" in r.stdout


def test_an_unreadable_artifact_is_UNREADABLE_not_a_mismatch(tmp_path: Path) -> None:
    """Exists but cannot be opened: the gate did not look, so it must not judge."""
    sha, lines = _doc(tmp_path)
    doc = tmp_path / "docs/f.spec.md"
    doc.chmod(0o000)
    try:
        r = _run(tmp_path, "--done-line", _done(sha, lines))
    finally:
        doc.chmod(0o644)
    if r.returncode == 0:  # running as root, where the chmod does not bite
        pytest.skip("artifact stayed readable — cannot exercise the permission path")
    assert r.returncode == 2, r.stdout
    assert "DONEGATE: UNREADABLE reason=artifact_unreadable" in r.stdout


def test_an_absent_repo_is_UNREADABLE(tmp_path: Path) -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(tmp_path / "nowhere"),
         "--done-line", "SPEC-AUTHOR: DONE path=x sha256=" + "a" * 64],
        capture_output=True, text=True)
    assert r.returncode == 2
    assert "reason=repo_absent" in r.stdout


# --- doctrine: the rule must exist on BOTH sides -------------------------------
#
# The gap this closes was not a bug in a script; it was a contract that existed
# only in hand-written dispatch prompts. So the agent-side rule and the
# orchestrator-side gate are pinned here as literals, the way
# `test_h_mad_agent_definitions.py` pins the r17 and REPORT= rules.


@pytest.mark.parametrize("name", ALL_AGENTS)
def test_the_agent_requires_the_digest_on_its_done_line(name: str) -> None:
    body = _norm(AGENTS / f"{name}.md")
    assert "line count and sha256, derived AFTER" in body, name
    assert "an instant, not a state" in body, name
    # The exact commands, so author and orchestrator measure the same thing.
    assert "shasum -a 256 \"$F\" | awk '{print $1}'" in body, name
    assert 'wc -l < "$F"' in body, name


@pytest.mark.parametrize("name", ALL_AGENTS)
def test_the_agent_says_lines_is_a_cross_check_and_not_the_gate(name: str) -> None:
    """Without this the units trap becomes a build failure the first time it fires."""
    body = _norm(AGENTS / f"{name}.md")
    assert "`sha256=` is the gate; `lines=` is a cross-check" in body, name


@pytest.mark.parametrize("name", AUTHORS)
def test_an_author_hashes_the_document_so_REPORT_none_does_not_weaken_it(name: str) -> None:
    """The brief's open question, answered at the site rather than left implicit."""
    body = _norm(AGENTS / f"{name}.md")
    assert "Hash the **document**, never your report file" in body, name
    assert "`REPORT=<none>` does not weaken this" in body, name


def test_the_auditor_hashes_its_report_and_has_no_none_variant() -> None:
    """`doc-auditor`'s deliverable IS the report; it must not hash someone else's doc."""
    body = _norm(AGENTS / "doc-auditor.md")
    assert "You hash the **report**, not the audited document" in body
    assert "you have no `<none>` variant" in body
    # Ordering matters: the marker is what tells the orchestrator the file is done.
    assert "BEFORE you create the `.done` marker" in body


@pytest.mark.parametrize("name,done", [
    ("spec-author", "SPEC-AUTHOR: DONE version=v1.N path=<the document you wrote> "
                    "lines=N sha256=<64 hex>"),
    ("plan-author", "PLAN-AUTHOR: DONE version=v1.N path=<the document you wrote> "
                    "lines=N sha256=<64 hex>"),
    ("design-author", "DESIGN-AUTHOR: DONE version=v1.N path=<the document you wrote> "
                      "lines=N sha256=<64 hex>"),
    ("implplan-author", "IMPLPLAN-AUTHOR: DONE version=v1.N tasks=N wiring=N "
                        "mutation_rows=N path=<the document you wrote> lines=N "
                        "sha256=<64 hex>"),
    ("doc-auditor", "DOC-AUDITOR: DONE must=N should=N nit=N path=<REPORT> lines=N "
                    "sha256=<64 hex>"),
])
def test_the_done_template_carries_the_three_fields(name: str, done: str) -> None:
    """The TEMPLATE, not the prose around it — an author copies the template."""
    assert done in _norm(AGENTS / f"{name}.md"), name


def test_the_orchestrator_owns_rule_6_and_names_the_gate() -> None:
    body = _norm(SKILL)
    assert ("Re-derive the artifact's sha256 and refuse a mismatch, BEFORE you read "
            "`$RP` or commit.") in body
    assert "h_mad_done_gate.py" in body
    assert "`DONEGATE:`" in body
    # `set -e` is inert in the Bash tool's top-level shell, so the explicit form is
    # the rule, not a stylistic preference. A bare call falls through on FAIL.
    assert "|| exit 1" in body
    assert "`set -e` is inert in the Bash tool's top-level shell" in body


def test_rule_6_says_what_a_mismatch_MEANS() -> None:
    """A halt that only reports `sha_mismatch` invites the wrong diagnosis.

    The obvious reading is a lying author; the real cause is almost always the
    orchestrator's own post-DONE dispatch making the author write again.
    """
    body = _norm(SKILL)
    assert "It is almost never a lying author." in body
    assert "your own post-DONE dispatch" in body


def test_rule_6_keeps_the_cannot_judge_distinct_from_the_refutation() -> None:
    body = _norm(SKILL)
    assert "`UNREADABLE` exits 2 because it is a cannot-judge" in body
    assert "`FAIL reason=artifact_absent`, not `UNREADABLE`" in body


def test_the_rule_count_matches_the_rules_that_follow() -> None:
    """It read "Four rules" beside five from the day rule 5 landed.

    A stale count in the sentence that introduces a list is the cheapest possible
    way to make a reader stop early, and nothing pinned it.
    """
    text = SKILL.read_text(encoding="utf-8")
    heading = "**Author dispatch rules the ORCHESTRATOR owns.**"
    assert heading in text
    section = text.split(heading, 1)[1]
    # The list ends at the next `### ` heading.
    section = section.split("\n### ", 1)[0]
    numbered = [ln for ln in section.splitlines()
                if len(ln) > 2 and ln[0].isdigit() and ln[1] == "." and ln[2] == " "]
    assert len(numbered) == 6, [ln[:40] for ln in numbered]
    assert "Six rules" in section.split("\n1. ", 1)[0]


def test_the_script_is_registered_in_the_skill_inventory() -> None:
    """An unlisted script is one nobody finds — the inventory is the index."""
    assert "- `h_mad_done_gate.py` —" in SKILL.read_text(encoding="utf-8")
