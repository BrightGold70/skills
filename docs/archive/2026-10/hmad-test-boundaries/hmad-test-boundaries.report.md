# Report: hmad-test-boundaries

## Executive Summary
Completed `hmad-test-boundaries` end-to-end across Phases 1–7, adding a mandatory 5-column `## Test Boundaries` section to Phase 4 Design documents, a deterministic standalone checker (`h-mad/scripts/h_mad_test_boundaries_check.py`) wired into `h-mad/scripts/h_mad_audit_gate.py`, Phase 4 auditor prompt rules (`h-mad/audit-prompt.template.md` and `h-mad/agents/doc-auditor.md`), and a 35-test + 8-mutation calibration suite (`MUTATION: ALL_CAUGHT`) with 100% FR/AC match rate and `READY_TO_MERGE` architectural review.

## Summary
We introduced upstream test-boundary and expected-result-source verification at H-MAD Phase 4 (Design) without altering bkit's `REQUIRED_SECTIONS` in `h_mad_doc_shape_check.py`. `h_mad_test_boundaries_check.py` deterministically validates the 5-column `## Test Boundaries` table (`Public interface`, `Acceptance criteria`, `Expected result source`, `Mocked dependencies`, `Exclusions`), reconciles active head-anchored spec `AC-X.Y[a-z]` items, blocks placeholder cells and closed tautological oracles, validates `verified by: audit | live-run | operator | doc-review` proving artifacts, and exempts pre-existing and archived designs unless `--no-exempt` is passed. `h_mad_audit_gate.py` loads the checker via `importlib.util.spec_from_file_location`, enforces the 3-arm activation predicate (`should_activate_design_check`), and suppresses `.gated.json` stamps when any activated design fails.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 2 |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% (6/6 FRs, 17/17 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` (`tools=26`, `channel=report-file`) |
| Tests | 35/35 in `test_h_mad_test_boundaries_check.py`, 427/427 in Phase 6a targeted suites, 1159/1159 in `h_mad_doc_consumers.py --run` (`0` failing) |
| Phases with back-propagation | Phase 3 & Phase 4: spec `v1.1`–`v1.5` reconciled AC letter suffixes, head-anchored active AC extraction, ancestor project-root inference, and directory/non-UTF-8 `UNREADABLE` routing |

## What Went Well
- Keeping `h_mad_test_boundaries_check.py` as the single authoritative owner of fenced-heading detection, paired `.spec.md` resolution, head-anchored AC extraction, and `should_activate_design_check` (loaded by `h_mad_audit_gate.py` via `importlib.util.spec_from_file_location`) avoided code duplication while preserving `tree_lock_plugin.py`'s stdlib-only isolated import invariant.
- Calibrating against 3 real archived designs (`exec-path-hardening` with 24 ACs, `audit-report-docs-copy` with 40 ACs, `tdd-gate-fail-opens` with 44 ACs) plus 5 seeded broken fixtures caught subtle spec formatting cases early (lettered `AC-2.6a`, retired `AC-3.7`, parenthesized tags before commas, and mid-line prose mentions) and verified `< 200ms` execution per design.
- Running `h_mad_doc_consumers.py --run` in Phase 5f caught an unpinned template reference in `test_grok_audit_surface_path_scope.py` (`test_switch_off_prompt_is_byte_identical_to_the_pinned_assembler`) before Phase 5g commit.

## What To Improve Next Time
- When a test pins historical assembler output against a past commit (`PINNED`), ensure from the start that both the code under test and any template file that evolves across future features are read from `PINNED` when testing flag-off equivalence.
- When wiring a new phase-specific check into `h_mad_audit_gate.py`, explicitly check `audit_file.name` against non-target phase report patterns (`.plan.audit.` / `.impl-plan.audit.`) up front so cross-phase `--gated` test fixtures do not trigger another phase's check.

## Carry Items
- None.

## Version History
- v1.0: Initial report draft.
