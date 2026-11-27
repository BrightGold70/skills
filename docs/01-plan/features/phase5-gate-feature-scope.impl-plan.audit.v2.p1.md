## Summary

I checked all 56 tasks against the paired documents and baseline code. The 55 mutation tables contain the stated 426 additions, but the writer contract, intermediate differential expectations, and planning-only shell tests would produce incorrect implementations or misleading gate evidence. This was a read-only review without pytest or mutation execution.
Evidence: 34 files opened, 68 greps run.

## Must-fix

- Reconcile the RED dispatch order — Task 5 needs Task 3’s implemented callee at RED. Its production-file checkpoint can preserve that callee only if the earlier GREEN has already run. Give the dispatched implementer an explicit per-task RED/GREEN order or restructure the dependent tests for the shared RED base.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `Task 5's callee from Task 3 included`
  quote: h-mad/references/codex-implementer-prompt.md › `every 5d runs before any 5e`

- Assign the gated and ungated harness commands explicitly — the Codex safe list permits `--check-anchors` only with at least one in-project spec argument. It admits neither `--append-row` nor the argument-free sweep. Keep the per-spec check in the gated dispatch and assign appends and the committed-spec sweep to the orchestrator that can run them.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › ``python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors`, with no spec argument`

- Decode the baseline Codex denials that carry no kind — at `7a3cca48`, `_main_guarded` emits valid denial JSON for an unreadable shell and an unidentified write target without a `kind=` field. A production denial also puts a semicolon after its kind. Exercise both forms, distinguish a missing kind from an invalid envelope, and require a kind only where the protocol supplies one.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `its kind the word after the reason's last `kind=``

- Track the differential by decision branch during partially landed steps — after Task 39 an ordinary Codex command uses filtered discovery while an FR-5 command still uses the old walk until Task 42. With one live record in an excluded tree, the two calls require different twins. The same gap occurs between Tasks 43 and 44 on agy. A single class set per surface cannot represent those intermediate full-suite runs.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `CHANGES_IN_FORCE: dict[str, frozenset[str]]`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The full suite runs once per task, not once per feature.`

- Make the timing exclusion test deterministic — counting the second checkout in `max_added_ms` changes the maximum only if that checkout is slower than every bounded case. Supply controlled timing samples with that ordering for the aggregation assertion and retain a separate real-hook smoke run.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `with `--runs 1` and `--repo` naming a scratch repository the test builds (with a second checkout)`

- Account for the legacy exception before switching the differential — both Python hooks call `_any_phase5_status` before branching. Until Task 47, a non-object file in an excluded directory can therefore decide a call before its newly scoped branch executes. Give this case and its readable control explicit expected outcomes at the earlier checkpoints and when the old traversal is removed.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `No decision moves: every surface already decides through the scan (Tasks 25 to 46).`

- Include shell calls in the timing bound — document, production, and state-file write targets do not exercise `codex-shell` or `agy-shell`. Add a real command on each shell, with and without a live root record, to the 20-run bounded scratch measurement. Otherwise slow shell decisions can pass Task 56.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the codex, agy and Claude hooks on the three targets of the root checkout`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `on all five surfaces: the decision is the one given with the tree absent`

- Separate filesystem path arguments from raw policy inputs — Tasks 4 and 6 demand equal answers for strings and `Path` objects even from `recorded_checkout` and `Scan.shell`. The stored checkout validator rejects non-strings, and a non-string command directory is unknown. Normalize internal filesystem paths at their boundary, preserve raw input validation, and test a usable checkout where the two classifications differ.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `each asserting that a `str` and a `Path` spelling of one fixture give equal answers`
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `a directory is known only as a string`

- Preserve independent environment arguments in Task 5 — the proposed bounded Git helper takes only argv, cwd, and budget. If it supplies the environment internally, removing that argument changes several calls together. Pass the environment through the helper from each bounded call site so each registered removal can affect its own pin.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `_bounded_git(argv, cwd, budget)`

- Make the timeout mutant terminate after its failure is detected — a timed thread join does not release the blocked worker. A non-daemon worker can keep pytest alive after the five-second assertion. Release the fake wait in `finally` and join the worker, or put it in a bounded disposable process.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `blocks on an event that is never set when it is given none`

- Exercise the missing precedence overlaps — Task 6 tests `checkout-match` with `target-match` but never with an unknown or matching command directory. Moving the directory checks above the session match can therefore leave every listed reason-order case green. Exercise the feasible directory overlaps and assert the winning reason.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › ``[checkout-match]` with the target in the named checkout (`target-match`)`

- Test the permissive direction of the bounded-run connection — both halves of Task 7’s pin require admission. A caller that treats every wrapper shape as valid can satisfy both. With the recorder removed, include a malformed wrapper whose inner command is admissible, assert refusal, and force the caller’s shape result to true to prove that assertion bites.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `its second half, with no recorder, admits `hmad-dispatch run --timeout 60 -- pytest``

- Use a Python 3.9-compatible writer type alias — the right-hand side of the `Step` assignment evaluates when the module loads. Postponed function annotations do not defer `dict | None` in that assignment. Use `Optional[dict]` there and include importing the writer in the interpreter controls.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `Step = Callable[[dict | None, Path], StepResult]`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `those are 3.9, 3.11, 3.12, 3.13, 3.14 and 3.15`

- Pass the feature key into the create step — for a missing record, its inputs are `None`, a store shared by multiple features, and a timestamp. Those inputs cannot supply the required `feature` property that `create_feature` currently writes. Bind the requested key and test two feature names against the same store.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `def _step_create(record: dict | None, store: Path, *, started_ts: str | None) -> StepResult: ...`

- Preserve the structured result of `drop_undeclared` — its library caller receives the exact removed keys. The proposed result retains only the final record and printable lines. A comma-separated diagnostic cannot distinguish a key containing a comma from two keys. Carry the removed keys out of the locked step and verify the existing library result.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `The library functions keep their signatures and wrap a one-step invocation.`

- Give Task 11 an available detector control — at its RED checkpoint the local writer and the extracted writer both reject undeclared fields. Substituting the local writer cannot make the observation fail there. Use a deliberately permissive scratch control at RED, or schedule the substitution after GREEN.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `Detector control, run once at RED: the same test with this tree's writer of Task 11 in place of the extracted one`

- Use the writer’s positional store argument in Task 13 — `main` declares `state_file` as a positional argument. Passing `--state-file` makes argparse exit before the membership check, including on the supposedly accepted store. Assert the refusal diagnostic and re-read both stores.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `once through the CLI (`--state-file`) and once through `merge_fields``

- Give the two seed pins independent assertions — the `[given]` pin cannot pass at RED if it requires the complete two-destination list before the resolved seed exists. Assert the given destination’s cardinality in its guard and the complete list in `[resolved]`, or change the RED split.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the exact list of destinations seeded: the given path and the resolved path, each once.`

- Specify the legacy reader adapter when Task 25 switches the judge — `_state_at` reports `not-a-regular-file` for a FIFO and `not-an-object` for either a non-object document or a malformed `orchestrator_state` map. `_state_status` raises for the first JSON shape but returns `unknown` for the malformed map. Preserve these separate outcomes through the shared reader and test the error token and exception path for each.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › ``judged_records` reads each file with `read_state`, takes its `live_records``
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › ``_state_at` and `_state_status` keep their names, arities and answers over it.`

- Correct Task 25’s production-write criterion — its blanket FR-4 refusal conflicts with the valid nonmatching linked and nested checkouts in its own parametrization. State the matching and nonmatching verdicts separately so an implementation that gates both cannot satisfy the criterion.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `every case of spec FR-4 still does`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `a record naming the main checkout does not apply in its linked worktree, and the reverse.`

- Label Task 29’s existing Claude connections as RED guards — Task 25 already scopes the `state` and `judge` callees, and Task 29 changes the outside-root listing route. Its in-root `[state]` and `[judge]` pins can pass before that edit. Assign their existing removal controls at RED and distinguish them from the new listing behavior.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the one shell change here is the out-of-root listing call`

- Verify the mutant-side refusal on removal A — its discriminating half normally expects an allow. A hook returning its catch-all denial also fails that assertion, even if the opposite half checks a valid baseline refusal. Capture the mutated outcome and require the intended branch diagnostic or another independent branch observation before crediting the kill.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `every test that kills an A row asserts the refusal's kind and the feature it names, not only that a refusal happened`

- Select the first eligible record for the FR-5 diagnostic — indexing `shell.applied` assumes that entry zero both applies and gates this shell. The status type promises only a tuple, and the new directory test supplies a single record. Specify a filtered, ordered tuple or select the eligible entry explicitly. Test an earlier nonmatching record and, in S9, an earlier planning record beside the gating one.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `applied=shell.applied[0]`

- Replace Task 47’s equivalent no-work-tree mutant — normal discovery already starts the streaming oracle there to learn that Git cannot answer. Starting it supplies no different observation. Mutate a second launch after the first failure and distinguish attempted starts from successfully launched children when Git is missing.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `at a root in no work tree the oracle is started`
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `At a root outside any git work tree the first process is the only one: its early end shows that.`

- Stage the agy planning guard when its mutant can act — at Task 48 agy still passes `every_stage`. With an applying planning record, the condition that every applying record is stage-exempt is false, so the named shell mutant cannot kill the agy guard. Move that ID to Task 50 and correct both tasks’ RED counts.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the shell ids observed failing under `shell-planning-hides-unreadable``

- Reverse Task 50’s planning-only unreadable expectation — with an unreadable file and only `applies=yes shell=no`, AC-8.1 requires both shells to refuse all three commands. Removing the unreadable file must change the safe-list and allow-line outcomes. Assert the refused outcomes and the clean twins separately.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `each command gets the decision it gets with the unreadable file removed, now that both shells exempt that record`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `the codex and agy shells refuse every command when no line says `shell=yes` or the file's top level is not an object`

- Assign Task 52 controls to the route that actually decides each guard — a non-arming command requiring an allow line is refused without that line even with the FR-5 classifier removed. Likewise, a stage-blind predicate cannot gate an other-checkout session whose record does not apply. Give those IDs allowance and applicability controls respectively, and name controls for the admitted writer-table rows before crediting all 43 guards.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › ``codex-arming-write-none` for the refused ones`

- Exercise checkout-bearing records from the mixed-schema writer — the `7a3cca48` writer merges submitted fields and validates against its sibling schema. With the new schema it can store a string checkout. Test both a field-free record and a record with an explicitly supplied usable checkout from matching and nonmatching sessions.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `a record the older writer leaves has no checkout field and must apply from every checkout`

- Test cross-lane owner recognition — `read_minted_owner` inspects one lane per call. A probe checking only the displayed lane passes the proposed local fixtures and misclassifies an ID minted in a different checked lane. Put the shared record in the first displayed lane and its only mint in a later checked lane, then assert one `minted` output row.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `on a real scratch git directory whose `h-mad-session-id.*` file names (or does not name) the record's owner`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › ``other` is an id no checked lane minted`

- Re-read state in the documented-command test — a command can emit the expected marker without changing the stage. After the mark and exit commands, reopen the scratch store and assert the resulting fields. For `exit-pending`, verify the live record is preserved.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `the documented mark and exit commands, run on a scratch store, print their `[H-MAD]` markers.`

- Record the command behind the filesystem-selector premise — Task 10 reports interpreter queries and the system-volume result without the invocations that produced them. Include the exact platform, selector/name query and observed answers beside the ruling so its evidence can be re-derived independently.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `it read 0 on the system volume of the machine of record`

## Should-fix

- Give every named mutation test a runnable spec header — the harness rejects a spec with a row-level `test` and no spec-level `target_command`. Convention 5 enumerates row keys but supplies neither that argv nor the baseline `command`. Specify both for the hand-authored first spec of each file, using an interpreter with pytest and the declared `h-mad/` working directory.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `Each row has the keys `name`, `_mechanism`, `file`, `find`, `replace` and `test``

- Make the simulated-Linux test run on Linux too — `monkeypatch.delattr` raises by default if the attribute is already absent. Remove `F_GETPATH` conditionally or with `raising=False` so the fallback runs on either host.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.impl-plan.md › `monkeypatch.delattr(fcntl, "F_GETPATH")`

## Nit

None
