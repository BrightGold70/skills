# Handoff — `hmad-dispatch exec agy` does not return after agy finishes (waits to `--timeout`, rc=124)

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `45db0187-646a-4c8d-a8b6-4ba7af410d0f`
**Supersedes:** none — first brief on this issue

## Session Summary

During HemaSuite `#18 gateway-consolidation` Phase-4 design audits (29 dual-surface cycles on
2026-09-03), `hmad-dispatch exec agy … --timeout 1800` twice kept running for the full 30 minutes
**after** agy had finished its turn and written the report file: the `--log` ends with the
`{"event":"result",…}` JSON, the `<report>.done` marker exists within ~4 min, and the wrapper only
returns when its own `--timeout` kills the child (`hmad-dispatch: agy exec rc=124`). Codex on the
same runner exits normally every time. Intermittent: 2 of 29 cycles (c18, c29); the other 27 agy
execs returned in 3–5 min with rc=0. Ownership moves to this lane: it is a defect in
`h-mad/scripts/hmad-dispatch.sh`'s `exec agy` completion detection, not in HemaSuite.

## Key Learnings

- **Completion signal ≠ process exit for `agy --print`.** The transcript carries a terminal
  `result` event and the report-file transport carries a `.done` marker; the wrapper waits on
  neither — it waits on the pid. When agy 1.1.25 lingers after its result (cause unknown; the
  process is idle, no further log lines, `#hmad-beat agy running Ns` heartbeats continue), the
  caller pays the whole `--timeout`.
- **The report was never at risk** — both times the collected report gated fine. The cost is
  wall-clock only (30 min × 2) plus a misleading `rc=124` that a naive orchestrator would read
  as "no verdict" and re-dispatch (the HemaSuite runner was changed to poll the `.done` markers
  and reap the pids instead: `<scratchpad>/run_c2.sh`).
- **`tree delta: 3 changed`** printed by the timed-out exec is a red herring: the coordinator
  committed the collected reports while the child was lingering, so the post-exec tree snapshot
  differs from the pre-exec one. An exec that lingers past its work makes its own tree-delta
  check meaningless.

## Next Steps

1. Reproduce with the report-file slot filled: dispatch any audit prompt via
   `hmad-dispatch exec agy <prompt> --out <o> --log <l> --timeout 600` and watch for the
   `.done` marker appearing while `ps -p <pid>` is still alive. Intermittent — loop it; the two
   hits were the 18th and 29th of 29 identical dispatches in one session.
2. In `h-mad/scripts/hmad-dispatch.sh` `exec agy` (the `--print` path around `:2628`/`:2720`),
   treat **either** the `{"event":"result"…}` line on the transcript **or** the `<report>.done`
   marker (when a report-file slot is known to the wrapper) as completion: stop waiting on the
   pid, `TERM` the child, return rc=0 with the captured response. Keep `--timeout` as the ceiling
   for the no-signal case only.
3. Make the timed-out-but-report-delivered case distinguishable from a genuine timeout in the
   exit line — today both print `agy exec rc=124`. A coordinator gating on rc alone re-dispatches
   work that is already on disk.
4. Add the case to `h-mad/references/failure-recovery.md` beside the "`exec agy` loses the report
   to its own last message" entry (2026-08-01): this is the mirror — the report survives, the
   process does not exit.

## Open / Blocked Items

- **`exec agy` lingers after `result`** — status: handed over, not started. `repo:
  /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills` · evidence
  in the sender's scratchpad
  `/private/tmp/claude-501/-Users-kimhawk-orca-HemaSuite/45db0187-646a-4c8d-a8b6-4ba7af410d0f/scratchpad/`:
  `c18_status.txt`, `c29_status.txt` (START/PIDS/AGY_RC=124 at +30:02), `c{18,29}_agy.stdout`
  (`agy exec rc=124`), `audit_gc_design_c{18,29}_agy.log` (ends in the `result` event; 14
  heartbeat lines each), `audit_gc_design_c{18,29}_agy.report.md.done` (present), and
  `c28_status.txt` as the normal-exit control (AGY_RC=0 at +2:13). `agy --version` → 1.1.25.
- **No h-mad claim exists for this issue** in `docs/.bkit-memory.json` (checked: no record) —
  nothing to release; the receiver claims fresh.

## Context for Next Session

**Files touched this session (sender side, HemaSuite):** none in this repo. The sender's runner
workaround lives only in its scratchpad (`run_c2.sh`: poll both `.done` markers up to 1800 s,
then `pkill -TERM -P <pid>`).

**Uncommitted changes:** none from this brief.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
grep -n "agy exec rc=\|_cmd_exec\b\|--print" h-mad/scripts/hmad-dispatch.sh | head
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature exec-agy-hang-after-report --create --claim "<this session>"
```

**Related docs:**
- `h-mad/references/failure-recovery.md` — the 2026-08-01 `exec agy` report-loss entry (mirror case).
- HemaSuite `docs/handoffs/2026-09-03-main__hmad-audit-loop-root-causes.md` (in this store) — the
  earlier brief from the same feature; this one is a separate, narrower defect.
