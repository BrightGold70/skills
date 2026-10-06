# Handoff — BashParse vouches only on positive evidence (review rounds 13-17)

**Date:** 2026-10-06
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-05-main__bashparse-third-reader.md

## Session Summary

The round-13 review of the round-12 `BashParse` fixes found a false PASS. That set off five review/fix rounds (13 through 17), all now merged and pushed:
- `c25df1f3`: `fix(h-mad): bash vouches for a quote only on positive evidence`.
- `fc23221a`: `fix(h-mad): coverage discloses aliases and sourced heredocs`.

`main` = `origin/main` = `fc23221a`.

**What changed.** bash no longer vouches because a perturbation *failed to break* the parse. Each probe now proves where a position IS, against a control that differs only in its payload:
- **Single quote** (`code_at`): `" 'op op' "` breaks the parse while `" 'x' "` does not, either ungrouped or inside `{ … }`.
- **Heredoc body** (`body_code_at(i, op, term)`): inserting a line `xx…\`, the terminator, the payload and `:<<'TERM'` proves the body is QUOTED. `xx…TERM` must occur nowhere in the block.

**Verification.**
- Full suite: 6220 passed, 0 failed.
- `expect_screens.json`: 117 rows, ALL_CAUGHT.
- code_at fuzz: 0 false proofs over 2,216 code positions.
- Round 17 found no must-fix. Rounds 14-16 each found one or two (two were regressions in this branch; both fixed).

The codex liveness probe is closed: ALIVE. The user declined codex's pending allowlist request.

## Key Learnings

- **A `bash -n` oracle may vouch only on positive evidence, never on absence.** bash 3.2 defers `$(…)`, backticks, `${…}` and arithmetic, so "the doubled operator still parses" is true of deferred code too. No finite set of closer runs leaves every nesting. A probe paired with a control is what works.
- **A probe and its control must differ only in payload, AND the payload must not join a word.** After `<<E`, `'x'` and `'&& &&'` become different heredoc delimiters (R14 M1). The fix is blanks around the payload plus refusing any position right after a backslash: a live `\` escapes the first blank, so `<<E\ 'x'` is the delimiter `E x`.
- **bash 3.2 `-n` exits 1, not 2, on a syntax error inside a top-level `NAME=( … )`.** Inside `{ }` it exits 2. Map only 0 to True and 2 to False; everything else, including a negative signal status, is None.
- **The lexer alone cannot decide heredoc quotedness.** A hidden unquoted `<<E` defeats it (R15). A `x\` line before the terminator proves quoting, because an unquoted body joins that line to the terminator. The join text must occur nowhere in the block, not merely as no word: a `<<axE` after a body line `a\` ends at the join (R16, R17).
- **A DEBUG trap clobbers PIPESTATUS in bash 3.2.** Measured: `false|true|(exit 3)` recorded `0`. That rules it out as a guard for the alias / `source` holes (task #14).
- **I edited the live checkout at first.** `h-mad/` is the live skill, so worktree from the first edit, not after. The rounds also showed that a mutation killed only by a crash (TypeError) proves nothing, and that a row whose guard a newer reader masks belongs on a stubbed-oracle test.
- **A bkit hook blocks bash heredocs that contain backticks** (`ENH-310 heredoc-bypass guard`). Write probe or edit scripts with the Write tool, then run them.

## Next Steps

1. **Task #14, the real runtime guard** for the two holes the coverage line now discloses: aliases enabled in a block, and `.`/`source` of a heredoc or stdin. A DEBUG trap is ruled out (it clobbers PIPESTATUS). Options: check `shopt -q expand_aliases` / `shopt -qo posix` inside the screen instrumentation (`h-mad/scripts/h_mad_expect_screens.py`, `instrument` and `_preamble` near :725), or refuse at run time without per-command traps. Repros: `scratchpad/r14/review-r14.md` S1 and `r17/review-r17.md` S4 (session-local, may be gone; the essentials are in row 1685's ROUND 14 and 17 notes).
2. **Re-run the HemaSuite calibration from a non-isolated session**, now against `fc23221a`: `python3 h-mad/scripts/h_mad_expect_screens.py <spec> <plan> --at 73856d92 --project-root /Users/kimhawk/orca/HemaSuite/hematology-paper-writer`, where the doc is the `website-corpus-root` spec and plan. Expected: `FAIL screens=15 unreadable=15`, or more refusals. Fewer refusals would be a finding.
3. **Root-cause the load-only flake** `test_h_mad_doc_consumers.py::test_run_interrupted_is_UNREADABLE_not_a_traceback`: `python3 h-mad/scripts/h_mad_failure_diff.py run --base main --repeat 5 -- h-mad/tests/test_h_mad_doc_consumers.py`. A second load-only flake appeared this session, `test_h_mad_tdd_judge.py::test_timeout_kind` (1 of 6192; passed 3/3 on both sides when run alone).
4. **Find which codex UserPromptSubmit hook emits invalid JSON.** Codex prints "Hook failed: hook returned invalid user prompt submit JSON output" on every prompt. graft's hook was checked and is valid. That leaves bkit, context-mode or oh-my-codex (see `~/.codex/config.toml` hook entries).

## Open / Blocked Items

**Carried from `bashparse-third-reader` (2026-10-05). Every item is accounted for:**
- **NS1, round-13 review:** **CLOSED.** It became rounds 13-17, merged as `c25df1f3`.
- **NS2, HemaSuite calibration:** open; see Next Step 2.
- **NS3, load-only flake:** open, unchanged; see Next Step 3.
- **NS4, live codex probe:** **CLOSED.** `PROBE: ALIVE`, answer correct in 6s. The pending "add `graft build --deep` to `.h-mad/phase5-shell-allow`?" was declined on the user's word; codex acknowledged.
- **Watch HemaSuite runs** (`vancouver-output-normalization`, owner `da53e8bb`): open. It now also gets this session's new over-refusals: a single-quoted operator inside `$(…)`, backticks or `${…}`; one right after a backslash; `$'…'`; a heredoc body followed by another heredoc on the same opener line; a top-level array quote in a block that ends in an EOF-ended heredoc or a `\`. Its worktree comment reads "plan v1.1 uncommitted, held · next: operator decides commit + audit cycle 2".
- **Deferred backlog rows** (census now OPEN=8): the five rows previously cited as 1269, 1351, 2166, 2314 and 2345 sit at 1269, 1351, 2213, 2361 and 2392 now that the file has grown. Two scout `maybe` rows are also open. All unchanged since 2026-10-05, except that this session added recurrence notes to the hollow-kill row and the stubbed-oracle-pin row (3rd recurrence). New this session: `commit the BashParse false-proof sweep as a test` (candidate: yes).
- **Deferred rows** (1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288): unchanged since 2026-10-05.
- **token-weather on the other Mac:** unchanged since 2026-10-04. User action.
- **Other Mac setup:** unchanged. User action: `h-mad/git-hooks/install.sh`, `pip install pytest-subtests`, `git pull`, then re-register the h-mad bootstrap agents.
- **Concurrent HemaSuite session shares the live skill through symlinks:** unchanged. It got this session's changes the moment they merged. For about 20 minutes early on, it also ran the unfinished code from the live checkout; that code only refuses more, never less.
- **`#56`'s residue trichotomy:** unchanged, deliberate.
- **`.codex/` untracked at repo root:** unchanged. It is codex's graft MCP registration and is left out of commits.
- **graft statusline via `~/.claude/hud/omc-graft-statusline.sh`:** unchanged.
- **Review residuals recorded on rows** (1406, 1937, and 1685's coverage line): unchanged.
- **Pass-log retention has no rotation** (`.h-mad/pass-logs/`): unchanged.
- **Worktree `/Users/kimhawk/orca/skills/.claude/worktrees/expect-screens-oracle`** (branch `worktree-expect-screens-oracle`): still waiting on the user's word. It is merged and clean. To remove: `git worktree remove .claude/worktrees/expect-screens-oracle && git branch -D worktree-expect-screens-oracle`.

**New this session:**
- **Task #14, runtime guard for aliases and `.`/`source` of stdin:** open. The stopgap disclosure is merged (`fc23221a`). Both holes are pre-existing on main; see Next Step 1.
- **Worktree `/Users/kimhawk/orca/skills/.claude/worktrees/bashparse-r13`:** removal waits on the user's word. It is currently on branch `fix/coverage-alias-source`; `fix/bashparse-r13` is also a branch. Both are fully merged into `main`. To remove: `git worktree remove .claude/worktrees/bashparse-r13 && git branch -d fix/bashparse-r13 fix/coverage-alias-source`.
- **Codex plugin hook emits invalid JSON:** open, low. See Next Step 4.
- **Accepted over-refusals added this session** (listed in the module docstring, measurement-discipline §FREEZE and row 1685): a single-quoted operator inside `$(…)`, backticks or `${…}`; one right after a backslash; `$'…'`; a heredoc body before another heredoc on the same line; a top-level array quote in a block that ends in an EOF-ended heredoc or a trailing `\`. A one-line `NAME=$('…&&…')` still passes through the carve-out.

## Context for Next Session

**Files touched this session (all in `c25df1f3` and `fc23221a`, pushed):**
- `h-mad/scripts/h_mad_expect_screens.py`: the `BashParse` redesign (`_parses` status map, `_proves`, `code_at` either-wrap, `body_code_at(i, op, term)` with the line check and join), a new `Line.term`, the module docstring and `COVERAGE`.
- `h-mad/tests/test_h_mad_expect_screens.py`: round 13-17 sections and the coverage test (198 tests).
- `h-mad/tests/mutation-specs/expect_screens.json`: 117 rows.
- `h-mad/references/measurement-discipline.md`: §FREEZE and the residual list.
- `docs/skill-candidates.md`: row 1685 notes ROUND 13 through 17.

**Worktree:** the session ended on the main checkout (`main`). The `bashparse-r13` worktree is still present; see Open Items.

**Uncommitted changes:** none besides this handoff. `.codex/` is untracked and not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                       # expect: in sync with origin/main at fc23221a or later
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK
python3 -m pytest -q h-mad/tests/test_h_mad_expect_screens.py              # 198 passed
```

**Related docs:**
- `docs/handoffs/2026-10-05-main__bashparse-third-reader.md` (predecessor).
- `h-mad/references/measurement-discipline.md` §FREEZE: the three readers, the positive-evidence probes, and the accepted over-refusals.
- `docs/skill-candidates.md` row 1685: notes ROUND 12 through ROUND 17.
- Review reports (session-local, may be gone): `/private/tmp/claude-501/-Users-kimhawk-orca-skills/2a786bfa-67b6-41ee-b7c5-d1af2922ff41/scratchpad/r13` … `r17/review-r1N.md`.
