# Analysis: gate-non-py-production-files

Change review — 3489f86b..7584ace9 — GATING. Phase 6a gap analysis against spec v1.13, design v1.4 and impl-plan v1.3.

## Executive Summary
All 11 FRs and all 55 ACs are met at 7584ace9; I read the code for each AC and executed the behaviour. The documents disagree in places, and none of those disagreements moves a verdict.

## Match Rate: 100%

FR level: 11 of 11 FRs have every AC met. AC level: 55 of 55 met, 0 unmet. Census re-derived: `h_mad_ac_census.py` prints `ACS: OK count=55 frs=11`, and `grep` over the spec finds 55 AC bullets and 11 FR headings.

## Evidence
- read: 41 files opened (spec, design, impl-plan, inline-protocols; 3 gates; target_identity, tdd_judge, wire_pin_gate, mutation_harness; non_py_gate_support and 11 test modules, 2 of them by test-name listing only and 2 by diff only; fr9_drive.py, readings.tsv, provenance.json; 4 prose references, helper-scripts.md by diff only; 11 mutation specs), plus the per-row FR-9 evidence files of rows 001 and 013 and all 11 `implementer.txt` files
- ran: 25 commands before finalising this report
- tests run: `test_h_mad_parse_tasks_paths.py`, `test_h_mad_tdd_gate_docs.py`, `test_h_mad_wire_pin_gate.py`, `test_h_mad_doc_data.py`, `test_h_mad_parse_tasks_non_py.py`, `test_h_mad_tdd_judge_listing.py`, `test_h_mad_fr9_drive_refusals.py` (259 passed); `test_h_mad_tdd_gate_non_py.py`, `test_h_mad_codex_tdd_gate_non_py.py`, `test_h_mad_agy_tdd_gate_non_py.py`, `test_h_mad_target_identity.py`, `test_h_mad_tdd_gate_judge.py` (355 passed). All are under `h-mad/tests/`, run on a scratch archive of 7584ace9
- An earlier run reported `test_corpus_old_fields_unperturbed` as failed. That was a partial scratch archive with no docs corpus. On the full archive it passes
- The repository was not modified: every execution ran on a scratch archive or clone, and `git status --short` in the worktree is empty at HEAD 7584ace9

### Instruments, all executed by this analysis
1. **Independent conformance driver.** It uses the spec's fixture verbatim and each hook's real entry point, runs each host on its own, and uses `/bin/bash` 3.2 for Claude. Each Claude-author reading was preceded by the `TDD-IMPLEMENTER:` check. Result: `TOTAL 191 FAILED 0`, which is 164 AC readings and 27 adversarial readings. Referred to below as "driver". The adversarial readings were a listed target not yet on disk, a root path with a space, a quote and `%20`, an unlisted name with a space and `%`, nested state, `docs/`, `src/docs/` and `fixtures/` locations, and `.bats` at the gates. A further 15 readings printed separately gave the expected verdict on all hosts: a root spelled through the `/tmp` symlink, a symlinked directory, and symlinks crossing doc and code names.
2. **Direct unit readings** of FR-1, FR-2 and FR-4 on the spec's literal inputs. Referred to below as "unit".
3. **Mutation harness** on a scratch clone at 7584ace9 (`h_mad_mutation_harness.py`, scored on its token). Every spec printed `ALL_CAUGHT`, with `survived=0 refused=0 crash_kills=0 hollow_kills=0`: `wire_pin_ungated` 2, `parse_tasks_non_py` 3, `judge_non_py` 1, `listing_connections` 6, `listing_matcher` 14, `claude_gate_listing` 13, `codex_gate_listing` 10, `agy_gate_listing` 8, `doc_data_definition` 34, `fr9_drive_refusals` 9. Total 100 mutants. `--check-anchors` printed `ANCHORS_OK specs=214 mutations=3012 ok=3012 drifted=0`.
4. **FR-9 driver re-run** in the scratch clone at HEAD 7584ace9, `--out` to scratch. Every invocation printed `FR9-DRIVE: PASS`, and all 33 of the 33 rows are `PASS`. The base re-derived to `e097dfcb`, plan blob `fef08298`, copy sha256 `832298b3`.

### Abbreviations in the AC table
- Tests, under `h-mad/tests/`: CL = `test_h_mad_tdd_gate_non_py.py`, CX = `test_h_mad_codex_tdd_gate_non_py.py`, AG = `test_h_mad_agy_tdd_gate_non_py.py`, JL = `test_h_mad_tdd_judge_listing.py`, PT = `test_h_mad_parse_tasks_non_py.py`, PP = `test_h_mad_parse_tasks_paths.py`, WP = `test_h_mad_wire_pin_gate.py`, DD = `test_h_mad_doc_data.py`, DOC = `test_h_mad_tdd_gate_docs.py`, FR9T = `test_h_mad_fr9_drive_refusals.py`.
- Code, under `h-mad/`: `sh` = `hooks/h-mad-tdd-gate.sh`, `cx` = `hooks/h-mad-codex-tdd-gate.py`, `ag` = `hooks/h-mad-agy-tdd-gate.py`, `judge` = `scripts/h_mad_tdd_judge.py`, `id` = `scripts/h_mad_target_identity.py`, `wp` = `scripts/h_mad_wire_pin_gate.py`.
- E = `docs/03-analysis/probes/gate-non-py-production-files/fr9/20261105T094753Z-c4cedc6d0d00/`.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: parser records every backticked production path | 5 | 5 | Complete | `wp:243-247` |
| FR-2: `ungated` retired | 4 | 4 | Complete | `wp:295` (`check` has no `ungated`); U1 and U2 caught |
| FR-3: one listing matcher | 5 | 5 | Complete | `judge:307`, `judge:339`, `cx:294`, `ag:195`, `sh:343` |
| FR-4: judge by the Task's tests only | 6 | 6 | Complete | `judge:381`, `judge:492` |
| FR-5: Claude gate | 8 | 8 | Complete | `sh:328`, `sh:340-347`, `sh:196-216` |
| FR-6: codex gate | 5 | 5 | Complete | `cx:281-304`, `cx:359`, `cx:369` |
| FR-7: agy gate | 4 | 4 | Complete | `ag:174`, `ag:183-207` |
| FR-8: undecidable listing fails closed | 4 | 4 | Complete | `judge:342-347`, `cx:290`, `cx:295`, `ag:189`, `ag:196`, `sh:206` |
| FR-9: end-to-end proof | 5 | 5 | Complete | `fr9_drive.py`; E/readings.tsv; re-run passes |
| FR-10: prose | 3 | 3 | Complete | `phase5-substeps.md:213`, `:230`, `:235`; `codex-implementer-prompt.md:19-24`; `codex-runtime.md:29` |
| FR-11: doc/data allowed | 6 | 6 | Complete | `id:19`, `id:33-38`, `sh:266-269`, `sh:328`, `cx:359`, `ag:174` |

## Acceptance Criteria

| AC | Status | Code | Test that pins it | What was executed, and what it asserts |
|---|---|---|---|---|
| AC-1.1 | MET | `wp:245-247` | PT::test_mixed_production_line_collects_all_three; PT::test_judge_cli_finds_each_token_of_a_mixed_production_line | Unit on the literal line: exactly the 3 strings. The test asserts list equality, using `x.sh` in place of `hmad-dispatch.sh` (Nit) |
| AC-1.2 | MET | `wp:245-247` | PP::test_paths_label_spelling, ::test_none_value_contributes_nothing, ::test_none_rule_keeps_a_real_path, ::test_label_lines_accumulate, ::test_existing_fields_unchanged, ::test_corpus_old_fields_unperturbed; PT::test_python_only_production_line_keeps_items_and_order | PP passes, and `git diff 3489f86b..7584ace9` on PP is empty, so it passes unmodified |
| AC-1.3 | MET | `wp:243` | PT::test_none_value_production_stays_empty; PT::test_judge_cli_ignores_a_none_production_value | Unit on the literal line: `[]` |
| AC-1.4 | MET | `wp:244-246` | PT::test_non_py_test_token_stays_out_of_tests_and_production; PT::test_judge_cli_ignores_a_non_py_test_token | Unit on the literal line: `tests == []` |
| AC-1.5 | MET | `wp:247` touches `production` only | PT::test_other_task_fields_match_with_and_without_a_non_py_token; PT::test_wire_pin_cli_output_ignores_a_non_py_token | Unit: all 9 named fields equal, with real values (budget 37, runner pytest) |
| AC-2.1 | MET | `wp` `main`, print loop deleted | WP::test_cli_prints_no_ungated_line | CLI run with a Test line and on the literal Production-only plan: first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0`, no `ungated:` |
| AC-2.2 | MET | `wp:295` | WP::test_check_and_tasks_carry_no_ungated_key | Unit: key absent from `check()` and from the task dict |
| AC-2.3 | MET | `wp:295` | WP::test_an_unshaped_plan_with_a_non_python_token_stays_unshaped | Unit: `verdict: UNSHAPED`, the remaining keys retained |
| AC-2.4 | MET | `wire_pin_ungated.json` | U1 → WP::test_a_shell_production_file_is_collected_in_production; U2 → WP::test_an_extensionless_production_path_is_collected_in_production | Harness: 2 mutants, 2 caught, 0 survived. U3, U4 and U5 retired; `_why` records it |
| AC-3.1 | MET | `judge:339`; `cx:294`; `ag:195`; `sh:199`, `sh:343` | Callee: CX-CALLEE, AG-CALLEE, CL-CALLEE. Connection: CX-REMOVE/FORCE, AG-REMOVE/FORCE, CL-REMOVE/FORCE, each naming that host's own test (CX::test_codex_listed_absent_test_denies, CX::test_codex_unlisted_code_like_allows, and the AG and CL equivalents) | Harness: listing_connections 6/6 and listing_matcher 14/14, `refused=0` (landing verified), `crash_kills=0`, every kill by its named test |
| AC-3.2 | MET | `id` canonicalise; `sh:343`; `cx:294`; `ag:195` | CL/CX/AG::test_*_symlink_alias_denies | Driver: `test-missing` on 3 hosts |
| AC-3.3 | MET | same | CL/CX/AG::test_*_case_fold_spelling_denies | Driver on APFS: `test-missing` on 3 hosts |
| AC-3.4 | MET | `judge:339-343`, `judge:381` | CL/CX/AG::test_*_hard_link_denies | Driver: `test-missing` on 3 hosts. The reason text comes from the `impl-plan` branch; a non-`.py` name map prints nothing (AC-4.6) |
| AC-3.5 | MET | `judge:329` (realpath compare) | CL/CX/AG::test_*_residual_spellings_allow; JL::test_listing_residual_spellings_are_not_listed | Driver: all three spellings ALLOW on 3 hosts |
| AC-4.1 | MET | `judge:381` | JL::test_judge_listed_non_py_failing_test_is_red_measured | Unit: `Verdict('ALLOW','red-measured','', 'impl-plan', …/tests/test_tool.py)` |
| AC-4.2 | MET | same | JL::test_judge_listed_non_py_passing_test_is_test_passing | Unit: `DENY test-passing` |
| AC-4.3 | MET | `judge:381-383` | JL::test_judge_listed_non_py_absent_test_is_test_missing | Unit: `DENY test-missing`, reason names `tests/test_tool.py` |
| AC-4.4 | MET | `judge:381-383` | JL::test_judge_listed_non_py_with_no_pytest_file_is_test_missing | Unit and driver with the literal `tests/tool.bats`: `DENY test-missing`. The test uses `tests/tool.sh` (Nit) |
| AC-4.5 | MET | `judge:492` | JL::test_target_module_names_is_empty_for_a_non_py_target; JL::test_non_py_module_not_found_scores_pytest_error; K-IMPORT-NONPY | Unit: both names give `frozenset()`. Guard on: `DENY pytest-error`. Guard removed: `ALLOW red-measured`. Harness: K-IMPORT-NONPY caught. `test_h_mad_tdd_judge.py` has no diff in the range |
| AC-4.6 | MET | `judge:381` and the name-map branch | JL::test_judge_unlisted_non_py_is_no_test_resolved | Unit: `DENY no-test-resolved`, `name map: empty for scripts/tool.sh` |
| AC-5.1 | MET | `sh:340-349`, `sh:402-407` | CL::test_claude_listed_absent_test_denies | Driver: `test-missing`; arrangement line correct; E row 001 |
| AC-5.2 | MET | same | CL::test_claude_listed_passing_test_denies; CL::test_claude_listed_failing_test_allows | Driver: `test-passing`, ALLOW |
| AC-5.3 | MET | same | CL::test_claude_listed_extensionless_absent_test_denies | Driver: `test-missing` |
| AC-5.4 | MET | `sh:203`, `sh:328` | CL::test_claude_unlisted_code_like_allows; CL::test_claude_unlisted_doc_data_allows | Driver: ALLOW, ALLOW |
| AC-5.5 | MET | `sh:358-369` | CL::test_claude_default_authorship_refuses_a_listed_target; CL::test_claude_default_authorship_allows_unlisted_doc_data | Driver: line `TDD-IMPLEMENTER: codex chosen=codex switch=none`; `codex-authorship`; ALLOW |
| AC-5.6 | MET | `sh:301`, `judge:734` | CL::test_claude_no_state_file_allows_a_listed_target; CL::test_claude_inactive_record_allows_a_listed_target | Driver: ALLOW in both arms |
| AC-5.7 | MET | `sh:313` | CL::test_claude_listed_exempt_location_allows | Driver with the literal `tests/helper.sh`: ALLOW |
| AC-5.8 | MET | `judge:343`, `sh:344` | CL::test_claude_selection_s1_allows; CL::test_claude_selection_s2_denies | Driver: S1 ALLOW, S2 `test-missing`. The test also asserts `hard.sh` and `test_hard.py` in the reason |
| AC-6.1 | MET | `cx:294-303`, `cx:369` | CX::test_codex_listed_absent_test_denies | Driver: `test-missing`; E row 004 |
| AC-6.2 | MET | same | CX::test_codex_listed_passing_test_denies; CX::test_codex_listed_failing_test_allows | Driver: `test-passing`, ALLOW |
| AC-6.3 | MET | `cx:297`, `cx:359` | CX::test_codex_unlisted_code_like_allows; CX::test_codex_unlisted_doc_data_allows | Driver, including the literal `*** Add File: notes.md`: ALLOW. The test drives `Update File` only (Should-fix) |
| AC-6.4 | MET | `cx:369` inside the `M:G5` loop | CX::test_codex_multi_target_patch_denies_on_the_listed_target | Driver, with the test absent and with it failing: DENY `test-missing`, ALLOW |
| AC-6.5 | MET | `judge:343`, `cx:299` | CX::test_codex_selection_s1_allows; CX::test_codex_selection_s2_denies | Driver: S1 ALLOW, S2 `test-missing` |
| AC-7.1 | MET | `ag:195-206` | AG::test_agy_listed_absent_test_denies | Driver: deny; E row 007 ends `kind=test-missing`. The helper asserts `endswith` and one `kind=` |
| AC-7.2 | MET | same | AG::test_agy_listed_passing_test_denies; AG::test_agy_listed_failing_test_allows | Driver: `test-passing`, `{"decision":"allow"}` |
| AC-7.3 | MET | `ag:174`, `ag:200` | AG::test_agy_unlisted_code_like_allows; AG::test_agy_unlisted_doc_data_allows | Driver: allow, allow |
| AC-7.4 | MET | `judge:343`, `ag:202` | AG::test_agy_selection_s1_allows; AG::test_agy_selection_s2_denies | Driver: S1 allow, S2 deny `test-missing` |
| AC-8.1 | MET | `judge:345`, `cx:295`, `ag:196`, `sh:206` | CL/CX/AG::test_*_unreadable_plan_is_judge_error | Driver with invalid UTF-8: `judge-error` on 3 hosts |
| AC-8.2 | MET | `judge:735`, `cx:290`, `ag:189`, `sh:206` | CL/CX/AG::test_*_unreadable_state_is_judge_error | Driver with the literal `scripts/other.sh` and `{not json`: `judge-error` on 3 hosts. The tests use `scripts/tool.sh` (Should-fix) |
| AC-8.3 | MET | `judge:317` | CL/CX/AG::test_*_absent_plan_allows; JL::test_listing_absent_plan_is_not_listed | Driver: ALLOW on 3 hosts |
| AC-8.4 | MET | `sh:328`, `cx:359`, `ag:174` | CL/CX/AG::test_*_doc_data_allows_in_undecidable_states | Driver: 12 readings (2 states × 2 targets × 3 hosts), all ALLOW |
| AC-9.1 | MET | `fr9_drive.py:139-141`, `:217-219`, `:257` | FR9T::test_fr9_driver_refuses (authorship-line) for the check | E rows 001-009 read as required; 3 Claude `implementer.txt` hold the required line; re-run PASS |
| AC-9.2 | MET | `fr9_drive.py:82-95` | FR9T::test_fr9_driver_refuses (dirty-hooks, hook-outside-tree, hook-blob-mismatch) | Evidence sha256 `73b0dbc5…`, `c23296c3…`, `d75edbe1…` equal `git show 7584ace9:<hook> \| shasum -a 256`. Evidence was taken at c4cedc6d; `git diff --name-only c4cedc6d 7584ace9` lists only the archreview and evidence files, so `h-mad/` is identical |
| AC-9.3 | MET | 59 new `# M:` markers in hooks, scripts and driver | the 10 specs above | Python census of markers against `find` text: 57 of 59 match directly. `M:G-DOCDATA-CASE` is covered by DD-CASE and DD-SUFFIX, which anchor the same line without the marker. `M:W7` is a launch line, not a guard, and has no row (Should-fix). Harness: 100/100 caught, `crash_kills=0`, `hollow_kills=0` |
| AC-9.4 | MET | `fr9_drive.py:142-150`, `:203-214` | none (evidence is the proof) | E rows 010-033: all 12 before rows ALLOW; after rows DENY `test-missing` on the listed-absent row and ALLOW on the others, per host. Re-run PASS. The 8 Claude replay rows hold the required line |
| AC-9.5 | MET | `fr9_drive.py:72-79`, `:98-111` | FR9T::test_fr9_driver_refuses (missing-base, base-is-head, plan-absent-at-base, plan-blob-mismatch) | Re-derived: `git merge-base 7584ace9 origin/main` = `e097dfcb`; blob = `fef08298…`; `git show e097dfcb:<plan> \| shasum -a 256` = `832298b3…`, equal to provenance. Before-side hook sha `c88d29f5…` reproduced from `e097dfcb` |
| AC-10.1 | MET | prose | DOC::test_gate_prose_has_no_retired_phrasing (8 branches) | Ran at 7584ace9: no line, for the 5-branch and for the design's 8-branch regex. Control at e4979ecd: 4 lines, 3 files, 5 occurrences (`git grep -o \| wc -l` = 5) |
| AC-10.2 | MET | `codex-implementer-prompt.md:19-24` | DOC::test_hook_bullets_state_the_shipped_rule | Passes. The diff adds the 11 tokens and removes none. Control on the e4979ecd bullets: each of the 11 tokens matches 0 of 4 bullets |
| AC-10.3 | MET | `phase5-substeps.md:230`, `:235` | DOC::test_skill_states_the_docs_first_component_rule | Passes. Anchor count is asserted as 1 and the five tokens are in the paragraph; `Both gates` is gone. The anchor's first words occur 0 times at e4979ecd |
| AC-11.1 | MET | `id:38`, `sh:328`, `cx:359`, `ag:174` | CL/CX/AG::test_*_listed_doc_data_allows | Driver: ALLOW on 3 hosts; control DENY per AC-5.1, 6.1, 7.1 |
| AC-11.2 | MET | `id:34` | CL/CX/AG::test_*_listed_upper_case_doc_data_allows | Driver: `CHANGES.MD` and `changes.md` ALLOW on 3 hosts |
| AC-11.3 | MET | `id:19`, `id:34` | CL/CX/AG::test_*_doc_data_member_allows (9 parameters each) | Driver: 54 readings (9 × 2 × 3), all ALLOW |
| AC-11.4 | MET | `id:34`, gates | CL/CX/AG::test_*_excluded_member_denies (7 parameters each) | Driver: 21 readings, all `test-missing` |
| AC-11.5 | MET | `id:38` | CL/CX/AG::test_*_mixed_hard_links_deny | Driver: `test-missing` on 3 hosts |
| AC-11.6 | MET | `id:19`, `sh:266` (no bash copy) | DD-CX-*, DD-AG-*, DD-CL-* naming each host's `[<suffix>]` parameter | Harness: 34/34 caught, including all 27 per-host per-suffix rows, `crash_kills=0`, each killed by its named test |

## Gaps
None

No AC is unmet, so the §4.5 classification table has no entry. The document disagreements are under Should-fix: they are reported, not resolved, and no verdict depends on them.

## Test Results
```
.venv/bin/python -m pytest -q   (at 7584ace9, measured by the orchestrator; not re-run)
8583 passed, 4 warnings in 2255.66s
```
Scoped re-runs by this analysis, on scratch archives of 7584ace9: 259 passed and 355 passed (modules listed under Evidence).

## Verdict
Match rate: 100% (threshold: 90%). Tests: 8583/8583 passing, per the orchestrator's measurement.
→ Advance to Phase 7. 0 gaps to close. The Should-fix items below do not gate.

## Must-fix
None

## Should-fix
- `# M:H-LIST-CONTEXT` is a shipped behaviour that spec, design and impl-plan never name, and the design says this region is unchanged. It prefixes `target=<selected>` to listed-target refusals. `grep -n H-LIST-CONTEXT` over the three documents prints nothing, and the plan's ledger says `claude_gate_listing.json` 12 where the tree has 13 rows, all caught. It cannot change a verdict and is gated on `ALL_NON_PY`, so `.py` output is untouched. Record it in the design and the ledger, because a later reader takes the design's "unchanged" as true. Introduced in d25bf350.
  quote: docs/02-design/features/gate-non-py-production-files.design.md:313 › `_read_state --target "$TARGET_PATH"  # M:H3   (unchanged from here to the end)`
  quote: h-mad/hooks/h-mad-tdd-gate.sh:406 › `[ "$ALL_NON_PY" = yes ]; then _refuse "${BASH_REMATCH[1]}" "target=$TARGET_PATH: ${BASH_REMATCH[2]}"; fi  # M:H-LIST-CONTEXT`
- Spec FR-5 and the shipped order disagree in wording (document disagreement, not an unmet AC). The spec orders "read state" before "decide listing"; the code calls `_read_listing` at line 343 and `_read_state` at line 349. The design argues this is one process doing both in order, citing the NFR's permission to merge, and a merged verb does read the chain first (`judge:730-740`). The driver found no verdict difference. I believe the spec's step wording should change to name the merged verb. This is the operator's or the document owner's call, and the code should stay.
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:135 › `1. Read state. `TDD-STATE: none` means ALLOW.`
  quote: docs/02-design/features/gate-non-py-production-files.design.md:330 › `**Steps 1 and 2 run in one process.**`
- Design v1.4 still describes eight driver refusals and an exit-1 residual, while the driver ships nine. Impl-plan departure 9 declares this and cites an operator ruling of 2026-11-04, and the code follows the plan. The design should be updated. `unverified`: the spec's Assumptions list rulings R-A to R-D and `grep` finds no plan-absent ruling in the spec, so the ruling is visible only through the impl-plan (lines 29 and 1124). I did not find its primary record.
  quote: docs/02-design/features/gate-non-py-production-files.design.md:465 › `The driver prints eight `FR9-DRIVE: UNREADABLE` reasons`
  quote: docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py:101 › `raise Refusal("plan-absent-at-base")`
- AC-8.2's stated target has no test on any host. The AC names the unlisted `scripts/other.sh`; all three `test_*_unreadable_state_is_judge_error` tests write the listed `scripts/tool.sh`. The driver read `judge-error` on the literal target on all three hosts, so the behaviour holds. A scratch mutant shows the gap: narrowing `# M:CX-CHAIN-UNREADABLE` to `names[0].name == "tool.sh"` leaves `test_h_mad_codex_tdd_gate_non_py.py` at `54 passed`, while an unlisted write in an unreadable state becomes ALLOW, and FR-8 states the opposite for that write. The mutant is contrived; the point is that nothing pins the AC's own target.
  quote: h-mad/tests/test_h_mad_codex_tdd_gate_non_py.py:83 › `_expect(root, "scripts/tool.sh", "deny", "judge-error",`
- AC-6.3's `*** Add File: notes.md` form is not driven by the new codex test module, because `run_codex` always writes an `Update File` header. `test_h_mad_codex_tdd_gate_judge.py` does use `Add File` headers, for other paths. The driver read ALLOW on the literal patch. An `Add File` for a listed script that does not exist yet is what a GREEN step that creates that script sends, and it has no non-py test. A scratch run read DENY `test-missing` on that patch, so the behaviour holds and only the pin is missing.
  quote: h-mad/tests/non_py_gate_support.py:183 › `patch = f"*** Begin Patch\n*** Update File: {relative}\n@@\n-x\n+y\n*** End Patch\n"`
- `# M:W7`, the new judge launch, has a marker and no mutation row, unlike its siblings `# M:W2` and `# M:W5B`, which have `W2R`/`W2F` and `W5BR`/`W5BF` rows in `claude_gate_judge_wiring.json`. AC-9.3 stays met, because AC-3.1 names the `M:H-LIST` call-site mutants as the connection entries. A scratch mutant replacing the launch with a constant `not-listed` was killed by `CL::test_claude_listed_absent_test_denies` (`1 failed`), so adding a row costs one spec entry and needs no new test.
  quote: h-mad/hooks/h-mad-tdd-gate.sh:199 › `LOUT=$(python3 "$JUDGE" listing --root "$ROOT_ABS" ${LARGS[@]+"${LARGS[@]}"} 2>/dev/null; printf 'rc=%s' "$?")  # M:W7`

## Nit
- AC-4.4's test uses `tests/tool.sh` where the AC says `tests/tool.bats`, and AC-1.1's test uses `x.sh` where the AC says `hmad-dispatch.sh`. Both literal inputs read correctly when I ran them, and `.bats` is the only named case, so spelling it would close the difference.
- A file named exactly `.py` gives split readings on an unlisted write: Claude DENY `no-test-resolved`, codex and agy ALLOW. The Terms call a name ending in `.py` not non-`.py`, while `Path(".py").suffix` is empty at `# M:CX-NOT-CODE-LIKE`, `# M:AG-NOT-CODE-LIKE` and `# M:K-IMPORT-NONPY`. The `_is_production_python` half of the split is on lines this range did not edit; I did not run the base commit.
- Spec FR-11's `M5` reach figures (128 tokens, 80 and 48) were not re-derived. No AC names them, and they do not affect a verdict.

## Version History
- v1.0: Initial gap analysis draft, Phase 6a, first measurement at 7584ace9.
