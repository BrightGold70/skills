# Handoff — tdd-gate-fail-opens merged to main; HemaSuite briefs resolved

**Date:** 2026-09-30
**Branch:** main
**Project:** skills
**Supersedes:** 2026-09-30-feature-tdd-gate-fail-opens__phase6-archreview-with-fixes.md

## Session Summary

`tdd-gate-fail-opens` is **complete**. It was merged to `main` as `d306820e` and pushed.
- **Suite on the merged tree:** 4872 passed and 1 failed. The failure is the known `test_top_level_key_set_still_matches`.
- **HemaSuite:** its gate tests pass 9/9 through the symlinked hook.
- **Phase 6:** gap analysis v2 scored a 100% match rate. The architectural review ran 7 cycles, which the operator authorised past the cap of 2, and ended `READY_TO_MERGE`.
- **Phase 7:** `PHASE7: READY`. The report and archive are at `docs/archive/2026-09/tdd-gate-fail-opens/`.

Also this session:
- **HemaSuite pin drift resolved** (`e1dfed23`). The skills side was wrong, and HemaSuite needs no change.
- **HemaSuite items (a), (c), (d) triaged.** Rows were filed on main (`198f2908`). (d) is fixed on main (`c820a1ac`: `exec codex` omits the `worker_done` coordinator line).

## Key Learnings

- **Fixtures that make two rules coincide hid two fail-opens that every gate passed:**
  - **M-6** used `tests -> src`, so lexical `..` collapse and kernel `..` collapse gave the same answer. The Codex gate had regressed to ALLOW.
  - **Pin drift** used paths the name map cannot map. The Claude gate judged `$CANON_PREFIX/$NAME`.

  Only a spec-literal fixture exposed them: the Phase 6 gap-analysis agent for M-6, and HemaSuite's own pin for the pin drift.
- **A handover's causal premise was false.** "It failed before this feature too" did not hold. Re-running on main and at the baseline took 2 minutes and reversed who owned the fix.
- **agy review cycles oscillated.** Cycle 2 demanded moving the on-disk lookup into the canonicaliser. Cycle 4 called that same move a design violation, because the design text lagged. When a finding contradicts an earlier operator decision, update the design; do not revert the code.
- **The T0 probe measured nothing on FR-8.** Its `python3` shim sits in an untrusted directory, so the Codex gate refused every cell for that reason alone. A probe cell that denies in both readings needs its deny reason checked.
- **Wire pins registered at 5c were h-mad-relative, so `verify --rootdir .` reported them missing.** Parametrised pins need every case listed.
- **The h-mad context-budget hook assumes a 1M-token window.** It reported 80.8% when the real figure was about 41%, and the loop was stopped early on it.

## Next Steps

1. **Operator decisions from gap analysis v2** (`docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.analysis.v2.md` §"Design-vs-spec items"):
   - **D-1:** spec FR-3 wording lags design v1.4's root-refuse.
   - **D-2:** Codex parity on a mode-000 root (`rglob` swallows `EACCES`).
   - **D-3:** the design v1.5 conjunct residual (a mis-cased root).
   - **D-4:** the spec's M-18/AC-3.3/AC-6.1 text for the Codex M-14 cell.
   - **N-1:** `..` through a mode-0311 directory is now refused `judge-error` when governed. Accept and document it, or narrow it.
2. **Carried residuals** (report §"Carry Items"):
   - the `UnicodeDecodeError` escape in `session_id_from_git_dir`;
   - two load-sensitive timing tests;
   - three pre-feature mutation specs with absolute `/opt/anaconda3/bin/python`;
   - missing MANUAL R-4/R-5 lines in `reading-fixed.txt`;
   - the Task 6 differential should gain name-map-mappable fixtures.
3. **Skill-candidate rows (a) and (c)** (`docs/skill-candidates.md`, 2026-09-30 section) are parked:
   - (a) audit-cycle scores the self-reported zero evidence without checking the transcript;
   - (c) the assembler never asks for mutation rows.

## Open / Blocked Items

- **Operator items D-1..D-4, N-1** — status: awaiting decision (Next Step 1).
- **Pre-existing failure `test_top_level_key_set_still_matches`** (live-binary drift) — unchanged.
- **Live smoke runs** (mhr V-11.1–5, operator step) — unchanged since 2026-09-29.
- **grok-author trial decision** — unchanged (memory `project_grok_author_trial.md`).
- **Leftover locked worktree `.claude/worktrees/agent-ae2695dac68faa13d`** — still locked. Remove it when idle: `git worktree remove <path> && git branch -d worktree-agent-ae2695dac68faa13d`.
- **`exec-pane` wrapper leak** (`docs/skill-candidates.md`) — unchanged.
- **Foreign `stash@{0}` ("resolved-model")** — untouched.
- **HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`** — unchanged; ownership stays here.
- **Closed this session:**
  - F1, F2, F3 and the cycle 4/6 findings — fixed, or kept by operator decision.
  - M-6 fail-open — fixed (`f75ca887`).
  - HemaSuite pin drift — fixed (`e1dfed23`; brief resolution `2508937d`).
  - HemaSuite items (a), (c), (d) — triaged (`198f2908`); (d) fixed (`c820a1ac`).
  - Phase 5/6/7 — closed, merged and pushed (`d306820e`).
  - Claims on `tdd-gate-fail-opens`, `hemasuite-tdd-gate-pin-drift` and `hmad-defects-from-hemasuite` — released.

## Context for Next Session

**Checkout:** `/Users/kimhawk/orca/skills` is on `main`, in sync with origin at `d306820e` (this handoff is the next commit). HemaSuite's hook symlinks here, so it runs `main`.

**Uncommitted changes:** none (this handoff aside).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills && git checkout main && git pull --ff-only
# Next Step 1: read analysis.v2 §Design-vs-spec items and decide D-1..D-4, N-1
```

**Related docs:** `docs/archive/2026-09/tdd-gate-fail-opens/` (report, analyses v1–v2, archreviews v1–v7); `docs/skill-candidates.md` (2026-09-30 sections).
