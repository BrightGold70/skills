Files changed:
- h-mad/tests/test_h_mad_implementer_neutral_prompt.py (new; four test nodes)

Pytest output (last 10 lines of the scoped RED run):
```text
E       assert 'grok' in "Hook: Codex's `h-mad-codex-tdd-gate.py` guards `apply_patch` and shell writes; Claude's `h-mad-tdd-gate.sh` guards `Write` and `Edit`. Both are ARMED during this phase and block production-code writes unless:"

h-mad/tests/test_h_mad_implementer_neutral_prompt.py:37: AssertionError
=========================== short test summary info ============================
FAILED h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_prompt_opening_names_no_implementer
FAILED h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_names_the_agy_gate
FAILED h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_names_the_agy_write_tools
FAILED h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate
ERROR h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate
========================== 4 failed, 1 error in 0.19s ==========================
```

Command:
`hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_implementer_neutral_prompt.py -v`

Regression guards:
`hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_tdd_gate_docs.py h-mad/tests/test_h_mad_extract_verdict.py::TestTheConcernShapeIsSpelled::test_both_codex_prompts_spell_the_label h-mad/tests/test_h_mad_portable_timeout.py -v --tb=short`

Result: `228 passed, 1 error in 8.05s`. All guard assertions passed on their first collected run; no guard was modified or forced to fail.

Known sandbox artifact (reported once): both sessions end with the existing leak-reaper teardown ERROR at conftest.py:183 / leak_reaper.py:34 because executing `ps` raises `PermissionError: [Errno 1] Operation not permitted`. As directed, this is not an input to STATUS. Scoped RED assertions are exactly 4 failing, 0 passing.

Self-review findings:
- RED-only scope satisfied: the sole repository change is the new test file. No production files, existing tests, mutation specifications, or commits were changed/created.
- Opening pin checks the first line starting `You are`, requires `the Phase-5 implementer`, rejects Codex/agy/grok/Claude case-insensitively, and preserves both template slots.
- Each Hook pin invokes the existing `_hook_block(text).splitlines()[0]`, so clauses appearing only in bullets cannot satisfy it. All five agy class-(b) tool names are individually asserted.
- Each requested acceptance property has a corresponding test. Mutation verification and production changes belong to GREEN and were not performed.
- `git diff --check` passed; final `git status --short` listed only the new test file.
- HMAD_STUB_HOSTILE is not applicable: these are direct pins against the committed prompt, with no agent/human fixture payload, stub invocation, subprocess input, or synthetic document fixture.

RED acceptance evidence (one line per test):
- `test_prompt_opening_names_no_implementer`: ordinary document assertion RED, not a missing-symbol or wiring failure; message `Prompt opening must name the Phase-5 implementer` names the tested property. Invokes `IMPLEMENTER_PROMPT.read_text(encoding="utf-8")` and inspects the actual first `You are` line; the same test asserts all implementer exclusions and both slots after GREEN.
- `test_hook_line_names_the_agy_gate`: ordinary document assertion RED; message `Hook line must name agy's h-mad-agy-tdd-gate.py gate` names the tested property. Invokes `_hook_block` on `IMPLEMENTER_PROMPT.read_text(...)`, takes only its first line, and asserts the gate on that actual line.
- `test_hook_line_names_the_agy_write_tools`: ordinary document assertion RED; message `Hook line must name agy for its class-(b) write tools` names the tested property. Invokes `_hook_block` on the actual prompt and takes only its first line; the same test then individually asserts `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `sed_file`, and `notebook_edit`.
- `test_hook_line_says_grok_has_no_write_time_gate`: ordinary document assertion RED; message `Hook line must name grok's write-time gate status` names the tested property. Invokes `_hook_block` on the actual prompt and takes only its first line; the same test also asserts the exact phrase `no write-time gate` after GREEN.

Passing-new-test vacuity review: no new test passed. Existing guard tests were left intact; they protect previously shipped behavior independently of the new FR-9/FR-10 requirements. These are document-pin tests, so no production method is invoked: their target is the prompt content itself, read directly from its production path.

Execution notes: initial concurrent invocations collected no tests: the scoped attempt refused with `SUITE: BUSY` while the guard attempt rejected the abbreviated node below. After both processes exited and the lock disappeared naturally, runs were repeated sequentially; no lock was deleted or bypassed. OneContext history was attempted per workspace policy but is unavailable outside its dashboard; repository evidence was sufficient.

Concerns: The dispatch's regression node `test_h_mad_extract_verdict.py::test_both_codex_prompts_spell_the_label` does not exist at module scope and collects zero tests. The actual node is nested under `TestTheConcernShapeIsSpelled`; both parametrized cases passed when run with the class-qualified node shown above. The coordinator should correct that node in future dispatches. RED work is complete; no code blocker remains.

Summary: added four meaningful document pins and verified four expected assertion failures, with all 228 named regression guard cases passing. Production remains unchanged for Phase 5e.

🌱 graft saved ~28,612 tokens this turn, 2 calls.

STATUS: DONE_WITH_CONCERNS
