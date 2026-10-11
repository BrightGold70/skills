# Handoff — fence probe committed, vancouver watch closed, h-mad todo list rebuilt

**Date:** 2026-10-12
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-08-main__token-weather-memory-probes.md

## Session Summary

This session resumed from `token-weather-memory-probes`. It committed the bash-3.2 fence probe as `h-mad/scripts/h_mad_bash4_fence_probe.py` with 31 tests (`a60122d9`, pushed). Before pushing, the full h-mad suite ran: 5958 passed.

The probe reproduces the hand measurement:
- HemaSuite: 1062 blocks, 0 regex hits, and the same 5 PARSE32 lines.
- skills: 2 `mapfile` hits.

The other open items were settled as follows:
- **token-weather band:** the user confirmed it is visible.
- **vancouver watch:** closed with a reason.
- **Other-Mac worktree removal:** cannot be done from this Mac (Hawk-MacStudio), where neither worktree exists.
- **Todo list:** rebuilt from `docs/skill-candidates.md`, scoped to h-mad and handoff. That gives 7 h-mad rows and 0 handoff rows.

## Key Learnings

- **A green foreground pytest does not prove `python3` has pytest.** rtk rewrites a foreground `python3 -m pytest` (its output reads `Pytest: N passed`). The same command backgrounded with a `>` redirect ran homebrew python 3.14 and failed with `No module named pytest`. For background suites, use `/opt/anaconda3/bin/python3 -m pytest`. `[gotcha, 0.5]`
- **A carried "watch X" item needs a close condition.** The vancouver watch existed to catch skills' new h-mad gates (expect-screens backstop, BashParse refusals, the `/bin/bash` pin) breaking a live HemaSuite run. It rode 5 handoffs after the lane had already run 5b and Tasks 1–19 GREEN under those gates. `[pattern, 0.5]`
- **The probe counts docs that contain shell blocks, not all `.md` files.** HemaSuite reads `docs=514`. The predecessor's "6750 docs" counted every markdown file, so the two numbers measure different things; the block count (1062) matches.

## Next Steps

1. **Pick an h-mad candidate from the task list** (#5–#11), `yes` rows first:
   - **#5, row 2214:** hollow-kill detector, in `h-mad/scripts/h_mad_mutation_harness.py`. Consider building #8 (row 2364, reachability) with it.
   - **#6, row 1351:** a `--verify` mode for `h-mad/scripts/h_mad_version_history.py`.
   - **#7, row 2486:** a bounded BashParse false-proof sweep test in `h-mad/tests/test_h_mad_expect_screens.py`.
2. **On the other Mac** (the user's word was given 2026-10-08, but it must be run there):
   ```bash
   git pull --ff-only
   git worktree remove .claude/worktrees/expect-screens-oracle && git branch -d worktree-expect-screens-oracle
   git worktree remove .claude/worktrees/bashparse-r13 && git branch -d fix/bashparse-r13 fix/coverage-alias-source
   ```
   Use `-d`, not the 10-06 handoff's `-D`. If `-d` refuses, a branch is not merged; stop and look.

## Open / Blocked Items

**h-mad skill candidates (todo #5–#11, from `docs/skill-candidates.md`; all open, none started):**
- Row 2214 · yes · hollow-kill detector.
- Row 1351 · yes · version-history `--verify`.
- Row 2486 · yes · BashParse false-proof sweep as a test.
- Row 2364 · maybe · mutation reachability before counting it caught.
- Row 2395 · maybe · per-mutation `requires` probe for host-dependent equivalence.
- Row 2481 · maybe · harness hint when a later guard masks a survivor.
- Row 1269 · maybe · archreview scorer tree-diff.
- **Not in the list on purpose:** rows 2476, 2492 and 2493, which are general git/test tooling, not h-mad or handoff. Their census status is unchanged.

**Carried from `token-weather-memory-probes` (2026-10-08):**
- **NS1: token-weather band visible after restart.** **CLOSED.** The user confirmed it is done.
- **NS2 / Open: other Mac — `git pull` and worktree cleanup.** Open, user action on the other Mac. See Next Step 2.
  - Neither worktree nor branch exists on Hawk-MacStudio (`git worktree list` shows main only).
  - The other checks owed there are unchanged: whether token-weather is registered, whether pytest-subtests is still needed, and the untracked `.codex/`.
- **NS3: commit the fence probe.** **CLOSED** in `a60122d9`. Skill-candidate row 2499 was flipped to LANDED.
- **Watch HemaSuite `vancouver-output-normalization`.** **CLOSED 2026-10-08** on the user's decision.
  - Reason: the risk it watched for (skills' stricter checks breaking that live run) did not happen. The lane ran 5b and Tasks 1–19 GREEN under them with no reported refusals.
  - Last observed state, read-only: worktree `/Users/kimhawk/orca/workspaces/HemaSuite/vancouver-output-normalization`, branch `feature/vancouver-output-normalization` at `36e7df15`, phase 5, unclaimed. Its next step is Task 20 in a fresh `/h-mad`.
  - The tree has uncommitted `.gitignore` and `graft/` changes. That is the lane's business.
- **Deferred backlog rows:** census now OPEN=10 (yes=3, maybe=7), after row 2499 landed.
- **Deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288:** unchanged since 2026-10-05.
- **Other Mac: pytest-subtests.** Unchanged, folded into NS2.
- **Concurrent HemaSuite session shares the live skill through symlinks:** unchanged.
- **`#56` residue trichotomy:** unchanged; deliberate.
- **`.codex/` untracked at the repo root (other Mac):** unchanged, folded into NS2.
- **graft statusline:** unchanged.
- **Review residuals on rows 1406, 1937 and 1685:** unchanged.
- **Pass-log rotation:** unchanged.
- **Accepted over-refusals (2026-10-06):** unchanged; documented.
- **V-11.1 accepted residuals:** deferred by design, unchanged.
- **`tdd-gate-fail-opens` evidence bookkeeping:** deferred, unchanged.
- **Foreign `stash@{0}` (resolved-model):** unchanged; do not touch.
- **Bash pin blast radius:** unchanged. The residue is 5 apostrophe-heredoc blocks in two HemaSuite plan docs that no runner executes; it is now re-measurable with `h_mad_bash4_fence_probe.py /Users/kimhawk/orca/HemaSuite`.
- **Blind-adjudication 5931-vs-5929 test-count gap:** unchanged; not traced. Today's full suite is 5958 on current main, which includes the 31 new tests.
- **Memory index:** `OK` at 18060 B (72%), up from 17493 B and now just over the 17500 compaction target. Not compacted this session.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_bash4_fence_probe.py` (new)
- `h-mad/tests/test_h_mad_bash4_fence_probe.py` (new)
- `docs/skill-candidates.md` (row 2499 marked LANDED; scout section added)
- `docs/learnings.md` (2 entries)
- This handoff

**Uncommitted changes:** none besides this handoff and the two doc updates above, which are committed with it.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                                       # expect main...origin/main
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md   # OPEN=10
python3 h-mad/scripts/h_mad_bash4_fence_probe.py --self-test      # SELFTEST OK regexes=20
/opt/anaconda3/bin/python3 -m pytest -q h-mad/tests/test_h_mad_bash4_fence_probe.py      # 31 passed
```

**Related docs:**
- `docs/handoffs/2026-10-08-main__token-weather-memory-probes.md` (predecessor)
- `docs/skill-candidates.md` (rows 1269, 1351, 2214, 2364, 2395, 2481, 2486)
- `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-08-feature-vancouver-output-normalization__h11-phase5-green-done.md` (the vancouver lane's own state)
