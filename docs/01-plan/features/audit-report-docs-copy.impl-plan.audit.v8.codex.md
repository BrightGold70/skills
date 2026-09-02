## Summary
The impl-plan is generally precise and aligns with the paired design on task order, file paths, CLI/gate token contracts, and docs placement. One connection-enforcement claim is not sound: the plan drops the force-direction mutation for the CLI→collector boundary even though an observable forced-call negative path exists.

## Must-fix
- Restore a force-direction mutation/test for the CLI→`collect()` connection — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:271-276` says an e′ mutant would be unobservable, but AC-2.10's bad `--project-root` case gives an observable negative path: if the semantic `project_root.is_dir()` refusal is neutralized and `collect()` is allowed to run with no report and no `--out`, `_collected_path` only joins paths and `collect()` can return `("none", None)`, yielding `COLLECT: MISSING`/exit 0 instead of the required operational error. The base Connection enforcement invariant requires both remove and force directions for a boundary call, so the 22-mutant spec leaves an unconditional CLI→collector route unpinned.

## Should-fix
- Reword the `PassSpec(out_path=None)` acceptance criterion — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md:76` reads like a literal constructor call, but the design and current namedtuple require `index`, `report_path`, and `rc` as well. Use `PassSpec(index=..., report_path=..., out_path=None, rc=...)` or "a PassSpec with out_path=None" to keep the task type contract unambiguous.

## Nit
None
