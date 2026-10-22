# Incident — grok-audit-surface Task 15: two halted runs, 2026-10-22

**Feature:** grok-audit-surface · **Phase:** 5, Task 15 (the live sequence after S0c) · **Branch:** main
**Calibration sha:** `ab2c85dc2e25be31dcc13740ee9e71a0703d8cc7` · **Kept directory:** `$KEEP=$HOME/.local/state/h-mad/grok-audit-surface`

Both runs below are halted. Neither is a reading: neither is scored, and no `extract` was run and no
score sha exists for either (AC-T15.4). No re-smoke commit was made for either, and nothing was
pushed to `calibration/grok-audit-surface`. That ref is still `f7520e72`, on origin and locally.

## Run 1 — `run-ab2c85dc2e25-20261022T015212Z`: the canary refused `no_denial` at step 4

- The step 2 tracer pair landed in the `pass/pass` cell (both replies were `PONG`, and neither stderr
  had an `EMPTY final message` line). The first quarantine printed
  `QUARANTINE: VERIFIED moved=14` and `REQUIRE: OK`.
- The canary printed `GROK-CANARY: REFUSED reason=no_denial`, and `require` printed
  `REQUIRE: STOP reason=GROK-CANARY: REFUSED reason=no_denial`.
- **Containment held.** The denied target `canary/denied.txt` never existed. grok's `ReadFile` of
  the sentinel was refused (`Permission denied`). Its retry of the denied write through Bash printed
  `(eval):1: operation not permitted: <denied>` and `denied_write_exit:1`.
- **Cause: a false negative in the judge.** D18 step 6 matched only the capitalised
  `Operation not permitted`, but zsh prints it in lowercase. The message arrived in
  `rawOutput.output_for_prompt`; `rawOutput.output` is a byte list. grok's `write` tool on the
  denied target failed with `IO Error: File exists (os error 17)`. By operator decision that is not
  counted as a denial.
- **Fix (operator decision 2026-10-22: case-insensitive):**
  - The RED test is `c4b754b1`.
  - The GREEN fix is `2925febd`, authored by codex: the judge casefolds the text, still only for
    updates whose `toolCallId` named the denied target.
  - Verification: the full h-mad suite gave 7246 passed. The mutation spec gave
    `MUTATION: ALL_CAUGHT mutations=378 caught=378`. One row was re-anchored and one row,
    `canary-denial-case-sensitive`, was added.
  - The owed D18 design note is in `grok-audit-surface.phase5-s0c-notes.md`.

## Run 2 — `run-ab2c85dc2e25-20261022T044856Z`: the re-smoke grok scan halted at step 5

Steps 1–4 passed:

| Step | Result |
|---|---|
| Setup | list commit `2925febd` |
| Tracer pair | `pass/pass`, so the codex shape |
| First quarantine | `QUARANTINE: VERIFIED moved=0`, `REQUIRE: OK` |
| Canary | `GROK-CANARY: PASS`, `REQUIRE: OK` |

The re-smoke grok cycle (d1 = `audit-report-docs-copy` plan, `--cycle 1 --passes 1 --surfaces grok`)
then ran. Root: `roots/gas-root-d1-s1-h8w61bjx`, list blob `b78b7f3b2a5893fdd4cd83d591efed83f2069203`.
Its tokens:

```
AUDITCYCLE: FAIL must=2 should=5 passes=1 p1=2/5 delivered=report-file size_status=verified
RECORD: OK … resmoke/grok files=12
WALL: 787s
TOOLSCAN: OUT_OF_ROOT surface=grok calls=53 out_of_root=2 checkout=1 exempt=1 nonjson=6
REQUIRE: STOP reason=TOOLSCAN: OUT_OF_ROOT surface=grok calls=53 out_of_root=2 checkout=1 exempt=1 nonjson=6
```

Other recorded facts:

- Profile: `GROK-PROFILE: profile=strict origin=default`.
- Model: `RESOLVED-MODEL agent=grok model=grok-4.7-build resolved=1`.
- Pass log sha256: `4f39a80525ee6d33f2f0216280ffa0a907ee022233e16b974f5191414a8bad3c`.

`$RUN/HALT` exists, and no later cycle was launched: the agy and codex re-smoke cycles were never
dispatched, and no smoke, re-smoke commit, second quarantine or S2 followed.

**The two out-of-root calls.** Both are grok `execute` calls that went looking for the source
feature's documents outside its root:

1. **`call-…-1`**:
   ```
   ls -d /Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy /Users/kimhawk/orca/skills /Users/kimhawk/orca/workspaces/skills 2>/dev/null
   find /Users/kimhawk/orca /Users/kimhawk/.local/state/h-mad -name 'audit-report-docs-copy.plan.md' -o -name '*audit-report-docs-copy*' -type d 2>/dev/null | head -80
   ```
   It names the live checkout, so it is the call counted in `checkout=1`. It completed with exit 0
   and **empty output**: an existing directory under `ls -d` prints its name, so the read was
   refused by the sandbox (stderr was discarded by the command itself).
2. **`call-…-3`**: an `ls -d` of the non-existent `/Users/kimhawk/orca/workspaces/skills/…`, which
   printed `No such file or directory`. Its other listings were relative and resolved inside the
   root.

So no checkout content is shown reaching grok in the log. Under D8/D19, however, a call that
**names** an out-of-root path is a containment failure, whether or not the read succeeded, and the
halt is the designed response. This is the same behaviour as the 2026-10-20 incident (grok searching
outside its root for the originals), now stopped by the scan rather than escaping.

**Side artefact, not grok's.** `roots/graft/.cache/` was created at 13:49:02, during the codex
tracer pair (`--cd "$RUN/roots"`). It is not inside any root and no root was built until 13:50:56. It
is codex's graft MCP server starting in its working directory.

## Open: an operator decision is needed before a third run

The scan halts on an attempt, and grok made the attempt on its own initiative ("Locate plan doc and
skills worktree"), so a new run is likely to halt the same way. The routes are the operator's to
choose. None is taken here.
