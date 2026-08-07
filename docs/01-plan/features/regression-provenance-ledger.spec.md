# Spec: regression-provenance-ledger

## Executive Summary

Connections proven at creation time become durable registry entries that every subsequent `/h-mad`
run re-verifies, so breaking an older feature's wire fails the current feature's gate instead of
shipping green.

## Goal

A feature can no longer silently remove functionality another feature established, because the
guarantee outlives the run that created it.

## Resolution of the brainstorm's open question 1

The operator approved without settling whether the pain is wires specifically or "any shipped
guarantee that silently stops holding". This spec resolves it deliberately rather than leaving it
to drift: **the record shape is generic (`kind` field, extensible), the implemented scope is
`kind: "wire"` only.** A later feature can add `kind: "counter"` or `kind: "invariant"` without
reshaping the registry or migrating entries. Widening the *scope* now would make the feature
unfinishable; widening the *schema* now costs one field.

## Functional Requirements

### FR-1: A durable wire registry

- **Description**: A wire proven during Phase 5 is written to a per-repo registry that survives the
  feature that created it. Records are append-oriented JSONL, one wire per line, carrying enough to
  re-run the pin and to name the owner when it breaks.
- **Acceptance Criteria**:
  - AC-1.1: A registry record validates against a schema requiring at minimum `kind`, `id`,
    `caller`, `callee`, `pin` (a runnable test node id), `owning_feature`, and `registered_ts`.
  - AC-1.2: `kind` is a validated enum whose only accepted value in this feature is `"wire"`; an
    unrecognised `kind` is rejected at write time, not silently stored.
  - AC-1.3: Writing a record with a duplicate `id` updates that record rather than appending a
    second one, and the registry never contains two records with the same `id`.
  - AC-1.4: A malformed line in the registry is a **loud** failure naming the line number, never a
    skipped entry — a skipped entry is an unguarded wire that reports as guarded.

### FR-2: Standing re-verification of every registered wire

- **Description**: Each `/h-mad` run re-runs **every** registry pin, not only the wires its own
  tasks touched. This is the requirement that converts "proven once" into "still true".
- **Acceptance Criteria**:
  - AC-2.1: The gate runs all `N` registry pins and reports `WIREREG: PASS|FAIL registered=N
    verified=K broken=J missing=M unverified_renames=R`.
  - AC-2.2: A pin that **runs and fails** is reported as `broken` and produces `FAIL`, and the
    output names the `owning_feature` of each broken wire — the operator must learn *whose*
    guarantee they broke, not merely that something is red.
  - AC-2.3: A pin whose **node id no longer resolves** (test renamed, moved, or deleted) is reported
    as `missing` and is distinct from `broken` in both the counts and the exit path. The two have
    opposite remedies: `broken` means fix the code, `missing` means the pin itself was removed and
    FR-4 applies.
  - AC-2.4: `missing > 0` produces `FAIL` unless every missing pin is covered by an FR-4
    declaration. Treating a vanished pin as "nothing to run" is the exact silent no-op this feature
    exists to prevent.
  - AC-2.5: Token/exit discipline matches every other h-mad gate: exit 0 on any verdict, exit 2 only
    on an operational error such as an unreadable registry.

### FR-3: Registry provenance must be distinguishable from registry absence

- **Description**: The registry lives at `.h-mad/wires.jsonl` by default. **`.h-mad/` is gitignored
  in the `skills` repo and is not in HemaSuite** (verified), so the identical gate would persist a
  registry in one repo and silently discard it in the other. An empty registry, an absent registry
  and an untracked registry must produce three different signals.
- **Acceptance Criteria**:
  - AC-3.1: An **absent** registry reports `WIREREG: PASS registered=0` and is an explicit no-op, so
    a repo that has not seeded one is not blocked.
  - AC-3.2: A registry file that exists but is **untracked or git-ignored** reports
    `WIREREG: UNTRACKED` and does **not** report `PASS` — the entries would not survive a clone, so
    reporting coverage would be a lie.
  - AC-3.3: The `UNTRACKED` message names the concrete remedy for the repo it is running in (a
    `!.h-mad/wires.jsonl` negation, or a tracked path override), not a generic instruction.
  - AC-3.4: `registered=N` is reported on every verdict, including `PASS`, so coverage is always
    visible and never implied. A green gate over an empty registry must be legible as such.

### FR-4: Removing a wire requires a declared provenance entry

- **Description**: Wires legitimately die — a feature supersedes a connection or replaces it. The
  removal must be declared, not performed by deleting a line. This is the deletion-ledger idea,
  scoped to where it belongs.
- **Acceptance Criteria**:
  - AC-4.1: A registry entry removed between `BASE` and `HEAD` with no matching declaration produces
    `FAIL`, naming the removed `id` and its `owning_feature`.
  - AC-4.2: A declaration must carry the removed `id`, a provenance classification from a validated
    enum (`superseded` | `pinned-a-defect` | `renamed`), **the feature that removed it** for every
    provenance, and additionally for `superseded` the feature that supersedes it. A free-text-only
    declaration is rejected. *Who removed it* and *what replaced it* are different questions: the
    first is always answerable and is what makes a tombstone attributable at all, while only
    `superseded` has a successor feature to name.
  - AC-4.3: `renamed` is mechanically verified — the new pin must resolve and pass. A rename that
    cannot be verified is treated as `superseded` and requires the naming.
  - AC-4.4: The declaration is discoverable from the removal alone: given a removed `id`, the gate
    can point at the declaration that authorised it.

### FR-5: Challenge an undeclared wiring task at 5f — warning first

- **Description**: `wiring` shape is currently self-declared and 4 of 172 HemaSuite impl-plans use
  it. The gate must challenge a task whose production diff introduces a call across a module
  boundary while declaring `new-behaviour` or `refactor`. **Warning-only in this feature**, because
  a false-positive rate high enough to be disabled is worse than no challenge at all.
- **Acceptance Criteria**:
  - AC-5.1: A task whose diff adds a call crossing a declared module boundary and does not declare
    `wiring` emits a named warning identifying the task and the crossing.
  - AC-5.2: The warning never changes the gate's verdict in this feature — `WIREPIN` and `WIREREG`
    verdicts are unaffected by AC-5.1 firing.
  - AC-5.3: The count of challenges raised and the count acknowledged are both reported, so the
    false-positive rate is **measured** before any later feature promotes this to a hard failure.
  - AC-5.4: What counts as a "module boundary" is read from configuration, not hardcoded, so a
    project can express its own topology.

### FR-6: Registration happens on the existing wiring path, not as a parallel step

- **Description**: A `wiring` task that passes the existing 5b wire-pin gate is registered
  automatically. Registration that depends on an orchestrator remembering a separate step will be
  forgotten, which is the same class of omission the Phase-7 `archreview` hole was.
- **Acceptance Criteria**:
  - AC-6.1: A `wiring` task with a filled `WIRE`/`WIRE-PIN` that passes the 5b gate produces a
    registry entry without a separate operator action.
  - AC-6.2: The registration is verified by reading the entry back and comparing it to what was
    written — not by the writer's exit code, and not by schema validation alone.
  - AC-6.3: A doc test asserts `SKILL.md` states registration is automatic on the 5b path and names
    where the registry lives.

## Non-Functional Requirements

- **Performance**: Re-verification costs **exactly two subprocesses regardless of registry size** —
  one whole-suite `--collect-only` to partition pins into resolving/missing, then one run of the
  resolving set. Measured: collection is 1086 tests in 0.23 s.

  **This supersedes v1.0's "single test selection" wording, which was falsified by probe.** Running
  all pins as one selection is not merely slower, it is wrong: a single unresolvable node id makes
  pytest abort the entire selection (`rc=4`, `no tests ran`) so **no** wire is verified while **no**
  test fails — the silent no-op this feature exists to remove. `--continue-on-collection-errors`
  does not rescue it. Resolving before running is therefore a correctness requirement, not an
  optimisation.
- **Security**: N/A — no network, no credentials, no new dependency. Stdlib Python plus git.
- **Compatibility**: An absent registry is a no-op (AC-3.1), so every existing repo and in-flight
  feature keeps working unchanged. The registry is additive; no existing gate's verdict grammar
  changes. `~/.claude/skills/h-mad` is a symlink into this repo, so both coupled suites must pass.

## Out-of-Scope

- **Auto-discovering wires by call-graph extraction.** The only mechanism that would retro-cover the
  168 undeclared impl-plans without human input, and deferred deliberately: dynamic dispatch,
  config-driven binding and framework hooks make the graph noisy, and a noisy gate gets disabled.
- **Chokepoint counter invariants** (`bound > 0`, `sections resolved == total`). All three known
  losses were caught this way, but only in a live e2e, which most features do not run. The `kind`
  field exists so this can be added without reshaping the registry.
- **Promoting FR-5 to a hard failure.** Requires the measured false-positive rate FR-5 produces.
- **Backfilling the existing 168 undeclared plans.** Separate effort; this feature provides the
  registry they would be backfilled into.
- **Any change to the Phase 3/4/5b audit gate, the mutation harness, or the Phase-7 gate.**

## Assumptions

- Pin identity is a pytest node id, and node ids are stable enough to serve as the re-run handle;
  AC-2.3 exists precisely because they sometimes are not.
- `BASE` for FR-4's removal comparison is the 5c baseline commit the impl-plan already records.
- The existing 5b wire-pin gate remains the single place a wiring task's pin is validated, so FR-6
  extends it rather than duplicating its parsing.
- A repo that seeds no registry genuinely wants no standing verification yet — silence there is
  correct, and AC-3.4 keeps that state visible rather than mistakable for coverage.

## Version History
- v1.0: Initial specification draft. Resolves brainstorm open question 1 (generic record shape,
  wire-only scope) and folds the `.h-mad/` gitignore asymmetry between `skills` and HemaSuite into
  FR-3 rather than leaving it as a deployment footnote.
- v1.1: Back-propagated from Phase 3 probe A3. The performance NFR's "single test selection"
  wording was falsified: one unresolvable node id aborts the whole selection (`rc=4`,
  `no tests ran`), so a single selection over all pins verifies **zero** wires while producing
  **zero** failures. Restated as two subprocesses (resolve, then run), and reclassified from an
  optimisation to a correctness requirement — it is what keeps AC-2.3's `missing` distinguishable
  from `broken`.
- v1.2: Back-propagated from Phase 4 design audit cycle 2. FR-5's title said the challenge runs
  **at 5b**; it cannot. 5b audits the impl-plan (`SKILL.md:271`) and production code is not written
  until 5e, so at 5b HEAD equals BASE and an AST comparison sees zero changes — a guard incapable
  of firing that would nonetheless report `challenges=0` as though it had looked. Retitled to
  **5f**, where the production diff exists and the verifier's `--base` is already in hand. No AC
  text changed: the ACs were always phrased against "a task whose diff adds a call", which is a
  5f-time fact. The consequence is that the challenge is retrospective, which is the correct
  strength for a warning-only mechanism.
- v1.3: Back-propagated from Phase 4 design audit cycle 6, which flagged two places where the
  design had grown **wider** than the spec. Both were resolved in the spec's favour of the design,
  because the design's version is the one the mechanism needs:
  - **AC-2.1** now carries `unverified_renames=R` in the token. Cycle 5 established that a
    `renamed` tombstone whose `successor_pin` does not exist must FAIL — otherwise the wire leaves
    `missing` (tombstoned) and never enters `broken` (never run), so a declared removal verifies
    nothing. A count that drives a FAIL has to appear in the grammar.
  - **AC-4.2** now requires `removed_by_feature` for **every** provenance, not only `superseded`.
    *Who removed it* and *what replaced it* are different questions; the first is always answerable
    and is what makes a tombstone attributable, and without it a `pinned-a-defect` or `renamed`
    tombstone is an anonymous edit.
