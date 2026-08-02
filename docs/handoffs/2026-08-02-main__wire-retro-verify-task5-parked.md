# Handoff — Wire-pin gate's first live 5b, and a retro-verification of two already-shipped wires

**Date:** 2026-08-02
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad`)

## Session Summary

Ran the wire-pin gate against a real impl-plan for the first time (`grounding-shadow-measurement.impl-plan.md` v1.5, HemaSuite): `WIREPIN: PASS tasks=5 wiring=2 unpinned=0 mislabeled=0`, and 4/4 mutations on that same real plan landed exactly as documented. That **falsified** the prior handoff's prediction that any legacy plan would halt `step5b:impl_plan_unshaped`. Then discovered the two `wiring` shapes were **retrofitted onto already-GREEN tasks ~10h after they shipped**, so no wire-scoped revert had ever run — and ran it: both wires are genuinely ENFORCED, in both directions. Task 5 (the FR-3 isolation harness) remains undispatched; the dispatch stopped one step short, at re-asserting `PREFLIGHT: PASS` after a re-pin.

## Key Learnings

- **A `WIREPIN: PASS` on a plan whose shapes were retrofitted after Phase 5e is a *documentation* PASS, not an enforcement one.** The gate lives at 5b — *before* dispatch. Commit dates proved it: Task 3 GREEN at 08-01 21:29, Task 4 GREEN at 08-01 22:15, plan v1.5 declaring both `wiring` at 08-02 08:05. Run against a plan edited after the fact, the gate certifies the plan is well-formed and says nothing about whether the connection was ever tested. This is a *new* direction on the blind spot — the existing memory names the callee-scoped-gate mechanism, not the retro-declaration one.
- **"Every shipped impl-plan returns `UNSHAPED`" is false as a blanket claim.** It holds for legacy `*.plan.md` (no `## Task N` headers at all → `tasks=0`), not for a regenerated `.impl-plan.md`. Check the specific plan; don't plan a dispatch around an expected halt that won't fire.
- **When `tasks=0`, the gate's `UNSHAPED` message misdiagnoses.** It prints "no task declares a **Task shape**" when the truth is "no task was found". Same halt, wrong remedy handed to an operator (they go add a field to a file with no tasks in it).
- **`h_mad_resume_decision.py` and `h_mad_state_write.py --claim` disagree about the same stale claim.** `resume_decision` treats a >2h-old claim as abandoned and returns `enter_autonomous`; `state_write --claim` refuses outright with `ERROR: … is owned by session …` and has no staleness allowance. A 19.6h-dead session blocked the claim while the router said proceed. `--force` is the only way through, which means the documented advisory-claim semantics are only half-implemented.
- **`hmad-dispatch launch codex` is currently unusable (J1).** It fails with "create response carries no paneKey, so the pane cannot be identified; nothing was pinned. The create-response handle is a pre-adoption placeholder (J1) and must not be pinned." `pin-agents` (Pass-0 `agentType` join) worked immediately as the fallback. The SKILL.md text still recommends `launch` as the zero-manual path.
- **`PREFLIGHT: FAIL stale=codex,agy` came back with `env_rc=0`** — the token-not-exit-code rule reproduced live, not just in doctrine.
- **`timeout` does not exist on macOS** (it's `gtimeout` from coreutils), and `grep --include=*.md` explodes under zsh globbing (`no matches found`). Both cost a wasted call this session.
- **My own grep pattern, not the plan, was wrong once.** `\*{0,2}WIRE\*{0,2}\s*:` cannot match `**WIRE** (\`wiring\` shape only):` — the parenthetical sits between the bold close and the colon. Reading the file directly refuted the finding before it was filed.

## Next Steps

1. **Re-assert preflight before any dispatch** — `hmad-dispatch env`, confirm `PREFLIGHT: PASS`. Agents were re-pinned this session (`codex → term_d8c8fa01-0227-4c24-a71a-3cfa7b2db9c9`, `agy → term_ef0c6dba-cfa0-443b-99bc-044bcd1c58ef` in `/Users/kimhawk/orca/HemaSuite/.h-mad/orca-pins.env`) but the required post-re-pin assertion never ran. Skipping it → halt `step5:preflight_failed`.
2. **Dispatch Task 5 RED+GREEN** — `tests/test_grounding_shadow_isolation.py` (absent). FR-3 verdict isolation + mutation harness; `new-behaviour` shape, **Production file: none (test-only)**. Plan §Task 5 at `docs/01-plan/features/grounding-shadow-measurement.impl-plan.md:337-341`. The plan's synthetic in-test section (bold-lead enumeration, `04_eligibility.md` house style, real n=0 / shadow n=6) supersedes the dead `sapphire_sa2` premise — do not go looking for that fixture.
3. **Strip a trailing parenthetical from the shape *value* in `_declared_shape`** — `h-mad/scripts/h_mad_wire_pin_gate.py:83`. `Task shape: wiring (connects X to Y)` currently lands in `mislabeled` with a confusing message. Fold in the `tasks=0` message fix (learning 3) while there — same file, `main()` around `:220-225`.
4. **[suggested] File the claim/resume staleness-window inconsistency** — `h-mad/scripts/h_mad_state_write.py` has no staleness allowance on `--claim` while `h_mad_resume_decision.py` has a 2h one.

## Open / Blocked Items

- **HemaSuite Task 5 — status: parked, undispatched.** `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: feature/196-grounding-shadow-measurement · worktree: none` @ `8ed16260`. Target: `tests/test_grounding_shadow_isolation.py`. Plan: `docs/01-plan/features/grounding-shadow-measurement.impl-plan.md` (v1.5). Feature is **force-claimed** by session `73aae80d-2b02-48ca-95c8-58c36869d24e` — release or re-claim before another session touches it. No blocker beyond the preflight re-assertion in Next Step 1.
- **`STALENESS: SUSPECT findings=2` on that feature — status: adjudicated, deliberately NOT corrected.** `phase_counter_behind` (`last_completed_phase=4` vs 17 commits) and `autonomous_flag_stale` (`phase='step5'` armed 19.6h, `halt_reason=null`). Both are **false positives here**: Phase 5 is genuinely incomplete (Task 5 absent) so 4 is correct, and the armed `step5` flag is what keeps `hooks/h-mad-tdd-gate.sh` blocking Claude's own Write/Edit on production `.py`. Disarming it to silence the check would open the exact hole the flag exists to close.
- **Full-demotion residual — status: accepted, documented not mechanical.** Shape demoted *and* `WIRE`/`WIRE-PIN` cleared → clean PASS. Reconfirmed live on the real plan this session. Only `h-mad/references/failure-recovery.md`'s mislabel row (operator prose) names it.
- **`hmad-dispatch launch` broken by J1 — status: open, worked around.** No paneKey in the create response. `pin-agents` is the working path. Not investigated further.

## Context for Next Session

**Files touched this session:**
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/feedback_wiring_tasks_need_a_wire_scoped_revert.md` (edited — "Run live on a real impl-plan 2026-08-02" + corrected caveat)
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md` (edited — hook now records the falsified claim)
- `/Users/kimhawk/orca/HemaSuite/.h-mad/orca-pins.env` (re-pinned codex + agy)
- Scratchpad probe `wire_revert.py` — written, used, **deleted** per skill discipline. Would need reconstruction to re-run: exact-string replace with an assert-landed guard (`hits != 1` → refuse), verbs `task3-cut` / `task4-cut` / `task4-force` / `restore`, `.py.wirebak` sidecar.
- No production or skill code changed. `~/orca/skills` is clean at `4478c3f`.

**Retro-verification evidence (the load-bearing result):**

| Wire | Mutation | Result |
|---|---|---|
| Task 3 `_run_section` (`engine/unified_engine.py:1606-1614`) | sever call site only, callee + tests intact | WIRE-PIN **failed**, 4/11 failed → **ENFORCED** |
| Task 4 `_run_narrative_finalizer` (`:2112-2120`) | sever call site only | WIRE-PIN **failed**, 6/10 failed → **ENFORCED** |
| Task 4 fall-through (`:2121-2123`) | force the wire to fire unconditionally | `test_finalizer_with_no_seeded_evidence_measures_nothing` **failed** → **ENFORCED** |

Baseline 21 passed; green returned after each restore (11 and 10); tree verified clean, no `.wirebak` residue. Every mutation asserted-landed before its run. The retrofit documented reality — both connections were genuinely tested, and the second-direction guard is caught by the pin `1ef807df` added the day before.

**Uncommitted changes:** `~/orca/skills` — none, clean at `4478c3f`, in sync with `origin/main`. HemaSuite — one pre-existing unrelated `M .bkit/state/pdca-status.json`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
/opt/anaconda3/bin/python3 -m pytest h-mad/tests -q     # 841 expected

cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
git checkout feature/196-grounding-shadow-measurement   # @ 8ed16260
/opt/anaconda3/bin/python3 -m pytest tests/test_grounding_shadow_*.py -q   # 21 expected
hmad-dispatch env                                        # MUST read PREFLIGHT: PASS before dispatch
```

A bare `python3` resolves to `/opt/homebrew/opt/python@3.14/bin/python3.14`, which has no pytest — use `/opt/anaconda3/bin/python3`. The gate itself is stdlib-only (pinned by `test_gate_is_stdlib_only`).

**Related docs:**
- Prior handoff: `docs/handoffs/2026-08-02-main__wire-pin-mislabel-merged.md`
- `h-mad/invariants.base.md` §"Connection enforcement"; `h-mad/SKILL.md:259` (5b gate invocation), `:271` (5e wire-scoped revert)
- Memory: `feedback_wiring_tasks_need_a_wire_scoped_revert.md`, `feedback_mutation_test_every_guard.md`, `project_grounding_shadow_measurement.md`
