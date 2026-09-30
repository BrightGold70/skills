# Handoff — HemaSuite's TDD-gate pin expects `kind=test-missing`; installed gate emits `kind=no-test-resolved`

**Date:** 2026-09-30
**Branch:** feature/tdd-gate-fail-opens
**Project:** skills
**Handover-From:** HemaSuite · main · session e4aeb3fb-1b4d-4aed-be7a-7874d48f2ca2
**Taken-Over-By:** skills · feature/tdd-gate-fail-opens · session bf7373d5-4abf-4023-9aaf-a20cfdd3be27 · 2026-09-30
**Supersedes:** none — first on this branch for this item

## Session Summary

A HemaSuite-side test that pins the **installed** h-mad TDD gate fails on HemaSuite `main`, and it failed before the
`review-comment-class-calibration` feature too, so it is not a HemaSuite regression. The gate and judge that produce the
verdict live here (`h-mad/hooks/h-mad-tdd-gate.sh` → `h-mad/scripts/h_mad_tdd_judge.py`), and this lane is actively
rewriting that gate, so this is the lane that knows which `kind` is intended. Handed over, not fixed.

## Key Learnings

- The deny text carries a clue worth checking before deciding who is wrong: `name map: empty for does_not_exist.py`.
  The hook was invoked with `hematology-paper-writer/tools/does_not_exist.py`, but the name map was asked about the bare
  basename. Either the relativisation against the project root lost the directory prefix, or the fixture's root is not
  what the judge thinks it is. If the name map had received the full relative path it might have mapped to a candidate
  test and produced `test-missing` (the `_test_missing` path, `h_mad_tdd_judge.py:184-185`), which is what the pin expects.
- The hook is a live symlink: `~/.claude/hooks/h-mad-tdd-gate.sh` → `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`.
  HemaSuite's suite therefore exercises **whatever branch this checkout is on** — currently `feature/tdd-gate-fail-opens`,
  not skills `main`. The `no-test-resolved` kind was introduced by `codex-tdd-gate-defects` Task 8 (`3d733de0`, already
  on skills `main`), so the drift is not specific to this branch either.

## Next Steps

1. Reproduce from HemaSuite (canonical venv, since the worktree venv has no pytest):
   ```bash
   cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
   .venv/bin/python -m pytest tests/test_h_mad_tdd_gate.py::test_phase5_active_blocks_production_without_test -q
   ```
   Observed 2026-09-30 (1 failed, 8 passed in that file):
   `[H-MAD-TDD-GATE] BLOCK kind=no-test-resolved: no test resolved; …/docs/01-plan/features/test-feature.impl-plan.md: absent; name map: empty for does_not_exist.py`
2. Decide which side is wrong:
   - **The judge is wrong**: the name map received a basename instead of the root-relative path (`h_mad_tdd_judge.py:281-289`, the `rel = real_target.relative_to(real_root)` step). Fix it here, test-first.
   - **The pin is stale**: `no-test-resolved` is the correct verdict for an unmapped path with no impl-plan. Then HemaSuite's assertion at `hematology-paper-writer/tests/test_h_mad_tdd_gate.py:116` should change. That edit belongs to HemaSuite `main`; say so in your closeout, or hand it back.
3. Whichever you choose, re-run step 1 as the acceptance check.

## Open / Blocked Items

- HemaSuite pin drift — status: not started. repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: any HemaSuite main
  worktree (e.g. `/Users/kimhawk/orca/workspaces/HemaSuite/review-comment-class-calibration`) · test:
  `hematology-paper-writer/tests/test_h_mad_tdd_gate.py:112-116` · gate: `h-mad/hooks/h-mad-tdd-gate.sh:232`,
  judge: `h-mad/scripts/h_mad_tdd_judge.py`.
- Claim: none. No h-mad feature was claimed for this item on either side, so nothing was released.

## Context for Next Session

**Files touched by the sender:** none. The sender only read files.

**Uncommitted changes:** not applicable to the receiver.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills   # feature/tdd-gate-fail-opens
# /handoff takeover  → adopts this brief
```

**Related docs:**
- Sender's closeout: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-30-main__rcc-closed-jev-gate-passed.md` (Open / Blocked Items).

## Resolution (2026-09-30, session 9cfdf8ab)

**Decided: the skills side was wrong; HemaSuite's pin is correct.** The premise "it failed before this feature too" did not hold: skills `main` and this feature's base `15681a53` both give `kind=test-missing`; only `feature/tdd-gate-fail-opens` gave `no-test-resolved`. Cause: `h-mad/hooks/h-mad-tdd-gate.sh` built `PRODUCTION_TARGET=$CANON_PREFIX/$NAME`, and `CANON_PREFIX` is the deepest EXISTING directory, so absent intermediate directories collapsed to `<root>/<name>`. Fixed test-first: RED `13f18121`, GREEN `e1dfed23` (`${CANON_TARGET%/*}/$NAME`, mutation row CG-PARENT). Acceptance: HemaSuite `tests/test_h_mad_tdd_gate.py` 9 passed. No HemaSuite change needed.
