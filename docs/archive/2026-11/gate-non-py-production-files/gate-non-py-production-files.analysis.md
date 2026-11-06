# Analysis: gate-non-py-production-files

Change review — 8a3fa99e..bbcd731b — GATING. Phase 6 gap analysis, fifth measurement, SCOPED, at bbcd731b against spec v1.15, design v1.12 and impl-plan v1.11. Files opened: 20 (see Evidence). No new census was derived, by the operator's choice.

## Executive Summary
Every item v4 filed as Must-fix is closed: AC-9.3 clause 1 holds against v4's census at 8a3fa99e, all three rows read and score as claimed, and a first-plan-only mutant now fails the `[absent]` node on all three hosts while each `[failing]` node stays green. The one thing not clean is the full suite: this commit has two readings, one red and one green, and the cause of the red one is unestablished.

## Match Rate: 100%

AC-9.3's reading rests on v4's census and not a fresh one.

FR level: 11 of 11 FRs have every AC met (11/11 x 100 = 100). AC level: 55 of 55 met. AC-9.3 clause 1 holds against v4's census at 8a3fa99e. Three censuses found 3, 16 and 2 lines by successively stronger methods, so this is not a claim that no further unanchored line exists. Of the 55 readings, 54 are carried from v4 and 1 (AC-9.3) is re-read here. The rate is therefore a statement about the lines v4 counted, not about every line a further census might count.

## Evidence
- read: 20 files opened. In spans: `analysis.v4.md`, `inline-protocols.md` (408-445), the impl-plan and design (word-level and raw range diffs, plus the lines quoted), `h_mad_tdd_judge.py`, `h_mad_mutation_harness.py`, `hmad-dispatch.sh`, `h_mad_reproduce_flake.py`, `non_py_gate_support.py`, the 3 `_non_py` host test modules, `test_h_mad_tdd_judge_listing.py`, `test_hmad_dispatch_exec_stamp.py`, `listing_matcher.json`, `final_suite_1failed.txt`. Single lines only: `h-mad-codex-tdd-gate.py`, `h-mad-agy-tdd-gate.py`, `h-mad-tdd-gate.sh`, `test_h_mad_tdd_gate_docs.py`. Grep only, not opened: the spec. Loaded by script only for names, counts and `command`: the other 12 of the feature's 13 mutation specs.
- ran: 25 Bash calls before this report, many holding several commands, all on scratch archives except reads and git queries. Scratch: a `git archive bbcd731b` extract committed once in a throwaway repository, under the scratchpad, each dependent `cd` confirmed by `pwd -P` before use, deleted before finishing. Interpreter: `.venv/bin/python`, absolute.
- tests run: `listing_matcher.json --only` each of the 3 new rows through the harness with `--python <absolute> --isolate`; 7 hand mutants plus one unmutated run over the 3 `_non_py` modules and `test_h_mad_tdd_judge_listing.py`, and an eighth mutant, `judge:757`, over the 2 Claude later-plan nodes only; `h_mad_reproduce_flake.py` on `test_heartbeat_stamps_across_three_intervals`; a scratch stall probe on the same test's helper. Full-suite runs, harness specs other than the 3 rows, `--check-anchors` and the FR-9 evidence were not re-run; those figures are the orchestrator's, quoted under Test Results.
- Scope, confirmed as asked: `git diff --name-only e524b58a bbcd731b -- h-mad/hooks h-mad/scripts` printed nothing. `git diff --name-only e097dfcb bbcd731b -- h-mad/tests/test_hmad_dispatch_exec_stamp.py h-mad/scripts/hmad-dispatch.sh h-mad/bin` printed nothing. `git diff --name-only e524b58a bbcd731b -- docs/03-analysis/probes/gate-non-py-production-files/fr9_drive.py` printed nothing, and `git merge-base bbcd731b origin/main` prints `e097dfcb7b74...`, so FR-9's commit and base stand.
- `docs/03-analysis/gate-non-py-production-files.analysis.md` and `.analysis.v4.md` are byte-identical at bbcd731b (`diff -q` printed nothing).
- The repository was not modified: `git status --short` counted 0 lines and HEAD stayed bbcd731b after the runs.
- One error of mine, so it is not read as a finding. My first flake-scope `git diff` used a wrong test path (`tests/...`, not `h-mad/tests/...`), which would have printed nothing for any tree. The reading above is from the corrected path.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: parser records every backticked production path | 5 | 5 | Complete | carried from v4 |
| FR-2: `ungated` retired | 4 | 4 | Complete | carried from v4 |
| FR-3: one listing matcher | 5 | 5 | Complete | carried from v4 |
| FR-4: judge by the Task's tests only | 6 | 6 | Complete | carried from v4 |
| FR-5: Claude gate | 8 | 8 | Complete | carried from v4 |
| FR-6: codex gate | 5 | 5 | Complete | carried from v4 |
| FR-7: agy gate | 4 | 4 | Complete | carried from v4 |
| FR-8: undecidable listing fails closed | 4 | 4 | Complete | carried from v4 |
| FR-9: end-to-end proof | 5 | 5 | Complete | AC-9.3 re-read here, against v4's census; the other 4 carried |
| FR-10: prose | 3 | 3 | Complete | carried from v4 |
| FR-11: doc/data allowed | 6 | 6 | Complete | carried from v4 |

## Rubric 1: v4's Gap 1 lines

| Line | Row | `find` count, line it lands on | Harness, `--only` that row, `--isolate`, absolute `--python` | Killer's assertion under my own copy of the mutant |
|---|---|---|---|---|
| `judge:344` | `L-UNREADABLE-ANY-PLAN` | 1, line 344 | `MUTATION: ALL_CAUGHT mutations=1 caught=1 survived=0 refused=0 unreadable=0 crash_kills=0 crash_visible=1/1 timeout_kills=0 untargeted=0/1 hollow_kills=0 host_skipped=0` | `test_listing_unreadable_when_no_plan_lists_the_target` asserts `Listing("unreadable", None, bad, "UnicodeDecodeError")` and received `Listing(value='not-listed', selected=None, error_file=None, error='')`. Own reason: the later unreadable plan was not inspected |
| `judge:738` | `LV-RECORDS` | 1, line 738 | `MUTATION: ALL_CAUGHT mutations=1 caught=1 survived=0 refused=0 unreadable=0 crash_kills=0 crash_visible=0/0 timeout_kills=0 untargeted=0/1 hollow_kills=0 host_skipped=0` | `test_claude_listing_only_in_a_later_active_plan_judges_its_test[absent]`: `a target listed only by a later readable active plan is listed: expected DENY kind=test-missing, received Outcome(decision='allow', kind='', reason='', rc=0)`. Own reason: the verb handed the matcher only the first record |

Under `judge:344`'s mutant, 4 of 248 nodes fail: the named test and the three `test_*_unlisted_beside_unreadable_is_judge_error`, each host reading `allow`. Under `judge:738`'s, 2 of 248 fail, both Claude: the named node and `test_claude_unlisted_beside_unreadable_is_judge_error`. Codex and agy stay green, as v4 said they would, since `cx:298` and `ag:195` carry that argument on those hosts.

`LV-RECORDS` names the sharper killer v4 asked for once the later-plan test existed. Its message names the property it mutates. Nothing was killed by a crash: both assertion lines read a clean `allow` or a clean `Listing`. On `LV-RECORDS` the harness's `crash_visible=0/0` is an empty denominator (Should-fix 2), so the evidence is the assertion line and not the harness's `no traceback` annotation.

**AC-9.3 clause 1 holds against v4's census at 8a3fa99e.** v4 classed 2 lines as a guard with no row, and both now have one. Production is unchanged since e524b58a, so v4's line numbers and classes still apply at bbcd731b. v4's 76 rowed guards are carried; I did not re-derive them. Three censuses found 3, 16 and 2 lines by successively stronger methods, so this is not a claim that no further unanchored line exists. In what I read I saw no further unanchored verdict line, and I did not go looking.

## Rubric 2: v4's Gap 2, first-plan-only mutant

Hand mutant, on a fresh scratch copy: `any(m.matches for m in plans)]` to `any(m.matches for m in plans[:1])]` at `judge:341`. Run over the 3 `_non_py` modules and `test_h_mad_tdd_judge_listing.py`. Unmutated: `248 passed in 49.67s`. Mutated: `3 failed, 245 passed in 47.44s`:

```
FAILED tests/test_h_mad_tdd_gate_non_py.py::test_claude_listing_only_in_a_later_active_plan_judges_its_test[absent]
FAILED tests/test_h_mad_codex_tdd_gate_non_py.py::test_codex_listing_only_in_a_later_active_plan_judges_its_test[absent]
FAILED tests/test_h_mad_agy_tdd_gate_non_py.py::test_agy_listing_only_in_a_later_active_plan_judges_its_test[absent]
```

- **Each host's `[absent]` node fails, and each host's `[failing]` node stays green** (none of the three is in the failing set). v4 read 0 failures across these modules on the same mutant, then 242 nodes; the only nodes added since are these 6.
- **The killer fails for the guard's own reason.** `L-ANY-PLAN-FIRST`'s named test reads `expected DENY kind=test-missing, received Outcome(decision='allow', kind='', reason='', rc=0)`. Codex reads the same and agy reads `received {'decision': 'allow'}`. The harness, `--only L-ANY-PLAN-FIRST`, `--isolate`: `MUTATION: ALL_CAUGHT mutations=1 caught=1 survived=0 refused=0 ... crash_visible=0/0 ... hollow_kills=0`, where v4's scratch row read `SURVIVED`.
- **The fixture's second plan is readable**, by a direct probe of `later_plan_fixture` for both `test_state` values, unmocked: `chain active 2`; `plan f.impl-plan.md status read err '' matches 0`; `plan g.impl-plan.md status read err '' matches 1`; `listing listed tool.sh`. Each plan also decodes as UTF-8.
- **The `[failing]` node is not a pin of the listing guard, and it is not vacuous.** A not-listed target also reads ALLOW, so that node stays green under `judge:341`'s mutant, which the plan says plainly. It does bite on a judge call handed the first record only: each mutant below fails that host's `[absent]` and `[failing]` nodes.

| Mutant, `chain.records[:1]` | v4 | At bbcd731b |
|---|---|---|
| `cx:303` | 0 failures in the four modules | 2 failed, 246 passed, `[absent]` reads `no-test-resolved`, `[failing]` reads DENY |
| `ag:202` | 0 failures in the four modules | 2 failed, 246 passed, same two nodes |
| `judge:757` (Claude's judge verb; predates the feature) | not driven | both Claude later-plan nodes fail; only those 2 were run |
| `cx:298` | not driven | 2 failed, `[absent]` and `test_codex_unlisted_beside_unreadable_is_judge_error` |
| `ag:195` | not driven | 2 failed, `[absent]` and `test_agy_unlisted_beside_unreadable_is_judge_error` |

## Rubric 3: every v4 item

| v4 item | Status | Evidence |
|---|---|---|
| Must-fix 1: `judge:344`, `judge:738` have no row | **closed**, against v4's census | Rubric 1 |
| Must-fix 2: later-plan listing held by no test; `L-ANY-PLAN` caught on a line with an unkilled fail-open | **closed** | Rubric 2. `L-ANY-PLAN-FIRST` exists and the mutant fails on all three hosts. One departure from v4's stated fix: Nit 1 below |
| Should-fix 1: plan's `command` sentences false | **closed**, one residual moved to Nit 2 | Below |
| Should-fix 2: `crash_visible=0/0` on host specs | **open**, and it now reaches 2 rows of `listing_matcher` | Harness frozen. `L-ANY-PLAN-FIRST` and `LV-RECORDS` printed `crash_visible=0/0`. I read the assertion lines for both, so the two new rows are not in doubt; the remaining host rows' lines stay unread |
| Should-fix 3, `unverified`: primary record of the ninth-refusal ruling | **open** | The grep for `plan-absent`, `absent at the base`, `ninth`, `nine refusals` on the spec printed nothing; plan:29 still the only statement |
| Nit: codex `kind=` token after a path | **open**, not re-driven | `cx:306` still has `{relative}: kind={verdict.kind}`; hooks frozen |
| Nit: `sh:2` and `test_hook_line_names_both_gates` | **open** | `sh:2` reads `gate for production Python writes`; `test_h_mad_tdd_gate_docs.py:71` keeps the name |
| Nit: two spellings of the `.py` rule | **open** | `cx:287`, `ag:183`, `judge:492` all still use `Path(...).suffix` |
| Nit: M5 reach figures | **open**, not re-derived | spec not in the range's diff |
| Nit: same-directory residual has no test | **open**, by no change | the range's test diff adds no hard link. Not re-grepped exhaustively |
| Nit: `L-READ-RECORD`, `L-MATCH-RECORD` killer's message names another property | **open** | `test_h_mad_tdd_judge_listing.py:112` unchanged |
| Nit: `H-LIST-TARGET`, `H-DOCDATA-NO-ARM` carry `symbol` `_read_listing` | **open** | loaded from `claude_gate_listing.json`, same value |

**The corrected `command` sentences, against the harness and the spec JSONs.** plan:16, and the two row headings at plan:267 and plan:455.

- "`git log` over `listing_matcher.json`, `doc_data_definition.json` and `listing_connections.json` shows one `command` per spec at every commit that touched it": **true**, by script over each commit's JSON: 7 commits and 1 `command`, 4 and 1, 3 and 1.
- "A row whose `test` is a host's test scores through `target_command`, which the harness extends with that `test` (`...:1860`)": **true**. Line 1860 reads `scoring_command = list(target_command) + [mutation["test"]]`, and `:1941-1942` run it.
- "`is tests/test_h_mad_doc_data.py`" (plan:267) and "`is tests/test_h_mad_tdd_judge_listing.py`" (plan:455): **true** at every commit of those specs.
- "`command` itself runs only the baseline, the survivor probe and the post-restore check": **true of every row of this feature, not of the harness.** The untargeted branch, `:2061`, also runs `command` and scores on it. Every row of the 13 specs has a `test` and every spec has a `target_command` (script: `no-test-rows= 0` on all 13), so no row here reaches it. v4's own list of sites also missed `:2061`. Nit 2.
- "so a survivor's 'whole suite' message reports that one file": **true**, `:2005` then `:2011`.

## Rubric 4: design and impl-plan diffs

No false statement found. Checked:

- Design Task 3: 27 rows, 21 judge-level, 6 host; script over the JSON and that sentence: no name in the design outside the JSON and none in the JSON outside the design. "Four of the twenty-one are killed by a Claude host test": the JSON's 10 rows outside the listing module are the 6 host entries plus `LV-NAMES`, `LV-CHAIN-TARGET`, `L-ANY-PLAN-FIRST`, `LV-RECORDS`.
- Design and plan: `L-ANY-PLAN` is an `all` mutant and `L-ANY-PLAN-FIRST` a `[:1]` one, by the JSON. `find` and `replace` text in plan departure 17 equals the JSON's for all three rows, with the line numbers it gives (341, 344, 738).
- Ledger: 10 specs by `len(mutations)` sum to 124, with each figure equal to plan:1345's; the table's last row reads 3 and the total 124; `git diff --numstat 92b6836e 5f72f9aa` prints `27 0` for the spec.
- `git diff --stat 92b6836e 5f72f9aa -- h-mad/hooks h-mad/scripts` printed nothing, and `5f72f9aa` touches exactly the 5 files the plan names. `git diff --stat 5f72f9aa bbcd731b -- h-mad` printed nothing, so a reading at `5f72f9aa` applies to the tree at bbcd731b.
- "Every second-plan fixture before this commit was unreadable", checked over the 5 files the sentence names. At 8a3fa99e the only non-`f` plans are `non_py_gate_support.py:150` and `test_h_mad_tdd_judge_listing.py:141`, `:156`, all invalid UTF-8. The host modules at bbcd731b have no `write_plan(` other than key `f`.
- `248 passed` and `3 failed, 3 passed`: my runs agree, as in Rubric 2.
- "The Claude test passes `author=True`, so it calls `assert_authorship` with key `f`": `_expect` lines 33-34. `test_claude_nested_state_governs_a_subproject_target` does not pass `author=True`.
- The sweep for stale figures: `24 rows`, `mutations=24`, `holds 24` and `121` on both documents. Each hit left is a dated departure or version entry stating the path to 124.
- Departure 17's account of v4 (91, 54 of 55, 3 then 16 then 2, "converging with no floor") matches v4's text.

Two imprecisions, neither false enough to gate: Nit 2 and Nit 3.

## Rubric 5: the two full-suite readings

Both verbatim, and neither settles the other.

```
1 failed, 8644 passed, 3 warnings in 2409.72s (0:40:09)     first run, final_suite_1failed.txt
8645 passed, 3 warnings in 2318.72s                         second run, orchestrator's reading, no file read
```

**The failing node's text:**

```
h-mad/tests/test_hmad_dispatch_exec_stamp.py:433: in test_heartbeat_stamps_across_three_intervals
    assert len(beats) >= 3, f"expected at least three heartbeat writes, got {beats!r}"
E   AssertionError: expected at least three heartbeat writes, got ['orca worktree set --worktree state-wt --comment h-mad: codex x · running · 0s⟦/h-mad⟧ --json', 'orca worktree set --worktree state-wt --comment h-mad: codex x · running · 3s⟦/h-mad⟧ --json']
```

**What I can establish:**
1. The test, `hmad-dispatch.sh` and `h-mad/bin` are unchanged since e097dfcb. `hmad-dispatch.sh` names none of the 6 production files this feature changed (`grep -c` printed 0 for each). The range's own changes are in other test modules. That is no change to the code under test. It does not exclude an interaction between tests in a full run.
2. The test is wall-clock by construction: a stub sleeping 3.3s, a 1s beat, a loop polling every 0.25s on bash's integer `SECONDS`, and a floor of 3 stamps, the start stamp included. The failing run recorded one beat after the start stamp, and that beat reads `3s`.
3. Its margin is small. An unmutated control on scratch, 3 of 3 runs, read beats `['0', '2', '3', '4']`: one above the floor.
4. It is one test in a tight cluster. The run's single `F` means `test_heartbeat_elapsed_values_are_monotonic` and `test_heartbeat_without_timeout_keeps_the_same_cadence`, which need 3 stamps from a shorter 3.2s sleep, passed in that same run. They were not reading the same seconds, so this says only that the condition, whatever it was, did not persist across the module.
5. `h_mad_reproduce_flake.py`, on the scratch archive, `--runs 5`, all 6 cells, 24 spinners in the `cpu` cells:

   ```
   FLAKE: fg-idle fails=0/5
   FLAKE: fg-cpu fails=0/5
   FLAKE: fg-fork fails=0/5
   FLAKE: bg-idle fails=0/5
   FLAKE: bg-cpu fails=0/5
   FLAKE: bg-fork fails=0/5
   FLAKE-VERDICT: NOT_REPRODUCED runs=30
   ```

   Load averages were `4.39` at the start and `18.98` at the end. So this does not show load sensitivity. It also does not clear load: it ran the node alone, not at 87 of 100 through a 40-minute suite.
6. Two mechanisms fit the text, and it cannot separate them. Either the dispatcher's loop was starved long enough to miss the ticks, or a beat was dropped silently: `_exec_stamp` returns 0 when `_exec_wt_target` fails (`hmad-dispatch.sh:2539`), and the loop sets `last_beat` regardless (`:2740`), so a dropped beat leaves no trace in this failure's output.
7. My stall probe does not favour the first. `SIGSTOP` on the dispatcher processes for 1.5s and 2.5s, each run 3 times, read beats such as `['0', '3', '4', '5']` and `['0', '4', '5', '6', '7']`, and none fell below the floor. The beats ran on to 6s and 7s, so the stall also lengthened the run. It did not reproduce `['0', '3']`. A probe that shape cannot prove or disprove starvation.
8. Orchestrator's `h_mad_failure_diff.py --repeat 5`, `FAILDIFF: SAME` with 0 failures on both sides: carried, not re-run. I did not check the conditions it ran under.

**The cause is unestablished.** I can say the code under test did not change in this feature's reach and that the test has one stamp of margin on a wall clock. I cannot say that load caused this failure, that it is harmless, or how often it recurs. One red in two full runs is the only rate available.

## Acceptance Criteria

Re-read at bbcd731b: **AC-9.3 only.** No AC's text changed: `git diff --name-only 8a3fa99e bbcd731b` on the spec printed nothing. No AC's test changed: over `h-mad/`, the 3 host modules' numstat is `9 1`, the 1 deletion in each being the `non_py_gate_support` import line gaining a name, and the helper and spec are `9 0` and `27 0`. Every other row is carried from v4, unread here, and v4 carried them from v3 and v2. Production is frozen since e524b58a. The modules naming those tests pass unmodified on my scratch archive, `248 passed`.

Abbreviations are v4's: CL, CX, AG, JL, PT, PP, WP, DD, DOC, FR9T under `h-mad/tests/`; E = the FR-9 evidence directory. `carried` means v4's reading at 8a3fa99e, itself carried from v3 at 246531ba and v2 at 57e4f9fc.

| AC | Verdict | Basis | Code | Test |
|---|---|---|---|---|
| AC-1.1 | MET | carried | `wp:245-247` | PT::test_mixed_production_line_collects_all_three (list equality on the AC's three strings) |
| AC-1.2 | MET | carried | `wp:245-247` | PP::test_paths_label_spelling, ::test_none_value_contributes_nothing, ::test_none_rule_keeps_a_real_path, ::test_label_lines_accumulate, ::test_existing_fields_unchanged, |
| AC-1.3 | MET | carried | `wp:243` | PT::test_none_value_production_stays_empty |
| AC-1.4 | MET | carried | `wp:244-247` | PT::test_non_py_test_token_stays_out_of_tests_and_production (asserts both lists) |
| AC-1.5 | MET | carried | `wp:247` touches `production` only | PT::test_other_task_fields_match_with_and_without_a_non_py_token (real values, budget 37) |
| AC-2.1 | MET | carried | `wp` `main`, print loop deleted | WP::test_cli_prints_no_ungated_line |
| AC-2.2 | MET | carried | `wp:295` | WP::test_check_and_tasks_carry_no_ungated_key |
| AC-2.3 | MET | carried | `wp:295` | WP::test_an_unshaped_plan_with_a_non_python_token_stays_unshaped |
| AC-2.4 | MET | carried | `wire_pin_ungated.json` | U1 → WP::test_a_shell_production_file_is_collected_in_production; U2 → WP::test_an_extensionless_production_path_is_collected_in_production |
| AC-3.1 | MET | carried | `judge:339`; `cx:298`; `ag:195`; `sh:199`, `sh:343` | CX-CALLEE, AG-CALLEE, CL-CALLEE; CX/AG/CL-REMOVE and -FORCE naming each host's own node |
| AC-3.2 | MET | carried | `id` canonicalise; `sh:343`; `cx:298`; `ag:195` | CL/CX/AG::test_*_symlink_alias_denies |
| AC-3.3 | MET | carried | same | CL/CX/AG::test_*_case_fold_spelling_denies |
| AC-3.4 | MET | carried | `judge:339-343`, `judge:381` | CL/CX/AG::test_*_hard_link_denies |
| AC-3.5 | MET | carried | realpath compare inside `_match_plans` | CL/CX/AG::test_*_residual_spellings_allow; JL::test_listing_residual_spellings_are_not_listed |
| AC-4.1 | MET | carried | `judge:381` | JL::test_judge_listed_non_py_failing_test_is_red_measured (whole Verdict equality) |
| AC-4.2 | MET | carried | same | JL::test_judge_listed_non_py_passing_test_is_test_passing |
| AC-4.3 | MET | carried | `judge:381-382` | JL::test_judge_listed_non_py_absent_test_is_test_missing |
| AC-4.4 | MET | carried | `judge:381-382` | JL::test_judge_listed_non_py_with_no_pytest_file_is_test_missing (literal `tests/tool.bats`) |
| AC-4.5 | MET | carried | `judge:492` | JL::test_target_module_names_is_empty_for_a_non_py_target; JL::test_non_py_module_not_found_scores_pytest_error (asserts `1 error`, the exact E line, score and verdict) |
| AC-4.6 | MET | carried | name-map branch of `resolve` | JL::test_judge_unlisted_non_py_is_no_test_resolved |
| AC-5.1 | MET | carried | `sh:340-349`, `sh:402-407` | CL::test_claude_listed_absent_test_denies |
| AC-5.2 | MET | carried | same | CL::test_claude_listed_passing_test_denies; CL::test_claude_listed_failing_test_allows |
| AC-5.3 | MET | carried | same | CL::test_claude_listed_extensionless_absent_test_denies |
| AC-5.4 | MET | carried | `sh:203`, `sh:328` | CL::test_claude_unlisted_code_like_allows; CL::test_claude_unlisted_doc_data_allows |
| AC-5.5 | MET | carried | `sh:358-369` | CL::test_claude_default_authorship_refuses_a_listed_target; CL::test_claude_default_authorship_allows_unlisted_doc_data |
| AC-5.6 | MET | carried | `sh:301`, `sh:203` | CL::test_claude_no_state_file_allows_a_listed_target; CL::test_claude_inactive_record_allows_a_listed_target |
| AC-5.7 | MET | carried | `sh:313` | CL::test_claude_listed_exempt_location_allows |
| AC-5.8 | MET | carried | `judge:343`, `sh:344` | CL::test_claude_selection_s1_allows; CL::test_claude_selection_s2_denies (also asserts `hard.sh` and `test_hard.py` in the reason) |
| AC-6.1 | MET | carried | `cx:298-306`, `cx:372` | CX::test_codex_listed_absent_test_denies |
| AC-6.2 | MET | carried | same | CX::test_codex_listed_passing_test_denies; CX::test_codex_listed_failing_test_allows |
| AC-6.3 | MET | carried | `cx:301`, `cx:363` | CX::test_codex_unlisted_code_like_allows; CX::test_codex_add_file_doc_data_allows |
| AC-6.4 | MET | carried | `cx:372` inside the `M:G5` loop | CX::test_codex_multi_target_patch_denies_on_the_listed_target |
| AC-6.5 | MET | carried | `judge:343`, `cx:303` | CX::test_codex_selection_s1_allows; CX::test_codex_selection_s2_denies |
| AC-7.1 | MET | carried | `ag:195-206` | AG::test_agy_listed_absent_test_denies |
| AC-7.2 | MET | carried | same | AG::test_agy_listed_passing_test_denies; AG::test_agy_listed_failing_test_allows |
| AC-7.3 | MET | carried | `ag:174`, `ag:200` | AG::test_agy_unlisted_code_like_allows; AG::test_agy_unlisted_doc_data_allows |
| AC-7.4 | MET | carried | `judge:343`, `ag:202` | AG::test_agy_selection_s1_allows; AG::test_agy_selection_s2_denies |
| AC-8.1 | MET | carried | `judge:320`, `judge:345`, `cx:299`, `ag:196`, `sh:206` | CL/CX/AG::test_*_unreadable_plan_is_judge_error |
| AC-8.2 | MET | carried | `judge:735`, `cx:294`, `ag:189`, `sh:206` | CL/CX/AG::test_*_unreadable_state_is_judge_error, parametrised on `scripts/other.sh` |
| AC-8.3 | MET | carried | `judge:317` | CL/CX/AG::test_*_absent_plan_allows; JL::test_listing_absent_plan_is_not_listed |
| AC-8.4 | MET | carried | `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_doc_data_allows_in_undecidable_states |
| AC-9.1 | MET | carried | drive:139-141, drive:217-219, drive:257 | FR9T::test_fr9_driver_refuses[authorship-line] for the check |
| AC-9.2 | MET | carried | drive:82-95 | FR9T::test_fr9_driver_refuses[dirty-hooks, hook-outside-tree, hook-blob-mismatch] |
| AC-9.4 | MET | carried | drive:142-150, drive:203-214 | none (evidence is the proof) |
| AC-9.5 | MET | carried | drive:72-79, drive:98-111 | FR9T::test_fr9_driver_refuses[missing-base, base-is-head, plan-absent-at-base, plan-blob-mismatch] |
| AC-10.1 | MET | carried | prose | DOC::test_gate_prose_has_no_retired_phrasing (8 branches) |
| AC-10.2 | MET | carried | `codex-implementer-prompt.md:19-24` | DOC::test_hook_bullets_state_the_shipped_rule |
| AC-10.3 | MET | carried | `phase5-substeps.md:230`, `:235` | DOC::test_skill_states_the_docs_first_component_rule |
| AC-11.1 | MET | carried | `id:38`, `sh:328`, `cx:363`, `ag:174` | CL/CX/AG::test_*_listed_doc_data_allows |
| AC-11.2 | MET | carried | `id:33-34` | CL/CX/AG::test_*_listed_upper_case_doc_data_allows |
| AC-11.3 | MET | carried | `id:19`, `id:33-34` | CL/CX/AG::test_*_doc_data_member_allows (9 parameters each) |
| AC-11.4 | MET | carried | `id:33-38`, gates | CL/CX/AG::test_*_excluded_member_denies (7 parameters each) |
| AC-11.5 | MET | carried | `id:38` | CL/CX/AG::test_*_mixed_hard_links_deny |
| AC-11.6 | MET | carried | `id:19`, `sh:266` (no bash copy) | DD-CX-*, DD-AG-*, DD-CL-* naming each host's `[<suffix>]` parameter |
| AC-9.3 | MET, against v4's census only | **re-read at bbcd731b** | `judge:341`, `judge:344`, `judge:738` frozen; `L-UNREADABLE-ANY-PLAN`, `LV-RECORDS`, `L-ANY-PLAN-FIRST` in `listing_matcher.json` | Clause 1 holds against v4's census at 8a3fa99e, not a claim that no further unanchored line exists. Clause 2 read on the 3 new rows and carried on the others. Clause 3 carried, harness frozen. See Rubric 1 |

## Gaps

None

## Test Results
```
.venv/bin/python -m pytest -q   (at bbcd731b, measured by the orchestrator; not re-run)
first run:   1 failed, 8644 passed, 3 warnings in 2409.72s
             FAILED h-mad/tests/test_hmad_dispatch_exec_stamp.py::test_heartbeat_stamps_across_three_intervals
second run:  8645 passed, 3 warnings in 2318.72s
```
Orchestrator's mutation figures, each `ALL_CAUGHT survived=0 refused=0`, not re-run except as stated: `wire_pin_ungated` 2, `parse_tasks_non_py` 3, `doc_data_definition` 34, `listing_matcher` 27, `listing_connections` 6, `judge_non_py` 1, `claude_gate_listing` 18, `codex_gate_listing` 13, `agy_gate_listing` 11, `fr9_drive_refusals` 9, `shared_gate_policy` 5, `codex_gate_tmp_reports` 9, `agy_tdd_gate` 23. `--check-anchors`: `ANCHORS_OK specs=214 mutations=3043`. FR-9 evidence: 33 of 33 PASS at e524b58a, `docs/03-analysis/probes/gate-non-py-production-files/fr9/20261106T014611Z-e524b58a6e47/`.

Scoped runs by this analysis on a scratch archive of bbcd731b: 3 `_non_py` modules and `test_h_mad_tdd_judge_listing.py`, `248 passed in 49.67s`. The 6 new nodes, `6 passed, 242 deselected in 2.87s`. Harness, `--only` each new row, all `ALL_CAUGHT mutations=1 caught=1 survived=0 refused=0 hollow_kills=0`.

## Verdict
Match rate: 100% (threshold: 90%), against v4's census and not a fresh one. Tests: 8645/8645 passing in the second run and 8644/8645 in the first, per the orchestrator's measurement, both reported.
→ The formula advances, and this gating pass carries 0 Must-fix. What the operator should weigh before Phase 7:

- **AC-9.3 is met on the lines v4 counted.** A further census might find more, and the operator chose not to run one.
- **The suite is not clean on the evidence.** One of two runs at this commit is red, on a test this feature did not touch, and the cause is unestablished. Calling it a flake is a likely description of a timing test with one stamp of margin. It is not a measured one, since the published reproducer read `NOT_REPRODUCED` over 30 runs.
- **No verdict moved in this range.** Hooks and scripts are frozen since e524b58a, and the range adds 6 test nodes and 3 rows.

## Must-fix
None

## Should-fix
- `unverified`: the cause of the first run's failure of `test_heartbeat_stamps_across_three_intervals` is unestablished. It is a Should-fix and not a Must-fix because I could not show it wrong, and no line this feature changed is reached by it, as far as `grep` on `hmad-dispatch.sh` shows. It matters because a merge decision reads the suite, and the suite at this commit has one red reading and one green. See Rubric 5 for what is and is not known. Separating the two mechanisms needs a failing run's `calls` capture or a stamp log, which this failure text does not hold.
  quote: h-mad/tests/test_hmad_dispatch_exec_stamp.py:433 › `assert len(beats) >= 3, f"expected at least three heartbeat writes, got {beats!r}"`
  quote: h-mad/scripts/hmad-dispatch.sh:2539 › `target="$(_exec_wt_target "$cd_dir" 2>/dev/null)" || return 0`
- Carried from v4 and widened: `crash_visible=0/0` is a reading with an empty denominator, and it now sits on `L-ANY-PLAN-FIRST` and `LV-RECORDS` as well as the three host specs. The harness's `assertion: no traceback` annotation proves nothing on those rows. Only reading the assertion line tells a crash from a guard. I did that for these 2 rows and they are guards; the remaining rows of the host specs stay unread by me.
  quote: h-mad/scripts/h_mad_mutation_harness.py:1726 › `is a bare count whose two causes`
- `unverified`: the operator ruling behind the ninth driver refusal still has no primary record I could find. Carried from v1 to v4. AC-9.5 does not depend on it.
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:29 › `This plan follows the operator ruling of 2026-11-04 instead`

## Nit
- New, 1: v4's fix asked for a row "naming the judge-level one", and no judge-level test with two readable plans was added, so `L-ANY-PLAN-FIRST` and `LV-RECORDS` both name the Claude `[absent]` node. The mutant still dies on all three hosts, so nothing is unpinned. `test_h_mad_tdd_judge_listing.py` simply holds no direct `listing()` case with two readable plans.
- New, 2: the plan's `command` sentence uses "only", and the harness's untargeted branch also runs `command` and scores on it at `:2061`. No row of this feature reaches that branch.
  quote: docs/01-plan/features/gate-non-py-production-files.impl-plan.md:16 › `itself runs only the baseline, the survivor probe and the post-restore check`
  quote: h-mad/scripts/h_mad_mutation_harness.py:2061 › `suite_green, suite_output = _run(command, root)`
- New, 3: design D4 says the test "pins that" and lists "a failing test is ALLOW" under it, with no note that a not-listed target also reads ALLOW. So the `[failing]` half does not pin the listing. The plan states this (`since not-listed also reads ALLOW`); the design does not.
  quote: docs/02-design/features/gate-non-py-production-files.design.md:236 › `a failing test is ALLOW`
- New, 4: `later_plan_fixture` sits after `two_record_fixture` in each host module's otherwise sorted import list.
- Carried: codex's refusal puts the target path before `kind=`, so a listed `scripts/kind=x.sh` carries two `kind=` tokens. Not re-driven, since production has not changed.
- Carried: `sh:2` still says "gate for production Python writes", and `test_hook_line_names_both_gates` keeps its old name.
- Carried: `# M:CX-NOT-CODE-LIKE`, `# M:AG-NOT-CODE-LIKE` and `# M:K-IMPORT-NONPY` keep `Path.suffix` beside the `.endswith` form at `id:358`, `cx:216` and `ag:161`.
- Carried: spec FR-11's M5 reach figures remain un-re-derived.
- Carried: the same-directory residual has no test.
- Carried: `L-READ-RECORD` and `L-MATCH-RECORD` die on a test whose message reads "a later listed canonical hard-link name must be considered". The value is right, but the message names another guard's property.
- Carried: `H-LIST-TARGET` (`sh:344`) and `H-DOCDATA-NO-ARM` (`sh:269`) carry `symbol` `_read_listing`, though neither line is inside that function.

## Version History
- v1.0: Initial gap analysis draft, Phase 6a, first measurement at 7584ace9 (100 at FR level, AC-9.3 read as met by a marker census).
- v2.0: Second gap analysis at 57e4f9fc against spec v1.14 (91 at FR level, 54 of 55 ACs). AC-9.3 moves to UNMET on three unmarked judge arms.
- v3.0: Third gap analysis at 246531ba against spec v1.15, design v1.10 and impl-plan v1.9 (91 at FR level, 54 of 55 ACs). A census of 158 changed decision lines finds 16 with no row, 3 of which no test kills.
- v4.0: Fourth gap analysis at 8a3fa99e against spec v1.15, design v1.11 and impl-plan v1.10 (91 at FR level, 54 of 55 ACs). A re-derived census of 174 lines finds 2 more with no row, and a new test gap: no test has a second readable active plan.
- v5.0: Fifth gap analysis, SCOPED, at bbcd731b against spec v1.15, design v1.12 and impl-plan v1.11 (100 at FR level, 55 of 55 ACs), with no new census by the operator's choice. AC-9.3 clause 1 holds against v4's census at 8a3fa99e, and that is not a claim that no further unanchored line exists. v4's two Must-fix closed; 54 AC rows carried from v4 and AC-9.3 re-read. Two full-suite readings at this commit, one red and one green, with the red one's cause unestablished: `FLAKE-VERDICT: NOT_REPRODUCED runs=30`.
