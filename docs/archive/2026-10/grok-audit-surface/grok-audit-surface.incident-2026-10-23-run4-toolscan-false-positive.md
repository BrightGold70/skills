# grok-audit-surface — run 4 incident: S2 halted at d2 on a TOOLSCAN false positive

**Date:** 2026-10-23 · **Run:** `/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261023T034641Z` (kept, never scored)
**Checkout sha at run:** `d8598290` (Task 14e landed) · **Smoke commit:** `b1562dd4` on `calibration/grok-audit-surface`
**Status:** incident evidence. The run halted in step 9 (S2), after the d2 cycle. Steps 9a, 10 and 11 were not run.

## What ran (Task 15, impl-plan v1.12)

| Step | Token |
|---|---|
| 1 Setup | `SETUP: OK run=run-ab2c85dc2e25-20261023T034641Z list_sha=d8598290…` (`list_blob=b78b7f3b`, the same blob as S1) |
| 2 codex tracer pair | `D16: cell=pass/pass shape=codex` |
| 3 quarantine | `QUARANTINE: VERIFIED moved=1` → `REQUIRE: OK` |
| 4 canary | `GROK-CANARY: PASS` → `REQUIRE: OK` |
| 5 assembler start | `ASSEMBLER-READING: sha=d8598290… dirty=no script_dir_env=unset` |
| 5 grok re-smoke | `AUDITCYCLE: FAIL must=4 should=4`; `TOOLSCAN: CLEAN surface=grok calls=52 out_of_root=0 checkout=0`; `REQUIRE: OK`; wall 863 s; grok-4.7-build |
| 5 agy re-smoke | `AUDITCYCLE: FAIL must=2 should=0 delivered=out`; 24 `read_file` DONE (run 3: 0 of 5); Gemini 4 Argon (Medium) |
| 5 codex re-smoke | `AUDITCYCLE: FAIL must=2 should=0`; gpt-6-luna, effort high |
| 6 smoke | `ROOT-ACCEPT: grok=accepted agy=accepted codex=accepted`; `TIMEOUT: wall_seconds=863 derived=1320`; **`SMOKE: PASS`** |
| 7 re-smoke commit | `COMMIT: OK sha=b1562dd4…` (parent `f7520e72`), pushed and confirmed with `ls-remote` |
| 8 second quarantine | `QUARANTINE: VERIFIED moved=1` → `REQUIRE: OK` |
| 9 S2 d1 v1 | `AUDITCYCLE: FAIL must=3 should=9 passes=3 delivered=report-file,out,report-file`; `TOOLSCAN: CLEAN calls=51 out_of_root=0 checkout=0 exempt=3`; `REQUIRE: OK` |
| 9 S2 d2 v1 | `AUDITCYCLE: FAIL must=11 should=4 passes=3 … size_status=unverified`; **`TOOLSCAN: OUT_OF_ROOT surface=grok calls=58 out_of_root=1 checkout=0 exempt=1`** → `REQUIRE: STOP` → `$RUN/HALT` |

Driver: `~/.local/state/h-mad/grok-audit-surface/s2-run4.sh`. It is the step-9 recipe: one `build-root --purpose s2v1` per pass, `--pass-root` ×3, and `--timeout 1320`.

## Finding 1: Task 14e works live

agy read the calibration root with `read_file`, and this run's smoke passed where run 3's failed with `nongit_root_refused:agy`. The agy gate still denies `run_command` and `write_file` there; the policy question (deny or allow when there is no git toplevel) is open. So agy delivers through `out` and not through a report file.

## Finding 2: the d2 halt is a false positive of the out-of-root scan

The one `out` path is `/opt/anaconda3`. It occurs only in a `grep` tool call (`p3.log:3282`):

```
{"toolName":"grep","rawInput":{"pattern":"python3\\.11|/opt/anaconda3","glob":"**/test_h_mad_audit_cycle.py","head_limit":15}}
```

The call has no path argument, so it searches the cwd, which is the root. `/opt/anaconda3` is part of the regex grok searched for; grok did not access it.

`named_paths` (`h-mad/scripts/h_mad_tool_calls.py:24-43`) takes every string argument of a call. The `|` in the pattern is in the lookbehind class, so the regex then extracts `/opt/anaconda3` as a path. Reproduced in process:

- `_strings(rawInput)` returns `['python3\\.11|/opt/anaconda3', '**/test_h_mad_audit_cycle.py']`.
- `named_paths` then returns `['/opt/anaconda3']`, and `classify_path` returns `out`.

The plan's rule still applies: `REQUIRE: STOP` halts the run, the run is not scored, and only a new run is a reading. Nothing past the d2 cycle was dispatched. The d1 and d2 readings stay under `$READING/s2/` as evidence and were not committed to the calibration branch.

## Open decision (operator)

The scan is a measurement instrument, and it read a search pattern as an access. The candidate remedies are:

1. **Fix the scan through TDD** (a new Task 14f). The search tools' `pattern` argument would stop being a path source, while a search's real path or glob arguments stay scanned. The positive control (step 10) must still read `checkout>0` after the fix. Then run 5 starts in a new run dir.
2. **Keep the scan conservative.** Accept that a pattern naming an outside path halts the run, and only re-run. This is not recommended: the false positive can recur on any document that cites a path outside the root.

The smoke commit `b1562dd4` stays on the calibration branch. A new run makes and pushes its own re-smoke commit on top.

**Decision (operator, 2026-10-23): remedy 1.** Impl-plan Task 14f (v1.13) excludes only the `pattern` argument of a grok `grep` call. A path inside shell text (`run_terminal_command`) is still scanned as-is and is recorded as a residual. Run 5 starts in a new run dir after 14f lands.
