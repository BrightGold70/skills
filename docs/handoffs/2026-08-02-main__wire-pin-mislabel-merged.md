# Handoff — Wire-pin gate: mislabel guard reviewed and merged

**Date:** 2026-08-02
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad`)

## Session Summary

Resumed the wire-pin arc from `2026-08-02-feature-wiring-task-shape-gate__wiring-task-shape-gate.md` and found that handoff already stale: PR #18 was merged (`eac5c8f`), and a follow-up commit had found a **second** hiding place — a *wrong* shape rather than an absent one — sitting unmerged in PR #19. Ran both suites (h-mad 841, HemaSuite consumer 48), reviewed the diff, smoke-verified the guard on a crafted plan, and squash-merged #19 as `9c1db8d`. `main` is clean and in sync; the wire-pin arc is done code-wise and now owes only its first live `/h-mad` 5b run.

## Key Learnings

- **A merged PR does not update the handoff that cited it.** The prior doc's Next Step 1 said "merge PR #18" and its Open Item said "#18 open, unmerged" — both were false within hours of writing, and only the resume reconciliation (`gh pr view 18` → `MERGED`, plus a squash commit whose title carries `(#18)`) caught it. A squash-merge title ending in `(#N)` is the cheapest possible signal that a cited PR already landed; read `git log` for it before trusting a handoff's PR state.
- **The mislabel guard closes the one-word demotion, not the two-edit one.** Verified live: changing `Task shape: wiring` → `refactor` while leaving `WIRE`/`WIRE-PIN` filled now FAILs with `mislabeled=1`. But clearing the fields *back to placeholders* in the same edit returns a clean PASS (`wiring=0 unpinned=0 mislabeled=0`) — indistinguishable from a genuine refactor task, so no mechanical signal exists. `failure-recovery.md`'s `step5b:wire_pin_shape_mislabel` row names that evasion in prose only. Correct scope, but the residual must not be mistaken for coverage.
- **A shape value with trailing prose reads as a mislabel, not as `wiring`.** `Task shape: wiring (connects X to Y)` fails the exact `== "wiring"` comparison (the `_FIELD_RE` parenthetical strip applies to the *label* side, not the value), so it lands in `mislabeled` with the confusing message ``declares `wiring (connects x to y)` but carries WIRE``. Fail-safe direction and a net improvement over the pre-PR silent PASS, but the message misreads.
- `_declared_shape` lowercases and rejects any value containing `|`, so `Wiring` is handled and an unedited `new-behaviour | refactor | wiring` template line correctly declares nothing rather than declaring a shape that happens to exclude `wiring`.

## Next Steps

1. Exercise the gate at a real Phase 5b — `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/<feature>.impl-plan.md`. Still never run inside a live `/h-mad` cycle. Expect `step5b:impl_plan_unshaped` on any legacy plan. [[feedback_tracer_bullet_before_ceremony]]
2. Dispatch HemaSuite Task 5 (grounding-shadow-measurement, impl-plan v1.4) — the memory-flagged next wiring site; confirms the 5e wire-scoped revert catches what a whole-module revert cannot. `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: feature/196`
3. [suggested] Consider tightening `_declared_shape` to strip a trailing parenthetical from the *value* so `wiring (connects X to Y)` scores as `wiring` — `h-mad/scripts/h_mad_wire_pin_gate.py:83`. Low priority; current behaviour is fail-safe.

## Open / Blocked Items

- **Gate never run in a live `/h-mad` 5b** — status: deferred, no work owed until the next feature reaches Phase 5. All evidence is unit tests, mutations (16/16 shape gate, 6/6 mislabel guard, 7/7 docs), and a read-only dogfood sweep over ~50 shipped impl-plans.
- **Full-demotion residual** — status: accepted, documented not mechanical. Shape demoted *and* `WIRE`/`WIRE-PIN` cleared → PASS. Only `h-mad/references/failure-recovery.md`'s mislabel row (operator prose) catches it.
- **Every legacy impl-plan returns `UNSHAPED`** — status: expected, not a defect. ~50 HemaSuite plans predate the `Task shape` field; the first live 5b halts unless the plan is regenerated against `h-mad/references/inline-protocols.md` §Phase 5a.
- **HemaSuite Task 5** — status: parked, unblocked at impl-plan v1.4. `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: feature/196 · worktree: none recorded`. Note the older memory (`project_grounding_shadow_measurement.md`) still calls Task 5 undispatchable on a missing `sapphire_sa2` fixture — v1.4 supersedes that; re-check before dispatch.

## Context for Next Session

**Files touched this session:** none — this session reviewed and merged work committed in a prior one. Merged by #19: `h-mad/SKILL.md`, `h-mad/references/failure-recovery.md`, `h-mad/scripts/h_mad_wire_pin_gate.py`, `h-mad/tests/test_h_mad_wire_pin_gate.py`, `h-mad/tests/test_h_mad_wiring_task_shape_docs.py`.

**Uncommitted changes:** none — tree clean, `main` @ `9c1db8d`, in sync with `origin/main`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
/opt/anaconda3/bin/python3 -m pytest h-mad/tests -q     # 841 expected
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q   # 48 expected
```

A bare `python3` here resolves to `/opt/homebrew/opt/python@3.14/bin/python3.14`, which has no pytest — use `/opt/anaconda3/bin/python3`. The gate itself is stdlib-only and runs under any `python3` (pinned by `test_gate_is_stdlib_only`).

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-02-feature-wiring-task-shape-gate__wiring-task-shape-gate.md`
- `h-mad/invariants.base.md` §"Connection enforcement"
- Memory: `feedback_wiring_tasks_need_a_wire_scoped_revert.md`, `feedback_mutation_test_every_guard.md`
