# Report: codex-tdd-gate-defects

## Executive Summary
Both Phase-5 TDD gates now take one verdict from a single shared judge. The five fail-opens that `reproduce.py` measured before merge are closed, and the feature merges at a 98% match rate with a `READY_TO_MERGE` architectural review.

## Summary
The feature adds `h-mad/scripts/h_mad_tdd_judge.py`, which reads the state chain, resolves the test for a production target (impl-plan Task first, then the name map), runs it within a 40 s budget and scores pytest's summary line. The Claude gate (`h-mad-tdd-gate.sh`, rewritten on refusal form (b): rc 0 plus a JSON deny) and the Codex gate (`h-mad-codex-tdd-gate.py`) both call it. The audit gate's suite scoring and the wire-pin parser gained the grammar the judge shares. The main decision was the V-0 reading (`E1_DOES_NOT_BLOCK`, form b chosen), because an `exit 1` hook never blocked a Write.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 |
| Design audit cycles | 2 |
| Impl-plan audit cycles | 2 (round cap; v1.2 corrective, delta review 0 must) |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 98% (46 of 47 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` (agy, tools=35) |
| Tests | 4196 passing / 1 failing (the pre-existing live-binary baseline node `test_top_level_key_set_still_matches`, the same reason as at BASE_SHA) |
| Phases with back-propagation | Phase 4: design v1.3 (DD-7 root-under-`tests/`, OQ-I3) propagated to spec/plan and to impl-plan v1.2 |

## What Went Well
- Reading the V-0 contract before rewriting the Claude gate settled the refusal form by measurement. The design had assumed `exit 1` blocks, and it does not.
- The 98 mutation rows in eight specs were re-verified independently of the implementer. Each Task 8 wire has a revert row killed by its WIRE-PIN.
- Every Task 11 item ran through a committed probe with its reading beside it, OQ-D1's live host-deadline probe included. OQ-D1 was run headless with V-0's mechanism rather than left to the operator.

## What To Improve Next Time
- A fresh-context verifier reproduced five fail-opens (D1–D5) after the suite, the mutation harness, the gate readings and an agy `READY_TO_MERGE` had all passed. The agy review named no file:line finding. Run the adversarial repro pass before 6a-prime, not after it.
- Codex returns BLOCKED on any step that writes inside `.git`. State this in the dispatch prompt up front, and run that step as the orchestrator.
- About one GREEN BLOCK in three was a defect in the RED test. Sweep every lookup of a defect before re-dispatching.
- §"Regression provenance" missed a stdin-only key (`test_h_mad_audit_suite_gate.py::run`). The census that fed it grouped by assertion change, not by top-level statement.
- Two suite tests mutate the tracked `h-mad/tests/conftest.py` in place (since `b1f8954c`). Any concurrent pytest in the same tree flakes. This caused the one "concurrency artifact" this feature saw.

## Carry Items
- **Follow-up feature (operator decision 2026-09-29): gate fail-opens D1–D5** from `codex-tdd-gate-defects.gap.v1.md`, D1 and D2 first. D1: a case-variant `.PY` suffix passes both gates on case-insensitive APFS. D2: a Codex patch header with a trailing space or CRLF escapes `PATCH_TARGET`. D3: a symlinked root spelling under `tests/` re-opens the §D9 exemption. D4: a `tests/` symlink to a production directory makes the two gates disagree. D5: `_run_bounded`'s post-kill `communicate()` has no timeout. All except D3's AC-6.15 angle are inherited from the base gates.
- OQ-D1, Codex half: open. The Codex gate is not registered on this machine.
- Live V-1: blocked on `~/.agents/skills/h-mad` (multi-host-runtime).
- grok-codex-fallback rebases onto this merge and re-plans its Tasks 12 and 14 onto §D13. multi-host-runtime rebases after grok.
- Plan text left stale (recorded in the analysis): Task 1 `# M:S…` tags; item 7's empty-stderr expectation under form b.
- The in-place `conftest.py` mutation hazard (pre-existing, outside this feature).
- HemaSuite #28 may re-arm its codex TDD hook once this is live-verified in that repository.

## Version History
- v1.0: Initial report draft (2026-09-29).
