# Plan: gate-blindness-hardening

## Executive Summary

Close the Phase-7 hole that lets an unrecorded architectural review pass silently, make the
headless review the ordinary way to satisfy 6a-prime so blocking a skip is safe, and give the
shared stubs an opt-in hostile-payload corpus so fixtures can express what agents actually emit.

## Overview

Two gates cannot see defects they are positioned to catch, and one feature demonstrated both.
A hardcoded heartbeat was caught only by 6a-prime — the pass the protocol tells you to skip —
and a comment-corrupting quoting bug was caught only by a live run, because every fixture feeds
tidy ASCII. Neither gate is missing; both are reachable-around.

## Scope

`h-mad/scripts/h_mad_phase7_preconditions.py`, `h-mad/scripts/h_mad_state_schema.json`,
`h-mad/SKILL.md` §6a-prime, `h-mad/references/codex-implementer-prompt.md`, and the shared
`h-mad/tests/stubs/`. User-visible behaviour: a feature can no longer close without a recorded
architectural review; 6a-prime is satisfiable by any session with the `agy` CLI; tests can
request hostile fixture payloads. No change to Phase 3/4/5b gates, the audit gate, or the
dispatch path.

## Goals

- Make an unrecorded review a blocker rather than silence — FR-1
- Make a skipped review stop the run — FR-2
- Preserve a deliberate, auditable escape for the genuinely reviewer-less case — FR-3
- Make the headless review the ordinary path, and record its verdict automatically — FR-4
- Let fixtures carry agent-shaped payloads, opt-in — FR-5
- Put the fixture convention where every RED dispatch reads it — FR-6

## Requirements

FR-1 unrecorded review blocks · FR-2 skip blocks · FR-3 explicit operator override ·
FR-4 headless 6a-prime + auto-record · FR-5 hostile stub corpus · FR-6 template mandate

## Verified assumptions (probe evidence)

**A1 — the hole is real and silent.** A record at `last_completed_phase 6`, valid analysis, no
halt, and no `archreview` key:

```
$ h_mad_phase7_preconditions.py <state> --feature probe-feat
PHASE7: READY blockers=0
```

`h_mad_phase7_preconditions.py:88-99` branches on `WITH_FIXES`/`NO` and `SKIPPED_NO_PANE` with
no `else`.

**A2 — no existing record trips the new blocker.** All 9 features at
`last_completed_phase = 7` carry `archreview: "READY_TO_MERGE"`; none is absent.

**A3 — `archreview` is already an enum**, so FR-3 extends it rather than adding a field, and a
misspelled value cannot reach disk (`h_mad_state_write.py` refuses out-of-schema values —
observed live this session on an unrelated key):

```
enum: ["READY_TO_MERGE", "WITH_FIXES", "NO", "SKIPPED_NO_PANE"]
```

**A4 — the schema already asserts what the gate fails to enforce.** Its own description says
`SKIPPED_NO_PANE` "is never equivalent to READY_TO_MERGE and must surface in the Phase 7
report." FR-2 makes the gate agree with the schema; it is not a new policy.

**A5 — six existing assertions pin the behaviour being inverted.** This is the principal risk
and is enumerated below rather than discovered during implementation:

| File | Assertion | Fate |
|---|---|---|
| `test_h_mad_phase7_preconditions.py` | `test_skipped_archreview_does_not_block` | inverted |
| `test_h_mad_phase7_preconditions.py` | `test_skipped_archreview_is_surfaced_as_a_warning` | rewritten to blocker |
| `test_h_mad_archreview_pane_halt.py` | `test_preflight_checks_the_pane_before_dispatching` | rewritten to `command -v agy` |
| `test_h_mad_archreview_pane_halt.py` | `test_names_unresolved_as_the_trigger` | rewritten |
| `test_h_mad_archreview_pane_halt.py` | `test_state_records_a_skipped_review` | retargeted to the override value |
| `test_h_mad_archreview_pane_halt.py` | `test_skipping_is_explicitly_not_a_pass` | **kept and strengthened** |

## Implementation Strategy

**Regression provenance first: these tests did not pin a defect.** They pin a prior deliberate
decision (#10 permitted proceeding without a reviewer pane), so they are retired knowingly, not
quietly. Their *intent* — a skip must never read as a pass — is the same intent this feature
serves, and it is served more strongly: today the skip is a warning that closes the feature,
after this it stops the run. `test_skipping_is_explicitly_not_a_pass` is therefore kept and
tightened rather than replaced, as the continuity marker between the two contracts.

This matters because inverting an assertion is the exact shape in which tests get weakened to
accommodate new behaviour. Every inverted test must assert the **new** contract positively, not
merely stop asserting the old one; a deletion is not a substitute.

### Landing order — all four, not two

**No blocker may land before the means of satisfying it exists.** The rule covers FR-1 as well
as FR-2; v1.0 stated it for FR-2 only, which left the sharper deadlock unguarded:

1. **FR-4** — headless review accepted **and its verdict auto-recorded**. Until this lands there
   is no ordinary way to *produce* an `archreview` value at all.
2. **FR-3** — the `SKIPPED_OPERATOR_OVERRIDE` escape exists, so a genuinely reviewer-less run
   has somewhere to go before either blocker is armed.
3. **FR-2** — a recorded skip now blocks.
4. **FR-1** — an *absent* review now blocks. Last, because it is the strictest and because it is
   the one that fires on records nobody edited.

Landing FR-1 before FR-4 is the specific deadlock: the field would become mandatory while
nothing yet writes it and no override exists. Via the symlink this repo *is* the live skill, so
the first run to hit that state is **this feature's own Phase 7** — the gate would block the
work that fixes it. FR-5/FR-6 are independent of this chain and may land any time.

**Prevent, then enforce.** FR-1 makes an absent field fail; FR-4's auto-record makes it not
happen. Enforcing an absence and preventing one are different guarantees, and the second is
what stops the blocker from becoming an obstacle a future run routes around.

**The corpus is data, not behaviour.** The stub gains strings and a selector, consulted only
when set — the established `HMAD_STUB_*` precedent that keeps 1143 tests untouched. The
`markers` corpus deliberately feeds our own span syntax back as content, which is the case the
live defect proved we never test.

**Deliberately untouched:** the audit gate, Phase 3/4/5b, the dispatch path, `_exec_*` helpers.

## Architecture Considerations

- **The gate is a pure predicate over a record plus an analysis file** — no I/O beyond reading
  them, so all of FR-1/2/3 are unit-testable without a live run.
- **Doc tests are the enforcement for protocol text.** `SKILL.md` and the implementer template
  have no runtime, so FR-4 and FR-6 are asserted by reading the files — an established pattern
  here (`test_h_mad_*_docs.py`, and the `--log` contract test shipped last feature).
- **Symlink coupling.** This repo is the live `~/.claude/skills/h-mad`; the gate being changed
  is the one that will gate *this* feature's own Phase 7. Sequence matters: the new blocker
  becomes active for this run the moment it lands.
- **Enum extension is backward-compatible** — adding a value cannot invalidate records using
  the existing four.

## Deliverables

| Deliverable | Target file(s) | Satisfies |
|---|---|---|
| `archreview` absent/null → blocker `archreview_not_run` | `h-mad/scripts/h_mad_phase7_preconditions.py` | FR-1 |
| `SKIPPED_NO_PANE` → blocker with remedy text | `h-mad/scripts/h_mad_phase7_preconditions.py` | FR-2 |
| `SKIPPED_OPERATOR_OVERRIDE` → ready + warning | `h-mad/scripts/h_mad_phase7_preconditions.py` | FR-3 |
| Enum extension | `h-mad/scripts/h_mad_state_schema.json` | FR-3 |
| 6a-prime accepts `exec agy`; records the assessment | `h-mad/SKILL.md` §6a-prime | FR-4 |
| Doc tests for the 6a-prime contract | `h-mad/tests/test_h_mad_archreview_pane_halt.py` (the existing home of the pane pins, retargeted) | FR-4 |
| Inverted/retargeted pins + new contract assertions | `h-mad/tests/test_h_mad_phase7_preconditions.py`, `h-mad/tests/test_h_mad_archreview_pane_halt.py` | FR-1–FR-4 |
| Hostile corpus + selector | `h-mad/tests/stubs/orca` (and shared helper if a second stub needs it) | FR-5 |
| Corpus tests | `h-mad/tests/test_h_mad_hostile_fixtures.py` (new) | FR-5 |
| Hostile-payload mandate + rationale | `h-mad/references/codex-implementer-prompt.md` | FR-6 |
| Doc tests for the implementer-template mandate | `h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py` (already asserts this template's RED/GREEN clauses) | FR-6 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Inverted assertions get deleted rather than re-pointed | The gate's contract silently loses coverage — the exact failure this feature exists to prevent | A5 enumerates all six up front; each must assert the new contract positively; net assertion count must not fall |
| A blocker lands before the way to satisfy it | A run cannot close and has no override — and via the symlink, **this feature's own Phase 7 is the first victim** | Strict ordering, all four: **FR-4 → FR-3 → FR-2 → FR-1** (see §"Landing order") |
| The new blocker strands **this** feature's own Phase 7 | Self-inflicted deadlock via the symlink | 6a-prime for this feature runs headless under the new contract — dogfooding it is the acceptance evidence |
| Hostile corpus breaks existing tests | Unrelated triage inside a gate feature | Opt-in knob, unset = today; assert the full 1143 with it unset |
| `markers` corpus corrupts the stub's own JSON | Fixture becomes unusable | Emit as JSON-encoded data; pin a round-trip test |
| A typo'd corpus name silently yields tidy input | Restores the blind fixture — the original defect class | Unrecognised name fails loudly (FR-5 AC-5.5) |
| Doc tests match prose loosely and pass on unrelated text | False confidence in a protocol change | Assert on the specific contract phrases; mutation-check by removing the sentence |

## Convention Prerequisites

- Branch `feature/NNN-gate-blindness-hardening` off `main` at 5c.
- Codex authors Phase 5 under the TDD gate; RED before GREEN per module.
- Every new guard mutation-verified via `h_mad_mutation_harness.py`; pass `root` explicitly
  (its default is the spec file's directory, which yields `BASELINE_NOT_GREEN` from a scratchpad).
- Both coupled suites (h-mad + handoff) green before merge.
- Inverted tests: assert the new contract, never merely drop the old assertion.

## Success Criteria

- All 25 spec ACs pass automated tests.
- The full suite passes with the hostile knob unset; count does not fall below the current 1143.
- Every new guard mutation-verified `ALL_CAUGHT`, including the doc-test guards.
- A record with no `archreview` returns `PHASE7: BLOCKED archreview_not_run`; the 9 existing
  closed records still return READY.
- **This feature's own 6a-prime runs headless and is auto-recorded**, closing Phase 7 under the
  new contract.

## Out-of-Scope (confirmed from spec)

- Hostile payloads by default; repo-wide fixture sweep.
- Mandating a live e2e before Phase-7 closure.
- Stale pin repair, `skill-monitoring` backfill past J18, mutation-harness `root` documentation.
- Any change to `h_mad_audit_gate.py` or Phase 3/4/5b.

## Next Steps

Operator approves v1.0 → Phase 3 audit cycle via `exec agy` → gate to must-fix = 0 and
should-fix = 0 → Phase 4 design.

## Version History

- v1.0: Initial plan draft.
- v1.1: Plan audit cycle 1 — 1 must-fix, 1 should-fix. The ordering rule named only FR-2, so
  FR-1 was unguarded: making an absent `archreview` a blocker before FR-4 writes one would make
  the field mandatory while nothing produces it and no override exists — and via the symlink the
  first run to hit that is this feature's own Phase 7. Replaced with an explicit four-step
  landing order (FR-4 → FR-3 → FR-2 → FR-1) in its own section. Deliverables now name the
  doc-test files enforcing FR-4 and FR-6, both of which are existing homes rather than new
  files: `test_h_mad_archreview_pane_halt.py` already holds the pane pins being retargeted, and
  `test_h_mad_tdd_dispatch_discipline_prompt.py` already asserts clauses of the implementer
  template.
