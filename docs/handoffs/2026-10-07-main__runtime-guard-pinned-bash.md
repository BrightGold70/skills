# Handoff — expect-screens runtime guard, pinned bash, flakes root-caused

**Date:** 2026-10-07
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-06-main__bashparse-positive-evidence.md

## Session Summary

This Mac's checkout had diverged from origin: 77 behind and 6 ahead, with unpushed commits from 2026-10-02. I reset `main` to `origin/main` and reviewed every unpushed commit. All but one are superseded upstream, and that one, blind adjudication, is archived on origin.

All four of the predecessor's Next Steps are closed:
- **Task #14 (runtime guard):** shipped.
- **HemaSuite calibration:** re-run, unchanged at 15/15 unreadable.
- **Load-only flakes:** both root-caused and fixed.
- **Codex hook error:** closed by the operator.

The session also found and fixed a larger problem. `run_block` and the `bash -n` oracle resolved `bash` by PATH, so on this Mac (Homebrew bash 5.3 first) four expect-screens guards never ran. Both now use `/bin/bash`.

`main` = `origin/main` = `5bd64b4d`. The tree is clean, and every verification below ran on the final code.

## Key Learnings

- **A test that sends SIGINT fails when the suite is started in the background.** A job launched with `&` (or nohup, or an agent's background shell) inherits SIGINT as SIG_IGN. Python keeps an inherited ignore, so the child never sees the interrupt. This was the "load-only" flake in `test_run_interrupted_is_UNREADABLE_not_a_traceback`, not load. Give the child `SIG_DFL` in `preexec_fn`. `[suggested gotcha, 0.7]`
- **A budget that includes the judge's own setup races the sleeper it is testing.** `budget_s=1.0` covers the judge's work before it spawns anything. Under load the group was killed before the sleeper wrote its pid, so the verdict was a correct `timeout` but `_pid_gone` failed "never wrote its child pid". Measured: budgets of 0.2s or less report `timeout` with no pidfile.
- **A mutation sweep under the default PATH found four guards that never ran.** Bash 5.3 doesn't need the guards that 3.2 needs, so their mutants survived (`trap-armed-inside-screens`, `failure-reported-at-heredoc-terminator`, two `oracle-*` rows). With `/bin/bash` first, all were caught. The pin is in `h_mad_doc_block_exec.BASH`.
- **Editing any tracked file while a mutation sweep runs voids it.** The harness reports `TREE_MOVED` with no scores. Commit, then sweep, then touch nothing.
- **Unpushed agent worktrees can hold commits the cherry-picked backup lacks.** The backup branch had blind adjudication without its review fix `61b7525a`. A merge-commit fix `e0995f6a` was never cherry-picked at all; it turned out to be unneeded, because upstream's parser differs and an evil-merge repro gives `claims=2` on current main. Diff every `agent-*` worktree against origin before deleting anything.
- **This Mac and the other one re-implemented the same work.** 4 of the 6 commits left unpushed on 2026-10-02 were rebuilt independently upstream on 10-04, and a backlog row was declined as "not built" while its code sat unpushed here. Push or archive before switching machines.
- **The suite lock refuses concurrent pytest runs** (`SUITE: BUSY`). A parallel stress run reports lock refusals, not flakes. Run stress serially.

## Next Steps

1. **On the other Mac:** `git pull`. Then remove its merged worktrees `expect-screens-oracle` and `bashparse-r13` per the 2026-10-06 commands, on the user's word. Its local `.codex/` and pass-logs live there too.
2. **[suggested]** Fence-scope the bash-4 check. A text grep over HemaSuite `*.md` (non-archive) found 0 uses of `declare -A`, `${x,,}`, `mapfile`/`readarray`, `|&`, `;;&` or globstar. A fence-scoped check would make the pin's safety for HemaSuite exact rather than likely. Same regex, restricted to `shell_blocks()` output.

## Open / Blocked Items

**Carried from `bashparse-positive-evidence` (2026-10-06):**
- **NS1, Task #14 runtime guard:** **CLOSED.** Shipped as `07dad5c2`, `0fcf3ad8` and `8a9c1d6a`. Every `.`/`source` and every alias mode at a screen now reads `UNREADABLE:unsupported_runtime=<source|aliases>@<doc>:<line>`. The residuals are listed in the coverage line: aliases toggled off between screens, `builtin`/`command` source inside a function, and a block that disarms the guard.
- **NS2, HemaSuite calibration:** **CLOSED.** Code before (`a261dab7`) and after (`8a9c1d6a`) the guard, each under bash 5.3 and 3.2: four runs, every one `FAIL screens=15 unreadable=15`, with identical per-screen lines.
- **NS3, load-only flakes:** **CLOSED.** `ca310b08` fixes the SIGINT disposition. `11b23b54` sets `SLEEPER_BUDGET_S = 3.0` on four tests and gives `_pid_gone` split deadlines. Mutant check: killing only the direct child still fails all four tests.
- **NS4, codex hook invalid JSON:** **CLOSED by the operator.** This Mac is unaffected: its only UserPromptSubmit hook is graft, and graft's output matches codex 0.160.1's embedded schema.
- **Watch HemaSuite `vancouver-output-normalization`:** unchanged; it is HemaSuite's lane. Its impl-plan v1.1 is now committed (`8f2e0c977`), so the 10-06 "uncommitted, held" note is stale. Its runs now also use pinned `/bin/bash` through the symlink.
- **Deferred backlog rows:** census OPEN=8 (yes=3, maybe=5) at the start of the session; all three `yes` rows were re-checked against source and are still open. The scout added 2 `maybe` rows, so the census now reads OPEN=10.
- **Deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288:** unchanged since 2026-10-05.
- **token-weather on the other Mac:** unchanged; user action.
- **Other Mac setup:** **done on THIS Mac.** The pre-push hook is linked, all 6 h-mad agents are linked, and pytest 9.1.1 has subtests built in, so `pytest-subtests` is not needed. Whether the other machine still needs it is unknown.
- **Concurrent HemaSuite session shares the live skill through symlinks:** unchanged. It received this session's guard and the bash pin on merge.
- **`#56` residue trichotomy:** unchanged; deliberate.
- **`.codex/` untracked at the repo root:** not present on this Mac; unchanged on the other.
- **graft statusline:** unchanged.
- **Review residuals on rows 1406, 1937 and 1685:** unchanged.
- **Pass-log rotation:** unchanged. There are no pass-logs on this Mac.
- **Worktree `expect-screens-oracle`:** not on this Mac; see Next Step 1.
- **Worktree `bashparse-r13`:** not on this Mac; see Next Step 1.
- **Accepted over-refusals (2026-10-06):** unchanged; documented.

**Carried from the local `v111-review-loop-closed` (2026-10-02):**
- **Memory-index test #28:** **CLOSED.** It passes now (30 passed).
- **V-11.1 accepted residuals:** deferred by design, unchanged.
- **`tdd-gate-fail-opens` evidence bookkeeping:** deferred, unchanged.
- **Foreign `stash@{0}` (resolved-model):** unchanged; do not touch.

**New this session:**
- **Auto-memory index at WARN** (`~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md`: 20605/25000 bytes, 136 lines, 82%). Compact to 17500 bytes / 140 lines by moving settled entries to `MEMORY-ARCHIVE.md`, with link conservation checked in the same script, before the next memory write. This WRITE added no memory for that reason.
- **`refs/archive/blind-adjudication` on origin:** points at `61b7525a` (builder + review fix). The declined row in `docs/skill-candidates.md` gives the reopen command. Its tests were not re-run against current `main`.
- **Worktree `/Users/kimhawk/orca/skills/.claude/worktrees/f2-lost-state`** (branch `fix/f2-workdir-and-lost-state`): **another session's live work**, with commits about 5 minutes before this WRITE. I did not touch it.
- **Bash pin blast radius:** `_run_with_streams` in `h_mad_doc_block_exec` is also pinned now. A text grep found no bash-4-only syntax in HemaSuite docs; see Next Step 2.

## Context for Next Session

**Files touched this session (all pushed):**
- `h-mad/scripts/h_mad_expect_screens.py`: runtime guard (`SHADOWS`, `RETURN_TRAP`, `ALIAS_CHECK`, `unsupported_runtime`), docstring and `COVERAGE`, and the oracle on `BASH`.
- `h-mad/scripts/h_mad_doc_block_exec.py`: `BASH = "/bin/bash"` if it exists, otherwise PATH.
- `h-mad/tests/test_h_mad_expect_screens.py`: task-14 tests, decoy-bash pin tests, and the `test_bash_unavailable_fails_closed` producer.
- `h-mad/tests/test_h_mad_doc_block_exec.py`: spawn failure is produced via `BASH`; the CLI uses a `_CLI_WITH_BASH` wrapper.
- `h-mad/tests/test_h_mad_doc_consumers.py`: SIGINT `SIG_DFL` for the child.
- `h-mad/tests/test_h_mad_tdd_judge.py`: `SLEEPER_BUDGET_S` and split `_pid_gone` deadlines.
- `h-mad/tests/mutation-specs/expect_screens.json` (128 rows) and `doc_block_exec.json` (91 rows).
- `h-mad/references/measurement-discipline.md`: §FREEZE residuals.
- `docs/skill-candidates.md`: a row-1685 note and the blinded-adjudication archive note.

**Verification on the final code:**
- Full `h-mad/tests`: 5894 passed. The drop from 5908 is 16 per-bash duplicates removed and 2 new tests added.
- `expect_screens` mutations under the default PATH: ALL_CAUGHT, 128/128.
- `doc_block_exec` mutations: ALL_CAUGHT, 91/91.
- Doc consumers of `skill-candidates.md`: 125 passed.

**Uncommitted changes:** none besides this handoff.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                      # expect main...origin/main
python3 -c "import sys;sys.path.insert(0,'h-mad/scripts');import h_mad_doc_block_exec as m;print(m.BASH)"   # /bin/bash
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md | grep TOTAL   # OPEN=10
```

**Related docs:**
- `docs/handoffs/2026-10-06-main__bashparse-positive-evidence.md` (predecessor).
- `h-mad/references/measurement-discipline.md` §FREEZE: the runtime guard and its residuals.
- `docs/skill-candidates.md` row 1685 (TASK #14 note), and the blinded-adjudication row with its CODE ARCHIVED note.
