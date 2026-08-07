# Gap Analysis: regression-provenance-ledger

**Match rate: 100%**

**Range:** `d3bab41` (5c baseline) → `499e33e` (5g + 6a-prime fixes)
**Suite:** 1254 passed, 0 failed, rc=0
**Architectural review:** `ASSESSMENT: READY_TO_MERGE` (cycle 2; cycle 1 returned `WITH_FIXES`)

## Method

Every acceptance criterion in the audited design's §"Test Plan" was mapped to the test that
executes it, by name. A criterion counts as covered only when a named test exercises it — not
when the production code appears to implement it. Where a mutation sweep showed a criterion's
test did not discriminate, the criterion was treated as **uncovered** until a discriminating
test existed; three such cases were found and closed during Phase 5 (see §"Coverage that was
claimed before it was real").

## AC coverage — 24 of 24

| AC | Requirement | Test |
|---|---|---|
| AC-1.1 | record missing a required field rejected at write | `test_register_rejects_a_record_missing_required_field` (6 params) + `test_register_generates_registered_timestamp_and_ignores_supplied_value` |
| AC-1.2 | `kind: "counter"` rejected — enum is wire-only | `test_register_rejects_counter_kind` |
| AC-1.3 | duplicate `id` written twice → one record, updated | `test_register_updates_a_duplicate_id_in_place` |
| AC-1.4 | malformed line raises, names the line number | `test_load_rejects_malformed_json_with_one_based_line_number` |
| AC-2.1 | 2 pins, 1 fails → correct counts; empty set spawns nothing | `test_run_pins_attributes_failed_pin_and_owning_feature`, `test_run_pins_empty_does_not_spawn_subprocess` |
| AC-2.2 | broken wire's owner named in output, not just counted | `test_run_pins_attributes_failed_pin_and_owning_feature` |
| AC-2.3 | renamed pin undeclared → `missing`, distinct from `broken` | `test_partition_separates_resolving_and_missing_active_records` |
| AC-2.4 | tombstoned record whose pin is gone is NOT `missing` | `test_partition_does_not_report_removed_pin_as_missing` |
| AC-2.5 | exit 0 on PASS/FAIL/UNTRACKED; 2 on unreadable | `test_main_missing_base_is_exit_2_and_verdicts_are_exit_0`, `test_main_collection_failure_is_cannot_judge_exit_2_not_fail` |
| AC-3.1 | registry absent → `PASS registered=0`, no git call | `test_absent_registry_is_pass_and_skips_trackedness` |
| AC-3.2 | registry gitignored → `UNTRACKED`, never `PASS` | `test_trackedness_reports_ignored_and_untracked_with_different_remedies` |
| AC-3.3 | remedy text differs ignored vs untracked | `test_trackedness_reports_ignored_and_untracked_with_different_remedies` |
| AC-3.4 | `registered=N` present on every verdict | `test_untracked_broken_registry_keeps_counts_and_detail_marker` |
| AC-4.1 | id at BASE, absent at HEAD, no tombstone → FAIL naming id + feature | `test_active_base_record_absent_at_head_is_an_undeclared_removal`, `test_compare_returns_the_base_record_for_an_undeclared_removal` |
| AC-4.2 | tombstone provenance fields required | `test_removed_tombstone_requires_removal_provenance`, `test_superseded_tombstone_requires_superseding_feature`, `test_any_tombstone_requires_removed_by_feature`, `test_renamed_tombstone_requires_successor_pin` |
| AC-4.3 | `renamed` successor must resolve **and** pass | `test_partition_resolves_present_rename_and_unverifies_absent_rename` |
| AC-4.4 | declaration findable from the removed id | `test_compare_returns_the_base_record_for_an_undeclared_removal` |
| AC-5.1 | undeclared cross-module call warns, naming task + crossing | `test_challenge_exempts_a_wiring_claim_with_a_cross_boundary_call`, `test_challenge_ignores_test_file_cross_boundary_calls`, `test_challenge_uses_base_path_for_a_renamed_file_ast_diff`, `test_ast_targets_are_structural_and_ignore_reindenting` |
| AC-5.2 | that warning leaves `WIREPIN`/`WIREREG` verdicts unchanged | `test_challenge_cli_is_verdict_neutral` |
| AC-5.3 | raised/acknowledged counts reported; no-diff ≠ `challenges=0` | `test_challenge_reports_no_production_diff_as_not_compared` |
| AC-5.4 | boundary config honoured, not hardcoded; absent ⇒ never fires | `test_challenge_without_boundaries_is_not_compared` |
| AC-6.1 | passing 5b wiring task registers, no operator action | `test_passing_wiring_task_is_registered` |
| AC-6.2 | read-back is runtime, not test-only | `test_register_runtime_readback_rejects_a_silent_write_drop` |
| AC-6.3 | `SKILL.md` states auto-registration + registry location | `test_skill_phase5b_documents_featured_wire_registration_and_executable_flags`, `test_skill_inventory_lists_wire_registry_helper` |

## Design-version rows and base invariants — all covered

| Requirement | Test |
|---|---|
| missing `--base` → exit 2 | `test_main_missing_base_is_exit_2_and_verdicts_are_exit_0` |
| invalid `--base` sha → exit 2, NOT an empty base set | `test_git_show_rejects_an_invalid_sha` |
| registry absent at a valid BASE → empty base set, no error | `test_load_base_treats_a_path_absent_at_a_valid_commit_as_empty` |
| `compare()` performs no git call | `test_compare_is_pure_and_does_not_call_git` |
| `partition()` performs no subprocess/git | `test_partition_is_pure_without_subprocess_or_git` |
| `challenge` without `--base` → exit 2 | `test_challenge_cli_requires_base` |
| reindent/line-wrap does NOT fire the challenge | `test_ast_targets_are_structural_and_ignore_reindenting` |
| **delete the `register()` call, callee intact ⇒ wire pin FAILS** | `test_passing_wiring_task_is_registered` + wire-scoped revert, run live |
| **registration fires unconditionally ⇒ fall-through test FAILS** | `test_new_behaviour_task_registers_nothing`, `test_register_wiring_tasks_ignores_real_wire_on_non_wiring_shape` |
| J18 live-registry protection | `test_wire_registry_guard_fires_on_a_deliberate_live_file_leak`, `test_wire_registry_guard_mutation_is_caught_by_harness` |
| five halt reasons, doc ≡ code | `test_skill_documents_exactly_all_registry_halt_reasons`, `test_fail_drivers_emit_named_halt_markers` |

## Mutation verification

Every guard was mutated to its permissive value via `h_mad_mutation_harness.py`. Final state, all
`refused=0` (so every anchor matched exactly once and every mutation actually landed):

| Scope | Result |
|---|---|
| Task 1 registry guards | `ALL_CAUGHT mutations=9 caught=9 survived=0 refused=0` |
| Task 1 J18 conftest guard | `ALL_CAUGHT mutations=1 caught=1 survived=0 refused=0` |
| Task 2 partition/run_pins | `ALL_CAUGHT mutations=5 caught=5 survived=0 refused=0` |
| Task 3 git_show/compare | `ALL_CAUGHT mutations=5 caught=5 survived=0 refused=0` |
| Task 4 CLI/trackedness | `ALL_CAUGHT mutations=7 caught=7 survived=0 refused=0` |
| Task 5 the wire, both directions | `ALL_CAUGHT mutations=6 caught=6 survived=0 refused=0` |
| Task 6 AST challenge | `ALL_CAUGHT mutations=5 caught=5 survived=0 refused=0` |
| Task 7 doc guards | `ALL_CAUGHT mutations=4 caught=4 survived=0 refused=0` |
| 6a-prime fixes | `ALL_CAUGHT mutations=3 caught=3 survived=0 refused=0` |

## Coverage that was claimed before it was real

Recorded because the gap it names is the reason this feature exists — a criterion with a
non-discriminating test is indistinguishable from a covered one until something mutates it.

- **Task 4** — 1 of 7 mutations survived: nothing pinned the active-only filter on undeclared
  removals. Closed with three discriminating tests.
- **Task 5** — 2 of 6 survived, including the unconditional direction the implementer's report had
  claimed verified. The FAIL-plan fixture used a wiring task with no pin, so the absent pin (not
  the FAIL verdict) was what blocked registration.
- **Task 6** — **5 of 6** survived. The ACs had tests; the tests did not discriminate, including
  AC-5.3c, whose entire point is that a run that looked and a run that could not look must not
  render identically.

## Defects found by running the tool, not by the suite

All would have shipped behind a green suite.

1. `collect()` ignored pytest's return code. Under the bare `python3` h-mad scripts are documented
   to run under (no pytest), collection returned an empty set and every pin reported `missing`.
2. Node ids came out rootdir-relative while registered pins are repo-relative, matched by string
   equality — so no wire could ever match, in the only configuration this repo can collect in.
3. `_register_wiring_tasks` required an ASCII `->` while the impl-plan template writes U+2192 `→`,
   so registration silently skipped **every** real wiring task while printing `WIREPIN: PASS`.
   It survived 96 tests, 6/6 mutations and the wire-scoped revert because every fixture used tidy
   ASCII.
4. (6a-prime) A pin whose test ERRORed, was SKIPPED or XFAILed fell into neither bucket, so
   `broken=0` and the verdict was `PASS`. Reproduced live: `WIREREG: PASS registered=1 verified=0
   broken=0`, exit 0, for a definitively broken wire.

## Live end-to-end verification

```
gate on the real impl-plan   → WIREPIN: PASS … registration: registered=1 skipped=0
verify                       → registered=1 verified=1 broken=0
delete the connection        → BROKEN regression-provenance-ledger: <pin>
                               [H-MAD] step5f:wire_regression:Task 5   broken=1
pin errors in setup          → BROKEN … (ERROR) + marker, FAIL   [was PASS before the 6a-prime fix]
no pytest available          → exit 2 naming "No module named pytest", never a FAIL
no boundary map              → WIRECHALLENGE: NOT_COMPARED reason=no_boundaries, rc 0
```

A regression that the callee's own 54 tests report as green is caught by the ledger. That is the
feature's premise, demonstrated rather than asserted.

## Residual risk

- **FR-5 is warning-only by construction** and rests on a static AST name index, so dynamic
  dispatch, `getattr`, and config-driven binding are invisible to it. It is a floor on detection,
  never a proof of absence, and may not gate a verdict until its rates are measured. This is
  deliberate and stated in the design.
- **The registry is gitignored in this repo** (`.h-mad/` is in `.gitignore`), so `verify` reports
  `UNTRACKED` here until an operator adds `!.h-mad/wires.jsonl`. That is FR-3 working as designed —
  it refuses to report coverage it cannot persist — and is an operator decision, not a defect.
