# Analysis: preflight-read-enforcement

> Cycle 1 — measured at commit `20cac8b` (Phase 5g), before the Phase-6b fix.

## Executive Summary

Every FR is implemented and the suite is green at 548/548, but two acceptance criteria have no
assertion anywhere, so two FRs fail the all-ACs-met rule and the FR-level match rate is 77.8%.

## Match Rate: 77.8%

FR-level (the formula: FRs where *every* AC is met ÷ total FRs): **7/9 = 77.8%**.
AC-level, for calibration: **35/37 = 94.6%**.

The two numbers diverge sharply because both misses are single ACs inside otherwise-complete FRs.

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: `env` emits a receipt on PASS | 5 | 5 | ✅ Complete | `hmad-dispatch.sh:98-124`, `:379`; `test_preflight_pass_writes_default_receipt_with_timestamp_and_fingerprint`, `test_preflight_receipt_fingerprint_is_stable_and_tracks_resolved_handles` |
| FR-2: failing preflight leaves no usable receipt | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:379`; `test_preflight_fail_without_receipt_leaves_no_receipt_and_preserves_verdict`, `test_preflight_fail_removes_existing_receipt` |
| FR-3: dispatch fails closed | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:855-863`; `test_send_without_receipt_refuses_before_delivery` (asserts the capture file, not just rc), `test_send_after_passing_env_delivers_on_enforced_path`, and the inline/indirection assertions at `test_hmad_dispatch.py:1647,1658` for AC-3.4 |
| FR-4: fingerprint mismatch invalidates | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:136-158`; `test_send_rejects_expired_and_rotated_receipts_with_distinct_reasons`, `test_receipt_for_unresolved_agent_is_invalid_after_pinning` |
| FR-5: freshness window | 4 | 3 | ⚠️ Partial | AC-5.1–5.3 covered (`test_send_rejects_expired_and_rotated_…` sets `TTL_SEC=1`). **AC-5.4 unmet** |
| FR-6: documented opt-out | 4 | 3 | ⚠️ Partial | AC-6.1–6.3 covered (`test_send_bypass_is_explicit_and_enforced_when_empty`, incl. the empty-string case). **AC-6.4 unmet** |
| FR-7: agent-conflict guard | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:828-840`, `:853`; `test_send_refuses_when_both_agents_resolve_to_one_handle`, `test_send_allows_distinct_agent_resolutions`, `test_send_unresolved_agents_is_not_refused_as_a_conflict` |
| FR-8: receipt path override | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:98-100`; `test_preflight_receipt_override_wins_over_pin_file_directory`, `test_default_preflight_receipt_is_gitignored`. AC-8.3 verified by measurement (below), by design |
| FR-9: docs state machinery | 4 | 4 | ✅ Complete | `SKILL.md` Phase-5 section, `references/agent-substrate.md`; `test_h_mad_preflight_docs.py` ×4 |

## Gaps

### Gap 1: AC-5.4 — the unset-TTL default is unasserted
- **Missing**: no test pins the default to 3600s. The existing expiry test sets
  `HMAD_PREFLIGHT_TTL_SEC="1"` explicitly, which satisfies AC-5.3 (configurable) but leaves the
  documented default unmeasured. It could be changed to any value, or to an unbounded window, with
  the suite still green.
- **Classification**: `code-vs-design` — the design specifies the 3600 default and the code
  implements it literally (`hmad-dispatch.sh:145`, `${HMAD_PREFLIGHT_TTL_SEC:-3600}`). This is a
  test-coverage defect, not an implementation defect.
- **Where it should be**: `h-mad/tests/test_hmad_dispatch.py`
- **Fix**: a test that ages a receipt to 3500s and expects delivery, then to 3700s and expects
  `preflight_expired`, **without** setting `HMAD_PREFLIGHT_TTL_SEC`.

### Gap 2: AC-6.4 — the bypass is never tested against the conflict guard
- **Missing**: no test combines `HMAD_SKIP_PREFLIGHT` with two agents resolving to one handle. The
  spec requires the bypass to waive the *receipt* requirement only.
- **Classification**: `code-vs-design` — the code is already correct because
  `_preflight_conflict_check || return 1` (`:853`) precedes the bypass branch (`:855`). But nothing
  holds that ordering, so a later refactor could move the conflict check inside the `else` and no
  test would notice.
- **Where it should be**: `h-mad/tests/test_hmad_dispatch.py`
- **Fix**: a test setting `HMAD_SKIP_PREFLIGHT=1` with both agents on one handle, expecting rc=1,
  `preflight_agent_conflict`, and no delivery call in the capture file.

## Notes on items deliberately not counted as gaps

- **AC-8.3** is verified by measurement, not by a test, as the spec and design both state. Measured
  this cycle: suite reported `539 passed` both with and without a receipt at the default path
  (counts compared, never the summary line — an elapsed-time difference in that line produced a
  false negative on the previous feature).
- **`AC-1.6` and `AC-6.5` appear in test docstrings but not in this spec.** They are pre-existing
  labels from `preflight-signal-discipline` (Wave 2), confirmed present on `main`. Different
  feature's numbering, not a mislabel introduced here.
- **AC-3.4, AC-5.3 and AC-6.2 are covered but unlabelled** — the assertions exist
  (`test_hmad_dispatch.py:1647,1658`, `:2537`, `:2514`) without naming the AC in a docstring. Counted
  as met on the strength of the assertion, not the label; a label comparison alone would have
  reported four false gaps here.

## Test Results

```
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q
548 passed in 17.01s
```

Guards additionally verified by mutation rather than by a green run:
- stubbing `_receipt_valid` to `return 0` → 4 failures
- stubbing `_preflight_conflict_check` to `return 0` → 1 failure
- removing `preflight_handles_rotated` from `SKILL.md` → 2 failures

## Verdict

Match rate: 77.8% (threshold: 90%). Tests: 548/548 passing.
→ **Iterate — 2 gaps to close.** Both are `code-vs-design` test-coverage gaps, so Phase 6b can close
them mechanically; neither is a `design-vs-spec` reconciliation question requiring the operator.

## Version History
- v1.0: Initial gap analysis draft.
