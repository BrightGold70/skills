Files changed:
- `h-mad/hooks/h-mad-codex-tdd-gate.py`
- `h-mad/scripts/h_mad_target_identity.py`
- `h-mad/tests/mutation-specs/assemble_tdd_mutation_rows.json`
- `h-mad/tests/mutation-specs/codex_gate_judge_wiring.json`
- `h-mad/tests/mutation-specs/codex_gate_shell_allowance.json`
- `h-mad/tests/mutation-specs/tdd_gate_differential.json`
- `h-mad/tests/mutation-specs/shared_gate_policy.json`

pytest output (last 10 lines), required scoped GREEN command:
`hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_shared_gate_policy.py -v`

```text
/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=============================== warnings summary ===============================
h-mad/tests/test_h_mad_shared_gate_policy.py::test_each_moved_function_has_one_definition_in_the_identity_module[_contained_venv_executable]
  h-mad/tests/test_h_mad_check_memory_index.py:63: DeprecationWarning: invalid escape sequence '\w'
    """Re-derive the contract rather than trusting the transcription.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_shared_gate_policy.py::test_codex_gate_self_check_parser_fail_is_a_verdict_with_exit_0
==================== 29 passed, 1 warning, 1 error in 4.97s ====================
```

Regression guards, unchanged, first run before production edits:
`176 passed, 1 error in 105.89s (0:01:45)`

Regression guards after GREEN (last 10 lines):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_codex_runtime.py::test_codex_hook_admits_mutation_harness_only_for_check_anchors
176 passed, 1 error in 105.50s (0:01:45)
```

Self-review findings:
- Confirmed RED: exactly 29 failing tests, zero passing tests, before production edits.
- GREEN: all 29 shared-policy test bodies pass; all 176 existing Codex gate/runtime test bodies pass both before and after edits.
- Moved all 17 functions and 8 constants into h_mad_target_identity.py. Source comparison against HEAD proves each definition is byte-for-byte unchanged, including decorators, except the specified _is_production_python fold_py_suffix substitution.
- The gate binds all 25 imported objects directly. The guarded import records _POLICY_IMPORT_ERROR; _main_guarded first re-raises it into main's existing M:G2 exception handler.
- Self-check policy-import failure prints its token on stderr and returns 2 before any policy probe. Parser and shell-policy verdict failures print on stdout and return 0.
- _load_identity, _relative_target, _tmp_report_target, _command_cwd, main's unsafe tuple, and _main_guarded's remaining composition are unchanged.
- All pre-existing identity definitions and all three scoped test files are unchanged. No test was added, weakened, or bypassed during GREEN.
- Both production files compile. git diff --check passes.
- Refreshed the ignored local graft cache. No unrelated tracked files changed.

Re-pointed rows (31 total):
- `assemble_tdd_mutation_rows.json`: `CX-MUT-ANCHORS`, `CX-MUT-WITHIN`.
- `codex_gate_judge_wiring.json`: `G1`, `G3`, `G4`, `G6`, `G6B`, `G7`, `G8`, `G6C`, `G9`, `G10`, `G11`, `CX-FOLD`, `CX-FORCE-SCRIPT`, `CX-SAFE`, `CX-EQ`, `CX-OPT-LONG`, `CX-OPT-SHORT`, `CX-RUN`, `CX-RUN-INNER`, `CX-RUN-TIMEOUT`, `F2-ESCAPE`.
- `codex_gate_shell_allowance.json`: `lexical-subset-dropped`, `executable-not-resolved`, `prefix-reduced-to-executable`, `malformed-line-skipped`, `unreadable-read-as-empty`, `guard-is-case-sensitive`.
- `tdd_gate_differential.json`: `DIFF-DOCS-CX-OFF`, `DIFF-DOCS-CX-ANYPART`.

CX-FOLD's find now calls fold_py_suffix directly. CX-FORCE-SCRIPT's replacement now calls canonical_directory directly. Both replacements compile and reference names available in the identity module; assertion kill scoring for these rows remains for the coordinator's existing-spec sweep.

New shared_gate_policy.json rows, all with symbol pins:
- fr6-import-guard-dropped — <module>.
- fr6-self-check-policy-import-branch-dropped — main.
- codex-selfcheck-shell-policy-exits-2 — main.
- codex-selfcheck-parser-exits-2 — main.

Anchor checks across all seven requested specs:
```text
ANCHORS: codex_gate_judge_wiring.json ok ok=45/45
ANCHORS: codex_gate_shell_allowance.json ok ok=9/9
ANCHORS: codex_gate_tmp_reports.json ok ok=4/4
ANCHORS: assemble_tdd_mutation_rows.json ok ok=5/5
ANCHORS: tdd_gate_differential.json ok ok=8/8
ANCHORS: target_identity.json ok ok=11/11
ANCHORS: shared_gate_policy.json ok ok=4/4
ANCHORS: ANCHORS_OK specs=7 mutations=86 ok=86 drifted=0 unreadable=0 skipped=0 unclassifiable=0
```
The existing CX-EQ self-matching advisory remains; 82 legacy rows lack symbol pins. All four new rows have pins. target_identity.json's 11 anchors remain unique, so no re-anchor was necessary in this checkout. codex_gate_tmp_reports.json remains unchanged.

Requested standalone shared-spec anchor command:
`/opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/shared_gate_policy.json`
Last line:
```text
[H-MAD] anchors ANCHORS_OK
```

Requested shared-spec mutation run, and no other full mutation sweep:
`hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/shared_gate_policy.json`
```text
MUTATION: BASELINE_NOT_GREEN
  the suite was already red before any mutation, so every mutation would 'fail' and the report would read as a clean sweep. Get to green first (halt `step5e:mutation_unverified:<module>`).
[H-MAD] shared_gate_policy mutation BASELINE_NOT_GREEN
```

Committed FR-6 probe, run from repository root:
```text
timeout-tree/unmodified: rc=0 stdout=judge-timeout want=judge-timeout err=
timeout-tree/new-module: rc=1 stdout=none want=none err=ModuleNotFoundError: No module named 'h_mad_gate_policy'
error-tree/unmodified: rc=0 stdout=judge-error want=judge-error err=
error-tree/G2-mutant: rc=1 stdout=none want=none err=ModuleNotFoundError: No module named 'h_mad_target_identity'
PROBE: PASS
```

Re-ran census_mutation_rows.py --root h-mad. Post-move reading:
```text
M-4/total-rows: computed=31 expected=62 MOVED
M-4/moved-rows: computed=0 expected=31 MOVED
M-4/absent-anchors: computed=0 expected=0 OK
M-4/non-unique-anchors: computed=0 expected=0 OK
```
The census intentionally retains the pre-move 4e4b5ded expectations and prints PROBE: FAIL after this move; its requested post-move measurement is zero. Its overall verdict was also FAIL before this task due to earlier-task changes outside M-4. The probe was not edited.

Concerns: The documented sandbox-only leak-reaper teardown raises PermissionError when invoking ps. All scoped test assertions pass, but pytest exits 1 for teardown, so the requested mutation harness refuses its baseline before applying any mutant. No MUTATION: ALL_CAUGHT claim is made. The coordinator must rerun shared_gate_policy.json outside the sandbox and score the other six existing specs, including assertion kills for CX-FOLD and CX-FORCE-SCRIPT. Per the dispatch's explicit instruction, this known sandbox artifact does not decide STATUS. No implementation issues were found.

🌱 graft saved ~38,578 tokens this turn (5 calls, including cache refresh).
STATUS: DONE
