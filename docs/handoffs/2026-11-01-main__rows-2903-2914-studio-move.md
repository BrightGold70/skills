# Handoff — Rows 2903 and 2914 landed, audit-cycle fixtures fixed, row-2910 plan approved; continue on the Mac Studio

**Date:** 2026-11-01
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-01-main__row2729-token-audit-hema-isolation.md
**Next-Session Focus:** On the Mac Studio, run the HemaSuite daemon restart, then implement row 2910 (split `h-mad/SKILL.md`) from its approved plan.
**Suggested-Skills:** handoff (resume and carry-forward), h-mad (`h_mad_failure_diff.py`, the mutation harness)

## Session Summary

Hawui-Macmini session. Everything is committed and pushed, so the next session can start on the Mac Studio with nothing left on this Mac.

- **Row 2903 (failure-diff `subject-changed`): LANDED.** `0cf50a39`, plus the review's must-fix `70ff28e1`.
- **Row 2914 (its should-fixes): LANDED** in `67b653eb`.
- **Test fixtures fixed:** the audit-cycle fixtures (`841a7671`) clear 29 environment failures on this Mac.
- **HemaSuite, pushed to `origin/main`:**
  - the claude -p isolation residuals (`e410554da`);
  - a sidecar test that rewrote a tracked file (`b7290f03c` filed, `520d3a1e1` fixed).
- **Row 2910 (split `h-mad/SKILL.md`):** the plan is approved but no work has started. It lives in `docs/01-plan/features/skill-md-split.plan.md`.

## Key Learnings

- **One test file failed for everyone else.** `test_hmad_dispatch_audit_cycle.py` hardcoded `/opt/anaconda3/bin/python3.11` (the Studio's interpreter) as the shebang and exec target of its shims. On every other host that cost 29 failures, which were read as "environment-only" for weeks. Use `sys.executable` in test shims. The handoff had guessed a missing symlink; that explained only 2 of the 29.
- **A gate grew a file-path sibling.** `h_mad_audit_gate.py` loads `h_mad_test_boundaries_check.py` via `Path(__file__).with_name(...)`. Any fixture that symlinks the gate into a scratch dir must symlink the sibling too. Since `9c6d5474` the gate also FAILs a canonical design doc that has no `## Test Boundaries` section.
- **A RED that passes means the fixture is wrong, not the code.** The first control-parent test passed because the control runs `--base main`, and the file under test existed only on the feature branch. A test of control-side behaviour must put the file in the BASE commit.
- **A stub must leave one guard alone.** A fake `git` that prints to stderr would let the stderr check mask the exit-code check, so a mutant of either survives. The `ls-files` stub exits 128 silently on purpose.
- **Editing the subject during a failure-diff run voids the run.** Since row 2903, any edit to the subject tree during `h_mad_failure_diff.py run` ends it `subject-changed`. That includes creating an untracked, non-ignored file such as a plan doc. Put work products in the scratchpad until the run finishes.
- **`trail check` raises false alarms here.** It flagged 12–14 "conflicts" per commit this session. All were keyword matches against unrelated learnings (reflog mtimes, `git checkout` restore, venv keep, statusline). Read them, then say so in the commit message.
- **`local_only_commits.py` measures "not on main", not "not pushed".** Its `UNIQUE` lines stay after a branch is pushed. To check pushed-ness, use `git rev-list --count origin/<b>..<b>`.

## Next Steps

1. **Mac Studio, HemaSuite (user action):**
   - Pull HemaSuite to `520d3a1e1` or later; this includes `7b8fc2ad0` (the ~600k-per-call isolation) and `e410554da` (the canary and race fixes).
   - Restart the agent daemon. Until then anemia_jmj runs the old code.
2. **Mac Studio:** check HemaSuite `docs/.bkit-memory.json` for owned records with a null heartbeat (`owner_session_id` / `owner_heartbeat_ts`). This is carried; it can only be done on the Studio.
3. **Row 2910: implement the approved plan** in `docs/01-plan/features/skill-md-split.plan.md`. Branch off `main`.
   - Corpus helper `h-mad/tests/skill_corpus.py`, then switch the 43 test files the plan lists to it. That commit must be suite-`SAME`.
   - Move the three sections into `references/phase5-substeps.md`, `references/teammate-authors.md` and `references/audit-prompt-assembly.md`.
   - Re-anchor the 25 mutation rows across 11 specs.
   - Add a budget test (SKILL.md ≤ 260 KB).
   - Verify with `h_mad_failure_diff.py run --base main`, then a fresh-context `change-reviewer`.
   - Re-measure the line ranges first if SKILL.md has moved.
4. **Mac Studio baseline:** run the full suite once to learn the Studio's environment failures:
   ```
   P=<studio python>; $P h-mad/scripts/h_mad_failure_diff.py run --base main --python $P --timeout 5400 --log-dir <dir outside the repo> -- h-mad/tests handoff/tests
   ```
   They will differ from this Mac's 9. The anaconda fix means the Studio no longer needs `/opt/anaconda3`, but it should still pass there.

## Open / Blocked Items

**Carried from `2026-11-01-main__row2729-token-audit-hema-isolation.md`:**

- **Row 2729 interpreter half:** closed earlier (`d937cc86`).
- **Row 2903:** closed. LANDED in `0cf50a39` and `70ff28e1`. Full suite `FAILDIFF: SAME both=38`.
- **Row 2856 gate half** (`.sh` production files gated by Task; an `/h-mad` feature): unchanged since 2026-11-01.
- **Row 2890 (`maybe`, append mutation rows without reformatting):** unchanged since 2026-11-01. This session appended 6 rows by text-preserving insertion again; the hand workaround still holds.
- **`test_grok_audit_surface_wrapper.py` 4 stamp-leg failures:** closed. Fixed in `841a7671`, which has three causes: the hardcoded interpreter, the missing sibling symlink, and the stale fixture design doc. `FAILDIFF: FIXED_ONLY control_only=29 both=9`.
- **[suggested] Wire `h_mad_reanchor_diff.py` into the re-anchor step:** unchanged since 2026-11-01.
- **Studio null-heartbeat check:** unchanged; Studio only (Next Step 2).
- **Watch-only triage rows (19, 51, etc.):** unchanged since 2026-10-27.
- **Residuals of the 2026-10-31 stamps:** unchanged since 2026-10-31.
- **Run 8 attempts 1–2:** evidence only, never a score. Unchanged since 2026-10-27.
- **Residuals of the 2026-11-01 landings** (git config under admitted `git diff`, `--text` refused, the re-anchor rule's rewrite blind spot): unchanged since 2026-11-01.
- **Environment-only failures on Hawui-Macmini:** now **9**, down from 38:
  - `test_h_mad_mutation_harness.py` 7;
  - `test_h_mad_codex_runtime.py` 1;
  - `test_h_mad_new_gate.py` 1.

  Not investigated. Compare with `h_mad_failure_diff.py`, never counts.
- **HemaSuite claude -p isolation residuals:**
  - closed in `e410554da` (HemaSuite `origin/main`): the token canary (warns once per process when context exceeds the prompt by more than 50k), the cwd-race retry, and the dead `NOTEBOOKLM_QUERY_TIMEOUT`;
  - still open (HemaSuite-owned, task only): drafting quality without the project CLAUDE.md, to be measured on the next manuscript run;
  - the worktree `HemaSuite-claude-isolation` was removed by someone else during this session.
- **HemaSuite per-call judge model:** not owned here; unchanged. Another session works it: worktrees `HemaSuite-judge-sdk` (branch `feat/judge-provenance-non-agent`) and earlier `HemaSuite-judge-model`. **Heads-up:** that session had uncommitted edits to `hematology-paper-writer/tools/agent_executor.py`, which `e410554da` also changed, so it will hit a rebase conflict.
- **HemaSuite test rewrote a tracked file mid-run:** closed. Filed `b7290f03c`, fixed `520d3a1e1`; the restore happens only when the bytes differ, pinned by an mtime assertion. Residual, recorded in HemaSuite's row: the suite-wide search for other unconditional restores was not done.
- **Token config change (user-approved, earlier session):** unchanged. 13 plugins are disabled in `~/.claude/settings.json` on **this Mac**. The `settings.json.bak-123954` backup was in the old session's scratchpad, which is not durable. The Studio's settings were not changed; apply the same on the Studio if wanted.

**New this session:**

- **Row 2914 (failure-diff should-fixes):** closed. LANDED in `67b653eb`; ALL_CAUGHT 13/13; `FAILDIFF: SAME both=38`.
- **Row 2910 (split h-mad/SKILL.md):** approved, not started (Next Step 3).
  - Plan: `docs/01-plan/features/skill-md-split.plan.md`.
  - The handoff/SKILL.md half of the row is out of scope for this slice.
- **New row 2924 (`candidate: yes`, this closeout's scout):** a `--subject-snapshot` mode so a failure-diff run measures a frozen copy and the checkout stays editable during the ~30–60 min suite.
- **Two pre-existing local-only refs, now pushed so they survive the move to the Studio. Neither came from this session, and neither is decided:**
  - `origin/park/grok-14h-home-rstrip` (`60635019`, 2026-10-25): the parked trailing-slash `HOME` fix to `h_mad_tool_calls.py` `scan_log`, plus 2 containment tests. Its remote branch had been deleted, but the fix is NOT on `main`. Decide: fold it in as a feature task, or drop it.
  - `origin/park/stash-assemble-tdd-json-2026-11-01` (`1d505e3d`): the local stash from 2026-11-01 09:54, which deletes 48 lines of `h-mad/tests/mutation-specs/assemble_tdd.json`. It sits on base `33a0dfdd`, which is on no remote. It looks like an aborted mid-edit state from the row-2729 session. Inspect, then most likely delete the branch.
  - The stash is still in this Mac's `git stash list`, which is harmless.

## Context for Next Session

**Files touched this session:**
- skills `main`:
  - `h-mad/scripts/h_mad_failure_diff.py`
  - `h-mad/tests/test_h_mad_failure_diff.py`
  - `h-mad/tests/mutation-specs/failure_diff_subject_changed.json`
  - `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
  - `h-mad/tests/test_grok_audit_surface_wrapper.py`
  - `docs/skill-candidates.md`
  - `docs/01-plan/features/skill-md-split.plan.md`
- HemaSuite `main`:
  - `hematology-paper-writer/tools/agent_executor.py`
  - `hematology-paper-writer/tests/test_agent_executor.py`
  - `hematology-paper-writer/tests/test_citation_fidelity_backtest.py`
  - `docs/skill-candidates.md`

**Uncommitted changes:** none. skills `main` is level with `origin/main`. Untracked `.trail/` is ignored.

**To resume (Mac Studio):**
```bash
cd ~/orca/skills && git checkout main && git pull --ff-only     # ≥ this handoff's commit
cd ~/orca/HemaSuite && git fetch && git log --oneline -1 origin/main   # ≥ 520d3a1e1; pull on the branch you run the daemon from
cat ~/orca/skills/docs/01-plan/features/skill-md-split.plan.md
```

**Related docs:**
- `docs/handoffs/2026-11-01-main__row2729-token-audit-hema-isolation.md` (predecessor)
- `docs/skill-candidates.md`: rows 2903 and 2914 LANDED, 2910 open, 2856 open, 2890 maybe
- HemaSuite `docs/skill-candidates.md`: the sidecar-rewrite row, LANDED
