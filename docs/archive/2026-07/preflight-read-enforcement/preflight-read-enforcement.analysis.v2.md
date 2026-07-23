# Analysis: preflight-read-enforcement

> Cycle 2 — re-measured at commit `bd20c5e`, after the Phase-6b fix closed both gaps.

## Executive Summary

Both cycle-1 gaps are closed; every AC in the spec now has an assertion (or, for AC-8.3, a
measurement it was specified to have), and the FR-level match rate is 100% at 550/550 passing.

## Match Rate: 100%

FR-level (the formula: FRs where *every* AC is met ÷ total FRs): **9/9 = 100%**.
AC-level, for calibration: **37/37 = 100%** (36 asserted by tests, AC-8.3 by measurement).

## FR Coverage

| FR | ACs Total | ACs Met | Status | Evidence |
|---|---|---|---|---|
| FR-1: `env` emits a receipt on PASS | 5 | 5 | ✅ Complete | `hmad-dispatch.sh:98-124`, `:379`; `test_preflight_pass_writes_default_receipt_with_timestamp_and_fingerprint`, `test_preflight_receipt_fingerprint_is_stable_and_tracks_resolved_handles` |
| FR-2: failing preflight leaves no usable receipt | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:379`; `test_preflight_fail_without_receipt_leaves_no_receipt_and_preserves_verdict`, `test_preflight_fail_removes_existing_receipt` |
| FR-3: dispatch fails closed | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:855-863`; `test_send_without_receipt_refuses_before_delivery` (asserts the capture file, not just rc), `test_send_after_passing_env_delivers_on_enforced_path`, and the inline/indirection assertions at `test_hmad_dispatch.py:1647,1658` for AC-3.4 |
| FR-4: fingerprint mismatch invalidates | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:136-158`; `test_send_rejects_expired_and_rotated_receipts_with_distinct_reasons`, `test_receipt_for_unresolved_agent_is_invalid_after_pinning` |
| FR-5: freshness window | 4 | 4 | ✅ Complete | AC-5.1–5.3 as before; AC-5.4 closed by `test_unset_ttl_uses_the_documented_3600_default` |
| FR-6: documented opt-out | 4 | 4 | ✅ Complete | AC-6.1–6.3 as before; AC-6.4 closed by `test_bypass_does_not_suppress_the_agent_conflict_guard` |
| FR-7: agent-conflict guard | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:828-840`, `:853`; `test_send_refuses_when_both_agents_resolve_to_one_handle`, `test_send_allows_distinct_agent_resolutions`, `test_send_unresolved_agents_is_not_refused_as_a_conflict` |
| FR-8: receipt path override | 4 | 4 | ✅ Complete | `hmad-dispatch.sh:98-100`; `test_preflight_receipt_override_wins_over_pin_file_directory`, `test_default_preflight_receipt_is_gitignored`. AC-8.3 verified by measurement (below), by design |
| FR-9: docs state machinery | 4 | 4 | ✅ Complete | `SKILL.md` Phase-5 section, `references/agent-substrate.md`; `test_h_mad_preflight_docs.py` ×4 |

## Gaps

None outstanding. Both cycle-1 gaps were closed in `bd20c5e`:

### Gap 1 (AC-5.4) — CLOSED
`test_unset_ttl_uses_the_documented_3600_default` ages a receipt to 3500s (expects delivery) and to
3700s (expects `preflight_expired`) **without** setting `HMAD_PREFLIGHT_TTL_SEC`.

### Gap 2 (AC-6.4) — CLOSED
`test_bypass_does_not_suppress_the_agent_conflict_guard` sets `HMAD_SKIP_PREFLIGHT=1` with both
agents on one handle and expects rc=1, `preflight_agent_conflict`, and no delivery call.

**Both are regression guards, so they passed on arrival** — which is exactly the shape that ships an
unenforced test. Each was therefore verified to *discriminate* by mutation instead: defaulting the
TTL to 999999 fails the first, and short-circuiting the conflict check under the bypass
(`[ -n "$HMAD_SKIP_PREFLIGHT" ] || _preflight_conflict_check`) fails the second.

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
550 passed in 18.32s
```

Guards additionally verified by mutation rather than by a green run:
- stubbing `_receipt_valid` to `return 0` → 4 failures
- stubbing `_preflight_conflict_check` to `return 0` → 1 failure
- removing `preflight_handles_rotated` from `SKILL.md` → 2 failures
- defaulting the TTL to 999999 → 1 failure (the new AC-5.4 guard)
- short-circuiting the conflict check under the bypass → 1 failure (the new AC-6.4 guard)

## Verdict

Match rate: 100% (threshold: 90%). Tests: 550/550 passing.
→ **Advance to Phase 7.** Phase 6a-prime returned `READY_TO_MERGE`.

## Version History
- v1.0: Initial gap analysis draft (77.8%, 2 gaps).
- v2.0: Re-measured after the Phase-6b fix — 100%, both gaps closed and mutation-verified.
