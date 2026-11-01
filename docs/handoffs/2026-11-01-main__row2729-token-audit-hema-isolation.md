# Handoff — Row 2729 landed; token audit; HemaSuite claude -p isolation; row 2903 parked on a WIP branch

**Date:** 2026-11-01
**Branch:** main
**Project:** skills
**Supersedes:** 2026-11-01-main__backlog-open-rows-to-three.md
**Next-Session Focus:** Finish row 2903 on `wip/row-2903-subject-changed`: apply the change-reviewer's must-fix and should-fixes, then merge to main.
**Suggested-Skills:** handoff (resume and carry-forward)

## Session Summary

This session resumed `backlog-open-rows-to-three` on Hawui-Macmini and finished three things.

- **Row 2729, interpreter half: landed** in `d937cc86` and pushed. GREEN's `--check-anchors` line now runs under an interpreter the Phase-5 gate trusts.
- **Row 2903: implemented but not finished.** The failure-diff tool now ends `subject-changed` when the subject tree changes mid-run. The full suite reads `SAME`, but the independent review found a fail-open, so the work is parked on the pushed branch `wip/row-2903-subject-changed` (`81e10cd1`).
- **Token audit.** Asked by the user. The Mac Studio's 10:00–13:00 surge, about 120M input-equivalent, came from HemaSuite's daemon. It made 472 headless `claude -p` calls on Opus, each booting the full harness at about 600k context. That was fixed in HemaSuite in 4 commits and pushed (`origin/main` `7b8fc2ad0`).

## Key Learnings

- **`claude -p --system-prompt X --tools ""` still loads the whole harness:** every MCP server, the user's plugins and hooks, the skill and agent listings, and CLAUDE.md.
  - Measured: 349,447 context tokens for a ~1k-token prompt. With `--strict-mcp-config --setting-sources "" --disable-slash-commands --no-session-persistence` it was 678.
  - `--bare` is not an option for subscription users: it never reads OAuth.
  - `--setting-sources ""` is accepted by 2.1.316 but undocumented. It also blocks an ancestor CLAUDE.md: a planted file did not load, while the positive control with `project` did.
- **Before trusting a mutation spec's verdict, re-measure after any reorder.** I reordered `ANCHOR_CHECK_PYTHONS` after a 4/4 run, which silently made one row non-discriminating on this host. Make tests host-independent by monkeypatching the candidate list with fake runnable scripts.
- **A content hash taken before and after cannot catch an edit reverted mid-run**, which was row 2903's reported case. A `(mtime_ns, size)` snapshot can, because the revert is itself a write. Dogfooding found three tests that rewrite tracked files in place:
  - two in skills (`census_registry.json` and `mutation_harness.json`), both fixed;
  - one in HemaSuite (`backtest_citation_fidelity.out.md`), still open.
- **Long sessions dominate token cost.**
  - A session resumed after an idle night re-caches its whole context: 491k tokens at 07:54 for HemaSuite `5b41d5bc`.
  - Status questions asked in a 600k session cost about 50k input-equivalent each.
  - This Mac's fixed baseline is about 145k per call. `h-mad/SKILL.md` is about 112k tokens and `handoff/SKILL.md` about 34k.
- **On the WIP branch, `--log-dir` equal to or containing the subject turns the new check off silently.** Until the must-fix lands, always pass a log dir outside the repo.

## Next Steps

1. **Finish row 2903** on `git checkout wip/row-2903-subject-changed`. The review is at `/private/tmp/claude-501/-Users-kimhawk-orca-skills/01ed0d3b-deaa-4fe4-a043-f4e4af1426db/scratchpad/review-2903.md`; it is scratchpad, so it may be gone, and its findings are summarised here. Each item needs a test and a mutation row:
   - **must-fix:** a `--log-dir` equal to or containing the subject makes the snapshot `{}` and the check silently off. Refuse it with `UNREADABLE reason=log-dir`. Anchor: `h_mad_failure_diff.py` `_tree_snapshot` `M:FD-SNAP-EXCLUDE`.
   - **untested fail-closed branches:** a failing `git ls-files` (stub `git` on PATH), a `stat` OSError, and a non-empty listing stderr (an unreadable untracked dir currently passes with `rc=0`) must each end `subject-snapshot-failed`.
   - **`--control-parent` inside the subject:** the control's own writes read as a subject change. Exclude the control dir too.
   - **`repeat=2` test** with the change only in run 1, expecting `run=1/2`, to pin the after-every-subject-run check (`M:FD-SNAP-SIDE`).
   - **docstring residuals:** an untracked file created and deleted inside one run; a rename away and back; edits inside a submodule or to an outside symlink target; ignored files the suite reads; a HEAD move with no file change.
   - **declined, with the reason recorded:** ctime/inode, because macOS changes ctime when an app opens a file and writes xattrs.
   - **nits:** an `… and N more` line when more than 15 paths changed; wording that says the comparison is against the pre-loop snapshot.

   Then rerun the full suite with `P=/opt/homebrew/opt/python@3.14/bin/python3.14; $P h-mad/scripts/h_mad_failure_diff.py run --base main --python $P --timeout 5400 --log-dir <dir outside the repo> -- h-mad/tests handoff/tests`, stamp row 2903 LANDED in `docs/skill-candidates.md`, and merge to main.
2. **Mac Studio (user action):** in HemaSuite, `git pull` (to `7b8fc2ad0` or later), then restart the agent daemon. Until then anemia_jmj runs the old ~600k-per-call code.
3. **Studio state** (carried; machine-local): check owned records with a null heartbeat in `/Users/kimhawk/orca/HemaSuite/docs/.bkit-memory.json` (`owner_session_id` / `owner_heartbeat_ts`).
4. **New row (this closeout's scout, `candidate: yes`):** split `h-mad/SKILL.md` (~391 KB, ~112k tokens) and `handoff/SKILL.md` (~34k) into a short core plus `references/*.md` read on demand.

## Open / Blocked Items

**Carried from `2026-11-01-main__backlog-open-rows-to-three.md`:**

- **Row 2729 interpreter half:** closed. LANDED in `d937cc86` and pushed. The row is stamped; the verifier prompt names the interpreter too.
- **Row 2903 (was 2902):** in progress on `wip/row-2903-subject-changed` (`81e10cd1`, pushed). Not merged: the must-fix is open (Next Step 1).
- **Row 2856 gate half** (`.sh` production files gated by Task; an `/h-mad` feature): unchanged since 2026-11-01.
- **Row 2890 (`maybe`):** append mutation rows without reformatting the spec. Unchanged since 2026-11-01.
- **`test_grok_audit_surface_wrapper.py` 4 stamp-leg failures:** unchanged since 2026-11-01. The suspected cause is a missing `h_mad_test_boundaries_check.py` symlink in `real-cycle-scripts/`. Note that the peer session `hemasuite-94` fast-forwarded skills main with grok-staging commits touching that test file (`c1267a83`..`1666e888`); re-check before working on it.
- **[suggested] Wire `h_mad_reanchor_diff.py` into the re-anchor step:** unchanged since 2026-11-01.
- **Studio null-heartbeat check:** unchanged; Studio only (Next Step 3).
- **Watch-only triage rows (19, 51, etc.):** unchanged since 2026-10-27.
- **Residuals of the 2026-10-31 stamps:** unchanged since 2026-10-31.
- **Run 8 attempts 1–2:** evidence only, never a score. Unchanged since 2026-10-27.
- **Residuals of the 2026-11-01 landings** (git config under admitted `git diff`, `--text` refused, the re-anchor rule's rewrite blind spot): unchanged since 2026-11-01.
- **Environment-only failures on Hawui-Macmini:** now 38, the same on subject and control (full suite measured this session). Use `h_mad_failure_diff.py`, never counts.

**New this session:**

- **HemaSuite claude -p isolation:** landed (`4f2c51f50`..`7b8fc2ad0` on HemaSuite `origin/main`; rebased commit ids). Repo `/Users/kimhawk/orca/HemaSuite`, branch `fix/claude-subprocess-isolation`, worktree `/Users/kimhawk/orca/HemaSuite-claude-isolation`. It is left in place because it holds another session's untracked note `.trail/learnings/2026-11-01-per-call-judge-model-through-the-hawk.md`. Remove the worktree only after that note is moved.
  - Residuals:
    - `--setting-sources ""` is undocumented, so add a token-count canary;
    - a race where the cwd is deleted between the check and the spawn fails one request;
    - drafting quality without the project CLAUDE.md was not measured end to end;
    - `NOTEBOOKLM_QUERY_TIMEOUT` is now dead for the claude path.
- **HemaSuite per-call judge model (`claude-sonnet-5-5`):** user-approved, owned by another HemaSuite session per that note. Precondition met (the isolation merge). Not owned here. Location: repo `/Users/kimhawk/orca/HemaSuite`, worktree `/Users/kimhawk/orca/HemaSuite-claude-isolation` (the note).
- **HemaSuite test rewrites a tracked file mid-run:** `docs/03-analysis/probes/citation-fidelity-judge/backtest_citation_fidelity.out.md` (bytes restored, mtime changed). Found by the row 2903 dogfood. It belongs to HemaSuite; not filed there yet.
- **Token config changed (user-approved):**
  - In `~/.claude/settings.json`, 13 plugins are disabled: 9 LSPs, bkit-starter, learning-output-style, and the duplicate code-review/commit-commands from `claude-code-plugins`.
  - The duplicate global caveman hooks were removed.
  - Backup: `/private/tmp/claude-501/-Users-kimhawk-orca-skills/01ed0d3b-deaa-4fe4-a043-f4e4af1426db/scratchpad/settings.json.bak-123954` (scratchpad, not durable; the file is not in git).
  - The claude.ai connectors are still connected; disconnecting them is the user's action.

## Context for Next Session

**Files touched this session:**
- skills main (`d937cc86`): `h-mad/scripts/h_mad_assemble_tdd.py`, `h-mad/scripts/h_mad_target_identity.py`, `h-mad/references/codex-verifier-prompt.md`, `h-mad/tests/test_h_mad_assemble_tdd.py`, `h-mad/tests/mutation-specs/anchor_check_python.json`, `docs/skill-candidates.md`.
- skills `wip/row-2903-subject-changed` (`81e10cd1`): `h-mad/scripts/h_mad_failure_diff.py`, `h-mad/tests/test_h_mad_failure_diff.py`, `h-mad/tests/test_h_mad_mutation_harness.py`, `handoff/tests/test_mutation_specs_clean.py`, `h-mad/tests/mutation-specs/failure_diff_subject_changed.json`.
- HemaSuite main (`7b8fc2ad0`): `hematology-paper-writer/tools/agent_executor.py`, `hematology-paper-writer/tests/test_agent_executor.py`.
- `.trail/learnings/2026-11-01-row-2729-green-anchor-check-under-hawk.md` (`c0de17d6`).

**Uncommitted changes:** none on main (untracked `.trail/` files only).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
git checkout wip/row-2903-subject-changed && git rebase main   # then Next Step 1
P=/opt/homebrew/opt/python@3.14/bin/python3.14
$P -m pytest h-mad/tests/test_h_mad_failure_diff.py -q
```

**Related docs:**
- `docs/handoffs/2026-11-01-main__backlog-open-rows-to-three.md`
- `docs/skill-candidates.md` (rows 2729 LANDED, 2856, 2890, 2903)
- HemaSuite `hematology-paper-writer/tools/agent_executor.py` (`CLAUDE_ISOLATION_FLAGS`, `_private_claude_cwd`)
