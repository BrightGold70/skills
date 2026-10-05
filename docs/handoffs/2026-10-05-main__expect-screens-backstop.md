# Handoff — expect-screens backstop merged; round 11 says stop patching the lexer

**Date:** 2026-10-05
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-05-main__backlog-burn-to-five.md

## Session Summary

Row 1685's round-10 must-fixes are fixed and merged as `398a5aec`, which is pushed. `main` = `origin/main` = `398a5aec`.

The fix is structural:
- `lex()` no longer looks for `&&`, `||` or `&`.
- `backstop()` is now the only list detector. It reads the raw text on its own model, and excludes text only where the lexer agrees it is single-quoted, or where both read it as a quoted-delimiter heredoc body.

**What it closes:** the three round-10 holes (H1, P1, K1/K2) and five more found during the build. 15 of the new tests read PASS on the old main.

**Verification:**
- 115 tests pass.
- `expect_screens.json`: 86 rows, ALL_CAUGHT.
- Full suite: 6137 passed, 0 failed.
- Calibration is unchanged:
  - design at `0021c77`: PASS screens=3;
  - design at `dadaf84`: three screens read `exit_status=2`;
  - HemaSuite at `73856d92`: 15 of 15 unreadable, for the same causes.

**Round 11** (fresh-context gating review) found 7 constructs that fool **both** readers. All 7 also read PASS on the old main. The user chose: merge now, then spike bash's own parser as the second reader (Next Step 1). The stale 1685 worktree and its branch are removed.

## Key Learnings

- **Two readers built from the same quote model are not independent.** "A misread must fool both" failed seven times in round 11 (`$$'`, backticks, `"${…'…}"`, a heredoc opener ending in `\`, `$(`+heredoc on 3.2, `$[1<<E]`, `export \`+carve-out). Agreement-based exclusion only helps where the failure modes are disjoint. That is the case for comments and heredoc confirmation, but not for basic quoting. The next independent reader has to be bash itself.
- **A backstop that refuses a superset of the lexer turns the lexer's mutation rows into survivors.** The first full run gave 17 SURVIVED, all lexer-refusal rows masked by the backstop. Root fix: delete the redundant lexer detection and port the rows onto the backstop's operator lines. More tests would not have fixed it.
- **A fix can disarm an existing mutation row without failing anything.** The new heredoc word-end rule made `'/<<EOF/'` never match, so the `heredoc-found-inside-quotes` row went inert. It needed a test input that still matches (`'/<<EOF /'`).
- **Never edit the tree while the mutation harness runs.** The harness reports TREE_MOVED and the run is wasted, even for a doc-only edit. Also, an identical source line (`elif ch in "'\""`) can silently break another row's "find exactly once" anchor.
- **`git diff X Y | wc -l && <delete>` is not a guard.** `wc` succeeds whatever the count, and I deleted a branch on that basis. The content proved to be on main, but check the number before deleting.
- **Codex in Phase 5 can run tests.** `pytest` and `python -m pytest` written plainly are allowed. Git, pipes, `&&`/`;`/`>`/`$(…)` and non-h-mad scripts are refused (`h-mad/hooks/h-mad-codex-tdd-gate.py:30-31`, `_safe_argv`). `.h-mad/phase5-shell-allow` is for unrelated work only, and it still cannot admit pipes.

## Next Steps

1. **Row 1685 spike (#22): bash's own parse as the independent list reader.** Wrap the block as `__f() { <block> }` under `/bin/bash` 3.2 and print it back with `declare -f __f`. The reviewer found this surfaced the hidden `&&` for 6 of the 7 round-11 constructs (M1–M6), unverified as a general design.
   - **What to check:**
     - `$(…)` text in 3.2: is it reprinted verbatim or parsed?
     - heredoc reprinting;
     - `&` jobs;
     - that parsing has no side effects;
     - M7, which is a statement-start check and not a quoting problem.
   - **Inputs:**
     - round-11 report `/private/tmp/claude-501/-Users-kimhawk-orca-skills/23db3646-f289-41d0-a329-a23d47b8e517/scratchpad/review-r11.md` (session-local, may be gone; the constructs are also in `docs/skill-candidates.md` row 1685, note "ROUND 11 OPEN");
     - the code at `h-mad/scripts/h_mad_expect_screens.py` (`backstop`, `_raw_op`, `_one_chain`).
   - **Also:** drop `&>>` and `|&` from the docstring and §FREEZE. They are bash-4 forms (N1).
2. **Root-cause the load-only flake** `test_h_mad_doc_consumers.py::test_run_interrupted_is_UNREADABLE_not_a_traceback`. Run: `python3 h-mad/scripts/h_mad_failure_diff.py run --base main --repeat 5 -- h-mad/tests/test_h_mad_doc_consumers.py`.
3. **Live codex probe** (deferred at the user's choice): `hmad-dispatch probe codex --timeout 60`. Check `hmad-dispatch env`'s `last=` first: the codex pane still holds a question about adding `graft build --deep` to a `.h-mad` file.
4. **Watch HemaSuite's live h-mad runs.** `vancouver-output-normalization` was LIVE at merge time. It now gets the backstop's extra refusals (operators in double quotes, comments and unquoted heredoc bodies; `<<\EOF`; `>&$fd`). It also still gets `SUITE: BUSY`, and the `report_path_handed` remedy is still "mint a fresh RUN".

## Open / Blocked Items

**Carried from `backlog-burn-to-five` (2026-10-05); every item is accounted for:**

- **NS1, row 1685 round 10:** **CLOSED.** Fixed and merged as `398a5aec` and pushed. Round 11 opened as new work: see Next Step 1.
- **NS2, remove the 1685 worktree:** **CLOSED.** `.claude/worktrees/agent-afb18b7aac5cbe3a7` and branch `worktree-agent-afb18b7aac5cbe3a7` (tip `aa2b968a`) were removed on the user's word. Its branch-only files and doc lines were verified present on main.
- **NS3, load-only flake:** open, unchanged. See Next Step 2.
- **NS4, live codex probe:** deferred, unchanged. See Next Step 3.
- **NS5, watch HemaSuite runs:** open, now also covering the backstop's refusals. See Next Step 4.
- **Deferred backlog rows** (1269, 1351, 2166, 2314, 2345): unchanged. The census now reads OPEN=6, because this session's scout added one `maybe` row: prove a squash-merged branch is on main before `branch -D`.
- **Deferred rows (1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288):** unchanged since 2026-10-05.
- **token-weather on the other Mac:** unchanged since 2026-10-04; user action.
- **Other Mac setup:** unchanged; user action. Run `h-mad/git-hooks/install.sh`, `pip install pytest-subtests` and `git pull`, then re-run the h-mad bootstrap agent registration.
- **A concurrent HemaSuite session shares the live skill through symlinks:** unchanged. `LIVE-RUNS: 1` at merge.
- **`#56`'s residue trichotomy:** unchanged, deliberate.
- **`.codex/` untracked at repo root:** unchanged. It is codex's graft MCP registration, left out of commits.
- **graft statusline via `~/.claude/hud/omc-graft-statusline.sh`:** unchanged.
- **Review residuals recorded on rows** (1406, 1937, 1685's coverage line): unchanged.
- **Pass-log retention has no rotation** (`.h-mad/pass-logs/`, about 300 KB per pass): unchanged; revisit if it gets big.

**New this session:**
- **Row 1685 round 11:** 7 must-fix, 2 should-fix, 1 nit. All are recorded on the row and pre-exist on main. See Next Step 1 (task #22).

## Context for Next Session

**Files touched this session (all in `398a5aec`, pushed):**
- `h-mad/scripts/h_mad_expect_screens.py`: `backstop`, `_raw_op`, `_quote_blind`, `_one_chain`, `PURE_ARITH`, and the HEREDOC word-end rule. The lexer's list detection is removed.
- `h-mad/tests/test_h_mad_expect_screens.py`: 16 new tests, plus one changed input.
- `h-mad/tests/mutation-specs/expect_screens.json`: 86 rows.
- `h-mad/references/measurement-discipline.md` §FREEZE.
- `docs/skill-candidates.md`: row 1685 has notes "ROUND 10 FIXED" and "ROUND 11 OPEN".

**Uncommitted changes:** none besides this handoff. `.codex/` is untracked and not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                       # expect: in sync with origin/main at 398a5aec or later
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK
python3 -m pytest -q h-mad/tests/test_h_mad_expect_screens.py              # 115 passed
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md | tail -1   # OPEN=6
```

**Related docs:**
- `docs/handoffs/2026-10-05-main__backlog-burn-to-five.md` (predecessor).
- `h-mad/references/measurement-discipline.md` §FREEZE: refusal rules, over-refusal, residuals.
- `h-mad/hooks/h-mad-codex-tdd-gate.py:30-31,432`: what codex's Phase-5 shell admits.
