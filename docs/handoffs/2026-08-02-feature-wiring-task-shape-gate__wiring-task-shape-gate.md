# Handoff — H-MAD `wiring` task shape + Phase-5b wire-pin gate

**Date:** 2026-08-02
**Branch:** feature/wiring-task-shape-gate (no upstream — never pushed)
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad`)

## Session Summary

Two consecutive H-MAD wiring tasks shipped their single load-bearing design decision untested — every audit cycle and the RED phase passed it, and only the mutation pass caught it, twice. Diagnosed the cause as structural rather than bad luck: **every Phase-5 gate is scoped to the CALLEE while a wiring task's deliverable is the CONNECTION**. Shipped the counter-measure in two commits — `7ee46f5` adds the `wiring` task shape, the `Connection enforcement` invariant, and the wire-scoped revert to 5d/5e; `f1dbf5c` adds `h_mad_wire_pin_gate.py`, the mechanical Phase-5b refusal of a wiring task with no `WIRE-PIN`. Both are complete, mutation-verified, and green (h-mad 824 passed, HemaSuite consumer 48 passed). The branch is **committed but unpushed and unmerged**.

## Key Learnings

- The blind spot is deterministic, not probabilistic. RED goes red because the callee is *absent*; the 5e whole-module revert removes caller **and** callee so its RED split returns identically for a wired and an unwired build; the anti-gaming audit finds a callee-scoped unit test perfectly discriminating; 6a-prime reviews a diff and sees a call site that is *present*. **Presence is not enforcement** — no layer below mutation can see an unenforced connection.
- 5b is the last gate that can require the pin. After 5b nothing in the pipeline can distinguish a wired build from an unwired one, so the obligation has to be mechanical at the impl-plan or it is unenforceable.
- `UNSHAPED` (exit 2) rather than silent PASS for legacy plans — same discipline as `h_mad_audit_gate.py`'s `GATE: INVALID`. "Cannot judge" must never read as "nothing to fix". Legacy plans predate the `Task shape` field, so a silent PASS would certify ~50 plans the gate never actually scored.
- **The mutation tool lied before the guard did.** One doc literal spans a line break in the raw source, so `.count()` returned 0 and the mutation was a silent no-op that reported the guard as enforced. Fixed with a wrap-aware regex (`r"\s+".join(re.escape(w) for w in literal.split())`) plus `n>0` and post-write assertions. Hazard #2 from `feedback_mutation_test_every_guard`, reproduced live.
- **Dogfooding found what 35 tests did not.** An earlier draft of the gate returned `tasks=0` on several shipped impl-plans: the parser required the literal word "Task" plus a colon, while real plans use `Task N —`, a parenthetical id qualifier, and module-style `M<n>` headers. A correctly *shaped* plan in those conventions would have halted for declaring nothing.
- **A DIRECTION-2 mutation exposed a non-discriminating test.** Relaxing the header id to `\S+` produced 0 failures — the prose-heading test used only multi-word headings, which the trailing `$` rejects anyway. Single-word headings lifted from real plans (`## Scope`, `### RED`) are the discriminating cases. Zero failures from a mutation is itself a finding.
- Doc tests must anchor on distinctive **contiguous whitespace-normalised literals**. An earlier assertion on component words passed with the documented guidance deleted, because both words already appeared in unrelated prose nearby.

## Next Steps

1. Decide whether to merge — the branch has no upstream and is 2 commits ahead of `main`: `git log --oneline main..feature/wiring-task-shape-gate`
2. If merging, run BOTH suites first (the skills repo is symlinked into `~/.claude/skills/h-mad`, so a skill script change lands in every consumer immediately) — `/opt/anaconda3/bin/python3 -m pytest h-mad/tests -q` in `/Users/kimhawk/orca/skills` AND `pytest tests/test_h_mad_*.py -q` in `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer`
3. Exercise the gate on the next real H-MAD feature at Phase 5b — `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/<feature>.impl-plan.md`. It has never run inside a live `/h-mad` cycle; every run so far was a test or a dogfood sweep. [[feedback_tracer_bullet_before_ceremony]]
4. Verify the memory's prediction at the remaining wiring site — memory `project_grounding_shadow_measurement.md` Task 5 was flagged as the next place to expect this defect class. Run the wire-scoped revert there and confirm the new 5e step catches it.

## Open / Blocked Items

- **Branch unpushed / unmerged** — status: not yet done, deliberate. `feature/wiring-task-shape-gate` has no upstream; nothing was pushed this session. `repo: /Users/kimhawk/orca/skills · branch: feature/wiring-task-shape-gate · worktree: none`
- **Gate never run in a live `/h-mad` cycle** — status: deferred. All evidence is unit tests (35), mutation (16/16 both directions), and a read-only dogfood sweep over ~50 shipped impl-plans. No feature has yet reached 5b with the gate wired in.
- **Every shipped impl-plan returns `UNSHAPED`** — status: expected, not a defect. ~50 HemaSuite plans predate the `Task shape` field. The first live 5b will halt `step5b:impl_plan_unshaped` unless the plan is regenerated against the current template (`references/inline-protocols.md` §Phase 5a). Worth knowing before it surprises someone mid-cycle.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` — 5b wire-pin gate invocation, 5d `wiring` shape paragraph, 5e wire-scoped revert
- `h-mad/invariants.base.md` — new `## Connection enforcement` section (auto Must-fix tier)
- `h-mad/references/inline-protocols.md` — impl-plan template `Task shape` / `WIRE` / `WIRE-PIN` fields
- `h-mad/references/codex-implementer-prompt.md` — pin is the load-bearing test
- `h-mad/references/codex-verifier-prompt.md` — `<INLINE_WIRE>` / `<INLINE_WIRE_PIN>` slots, step 1b
- `h-mad/references/failure-recovery.md` — 5 new halt rows
- `h-mad/scripts/h_mad_wire_pin_gate.py` — NEW, stdlib-only
- `h-mad/tests/test_h_mad_wire_pin_gate.py` — NEW, 35 tests
- `h-mad/tests/test_h_mad_wiring_task_shape_docs.py` — NEW, doc pins
- `h-mad/tests/test_h_mad_invariants_layering.py` — `Connection enforcement` heading + literal test

**Uncommitted changes:** none — tree clean. Skill work at `f1dbf5c`, this handoff at `d01ac13`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/wiring-task-shape-gate
/opt/anaconda3/bin/python3 -m pytest h-mad/tests -q     # 824 expected
# consumer suite — the skills repo is symlinked into ~/.claude/skills
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q   # 48 expected
```

Note: a bare `python3` in this shell resolves to `/opt/homebrew/opt/python@3.14/bin/python3.14`, which has no pytest. Use `/opt/anaconda3/bin/python3`. The gate itself is stdlib-only and runs under any `python3` — that is a pinned test (`test_gate_is_stdlib_only`).

**Mutation harnesses** (scratchpad, not committed):
- `<scratchpad>/mutate_wire_pin_gate.py` — 16 gate mutations, both directions
- `<scratchpad>/mutate_wiring_docs.py` — 16 doc-literal mutations, wrap-aware

**Related docs:**
- `h-mad/invariants.base.md` §"Connection enforcement" — the rule the audit layers previously lacked
- Memory: `feedback_wiring_tasks_need_a_wire_scoped_revert.md`, `feedback_mutation_test_every_guard.md`, `feedback_impl_plan_pins_the_blind_spot.md`
