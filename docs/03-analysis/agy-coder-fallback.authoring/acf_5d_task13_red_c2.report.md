# Task 13 RED — correction cycle 2

Changed only `h-mad/tests/test_h_mad_new_caller_carveout_copies.py`, inside `test_locator_refuses_zero_or_many_spans` (the twelve parametrized controls).

- Replaced the anchored exception regex with `re.escape(f"{name}: expected exactly one span, found {expected}")`, searched without a `$` anchor so pytest assertion-rewrite detail is accepted.
- L4 takes its doctoring anchor from the returned 5d remedy cell (`span.strip()`), identifies its unique source row using that text, and removes or duplicates that row to produce zero or two genuine L4 matches.
- The two-L6 setup now duplicates only the selected GREEN paragraph in place, using the same bounded paragraph duplication as L3. Direct inspection of the original setup already yielded two L6 spans and the proper refusal. The pytest traceback confirms there was no separate two-L6 setup ERROR; see the sandbox note below.
- Each raises context contains only `locate(doctored)`. If that call returns instead of refusing, pytest fails with DID NOT RAISE. No control fabricates a refusal or catches a setup assertion as success.

Verification counts:

| Run | Failed | Passed | Errors |
| --- | ---: | ---: | ---: |
| Targeted RED | 6 | 12 | 1 |
| Three regression guards | 0 | 190 | 1 |

Targeted command (executed through `rtk proxy`):
`/opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_new_caller_carveout_copies.py -q -p no:cacheprovider`

The six failures are exactly `test_copy_carries_the_canonical_block[L1]` through `[L6]`, each finding zero copies of the canonical block. All twelve zero/two locator controls pass.

Regression command (executed through `rtk proxy`):
`/opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_agent_definitions.py h-mad/tests/test_h_mad_wiring_task_shape_docs.py h-mad/tests/test_h_mad_assemble_tdd.py -q -p no:cacheprovider`

All 190 regression tests pass. No full suite was run and no other test commands were run.

Known sandbox artefact, excluded from STATUS as instructed: both pytest sessions raise PermissionError at session leak-reaper teardown invoking `ps -axo pid=,command=` (`conftest.py:183` -> `leak_reaper.py:34`). In the targeted run pytest attaches it to the final item, two-L6, whose test call passed; in the regression run it attaches it to the final assembler test. This was neither suppressed nor modified. Both command exit codes are 1.

Scope verified against a pre-edit snapshot: byte-identical content before the control function, and identical module AST after excluding only that function. CANONICAL, COPIES, all six copy tests, and all real-tree locator implementations remain unchanged. No production files, mutation rows, workflow state, or cycle-1 report were edited.

OneContext lookup was attempted as required; unavailable outside a OneContext environment. The supplied correction instructions and cycle-1 report provided the needed context.

STATUS: DONE
