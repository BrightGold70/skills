DESIGN-AUTHOR: DONE version=v1.1 path=docs/02-design/features/hmad-test-boundaries.design.md lines=899 sha256=2253319f0d97dd1f55374d6b338c1e4b046fd6721dd6a08edd26aac41b5c8a65
REPORT=docs/03-analysis/hmad-test-boundaries.design-author.v1.1.report.md

# Design-Author Report (`v1.1`): `hmad-test-boundaries`

## Summary of Revisions (`v1.0` -> `v1.1`)

Updated `docs/02-design/features/hmad-test-boundaries.design.md` from `v1.0` to `v1.1` to resolve all verified findings from Phase 4 Design Audit Cycle 1 (`docs/02-design/features/hmad-test-boundaries.design.audit.v1.p1.md` and `docs/02-design/features/hmad-test-boundaries.design.audit.v1.p2.md`):

1. **`v1.p1` Must-fix 1 & Must-fix 2 + `v1.p2` Should-fix 1 (`build` — Project root derivation `parents[3]`, two-branch `resolve_spec_path`, and propagation from `h_mad_audit_gate.py`):**
   - Added `infer_project_root(design_path: Path, root: Path | None = None) -> Path | None` in `h-mad/scripts/h_mad_test_boundaries_check.py` (`Section 2.3` item 2 and `## API / Interface Changes` Section 2):
     - Returns `Path(root).resolve()` when `root is not None`.
     - Returns `abs_design.parents[3]` when `len(abs_design.parts) >= 4` and `abs_design.parts[-4:-1] == ("docs", "02-design", "features")` (fixing the `parents[2]` off-by-one bug where `parents[2]` was `docs`).
     - Returns `abs_design.parents[3]` when `len(abs_design.parts) >= 4` and `abs_design.parts[-4:-2] == ("docs", "archive")` (or the ancestor immediately above `"docs"` when `("docs", "archive")` appear as adjacent segments in `abs_design.parts[:-1]`).
     - Returns `None` for design paths outside `docs/02-design/features/` and `docs/archive/` (such as bare synthetic fixtures in `tmp_path`).
   - Updated `resolve_spec_path(design_path: Path, spec_path: Path | None = None, root: Path | None = None) -> Path` (`Section 2.3` item 3 and `## API / Interface Changes` Section 2) to implement the strict two-branch rule from `spec.md` `FR-2.1` and `FR-4.2` Arm 3:
     - **Branch 1 (`abs_design` is under `docs/02-design/features/`):** Let `plan_cand = proj_root / "docs" / "01-plan" / "features" / f"{feature}.spec.md"`. Returns `plan_cand` if `plan_cand.exists()`, else `sib_cand` if `sib_cand.exists()`, else `plan_cand`.
     - **Branch 2 (`abs_design` is NOT under `docs/02-design/features/`):** Returns `sib_cand` **only** (never falling back to `plan_cand` or `cwd_cand`).
   - Updated `should_activate_design_check(design_path: Path, root: Path | None = None) -> bool` (`Section 2.3` item 5) so Arm 1 never defaults `effective_root` to the skill checkout root (`REPO_ROOT`) and instead inspects `abs_design.parts[-4:-1] == ("docs", "02-design", "features")`, adjacent `("docs", "archive")` segments in `abs_design.parts[:-1]`, or `root` when explicitly supplied.
   - Updated `_candidate_design_paths` and `_run_design_boundaries_checks` in `h-mad/scripts/h_mad_audit_gate.py` (`Section 3.2`) and the Direction 2 mutation anchor in `h-mad/tests/mutation-specs/test_boundaries_gate.json` (`Section 5.2`) so `h_mad_audit_gate.py` derives `proj_root = checker.infer_project_root(design_path)`, passes `proj_root` to `checker.should_activate_design_check(design_path, proj_root)`, and passes `["--root", str(proj_root)]` to `h_mad_test_boundaries_check.py`.
   - Added explicit test specifications in `Section 5.1` (`TestCliAndTableValidation` and `TestExemptionsAndAuditGateIntegration`) for (a) invoking `h_mad_test_boundaries_check.py` from a different `cwd` (`tmp_path`) on an absolute `/.../docs/02-design/features/demo.design.md` without `--root` and (b) running `h_mad_audit_gate.py` against a separate project tree under `tmp_path / "external_project" / "docs" / "02-design" / "features" / "demo.design.md"` with a missing `## Test Boundaries` section and no paired spec.
   - **Swept surfaces:** `## Executive Summary`, `## Architecture Overview`, `### Component Boundary Interactions`, `Component 2` (`2.2`, `2.3`), `Component 3` (`3.2`), `Component 5` (`5.1`, `5.2`), `## Components Changed / Added`, `## Implementation Order`, `## API / Interface Changes`, `## Test Strategy`, `## Invariant Compliance`.

2. **`v1.p1` Must-fix 3 (`build` — `AC-1.3` host-independent `<skill_dir>` instruction in `h-mad/agents/design-author.md`):**
   - Replaced the hardcoded `~/.claude/skills/h-mad` command in `Component 1` (`Section 1.3`) and `## Components Changed / Added` with:
     `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md`
     with the clarifying parenthetical `(where <skill_dir> is the active H-MAD skill directory for the current host, e.g. h-mad in this checkout, ~/.claude/skills/h-mad, ~/.agents/skills/h-mad, or ~/.gemini/config/skills/h-mad)`.
   - Updated `TestDesignAuthorAndSelfBootstrap` (`Section 5.1` #1) to assert that `h-mad/agents/design-author.md` contains the exact host-independent substring `python3 <skill_dir>/scripts/h_mad_test_boundaries_check.py docs/02-design/features/<feature>.design.md --spec docs/01-plan/features/<feature>.spec.md`.
   - **Swept surfaces:** `Component 1` (`1.3`), `Component 5` (`5.1` #1), `## Components Changed / Added`. (`grep -n "~/.claude/skills/h-mad/scripts/h_mad_test_boundaries_check.py"` returns 0 matches.)

3. **`v1.p1` Must-fix 4 (`build` — Unreadable candidate/spec handling in `should_activate_design_check`):**
   - Updated `should_activate_design_check` (`Section 2.3` item 5) so that in Arm 2 and Arm 3, if `design_path` or an existing `spec_candidate` (`spec_candidate.exists()`) is a directory or raises `(OSError, UnicodeDecodeError)` on `read_text(encoding="utf-8")`, `should_activate_design_check` returns `True` so `h_mad_audit_gate.py` invokes `h_mad_test_boundaries_check.py`, which emits `TEST-BOUNDARIES: UNREADABLE` (exit `2`) and fails the gate closed (`GATE: FAIL`) instead of crashing with an uncaught exception.
   - Added an explicit test case in `TestExemptionsAndAuditGateIntegration` (`Section 5.1` #4) exercising `h_mad_audit_gate.py` on an external `.design.md` (with no `## Test Boundaries` heading) paired with a sibling `.spec.md` containing invalid UTF-8 bytes (`b"\xff\xfe"`).
   - **Swept surfaces:** `Component 2` (`2.3` item 5), `Component 5` (`5.1` #4), `## Components Changed / Added`, `## Implementation Order`, `## Test Strategy`.

4. **`v1.p1` Should-fix 1 (`build` — Row 1 of `## Test Boundaries` in `hmad-test-boundaries.design.md`):**
   - Updated Row 1 (`AC-1.1, AC-1.2`) of `## Test Boundaries` in `docs/02-design/features/hmad-test-boundaries.design.md` to name the public contract surfaces `` `h-mad/references/inline-protocols.md` (Phase 4 — Design template) & `h-mad/scripts/h_mad_doc_shape_check.py::check_document` `` in column 1 and the independent specification & bkit superset contract in `docs/01-plan/features/hmad-test-boundaries.spec.md` (`FR-1.1`, `AC-1.1`, `AC-1.2`: `14` ordered `## ` headings in the Phase 4 template and the `7` required bkit design headings) `(verified by: h-mad/tests/test_h_mad_doc_templates.py, h-mad/tests/test_h_mad_doc_shape_check.py)` in column 3.

5. **`v1.p2` Nit 1 (`Overview` spec version reference):**
   - Updated `docs/01-plan/features/hmad-test-boundaries.spec.md` citation in `## Overview` (line 14) from `(`v1.3`)` to `(`v1.4`)`.

## Self-Check Verification Outputs

1. **`h_mad_version_history.py`:**
   - `VERSION-HISTORY: OK path=docs/02-design/features/hmad-test-boundaries.design.md version=v1.1 line=899 placement=append`
2. **`h_mad_precheck_doc.py`:**
   - Command: `python3 h-mad/scripts/h_mad_precheck_doc.py docs/02-design/features/hmad-test-boundaries.design.md --phase design --root /Users/kimhawk/orca/skills --allow h-mad/scripts/h_mad_test_boundaries_check.py --allow h-mad/tests/test_h_mad_test_boundaries_check.py --allow h-mad/tests/mutation-specs/test_boundaries_gate.json`
   - Output: `PRECHECK: PASS issues=0`
3. **`h_mad_doc_shape_check.py`:**
   - Command: `python3 h-mad/scripts/h_mad_doc_shape_check.py docs/02-design/features/hmad-test-boundaries.design.md`
   - Output: `DOC-SHAPE: PASS path=docs/02-design/features/hmad-test-boundaries.design.md type=design`
4. **`h_mad_ac_census.py`:**
   - Command: `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md docs/02-design/features/hmad-test-boundaries.design.md`
   - Output: `ACS: OK count=17 frs=6`
5. **`h_mad_assemble_audit.py`:**
   - Command: `python3 h-mad/scripts/h_mad_assemble_audit.py --feature hmad-test-boundaries --phase design --project-root /Users/kimhawk/orca/skills --cycle 2 --out /tmp/preflight_design_v1.1.prompt.md && rm -f /tmp/preflight_design_v1.1.prompt.md`
   - Output: `ASSEMBLE: PASS /tmp/preflight_design_v1.1.prompt.md 255950B (250.0 KB) sentinel=AUDIT-hmad-test-boundaries-design-v2 size_status=unverified`
