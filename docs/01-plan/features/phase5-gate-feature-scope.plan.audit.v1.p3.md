## Summary
Plan v1.2 carries FR-1 through FR-11 as spec v1.4 writes them, and the step5 census, the schema-order placement, and the empty `h-mad` diff from `7a3cca48` to `b29173f1` match the tree. The documented exit clears `phase` from a directory outside the named checkout, and the worktree steps treat a gitignored state file as a symlink with no creation step, so this feature's own implementer session would stand down. The 2.1–2.3 s scan premise records three samples and no runnable command.

| FR | Axis C |
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
| FR-11 | implemented-as-written |

Evidence: 36 files opened, 26 greps run.

## Must-fix
- The documentation step runs the FR-7 exit from a directory outside the named checkout, because rule 5 judges where the command runs. FR-3 applies a live record when any of its rules holds: rule 3 is session-checkout match, and rule 5 adds a gate when the named checkout contains the command directory. A codex or agy session whose checkout the record names stays gated when that directory is elsewhere. Contract text and the AC-11.1 / AC-7 tests written from this sentence would require a `phase` clear the gate refuses. The spec's exit is an ungated session: the operator, Claude, grok, or a codex or agy session whose own checkout the record does not name.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The documented exit is run from a directory outside the named checkout, because rule 5 judges where the command runs.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `is performed by an ungated session: the operator at a terminal, a Claude or grok session, or a codex or agy session whose checkout the record does not name.`
- Convention Prerequisites says the worktree's `docs/.bkit-memory.json` is a symlink to the main checkout's file, and the steps before that sentence create the worktree and a `.venv` only. The path is gitignored, so a fresh linked worktree does not receive it. In this checkout the file is a regular file (`ls -ld`: `-rw-------`, 52336 bytes). Discovery is from the session root, so the implementer there does not see this feature's record and the installed gate stands down for the whole of Phase 5. A recorded gotcha already says to provision that file before 5d.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `in the worktree is a symlink to the main checkout's file, so the implementer's gate sees this feature's record. Until this feature lands, state writes go to the main checkout's path and never through the link.`
  quote: docs/learnings.md › `h-mad state docs/.bkit-memory.json is gitignored, so a fresh feature git worktree has no state and the TDD gates stand down there; provision state before 5d`
  quote: .gitignore › `docs/.bkit-memory.json`
- The old-scan timing premise (2.1 to 2.3 s, samples 2.13, 2.19 and 2.33 s) names a function, an interpreter and "three warm calls", and it does not give an inline runnable command. Base invariant "Behavioural premises carry their command" requires that command beside the output. The 300 ms bound remains the spec's; correcting the citation leaves the tree unchanged.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The old scan alone took 2.1 to 2.3 s here (three warm calls of `_any_phase5_status(Path('.').resolve())` from the repository root under python3.11, 2.13, 2.19 and 2.33 s)`
  quote: h-mad/invariants.base.md › `MUST carry the exact command that produced it, inline and`

## Should-fix
- The structural git-environment test is specified over the hooks, the identity module and the judge, while the Claude hook's shell scratch lookup stays an `env -u` of the four variables around `git` and is not rewritten. A scan of `h-mad/hooks/h-mad-tdd-gate.sh` fails on `_outside_every_work_tree` until the test's exclusion is written down. The following sentence names the lookup and does not state the exclusion.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `a structural test over the hooks, the identity module and the judge finds no git call without it. The shell-side scratch lookup of the Claude hook already leaves the same four out and is not rewritten.`
  quote: h-mad/hooks/h-mad-tdd-gate.sh › `env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR -u GIT_CEILING_DIRECTORIES`
- `test_each_moved_function_has_one_definition_in_the_identity_module` runs only for names in `MOVED_FUNCTIONS`. The plan says a copy of a shared policy function anywhere under `h-mad/` breaks that test. Discovery, applicability, stage and the arming checks are new names, so a second definition of any of them stays green until `MOVED_FUNCTIONS` gains that name. The implementer has to extend the tuple; the plan treats the current test as already covering those names.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `requires each shared policy function to have exactly one definition, there.`
  quote: h-mad/tests/test_h_mad_shared_gate_policy.py › `@pytest.mark.parametrize("name", MOVED_FUNCTIONS, ids=MOVED_FUNCTIONS)`
- Row 9's agy shell pin expects `[workspace-mismatch-planning]` not to be refused, which is the FR-9 stage exemption (AC-9.8). The order table places agy `run_command` in S8, whose effect is that the stage is still ignored, and places the exemption in S9. A wiring task that lands that id with row 9 is red on an S8 tree that matches the order table, or it opens the 5a–5d window inside S8. Those planning ids belong on the S9 task.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `(not refused) and`

## Nit
- The shared-tree risk says 19 commits in the seven days to `7a3cca48` and cites `git log --since=2026-11-17 --oneline main`. That command on current `main` lists 21 commits; the two after `7a3cca48` are `2b0db79a` and `b29173f1`. Pin the rev the 19 was counted on.
- The scope bullet that a checkout no live record names runs without the Phase-5 command list reads as every unnamed checkout being ungated. FR-4 stays in force under Requirements, with all 88 acceptance criteria unreduced, so the bullet is loose wording.
