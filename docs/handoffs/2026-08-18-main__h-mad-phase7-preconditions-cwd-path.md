# Handoff — `h_mad_phase7_preconditions.py` resolves the analysis path against CWD

**Date:** 2026-08-18
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session 18ecfc0f-bc2d-404c-935d-b6fde4aa9faf

## Session Summary

Found while running H-MAD Phase 7 for HemaSuite feature #53: `h_mad_phase7_preconditions.py` reports
**BLOCKED or READY for the same feature depending on which directory you invoke it from**, because it
joins the analysis doc's relative path onto the process CWD instead of resolving it against the state
file it was handed. Diagnosed and reproduced, **not fixed** — the fix belongs in this repo, not in
HemaSuite where it was found. Nothing here is claimed; there is no h-mad state to release.

## Key Learnings

- The state file argument already names the project tree the feature belongs to, so it is the only
  meaningful anchor for the analysis path. CWD is not — H-MAD is routinely driven from a monorepo
  root against a sub-project's state file, which is HemaSuite's entire layout
  (`hematology-paper-writer/docs/.bkit-memory.json`).
- The failure direction observed was *safe* (false BLOCKED). The mirror image is not: run it from a
  tree that happens to have a file at the same relative path and it reports **READY on someone
  else's analysis**, which is a gate passing on the wrong evidence.

## Next Steps

1. **Reproduce** — two invocations, identical state and files, only CWD differs:
   ```bash
   # from the monorepo root, absolute state path
   cd /Users/kimhawk/orca/HemaSuite
   python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py \
     hematology-paper-writer/docs/.bkit-memory.json --feature article-path-ledger-wipe
   #   -> PHASE7: BLOCKED blockers=1 / analysis_missing: no gap analysis at
   #      docs/03-analysis/article-path-ledger-wipe.analysis.md

   # from the sub-project
   cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
   python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py \
     docs/.bkit-memory.json --feature article-path-ledger-wipe
   #   -> PHASE7: READY blockers=0
   ```
   Note the feature is now archived, so the analysis lives at
   `hematology-paper-writer/docs/archive/2026-08/article-path-ledger-wipe/…analysis.md` — pick any
   currently-live feature to reproduce against, or temporarily restore a path.
2. **Fix** — resolve the analysis path against `Path(state_file).parent` (the writer scripts in this
   repo already do this), not against CWD.
   `h-mad/scripts/h_mad_phase7_preconditions.py`
3. **Regression test** — invoke the check from two different CWDs against one state file and assert
   the verdict is identical. Without that, the next refactor reintroduces it silently, since both
   verdicts look plausible in isolation.
4. **Sweep the sibling scripts** for the same shape — anything under `h-mad/scripts/` that takes a
   state-file argument and then opens a relative doc path is exposed to this.

## Open / Blocked Items

- **The cwd-relative resolution itself** — status: diagnosed and reproduced, not fixed. Ownership is
  being transferred here with this brief; it was found in HemaSuite but the defect is entirely in
  this repo's `h-mad/scripts/`.
- **`~/.claude/skills` is not a separate checkout** — status: context, not a task.
  `~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py` resolves to
  `/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_phase7_preconditions.py`, so an edit here is live
  for every project immediately. See `[[feedback_skills_symlink_couples_repos]]`.

## Context for Next Session

**Files touched this session:** none in this repo — this brief is the only artifact.

**Uncommitted changes:** none from this handover.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
sed -n '/analysis/p' h-mad/scripts/h_mad_phase7_preconditions.py   # find the path join
```

**Related docs:**
- Originating session's handoff:
  `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-18-main__aplw-shipped-attribution-order-fixes.md`
- Tracked in the sender's list as **#112**.
