# agy-coder-fallback — Tasks 18 (pre-merge re-measurement) and 19 (incident replay)

Measured by the orchestrator at `3236ade6` (Task 17 GREEN), outside the sandbox.

## Task 18
```
READING: line=10 strings=5 comments=0 text=5 joined=10 union=10 unparsed=0
UNION: h-mad/SKILL.md
REVIEW: OK sha256=f8413f73eb7d155d1b6a49bfa36ff446fbae1c63cf3424b7bc1ee139bf36308f :: RULE WITH CARVE-OUT: line 500 includes caller-created, callee-resolves, name-both and call-only wire-cut condition
UNION: h-mad/references/codex-implementer-prompt.md
REVIEW: OK sha256=98cbbab1bb1e9b6fef835ec7f0d1e8d75f781bf883720c8904609d7c8711ae49 :: RULE WITH CARVE-OUT: all three copies, lines 60, 68 and 72, carry the full three-sentence block individually.
UNION: h-mad/references/failure-recovery.md
REVIEW: OK sha256=e08033f2e9ac2aa233486e740d889cdf1b27085f0764b37b10e1f2c9904030fe :: RULE WITH CARVE-OUT: the line 36 remedy contains the full block.
UNION: h-mad/scripts/h_mad_assemble_tdd.py
REVIEW: OK sha256=ecb14c4aa31e42254c886869902b625f3b027daaecc6c08a5bd3e7068a798468 :: RULE WITH CARVE-OUT: the joined wiring header at lines 477-483 contains the full block after its general prohibiti
UNION: h-mad/tests/fixtures/codex-text-8-exec.log
REVIEW: OK sha256=cc0843bf8790c04f83c5fd4a0f06247f165b92abbb733873954200ac7252055b :: NO GENERAL RULE: line 974 describes one existing-caller recorder test's len(calls) assertion in captured output, n
UNION: h-mad/tests/mutation-specs/new_caller_carveout_copies.json
REVIEW: OK sha256=de2c68a37ae31c71117e5c54535989cb0a704062b60ace56d206a69d13848b3b :: MUTATION DATA: find/replace pairs deliberately damage individual carve-out sentences; these are negative controls,
UNION: h-mad/tests/test_h_mad_agent_definitions.py
REVIEW: OK sha256=86b40df7c613ec0b7d80267e581f884ec74b50e4df30347801cbb90854c9b8f8 :: NO BLANKET RULE: line 77 pins new-symbol import-shaped RED wording; it does not forbid the new-caller carve-out.
UNION: h-mad/tests/test_h_mad_new_caller_carveout_copies.py
REVIEW: OK sha256=61f337263e106b5451506642ec76f3ea78267faf3c48725288d725a32ee3e66d :: RULE WITH CARVE-OUT: CANONICAL at lines 16-21 contains the full block; the six locators require each individual co
UNION: h-mad/tests/test_h_mad_wire_pin_gate.py
REVIEW: OK sha256=c475e310a0802e46b390f5bacf62d8b6f3a985987c19a2baf135ceb0873a5112 :: NO GENERAL RULE: lines 576-582 explain scaffolding for an existing caller's registration assertion; they prescribe
UNION: h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py
REVIEW: OK sha256=a093daa2d47684990ca0a3911010baa877c7f279161153ee1b68825916785837 :: RULE WITH CARVE-OUT: new_rule at lines 56-62 requires caller AND callee resolution; old_rule is explicitly Before 
PROBE: PASS
--control → PROBE: FAIL
HEAD: 3236ade63000759101b8d5de7e4bdc1558329b73
M-2/hooks/h-mad-tdd-gate.sh/rows: computed=62 expected=56 MOVED
M-2/scripts/h_mad_tdd_judge.py/rows: computed=41 expected=36 MOVED
M-2/hooks/h-mad-codex-tdd-gate.py/rows: computed=35 expected=62 MOVED
M-2/scripts/h_mad_assemble_tdd.py/rows: computed=65 expected=60 MOVED
M-2/scripts/h_mad_phase7_preconditions.py/rows: computed=16 expected=12 MOVED
M-2/scripts/h_mad_hook_wiring.py/rows: computed=18 expected=10 MOVED
M-2/scripts/h_mad_state_write.py/rows: computed=26 expected=21 MOVED
M-2/scripts/h_mad_target_identity.py/rows: computed=46 expected=15 MOVED
M-3/rows: computed=10 expected=8 MOVED
M-4/moved-rows: computed=0 expected=31 MOVED
M-4/absent-anchors: computed=0 expected=0 OK
M-4/non-unique-anchors: computed=0 expected=0 OK
PROBE: FAIL
DO-1a files: computed=7 expected=6 MOVED
DO-1a/four-pattern files: computed=12 expected=7 MOVED
prompt distinct literals: actual=27 expected=23
prompt test files: actual=9 expected=8
total names: computed=58 expected=58 OK
PROBE: PASS
```

- AC-9.1: union = 10 files, `unparsed=0`; every hit carries a sha256-pinned hand reading; every
  rule-stating hit is one of the six FR-9 copies and carries the carve-out; the other hits are
  fixtures, the mutation spec and tests. **Met.**
- Census readings: `PROBE: FAIL` against the 4e4b5ded EXPECT is by construction (Tasks 1–17 add
  rows and pin files). M-4 `moved-rows=0` (**met**; Codex-gate rows 35 = 31 kept + 4 Task 4;
  identity 46 = 15 + 31 moved). Doc pins 27 literals / 9 files = D5d-6. Class inventory PASS.
- `review_independence_unrecorded` over the edited files: SKILL.md:346, SKILL.md:354,
  h_mad_phase7_preconditions.py:143 — none states the trigger as agy-only. **Met.**

## Task 19
```
HEMASUITE_HEAD: ad9b7abcea58baae5ac0244ceb215f00b5f5de67
CASE: T4 WIRE-PIN 1 task=531a6296b caller=resolve_registry_notebook callee=registry_arm_notebook_id
MEASURED: direct-parent-RED failed=True passed=False exception="AttributeError: module 'tools.notebooklm_integration' has no attribute 'resolve_registry_notebook'"
RECORD direct: exception="AttributeError: module 'tools.notebooklm_integration' has no attribute 'resolve_registry_notebook'" callee_resolves=True old=halt new=valid reproduced=True
RECORD scaffold: not applicable; committed T4 pin is the direct form
MEASURED: committed-task-GREEN-control failed=False passed=True exception=''
MEASURED: committed-task-wire-cut-RED failed=True passed=False exception='AssertionError: resolver must call the real registry arm exactly once with the project record'
RECORD wire-cut: green=True caller_and_callee_kept=True exception='AssertionError: resolver must call the real registry arm exactly once with the project record' reproduced=True
RECORD citation: evidence=M4.1 located=True
CASE RESULT: T4 WIRE-PIN 1 reproduced=True
CASE: T5 WIRE-PIN 1 task=7aa0d9dec caller=initialize_project_notebook callee=resolve_registry_notebook
MEASURED: direct-parent-RED failed=True passed=False exception="AttributeError: module 'tools.notebooklm_integration' has no attribute 'initialize_project_notebook'"
RECORD direct: exception="AttributeError: module 'tools.notebooklm_integration' has no attribute 'initialize_project_notebook'" callee_resolves=True old=halt new=valid reproduced=True
MEASURED: committed-scaffold-parent-RED failed=True passed=False exception='AssertionError: initialize must reach resolve_registry_notebook exactly once with (\'p\',); captured outcome=TypeError("\'NoneType\' object is n
RECORD scaffold: exception='AssertionError: initialize must reach resolve_registry_notebook exactly once with (\'p\',); captured outcome=TypeError("\'NoneType\' object is not callable")' old=valid reproduced=True
MEASURED: committed-task-GREEN-control failed=False passed=True exception=''
MEASURED: committed-task-wire-cut-RED failed=True passed=False exception="AssertionError: initialize must reach resolve_registry_notebook exactly once with ('p',); captured outcome=InitializeResult(project='p', notebook=
RECORD wire-cut: green=True caller_and_callee_kept=True exception="AssertionError: initialize must reach resolve_registry_notebook exactly once with ('p',); captured outcome=InitializeResult(project='p', notebook='111111
RECORD citation: evidence=M5.1 located=True
CASE RESULT: T5 WIRE-PIN 1 reproduced=True
CASE: T6 WIRE-PIN 2 task=c2d671f6b caller=generate_setup_report callee=resolve_registry_notebook
MEASURED: direct-parent-RED failed=True passed=False exception="AttributeError: 'NotebookLMIntegration' object has no attribute 'generate_setup_report'"
RECORD direct: exception="AttributeError: 'NotebookLMIntegration' object has no attribute 'generate_setup_report'" callee_resolves=True old=halt new=valid reproduced=True
MEASURED: committed-scaffold-parent-RED failed=True passed=False exception='AssertionError: status report must resolve its project via registry_arm_notebook_id exactly once'
RECORD scaffold: exception='AssertionError: status report must resolve its project via registry_arm_notebook_id exactly once' old=valid reproduced=True
MEASURED: committed-task-GREEN-control failed=False passed=True exception=''
MEASURED: committed-task-wire-cut-RED failed=True passed=False exception='AssertionError: status report must resolve its project via registry_arm_notebook_id exactly once'
RECORD wire-cut: green=True caller_and_callee_kept=True exception='AssertionError: status report must resolve its project via registry_arm_notebook_id exactly once' reproduced=True
RECORD citation: evidence=WIRE 2 located=True
CASE RESULT: T6 WIRE-PIN 2 reproduced=True
AC-9.3: cases=3 reproduced=3 non_reproduced=0
PROBE: PASS
```

- AC-9.3: 3 cases reproduced, 0 non-reproduced. **Met.** HemaSuite HEAD and its pre-existing dirty
  status (76 lines) unchanged across the run: `git archive` exports only.
