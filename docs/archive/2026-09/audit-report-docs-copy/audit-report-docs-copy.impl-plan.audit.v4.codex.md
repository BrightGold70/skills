## Summary
The implementation plan is now specific enough on task ordering, file paths, and the 22-row mutation table. One hard verification gap remains in Task 6: it relies on the existing harness to prove spec shape and named-test coverage that the harness does not currently enforce.

## Must-fix
- Task 6 says the harness proves every mutation has `_mechanism` and a named `test`, but the current harness does not enforce that — `h-mad/scripts/h_mad_mutation_harness.py` only requires `name`, `file`, `find`, and `replace`, treats `test` as optional, and never validates `_mechanism`. A `collect_report.json` mutation without `test` can fall back to whole-suite scoring and still report `MUTATION: ALL_CAUGHT`, leaving Test discrimination/Mutation verification unenforced. Add an executable shape check, or extend `--check-anchors`, that asserts exactly the 22 mutation names and required keys including `test` and `_mechanism` before relying on AC-6.3.

## Should-fix
- The paired design still has stale mutation-count prose — `docs/02-design/features/audit-report-docs-copy.design.md` describes `22` as `17 + 2` and also as the previous set plus `k/k′/l/l′`, while the impl-plan table correctly lists 22. The impl-plan table is clear enough to implement from, but the cross-doc count drift is avoidable and weakens the count-sweep claim.

## Nit
- Task 3 requires importing `validate_surface` while also saying the CLI performs no surface pre-validation; explain that the import is intentionally unused or drop it from the import list so it does not invite the forbidden extra check.
