Files changed:
- h-mad/SKILL.md
- h-mad/tests/mutation-specs/review_attribution_docs.json (new; six deletion mutations, each with its enclosing heading as symbol)

Implemented Task 17, Phase 5e GREEN:
- Phase-7 closure item 7 carries all WARNING lines, names the three warning codes, and specifies review_independence appends after 5e-review, 5e-verify and 6a-prime for every implementer.
- Attribution uses accepted implementation dispatches, with their TDD-IMPLEMENTER token / --agent (including claude), never implementer_switch.to or the routing implementer field. Durable implementation_authors alone supplies each module's complete author set and latest author; all three closed no-entry cases are explicit.
- The 5e bullet requires implementation_authors appends at GREEN acceptance and each accepted fix, before review. The 6a-prime bullet requires the same after accepted WITH_FIXES fixes. Both use the specified module/agent JSON form. The 5d bullet is unchanged.
- OD-1(A) remains test-local transcription only; no production attribution reader or helper was added.

pytest output (last 10 lines, required scoped -v run):
```text
                if errno_num != 0:
                    err_msg = os.strerror(errno_num)
                if err_filename is not None:
>                   raise child_exception_type(errno_num, err_msg, err_filename)
E                   PermissionError: [Errno 1] Operation not permitted: 'ps'

/opt/anaconda3/lib/python3.11/subprocess.py:1953: PermissionError
=========================== short test summary info ============================
ERROR h-mad/tests/test_h_mad_review_attribution_docs.py::test_transcription_is_tied_to_the_skill_text
========================= 12 passed, 1 error in 0.40s ==========================
```

Verification:
- Initial run: the task's exact six failures / six passes; all 56 mandated regression guards passed from the first run.
- Final task run: all 12 test bodies passed, including all five hostile-input transcription fixtures.
- Final regression run: all 83 test bodies passed across test_h_mad_archreview_pane_halt.py, test_h_mad_phase7_integrate_docs.py, test_h_mad_wiring_task_shape_docs.py, Task 16's test_h_mad_agy_authorship_docs.py, and Task 13's test_h_mad_new_caller_carveout_copies.py.
- Known sandbox artifact: the shared leak-reaper session teardown cannot execute ps (PermissionError); pytest therefore exits 1 with one teardown ERROR. Per coordinator instruction this is reported separately and is not a STATUS input.
- Production-only revert reproduced the same six named failures and six passes; restoration was verified by rerunning the scoped tests. A misplaced closure insertion during restoration was caught by that check, corrected, and reverified.
- git diff --check is clean. No tests were modified or weakened; no commit was created.
- Required new-spec --check-anchors: 6/6 valid.
- All repository mutation specs naming SKILL.md were checked: ANCHORS_OK specs=22 mutations=364 ok=364 drifted=0 unreadable=0 skipped=0 unclassifiable=0.
- Harness last line: `[H-MAD] anchors ANCHORS_OK`.
- Only --check-anchors mode was run. Full mutation scoring / MUTATION: ALL_CAUGHT is left to the orchestrator as explicitly directed; it is not claimed here.

Self-review findings: none outstanding. The unchanged negative 5d pin and existing documentation pins pass. Existing behavior was preserved; all requested new procedure text and six mutation rows are present. AC-7.3 retains OD-1(A)'s stated limit: the transcription checks what the prose selects, not whether an orchestrator applies it.

Concerns: none

🌱 graft saved ~62,839 tokens this turn, 1 call.
STATUS: DONE
