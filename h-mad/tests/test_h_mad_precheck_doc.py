"""Phase-document pre-dispatch precheck (#20).

The class this closes: a share of every first audit cycle's findings are premises a
`grep` would have refuted BEFORE the prompt was assembled, and each one costs a full
dual-surface cycle (two dispatches, ~4 min wall) to discover.

The acceptance corpus is REAL, not tidy: `doc-block-exec.impl-plan.md` at `f6345c4`
(v1.31), which impl-plan audit cycle 33 reviewed. Its top must-fix was six stale
`h-mad/SKILL.md` line pins, and one of its nits was a provenance sha that had moved.
Today's v1.36 is the control: the same detectors must be quiet on it.

Every detector has a test that fails when that detector is removed. `ALL_CAUGHT`
without a per-detector assertion is a wrong-catcher hole.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "h-mad" / "scripts" / "h_mad_precheck_doc.py"


def run(*args, cwd=None):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO),
    )
    return r


def token(out):
    """The PRECHECK: line. Read the token, never `$?`."""
    for line in out.splitlines():
        if line.startswith("PRECHECK:"):
            return line
    return ""


def details(out, kind):
    return [l for l in out.splitlines() if l.startswith(f"{kind}:")]


def write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body)
    return p


# --------------------------------------------------------------------------
# Contract: token discipline
# --------------------------------------------------------------------------


def test_emits_a_verdict_token_and_exits_zero_on_both_verdicts(tmp_path):
    clean = write(tmp_path, "clean.impl-plan.md", "# Doc\n\nNothing to see.\n")
    r = run(clean, "--phase", "impl-plan", "--root", REPO)
    assert r.returncode == 0, r.stderr
    assert token(r.stdout).startswith("PRECHECK: PASS"), r.stdout

    dirty = write(tmp_path, "d.impl-plan.md", "Resolve `timeout=…` before dispatch.\n")
    r2 = run(dirty, "--phase", "impl-plan", "--root", REPO)
    assert r2.returncode == 0, "a FAIL verdict is a measured outcome, not an operational error"
    assert token(r2.stdout).startswith("PRECHECK: FAIL"), r2.stdout


def test_unreadable_document_is_a_cannot_judge_not_a_pass(tmp_path):
    r = run(tmp_path / "does-not-exist.md", "--phase", "plan", "--root", REPO)
    assert r.returncode == 2, "an operational error exits 2"
    assert token(r.stdout).startswith("PRECHECK: UNREADABLE"), r.stdout
    assert "PASS" not in token(r.stdout)


def test_issue_count_in_the_token_matches_the_detail_lines(tmp_path):
    doc = write(
        tmp_path,
        "x.impl-plan.md",
        "TBD one.\nTODO two.\nFIXME three.\n",
    )
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    line = token(r.stdout)
    n = int(line.split("issues=")[1].split()[0])
    hard = [l for l in r.stdout.splitlines() if l.split(":")[0] in
            {"PLACEHOLDER", "LINEPIN", "PINDRIFT", "UNKNOWNSHA"}
            and "advisory" not in l]
    assert n == len(hard), f"token says {n}, detail lines are {len(hard)}:\n{r.stdout}"


# --------------------------------------------------------------------------
# One test per detector. Each fails if its detector is removed.
# --------------------------------------------------------------------------


def test_PATH_reports_a_missing_file_but_never_moves_the_verdict(tmp_path):
    """A planning document names files the feature will CREATE.

    Filed as a hard finding this produced 104 hits on a design document that had
    passed 83 cycles. Absence is the normal case; only a reader can tell a
    to-be-created file from a stale citation, so this reports and never blocks.
    """
    doc = write(tmp_path, "x.impl-plan.md", "Edit `h-mad/scripts/no_such_script.py` at Task 1.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "PATH"), r.stdout
    assert "no_such_script.py" in r.stdout
    assert token(r.stdout).startswith("PRECHECK: PASS"), r.stdout


def test_PATH_is_quiet_on_a_file_that_exists(tmp_path):
    doc = write(tmp_path, "x.impl-plan.md", "Edit `h-mad/scripts/h_mad_audit_gate.py` at Task 1.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert not details(r.stdout, "PATH"), r.stdout


def test_SYMBOL_reports_an_absent_symbol_but_never_blocks(tmp_path):
    doc = write(
        tmp_path,
        "x.impl-plan.md",
        "The entry point is `h-mad/scripts/h_mad_audit_gate.py:no_such_function`.\n",
    )
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "SYMBOL"), r.stdout
    assert "no_such_function" in r.stdout
    assert token(r.stdout).startswith("PRECHECK: PASS"), (
        "a planning document names symbols the feature will add:\n" + r.stdout
    )


def test_SYMBOL_is_quiet_on_a_symbol_that_exists(tmp_path):
    doc = write(
        tmp_path,
        "x.impl-plan.md",
        "The entry point is `h-mad/scripts/h_mad_audit_gate.py:classify`.\n",
    )
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert not details(r.stdout, "SYMBOL"), r.stdout


def test_PLACEHOLDER_flags_an_unresolved_slot(tmp_path):
    doc = write(tmp_path, "x.impl-plan.md", "Dispatch with `timeout=…` once decided.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "PLACEHOLDER"), r.stdout


def test_PLACEHOLDER_flags_TBD_and_TODO(tmp_path):
    doc = write(tmp_path, "x.impl-plan.md", "TBD: pick the exception.\nTODO: count the rows.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert len(details(r.stdout, "PLACEHOLDER")) == 2, r.stdout


def test_LINEPIN_is_reported_for_every_phase(tmp_path):
    """Reported, not blocking.

    The author contracts say never write a line number, but the documents in this
    tree carry them by the dozen — 49 on a plan that had passed 74 cycles. A gate
    that fails every real document is not a gate, so an ordinary pin is surfaced
    for triage and only a PROVABLY wrong one (past end-of-file, or drifted since
    the document's own provenance commit) moves the verdict.
    """
    body = "The heading is at `h-mad/SKILL.md:1897`.\n"
    for phase in ("design", "plan", "impl-plan"):
        doc = write(tmp_path, f"x.{phase}.md", body)
        r = run(doc, "--phase", phase, "--root", REPO)
        assert details(r.stdout, "LINEPIN"), f"{phase}: {r.stdout}"


def test_LINEPIN_catches_the_bare_colon_form_the_c33_corpus_used(tmp_path):
    """Five of c33's six stale pins were written as bare `:1809`, not `path:1809`."""
    doc = write(
        tmp_path,
        "x.design.md",
        "The four fences open at `:1809`, `:1822`, `:1832` and `:1845`.\n",
    )
    r = run(doc, "--phase", "design", "--root", REPO)
    assert len(details(r.stdout, "LINEPIN")) == 4, r.stdout


def test_LINEPIN_past_end_of_file_is_a_hard_finding_even_for_impl_plan(tmp_path):
    doc = write(tmp_path, "x.impl-plan.md", "See `h-mad/scripts/h_mad_audit_gate.py:999999`.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "LINEPIN"), r.stdout
    assert "past_eof" in r.stdout


def test_STALESHA_reports_a_behind_HEAD_provenance_but_never_blocks(tmp_path):
    """Behind-HEAD is the NORMAL condition of every written measurement.

    Filed as a hard finding it fires on every correctly-provenanced number in the
    tree — the plan and impl-plan carry `1861157` and `b7d0d77` on measurement after
    measurement, all of them properly cited. Only a reader knows whether the thing
    measured has since changed, so this reports and never blocks.
    """
    head_parent = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD~1"],
        cwd=str(REPO), capture_output=True, text=True,
    ).stdout.strip()
    doc = write(tmp_path, "x.impl-plan.md", f"Anchors verified at HEAD `{head_parent}`.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "STALESHA"), r.stdout
    assert token(r.stdout).startswith("PRECHECK: PASS"), r.stdout


def test_UNKNOWNSHA_is_hard_when_the_commit_is_not_in_this_repository(tmp_path):
    """A sha naming no commit here cannot have been measured at."""
    doc = write(tmp_path, "x.impl-plan.md", "Anchors verified at HEAD `deadbee`.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "UNKNOWNSHA"), r.stdout
    assert token(r.stdout).startswith("PRECHECK: FAIL"), r.stdout


def test_STALESHA_is_quiet_when_the_provenance_commit_is_HEAD(tmp_path):
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(REPO), capture_output=True, text=True,
    ).stdout.strip()
    doc = write(tmp_path, "x.impl-plan.md", f"Anchors verified at HEAD `{head}`.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert not details(r.stdout, "STALESHA"), r.stdout


def test_COUNT_is_advisory_and_never_moves_the_verdict(tmp_path):
    """An unproven heuristic reports; it never blocks. Same rule as `wire_registry challenge`."""
    doc = write(
        tmp_path,
        "x.impl-plan.md",
        "Task 1 lists the 3 exception classes:\n\n- Alpha\n- Beta\n- Gamma\n- Delta\n",
    )
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(r.stdout, "COUNT"), "the mismatch should be reported"
    assert token(r.stdout).startswith("PRECHECK: PASS"), (
        "a COUNT line must not turn a clean document into a FAIL:\n" + r.stdout
    )


# --------------------------------------------------------------------------
# `--allow` is an input, never inferred
# --------------------------------------------------------------------------


def test_allow_suppresses_a_hit_and_is_reported_as_allowed(tmp_path):
    doc = write(tmp_path, "x.impl-plan.md", "Dispatch with `timeout=…` once decided.\n")
    before = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert details(before.stdout, "PLACEHOLDER")

    after = run(doc, "--phase", "impl-plan", "--root", REPO, "--allow", "timeout=…")
    assert not details(after.stdout, "PLACEHOLDER"), after.stdout
    assert "ALLOWED:" in after.stdout, "an allowed hit is named, never silently dropped"
    assert token(after.stdout).startswith("PRECHECK: PASS")


# --------------------------------------------------------------------------
# Acceptance against the REAL c33 corpus, its control, and a noise floor
# --------------------------------------------------------------------------


CORPUS_SHA = "f6345c4"
IMPL_PLAN = "docs/01-plan/features/doc-block-exec.impl-plan.md"


@pytest.fixture(scope="module")
def c33_corpus(tmp_path_factory):
    """impl-plan v1.31 — the document audit cycle 33 actually reviewed."""
    r = subprocess.run(
        ["git", "show", f"{CORPUS_SHA}:{IMPL_PLAN}"],
        cwd=str(REPO), capture_output=True, text=True,
    )
    if r.returncode != 0:
        pytest.skip(f"corpus commit {CORPUS_SHA} not in this clone")
    p = tmp_path_factory.mktemp("corpus") / "c33.impl-plan.md"
    p.write_text(r.stdout)
    return p


def test_corpus_c33_the_six_stale_line_pins_are_caught(c33_corpus):
    """c33's top must-fix: six SKILL.md line pins, stale by 93 lines.

    One is written `h-mad/SKILL.md:1804`; the other five are bare `:1809` etc.
    """
    r = run(c33_corpus, "--phase", "design", "--root", REPO)
    pins = details(r.stdout, "LINEPIN") + details(r.stdout, "PINDRIFT")
    joined = "\n".join(pins)
    for n in ("1804", "1809", "1822", "1832", "1845", "1850"):
        assert n in joined, f"missed the stale pin :{n}\n{joined}"


def test_corpus_c33_the_stale_provenance_sha_is_caught(c33_corpus):
    """c33 nit: `verified at HEAD 8599e28` when HEAD had moved.

    It is reported as an advisory, matching the severity the audit itself gave it.
    """
    r = run(c33_corpus, "--phase", "impl-plan", "--root", REPO)
    assert "8599e28" in r.stdout, r.stdout[:2000]


def test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins(c33_corpus):
    """The control. I first wrote this asserting v1.36 carries NO line pins; that
    premise was false and the test caught me — it still carries short pins into
    `docsections.py`. What c33 actually fixed is the six `h-mad/SKILL.md` pins, so
    that is what the control asserts.

    A detector that fires identically on corpus and control has learned nothing.
    """
    r = run(REPO / IMPL_PLAN, "--phase", "design", "--root", REPO)
    joined = "\n".join(details(r.stdout, "LINEPIN"))
    # The path-qualified form is what c33 flagged and what v1.36 removed.
    assert "SKILL.md:" not in joined, joined
    # A bare `:1804` DOES survive — in a paragraph narrating that very staleness
    # ("the heading sat at `:1804` … at `:1897` at `b7d0d77`"). A document
    # explaining a stale pin legitimately quotes the stale number, which no
    # detector can distinguish from the defect. That residual is stated, not
    # engineered around: it is why LINEPIN is a finding a reader triages rather
    # than an error, and why `--allow` exists.
    # I also asserted here that the corpus carries strictly MORE pins than the
    # control. Measured, that is false: 42 in the corpus against 53 today. v1.36
    # removed the six SKILL.md pins and added shorter ones elsewhere. The count is
    # not the signal; the path-qualified form is, and it is asserted above.


@pytest.mark.parametrize(
    "doc,phase",
    [
        ("docs/02-design/features/doc-block-exec.design.md", "design"),
        ("docs/01-plan/features/doc-block-exec.plan.md", "plan"),
        ("docs/01-plan/features/doc-block-exec.impl-plan.md", "impl-plan"),
    ],
)
def test_noise_floor_on_documents_that_survived_eighty_cycles(doc, phase):
    """A detector too noisy to gate must be discovered HERE, not at a dispatch.

    These three documents passed 83/74/34 audit cycles. A double-digit hard-finding
    count on any of them means the detector is measuring style, not defects — and the
    number is asserted rather than eyeballed so a regression in precision is loud.
    """
    p = REPO / doc
    if not p.exists():
        pytest.skip(f"{doc} absent")
    r = run(p, "--phase", phase, "--root", REPO)
    hard = [l for l in r.stdout.splitlines()
            if l.split(":")[0] in {"PLACEHOLDER", "LINEPIN", "PINDRIFT", "UNKNOWNSHA"}
            and "advisory" not in l]
    assert len(hard) <= 12, (
        f"{doc}: {len(hard)} hard findings — too noisy to gate on:\n"
        + "\n".join(hard[:20])
    )


def test_json_output_carries_the_same_verdict_as_the_token(tmp_path):
    doc = write(tmp_path, "x.impl-plan.md", "TBD: decide.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO, "--json")
    payload = json.loads(r.stdout)
    assert payload["verdict"] == "FAIL"
    assert payload["issues"] == len(payload["findings"])
