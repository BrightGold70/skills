# Analysis: gate-non-py-production-files

Change review — 3489f86b..57e4f9fc — GATING. Phase 6 gap analysis, second measurement, against spec v1.14, design and impl-plan at 57e4f9fc. Files opened: 59 (46 read in slices or whole, 13 by grep or diff only).

## Executive Summary
Every gate verdict the spec names holds on all three hosts at 57e4f9fc, but AC-9.3 is unmet: three new FR-8 and FR-3 decision arms in the judge have no mutation-spec entry, so FR-9 is partial. Existing tests already kill all three arms, so this is a gap in the mutation ledger and no verdict is wrong today.

## Match Rate: 91%

FR level: 10 of 11 FRs have every AC met (10/11 = 90.9, stated as 91). AC level: 54 of 55 met, 1 unmet. Census taken from the spec's AC bullets: 55 ids across 11 FRs, and each id has a row below.

## Evidence
- read: 59 files. Spec; inline-protocols; design and impl-plan (slices); 3 gates; judge, target_identity and wire_pin_gate; 6 references including SKILL.md, agy-runtime.md and helper-scripts.md; non_py_gate_support.py and 13 test modules; fr9_drive.py; readings.tsv, provenance.json and 4 per-row FR-9 evidence file types; 13 mutation specs; analysis.v1.md (opened only after my AC table was complete); archreview.v6.md. By grep or diff only: mutation harness, phase7_preconditions, helper-scripts, 5 test modules (agy non_py, doc_data, wire_pin_gate, target_identity, tdd_gate_judge), archreview.v1 to v5.
- ran: 23 commands before writing this report.
- tests run, all on scratch archives of 57e4f9fc, under `h-mad/tests/`: `test_h_mad_tdd_gate_docs.py`, `test_h_mad_tdd_judge_listing.py`, `test_h_mad_parse_tasks_non_py.py`, `test_h_mad_doc_data.py`, `test_h_mad_wire_pin_gate.py`, `test_h_mad_parse_tasks_paths.py`; then `test_h_mad_tdd_gate_non_py.py`, `test_h_mad_codex_tdd_gate_non_py.py`, `test_h_mad_agy_tdd_gate_non_py.py`, `test_h_mad_codex_gate_tmp_reports.py`, `test_h_mad_fr9_drive_refusals.py`, `test_h_mad_target_identity.py`, `test_h_mad_tdd_gate_judge.py`.
- The repository was not modified: `git status --short` in the worktree printed nothing after all runs, and HEAD stayed 57e4f9fc.
- Three of my own false starts, stated so they are not mistaken for findings. My first driver fixture had no `.venv`, so nine readings gave `pytest-missing`; with a `.venv` built the way fr9_drive.py builds it, all nine read as specified. `test_corpus_old_fields_unperturbed` failed on a partial archive with no tracked docs corpus; once the docs were committed in the archive, `test_h_mad_parse_tasks_paths.py` read `23 passed`. The harness printed `MUTATION: PRECHECK_FAILED specs=200 drifted=0 unreadable=2` on that same partial archive; on a whole-commit archive it ran as listed below.

### Instruments, all executed by this analysis
1. **Independent driver.** It is my own code and imports none of the repository's test helpers. It uses the spec's fixture, each hook's real entry point and stdin payload, an explicit minimal environment (HOME, PATH, LANG, TMPDIR), and `/bin/bash` for Claude. It runs each host alone. Result on AC readings: 178 readings in the first pass plus 15 in the `.venv` pass, 0 wrong once the fixture was corrected. Authorship lines read as the spec requires: `TDD-IMPLEMENTER: claude chosen=codex switch=peers-out reason=env` and `TDD-IMPLEMENTER: codex chosen=codex switch=none`. Referred to below as "driver".
2. **Direct readings.** FR-1, FR-2 and FR-4 were read in-process on the spec's literal inputs, including AC-4.5 with and without the guard. Referred to below as "unit".
3. **Three-tree comparison.** The same probes ran on 3489f86b (base), 7584ace9 (v1) and 57e4f9fc (head). See §"Later production changes".
4. **Hand mutants driven through real hooks.** See §"Mutants driven through the real hooks".
5. **Mutation harness sample**, whole-commit archive, `--isolate` with an absolute `--python`: `wire_pin_ungated` `ALL_CAUGHT mutations=2`, `judge_non_py` `ALL_CAUGHT mutations=1`, `listing_connections` `ALL_CAUGHT mutations=6`, each with `survived=0 refused=0 hollow_kills=0`. The other specs' figures are the orchestrator's measurement, and I read their rows.

### Abbreviations in the AC table
- Tests, under `h-mad/tests/`: CL = `test_h_mad_tdd_gate_non_py.py`, CX = `test_h_mad_codex_tdd_gate_non_py.py`, AG = `test_h_mad_agy_tdd_gate_non_py.py`, JL = `test_h_mad_tdd_judge_listing.py`, PT = `test_h_mad_parse_tasks_non_py.py`, PP = `test_h_mad_parse_tasks_paths.py`, WP = `test_h_mad_wire_pin_gate.py`, DD = `test_h_mad_doc_data.py`, DOC = `test_h_mad_tdd_gate_docs.py`, FR9T = `test_h_mad_fr9_drive_refusals.py`.
- Code, under `h-mad/`: `sh` = `hooks/h-mad-tdd-gate.sh`, `cx` = `hooks/h-mad-codex-tdd-gate.py`, `ag` = `hooks/h-mad-agy-tdd-gate.py`, `judge` = `scripts/h_mad_tdd_judge.py`, `id` = `scripts/h_mad_target_identity.py`, `wp` = `scripts/h_mad_wire_pin_gate.py`.
- E = `docs/03-analysis/probes/gate-non-py-production-files/fr9/20261106T014611Z-e524b58a6e47/`. drive = `docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py`.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: parser records every backticked production path | 5 | 5 | Complete | `wp:243-247` |
| FR-2: `ungated` retired | 4 | 4 | Complete | `wp:295` (`check`), U1 and U2 caught |
| FR-3: one listing matcher | 5 | 5 | Complete | `judge:307`, `judge:339`, `cx:298`, `ag:195`, `sh:199`, `sh:343` |
| FR-4: judge by the Task's tests only | 6 | 6 | Complete | `judge:381`, `judge:492` |
| FR-5: Claude gate | 8 | 8 | Complete | `sh:328`, `sh:340-347`, `sh:196-216` |
| FR-6: codex gate | 5 | 5 | Complete | `cx:285-307`, `cx:363`, `cx:372` |
| FR-7: agy gate | 4 | 4 | Complete | `ag:174`, `ag:183-208` |
| FR-8: undecidable listing fails closed | 4 | 4 | Complete | `judge:320`, `judge:344-346`, `cx:294`, `cx:299`, `ag:189`, `ag:196`, `sh:206` |
| FR-9: end-to-end proof | 5 | 4 | Partial | Missing AC-9.3 |
| FR-10: prose | 3 | 3 | Complete | `phase5-substeps.md:213`, `:230`, `:235`; `codex-implementer-prompt.md:19-24`; `codex-runtime.md:29` |
| FR-11: doc/data allowed | 6 | 6 | Complete | `id:19`, `id:33-38`, `sh:266-269`, `sh:328`, `cx:363`, `ag:174` |

## Acceptance Criteria

| AC | Verdict | Code | Test (what it asserts) | What this analysis executed |
|---|---|---|---|---|
| AC-1.1 | MET | `wp:245-247` | PT::test_mixed_production_line_collects_all_three (list equality on the AC's three strings) | Unit on the literal line: the three strings, `.py` first, then line order |
| AC-1.2 | MET | `wp:245-247` | PP::test_paths_label_spelling, ::test_none_value_contributes_nothing, ::test_none_rule_keeps_a_real_path, ::test_label_lines_accumulate, ::test_existing_fields_unchanged, ::test_corpus_old_fields_unperturbed; PT::test_python_only_production_line_keeps_items_and_order | PP not in the range's diff; 23 passed. Unit: `['b.py','a.py','c.py']` |
| AC-1.3 | MET | `wp:243` | PT::test_none_value_production_stays_empty | Unit: `[]`; driver: none-valued line leaves `scripts/tool.sh` ALLOW on 3 hosts |
| AC-1.4 | MET | `wp:244-247` | PT::test_non_py_test_token_stays_out_of_tests_and_production (asserts both lists) | Unit: `tests == []` |
| AC-1.5 | MET | `wp:247` touches `production` only | PT::test_other_task_fields_match_with_and_without_a_non_py_token (real values, budget 37) | Unit: every other key equal, same key set |
| AC-2.1 | MET | `wp` `main`, print loop deleted | WP::test_cli_prints_no_ungated_line | CLI: first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0`, no `ungated:` line |
| AC-2.2 | MET | `wp:295` | WP::test_check_and_tasks_carry_no_ungated_key | Unit: key absent from `check()` and the task dict |
| AC-2.3 | MET | `wp:295` | WP::test_an_unshaped_plan_with_a_non_python_token_stays_unshaped | Unit: `verdict: UNSHAPED`, other keys retained |
| AC-2.4 | MET | `wire_pin_ungated.json` | U1 → WP::test_a_shell_production_file_is_collected_in_production; U2 → WP::test_an_extensionless_production_path_is_collected_in_production | Harness: `ALL_CAUGHT mutations=2 survived=0`. U3 to U5 retired |
| AC-3.1 | MET | `judge:339`; `cx:298`; `ag:195`; `sh:199`, `sh:343` | CX-CALLEE, AG-CALLEE, CL-CALLEE; CX/AG/CL-REMOVE and -FORCE naming each host's own node | Harness: `listing_connections` `ALL_CAUGHT mutations=6 refused=0`. Driver with the callee mutated: tool.sh ALLOW on 3 hosts. Connection mutants flip one host only (see below) |
| AC-3.2 | MET | `id` canonicalise; `sh:343`; `cx:298`; `ag:195` | CL/CX/AG::test_*_symlink_alias_denies | Driver: `test-missing` on 3 hosts |
| AC-3.3 | MET | same | CL/CX/AG::test_*_case_fold_spelling_denies | Driver on APFS: `test-missing` on 3 hosts |
| AC-3.4 | MET | `judge:339-343`, `judge:381` | CL/CX/AG::test_*_hard_link_denies | Driver: `test-missing` on 3 hosts; `test-missing` proves the impl-plan branch, since a non-`.py` name map gives `no-test-resolved` (AC-4.6) |
| AC-3.5 | MET | realpath compare inside `_match_plans` | CL/CX/AG::test_*_residual_spellings_allow; JL::test_listing_residual_spellings_are_not_listed | Driver: all three spellings ALLOW on 3 hosts, including plan `new.sh` written as `New.SH` |
| AC-4.1 | MET | `judge:381` | JL::test_judge_listed_non_py_failing_test_is_red_measured (whole Verdict equality) | Unit: `ALLOW red-measured`, source `impl-plan`, `tests/test_tool.py` |
| AC-4.2 | MET | same | JL::test_judge_listed_non_py_passing_test_is_test_passing | Unit: `DENY test-passing` |
| AC-4.3 | MET | `judge:381-382` | JL::test_judge_listed_non_py_absent_test_is_test_missing | Unit: `DENY test-missing`, reason names `tests/test_tool.py` |
| AC-4.4 | MET | `judge:381-382` | JL::test_judge_listed_non_py_with_no_pytest_file_is_test_missing (literal `tests/tool.bats`) | Unit: `DENY test-missing`, resolution `('impl-plan', ())`; driver: `test-missing` on 3 hosts |
| AC-4.5 | MET | `judge:492` | JL::test_target_module_names_is_empty_for_a_non_py_target; JL::test_non_py_module_not_found_scores_pytest_error (asserts `1 error`, the exact E line, score and verdict) | Unit, collection form: guard on `DENY pytest-error`; guard replaced by the old body `ALLOW red-measured`. Harness: K-IMPORT-NONPY caught. `.py` control `ALLOW red-measured` |
| AC-4.6 | MET | name-map branch of `resolve` | JL::test_judge_unlisted_non_py_is_no_test_resolved | Unit: `DENY no-test-resolved` |
| AC-5.1 | MET | `sh:340-349`, `sh:402-407` | CL::test_claude_listed_absent_test_denies | Driver: `test-missing`, arrangement line correct; E row 001 |
| AC-5.2 | MET | same | CL::test_claude_listed_passing_test_denies; CL::test_claude_listed_failing_test_allows | Driver: `test-passing`, ALLOW |
| AC-5.3 | MET | same | CL::test_claude_listed_extensionless_absent_test_denies | Driver: `test-missing` |
| AC-5.4 | MET | `sh:203`, `sh:328` | CL::test_claude_unlisted_code_like_allows; CL::test_claude_unlisted_doc_data_allows | Driver: ALLOW, ALLOW |
| AC-5.5 | MET | `sh:358-369` | CL::test_claude_default_authorship_refuses_a_listed_target; CL::test_claude_default_authorship_allows_unlisted_doc_data | Driver with a codex stub on PATH: `codex-authorship`; ALLOW |
| AC-5.6 | MET | `sh:301`, `sh:203` | CL::test_claude_no_state_file_allows_a_listed_target; CL::test_claude_inactive_record_allows_a_listed_target | Driver: ALLOW in both arms |
| AC-5.7 | MET | `sh:313` | CL::test_claude_listed_exempt_location_allows | Driver: `tests/helper.sh` ALLOW; `fixtures/` and `docs/` too, on all hosts |
| AC-5.8 | MET | `judge:343`, `sh:344` | CL::test_claude_selection_s1_allows; CL::test_claude_selection_s2_denies (also asserts `hard.sh` and `test_hard.py` in the reason) | Driver: S1 ALLOW, S2 `test-missing` |
| AC-6.1 | MET | `cx:298-306`, `cx:372` | CX::test_codex_listed_absent_test_denies | Driver: `test-missing`; E row 012 |
| AC-6.2 | MET | same | CX::test_codex_listed_passing_test_denies; CX::test_codex_listed_failing_test_allows | Driver: `test-passing`, ALLOW |
| AC-6.3 | MET | `cx:301`, `cx:363` | CX::test_codex_unlisted_code_like_allows; CX::test_codex_add_file_doc_data_allows | Driver including the literal `*** Add File: notes.md`: ALLOW, ALLOW |
| AC-6.4 | MET | `cx:372` inside the `M:G5` loop | CX::test_codex_multi_target_patch_denies_on_the_listed_target | Driver: DENY `test-missing` |
| AC-6.5 | MET | `judge:343`, `cx:303` | CX::test_codex_selection_s1_allows; CX::test_codex_selection_s2_denies | Driver: S1 ALLOW, S2 `test-missing` |
| AC-7.1 | MET | `ag:195-206` | AG::test_agy_listed_absent_test_denies | Driver: deny; reason ends `kind=test-missing` per `ag:206`; E row 023 |
| AC-7.2 | MET | same | AG::test_agy_listed_passing_test_denies; AG::test_agy_listed_failing_test_allows | Driver: `test-passing`, `{"decision": "allow"}` |
| AC-7.3 | MET | `ag:174`, `ag:200` | AG::test_agy_unlisted_code_like_allows; AG::test_agy_unlisted_doc_data_allows | Driver: allow, allow |
| AC-7.4 | MET | `judge:343`, `ag:202` | AG::test_agy_selection_s1_allows; AG::test_agy_selection_s2_denies | Driver: S1 allow, S2 deny `test-missing` |
| AC-8.1 | MET | `judge:320`, `judge:345`, `cx:299`, `ag:196`, `sh:206` | CL/CX/AG::test_*_unreadable_plan_is_judge_error | Driver: `judge-error` on 3 hosts; also mode 000, a directory, and a symlink loop in place of the plan |
| AC-8.2 | MET | `judge:735`, `cx:294`, `ag:189`, `sh:206` | CL/CX/AG::test_*_unreadable_state_is_judge_error, parametrised on `scripts/other.sh` | Driver with `{not json`: `judge-error` on 3 hosts |
| AC-8.3 | MET | `judge:317` | CL/CX/AG::test_*_absent_plan_allows; JL::test_listing_absent_plan_is_not_listed | Driver: ALLOW on 3 hosts |
| AC-8.4 | MET | `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_doc_data_allows_in_undecidable_states | Driver: 12 readings, all ALLOW |
| AC-9.1 | MET | drive:139-141, drive:217-219, drive:257 | FR9T::test_fr9_driver_refuses[authorship-line] for the check | E rows 001-003, 012-014, 023-025 read as required; the Claude rows' `implementer.txt` holds the required line |
| AC-9.2 | MET | drive:82-95 | FR9T::test_fr9_driver_refuses[dirty-hooks, hook-outside-tree, hook-blob-mismatch] | Provenance sha256 prefixes `73b0dbc5bd41`, `f13b0042ec69`, `183baa59b299` equal `git show 57e4f9fc:<hook> \| shasum -a 256`. Evidence commit is e524b58a; `git diff --name-only e524b58a 57e4f9fc -- h-mad/hooks h-mad/scripts` printed nothing |
| AC-9.3 | **UNMET** (`both`) | `judge:320`, `judge:739`, `judge:741` | Tests kill them, but no mutation-spec row exists | See Gap 1 and Must-fix. The other 54 of the 55 new markers match a row by marker text, and `M:G-DOCDATA-CASE` is covered by DD-CASE and DD-SUFFIX on the same line. The harness scores on the pytest summary (`h_mad_mutation_harness.py:492-505`) |
| AC-9.4 | MET | drive:142-150, drive:203-214 | none (evidence is the proof) | E rows 004-011, 015-022, 026-033: all 12 before rows ALLOW; each host's after row DENY `test-missing` on the listed-absent row and ALLOW on the others; PASS on 33 of 33 |
| AC-9.5 | MET | drive:72-79, drive:98-111 | FR9T::test_fr9_driver_refuses[missing-base, base-is-head, plan-absent-at-base, plan-blob-mismatch] | Provenance base `e097dfcb`; `git merge-base 57e4f9fc origin/main` prints the same; `git rev-parse e097dfcb:<plan>` prints `fef082989979…`, equal to `plan_blob` and `copy_blob`; before-side hook shas recorded per host |
| AC-10.1 | MET | prose | DOC::test_gate_prose_has_no_retired_phrasing (8 branches) | Ran the five-branch `git grep` at 57e4f9fc: no line, rc=1 |
| AC-10.2 | MET | `codex-implementer-prompt.md:19-24` | DOC::test_hook_bullets_state_the_shipped_rule | Module passes. Node on the e4979ecd prose: fails `Hook bullets must state '.md'` |
| AC-10.3 | MET | `phase5-substeps.md:230`, `:235` | DOC::test_skill_states_the_docs_first_component_rule | Passes. Node on the e4979ecd prose: fails `assert 0 == 1` on the anchor count |
| AC-11.1 | MET | `id:38`, `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_listed_doc_data_allows | Driver: ALLOW on 3 hosts; the control reads DENY `test-missing` |
| AC-11.2 | MET | `id:33-34` | CL/CX/AG::test_*_listed_upper_case_doc_data_allows | Driver: `CHANGES.MD` and `changes.md` ALLOW on 3 hosts |
| AC-11.3 | MET | `id:19`, `id:33-34` | CL/CX/AG::test_*_doc_data_member_allows (9 parameters each) | Driver: 54 readings, all ALLOW |
| AC-11.4 | MET | `id:33-38`, gates | CL/CX/AG::test_*_excluded_member_denies (7 parameters each) | Driver: 21 readings, all `test-missing` |
| AC-11.5 | MET | `id:38` | CL/CX/AG::test_*_mixed_hard_links_deny | Driver: `test-missing` on 3 hosts |
| AC-11.6 | MET | `id:19`, `sh:266` (no bash copy) | DD-CX-*, DD-AG-*, DD-CL-* naming each host's `[<suffix>]` parameter | Driver with `.md` removed: `x.md` DENY `test-missing` on 3 hosts. The 34-row spec's score is the orchestrator's measurement |

## Gaps

### Gap 1: AC-9.3, three new decision arms have no mutation-spec entry
- **Missing**: AC-9.3 requires a mutation-spec entry for every new guard in FR-1, FR-3 to FR-8 and FR-11. These three arms have none: `judge:320` (FR-8's source: an unreadable plan is recorded as `unreadable`, not `absent`), `judge:741` (Claude's only route from an unreadable plan to `TDD-LISTING: unreadable`) and `judge:739` (Claude's only route to `TDD-LISTING: listed`). A grep over every file in `h-mad/tests/mutation-specs/` for those lines finds only `listing_matcher.json:54`, which is L-ABSENT's `replace` text and not an anchor.
- **Classification**: `both`. The design's mutation list (design:599) names `# M:L-SELECT`, `# M:L-UNREADABLE`, listed-outranks-unreadable and any-name. The impl-plan's "Added guard rows" (departure 7, line 27) adds `LV-NONE`, `LV-CHAIN-UNREADABLE` and `LV-RC`, so of the six rows in its own CLI value table (plan:340-345) it marks three and leaves out the `active, unreadable` and `active, listed` rows. Neither document argues for omitting them, and neither the code nor the specs carry them.
- **Why v1 read this as met**: its census matched `# M:` markers against `find` text, so an unmarked arm could not appear in it. The code has not moved since v1: `git diff 7584ace9 57e4f9fc` touches three production files, and the judge is not one of them. This is a measurement difference, not a regression.
- **Where it should be**: `h-mad/tests/mutation-specs/listing_matcher.json`.
- **Fix**: amend the design's and the plan's row lists, then add three rows. No new test is needed, because the killers below were measured on an archive:
  - `elif result.value == "unreadable":` → `elif False:`, killed by JL::test_listing_cli_active_unreadable_prints_unreadable (`1 failed, 22 passed`).
  - `if result.value == "listed":` → `if False:`, killed by JL::test_listing_cli_listed_prints_the_encoded_target (`1 failed, 22 passed`).
  - `result.append(PlanMatch(plan, "unreadable", type(exc).__name__, ()))` → `result.append(PlanMatch(plan, "absent", "", ()))`, killed by JL::test_listing_unreadable_when_no_plan_lists_the_target and JL::test_listing_cli_active_unreadable_prints_unreadable (`2 failed, 21 passed`).
- **Refutation path**: if the operator rules that AC-9.3's "guard" means a marked guard, the rate is 100 and this gap closes. I do not read it that way, because each arm decides a fail-open against a fail-closed verdict.

## Mutants driven through the real hooks
Each row applies one edit to a scratch copy of 57e4f9fc and drives my driver, test absent.

| Mutant | Target | Claude | codex | agy |
|---|---|---|---|---|
| callee `listing` always not-listed | `scripts/tool.sh` | ALLOW | ALLOW | ALLOW |
| `.md` dropped from `DOC_DATA_SUFFIXES` | listed `x.md` | DENY test-missing | DENY test-missing | DENY test-missing |
| CL-REMOVE | `scripts/tool.sh` | ALLOW | DENY test-missing | DENY test-missing |
| CL-FORCE | `scripts/other.sh` | DENY no-test-resolved | ALLOW | ALLOW |
| CX-REMOVE | `scripts/tool.sh` | DENY test-missing | ALLOW | DENY test-missing |
| AG-FORCE | `scripts/other.sh` | ALLOW | ALLOW | DENY no-test-resolved |
| `judge:741` arm off (Gap 1) | `scripts/other.sh`, AC-8.1 state | **ALLOW** | DENY judge-error | DENY judge-error |
| `judge:739` arm off (Gap 1) | `scripts/tool.sh` | **ALLOW** | DENY test-missing | DENY test-missing |
| `judge:320` recorded as absent (Gap 1) | `scripts/other.sh`, AC-8.1 state | **ALLOW** | **ALLOW** | **ALLOW** |

## Later production changes (7584ace9 to 57e4f9fc)
`git log 7584ace9..57e4f9fc` moves three production files: `id` (`M:G-PY-NAME`), `cx` (`_tmp_report_target`) and `ag` (`M:AG-TMP-PY-NAME`). No AC reading moved: the 55-row table above was taken at head, and none of the three changes reaches a non-`.py` AC fixture.

The three-tree comparison, with the test absent, moved these rows and only these. "DENY outside" means codex's fail-closed reason with no `kind=`, or agy's `target-outside-root`.

| Target | Host | base and v1 | head |
|---|---|---|---|
| in root `.py`, `.PY`, `scripts/.py`, absent `scripts/.Py` | codex, agy | ALLOW | DENY no-test-resolved |
| `/tmp/.py` | codex, agy | ALLOW | DENY outside |
| `/tmp/hl.txt` hard-linked in the same directory to `x.py` | codex | ALLOW | DENY outside |
| `/tmp/hl2.md` hard-linked in the same directory to `.py` | codex, agy | ALLOW | DENY outside |
| `/tmp/sub/a.txt` hard-linked in the same directory to `.Py` | codex, agy | ALLOW | DENY outside |

Claude read DENY `no-test-resolved` on all of these in all three trees, so head makes the hosts agree on the verdict; they differ only on the kind, as they do for `x.py`.

These rows did not move in any tree on any host: in root `x.py`, `sub/X.PY`, absent `new.py`, `tests/.py`, `docs/.py`, `docs/x.py`, `tests/x.py`, `test_x.py`, `conftest.py`, `scripts/test_x.PY`; under `/tmp` `note.txt`, `run.sh`, `launcher`, `README.md`, `x.py`, `X.PY`, a symlink to `x.py`, a dangling symlink, absent `newabsent.txt`, absent `newabsent.py`; outside `/tmp`, absent `.sh`, `.py` and `.md`.

Every move is ALLOW to DENY, so there is no new allow. The moves follow the spec's Terms, which define `.py`-ness by the name's end. They also make three spec sentences false, which is Should-fix 1.

archreview.v6's READY_TO_MERGE was not used. I ran its subject myself: `test_h_mad_codex_gate_tmp_reports.py` and the codex and agy modules pass (429 passed with the others listed above), and the Must-fix here lies outside that review's commit range.

## Adversarial readings at head (not named by any AC)
All gave the expected verdict on all three hosts unless noted, test absent.
- Nested state and plan in a subproject: `sub/scripts/s.sh` DENY `test-missing`.
- Listed hostile names: `한글.sh`, `a%20b.sh`, `rc=1.sh`, `-n.sh`, `a'b.sh`, `a"b.sh`, `a\tb.sh`, `[x].sh`, `*.sh`: DENY `test-missing`. `kind=x.sh` also denies, see Nit 1.
- Listed target absent on disk, including in an absent directory: DENY `test-missing`.
- Symlink crossings: `tests/l.sh` → `scripts/tool.sh` DENY; `scripts/lh.sh` → `tests/helper.sh` ALLOW; `doc.md` → listed `.sh` DENY; `exe.sh` → `README.md` ALLOW.
- Mixed hard links: unlisted `.sh` plus production `.py` DENY `no-test-resolved`; listed `.md` plus unlisted `.sh` DENY `test-missing`; listed `.sh` plus `test_*.py` splits, see Should-fix 2.
- Dangling symlink as the plan reads as absent: ALLOW, matching FR-8's "absent".
- codex paths: `*** Move to:` onto a listed target, `*** Delete File:`, subdirectory payload cwd, `..` spelling and an absolute path: all DENY `test-missing`.
- Claude `Edit` payload and agy `replace_file_content`: DENY `test-missing`. A directory target reads the same in base and head on each host.

## Status of v1's Should-fix and Nit items at 57e4f9fc

| v1 item | Status | Evidence |
|---|---|---|
| SF `# M:H-LIST-CONTEXT` unnamed in the documents | closed | design:313, design:333, design:342; plan:31 (departure 11); plan:995 ledger says 15 rows; `claude_gate_listing.json` holds 15 |
| SF spec FR-5 wording against the shipped order | closed | spec:134-139 (v1.14) names the merged verb, the `TDD-LISTING:` values and the later reads |
| SF design says eight refusals | closed for the design, moved for the ruling | design:523 says nine; design:517 and design:531 name `plan-absent-at-base`. The ruling's primary record is still not found, see Should-fix 4 |
| SF AC-8.2's target has no test | closed | CL:158-159, CX:147-148, AG:146-147 parametrise on `scripts/other.sh`. v1's narrowing mutant now reads `1 failed, 70 passed`: `test_codex_unreadable_state_is_judge_error[scripts/other.sh]` |
| SF AC-6.3 Add File not driven | closed | `non_py_gate_support.py:184-185`; CX:205 and CX:210 |
| SF `# M:W7` has no row | closed | `W7R` and `W7F` at `claude_gate_listing.json:114`, `:123` |
| Nit AC-4.4 and AC-1.1 test spellings | closed | JL:312 uses `tests/tool.bats`; PT:76 uses `hmad-dispatch.sh` |
| Nit `.py` split readings | closed on the verdict | Three-tree table above. The three `Path.suffix` sites it named remain, see Nit 3 |
| Nit M5 reach figures not re-derived | open | Not re-derived here either. No AC names them |

## Test Results
```
.venv/bin/python -m pytest -q   (at 57e4f9fc, measured by the orchestrator; not re-run)
8636 passed, 3 warnings in 3091.69s
```
Scoped runs by this analysis on scratch archives of 57e4f9fc: docs, listing, parse, doc_data and wire_pin modules plus PP, 249 passed with one failure attributed to my partial archive, and PP `23 passed` once the docs were tracked; the seven gate and driver modules, `429 passed in 176.67s`.

Orchestrator's mutation figures, each `ALL_CAUGHT survived=0 refused=0`, not re-run except the three marked: `wire_pin_ungated` 2 (re-run), `parse_tasks_non_py` 3, `doc_data_definition` 34, `listing_matcher` 14, `listing_connections` 6 (re-run), `judge_non_py` 1 (re-run), `claude_gate_listing` 15, `codex_gate_listing` 10, `agy_gate_listing` 8, `fr9_drive_refusals` 9, `shared_gate_policy` 5, `codex_gate_tmp_reports` 9, `agy_tdd_gate` 23. `--check-anchors`: `ANCHORS_OK specs=214 mutations=3021`. FR-9 evidence: 33 of 33 PASS.

## Verdict
Match rate: 91% (threshold: 90%). Tests: 8636/8636 passing, per the orchestrator's measurement.
→ The formula alone would advance. This pass is GATING, so iterate first: 1 gap to close, or refute it by the path in Gap 1. It takes three spec rows and two document lines, and needs no code or test change. Re-measure afterwards, because this report's rate then no longer holds.

## Must-fix
- AC-9.3 is unmet: three new decision arms in the judge have no mutation-spec row. Failure scenario: a change makes `_match_plans` record an unreadable plan as `absent`, or removes the `listing` verb's unreadable arm. With `R/docs/01-plan/features/f.impl-plan.md` holding invalid UTF-8, a write to `scripts/other.sh` then reads ALLOW on all three hosts for the first change and on Claude for the second (both driven above), where AC-8.1 requires DENY `judge-error`. The harness cannot report either, because it has no row to run. The module's tests still catch both today (Gap 1), so the protection exists and the AC's required record does not.
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:221 › `Every new guard in FR-1, FR-3 to FR-8 and FR-11 has a mutation-spec entry.`
  quote: h-mad/scripts/h_mad_tdd_judge.py:320 › `result.append(PlanMatch(plan, "unreadable", type(exc).__name__, ()))`
  quote: h-mad/scripts/h_mad_tdd_judge.py:739 › `if result.value == "listed":`
  quote: h-mad/scripts/h_mad_tdd_judge.py:741 › `elif result.value == "unreadable":`

## Should-fix
- Three spec sentences are false at this commit, and the design alone records why. Commits 6d7df544, 716dbdaa and 55daf487 turned ALLOW into refusals for `.py`-named names and for out-of-root hard links to them (table above). FR-7 still says the T1–T5 checks are unchanged, but `ag:161` changed. The Security NFR still says FR-8 states every ALLOW-to-DENY case, but it does not state these. §(d) still says the out-of-root rules are unaffected. No AC depends on the sentences and the code should stay, because it follows the Terms. The spec should change, and that is the document owner's call; the design carries the argument (design:391-426).
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:172 › `The existing T1–T5 checks run first and are unchanged`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:293 › `FR-8 states every case that turns an existing ALLOW into a DENY.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:326 › `The out-of-root rules are unaffected`
- A listed `scripts/tool.sh` with a same-directory hard link `scripts/test_t.py` splits the hosts, and no document names the residual. With the test absent, Claude reads DENY `no-test-resolved` while codex and agy read ALLOW, so the listed file is written with no RED. The split is the same in all three trees, so this feature did not introduce it, but this feature made the listed file judgeable and its Out-of-Scope list covers only the production-`.py` mixed case. By the Terms such a target is not non-`.py`, so no AC breaks. Name it as a residual, or decide which verdict the hosts should share. Reaching it needs a hard link, which Phase-5 shell policy usually refuses.
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md:340 › `A target with both a production-`.py` name and a listed code-like name.`
  quote: h-mad/hooks/h-mad-codex-tdd-gate.py:287 › `if any(Path(fold_py_suffix(n)).suffix == ".py" for n in resolved.names):  # M:CX-NOT-CODE-LIKE`
- `test_claude_missing_docdata_line_is_judge_error` passes through a guard other than the one its name states. With `emit_doc_data` printing nothing, the hook takes the record's last canon line as the docdata line and truncates the record, and the refusal it reads is `CANON field count mismatch` from `_read_canon`, before `# M:H-DOCDATA-LINE`. The test asserts no reason, unlike its sibling test. The outcome is fail-closed, so nothing is exposed. Assert the actual reason so the test states what protects this case.
  quote: h-mad/tests/test_h_mad_tdd_gate_non_py.py:245 › `_listing_stub(root, tmp_path, "TDD-LISTING: not-listed\n", docdata=" pass")`
- `unverified`: the operator ruling behind the ninth driver refusal has no primary record I could find. The spec's Assumptions list R-A to R-D, a grep of the spec for `plan-absent` and `absent at the base` prints nothing, and the ruling is visible only through the impl-plan. Carried over from v1. FR-9's AC-9.5 does not depend on it.
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:29 › `This plan follows the operator ruling of 2026-11-04 instead`

## Nit
- codex's refusal puts the target path before `kind=`, so a listed `scripts/kind=x.sh` carries two `kind=` tokens and the first is the filename's. agy rewrites `kind=` to `kind:` in its detail (`ag:205`), and Claude's real token comes first. The `.py` branch has the same form (`cx:385`). fr9_drive's `_verdict` would score this row `ERROR`, not a verdict.
- `sh:2` still says "gate for production Python writes", and `DOC::test_hook_line_names_both_gates` keeps its old name while the prose now says three gates.
- `# M:CX-NOT-CODE-LIKE`, `# M:AG-NOT-CODE-LIKE` and `# M:K-IMPORT-NONPY` keep `Path.suffix` beside the `.endswith` form used at `id:358`, `cx:216` and `ag:161`. The design argues they are equivalent (design:405 onward). My readings agree, since `tests/.py` and `docs/.py` read ALLOW on all hosts and no non-exempt `.py` name reached them, but a reader now has to hold two spellings of one rule.
- Spec FR-11's M5 reach figures (128 tokens, 80 and 48) remain un-re-derived. No AC names them.

## Version History
- v1.0: Initial gap analysis draft, Phase 6a, first measurement at 7584ace9 (100 at FR level, AC-9.3 read as met by a marker census).
- v2.0: Second gap analysis at 57e4f9fc against spec v1.14 (91 at FR level, 54 of 55 ACs). AC-9.3 moves to UNMET on unmarked judge arms with no mutation row; all of v1's six Should-fix items closed, one with its ruling record still unverified; two of three Nits closed. The later `.py`-name and `/tmp` changes moved no AC reading.
