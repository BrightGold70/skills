# grok-audit-surface — run 6 incident: S2 halted at d3 on a TOOLSCAN false positive (write.content)

**Date:** 2026-10-23 · **Run:** `/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261023T081135Z` (kept, never scored)
**Checkout sha at run:** `a805f07b` (Tasks 14e and 14f, re-smoke `--timeout 1800`) · **Smoke commit:** `533ed0c5` (parent `b1562dd4`) on `calibration/grok-audit-surface`
**Status:** incident evidence. Step 9 halted after the d3 cycle; 9a, 10 and 11 were not run.

## What ran (driver `run6-all.sh`, impl-plan v1.14)

| Step | Token |
|---|---|
| 1–4 | `SETUP: OK … list_sha=a805f07b…`; `D16: cell=pass/pass`; `QUARANTINE: VERIFIED` → `REQUIRE: OK`; `GROK-CANARY: PASS` → `REQUIRE: OK` |
| 5 | `ASSEMBLER-READING: sha=a805f07b… dirty=no` |
| 5 grok | `AUDITCYCLE: FAIL must=2 should=4 delivered=report-file`; wall 745 s; `TOOLSCAN: CLEAN calls=55 out_of_root=0` |
| 5 agy | `AUDITCYCLE: FAIL must=3 should=2 delivered=out` |
| 5 codex | `AUDITCYCLE: FAIL must=4 should=1 delivered=report-file` |
| 6 | `ROOT-ACCEPT: grok=accepted agy=accepted codex=accepted`; `TIMEOUT: wall_seconds=745 derived=1140`; **`SMOKE: PASS`** |
| 7 | `COMMIT: OK sha=533ed0c5…`, pushed and confirmed |
| 8 | `QUARANTINE: VERIFIED moved=1` → `REQUIRE: OK` |
| 9 d1 v1 | `AUDITCYCLE: FAIL must=8 should=6 passes=3`; 808 s; `TOOLSCAN: CLEAN calls=40` |
| 9 d2 v1 | `AUDITCYCLE: FAIL must=10 should=3 passes=3`; 1007 s; `TOOLSCAN: CLEAN calls=69` |
| 9 d3 v1 | `AUDITCYCLE: FAIL must=8 should=3 passes=3`; 840 s; **`TOOLSCAN: OUT_OF_ROOT calls=64 out_of_root=1 checkout=0`** → `REQUIRE: STOP` |

## Cause: the same class as run 4

The one `out` path is `/tmp/audit_`, at `p3.log:4269`, in a grok `write` call. That call's `file_path` is inside the root: `.hmad-report/audit_…_p3.report.md`, which is grok's own report. The `/tmp/audit_` string comes from its `content`, the report prose, which discusses the audited impl-plan's `/tmp` paths. Grok wrote a file inside the root; it accessed nothing outside it.

Task 14f excluded only `grep.pattern`. The scanner still reads every other string argument as a possible path, including payloads, which are text the tool writes or searches for rather than a location it touches.

A census of every recorded grok log by argument key found payload-key hits on `write.content` (19), `grep.pattern` (5), `search_replace.old_string` (1) and `search_replace.new_string` (1). The census used a rough per-log root heuristic, so its counts for the real path keys are not reliable.

## Decision (operator, 2026-10-23)

Task 14g (impl-plan v1.15) replaces 14f's single exclusion with a named per-tool table of grok payload arguments: `grep.pattern`, `write.content`, `search_replace.old_string` and `search_replace.new_string`. Every path argument, `run_terminal_command.command` and every argument of an unknown tool are still scanned.

Before run 7, every recorded grok S1, re-smoke and S2 log is re-scanned with the old and the new scanner. Any newly CLEAN log must owe its change to a payload argument only, and the positive control must still read `checkout>0`.
