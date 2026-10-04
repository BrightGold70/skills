# Handoff — H-MAD TDD gate blocked a manuscript run outside the feature it guards

**Date:** 2026-10-04
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · main · session 156b7445-4dfd-4393-9c43-c45636039df2
**Taken-Over-By:** skills · main · session 20c02ecf-4fa6-42c2-821f-b93175bcd8e1 · 2026-10-04
**Supersedes:** none — first on this branch for this topic

## Session Summary

HemaSuite triaged the anemia-jmj revision run of 2026-10-03 into code fixes
(`docs/03-analysis/anemia-jmj-improvement-triage-2026-10-04.md` in HemaSuite, row **T**). One row
belongs here. That run was driven by OpenAI Codex. While HemaSuite's
`guideline-web-evidence-admission` feature was in Phase 5, the H-MAD guard rejected the manuscript
pipeline launch. That launch was document work unrelated to the feature. The operator had to pause
the feature's state and restore it afterwards. The run's own suggestion: *scope feature-code guards
separately from authorized manuscript artifact generation.*

**The premise is unverified. Check it before building anything.** The only evidence is one table row
in the run's `Errors_and_Improvements.md`. Its text is quoted below. No hook log, command or
`permissionDecision` payload was kept. The likeliest explanation is one this lane already closed: the
stale `~/.agents` codex copy that the 2026-10-04 upstream-sync session found behind every codex-gate
refusal (`docs/handoffs/2026-10-04-main__upstream-sync-gate-fixes.md`, brief items 1–5). If the
current hook does not reproduce the block, close this brief as covered by that fix.

## Key Learnings

- The run's record, verbatim: *"Unrelated H-MAD feature guard blocked document work | The Phase 5
  guard for `guideline-web-evidence-admission` rejected the pipeline launch. The user explicitly
  authorized a temporary pause followed by restoration. No feature code, tests, ownership, or
  heartbeat fields were changed."*
- A HemaSuite read-only triage agent read the current hook and reported the following. Re-read it
  yourself before relying on it:
  - Bash is never gated; the matcher is `Write|Edit`.
  - Non-`.py` writes are allowed.
  - `_chain_may_hold_state` (`h-mad/hooks/h-mad-tdd-gate.sh:47-48`) returns 0 at
    `_absent_at "$root" || return 0` whenever the project root has `docs/`. That return comes before
    the target-is-outside-root check at `:53-55`, so a Write/Edit of a `*.py` file outside the repo
    (a scratch driver script) during any active Phase 5 can be judged as production code.
  - Hook last touched at `962c47fb`.
  - Note the tension with `2a0cc74d`, which already admits out-of-root writes under `/tmp` that are
    not `.py`.

## Next Steps

1. **Reproduce first** against the current symlinked hook, with a Phase-5 state fixture. The
   2026-10-04 upstream-sync session replayed the live hook the same way. Try two writes:
   - (a) Write/Edit of a `.py` file under `$TMPDIR` or a session scratchpad, outside the project
     root;
   - (b) a Bash `hpw …` / `python -m cli …` launch.

   If neither is denied, close this brief as covered by the stale-copy fix. Record which (a)/(b)
   were tried.
2. **If (a) is denied:** decide whether a target outside `CLAUDE_PROJECT_DIR` (or under `$TMPDIR` /
   the scratchpad) should skip the gate. `_chain_may_hold_state` (`:47-55`) is where the root check
   short-circuits ahead of the target check. Keep fail-closed for unreadable state and for targets
   that cannot be identified (`:132-144`, `:235-240` per the triage).
3. **If (b) is denied:** that contradicts the Write|Edit-only matcher. Find which host config gates
   Bash, starting with the codex hooks under `~/.agents`.

## Open / Blocked Items

- Row T — status: **unverified premise**; blocked on step 1.
  - Location: `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
  - Hook: `h-mad/hooks/h-mad-tdd-gate.sh`.
  - Source record: `/Users/kimhawk/Library/CloudStorage/Dropbox-EUMCIMH/Kim Hawk/Paper/KASCH/2026-09/anemia-jmj/Revision/Errors_and_Improvements.md`
    (table "Issues observed during the work", first row).
  - Triage: HemaSuite `docs/03-analysis/anemia-jmj-improvement-triage-2026-10-04.md` (on HemaSuite
    `main` at `e6e0440b`).
- No h-mad claim exists for this. It was never a HemaSuite feature, so nothing was released.

## Context for Next Session

**Files touched this session (sender side):** none in this repo. HemaSuite landed its quick fixes
`ad940b8d..e6e0440b` on its `main`.

**Uncommitted changes:** this brief is untracked in `docs/handoffs/`. Commit it when you take it over.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
python3 ~/.claude/skills/handoff/scripts/handoff_paths.py pending-handovers
```

**Related docs:**
- `docs/handoffs/2026-10-04-main__upstream-sync-gate-fixes.md` (stale-copy root cause, `2a0cc74d`)
- `docs/handoffs/2026-10-03-main__hmad-codex-gate-project-venv.md` (the prior HemaSuite brief)
