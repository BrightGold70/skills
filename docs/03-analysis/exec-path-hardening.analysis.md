# Gap Analysis: exec-path-hardening

> Phase 6a. Design: `docs/02-design/features/exec-path-hardening.design.md` (v1.5)
> Spec: `docs/01-plan/features/exec-path-hardening.spec.md` (v1.2)
> Base `c9ce526` → Head (pre-report) `9f02c75` + Phase-6b gap closure.

## Match rate

**Match rate: 100% (24/24 spec ACs implemented and pinned by a discriminating test).**

Reached after one Phase-6b iterate cycle. The first pass measured **21/24 fully covered**
(87.5%) with FR-4's three non-interference ACs only partially pinned; those were closed rather
than argued, and each was then mutation-checked.

## Per-AC reconciliation

| Spec AC | Pinning test | Status |
|---|---|---|
| AC-1.1 ≥2 stamps, one pre-agent | `test_start_stamp_is_written_before_the_agent_runs` | ✅ |
| AC-1.2 exit carries agent+rc+verdict | `test_exit_stamp_carries_agent_rc_and_verdict` | ✅ |
| AC-1.3 cmux zero calls, identical output | `test_start_stamp_is_silent_on_cmux`, `test_ac_4_3_cmux_makes_zero_orca_calls` | ✅ |
| AC-1.4 orca non-zero → rc unchanged | `test_ac_4_4_orca_failure_is_silent_success` | ✅ |
| AC-1.5 orca hangs → bounded | `test_ac_4_5_hanging_orca_is_bounded_and_silent`, `test_ac_3_9_hanging_orca_read_is_bounded` | ✅ |
| AC-2.1 >1 beat, overwrite not append | `test_heartbeat_stamps_across_three_intervals` | ✅ |
| AC-2.2 elapsed monotonic | `test_heartbeat_elapsed_values_are_monotonic` | ✅ (see §6a-prime) |
| AC-2.3 interval 0 → no beats | `test_zero_heartbeat_still_has_start_and_exit_but_no_beats` | ✅ |
| AC-2.4 no `--timeout` → same cadence | `test_heartbeat_without_timeout_keeps_the_same_cadence` | ✅ |
| AC-2.5 failing beat doesn't kill dispatch | `test_heartbeat_shorter_than_stamp_timeout_terminates` | ✅ |
| AC-3.1 one notify after exit | `test_exit_notify_fires_once_with_rc` | ✅ |
| AC-3.2 body carries `rc=<n>` | `test_exit_notify_fires_once_with_rc` | ✅ |
| AC-3.3 failing notify → rc/stdout unchanged | `test_notify_failure_does_not_change_exec_rc_or_stdout` | ✅ |
| AC-4.1 stdout byte-identical on/off | `test_ac_4_1_stdout_is_byte_identical_with_surfaces_on_and_off` | ✅ **added in 6b** |
| AC-4.2 rc-3 path byte-identical | `test_ac_4_2_empty_final_message_path_is_byte_identical` | ✅ **added in 6b** |
| AC-4.3 rc survives every surface failing | `test_ac_4_3_agent_rc_survives_every_surface_failing` | ✅ **added in 6b** |
| AC-4.4 mutation-verified | `MUTATION: ALL_CAUGHT mutations=5 caught=5 survived=0 refused=0` | ✅ |
| AC-5.1 codex `--log` preserves prior | `test_..._log_append` (codex half) | ✅ |
| AC-5.2 agy equivalent, one parameterised test | same test, agy half | ✅ |
| AC-5.3 agy caller-log recovery unchanged | `test_agy_empty_response_recovers_verdict_from_caller_log` | ✅ |
| AC-5.4 docs state the same contract | `test_skill_docs_describe_log_append_without_codex_truncation_claim` | ✅ |
| AC-6.1 `--cd` targets its worktree | `test_stamp_targets_the_cd_worktree_not_active` | ✅ |
| AC-6.2 `active` fallback | `test_ac_3_4_active_fallback...` | ✅ |
| AC-6.3 unreadable → zero writes | `test_stamp_abandons_write_when_resolver_fails` | ✅ |

Suite: **1060 passed, 0 failed**. `bash -n` clean. Both symlink-coupled suites run.

## Connection enforcement

All five wires verified by wire-scoped revert — call site removed, callee and tests intact,
named pin fails, restore, pin passes:

| Wire | Pin | Wired-out | Restored |
|---|---|---|---|
| W1 start | `test_start_stamp_is_written_before_the_agent_runs` | 1 failed | 1 passed |
| W2 heartbeat | `test_heartbeat_stamps_across_three_intervals` | 1 failed | 1 passed |
| W3 exit | `test_exit_stamp_carries_agent_rc_and_verdict` | 1 failed | 1 passed |
| W4 notify | `test_exit_notify_fires_once_with_rc` | 1 failed | 1 passed |
| W5 resolver | `test_stamp_targets_the_cd_worktree_not_active` | 1 failed | 1 passed |

W5 shipped early — module 1 implemented the design's "resolve via `_exec_wt_target`" step, so
its pin never went RED. The wire-scoped revert is what established the connection is enforced,
which is the property the pin exists to prove and which a RED could not have shown afterwards.

## What 6a-prime caught that nothing else did

`ASSESSMENT: WITH_FIXES` → fixed → re-run → `ASSESSMENT: READY_TO_MERGE`.

The `beat` stamp **hardcoded `running · 0m`**. A multi-hour dispatch would have reported `0m`
for its entire duration, defeating the single thing a heartbeat exists for. It passed:

- a 1055-green suite,
- a clean `ALL_CAUGHT` 5/5 mutation sweep,
- five wire-scoped reverts,

because AC-2.2's assertion was `values == sorted(values)` — and `[0, 0, 0]` is sorted. Minute
granularity was part of the cover: the field reads `0m` for the whole first minute, so no short
test could observe it advancing. Fixed by measuring from a dispatch-start marker and reporting
seconds below a minute; the test now also requires strict growth, and mutating the fix back to
the hardcoded form makes it fail.

This is the recorded pattern that every review layer reasons *inside* the pinned contract and
only 6a-prime looks outside it.

## Two vacuous tests I wrote and caught

Recorded because both would have shipped as coverage:

1. `HMAD_STUB_ORCA_RC` / `HMAD_STUB_CMUX_RC` did not exist in the stubs — the "every surface
   stubbed failing" test set env vars nothing read, so no surface failed. Knobs made real.
2. Even with real knobs, the test omitted `state=`, so the resolver had no payload and the
   stamp abandoned **before writing** — the write-failure path it existed to cover was never
   reached, and it passed with both guard layers mutated out. Adding `state=` made it
   discriminate (3 failed mutated / 3 passed restored).

The guard here is layered on purpose — `_exec_stamp` returns 0 internally *and* every call site
is `|| true` — so a single-layer mutation cannot falsify it; the check requires breaking both.

## Residual notes

- **6a-prime ran via `exec agy`, not a pane.** SKILL.md's 6a-prime mandates a pane preflight and
  would have recorded `archreview: SKIPPED_NO_PANE` (both pins are stale). `exec agy` is
  pane-independent and ran a real review that found a real defect, so recording a skip would
  have been false. Recorded as `READY_TO_MERGE` with this deviation stated.
- The stale codex/agy pane pins (`PREFLIGHT: FAIL stale=codex,agy`) were never repaired; the
  whole feature dispatched headless. That is the transport this feature is about.
