# Handoff — headless dispatch visibility: live streams, `progress`, and `exec-pane`

**Date:** 2026-08-19
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Made h-mad's headless `exec` dispatches watchable while they run. Shipped in seven commits
(`e78b46a`..`1dd7983`, all pushed): `exec agy` now streams NDJSON to `--log` instead of emitting
nothing until exit; a new `hmad-dispatch progress <log>` verb gives a bounded, non-blocking digest;
a new `hmad-dispatch exec-pane` verb runs a dispatch inside a visible Orca zsh pane, pooling and
reusing one pane per worktree; and `--wait` latency dropped from a 2s poll to 0.5s. **Done** —
1349 tests pass, every new guard mutation-tested, and both verbs verified live end to end against
real Orca, real agy, and real codex. Also closed an inbound handover brief that had been sitting
untracked in this repo all session: its premise was already false when written.

## Key Learnings

- **The two backends were never equally blind, and the docs said they were.** `codex exec` wrote its
  transcript to `--log` live all along (measured: 811 → 1446 bytes mid-run). `agy --print` in text
  mode emits *nothing* until the turn completes, and the wrapper captured it to a temp file and only
  appended to `--log` at exit — so agy's log held **zero bytes for the entire run**. `agy
  --output-format stream-json` is the only live channel; `--log-file` is language-server noise
  (auth/gRPC traces) with no step information.
- **`orca terminal wait --for exit` does not carry the command's exit code.** A pane running
  `sleep 2; exit 9` reports `{"satisfied":true,"status":"exited","exitCode":0}`. Anything built on it
  reads every failure as success. It also has no usable completion shape either way: end the command
  with `exit` and the shell dies (code still wrong, scrollback lost); return to a prompt and it times
  out because the shell is alive. Capture rc from the command itself.
- **A tab title cannot mark pane state.** zsh emits an OSC title sequence at every prompt, so a pane
  renamed to `h-mad slot · idle` reads back as `~/orca/skills` the moment it reaches a prompt.
  Verified before building on it. Slot state has to live in files.
- **`ORCA_TERMINAL_HANDLE` is set inside a pane created by `terminal create`**, which is what lets a
  pane register and release its own pool slot — and what makes `--split` with no value mean "this
  terminal" unambiguously.
- **A pane running `exec` bare is blind.** `exec` redirects the stream into `--log`, so the pane
  shows the echoed command and nothing else until the run ends (measured: t+14s, one line in the
  pane, three events in the log). The pane must digest the log itself. `tail -f` is right *there* and
  nowhere else — it never returns, so an orchestrating agent cannot use it.
- **The perceived result latency was self-inflicted.** `exec` returns within ~1s of the agent
  producing its result (measured: result t+23.44s, `exec` returned t+24.43s). The delay was the
  waiting: a 2s rc poll plus a documented 30–60s orchestrator `progress` cadence. Backgrounding the
  blocking form so the harness re-invokes on exit is a completion *signal*, not a poll.
- **A multi-edit script that writes once at the end loses its *successful* edits when a later one
  raises.** One block did four SKILL.md replacements and died on edit 2; edit 1 was discarded with
  it, and the follow-up repaired only what visibly failed. Net: `exec-pane` shipped undocumented for
  a commit. The traceback names the one edit you don't need told about.
- **A static test stub cannot express "alive when the wait began, dead before it ended."** Two pool
  mutants survived behind exactly that gap; the fix was a stub reading liveness from a file the test
  rewrites mid-run. One of them was a real bug — a "the pane died, stop waiting" check consulting a
  handle list captured once before the loop.

## Next Steps

1. Re-run a real H-MAD audit phase through the new transport to confirm nothing regressed in
   anger — `hmad-dispatch exec-pane agy <audit-prompt> --out <o> --wait` from a HemaSuite feature,
   then extract with `h_mad_extract_verdict.py`.
2. `[suggested]` Consider teaching `references/failure-recovery.md`'s `<phase>:no_verdict` row to
   name `exec-pane` alongside `exec` — it currently points only at `hmad-dispatch progress <log>`.
   File: `h-mad/references/failure-recovery.md:45`.
3. `[suggested]` The `docs/skill-candidates.md` backlog was not reconciled this session
   (`--skip-scout` was not set, but the scout phase found no new candidates worth appending; the
   existing open rows are untouched and may be stale). Worth a pass next session.

## Open / Blocked Items

- **Inbound handover brief — CLOSED this session, no fix was needed.**
  `docs/handoffs/2026-08-19-main__hmad-dispatch-exec-agy-flag-order.md` (from HemaSuite ·
  `feature/71-run-report-seam-restoration` · session `679a9622`) claimed `exec agy` passed
  `--print` before its boolean flags. It did not, and had not: at `00fbff4` — this repo's HEAD
  *before* any of today's work — the agy branch already built `args=(--dangerously-skip-permissions)`
  first and appended `--print "$prompt"` last. Its Next Steps 1 and 2 needed no action (`--cd` also
  verified working live, `PROBE_OK`); Step 3's requested argv guard was delivered incidentally this
  session as `h-mad/tests/test_hmad_dispatch_progress.py:82`. **No h-mad claim existed**, so none was
  released. The brief's real observation (`rc=124`, 0-byte `--log`) is separately explained by the
  text-mode blindness this session fixed, and is not a flag bug.
- **Step 4 of that brief — routed to HemaSuite.** "Cross out the corresponding HemaSuite todo" is
  their item, not this repo's. Closure brief written to
  `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-19-main__exec-agy-flag-order-closed-no-fix-needed.md`.
  Deliberately **not** committed, pushed, or delivered to an agent lane there — HemaSuite has `#71`
  in flight and an unrequested commit or spawned worktree would be an outward action nobody asked
  for. repo: `/Users/kimhawk/orca/HemaSuite` · branch: `main` · worktree: none.
- **One mutant left alive on purpose.** Removing the `.finishing` entry condition in
  `_cmd_exec_pane`'s reuse wait changes behaviour by ~0.2s, because the loop's own give-up check
  catches the same case on the first tick. Kept for clarity and to avoid a pointless sleep — not
  because a test can distinguish it. Recorded rather than papered over with a contrived assertion.
- **Not verified:** none of this has been exercised by an actual gated H-MAD phase yet (Next Step 1).
  All live verification was purpose-built probes.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — `_agy_ndjson_response`, `_exec_log_format`, `_exec_log_age`,
  `_render_progress`, `_cmd_progress`, `_cmd_exec_pane`, `_pane_slot_*`, `_shq`, `_self_path`
- `h-mad/SKILL.md` — §"Watching a headless dispatch", §"Making a dispatch visible in Orca (zsh shell pane)"
- `h-mad/references/failure-recovery.md`, `h-mad/references/codex-verifier-prompt.md`,
  `h-mad/references/agy-skill-reviewer-prompt.md`
- `h-mad/tests/test_hmad_dispatch_progress.py` (new), `h-mad/tests/test_hmad_dispatch_exec_pane.py` (new),
  `h-mad/tests/test_h_mad_pane_visible_dispatch_docs.py` (new),
  `h-mad/tests/test_hmad_dispatch_exec.py`, `h-mad/tests/stubs/agy`

**Uncommitted changes:** none in tracked files. One untracked file remains by design:
`docs/handoffs/2026-08-19-main__hmad-dispatch-exec-agy-flag-order.md` (the inbound brief, closed
above) — committed together with this handoff.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                   # in sync with origin/main at 1dd7983
cd h-mad && python3.11 -m pytest tests/ -q          # 1349 passed, ~3min
```

**New commands this session:**
```bash
hmad-dispatch progress <log> [--lines n] [--pid p]          # bounded, non-blocking; NEVER tail -f
hmad-dispatch exec-pane agy <prompt> --out <o> --split      # this surface
hmad-dispatch exec-pane agy <prompt> --out <o> --wait       # drop-in for `exec`
```

**Related docs:**
- `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e", §"Watching a headless dispatch",
  §"Making a dispatch visible in Orca (zsh shell pane)"
- Closure brief sent to HemaSuite (above)
- Commits: `e78b46a` `aac66fb` `54d909c` `6428cd1` `739f990` `d29f37e` `83d0a33` `1dd7983`
