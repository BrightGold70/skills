AUDIT-agy-coder-fallback-impl-plan-v1-BEGIN
## Summary
The plan needs correction before 5d: its mandatory grammar and anchor checks cannot pass as written, and several gate, capture, and test contracts have gaps. The published M-2/M-3 censuses reproduced; the repository remains unchanged.

Evidence: 399 files opened (388 through scripted source/spec censuses), 15 greps run.

## Must-fix
- Update the grammar probe in Task 3 — The required post-GREEN probe cannot pass after the prescribed grammar change. In a read-only controlled pair, the committed probe returned PROBE: PASS for the current hook and PROBE: FAIL for Task 3's grammar, because it inserts another author group into the already-updated grammar. Add the probe to Task 3's edited files, make it validate the shipped grammar, and retain a failing control.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `must print `PROBE: PASS` under `/bin/bash` and `/opt/homebrew/bin/bash`.`
  quote: docs/03-analysis/probes/agy-coder-fallback/fr3_state_line_grammar.py › `new = old[: -len(OLD_TAIL)] + NEW_TAIL`
- Correct the mandatory anchor-check invocation — From the stated h-mad/ working directory, the documented script path resolves to h-mad/h-mad/scripts/h_mad_mutation_harness.py. Running it produced “can't open file” and exit 2; using scripts/h_mad_mutation_harness.py instead produced ANCHORS: ANCHORS_OK for heartbeat_beat.json. Choose one consistent working directory and executable/spec path convention for every Task.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `edited>` from `h-mad/` and require `ANCHORS: ANCHORS_OK`. A row the edit breaks is re-anchored in`
- Make ordinary agy self-check failures exit 0 — Task 5 assigns a nonzero exit to normal classifier or shell-policy FAIL verdicts consumed by the wiring check. That violates Audit-gate signal discipline. Print the explicit FAIL token on stdout and exit 0 for normal verdicts; reserve nonzero exits for operational errors, and test a policy FAIL separately from the missing-module fixture.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `nonzero exit, over the design's four checks (`view_file` in (a) and `call_mcp_tool` in (d);`
- Specify and pin the switch-record failure handling in Task 16 — Task 2 produces record=failed, but the documentation Task's staging requirement and test only require TDD-IMPLEMENTER: to appear. They do not require --record or the caller's mandatory step5:implementer_switch_unrecorded halt. A staging procedure that silently dispatches after a failed switch write satisfies those proposed assertions. Add the complete staging command, token branches, refusal to dispatch on record=failed, and a discriminating documentation control.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › ``TDD-IMPLEMENTER:` staging step. The teammate-audit bullet starting`
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › ``step5:implementer_switch_unrecorded`, because a switch that is not in state is exactly the`
- Require the complete real payload capture in Task 20 — The Task permits whatever subset of class-(b) tools happened to be observed and omits run_command from the capture contract. FR-8 requires one real toolCall per class-(b) tool and per run_command, including whether workspacePaths is present. Require all five path-write tools plus run_command, preserve their actual envelopes and capture commands, and fail the capture gate when a required sample is missing.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `   per class-(b) tool the capture observed: the captured payload, aimed at a production `.py``
  quote: docs/01-plan/features/agy-coder-fallback.spec.md › `1. **Payload capture.** A temporary capture hook records one real `toolCall` per class-(b) tool`
- Derive Task 20's RED split from the captured keys — The claim that every captured tool's key is absent at RED is not established: Task 5 already supplies write_to_file -> TargetFile. If that is the observed hook key, its captured-payload test already passes after Tasks 6–7. Record known-key cases as regression passes, count only genuinely new mappings as failures, and permit a capture-only gate when no mapping changes. Otherwise a correct baseline violates the dispatch's declared RED contract.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `**RED split**: item 1 has one node per observed tool, and each fails at RED (its key is not in`
- Add the converse wiring mutation for Task 10 — The planned wire-cut checks removal of the check subprocess, but no mutation forces the agy-only check to run for codex/grok. Connection enforcement explicitly requires both directions. Add that mutation and name the negative fixture that kills it (an existing Codex/grok regression may suffice), proving those agents continue when the agy hook is unwired; update the mutation ledger accordingly.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `| `wire-check-not-run` (wire-cut) | the check subprocess call deleted, the check and `assemble` kept | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_agy_runs_the_wiring_check_before_assembling` |`
- Require an H-MAD marker for the new halt transition — Task 10 specifies the new HALT output and its early returns, but supplies neither an [H-MAD] marker there nor a caller obligation to emit one when consuming it. That leaves the new halt without the log marker required by Marker discipline. Specify the marker at the actual transition, preserve the machine-readable verdict token, and pin the marker in the halt-path tests.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `prompt, exit 0; `UNREADABLE` → the same two lines, exit 2; no `AGY-GATE:` line or a timeout →`
- Make Task 11's same-key assertion discriminate against argparse — The listed assertions already hold before --append exists: the current writer exits 2, includes the supplied key in “unrecognized arguments: --append …”, and never opens the store. I reproduced that rejection without creating the control state file. Require the exact same-key conflict diagnostic, not merely the key, and use the existing non-append-only array production_paths_needing_red_tests so APPEND_ONLY cannot mask removal of the conflict guard.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `   — exit 2, stderr names the key, store unchanged.`

## Should-fix
- Separate status fixture IDs from resolver reason values — Task 2 labels the causes status-unavailable/status-exhausted and says reason equals the cause, while the agreed reason enum contains only env/status/cli-absent. State explicitly that both status fixtures expect reason == "status"; otherwise a literal implementation of the test instructions conflicts with the persisted switch schema.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `   `cli-absent`; `reason` equals that cause. 4 nodes.`
  quote: docs/02-design/features/agy-coder-fallback.design.md › `  `["codex", "agy", "grok", "claude"]`, `reason` takes `enum` `["env", "status", "cli-absent"]`, and`
- Close OD-2 before handing Task 6 to an implementer — The supposedly unread directory behavior is directly observable: canonicalise(root, ".", root) and an existing directory both returned unresolvable=False and names=() in this checkout. Under the prescribed T6 sequence that reaches allow. Decide whether that behavior is retained or refused, document the result, and add the corresponding fixture instead of carrying an unspecified decision into 5e.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `from its `resolved.names`, are unread. This Task adds no fixture for it and does not design it.`
- Account for both changed timeout tests in Task 22's RED contract — When the derived default differs from 1500, Task 22 updates both the parametrized default-timeout test and test_agent_agy_wired_writes_the_prompt, whose Task 10 assertion also pins --timeout 1500. If both new expectations land at RED, two node IDs fail, not one. State the staging exception explicitly if the second expectation is intended to move only at GREEN; otherwise correct the split to two failures.
  class: build
  quote: docs/01-plan/features/agy-coder-fallback.impl-plan.md › `**RED split**: 1 F, or 0 when the derived figure is 1500.`

## Nit
None

🌱 graft saved ~104,339 tokens this turn (10 calls).
AUDIT-agy-coder-fallback-impl-plan-v1-END
