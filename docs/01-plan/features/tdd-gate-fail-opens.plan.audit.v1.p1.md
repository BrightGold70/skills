AUDIT-tdd-gate-fail-opens-plan-v1-BEGIN
## Summary
The plan covers FR-2 through FR-5 and FR-7 as written, but restates FR-1 and FR-6 in ways that weaken required checks. The probe contract and evidence trail also have blocking gaps; the published mutation floor is one low.

| FR | Classification |
|---|---|
| FR-1 | restated |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | restated |
| FR-7 | implemented-as-written |

Evidence: 9 repository files opened, 9 greps run; current gate, judge, test-helper, plan, spec, and invariant spans inspected. 🌱 graft saved ~75,107 tokens this turn (1 call).

## Must-fix
- FR-1 is restated for Claude outside-root exemptions: the plan says every exemption reads canonical values, while spec FR-1 step 7 retains the narrower raw-spelling match as well. Preserve the `# M:H20` dual check and pin an outside-root symlink control; otherwise an outside-root path whose canonical form enters `tests/` can soften without being among the three approved ALLOW changes.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `every exemption, `IN_ROOT` and the suffix test read the canonical values`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `which also requires the raw spelling to match`
- FR-6 is restated as decision equality plus a derived deny count. The spec additionally requires equal denial kinds and a published expected decision and kind for each cell; add those assertions explicitly to T6 so a cross-gate kind disagreement fails.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `with an expectation table whose deny count the test derives`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `on every cell where both deny, the kinds are equal`
- The committed probe is specified to depend on a real `codex` executable being on PATH, even though the base invariant forbids scripts or tests invoking an agent CLI for their own work. Separate the live Codex grammar measurement from the committed probe, or route it through an allowed dispatch verb, and reconcile the spec's T0 promise.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `A cell that needs `codex` prints an explicit`
  quote: h-mad/invariants.base.md › `never imported, required, or invoked by a script or test for its own work`
- Load-bearing behavioural readings lack runnable commands: the F_GETPATH, permission and gate-cell results are attributed to deleted scratch scripts, and the Claude Edit result names no invocation. The base invariant requires the exact command beside each observed output; commit the reproducer or include executable commands before using these readings to freeze the design.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `scratch probe, run and deleted; readings at`
  quote: h-mad/invariants.base.md › `MUST carry the exact command that produced it, inline and`
- The plan's success gate points the spec's measured-premises table at T9's fixed reading, while the spec explicitly says to replace that table with T0's unfixed reading. Keep the unfixed premise pointer and cite T9 separately; otherwise the historical measurements lose their source.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `replaced by a pointer to that reading (spec author).`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `commits its unfixed reading, and is then replaced by a pointer to that one reading.`

## Should-fix
- T8's stated floor of 19 mutations is one low: its 16 parenthetical guard sites plus three split pairs yield 19, and “the fold in each gate” adds a second gate-specific mutant, yielding a minimum of 20. Correct the published floor and retain the per-guard census as the acceptance check.
  class: measurement
  quote: docs/01-plan/features/tdd-gate-fail-opens.plan.md › `19 is a **floor** on mutations, not their count`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `the fold in each gate (AC-2.2)`

## Nit
None
AUDIT-tdd-gate-fail-opens-plan-v1-END
