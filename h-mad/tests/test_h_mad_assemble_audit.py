"""The shipped assembler: SKILL.md steps 1, 1.5, 2-6.6 and the 7.2 preflight.

Assembly was prose an orchestrator executed by hand every cycle, and every defect
in this area came from that -- rubrics inlined twice into a mangled blockquote,
`{Design only - cross-doc:}` reaching the reviewer in 69 of 69 dispatched prompts,
a duplication grep hardcoding a project-authored heading. None raised an error.
These tests pin the mechanical replacement.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
SCRIPT = SKILL_DIR / "scripts" / "h_mad_assemble_audit.py"

sys.path.insert(0, str(SKILL_DIR / "scripts"))
from h_mad_assemble_audit import assemble, preflight  # noqa: E402

SPEC = "# Spec: demo\n\n## Functional Requirements\n- FR-1 do the thing (AC-1.1)\n"
PLAN = "# Plan: demo\n\nStrategy for FR-1.\n"
DESIGN = "# Design: demo\n\nHow FR-1 is built.\n"
IMPL = "# Impl-plan: demo\n\nTask 1.\n"
PROJECT_INV = "# Demo Project Axis B Invariants\n\n## Demo rule\n- Do the demo thing.\n"


def _project(tmp_path: Path, *, with_project_invariants: bool = True) -> Path:
    # Mirrors the real bkit PDCA layout: design docs live under docs/02-design/,
    # NOT beside spec/plan/impl-plan. The first version of this fixture put all
    # four in one directory, so it passed while the assembler could not locate a
    # single real design document.
    docs = tmp_path / "docs/01-plan/features"
    docs.mkdir(parents=True)
    design = tmp_path / "docs/02-design/features"
    design.mkdir(parents=True)
    (docs / "demo.spec.md").write_text(SPEC)
    (docs / "demo.plan.md").write_text(PLAN)
    (design / "demo.design.md").write_text(DESIGN)
    (docs / "demo.impl-plan.md").write_text(IMPL)
    if with_project_invariants:
        (tmp_path / ".h-mad").mkdir()
        (tmp_path / ".h-mad/invariants.md").write_text(PROJECT_INV)
    return tmp_path


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def _assemble(root: Path, phase: str):
    return assemble(
        feature="demo", phase=phase, project_root=root,
        docs_dir=root / "docs/01-plan/features",
        sentinel="AUDIT-demo-x-v1", report_file="/tmp/demo.report.md",
        template=SKILL_DIR / "audit-prompt.template.md",
    )


class TestAssembledPromptIsClean:
    def test_every_phase_assembles_with_no_residue(self, tmp_path):
        root = _project(tmp_path)
        for phase in ("plan", "design", "impl-plan"):
            text, problems = _assemble(root, phase)
            assert problems == [], f"{phase}: {problems}"
            assert "<INLINE_" not in text and "{{" not in text
            assert "<AUDIT_SENTINEL>" not in text and "<REPORT_FILE_PATH>" not in text

    def test_each_rubric_is_inlined_exactly_once(self, tmp_path):
        root = _project(tmp_path)
        text, _ = _assemble(root, "design")
        assert text.count("# H-MAD Base Invariants") == 1
        assert text.count("# Demo Project Axis B Invariants") == 1

    def test_orchestrator_note_never_reaches_the_reviewer(self, tmp_path):
        text, _ = _assemble(_project(tmp_path), "plan")
        assert "ORCHESTRATOR-NOTE" not in text
        assert "Audit Prompt Template" not in text
        assert text.lstrip().startswith("You are the agy audit reviewer")

    def test_phase_scoping_of_paired_documents(self, tmp_path):
        root = _project(tmp_path)
        plan, _ = _assemble(root, "plan")
        design, _ = _assemble(root, "design")
        impl, _ = _assemble(root, "impl-plan")
        # The plan audit gets the spec but no paired plan/design, and the label
        # is dropped with it -- a bare label reads as a *missing* document.
        assert "# Spec: demo" in plan and "Paired audited plan:" not in plan
        assert "# Plan: demo" in design and "# Spec: demo" in design
        # The impl-plan audit contracts against the design, not the spec.
        assert "# Design: demo" in impl
        assert "Axis C" not in impl and "# Spec: demo" not in impl

    def test_absent_project_invariants_are_legal(self, tmp_path):
        """The base layer still applies when a project ships no invariants file."""
        root = _project(tmp_path, with_project_invariants=False)
        text, problems = _assemble(root, "plan")
        assert problems == []
        assert "# H-MAD Base Invariants" in text


class TestPreflightCatchesWhatHandAssemblyMissed:
    def test_unfilled_slot_is_caught(self):
        assert any("unfilled_slot" in p
                   for p in preflight("x <INLINE_PAIRED_PLAN> y", {}))

    def test_unresolved_conditional_is_caught(self):
        assert any("unresolved_conditional" in p
                   for p in preflight("{{ONLY:design}} x", {}))

    def test_duplicated_rubric_is_caught(self):
        body = "# Some Project Heading\n- rule\n"
        problems = preflight(body + "\n" + body, {"project": body})
        assert any("appears 2x" in p for p in problems)

    def test_duplication_needle_follows_a_project_authored_heading(self):
        """The heading is written by the project, so it cannot be hardcoded:
        HemaSuite's reads '# HPW Project Axis B Invariants'. A fixed needle
        reports 0, which reads as 'the project layer was never inlined'."""
        body = "# HPW Project Axis B Invariants\n- rule\n"
        assert preflight("prompt\n" + body, {"project": body}) == []
        assert any("appears 0x" in p for p in preflight("prompt only", {"project": body}))


class TestSignalDiscipline:
    """Base invariant 'Audit-gate signal discipline': a verdict the orchestrator
    consumes goes to stdout and exits 0. A non-zero exit means an operational
    error, never 'the prompt was rejected' -- it registers as a tool failure and
    leaks into coexisting plugins' error handling."""

    def test_pass_emits_token_and_exits_zero(self, tmp_path):
        root = _project(tmp_path)
        out = tmp_path / "prompt.txt"
        r = _run("--feature", "demo", "--phase", "plan",
                 "--project-root", str(root), "--out", str(out))
        assert r.returncode == 0, r.stderr
        assert r.stdout.startswith("ASSEMBLE: PASS")
        assert out.is_file() and out.read_text().startswith("You are the agy audit reviewer")

    def test_halt_is_a_verdict_not_a_process_failure(self, tmp_path):
        """Uses a template carrying a slot the assembler has no input for, so the
        preflight rejects an otherwise fully assembled prompt."""
        root = _project(tmp_path)
        bad_template = tmp_path / "bad.template.md"
        bad_template.write_text(
            "You are the agy audit reviewer.\n\n"
            "Target: <INLINE_TARGET_DOC>\n"
            "Base: <INLINE_BASE_INVARIANTS>\n"
            "Project: <INLINE_PROJECT_INVARIANTS>\n"
            "Sentinel: <AUDIT_SENTINEL>\nReport: <REPORT_FILE_PATH>\n"
            "Stray: <INLINE_NEVER_FILLED>\n"
        )
        out = tmp_path / "prompt.txt"
        r = _run("--feature", "demo", "--phase", "plan", "--project-root", str(root),
                 "--out", str(out), "--template", str(bad_template))
        assert r.returncode == 0, "a rejected prompt is a verdict, not a crash"
        assert r.stdout.startswith("ASSEMBLE: HALT")
        assert "unfilled_slot" in r.stdout
        assert not out.exists(), "a halted prompt must not be written — it could be sent"

    def test_missing_input_is_an_operational_error(self, tmp_path):
        r = _run("--feature", "nope", "--phase", "plan", "--project-root", str(tmp_path))
        assert r.returncode == 1
        assert "cannot assemble" in r.stderr
        assert "ASSEMBLE:" not in r.stdout

    def test_unknown_phase_is_rejected(self, tmp_path):
        r = _run("--feature", "demo", "--phase", "bogus", "--project-root", str(tmp_path))
        assert r.returncode != 0
        assert "ASSEMBLE: PASS" not in r.stdout


def test_design_docs_are_read_from_the_design_directory(tmp_path):
    """Regression: assuming one docs dir for every type made every design and
    impl-plan audit unassemblable against a real project, while unit tests that
    colocated the fixtures passed."""
    root = _project(tmp_path)
    assert not (root / "docs/01-plan/features/demo.design.md").exists()

    design_text, problems = _assemble(root, "design")
    assert problems == []
    assert "# Design: demo" in design_text        # target doc, from docs/02-design
    assert "# Plan: demo" in design_text          # paired plan, from docs/01-plan

    impl_text, problems = _assemble(root, "impl-plan")
    assert problems == []
    assert "# Design: demo" in impl_text          # paired design, from docs/02-design


def test_size_warning_fires_before_the_cliff_not_only_past_it(tmp_path):
    """The warning must arrive while there is still room to act, not only after.

    Re-anchored 2026-07-23. The thresholds used to encode a "49 KB reviewer
    cliff" that never reproduced for the delivery mode this skill uses: `send`
    switches to file indirection above 8192 B, so every audit prompt is read from
    a file, and five file-indirection prompts spanning 52,997-61,493 B were all
    answered normally. The bands now straddle the largest CONFIRMED-answered size
    (61,493 B) rather than a predicted failure point."""
    root = _project(tmp_path)
    spec = root / "docs/01-plan/features/demo.spec.md"
    out = tmp_path / "prompt.txt"

    def size_of(filler_lines: int) -> tuple[str, int]:
        spec.write_text("# Spec: demo\n\n## Functional Requirements\n"
                        + "- FR-1 filler (AC-1.1)\n" * filler_lines)
        r = _run("--feature", "demo", "--phase", "plan",
                 "--project-root", str(root), "--out", str(out))
        assert r.returncode == 0, r.stderr
        return r.stdout, out.stat().st_size

    quiet, small = size_of(10)
    assert "~" not in quiet and "!" not in quiet, f"no warning expected at {small}B"

    # Filler counts are calibrated to land in the bands, NOT arbitrary. Adding
    # rules to invariants.base.md moves every prompt, because that file is inlined
    # verbatim into all of them -- recalibrate the fixture rather than widen the
    # band, because the band is the assertion.
    approaching, mid = size_of(2200)
    assert 60 * 1024 < mid <= 64 * 1024, f"fixture drifted: {mid}B"
    assert "approaching" in approaching

    past, big = size_of(2300)
    assert big > 64 * 1024, f"fixture drifted: {big}B"
    assert "exceeds the largest prompt confirmed answered" in past
    # The old wording predicted a failure ("past the measured 49 KB reviewer
    # cliff ... a silent empty reply is the expected failure") at sizes since
    # measured as fine. Assert it is gone, so it cannot creep back.
    assert "reviewer cliff" not in past
    assert "reviewer cliff" not in approaching


# --- J12: size must travel ON the verdict line, not beside it -----------------
#
# `SKILL.md` mandates asserting `ASSEMBLE: PASS` before dispatch. The size
# warning was a SEPARATE `!` line, so an orchestrator following the documented
# contract exactly never had to read it -- the same defect class the `PREFLIGHT:`
# token was created to fix, one signal over.
#
# The filed fix direction offered `ASSEMBLE: PASS_OVERSIZE`. Testing that
# proposal kills it: "ASSEMBLE: PASS_OVERSIZE" matches a `grep "ASSEMBLE: PASS"`
# and satisfies `startswith("ASSEMBLE: PASS")` -- which is how every current
# consumer, including this file's own tests, reads the token. It would have
# reproduced J12 rather than fixed it.
#
# The other option, `ASSEMBLE: HALT <phase>:oversize`, is now contradicted by
# evidence: J13 measured five file-indirection prompts spanning 53-61 KB all
# answered. Halting on a size that demonstrably works would be a regression.
#
# So: a REQUIRED machine-readable field on the PASS line itself. "Proceed" stays
# correct, and the field lands inside the line the mandated read already parses.


def test_assemble_pass_always_carries_a_size_status_field(tmp_path):
    root = _project(tmp_path)
    out = tmp_path / "prompt.txt"
    r = _run("--feature", "demo", "--phase", "plan",
             "--project-root", str(root), "--out", str(out))
    assert r.returncode == 0, r.stderr
    line = r.stdout.splitlines()[0]
    assert line.startswith("ASSEMBLE: PASS")
    assert "size_status=" in line, (
        "size must be on the verdict line; beside it is what J12 filed"
    )
    assert "size_status=verified" in line


def test_size_status_flips_to_unverified_past_the_confirmed_ceiling(tmp_path):
    root = _project(tmp_path)
    spec = root / "docs/01-plan/features/demo.spec.md"
    out = tmp_path / "prompt.txt"
    spec.write_text("# Spec: demo\n\n## Functional Requirements\n"
                    + "- FR-1 filler (AC-1.1)\n" * 2300)
    r = _run("--feature", "demo", "--phase", "plan",
             "--project-root", str(root), "--out", str(out))
    assert r.returncode == 0, r.stderr
    line = r.stdout.splitlines()[0]
    assert "size_status=unverified" in line
    # Still a PASS: the evidence says prompts this size answer.
    assert line.startswith("ASSEMBLE: PASS ")


def test_oversize_verdict_token_is_not_a_pass_substring_variant(tmp_path):
    # Regression guard for the rejected design. If someone later "folds size into
    # the verdict" by appending to the token, every PASS-grep consumer silently
    # keeps passing. Assert the token stays exactly PASS or HALT.
    root = _project(tmp_path)
    spec = root / "docs/01-plan/features/demo.spec.md"
    out = tmp_path / "prompt.txt"
    spec.write_text("# Spec: demo\n\n## Functional Requirements\n"
                    + "- FR-1 filler (AC-1.1)\n" * 2300)
    r = _run("--feature", "demo", "--phase", "plan",
             "--project-root", str(root), "--out", str(out))
    token = r.stdout.splitlines()[0].split()[1]
    assert token in ("PASS", "HALT"), f"verdict token drifted to {token!r}"
