# Gap Analysis — anchor-precheck-phase-5e-wiring

**Phase:** 6a
**Base:** `b5c8f41` (5c) → **Head:** `adc735b`
**Spec:** 7 FRs / 38 ACs
**Suites:** h-mad 2105 passed · handoff 57 passed
**Sweep:** `ANCHORS_OK specs=17 mutations=244 ok=244 drifted=0 unreadable=0`
**Mutation:** `ALL_CAUGHT mutations=36 caught=36 survived=0 refused=0`
**6a-prime:** `READY_TO_MERGE` (cycle 7). Seven cycles: 3, 2, CLEAN, 3, 2, 2, CLEAN — twelve findings raised, nine accepted and fixed, three rejected on their premises. Cycle 3's clean verdict did NOT hold: cycle 4 then found a Critical vacuous pass.

## Match rate

**Match rate: 100%** — 38 of 38 ACs satisfied.

Each row names the pinning test, or the live verification where the AC is about
observable binary behaviour rather than a unit-testable property.

## FR-1 — a relative `root` resolves against the spec's own directory

| AC | Evidence |
|---|---|
| AC-1.1 | `test_relative_root_is_resolved_against_the_spec_dir_from_any_cwd` — three cwds, one resolved value |
| AC-1.2 | `test_absolute_root_is_used_exactly_from_any_cwd` |
| AC-1.3 | `test_absent_root_defaults_to_the_spec_file_directory` |
| AC-1.4 | `test_precheck_and_run_share_the_root_resolver` — per-call counts, plus asserts the old expression is gone |
| AC-1.5 | Pre-existing suite unchanged and green |

## FR-2 — every committed spec carries a portable, spec-relative root

| AC | Evidence |
|---|---|
| AC-2.1 | `test_no_committed_spec_has_an_absolute_root` (walks the repository, non-vacuity guarded) |
| AC-2.2 | Live: identical `ANCHORS_OK specs=17 mutations=243 ok=243` from repo root, `/tmp`, and `/Users/kimhawk` |
| AC-2.3 | Live: identical verdict with the skills copied to an unrelated absolute path |
| AC-2.4 | Live: run inside a `git worktree` resolved into the worktree and left the main checkout byte-identical; the pre-change absolute root was shown to resolve to the **main checkout** from inside that worktree |
| AC-2.5 | Fingerprint before/after: every `(find, replace)` byte-identical, every count unchanged; cross-checked against `git show HEAD` for all 17 |
| AC-2.6 | `test_every_committed_spec_resolves_within_its_own_skill` (uses `_resolve_root`, last-`tests`-component skill dir) |

## FR-3 — the run refuses when any spec in its set has drifted

| AC | Evidence |
|---|---|
| AC-3.1 | **WIRE-PIN** `test_clean_spec_beside_a_drifted_sibling_refuses_before_mutating` — verdict, absence of count keys, byte identity |
| AC-3.2 | `test_all_clean_sibling_directory_still_runs_to_ordinary_verdict` (fall-through) |
| AC-3.3 | `test_sibling_precheck_refusal_names_spec_mutation_and_resolved_root` |
| AC-3.4 | `test_self_drift_and_sibling_drift_have_distinct_refusal_text` |
| AC-3.5 | `test_drifted_spec_in_a_different_directory_does_not_affect_run` |
| AC-6.4-wire | `test_all_caught_result_carries_sibling_precheck_census` |

**Wire discrimination, both directions, run twice (before and after the cycle-1 shape change):**
removing the call fails the WIRE-PIN; forcing the precheck to fire unconditionally fails the
fall-through. Each mutation was asserted to have landed before its result was trusted.

## FR-4 — the refusal is a distinct verdict carrying no mutation counts

| AC | Evidence |
|---|---|
| AC-4.1 | `test_precheck_failed_summary_line_has_sweep_counts_and_no_mutation_counts`; live line checked for each of the four forbidden substrings individually |
| AC-4.2 | `test_precheck_failed_exits_two`; live exit code 2 |
| AC-4.3 | `test_refused_consumers_do_not_match_precheck_failed` (repository grep) |
| AC-4.4 | `test_precheck_failed_emits_hmad_marker`; live `[H-MAD] … PRECHECK_FAILED` |
| AC-4.5 | Re-anchored in the same commit as the summary-line change (`fa3434b`); `ANCHORS_OK` after |
| AC-4.6 | `test_specerror_sibling_is_unreadable_precheck_failed_with_zero_drift`; live `drifted=0 unreadable=1` naming the loader's error text |

## FR-5 — the suite asserts the repository's own committed specs are un-drifted

| AC | Evidence |
|---|---|
| AC-5.1 | `test_committed_mutation_specs_are_not_drifted` (both projects) |
| AC-5.2 | Non-vacuity assert in the walk helper; driven empirically with an empty directory in **both** copies — each raises |
| AC-5.3 | Located from `Path(__file__).resolve().parents[1]`; verified from repo root, project dir, and via the skills symlink |
| AC-5.4 | Calls `precheck_spec()`; no second copy of the one-match rule |
| AC-5.5 | `test_committed_mutation_spec_drift_check_is_discriminating` (both projects) — drifts a committed anchor, asserts the failure, restores original bytes in `finally` and verifies by re-reading. Confirmed under a full-suite run that no committed spec is left modified. |

## FR-6 — a non-spec file is never mistaken for drift

| AC | Evidence |
|---|---|
| AC-6.1 | `test_classifier_agrees_with_load_spec_on_the_mutations_gate` — differential over a shared corpus, not two examples |
| AC-6.2 | `test_unparseable_json_is_named_and_not_counted_as_anchor_drift` |
| AC-6.3 | `test_spec_classification_does_not_skip_a_spec_that_fails_deeper_validation`; live: a corrupt spec stays `UNREADABLE` driving `ANCHORS_DRIFTED` with `skipped=0` |
| AC-6.4 | `test_anchor_sweep_names_skipped_and_unclassifiable_files_on_success` and `test_cli_names_skipped_and_unclassifiable_siblings_on_success`; live on both the sweep and a mutation run |
| AC-6.5 | `test_every_committed_mutation_spec_classifies_as_spec` |
| AC-6.6 | Differential corpus of 8 run pre/post against a softening list **enumerated before the change**; exactly the three intended softenings observed, items 3 and 4 did not soften |

## FR-7 — documentation states the obligation as mechanical

| AC | Evidence |
|---|---|
| AC-7.1 | `test_skill_documents_the_precheck_is_automatic` — asserts the new claim present **and** the stale operator instruction gone |
| AC-7.2 | `test_recovery_table_carries_the_new_verdict` — SKILL.md registry entry and the module docstring verdict table |
| AC-7.3 | Same test — spec-relative root documented in both surfaces |
| AC-7.4 | Same test |
| AC-7.5 | Same test — `failure-recovery.md` row with halt reason and remedy |

## Findings from the 6a-prime cycles (all fixed)

Cycle 1 (3) — result shape used a side-channel flag on the reused dict; skipped files dropped
from the suite assertion message; the sweep summary line grew two fields.
Cycle 2 (2) — AC-5.5's discrimination was never a committed test; `main()` never named skipped
siblings on a mutation run. The cycle-2 edit also introduced three duplicate top-level
definitions, found by grepping for duplicates rather than by the green suite.

## Defects found by mutation that the suite could not see

- `a-bad-spec-aborts-the-sweep` survived after Task 3, killed by the wrong assertion: its
  fixture was a **missing** file, which the new classifier skips before `precheck_spec` runs, so
  the test no longer reached the branch it names.
- The same mutation's anchor later matched **twice** after Task 4 added a second `except
  SpecError`, so it measured nothing while printing a verdict-shaped line. Re-anchored.


## Findings raised across the seven 6a-prime cycles

Twelve raised, nine accepted and fixed, three rejected on their premises.

| # | Cycle | Finding | Outcome |
|---|---|---|---|
| 1 | c1 | `run_spec` returned `REFUSED` + a side-channel flag on the reused dict, carrying every mutation count key | fixed — design's separate `PRECHECK_FAILED` dict |
| 2 | c1 | skipped files dropped from the committed-spec assertion message | fixed, both projects |
| 3 | c1 | the `--check-anchors` summary grew `skipped=`/`unclassifiable=` | fixed — summary restored to five pinned fields, detail lines kept |
| 4 | c2 | AC-5.5's discrimination existed only as a hand-run, never a committed test | fixed — drift/restore test in both projects, restore verified by re-read under `finally` |
| 5 | c2 | `main()` never named skipped siblings on a mutation run | fixed — named on every verdict |
| 6 | c4 | **`--check-anchors` returned `ANCHORS_OK` on a sweep that examined nothing** | fixed — new `ANCHORS_NOTHING_SWEPT`, exit 2 |
| 7 | c4 | a "Facade-Routing invariant" violation | **rejected** — no such invariant in either layer (checked with a positive control); contradicts c1's own accepted fix |
| 8 | c4 | `ANCHORS_DRIFTED`/`REFUSED` each absorb two cannot-judges | **deferred** — pre-existing F2, operator decision; filed as J37 |
| 9 | c5 | the suite assertion FAILED on any skipped file | fixed — skipped named but non-gating; both directions pinned |
| 10 | c5 | the classifier/loader agreement test omitted the AC-6.3 shape | fixed in the test; the prescribed `_load_spec` reorder **rejected** as not what AC-6.1 asks |
| 11 | c6 | **the WIRE-PIN had gone vacuous** — c1's fresh-dict fix made "keys absent" true by construction | fixed — monkeypatched `_suite_is_green`/`Path.write_text`, proven to fail when the refusal is moved after the loop |
| 12 | c6 | AC-6.6 should be a unit test | **rejected** — AC-6.6's own text: "A passing suite is not accepted as evidence for this AC" |

Findings 6 and 11 are the two that a green suite could never have surfaced, and both were
defects the feature introduced into its own guarantees: a sweep that measured nothing reporting
OK, and the feature's most important test quietly ceasing to test ordering because an earlier
fix in the same feature changed the shape it asserted on.
