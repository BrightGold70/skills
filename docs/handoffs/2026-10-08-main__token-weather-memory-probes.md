# Handoff — token-weather installed, memory index compacted, bash-4 fence probe, blind-adjudication re-verified

**Date:** 2026-10-08
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-07-main__runtime-guard-pinned-bash.md

## Session Summary

This session resumed from `runtime-guard-pinned-bash` and closed four of its five items. Code changes: none. All changes were to machine config (outside the repo) or were read-only measurements.

- **token-weather mod installed on this Mac.** `~/.claude/mods/token-weather` is a symlink into the repo, and the mod is registered in `~/.claude/settings.json`. It is NOT loaded in the session that installed it; restart Claude Code to see it.
- **Memory index compacted.** It went from 20605 B to 17493 B, under the 17500 target; the checker reports `OK`.
- **Bash pin is safe for HemaSuite.** The probe was scoped to bash/sh code fences. No block that a runner executes needs bash 4.
- **Blind-adjudication archive still works on current main.** Cherry-picked onto `d5797898`: its own tests, its mutation spec and the full suite are all green.

`main` = `origin/main` = `23b67cb2`. That includes the f2 lane's three commits, which merged while this session ran. The tree is clean apart from this handoff.

## Key Learnings

- **The three memory dirs are one store.** `-Users-kimhawk-Coding/memory` and `-Users-kimhawk-orca-skills/memory` are both symlinks to `-Users-kimhawk-orca/memory`. The size warning named the Coding path and the handoff named the orca-skills path, but it is one file. `h_mad_check_memory_index.py` de-duplicates them by inode.
- **Bash 3.2 rejects an apostrophe inside a `$(cat <<'EOF' … EOF)` heredoc body.** It reports `unexpected EOF while looking for matching '`, while bash 5.3 parses the same block. A search for bash-4 features cannot find this; only `/bin/bash -n` does. HemaSuite has 5 such blocks, all in docs that no runner executes. `[suggested gotcha, 0.7]`
- **`bash -c '…'` inside a doc block resolves `bash` from PATH, not the pin.** So `mapfile` inside `bash -c` stays outside the `/bin/bash` pin, which only covers the outer shell.
- **`expect_screens.certify` returns `[]` before running anything when a doc has no `# expect <N>` screen.** It checks `screens_in`/`unparsed_in` first. So whether a doc's blocks can run at all depends on it carrying a screen, not merely on it being a `.md` with bash fences.

## Next Steps

1. **Restart Claude Code to load token-weather, then confirm the band is visible.** It shows context-window fill, drawn above the prompt. No other action is needed: `claude plugin validate` passes with 1 warning (no author field) and `claude plugin test` gives 17 pass.
2. **On the other Mac:** `git pull`, then remove its merged worktrees `expect-screens-oracle` and `bashparse-r13` per the 2026-10-06 commands, on the user's word. Its local `.codex/` and pass-logs live there too.
3. **[optional] Commit the fence probe** if a re-runnable instrument is wanted. It is `bash4_fence_probe.py`, in the scratchpad (volatile); content summarised under Open Items. The user has not decided.

## Open / Blocked Items

**Carried from `runtime-guard-pinned-bash` (2026-10-07):**
- **NS1 (other Mac: `git pull` + worktree cleanup):** unchanged since 2026-10-07; user action. Now Next Step 2.
- **NS2 (fence-scope the bash-4 check):** **CLOSED**, measured this session. Scope was `shell_blocks()` (bash/sh fences, a superset of `hmad:exec`), with 20 bash-4/5 feature regexes plus `/bin/bash -n` vs bash 5.3 `-n`. Positive controls: 20/20 regexes fired, and `;;&` is rejected by 3.2 but accepted by 5.3.
  - HemaSuite (non-archive): 6750 docs, 1062 blocks, **0 regex hits**, 5 parse-only-under-3.2 failures. All 5 are the apostrophe-heredoc pattern in `docs/superpowers/plans/2026-05-22-hemasuite-audit-phase.md` (lines 476, 1243) and `…-workflow-orchestrator.md` (lines 1942, 2012, 2249). Neither doc has `# expect` or `hmad:exec`, so no runner executes them.
  - skills: 0 parse diffs. 2 unique `mapfile` hits, in `docs/handoffs/2026-08-31-main__j1-pane-pin-takeover-and-handover.md:112` and `2026-09-01-main__wire-pin-gate-and-skill-upgrades.md:110`. Both are inside `bash -c` and neither doc has screens.
  - The probe was not committed; see Next Step 3.
- **Watch HemaSuite `vancouver-output-normalization`:** unchanged; HemaSuite's lane (Orca comment: impl-plan v1.1 committed, next 5b audit cycle 1).
- **Deferred backlog rows:** census OPEN=11. The 3 `yes` rows are unchanged; this session's scout added 1 `maybe` (bash-3.2 compat probe).
- **Deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288:** unchanged since 2026-10-05.
- **token-weather on the other Mac:** **CLOSED on THIS Mac**, installed 2026-10-07 per `mods/token-weather/README.md`. The settings backup is at the session scratchpad's `settings.json.bak` (volatile). Whether the *other* Mac (the one that originally built it) has it registered was not checked; the 10-03 handoff says it was registered there.
- **Other Mac setup (pytest-subtests):** unchanged; unknown whether it is still needed there.
- **Concurrent HemaSuite session shares the live skill through symlinks:** unchanged.
- **`#56` residue trichotomy:** unchanged; deliberate.
- **`.codex/` untracked at the repo root:** unchanged (other Mac only).
- **graft statusline:** unchanged.
- **Review residuals on rows 1406, 1937 and 1685:** unchanged.
- **Pass-log rotation:** unchanged.
- **Worktrees `expect-screens-oracle`, `bashparse-r13`:** not on this Mac; see Next Step 2.
- **Accepted over-refusals (2026-10-06):** unchanged; documented.
- **V-11.1 accepted residuals:** deferred by design, unchanged.
- **`tdd-gate-fail-opens` evidence bookkeeping:** deferred, unchanged.
- **Foreign `stash@{0}` (resolved-model):** unchanged; do not touch.
- **Auto-memory index at WARN:** **CLOSED.**
  - Size: 20605 B / 136 lines → 17493 B / 122 lines (70%); `h_mad_check_memory_index.py` gives `OK`, rc 0.
  - Moved 9 settled or codified entries plus the "Skills — current shape" section into `MEMORY-ARCHIVE.md` under `## Moved 2026-10-07`, and trimmed about 20 long hooks.
  - Link conservation was checked in the same script: 250 links, all targets present. `test_h_mad_check_memory_index.py` gives 30 passed.
  - Backups `MEMORY.md.bak` and `MEMORY-ARCHIVE.md.bak` are in the scratchpad (volatile).
- **`refs/archive/blind-adjudication` tests not re-run:** **CLOSED.**
  - Cherry-picked `546d1272` and `61b7525a` onto `d5797898` in a temp worktree, with no conflicts.
  - Results: own tests 35 passed; `--check-anchors` ANCHORS_OK; mutation `ALL_CAUGHT mutations=11 caught=11 … crash_kills=0 crash_visible=5/32`; full `h-mad/tests` **5931 passed**, 0 failed, in 21m42s.
  - The temp worktree was removed and nothing was pushed. The row stays DECLINED; this only proves reopening costs two cherry-picks.
  - Caveats:
    - 5931 is 2 more than the 5894 + 35 = 5929 expected; the gap was not traced.
    - The harness warns that none of the 11 mutations carries a `symbol` pin.
    - The run predates the f2 merge (`510ff98d..23b67cb2`).
- **Worktree `f2-lost-state` (another session's live work):** **CLOSED.** It merged to main as `510ff98d`, `c3760d67` and `23b67cb2`, and the worktree is gone from `git worktree list`.
- **Bash pin blast radius:** now exact for HemaSuite (see NS2). The only residue is the 5 apostrophe-heredoc blocks, which would break if someone added a `# expect` screen to those two plan docs.

## Context for Next Session

**Files touched this session:**
- No tracked repo files besides this handoff.
- Outside the repo:
  - `~/.claude/mods/token-weather` (new symlink).
  - `~/.claude/settings.json`: `env.CLAUDE_CODE_PLUGIN_DIRS` added.
  - `~/.claude/projects/-Users-kimhawk-orca/memory/MEMORY.md` and `MEMORY-ARCHIVE.md`.
- Scratchpad (volatile): `bash4_fence_probe.py`, `hs.out`, `sk.out`, `ba-mut.out`, `ba-suite.out`, plus the backups above.

**Uncommitted changes:** none besides this handoff.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                      # expect main...origin/main
python3 h-mad/scripts/h_mad_check_memory_index.py   # OK, ~70%
readlink ~/.claude/mods/token-weather            # → /Users/kimhawk/orca/skills/mods/token-weather
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md | grep TOTAL   # OPEN=11
```

**Related docs:**
- `docs/handoffs/2026-10-07-main__runtime-guard-pinned-bash.md` (predecessor).
- `mods/token-weather/README.md` (install steps).
- `docs/skill-candidates.md` (the blinded-adjudication row with its CODE ARCHIVED note).
