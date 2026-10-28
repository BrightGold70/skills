SPEC-AUTHOR: DONE version=v1.8 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.spec.md lines=294 sha256=d48bf00761679fa57197a2dc2395bba0fe8567bc0b4ceb8e8567aab9aac3a421

## Premises verified (HEAD e39f15c5; ground truth: docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py)
- GRAMMAR has 9 keys (ast count = 9): check-ledger, build-root, record-cycle, commit-data, smoke, extract, score, rescore, main-leak. The test MODES tuple matches.
- main(): when argv is empty or argv[0] is not in GRAMMAR, it prints `PROBE: UNREADABLE reason=unknown_mode` (M:GAS-UNKNOWN-MODE), then usage and an `[H-MAD]` marker on stderr, and returns 2.
  - Run live: `""` and `nope` each print that line with rc=2.
  - Test: test_unknown_mode_prints_the_probe_token.
- _TokenArgumentParser: add_help=False, allow_abbrev=False. error() raises UsageError(ProbeRefusal). Subparsers use the same class (build_parser, parser_class=_TokenArgumentParser).
  - refusal_token gives a non-Refusal outside the smoke `internal:<Name>`. The smoke gets `input_unparseable:<_OPEN_INPUT or --data value or "">`.
  - Run live:
    - `score --help` gives `SEEDSCORE: UNREADABLE reason=internal:UsageError`, rc=2.
    - `smoke --help` gives `SMOKE: UNREADABLE reason=input_unparseable:` (empty path), rc=2.
    - a bad `--purpose` choice gives `ROOT: UNREADABLE reason=internal:UsageError`, rc=2.
  - A traceback is printed only for exceptions outside ProbeRefusal (M:GAS-TRACEBACK-SCOPE).
  - Tests: test_usage_error_prints_the_mode_token, test_help_flag_prints_the_mode_token, test_abbreviated_flag_is_a_usage_error (check-ledger only), test_internal_failure_prints_the_mode_token.
- list_check:
  - an absent root.txt gives `list_changed:unrecorded` (M:GAS-LIST-UNRECORDED).
  - a root.txt that does not have exactly one `ROOT: READY ` line, or whose one line fails parse_root_line, gives `list_changed:unrecorded` (M:GAS-LIST-MALFORMED).
  - parse_root_line requires exactly the 7 keys doc, purpose, path, calibration, list_commit, list_blob and absent, each once and non-empty.
  - Tests: test_list_changed_unrecorded_root_record, test_list_changed_malformed_root_record (missing list_blob).
- smoke:
  - parse_effort_items returning None (two `Effort:` lines, an item not matching `p\d+ `, or an empty block) gives input_unparseable:<auditcycle.txt>.
  - On a dispatched cycle, the grok log is read first.
    - If it is missing, the token is input_missing:<log>.
    - If it has no typed events, the token is input_unparseable:<log>.
  - After that, effort_form wrong-file or unknown gives input_unparseable:<auditcycle.txt>.
  - Tests: test_smoke_effort_codex_text_item_refuses_as_wrong_file, test_smoke_effort_missing_item_refuses_as_wrong_file, test_smoke_effort_empty_item_refuses_as_wrong_file, test_smoke_unrecognised_effort_item_refuses, test_smoke_refuses_a_malformed_effort_block.
- score: when a cycle's Effort block does not parse, evidence[surface]="unreadable" for every surface in that cycle (M:GAS-SCORE-EFFORT-MALFORMED).
  - The SURFACE line prints `delivered=` and `low_evidence=`.
  - verdict(totals) does not read either field.
  - Test: test_score_maps_a_malformed_effort_block (asserts the verdict is unchanged).

## Findings applied (all impl-plan-author OWED items addressed to the SPEC)
- v1.1–v1.3, D2 `PROBE:` prefix:
  - AC-5.1 states the no-mode rule (`PROBE: UNREADABLE reason=unknown_mode`, exit 2, stdout holds only that line, `PROBE:` belongs to no mode).
  - AC-5.1 states the usage-error contract (`internal:UsageError` on the mode's own token; for the smoke, `input_unparseable:<--data value>`), with no traceback.
  - AC-5.4 says PROBE is outside the fifteen and names internal:UsageError.
- v1.4, AC-5.4 `list_changed:unrecorded` for a malformed READY record: the rule now has trigger (a) absent and trigger (b) not exactly one parseable READY line, with three shapes. AC-5.5 has fixtures for each.
- v1.4 says `root_record:no_line` is owed to AC-5.4. It is NOT applied: it is a record-cycle reason (`RECORD: REFUSED` grammar), not a SEEDSCORE reason. The spec delegates the per-mode grammars to the design, so it is owed to the design only (see contradictions).
- v1, AC-1.7 carry 10:
  - The `input_unparseable` bullet names the Effort-block and wrong-file triggers.
  - New paragraph "What the restore remedy cannot clear". Its axis is "the refused bytes are the bytes the S1 run produced". It has two members, and its residual is that the probe cannot tell an intact copy from a damaged one.
  - The fixture paragraph is extended.
- v1 D2/D1 (ii), the empty `--data` path: AC-1.7 now states that the path is empty when no `--data` was given.
- Task 9 option (b) per the orchestrator: AC-5.4 is NOT extended. AC-3.4 ("as counts") and AC-5.2 (the closed field list) contradicted the code's `low_evidence=unreadable` and its `delivered=` and `low_evidence=` fields, so I followed the code: both are stated as observational and are never read by the verdict. AC-5.5 has a fixture for this.
- Task 5 (b): no change to D5's order. Nothing about it is touched.

## Values swept (grep -n -o over the spec; occurrences listed by line)
- unrecorded at 192, 196 x2, 294 (history).
- unknown_mode at 171 x3, 195, 196, 294.
- UsageError at 171, 193, 196 x2, 294 x2.
- low_evidence= at 149 x2, 172 x2, 196, 294.
- "nine modes" at 171, 196, 294.
- "ifteen" at 179, 195, 292, 293, 294. The count is unchanged at 15, because no reason form was added.
- "names no list blob": one occurrence (192), now framed as a case of (b).
- "as counts": one occurrence (149), qualified.
- No derived figures depend on the changed values.

## Contradictions found
- The v1.4 report routes `root_record:no_line` to "spec AC-5.4", but the spec has no record-cycle grammar, so it is design-only. I followed the code.

## Placeholder scan
- `PRECHECK: PASS issues=0`.
- All advisories were already present before this revision:
  - STALESHA on the premise stamps and the Version History.
  - PATH: measurement.md is a future file.
  - COUNT at L32, L132, L180 and L292: these are pre-existing text and are not counts of the adjacent list.

## Owed by other documents
- DESIGN D2 / per-mode token-grammar table:
  - add the `PROBE:` row (unknown_mode, exit 2, stdout holds only that line).
  - state that a usage error is internal:UsageError per mode, with the smoke's empty path when there is no `--data`.
- DESIGN D5 / record-cycle: `root_record:no_line` covers zero or several READY lines and a malformed one (v1.4).
- DESIGN D13 / score: the `low_evidence=` source and the `unreadable` value (option (b)).
- DESIGN D1: traceback scope, the `_OPEN_INPUT` channel and `Refusal.reason` (carried items).
- IMPL-PLAN / tests: AC-5.5 now requires `list_changed` trigger-(b) fixtures for "no ROOT: READY line" and "two READY lines". Neither exists today. Only the missing-list_blob shape is pinned (test_list_changed_malformed_root_record), and the `len(records)==1` branch shares the M:GAS-LIST-MALFORMED marker. These 2 tests are owed.
- All other AC-5.5 additions map to existing tests listed above.

## Tree
- I edited only the spec. design.md shows as modified, but that is the concurrent design-author's work, not mine.
- I created no probe files: the live probe runs wrote nothing.
- Nothing is committed.
