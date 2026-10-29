SPEC-AUTHOR: DONE version=v1.0 path=docs/01-plan/features/hmad-test-boundaries.spec.md lines=245 sha256=2701e19f154f6602a6ba7da272a6779bd5b2fe8643f5a3542f7a79dded35fdce
REPORT=/Users/kimhawk/orca/skills/docs/03-analysis/hmad-test-boundaries.spec-author.v1.0.report.md

# Spec Author Report — `hmad-test-boundaries` (v1.0)

## Summary

Authored initial specification `docs/01-plan/features/hmad-test-boundaries.spec.md` (`v1.0`, `245` lines, `sha256=2701e19f154f6602a6ba7da272a6779bd5b2fe8643f5a3542f7a79dded35fdce`) for the `hmad-test-boundaries` feature (`6` functional requirement groups `FR-1`..`FR-6`, `17` acceptance criteria `AC-1.1`..`AC-6.3`).

## Premises Verified Against the Tree (`HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82`)

1. **`h_mad_doc_shape_check.py` mirror fidelity:** `REQUIRED_SECTIONS["design"]` has `7` headings (`["Executive Summary", "Overview", "Architecture", "Detailed Design", "Implementation Order", "Test Plan", "Version History"]`), enforced by `TestMirrorFidelity::test_required_sections_match_the_live_validator` in `h-mad/tests/test_h_mad_doc_shape_check.py`. Specified that `REQUIRED_SECTIONS["design"]` remains untouched while `## Test Boundaries` is added to the Phase 4 template in `h-mad/references/inline-protocols.md` (`13 -> 14` headings) and `PRIOR_HMAD_HEADINGS["design"]` in `h-mad/tests/test_h_mad_doc_templates.py` (`7 -> 8` headings).
2. **Existing design corpus:** `git ls-files 'docs/**/*.design.md'` lists `39` files (`10` under `docs/02-design/features/` and `29` under `docs/archive/`), `0` of which contain `## Test Boundaries`. Enumerated the closed `PRE_EXISTING_FEATURES` frozenset (`10` feature stems) and the `"archive"` path-component check for `TEST-BOUNDARIES: EXEMPT`, with opt-in evaluation whenever `## Test Boundaries` is present or `--no-exempt` is passed.
3. **`h_mad_audit_gate.py` isolation & mutation anchors:** Verified that `h-mad/tests/tree_lock_plugin.py` loads `h_mad_audit_gate.py` via `importlib.util.spec_from_file_location` without adding `h-mad/scripts` to `sys.path` (requiring stdlib-only top-level imports), that `audit_suite_gate.json` and `audit_gate_stamp.json` anchor on `    stamped = ""\n    if args.gated and verdict == "PASS":`, and that `h_mad_audit_cycle.py` checks `len(findings) == must` against `GATE: <verdict> must=<M> should=<S>`. Specified `h_mad_audit_gate.py` integration to preserve all three invariants and backward compatibility with existing synthetic `.design.md` test fixtures.
4. **Active vs. retired spec ACs:** Verified that `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.spec.md` contains retired `AC-3.7` (`- AC-3.7: Retired in v1.10. ...`). Specified active AC extraction that excludes `~~AC-X.Y~~` and `AC-X.Y: Retired ...` lines while requiring 100% coverage of active ACs.
5. **Calibration targets:** Verified exact paths and active AC counts for the 3 archived calibration targets:
   - `docs/archive/2026-08/exec-path-hardening/exec-path-hardening.{design,spec}.md` (`6` active ACs)
   - `docs/archive/2026-09/audit-report-docs-copy/audit-report-docs-copy.{design,spec}.md` (`8` active ACs)
   - `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.{design,spec}.md` (`9` active ACs)

## Verification Tokens

- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_precheck_doc.py docs/01-plan/features/hmad-test-boundaries.spec.md --phase spec --root /Users/kimhawk/orca/skills`
  -> `PRECHECK: PASS issues=0` (advisory `PATH:` notes only for new files to be created in Phase 6: `h-mad/scripts/h_mad_test_boundaries_check.py`, `h-mad/tests/test_h_mad_test_boundaries_check.py`, `h-mad/tests/mutation-specs/test_boundaries_gate.json`)
- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_doc_shape_check.py docs/01-plan/features/hmad-test-boundaries.spec.md`
  -> `DOC-SHAPE: SKIP path=docs/01-plan/features/hmad-test-boundaries.spec.md type=none`
- `python3 /Users/kimhawk/.gemini/config/skills/h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/hmad-test-boundaries.spec.md`
  -> `ACS: OK count=17 frs=6`

## Other Documents

No other files were edited. Input documents `docs/01-plan/features/hmad-test-boundaries-brainstorm.md` and `docs/superpowers/specs/2026-10-27-hmad-test-boundaries-design.md` require no changes.
