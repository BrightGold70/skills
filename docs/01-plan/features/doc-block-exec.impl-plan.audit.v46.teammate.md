## Summary
IN PROGRESS — written incrementally so a partial result survives; findings below are already verified.
GATING pass, one surface only (codex exhausted); no two-surface clean and no exit gate is claimable from this.
Evidence: 9 files opened, 34 greps run.

## Must-fix
- The per-needle breakdown of the pre-dispatch sweep is stamped at the WRONG SHA and contradicts the stamp line four lines below it. Re-run over the body (everything above `## Version History`) with the sweep's own five needles: at `dfae038` the debt word matches **24** lines and the union **26**; the published `23 / 1 / 1 / 0 = 25` is the reading on **`3f70eb3`**, v1.51's own tree. The same paragraph then correctly stamps "**26** on the tree v1.50 ships" — and `dfae038` IS the tree v1.50 ships (`git show dfae038:<this file> | grep -oE '^- v1\.[0-9]+' | tail -1` → `v1.50`), so the document publishes 25 and 26 for one blob. This is the species of error the paragraph exists to prevent.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `At `dfae038`, over the
  body, by line: the debt word **23**, `spec\.md:` **1**, `design\.md:` **1**, `plan\.md:` **0** —
  and 23 + 1 + 1 + 0 is the **25** the whole sweep returns, so no line is reached by two needles.`

- The v1.51 Version History entry asserts that `df04e8e` and `dfae038` touched only `docs/handoffs/`. That is false: `git show --stat dfae038` names `docs/learnings.md` (5 lines) and `docs/skill-candidates.md` (4 lines) besides the handoff file. The conclusion the sentence supports is independently true (`git diff --name-only 00b961f..dfae038` over the four feature documents is empty, verified), so the repair is to state the measurement that was actually run rather than a scope claim that was not.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` `df04e8e` and `dfae038` touched only `docs/handoffs/` ``

- The Conventions residual routes the reader to the wrong task for the one `§`-reference r15 retired. `Task 3` spans lines 2059–2252 and contains **no** delta block and no `§` occurrence at all; the retired `§Scanning` site and its re-derivation are in **Task 1**, inside `# h-mad/tests/docsections.py  (delta)` (block opens at :1810, the re-derivation runs :1826–1834). A wrong internal locator in the very sentence that rules on locations is the class member the rule is written against.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `(delta self-review r15; the site and its
  re-derivation are in Task 3's delta block)`

## Should-fix
- The v1.51 entry points at the v1.50 entry as being "below" it. In the Version History the entries ascend, so v1.50 is the line **above** v1.51 (`:3391` vs `:3392`). A direction word is a location and expires the same way the rule one paragraph over says a section name does.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `The v1.50 entry below carries the same wrong figure and takes a **bracketed appended correc`

- The body says the retired cardinal itself is inside the v1.50 entry's bracketed correction; it is not. The bracket (added at v1.51, verified by diffing the entry between `dfae038` and `3f70eb3`) carries the *reading* — "returns **4**" and the four glob forms — but never the retired value. The retired value sits in that entry's original prose, ~400 characters earlier and outside the bracket. Either the sentence should say "in the v1.50 entry, annotated by its bracketed correction", or the bracket should carry it.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `The wrong value and the reading that
  retired it are in the v1.50 Version History entry's bracketed correction`

## Nit
None
