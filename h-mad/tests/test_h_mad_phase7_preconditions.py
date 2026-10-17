"""Phase 7 merges. Nothing stopped it merging before Phase 6 ran.

SKILL.md documents 6 (verification) before 7 (closure), and 7 is what merges and
pushes. The ordering lived only as prose in a document the orchestrator trusts
itself to follow.

Observed: a feature completed Phase 5, merged to main and pushed — no gap
analysis, no architectural review, no telemetry, no archive. The suite was green,
which was the only signal anyone had, and green tests turned out to say nothing
about spec conformance: the later gap analysis measured 0%.

This gate makes the sequence checkable instead of merely documented. It reads
state and the analysis artifact; it does not merge anything itself.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_phase7_preconditions.py"
sys.path.insert(0, str(SCRIPTS))

import h_mad_phase7_preconditions as p7  # noqa: E402

READY = {
    "feature": "demo",
    "started_ts": "2026-07-22T00:00:00Z",
    "last_completed_phase": 6,
    "current_phase": 7,
    "phase": None,
    "audit_cycles": {"plan": 1, "design": 1, "impl_plan": 1},
    "iterate_cycles": 0,
    "halt_reason": None,
    "halt_ts": None,
    "archreview": "READY_TO_MERGE",
}

# FR-7: a READY record whose 6a-prime review is recorded, for guards that pin an exact warning set
# unrelated to review independence (review_independence_unrecorded would otherwise fire).
REVIEWED = dict(READY, review_independence=[{"leg": "6a-prime", "module": None, "reviewer": "agy",
                                            "implementer": "codex", "independent": True}])

ANALYSIS = "# Analysis: demo\n\n## Match Rate: 96%\n\n## Verdict\nAdvance.\n"


def codes(result):
    return {b["code"] for b in result["blockers"]}


class TestMatchRateParsing:
    def test_reads_a_percentage(self):
        assert p7.parse_match_rate("## Match Rate: 96%") == 96.0

    def test_reads_a_decimal(self):
        assert p7.parse_match_rate("## Match Rate: 89.5%") == 89.5

    def test_reads_a_bolded_zero(self):
        """The real analysis wrote **0%** — a falsy value that must not be
        mistaken for 'absent'."""
        assert p7.parse_match_rate("## Match Rate: **0%**") == 0.0

    def test_absent_rate_is_none_not_zero(self):
        assert p7.parse_match_rate("# Analysis\nno rate here") is None

    def test_takes_the_first_rate(self):
        assert p7.parse_match_rate("## Match Rate: 96%\nlater: 12%") == 96.0

    def test_reads_the_underscore_spelling_the_analysis_template_emits(self):
        """#155 — the Phase-6a awk template prints `match_rate=`; `_` is not whitespace.

        `PHASE7: match_rate_unreadable` fired on an analysis that stated its rate
        correctly in the shape the template emits, and the closure had to add a
        second prose line for the gate to read. The blocker text named a real
        hazard (no measurement) that was not the one present.
        """
        line = "Result: `satisfied=49 partial=0 not_satisfied=0 total=49 match_rate=100.00% (49/49)`."
        assert p7.parse_match_rate(line) == 100.0

    def test_the_templates_own_format_string_is_not_a_rate(self):
        """The awk command itself carries `match_rate=%.2f%%` — no digits, no match."""
        assert p7.parse_match_rate('printf "match_rate=%.2f%%"') is None


class TestCalibrationAgainstDocumentsThatAlreadyPassed:
    """Widening the regex must not move any rate a passed analysis already stated.

    Every hard detector this repo wrote fired on documents that had already passed
    audit; a widened pattern is calibrated the same way — against the live tree,
    not a fixture (§feedback: calibrate a new gate against artifacts that passed).
    """

    _NARROW = __import__("re").compile(
        r"match\s*rate\s*[:=]\s*\**\s*(\d+(?:\.\d+)?)\s*%", __import__("re").I
    )

    def _docs(self):
        root = Path(__file__).resolve().parents[2] / "docs"
        return sorted(list((root / "03-analysis").glob("*.analysis.md"))
                      + list((root / "archive").glob("*/*/*.analysis.md")))

    def test_every_rate_the_narrow_pattern_read_is_read_identically(self):
        docs = self._docs()
        assert docs, "no analysis documents found — the calibration measured nothing"
        moved = []
        for doc in docs:
            text = doc.read_text(encoding="utf-8", errors="replace")
            narrow = self._NARROW.search(text)
            wide = p7.parse_match_rate(text)
            if narrow is not None and wide != float(narrow.group(1)):
                moved.append((doc.name, narrow.group(1), wide))
        assert not moved, f"widened pattern moved a passed rate: {moved}"

    def test_the_doc_block_exec_analysis_reads_100(self):
        """Located by glob: Phase 7 archives `docs/03-analysis/<feature>*`."""
        docs = Path(__file__).resolve().parents[2] / "docs"
        found = [p for p in docs.glob("**/doc-block-exec.analysis.md")]
        assert found, "doc-block-exec.analysis.md is gone from docs/ entirely"
        for doc in found:
            assert p7.parse_match_rate(doc.read_text(encoding="utf-8")) == 100.0, doc


class TestBlockers:
    def test_ready_state_passes(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        assert p7.check(READY, a)["ready"] is True

    def test_phase_below_6_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, last_completed_phase=5)
        assert "verification_not_run" in codes(p7.check(rec, a))

    def test_missing_analysis_blocks(self, tmp_path):
        assert "analysis_missing" in codes(p7.check(READY, tmp_path / "nope.md"))

    def test_low_match_rate_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text("## Match Rate: 42%")
        assert "match_rate_below_threshold" in codes(p7.check(READY, a))

    def test_zero_match_rate_blocks(self, tmp_path):
        """The exact observed case. A falsy rate must block, not skip the check."""
        a = tmp_path / "demo.analysis.md"
        a.write_text("## Match Rate: **0%**")
        assert "match_rate_below_threshold" in codes(p7.check(READY, a))

    def test_unparseable_rate_blocks(self, tmp_path):
        """An analysis with no measurement is not evidence of a passing one."""
        a = tmp_path / "demo.analysis.md"
        a.write_text("# Analysis: demo\nlooks fine to me")
        assert "match_rate_unreadable" in codes(p7.check(READY, a))

    def test_open_halt_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, halt_reason="step6a:x")
        assert "halted" in codes(p7.check(rec, a))

    def test_blockers_accumulate(self, tmp_path):
        rec = dict(READY, last_completed_phase=4, halt_reason="step5:x")
        result = p7.check(rec, tmp_path / "nope.md")
        assert len(result["blockers"]) >= 3
        assert result["ready"] is False


class TestArchreviewLadder:
    """Archreview outcomes have distinct gate and reporting semantics."""

    def test_missing_archreview_blocks_as_not_run(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY)
        rec.pop("archreview")
        result = p7.check(rec, a)
        assert result["ready"] is False
        assert "archreview_not_run" in codes(result)

    def test_null_archreview_blocks_as_not_run(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview=None)
        result = p7.check(rec, a)
        assert result["ready"] is False
        assert "archreview_not_run" in codes(result)

    def test_missing_archreview_blocker_explains_how_to_populate_it(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY)
        rec.pop("archreview")
        result = p7.check(rec, a)
        blocker = next(
            b for b in result["blockers"] if b["code"] == "archreview_not_run"
        )
        detail = blocker["detail"]
        assert "archreview" in detail
        assert "6a-prime" in detail
        assert "record" in detail.lower()

    def test_unknown_skipped_archreview_blocks_without_warning(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_FOO")
        result = p7.check(rec, a)
        assert result["ready"] is False
        assert "archreview_not_run" in codes(result)
        assert all(w["code"] != "archreview_not_run" for w in result["warnings"])

    def test_only_explicit_passes_are_ready_across_archreview_values(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        cases = [
            ("READY_TO_MERGE", True),
            ("WITH_FIXES", False),
            ("NO", False),
            ("SKIPPED_NO_PANE", False),
            ("SKIPPED_OPERATOR_OVERRIDE", True),
            ("SKIPPED_FOO", False),
            (None, False),
            ("__ABSENT__", False),
        ]
        observed = []
        for value, expected_ready in cases:
            rec = dict(READY)
            if value == "__ABSENT__":
                rec.pop("archreview")
            else:
                rec["archreview"] = value
            observed.append((value, p7.check(rec, a)["ready"], expected_ready))
        assert observed == [(value, expected, expected) for value, expected in cases]

    def test_skipped_archreview_blocks(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_NO_PANE")
        result = p7.check(rec, a)
        assert result["ready"] is False
        assert "archreview_skipped" in codes(result)

    def test_skipped_archreview_is_a_blocker_not_a_warning(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_NO_PANE")
        result = p7.check(rec, a)
        assert any(b["code"] == "archreview_skipped" for b in result["blockers"])
        assert all(w["code"] != "archreview_skipped" for w in result["warnings"])

    def test_skipped_archreview_blocker_points_to_headless_review(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_NO_PANE")
        result = p7.check(rec, a)
        blocker = next(b for b in result["blockers"] if b["code"] == "archreview_skipped")
        assert "exec agy" in blocker["detail"]
        assert "satisfies the gate" in blocker["detail"]

    def test_failed_archreview_does_block(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="NO")
        assert "archreview_failed" in codes(p7.check(rec, a))

    def test_operator_override_is_ready_with_warning(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_OPERATOR_OVERRIDE")
        result = p7.check(rec, a)
        assert result["ready"] is True
        assert any(
            warning["code"] == "archreview_overridden"
            for warning in result["warnings"]
        ), "operator override must be surfaced as a warning"

    def test_operator_override_warning_requires_phase7_report_disclosure(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        rec = dict(READY, archreview="SKIPPED_OPERATOR_OVERRIDE")
        result = p7.check(rec, a)
        assert any(
            "Phase 7 report" in warning["detail"]
            and "not READY_TO_MERGE" in warning["detail"]
            for warning in result["warnings"]
        ), "override warning must disclose the Phase 7 report and non-READY status"


class TestCli:
    def store(self, tmp_path, rec):
        p = tmp_path / "state.json"
        p.write_text(json.dumps({"version": 1, "orchestrator_state": {"demo": rec}}))
        return p

    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *[str(a) for a in args]],
            capture_output=True, text=True,
        )

    def test_ready_prints_token_and_exits_0(self, tmp_path):
        a = tmp_path / "demo.analysis.md"
        a.write_text(ANALYSIS)
        versioned = tmp_path / "docs" / "03-analysis" / "demo.analysis.v1.md"
        versioned.parent.mkdir(parents=True)
        versioned.write_text(ANALYSIS)
        p = self.store(tmp_path, READY)
        r = self.run(p, "--feature", "demo", "--analysis", a)
        assert r.returncode == 0
        assert "PHASE7: READY" in r.stdout

    def test_blocked_prints_reasons_and_still_exits_0(self, tmp_path):
        p = self.store(tmp_path, dict(READY, last_completed_phase=5))
        r = self.run(p, "--feature", "demo", "--analysis", tmp_path / "nope.md")
        assert r.returncode == 0, "verdict travels in the token, not the exit code"
        assert "PHASE7: BLOCKED" in r.stdout
        assert "verification_not_run" in r.stdout

    def test_emits_hmad_marker(self, tmp_path):
        p = self.store(tmp_path, dict(READY, last_completed_phase=5))
        r = self.run(p, "--feature", "demo", "--analysis", tmp_path / "nope.md")
        assert "[H-MAD]" in r.stdout

    def test_missing_feature_exits_2(self, tmp_path):
        p = self.store(tmp_path, READY)
        r = self.run(p, "--feature", "nope", "--analysis", tmp_path / "a.md")
        assert r.returncode == 2


class TestParkedMutationSpecs:
    """#142 — D2's residual. A spec parked as `<name>.json.pending` and never
    restored to `tests/mutation-specs/<name>.json` has guards nobody measured, and
    the sibling sweep cannot see it because parking moved it out of the swept dir.
    A parked copy WITH a live twin is provenance and passes (the convention says
    keep it). Anchored on the state file's docs root, never the analysis path.
    """

    def _tree(self, tmp_path, feature="demo", parked=(), live=()):
        docs = tmp_path / "docs"
        pend = docs / "03-analysis" / f"{feature}.pending-mutation-specs"
        pend.mkdir(parents=True)
        for name in parked:
            (pend / f"{name}.json.pending").write_text("{}", encoding="utf-8")
        specs = tmp_path / "proj" / "tests" / "mutation-specs"
        specs.mkdir(parents=True)
        for name in live:
            (specs / f"{name}.json").write_text("{}", encoding="utf-8")
        a = docs / "03-analysis" / f"{feature}.analysis.md"
        a.write_text(ANALYSIS, encoding="utf-8")
        (docs / "03-analysis" / f"{feature}.analysis.v1.md").write_text(ANALYSIS, encoding="utf-8")
        return a, specs, docs

    def test_a_parked_spec_with_a_live_twin_is_provenance_not_a_blocker(self, tmp_path):
        a, _, docs = self._tree(tmp_path, parked=["x"], live=["x"])
        result = p7.check(REVIEWED, a, docs_root=docs)
        assert "pending_mutation_spec_not_restored" not in codes(result)
        assert result["ready"] and not result["warnings"]

    def test_a_parked_spec_never_moved_back_blocks(self, tmp_path):
        a, _, docs = self._tree(tmp_path, parked=["x", "y"], live=["x"])
        result = p7.check(READY, a, docs_root=docs)
        assert "pending_mutation_spec_not_restored" in codes(result)
        detail = next(b["detail"] for b in result["blockers"]
                      if b["code"] == "pending_mutation_spec_not_restored")
        assert "y.json.pending" in detail and "x.json.pending" not in detail

    def test_no_pending_dir_is_silent(self, tmp_path):
        a, _, docs = self._tree(tmp_path)
        result = p7.check(REVIEWED, a, docs_root=docs)
        assert result["ready"] and not result["warnings"]

    def test_no_specs_dir_at_all_is_a_warning_not_a_verdict(self, tmp_path):
        """'I could not check' must not read as 'never moved back'."""
        docs = tmp_path / "docs"
        pend = docs / "03-analysis" / "demo.pending-mutation-specs"
        pend.mkdir(parents=True)
        (pend / "x.json.pending").write_text("{}", encoding="utf-8")
        a = docs / "03-analysis" / "demo.analysis.md"
        a.write_text(ANALYSIS, encoding="utf-8")
        result = p7.check(REVIEWED, a, docs_root=docs)
        assert "pending_mutation_spec_not_restored" not in codes(result)
        assert {w["code"] for w in result["warnings"]} == {"pending_specs_unverified"}

    def test_no_docs_root_skips_with_a_warning_never_derives_from_the_analysis_path(self, tmp_path):
        a, _, _ = self._tree(tmp_path, parked=["x"], live=[])
        result = p7.check(REVIEWED, a)
        assert "pending_mutation_spec_not_restored" not in codes(result)
        assert {w["code"] for w in result["warnings"]} == {"pending_specs_unverified",
                                                          "analysis_versions_unverified"}

    def test_an_explicit_analysis_elsewhere_does_not_move_the_root(self, tmp_path):
        """`--analysis /tmp/x.analysis.md` used to derive the repo root as `/`."""
        a, _, docs = self._tree(tmp_path, parked=["x"], live=[])
        elsewhere = tmp_path / "elsewhere" / "x.analysis.md"
        elsewhere.parent.mkdir()
        elsewhere.write_text(ANALYSIS, encoding="utf-8")
        assert "pending_mutation_spec_not_restored" in codes(p7.check(READY, elsewhere, docs_root=docs))

    def test_a_sibling_projects_specs_are_not_adopted(self, tmp_path):
        """Monorepo: HemaSuite/docs beside hematology-paper-writer/tests/mutation-specs.
        The docs root's own parent has no spec dir; the sibling's must not count."""
        docs = tmp_path / "HemaSuite" / "docs"
        pend = docs / "03-analysis" / "demo.pending-mutation-specs"
        pend.mkdir(parents=True)
        (pend / "x.json.pending").write_text("{}", encoding="utf-8")
        sib = tmp_path / "HemaSuite" / "hematology-paper-writer" / "tests" / "mutation-specs"
        sib.mkdir(parents=True)
        (sib / "x.json").write_text("{}", encoding="utf-8")
        a = docs / "03-analysis" / "demo.analysis.md"
        a.write_text(ANALYSIS, encoding="utf-8")
        # The default walk is bounded (two levels below the docs root's parent), so
        # from HemaSuite/ it DOES find the sub-project's dir: the default is
        # layout-bounded, not project-aware, and the monorepo case passes its own
        # dir explicitly. Pin both halves: the default adopts the sibling (documented
        # residual), the explicit form does not.
        by_default = p7.check(READY, a, docs_root=docs)
        assert "pending_mutation_spec_not_restored" not in codes(by_default)
        explicit = p7.check(READY, a, spec_dirs=[tmp_path / "HemaSuite" / "tests" / "mutation-specs"],
                            docs_root=docs)
        assert "pending_mutation_spec_not_restored" in codes(explicit)

    def test_the_selecting_name_gates_even_when_the_records_feature_field_drifted(self, tmp_path):
        a, _, docs = self._tree(tmp_path, parked=["x"], live=[])
        drifted = dict(READY, feature="something-else")
        assert "pending_mutation_spec_not_restored" in codes(
            p7.check(drifted, a, docs_root=docs, feature="demo"))

    def test_explicit_specs_dir_is_honoured(self, tmp_path):
        a, specs, docs = self._tree(tmp_path, parked=["x"], live=[])
        elsewhere = tmp_path / "other"
        elsewhere.mkdir()
        (elsewhere / "x.json").write_text("{}", encoding="utf-8")
        assert p7.check(READY, a, [elsewhere], docs_root=docs)["ready"]
        assert not p7.check(READY, a, [specs], docs_root=docs)["ready"]

    def test_cli_anchors_on_the_state_file_and_reports_the_blocker(self, tmp_path):
        a, specs, docs = self._tree(tmp_path, parked=["x"], live=[])
        state = docs / ".bkit-memory.json"
        state.write_text(json.dumps({"orchestrator_state": {"demo": READY}}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(state), "--feature", "demo",
                            "--analysis", str(a), "--mutation-specs-dir", str(specs)],
                           capture_output=True, text=True, cwd=str(tmp_path / "proj"))
        assert r.returncode == 0
        assert "PHASE7: BLOCKED" in r.stdout
        assert "pending_mutation_spec_not_restored" in r.stdout

    def test_calibrated_against_doc_block_exec_which_closed_with_two_provenance_copies(self):
        """The live tree: both parked specs have live twins, so the gate must pass.
        Located by glob because Phase 7 archives `docs/03-analysis/<feature>*`."""
        repo = Path(__file__).resolve().parents[2]
        dirs = [d for d in (repo / "docs").glob("**/doc-block-exec.pending-mutation-specs")
                if d.is_dir()]
        assert dirs, "doc-block-exec's parked specs are gone from docs/ entirely"
        specs = [repo / "h-mad" / "tests" / "mutation-specs"]
        for d in dirs:
            restored, unrestored = p7.split_parked(d, specs)
            assert len(restored) == 2 and unrestored == [], (d, unrestored)


class TestVersionedAnalysis:
    """Telemetry derives `iterate_cycles` as `max(N) - 1` over
    `<feature>.analysis.v<N>.md` and reads no counter. inline-protocols.md has said
    since 2026-07-23 that 6a writes v1 and each 6b cycle writes the next v<N>, and
    nothing checked it. grok-codex-fallback (1 iterate cycle) and multi-host-runtime
    (2) closed with only the unversioned `analysis.md` -- the verifier's report was
    saved as `gap.v1.md`, a name no counter reads, and each 6b cycle was narrated
    inside the one unversioned file -- so telemetry recorded `iterate_cycles=0` for
    both. The gate now refuses to close on an unversioned-only analysis.
    """

    def _tree(self, tmp_path, versions=(1,)):
        docs = tmp_path / "docs"
        (docs / "03-analysis").mkdir(parents=True)
        a = docs / "03-analysis" / "demo.analysis.md"
        a.write_text(ANALYSIS, encoding="utf-8")
        for n in versions:
            (docs / "03-analysis" / f"demo.analysis.v{n}.md").write_text(ANALYSIS, encoding="utf-8")
        return a, docs

    def test_an_unversioned_only_analysis_blocks(self, tmp_path):
        """The grok / multi-host-runtime shape: a passing rate, a `gap.v1.md`, no v<N>."""
        a, docs = self._tree(tmp_path, versions=())
        (docs / "03-analysis" / "demo.gap.v1.md").write_text(ANALYSIS, encoding="utf-8")
        result = p7.check(READY, a, docs_root=docs, feature="demo")
        assert "analysis_unversioned" in codes(result)
        detail = next(b["detail"] for b in result["blockers"] if b["code"] == "analysis_unversioned")
        assert "demo.analysis.v<N>.md" in detail
        assert "iterate_cycles" in detail

    def test_a_versioned_analysis_is_ready(self, tmp_path):
        """Positive control: the fixture can produce READY at all."""
        a, docs = self._tree(tmp_path, versions=(1,))
        result = p7.check(REVIEWED, a, docs_root=docs, feature="demo")
        assert result["ready"], result
        assert not result["warnings"]

    def test_an_archived_versioned_analysis_counts(self, tmp_path):
        """Searched where telemetry searches: live 03-analysis AND archive/*/<feature>/."""
        a, docs = self._tree(tmp_path, versions=())
        arch = docs / "archive" / "2026-09" / "demo"
        arch.mkdir(parents=True)
        (arch / "demo.analysis.v1.md").write_text(ANALYSIS, encoding="utf-8")
        assert "analysis_unversioned" not in codes(p7.check(READY, a, docs_root=docs, feature="demo"))

    def test_state_claiming_more_iterate_cycles_than_the_files_show_blocks(self, tmp_path):
        """v1 written, then 6b overwrote in place: existence passes, the count is lost.
        multi-host-runtime's state said iterate_cycles=2; two cycles need a v3."""
        a, docs = self._tree(tmp_path, versions=(1,))
        result = p7.check(dict(READY, iterate_cycles=2), a, docs_root=docs, feature="demo")
        assert "iterate_cycles_unrecorded" in codes(result)
        detail = next(b["detail"] for b in result["blockers"]
                      if b["code"] == "iterate_cycles_unrecorded")
        assert "iterate_cycles=2" in detail and "derive 0" in detail

    def test_matching_state_and_files_are_ready(self, tmp_path):
        a, docs = self._tree(tmp_path, versions=(1, 2, 3))
        assert p7.check(dict(READY, iterate_cycles=2), a, docs_root=docs, feature="demo")["ready"]

    def test_no_docs_root_is_a_warning_not_a_pass_or_a_verdict(self, tmp_path):
        a, _ = self._tree(tmp_path, versions=())
        result = p7.check(READY, a)
        assert "analysis_unversioned" not in codes(result)
        assert "analysis_versions_unverified" in {w["code"] for w in result["warnings"]}

    def test_cli_blocks_an_unversioned_only_analysis(self, tmp_path):
        a, docs = self._tree(tmp_path, versions=())
        state = docs / ".bkit-memory.json"
        state.write_text(json.dumps({"orchestrator_state": {"demo": READY}}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(state), "--feature", "demo"],
                           capture_output=True, text=True, cwd=str(tmp_path))
        assert "PHASE7: BLOCKED" in r.stdout, r.stdout
        assert "analysis_unversioned" in r.stdout


class TestReviewIndependence:
    """FR-7 warnings describe recorded reviews without changing the verdict."""

    @pytest.fixture
    def hostile_module(self, hermetic_env):
        env = {key: value for key, value in hermetic_env().items()
               if not key.startswith("HMAD_STUB_")}
        env["HMAD_STUB_HOSTILE"] = "all"
        result = subprocess.run(
            ["bash", str(Path(__file__).parent / "stubs" / "orca"),
             "worktree", "set", "--comment", "module fixture"],
            capture_output=True, text=True, env=env, timeout=10, check=True,
        )
        module = json.loads(result.stdout)["result"]["worktree"]["comment"]
        assert "\n" in module and "[a](b)" in module and "⟦/h-mad⟧" in module
        return module

    @pytest.fixture
    def analysis_tree(self, tmp_path):
        docs = tmp_path / "docs"
        analysis = docs / "03-analysis" / "demo.analysis.v1.md"
        analysis.parent.mkdir(parents=True)
        analysis.write_text(ANALYSIS, encoding="utf-8")
        specs = tmp_path / "tests" / "mutation-specs"
        specs.mkdir(parents=True)
        return analysis, docs, specs

    def _entry(self, module, **overrides):
        return {"leg": "5e-review", "module": module, "reviewer": "agy",
                "implementer": "codex", "independent": True, **overrides}

    def _check(self, record, analysis_tree):
        analysis, docs, specs = analysis_tree
        return p7.check(record, analysis, spec_dirs=[specs],
                        docs_root=docs, feature="demo")

    def test_non_independent_entry_warns(self, analysis_tree, hostile_module):
        entries = [
            self._entry(hostile_module, reviewer="codex", independent=False),
            self._entry(hostile_module + " second", leg="6a-prime",
                        implementer="agy", independent=False),
        ]
        result = self._check(dict(READY, review_independence=entries), analysis_tree)
        warnings = [w for w in result["warnings"] if w["code"] == "review_non_independent"]
        assert len(warnings) == 2, "review_non_independent must warn once per non-independent entry"
        for entry in entries:
            assert any(all(entry[key] in w["detail"]
                           for key in ("leg", "module", "implementer"))
                       for w in warnings), "review_non_independent must name leg, hostile module and agent"
        assert {w["code"] for w in result["warnings"]} == {"review_non_independent"}
        assert result["ready"] is True and result["blockers"] == []

    @pytest.mark.parametrize("case", ["bad-leg", "lying-boolean", "field-not-a-list"])
    def test_malformed_entry_warns(self, case, analysis_tree, hostile_module):
        if case == "bad-leg":
            value = [self._entry(hostile_module, leg="bad-leg"),
                     self._entry(hostile_module, leg="bad-leg")]
        elif case == "lying-boolean":
            value = [self._entry(hostile_module, reviewer="codex", independent=True),
                     self._entry(hostile_module, independent=False)]
        else:
            value = hostile_module
        record = dict(READY, archreview="SKIPPED_OPERATOR_OVERRIDE", review_independence=value)
        result = self._check(record, analysis_tree)
        malformed = [w for w in result["warnings"]
                     if w["code"] == "review_independence_malformed"]
        expected = 1 if case == "field-not-a-list" else 2
        assert len(malformed) == expected, (
            f"review_independence_malformed must warn {expected} times for {case}"
        )
        assert "review_non_independent" not in {w["code"] for w in result["warnings"]}, (
            "malformed entries must never be interpreted as well-formed non-independent reviews"
        )
        assert result["ready"] is True and result["blockers"] == []

    @pytest.mark.parametrize("routing", [
        pytest.param({}, id="codex-field-absent"),
        pytest.param({"implementer": "codex"}, id="codex"),
        pytest.param({"implementer": "agy"}, id="agy"),
        pytest.param({"implementer_switch": {"to": "grok"}}, id="grok"),
        pytest.param({"implementer_switch": {"to": "claude"}}, id="claude"),
    ])
    def test_unrecorded_fires_for_each_implementer(self, routing, analysis_tree, hostile_module):
        record = dict(READY, review_independence=[self._entry(hostile_module)], **routing)
        result = self._check(record, analysis_tree)
        warnings = [w for w in result["warnings"]
                    if w["code"] == "review_independence_unrecorded"]
        assert len(warnings) == 1, (
            f"review_independence_unrecorded must fire independently of routing {routing!r}"
        )
        assert result["ready"] is True and result["blockers"] == []

    @pytest.mark.parametrize("archreview", ["READY_TO_MERGE", "WITH_FIXES", "NO"])
    def test_unrecorded_fires_for_each_archreview_value(self, archreview, analysis_tree, hostile_module):
        record = dict(READY, archreview=archreview,
                      review_independence=[self._entry(hostile_module)])
        result = self._check(record, analysis_tree)
        warnings = [w for w in result["warnings"]
                    if w["code"] == "review_independence_unrecorded"]
        assert len(warnings) == 1, (
            f"review_independence_unrecorded must fire for archreview={archreview}"
        )

    @pytest.mark.parametrize("case", [
        "has-6a-prime-entry", "archreview-absent",
        "SKIPPED_NO_PANE", "SKIPPED_OPERATOR_OVERRIDE",
    ])
    def test_unrecorded_is_quiet(self, case, analysis_tree, hostile_module):
        record = dict(READY, review_independence=[self._entry(hostile_module)])
        if case == "has-6a-prime-entry":
            record["review_independence"].append(self._entry(hostile_module, leg="6a-prime"))
        elif case == "archreview-absent":
            record.pop("archreview")
        else:
            record["archreview"] = case
        result = self._check(record, analysis_tree)
        assert "review_independence_unrecorded" not in {w["code"] for w in result["warnings"]}, (
            f"review_independence_unrecorded must stay quiet for {case}"
        )
        assert not any(w["code"].startswith("review_") for w in result["warnings"]), (
            "well-formed independent entries must produce no review warnings when unrecorded is quiet"
        )

    def test_malformed_6a_prime_entry_is_not_recorded(self, analysis_tree, hostile_module):
        entry = self._entry(hostile_module, leg="6a-prime", reviewer="codex", independent=True)
        result = self._check(dict(READY, review_independence=[entry]), analysis_tree)
        warning_codes = [w["code"] for w in result["warnings"]]
        assert sorted(warning_codes) == sorted([
            "review_independence_malformed", "review_independence_unrecorded",
        ]), "a malformed 6a-prime must warn as malformed AND leave review independence unrecorded"
        assert result["ready"] is True and result["blockers"] == []

    def test_unrecorded_detail_names_entry_authors_not_routing(self, analysis_tree, hostile_module):
        record = dict(READY, implementer="agy", implementer_switch={"to": "agy"},
                      implementation_authors=[{"module": hostile_module, "agent": "agy"}],
                      review_independence=[self._entry(hostile_module)])
        result = self._check(record, analysis_tree)
        warnings = [w for w in result["warnings"]
                    if w["code"] == "review_independence_unrecorded"]
        assert len(warnings) == 1, "review_independence_unrecorded must expose entry authors"
        detail = warnings[0]["detail"]
        assert "codex" in detail and "agy" not in detail, (
            "unrecorded detail must name codex from 5e entries, never agy from routing or author logs"
        )
        record["review_independence"] = [self._entry(hostile_module, implementer=agent)
                                         for agent in ("grok", "codex", "grok")]
        result = self._check(record, analysis_tree)
        warnings = [w for w in result["warnings"]
                    if w["code"] == "review_independence_unrecorded"]
        assert len(warnings) == 1, "unrecorded author detail must also handle multiple entries"
        detail = warnings[0]["detail"]
        assert detail.count("codex") == 1 and detail.count("grok") == 1, (
            "unrecorded detail must name distinct entry authors only once"
        )
        assert detail.index("codex") < detail.index("grok"), "entry authors must be sorted"

    def test_unrecorded_detail_without_5e_entries_says_unrecorded(self, analysis_tree):
        record = dict(READY, implementer="agy", implementer_switch={"to": "grok"},
                      review_independence=[])
        result = self._check(record, analysis_tree)
        warnings = [w for w in result["warnings"]
                    if w["code"] == "review_independence_unrecorded"]
        assert len(warnings) == 1, "review_independence_unrecorded must warn when the entry list is empty"
        assert "authors=unrecorded" in warnings[0]["detail"], (
            "unrecorded detail without well-formed 5e entries must say authors=unrecorded"
        )

    def test_warnings_never_move_ready(self, analysis_tree, hostile_module):
        values = [
            [self._entry(hostile_module, reviewer="codex", independent=False)],
            [self._entry(hostile_module, leg="bad-leg")],
            hostile_module,
            [],
        ]
        for base in (dict(READY), dict(READY, last_completed_phase=5)):
            before = self._check(base, analysis_tree)
            assert before["ready"] is (base["last_completed_phase"] == 6)
            for value in values:
                after = self._check(dict(base, review_independence=value), analysis_tree)
                assert after["ready"] is before["ready"], "review warnings must never move ready"
                assert after["blockers"] == before["blockers"], "review warnings must never touch blockers"

    def test_warning_lines_print_through_main(self, analysis_tree, hostile_module, capsys):
        analysis, docs, specs = analysis_tree
        record = dict(READY, review_independence=[
            self._entry(hostile_module, reviewer="codex", independent=False),
            self._entry(hostile_module, leg="6a-prime", reviewer="codex", independent=True),
        ])
        state = docs / ".bkit-memory.json"
        state.write_text(json.dumps({"orchestrator_state": {"demo": record}}), encoding="utf-8")
        rc = p7.main([str(state), "--feature", "demo", "--analysis", str(analysis),
                      "--mutation-specs-dir", str(specs)])
        output = capsys.readouterr().out
        for code in ("review_non_independent", "review_independence_malformed",
                     "review_independence_unrecorded"):
            assert f"  WARNING {code}: " in output, f"main must print WARNING {code}: <detail>"
        result = self._check(record, analysis_tree)
        for warning in result["warnings"]:
            assert f"  WARNING {warning['code']}: {warning['detail']}" in output, (
                "main must preserve each warning detail, including hostile module input"
            )
        assert rc == 0 and "PHASE7: READY blockers=0" in output, (
            "main must keep the READY verdict and exit code when only review warnings are present"
        )
