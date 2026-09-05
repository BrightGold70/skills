AUDIT-doc-block-exec-plan-v86-BEGIN
## Summary
| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

The plan covers all six functional requirements without an unacknowledged narrowing. Four provenance records are internally false or ambiguous, making their cited audit baseline unreproducible.  
Evidence: 4 files opened, 18 grep/read checks run.

## Must-fix
- The ledger history misattributes `72/83` to v1.101 — the v1.101 landed plan records `72/84`; the plan’s own series assigns `72/83` to earlier points. This makes the recurrence attribution false.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**codex \`72\` against teammate \`85\` at \`00b961f\`. v1.101's published pair was \`72\`/\`83\` and the`
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``700c599` **72/83** · `8c6539a` **72/84** · `b3be433` **72/84** · `00b961f` **72/85**.`
- The path premise used for v1.102’s stamp closure is false: `dfae038` also changes `docs/learnings.md` and `docs/skill-candidates.md`, not handoffs alone. The cited directory-collapse evidence hides this distinction.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `two, \`df04e8e\` and \`dfae038\`, touch \`docs/handoffs/\` alone.`
- The v1.102 `ten of the eleven` sweep records an impossible result — its whole-file command currently returns 3 and its body-scoped form returns 0, not the claimed 1. This violates the plan’s own command-backed behavioural-premise rule.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `tr '\n' ' ' < <doc> | grep -oiF 'ten of the eleven' | wc -l returns 1, the surviving hit being the bracketed Version History entry.`
- The plan assigns two different measurement commits to v1.102’s wider-corpus ledger — it defines `dfae038` as the v1.102 measurement commit, then calls `00b961f` the commit this revision is measured against. The required re-run target is therefore ambiguous.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `v1.102 is measured at \`dfae038\`.`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `The wider-corpus readings this revision takes are the codex-leg ledger`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the commit v1.101 landed at and the one this revision is measured against`

## Should-fix
- The present-tense “two still-owed spec commands” is stale against the current spec: `2486` is explicitly retired and AC-4.2 includes `BAD_ARGS` in the exit-0 set. Stamp the historical claim to the intended revision or update it.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `the two still-owed spec commands`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `Both are \`+61\` on the retired \`2748\`/\`2486\` pair`
  quote: docs/01-plan/features/doc-block-exec.spec.md › ``BAD_ARGS`, `BAD_SUBST`, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO` and `TIMEOUT` each`

## Nit
None
AUDIT-doc-block-exec-plan-v86-END