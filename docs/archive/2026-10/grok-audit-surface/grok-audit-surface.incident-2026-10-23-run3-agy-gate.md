# grok-audit-surface — run 3 incident: the agy re-smoke leg was denied by h-mad's own agy Phase-5 hook

**Date:** 2026-10-23 · **Run:** `/Users/kimhawk/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261022T222714Z` (kept, never committed, never scored)
**Checkout sha at run:** `e3629604` (Tasks 14a–14d landed) · **Status:** incident evidence; halted before step 6b/7.

## What ran (Task 15, impl-plan v1.11)

| Step | Token |
|---|---|
| 1 Setup | `SETUP: OK run=run-ab2c85dc2e25-20261022T222714Z` |
| 2 codex tracer pair | `D16: cell=pass/pass shape=codex` |
| 3 quarantine | `QUARANTINE: VERIFIED moved=1` → `REQUIRE: OK` |
| 4 canary | `GROK-CANARY: PASS` → `REQUIRE: OK` |
| 5 assembler start | `ASSEMBLER-READING: sha=e3629604… dirty=no script_dir_env=unset here=…/h-mad/scripts` |
| 5 grok re-smoke | `AUDITCYCLE: FAIL must=4 should=1`; `TOOLSCAN: CLEAN surface=grok calls=49 out_of_root=0 checkout=0 exempt=0 nonjson=5` → `REQUIRE: OK`; wall 678 s; model grok-4.7-build |
| 5 agy re-smoke | `AUDITCYCLE: UNVERIFIED reason=unscorable_report:p1 … delivered=unscorable:zero-evidence`; model Gemini 4 Argon (Medium) |
| 5 codex re-smoke | `AUDITCYCLE: FAIL must=4 should=0`; model gpt-6-luna, effort high |
| 6 smoke | `ROOT-ACCEPT: grok=accepted agy=refused codex=accepted`; `SMOKE: FAIL reason=nongit_root_refused:agy` |

## Finding 1 — route (b) works for grok

Run 2 halted on `TOOLSCAN: OUT_OF_ROOT … out_of_root=2 checkout=1`. Run 3, with the Task 14a–14c
path-scope clause in grok's prompt, scanned `out_of_root=0 checkout=0`. One run, one doc (d1/s1):
evidence for the ruling, not yet a calibration reading.

## Finding 2 — the smoke FAIL is an artifact of h-mad's own gate

Every agy tool call in `resmoke/agy/p1.log` was refused with
`tool call denied by pre-tool hook: Gate could not reach a judgement. kind=judge-error` (6 occurrences).
The agy Phase-5 TDD hook (`h-mad/hooks/h-mad-agy-tdd-gate.py`, wired globally for agy) is armed because
this feature's record is `phase=step5`, and in the non-git calibration root under `$RUN/roots/` it
cannot reach a judgement, so it fails closed. The probe's smoke reads the resulting empty, zero-evidence
agy pass as "agy refuses a non-git root" (`nongit_root_refused:agy`). That is a statement about our
gate, not about agy. The plan's smoke-failure branch (assembler end/check, commit the reading, Task 16
publishes) was therefore NOT taken: it would publish a contaminated reading. Nothing was committed to
`calibration/grok-audit-surface`; no assembler end reading was taken.

## Open decision for the next session (operator)

Task 15 runs live agy cycles while Phase 5 is armed for the same feature, and no document reconciles the
two. Candidate resolutions, none chosen:
1. The agy gate stands down for paths outside the project root (calibration roots live under
   `~/.local/state/h-mad/`), as the Claude gate does for a target outside its root.
2. A sanctioned, recorded disarm window for Task 15's live cycles (the skill forbids `phase=null`
   before 5g, so this needs an explicit rule, not an ad-hoc flip).
3. Run Task 15 from a state where this feature is not `step5` (sequence change in the impl-plan).

Run 2's grok STOP happened before its agy cycle, so this is the first run in which the agy leg met the
armed gate. Run 3's directory is kept as evidence; a new run directory is required after the fix.

## Addendum 2026-10-23 (next session): the cause is not `phase=step5`

Finding 2's "armed because this feature's record is `phase=step5`" is **false**. The two resolutions that
depend on it, 2 (disarm window) and 3 (resequence out of `step5`), cannot fix run 4.

- **Where the hook comes from.** The hook is wired per project, not globally:
  `~/.gemini/config/hooks.json` has no tdd-gate entry. `.agents/hooks.json` is tracked (since
  `f3233797`), so `git archive` copies it into every calibration root.
- **Why it denies in every phase.** agy runs the hook with cwd `$ROOT/.agents`. The gate then runs
  `git -C <cwd>.parent rev-parse --show-toplevel` (`h-mad/hooks/h-mad-agy-tdd-gate.py:104`) before it
  reads any phase. The root is non-git by design (`reach_check`), so the call raises, and the `finally`
  block denies with `kind=judge-error`. This happens for every class except (a), which returns `allow`
  before the lookup.
- **Reproduction.** From `$ROOT/.agents`, `read_file` gives
  `{"decision": "deny", "reason": "Gate could not reach a judgement. kind=judge-error"}` and
  `view_file` gives `{"decision": "allow"}`. From `/tmp`, with no h-mad state at all, the result is the
  same deny.
- **Why S1 passed and run 3 failed.** Both used the same gate, the same tree (`ab2c85dc`) and the same
  model (Gemini 4 Argon (Medium)). S1's agy read with `view_file` (40 DONE, plus 1 `run_command` and
  1 `write_to_file` denied). Run 3's agy read with `read_file` (5 denied, plus 1 `run_command` denied).
- **What `read_file` is.** It is absent from agy's advertised init inventory (60 names), but agy
  executes it as a read-only tool: about 1233 DONE steps answer `Showing lines a-b of n`. The old S2
  data, dated 2026-10-20 and kept only as evidence, already carries the same `read_file` denials.

Remedy ordered by the operator (option A): impl-plan Task 14e (v1.12) adds `read_file` to the gate's
class (a). Open policy, not decided here: whether the gate should deny or allow a call when no git
toplevel exists.
