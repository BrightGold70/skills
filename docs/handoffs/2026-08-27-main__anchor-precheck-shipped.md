# Handoff — anchor-precheck-phase-5e-wiring shipped; J30/J42 reconciled

**Date:** 2026-08-27
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Resumed `anchor-precheck-phase-5e-wiring` from the 2026-08-26 handoff (paused mid-5d with Task 1
RED committed) and carried it to **done**: Tasks 1–7, Phase 5f/5g, seven 6a-prime cycles, Phase 7,
archived, **merged to `main` as `713f9ad` and pushed**. 38/38 ACs, both coupled suites green.
Afterwards reconciled `J30` (closed five days earlier, row never flipped) and fixed the `J42` it
turned up. Nothing is in flight; the registry has 8 deliberate deferrals.

## Key Learnings

- **A fix can silently hollow an assertion written two cycles earlier.** The WIRE-PIN proved
  ordering via "the count keys are absent". Cycle 1 then changed `run_spec` to build a *fresh*
  dict for `PRECHECK_FAILED`, making that true **by construction** — the pin went tautological
  without anyone touching it. Re-verify pins after any change to the shape they assert on.
- **One clean audit cycle is not a stopping signal, and this is now measured rather than
  asserted.** Cycle 3 returned `READY_TO_MERGE`; cycle 4 then found a Critical vacuous pass. The
  cycle sequence was 3, 2, CLEAN, 3, 2, 2, CLEAN.
- **The two defects a green suite of 2107 tests could never surface were both ones the feature
  introduced into its own guarantees** — `--check-anchors` reporting `ANCHORS_OK` on a sweep that
  examined nothing, and the WIRE-PIN above. Neither is a coding error; both are guarantees quietly
  ceasing to hold.
- **3 of 12 reviewer findings had premises that failed checking.** One cited a "Facade-Routing
  invariant" that exists in neither invariants layer — and *proving that null was real needed a
  positive control*, because a grep returning nothing looks identical to a grep against the wrong
  file. Another prescribed a `_load_spec` reorder AC-6.1 does not ask for; a third demanded AC-6.6
  become a unit test when that AC's own text says "a passing suite is not accepted as evidence".
- **A dispatch report can be right about its actions and wrong about its numbers.** One reported
  the sweep as `mutations=238` when the tree held 244, every spec byte-identical to HEAD, inside a
  report whose other figures all checked out. Re-derive counts; never carry one from a report.
- **A monitoring row can outlive its fix by days.** J30's fix merged 2026-08-22; the row still read
  `MONITORING` on 08-27, so the memory file said CLOSED while the registry said open. Related: a
  "registry 0 open" census in memory was true for two days and then wrong for weeks.
- **`h_mad_state_write.py` refusing an invented key is the guard working.** It refused
  `merged_sha`; the schema's completion vocabulary is `last_completed_phase` + `phase=null`, and
  the sha belongs in git.

## Next Steps

Nothing is blocked or owed on this feature. The registry is the only queue:

1. `[suggested]` Work `J34` — `h_mad_assemble_tdd.py` composes `--out`/`--log` from the module path
   verbatim, so every command block it prints for this repo names a non-existent directory —
   `h-mad/scripts/h_mad_assemble_tdd.py`, see `docs/skill-monitoring.md`
2. `[suggested]` Work `J35` — `hmad-dispatch progress` exits non-zero on a normal LIVE poll, against
   SKILL.md's own "0 for every observable state by design"
3. `[suggested]` Work `J37` (🔴) — `ANCHORS_DRIFTED`/`REFUSED` each still absorb two distinct
   cannot-judges; this is the long-standing F2, deferred by operator decision, not an oversight

## Open / Blocked Items

- **Registry: 8 open** (`J34`–`J41`) — all deliberate deferrals, none blocking, all in
  `docs/skill-monitoring.md`. Nothing parked outside this repo/branch.
- **Old plans without reports** — `claude-context-reduction`, `hemasuite-100-percent`,
  `hpw-csa-*`, `hpw-protocol-extraction` in `docs/01-plan/features/`. Pre-existing, carry no
  `status:` frontmatter, and unrelated to this session — recorded so the next scan does not
  re-derive them, not proposed as work.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_mutation_harness.py` — `_resolve_root`, `classify_spec_file`,
  `_sibling_specs`, the sibling precheck wire, `PRECHECK_FAILED`, `ANCHORS_NOTHING_SWEPT`
- `h-mad/tests/test_h_mad_mutation_harness.py` · `handoff/tests/test_mutation_specs_clean.py` (new)
- `h-mad/tests/mutation-specs/*.json` — all 17 re-rooted to `../..`; `mutation_harness.json` 24→36
- `h-mad/SKILL.md` · `h-mad/references/failure-recovery.md` · `h-mad/tests/test_h_mad_batch_doc_rules.py`
- `docs/skill-monitoring.md` — J30 flipped, J34–J42 filed, J42 fixed
- `docs/archive/2026-08/anchor-precheck-phase-5e-wiring/` — 33 docs + 7 `.archreview.vN.md`

**Uncommitted changes:** none — clean at `713f9ad`, `origin/main == main`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
grep -c '| MONITORING |' docs/skill-monitoring.md   # the only open queue: expect 8
```

**Environment facts that each cost a real mistake to learn:**
- Interpreter is `/opt/anaconda3/bin/python3.11`. A bare `python3` is 3.14 with **no pytest** —
  `h_mad_wire_registry.py verify` fails opaquely under it.
- Every `exec codex` needs `--model gpt-5.5`.
- Never `timeout`/`gtimeout` — use `hmad-dispatch run --timeout <s> -- <cmd>`.
- Commit messages go through `git commit -F <file>` (bkit ENH-310).
- **zsh does not word-split unquoted `$var`** (only command substitution), so
  `--check-anchors $SPECS` silently collapses to one argument and reports `specs=1`.

**Related docs:**
- `docs/archive/2026-08/anchor-precheck-phase-5e-wiring/` — report, analysis, dogfood ledger
  (F1–F18), and the seven architectural reviews
- `docs/skill-monitoring.md` — the standing registry
