# Handoff — bkit SubagentStop re-wake: h-mad rule, two bkit patches, patch-verify hook (addendum)

**Date:** 2026-10-29
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-28-main__bkit-subagentstop-rewake.md, 2026-10-27-main__grok-pass-task16-14j.md

> **Addendum, not the main line.** The main skills backlog (row 17 test-boundaries, rows 18/28/33…)
> is being driven by the **agy lane** (h-mad owner session `5784fe02`, feature
> `hmad-test-boundaries`, Phase 5, branch `feature/hmad-test-boundaries`). This doc records the
> side work of Claude session `85878391` (skills-aa) and carries the predecessor's items forward
> unchanged where that lane owns them. It was committed on `main` through a temporary worktree,
> because the shared tree `/Users/kimhawk/orca/skills` is checked out on the agy lane's branch.

## Session Summary

Took over the HemaSuite brief on bkit's `SubagentStop` hook re-waking every h-mad author after
DONE, reproduced it here (9 hints, 8 extra DONE turns per stop), and confirmed from the Claude Code
hooks docs that it is designed behaviour (8-continuation cap, reset on any tool call), so the defect
is bkit's. Shipped: a post-DONE rule in all six h-mad agents + `SKILL.md` entry (`ea21a222`,
`3a65a2d0`), a carried bkit SubagentStop patch (`c8df5312`), a carried sprint Stop
`stop_hook_active` guard and a correction of my own false "five blocking handlers" claim
(`278fc850`), and a SessionStart hook that re-verifies all six carried plugin patches after a plugin
update (`d13f5e8f`). Also merged HemaSuite's `fix/suite-timeout` (`12fd1775`). All pushed;
`origin/main` = `d13f5e8f`. Done, except the Mac mini install (Next Step 1).

## Key Learnings

- **`SubagentStop`/`Stop` `additionalContext` keeps the agent running by design** (hooks.md:2610,
  2736-2738): 8-consecutive-continuation cap, overridable by `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, and
  the count **resets on every tool call** — an agent that acts on a hint can be re-woken without
  limit. Measured: 9 hints → 1 real DONE + 8 re-wakes; patched → 0.
- **Read-off-the-source claims about reachability were wrong.** Four of bkit's five
  `outputStopSurface` callers (`pdca-skill`, `plan-plus`, `gap-detector`, `iterator`) return at the
  bare-require guard when `unified-stop.js` `require()`s them; only `sprint-skill-stop.js` (exports
  `run()`) can block. I published the wrong version in `SKILL.md` and #162 before driving it live,
  then corrected both.
- **The shared tree's branch moved under me.** The agy lane checked out
  `feature/hmad-test-boundaries` at 10-28 18:42 KST; my next commit `3c34bba8` landed on their
  branch. Every guard I had (exact staged paths, diff checks, green suite) passed — none reads the
  branch. Repaired by `cherry-pick -x` onto `main` (`278fc850`) via a temp worktree. Memory:
  `feedback_shared_tree_branch_before_commit.md`.
- **The h-mad host-construct parity check flags any backticked Claude Code hook name in a skill
  file.** Naming `` `SubagentStop` `` in `SKILL.md` failed
  `test_live_registry_and_skill_files_are_clean` until it was added to the `hook-event` pattern in
  `h-mad/references/host-constructs.json` (+ one branch sample in the parity test).
- **The full h-mad suite is ~40-44 min and `rtk proxy` buffers its output** — an empty output file
  mid-run is not a hang; a pytest at 0% CPU was waiting on subprocess-spawning tests.

## Next Steps

1. **Install the patches + patch-verify hook on Hawui-Macmini** (the predecessor names it as the
   other Mac; not the MacBook). Pull `main`, apply each `docs/patches/bkit-*/*.patch` per its
   README, `cp docs/patches/patch-verify-on-update.sh ~/.claude/hooks/`, add the SessionStart entry
   (`"command": "bash $HOME/.claude/hooks/patch-verify-on-update.sh", "timeout": 120`), then
   `rm -f ~/.claude/state/patch-verify.state` and run the hook once; it must print nothing.
   Not reachable from the Mac Studio session (no SSH host, no live session there).
2. **Check bkit #162 for a maintainer reply** — `gh issue view 162 -R ww-w-ai/bkit-claude-code`.
   If upstream ships the fix, drop the matching local patch (its `verify.js` will then report the
   patch MISSING with the behaviour already correct — read the README before re-applying).
3. **Check whether the agy lane read the note about `3c34bba8`** — `memory_message_list` on
   workspace `default`, project `brightgold70-skills` (list, do NOT pop: it is a shared inbox and
   the note is addressed to that lane). Dropping the commit is their call.

## Open / Blocked Items

**This session:**

- **`3c34bba8` sits on `feature/hmad-test-boundaries`** (the agy lane's branch, local only). Same
  change is on `main` as `278fc850`. Note left in the ai-memory inbox (msg `01a18541…`, pending,
  unread as of 02:33Z) and in the Orca worktree comment. Keep → later merge is clean; drop →
  `git rebase --onto 35b013b5 3c34bba8 feature/hmad-test-boundaries` when that lane is idle.
  Status: their decision. repo: `/Users/kimhawk/orca/skills` · branch: `feature/hmad-test-boundaries` · worktree: the shared tree.
- **bkit #162** (`ww-w-ai/bkit-claude-code#162`, repo moved from `popup-studio-ai`): open, no
  maintainer response, `bug` label did not attach; correction comment posted. Status: watch.
- **Two new carried bkit patches**, applied on the **Mac Studio only**, bkit 2.1.40:
  `docs/patches/bkit-subagentstop-additionalcontext/` and `docs/patches/bkit-sprint-stop-hook-active/`.
  Status: watch (the hook now does the watching on this Mac).
- **`~/.claude/hooks/patch-verify-on-update.sh` is a copy** of `docs/patches/patch-verify-on-update.sh`;
  re-copy after editing the repo version. It only re-checks when installed plugins or the verify
  scripts change — delete `~/.claude/state/patch-verify.state` to force a check.
- **HemaSuite phantom bkit `tools` feature:** already gone (primaryFeature `None` in both HemaSuite
  state files; bkit's own generator returns no hint). Closed — no edit made.
- **Security-review flag on `h-mad/scripts/h_mad_audit_gate.py` (`if False:`)**: transient,
  uncommitted, in the agy lane's tree; the line reads `if not tb_ok:` again and the code is on no
  committed ref. Closed for this lane; theirs if it recurs.
- **h-mad claim `bkit-subagentstop-rewake`** in `docs/.bkit-memory.json` held by `85878391`: the
  work is done; released at this closeout.

**Carried from `2026-10-28-main__bkit-subagentstop-rewake.md` (the HemaSuite brief):**

- Next Step 1 (reproduce): **closed** — 9 hints / 8 re-wakes, transcript in session `85878391`.
- Next Step 2 (h-mad defence): **closed** — options (a)+(b) shipped in `ea21a222`; (c) noted in
  the `SKILL.md` bullet; (d) detector not built (not worth it — the hook is now patched and verified).
- Next Step 3 (vendor fix): **closed** — `c8df5312` + #162.
- Next Step 4 (HemaSuite phantom features): **closed** — already cleared, see above.
- Open: CC behaviour documented vs regression — **closed** (documented, hooks.md:2610).
- Open: main-session `Stop` hook — **closed** (only `sprint` can block; guarded in `278fc850`).
- Open: `fix/suite-timeout` lane — **closed**, merged as `12fd1775` at hemasuite-81's request;
  worktree `skills-suite-timeout` removed, branch kept.

**Carried from `2026-10-27-main__grok-pass-task16-14j.md`** (driven by the agy lane unless noted):

- Next Step 1 / row 17 scope: **in progress in the agy lane** as h-mad feature
  `hmad-test-boundaries`, Phase 5 (commit `35b013b5` on `feature/hmad-test-boundaries`).
- Next Step 2 / `grok-audit-surface` Task 17: **closed** — `c018f177` (S4 route) and `9f330f71`
  (closure + archive).
- Next Step 3 / row 28 split: unchanged since 2026-10-27.
- Next Step 4 / row 18 brainstorm: unchanged since 2026-10-27.
- Next Step 5 / triage rows 33, 35, 38, 39, 44, 46: unchanged since 2026-10-27
  (`docs/03-analysis/2026-10-25-backlog-triage.md`).
- bkit G-004 + G-001 patches: applied on the Mac Studio; **Hawui-Macmini still owed** — folded into
  Next Step 1 above. Now also watched by the patch-verify hook on this Mac.
- G-001 upstream `ww-w-ai/bkit-claude-code#161`: watch, unchanged.
- New `skill-candidates` rows (census OPEN 31): open backlog, unchanged.
- HemaSuite `document-intake-source-review::Task 6` WIRE-RUNNER: owed by HemaSuite, unchanged.
- Wire-registry `missing=268`: blocked on a HemaSuite checkout, unchanged.
- Codex pin `term_134b0865…` stale — re-pin before any codex dispatch: unchanged.
- Run 8 attempts 1-2 are evidence only, never score: unchanged.
- Rows 23 and 34 (local-only `verify-hmad-*` skills; ~179 leaked `hmad_exec_prompt.*` temp files):
  unverified, actionable on this Mac, unchanged.
- Rows blocked on HemaSuite (41, 49, 50, 52) and watch-only rows: unchanged.

## Context for Next Session

**Files touched this session (all committed and pushed on `main`):**
- `h-mad/agents/{spec,plan,design,implplan}-author.md`, `h-mad/agents/{doc-auditor,change-reviewer}.md`
- `h-mad/SKILL.md` §"Known interactions" (bkit SubagentStop entry)
- `h-mad/references/host-constructs.json`, `h-mad/tests/test_host_construct_parity.py`
- `h-mad/tests/test_h_mad_subagentstop_rewake_docs.py` (new, 28 tests, mutation-checked)
- `docs/patches/bkit-subagentstop-additionalcontext/`, `docs/patches/bkit-sprint-stop-hook-active/`
- `docs/patches/patch-verify-on-update.sh`
- `docs/handoffs/2026-10-28-main__bkit-subagentstop-rewake.md` (Taken-Over-By stamp)

**Outside the repo:** `~/.claude/settings.json` (one SessionStart entry),
`~/.claude/hooks/patch-verify-on-update.sh`, bkit 2.1.40 cache (two patches applied),
memory `feedback_shared_tree_branch_before_commit.md`.

**Worktree:** the shared tree `/Users/kimhawk/orca/skills` is on `feature/hmad-test-boundaries`
(agy lane, live, uncommitted work present). Do skills `main` work in your own worktree.

**Uncommitted changes:** none of this session's; the shared tree's are the agy lane's.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git fetch && git log --oneline -1 origin/main          # expect d13f5e8f or later
git rev-parse --abbrev-ref HEAD                         # if not main: work via a worktree
git worktree add <scratch>/mainwt main
for v in docs/patches/*/verify.js; do node "$v" | tail -1; done
```

**Related docs:**
- `docs/patches/bkit-subagentstop-additionalcontext/{README,UPSTREAM-REPORT}.md`
- `docs/patches/bkit-sprint-stop-hook-active/README.md`
- https://github.com/ww-w-ai/bkit-claude-code/issues/162
- https://code.claude.com/docs/en/hooks.md (Stop / SubagentStop decision control)
