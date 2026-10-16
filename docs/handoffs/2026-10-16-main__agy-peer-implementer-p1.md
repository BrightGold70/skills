# Handoff — #41 brief fixes landed; agy-coder-fallback Phase 1 approved

**Date:** 2026-10-16
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-10-16-main__branch-evidence-flake-recon.md, 2026-10-16-main__hmad-notebooklm-carry-fixes.md

## Session Summary

This session resumed from the flake-recon handoff, traced the blind-adjudication count gap, verified
`land-on-main-from-worktree` on HemaSuite, took over HemaSuite's #101 brief and landed 2 of its 3 h-mad fixes:
- `31d17ac8` — `h_mad_assemble_tdd.py` inlines the global impl-plan sections a task cites.
- `083a8233` — `h_mad_phase7_preconditions.py` gains `--docs-root`.

Each fix was verified by a full `h-mad/tests` run: 6035 and 6042 passed.

It then started a new H-MAD feature, **`agy-coder-fallback`**, which makes agy a peer Phase-5 implementer
with Codex's standing. Phase 1 is approved (brainstorm v1.1, `d0617f0e`); Phase 2 (spec) is next and
should start in a fresh session, because this one ended at about 50% of the context window.

## Key Learnings

- **The blind-adjudication gap (5931 vs 5929) is closed.** The 2 extra tests are cases that
  `test_h_mad_portable_timeout.py` adds for each script it scans
  (`[h_mad_blind_adjudication.py]` × 2 tests). I found them by diffing `--collect-only` output between
  `d5797898` and the same commit with the feature cherry-picked. A new script grows test counts
  outside its own test file. `[gotcha, 0.7]`
- **Only anaconda's interpreter has pytest here.** That is `/opt/anaconda3/bin/python3`; there is no
  xdist, so `-n auto` errors. A bare `python3 -m pytest --version` "works" only because the rtk hook
  rewrites it. A background `… | tail || true` masked the xdist error as exit 0, so run the suite
  without `|| true` and append `RC=$?` to a log. `[gotcha, 0.7]`
- **Calibrate a citation-resolver on the corpus before choosing halt vs. report.** 241 impl-plans
  carried 220 unqualified `§"…"` citations that point at other documents; halting on them would have
  refused nearly every plan. `[pattern, 0.7]`
- **New code can silently break mutation anchors that already exist.** It does this by duplicating
  their text (2 rows started matching twice) or by rewriting the anchored line. Run `--check-anchors`
  over all specs after the change, and fix your own code or re-anchor that row to the same intent.
  `[gotcha, 0.7]`
- **agy already has a PreToolUse hook contract,** documented in `h-mad/references/agy-runtime.md`
  §"Hooks". The halt `step5:agy_tdd_hook_unverified` stays in force until a real refusal by an agy
  gate is observed.

## Next Steps

1. **agy-coder-fallback Phase 2 (spec)** — in a fresh session: `/clear`, then `/h-mad "agy-coder-fallback"`.
   - The router should answer `resume_manual` at phase 2. Claim the feature, then dispatch the
     `spec-author` teammate.
   - Source: `docs/01-plan/features/agy-coder-fallback-brainstorm.md` v1.1. It records 6 operator
     decisions and 8 open questions for the spec to settle: `run_command` residual, hook scope, payload
     cwd, timeout, availability probe, project default, where the non-independent flag lives, audit legs.
2. **Brief fix 3 (#8): WIRE-PIN new-caller RED case** — `h-mad/references/codex-implementer-prompt.md:68`
   and the RED clause at `:60`. Fold it into agy-coder-fallback's Phase 5, because that feature makes
   the prompt implementer-neutral, so the prompt changes once.
3. Triage the open skill-candidate rows: `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`.
   - It showed OPEN=13 at session start; run it again after this closeout's scout.
   - 2595 duplicates 2576, and 2598 duplicates 2582.
   - (e) :2549 is the same idea as HemaSuite's `tdd-judge-test-file-budget`.

## Open / Blocked Items

**New this session:**
- `agy-coder-fallback` — status: Phase 1 complete, Phase 2 next. State: `last_completed_phase=1`,
  `current_phase=2`, claimed by session b8b4a01f (released at this closeout). Key decisions:
  - agy is a **peer** of Codex (not a fallback): per-feature `implementer=codex|agy` with an automatic,
    recorded peer switch;
  - an agy-authorship gate on the Claude side, plus an agy-native write gate;
  - agy reviews its own code, flagged non-independent, even when Codex is available;
  - a live tracer task.
  The slug says "fallback" but is kept on purpose; see the brainstorm's slug note.

**Carried from `2026-10-16-main__hmad-notebooklm-carry-fixes.md`**
(Handover-From HemaSuite · main · session 0980df8b; taken over by session b8b4a01f, stamped in `c54b6f1e`):
- **Fix 1, assemble_tdd global sections:** CLOSED `31d17ac8`.
  - Unresolved `§` citations are reported under `PASS`, not halted. This departs from the brief, on the
    220-of-241 calibration.
  - 12 tests, 9 mutation rows, ALL_CAUGHT 48/48.
- **Fix 2, phase7 `--docs-root`:** CLOSED `083a8233`. 7 tests, 4 mutation rows + 1 re-anchored; 8/8 and 6/6.
- **Fix 3, WIRE-PIN new-caller rule:** OPEN, unchanged; re-verified 2026-10-16 (no "new caller" text
  at `codex-implementer-prompt.md:68`). See Next Step 2.
- Evidence sources (read-only): repo `/Users/kimhawk/orca/HemaSuite` · branch `main` · worktree none ·
  `docs/archive/2026-10/notebooklm-integration-interface/{…report.md, …analysis.v1.md}`,
  `docs/handoffs/2026-10-16-main__notebooklm-feature-complete.md`.
- Feature record `hmad-notebooklm-carry-fixes` is claimed in `docs/.bkit-memory.json`. It stays open
  until fix 3 lands.

**Carried from `2026-10-16-main__branch-evidence-flake-recon.md`:**
- **Blind-adjudication 5931-vs-5929 gap:** CLOSED this session (see Key Learnings).
- **`land-on-main-from-worktree` on HemaSuite main:** CLOSED. Verified still open as a candidate;
  status lines for :1413 and :1414 were pushed to HemaSuite main as `79bde9041`. It overlaps
  `ff-land-quick-fix` (1367/1376) and `ff-guarded-push` (1330).
- **Census rows:** OPEN=13 (11 maybe + 2 yes), not the 10 the predecessor said, because its own scout
  appended 2595/2598/2603. Next Step 3.
- **NS2, HemaSuite feature/204 `INCOMPLETE reason=no-mutation-spec`:** unchanged; HemaSuite's call.
- **Unchanged since 2026-10-05:** deferred rows 1931, 1624, 1679, 1662, 1387, 1348, 2113, 2288.
- **Unchanged since 2026-10-12:** rows 2364/2395/1269 (deferred) and 2481/2496 (maybe).
- **Unchanged:** concurrent HemaSuite sessions share the live skill through symlinks, so mutation
  sweeps run in throwaway worktrees.
- **Unchanged:** `#56` residue trichotomy, graft statusline, review residuals on rows 1406/1937/1685,
  pass-log rotation, the accepted over-refusals (2026-10-06), V-11.1 residuals, `tdd-gate-fail-opens`
  bookkeeping.
- **Foreign `stash@{0}` (resolved-model):** unchanged; do not touch.
- **Bash pin blast radius:** unchanged (`h_mad_bash4_fence_probe.py`).
- **Memory index above the 17500 compaction target:** unchanged; not re-measured.
- **NS1, other-Mac cleanup:** withdrawn by the operator 2026-10-15; no further carry.
- **HemaSuite canonical checkout:** 1 ahead and 1 behind `origin/main`, with uncommitted `graft/` edits
  from another lane. Not pulled. Run `git -C /Users/kimhawk/orca/HemaSuite pull --rebase` when that
  lane is idle.

## Context for Next Session

**Files touched this session:**
- skills: `h-mad/scripts/h_mad_assemble_tdd.py`, `h-mad/tests/test_h_mad_assemble_tdd.py`,
  `h-mad/tests/mutation-specs/assemble_tdd.json` (`31d17ac8`)
- skills: `h-mad/scripts/h_mad_phase7_preconditions.py`, `h-mad/tests/test_h_mad_phase7_analysis_anchor.py`,
  `h-mad/tests/mutation-specs/phase7_analysis_anchor.json`, `h-mad/SKILL.md` (`083a8233`)
- skills: `docs/handoffs/2026-10-16-main__hmad-notebooklm-carry-fixes.md` (Taken-Over-By),
  `docs/01-plan/features/agy-coder-fallback-brainstorm.md`
- HemaSuite: `docs/skill-candidates.md` (`79bde9041`, from a throwaway worktree, since removed)

**Uncommitted changes:** none besides this handoff and its learnings.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch        # expect main...origin/main
# then: /h-mad "agy-coder-fallback"   → Phase 2 spec
```

**Related docs:**
- `docs/01-plan/features/agy-coder-fallback-brainstorm.md` (v1.1)
- `h-mad/references/agy-runtime.md` §"Hooks", §"The TDD gate"
- `h-mad/SKILL.md` §"Codex authors Phase 5", §"Exit-code dispatch for 5d/5e"
- `docs/handoffs/2026-10-16-main__hmad-notebooklm-carry-fixes.md`
