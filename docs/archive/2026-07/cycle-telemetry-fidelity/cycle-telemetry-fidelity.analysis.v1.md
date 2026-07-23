# Analysis: cycle-telemetry-fidelity

## Executive Summary

All 7 FRs and all 30 spec ACs are implemented and covered by passing tests, verified against
live repository data as well as fixtures; match rate 100%.

## Match Rate: 100%

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: audit cycles derived from artifacts | 5 | 5 | ✅ Complete | `h_mad_cycle_counts.py:69-86,124-129` |
| FR-2: Phase 6b emits per-cycle analysis | 4 | 4 | ✅ Complete | `references/inline-protocols.md` §Phase 6 step 6, §Phase 6b step 3 |
| FR-3: iterate cycles derived | 4 | 4 | ✅ Complete | `h_mad_cycle_counts.py:89-102,132-135` |
| FR-4: record writes derived counts | 4 | 4 | ✅ Complete | `h_mad_telemetry.py` `cmd_record` |
| FR-5: summary backfills on read | 5 | 5 | ✅ Complete | `h_mad_telemetry.py` `cmd_summary` |
| FR-6: archived and live both found | 4 | 4 | ✅ Complete | `h_mad_cycle_counts.py:18-34` |
| FR-7: matching anchored, templates excluded | 4 | 4 | ✅ Complete | `h_mad_cycle_counts.py:46,57` |

### Per-AC evidence

**FR-1** — AC-1.1 `test_two_contiguous_plan_audits_derive_cycle_two`; AC-1.2
`test_missing_phase_is_zero_and_latest_audit_is_highest`; AC-1.3
`test_audit_artifacts_maps_versions_and_skips_gaps` (v1+v3 → 3); AC-1.4
`test_plan_and_impl_plan_audits_derive_expected_phase_dict`; AC-1.5
`test_public_derivations_delegate_to_artifact_discovery` (records calls, asserts exact phases) and
`test_derivation_helpers_contain_no_independent_glob_or_regex` (rejects `.glob(`, `rglob`,
`fnmatch`, `import glob`, `glob.glob`, `re.compile`).

**FR-2** — AC-2.1 `test_phase6_save_versions_analysis_and_refreshes_legacy_path`; AC-2.2
`test_phase6b_versions_next_unused_cycle_without_overwriting_and_refreshes_latest`; AC-2.3
`test_protocol_explains_latest_unversioned_path_and_phase7_parser_dependency`; AC-2.4
`test_protocol_names_cycle_count_consumer_and_iteration_formula`. All four slice the relevant
section between headings rather than searching the whole document.

**FR-3** — AC-3.1/3.3 `test_single_analysis_version_and_absence_both_have_zero_iterations`;
AC-3.2 `test_four_contiguous_analysis_versions_derive_three_iterations` plus the non-contiguous
case in `test_analysis_artifacts_and_iterate_cycles`; AC-3.4
`test_unversioned_analysis_is_not_an_artifact`.

**FR-4** — AC-4.1 `test_record_derives_counts_and_defaults_docs_root_to_docs_state_parent`;
AC-4.2 same test; AC-4.3 `test_record_error_paths_keep_codes_with_docs_root_flag` (parametrized
over missing/malformed/absent, asserting each distinct stderr reason **and** that the others are
absent); AC-4.4 `test_record_without_artifacts_records_zero_counts`.

**FR-5** — AC-5.1 `test_summary_displays_derived_counts_over_stored_zero_counts`; AC-5.2
`test_summary_falls_back_to_stored_counts_when_no_artifacts_exist` **and**
`test_summary_uses_empty_mapping_fallback_not_zero_derived_count`, the latter being the
discriminating case; AC-5.3/5.4
`test_summary_derivation_does_not_modify_input_bytes_and_warns_on_derived_plan`; AC-5.5
`test_summary_docs_root_flag_is_used_and_existing_flags_remain_accepted`.

**FR-6** — AC-6.1 `test_audit_cycles_discovers_all_phase_roots`; AC-6.2/6.3
`test_archive_audits_are_included_and_can_be_disabled` and
`test_archived_audits_from_multiple_months_are_both_discovered`; AC-6.4
`test_analysis_artifacts_and_iterate_cycles`.

**FR-7** — AC-7.1 `test_literal_feature_boundary_excludes_prefix_collisions`; AC-7.2
`test_templates_are_never_searched` (uses the real `audit-example.audit.v1.md` filename); AC-7.3
`test_malformed_versions_are_ignored_without_raising`; AC-7.4
`test_case_sensitive_feature_filter_survives_case_insensitive_glob`.

## Gaps

None. All 30 spec ACs are met.

### Observations (not gaps)

- **Same-version collision between a live root and the archive is unspecified.** If
  `docs/01-plan/features/f.plan.audit.v2.md` and `docs/archive/2026-07/f/f.plan.audit.v2.md` both
  existed, the archive would win by dict overwrite (archive roots are iterated last). No spec
  language covers it and no test exercises it. It cannot arise from the documented workflow —
  archiving moves files rather than copying them — so this is recorded as undefined rather than
  wrong.
- **Double scan in `cmd_summary`.** `audit_maps` calls `audit_artifacts` per phase and
  `audit_cycles` calls it again internally, so six directory scans occur where three would do.
  Correct, and within the NFR ("no perceptible delay"); noted rather than optimised.
- **Two defects found outside this feature's scope** and filed in `docs/skill-monitoring.md`
  rather than fixed here: J8 (`elapsed_min` ≈ 56 years in every telemetry row, pre-existing) and
  J9 (`test_alive_cmux_true` is environment-dependent).

## Test Results

```
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q
498 passed in 10.07s
```

Feature-owned tests in isolation: 51 passed (21 + 9 + 7 + 4 + 3 definitions, expanded by
parametrisation).

Baseline before the feature: 454 passed. Net +44 tests, zero regressions.

### Live verification (not fixtures)

Run under the **bare `python3`**, which lacks `jsonschema` — proving the F8 containment the NFR
requires rather than asserting it:

| Archived feature | Derived | Expected |
|---|---|---|
| `orca-git-native-checkpoints-and-merge-gate` | `{plan: 2, design: 2, impl_plan: 1}` | match |
| `worktree-parallel-multi-module-tdd` | `{plan: 3, design: 2, impl_plan: 2}` | match |
| `dispatch-resolve-verb` | `{plan: 2, design: 1, impl_plan: 1}` | match |

On the real `.h-mad/telemetry.jsonl`: rows that **store** `{'plan': 0, 'design': 0, 'impl_plan': 0}`
now **display** `2/2/1` and `2/1/1`, and the file's md5 is identical before and after `summary` —
the append-only log is not rewritten.

This feature also derives its own history correctly: `{plan: 1, design: 2, impl_plan: 2}`, which
matches the audit cycles actually consumed (plan clean on cycle 1; design v1 FAIL must=3 → v2
PASS; impl-plan v1 FAIL must=1 should=2 → v2 PASS).

## Verdict

Match rate: 100% (threshold: 90%). Tests: 498/498 passing. 6a-prime: `READY_TO_MERGE`.
→ Advance to Phase 7.

## Version History
- v1.0: Initial gap analysis. Match rate 100%, suite 498/0.
