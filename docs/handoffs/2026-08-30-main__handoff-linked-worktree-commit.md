# Handoff — the handoff skill orphans its own doc when WRITE runs from a linked worktree

**Date:** 2026-08-30
**Branch:** `main`
**Project:** `/Users/kimhawk/orca/skills` (the `handoff` skill)
**Handover-From:** HemaSuite · main · session 756df57f-fc81-4d46-b845-01e658cd0bf4

## Session Summary

WRITE mode resolves the canonical **main-worktree** handoff store and writes the doc there, then
its "Commit and push" finale **deliberately declines to commit** when it detects it is running from
a linked worktree. Under Orca, where sessions routinely run in sibling worktrees, that combination
writes a file nobody stages. **Three docs became untracked orphans on 2026-08-29 with zero commits
across all refs**, one of them the doc a session had just resumed from. Two sessions have now
worked around it by hand with a disposable worktree. Nothing is fixed; this brief hands the fix
over. **Scoped and evidenced, not started** — no branch, no code.

## Key Learnings

- **The two halves are individually correct and jointly broken.** Writing to the canonical store is
  right (`handoff/SKILL.md:794-799` — every parallel worktree reads one store, and the doc survives
  worktree removal). Declining to commit into the main worktree is also right (`:910` — that tree
  may be mid-work on an unrelated branch). The defect is that nothing closes the loop between them,
  so the honest "I did not commit this" note is the last thing that ever happens to the file.
- **The failure is silent in the worst direction.** WRITE reports success, the doc exists on disk,
  the INDEX entry is written, and the learnings land. Every observable says the handoff worked. Only
  `git log --all -- <path>` returning zero commits shows otherwise, and nothing prompts anyone to run
  it.
- **The obvious fix — copy the files into a clean worktree and commit — is a trap.** Measured
  2026-08-30: the shared HemaSuite checkout was **125 commits behind** with another session's
  uncommitted work, so copying its `docs/learnings.md` and `docs/skill-candidates.md` wholesale
  would have **deleted 40 and 120 lines** that exist on main. Any automated fix must re-apply *this
  session's additions* onto a clean base, never copy whole files.
- **A stale checkout does not error, it under-reports.** The skill-candidates census run in that
  125-behind tree returned `128 yes / 191 open`; the same command on `origin/main` returned
  `138 yes / 211 open`. If the scout phase moves into a clean worktree as part of this fix, that is
  a second bug it closes for free.
- **`git rev-parse --git-common-dir` is the detection that already works** (`handoff_paths.py:36-53`,
  `canonical_root`). The fix does not need new detection — it needs a *destination* for the commit
  when detection says "linked worktree".

## Next Steps

1. **Reproduce it first, cheaply** — from any linked worktree, run WRITE with `--skip-scout
   --skip-learnings --skip-memories`, then `git log --all --oneline -- <the path it printed>`.
   Zero commits is the bug. Do this before designing; the premise is a claim from a session that
   has stopped.
2. **Pick the destination.** Three shapes, none obviously right — this is the decision the fix turns
   on, and it wants an operator call before code:
   - **(a) Disposable worktree.** WRITE creates a short-lived worktree off `origin/<default>`,
     re-applies this session's additions there, commits, pushes, opens a PR, tears the worktree
     down. This is exactly what two sessions did by hand (HemaSuite PRs #26 and #31), so the shape
     is proven — but it makes WRITE open a PR, which is a large behaviour change for a closeout
     step, and it needs a `gh` dependency the skill does not currently have.
   - **(b) Commit into the main worktree only when it is safe.** If the main tree is clean and on
     the default branch, commit there as today's main-worktree path already does; otherwise fall
     back to (a) or to (c). Smallest change, and it does nothing in the common case that actually
     bites — the main checkout is usually dirty, which is *why* the skip exists.
   - **(c) Stage without committing, and say so loudly.** `git add` the paths in the main worktree
     and make the report state that a commit is owed, with the exact command. Honest and tiny, but
     it still relies on a human acting, which is the step that has now failed three times.
3. **Whatever is chosen, guarantee the loop closes.** The property to test is not "a commit
   happened" — it is that **no path through WRITE ends with an unreferenced file**. A test that
   asserts the happy path leaves the linked-worktree branch exactly as broken as it is now.
4. **Pin it with a doc-test.** `handoff/scripts/test_handover_docs.py` already exercises this
   skill's documented contracts; that is the natural home rather than a new harness.

## Open / Blocked Items

- **The fix itself** — status: not started, scoped only. `repo: /Users/kimhawk/orca/skills ·
  branch: main (no branch cut) · worktree: none`. Key files: `handoff/SKILL.md` §"Commit and push"
  (the skip branch at `:910`, the store resolution at `:794-799`), `handoff/scripts/handoff_paths.py`
  (`canonical_root`, `:36-53`), `handoff/scripts/test_handover_docs.py` (existing doc-test harness).
  **Nothing is claimed** — `h_mad_resume_decision.py` returned `start_fresh` for
  `handoff-linked-worktree-commit` against `/Users/kimhawk/orca/skills/docs/.bkit-memory.json`
  (25 features present, none by that name, no owner). Claim it before working it.
- **Destination decision (Next Step 2)** — status: blocked on an operator call. (a), (b) and (c)
  differ in blast radius, not just implementation: (a) changes what a closeout *does*, (b) is nearly
  a no-op in the case that bites, (c) keeps a human in a loop that has already failed three times.
- **`orca/skills` is 2 commits behind `origin/main`** — status: informational. Pull before cutting a
  branch.
- **The symlink couples this repo to live behaviour** — status: standing constraint, not a blocker.
  `~/.claude/skills/handoff` is a symlink into this checkout, so editing the working tree edits the
  **live** skill for every in-flight session. Per `h-mad/SKILL.md` §"Editing this skill while a run
  is in flight", do the work in a git worktree and merge when clean.

## Context for Next Session

**Evidence, all verified 2026-08-29/30 rather than carried:**
- Three orphans, `git log --all` = 0 commits each:
  `2026-08-28-feature-mmp-impl__impl-plan-cycles-11-25.md`,
  `2026-08-29-feature-mmp-impl__mmp-shipped-to-main.md`,
  `2026-08-29-feature-mmp-impl__phase5d-complete-13-tasks-shipped.md`.
  Rescued into HemaSuite PR #26 (`e42d5a86`).
- A fourth doc *looked* orphaned and was not — it was committed on another branch and read as `??`
  only because the shared checkout was 125 commits behind. **A `??` in a stale checkout is not
  evidence a file is uncommitted**; check `git log --all` before calling anything an orphan.
- 2026-08-30's own closeout hit the same wall and was committed from a disposable worktree
  (HemaSuite PR #31, `ddaac29a`), re-applying only that session's additions onto a clean base.

**Files to touch:** `handoff/SKILL.md`, `handoff/scripts/handoff_paths.py` (maybe — detection
already works), `handoff/scripts/test_handover_docs.py`.

**Uncommitted changes:** none in `orca/skills`; the tree was clean at handover.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only            # 2 behind origin/main at handover
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature handoff-linked-worktree-commit --create --claim "<your-session-id>"
# then reproduce per Next Step 1 before designing anything
```

**Related docs:**
- Sender's closeout: `HemaSuite:docs/handoffs/2026-08-30-main__two-false-premises-main-green.md`
  (its Open Items carry this bug's one-line pointer)
- `handoff/SKILL.md` §"Commit and push (default finale)"
- `h-mad/SKILL.md` §"Editing this skill while a run is in flight"
