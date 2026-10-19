IMPLPLAN-AUTHOR: DONE version=v1.3 tasks=18 wiring=1 mutation_rows=171 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.impl-plan.md lines=1683 sha256=3015ade96e9492866ebbb9ad0d6c175377756a21a1f23cd4e3a49f4025c8c8e8

## Ownership check before writing
The document's sha256 was 4b8400ba95e5e2a6dd2c1fb81085dd73cb959b5205972e56d233ef48a2176702 and its newest Version History entry was `- v1.2`, so nobody else had written it. I bumped the version with `h_mad_version_history.py --version v1.3` (`VERSION-HISTORY: OK … line=1683`). Not committed.

## Gates
- `PRECHECK: PASS issues=0`. Advisories:
  - COUNT L1383 and L1489, as before.
  - STALESHA L1443 `30917a1a`: harmless, because `git diff --quiet 30917a1a HEAD -- h-mad <design>` exits 0.
  - The dated Version History entries.
- `ACS: OK count=51 frs=10`.
- `WIREPIN: PASS tasks=18 wiring=1 unpinned=0 mislabeled=0`, with a scratch registry deleted afterwards.

## Per finding
None rejected. Each fix comes with the command that proves it.

**agy-S1: Test 4 lacks the smoke exception.** Premise HOLDS.
- In v1.2, Test 4's assertion said `reason=internal:UsageError` with no `smoke` exception, while Tests 1 and 2 carried it.
- agy's quoted design sentence ("Every parser error in the table's other eight modes …") is not in the design: `grep -n "Every parser error in the table" <design>` printed nothing. The plan-side premise holds without it.
- Fix: Task 2 Test 4 now gives the `smoke` token as `input_unparseable:` followed by the `--data` value.
- Proof: `grep -n "the \`--data\` value, as in Tests 1 and 2" <impl-plan>` prints 1 line.

**agy-S2: how the smoke's open input reaches `refusal_token`.** Premise HOLDS.
- In v1.2 nothing connected the input Task 7's smoke had open to Task 2's `refusal_token(mode, exc, argv)`.
- Fix: a module-level `_OPEN_INPUT`, reset at the start of every `main` call and assigned by `smoke` before it opens each input, read directly by `refusal_token`. The order is `_OPEN_INPUT`, then argv's `--data`, then the empty string (D1).
- Proof: `grep -c "_OPEN_INPUT" <impl-plan>` prints 5 (Task 2 rule, code structure, Task 7).

**codex-M1: refusal classes inherit `Exception`.** Premise HOLDS.
- In v1.2, `grep -n "(Exception)"` showed `Refusal` and the seven reset classes inheriting `Exception`.
- Fix: all now subclass `ProbeRefusal`. AC-T5.1 adds a check that there are 0 `Traceback` occurrences on each non-usage refusal; rule (3) of the Rules section names those assertions.
- Proof: `grep -n "(Exception)" <impl-plan>` prints only `class ProbeRefusal(Exception)`.

**codex-M2: in-process assertions do not forward stderr.** Premise HOLDS.
- The v1.2 rule (2) covered subprocess assertions only, and `crash_kill` returned `None` on a suppressed traceback (my cycle-1 probe).
- Fix: rule (2) now covers in-process `main(argv)` assertions too: `out, err = capsys.readouterr()`, then `assert …, err`. The intentional-exception tests stay excepted, as before.
- Proof: `grep -n "in-process \`main(argv)\` assertion passes the captured one" <impl-plan>` prints 1 line.

**codex-M3: behavioural readings lack their commands.** Premise HOLDS.
- Fix: runnable commands with their observed outputs now sit beside the Task 2 argparse readings and the Task 5 `O_NOFOLLOW` readings. I re-ran them all this round:
  - argparse `.exit(` sites: 3.11.8 gives 4, 3.15.0 gives 4.
  - `smoke --help`: `SystemExit 0`, 105 bytes on stdout, on both interpreters.
  - `O_NOFOLLOW` on a link: `ELOOP`.
  - A parent link with `O_NOFOLLOW` wrote the outside file (`X`).
  - The `O_NOFOLLOW` command uses a self-removing `TemporaryDirectory`, so nothing is left behind.
- Proof: `grep -cE '^# (3\.11\.8 4|link: ELOOP)$' <impl-plan>` prints 2. The BRE `\|` form I tried first printed 1, so the ERE form is the one to use.

**codex-S1: no failing pin for `grok-runtime.md`.** Premise HOLDS.
- In v1.2, Task 16's tests named only SKILL.md and the measurement doc.
- Fix:
  - New test `test_grok_runtime_states_the_outcome_sentence`. It checks the AC-1.5 sentence on a scored outcome or the AC-1.8 sentence on a smoke failure, plus the unchanged 1.0.41 host-mapping sentence. It fails at RED because the outcome sentence is absent, which is the negative observation for that half.
  - New row K6 (1.0.41 → 1.0.40 in `references/grok-runtime.md`) is the negative observation for the preserved sentence. Its find matches 1 line (`grep -cF`).
- Task 16 RED: 4 F on PASS or a smoke failure; 5 nodes (4 F, 1 P) on MISS or INCONCLUSIVE.
- Proof: `grep -n "grok-runtime-host-sentence-changed" <impl-plan>` prints 1 line.

**codex-S2: no negative fixtures for the ROOT and Effort parsers.** Premise HOLDS.
- In v1.2 only the must-parse tests existed for these two; `AUDITCYCLE` already had a must-not-parse test.
- Fix, closing the class "every D10 token parser has a must-not-parse fixture":
  - Task 4 adds `test_root_line_parser_rejects_a_malformed_root_line` and row `p-parse-root`.
  - Task 7 adds `test_effort_parser_rejects_a_malformed_effort_block` and row `p-parse-effort`. The `- ` bullet it checks for is the one `render` writes: `lines.extend(f"- {item}" for item in effort)` in `h_mad_audit_cycle.render`.
  - Both parsers return `None` on a malformed input.
- Proof: `grep -c "rejects_a_malformed_root_line\|rejects_a_malformed_effort_block" <impl-plan>` prints 4 (each test named in its list and in its row).

## Counts (value-swept and parsed from the document)
- **S0:** 171 rows, from 169: T4 13 → 14, T7 24 → 25. 143 are P-rows and 28 are named.
- **After Task 16:** 172 rows on PASS or a smoke failure (adds K6); 174 on MISS or INCONCLUSIVE (adds K4, K5 and K6).
- **Markers:** 117, from 115: T4 10 → 11, T7 14 → 15.
- **RED:** T4 21 F, T7 46 F, T16 as above.
- **Updated:** the Executive Summary, AC-T14.2 (`0/171`), AC-T14.4 ("117 and 171"), AC-T16.3 (172 or 174).
- **Parser check:** 174 table rows in total (171 + 3 conditional) and 117 distinct markers. Every row's test is in its Task's test list, except the existing tests named in v1.2.

## Phase-5 notes (not put into the document)
- A K6 mutant in `references/grok-runtime.md` also changes text that no other test reads; that is harmless.
- Task 16's slot-rule version parsing is shared by two tests (`test_unmeasured_sites_match_the_outcome` and the new runtime test). 5d should implement it once, as a helper in the docs test module.

## OWED-ELSEWHERE
- The v1.2 items (D1 traceback scope, the D12 `extract_all` signature, the D2 `PROBE:` prefix, and the plan-added Test Plan entries).
- New this round:
  - Design D1: the `_OPEN_INPUT` channel.
  - Design D10: the plan-added must-not-parse tests.
  - Design Test Plan: `test_grok_runtime_states_the_outcome_sentence` and K6.

## Tree
The impl-plan is modified and uncommitted. The audit report files belong to the orchestrator.
