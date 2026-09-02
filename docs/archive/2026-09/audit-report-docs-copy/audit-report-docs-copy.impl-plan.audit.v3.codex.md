## Summary
The impl-plan is close to executable and has incorporated the prior mutation-output fixes, but two remaining instructions are inconsistent enough to undermine the checkpoints they are supposed to prove. The main gaps are in Task 6's mutation command surface and Task 3's hand-replay evidence target.

## Must-fix
- Task 6's JSON skeleton omits one of the five required test files — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:259` and `:262-263` say the mutation spec command runs five new/changed files including `tests/test_h_mad_audit_cycle.py`, but the code block at `:283` lists only four and omits that file. The harness uses `command` for baseline/restore and fallback suite checks, so an implementation copied from the skeleton can report `MUTATION: ALL_CAUGHT` without running the AC-3.3 consumer test surface, weakening Mutation verification/Test discrimination.
- The AC-2.9 hand-replay evidence target names a duplicate version line — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:175` requires pasting the replay transcript as a new `v1.7` line in `audit-report-docs-copy.plan.md`, but that plan already has `v1.7` at `docs/01-plan/features/audit-report-docs-copy.plan.md:219`. Since the replay is the base Incident replay evidence and gates Task 4, the exact instruction either creates a duplicate Version History entry or is refused by the version-history helper instead of producing an unambiguous checkpoint.

## Should-fix
- Task 6 still says the existing `test_audit_cycle_mutation_specs_*` tests validate the new spec — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:276-278` conflicts with AC-6.4 at `:321`, which says those tests load only the two existing specs and are not extended. The AC is clearer than the prose, but leaving both invites an implementer to edit the file AC-6.4 forbids or to over-credit the old spec-registry tests.
- Task 5's task metadata names only `h-mad/SKILL.md` as the production file even though the task also modifies `h-mad/references/orchestration-mode.md` — the path is present in the description and AC-4.2, but not in the metadata at `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:218`. This is not a design gap, but it is inconsistent with the impl-plan's exact-file-path contract.

## Nit
- The impl-plan source pointer says the paired design is post-audit `v1.11`, while the saved design has a `v1.12` Version History entry. Update the citation so reviewers can tell the impl-plan is based on the latest design text.
