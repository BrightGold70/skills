## Summary
The impl-plan is mostly implementable: task order, file paths, CLI/gate token contracts, and mutation-spec shape are concrete enough to drive work. I found no hard invariant breach, but the paired design and a few AC wordings still carry stale or ambiguous instructions that can mislead implementation.

## Must-fix
None

## Should-fix
- Paired design still contradicts the impl-plan on the CLI import and mutation set - `docs/02-design/features/audit-report-docs-copy.design.md:240-241` says the CLI imports `validate_surface`, and `:456` still says `CLI->collect() (e/e')`, while the impl-plan explicitly says NOT to import `validate_surface` and that e' was dropped. This is not just editorial: it reopens the pre-validation/single-validator confusion and the 22-vs-23 mutation decision.
- AC-3.5a is ambiguous about `_VERSION_RE` matching for non-transport names - it says the fixture covers the AC-3.5 corpus, then says every non-transport audit name matches `_VERSION_RE`; read literally this is false for `f.report.md`, `gate-blindness-hardening.report.md`, `audit-report-docs-copy.report.md`, and `x.md`. Scope that assertion to docs audit artifact names (`*.audit.v*.md`) so the test author does not encode an impossible property.
- The AC-2.9 hand replay writes `docs/01-plan/features/audit-report-docs-copy.plan.md`, but Task 3 metadata and the Components Changed table do not list that file - the AC itself is explicit, yet the task/file inventory is incomplete. For a writing plan that emphasizes exact paths and scoped changes, the evidence-bearing plan-history edit should be listed as a Task 3 artifact or checkpoint output.

## Nit
- The impl-plan source header cites the paired design as v1.13, but the saved design document is now v1.14. Since the plan relies on design provenance, update the header to the current version or state why v1.14 is intentionally excluded.
