Files changed:
- h-mad/tests/test_h_mad_review_attribution_docs.py (new; the only worktree change)

pytest output (last 10 lines of the final scoped RED run):
```text
h-mad/tests/test_h_mad_review_attribution_docs.py:37: AssertionError
=========================== short test summary info ============================
FAILED h-mad/tests/test_h_mad_review_attribution_docs.py::test_closure_step_carries_every_warning_line
FAILED h-mad/tests/test_h_mad_review_attribution_docs.py::test_closure_step_appends_review_independence_for_every_implementer
FAILED h-mad/tests/test_h_mad_review_attribution_docs.py::test_attribution_step_names_the_dispatch_as_the_source
FAILED h-mad/tests/test_h_mad_review_attribution_docs.py::test_5e_bullet_appends_the_author_at_green_acceptance
FAILED h-mad/tests/test_h_mad_review_attribution_docs.py::test_6a_prime_fix_appends_the_author
FAILED h-mad/tests/test_h_mad_review_attribution_docs.py::test_transcription_is_tied_to_the_skill_text
ERROR h-mad/tests/test_h_mad_review_attribution_docs.py::test_transcription_is_tied_to_the_skill_text
===================== 6 failed, 6 passed, 1 error in 0.41s =====================
```

Commands and results:
- `hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_review_attribution_docs.py -v`: collected 12 nodes; expected 6 assertion failures and 6 passes, both initially and after final test-only refinements.
- `hmad-dispatch run --timeout 180 -- /opt/anaconda3/bin/python3 -m pytest h-mad/tests/test_h_mad_archreview_pane_halt.py h-mad/tests/test_h_mad_phase7_integrate_docs.py h-mad/tests/test_h_mad_wiring_task_shape_docs.py -v`: all 56 regression assertions passed on the first measured run (`56 passed, 1 error in 0.50s`). A premature earlier guard attempt was refused with `SUITE: BUSY` while RED teardown retained the lock; it measured nothing. The guard command was rerun only after RED exited. No lock or fixture was changed.
- Known sandbox artifact, recorded here once: session leak-reaper teardown raises `PermissionError: [Errno 1] Operation not permitted: 'ps'` at `h-mad/tests/conftest.py:183` / `leak_reaper.py:34`. It affects both pytest summaries, is separate from test assertions, and is excluded from the status decision as instructed.
- Whitespace checks produced no diagnostics. Final `git status --short` named only the new test file. Production files, mutation specifications and existing tests are unchanged. No full-suite run, commit or production implementation was performed.

Self-review findings:
- All eight prescribed test functions exist, with five named AC-7.3 parameters yielding exactly 12 collected nodes.
- Six doc tests fail on explicit assertions naming the missing procedure property. There are no import, attribute or name errors standing in for RED behavior. This is the dispatched `new-behaviour` documentation task, not a wiring pin or new-production-symbol task.
- The closure locator uses the exact `str.index` boundary from `7. **Closure (autonomous)**` to the next `\n## Phase 5`. The other locators cover the unique 5d, 5e and 6a-prime bullet spans specified by the task.
- Author append pins require design FR-7's JSON object with exactly `module` and `agent`; they also require acceptance, accepted fixes, the resolved dispatch agent and before-review ordering. The 5d negative guard forbids an author append.
- The test-local `attribute(record, leg, module, reviewer)` validates all author entries, selects the target module's complete author set and latest entry, and returns no entry for each closed missing/malformed case. Cross-module authors are present so a global latest-author or global-author-set reading cannot silently satisfy the fixtures.
- Hostile agent-supplied module text comes from the existing `tests/stubs/orca` using `HMAD_STUB_HOSTILE=all`; it includes markdown, marker syntax, a newline and a tab. Closed agent enum values remain valid schema values. Records are written and reread as JSON before the final attribution call; no transient dispatch context is supplied to the correct transcription.
- Each AC-7.3 case asserts the correct complete entry (or no entry), runs its named mutant transcription, and asserts the mutant yields the wrong result. Routing additionally drives the existing production `h_mad_phase7_preconditions.check` twice to prove its warning distinguishes correct self-review attribution from routing-based misattribution.
- The six future doc-pin mutation rows are deliberately not added or run in RED, per the coordinator notes. `MUTATION: ALL_CAUGHT` remains a GREEN verification obligation.

RED acceptance evidence — one line per collected test:
1. FAIL `test_closure_step_carries_every_warning_line`: AssertionError "Phase-7 closure must carry every WARNING line into the report" names the missing property; invokes `_closure` -> `_span` -> `SKILL.read_text`, then `_require`, directly inspecting the authoritative closure slice. It additionally pins all three review WARNING codes.
2. FAIL `test_closure_step_appends_review_independence_for_every_implementer`: AssertionError "closure must append review independence after each of the three review legs" names the missing property; invokes `_closure` and `_require`, directly inspecting the closure slice, with subsequent assertions for the append, every implementer, five JSON keys, independence comparison and per-module 6a-prime entries.
3. FAIL `test_attribution_step_names_the_dispatch_as_the_source`: AssertionError "attribution must name the accepted implementation dispatch as implementer source" names the missing property; invokes `_closure` and `_require`, with additional pins forbidding both routing fields and explaining the resolved token, --agent and claude fallback.
4. FAIL `test_5e_bullet_appends_the_author_at_green_acceptance`: AssertionError "5e GREEN acceptance: missing --append implementation_authors JSON" names the missing property; invokes `_span` and `_author_append` on the 5e bullet. It also checks accepted GREEN status, before-spec-review ordering and accepted fixes before their next review.
5. FAIL `test_6a_prime_fix_appends_the_author`: AssertionError "6a-prime accepted fix: missing --append implementation_authors JSON" names the missing property; invokes `_span` and `_author_append` on the 6a-prime bullet, with pins for WITH_FIXES, acceptance, dispatch token and before-next-review ordering.
6. PASS `test_5d_bullet_appends_no_author`: non-vacuous negative pin; invokes `_span` and a regex forbidding `--append implementation_authors=` in the RED bullet. Introducing the prohibited author append makes it fail. Removing the bullet also fails its unique-prefix assertion.
7. PASS `test_attribution_transcription[routing-is-not-authorship]`: invokes test-local `attribute` and `_mutant_attribute` (`routing-as-authorship`), then production `p7.check`, whose review-warning path contains the behavior asserted. Deleting attribution or its self-review branch changes the asserted complete entry; deleting check's review_non_independent warning fails the explicit warning assertion. The mutant incorrectly yields an independent agy implementer and suppresses that warning.
8. PASS `test_attribution_transcription[multi-author-recovered]`: invokes `attribute` for grok 5e-review, codex 5e-verify and, after durable reload, agy 6a-prime; these are the methods containing the transcribed selection rule. Removing complete-set recovery or substituting the latest author fails the agy self-review expectation. The named review-projection mutant recovers only codex and incorrectly marks agy independent.
9. PASS `test_attribution_transcription[pre-field-feature]`: invokes `attribute` and the `absent-means-independent` mutant; deleting the no-entry handling fails explicit `None` assertions. Additional subcases check empty/unrelated-module authors, non-list fields, invalid agents and a malformed entry for a different module invalidating the whole set. The mutant treats absence as an empty set and emits an independent entry.
10. PASS `test_attribution_transcription[red-is-not-authorship]`: invokes `attribute` on the accepted Codex author record and the `red-counts-as-author` mutant on an agy RED then Codex GREEN history. Removing attribution or reading the RED author fails the complete codex/independent=true expectation; the named mutant yields agy/false. This tests the durable-state transcription, not execution of an author-append procedure.
11. PASS `test_attribution_transcription[unaccepted-dispatches-author-nothing]`: invokes `attribute` on the accepted Codex author record and the `unaccepted-counts-as-author` mutant on a rejected agy GREEN followed by an accepted Codex GREEN. Removing attribution or including the unaccepted agent fails the complete codex/independent=true expectation; the named mutant yields agy/false. This tests the durable-state transcription, not dispatch acceptance machinery.
12. FAIL `test_transcription_is_tied_to_the_skill_text`: AssertionError "FR-7 transcription must be tied to SKILL.md rule: The author set is read from `implementation_authors` only" names the missing property; invokes `_closure` and `_require` against the same authoritative slice. Remaining pins tie validation, author-set selection, dispatch exclusions and the three closed no-entry cases to the transcription.

Concerns: OD-1(A)'s declared residual remains: a test-local transcription and documentation pins establish the rule selected by the text, but cannot establish that an orchestrator actually appends authors before review or follows the attribution rule at runtime. No script surface was introduced, consistent with spec FR-1. The requested RED work itself is complete; the six documentation failures are intentional and await GREEN.

Context retrieval: checked the design FR-7 / FR-10 and the five spec AC-7.3 fixtures. The required OneContext history lookup was attempted after locating its installed skill; it is unavailable outside a OneContext dashboard session. The supplied dispatch and checked-in design supplied the needed task context.

🌱 graft saved ~27,838 tokens this turn, 1 call.

STATUS: DONE_WITH_CONCERNS
