# Spec: gate-blindness-hardening

## Executive Summary

The Phase-7 gate stops treating an unrecorded architectural review as success, 6a-prime accepts
a headless `exec agy` review so the ordinary session can satisfy it, and the shared test stubs
gain an opt-in hostile-payload corpus so fixtures can carry the characters agents actually emit.

## Goal

A feature cannot close without an architectural review having actually happened, and the test
fixtures can express the payloads that hid a card-corrupting defect through every other gate.

## Functional Requirements

### FR-1: An unrecorded architectural review blocks Phase 7

- **Description**: `h_mad_phase7_preconditions.py` currently branches on `WITH_FIXES`/`NO`
  (blocker) and `SKIPPED_NO_PANE` (warning) with no `else`, so a record that never wrote
  `archreview` returns `PHASE7: READY blockers=0`. An absent review must be a blocker with its
  own code, distinct from a review that ran and failed.
- **Acceptance Criteria**:
  - AC-1.1: A record with `last_completed_phase = 6`, a valid analysis at threshold, no open
    halt, and **no `archreview` key** returns `PHASE7: BLOCKED` with a blocker whose code is
    `archreview_not_run`.
  - AC-1.2: The same record with `archreview: null` also returns `PHASE7: BLOCKED blockers>=1`.
    Defensive: the schema enum excludes `null`, so `h_mad_state_write.py` cannot produce this —
    it can only arrive from a hand-edited or legacy store, which is exactly the case the gate
    must not read as success. The AC drives the gate directly, not through the writer.
  - AC-1.3: The blocker detail names the field and how to satisfy it, not just that it failed —
    a returncode-only assertion must not be able to pass this AC.
  - AC-1.4: `archreview: "READY_TO_MERGE"` continues to return `PHASE7: READY blockers=0`;
    all 9 existing closed records carry that value and none may newly block.
  - AC-1.5: The token/exit discipline is unchanged — exit 0 on any verdict, 2 only on
    operational error.

### FR-2: A skipped review blocks rather than warns

- **Description**: `SKIPPED_NO_PANE` is currently a warning, so a skip closes the feature. Once
  FR-4 makes a headless review available to any session with the `agy` CLI, a genuine skip is
  rare enough to stop the run.
- **Acceptance Criteria**:
  - AC-2.1: `archreview: "SKIPPED_NO_PANE"` returns `PHASE7: BLOCKED` with code
    `archreview_skipped`.
  - AC-2.2: The blocker detail states that a headless `exec agy` review satisfies the gate, so
    the operator is pointed at the remedy rather than at the override.
  - AC-2.3: No warning path silently accepts any `SKIPPED_*` value other than the FR-3 override.

### FR-3: A genuine skip requires an explicit, recorded operator override

- **Description**: When neither a reviewer pane nor the `agy` CLI exists, the run must still be
  closable — but only by a deliberate, auditable act, not by omission.
- **Acceptance Criteria**:
  - AC-3.1: `archreview: "SKIPPED_OPERATOR_OVERRIDE"` returns `PHASE7: READY` with a
    **warning** whose code is `archreview_overridden`.
  - AC-3.2: The value is added to the state schema's `archreview` enum, so
    `h_mad_state_write.py` accepts it and rejects a misspelling (an invented value must not
    reach disk).
  - AC-3.3: The warning text requires the override to be carried into the Phase-7 report, so a
    reader cannot believe a review happened.
  - AC-3.4: The override is the ONLY value that converts a missing review into a ready state.

### FR-4: 6a-prime is satisfied by a headless `exec agy` review

- **Description**: `SKILL.md` §6a-prime mandates a pane preflight (`hmad-dispatch alive agy`)
  and halts `step6a-prime:no_reviewer_pane` otherwise. `exec` is the documented default for
  every other audit dispatch and is pane-independent, so the protocol's precondition fails in
  the ordinary case and steers the run into FR-1's hole. The preflight becomes
  `command -v agy`, matching §"Reviewing a skill with agy".
- **Acceptance Criteria**:
  - AC-4.1: A doc test asserts §6a-prime states that `exec agy` satisfies the gate and does not
    require a resolved pane.
  - AC-4.2: A doc test asserts §6a-prime no longer instructs recording `SKIPPED_NO_PANE` as the
    ordinary response to an unresolved pane.
  - AC-4.3: A doc test asserts §6a-prime instructs writing the extracted `ASSESSMENT:` value
    into `orchestrator_state[<feature>].archreview` immediately after extraction — so the field
    is recorded automatically rather than remembered. Enforcing an absence (FR-1) and
    preventing it are different guarantees; this AC is the second.
  - AC-4.4: A doc test asserts the halt route for a genuinely unavailable reviewer names
    `SKIPPED_OPERATOR_OVERRIDE`, not `SKIPPED_NO_PANE`.

### FR-5: Stubs can emit hostile payloads, opt-in

- **Description**: Shared stubs return tidy ASCII (`"comment":"c"`), which is why a
  glob-unsafe span replacement survived 1063 tests, a clean 5/5 mutation sweep, five
  wire-scoped reverts and a clean architectural review. Add a hostile corpus, consulted only
  when explicitly requested — the existing `HMAD_STUB_*` precedent.
- **Acceptance Criteria**:
  - AC-5.1: With the hostile knob **unset**, every one of the 1143 currently-passing tests
    across both coupled suites passes unchanged.
  - AC-5.2: The knob accepts a named corpus so a test can request the hazard it cares about:
    at minimum `markdown` (`[x](y)`, `**bold**`, `*`, `[`), `newlines`, `markers` (the literal
    `h-mad: ` lead-in and `⟦/h-mad⟧` terminator), and `all`.
  - AC-5.3: The `markdown` corpus contains at least one `[` and one `*`, asserted directly —
    these are the glob metacharacters that caused the live defect, so their presence is the
    point of the corpus and must not be assertable only by proxy.
  - AC-5.4: The `markers` corpus round-trips through the stub as **data**: requesting it does
    not corrupt the stub's own JSON envelope.
  - AC-5.5: An unrecognised corpus name is a loud failure, not a silent fallback to tidy input —
    a typo must not quietly restore the blind fixture.

### FR-6: The RED-dispatch template mandates hostile payloads

- **Description**: A convention that lives only in one test file decays to whatever the next
  author types. `references/codex-implementer-prompt.md` is what every 5d dispatch reads.
- **Acceptance Criteria**:
  - AC-6.1: A doc test asserts the implementer template instructs the agent to drive hostile
    payloads for any value that originates from an agent or a human, naming the corpus knob.
  - AC-6.2: The template states *why* — tidy ASCII fixtures let a real defect through every
    gate — so the instruction is not a rule without a reason a future reader can weigh.

## Non-Functional Requirements

- **Performance**: N/A. Gate changes are pure predicate logic; the corpus is static strings.
- **Security**: N/A — no new dependency, no network, no credentials. The `markers` corpus is
  deliberately adversarial input to our own parser, which is the intent.
- **Compatibility**: All 9 existing closed records carry `archreview: READY_TO_MERGE` (verified),
  so FR-1's blocker trips none of them. The hostile knob is unset by default. `~/.claude/skills/h-mad`
  is a symlink into this repo, so both coupled suites must pass before merge.

## Out-of-Scope

- Making hostile payloads the **default** — the strongest guarantee, but it would break an
  unknown number of the 1143 existing tests and force unrelated triage inside a feature about
  gate correctness.
- A repo-wide fixture sweep beyond the stubs the exec path shares.
- Requiring a live e2e before Phase-7 closure. A live run is what found the glob defect, but
  this would redefine "done" for every feature and most have no meaningful live surface.
  Follow-up, not folded in.
- Repairing the stale codex/agy pins, backfilling `docs/skill-monitoring.md` past J18, and
  documenting the mutation-harness `root` key. All real, all separate.
- Changing the audit-gate (`h_mad_audit_gate.py`) or any Phase 3/4/5b behaviour.

## Assumptions

- `h_mad_phase7_preconditions.py` remains the single Phase-7 gate; no other code path closes a
  feature.
- The `archreview` field is already in the strict state schema (existing records validate), so
  FR-3 extends an enum rather than adding a field.
- Doc tests over `SKILL.md` and the implementer template are acceptable enforcement for
  protocol text, as already used by `test_skill_docs_describe_log_append_...`.

## Version History

- v1.0: Initial specification draft.
