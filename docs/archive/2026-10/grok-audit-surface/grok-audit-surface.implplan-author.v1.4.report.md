IMPLPLAN-AUTHOR: DONE version=v1.4 tasks=18 wiring=1 mutation_rows=180 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.impl-plan.md lines=1856 sha256=100b93d237ef2b8c038b67b210ee1a97bc1cb324e566869548c741b8c9f250cc

## Ownership check before writing
The document's sha256 was 3015ade96e9492866ebbb9ad0d6c175377756a21a1f23cd4e3a49f4025c8c8e8 and its newest Version History entry was `- v1.3`, so nobody else had written it. I bumped the version with `h_mad_version_history.py --version v1.4` (`VERSION-HISTORY: OK … line=1856`). Not committed.

## Gates
- `PRECHECK: PASS issues=0`. Advisories:
  - COUNT L1545 "17 rows" and L1651 "0 files", as before.
  - COUNT L1757 "2 rows": these are K6 and K7, listed as two bullets.
  - STALESHA L1605 `30917a1a`: `h-mad` and the design are unchanged from there to HEAD, as v1.3 showed.
  - The dated Version History entries.
- `ACS: OK count=51 frs=10`.
- `WIREPIN: PASS tasks=18 wiring=1 unpinned=0 mislabeled=0`, with a scratch registry deleted afterwards.
- Task 8's three registered WIRE-PINs keep their test names: `test_must_count_mismatch_through_production_path`, `test_extract_parity_collapsing_group` and `test_should_findings_are_written_on_a_count_difference` (`grep -n '^\*\*WIRE-PIN' <doc>`).

## Reproduce blocks
I extracted the plan's three published reproduce blocks (Task 2 argparse, Task 5 `O_NOFOLLOW`, Task 9 `Fraction`) and executed them. Each block's output equals the `# ` lines the plan publishes: MATCH 20/20, 2/2 and 1/1 lines. The scratch extract was deleted afterwards.

## Per finding
None rejected. Every premise held when checked against the plan text and the tree.

**S1 (`_OPEN_INPUT` unpinned).** HOLDS.
- Premise: `grep -n '_OPEN_INPUT'` found no test or row in v1.3; Test 1 replaces the handler, and Tests 2 and 4 fail at parse time.
- Fix, option (a) of the review:
  - Task 7 `test_smoke_last_resort_names_the_open_input` and row `p-open-input` (`# M:GAS-OPEN-INPUT`).
  - Task 2 states that `_OPEN_INPUT` is never cleared and that the last input opened is reported.
- Proof: `grep -c "p-open-input\|test_smoke_last_resort_names_the_open_input" <doc>` is 4 or more.

**S2 (Effort block grammar and its callers).** HOLDS.
- Premise: `render` writes `Effort:` only `if effort:`, followed by `- {item}` lines, and then `[H-MAD]` or `Premise checklist:` (h_mad_audit_cycle.py:1046-1048, 1072-1074).
- Fix, Task 7, "The `Effort:` block grammar":
  - Text with no `Effort:` line returns `[]`.
  - The terminator is the first line that does not begin with `- `.
  - Three distinct `None` conditions, each with a fixture and a row: ITEM (a `- x1 …` item), EMPTY and TWICE.
- Callers:
  - smoke: `test_smoke_refuses_a_malformed_effort_block` and `p-smoke-effort-malformed`. The fixture is a non-dispatch grok cycle, so that the mapping is the only guard; on a cycle that reached dispatch, step 3's absent-item check prints the same token.
  - score: OPEN-DECISION on Task 9 with two implementations named, plus a counted fixture and row (`test_score_maps_a_malformed_effort_block`, `p-score-effort-malformed`).
  - extract: stated not to call the parser, and Task 8's dependency text is corrected.
- Proof: `grep -c "GAS-PARSE-EFFORT-\(ITEM\|EMPTY\|TWICE\)" <doc>` is 6 (each in the grammar text and in its row).

**S3 (`parse_root_line`'s `None` callers).** HOLDS.
- Premise: Task 6's and Task 10's tests covered only a missing line or record.
- Fix:
  - Task 6 maps `None` to `root_record:no_line` and adds `test_record_cycle_refuses_a_root_record_with_a_malformed_ready_line` with `p-record-root-malformed`.
  - Task 10 maps `None` to `list_changed:unrecorded` and adds `test_list_changed_malformed_root_record` with `p-list-malformed`.
  - Both are marked as plan extensions, owed to the design and spec.
- Proof: `grep -c "malformed_ready_line\|malformed_root_record" <doc>` is 4.

**S4 (assertion order can hide a crash).** HOLDS.
- Fix: rule (3) now has an **Order** clause. In every test with both a token assertion and a traceback-count assertion, the token assertion (with stderr as its message) comes first. AC-T5.1 restates the order as steps 1-3.
- Proof: `grep -c "Order (axis: an assertion whose message withholds stderr)" <doc>` is 1.

**S5 (`Refusal` coverage and its token channel).** HOLDS.
- Fix:
  - AC-T5.1 now names all 10 refusal tests, including the three that raise `Refusal` (git_target, rescans_after_removal, runs_the_reach_check).
  - Task 2 states that handlers do not catch `Refusal`; `refusal_token` prints `exc.reason` (`# M:GAS-REFUSAL-REASON`, row `p-refusal-reason` in Task 3).
  - Optional row added: `p-traceback-scope-reset` narrows the traceback scope to `UsageError` and targets `test_build_root_reset_refuses_an_empty_target`.
- Proof: `grep -c "p-refusal-reason\|p-traceback-scope-reset" <doc>` is 4 or more.

**S6 (outcome-sentence absence).** HOLDS.
- Fix:
  - Task 16's `test_grok_runtime_states_the_outcome_sentence` also asserts that the other branch's sentence is absent.
  - New row K7 inserts that sentence, so the absence assertion is observed failing.
  - Production-files line updated.
- Proof: `grep -c "grok-runtime-other-branch-sentence-added" <doc>` is 1.

**S7 (measurement: three readings without commands).** HOLDS.
- Fix:
  - The Task 2 block now prints the 4 `.exit(` lines themselves instead of a count, and adds the plain-top-level-parser and `allow_abbrev` readings.
  - `python3` is pinned as `/opt/homebrew/opt/python@3.15/bin/python3.15` (verified: `Python 3.15.0`).
  - Task 9 has a `Fraction` reproduce block.
- Proof: the execution above (MATCH in all three blocks).

**Nits.** All four applied.
- The v1.2 and v1.3 entries are label-fixed to "document sha256 5490674" and "document sha256 4b8400ba". 5490674354db is the sha256 of the v1.1 document I reported in v1.1's DONE line, which resolves the reviewer's unverified referent.
- The v1.4 entry cites commit 5f10a1d9 and document sha256 3015ade9 separately.
- Task 16's production-files line is updated.
- `python3.15` is pinned by absolute path.
- Rule (3) gives the in-process spelling `err.count(...)`.

## Counts (value-swept and parsed from the document)
- **S0 rows: 180**, from 171. 28 named rows and 152 P-rows.
  - By Task: T2 6, T3 15, T4 14, T5 14, T6 12, T7 29, T8 20, T9 26, T10 22, T11 2, T12 17, T13 3.
- **After Task 16:** 182 rows on PASS or a smoke failure (K6 and K7); 184 on MISS or INCONCLUSIVE (also K4 and K5).
- **Markers: 125**, from 117 (parsed: 125 distinct).
- **RED:**
  - T6: 16 F.
  - T7: 48 F (smoke module 44 + probe module 4).
  - T9: 32 F.
  - T10: 44 ids, 33 F and 11 P.
  - T16: unchanged, 4 tests on every outcome.
- **Updated in the document:** the Executive Summary, AC-T14.2 (`0/180`), AC-T14.4 ("125 and 180"), AC-T16.3 (182 or 184).

## Phase-5 notes (not put into the document)
- With `_OPEN_INPUT` never cleared, an exception during `smoke`'s published-line printing, after every input has closed, reports the last input. That is the stated reading; 5d may prefer clearing it on close, which would be a design question.
- `p-traceback-scope-reset` shares its `find` with `p-traceback-scope`. Both are valid rows on one marker line; 5e should not treat the shared find as a duplicate.

## OWED-ELSEWHERE (new this round)
- Design D5 and spec AC-5.4: `root_record:no_line` and `list_changed:unrecorded` are extended to a malformed `ROOT: READY` line or record.
- Design D11: the `Effort:` block grammar.
- Design D13 and spec AC-5.4: the source of `low_evidence=` and score's `None` mapping (Task 9 OPEN-DECISION; option (a) extends `cycle_token` trigger (2)).
- Design D1: the `Refusal` → `exc.reason` channel in `refusal_token`.

## Tree
The impl-plan is modified and uncommitted. The other scratchpad files are the orchestrator's, not mine.
