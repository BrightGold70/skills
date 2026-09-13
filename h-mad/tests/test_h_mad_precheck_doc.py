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

sys.path.insert(0, str(SCRIPT.parent))
from h_mad_precheck_doc import HARD_KINDS  # noqa: E402

# `HARD_KINDS` was defined at :93 and read by NOTHING — the script decides hardness
# by which list a hit is appended to, and both filters below used to spell the set
# out as their own literal. That duplication is what made a mutation of the constant
# look like a behavioural change; it survived, correctly, because the constant is
# inert. Importing it here gives the name one consumer, so the two sets cannot drift
# from each other again. It still does not drive the script — see the filed row.


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
    hard = [l for l in r.stdout.splitlines() if l.split(":")[0] in set(HARD_KINDS)
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
        # "Reported, not blocking" is half this test's own docstring and was never
        # asserted: `details()` matches the printed line, which looks identical
        # whether the hit landed in `findings` or `advisories`. Promoting this
        # branch to a hard finding therefore survived the mutation battery — and it
        # is the cannot-judge direction, where the document carries no provenance
        # sha to measure drift against. "I could not check" must not be scored as
        # "it is broken".
        assert token(r.stdout).startswith("PRECHECK: PASS"), (
            f"{phase}: an unprovenanced pin must not move the verdict\n{r.stdout}")


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


def test_PINDRIFT_fires_when_a_pinned_file_changed_since_the_provenance(tmp_path):
    """PINDRIFT had NO test of its own until 2026-09-07, though it is one of the
    four hard kinds.

    Its only exercise was being counted by the noise-floor test at the bottom of
    this file, and `test_corpus_c33_the_six_stale_line_pins_are_caught` accepts a
    hit under EITHER `LINEPIN` or `PINDRIFT`, so neither discriminated it. When the
    floor stopped counting PINDRIFT — it measures tree drift against a frozen
    document, not document quality — that would have left the detector with zero
    behavioural coverage. Found by asking what the floor change cost before making
    it, which is the "name the observation that differs" rule applied to a test.
    """
    changed = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", "h-mad/scripts/h_mad_precheck_doc.py"],
        cwd=str(REPO), capture_output=True, text=True,
    ).stdout.strip()
    older = subprocess.run(
        ["git", "rev-parse", "--short", f"{changed}~1"],
        cwd=str(REPO), capture_output=True, text=True,
    ).stdout.strip()
    if not older:
        pytest.skip("no commit before the last change to the pinned file")
    doc = write(
        tmp_path, "x.impl-plan.md",
        f"Anchors verified at HEAD `{older}`.\n\n"
        "See `h-mad/scripts/h_mad_precheck_doc.py:1` for the scanner.\n",
    )
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    hits = details(r.stdout, "PINDRIFT")
    assert hits, r.stdout
    assert "h_mad_precheck_doc.py" in "\n".join(hits), hits
    assert token(r.stdout).startswith("PRECHECK: FAIL"), r.stdout


def test_PINDRIFT_is_quiet_when_the_pinned_file_has_not_moved(tmp_path):
    """The other direction. Without this the detector could fire unconditionally
    and the test above would still pass — a criterion that cannot discriminate in
    either direction is vacuous (`invariants.base.md` §Test discrimination)."""
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(REPO), capture_output=True, text=True,
    ).stdout.strip()
    doc = write(
        tmp_path, "x.impl-plan.md",
        f"Anchors verified at HEAD `{head}`.\n\n"
        "See `h-mad/scripts/h_mad_precheck_doc.py:1` for the scanner.\n",
    )
    r = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert not details(r.stdout, "PINDRIFT"), r.stdout


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
        # Archived 2026-09-07 when Phase 7c was completed for this closed feature:
        # the calibration corpus follows the documents. They are the same three
        # that survived 80+ audit cycles, which is what the floor calibrates.
        ("docs/archive/2026-09/doc-block-exec/doc-block-exec.design.md", "design"),
        ("docs/archive/2026-09/doc-block-exec/doc-block-exec.plan.md", "plan"),
        ("docs/archive/2026-09/doc-block-exec/doc-block-exec.impl-plan.md", "impl-plan"),
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
    # PINDRIFT is deliberately NOT counted here, and this is the one detector
    # exclusion in the file. The floor asks "is this detector measuring style
    # rather than defects?" — a property of the DOCUMENT. These three documents are
    # archived and frozen, so their PINDRIFT count measures how far the TREE has
    # moved since the freeze: every later commit touching any pinned file adds one,
    # without the document changing at all. It is therefore monotonically
    # increasing and unrelated to precision.
    #
    # Measured 2026-09-07: the impl-plan stood at 11 PLACEHOLDER + 2 PINDRIFT = 13
    # against a ceiling of 12, and the suite went red on `88cea92` — a commit to
    # `handoff/scripts/test_handover_docs.py`, which this archived document happens
    # to pin. `85fe94a` was green at 12, i.e. exactly at the boundary, so one
    # ordinary commit tipped it. Raising the ceiling would buy a few commits and
    # recur; this is the third time this shape has been recorded.
    # PINDRIFT keeps its own two tests above (added in the same change, because it
    # had NONE and this count was its only exercise).
    hard = [l for l in r.stdout.splitlines()
            if l.split(":")[0] in set(HARD_KINDS) - {"PINDRIFT"}
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


def _root_commit() -> str:
    """A commit everything has changed since, so PINDRIFT fires on any real pin."""
    return subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=str(REPO), capture_output=True, text=True,
    ).stdout.strip().splitlines()[0][:7]


_TWO_PINS = (
    "See `h-mad/scripts/h_mad_precheck_doc.py:1` for the scanner.\n"
    "See `h-mad/scripts/h_mad_version_history.py:1` for the bumper.\n"
)


def test_allow_historical_demotes_ONE_pin_and_leaves_the_other_hard(tmp_path):
    """#30 option (c), and the test that makes it different from option (a).

    Raising the document's provenance sha silences EVERY PINDRIFT at once without
    repairing a single pin — measured on `gateway-consolidation.design.md`: v1.15 at
    its own tree `FAIL issues=41`, v1.16 `PASS issues=0` purely because it named
    HEAD, 26 findings gone advisory and zero pins repaired. So the detector's green
    got strongest exactly as the document rotted.

    A declared-historical pin must therefore be demoted ALONE. If the flag demoted
    everything it would be provenance-raising with extra steps.
    """
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md", f"Anchors verified at HEAD `{older}`.\n\n" + _TWO_PINS)

    both = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert len(details(both.stdout, "PINDRIFT")) == 2, both.stdout

    one = run(doc, "--phase", "impl-plan", "--root", REPO,
              "--allow-historical", "h_mad_precheck_doc.py:1")
    hits = details(one.stdout, "PINDRIFT")
    assert len(hits) == 1, hits
    assert "h_mad_version_history.py" in "\n".join(hits), hits
    assert token(one.stdout).startswith("PRECHECK: FAIL"), one.stdout


_TWO_PINS_ONE_FILE = (
    "See `h-mad/scripts/h_mad_precheck_doc.py:1` for the head.\n"
    "See `h-mad/scripts/h_mad_precheck_doc.py:12` for the rest.\n"
)


def test_allow_historical_does_not_silence_a_pin_whose_line_is_a_PREFIX(tmp_path):
    """The collision `_TWO_PINS` structurally cannot express, because it uses two
    DIFFERENT files — so every same-file interaction was untested.

    `historical_by` matched with `in`, and the span it is handed ends with the pin.
    So declaring `…py:1` also matched `…py:12`, `…py:150`, and every other
    `…py:1*`: one declaration silenced a whole family of undeclared pins and the
    verdict flipped FAIL issues=2 -> PASS issues=0. That is the mass-silencing this
    flag exists to REPLACE, reappearing inside the replacement.

    Both halves are asserted, because a fix that merely stopped demoting would pass
    the first and break the feature: the declared pin must still go, and only it.
    """
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md",
                f"Anchors verified at HEAD `{older}`.\n\n" + _TWO_PINS_ONE_FILE)

    both = run(doc, "--phase", "impl-plan", "--root", REPO)
    assert len(details(both.stdout, "PINDRIFT")) == 2, both.stdout

    one = run(doc, "--phase", "impl-plan", "--root", REPO,
              "--allow-historical", "h_mad_precheck_doc.py:1")
    hits = details(one.stdout, "PINDRIFT")
    assert len(hits) == 1, (
        "declaring `:1` historical must not also silence `:12` — that is "
        f"provenance-raising with extra steps: {hits}")
    assert ":12" in "\n".join(hits), hits
    assert token(one.stdout).startswith("PRECHECK: FAIL"), one.stdout


def test_allow_historical_still_matches_a_bare_filename_not_only_the_full_path(tmp_path):
    """The anchoring must not become equality. The documented and tested input is a
    BARE filename, while the span the caller builds is repo-relative — so a strict
    `==` would silently stop demoting anything and every existing caller would find
    its declarations ignored, with no error to say so."""
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md",
                f"Anchors verified at HEAD `{older}`.\n\n" + _TWO_PINS_ONE_FILE)
    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "h_mad_precheck_doc.py")
    assert not details(r.stdout, "PINDRIFT"), (
        "a bare filename must still demote the whole file", r.stdout)


def test_allow_historical_accepts_a_token_written_with_a_LEADING_SLASH(tmp_path):
    """A declaration that is ignored without an error is worse than one refused.

    Under the old `in` a token written `/h_mad_precheck_doc.py:1` matched; the
    anchor silently stopped it, because the span cannot end with `//…`. The
    operator sees the pin still reported as a finding and concludes the flag is
    broken — which is exactly the silent-ignore this spec's own
    `the-anchor-tightens-to-equality` mutation describes, reintroduced by the fix
    for the opposite defect.
    """
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md",
                f"Anchors verified at HEAD `{older}`.\n\n"
                "See `h-mad/scripts/h_mad_precheck_doc.py:1` for the head.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "/h_mad_precheck_doc.py:1")
    assert not details(r.stdout, "PINDRIFT"), (
        "a leading slash must not silently disable the declaration", r.stdout)


def test_allow_historical_does_not_match_a_bare_filename_SUFFIX_of_another(tmp_path):
    """The `/` in the anchor, and the only test that can see it.

    A suffix match with no path boundary is nearly right: it fixes the `:1`/`:12`
    prefix collision, so every other test here passes under it. What it still gets
    wrong is a DIFFERENT file whose name merely ends the same way — `precheck_doc.py`
    is a suffix of `h_mad_precheck_doc.py`, so declaring the former would silence a
    pin into the latter.

    Verified to discriminate: the `the-path-boundary-is-dropped` mutation SURVIVED
    the whole suite before this test existed, including
    `test_allow_historical_demotes_ONE_pin_and_leaves_the_other_hard` — that one uses
    two unrelated filename stems, so no suffix collision is reachable through it.
    A mutation the suite does not notice is a guard that does not bite.
    """
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md",
                f"Anchors verified at HEAD `{older}`.\n\n"
                "See `h-mad/scripts/h_mad_precheck_doc.py:1` for the head.\n")

    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "precheck_doc.py:1")
    assert len(details(r.stdout, "PINDRIFT")) == 1, (
        "`precheck_doc.py:1` is a bare SUFFIX of `h_mad_precheck_doc.py:1`, a "
        "different file — declaring it must silence nothing", r.stdout)


def test_allow_historical_clears_the_verdict_when_every_drifted_pin_is_declared(tmp_path):
    """Declaring all of them is legitimate and must reach PASS — otherwise the flag
    is unusable and authors go back to raising provenance, which is the defect."""
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md", f"Anchors verified at HEAD `{older}`.\n\n" + _TWO_PINS)
    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "h_mad_precheck_doc.py",
            "--allow-historical", "h_mad_version_history.py")
    assert not details(r.stdout, "PINDRIFT"), r.stdout


def test_a_declared_historical_pin_is_REPORTED_not_silently_dropped(tmp_path):
    """`allowed` exists so a suppression is visible. A demotion nobody can see is
    indistinguishable from a detector that never fired."""
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md", f"Anchors verified at HEAD `{older}`.\n\n" + _TWO_PINS)
    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "h_mad_precheck_doc.py:1")
    assert "PINDRIFT" in r.stdout and "declared historical" in r.stdout, r.stdout


def test_a_non_matching_allow_historical_demotes_nothing(tmp_path):
    """The control. A substring that matches no pin must leave the verdict alone, or
    the flag would be a blanket switch wearing a per-pin costume."""
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md", f"Anchors verified at HEAD `{older}`.\n\n" + _TWO_PINS)
    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "no_such_file.py")
    assert len(details(r.stdout, "PINDRIFT")) == 2, r.stdout
    assert token(r.stdout).startswith("PRECHECK: FAIL"), r.stdout


def test_allow_historical_does_not_touch_the_other_hard_kinds(tmp_path):
    """Scoped to PINDRIFT. A pin past end-of-file is provably wrong whatever the
    provenance says, and no declaration should reach it."""
    older = _root_commit()
    doc = write(tmp_path, "x.impl-plan.md",
                f"Anchors verified at HEAD `{older}`.\n\n"
                "See `h-mad/scripts/h_mad_precheck_doc.py:999999` for the scanner.\n")
    r = run(doc, "--phase", "impl-plan", "--root", REPO,
            "--allow-historical", "h_mad_precheck_doc.py")
    assert details(r.stdout, "LINEPIN"), r.stdout
    assert token(r.stdout).startswith("PRECHECK: FAIL"), r.stdout


class TestTheLinePinAdvisoryTellsTheTruthAboutWhatItChecked:
    """The arm reported a VERIFIED-CLEAN pin as one it could not judge.

    `else` was reached in two cases: `prov is None` (genuinely unjudgeable) and `prov`
    present with `_changed_since` False (checked, clean). Both printed "line pin with
    no provenance commit to check it against" — while a PINDRIFT finding on the next
    line of the same output named that very sha. The arm destroyed exactly the
    distinction its own comment exists to preserve: "I could not check" is not "it is
    fine", and here "it is fine" was printed as "I could not check".
    """

    def _repo(self, tmp_path):
        import subprocess as sp
        r = tmp_path / "r"
        (r / "sub").mkdir(parents=True)
        sp.run(["git", "init", "-q", "-b", "main", str(r)], check=True, capture_output=True)
        (r / "sub" / "f.py").write_text("a\nb\nc\nd\n", encoding="utf-8")
        (r / "sub" / "other.py").write_text("x\ny\n", encoding="utf-8")
        g = lambda *a: sp.run(["git", "-C", str(r), *a], check=True, capture_output=True, text=True)
        g("add", "-A"); g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "one")
        prov = g("rev-parse", "HEAD").stdout.strip()
        (r / "sub" / "other.py").write_text("x\ny\nz-CHANGED\n", encoding="utf-8")
        g("add", "-A"); g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "two")
        doc = r / "doc.md"
        doc.write_text(
            f"# D\n\nMeasured at `{prov}`.\n\n"
            "UNCHANGED file pin `sub/f.py:3`.\nCHANGED file pin `sub/other.py:2`.\n",
            encoding="utf-8")
        return r, doc, prov

    def test_a_checked_and_clean_pin_names_the_sha_it_was_checked_against(self, tmp_path):
        r, doc, prov = self._repo(tmp_path)

        out = run(doc, "--phase", "design", "--root", r).stdout
        linepin = [ln for ln in out.splitlines() if "LINEPIN" in ln]
        assert len(linepin) == 1, out

        assert "no provenance commit" not in linepin[0], (
            "a pin checked against a real provenance sha is reported as having none:\n"
            + out)
        assert "unchanged since" in linepin[0], linepin[0]
        assert prov[:7] in linepin[0], (
            "the advisory must name the sha it measured against\n" + linepin[0])

    def test_the_two_advisories_cannot_contradict_the_same_output(self, tmp_path):
        """The tell that made this findable: PINDRIFT and LINEPIN in ONE run disagreed
        about whether a provenance commit existed."""
        r, doc, prov = self._repo(tmp_path)

        out = run(doc, "--phase", "design", "--root", r).stdout
        assert "PINDRIFT" in out and prov[:7] in out, out
        pindrift = [ln for ln in out.splitlines() if "PINDRIFT" in ln][0]
        linepin = [ln for ln in out.splitlines() if "LINEPIN" in ln][0]
        assert prov[:7] in pindrift and prov[:7] in linepin, (
            "one run, two lines, disagreeing about whether a provenance sha exists:\n"
            f"{pindrift}\n{linepin}")

    def test_with_NO_provenance_the_cannot_judge_message_is_kept(self, tmp_path):
        """The honest case must keep its honest wording — the fix splits the arm, it
        does not relabel everything as checked."""
        r, doc, _prov = self._repo(tmp_path)
        doc.write_text("# D\n\nNo provenance here.\n\nPin `sub/f.py:3`.\n",
                       encoding="utf-8")

        out = run(doc, "--phase", "design", "--root", r).stdout
        linepin = [ln for ln in out.splitlines() if "LINEPIN" in ln]
        assert len(linepin) == 1, out
        assert "no provenance commit to check it against" in linepin[0], linepin[0]
        assert "unchanged since" not in linepin[0], linepin[0]

    def test_the_verdict_and_the_advisory_count_do_not_move(self, tmp_path):
        """Same kind, same count, advisory either way — only the sentence changed. A
        verdict shift here would be a different change needing its own argument."""
        r, doc, _prov = self._repo(tmp_path)

        out = run(doc, "--phase", "design", "--root", r).stdout
        assert "PRECHECK: FAIL issues=1" in out, out
        assert out.count("LINEPIN") == 1, out
        assert "advisory — does not move the verdict" in [
            ln for ln in out.splitlines() if "LINEPIN" in ln][0]
