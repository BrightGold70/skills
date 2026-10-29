DESIGN-AUTHOR: DONE version=v1.2 path=docs/02-design/features/hmad-test-boundaries.design.md lines=912 sha256=568b65bb1b715514f01736ccc4fd25b5a5ab344a1a7ffed52a837a727f766457
REPORT=docs/03-analysis/hmad-test-boundaries.design-author.v1.2.report.md

# Design-Author Report (`v1.2`): `hmad-test-boundaries`

## Summary of Revisions (`v1.1` -> `v1.2`)

Updated `docs/02-design/features/hmad-test-boundaries.design.md` from `v1.1` to `v1.2` to resolve all verified findings from Phase 4 Design Audit Cycle 2 (`docs/02-design/features/hmad-test-boundaries.design.audit.v2.p1.md`):

1. **`v2.p1` Must-fix 2 (`build` — `AC-4.2` existing directory-valued design candidates must route to `UNREADABLE` instead of being skipped by `is_file()`):**
   - In Component 2 (`Section 2.3` item 5, `should_activate_design_check`):
     - Replaced `If not Path(design_path).is_file(), returns False.` with:
       - `If not Path(design_path).exists(), returns False.`
       - `If Path(design_path).is_dir(), returns True (routing the directory candidate to check_design / CLI so it emits TEST-BOUNDARIES: UNREADABLE path=<design_path> err=IsADirectoryError and exits 2).`
   - In Component 3 (`Section 3.2`, `_candidate_design_paths` and `_run_design_boundaries_checks` in `h-mad/scripts/h_mad_audit_gate.py`):
     - Replaced `.is_file()` filtering with `.exists()` across both `_candidate_design_paths` (`co_located.exists()` and `canonical.exists()` for positional `<report>` arguments) and `_run_design_boundaries_checks` (`candidates = [p for p in _candidate_design_paths(audit_file, gated) if p.exists()]`).
   - In Component 5 (`Section 5.1` #4, `TestExemptionsAndAuditGateIntegration`):
     - Added the explicit regression test **Directory-valued design candidate fail-closed gate test (`AC-2.1`, `AC-4.2`)** where `h_mad_audit_gate.py` is invoked with a positional `<feature>.design.audit.v1.p1.md` report (and no `--gated`) whose co-located canonical `docs/02-design/features/<feature>.design.md` is a **directory** (`mkdir()`), asserting `should_activate_design_check` returns `True`, `h_mad_audit_gate.py` emits `GATE: FAIL` and `TEST-BOUNDARIES: UNREADABLE ... err=IsADirectoryError`, and does not pass silently.
   - **Swept surfaces:** `## Architecture Overview`, `Component 2` (`Section 2.3` item 5), `Component 3` (`Section 3.2`), `Component 5` (`Section 5.1` #4), `## Components Changed / Added`, `## Implementation Order`, `## Test Strategy`.

2. **`v2.p1` Must-fix 1 (`build` — `AC-2.1` default `--root` project-root inference vs `cwd` fallback):**
   - Updated the `docs/01-plan/features/hmad-test-boundaries.spec.md` version citation in `## Overview` (line 14) from `(`v1.4`)` to `(`v1.5`)`.
   - In Component 2 (`Section 2.1`, `Section 2.3` item 2 `infer_project_root`), `## API / Interface Changes` Section 1 (`--root <project_root>` table row), and Component 5 (`Section 5.1` #2 `TestCliAndTableValidation`):
     - Explicitly specified that when `--root` is omitted, `infer_project_root` infers `<design_path>`'s ancestor project root (`abs_design.parents[3]`) when `<design_path>` is under `docs/02-design/features/` or `docs/archive/`, and falls back to `Path.cwd().resolve()` when a caller needs a default root for a non-canonical path (matching `spec.md` `v1.5` `FR-2.1`), and included a test in `TestCliAndTableValidation` distinguishing canonical ancestor inference (without `--root` from another `cwd`) from an explicit `--root` override.
   - **Swept surfaces:** `## Overview`, `Component 2` (`Section 2.1`, `Section 2.3` item 2), `Component 5` (`Section 5.1` #2), `## API / Interface Changes` (`Section 1`).

## Self-Check Verification Outputs

1. **`h_mad_version_history.py`:**
   - `VERSION-HISTORY: OK path=docs/02-design/features/hmad-test-boundaries.design.md version=v1.2 line=912 placement=append`
2. **`h_mad_precheck_doc.py`:**
   - Command: `python3 h-mad/scripts/h_mad_precheck_doc.py docs/02-design/features/hmad-test-boundaries.design.md --phase design --root /Users/kimhawk/orca/skills --allow h-mad/scripts/h_mad_test_boundaries_check.py --allow h-mad/tests/test_h_mad_test_boundaries_check.py --allow h-mad/tests/mutation-specs/test_boundaries_gate.json`
   - Output: `PRECHECK: PASS issues=0`
3. **`h_mad_doc_shape_check.py`:**
   - Command: `python3 h-mad/scripts/h_mad_doc_shape_check.py docs/02-design/features/hmad-test-boundaries.design.md`
   - Output: `DOC-SHAPE: PASS path=docs/02-design/features/hmad-test-boundaries.design.md type=design`
4. **`h_mad_ac_census.py`:**
   - Command: `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md docs/01-plan/features/hmad-test-boundaries.plan.md docs/02-design/features/hmad-test-boundaries.design.md`
   - Output: `ACS: OK count=17 frs=6`
