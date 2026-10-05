# Handoff — backlog burn 32 → 5, /tmp race root-caused, suite lock everywhere

**Date:** 2026-10-05
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-05-main__prescribed-blocks-claim-once.md

## Session Summary

The open backlog went from **32 to 5**. The 5 left are all deliberately deferred, each with a reopen condition written on its row.
- **Built and landed (9 rows):** 1628, 1685, 1937, 1391 + 745 (and 2361, folded into 1391), 1406, 2370, 2375 and 2364.
- **Calibrated not-buildable:** 1349 and 2119.
- **Triaged closed (16):** recorded in commits c203d391, 2c975f5a and 5b83d62f.

Every build went through a worktree executor, then my own re-verification, then fresh-context `change-reviewer` rounds, then a squash merge.

Root cause of the day's load-only flakes: conftest swept the shared `/tmp/audit_*_run*` files, deleting other worktrees' live files. Fixed in `80df76e0`.

**Final state:**
- Full suite at `54ed5aca`: **6116 passed, 0 failed**.
- `main` = `origin/main` = `e4011d25`, pushed. Only `e4011d25` (one small expect-screens fix) landed after that suite run.
- The graft statusline wrapper now runs under the OMC HUD (outside the repo, `~/.claude/hud/omc-graft-statusline.sh`).

## Key Learnings

- **A lexical bash analyser cannot be made complete by exceptions.** Row 1685 (`h_mad_expect_screens.py`) needed 9 review rounds. Every exemption keyed on command text opened a hole the next round found: grep no-match, env-prefix, `NAME=$(…)`, `|| exit`, conditions, the braced status-1 remedy, `[[`/`((`. Two of those holes came from relaxations I asked for. What converged was zero exceptions, refusing `&&`/`||`/`&`, plus a remedy that needs no `||` (`awk '/pat/'`, `sed -n '/pat/p'`) and disclosed residuals printed on every run.
- **Only after the full set of mechanisms was in did that converge.** It needed `set -o pipefail` and the ERR trap together, with refusal of everything the trap cannot see.
- **A before/after glob set-difference over a shared directory is a cross-session race.** conftest's `_remove_fresh_stem_files_this_run_created` deleted concurrent worktrees' `/tmp/audit_*_run*` files. That was the source of the flakes in `test_hmad_dispatch_audit_cycle.py` and `report_path_handed`, and of harness BASELINE_NOT_GREEN/RESTORE_FAILED under load. Measured over 14 concurrent sessions: on main, 5 of 7 failed; with the fix, 0 of 8. The fix is a private per-session dir via `HMAD_AUDIT_STEM_DIR`.
- **`pytest_sessionstart` in a non-initial conftest never fires.** So a lock placed in `h-mad/tests/conftest.py` skipped `handoff/` runs. The lock now lives in a repo-root `conftest.py` plus `h-mad/tests/tree_lock_plugin.py`.
- **Executors routinely end with "Done." / "No action." / "Nothing is pending." and no evidence.** Always verify the branch tip yourself. `h_mad_branch_evidence.py` (row 2375) now does it mechanically.
- **zsh does not word-split an unquoted `$VAR`.** A verify loop `for s in $S` ran one bogus argument and reported "no tests ran". Wrap such loops in `bash -c`.
- **Merging two branches that both edit `conftest.py` produced two `pytest_configure` definitions.** One silently shadowed the other. Fix: integrate both on one branch, add a test that fails if either behaviour is dropped, then merge.
- **The `[H-MAD] Context budget` hook ceiling is 45%.** This session ran to 70% under `/loop`. Each review round costs about 1–2% of orchestrator context, even when it is fully delegated.

## Next Steps

1. **Row 1685: round 10 found 2 more must-fixes. Do the structural backstop the reviewer prescribed, not more lexer patches.** Both are PASS results over an unrecorded git 128 on main `e4011d25`. All are reproduced, with bash rc=0 in each case.
   - **(H1) Unquoted heredoc bodies are not lexed,** yet bash runs the `$(…)` and backtick spans inside them. Reproduction: `cat > note.txt <<NOTE` / `$(G && echo listed)` / `NOTE` reads PASS. The anchor is `M:HEREDOC-BODY`, `h_mad_expect_screens.py:223`.
   - **(P1) A ` #` inside `${…}` is read as a comment.** Example: `X=${PWD// #/}; G && echo ok`. The anchor is `M:COMMENT-UNQUOTED`, `:287`.
   - **(K1/K2) Escaped operators are misread.** `G \&& wait` and `G \|& wait` are lexed as a redirect, so the real background `&` is excluded. The anchor is `M:REDIRECT-NOT-JOB`, `:269`.
   - **Fix that ends the class:** add a fail-closed raw-text BACKSTOP that runs independently of the lexer. It refuses any line whose raw text contains `&&`, `||`, or an `&` that does not match a strict redirect pattern (`[0-9]*>&[0-9-]`, `<&`, `&>>?`, `|&`). It excludes only single-quoted spans and quoted-delimiter heredoc bodies. It over-refuses by design. Add RED tests H1, P1, K1 and K2 first, then the backstop, then a mutation row. Re-run the 0021c77 calibration, which must still PASS screens=3.
   - **Earlier pointer, kept for reference:** round 10 was a closure check. The reviewer has `aa2b968a` (= main `e4011d25`), and the report is `/private/tmp/claude-501/-Users-kimhawk-orca-skills/588eb758-2644-4bc7-a4cf-dfd5baf8e06e/scratchpad/review-expect-screens-5cba8c6b.md` §"Round 10". The scratchpad is session-local and may be gone. If so, start a fresh `change-reviewer` on `h-mad/scripts/h_mad_expect_screens.py` at HEAD. Scope it to: any remaining text-keyed exemption that suppresses `&&`, `||` or `&` (including the redirect forms `2>&1`, `>&2`, `&>`), and any new fail-open. The residuals printed on the coverage line are accepted.
2. **Remove the 1685 worktree once round 10 is settled:** `git worktree remove .claude/worktrees/agent-afb18b7aac5cbe3a7 && git branch -D worktree-agent-afb18b7aac5cbe3a7`. It is merged in substance; main holds its diffs as squashed fix-forwards.
3. **Root-cause the load-only flake** `test_h_mad_doc_consumers.py::test_run_interrupted_is_UNREADABLE_not_a_traceback`. It failed once in an 82-file consumer run while other worktrees were testing, and passes 3/3 alone. Use the new tool: `python3 h-mad/scripts/h_mad_failure_diff.py run --base main --repeat 5 -- h-mad/tests/test_h_mad_doc_consumers.py`.
4. **Live codex probe** (carried; deferred at the user's choice): `hmad-dispatch probe codex --timeout 60`. First check `hmad-dispatch env`'s `last=`. The codex pane held a pending question about adding `graft build --deep` to a `.h-mad` file.
5. **Watch HemaSuite's live h-mad runs** (carried). Since 80df76e0 two things matter:
   - HemaSuite pytest sessions on the SAME toplevel now get `SUITE: BUSY` (rc 75) if they overlap.
   - The `report_path_handed` HALT remedy is still "mint a fresh RUN".

## Open / Blocked Items

**Carried from `prescribed-blocks-claim-once` (2026-10-05); every item is accounted for:**

- **Next Step 1, build open rows:** **CLOSED.** The backlog went 32 → 5.
  - Landed: 1406 `4739cd58`; 1685 `530e4564` + fix-forwards through `e4011d25`; 1391 + 745 `a9ad4d22` + `80df76e0`; 1937 `132f056f`; 2370 `dd4af081`; 1628 `7e10f543`; 2364 `fb474949`; 2375 `ce8e2116`.
  - Calibrated not built: 1349 (`dae6f0b8`, 0/4 recall) and 2119 (no signature hit in 145 specs).
  - Triage notes: `c203d391`, `2c975f5a`, `5b83d62f`.
  - The 5 still open are deferred with a reopen condition each: 1269, 1351, 2166, 2314, 2345.
- **Next Step 2, live codex probe:** deferred, unchanged. See Next Step 4.
- **Next Step 3, row T in HemaSuite:** was CLOSED in the predecessor. Nothing further.
- **token-weather on the other Mac:** unchanged since 2026-10-04; user action.
- **Other Mac setup:** unchanged; user action. Run `h-mad/git-hooks/install.sh`, `pip install pytest-subtests` and `git pull`, then re-run the h-mad bootstrap agent registration. It also needs the suite-lock root `conftest.py`, which arrives with the pull.
- **A concurrent session shares this working tree:** unchanged. A HemaSuite run was LIVE all session; every commit hook printed `LIVE-RUNS: 1`, and lane liveness read `failed-round-diagnostic-letter` as LIVE with transcript age about 1–16 s. All skill changes reached it through the symlinks; the suite lock is per toplevel, so HemaSuite runs do not contend with this repo's.
- **`#56`'s residue trichotomy:** unchanged, deliberate.
- **Deferred rows (1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288):** unchanged. Line numbers have shifted by roughly +5 to +50 because of today's notes; the census lists the current open set.
- **`.codex/` untracked at repo root:** unchanged. It is codex's graft MCP registration, left out of commits.
- **graft MCP:** was CLOSED in the predecessor. New this session: the graft statusline is shown via `~/.claude/hud/omc-graft-statusline.sh`, and `~/.claude/settings.json` `statusLine` points at it. The backup is `~/.claude/settings.json.bak-statusline-*`. The wrapper adds about 110 ms per render; graft reports its own `ctx` beside OMC's.
- **Live h-mad run in HemaSuite received the skill changes:** behaviour changes this time:
  - SUITE: BUSY when a second pytest runs on the same toplevel;
  - the LIVENESS evidence line;
  - new advisory fields on the EVIDENCE line;
  - pass logs copied to `.h-mad/pass-logs/`.

**New this session:**

- **Row 1685 round 10:** pending. See Next Step 1.
- **Flake `test_run_interrupted_is_UNREADABLE_not_a_traceback`:** open. See Next Step 3.
- **Review residuals recorded on rows, not bugs:**
  - 1406: ps-argv flags, merge-imported commits, a codex/agy owner has two clocks.
  - 1937: no transcript size cap, heredoc tokenising, no pass-log rotation.
  - 1685: the coverage line names child shells, eval, untagged expectations, absolute paths, failing conditions and `!`.
- **Pass-log retention has no rotation.** `.h-mad/pass-logs/` grows at about 300 KB per pass (gitignored). Revisit if it gets big.

## Context for Next Session

**Files touched this session (all committed and pushed):**
- New scripts:
  - `h-mad/scripts/h_mad_delta_stage.py`
  - `h_mad_expect_screens.py`
  - `h_mad_lane_liveness.py`
  - `h_mad_failure_diff.py`
  - `h_mad_branch_evidence.py`
- New infra: `conftest.py` (repo root) and `h-mad/tests/tree_lock_plugin.py`.
- Changed:
  - `h-mad/tests/conftest.py`
  - `h-mad/tests/suite_lock_support.py`
  - `h-mad/scripts/h_mad_review_evidence.py`
  - `h_mad_audit_cycle.py`
  - `h_mad_assemble_audit.py` (`doc_path()` factored out)
  - `h_mad_state_ownership.py`
  - `h_mad_live_runs.py`
  - `h_mad_state_write.py`
  - `h_mad_mutation_harness.py`
  - `h_mad_audit_gate.py`
  - `h_mad_wire_registry.py`
  - `h_mad_doc_consumers.py` (`--run`)
  - `hmad-dispatch.sh` (`HMAD_AUDIT_STEM_DIR`)
- Docs:
  - `h-mad/SKILL.md`
  - `handoff/SKILL.md`
  - `h-mad/references/measurement-discipline.md`
  - `docs/skill-candidates.md`
- New mutation specs: `delta_stage`, `expect_screens`, `evidence_targets`, `suite_lock`, `suite_tree_digest`, `lane_liveness`, `doc_consumers_run`, `failure_diff`, `branch_evidence`, `audit_stem_dir`.
- Outside the repo: `~/.claude/hud/omc-graft-statusline.sh` and `~/.claude/settings.json` (`statusLine`).

**Worktree:** one stale agent worktree remains, `.claude/worktrees/agent-afb18b7aac5cbe3a7` (branch `worktree-agent-afb18b7aac5cbe3a7`, row 1685). See Next Step 2.

**Uncommitted changes:** none besides this handoff. `.codex/` is untracked and not ours.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                       # expect: in sync with origin/main
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors | tail -1   # ANCHORS_OK
python3 -m pytest -q                              # ~17.5 min; expect 0 failed (6116 at 54ed5aca)
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md   # OPEN=5
python3 h-mad/scripts/h_mad_branch_evidence.py <worktree-or-branch>   # verify any executor branch
```

**Related docs:**
- `docs/handoffs/2026-10-05-main__prescribed-blocks-claim-once.md` (predecessor).
- `h-mad/references/measurement-discipline.md` §FREEZE: the expect-screens rule, its remedy and its residuals.
- `docs/skill-candidates.md`: LANDED, DECLINED and DEFERRED notes dated 2026-10-05 on every row touched.
