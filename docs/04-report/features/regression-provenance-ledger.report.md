# Report: regression-provenance-ledger

**Shipped:** 2026-08-07 · **Branch:** `feature/215-regression-provenance-ledger`
**Range:** `d3bab41` (5c baseline) → `499e33e`
**Suite:** 1254 passed, 0 failed · **Match rate: 100%** · **Archreview:** `READY_TO_MERGE`

## Executive Summary

A proven wire now outlives the feature that proved it. h-mad's wire machinery was entirely
creation-time — the 5b gate, the 5d RED check and the 5e revert all fire while a wire is being
built, and nothing re-checked it afterwards. This feature adds a durable per-repo registry written
automatically on the path that already exists (5b, on `WIREPIN: PASS`) and re-verified on every
subsequent run (5f), so a later feature that breaks an earlier feature's connection fails its own
gate and is told whose wire it broke. Seven tasks, one new wire, pinned in both mutation
directions. 1254 tests pass; match rate 100%; architectural review `READY_TO_MERGE`.

The run's most useful output was not the code. Four defects of exactly the class the feature
targets — a silent no-op reporting success — were found *inside the feature*, and every one of them
was invisible to a green suite. They are catalogued below because the detection method, not the
fix, is the transferable part.

## What shipped

h-mad proved a connection the day it was built and never re-checked it. Combined with near-total
under-declaration of the `wiring` shape (HemaSuite: 4 of 172 impl-plans; 1 WIRE-PIN test in ~8000),
that is the mechanism behind "existing features lose their functionality while the suite stays
green". This feature makes a proven wire durable and re-verifies it on every subsequent run.

- **`h-mad/scripts/h_mad_wire_registry.py`** (new, stdlib-only) — record schema over
  `.h-mad/wires.jsonl`; `load()` raising on a malformed line naming the 1-based line number;
  batch `register()` with a **runtime** read-back; pure `partition()` returning three sets;
  conditional `run_pins()`; `git_show()` validating its own SHA; pure `compare()`; the `WIREREG:`
  verdict grammar with trackedness; and the warning-only AST `challenge`.
- **`h-mad/scripts/h_mad_wire_pin_gate.py`** — on `WIREPIN: PASS`, `main()` calls
  `registry.register()`. That call is the one new wire, pinned in both mutation directions.
- **`h-mad/tests/conftest.py`** — sibling J18 guard protecting the live registry.
- **`h-mad/SKILL.md`** — 5b registers, 5f re-verifies and challenges, five named halt reasons.

Two design decisions carried the shape. `check()` stays a pure predicate, so registration is I/O
and lives in `main()` — which is exactly what makes the call pinnable. And the verifier resolves
before it runs: an unresolvable node id aborts a whole pytest selection (`rc=4`), and an empty
selection collects the entire tree (1331 tests), so `run_pins()` spawns nothing when the resolving
set is empty.

## Cycle counts

| Phase | Cycles |
|---|---|
| Plan audit | 5 |
| Design audit | 8 |
| Impl-plan audit (5b) | 8 |
| Iterate (6b) | 0 |
| Architectural review (6a-prime) | 2 |

Substrate: orca, both agents dispatched headless via `exec` (no pane, no scrape).

## What the gates actually caught

Every task passed its implementer's own `STATUS: DONE` before failing an independent check.

**Three mutation sweeps came back `SURVIVED` after a DONE.** Task 4 (1 of 7), Task 5 (2 of 6 —
including the direction the report explicitly claimed verified), Task 6 (**5 of 6**). In each case
the acceptance criteria had tests; the tests simply did not discriminate, which is
indistinguishable from absent until something mutates them.

**Four defects were found by running the tool, not by the suite.** All four would have shipped:

1. `collect()` ignored pytest's return code. h-mad scripts are documented to run under a bare
   `python3`, which here has no pytest — so collection returned an **empty set**, every pin
   partitioned to `missing`, and the gate announced that all wires were gone when it had never run.
   A cannot-judge rendering as a verdict.
2. `collect()`/`run_pins()` ran with `cwd=rootdir`, yielding rootdir-relative node ids, while
   registered pins are repo-relative and matched by string equality. They could never match except
   at the repo root — which this repo cannot collect at all. **Every registered wire would have
   reported `missing`**: the maximal false FAIL, in the only working configuration.
3. `_register_wiring_tasks` required an ASCII `->`, but the impl-plan template every plan is
   generated from writes **U+2192 `→`**. Registration silently skipped every real wiring task while
   the gate printed `WIREPIN: PASS`. It survived 96 gate tests, 6/6 mutations and the wire-scoped
   revert **because every fixture wrote the arrow as tidy ASCII** — the fixtures made the defect
   class unreachable rather than merely untested.
4. (6a-prime) A pin whose test ERRORed in setup, or was SKIPPED/XFAILed, landed in neither bucket:
   it printed `INTERNAL INCONSISTENCY`, which carries no halt marker and no verdict effect, and
   `broken` stayed empty. Reproduced live: `WIREREG: PASS registered=1 verified=0 broken=0`, exit 0,
   for a definitively broken wire. Now fails closed, naming the reason per pin.

Defects 1–4 are all the same shape as the one the feature was built to remove, occurring inside
the feature. That is the finding worth carrying forward.

## Proof it works

```
gate on the real impl-plan   → WIREPIN: PASS … registration: registered=1 skipped=0
verify                       → registered=1 verified=1 broken=0
delete the connection        → BROKEN regression-provenance-ledger: <pin>
                               [H-MAD] step5f:wire_regression:Task 5   broken=1
```

The wire-scoped revert makes the structural point: with the connection deleted and the callee
untouched, the WIRE-PIN fails while `test_h_mad_wire_registry.py` stays **54/54 green**. A
module-level revert removes both sides and is incapable of establishing this.

## Corrections to the process, not just the code

- **Impl-plan audits never inline the paired plan.** Eight clean 5b cycles verified impl-plan ↔
  design and were structurally blind to `plan.md` drifting. Found by inspection; the plan's v1.5
  entry records the blind spot, not just the fix.
- **5b surfaced defects in the design itself**, and audit cycle 7 correctly refused to defer them
  to 6a-prime — 6a-prime reviews code *against* the design, so a stale design would have flagged
  correct code as drift. Design back-propagated to v1.9 in the same pass.
- **A `REFUSED` mutation is not a pass.** One sweep came back `REFUSED` because two anchors were
  written from memory rather than read from the source; they matched zero times, leaving the guards
  intact and the suite green — which is exactly what an enforced guard looks like.

## Residual / carried

- **FR-5 ships warning-only.** It rests on a static AST name index, so dynamic dispatch, `getattr`,
  and config-driven binding are invisible to it. A floor on detection, never a proof of absence;
  it may not gate a verdict until its false-positive and false-negative rates are measured.
- **`.h-mad/` is gitignored in this repo**, so `verify` reports `UNTRACKED` here until an operator
  adds `!.h-mad/wires.jsonl`. That is FR-3 working as designed — it refuses to report coverage it
  cannot persist — and is an operator decision.
- **Nothing registers retroactively.** The registry starts empty and fills as features pass 5b, so
  the ledger's value compounds rather than arriving whole.
- **Operational hazard worth knowing:** `.h-mad/` holds both ignored runtime state and the
  **tracked** `invariants.md`. Cleanup must target `.h-mad/wires.jsonl` specifically; `rm -rf .h-mad`
  deletes a load-bearing tracked file. Hit once during this run, caught before any commit.

## Version History

- v1.0 (2026-08-07): Phase 7 closure. Range `d3bab41`..`499e33e`. 1254 passed / 0 failed,
  match rate 100%, `ASSESSMENT: READY_TO_MERGE` at 6a-prime cycle 2 (cycle 1 returned
  `WITH_FIXES` with 2 Critical + 2 Important, all four premises verified and all four fixed).
  Audit cycles: plan 5, design 8, impl-plan 8, iterate 0. Substrate orca, both agents via `exec`.
