# Handoff — branch-evidence multiproject fix, exec-pane race, HemaSuite 2nd reconciliation

**Date:** 2026-10-16
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-15-main__candidates-burn-run-suggest.md, 2026-10-15-main__branch-evidence-multiproject.md

## Session Summary

The session ran 2026-10-15 to 10-16 and is all done and pushed (`origin/main` = `efeca369`).
- **J52/J53.** The orphaned entries were adopted and the census pins bumped (`a00ee6ff`).
- **Brief.** The HemaSuite brief `branch-evidence-multiproject` was taken over and closed.
  - `h_mad_branch_evidence.py` now runs one pytest per rootdir, under that sub-project's own venv (`fecae140`).
  - A test in a sibling rootdir is now selected only by an import-shaped reference (`67dc3b62`).
  - On the live HemaSuite feature/204 branch the result went from `UNREADABLE rc4` to `PASS files=199 passed=3291`. The HemaSuite lane was notified, and the claim was released.
- **Second reconciliation pass.** The 22 HemaSuite skill-candidate rows were reconciled. HemaSuite `001656eb3` brings census OPEN from 68 to 62. The verdicts are in skills `18c5335e`.
- **Exec-pane race.** It was a real production race in the slot-release order (`2658b600`).
- **CC 2.1.301 pins.** The claude-binary pins broken by the auto-update were re-anchored (`efeca369`).
- **Full suite.** 6380 passed, 0 failed.

## Key Learnings

- **A fixture that passes before the fix is not a reproduction.** The first two-sub-project fixture went green on the unfixed code. The collision needs `tests/__init__.py` packages in both sub-projects, because both then import as `tests.conftest`. Run the RED before writing the fix. `[gotcha, 0.7]`
- **A microsecond race does not reproduce under CPU stress.** The old and new exec-pane orders both passed 10/10 under 24 burners. Holding each intermediate state open (0.6 s per step) reproduced the exact suite failure deterministically. `[solution, 0.7]`
- **A binary pin on `var \w+=<value>,` can match an unrelated constant.** It matched one for three versions. CC 2.1.301 renamed that constant to `$Po` and the pin broke; the real cap was never what it pinned. Anchor on a semantic neighbour, such as `"MEMORY.md",x=200,y=25000,`. `[gotcha, 0.7]`
- **Editing the tree while a full suite runs voids that run.** The suite reported `SUITE: TREE_MOVED`, and the scoped re-run was refused as `SUITE: BUSY` because the suite held the lock. Batch the edits, then run the suite once. `[gotcha, 0.5]`
- **Markdown table cells escape `|` as `\|`.** When verdict text is copied from a table into prose (here, status lines), unescape it, or a `grep -E` alternation turns into a literal pipe. `[gotcha, 0.5]`
- **Re-derive a brief's "which tests matched and why".** The brief called `test_so_scope_boundary`'s match a comment mention. It is actually a dotted module string (`"engine.knowledge_orchestrator"`), and it correctly stays selected. `[pattern, 0.3]`

## Next Steps

1. Triage the 10 open `maybe` rows: `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`. (b) :2533, (d) :2544 and (e) :2549 come from HemaSuite's item 12. (e), the TDD judge's 40 s budget, is the same idea as HemaSuite's `tdd-judge-test-file-budget` (STILL-OPEN, `h_mad_tdd_judge.py:28`).
2. Optional: the HemaSuite branch `feature/204` reads `INCOMPLETE reason=no-mutation-spec` for 4 probe scripts under `docs/03-analysis/probes/synopsis-path-preflight/*.py`. That is HemaSuite's call; they were told on 2026-10-15.

## Open / Blocked Items

**Carried from `2026-10-15-main__candidates-burn-run-suggest.md`:**
- NS1, other-Mac `git pull` + worktree cleanup + pytest-subtests + `.codex/`: **WITHDRAWN by the operator** 2026-10-15 ("forget #1").
- NS2, J52/J53 census pin bump: **CLOSED** `a00ee6ff`. The entries were adopted here, since nobody else would commit them; the writing HemaSuite session had ended. Pins are 50/83, OPEN=2.
- NS3, the second HemaSuite reconciliation: **CLOSED** HemaSuite `001656eb3` + skills `18c5335e`. 23 status lines were inserted. Results: LANDED 2 names (4 lines), SUPERSEDED 1, DECLINED 1, STILL-OPEN 13.
- Still uncovered from the first pass:
  - `land-on-main-from-worktree` is now on HemaSuite main but was not in its open list; unverified.
  - `pid-and-log-watcher` is open and was reconciled in the first pass (STILL-OPEN partial).
- Deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288: unchanged since 2026-10-05.
- Rows 2364/2395/1269 (deferred) and 2481/2496 (maybe): unchanged since 2026-10-12.
- Concurrent HemaSuite sessions share the live skill through symlinks: unchanged. Every mutation sweep this session ran in a throwaway worktree for that reason.
- `#56` residue trichotomy, graft statusline, review residuals on rows 1406/1937/1685, pass-log rotation, accepted over-refusals (2026-10-06), V-11.1 residuals, `tdd-gate-fail-opens` bookkeeping: unchanged.
- Foreign `stash@{0}` (resolved-model): unchanged; do not touch.
- Bash pin blast radius: unchanged (`h_mad_bash4_fence_probe.py`).
- Blind-adjudication 5931-vs-5929 test-count gap: unchanged, not traced. The full suite is now 6380.
- Memory index: above the 17500 compaction target; not compacted (not re-measured this session).
- Census: skills OPEN=10, all `maybe`. It was 8 before the 2026-10-15 closeout appended rows 2576/2582. J-entries: 50, 2 open (J52, J53 MONITORING).

**From the taken-over brief `2026-10-15-main__branch-evidence-multiproject.md`** (Handover-From HemaSuite · feature/204-synopsis-path-preflight · session b5c8fa27; taken over by session e442f689):
- NS1, reproduce: done. It was the same `ValueError: Plugin already registered`. With the substituted pair the exit code was rc=1/no-summary rather than rc=4; the verdict is UNREADABLE either way.
- NS2, run shape: **CLOSED** `fecae140`.
- NS3, selection: **CLOSED** `67dc3b62`.
- NS4, tests: **CLOSED** in those two commits. 9 new tests; 61 mutation rows ALL_CAUGHT.
- NS5, notify the HemaSuite lane: **DONE** 2026-10-15 via `orca terminal send` to `term_9214f6c2…`. That proves delivery only, not pickup. The claim `branch-evidence-multiproject` was released.
- repo: /Users/kimhawk/orca/HemaSuite · branch: feature/204-synopsis-path-preflight · worktree: /Users/kimhawk/orca/workspaces/HemaSuite/synopsis-path-preflight. HemaSuite's Task 3 waiver cites the brief.

**New this session:**
- The exec-pane flake (`test_a_finishing_slot_is_waited_for_and_then_reused`): **CLOSED** `2658b600`. It was a real race: the release cleared `.finishing` before writing `.idle`.
- CC 2.1.301 broke the claude-binary pins: **CLOSED** `efeca369`.
- A behaviour change worth knowing: `branch_evidence` now reads `UNREADABLE pytest-missing` for a repo whose top-level `.venv` lacks pytest. It no longer falls back to the collector's interpreter. Skills has no such venv.

## Context for Next Session

**Files touched this session (all committed):**
- `h-mad/scripts/h_mad_branch_evidence.py`, `h-mad/tests/test_h_mad_branch_evidence.py`, `h-mad/tests/mutation-specs/branch_evidence.json`
- `h-mad/scripts/hmad-dispatch.sh`, `h-mad/tests/test_hmad_dispatch_exec_pane.py`, `h-mad/tests/mutation-specs/exec_pane_release_order.json` (new)
- `h-mad/tests/test_skill_body_renderer_args.py`, `h-mad/tests/test_h_mad_check_memory_index.py`
- `docs/skill-monitoring.md` (J52/J53), `handoff/tests/test_skill_candidates_census.py`
- `docs/03-analysis/2026-10-13-hemasuite-skill-candidates-reconciliation.md` (§Second pass)
- `docs/handoffs/2026-10-15-main__branch-evidence-multiproject.md` (Taken-Over-By)
- HemaSuite: `docs/skill-candidates.md` (`001656eb3`, from a throwaway worktree, since removed)

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect main...origin/main, clean
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md   # OPEN=10
```

**Related docs:**
- `docs/handoffs/2026-10-15-main__branch-evidence-multiproject.md` (the taken-over brief)
- `docs/03-analysis/2026-10-13-hemasuite-skill-candidates-reconciliation.md`
