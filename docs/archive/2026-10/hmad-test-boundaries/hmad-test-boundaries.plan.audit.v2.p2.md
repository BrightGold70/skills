## Summary
`docs/01-plan/features/hmad-test-boundaries.plan.md` (v1.2) is internally consistent, complies with all Axis B base and project invariants, and reconciles cleanly against `docs/01-plan/features/hmad-test-boundaries.spec.md` (v1.2) across all 6 functional requirements (`FR-1`..`FR-6`) and 17 acceptance criteria (`AC-1.1`..`AC-6.3`). All Cycle 1 findings and tree-derived measurements (`13 -> 14` Phase 4 template headings, `7 -> 8` `PRIOR_HMAD_HEADINGS["design"]` entries, `39` tracked design files across `10` active and `29` archived, and active AC counts `17`, `24`, `40`, `44`, `63`) were re-derived at `HEAD = 9f330f71d65b5e667bd42a92065e77b9bd030d82` and verified to match.
Evidence: 14 files opened, 6 greps run.

| Requirement | Classification | Notes |
|---|---|---|
| `FR-1` | `implemented-as-written` | Covers `## Test Boundaries` template addition (`13 -> 14` headings), `PRIOR_HMAD_HEADINGS["design"]` (`7 -> 8`), `h_mad_doc_shape_check.py` preservation (`7` headings), and `design-author.md` self-bootstrapping workflow (`AC-1.1`..`AC-1.3`). |
| `FR-2` | `implemented-as-written` | Covers `h_mad_test_boundaries_check.py` CLI flags, 4-token stdout contract (`PASS`/`EXEMPT`/`FAIL` exit `0`, `UNREADABLE` exit `2`), 10-code failure vocabulary including `missing_spec` vs `UNREADABLE` and zero-AC-token `invalid_columns`, placeholder blocklist, and tautological-oracle rules (`AC-2.1`..`AC-2.4`). |
| `FR-3` | `implemented-as-written` | Covers head-anchored spec AC extraction, `[:.,\s-]+` retired-AC filtering, multi-token cell extraction, `uncovered_ac`/`unknown_ac`, and `verified by:` proving-artifact rules (`AC-3.1`..`AC-3.2`). |
| `FR-4` | `implemented-as-written` | Covers `PRE_EXISTING_FEATURES` (`10` stems) and `archive` exemptions, repeatable `--gated`/positional `<report>` candidate selection, 3-arm activation, pre-stamp verdict evaluation, post-`GATE:`/`GATE-CLASS:`/`GATE-LEGS:` stdout ordering, and two-direction connection enforcement (`AC-4.1`..`AC-4.4`). |
| `FR-5` | `implemented-as-written` | Covers Phase 4 `{{ONLY:design}}` audit prompt criteria and `doc-auditor.md` rules with explicit non-exempt qualification for missing `## Test Boundaries` (`AC-5.1`). |
| `FR-6` | `implemented-as-written` | Covers 3 archived calibration pairs (`24`, `40`, `44` active ACs), 5 seeded broken fixture classes, and `test_boundaries_gate.json` mutation verification including both connection directions (`AC-6.1`..`AC-6.3`). |

## Must-fix
None

## Should-fix
None

## Nit
- In `h-mad/tests/mutation-specs/test_boundaries_gate.json`, remember during Phase 4/6 to include the required `"root": "../.."`, `"command"`, and `"target_command"` argv lists alongside `"mutations"` (as required by `h_mad_mutation_harness.py:_load_spec`), since `"test_file"` alone is not parsed by `_load_spec`.
