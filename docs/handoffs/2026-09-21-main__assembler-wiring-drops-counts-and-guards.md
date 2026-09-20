# Handoff — `h_mad_assemble_tdd.py` drops `--expect-fail`/`--expect-pass`/`--guard` on every `wiring` task

**Date:** 2026-09-21
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · feature/046-deck-guided-narrative-assets · session 3d65fe3c-0568-4f1a-82f6-4d77238017dc
**Taken-Over-By:** skills · main · session ffaec156-1056-4683-a0c2-abf87e0614b9 · 2026-09-21
**Supersedes:** none — this is an inbound handover, not a closeout

## Session Summary

A defect in **this repo's** `h-mad/scripts/h_mad_assemble_tdd.py` was found and filed while running
an H-MAD Phase 5 in HemaSuite. It was diagnosed by control/treatment there, written up there, and
never fixed, because it lives here. Ownership moves with this brief. **Nothing in this repo has been
edited** — the sender only read it.

On a `wiring`-shaped task the assembler emits the WIRE/WIRE-PIN lines *instead of* the expected-counts
line and the regression-guard line, rather than in addition to them. The dispatched prompt therefore
states no counts and labels no guards, while the template still promises it does.

## Key Learnings

- **It is an `if`/`else`, not a missing feature.** `h-mad/scripts/h_mad_assemble_tdd.py:237-253`:
  `if shape == "wiring":` appends the WIRE lines; the counts line and the guards line are in the
  `else` arm. Re-verified live against this repo's working tree on 2026-09-21 — still present.
- **Proved by control/treatment with sentinel guard names**, not by reading: a `new-behaviour` task
  emits the counts and guards at prompt lines 59-60; the identical task declared `wiring` emits
  neither.
- **The blast radius is larger than the diff.** SKILL.md's own operating note says that on a wiring
  task the dispatch preamble is *the only place* counts and guard labels appear. So for HemaSuite
  Tasks 6, 12, 13 and 14 the orchestrator's habit of restating counts by hand was not *correcting*
  the spliced values — it was the sole source of them. Any wiring task dispatched by an orchestrator
  without that habit shipped with no counts at all.
- **`wiring` deliberately needs no counts, and that is not the defect.** A wiring task's RED split is
  identical either way, which is why SKILL.md exempts it from `counts_required`. The defect is that
  the **guards** go with them, and guards are orthogonal to shape.
- Not urgent for HemaSuite's current feature — its remaining Tasks 18 and 19 are `refactor`, so this
  will not bite there. It bites every `wiring` task in every project.

## Next Steps

1. Read the sender's writeup in full before designing the fix — it holds the control/treatment
   transcript and the exact prompt line numbers:
   `/Users/kimhawk/orca/HemaSuite/docs/03-analysis/h-mad-assembler-drops-counts-and-guards-on-wiring-tasks.md`
   (read-only, in the sender's tree; copy anything you need into this repo).
2. Re-verify the premise here before editing — `sed -n '236,254p' h-mad/scripts/h_mad_assemble_tdd.py`
   and confirm the counts/guards lines are still inside the `else`.
3. Decide the contract, which is the one judgement in this task: on a `wiring` task, should the
   prompt carry **WIRE lines + guards** (counts still exempt), or **WIRE lines + guards + counts**?
   SKILL.md's `counts_required` exemption argues for the first; `h_mad_assemble_tdd.py:212` is where
   that exemption is enforced and must stay consistent with whatever you choose.
4. TDD it: a RED asserting a `wiring` task's assembled prompt contains its guard labels, then the
   `if`/`else` repair. Pin both shapes — a fix that emits guards for `wiring` while dropping them for
   `new-behaviour` would pass a one-shape test.
5. Mutation-verify: collapse the repair back into the `else` arm and confirm the new test bites.
   `h-mad/tests/mutation-specs/` is the store; anchor on the emitted line, not on the `if`.
6. Run BOTH coupled suites before merging — `~/.claude/skills/h-mad` is a symlink into this checkout,
   so a change here is live for any in-flight H-MAD run and reaches sibling repos' tests.

## Open / Blocked Items

- **The fix itself** — status: not started, unblocked, ownership now here.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree, clean at handover)`
  · file: `h-mad/scripts/h_mad_assemble_tdd.py:237-253`
  · sender's evidence: `/Users/kimhawk/orca/HemaSuite/docs/03-analysis/h-mad-assembler-drops-counts-and-guards-on-wiring-tasks.md`
  · sender's filing commit (in HemaSuite, not here): `08eb0879`
- **A sibling defect in the same file, NOT part of this handover** — `h_mad_assemble_tdd.py` prints an
  unrunnable run command when `--test-path` is given subproject-relative. Workaround in use is to pass
  root-relative paths; the real fix is input validation. It stays on the sender's list because it has
  not been diagnosed to the same standard. Mentioned only so that whoever opens this file is not
  surprised to find two problems in it. If you fix both, say so and the sender will drop theirs.
- **No claim was released, because none existed.** The skills store holds 40 records and none is this
  work; the three name-similar records are other features and all are unowned
  (`tdd-dispatch-verification-discipline` phase 7, `anchor-precheck-phase-5e-wiring` phase 7,
  `assemble-tdd-path-slug` phase 0). The taker should `--create --claim` under this brief's slug.

## Context for Next Session

**Files touched this session:** none in this repo. The sender read
`h-mad/scripts/h_mad_assemble_tdd.py` only.

**Uncommitted changes:** none in this repo at the moment of handover (`git status --short` clean on
`main`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
sed -n '236,254p' h-mad/scripts/h_mad_assemble_tdd.py    # confirm the else-arm still holds counts+guards
```

**Related docs:**
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" — 5d's counts requirement and the `wiring`
  exemption
- `h-mad/SKILL.md` §"Helper scripts" → `h_mad_assemble_tdd.py` — the halt-reason list this fix must
  stay consistent with (`counts_required`, `no_wire_pin`)
- `h-mad/scripts/h_mad_wire_pin_gate.py` — the other half of the wiring contract, for reference
