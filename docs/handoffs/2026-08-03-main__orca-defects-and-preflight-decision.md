# Handoff — Two Orca defects written up, report-file transport live-verified, pre-flight decided against

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad` and `~/.claude/skills/handoff`)

## Session Summary

Resumed from `2026-08-03-main__agent-identity-and-await-correctness.md` and cleared all three of its
Next Steps. Three commits on `main` (`a816842`, `1d96cd6`, `1134192`), pushed, clean, in sync;
suites 1073 (was 1072) + 48. The headline is not the commits — it is that **both carried "clean
reproduction" premises were false when actually re-run**, and so was a claim in the bug report I
wrote from one of them. Nothing is blocked. The one thing deliberately left open is filing the two
bug docs upstream, which was the operator's call.

## Key Learnings

- **A parked "clean reproduction" is a claim, not evidence — re-run it before writing it up.**
  Twice this session a carried repro survived a handoff, a resume, and a write-up, and died in
  seconds to a control run. Both were mine, written the same day. The prior session was not sloppy;
  a repro is simply a hypothesis with a command attached, and only running it is measurement.
- **`worker-abandon` and `worker-stop` BOTH answer `dispatch_not_found` for a dispatch that
  `dispatch-show` returns as `status: dispatched`** — and that a second `dispatch --to` the same
  terminal refuses by name as "already has an active dispatch". Three commands, one runtime,
  seconds apart, two answers. The whole documented fencing path is unreachable for dispatches made
  by the low-level `orchestration dispatch` verb. The parked repro blamed
  `task-update --status ready`; a control with *nothing* between dispatch and abandon fails
  identically, so that attribution was wrong and the defect is broader than recorded.
- **`task-update --status completed` is the only working release.** It settles the dispatch
  (`status: completed`, `completed_at` stamped) and frees the terminal. `--status ready` does not —
  correctly, it is not a terminal state. So the only escape from a wedged pane records abandoned
  work as completed, which is exactly the provenance lie `worker-abandon` exists to prevent.
- **`terminal read`'s empty result is recoverable-forward.** The doc I wrote claimed the verb cannot
  see a live working pane's output. It can. Controlled comparison of the two restart-surviving panes,
  read seconds apart: codex (idle since restart) → 0 lines, cursors `"0"`/`"0"`; agy (written to
  since) → 61 lines, `14092` → `16092`. The buffer repopulates the moment new output arrives. The
  real defect is narrower: pre-restart scrollback is discarded and reported as an ordinary empty
  buffer, so only an *idle* restart-surviving pane is undiagnosable.
- **`dispatch --inject` into an agentless pane is refused ATOMICALLY.** Non-zero, stdout empty,
  error on stderr, and `dispatch-show --task` afterwards returns `dispatch: null` — no task row, no
  binding, nothing to clean up, pane free for a later dispatch. This is why J22 decided against a
  wrapper pre-flight: a check could only add a TOCTOU window, and would have to re-derive "is an
  agent here" from signals falsified above.
- **Give the transport e2e real work to do and it audits something for free.** The report-file
  live test carried an adversarial review of my own bug doc as its payload. Both findings were
  correct, and chasing the first one is what falsified the doc's central claim. A smoke-test payload
  would have proven the same transport and found nothing.
- **A 9-second gap made the `.done` marker rule visible.** agy wrote the report at 19:10:12 and the
  marker at 19:10:21; `report-wait` correctly polled through the window where the file existed
  unmarked. Existence-keyed transport would have read a possibly-partial file. Previously only the
  stub modelled this.
- **Mutation-test the CONTENT assertions, not just the guard.** Two of the five J22 mutations keep
  the exit code and stream routing correct and strip only the message text; both were caught, which
  is what proves the "names the terminal / cause / remedy" assertions carry the decision. A guard
  test that only asserts `returncode != 0` would have survived both.
- `orca terminal read` takes `--limit`, not `--lines` (the error helpfully suggests it). Minor, but
  the flag list in the error is the only place it is documented.

## Next Steps

1. **File the two bug docs upstream to `stablyai/orca`** — written, committed, deliberately not
   filed (operator chose docs-only this session). `gh` is authenticated as `BrightGold70` and the
   repo is public. Then stamp a `> Filed: <url> (<date>)` blockquote at the top of each, matching
   `docs/orca-feature-request-terminal-identity.md:3`.
   - `docs/orca-bug-worker-release-dispatch-not-found.md`
   - `docs/orca-bug-terminal-read-empty-after-restart.md`
2. **Optional, to sharpen bug (a):** run the positive control the report explicitly marks as
   unmeasured — does `worker-abandon` resolve a dispatch created by `worker-start` (which populates
   `launch_token_hash` / `capability_hash` / `process_incarnation`, all null on the failing rows)?
   Needs a live recognized agent in the target terminal; `worker-start --terminal` on a plain shell
   returns `agent_unconfigured`. If it resolves, the report's hypothesis is confirmed and the fix
   narrows to "widen the lookup or rename the error".

## Open / Blocked Items

- **Two Orca bug docs not filed upstream** — status: deliberate, not blocked. See Next Step 1. The
  docs are on `main` and pushed; only the GitHub issues and the `> Filed:` stamps are owed.
- **`worker-start` positive control for the abandon hypothesis** — status: deferred, not blocked.
  See Next Step 2. The report already states this was not measured rather than asserting a cause,
  so the write-up is honest without it.
- **An inbound handover marker landed mid-closeout and is UNCOMMITTED — not mine, deliberately left
  alone.** While this doc was being written, `docs/handoffs/2026-08-03-main__five-hmad-items-handover.md`
  gained a one-line `**Handover-From:** HemaSuite · feature/196-grounding-shadow-measurement ·
  session d185c497-29e4-4de0-ac43-d3770b39d1d0` under its `**Project:**` line — the machine-detectable
  marker that switches on READ's §"Take over handed-over work". A live HemaSuite session appears to be
  retrofitting it to a brief already addressed to this repo. I did **not** stage or commit it (a
  session's in-flight edit is not mine to land) and did **not** take the work over (that is a READ
  decision, made deliberately, not a side effect of closing out). Next session: it will show as a
  dirty file; `git diff` it, and if the marker is complete, that brief is now a claimable handover —
  go through READ Step 3.5 (claim via `h_mad_state_write.py --claim` after asking the oracle) rather
  than just working it.
- **Nothing else parked outside this repo.** No foreign-worktree items I own, so no HANDOVER was
  needed from here. The
  HemaSuite `feature/196` lane remains its own (`worktree ps` shows `Tasks 1-4 GREEN, Task 5
  unstarted`, brief at
  `docs/handoffs/2026-08-03-feature-196-grounding-shadow-measurement__task5-handover.md`); do not
  adopt it from here.

## Context for Next Session

**Files touched this session (all committed to `main`, pushed):**
- `docs/orca-bug-worker-release-dispatch-not-found.md` — **new** (`a816842`)
- `docs/orca-bug-terminal-read-empty-after-restart.md` — **new** (`a816842`), rewritten (`1d96cd6`)
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_dispatch` J22 decision comment only, no behaviour change
  (`1134192`); verified mechanically that every changed line is a comment
- `h-mad/tests/test_hmad_dispatch.py` — **new** `test_dispatch_surfaces_the_agentless_refusal_intact`
  (`1134192`)

**Uncommitted changes:** none (this handoff aside).

**Branches:** none local beyond `main`; `origin` carries `main` only.

**Orchestration probe state — already cleaned up, no action needed.** Three scratch terminals
created and closed (`REPRO-SCRATCH`, `-2`, `-3`, `PREFLIGHT-PROBE`); five probe tasks settled to
`completed` so no pane is left wedged. Run `run_1632386a175a` is still bound to this coordinator
pane. `hmad-dispatch env` → `PREFLIGHT: PASS`, pins intact (codex `term_7d59e6d2-…`,
agy `term_4d3f4261-…`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                                     # @ 1134192
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/scripts -q   # 1073 expected

# the coupled consumer suite — the symlink means this repo's HEAD is what it runs
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q         # 48 expected
```
A bare `python3` is homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3` for tests.
`timeout` does not exist on macOS (it is `gtimeout`); a command prefixed with it silently fails as
`command not found` while a surrounding `echo rc=$?` still prints 0.

**Reproducing the two Orca defects (both repros are in the docs, verbatim, and both were re-run
this session against Orca `appVersion` 1.4.164):**
```bash
orca status --json | jq -r '.result.runtime.appVersion'   # pin the version before quoting a repro
```

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-03-main__agent-identity-and-await-correctness.md`
- Filing precedent + house style: `docs/orca-feature-request-terminal-identity.md`
- Report-file transport spec: `h-mad/references/orchestration-mode.md:168`
- The version-matched Orca guide (ground truth for the command surface): `orca skills get orchestration`
