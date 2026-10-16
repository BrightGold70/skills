# agy-coder-fallback — 5d worktree state provisioning (decision)

**Date:** 2026-10-17 · **Decided by:** operator ("Main is right") after investigation
**Decision:** run every h-mad state op against the MAIN store; do NOT symlink the
worktree's `docs/.bkit-memory.json`.

## Rule for 5d/5e

- State ops: `--state /Users/kimhawk/orca/skills/docs/.bkit-memory.json` (explicit, always).
- Codex dispatch: `hmad-dispatch exec codex … --cd /Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`.
- The Claude orchestrator session stays rooted at `/Users/kimhawk/orca/skills` (`CLAUDE_PROJECT_DIR`).
  Never open the orchestrator in the worktree.

## Evidence

1. **Symlink self-destructs (measured, scratchpad fixture).** `h_mad_state_write.py:141`
   saves via `os.replace(tmp, state_file)` with `tmp` beside the path. Through a symlink it
   replaces the LINK with a regular file: after one `--claim probe-sid` via the link, the
   worktree file was `-rw-------` (no longer a link) with owner `probe-sid`, main owner
   `None`. Silent split; no error.
2. **Symlink double-reports lanes.** `h_mad_live_runs.py:41` / `h_mad_lane_liveness.py:34`
   read `docs/.bkit-memory.json` per lane, so an intact link shows one claim under two lanes.
3. **Main store + current Claude gate = fail closed for worktree writes (measured).**
   - `h_mad_tdd_judge.py state --root <main> --target <wt>/h-mad/scripts/h_mad_tdd_judge.py`
     → `TDD-STATE: active … record=agy-coder-fallback,available,<main>/docs/.bkit-memory.json`
   - `judge` same args → `TDD-JUDGE: DENY kind=no-test-resolved … name map: target outside root`
   - `state --root <wt>` → `TDD-STATE: none` (gate would ALLOW) — hence the orchestrator-root rule.
4. **Codex is ungated either way.** `~/.codex/hooks.json` has no TDD-gate entry; worktree has
   no `.codex/`. A symlink would not add Codex gating. 5d enforcement is the RED/GREEN verdict
   (`h_mad_extract_verdict.py`) + `h_mad_done_gate.py` + mutation harness, none of which read
   the state file.

## Residual

Codex writes have no hook in this repo (already noted in plan/spec). Unchanged by this decision.
