Files changed:
- h-mad/references/codex-implementer-prompt.md
- h-mad/tests/mutation-specs/implementer_neutral_prompt.json (new, four rows)

The opening names the Phase-5 implementer and preserves both template slots. The single Hook line names Codex, agy and all five class-(b) write tools, grok with no write-time gate, and Claude. The hook bullets and all other prompt content are unchanged. Existing RED tests were not modified. No commit was made.

pytest output (last 10 lines of the scoped GREEN run):
```text
h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate PASSED [100%]
h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate ERROR [100%]

==================================== ERRORS ====================================
_____ ERROR at teardown of test_hook_line_says_grok_has_no_write_time_gate _____
E   PermissionError: [Errno 1] Operation not permitted: 'ps'
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_implementer_neutral_prompt.py::test_hook_line_says_grok_has_no_write_time_gate
========================== 4 passed, 1 error in 0.16s ==========================
```
The displayed block includes the final blank separator lines as emitted. Command: hmad-dispatch run --timeout 120 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_implementer_neutral_prompt.py -v --tb=line

Regression output (last 10 lines):
```text
h-mad/tests/test_h_mad_extract_verdict.py::TestTheConcernShapeIsSpelled::test_both_codex_prompts_spell_the_label[codex-verifier-prompt.md] PASSED [100%]
h-mad/tests/test_h_mad_extract_verdict.py::TestTheConcernShapeIsSpelled::test_both_codex_prompts_spell_the_label[codex-verifier-prompt.md] ERROR [100%]

==================================== ERRORS ====================================
_ ERROR at teardown of TestTheConcernShapeIsSpelled.test_both_codex_prompts_spell_the_label[codex-verifier-prompt.md] _
E   PermissionError: [Errno 1] Operation not permitted: 'ps'
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_extract_verdict.py::TestTheConcernShapeIsSpelled::test_both_codex_prompts_spell_the_label[codex-verifier-prompt.md]
========================= 228 passed, 1 error in 8.64s =========================
```
Regression scope: test_h_mad_tdd_gate_docs.py, test_h_mad_portable_timeout.py, and TestTheConcernShapeIsSpelled::test_both_codex_prompts_spell_the_label in test_h_mad_extract_verdict.py. An initial selector without its enclosing class collected no tests; the corrected selector above was run successfully.

Self-review findings:
- Before editing, all four task tests failed on their intended properties: neutral opening, agy gate, agy tools, and grok status. No import or missing-symbol failures substituted for assertions.
- Regression guards passed from the first run: 226 assertions before editing. Final regression scope also includes two verdict-label cases: 228 assertions pass.
- Both template slots remain; exactly one Hook line remains; the line and its bullets have no angle brackets or ASCII arrows.
- Only two production-document lines changed; Task 13 content is preserved. Tests and census expectations were not weakened or restructured.
- All mutation rows name their enclosing heading: the document title for the opening, Context for Hook-line mutations.
- git diff --check passes.
- Hostile agent/human fixtures are not applicable: these tests read a static template and invoke no agent stub.

Known sandbox artifact (not a STATUS input): session leak-reaper teardown invokes ps, which the sandbox refuses. All test assertions passed; pytest exits 1 because of that teardown error. No fixture bypass was installed.

Mutation anchor verification:
Command: /opt/anaconda3/bin/python3 /Users/kimhawk/orca/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/implementer_neutral_prompt.json
```text
ANCHORS: implementer_neutral_prompt.json ok ok=4/4
ANCHORS: ANCHORS_OK specs=1 mutations=4 ok=4 drifted=0 unreadable=0 skipped=0 unclassifiable=0
[H-MAD] anchors ANCHORS_OK
```
Quoted last line: [H-MAD] anchors ANCHORS_OK
The full mutation harness was not run, as instructed. MUTATION: ALL_CAUGHT remains for coordinator scoring; it is not claimed here.

Census command: python3 docs/03-analysis/probes/agy-coder-fallback/census_doc_pins.py
Census tail:
```text
EXPECT-LITERALS[prompt-hook-block]: none
EXPECT-ABSENT[prompt-hook-block]: '<', '>'
EXPECT[prompt-hook-block]: OK
hand-found pins: listed in EXPECT; they are not derived by the >=16-character matcher
residual: short literals; space-free literals; run-time-built literals; negative assertions; structural locators
moved figures: distinct_literals, test_files
PROBE: FAIL
```
All named pin checks are OK. Numeric census: actual=27 distinct literals in 9 files; expected=23 in 8 files.

Blockers: The required census reports PROBE: FAIL because its expected numeric figures are stale. A control using git show HEAD:h-mad/references/codex-implementer-prompt.md, written to a temporary file with the same basename and passed through the probe's --prompt option, reports the identical 27/9 versus 23/8 discrepancy at HEAD 3eec301d7c29546e023b1ccb90ba792c272c5a1a. This task moved no literal pins or census counts. Per the dispatch's count-discrepancy stop rule, the probe and its expectations were left untouched. The implementation and mutation rows are ready, but a clean required census verdict needs coordinator reconciliation of that pre-existing mismatch.

Graft saved approximately 31,538 tokens in one call.

STATUS: BLOCKED
