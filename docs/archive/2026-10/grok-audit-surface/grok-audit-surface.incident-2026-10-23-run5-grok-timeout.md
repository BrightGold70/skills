# grok-audit-surface — run 5 incident: the smoke failed when grok's re-smoke hit the 900 s default

**Date:** 2026-10-23 · **Run:** `/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261023T070009Z` (kept; never committed; never scored)
**Checkout sha at run:** `dbf92b17` (Tasks 14e and 14f landed) · **Status:** stopped at step 6; nothing was pushed for this run.

## What ran (Task 15, impl-plan v1.13; driver `run5-all.sh`)

| Step | Token |
|---|---|
| 1–4 | `SETUP: OK … list_sha=dbf92b17…`, `D16: cell=pass/pass`, `QUARANTINE: VERIFIED moved=2` → `REQUIRE: OK`, `GROK-CANARY: PASS` → `REQUIRE: OK` |
| 5 assembler start | `ASSEMBLER-READING: sha=dbf92b17… dirty=no` |
| 5 grok re-smoke | `AUDITCYCLE: UNVERIFIED reason=no_report:p1 delivered=none`; stderr `grok exec rc=124 (timeout)`; wall 909 s; `TOOLSCAN: CLEAN calls=61 out_of_root=0 checkout=0` → `REQUIRE: OK`; `RESOLVED-MODEL: UNKNOWN` (the log has no `end` event) |
| 5 agy re-smoke | `AUDITCYCLE: FAIL must=2 should=2 delivered=out`; Gemini 4 Argon (Medium) |
| 5 codex re-smoke | `AUDITCYCLE: FAIL must=2 should=0 delivered=report-file`; gpt-6-luna, effort high |
| 6 smoke | `ROOT-ACCEPT: grok=refused agy=accepted codex=accepted`; `TIMEOUT: wall_seconds=909 derived=1380`; **`SMOKE: FAIL reason=truncated,vocab_missing:end,no_delivery,nongit_root_refused:grok`** |

## Cause

The re-smoke `audit-cycle` passed no `--timeout` (design D8: "The re-smoke omits `--timeout`, so the wrapper default of 900 s applies"). The wrapper default is `timeout="900"` in `_cmd_audit_cycle`.

Grok's d1 audit pass needed longer than 900 s. It was killed mid-thought: the last log lines are `thought` events, and the log has no `end` event. Spec AC-1.1 makes a `grok-truncated` reading a smoke failure that is not retried, so the smoke result is correct under the documents as written.

The recorded grok d1 re-smoke walls are 678 s (run 3), 863 s (run 4) and over 900 s (run 5). The measurement straddles the cap. `nongit_root_refused:grok` follows from `no_delivery` and does not show that grok refused the root.

## Decision (operator, 2026-10-23)

The documents are amended (design v1.17, spec v1.22, impl-plan v1.14). The re-smoke passes `--timeout 1800` on every cycle, so it **measures** grok's wall time instead of clipping it. 900 s stays the floor of AC-1.4's derived S2 timeout and is no longer a pass/fail bar for the smoke.

Run 6 runs in a new run directory. Nothing from run 5 goes to the calibration branch.
