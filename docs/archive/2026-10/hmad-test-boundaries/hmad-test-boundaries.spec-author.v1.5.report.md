# Spec Author Report — `hmad-test-boundaries` (`v1.5`)

- **Document:** `docs/01-plan/features/hmad-test-boundaries.spec.md`
- **Version:** `v1.5`
- **Lines:** `264`
- **SHA-256:** `9a542a6490574197850310261ac7fa1de2dabfc1f07d8fec75755528e492f121`
- **Inputs Read:**
  - `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.4`)
  - `docs/03-analysis/hmad-test-boundaries.spec-author.v1.4.report.md`

## 1. Summary of Revision (`v1.4` -> `v1.5`)

1. **`FR-2.1` & `AC-2.1` (`--root` ancestor project-root inference):**
   - Updated the `--root <project_root>` bullet in `FR-2.1` and the CLI flags clause in `AC-2.1` to specify that when `--root` is omitted, the effective project root is inferred as `<design_path>`'s ancestor project root (`abs_design.parents[3]`) when `<design_path>` resolves under `<project_root>/docs/02-design/features/<feature>.design.md` or `<project_root>/docs/archive/...`, and falls back to `Path.cwd().resolve()` otherwise, ensuring invocations from another working directory or an external skill installation directory without `--root` still resolve `<project_root>/docs/01-plan/features/<feature>.spec.md`.
2. **`FR-4.2` & `AC-4.2` (`Path(design_path).exists()` candidate selection, `<root>` inference, and `UNREADABLE` fail-closed activation):**
   - Updated `FR-4.2` and `AC-4.2` to specify `Path(design_path).exists()` (not `is_file()`) for candidate selection and `should_activate_design_check`, infer `<root>` from `abs_design.parents[3]` when `root` is `None` and `<design_path>` resolves under `<project_root>/docs/02-design/features/<feature>.design.md` or `<project_root>/docs/archive/...` (else `Path.cwd().resolve()`), and return `True` from `should_activate_design_check` when an existing candidate `<design_path>` (or its existing resolved `<spec_path>`) is a directory or cannot be decoded as UTF-8 so `h_mad_test_boundaries_check.py` emits `TEST-BOUNDARIES: UNREADABLE` (exit `2`) and `h_mad_audit_gate.py` returns `GATE: FAIL`.
3. **Version History (`## Version History`):**
   - Appended the `v1.5` entry to `## Version History`.

## 2. Self-Check Verification Outputs

1. **`h_mad_precheck_doc.py`:**
   ```text
   PRECHECK: PASS issues=0
   [H-MAD] precheck hmad-test-boundaries.spec.md PASS issues=0
   ```
2. **`h_mad_doc_shape_check.py`:**
   ```text
   DOC-SHAPE: SKIP path=docs/01-plan/features/hmad-test-boundaries.spec.md type=none
   ```
3. **`h_mad_ac_census.py`:**
   ```text
   ACS: OK count=17 frs=6
   ```

## 3. Notes for Other Documents

- None (`docs/02-design/features/hmad-test-boundaries.design.md` is reconciled in parallel for Phase 4 Design Audit Cycle 2).
