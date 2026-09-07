# doc-block-exec — Phase 6a gap analysis

## Scope and method

This is an assessment of shipped commit `d61dd93`, not the dirty working-tree
overlay observed during the review.  The overlay adds a shared key-validity
predicate and a test for it; neither is in the stated HEAD.  Production and test
evidence below was read with `git show d61dd93:<path>` where that distinction
matters.

The AC denominator was mechanically enumerated with:

```sh
grep -nE '^  - AC-[0-9]+\.[0-9]+:' docs/01-plan/features/doc-block-exec.spec.md
printf 'AC_TOTAL='; grep -cE '^  - AC-[0-9]+\.[0-9]+:' docs/01-plan/features/doc-block-exec.spec.md
printf 'DUPLICATE_ANCHORS='; grep -oE '^  - AC-[0-9]+\.[0-9]+:' docs/01-plan/features/doc-block-exec.spec.md | sort | uniq -cd | wc -l
```

It returned `AC_TOTAL=49` and `DUPLICATE_ANCHORS=0`.  Thus the denominator is
49 unique ACs, not an eyeballed total.

Verdicts use **satisfied**, **partially satisfied**, and **not satisfied**.  A
test node is evidence of the shipped behaviour; an AC that depends on a failed
full-suite condition is not satisfied even if its local pin passes.

## AC-by-AC evidence

| AC | Verdict | Shipped evidence |
|---|---|---|
| AC-1.1 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_tagged_fence_under_heading_is_extracted` |
| AC-1.2 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_untagged_fence_is_not_a_candidate` |
| AC-1.3 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_two_tagged_blocks_without_index_are_ambiguous` |
| AC-1.4 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_index_selects_and_past_end_is_not_found` |
| AC-1.5 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_section_owns_deeper_headings`; `test_adjacent_heading_bounds_the_section`; `test_heading_lookalikes_are_not_headings` |
| AC-1.6 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_quoted_tag_inside_longer_fence_is_not_an_opener`; `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener` |
| AC-1.7 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse` |
| AC-1.8 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_extract_has_no_fence_state_of_its_own`; `h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` |
| AC-1.9 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_cli_index_zero_and_negative_are_bad_index` |
| AC-2.1 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_cli_subst_value_reaches_the_child` |
| AC-2.2 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_absent_key_refuses`; `test_empty_substitution_map_is_a_no_op` |
| AC-2.3 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_cli_missing_keys_list_in_argument_order` |
| AC-2.4 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_metacharacter_key_is_literal` |
| AC-2.5 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_multi_occurrence_count_equals_replacements` |
| AC-2.6 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_value_containing_another_key_is_not_rescanned` |
| AC-2.7 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_substitute_refuses_intersecting_spans`; `test_substitute_refuses_overlapping_occurrences_of_one_key`; `test_cli_subst_overlap_detail_lines` |
| AC-2.8 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_subst_without_equals_is_bad_subst`; `test_subst_empty_key_is_bad_subst`; `test_duplicate_substitution_key_refuses`; `test_subst_value_may_contain_equals` |
| AC-3.1 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_block_runs_in_the_temp_cwd` |
| AC-3.2 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_block_leaves_the_working_tree_untouched` |
| AC-3.3 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_unset_variable_fails_under_strict` |
| AC-3.4 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_bare_exit_in_plain_mode_returns_rc` |
| AC-3.5 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_pipefail_strict_vs_plain` |
| AC-3.6 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_streams_are_separate_str` |
| AC-3.7 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_unknown_info_key_refuses`; `test_duplicate_info_tokens_refuse` |
| AC-3.8 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_stream_paths_receive_the_streams`; `test_final_write_readback_catches_a_silent_no_op` |
| AC-3.9 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_hard_linked_stream_paths_refuse`; `test_alias_refusal_unlink_failure_reports_leftover` |
| AC-3.10 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_stream_path_fifo_without_reader_refuses_bounded`; `test_rollback_skips_unlink_on_identity_mismatch` |
| AC-3.11 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_preamble_binds_a_variable_and_leaves_text_unchanged`; `test_preamble_and_substitution_compose` |
| AC-3.12 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_failing_preamble_is_visible_as_the_combined_rc` |
| AC-3.13 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_cwd_mode_is_0700_under_hostile_umask`; `test_no_mktemp_invocation_in_source` |
| AC-3.14 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_cleanup_readback_catches_silent_retention`; `test_cleanup_failure_outranks_timeout_injected` |
| AC-4.1 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_ran_line_and_exit_zero_with_nonzero_rc`; `test_malformed_invocation_is_a_verdict` |
| AC-4.2 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_verdict_table_exit_codes` |
| AC-4.3 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_no_refusal_carries_rc` |
| AC-4.4 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_only_ambiguous_carries_blocks` |
| AC-4.5 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_every_emittable_line_has_a_registry_row`; `test_registry_rows_cover_only_emittable_lines` |
| AC-4.6 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_every_docblockerror_subclass_has_a_verdict`; `test_cli_launch_failed_lines` |
| AC-5.1 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_sleeping_block_times_out` |
| AC-5.2 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_in_group_descendant_is_reaped` |
| AC-5.3 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_no_timeout_invocation_in_source` |
| AC-5.4 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_temp_cwd_removed_after_timeout` |
| AC-5.5 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_timeout_survives_a_group_that_already_emptied`; `test_timeout_drain_is_bounded_against_an_escapee` |
| AC-5.6 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_cli_bad_timeout_values`; `test_unrepresentable_timeout_refuses_before_spawn` |
| AC-6.1 | satisfied | `h-mad/tests/test_h_mad_doc_block_exec.py::test_exactly_one_tagged_fence_in_the_tree` |
| AC-6.2 | satisfied | `h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec`; `test_exec_block_scan_performs_no_execution` |
| AC-6.3 | satisfied | `h-mad/tests/test_h_mad_collect_report_docs.py::test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`; `test_gate_block_does_not_exit_the_operators_shell` |
| AC-6.4 | satisfied | The local floor pin is `h-mad/tests/test_h_mad_doc_block_exec.py::test_suite_floor_holds`, and the full suite passes: `2792 passed in 465.32s`, 0 failed, re-derived by the orchestrator at HEAD `92ae93a` on a clean tree. [Bracket-correction: this row read `not satisfied` when first written, on a reading of `13 failed, 2778 passed`. That reading was a TORN TREE, not a defect — the orchestrator dispatched this gap analysis CONCURRENTLY with the Phase-6b fix, so the suite ran while `h_mad_doc_block_exec.py` was being edited underneath it. Three independent readings agree the tree is green: `2791 passed` before the fix, `2792 passed` reported by the fix dispatch, and `2792 passed` re-derived afterwards on the committed tree. The original reading is recorded rather than deleted, because the scheduling error is the finding.] |
| AC-6.5 | satisfied | `h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec`; `test_recipe_runs_through_run_block` |
| AC-6.6 | satisfied | `h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_refuses_an_untagged_recipe` |

## Classification and match rate

The following command counts the verdict column in the table above and computes
the rate using satisfied ACs only (partials are deliberately excluded):

```sh
awk -F'|' '/^\| AC-[0-9]+\.[0-9]+ / {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); total++; if ($3 == "satisfied") sat++; else if ($3 == "partially satisfied") partial++; else if ($3 == "not satisfied") unsat++} END {printf "satisfied=%d partial=%d not_satisfied=%d total=%d match_rate=%.2f%% (%d/%d)\n", sat, partial, unsat, total, 100*sat/total, sat, total}' docs/03-analysis/doc-block-exec.analysis.md
```

Result: `satisfied=49 partial=0 not_satisfied=0 total=49 match_rate=100.00% (49/49)`.
[Bracket-correction: first published as `satisfied=48 ... match_rate=97.96% (48/49)`. The single
`not satisfied` was AC-6.4, marked so on a torn-tree suite reading taken while the Phase-6b fix was
editing the module underneath this analysis — see that row. The figure above is the output of the
command in this section, re-run after the correction rather than retyped, at HEAD `92ae93a`.]
Partials therefore contribute zero to the numerator; there are none in this run.

## Verification

The requested command was run exactly as follows:

```sh
cd /Users/kimhawk/orca/skills/h-mad && python3.11 -m pytest tests/ -q
```

Its exact summary line, re-derived by the orchestrator on a clean tree at HEAD `92ae93a`, is:

```text
2792 passed in 465.32s (0:07:45)
```

AC-6.4's unqualified "full suite passes" requirement is therefore **satisfied**.

[Bracket-correction, and the superseded reading is kept because the cause is the finding.
This section first published `13 failed, 2778 passed in 461.99s (0:07:41)`, attributing the
failures to thirteen nodes in `tests/test_hmad_dispatch_audit_cycle.py`. That was a TORN TREE,
not a defect in this feature or in that suite: the orchestrator dispatched this gap analysis
CONCURRENTLY with the Phase-6b fix, so the suite ran while `h_mad_doc_block_exec.py` was being
rewritten underneath it. The two dispatches were treated as independent and were not — one edits
the module the other imports.

Three readings, taken at three separate instants, agree the tree is green and isolate the torn
one as the outlier:
  before the 6b fix, clean tree           2791 passed, 0 failed
  reported by the 6b fix dispatch itself  2792 passed, 0 failed
  re-derived after commit, clean tree     2792 passed, 0 failed   <- the line above
The +1 across the first and third is the fix's own pin test,
`test_empty_substitution_key_validation_routes_api_and_cli_through_one_predicate`, and it is
accounted for rather than absorbed.]

## Known open decision

`docs/01-plan/features/doc-block-exec.impl-plan.md:2894` records the open choice
between one shared CLI/API key-validity predicate and a cross-surface equivalence
test.  At shipped `d61dd93`, neither branch is present: the API guards with
`"" in subs` while the CLI guards with `raw.startswith("=")`.  This does **not**
affect any AC verdict: AC-2.8 requires both public surfaces to reject an empty
key with their respective API/CLI diagnostics, and the cited shipped tests cover
both.  It remains a maintainability/testing gap rather than an unmet acceptance
criterion.
