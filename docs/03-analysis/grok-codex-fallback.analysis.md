# grok-codex-fallback analysis

Phase 5 readings recorded from 2026-09-29, after the rebase onto main `8ef6009f` (merge of
codex-tdd-gate-defects). Tasks 1–11 and 13 were implemented before the rebase; their readings live
in their commit messages.

## Rebase

24 commits replayed onto `8ef6009f`. The only conflict was `.h-mad/wires.jsonl`, resolved as main's
25 records plus this feature's 13 (no key in common). The first post-rebase full suite read
`2 failed, 4369 passed`: the baseline node and
`test_h_mad_assemble_tdd_agent.py::test_no_agent_output_is_byte_identical_to_base`, whose base pin
`507214d` predated the merged implementer prompt (+140 bytes). Re-pinned to `8ef6009f` (`f2ff9261`).

## Documents after the rebase

Spec v1.5 (`02283561`), design v1.3 (`6277d703`), impl-plan v1.4 → v1.6.1 (`aaf796eb`, `9428b68d`,
`c0ab18e2`, `deb85703`, `c9eec88c`), with advisory delta reviews v1.4 (0/5/6) and v1.5 (1/3/3). Two
orchestrator errata came from execution: v1.5.1 (Task 12 RED split 64/128, test 18's `grok` item
asserts a diagnostic the RED gate cannot print) and v1.6.1 (row G9 survived because the v1.5 tag
agreement check also refuses an out-of-range fold; the test now asserts the range check's own
diagnostic).

## Task 12 — tdd-gate fallback agent

RED `b190f01d`: 64 failed / 128 passed on the new file (both locales); migrated files 25 failed /
168 passed. GREEN `0d6088bc`: 385 passed across the three gate/judge files (both locales); anchors
1005/1005; `claude_gate_judge_wiring.json` ALL_CAUGHT 37/37; each WIRE-PIN fails on its
wire-scoped revert (fold call → `none`; `FALLBACK` → `none`). Full suite: 1 failed (baseline) /
4562 passed. Registry move `c8f07e13`: 40 records, 15 of this feature's; `verify --base 8ef6009f`
reads `WIREREG: FAIL verified=36 missing=4`, all four multi-host-runtime records whose pins exist
only on the unmerged mhr branch.

## Task 14 — mutation specs

Seven specs, 65 rows (`18072a14`), each `ALL_CAUGHT`; the six committed gate/judge specs re-run
`ALL_CAUGHT`; aggregate `ANCHORS_OK specs=114 mutations=1070`. Two specs first read
`BASELINE_NOT_GREEN` because `test_h_mad_assemble_tdd_agent.py` ran `git archive … h-mad` from the
harness cwd `h-mad/`; fixed to run from the repository root. Crash kills recorded: E4 and E10
(`TypeError`, in tests whose subject is that no crash occurs) and A1 (`KeyError`).

## Task 15 — docs

RED `bad52410` 6 failed / 1 passed; GREEN `b6bd4402` 7 passed; codex full suite 1 failed (baseline)
/ 4569 passed; anchors 1070/1070.

## Task 16 — regression floor

`FLOOR: PASS files=270 suite_rc=1` (`probes/grok-codex-fallback/t16-floor.reading.b6bd4402.txt`);
every carve-out file reports its stated change and `rest_equals_base=True`.

## Task 17 — live smoke

`SMOKE: PASS` against grok 1.0.41: `RESOLVED-MODEL agent=grok model=grok-4.7-build`,
`EVIDENCE: PASS tools=10 ok=10 unresolved=0 thinking=1018 format=grok stop_reason=end_turn`
(`probes/grok-codex-fallback/t17-smoke.reading.b6bd4402.txt`).
