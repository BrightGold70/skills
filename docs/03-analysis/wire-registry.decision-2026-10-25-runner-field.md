# Decision — a non-pytest WIRE-PIN carries a `runner` field; no resolver yet

**Date:** 2026-10-25 · **Decided by:** operator · **Status:** implemented on branch `feat/wire-pin-runner`
(the runner comes from an explicit `**WIRE-RUNNER**:` field, one per task; a non-pytest pin must
name a non-`.py` file; `verify` re-validates every record it reads)
**Origin:** handoff `docs/handoffs/2026-10-25-main__wire-registry-and-bkit-g001.md` Next Step 2
(HemaSuite PR BrightGold70/HemaSuite#52).
**Example record:** HemaSuite `document-intake-source-review::Task 6`, pin
`hemasuite/workbench/web/e2e/source-review.spec.ts::opens_every_fragment_on_original_rotated_or_cropped_page`.

## Problem

`h_mad_wire_registry.py verify` resolves every active pin against a **pytest** collection
(`collect` `:501`, `partition` `:420`). A Playwright pin can never appear in that collection, so it
falls into `missing`. That emits `step5f:wire_pin_missing:…` and turns the verdict to `FAIL`
(`:736-755`). That FAIL is a false regression report, made by construction.

## Options considered

1. **`runner` field, no resolver yet** — **CHOSEN.**
2. `runner` field plus a Playwright resolver (`npx playwright test --list` / `-g`). Rejected for
   now. It needs node, the project's Playwright install and browsers at 5f. It is slow, fragile
   across environments, and there is no checkout here to build it against. It can be added later
   with no record migration, because option 1 already stores the field it would dispatch on.
3. `status: unverifiable-by-registry`. Rejected. It records no reason. It also overloads
   `status`, whose job is the record lifecycle (`active` / `removed`). And a pytest pin could be
   parked there by hand to dodge a real FAIL.

## The decision

- A record may carry `runner`, one of `pytest` (the default when absent) or `playwright`. Absent
  means `pytest`, so all 268 existing records stay valid unchanged.
- `verify` partitions active records by runner. **Only `pytest` records reach `collect` /
  `partition` / `run_pins`.** A record whose runner has no resolver goes to a new **`unverifiable`**
  bucket.
- `unverifiable` is **cannot-judge, never FAIL and never silent PASS.** It is counted on the token
  line (`… unverifiable=N`) and named per record (`[H-MAD] step5f:wire_pin_unverifiable:<label>
  runner=playwright`). It does **not** add a FAIL driver. The verdict stays `PASS` when nothing
  else fails, so readers must read the count rather than the verdict alone. The SKILL.md 5f text
  must say so.
- Validation: `runner` must be one of the known values, and a `.py` pin must not claim
  `runner: playwright`. That closes the dodge from option 3.

## Open for the implementer (not decided here)

- **Where `runner` is set.** Records are written at 5b by `h_mad_wire_pin_gate.py` (SKILL.md
  `:491-494`). Either infer it from the pin's file (`.py` → `pytest`; `.spec.ts`/`.test.ts` →
  `playwright`), or read an explicit impl-plan field. Inference needs no new impl-plan syntax;
  explicit is self-documenting. Decide with the plan.
- **A mixed record** (a pin list naming both runners). Simplest is to refuse it at validation:
  one runner per record. Confirm with the plan.
- **Back-fill.** The HemaSuite Task 6 record needs `runner: playwright` added once this ships.

## Not in scope

The `missing=268` defect is a separate open item (task #2). It reports **every** record missing
and is an instrument fault, unrelated to runner. This decision does not fix it, and its fix does
not depend on this decision.

## Implementation route

The change touches `h_mad_wire_registry.py`, `h_mad_wire_pin_gate.py`, their tests and
SKILL.md §5b/§5f. That is three or more files, so it needs a plan first and test-first
implementation. It is filed as a follow-up and not started.
