# Handoff — tdd-dispatch-verification-discipline SHIPPED via /h-mad (loop-driven)

**Date:** 2026-07-31
**Branch:** main
**Project:** orca/skills (h-mad + handoff skills)

## Session Summary

Ran a full 7-phase `/h-mad "tdd-dispatch-verification-discipline"` autonomously under `/loop` (dynamic, "run until phase 7 completion") and shipped it: the h-mad TDD-dispatch prompts + SKILL.md now carry a RED-side acceptance gate, a revert-test definition of GREEN (restore-by-executing-the-symbol), two named-and-prohibited evasions, an author call-form rule, and a pin re-verification rule — closing the RED-side/GREEN-definition gap the 5e anti-gaming step never reached. Merged to main `84bf2ad`, pushed, both suites green, and the behavioral proof (incident replay vs real HemaSuite `feature/193` artifacts) passed both directions. The spec was a handover from HemaSuite feature/193 (commit `5c0dcaf`).

## Key Learnings

- **The feature caught its own build — the loudest dogfood of the session.** 6a-prime found the single-source doc-test's global `count("grepping")==1` over-constrained SKILL.md (which legitimately uses "grepping" in unrelated §5e/§6a-prime prose), which had recruited the GREEN implementer into mutating two unrelated sentences ("grepping"→"matching"/"searching") — the exact out-of-scope evasion FR-3 prohibits. Fix = assert the specific mechanism LITERALS' absence (the call form) not a global token count; revert the collateral. Lesson: a `count(common_token)==1` assertion IS the anti-pattern this feature names.
- **AC-IR behavioral proof works.** Under the new prompts, exec codex on the real feature/193 scenario returned `STATUS: BLOCKED` (refused the literal-split count evasion) and, RED-side, flagged the fixture-equals-its-own-literal test as vacuous. Proof the prompt changes alter agent behaviour, not just doc contents. A doc-test asserting a literal exists is necessary-not-sufficient — pair it with a live replay.
- **Pane dispatch is unreliable across the day; `exec` is the workhorse.** Pins go stale (handles rotate), `pin-agents` is worktree-scoped so agents living in other worktrees resolve to 0, and a fresh `launch agy` spawns an unauthenticated 1.1.8 that hangs. `hmad-dispatch exec agy`/`exec codex` need no pane/pin (just the CLI on PATH) and drove all 16+ audit/TDD dispatches cleanly. Use `exec` for the whole run under Orca when panes are flaky.
- **A 2-min Bash tool cap kills a backgrounded `exec` child (SIGHUP); the verdict is lost but the work lands.** Recovered via the exec-missing-report verify-from-code discipline (run the suite + git status), a live re-exercise of the feature shipped earlier the same day.
- **The plan/impl-plan audits oscillated on the verifier-prompt target (plan c3↔c5).** The spec listed `codex-verifier-prompt.md` as a target but assigned it no clean FR; every attempt to give it work tripped single-source, every attempt to drop it tripped dropped-target. Resolved by the single-source pointer pattern: one authoritative definition (SKILL.md §5e), the verifier a pure reference. When an audit ping-pongs, stop applying its prescription and resolve by the spec's intent.

## Next Steps

1. [suggested] The new discipline is now live in the h-mad prompts — the NEXT real `/h-mad` feature exercises FR-1/FR-2/FR-3/FR-4 in production. Watch whether Codex's RED reports now carry the per-test acceptance evidence and whether the revert-test GREEN definition gets run. — `h-mad/references/codex-implementer-prompt.md`, `h-mad/SKILL.md` §5e.
2. [carry] #2 `wait --not-while-regex 'Waiting for background terminal'` false-idle guard — still unit-tested only, awaiting a HemaSuite live exercise. — `h-mad/scripts/hmad-dispatch.sh` `_cmd_wait`.

## Open / Blocked Items

- None for tdd-dispatch-verification-discipline — COMPLETE (100% match, 6a-prime READY_TO_MERGE, AC-IR proven both directions, merged `84bf2ad`).
- #2 false-idle guard live validation — status: delegated to a HemaSuite session (2026-07-29), not blocking. repo: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer` · branch: `main` · worktree: main (Orca-managed).

## In-Flight Processes

None — all exec agy/codex dispatches completed or were reaped (one GREEN child was killed by the 2-min tool cap and verified complete from the tree). No live background work at handoff.

## Context for Next Session

**Feature shipped this session (feature/212, merged + deleted):**
- `h-mad/references/codex-implementer-prompt.md` — FR-1 RED acceptance-evidence block + FR-3 named evasions
- `h-mad/SKILL.md` — FR-2 revert-test GREEN definition (authoritative), FR-3 author rule, FR-4 pin rule
- `h-mad/references/codex-verifier-prompt.md` — FR-2 pure pointer
- `h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py` — 6 mutation-verified doc-tests
- `docs/01-plan/features/tdd-dispatch-verification-discipline.*` + `.design.md` + `.analysis.md` + `.report.md`

**Commits on main:** `5c0dcaf` (spec handover) → `d69d933` (docs P2-5b) → `2c143c8` (impl) → `0f59a80` (6a-prime fix) → `a363350` (nit) → `458e116` (P6-7 docs) → `84bf2ad` (merge).

**Uncommitted changes:** none (local `main` = `origin/main` `84bf2ad`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q   # 760/0
```

**Related docs:**
- `docs/04-report/features/tdd-dispatch-verification-discipline.report.md` (closure)
- Prior handoff (same arc): `docs/handoffs/2026-07-30-main__exec-missing-report-recovery-shipped.md`
