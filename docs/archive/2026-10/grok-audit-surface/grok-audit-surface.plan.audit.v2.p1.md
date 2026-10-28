## Summary
The plan covers FR-1 through FR-10 at the required strategy level, including the live/CI boundary and every outcome branch. Two base-invariant gaps remain: the prompt-divergence predicate can fork between the wrapper and probe, and the plan does not require discrimination evidence for almost all new tests.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |
| FR-7 | implemented-as-written |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | implemented-as-written |

Evidence: 10 files opened, 4 greps run.

## Must-fix
- The prompt-diff predicate is specified for both the shell wrapper and the probe, but the plan leaves the probe's mechanism open and does not require a shared authority or byte-equivalence/differential test. That breaches the single-source contract: a later change to the wrapper's report-path mask can make calibration accept prompts which production rejects (or conversely). Commit to consuming the wrapper's recorded verdict, centralising the rule in one callable helper, or a corpus test that proves the two implementations equivalent.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `The probe's AC-3.2 check applies the same rule.`
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `whether the probe re-runs the diff or reads the wrapper's \`prompt_divergence\` halt`
- The test plan records a RED run only for the AC-6.2a documentation test, while it adds scorer, gate, round-cap, and three-surface tests without requiring each test/guard to be observed failing against the unfixed or deliberately weakened behavior. A green fixture suite would therefore not establish that its assertions discriminate; require a verified targeted mutation/revert and RED result for every new test or mutation guard, including the existing-behaviour pins.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `AC-6.2a (RED run of the new doc test against the uncorrected SKILL.md, then the correction)`
  quote: docs/01-plan/features/grok-audit-surface.plan.md › `FR-5 probe and every AC-5.5 fixture; AC-8.1/8.2 tests; AC-9.1–9.4 tests; FR-10 tests`

## Should-fix
None

## Nit
None
