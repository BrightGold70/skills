# agy-coder-fallback — 5d Task 4 record

Codex GREEN `STATUS: DONE`; its mutation baseline could not run in the sandbox (leak-reaper `ps`
teardown), so every sweep below was scored by the orchestrator outside the sandbox.

- Move audit (`ast` source segments, HEAD gate vs identity module): 24 of 25 byte-identical; the
  one diff is the plan's `_load_identity().fold_py_suffix` → `fold_py_suffix`. None of the 25
  still defined in the gate.
- Tests: shared-policy + Codex gate judge + runtime + target identity + mutation harness →
  `448 passed`. `fr6_import_failure_pair.py` → `PROBE: PASS`.
- `ANCHORS_OK` 7 specs 86/86. All 7 specs `MUTATION: ALL_CAUGHT`:
  codex_gate_judge_wiring 45/45 (`crash_kills=0`: `CX-FOLD`, `CX-FORCE-SCRIPT` die by assertion),
  codex_gate_shell_allowance 9/9, codex_gate_tmp_reports 4/4, assemble_tdd_mutation_rows 5/5,
  tdd_gate_differential 8/8, target_identity 11/11, shared_gate_policy 4/4 (symbols set).
- Revert probe (HEAD gate + identity): `29 failed` = RED split; restored `29 passed`.
- Post-move census (`census_mutation_rows.py`): `M-4/moved-rows=0` (plan target: 0 Codex-gate
  rows inside a moved span); Codex-gate rows 62 → 31; absent/non-unique anchors 0. `PROBE: FAIL`
  against the 4e4b5ded EXPECT is by construction (M-4 measures the pre-move gate).
