# Handoff — Task 3 verify + dispatch-transport live validation

**Date:** 2026-07-29
**Branch:** main
**Project:** orca/skills (h-mad skill)

## Session Summary

Resumed from the 2026-07-28 j17 handoff and cleared all three restored todos. **Task 3** (`synopsis-authoritative-registry`, notebook resolution order) turned out to be already merged to `main` via `feature/191` since that handoff was written, so the owed work was verification-only — ran the full 5e verify against merged code (25 module / 7819 full, 0 failures, 4 properties confirmed, anti-gaming clean). Then live-validated the h-mad dispatch transports end-to-end: **exec-default** (`codex` + `agy exec --log`) and the **pane path** (`--after-marker` boundary-echo). All green. Two doc commits pushed; no production code touched this session.

## Key Learnings

- **A handoff's "parked, nothing committed" can be stale by the next session.** Task 3 was described as parked in its own worktree; in reality `feature/191` had merged to `main`, so the fix was live and only verification remained. Always reconcile the branch/merge state before assuming parked work is unstarted.
- **The dispatch transport faithfully carries a wrong verdict.** A real `codex exec` returned `STATUS: DONE` while miscounting (said 21 tests, actual 28). Exit 0 + a STATUS line never means correct work — the extractor carries the token, it cannot judge truth. Always grep the real numbers the agent quoted. (Reproduces the J17 discipline live.)
- **The J17 false-DONE is real and the guard neutralizes it — proven by reconstruction.** Silent-pane buffer (echoed contract `STATUS: DONE` + boundary, no answer): without `--after-marker` → `STATUS: DONE` rc=0 (the bug); with `--after-marker` → rc=2 "no verdict" (fails closed). Boundary absent → rc=2.
- **Boundary round-trips into a real agent pane.** Read-only scrape of live pane `term_cc1ac309` showed 6 genuine `===HMAD-DISPATCH-BOUNDARY===` echoes with the agent's response rendering after the last one — (B) confirmed without sending anything into a user pane.
- **Never hijack a user's live Orca pane.** Several live panes held the user's active agents (HemaSuite codex, a Gemini prompt, a beaming Task-3 pane — the last was *this* session surfaced in Orca). Validation used read-only pane reads + reconstructed buffers + throwaway read-only `exec` only.
- **`codex exec --log` streams truly live (33→564 lines mid-run); `agy exec --log` buffers** (`--print` lands the response together at the end). Both preserve exit code (direct redirect, not a pipe).
- **`orca terminal read` JSON shape:** lines are at `.result.terminal.tail[]` (not `.rows[]`), read-only, `--limit <n>` pulls more retained scrollback.

## Next Steps

1. `wait --not-while-regex 'Waiting for background terminal'` false-idle guard was NOT live-exercised this session (only the boundary-echo/`--after-marker` half of J17). Exercise it on a real pane dispatch that delegates to a background terminal — `h-mad/SKILL.md` §"Reading a dispatch verdict".
2. `docs/skill-candidates.md` row **hmad-5e-verify-recipe** is `candidate: yes` — promote to a real skill/checklist when convenient; the `codex_task3_verify.txt` prompt (in a HemaSuite scratchpad) is its template.
3. [suggested] On the next real feature 5d/5e, use exec-default for the one-shot and confirm the content-crosscheck habit (grep the agent's quoted numbers) becomes routine, per the new `docs/learnings.md` gotcha.

## Open / Blocked Items

- `wait` false-idle guard (`--not-while-regex`) — status: not yet live-validated (deferred; needs a background-terminal-delegating pane dispatch). Not blocking — unit-tested in `test_hmad_dispatch.py`.

## Context for Next Session

**Files touched this session:**
- `docs/learnings.md` — 2 entries (commit `82438ca`)
- `docs/skill-candidates.md` — scout entry (commit `10168f9`)
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/feedback_hmad_dispatch_verdict_echo_and_idle.md` — live-validation reinforcement (user-global, not in repo)

No production code changed. Task 3's shipped code lives on `main` (merged via `feature/191`): `engine/_ko_notebooks.py`, `tests/test__ko_notebooks.py` in `HemaSuite/hematology-paper-writer`.

**Uncommitted changes:** none (both doc commits pushed; local `main` = `origin/main` `10168f9`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# exec transport: h-mad/SKILL.md §"Exit-code dispatch for 5d/5e"
# pane verdict:   h-mad/SKILL.md §"Reading a dispatch verdict"
```

**Related docs:**
- `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e" and §"Reading a dispatch verdict"
- Prior handoff: `docs/handoffs/2026-07-28-main__j17-dispatch-verdict-guard.md`
- Task 3 verify template: `codex_task3_verify.txt` (HemaSuite session scratchpad)
