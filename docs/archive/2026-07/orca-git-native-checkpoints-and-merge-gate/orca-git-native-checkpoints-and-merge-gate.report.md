# Report: orca-git-native-checkpoints-and-merge-gate

## Executive Summary
Shipped Orca git-native checkpoints and a safety-valve merge gate into the `handoff` and `h-mad` skills, behind the existing `hmad-dispatch` abstraction and fully substrate-gated — non-Orca runs are byte-identical to before.

## Summary
Added two additive `hmad-dispatch` verbs (`worktree-comment`, `worktree-current`, both capture-then-`.ok` so an error envelope can't read as success), flipped the substrate-detection default to Orca (a two-branch swap), gave `handoff` a durable WRITE checkpoint stamp + READ worktree reconcile, and wrapped the h-mad Phase-5 winner-merge in a decision gate that auto-records clean merges and blocks only on conflict/DRIFT. Key decision: keep every Orca call inside `hmad-dispatch` (the chokepoint invariant), which the plan audit caught being violated by FR-4 and drove the addition of `worktree-current`. Code TDD'd by Codex; every phase gated by an independent agy review.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | 2 (cycle 1: FR-4 chokepoint contradiction → added `worktree-current`; cycle 2 clean) |
| Design audit cycles | 2 (cycle 1: AC-1.3 msg, AC-1.5 `ok:false` pipe gap, D3 two-branch; cycle 2 clean) |
| Impl-plan audit cycles | 1 (clean) |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% (35/35 ACs) |
| 6a-prime architectural review | `READY_TO_MERGE` |
| Tests | 342 passing / 0 failing (pins stripped; +13 new) |
| Phases with back-propagation | None |

## What Went Well
- The audit chain earned its keep: the plan audit caught a real self-contradiction (FR-4 required raw `orca` calls the plan's chokepoint rule forbade), and the design audit caught a genuine bug (a bare `orca … | _json_extract` pipe silently swallowing an `ok:false` envelope). Both would have shipped otherwise.
- Codex RED/GREEN was clean and honest — 13 tests, no skips/hollow stubs, real implementation matching the design line-for-line; verified independently (inspection + pins-stripped pytest).
- Substrate abstraction held: the whole feature added Orca surface to two skills with zero raw `orca` in either skill body.

## What To Improve Next Time
- The agy (Gemini-TUI) audit substrate cost the most wall-clock: unreliable idle detection, per-frame redraw fragmenting sentinels, a mid-run homebrew self-upgrade, and a gate that false-passed indented/`•`-bulleted output. All captured as F1–F13 in `docs/orca-git-native-skill-upgrade-findings.md` for a follow-up skill-hardening pass.
- Never send a bare Enter to nudge Antigravity — it submits a blank turn. Ctrl-C-to-freeze-scrollback became the reliable capture technique.

## Carry Items
- **Post-Phase-7 skill hardening**: action F1–F13 in `docs/orca-git-native-skill-upgrade-findings.md` — chiefly F1/F2 (audit gate false-passes on TUI output / empty extract), F11 (existing verbs swallow `ok:false`), F12 (`autonomous_entry_ts` schema mismatch), F13 (test `run()` leaks `HMAD_ORCA_*` pins).
- **handoff install-copy sync (F10)**: `~/.claude/skills/handoff` is a real dir, not a symlink to the repo (unlike `h-mad`), so these changes are NOT yet live in the installed skill. Re-sync or symlink it.
- **Live smoke DONE (verbs)**: against the live Orca runtime, `worktree-comment active "handoff: orca-git-native · shipped · …"` returned exit 0 and `worktree-current` read the stamp back on `feature/185`; the non-orca guard exits 2. The verb round-trip + degradation is e2e-verified. Still not run e2e: the full `handoff` WRITE/READ *protocol* path (skill prose driving the verbs) and a real Phase-5 merge-gate on a throwaway module — those remain doc-verified only.

## Version History
- v1.0: Initial report draft.
