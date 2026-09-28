AUDIT-grok-codex-fallback-impl-plan-v2-BEGIN
## Summary
Three blocking gaps remain in the regression gate and malformed-log handling. The plan was checked against the current reader, hook, wrapper, and test harness sources.
Evidence: 12 files opened, 11 greps run; 🌱 graft saved ~109,964 tokens (~$0.06) this turn, 1 call.

## Must-fix
- Task 16 can emit `FLOOR: PASS` after the full suite or either collection fails — its pytest command has no failure guard, and the collection pipelines end in `sort`, which masks pytest's exit status. Guard those commands and prove a failed suite or collection cannot reach the pass token.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`
- The planned `scan()` change leaves valid JSON with an unhashable `event` value able to crash the evidence CLI and `measure_effort()` before grok detection — F0 alone gives `agy_events=0`, while prepending `{"event":[]}` raises `TypeError` at `h_mad_review_evidence.py:141`. Add a typed membership guard and a mixed-log regression test, and record the additional deviation from design's unchanged-`scan()` claim.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `except (ValueError, TypeError, RecursionError):`
- Task 17 allows parser changes after Task 16's regression gate but prescribes only a smoke rerun — the final code could merge without the coupled suite and affected mutation rows being revalidated. Require those gates again after any live-envelope repair.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `A live envelope that disagrees with F0 fixes the parsers against the`

## Should-fix
- Task 16 merely prints the content-classifier sweep — a new classifier can appear without a required review or gate failure. Compare its file set with the expected population or require an explicit disposition for additions.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `# the design's class sweep, recorded`

## Nit
None
AUDIT-grok-codex-fallback-impl-plan-v2-END
