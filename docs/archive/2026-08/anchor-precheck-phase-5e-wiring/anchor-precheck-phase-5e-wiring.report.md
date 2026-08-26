# Report — anchor-precheck-phase-5e-wiring

**Completed:** 2026-08-26 · **Branch:** `feature/197-anchor-precheck-phase-5e-wiring`
**Range:** `b5c8f41` (5c baseline) … `adc735b`
**Match rate:** 100% (38/38 ACs) · **6a-prime:** `READY_TO_MERGE` (cycle 7)
**Audit cycles:** plan 4 · design 6 · impl-plan 3 · 6a-prime 7

## Executive Summary

The mutation-harness anchor sweep is now an obligation a run cannot silently skip: a suite
assertion over the repository's own committed specs, plus a sibling-only precheck inside
`run_spec` that refuses before executing anything when a neighbour's spec has drifted. All 38
acceptance criteria are satisfied and the architectural review is `READY_TO_MERGE`.

The result that matters most is not in the acceptance criteria. Seven review cycles raised
twelve findings; nine were real and fixed, three did not survive checking their premises. Two of
the real ones were defects this feature introduced into its own guarantees — a sweep that
examined nothing reporting `ANCHORS_OK`, and the feature's own WIRE-PIN quietly ceasing to test
ordering because an earlier fix in the same feature changed the shape it asserted on. Neither
was visible to a green suite of 2105 tests.

## What shipped

The mutation-harness anchor sweep is now an obligation a run cannot silently skip.

1. **`_resolve_root`** — one root-resolution authority. A relative spec `root` is spec-relative,
   not cwd-relative, so a spec resolves the same targets from any directory and inside a git
   worktree.
2. **All 17 committed specs re-rooted** to `../..`. They were pinned to
   `/Users/kimhawk/orca/skills/…`, which broke off this machine and — the sharper half — made a
   mutation run inside a worktree resolve to the **main checkout**. Demonstrated and closed.
3. **`classify_spec_file`** — `spec` / `not-a-spec` / `unclassifiable`, keyed on `_load_spec`'s
   own necessary condition rather than a second guess at spec shape.
4. **The sibling precheck, wired into `run_spec`** — sweeps sibling specs and refuses before
   executing anything when a neighbour has drifted or failed to load.
5. **`PRECHECK_FAILED`** — its own verdict, carrying sweep counts and no mutation counts, exit 2.
   Named FAILED rather than DRIFTED because an unreadable-only refusal reports `drifted=0`.
6. **A per-project suite assertion** that the repository's own committed specs are un-drifted —
   the always-on half, riding the full-suite run whether or not any mutation cycle happens.
7. **Documentation** — the obligation is now described as mechanical, not advisory.

Plus, from the review cycles: **`ANCHORS_NOTHING_SWEPT`** (exit 2), because a sweep that
examined nothing was returning `ANCHORS_OK`.

## What the process caught that a green suite did not

- `a-bad-spec-aborts-the-sweep` **survived, killed by the wrong assertion**: its fixture was a
  *missing* file, which the new classifier skips before `precheck_spec` runs, so the test no
  longer reached the branch it names. Only the named-test discrimination could see this.
- The same mutation's anchor later matched **twice** after a second `except SpecError` appeared,
  so it measured nothing while printing a verdict-shaped line.
- **`--check-anchors` returned `ANCHORS_OK` on a sweep of nothing** — a vacuous pass this feature
  introduced into the sweep it exists to harden.
- **The WIRE-PIN went vacuous** because an earlier fix *in this same feature* changed the result
  shape, making "count keys absent" true by construction.
- The committed-spec assertion **failed on any skipped file**, recreating the failure the
  classifier filter was added to prevent.
- Two RED tests hit their stated counts while asserting the wrong thing, and one pair of guards
  would have **passed vacuously on an empty walk**.

Both wire directions were verified by hand — twice, because the result-shape change invalidated
the first run — and every mutation was asserted to have landed before its result was trusted.

## Deferred, filed as monitoring rows

`J34` assembler path composition · `J35` `progress` exit code contradicts its documented contract
· `J36` a dispatch reported a fabricated sweep count · `J37` `ANCHORS_DRIFTED`/`REFUSED` still
collapse two cannot-judges (pre-existing F2) · `J38`–`J41` `h_mad_ab_dispatch` defects and the
absent 5c-baseline state field.

## Owed

- Merge to `main` and push — deliberately left to the operator.
- The feature's own dogfood ledger (F1–F18) remains the fuller narrative.

## Version History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-08-26 | Initial report at Phase 7 close. Range `b5c8f41`…`adc735b`, match rate 100% (38/38), 6a-prime `READY_TO_MERGE` on cycle 7. |
