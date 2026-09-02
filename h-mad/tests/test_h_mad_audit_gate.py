import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
MODULE_PATH = SCRIPT_DIR / "h_mad_audit_gate.py"

sys.path.insert(0, str(SCRIPT_DIR))

import h_mad_audit_gate as audit_gate  # noqa: E402
import h_mad_cycle_counts as cycle_counts  # noqa: E402
from h_mad_audit_gate import classify, stamp_path  # noqa: E402
from h_mad_audit_cycle import _collected_path  # noqa: E402


def run_gate(audit_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), str(audit_file), *args],
        check=False,
        capture_output=True,
        text=True,
    )


HOSTILE_CLEAN_AUDIT = """# Audit body with hostile reviewer payload

## Must-fix
None

## Should-fix
None

## Notes
human-origin marker text: {{INLINE_MARKER}} [link](target) **bold**
second line with AUDITCYCLE: fake marker
"""


TRANSPORT_NAMES = [
    "audit_f_plan_cycle3_codex.report.md",
    "audit_hnag_c28_agy.report.md",
    "audit_hnag_implplan_c11.report.md",
    "audit_f_plan_cycle8_codex_draft.report.md",
    "audit_f_plan_cycle8_agy_p2.report.md",
]


def transport_re() -> re.Pattern[str]:
    pattern = getattr(audit_gate, "TRANSPORT_RE", None)
    assert pattern is not None, "TRANSPORT_RE must define the single transport grammar"
    return pattern


def is_transport(path: Path) -> bool:
    predicate = getattr(audit_gate, "is_transport_path", None)
    assert predicate is not None, "is_transport_path() must expose the transport-name predicate"
    return bool(predicate(path))


@pytest.mark.parametrize("name", TRANSPORT_NAMES)
def test_cli_transport_named_report_is_invalid_before_scoring(
    tmp_path: Path, name: str
) -> None:
    audit_file = tmp_path / name
    audit_file.write_text(HOSTILE_CLEAN_AUDIT, encoding="utf-8")

    result = run_gate(audit_file)
    lines = result.stdout.splitlines()

    assert result.returncode == 2, "transport report names must be refused before scoring"
    assert lines[0] == "GATE: INVALID must=0 should=0"
    assert (
        lines[1]
        == f"[H-MAD] {audit_file.name.split('.')[0]} gate INVALID "
        "(transport file — collect it into docs first: h_mad_collect_report.py)"
    )
    assert result.stderr == ""


def test_is_transport_path_uses_transport_filename_grammar(tmp_path: Path) -> None:
    assert is_transport(tmp_path / "audit_f_plan_cycle3_codex.report.md")
    assert not is_transport(tmp_path / "audit_f.plan.audit.v8.report.md")
    assert not is_transport(tmp_path / "f.report.md")


def test_cli_collected_audit_doc_with_transport_bytes_scores_normally(tmp_path: Path) -> None:
    audit_file = tmp_path / "docs" / "01-plan" / "features" / "f.plan.audit.v3.codex.md"
    audit_file.parent.mkdir(parents=True)
    audit_file.write_text(HOSTILE_CLEAN_AUDIT, encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert re.search(r"^GATE: (?:PASS|FAIL) must=\d+ should=\d+$", result.stdout, re.MULTILINE)
    assert "GATE: INVALID" not in result.stdout


@pytest.mark.parametrize(
    "relative",
    [
        "f.report.md",
        "gate-blindness-hardening.report.md",
        "audit-report-docs-copy.report.md",
        "audit_f.plan.audit.v8.report.md",
        "x.md",
    ],
)
def test_cli_non_transport_report_like_names_score_normally(
    tmp_path: Path, relative: str
) -> None:
    audit_file = tmp_path / relative
    audit_file.write_text(HOSTILE_CLEAN_AUDIT, encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert re.search(r"^GATE: (?:PASS|FAIL) must=\d+ should=\d+$", result.stdout, re.MULTILINE)
    assert "GATE: INVALID" not in result.stdout


def test_cli_report_phase_doc_scores_normally(tmp_path: Path) -> None:
    audit_file = tmp_path / "docs" / "04-report" / "features" / "x.report.md"
    audit_file.parent.mkdir(parents=True)
    audit_file.write_text(HOSTILE_CLEAN_AUDIT, encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert re.search(r"^GATE: (?:PASS|FAIL) must=\d+ should=\d+$", result.stdout, re.MULTILINE)


def test_transport_regex_corpus_is_disjoint_from_versioned_audit_docs() -> None:
    corpus = [
        *[(name, "transport") for name in TRANSPORT_NAMES],
        ("f.plan.audit.v3.md", "audit_doc"),
        ("f.plan.audit.v3.p1.md", "audit_doc"),
        ("f.plan.audit.v3.p2.md", "audit_doc"),
        ("f.plan.audit.v3.codex.md", "audit_doc"),
        ("f.plan.audit.v3.agy.md", "audit_doc"),
        ("f.plan.audit.v3.codex_draft.md", "audit_doc"),
        ("audit_f.plan.audit.v8.report.md", "audit_doc"),
        ("audit_f.plan.audit.v8.codex.md", "audit_doc"),
        ("f.report.md", "other"),
        ("gate-blindness-hardening.report.md", "other"),
        ("audit-report-docs-copy.report.md", "other"),
        ("x.md", "other"),
    ]

    for name, kind in corpus:
        matches_transport = bool(transport_re().match(name))
        matches_audit_doc = bool(cycle_counts._VERSION_RE.search(name))

        assert (
            (kind == "transport") == matches_transport
        ), f"TRANSPORT_RE must classify {name!r} as {kind}"
        if kind == "audit_doc":
            assert matches_audit_doc, f"_VERSION_RE must accept audit doc name {name!r}"
        if kind == "other":
            assert not matches_transport, f"other name {name!r} must not be transport"
        assert not (
            matches_transport and matches_audit_doc
        ), f"{name!r} must not match both transport and audit-doc grammars"


def test_live_docs_audit_artifacts_are_not_transport_paths() -> None:
    artifacts = sorted(REPO_ROOT.glob("docs/**/*.audit.v*.md"))

    assert len(artifacts) >= 100, "live/archive audit corpus must be non-vacuous"
    offenders = [path for path in artifacts if is_transport(path)]
    assert offenders == [], "versioned docs audit artifacts must not be transport paths"


def test_collected_path_names_match_audit_doc_grammar_not_transport(
    tmp_path: Path,
) -> None:
    examples = [
        (feature, surface, phase)
        for feature, surface in [
            ("audit_f", "report"),
            ("audit_x", "report_md"),
            ("audit_", "p"),
            ("f", "codex"),
            ("nlm-cli-version-pin", "agy"),
        ]
        for phase in ["plan", "design", "impl-plan"]
    ]

    for feature, surface, phase in examples:
        path = _collected_path(
            project_root=tmp_path,
            feature=feature,
            phase=phase,
            cycle=8,
            index=1,
            surface=surface,
        )

        assert cycle_counts._VERSION_RE.search(
            path.name
        ), f"_collected_path() must emit audit-doc names, got {path.name!r}"
        assert not transport_re().match(
            path.name
        ), f"_collected_path() name {path.name!r} must not match transport grammar"


def test_verify_stamp_transport_name_remains_unstamped(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit_f_plan_cycle3_codex.report.md"

    result = run_gate(audit_file, "--verify-stamp")

    assert result.returncode == 2
    assert "GATESTAMP: UNSTAMPED checked=0 changed=0" in result.stdout


def test_classify_bare_none_sections_pass() -> None:
    text = "## Must-fix\nNone\n## Should-fix\nNone\n"

    assert classify(text) == {
        "verdict": "PASS",
        "must_count": 0,
        "should_count": 0,
    }


def test_classify_stray_dash_none_is_not_blocking() -> None:
    text = "## Must-fix\n- None\n## Should-fix\nNone\n"

    result = classify(text)

    assert result["verdict"] == "PASS"
    assert result["must_count"] == 0
    assert result["should_count"] == 0


def test_classify_real_must_fix_bullet_fails() -> None:
    result = classify("## Must-fix\n- real issue - why\n")

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1
    assert result["should_count"] == 0


def test_classify_header_only_sections_do_not_count() -> None:
    text = "## Must-fix\n## Should-fix\n## Notes\n- not blocking\n"

    assert classify(text) == {
        "verdict": "PASS",
        "must_count": 0,
        "should_count": 0,
    }


def test_classify_acknowledged_items_are_excluded_from_counts() -> None:
    text = "\n".join(
        [
            "## Must-fix",
            "- base-layer item waived by operator",
            "- still broken",
            "## Should-fix",
            "- acknowledged should item",
            "- should still block",
            "## Acknowledged-not-fixed",
            "- base-layer item waived by operator",
            "- acknowledged should item",
            "",
        ]
    )

    result = classify(
        text,
        acknowledged={
            "base-layer item waived by operator",
            "acknowledged should item",
        },
    )

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1
    assert result["should_count"] == 1


def test_classify_section_with_every_bullet_acknowledged_is_clean() -> None:
    """A section whose bullets are ALL acknowledged is cleared, not off-template.

    The `bullets` list going empty has two causes that must not share an answer:
    the section never carried a bullet marker (prose/numbered finding written
    off-template — count 1, fail-safe), or it carried bullets and the operator
    acknowledged every one (count 0, the escape hatch working as documented).
    Conflating them made `## Acknowledged-not-fixed` unable to clear any section
    holding two or more findings — measured on `guideline-claim-like-visibility`,
    where it capped the escape at one bullet per section and left three gates
    permanently FAIL.
    """
    text = "\n".join(
        [
            "## Must-fix",
            "- alpha",
            "- beta",
            "## Should-fix",
            "- gamma",
            "## Acknowledged-not-fixed",
            "- alpha",
            "- beta",
            "- gamma",
            "",
        ]
    )

    result = classify(text, acknowledged={"alpha", "beta", "gamma"})

    assert result == {"verdict": "PASS", "must_count": 0, "should_count": 0}


def test_classify_off_template_prose_still_counts_when_not_acknowledged() -> None:
    """The fail-safe the fix narrows must keep firing for genuinely bulletless content."""
    text = "\n".join(
        [
            "## Must-fix",
            "The plan contradicts the design on AC-3.2.",
            "## Should-fix",
            "None",
            "",
        ]
    )

    assert classify(text, acknowledged={"alpha"})["must_count"] == 1


def test_cli_clean_file_prints_pass_marker_and_exits_zero(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text("## Must-fix\nNone\n## Should-fix\nNone\n", encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: PASS must=0 should=0" in result.stdout
    assert "[H-MAD]" in result.stdout
    assert "gate PASS" in result.stdout
    assert result.stderr == ""


def test_cli_dirty_file_prints_fail_marker_and_exits_zero(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text(
        "## Must-fix\n- fix this\n## Should-fix\n- also fix this\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: FAIL must=1 should=1" in result.stdout
    assert "[H-MAD]" in result.stdout
    assert "gate FAIL" in result.stdout
    assert result.stderr == ""


def test_cli_missing_file_prints_stderr_and_exits_two(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.md"

    result = run_gate(missing_file)

    assert result.returncode == 2
    assert result.stderr
    assert result.stdout == ""


def test_cli_must_only_bases_verdict_on_must_count(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text(
        "## Must-fix\nNone\n## Should-fix\n- should-only issue\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file, "--must-only")

    assert result.returncode == 0
    assert "GATE: PASS must=0 should=1" in result.stdout
    assert "gate PASS" in result.stdout


def test_cli_marker_feature_is_derived_from_filename(tmp_path: Path) -> None:
    # Project-agnostic: the [H-MAD] marker feature must come from the audit
    # filename, not a hardcoded constant.
    audit_file = tmp_path / "some-other-feature.plan.audit.v1.md"
    audit_file.write_text("## Must-fix\nNone\n## Should-fix\nNone\n", encoding="utf-8")

    result = run_gate(audit_file)

    assert "[H-MAD] some-other-feature gate PASS" in result.stdout
    assert "h-mad-audit-surfaces-reconcile" not in result.stdout


def test_classify_indented_gemini_tui_output_counts_findings() -> None:
    # F1: agy (Gemini) renders every line indented ~2 spaces. A real Must-fix
    # must still be counted, not silently scored PASS by a column-0 header match.
    text = "  ## Must-fix\n  - real issue - why\n  ## Should-fix\n  None\n"

    result = classify(text)

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1
    assert result["should_count"] == 0


def test_classify_unicode_and_asterisk_bullets_count() -> None:
    # F1: agy emits `•`, other tools `*`; both are blocking bullets.
    text = "## Must-fix\n• bullet issue\n* asterisk issue\n## Should-fix\nNone\n"

    result = classify(text)

    assert result["must_count"] == 2
    assert result["verdict"] == "FAIL"


def test_classify_indented_bare_none_still_passes() -> None:
    # F1: indentation must not turn a clean (None) audit into a false FAIL.
    text = "  ## Must-fix\n  None\n  ## Should-fix\n  None\n"

    assert classify(text) == {"verdict": "PASS", "must_count": 0, "should_count": 0}


def test_cli_indented_bullet_scored_end_to_end(tmp_path: Path) -> None:
    # F1 end-to-end: an indented `•` Must-fix must FAIL (exit 0), not false-PASS.
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text(
        "  ## Summary\n  x\n  ## Must-fix\n  • real problem — why\n  ## Should-fix\n  None\n  ## Nit\n  None\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: FAIL must=1 should=0" in result.stdout


def test_cli_header_less_input_is_invalid_exit_two(tmp_path: Path) -> None:
    # F2: an empty/garbled extract lacking the mandatory sections must NOT score
    # as a clean PASS. It is an operational error: GATE: INVALID, exit 2.
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text("", encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 2
    assert "GATE: INVALID" in result.stdout
    assert "PASS" not in result.stdout


def test_cli_garbage_without_sections_is_invalid(tmp_path: Path) -> None:
    # F2: non-empty but section-less content (a stray scrape) is still INVALID.
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text("some terminal noise\n> prompt\n", encoding="utf-8")

    result = run_gate(audit_file)

    assert result.returncode == 2
    assert "GATE: INVALID" in result.stdout


def test_emphasis_note_under_section_is_fail_safe_not_silent_pass() -> None:
    # Fail-safe (F14): a section that is neither the `None` sentinel nor a bullet
    # list is off-template. Rather than silently PASS, it counts as a finding so a
    # human reformats it (to `None` if truly clean). A false FAIL blocks a merge;
    # a false PASS ships a defect.
    text = "## Must-fix\n**Note:** all clear\n## Should-fix\nNone\n"

    result = classify(text)

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1


def test_prose_finding_without_bullet_fails(  ) -> None:
    # F14: a real finding written as prose (no bullet) must not score PASS.
    text = "## Must-fix\nThe plan omits error handling for the retry path.\n## Should-fix\nNone\n"

    result = classify(text)

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1


def test_numbered_and_blockquote_findings_fail() -> None:
    # F14: numbered-list and blockquote findings are counted, not missed.
    numbered = classify("## Must-fix\n1. real blocking issue\n## Should-fix\nNone\n")
    assert numbered["verdict"] == "FAIL" and numbered["must_count"] == 1

    quoted = classify("## Must-fix\n> real issue via blockquote\n## Should-fix\nNone\n")
    assert quoted["verdict"] == "FAIL" and quoted["must_count"] == 1


def test_wrapped_multiline_bullet_counts_once() -> None:
    # A long bullet wrapped across lines (agy does this) is ONE finding, and its
    # continuation line must not itself be counted as a prose finding.
    text = (
        "## Must-fix\n"
        "- FR-4 restatement — the spec requires the raw call\n"
        "and the design forbids it, which is narrower.\n"
        "## Should-fix\nNone\n"
    )

    result = classify(text)

    assert result["verdict"] == "FAIL"
    assert result["must_count"] == 1


def test_cli_prose_finding_fails_end_to_end(tmp_path: Path) -> None:
    audit_file = tmp_path / "feat.plan.audit.v1.md"
    audit_file.write_text(
        "## Summary\nx\n## Must-fix\nThe design drops AC-2.2 silently.\n## Should-fix\nNone\n## Nit\nNone\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file)

    assert result.returncode == 0  # a FAIL verdict still exits 0 (signal discipline)
    assert "GATE: FAIL must=1 should=0" in result.stdout


def test_production_module_uses_only_stdlib_imports() -> None:
    stdlib = getattr(sys, "stdlib_module_names", set())
    if not stdlib:
        pytest.skip("sys.stdlib_module_names is unavailable on this Python")

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.partition(".")[0])

    assert imported_roots <= stdlib


# --- D-2: the `None` sentinel must tolerate trailing punctuation ---------------
#
# agy writes `None.` — with a trailing period — and `p.lower() == "none"` misses
# it. The section then falls through to the fail-safe branch ("non-`None` content
# with no countable bullet -> count 1") and MANUFACTURES one phantom finding per
# section. Observed live on `grounding-evidence-coverage` impl-plan cycle 23 pass
# B: `Must-fix: None.` / `Should-fix: None.` scored `GATE: FAIL must=1 should=1`
# with nothing behind it. The fail-safe DIRECTION stays (a false FAIL beats a
# false PASS); only the sentinel comparison is normalised.


@pytest.mark.parametrize(
    "sentinel",
    ["None.", "None", "- None.", "* None.", "• None.", "None .", "  None.  ", "NONE."],
)
def test_classify_punctuated_none_sentinel_is_clean(sentinel: str) -> None:
    text = f"## Must-fix\n{sentinel}\n## Should-fix\n{sentinel}\n"

    assert classify(text) == {"verdict": "PASS", "must_count": 0, "should_count": 0}


def test_classify_none_prefixed_prose_is_still_a_finding() -> None:
    # The normalisation must strip punctuation, not match a prefix: a real finding
    # that merely STARTS with the word None must still count.
    text = "## Must-fix\nNone of the ACs pin the emitter — AC-3.2 is unbuildable.\n## Should-fix\nNone.\n"

    result = classify(text)

    assert result["must_count"] == 1
    assert result["should_count"] == 0
    assert result["verdict"] == "FAIL"


def test_classify_fail_safe_prose_finding_survives_the_fix() -> None:
    # The fail-safe branch itself must NOT be loosened: off-template prose with no
    # bullet still counts 1 rather than being silently missed (F14).
    text = "## Must-fix\nThe plan pins the wrong file.\n## Should-fix\nNone.\n"

    result = classify(text)

    assert result["must_count"] == 1
    assert result["should_count"] == 0


def test_cli_dot_none_report_passes_end_to_end(tmp_path: Path) -> None:
    # D-2 end-to-end, the live artifact: a report whose empty sections read
    # `None.` must score PASS, not a phantom `FAIL must=1 should=1`.
    audit_file = tmp_path / "feat.impl-plan.audit.v23.md"
    audit_file.write_text(
        "## Summary\nx\n\n## Must-fix\nNone.\n\n## Should-fix\nNone.\n\n## Nit\nNone.\n",
        encoding="utf-8",
    )

    result = run_gate(audit_file)

    assert result.returncode == 0
    assert "GATE: PASS must=0 should=0" in result.stdout


@pytest.mark.parametrize("sentinel", ["**None**", "_None_", "`None`", "- **None**"])
def test_classify_emphasised_none_sentinel_is_clean(sentinel: str) -> None:
    # Same defect class as `None.`: markdown emphasis around the sentinel must
    # not manufacture a finding either.
    text = f"## Must-fix\n{sentinel}\n## Should-fix\n{sentinel}\n"

    assert classify(text) == {"verdict": "PASS", "must_count": 0, "should_count": 0}


def test_classify_punctuated_none_bullet_beside_a_real_bullet_is_not_counted() -> None:
    # Pins the SECOND `_is_none_sentinel` call site (the bullet filter). When every
    # payload is a sentinel the function returns 0 before reaching that filter, so
    # only a MIXED section exercises it: a real finding plus a `- None.` bullet
    # must count 1, not 2.
    text = "## Must-fix\n- real issue — why\n- None.\n## Should-fix\nNone.\n"

    result = classify(text)

    assert result["must_count"] == 1
    assert result["should_count"] == 0


# --- the stamp: a PASS is about content, and content moves ------------------
#
# Measured: a design audited clean twice still produced 9 findings on the next
# cycle, and 4 of them came from the edits that fixed the PREVIOUS cycle. The
# gate reads the audit file, never the document the audit judged, so a PASS
# survives every later edit to the thing it passed. The stamp records what was
# gated; the readback answers "is that verdict still about this content?".

CLEAN_AUDIT = "## Must-fix\n\nNone\n\n## Should-fix\n\nNone\n"
DIRTY_AUDIT = "## Must-fix\n\n- a real finding\n\n## Should-fix\n\nNone\n"


def _stamped(tmp_path: Path, audit_text: str = CLEAN_AUDIT):
    audit = tmp_path / "feat.design.audit.v1.md"
    audit.write_text(audit_text, encoding="utf-8")
    design = tmp_path / "feat.design.md"
    design.write_text("the design as audited\n", encoding="utf-8")
    return audit, design


def _verify(audit: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), str(audit), "--verify-stamp"],
        check=False, capture_output=True, text=True,
    )


def _cross_directory_stamp_layout(tmp_path: Path):
    audit_dir = tmp_path / "docs" / "02-design" / "features"
    plan_dir = tmp_path / "docs" / "01-plan" / "features"
    audit_dir.mkdir(parents=True)
    plan_dir.mkdir(parents=True)

    audit = audit_dir / "feat.impl-plan.audit.v1.md"
    audit.write_text(CLEAN_AUDIT, encoding="utf-8")
    design = audit_dir / "feat.design.md"
    design.write_text("the design as audited\n", encoding="utf-8")
    plan = plan_dir / "feat.spec.md"
    plan.write_text("the plan as audited\n", encoding="utf-8")
    return audit, design, plan


def test_a_pass_records_what_it_gated(tmp_path: Path) -> None:
    audit, design = _stamped(tmp_path)

    proc = run_gate(audit, "--gated", str(design))

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "GATE: PASS" in proc.stdout, proc.stdout
    assert "gated=1" in proc.stdout, "the verdict line must say how much it gated"
    assert (tmp_path / "feat.design.audit.v1.md.gated.json").exists()


def test_the_verdict_line_is_unchanged_without_the_flag(tmp_path: Path) -> None:
    """Every existing caller reads this line; the stamp is opt-in, not a rewrite."""
    audit, _ = _stamped(tmp_path)

    proc = run_gate(audit)

    assert proc.stdout.splitlines()[0] == "GATE: PASS must=0 should=0", proc.stdout
    assert not (tmp_path / "feat.design.audit.v1.md.gated.json").exists()


def test_unchanged_content_verifies_as_current(tmp_path: Path) -> None:
    audit, design = _stamped(tmp_path)
    run_gate(audit, "--gated", str(design))

    proc = _verify(audit)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "GATESTAMP: CURRENT" in proc.stdout, proc.stdout


def test_content_edited_after_the_pass_is_stale_and_names_the_file(
    tmp_path: Path,
) -> None:
    """The whole point: the verdict is no longer about what is on disk."""
    audit, design = _stamped(tmp_path)
    run_gate(audit, "--gated", str(design))

    design.write_text("the design, edited to fix the last cycle\n", encoding="utf-8")
    proc = _verify(audit)

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "GATESTAMP: STALE" in proc.stdout, proc.stdout
    assert "feat.design.md" in proc.stdout, "a stale verdict must name what moved"


def test_a_deleted_gated_file_is_stale_not_current(tmp_path: Path) -> None:
    audit, design = _stamped(tmp_path)
    run_gate(audit, "--gated", str(design))
    design.unlink()

    proc = _verify(audit)

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "GATESTAMP: STALE" in proc.stdout, proc.stdout


def test_verifying_without_a_stamp_is_a_cannot_judge(tmp_path: Path) -> None:
    """Never CURRENT: nothing was recorded, so nothing was compared. A missing
    stamp reading as `current` is the same class of lie as `no report` reading
    as `no findings`, which is why `INVALID` exists two functions up."""
    audit, _ = _stamped(tmp_path)

    proc = _verify(audit)

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "GATESTAMP: UNSTAMPED" in proc.stdout, proc.stdout
    assert "CURRENT" not in proc.stdout


def test_a_failing_gate_records_nothing(tmp_path: Path) -> None:
    """A stamp means "this content was passed". Writing one on FAIL would let a
    later readback report CURRENT over a verdict that blocked."""
    audit, design = _stamped(tmp_path, DIRTY_AUDIT)

    proc = run_gate(audit, "--gated", str(design))

    assert "GATE: FAIL" in proc.stdout, proc.stdout
    assert not (tmp_path / "feat.design.audit.v1.md.gated.json").exists()


def test_several_gated_files_are_all_recorded(tmp_path: Path) -> None:
    """A cycle gates the design AND the impl-plan; stamping one is a half-guard."""
    audit, design = _stamped(tmp_path)
    plan = tmp_path / "feat.impl-plan.md"
    plan.write_text("tasks\n", encoding="utf-8")

    run_gate(audit, "--gated", str(design), "--gated", str(plan))
    plan.write_text("tasks, edited\n", encoding="utf-8")
    proc = _verify(audit)

    assert "GATESTAMP: STALE" in proc.stdout, proc.stdout
    assert "feat.impl-plan.md" in proc.stdout, proc.stdout


def test_cross_directory_gated_file_verifies_current_when_unchanged(
    tmp_path: Path,
) -> None:
    audit, _, plan = _cross_directory_stamp_layout(tmp_path)

    stamped = run_gate(audit, "--gated", str(plan))
    proc = _verify(audit)

    assert stamped.returncode == 0, stamped.stdout + stamped.stderr
    assert "GATESTAMP: CURRENT checked=1 changed=0" in proc.stdout, proc.stdout
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_cross_directory_gated_file_modified_after_stamp_is_stale_not_decoy_current(
    tmp_path: Path,
) -> None:
    audit, _, plan = _cross_directory_stamp_layout(tmp_path)
    (audit.parent / plan.name).write_text("the plan as audited\n", encoding="utf-8")

    stamped = run_gate(audit, "--gated", str(plan))
    plan.write_text("the plan after implementation edits\n", encoding="utf-8")
    proc = _verify(audit)

    assert stamped.returncode == 0, stamped.stdout + stamped.stderr
    assert "GATESTAMP: STALE checked=1 changed=1" in proc.stdout, proc.stdout
    assert "feat.spec.md" in proc.stdout, proc.stdout
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_mixed_cross_directory_stamp_keeps_same_directory_basename_compatible(
    tmp_path: Path,
) -> None:
    audit, design, plan = _cross_directory_stamp_layout(tmp_path)

    stamped = run_gate(audit, "--gated", str(design), "--gated", str(plan))
    stamp = json.loads(stamp_path(audit).read_text(encoding="utf-8"))
    proc = _verify(audit)

    assert stamped.returncode == 0, stamped.stdout + stamped.stderr
    assert "feat.design.md" in stamp["files"]
    assert "GATESTAMP: CURRENT checked=2 changed=0" in proc.stdout, proc.stdout
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_an_unreadable_gated_file_refuses_rather_than_stamping_a_hole(
    tmp_path: Path,
) -> None:
    """Stamping a file it could not read would record a verdict over content it
    never saw — and the readback would then compare that fiction to reality."""
    audit, _ = _stamped(tmp_path)

    proc = run_gate(audit, "--gated", str(tmp_path / "nope.md"))

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "GATE: UNSTAMPABLE" in proc.stdout, proc.stdout
    assert not (tmp_path / "feat.design.audit.v1.md.gated.json").exists()


def test_the_skill_documents_the_stamp() -> None:
    skill = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
    assert "--verify-stamp" in skill, "a readback nobody is told to run is never run"
    assert "GATESTAMP:" in skill, "the token is undocumented"
