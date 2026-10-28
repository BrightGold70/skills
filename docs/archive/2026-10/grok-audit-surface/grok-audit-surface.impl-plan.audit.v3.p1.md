AUDIT-grok-audit-surface-impl-plan-v3-BEGIN
## Summary

The plan still has implementation blockers and a merge gate that can accept an unexecuted work-tree dispatch. I swept Tasks 0–30 against the paired spec/design and unchanged S0 sources; prospective canary mutants were assessed from the specified control flow, not executed.

Evidence: 15 files opened, 0 greps run. Targeted text searches used JavaScript.

## Must-fix

- Resolve Task 26 before approving implementation. Its missing-root fixture is required to produce both list_changed:unrecorded in pass (a) and cycle_token in pass (b), which cannot both happen. The plan explicitly stops RED pending a ruling, so Tasks 26–29 have no executable, fixed contract. Choose the missing-record precedence and surplus-record policy, update the paired spec/design, and freeze the fixture, row and gate totals.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``D12's order (reported as a contradiction; not resolved here).**``

- Task 24 assigns scratch storage to the fixture Git checkout. build_repo already creates and initializes <tmp_path>/work; the proposed --work-dir <tmp_path>/work therefore trips the new WorkDirInGitTree refusal before the existing ledger/root/rescore cases reach their intended checks. Create a separate existing sibling scratch directory outside that checkout and the stand-in system temp, and pass it through the shared helpers.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``--work-dir <tmp_path>/work``
  quote: h-mad/tests/grokauditfixtures.py › ``work = tmp_path / "work"``

- Scrub Git environment variables for Task 19’s check-ignore call as well as rev-parse. The prescribed second call inherits GIT_DIR/GIT_WORK_TREE and can consult another repository or refuse a valid checkout, contradicting the ambient-Git test. A read-only control here returned 0 for the prescribed check-ignore with a clean environment and 128 with GIT_DIR=/dev/null. Apply the same clean environment to both calls; test with two repositories whose ignore rules differ.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``git -C "$T" check-ignore -q .h-mad/tmp/hmad_exec_grok.probe``

- Task 23’s usage-guard mutants lack distinguishing assertions. With the run directory missing, disabling CANARY-RUNDIR-EXISTS still reaches the no-roots refusal; disabling CANARY-RUNDIR-GIVEN likewise reaches the absolute-path refusal. The specified exit 2, absent token and common usage line are unchanged, so rows 22/24 can survive despite correct guards and block ALL_CAUGHT. Assert guard-specific diagnostics, or define non-equivalent reason mutations while preserving the operational exit contract.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``errors exit 2 with usage on stderr and no``

- Make the replaced-sentinel fixture reach the sentinel check. Task 23 adopts the real plant → exec → judge route, but its paired design says that stub logs nothing. The current _cmd_exec turns an empty final response into rc=3 (hmad-dispatch.sh:3366–3374), and the planned judge checks cannot_run before sentinel_changed. Supply a completed, non-secret transcript with a final response, or explicitly test the judge boundary with rc=0; preserve the end-to-end expected-value coverage.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``exec → judge path)``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``with another 32-hex token and logs nothing:``

- Task 30 can certify a work-tree dispatch that never ran. Its work-tree leg gates only on unchanged Git status and zero leftover staging directories; an early staging refusal produces both observations, while the passing canary exercises only the export-root branch. Capture the work-tree stdout/stderr and require the expected OK response plus evidence of a completed live dispatch before accepting cleanup/status results. Otherwise the pre-merge gate violates Test discrimination and Wrapper–runtime reconciliation.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``- [ ] AC-T30.2: `STATUS=same`, and the staging-directory count prints `0`.``

- Task 24 needs the mandated old/new guard differential. Inverting the destructive reset’s temp-directory predicate deliberately accepts locations the shipped check rejected, but the task lists individual new fixtures only. Add a corpus comparing the complete old and new reset preconditions, account for every softened verdict, and include sibling/nested roots, wrong document prefixes, physical/symlink spellings and Git targets. This is the base Guard narrowing requirement, independent of a green regression suite.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``"resolved target inside system temp", raising `ResetTargetInSystemTemp```

## Should-fix

- Assign the per-pass quote-root migration to an S0c task and add an extraction-path fixture. The current extract_all still reads cycle/root.txt (grok_audit_probe.py:1078), while S0c writes pN.root.txt and leaves no S2 root.txt. No S0c task explicitly changes that hint lookup. An absolute quote from pass 2/3 can consequently resolve against the live filesystem instead of its exported seeded/paired copy. Update the lookup to the finding’s pass record and test after the live root is unavailable; hints remain advisory.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › ``no `root.txt```
  quote: docs/02-design/features/grok-audit-surface.design.md › ``(`p<i>.root.txt` `path=` for an S2 cycle from v1.6, `root.txt` otherwise)``

## Nit

None
AUDIT-grok-audit-surface-impl-plan-v3-END
