AUDIT-phase5-gate-feature-scope-plan-v2-BEGIN
## Summary

The plan covers every functional requirement, but its proposed evidence for FR-4 and FR-10 is weaker than the specification. The baseline extraction, writer tests and landing sequence also need corrections before their results can establish that the change is safe to install.

Evidence: 24 files opened, 14 greps run.

| Requirement | Classification | Basis |
|---|---|---|
| FR-1 | implemented-as-written | S2 covers checkout validation, clearing, canonical spelling and shared stores. |
| FR-2 | implemented-as-written | S1 defines discovery for the session scan and target chain, including excluded and nested trees. |
| FR-3 | implemented-as-written | S6–S8 route decisions by session, target and command directory. |
| FR-4 | restated | The admitted half of the unreadable-root test removes the live record. |
| FR-5 | implemented-as-written | S5, S8 and S9 apply the writer grammar across shell admission routes. |
| FR-6 | implemented-as-written | The three write hooks cover both checkout roots and both spellings of a linked target. |
| FR-7 | implemented-as-written | The route and topology tests cover state writes, halts and exits. |
| FR-8 | implemented-as-written | The scope verb and shell diagnostics expose the applying record and reason. |
| FR-9 | implemented-as-written | S3 and S9 cover the staging check, planning window and unreadable-root exception. |
| FR-10 | restated | The crossed differential accepts class membership as an explanation for a changed verdict. |
| FR-11 | implemented-as-written | S3 and S10 cover staging, recovery and the host documentation. |

## Must-fix

- FR-4 gives two different instructions for the unreadable-root control — removing the live record can produce an allow even if the implementation ignores root readability. Keep the inactive fixture to exercise the branch. Add a separate pair with identical live record, stage and command, changing only root readability in a checkout the record does not name. Assert the appropriate hook decision or verb output in each half.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The admitted half has a state file that is present and holds no live record, so that the call is reached.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `the same case with the root made readable and inside a checkout the record does not name, and git available.`
- FR-10 weakens the differential’s verdict check to fixture membership — an excluded copy can coexist with an ordinary live root record. Removing the copy must leave a refused command refused, yet a changed verdict in that fixture qualifies as D1 under the stated rule. Derive the expected verdict after the permitted change for each crossed case, including when another record still governs it.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `In the crossed corpus a difference is explained when the facts of its fixture put it in at least one class`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Every difference is in D1 to D7, each class has at least one difference under at least one of them, and no other allow or refuse changes.`
- The baseline extraction omits the dispatch executable whose identity the old hook checks — the historical module resolves its trusted wrapper relative to its own tree. A wrapper from the installed tree cannot serve as the baseline positive control for a wrapped allowance. Include the historical executable and its backing file, resolve each side’s wrapper locally, and demonstrate admission on both sides before comparing changes.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `git archive 7a3cca48 h-mad/hooks h-mad/scripts`
  quote: h-mad/scripts/h_mad_target_identity.py › `return (_trusted_executable(argv[0]) == hmad_dispatch`
- The CLI needs a byte-preservation test for compound writes — the historical writer persists a create or claim before it calls `merge_fields`. If a new checkout or stage validation refuses there, an earlier operation can already be on disk. Exercise a valid create or claim followed by a refused new-field assignment in the same invocation. Verify the entire store against its pre-call bytes and make validation and persistence atomic for this case.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `each through the CLI and through `merge_fields``
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `and leaves the store byte-identical`
  quote: h-mad/scripts/h_mad_state_write.py › `create_feature(args.state_file, args.feature, args.started_ts)`
- The pruning test records directory visits without requiring them to stop — a walker can enumerate excluded descendants, omit them from Git’s inputs, and avoid opening every state file. Both stated failure predicates then stay false. Assert the recorded directory visits as well as file opens and classification inputs. Include a case where the excluded tree holds the only candidate, to establish how pruning works alongside the restriction on starting Git before finding a candidate.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `It fails when a path strictly below the highest excluded directory is a classification input of its own, or when a state file below it is opened.`
- Rows 15 and 16 assign separate mutations to one existing connection — the judge CLI calls `read_chain` once before branching to `state` or `judge`. Count that common call once and run both verbs against its mutants, or identify two distinct downstream calls and mutate those. For `judge`, assert the verdict kind or a measured allow, since an inactive chain itself produces a denial.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `each mutant changes the call site only.`
  quote: h-mad/scripts/h_mad_tdd_judge.py › `chain = read_chain(root, target)`
- S3 leaves the recovery token ambiguous when both staging checks apply — a matching live feature can be at planning and name a different checkout, and different discovered records for that feature can also trigger the two checks. Define a deterministic first HALT and the sequence of corrective actions. Test both conditions together, with discovery order reversed, and verify that the prompt is unchanged and no stamp is created.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `with the FR-11 record lookup and the re-stage route of each check`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `a refusal of AC-9.5 or AC-11.2 applies when any live record so found meets its condition.`
- The mixed-writer landing check cannot establish which updates survived — endpoint process lists miss a writer that starts and finishes between readings. A changed final store also cannot reveal a second intended update that was overwritten, and hashing contents alone cannot distinguish a link from a regular copy of the same bytes. Either coordinate a writer-free interval or record enough operation and link-identity evidence to reconcile the writes. Exercise that procedure with overlapping scratch writers before promising repair.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `Detection covers the listed lanes.`
  quote: h-mad/scripts/h_mad_state_write.py › `os.replace(tmp, state_file)`
- The mixture test treats an unrelated implementer response as a successful write — the historical verb can emit `no-record`, an unchanged choice, or a switch with no write needed, all without `record=failed`. Give it a switch that actually requires persistence, assert the exact result and re-read the switch record. Separately exercise an actual write refusal and verify unchanged bytes.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `no line without `record=failed``
  quote: h-mad/scripts/h_mad_tdd_judge.py › `line = f"no-record feature={_enc(args.feature)}"`
- The feature branch is created twice in this feature’s own run — following the installed 5c command after the pre-5a worktree instruction encounters an existing branch. Use a detached worktree before 5a and create the feature branch there at 5c, or document a verified existing-branch path that still makes the impl-plan commit the first feature commit.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `Create the feature branch and linked worktree from current `main``
  quote: h-mad/references/phase5-substeps.md › `git checkout -b feature/NNN-<slug>`
- Landing step 1 has a circular prerequisite — it requires all success criteria before step 2 shows the report and step 5 moves the main checkout to the tested commit. Specify which evidence releases the feature branch for landing and which observations complete landing. Otherwise the prescribed sequence cannot start on a feature branch ahead of main.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `All success criteria met on the feature branch, rebased on current `main`.`
- Rollback lacks a readback of the installed policy — after the revert, check the resulting tree and rerun an installed-hook allow and refusal on scratch state. A successful recovery should have observable completion criteria just as the fast-forward does.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `they come back as step 4 says.`

## Should-fix

None

## Nit

None
AUDIT-phase5-gate-feature-scope-plan-v2-END
