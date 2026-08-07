# Plan: regression-provenance-ledger

## Executive Summary

Make a proven wire durable: register it on the existing 5b path, re-verify every registered wire on
every subsequent run using a resolve-first/run-second scheme that keeps `missing` and `broken`
distinguishable, and refuse to report coverage the registry cannot actually persist.

## Overview

H-MAD proves a connection the day it is built and never re-checks it. Combined with near-total
under-declaration of the `wiring` shape, almost every wire in both repos is unguarded — which is
the mechanism behind "existing features lose their functionality while the suite stays green".

## Scope

New: `h-mad/scripts/h_mad_wire_registry.py` (writer + verifier), `.h-mad/wires.jsonl` (per-repo
data), tests. Modified: `h-mad/scripts/h_mad_wire_pin_gate.py` (FR-6 registration hook),
`h-mad/SKILL.md` (5b registration + 5f re-verification), `h-mad/references/…` as needed.
User-visible: a feature that breaks a previously registered wire fails its own gate and is told
whose wire it broke. No change to Phase 3/4 audit gates, the mutation harness, or the Phase-7 gate.

## Goals

- A proven wire outlives the feature that proved it — FR-1
- Every run re-verifies every registered wire, naming the owner on breakage — FR-2
- Coverage is never implied; an unpersistable registry cannot report PASS — FR-3
- Removing a wire is declared, not performed by deletion — FR-4
- Under-declaration of `wiring` is challenged and *measured* before it is enforced — FR-5
- Registration cannot be forgotten, because it rides the path that already exists — FR-6

## Requirements

FR-1 durable registry · FR-2 standing re-verification · FR-3 provenance vs absence ·
FR-4 declared removal · FR-5 shape challenge (warning-only) · FR-6 registration on the 5b path

## Verified assumptions (probe evidence)

Every claim below was executed in this repo before the plan was written.

**A1 — the same gate would behave differently per repo, silently.** `.h-mad/` is gitignored in
`skills` and is not in HemaSuite:

```
$ git -C skills check-ignore -v .h-mad/wires.jsonl
.gitignore:32:.h-mad/   .h-mad/wires.jsonl
$ git -C HemaSuite check-ignore -v .h-mad/wires.jsonl
(not ignored in HemaSuite)
```

A registry written to the default path in `skills` would never be committed, so the gate would
report `registered=0 PASS` forever. FR-3 exists because of this measurement, not in anticipation.

**A2 — under-declaration is the hole, not test deletion.**

```
HemaSuite:  172 impl-plans · 4 declare a `wiring` task · 1 WIRE-PIN test file in ~8000 tests
skills:     wire-pin gate created 2026-08-02 (eac5c8f) · 1 impl-plan has ever declared wiring
```

Test deletion, by contrast, appears in 1 of the last 14 features here and 3 of 14 in HemaSuite —
real, but far too rare to explain the reported pain.

**A3 — PRINCIPAL DESIGN DRIVER: one unresolvable node id aborts the entire selection.** Running a
valid pin alongside a renamed one does not run the valid pin:

```
$ pytest <real-pin> <renamed-pin> -q
ERROR: not found: …::test_does_not_exist
no tests ran in 0.02s          rc=4
$ pytest <real-pin> -q
1 passed                        rc=0
$ pytest <real-pin> <renamed-pin> -q --continue-on-collection-errors
no tests ran                    rc=4      # the flag does NOT rescue it
```

**This falsifies the spec's NFR as written** ("must support running the registry as a single test
selection"). A single selection over all pins means one renamed pin verifies **zero** wires while
producing no test failures — precisely the silent no-op this feature exists to remove. `rc=4`
(pytest `USAGE_ERROR`) is distinct from `rc=1` (failures) and `rc=0`, so the condition is
detectable; it just cannot be recovered from inside one selection.

**A4 — resolve-first is cheap and exact, so A3 is fully mitigable.** One whole-suite collection
yields matchable node ids:

```
$ pytest h-mad/tests/ --collect-only -q      →  1086 tests collected in 0.23s (real 0.68s)
$ … | grep -cF '<a real pin node id>'        →  1
$ … | grep -cF '<a renamed pin node id>'     →  0
```

So all `N` pins resolve by set membership against **one** collection — O(1) subprocesses, not O(N)
— and only the resolving set is then executed. Total cost: two processes regardless of registry
size. This is what makes AC-2.3 mechanical rather than aspirational.

**A5 — every existing wire mechanism is creation-time only.** The 5b gate reads the impl-plan, 5d
checks the RED failure reason, 5e runs the wire-scoped revert. All three fire while the wire is
being built; none re-runs afterwards. Verified by reading `SKILL.md` §5b/5d/5e — there is no
consumer of `WIRE-PIN` after 5g.

## Implementation Strategy

**Resolve, then run — never one selection over everything.** The verifier makes **at most** two
subprocess calls: a whole-suite `--collect-only -q` to partition registered pins into
resolving/missing, then a single run of the resolving set. `missing` is derived without executing
anything, which is why it cannot be confused with `broken`.

**The second call is skipped entirely when the resolving set is empty — this is a correctness
guard, not an optimisation.** `pytest` with no node-id arguments does not run nothing; it collects
the whole tree. Measured from this repo root:

```
$ pytest -q --collect-only          →  1331 tests collected
$ pytest -q ""                      →  (same whole-tree collection)
```

So a registry whose pins are all `missing` or all tombstoned would, on a naive implementation, run
the **entire suite** and report `verified=` the whole test count — a false PASS at maximum scale,
produced by the one gate meant to prevent false passes. When the resolving set is empty the
verifier makes one subprocess call, not two, and yields `verified=0 broken=0` with the `missing`
count intact.

**`missing` and `broken` have opposite remedies, so they must never share a count.** `broken` means
the code regressed — fix the code. `missing` means the pin itself is gone — FR-4 applies. Collapsing
them re-creates the hole: a deleted pin would read as "nothing to run".

**A removal is a tombstone in the registry, not a second store.** FR-4's declaration lives at the
same `id`, in `.h-mad/wires.jsonl`, as a record whose `status` becomes `removed` and which carries
`removal_provenance` (`superseded` | `pinned-a-defect` | `renamed`), `removed_by_feature`, and for
`superseded` the superseding feature. **Removing a wire therefore means editing its line, never
deleting it**, and an `id` present at `BASE` that is *absent* at `HEAD` — as opposed to
tombstoned — is the undeclared removal AC-4.1 fails on.

A `renamed` tombstone carries an explicit **`successor_pin`** field naming the new node id; AC-4.3's
mechanical check is "that successor resolves in the collection AND passes when run". Renaming is
deliberately *not* modelled as editing the surviving record's `pin` in place, because an in-place
edit is indistinguishable in a `BASE..HEAD` diff from repointing a pin at a weaker test — the
tombstone plus successor keeps both the old identity and the new one on the record.

**`BASE` is supplied explicitly by the orchestrator, and its absence is an operational error —
`exit 2`, not a new verdict token.** The verifier takes `--base <sha>` (the 5c baseline the
impl-plan already records) and does not guess it from `origin/HEAD`, `main`, or a reflog — the
fanout-teardown defect measured earlier in this repo came from exactly that kind of inferred base.
A missing required input is a *cannot-judge*, which the established grammar already has a slot for:
`exit 2`, exactly as `UNREADABLE` does in the wire-pin gate and `h_mad_state_validate.py`. Inventing
a bespoke stdout token that exits 0 would dilute the verdict grammar and re-open the very confusion
the token discipline exists to prevent. It may print a diagnostic token alongside (the `UNSHAPED`
precedent), but the exit code carries the signal, and it cannot be mistaken for `PASS`.

The BASE registry is read with `git show <base>:.h-mad/wires.jsonl`, not from a working-tree copy —
a working-tree read would compare HEAD against itself whenever the file is dirty. A `BASE` at which
the file did not yet exist is "no registry then", not an error: every `id` present at HEAD is new.

Three alternatives for the declaration's home were rejected. A separate `.h-mad/wire-removals.jsonl` doubles the surface FR-3
must check for trackedness and lets the two files disagree. Declaring in the impl-plan puts a
permanent fact in a per-feature document nothing reads after that feature merges — the exact
creation-time-only mistake A5 measured. A free-standing ledger file needs its own BASE..HEAD
reconciliation, which is the problem being solved, one level up. The tombstone makes AC-4.4
("discoverable from the removal alone") true by construction: the declaration *is* the record, at
the same key.

**Coverage is reported, never implied.** `registered=N` appears on every verdict including `PASS`,
so a green gate over an empty registry is legible as exactly that. This is the honest answer to the
bootstrapping problem — the registry starts near-empty and must *look* near-empty.

**FR-5 is warning-only in this feature, deliberately.** The shape challenge is the highest-value
idea here and the highest false-positive risk; 4-of-172 is a measure of an unchallenged opt-in, not
a true rate. Shipping it as a hard failure risks a gate noisy enough to be disabled, which is worse
than none. It reports raised/acknowledged counts so a later feature can promote it on data.

**Spec correction required (back-propagation).** The NFR "must support running the registry as a
single test selection" is falsified by A3 and must be restated as "two subprocesses total,
independent of registry size — one resolve, one run". Carried as a Phase-2 amendment rather than
silently reinterpreted.

**Deliberately untouched:** Phase 3/4 audit gates, `h_mad_mutation_harness.py`,
`h_mad_phase7_preconditions.py`, and the `WIRE`/`WIRE-PIN` parsing already in the 5b gate — FR-6
extends that parser rather than duplicating it.

## Architecture Considerations

- **The verifier is a pure function over (registry, collected node ids, run results)**, so FR-1–FR-4
  are unit-testable with no live pytest run; the two subprocess calls are the only I/O.
- **Registration rides the 5b gate** because a separate step gets forgotten — the same omission
  class as the Phase-7 `archreview` hole this session just closed, where the field was optional by
  omission and nothing marked the absence.
- **That registration hook is itself a wire, and this feature must pin it.** A read-back check
  (AC-6.2) proves the write landed; it does **not** prove the 5b gate still calls the writer. Delete
  the call and the writer keeps working, its unit tests keep passing, and registration silently
  stops — the exact failure mode this feature exists to catch, reproduced inside it. The
  registration task is therefore `wiring` shape with a `WIRE-PIN` that fails on a wire-scoped
  revert (call removed, callee intact), per `invariants.base.md` §"Connection enforcement" —
  **in both directions**. `invariants.base.md:107` requires the second mutation too: force the
  connection to fire **unconditionally** and confirm the fall-through/negative test fails. One
  direction certifies only that the wire can be absent, not that it is *conditional*; a
  registration hook that fires on every task, including non-`wiring` ones, would pass the
  removal-direction pin and silently pollute the registry.
- **Symlink coupling.** `~/.claude/skills/h-mad` is this repo, so the gate is live for the run that
  builds it. Unlike `gate-blindness-hardening`, an absent registry is a no-op (AC-3.1), so there is
  no self-deadlock — but the first registered wire is live immediately.
- **Registry is data, not behaviour**, and per-repo. An absent file means an empty registry, so
  every existing repo and in-flight feature is unaffected until it seeds one.
- **The writer decides *where* state is written, which is the J18 hazard exactly.** Mutation-testing
  `_pin_file`'s override branch once redirected the whole suite's writes onto the developer's live
  `.h-mad/orca-pins.env`, replacing two real agent handles with test fixtures — while the run
  reported 642 passed, because the tests assert what a file contains and never where it is *not*.
  This feature adds a second such resolver, so the same protection is mandatory and belongs in the
  same place: extend `h-mad/tests/conftest.py`'s existing session-scoped autouse guard
  (`_protect_live_pin_file`) to snapshot and restore the live `.h-mad/wires.jsonl`, failing loudly
  and naming the likely cause if the session moved it. Per-test `tmp_path` redirection is necessary
  but **not** sufficient: the failure mode is a mutation that disables the redirection branch
  itself, which no test using that branch can detect.

## Deliverables

| Deliverable | Target file(s) | Satisfies |
|---|---|---|
| Registry record schema + writer. Required fields per AC-1.1: `kind`, `id`, `caller`, `callee`, `pin`, `owning_feature`, `registered_ts`; plus `status` and, on a tombstone, `removal_provenance`, `removed_by_feature`, and `successor_pin` for `renamed`. Dedupe by `id`, validated `kind` enum, loud malformed-line failure naming the line number | `h-mad/scripts/h_mad_wire_registry.py` | FR-1 |
| Live-registry protection: extend `conftest.py`'s session-scoped autouse guard to snapshot/restore `.h-mad/wires.jsonl` (J18 class — the writer is a path resolver) | `h-mad/tests/conftest.py` | FR-1, base invariant |
| Resolve-first verifier + `WIREREG:` token with `registered/verified/broken/missing` | `h-mad/scripts/h_mad_wire_registry.py` | FR-2 |
| Trackedness detection + `UNTRACKED` verdict + repo-specific remedy text | `h-mad/scripts/h_mad_wire_registry.py` | FR-3 |
| Tombstone removal (`status: removed` + provenance enum at the same `id`) + `BASE..HEAD` absent-vs-tombstoned comparison + mechanical `renamed` check | `h-mad/scripts/h_mad_wire_registry.py` | FR-4 |
| Shape challenge (warning-only) + raised/acknowledged counts + configurable boundaries | `h-mad/scripts/h_mad_wire_pin_gate.py` | FR-5 |
| Auto-registration on a passing 5b wiring task, verified by read-back | `h-mad/scripts/h_mad_wire_pin_gate.py` | FR-6 |
| **Connection-enforcement test for the 5b→writer link** — the impl-plan task that adds registration MUST be `wiring` shape and carry a `WIRE-PIN` that fails when the *call* from the 5b gate to the registry writer is removed while the writer itself is left intact | `h-mad/tests/…` (pin), impl-plan (declaration) | FR-6, base invariant |
| Protocol: 5b registers, 5f re-verifies. The 5f step MUST name its halt reasons and emit an `[H-MAD]` marker on each — `step5f:wire_regression:<id>` on `broken`, `step5f:wire_pin_missing:<id>` on an undeclared `missing`, `step5f:registry_untracked` on `UNTRACKED` — so a halted run is diagnosable from logs alone (`invariants.base.md:61`) | `h-mad/SKILL.md` | FR-2, FR-6, base invariant |
| Unit tests for all of the above | `h-mad/tests/test_h_mad_wire_registry.py` (new) | FR-1–FR-4 |
| Doc tests for the protocol contract | `h-mad/tests/test_h_mad_wire_pin_gate.py` or a doc-test home | FR-5, FR-6 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **One renamed pin verifies zero wires and reports no failures** | The gate becomes the silent no-op it was built to prevent | A3/A4: resolve-first partitions before running; `missing` is derived without execution and fails the gate unless declared (AC-2.4) |
| Registry unpersistable in `skills` (gitignored) while working in HemaSuite | Coverage reported that would not survive a clone | FR-3: `UNTRACKED` is a distinct verdict that is **not** PASS, with repo-specific remedy text |
| Registry starts near-empty, guarding almost nothing | False confidence that regressions are now caught | `registered=N` on every verdict incl. PASS (AC-3.4); seed by registering whenever a feature touches a wire; report the number in the Phase-7 row |
| Shape challenge false positives | A noisy gate gets disabled, losing the whole mechanism | FR-5 warning-only, verdict-neutral (AC-5.2), with raised/acknowledged counts so promotion is data-driven |
| A red pin is commented out to reach green | The exact evasion this feature exists to stop | FR-4: an undeclared removal fails, naming the `id` and its owning feature |
| Node ids are not as stable as assumed | Spurious `missing` on ordinary refactors | AC-4.3 `renamed` is mechanically verified (new pin must resolve AND pass); a rename that cannot be verified is treated as `superseded` and must name a successor |
| Feature is live for its own run via the symlink | Self-inflicted block | Absent registry is a no-op (AC-3.1); register this feature's own wires only after the verifier is green |

## Convention Prerequisites

- Branch `feature/NNN-regression-provenance-ledger` off `main` at 5c.
- Codex authors Phase 5 under the TDD gate; RED before GREEN per task.
- Every new guard mutation-verified via `h_mad_mutation_harness.py`, passing `root` explicitly
  (its default is the spec file's directory, which yields `BASELINE_NOT_GREEN` from a scratchpad).
- Both coupled suites (h-mad + handoff) green before merge; measure the branch-point count fresh
  rather than carrying a number from a prior feature.
- Any pre-existing test this feature inverts must assert the new contract positively and be renamed
  to match what it asserts — a deletion is not a substitute.

## Success Criteria

- All spec ACs pass automated tests.
- A registry containing one **undeclared renamed** pin and one **failing** pin produces
  `WIREREG: FAIL registered=2 verified=0 broken=1 missing=1` — the two are separately counted, from
  one resolve and one run. A **declared** rename (tombstoned with `removal_provenance: renamed` and
  a successor pin that resolves and passes) does **not** count as `missing`; that is the whole
  difference FR-4 buys.
- Deleting a registry line rather than tombstoning it fails the gate, naming the `id` and its
  owning feature.
- Removing the 5b gate's *call* to the registry writer, with the writer left intact, fails the
  registration task's `WIRE-PIN`.
- A registry file that exists but is gitignored produces `WIREREG: UNTRACKED`, never `PASS`.
- An absent registry produces `WIREREG: PASS registered=0` and blocks nothing.
- Verifier cost is at most two **pytest** subprocesses regardless of registry size, and **exactly
  one** when the resolving set is empty. **No per-record process of any kind.** The handful of git
  calls (trackedness, SHA validation, BASE read) are O(1) in registry size and several are skipped
  outright — the constraint exists to forbid work that scales with `N`, not to cap total processes.
- A registry whose pins are **all** missing or tombstoned reports `verified=0 broken=0` and does
  **not** invoke pytest a second time — asserted directly, because the naive implementation would
  collect the whole tree (1331 tests here) and report it as verified.
- Invoked without `--base`, the verifier **exits 2** (operational error), never `PASS` and never a
  verdict exit.
- Removing the 5b gate's call to the writer fails the `WIRE-PIN`, **and** forcing the registration
  to fire unconditionally fails a fall-through test — both mutation directions, per
  `invariants.base.md:107`.
- Mutating the registry writer's path-resolution branch does not touch the developer's live
  `.h-mad/wires.jsonl`: the conftest guard fires, restores it, and turns the suite red.
- This feature's own wires are registered and re-verified by its own verifier before merge.

## Out-of-Scope (confirmed from spec)

- Call-graph auto-discovery of undeclared wires; chokepoint counter invariants (the `kind` field
  exists so these can be added without reshaping the registry).
- Promoting FR-5 to a hard failure; backfilling the 168 undeclared impl-plans.
- Any change to the audit gate, mutation harness, or Phase-7 gate.

## Next Steps

Operator approves v1.0 → Phase 3 audit cycle via `exec agy` → gate to must-fix = 0 and
should-fix = 0 → Phase 4 design.

## Version History
- v1.0: Initial plan draft. Five assumptions probed before drafting; A3 (one unresolvable node id
  aborts the whole selection, and `--continue-on-collection-errors` does not help) falsified the
  spec's single-selection NFR and became the principal design driver, with A4 establishing that
  resolve-first costs two subprocesses regardless of registry size.
- v1.1: Plan audit cycle 1 — 2 must-fix, 0 should-fix, 1 nit. Both premises checked and held.
  1. **This feature's own new wire was unpinned.** The 5b-gate→registry-writer link is a
     connection, and AC-6.2's read-back proves only that the write landed, not that the gate still
     calls the writer: delete the call and the writer keeps working with its unit tests green,
     while registration silently stops. A feature about wire enforcement had reproduced the exact
     failure it exists to catch, inside itself. The registration task is now mandated `wiring`
     shape with a `WIRE-PIN` that fails on a wire-scoped revert, as a deliverable and a success
     criterion.
  2. **FR-4 never said where a removal declaration lives.** Resolved as a **tombstone at the same
     `id` in the registry** — removal edits the record (`status: removed` plus provenance) and
     never deletes the line, so an `id` absent at `HEAD` rather than tombstoned is the undeclared
     removal. Three alternatives were rejected in-plan: a second `.jsonl` doubles FR-3's
     trackedness surface and can disagree with the registry; declaring in the impl-plan buries a
     permanent fact in a per-feature document nothing reads after merge — the creation-time-only
     mistake A5 measured; a free-standing ledger needs its own BASE..HEAD reconciliation, which is
     the problem being solved one level up. The tombstone makes AC-4.4 true by construction.
  3. (nit, applied) Success criteria now say **undeclared** renamed pin, and state explicitly that
     a declared rename does not count as `missing`.
- v1.2: Plan audit cycle 2 — 2 must-fix, 1 should-fix. All three premises checked; the first was
  probed rather than reasoned about.
  1. **An empty resolving set would have run the whole suite.** `pytest` with no node-id arguments
     collects the entire tree — measured at **1331 tests** from this repo root — so a registry whose
     pins were all `missing` or tombstoned would report `verified=` the full test count: a false
     PASS at maximum scale, emitted by the gate built to stop false passes. The second subprocess
     is now explicitly skipped on an empty resolving set, and that case is a named success
     criterion rather than an implementation detail.
  2. **`BASE` discovery was unspecified.** Now an explicit `--base <sha>` from the orchestrator,
     never inferred — an inferred base is what broke fanout teardown earlier in this repo. Absence
     of `--base` is a refusal with its own token, never `PASS`, because a comparison that did not
     run must not read as "no undeclared removals".
  3. (should-fix) **`renamed` had no successor linkage.** The tombstone now carries an explicit
     `successor_pin`. Renaming is deliberately not modelled as editing the surviving record's `pin`
     in place: in a `BASE..HEAD` diff that is indistinguishable from repointing a pin at a weaker
     test.
- v1.3: Plan audit cycle 3 — 3 must-fix, 2 should-fix. All five premises checked against the source
  before applying; three were base-invariant violations in this plan, not in the spec.
  1. **Connection enforcement was specified in one direction only.** `invariants.base.md:107`
     requires the second mutation — force the connection to fire **unconditionally** and confirm a
     fall-through test fails. Verified in the source. The removal direction alone certifies that
     the wire *can be absent*, not that it is conditional, so a registration hook firing on every
     task (including non-`wiring` ones) would have passed while silently polluting the registry.
  2. **Missing `--base` was going to invent a verdict token.** Corrected to `exit 2`: a missing
     required input is a cannot-judge, and the grammar already has that slot (`UNREADABLE`,
     `UNSHAPED`). A bespoke token exiting 0 would dilute exactly the discipline it was imitating.
     Also pinned the read as `git show <base>:.h-mad/wires.jsonl` rather than a working-tree copy,
     which would compare HEAD against itself whenever the file is dirty.
  3. **The registry writer is a path resolver, which is the J18 hazard.** Mutation-testing
     `_pin_file`'s override branch once redirected the entire suite's writes onto the live pin file
     while reporting 642 passed. This feature adds a second such resolver, so the protection is
     mandatory and extends `conftest.py`'s existing `_protect_live_pin_file` guard rather than
     adding a parallel one. `tmp_path` redirection is necessary but not sufficient: the failure is
     a mutation that disables the redirection branch itself.
  4. (should-fix) Deliverable now lists every AC-1.1 field explicitly instead of gesturing at
     "schema".
  5. (should-fix) BASE extraction mechanism named exactly, including the "registry absent at BASE"
     case, which is *new entries*, not an error.
- v1.4: Plan audit cycle 4 — 0 must-fix, 1 should-fix. Premise verified at
  `invariants.base.md:61` ("Orchestrator phase transitions and halts MUST emit `[H-MAD]` log
  markers … Silent state transitions are a violation"). The plan added a 5f step that can halt the
  run but never said it must announce itself, so a `WIREREG: FAIL` would have stopped a run
  undiagnosably from logs. The 5f deliverable now names three halt reasons —
  `step5f:wire_regression:<id>`, `step5f:wire_pin_missing:<id>`, `step5f:registry_untracked` —
  each with an `[H-MAD]` marker.
