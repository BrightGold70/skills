## Summary
The design covers most of the spec, but several acceptance criteria are narrowed and the containment workflow has unresolved contract and verification gaps. The targeted smoke checks reproduced both non-grok-shape PASS cases: 2 tests passed, 42 tests deselected.

| Acceptance criteria | Classification |
|---|---|
| AC-1.1 | restated |
| AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7 | implemented-as-written |
| AC-1.8 | restated |
| AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6 | implemented-as-written |
| AC-2.7 | restated |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3 | implemented-as-written |
| AC-5.4 | restated |
| AC-5.5 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.2a, AC-6.3, AC-6.4, AC-6.5 | implemented-as-written |
| AC-6.6 | restated |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4 | implemented-as-written |
| AC-8.1, AC-8.2, AC-8.3 | implemented-as-written |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | implemented-as-written |
| AC-10.1, AC-10.2, AC-10.3 | implemented-as-written |
| AC-11.1, AC-11.2, AC-11.3, AC-11.4, AC-11.5 | implemented-as-written |
| AC-11.6 | restated |
| AC-11.7 | implemented-as-written |

Evidence: 24 files opened, 0 greps run.
The 63 AC identifiers were enumerated from the spec. Direct reads included the design, spec, plan, wrapper, probe, gate, tests and a kept agy log; shell-policy restrictions blocked grep, git, graft and history commands. No live agent was dispatched.

## Must-fix

- **AC-1.1: the design permits PASS without the required grok Effort shape.** The spec requires `format=grok`; D11 expressly permits `parsed` and `unparseable` items to pass and pins that behavior. Running `/opt/anaconda3/bin/python3.11 -m pytest -p no:cacheprovider h-mad/tests/test_grok_audit_surface_smoke.py -q -k 'parsed_item_with_all_three_types or deep_grok_types'` passed both tests, whose assertions verify those shapes before expecting the default `SMOKE: PASS`. This is a narrower acceptance predicate, not merely an observational residual. Reconcile the predicate and its closed failure vocabulary in the spec, then align the design and tests; do not silently replace the token authority with a second log classifier.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `and the cycle's `Effort:` block reports `format=grok` (shape `grok`), not `grok-truncated`.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `Both are pinned as residuals by fixtures (Test Plan), so a change that closes or widens either shows.`

- **AC-1.8: D15 makes the smoke-failure publication branch unsatisfiable.** The spec publishes a smoke-only measurement without starting S2. D8 correctly runs the second quarantine only after smoke PASS, but D15 requires both quarantine lines on every published outcome; it also unconditionally requests the score's containment lines. A legitimate smoke failure cannot supply those records. Make publication requirements conditional on stages actually reached, explicitly marking later stages not run, and pin the smoke-failure document shape.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `S2 does not start. No calibration runs, no findings are labelled, and no `SEEDSCORE:` verdict exists or is published.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `every item on every outcome that publishes the doc:`

- **AC-2.7: the add-only rule is applied before the calibration sha is fixed and leaves no namespace for later readings.** The spec freezes files present at the calibration sha and permits later calibrations as new readings. D9 instead rejects every replacement from the first branch commit, while also promising S0b span corrections through subsequent commits; changing a span necessarily changes the ledger and a seeded copy. After the first new reading, the fixed `resmoke/`, `s2/`, findings and labels paths likewise cannot accept another run. Define pre-freeze authoring behavior and immutable per-reading storage/selection, or obtain an explicit spec restriction; retain byte identity for frozen readings.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `every file present at the calibration sha (the ledger and every seeded copy) is byte-identical at the smoke commit and at the score sha`
  quote: docs/02-design/features/grok-audit-surface.design.md › `**v1.6: every branch commit is add-only.**`

- **AC-5.4: D12 adds a third trigger to a closed two-trigger reason.** With a valid, readable, clean grok log but malformed `s2/run.txt`, D12 emits `out_of_root:<doc>.v<N>`. The spec limits that reason to a nonzero scan count or an absent/unreadable/no-event log. Rejecting missing scan provenance is sensible, but this changes the refusal contract and the implementer's fixture expectations. Add the run-record trigger to the spec explicitly, or select a spec-authorized refusal without weakening fail-closed behavior.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `The triggers are exactly two: (1) the scan's out-of-root count for the grok pass is non-zero; (2) the grok pass's log is absent or unreadable, or yields no parseable event, so the scan cannot be run.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `a `s2/run.txt` that `parse_run_line` rejects makes every grok pass unscannable`

- **AC-6.6: the halt connection is neither implemented in the cycle template nor given its required fixture.** The template tees the scan and ends without consuming its token or writing HALT; prose assigns that step to the operator. A start-only existence check also permits a lane to pass the check, build roots, and dispatch after another lane records a failure. D8's additional-cycle allowance is weaker than the spec's prohibition, and D19's test list exercises the scanner rather than scan-result-to-dispatch prevention. Define the token consumer and coordinated launch boundary, emit the halt marker, and add the required stub-driven fixture proving no later cycle launches, including OUT_OF_ROOT, UNREADABLE and missing-token cases.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `No further cycle of that run is dispatched (cycles already in flight finish and are recorded)`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `A halt fixture asserts that no further cycle is dispatched.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `so a halt stops at most one more cycle per lane, each of which still ends in a scan.`

- **AC-11.6: the quarantine's newly required internal-refusal fixtures are missing.** Spec v1.13 requires separate injected-exception and usage-error fixtures. D20 names tests for the five ordinary reasons, verified outcomes and preservation, but neither internal case; the general mutation rule cannot identify a fixture that the design never specifies. Add both fixtures with exact final-token, exit and no-move assertions, and discriminate the corresponding exception/usage connections.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `all six, `internal` among them, planted by an injected exception and, separately, by a usage error`
  quote: docs/02-design/features/grok-audit-surface.design.md › `a usage error or an escaping exception prints `QUARANTINE: REFUSED reason=internal:<E>``

- **The new external-runtime verb has no live verification gate before shipping.** D18 specifies stub-only tests, and D8 first exercises the new canary after FR-11 has shipped. The incident's direct sandbox observations do not exercise the new plant → exec → judge integration, its staged prompt, or its denial attribution. This violates Wrapper–runtime reconciliation. Add a pre-ship, unseeded live round trip through the new verb with its command and observed artifacts recorded; this can run before any seeded dispatch and does not conflict with FR-11 gating.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `FR-11 shipped and its tests green (spec FR-11 gating)`
  quote: docs/02-design/features/grok-audit-surface.design.md › `a stub `grok` on `PATH` that plants one outcome each`

- **The unconditional production entry change is not propagated into SKILL.md's entry contract.** D16 changes every `exec grok` invocation, adds a required override for weaker profiles, and refuses additional working-directory cases. D14's specified SKILL.md edits cover audit wording and routing, while the new sandbox contract is assigned only to the substrate reference. The current entry bullet describes staging, timeout and evidence without these constraints. Update that bullet unconditionally with the strict default, override and refusal behavior, and pin it; otherwise Skill manifest integrity is violated when FR-11 ships independently of S3.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `Every `exec grok`, a Phase-5 implementer included, now runs `strict``
  quote: h-mad/SKILL.md › `Stage with `h_mad_assemble_tdd.py --agent grok`;`

## Should-fix

- **D20's spec reconciliation note is stale.** The current spec already includes the sixth quarantine reason, so describing it as still owed obscures which contract is authoritative. Refresh that note and the current-revision references without changing the six-form implementation.
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › `owed to the spec, which lists five`
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `It is the sixth form, a last resort that none of the five names`

## Nit
None
