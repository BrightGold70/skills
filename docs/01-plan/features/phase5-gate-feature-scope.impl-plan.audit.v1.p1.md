## Summary

I checked all 56 tasks against the paired requirements and the source at `bb88b6cc` without running tests or modifying the repository. The mutation tables reconcile to 389 additions and 9 removals, but several named tests cannot observe their assigned change, and the stated RED bases cannot be reproduced as written.

Evidence: 32 files opened, 10 greps run.

## Must-fix

- Use repository-relative node IDs for `WIRE-PIN` and skill-relative IDs for mutation rows. The registry stores the declared pin verbatim. Its resolver cannot match `tests/test_x.py::test_y[id]` against the repository collection’s `h-mad/tests/test_x.py::test_y[id]`. A passing test would still be reported missing at 5f.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `A test is named by its node id relative to`
  quote: h-mad/references/phase5-substeps.md › `whose node ids are repo-relative`
- Give each task a reproducible RED base within its step. Tasks 3–5 successively edit the same identity module before S1 is committed. The prescribed whole-file stash for Task 5 also removes Tasks 3 and 4, including the callee that its wire pin requires. Use task checkpoints or verify against a saved pre-task tree while preserving the intended step commit.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `One commit per step, at 5g, after every task of that step is green`
  quote: h-mad/references/phase5-substeps.md › `git stash push -u -- <production-paths>`
- Align staged pytest inputs with the stated counts. Task 54 runs the same file that already contains Task 53’s 30 passing nodes. A file-wide run yields 7 failing and 30 passing at RED, then 37 passing at GREEN, assuming the earlier tests stay green. Either stage task-specific selections or publish cumulative counts for the actual paths. The same issue starts at Task 2.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `RED 7 failing, 0 passing; GREEN 7 passing.`
  quote: h-mad/scripts/h_mad_assemble_tdd.py › `These are totals across every test path in this dispatch, not per file.`
- Give Task 1 a verdict decoder for each host. `tdd_gate_support.decision` accepts a silent allow or the Claude denial protocol. Agy prints a JSON decision for both outcomes, and Codex denial reasons use a different kind grammar. The specified decoder classifies an ordinary agy allow as invalid. Require baseline allow, deny and malformed-output controls for each adapter before comparing twins.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `tdd_gate_support.decision`
  quote: h-mad/tests/tdd_gate_support.py › `if result.returncode == 0 and not result.stdout:`
  quote: h-mad/hooks/h-mad-agy-tdd-gate.py › `print(json.dumps(decision))`
- Discover interpreters by executable identity. Two distinct installations can share a minor version, so taking the first launcher for that version silently drops the second. Resolve aliases to the same executable once and exercise both when the executables differ. Test the collision as well as the missing-launcher case.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `each id takes the first launcher whose version matches it`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `The supported Pythons are the distinct interpreters among`
- Correct the FR-4 expected-outcome table. A valid record naming the main checkout permits the write or shell command from the linked checkout in the AC-4.13 fixture. AC-4.14 has the same direction for nested checkouts. The blanket refused-half rule would make the correct implementation fail on every host. Give these cases an admitted nonmatch and a gated matching control.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the refused half from a session in a checkout the record does not name`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `a record naming the main checkout does not apply in its linked worktree, and the reverse.`
- Give Task 6 feasible precedence fixtures. A stored checkout cannot be both absent and usable, and a single checkout lookup cannot simultaneously be unknown and match. Use overlapping conditions to test precedence, then separate fixtures to exercise mutually exclusive reasons.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `also holds every condition of the reasons after it`
- Make Task 5’s timeout test reach the second timeout. A child that stops reading is still killed by SIGKILL. Its prompt exit gives the same observation with a bounded or unbounded subsequent wait. Keep the real-child reaping test and add a controlled wait that times out after kill and verifies that the caller returns the specified result.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `by one that stops reading`
- Exercise the FR-5 superset check after the new writer fields exist. In S1 the real writer cannot produce a successful checkout or stage change, so Task 9 can pass without comparing either effect. Re-run with S2-valid inputs, assert an observed store change for each arming field, and check that the classifier detects each successful write.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `every invocation that changes an arming field is a hit.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `the set that the gate treats as changing an arming field includes every invocation that, run by the real writer on a scratch store, changes one.`
- Guard the filesystem capability lookup in Task 10. The SDK defines selector 11 for Darwin, but a numeric `pathconf` selector has platform-specific meaning. The fallback on exception cannot detect a successful query for a different property. Use a known platform mapping or a reported capability name, and test the unsupported and indeterminate results separately.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `os.pathconf(directory, 11)`
- Specify one writer step-result contract. `_step_drop` returns a pair, while `apply_invocation` accepts steps returning dictionaries. The runner also needs the changed/no-op decision and deferred output from each step. Thread the existing caller-supplied `now` through beat and merge so a transactional invocation preserves the public clock behavior.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `def apply_invocation(state_file: Path, feature: str, steps: Sequence[Callable[[dict | None], dict]]) -> dict: ...`
  quote: h-mad/tests/test_h_mad_state_write.py › `sw.beat(p, "demo", "me", now="2026-07-22T01:30:00Z")`
- Pass the frozen store path to Task 13’s membership check. `_step_merge` receives the record, fields, session ID and appends. None identifies which store `_mutate` locked. Carry that path into the step or perform membership validation where the locked path and proposed checkout are both available. Exercise the two-store case through the CLI and the library.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `def _step_merge(record: dict, fields: dict, *, session_id: str | None, appends: list) -> dict: ...  # gains the call`
- Change the killer for Task 14’s fixed resolved seed. When both paths agree, the resolved-path call is skipped, so changing its argument cannot affect `test_seed_once_when_paths_agree`. Run the mutant on a symlinked store and verify the exact distinct destinations. Keep the equal-path case for a mutant that duplicates the call.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the resolved call seeds one fixed path`
- Move the scope-dependent FR-6 controls to each host’s rerouting task. Tasks 21, 23 and 24 run the shared-store cases while S5 still treats every live record as applying. In the AC-6.8 fixture this would refuse M’s own state file. Stage that preservation assertion in S6 for Claude and S7 for Codex and agy, and retain the unconditional S5 protection checks.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `so every live record of today's discovery counts`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `and M's own file keeps its present decision there.`
- Normalize the Claude root before the S5 legacy walk. Task 24 passes a `str` to `unscoped_judge` without a precomputed walk. Task 20 then reaches the Path-only `root.rglob` call, producing a hook error even for an ordinary permitted write. Make the conversion at one boundary and test the real emitter with its string input.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `def emit_arming(root: str, raw: str, identity: Identity) -> None: ...`
  quote: h-mad/scripts/h_mad_target_identity.py › `root.rglob("docs/.bkit-memory.json")`
- Specify the record conversion at Task 25. Task 6 types `Applied.record` as `LiveRecord`, while the judge needs a `Record` with `key`, authoring fields and `checkout` for listing. Define where the judged result acquires that type and preserve the nonapplying entries needed by Task 27. Exercise both consumers with the same stored record.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `a `Record` carrying the reason`
- Re-anchor `H-LIST-INROOT` at the outside-root unreadable-state decision. The existing killer writes invalid bytes. There is no live record for a retention filter to keep or drop, so changing that filter alone cannot flip the killer. Preserve its original discrimination while keeping the new applicability-filter mutations separate.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `moves to the judge line that holds the AC-3.4 filter`
  quote: h-mad/tests/mutation-specs/claude_gate_listing.json › `Read the governing root's unreadable state for an outside-root code-like target.`
- Carry the applying reason into Task 42’s refusal formatter. `LiveRecord` contains the feature, file and stored data. The reason belongs to `Applied` and can differ with the command directory for the same record. Pass the applying entry or its formatted description and test both contexts on Codex and agy.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `def arming_refusal(hit: ArmingWrite, record: LiveRecord | None) -> str: ...  # the fourth exit actor; describe's reason`
- Move Task 43’s planning-sensitive unreadable-state control to S9. For session and directory queries, an applying planning record produces `shell=no` in the scope verb. In S8 both hooks still use `every_stage`, so that same record yields active ahead of unreadable and admits a safe command. Run the stage-independent controls in S8 and the planning case after both shells gain the predicate.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `test_unreadable_agrees_with_hooks[session|directory]`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `the codex and agy shells refuse every command when no line says `shell=yes` or the file's top level is not an object`
- Preserve the legacy exception when Task 47 changes `_any_phase5_status`. Returning the nonthrowing scan’s value directly loses the distinction between a non-object top level and an ordinary unreadable file. Keep the compatibility check before active can win, and test a non-object file beside an applying live record through both shells.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `scan.session().value`
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `re-raises what it raises today`
- Supply a failing control for the credited regression guards. Task 47 explicitly counts process-lifecycle tests that fail on no removal, and Tasks 11, 48 and 52 also credit guards without a demonstrated failure. Run a controlled violation of each asserted property, or retain it as an observation outside the mutation and RED proof.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `guards; a property check that fails on no removal`
- Replace the Task 52 exit mutant. Once the sole live record has exited, removal A falls back to the original expression. The next command therefore sees the same inactive status in both runs. Use a control that retains the pre-exit state or status and check the next command in the formerly gated session. The `[ungated]` route likewise needs a mutation at its guard because an always-hit classifier behind an inactive guard is never called.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `test_exit_ungates_next_command[codex|agy]`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `After the exit by an ungated session, the next command in the formerly gated session is judged as not gated.`
- Stage Task 53’s `lane_listing` callee before its connection pin. Both the CLI caller and this callee first appear in the missing probe, so `[listing]` cannot use the missing-caller exception at RED. Provide the working callee first or a runnable CLI scaffold, then observe a caller assertion fail when only its listing connection is absent.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `every one failing at RED (the probe does not exist).`
  quote: h-mad/references/phase5-substeps.md › `the missing symbol is the caller the task creates, and the callee resolves at the RED base.`
- Separate the landing probe’s owner and heartbeat fixtures. With the proposed clock switch set, the actual `read_minted_owner` returns `False` before examining the lane. The minted-owner test and its removal mutant therefore have identical evidence. Run the owner pin with a real scratch Git directory and the switch unset. Isolate the heartbeat-only reading separately.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the liveness clocks other than the heartbeat are switched off by `H_MAD_LIVENESS_CLOCKS_OFF`.`
  quote: h-mad/scripts/h_mad_state_ownership.py › `def read_minted_owner(lane, session_id: str) -> bool:`
- Correct Task 55’s RED split. The tests must exist to be collected. Once authored, the already-true prohibition on documented step6/step7 commands is a passing guard. Its mutation supplies the failing observation. With the rest of the stated split unchanged, RED has at most 32 failing nodes and at least one passing node.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `it is listed as failing because the test file does not exist at RED`
- Schedule the S6 Claude timing check before S7. Task 2 takes a baseline and Task 56 measures the completed feature. Neither supplies the intermediate whole-hook result at the commit where the Claude discovery changes. Record the S6 medians on both required repositories and apply the over-bound decision there.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/timing.py --old "$OLD" --runs 20`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `A median over the bound in S6 is put to the operator before S7 begins.`
- Drive the topology cases under every supported hook and writer interpreter. Task 56 invokes the topology file once through the 3.11 venv, and Task 52 supplies topology IDs without specifying an internal launcher loop. Keep pytest in the thin venv and vary the invoked processes, with evidence of which interpreter ran each topology. Apply the same launcher coverage to the checkout-field cases of AC-4.10 through AC-4.12. The field-free differential cannot cover those records.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `.venv/bin/python -m pytest h-mad/tests/test_h_mad_phase5_scope_topologies.py -q`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `differential and topologies under every supported Python`
- Assign the mixed-version run an executable entry point. Task 56 lists the mixture verdict as an operational reading, but none of Tasks 1–55 constructs and runs the gate, writer and staging mixtures. Name a harness or give runnable commands that assemble each set, exercise its corpus and identify the failing combination. An old-versus-new run alone cannot establish the mixed result.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `each set's corpus run on every mixture of old and new files, no mixture allowing what both trees refuse.`
- Make the final timing matrix include an explicit target in a second checkout. The three target kinds on the root checkout do not exercise the additional discovery. Report this measurement separately from the two repositories subject to the 300 ms bound.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the codex, agy and Claude hooks on the three targets`
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `and a target in another checkout, whose own discovery is a second one.`
- Specify which check demonstrates the simulated Linux path. The mounted case-sensitive volume covers filesystem spelling, but it still runs the Darwin interpreter. Run or identify a test that removes `F_GETPATH` and exercises checkout matching through the fallback before labelling the evidence simulated.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the Linux evidence is called simulated.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `-absent branch by patching.`
- Strengthen the probe’s read-only test. Identical file hashes cannot detect a file opened for writing and closed unchanged, or a temporary file created and removed. Observe write-capable opens during the probe and keep the before/after store checks for persistent effects.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `file hashes around the run.`

## Should-fix

- Make Task 4’s locale precondition explicit in its tests. It requires an exact English Git diagnostic before Task 5 supplies the production environment. Set the fixture locale for the intermediate test and give Task 5 the inherited-locale integration check.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `This task gives that call no environment argument`
- Define `base` at the Codex FR-6 call site in S5. The current code resolves payload cwd inside `_relative_target`. Reuse that resolution before the head-of-loop check and exercise a relative target from a subdirectory so the check and the actual write use the same path.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `arming_target(scan, raw, base, judged)`
- Correct the collection-count expectation. Task 38 adds 3 nodes and removes 16, for a net decrease of 13 nodes in that task. Compare each collection with the expected additions and removals so the planned cleanup does not look like lost coverage.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `Its collected count is re-taken at 5c and only grows from there.`

## Nit

None
