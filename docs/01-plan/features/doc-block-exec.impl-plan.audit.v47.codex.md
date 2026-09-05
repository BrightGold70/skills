AUDIT-doc-block-exec-impl-plan-v47-BEGIN
## Summary

The plan has six blocking inconsistencies in substitution, mutation discrimination, RED gates, and error handling. Repository reads and read-only probes support these findings; the proposed helper does not yet exist, so its implementation tests were not run.

Evidence: 13 files opened, 3 greps run.

## Must-fix

- **Substitution can report replacements it never performs.** For text `abc` and substitutions `ab→X`, `bc→Y`, neither key contains the other, so the prescribed check accepts them. The prescribed algorithm returns `Xc` while reporting both counts as 1; reversing map order produces the same failure. Detect intersecting match spans and define their disposition before replacement, with a discriminating test.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `counts are`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `taken on the original `block.text` (`text.count(key)` per key); every key with count 0 is`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `the reported occurrence count equals the number replaced.`

- **The wire-only failure requirement conflicts with the nested pytest test.** `test_docsections_imports_when_collected_alone` runs all of `test_docsections.py`, including the WIRE-PIN, and requires exit 0. A persisted delegation mutant therefore fails both the WIRE-PIN and that enclosing helper test. The promised isolated failure cannot occur. Make the import check import/collection-only, or explicitly accommodate this collateral failure in the verification contract.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**every other test stays green**: the helper's own behaviour tests`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `subprocess.run([sys.executable, "-m", "pytest", "h-mad/tests/test_docsections.py", "-q"], cwd=REPO_ROOT)` exits 0`

- **The field-escaping mutants do not isolate the properties claimed.** Returning the input unchanged removes JSON quoting and Unicode escaping together. Consequently, `field-escape-removed` also exposes `rc=0` token injection and the Unicode separators, contradicting the asserted mutual discrimination. Define separate payloads that preserve the other properties, then verify the claimed failure matrix.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` `field-escape-removed` (`_field` returns its input unchanged, so a ``
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `the newline test's one-line assertion still holds under it, and that row keeps the quoting, so this`

- **The guard-narrowing invariant is false on the live document.** A fence-aware read finds a bare `#` outside fences at `h-mad/SKILL.md:984`, immediately before “Reading a dispatch verdict.” The old space-required predicate rejects it; the prescribed ATX predicate accepts it. Replace the zero-softening invariant with explicit accounting for this changed boundary and the other accepted grammar shapes.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` the differential, not its size**: `new_only=0` — the narrowed guard accepts nothing the old regex ``
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` refused — and every one of `old_only` a `#` line inside a fence. ``

- **Cleanup exception chaining does not implement its stated fallback.** Executing `raise ... from pending` with `pending=None` produces `__cause__ is None` and suppresses implicit context; it does not select `cleanup_error`. Explicitly choose the pending exception or cleanup error, and test cleanup failure after an otherwise successful run.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` `from pending` (so `__cause__` is the pending `BlockTimeout`/`LaunchFailed` when there is one, else ``
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` `cleanup_error`); elif `pending is not None` → raise it; else return ``

- **The RED pass counts cannot match the commanded test scope.** Tasks 2–4 run the accumulating test file, while their expected passing counts exclude earlier tasks’ tests. The assembler compares actual pytest totals with `--expect-pass`, so following these instructions rejects the intended RED result. Scope the command to new tests or derive whole-file counts. Task 4 also incorrectly predicts a traceback: running a valid module without a CLI entrypoint normally exits 0 silently.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `exceptions already exist from Task 1); expected passing = 0; the Task 1 tests are regression guards and stay green.`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `CLI exit 1 with a traceback, the in-process `main` tests and the API tests raise `AttributeError`); expected passing = 0; Tasks 1–3 tests are`

## Should-fix

- **The self-reference gate fails on the shipping body.** The published regex returns four matching lines on v1.52, while its site remains stamped v1.50. Reconcile the current prose with this gate and publish its current reading; the historical zero does not validate the shipping text.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `**No body sentence in this document identifies the shipping revision by a RELATIVE phrase.**`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `It reads **0** on the body v1.50 ships, re-run after v1.50's last edit landed`

- **The mutation-payload classification contradicts the declared file split.** The conventions place all 81 rows on the new-helper-file side, but `registry-row-removed` targets existing `SKILL.md`. State an explicit exception for its newly introduced registry text and when its anchor becomes concrete.
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` names the anchor-*text*-rewritten case, not the anchor-*file*-moved one. `doc_block_exec.json`'s 81 rows are wholly on the second side. ``
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` 25 + 5 + 24 + 27 = **81 rows**, split **80 of the helper's source and 1 of `h-mad/SKILL.md`**. ``

## Nit

None
AUDIT-doc-block-exec-impl-plan-v47-END