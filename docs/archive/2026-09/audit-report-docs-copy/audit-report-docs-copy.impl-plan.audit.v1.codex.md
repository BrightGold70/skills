## Summary
The implementation plan is generally well ordered and tracks the paired design, but two verification gaps remain hard enough to block: the fallback writer readback is not independently pinned, and the real incident replay is reduced to an underspecified note outside the executable AC. I also found two plan-quality issues around mutation-spec specificity and the existing spec-registry test claim.

## Must-fix
- `_write_collected_report` readback is not independently pinned — the plan requires both writers to read back, but Task 1 AC-2.12 only names `_copy_collected_report`, Task 3 AC-2.12 does not require an `--out`-rung readback-failure case, and Task 6 mutates only “copy readback removed” plus “out-rung conflict check removed”; an implementation could omit the `--out` writer readback and still satisfy the listed mutations, violating Mutation verification/Test discrimination for the fallback write path.
- The real incident replay is not an executable implementation-plan requirement — the source spec/design name the reachable survivor `/tmp/audit_nlmpin_plan_cycle8_codex.report.md` and require a scratch-root hand replay transcript, and that file exists locally, but the impl-plan’s AC-2.9 only specifies an isolated synthetic suite replay while the executive summary merely says “hand replay runs after task 3”; this leaves the Incident replay invariant dependent on memory instead of an exact artifact/path/transcript requirement.

## Should-fix
- Task 6 leaves the 19 mutation anchors as ellipsis placeholders — the plan says each mutation is an exact `find`/`replace`, but the only JSON block uses `"name": "..."`, `"file": "scripts/…"`, `"find": "…"`, and `"test": "tests/…::test_…"`; at least a table of the 19 mutation names, production files, intended anchor snippets, and named tests would prevent the implementer from inventing a weaker spec.
- The statement that existing `test_audit_cycle_mutation_specs_*` tests validate the new spec is ambiguous against the current tree — those tests currently load only the two audit-cycle specs under `h-mad/tests/specs`, so the plan should state whether Task 6 extends them to include `h-mad/tests/mutation-specs/collect_report.json` or relies on the direct harness/check-anchors AC instead.

## Nit
- “Delegate exactly as `report-wait` does” is slightly imprecise because the planned `collect-report` helper uses `HMAD_AUDIT_CYCLE_SCRIPT_DIR`, while the current `_cmd_report_wait` derives `here` directly; “same pure delegation shape” would avoid a false expectation of byte-identical wrapper code.
