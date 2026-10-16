SPEC-AUTHOR: DONE version=v1.2 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=501 sha256=e18239c28885b5dec82b24afe9b71773ced92ebffa72b2426d9d8742322636dc

Pre-write assertion: sha d92cfe3c… matched; newest VH entry v1.1; mtime 1792123465 unchanged before edits.

premises verified:
- h-mad/scripts/h_mad_phase7_preconditions.py check(): `sed -n 163,205p` -> archreview WITH_FIXES|NO = blocker archreview_failed; SKIPPED_NO_PANE = blocker archreview_skipped; SKIPPED_OPERATOR_OVERRIDE = warning archreview_overridden; READY_TO_MERGE = pass; else (absent/unrecognised) = blocker archreview_not_run.
- CLI prints warnings as `  WARNING {code}: {detail}` (grep -n WARNING -> print line in main()). Matches existing FR-7 text.
- Callers of h_mad_phase7_preconditions: `git ls-files 'h-mad/**' 'tests/**' '*.py' '*.sh' | xargs grep -ln phase7_preconditions | grep -v ^docs/` -> 9 files: the script, its 3 tests, 2 mutation specs, SKILL.md, failure-recovery.md, inline-protocols.md. No batch caller over archived features (code callers = the CLI and its tests).
- FR-1 `implementer` takes only codex|agy|null; grok/claude reach FR-7 only via implementer_switch.to (spec FR-1, read in place).

findings applied:
- Operator decision -> D-11 (new Decisions bullet): unrecorded warning widened to codex|agy|grok|claude, matching D-9; warning only; operator rationale recorded.
- FR-7 Surface bullet rewritten: trigger = a 6a-prime leg ran (archreview READY_TO_MERGE|WITH_FIXES|NO) and no leg=6a-prime entry. Other archreview values add no unrecorded warning because each already surfaces with its own code and no leg ran. NOTE: this pin is my refinement, not in the operator's words. The v1.1 trigger ("no 6a-prime entry") would have fired on a reviewer-less SKIPPED_OPERATOR_OVERRIDE feature, where nothing ran and there is nothing to record; widening to every implementer would have made that a false warning on every such feature. Revert = drop the archreview clause.
- Pre-existing features settled (FR-7 sub-bullet + D-11 sub-bullet): no grandfather rule; archived features are unaffected (nothing re-runs the check over them); an in-flight feature whose 6a-prime predates the field gets the warning, and the remedy is to backfill the entry from the dispatch log or carry the warning into the report. Rationale: the only signal a grandfather rule could use (review_independence absent) IS the skip, so it would silence the case the warning exists for.
- AC-7.2 added: one fixture per implementer (codex incl. absent field; grok/claude via implementer_switch.to) and per running archreview value; negative cases for an existing entry and for archreview absent / SKIPPED_NO_PANE / SKIPPED_OPERATOR_OVERRIDE. AC-7.1 is unchanged: it still has three FR-7 warning codes.

values swept:
- agy-only trigger: `grep -n 'review_independence_unrecorded\|implementer was\|agy` at any point'` before the edit -> 1 matching line (FR-7 only); after the edit, `grep -n 'agy-only\|agy only'` -> only the D-11 sentence that describes what was widened.
- D-ranges / counts: `grep -n 'D-1\.\.\|D-10\b\|D-11\|three FR-7'` -> the v1.0 VH entry "D-1..D-8" is historical and left as is; "three FR-7 warnings" is still correct (non_independent, unrecorded, malformed: 3 codes).
- No numbers changed, and no measured value moved.

contradictions found: none with the tree. Flag: the archreview-gated trigger is a judgement I added, explained above, and can be reverted.
placeholder scan: PRECHECK: PASS issues=0. 8 PATH advisories, all from before this revision and kept on purpose: h-mad/hooks/h-mad-agy-tdd-gate.py and .agents/hooks.json are files this feature creates, and .codex/hooks.json is the HemaSuite path cited for D-2 (this repo has no .codex/).
owed by other documents:
- plan/design (if they restate FR-7's unrecorded trigger as agy-only) must take D-11 and the archreview-gated trigger; I did not grep them (outside my file scope). That sweep is owed.
- SKILL.md Phase-7 / 6a-prime text (FR-10 surface): after recording 6a-prime, the orchestrator appends the review_independence entry for every implementer, not only agy.
- Carried from v1.0: agy-runtime.md §"Hooks" SessionStart re-check.
