AUDIT-phase5-gate-feature-scope-plan-v1-BEGIN
## Summary

Five functional requirements yield different implementation or test decisions when the plan is reconciled with the spec. The baseline source also exposes gaps in the landing procedure, mutation controls and evidence used to accept the change.

Evidence: 21 files opened, 23 greps run.

| Requirement | Axis C classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | restated |
| FR-3 | restated |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | restated |
| FR-7 | restated |
| FR-8 | implemented-as-written |
| FR-9 | implemented-as-written |
| FR-10 | restated |
| FR-11 | implemented-as-written |

## Must-fix

- FR-2 substitutes batching for pruning. The proposed walk can visit every excluded descendant and still pass both the process-count and file-open checks. Observe directory visits or classification inputs, with a tracked-content control, so the test fails if discovery individually classifies copies below an excluded root.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The walk stays as it is in what it descends into and in what it cannot enter.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `A git-excluded tree is pruned as a tree: it is judged once, at its highest excluded directory`
- FR-3 gives the target a vote when it cannot be resolved. Row 5, inherited by agy row 11, would over-gate an otherwise ungated session. Split this fixture from a resolvable target whose checkout Git cannot identify. Only the latter gets the unknown-checkout rule.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `codex per-target (unresolvable, outside the root, allowance file, production, listed) | session plus target applicability`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `A write with no identifiable or resolvable target, an agy workspace mismatch and an agy tool outside the admitted classes are judged on rules 1 to 3`
- FR-6 makes protection of an off-chain state-file referent conditional on a future decision. The proposed target-only filter lacks the information to recognize that referent. Commit to coverage within the timing bound and require a real-hook case for the alias, or obtain an explicit spec change.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The design either pays for discovery there inside the 300 ms bound or returns the case for a spec residual`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `a state file discovered from either, and a `.git` component inside either, is protected.`
- FR-7 leaves the halt-field write without an established route in the shared-store worktree. The current safe-list check resolves the store and requires it to lie under the session root’s docs directory. A worktree link to the main checkout’s file fails that check. Exercise a halt-only write through both real shell hooks in this topology, re-read the shared record, and specify the authorization the working route requires.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `unchanged in what they admit; FR-5 is a check in front of both, not a change to the list.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `From a gated session, halt fields can be written while `phase` cannot.`
- FR-10 requires an exclusive cause for each difference where the spec permits overlap. An excluded tree can also lie under a fixtures directory. Use isolated controls to establish each class and accept explained overlaps in the crossed corpus. Give D5 a writer observation as well. Hook verdicts alone cannot show whether a successful write preserved a symlink.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `every difference between the two trees is accounted to exactly one of D1 to D7`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Every difference is in D1 to D7, each class has at least one difference under at least one of them, and no other allow or refuse changes.`
- The new staging refusals conflict with the base signal contract. A readable record at the planning stage or in another checkout produces an ordinary policy verdict. Reconcile AC-9.5 and AC-11.2 with the invariant before implementation. Assert the HALT stdout token, exit 0 and absence of a staged prompt for both refusals.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › ``checkout_mismatch` and `phase5_stage_planning` halts in `h_mad_assemble_tdd.py``
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › ``ASSEMBLE-TDD: HALT phase5_stage_planning` and exit 2.`
  quote: h-mad/invariants.base.md › `**exit 0** on a normal verdict (PASS or FAIL).`
- The prescribed reverse mutation can duplicate removal. For an arming-file refusal, deleting the check and forcing a permissive answer both admit the protected write. Both mutants can be caught while an unconditional refusal goes undetected. Force refusal on an ordinary allowed write as the opposite control. For Git-environment wires, vary the environment at the call site while leaving the lookup implementation intact.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `Each row also has the reverse mutation (the call forced to the permissive answer)`
  quote: h-mad/invariants.base.md › `unconditionally → the fall-through/negative test must fail.`
- The Git-variable positive control is undefined in no-Git corpus cells. With an explicit root, no state and no sub-project candidate, the performance contract requires zero added Git calls. There is no hook question in that cell whose answer can change. Establish effective values in paired fixtures for each variable and host, record the observed Git answers, then reuse those settings in no-call cells while checking the verdict and process count.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `A case first asks git directly a question the hook asks in that case`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `with no live record, a hook starts no git process beyond those it starts now, except to classify a sub-project state file it found.`
- The landing test omits the schema from the writer combinations. The validator loads its strict schema from disk and caches it in-process. An older writer loading a newer schema is a different case from the archived older writer with its own schema. A momentary check for running writers leaves time for another invocation to start. Exercise the mixed writer/schema pair and concurrent writes in scratch, or establish writer exclusion through verification.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `each mixture of old and new among the six policy files (three hooks, identity, judge, writer)`
- The fast-forward command does not identify the reviewed commit. The observed branch status is `main...origin/main`, so the argument-free merge can report that main is current while the feature remains unlanded. Capture the tested feature SHA, pass it as the merge target, and require the resulting HEAD to equal it before installed checks or rollback.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `then `git merge --ff-only`. If it is refused, return to step 1.`
  quote: h-mad/invariants.base.md › `an **exit code is not evidence that a mutation`
- The landing procedure calls a Claude hook self-check that does not exist. The shell hook reads a write payload and uses its first argument as a fallback target. Passing `--self-check` exercises ordinary target handling. Require the existing self-check tokens for codex and agy and an installed Claude invocation with known allow and deny observations.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `each hook's self-check through each install link`
- The pin census cannot be re-derived from the recorded command. The file-selection pipeline and pytest invocation omit the instrumentation and control invocation that produced the per-class counts. Identify a retrievable instrument revision and record the capture and control commands before relying on the zero counts to constrain test edits.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `S0 commits the instrument and its control as the pin census probe`
  quote: h-mad/invariants.base.md › `MUST carry the exact command that produced it, inline and`

## Should-fix

- S0 schedules the landing probe before its discovery dependency exists, while S1 says nothing calls the new helpers. Separate baseline capture from the final probe and place the latter where its discovery-removal test can run.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `the timing probe; the landing probe; the census of existing pins`
- The worktree handoff omits the untracked plan, spec and brainstorm. `git status --short --branch` lists all three as untracked in main. A linked worktree created from main will lack them. Name the transfer step and compare the reviewed document hashes before 5a consumes them.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `Create the feature branch and linked worktree from current `main``
- The instruction to use two audit surfaces omits the first-cycle routing condition. Reference the existing first-gate rules so the third surface runs when available and the recorded stamp reflects the actual legs.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `Plan audit on two surfaces, then revision in a fresh author context.`
  quote: h-mad/SKILL.md › `First gating cycle of a document, codex available: `codex` + `agy` + `grok` via`

## Nit

None
AUDIT-phase5-gate-feature-scope-plan-v1-END
