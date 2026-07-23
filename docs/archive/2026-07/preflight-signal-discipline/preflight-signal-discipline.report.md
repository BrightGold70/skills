# Report: preflight-signal-discipline

## Executive Summary

Wave 2 of the h-mad remediation sequence shipped: `hmad-dispatch env` now ends in a canonical
`PREFLIGHT: PASS|FAIL` token with the exit code untouched, `SKILL.md` obliges an orchestrator to
assert it (and `ASSEMBLE: PASS`) before dispatching, and the session pin file can no longer leak into
the test suite — closing J7, which had made "follow the protocol" and "get a green suite" mutually
exclusive.

## Summary

`_cmd_env` already detected the two conditions that silently destroy a dispatch — a stale pin and a
codex/agy handle collision — but printed them as prose nothing was required to read. The token makes
that detection consumable; the mandated read makes it binding. Folded in was J7: `_pin_file()`
resolves a **cwd-relative** default and pytest's cwd is the repo, so the repo's own
`.h-mad/orca-pins.env` was read by any test that set no explicit value. Because Phase-5 preflight
*requires* `pin-agents` and Phase 5f *requires* the full suite, following the protocol guaranteed a
red suite in the repo that owns those tests.

Both halves are preflight correctness, which is why they were one feature rather than two.

## Metrics

| Metric | Value |
|---|---|
| Spec | 7 FRs / 26 ACs |
| Match rate | **100% (26/26)** |
| Suite | **530 passed** (498 at Wave 1 → 530) |
| Suite with pin file present | **530 passed** — identical (AC-6.2) |
| Baseline before J7 fix | 17 failed / 136 passed in `test_hmad_dispatch.py` |
| Audit cycles | plan 1, design 2, impl-plan 1 |
| Iterate cycles | 0 |
| 6a-prime | cycle 1 `WITH_FIXES` → cycle 2 `READY_TO_MERGE` |
| Commits | `aa1f01a` (baseline) → `fcea6ab` |

## What Went Well

- **The feature caught its own hazard, live.** Mid-way through its own 6a-prime re-review, agy's pane
  restarted and its handle rotated. The mandated read — added two commits earlier — printed
  `PREFLIGHT: FAIL stale=agy` and `send` refused. The dispatch was stopped, agy re-identified by
  content, re-pinned, re-asserted, re-dispatched. That is the same handle-rotation class that lost a
  Task-2 RED dispatch on HemaSuite and put this wave on the board.
- **RED caught a defect in the design.** The Task-1 tests consumed `_NO_PIN_FILE` via `.is_absolute()`
  / `.parents` / `.exists()`, pinning it as a `Path`; the design had specified `os.path.join`, which
  returns a `str` and would have raised `AttributeError`. The implementation was adapted to the tests
  rather than the reverse.
- **"Stop, don't improvise" paid for itself immediately.** The first Task-1 dispatch named
  `REPO_ROOT`/`SKILL_DIR` as pinned API; they do not exist in that module (it defines `SKILL`).
  Codex returned `NEEDS_CONTEXT` and left the tree clean instead of inventing a plausible
  `REPO_ROOT = Path(__file__).resolve().parents[2]` that would have worked while silently forking the
  module's convention.
- **Guards were labelled, so none were gamed.** Both RED dispatches stated expected pass/fail counts
  (3/2 and 12/3) and said outright that an all-failing run meant the guards had been over-strengthened
  — the documented failure mode for refactor-shaped tasks.
- **Regression tests were proven to discriminate.** The two 6a-prime fixes were temporarily reverted
  to confirm the new tests fail against the old behaviour before being kept.

## What To Improve Next Time

- **Verify pinned API against the actual file, not a sibling.** `REPO_ROOT`/`SKILL_DIR` were carried
  over from `test_h_mad_audit_conditionals.py`, which does define them. One grep would have prevented
  a wasted dispatch cycle.
- **Reason about scope extensions as carefully as the original scope.** FR-7 (the automation precheck)
  was added during Phase 1 and introduced the one genuine hazard 6a-prime found: gating on
  `PREFLIGHT: PASS` alone meant an automation with no agents pinned would preflight green. The
  original lenient-FAIL decision was sound; the extension around it was not thought through.
- **A measurement harness can produce false negatives.** The AC-6.2 check first compared whole pytest
  summary lines including elapsed time (`11.75s` vs `11.57s`) and reported a failure that did not
  exist. Compare the counts, not the line.

## Carry Items

- **The mandated reads are protocol, not machinery** (FR-4/FR-5). Nothing mechanically enforces that
  an orchestrator asserts the token. Declared Out-of-Scope in the spec and confirmed a real residue by
  6a-prime cycle 1. **Wave 3's dogfood run is the exercise** — it should be treated as the test of
  this wave, not a formality.
- **The CONFLICT case is not mechanically guarded.** `send` refuses a *stale* handle (`912b93a`), so
  the original hazard is blocked at the boundary; two agents on one **live** handle remains detectable
  only by the protocol read.
- **J8 root cause identified** (not fixed). This feature's telemetry row reads `110.3m` elapsed while
  every prior row reads ~`29744612.6m` (≈56 years). The only difference is that this run passed an
  explicit `--started-ts` to `h_mad_state_write.py --create`. The defect is therefore in the writer's
  **default** `started_ts`, not in `h_mad_telemetry.py`'s reader. That narrows J8 considerably.
- **Report-contract gap.** The Task-2 GREEN dispatch returned `DONE_WITH_CONCERNS` while naming no
  concern anywhere in its report. A verdict declaring doubt without stating it is unactionable; worth
  a `docs/skill-monitoring.md` entry.
- **J1, J9** untouched, as scoped.

## Version History
- v1.0: Phase 7 closure report.
