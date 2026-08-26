# Handoff — anchor-precheck-phase-5e-wiring, paused mid-Phase-5d

**Date:** 2026-08-26
**Branch:** feature/197-anchor-precheck-phase-5e-wiring
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Ran `/h-mad "anchor-precheck-phase-5e-wiring"` from `start_fresh` through Phases 1–4 (all gates
clean) and into Phase 5d. The feature makes the mutation-harness anchor sweep an obligation a run
cannot silently skip: a suite assertion over the repository's own committed specs, plus a
sibling-only precheck inside `run_spec` that refuses on a neighbour's drift. Design is audited clean
over six cycles; the 7-task impl-plan is audited and committed; **Task 1's RED is committed and
verified**. Paused at the operator's direction on context budget (57.9% of a 1M window against an
80% halt ceiling) with Task 1 GREEN and Tasks 2–7 outstanding. A separate defect found while
dogfooding (`F16`) was fixed and shipped in-session.

## Key Learnings

- **`low-evidence` in the audit-cycle `Effort:` block keys on tool count, and tool count does not
  discriminate on this transport.** The audit prompt inlines plan, spec and both invariant layers, so
  a pass never needs to read anything and 1–2 calls is the expected floor. Every pass in this run was
  flagged `low-evidence`, including the two that found six real Must-fix items. **Thinking tokens
  tracked usefulness instead**: passes below ~6k found nothing (0 findings across six Phase-3
  passes); passes at 8.8k–14.7k found everything. Read the block as a triage hint weighted on
  thinking, never as a verdict in either direction.
- **A high-evidence review can be worse than a low-evidence one.** A dispatch explicitly told to
  verify against the repo made 16 successful reads, correctly confirmed all seven factual claims it
  was asked to check, then declared "every FR and AC is fully satisfied" — false in four places the
  low-evidence passes caught. Evidence gates answer *did it look*, not *did it think*.
- **Five consecutive design-audit cycles found defects created by the previous cycle's fix.** Prose
  fix → didn't reach the schema → schema fix exposed a verdict-name collapse → verdict fix → census
  didn't survive the success path → census described in five places with three shapes → schema-once
  fix moved the ambiguity to a new name. Each fix was correct; each opened the next. This is the
  measured argument against closing an audit on one clean cycle.
- **Never issue a version-history bump in the same command as the edit it describes.** A `.replace()`
  whose anchor had drifted wrote nothing and raised, while `h_mad_version_history.py` ran anyway in
  the same command and appended "corrected the measurement to 7-of-177". For one command the document
  advertised a fix it did not contain — its own change log was the least reliable statement in it.
- **RED tests can hit the stated counts and still assert the wrong thing.** Task 1's RED matched
  `2 failed, 55 passed` exactly and contained `assert source.count("_resolve_root(") == 3` — an
  occurrence count over the whole file, which passes if `precheck_spec` resolves twice and `run_spec`
  never does. The monkeypatch replacement compared against `[tuple] * 2`, which admits the same case.
  Counts matching is necessary, not sufficient; neither defect could have been caught by the
  impl-plan audit, which never sees the tests the implementer writes.
- **An absolute path in a committed file is a portability defect twice over.** All 17 mutation specs
  pinned `/Users/kimhawk/orca/skills/...`, which breaks off this machine *and* makes a mutation run
  inside a git worktree resolve to the main checkout — relevant because Phase-5 fanout creates
  worktrees.

## Next Steps

1. **Task 1 GREEN** — implement `_resolve_root` in `h-mad/scripts/h_mad_mutation_harness.py` so the
   two committed RED tests pass. Stage with:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_tdd.py --feature anchor-precheck-phase-5e-wiring --task "Task 1" --phase green --project-root /Users/kimhawk/orca/skills --module h-mad/scripts/h_mad_mutation_harness.py --test-path h-mad/tests/test_h_mad_mutation_harness.py --python /opt/anaconda3/bin/python3.11 --prompt <scratch>/task1_green.md`
2. **Establish GREEN by the revert test, not by "tests pass"** —
   `git add -N -- <prod>; git stash push -- <prod>; git diff --quiet -- <prod> || echo "REVERT DID NOT LAND"`,
   confirm the RED split returns exactly `2 failed, 55 passed`, `git stash pop`, then re-run the
   suite to prove restoration by execution rather than by grepping the source.
3. **Tasks 2–7 in order** — the dependency chain is real, not preference:
   1 → 2 → (3) → 4 → 5 → 6 → 7. See `docs/01-plan/features/anchor-precheck-phase-5e-wiring.impl-plan.md`.
4. **Task 4 is the wiring task and needs BOTH mutation directions** — remove the call (WIRE-PIN
   `test_clean_spec_beside_a_drifted_sibling_refuses_before_mutating` must fail) *and* force it to
   fire unconditionally (AC-3.2's all-clean-directory test must fail). One direction certifies a
   connection that always fires just as happily as one that fires correctly.
5. **Task 5 must re-anchor `h-mad/tests/mutation-specs/mutation_harness.json` in the same commit** —
   its `change-the-summary-line-callers-parse` mutation anchors the exact summary-line f-string
   Task 5 rewrites. The feature trips the guard it is building.
6. **5f** — `h_mad_wire_registry.py verify --base b5c8f41 --rootdir /Users/kimhawk/orca/skills --testpath h-mad/tests`,
   then `challenge --base b5c8f41`, then the full suite in **both** coupled repos.
7. **Phase 6/7** — 6a-prime via `exec agy` with BASE `b5c8f41`; cite files by ABSOLUTE path and
   instruct the reviewer to return `ASSESSMENT: NO` if its reads fail. Then
   `h_mad_phase7_preconditions.py`, telemetry, report, archive.
8. `[suggested]` **File the monitoring rows** the ledger owes: F1–F6 (tool defects found staging the
   A/B probe), F17 (state schema has no field for the 5c baseline sha).

## Open / Blocked Items

- **Tasks 2–7 of the impl-plan** — status: not started. All artefacts in this repo/branch; nothing
  parked elsewhere.
- **Task 1 GREEN** — status: not started; RED committed at `c57ae40`.
- **F2 — `--check-anchors` verdict/exit discipline** — status: deferred, out of scope by operator
  decision. `ANCHORS_DRIFTED` is a real verdict that exits 2, and an unusable spec JSON collapses
  into that same word. Fails toward re-anchoring (the safe direction). Owed: a
  `docs/skill-monitoring.md` row at Phase 7.
- **F1, F3–F6 — `h_mad_ab_dispatch.py` and harness defects** — status: deferred to monitoring rows.
  Notably `--run` rejects flag-shaped tokens in the form SKILL.md documents (`--run --model` fails;
  `--run=--model` works), and `_observe` takes the FIRST regex match where every other extractor in
  the skill takes the last.
- **F17 — no state-schema field for the 5c baseline sha** — status: deferred. `h_mad_state_write.py`
  correctly refused the invented key. Value is derivable: `git merge-base main <branch>` → `b5c8f41`.
- **The feature branch has no upstream** — status: informational. `git push -u origin HEAD` when
  ready; nothing has been pushed for this branch.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/anchor-precheck-phase-5e-wiring-brainstorm.md` (v1.5)
- `docs/01-plan/features/anchor-precheck-phase-5e-wiring.spec.md` (v1.3, 7 FRs / 38 ACs)
- `docs/01-plan/features/anchor-precheck-phase-5e-wiring.plan.md` (v1.3)
- `docs/01-plan/features/anchor-precheck-phase-5e-wiring.impl-plan.md` (7 tasks)
- `docs/01-plan/features/anchor-precheck-phase-5e-wiring.dogfood.md` (v1.11, findings F1–F17)
- `docs/02-design/features/anchor-precheck-phase-5e-wiring.design.md` (v1.5, gate PASS + stamp CURRENT)
- `h-mad/scripts/h_mad_audit_gate.py` (F16 fix, shipped)
- `h-mad/tests/test_h_mad_audit_gate.py` (3 new tests for F16)
- `h-mad/tests/test_h_mad_mutation_harness.py` (Task 1 RED)
- `h-mad/tests/mutation-specs/audit_gate_stamp.json` (+1 mutation, now 11)

**Uncommitted changes:** none — tree clean at `c57ae40`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/197-anchor-precheck-phase-5e-wiring
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
# state says phase=step5, so the TDD gate hook is ARMED: Claude's own
# production .py writes are blocked and Codex must author. That is correct.
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_h_mad_mutation_harness.py -q
#   expect: 2 failed, 55 passed   (Task 1 RED, unimplemented)
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run
```

**Environment facts that each cost a real mistake to learn:**
- Interpreter is `/opt/anaconda3/bin/python3.11`. A bare `python3` here is 3.14 with **no pytest**.
- Every `exec codex` needs `--model gpt-5.5`; the config default (`gpt-5.6-luna`) cannot execute
  tools and fails as a well-formed `STATUS: BLOCKED`.
- Never `timeout`/`gtimeout` — use `hmad-dispatch run --timeout <s> -- <cmd>`.
- `ls` appears to hang under the rtk command-rewrite hook; use `find`/`test -f`/`wc` instead.
- Commit messages go through `git commit -F <file>`; bkit ENH-310 denies heredoc-in-command-substitution.

**Related docs:**
- Seed: `docs/01-plan/features/anchor-precheck-phase-5e-wiring.seed.md`
- Dogfood ledger (F1–F17): `docs/01-plan/features/anchor-precheck-phase-5e-wiring.dogfood.md`
- All six seed dogfood checkpoints are **closed**; four produced findings.
