# Handoff — BashParse: bash's own parse is the third list reader

**Date:** 2026-10-05
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-05-main__expect-screens-backstop.md

## Session Summary

Spike #22 (row 1685, round 11) is done. The fix is merged and pushed as `8f8b7de0`, so `main` = `origin/main` = `8f8b7de0`.

**What changed.** `h_mad_expect_screens.py` gains `BashParse`, which runs `bash -n` on a perturbed copy of the block and never executes it.
- A position is excluded only when the lexer, the backstop and bash all read it as literal.
- The `NAME=$(a && b)` carve-out also needs bash to read a statement start.

**Round 12.** A fresh-context review of the first cut (`8e24635d`) found 3 must-fix holes, 1 should-fix and 1 nit. All are fixed in the same merge.

**Verification:**
- Full suite: 6165 passed, 0 failed.
- `expect_screens.json`: 100 rows, ALL_CAUGHT.
- 28 new tests.
- The calibration on the `0021c77` design doc gives the same result as main's tool.

**Not yet reviewed.** The round-12 fixes themselves have had no fresh-context review.

## Key Learnings

- **`declare -f` is not a safe reader of untrusted shell; `bash -n` is.** A block that closes the `__f() {` wrapper runs at top level under `declare -f`: a `touch` ran. `bash -n` never executes anything.
- **bash 3.2 `-n` parses only the top level.** It defers `$(…)`, backticks, `<(…)`, `$((…))` and `$[…]` to run time: `bash -n -c 'echo $(a && && b)'` is rc 0. A perturbation oracle therefore needs closer runs that push a position out to top level.
- **A closer containing a backtick pairs with any later backtick in the block,** including one in a comment. That reopened every top-level hole (R12 M1). You need a backtick-free closer run (`)`×8) as well as the backtick run. Each run is pinned by its own mutation row.
- **A reserved-word probe also fires in one-word slots.** `then` breaks the parse at a statement start, but also in a `case` subject or a `[[ -n` operand. Pair it with a plain-word probe: a statement start is where `then` breaks the parse AND `x` does not. Measured on 15 of 15 slot cases.
- **Never collapse "no answer" into a boolean that a `not` then inverts.** `_parses` returning False on a timeout made `starts_statement` vouch: fail-open (R12 M3). Make it tri-state (None = no answer), and have every caller compare with `is True` / `is False`.
- **When a new reader backs up two old ones, the old agreement checks' mutants survive.** Here that was 4 rows. Keep the checks as defence in depth, and pin those rows to tests where a stubbed bash vouches wrongly, rather than deleting them.
- **The worktree isolation guard refuses compound commands, `trap`, and git in other repos.** It also stalled a subagent for 600s. Tell reviewers to run one plain command per call, put probes in Python scripts, and write the report incrementally. HemaSuite calibration cannot run from an isolated session.

## Next Steps

1. **Round-13 fresh-context review of the round-12 fixes** (commit `cd8fba95`; on main as part of `8f8b7de0`). Scope: `BashParse.CLOSERS`, `code_at`, `starts_statement`, and `_parses`'s tri-state, all in `h-mad/scripts/h_mad_expect_screens.py`. Use the `change-reviewer` agent with the isolation-safe instructions from Key Learnings. Prior reports: `/private/tmp/claude-501/-Users-kimhawk-orca-skills/c88e53df-8f26-4416-840e-dff6d6f305da/scratchpad/s22/review-r12.md` (session-local, may be gone; row 1685's "ROUND 12 FIXED" note has the essentials).
2. **Re-run the HemaSuite calibration from a non-isolated session.** The doc is `website-corpus-root` spec + plan at `73856d92`. Compare main's old tool with the new one: `python3 h-mad/scripts/h_mad_expect_screens.py <spec> <plan> --at 73856d92 --project-root /Users/kimhawk/orca/HemaSuite/hematology-paper-writer`. Expected: `FAIL screens=15 unreadable=15`, unchanged.
3. **Root-cause the load-only flake** `test_h_mad_doc_consumers.py::test_run_interrupted_is_UNREADABLE_not_a_traceback`. Run: `python3 h-mad/scripts/h_mad_failure_diff.py run --base main --repeat 5 -- h-mad/tests/test_h_mad_doc_consumers.py`.
4. **Live codex probe:** `hmad-dispatch probe codex --timeout 60`. The codex pane still holds a question about `graft build --deep`.

## Open / Blocked Items

**Carried from `expect-screens-backstop` (2026-10-05); every item is accounted for:**
- **NS1, row 1685 spike #22:** **CLOSED.** Merged and pushed as `8f8b7de0`. Round 13 (review of the round-12 fixes) is new work; see Next Step 1.
- **NS2, load-only flake:** open, unchanged. See Next Step 3.
- **NS3, live codex probe:** deferred, unchanged. See Next Step 4.
- **NS4, watch HemaSuite runs:** open. `vancouver-output-normalization` was LIVE at merge, owner `da53e8bb`. It now also gets BashParse's refusals: a single-quoted operator in backticks, a quoted heredoc in `$(…)`, and every round-11 and round-12 construct. Still `SUITE: BUSY`; the `report_path_handed` remedy is still "mint a fresh RUN".
- **N1 (`&>>`/`|&` docs):** **CLOSED** in `8f8b7de0`.
- **Deferred backlog rows** (1269, 1351, 2166, 2314, 2345, plus the scout's squash-merge `maybe` row): unchanged since 2026-10-05. The census now reads OPEN=7, because this session's scout added one `maybe` row: a harness hint for agreement-check mutants that a new reader masks.
- **Deferred rows (1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288):** unchanged since 2026-10-05.
- **token-weather on the other Mac:** unchanged since 2026-10-04; user action.
- **Other Mac setup:** unchanged; user action. Run `h-mad/git-hooks/install.sh`, `pip install pytest-subtests` and `git pull`, then re-register the h-mad bootstrap agents.
- **Concurrent HemaSuite session shares the live skill through symlinks:** unchanged. `LIVE-RUNS: 1` at merge.
- **`#56`'s residue trichotomy:** unchanged, deliberate.
- **`.codex/` untracked at repo root:** unchanged. It is codex's graft MCP registration, left out of commits.
- **graft statusline via `~/.claude/hud/omc-graft-statusline.sh`:** unchanged.
- **Review residuals recorded on rows** (1406, 1937, 1685's coverage line): unchanged.
- **Pass-log retention has no rotation** (`.h-mad/pass-logs/`): unchanged.

**New this session:**
- **Worktree `/Users/kimhawk/orca/skills/.claude/worktrees/expect-screens-oracle`, branch `worktree-expect-screens-oracle` (tip `cd8fba95`):** left in place, waiting on the user's word. Its tree is byte-identical to main at `8f8b7de0` (`git diff --stat HEAD worktree-expect-screens-oracle` is empty). To remove it, run `git worktree remove` on it, then `git branch -D worktree-expect-screens-oracle`.
- **HemaSuite calibration not re-run:** see Next Step 2.

## Context for Next Session

**Files touched this session (all in `8f8b7de0`, pushed):**
- `h-mad/scripts/h_mad_expect_screens.py`: `BashParse` (`CLOSERS`, `_parses`, `code_at`, `starts_statement`), wired into `backstop` (`M:ORACLE-DATA`, `M:ORACLE-BODY`, `M:ORACLE-CHAIN-START`), plus docstrings and N1.
- `h-mad/tests/test_h_mad_expect_screens.py`: 28 new tests (R11, R12, stubbed-oracle defence in depth).
- `h-mad/tests/mutation-specs/expect_screens.json`: 100 rows.
- `h-mad/references/measurement-discipline.md` §FREEZE.
- `docs/skill-candidates.md`, row 1685: notes "SPIKE #22" and "ROUND 12 FIXED".

**Uncommitted changes:** none besides this handoff. `.codex/` is untracked and not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                       # expect: in sync with origin/main at 8f8b7de0 or later
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK
python3 -m pytest -q h-mad/tests/test_h_mad_expect_screens.py              # 143 passed
```

**Related docs:**
- `docs/handoffs/2026-10-05-main__expect-screens-backstop.md` (predecessor).
- `h-mad/references/measurement-discipline.md` §FREEZE: the three readers and the accepted over-refusals.
- Spike probes (session-local): `/private/tmp/claude-501/-Users-kimhawk-orca-skills/c88e53df-8f26-4416-840e-dff6d6f305da/scratchpad/s22/`.
