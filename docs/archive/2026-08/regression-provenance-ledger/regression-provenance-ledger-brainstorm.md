# Brainstorm: regression-provenance-ledger

## Executive Summary

H-MAD can prove a connection exists on the day it is built and has **no mechanism that ever
re-checks it**; combined with near-total under-declaration of `wiring` tasks (4 of 172 impl-plans
in HemaSuite), that leaves almost every wire in the codebase unguarded, which is why existing
features silently lose functionality while the suite stays green.

## Problem Statement

New features break connections that older features established. The suite stays green because
nothing ever asserted the connection — not because a test was deleted or weakened.

## Measured evidence

Gathered before drafting, and it redirected the design away from the operator's and my own first
hypothesis.

**Test deletion is NOT the dominant mechanism.** Across the last 14 merged features:

| repo | features that deleted tests | that removed assertions |
|---|---|---|
| `skills` | 1 of 14 (this session's own, 6 removals) | 2 of 14 |
| `HemaSuite` | 3 of 14 | 7 of 14 (worst: #188, 19 assertions) |

Real, worth guarding, but far too rare to explain "many existing features lost their
functionality".

**Wire declaration is the actual hole.**

```
HemaSuite:  172 impl-plans  ·    4 declare a `wiring` task
            ~8000 tests     ·    1 WIRE-PIN test file in the entire suite
skills:      the wire-pin gate did not exist until 2026-08-02 (eac5c8f)
             exactly 1 impl-plan has ever declared a wiring task
```

So ~98% of tasks that connected something declared themselves `new-behaviour` or `refactor`, and
carry no pin. Nothing can notice when those wires die.

**Every h-mad wire mechanism is creation-time only.** The 5b wire-pin gate checks the *plan*
declares a pin; 5d checks the RED fails for a caller-side reason; 5e runs the wire-scoped revert.
All three fire while the wire is being built. **None runs again, ever.** A wire is proven once and
then trusted forever.

**The known losses match this shape exactly**, and each was caught by a live run rather than the
suite:

- `lecture-reference-binding` — green suite, then live proved **0 of 30 citations bound**; the PDF
  tier was structurally dead.
- `#88 manuscript-section-config-resolution` — **80/80 sections had fallen to `_default`**.
- `#35` — narrative runs shipping **empty manuscripts**; one poisoned block failed all 9 refinement
  items and a `1.00 vacuous` score passed them.

Note the form of all three: **a collapsed counter at a chokepoint** (`0/30`, `80/80`, empty). That
is what a lost wire looks like from the outside, and it is measurable.

## Proposed Approach

**A standing wire registry, re-verified on every run.** Three parts, in dependency order:

1. **Registry** — wires become durable records in `.h-mad/wires.jsonl` (caller → callee, the pin
   test, the owning feature), not lines in one feature's impl-plan that stop mattering once it
   merges.
2. **Standing re-verification** — every feature's Phase 5f/6 re-runs the whole registry, not just
   its own pins. Breaking feature A's wire fails feature B's gate, with A named. This is the part
   that converts "proven once" into "still true".
3. **Shape challenge at 5b** — stop trusting the self-declaration. If a task's production diff adds
   or changes a call crossing a module boundary and the task did not declare `wiring`, fail and make
   it declare. 4 of 172 is not a true rate; it is the measure of an unchallenged opt-in.

Removal from the registry is allowed but must be **declared with provenance** — this is where the
original "deletion ledger" idea belongs: as the supporting rule that stops a red pin being deleted
to get green, not as the headline mechanism.

## Alternatives Considered

- **Deletion/provenance ledger alone** (my first recommendation to the operator) — rejected as the
  *primary* mechanism on the measurement above: it guards tests that exist, and the problem is that
  the wires were never pinned. It survives as part 3's removal rule.
- **Net-assertion-count floor** — rejected. Already prose in this repo and unenforced for good
  reason: 7 removed against 56 added passes trivially, and it creates pressure to pad.
- **Extend 6a-prime to review removals** — rejected. It already had this session's diff, saw six
  test removals, and returned `READY_TO_MERGE` without mentioning them. Advisory ≠ gate.
- **Full call-graph extraction to auto-discover every wire** — deferred, not rejected. It is the
  only thing that retro-covers the 168 undeclared plans without human input, but dynamic dispatch,
  config-driven binding and framework hooks make the graph noisy, and a noisy gate gets disabled.
  Candidate follow-on once the registry shape is proven.
- **Chokepoint counter invariants** (`bound > 0`, `sections resolved by config == total`) — strong
  and matches all three known losses, but only observable in a live e2e, which most features do not
  run. Candidate follow-on, and the natural bridge to a live-e2e gate.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Bootstrapping: 168 existing plans have no pins, so the registry starts near-empty and guards almost nothing on day one | **H** | Seed deliberately rather than pretending coverage exists: register a wire whenever a feature *touches* one, and backfill the known-lost wires (lecture PDF tier, section config resolution) as the first entries. Report registry size in the Phase-7 row so coverage is visible, never implied |
| Registry rot — a pin that no longer compiles gets commented out to get green | M | Removal requires a declared provenance entry; an undeclared drop fails the gate. This is the deletion-ledger idea, correctly scoped |
| Shape challenge is noisy — every import looks like a wire | **H** | Scope to calls crossing a declared module boundary, and start it as a *warning* that must be acknowledged rather than a hard fail, so the false-positive rate is measured before it can block |
| Cross-repo blast radius — the gate ships through the symlink and hits HemaSuite's 8000-test suite immediately | M | Registry is per-repo (`.h-mad/wires.jsonl`); an absent registry means an empty one, so the gate is a no-op until a repo seeds it |
| The gate protects wires and the operator's losses are broader than wires | M | Open question below; resolve in Phase 2 before committing scope |

## Dependencies

None external. Builds on existing h-mad machinery: the `wiring` task shape, `WIRE`/`WIRE-PIN`
fields, `h_mad_wire_pin_gate.py`, and the wire-scoped revert. This feature makes them **persistent
and re-checked** rather than adding a parallel mechanism.

## Open Questions

1. **Is "wiring" the whole of the operator's pain, or its most legible part?** The answer given was
   "many existing features lost their functionalities like losing wiring" — *like* may be an
   analogy. If the real class is "any shipped guarantee silently stops holding", the registry should
   store behavioural invariants, of which a wire is one kind. This changes the record shape and must
   be settled in Phase 2.
2. **What re-verifies a wire that has no runnable pin?** The 168 undeclared plans cannot get a pin
   without someone writing one. Is a *declared but unpinned* wire (a documented edge with no test) a
   useful registry entry, or does it manufacture false confidence?
3. **Where does the standing re-verification run** — 5f (cheap, every run) or Phase 6 (once, before
   closure)? 5f catches it earlier; Phase 6 keeps the inner loop fast.
4. **Does a live-e2e chokepoint counter belong in this feature or the next?** All three known losses
   were caught by a counter in a live run and by nothing else.

## Version History
- v1.0: Initial brainstorm draft. Direction changed during drafting: the deletion-ledger approach
  originally advised was demoted after measurement showed test deletion occurs in 1 of 14 features
  here and 3 of 14 in HemaSuite, while wire declaration sits at 4 of 172 impl-plans and 1 pin test
  across ~8000 tests.
