# Spec Author Report — `hmad-test-boundaries` (v1.3)

- **Target Document**: `docs/01-plan/features/hmad-test-boundaries.spec.md`
- **Version**: `v1.3`
- **Lines**: `262`
- **SHA-256**: `cc802e250fd6e0492c4303c7a7f84c7efa2c65ebdafd33076051426136926779`

## Changes Applied in v1.3 (Phase 3 Plan Audit Cycle 2 Resolution)

1. **`v2.p1` Must-fix 1 (`build` — Single authoritative implementation & parity test for 3-arm gate activation across isolated gate loading):**
   - Updated `FR-4.2`, `AC-4.2`, and `AC-4.3` to specify that `h-mad/scripts/h_mad_test_boundaries_check.py` is the single authoritative owner of fenced-code-block-aware `## Test Boundaries` heading detection, paired `.spec.md` path resolution (`<root>/docs/01-plan/features/<feature>.spec.md`, then `<design_dir>/<feature>.spec.md`), head-defined `AC-X.Y[a-z]` extraction (including retired-AC filtering under `FR-3.1`), and the 3-arm activation helper `should_activate_design_check(design_path: Path, root: Path | None = None) -> bool` (where arm 3 activates when the resolved paired `<feature>.spec.md` contains `>= 1` **active** head-anchored `AC-X.Y[a-z]` item under `FR-3.1`).
   - Specified that `h-mad/scripts/h_mad_audit_gate.py` loads `h_mad_test_boundaries_check.py` via standard-library `importlib.util.spec_from_file_location` from `Path(__file__).with_name("h_mad_test_boundaries_check.py")` inside a helper function (never a top-level sibling `import`) and calls `should_activate_design_check(design_path)` rather than duplicating the fenced-heading scanner, spec-path resolver, or head-AC regex.
   - Required a parity test in `h-mad/tests/test_h_mad_test_boundaries_check.py` across both surfaces (`h_mad_test_boundaries_check.should_activate_design_check` called directly vs `h_mad_audit_gate` loaded in isolation via `importlib.util.spec_from_file_location` with `h-mad/scripts` absent from `sys.path`) covering fenced `## Test Boundaries` headings (` ``` ` / `~~~`), active lettered ACs (`AC-X.Ya`) vs retired-only specs, and both spec resolution paths (`<root>/docs/01-plan/features/<feature>.spec.md` and co-located `<design_dir>/<feature>.spec.md`).

2. **`v2.p1` Should-fix 2 (`build` — `< 200ms` per-design performance check):**
   - Updated `FR-6.1`, `AC-6.1`, and `## Non-Functional Requirements` to require `h-mad/tests/test_h_mad_test_boundaries_check.py` to measure wall-clock execution time (`time.monotonic()`) on each of the 3 archived calibration pairs and assert each run completes in `< 200ms` (`< 0.200` seconds).

3. **`v2.p2` Nit 1 (`h_mad_mutation_harness.py:_load_spec` schema keys for `test_boundaries_gate.json`):**
   - Updated `FR-6.3` and `AC-6.3` to specify that `h-mad/tests/mutation-specs/test_boundaries_gate.json` includes the required top-level `"root": "../.."`, `"command"`, `"target_command"`, and `"mutations"` keys expected by `h_mad_mutation_harness.py:_load_spec` (pointing pytest at `h-mad/tests/test_h_mad_test_boundaries_check.py`).

## Self-Check Verification

- `python3 h-mad/scripts/h_mad_version_history.py docs/01-plan/features/hmad-test-boundaries.spec.md --version v1.3 ...` -> `VERSION-HISTORY: OK path=docs/01-plan/features/hmad-test-boundaries.spec.md version=v1.3 line=262 placement=append`
- `python3 h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.spec.md --phase spec --root /Users/kimhawk/orca/skills --allow h-mad/scripts/h_mad_test_boundaries_check.py --allow h-mad/tests/test_h_mad_test_boundaries_check.py --allow h-mad/tests/mutation-specs/test_boundaries_gate.json --allow docs/02-design/features/hmad-test-boundaries.design.md` -> `PRECHECK: PASS issues=0`
- `python3 h-mad/scripts/h_mad_doc_shape_check.py docs/01-plan/features/hmad-test-boundaries.spec.md` -> `DOC-SHAPE: SKIP path=docs/01-plan/features/hmad-test-boundaries.spec.md type=none`
- `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md` -> `ACS: OK count=17 frs=6`
