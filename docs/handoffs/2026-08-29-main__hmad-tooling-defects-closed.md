# Handoff — two h-mad tooling defects closed (inbound handover from HemaSuite)

**Date:** 2026-08-29
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Took over the inbound handover in `docs/handoffs/2026-08-29-main__hmad-tooling-defects.md` (from
HemaSuite session f419d046) and closed both defects it carried. Each got a root-cause fix, a
regression test, and a mutation spec; both specs are ALL_CAUGHT (11/11). Merged to `main` as
`2b569da` and pushed — `main` is in sync with `origin/main`, tree clean, and the fixes are live via
the `~/.claude/skills/h-mad` symlink. **Done, not partial**: the action queue from the brief is
empty and nothing is parked.

One of the brief's premises did not survive verification — see Key Learnings — so the inbound doc
was corrected in the same pass rather than left to mislead the next reader.

## Key Learnings

- **`git show <sha>:<path>` resolves `<path>` from the work tree root, not from the cwd it runs
  in** — unlike pathspec arguments (`check-ignore`, `ls-files`), which *are* cwd-relative. Mixing
  the two in one module is how J49 hid: `trackedness()` was correct with a cwd-relative path while
  `load_base()` silently read a different project's file, and both spellings look identical on the
  page.
- **A defect that is invisible in the common configuration is not a rare defect, it is an unobserved
  one.** J49 could only be seen where cwd ≠ git root, so the nested fixture is not an edge case in
  its tests — it is the only configuration where the guard is observable at all. A single-project
  fixture would have passed against the broken code.
- **A guard's escape hatch must not be the practice the guard exists to prevent.** J48's writer
  validated the whole merged record, so a key that arrived by hand-edit made the record unwritable
  by the only tool allowed to write it — leaving the hand-edit as the sole way out. The fix is a
  sanctioned repair verb, not a wider schema: widening buys a record's mobility by permanently
  declaring a field nothing reads.
- **Where you put a precondition check decides which tests you break.** Moving the git-root lookup
  into `_registry_base_path` broke 14 tests that stub `load_base`, because `verify` computed the
  path *eagerly* as an argument to the stub. The fix was to let the no-work-tree case fall through
  to git's own refusal rather than raise early — one refusal, at the layer that actually consults
  git. Worth checking before hardening any function whose result is passed to something tests
  monkeypatch.
- **Never run the mutation harness and the test suite against the same tree at once.** The harness
  edits source in place and reverts after each mutation; a concurrent `pytest` reads whatever the
  harness happens to have applied. Cost two discarded suite runs before I noticed the results were
  meaningless — the failures looked like real regressions.
- **A handoff premise is a claim, not a fact.** Next Step 2 of the inbound brief asked me to find
  "whatever in the Phase-5 flow wrote them" — nothing did. A two-minute grep settled it before any
  code was written; adopting the premise would have meant hunting a writer that does not exist.

## Next Steps

Both handed-over items are closed and nothing is parked — this is a clean stopping point. These are
genuine follow-ups, none urgent.

1. `[suggested]` Consider whether `h_mad_state_write.py --drop-undeclared` should also be reachable
   from the resume path, so a bricked record is repaired where it is first *noticed* rather than
   only where an operator thinks to look — `h-mad/scripts/h_mad_resume_decision.py` currently
   returns a routing token and never inspects the record's key set.
2. `[suggested]` The same root-vs-cwd confusion may exist elsewhere: audit other `git show`
   call sites for repo-relative paths built from something other than the work tree root —
   `grep -rn '"show", f"' h-mad/scripts/` is the starting point. Only `h_mad_wire_registry.py` was
   checked this session.

## Open / Blocked Items

None. The two inbound items (#48, #49) are done and the source brief has been corrected to say so.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_wire_registry.py` — `_git_root()` added; `_registry_base_path()` resolves against the git root and refuses an outside registry
- `h-mad/scripts/h_mad_state_write.py` — `_refusal()`, `drop_undeclared()`, `--drop-undeclared` CLI flag
- `h-mad/scripts/h_mad_state_validate.py` — `undeclared_keys()`, `_schema()` cache
- `h-mad/SKILL.md` — repair-verb guidance + both inventory lines
- `h-mad/tests/test_h_mad_wire_registry.py` — nested-project fixture + 4 tests
- `h-mad/tests/test_h_mad_state_write.py` — `TestUndeclaredKeys` (9 tests)
- `h-mad/tests/mutation-specs/wire_registry_base_path.json` — new (4 mutations)
- `h-mad/tests/mutation-specs/state_undeclared_keys.json` — new (7 mutations)
- `docs/handoffs/2026-08-29-main__hmad-tooling-defects.md` — corrected: both items marked DONE, and the Phase-5-writer premise retracted

**Verification performed:**
- Full suite on the merged tree: **2274 passed, 2 skipped** (4m45s), run with nothing else touching the tree
- Both mutation specs: **ALL_CAUGHT**, 11/11, each mutation killed by its own named test
- Anchors re-checked after the merge: `ANCHORS_OK specs=2 mutations=11 drifted=0`
- Live skill confirmed through the symlink (`--drop-undeclared` present in the real CLI help)

**Worktree:** none remaining. Work was done in `.claude/worktrees/hmad-tooling-defects` (branch
`worktree-hmad-tooling-defects`) so the live skill stayed untouched while other sessions ran against
it; both were removed after the merge — `git branch -d` verified the branch was fully merged first.

**Uncommitted changes:** none at the time of drafting — tree clean, `main` in sync with
`origin/main` at `2b569da`. This handoff and the brief correction land on top of it.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
```

**Related:**
- Inbound brief: `docs/handoffs/2026-08-29-main__hmad-tooling-defects.md` (now corrected)
- The run that found both: HemaSuite `feature/202-guideline-claim-like-visibility`, merged as `911a377f`
- Sibling defect fixed earlier in this lane: `2b3b4f0` — a fully-acknowledged gate section is clean, not off-template
