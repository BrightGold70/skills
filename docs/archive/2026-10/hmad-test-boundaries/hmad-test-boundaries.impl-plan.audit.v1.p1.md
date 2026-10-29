AUDIT-hmad-test-boundaries-impl-plan-v1-BEGIN
## Summary

The plan has conflicting implementation contracts and gaps in test enforcement that should be resolved before implementation. Repository inspection and in-memory controls confirmed the findings below; OneContext history was unavailable.
Evidence: 203 files opened, 7 greps run.
🌱 graft saved ~309,164 tokens this turn, 6 calls.

## Must-fix

- Task 1 requires a placeholder assertion that contradicts the closed specification — the prescribed rules accept `none — explanation` and `none (explanation)` outside column 4, while the planned test requires `placeholder_cell`. An in-memory evaluation reproduced this difference. Reject bare `none` outside column 4, but preserve the spec's residual rule for explanatory phrases; another column-specific rule may still reject them.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``are accepted in `Mocked dependencies` (column 4) and rejected as `placeholder_cell` in the other 4 columns.``
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › ``Residual: Any non-empty cell whose normalized text is not in the closed exact-token set and does not start with `"tbd "`, `"todo "`, `"fixme "`, or `"placeholder "` passes the placeholder check (and is then evaluated by the column-specific rules in FR-2.5 and FR-3).``

- The archive-root formula does not return the promised project root — for `/project/docs/archive/2026-08/demo/demo.design.md`, `parents[3]` evaluates to `/project/docs`, not `/project`. Archive depth varies, so reconcile the inherited formula with the stated ancestor contract and add a direct archive-root assertion; the planned canonical-design test and calibration copies outside the archive do not expose this.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``Otherwise, for canonical paths under `<project_root>/docs/02-design/features/<feature>.design.md` or `<project_root>/docs/archive/...`, returns `abs_design.parents[3]` (the ancestor immediately above `docs/`)``

- Task 2 does not enforce the template's required table — its existing template test checks headings only. I applied the planned expected-heading update in memory and supplied a template containing only the new heading, without its table; the design assertion still passed. Add table/header/order assertions against the actual Phase 4 template and observe failure with the table removed while retaining the heading. Otherwise AC-1.1's table requirement lacks a discriminating check.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``Update `PRIOR_HMAD_HEADINGS["design"]` from `7` entries to `8` entries by inserting `"Test Boundaries"` immediately after `"Test Strategy"` and before `"Invariant Compliance"``
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › ``contains the `## Test Boundaries` heading (increasing the Phase 4 design template from 13 to 14 `## ` headings) and the 5-column Markdown table header``

- Task 3 omits the activated-success gate cases required by spec AC-4.3 — the listed integration tests exercise activated failures and inactive success; exemption tests invoke the checker directly. A gate that rejects every activated candidate would satisfy those observations. Add activated `PASS` and `EXEMPT` CLI cases asserting `GATE: PASS`, emitted checker tokens, and readable stamps, and demonstrate that rejecting these statuses makes them fail.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``add `6` methods to `TestExemptionsAndAuditGateIntegration```
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › ``every activated candidate design (evaluated via `h_mad_test_boundaries_check.should_activate_design_check` where arm 3 checks for `>= 1` **active** head-anchored `AC-X.Y[a-z]` item) passes (`TEST-BOUNDARIES: PASS`) or is exempt (`TEST-BOUNDARIES: EXEMPT`)``

- The published non-interference corpus is incorrect at its cited commit — `git ls-tree -r --name-only c8df5312bebfad93d95019db604686af3a5de068 -- h-mad/tests/mutation-specs`, filtered to the declared JSON glob, yields 178 tracked files, not 40; all 178 current JSON objects contain mutation specifications. Re-derive the evidence over the actual corpus and record its command; the claimed comprehensive sweep is not established by the published census.
  class: measurement
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › ``Verified against all `40` files in `h-mad/tests/mutation-specs/*.json` at commit `c8df5312bebfad93d95019db604686af3a5de068```

## Should-fix

- Candidate selection applies existence filtering too late — a nonexistent explicit `--gated missing.design.md` makes `_candidate_design_paths` return before positional fallback, then `_run_design_boundaries_checks` returns `(True, [])` even when the report's co-located design exists. I reproduced this with the supplied helper code. Filter existing explicit candidates before deciding whether to fall back, and test this combination. The later stamp read currently fails operationally, so this is not a demonstrated PASS bypass.
  class: build
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › `if path.name.endswith(".design.md"):`
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › ``If that list is empty, inspect all positional `<report>` arguments (`audit_file`)``

- Correct the verification pointers and AC labels — the AC-1.2 matrix names a nonexistent method; the actual method is `TestMirrorFidelity::test_required_sections_match_the_live_validator`. Task 1 also relabels tautology as AC-2.3 and fences as AC-2.4, whereas the spec assigns AC-2.3 to empty/placeholder cells and AC-2.4 to tautology. The behaviors have planned tests, but the published traceability points to the wrong evidence.
  class: measurement
  quote: docs/01-plan/features/hmad-test-boundaries.impl-plan.md › `h-mad/tests/test_h_mad_doc_shape_check.py::TestMirrorFidelity::test_required_sections_match_bkit`; ``**AC-2.3**: Rejects `tautological_oracle` when `Expected result source` ``; ``**AC-2.4**: Ignores `## Test Boundaries` headings and pipe tables inside CommonMark fenced code blocks``
  quote: docs/01-plan/features/hmad-test-boundaries.spec.md › ``**AC-2.3:** When any cell is empty or matches the closed placeholder blocklist``; ``**AC-2.4:** When `Expected result source` matches any entry or regex in the closed tautological-oracle set``

## Nit

None
AUDIT-hmad-test-boundaries-impl-plan-v1-END
