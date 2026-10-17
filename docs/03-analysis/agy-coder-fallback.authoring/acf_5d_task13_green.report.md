Files changed:
- h-mad/references/codex-implementer-prompt.md
- h-mad/SKILL.md
- h-mad/references/failure-recovery.md
- h-mad/scripts/h_mad_assemble_tdd.py
- h-mad/tests/mutation-specs/new_caller_carveout_copies.json

Summary:
Inserted the verbatim FR-9 three-sentence canonical block immediately after each of the six specified context sentences. L5 changes "symbol." to "symbol. " and adds adjacent literals, retaining "never a missing". Added eight mutation rows: fr9-copy-L1 through fr9-copy-L6 and fr9-L4-sentence-2/3. Every row has a symbol pin, a uniquely matching find, the specified minimal replacement, and the named canonical-block test. No test files or existing mutation rows changed.

pytest output (last 10 lines, target GREEN run):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_new_caller_carveout_copies.py::test_locator_refuses_zero_or_many_spans[two-L6]
========================= 18 passed, 1 error in 0.28s ==========================
```

pytest output (last 10 lines, regression guards after implementation):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_assemble_tdd.py::TestReferencedGlobalSections::test_the_cli_reports_inlined_and_unresolved_under_the_pass_line
========================= 190 passed, 1 error in 8.59s =========================
```

Commands:
- hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_new_caller_carveout_copies.py -v
- hmad-dispatch run --timeout 600 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agent_definitions.py h-mad/tests/test_h_mad_wiring_task_shape_docs.py h-mad/tests/test_h_mad_assemble_tdd.py -v

Evidence:
- Before edits: exact expected RED split, 6 failed / 12 passed; all failures name the absent canonical block, not an import or missing symbol. All 190 regression assertions passed on their first run.
- After edits: 18 target assertions passed and all 190 regression assertions passed.
- Known sandbox artefact, reported once: both pytest sessions exit 1 solely because leak-reaper teardown invokes ps and receives PermissionError. Per coordinator instruction, this does not decide STATUS; no fixtures or tests were changed to suppress it.
- New-spec command: /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/new_caller_carveout_copies.json
- Its last line: [H-MAD] anchors ANCHORS_OK
- Its scored summary: ANCHORS: ANCHORS_OK specs=1 mutations=8 ok=8 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Discovered every existing spec naming SKILL.md, references/failure-recovery.md, or scripts/h_mad_assemble_tdd.py and checked all 24 specs: ANCHORS: ANCHORS_OK specs=24 mutations=404 ok=404 drifted=0 unreadable=0 skipped=0 unclassifiable=0
- Existing specs checked: archreview_done_marker_recovery, assemble_tdd, assemble_tdd_agent, assemble_tdd_agy, assemble_tdd_env_known, assemble_tdd_mutation_rows, author_done_line, author_report_path, baseline_sha, batch_doc_rules, context_budget_docs, delta_stage, doc_block_exec, fill_slots, grok_wire_reverts, hook_wiring, host_runtime_docs, orchestrator_freeze_and_document, phase7_integrate_blockers_documented, probe_hygiene_and_h8_extensions, resume_decision_cannot_judge, skill_body_renderer_args, tail_signature_pass, wire_registry_key.
- Drift: none. Existing advisory messages concern pre-existing self-matching/unpinned rows; no rows were changed.
- git diff --check passed.
- No unscoped test run. No harness execution without --check-anchors. The coordinator must score the eight rows individually outside the sandbox; MUTATION: ALL_CAUGHT is not claimed here.

Self-review findings:
- All six locators select their intended copy and find the complete canonical block exactly once.
- The 12 zero/two-span controls still pass; tests were not weakened.
- All four production files remain within scope and retain the existing doc-pin sentences.
- The assembler edit is confined to the specified wiring lines.append(...) string, preserving Task 10's existing implementation.
- Reviewed all eight mutation rows and the complete production diff.
- No code concerns found. OneContext history lookup was attempted under workspace instructions but is unavailable outside its dashboard environment.

Concerns: none

🌱 graft saved ~63,922 tokens this turn, 2 calls.
STATUS: DONE
