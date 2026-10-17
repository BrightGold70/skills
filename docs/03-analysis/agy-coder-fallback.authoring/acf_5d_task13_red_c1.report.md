Files changed:
- h-mad/tests/test_h_mad_new_caller_carveout_copies.py (new; the only worktree change)

Summary: Phase 5d Task 13 is BLOCKED by the first-run count discrepancy. Expected 6 failed / 12 passed; observed 18 failed / 0 passed, plus the declared sandbox teardown error. Stopped without repairing or reconciling the unexpected failures, as the dispatch explicitly requires. No production files or mutation rows were modified.

Command:
`rtk proxy hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_new_caller_carveout_copies.py -v`

pytest output (last 10 lines):
```text
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[zero-L5]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[zero-L6]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L1]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L2]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L3]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L4]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L5]
FAILED h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L6]
ERROR h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L6]
========================= 18 failed, 1 error in 6.28s ==========================
```

Self-review findings:
- Read spec FR-9's quoted block and design FR-9's L1–L6 definitions. CANONICAL holds exactly the three sentences with quote wrapping removed.
- All six original-source locators successfully returned one span: each equivalence check reached its canonical-block count assertion and found zero copies.
- Six canonical-block failures are valid source-content assertion REDs, not missing-symbol errors. This dispatch has task shape new-behaviour, not wiring.
- The twelve locator controls are NOT accepted evidence: ten fail because their strict exception-message regex ends at `$`, while pytest appends assertion-rewrite detail after the intended message; two L4 cases fail earlier because the recovery token is in the third table cell and the locator correctly returns only the fourth/remedy cell.
- The passing-control obligation cannot be satisfied: zero tests passed. No passing test was weakened or forced to fail.
- The production paths have an empty git diff. Final git status lists only the new test file.
- Regression guards were not run because the dispatch requires stopping when the observed split differs. Their green status remains unverified for this dispatch.
- Mutation rows and sweeps are deferred to GREEN as instructed. No full suite was run.
- HMAD_STUB_HOSTILE is not applicable to these source-document and AST inspections: no agent/human runtime input or orca stub fixture is exercised.

RED acceptance evidence (one line per collected test; IDs below are in h-mad/tests/test_h_mad_new_caller_carveout_copies.py):
- test_copy_carries_the_canonical_block[L1]: FAIL, valid property assertion: "L1 (references/codex-implementer-prompt.md): expected exactly one complete FR-9 canonical three-sentence new-caller carve-out block; found 0". Invokes L1 -> _only and collapse; selects prompt RED item 1. No missing-symbol error.
- test_copy_carries_the_canonical_block[L2]: FAIL, valid property assertion: "L2 (references/codex-implementer-prompt.md): expected exactly one complete FR-9 canonical three-sentence new-caller carve-out block; found 0". Invokes L2 -> _paragraph -> _only and collapse; selects the WIRE-PIN paragraph. No missing-symbol error.
- test_copy_carries_the_canonical_block[L3]: FAIL, valid property assertion: "L3 (SKILL.md): expected exactly one complete FR-9 canonical three-sentence new-caller carve-out block; found 0". Invokes L3 -> titled_section -> _paragraph -> _only and collapse; selects the Phase-5 wiring block. No missing-symbol error.
- test_copy_carries_the_canonical_block[L4]: FAIL, valid property assertion: "L4 (references/failure-recovery.md): expected exactly one complete FR-9 canonical three-sentence new-caller carve-out block; found 0". Invokes L4 -> _only and collapse; selects the red_wrong_reason remedy cell. No missing-symbol error.
- test_copy_carries_the_canonical_block[L5]: FAIL, valid property assertion: "L5 (scripts/h_mad_assemble_tdd.py): expected exactly one complete FR-9 canonical three-sentence new-caller carve-out block; found 0". Invokes L5 -> _assembler_copy_nodes -> ast.parse/_only and collapse; selects the joined string constant inside assemble(). Does not execute assemble(), because this property concerns its source copy. No missing-symbol error.
- test_copy_carries_the_canonical_block[L6]: FAIL, valid property assertion: "L6 (references/codex-implementer-prompt.md): expected exactly one complete FR-9 canonical three-sentence new-caller carve-out block; found 0". Invokes L6 -> _paragraph -> _only and collapse; selects the GREEN paragraph. No missing-symbol error.
- test_locator_refuses_zero_or_many_spans[zero-L1]: FAIL unexpectedly. Invokes L1 -> _only on doctored source; correctly raises "L1: expected exactly one span, found 0", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[zero-L2]: FAIL unexpectedly. Invokes L2 -> _paragraph -> _only on doctored source; correctly raises "L2: expected exactly one span, found 0", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[zero-L3]: FAIL unexpectedly. Invokes L3 -> titled_section/_paragraph/_only on doctored source; correctly raises "L3: expected exactly one span, found 0", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[zero-L4]: FAIL unexpectedly at setup assertion `anchor in span`. Invokes L4 on original source only; the token belongs to the third cell, outside the returned remedy cell. Does not exercise doctored-source rejection. Invalid RED.
- test_locator_refuses_zero_or_many_spans[zero-L5]: FAIL unexpectedly. Invokes L5 -> _assembler_copy_nodes/_only on doctored source; correctly raises "L5: expected exactly one span, found 0", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[zero-L6]: FAIL unexpectedly. Invokes L6 -> _paragraph -> _only on doctored source; correctly raises "L6: expected exactly one span, found 0", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[two-L1]: FAIL unexpectedly. Invokes L1 -> _only on duplicated source; correctly raises "L1: expected exactly one span, found 2", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[two-L2]: FAIL unexpectedly. Invokes L2 -> _paragraph -> _only on duplicated source; correctly raises "L2: expected exactly one span, found 2", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[two-L3]: FAIL unexpectedly. Invokes L3 -> titled_section/_paragraph/_only with two blocks in one section; correctly raises "L3: expected exactly one span, found 2", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[two-L4]: FAIL unexpectedly at setup assertion `anchor in span`. Invokes L4 on original source only; the token belongs to the third cell, outside the returned remedy cell. Does not exercise doctored-source rejection. Invalid RED.
- test_locator_refuses_zero_or_many_spans[two-L5]: FAIL unexpectedly. Invokes L5 -> _assembler_copy_nodes/_only with two string constants in one assemble(); correctly raises "L5: expected exactly one span, found 2", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.
- test_locator_refuses_zero_or_many_spans[two-L6]: FAIL unexpectedly. Invokes L6 -> _paragraph -> _only on duplicated source; correctly raises "L6: expected exactly one span, found 2", but the strict pytest.raises message regex rejects appended assertion detail. Invalid RED for the intended passing control.

Concerns: First-run split is 18 F / 0 P rather than 6 F / 12 P due to defects in the new test's control assertions. Correcting the message-matching check and the L4 setup assertion is the next required work; no production change is needed to address those control defects. This dispatch stops here under its explicit discrepancy rule.

Sandbox artefact (not status-determining): the session leak-reaper teardown raises PermissionError invoking `ps -axo pid=,command=`. This is the declared environment error and was not modified or suppressed.

History lookup was attempted under the repository's OneContext instruction but is unavailable outside a OneContext dashboard session. The task is grounded in the supplied spec/design instead.

graft saved approximately 19,704 tokens this turn (1 call; no dollar estimate supplied).

STATUS: BLOCKED
