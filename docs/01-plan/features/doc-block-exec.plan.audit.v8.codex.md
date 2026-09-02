## Summary
All six functional requirements are implemented-as-written at plan granularity. The plan nevertheless contains two FR-6 implementation gaps: one success condition contradicts the deliberate non-executing scan, and the migration does not specify how the documented block receives the collection result it needs to exercise its delivered branch.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-6's success criterion is impossible alongside its stated scope — it requires “No hand-written ` ```bash ` extraction remains in `h-mad/tests/test_h_mad_collect_report_docs.py`,” but the plan and AC-6.2 deliberately retain `:412`'s `re.findall(r"```bash\n…")` text scan because it inspects an untagged `exec codex` recipe that must not run. A compliant implementation would therefore fail its own success criterion (or wrongly migrate/run `:412`); narrow the criterion to removal of the executing `:270` extraction and `run_recipe` execution path.
- FR-6 does not specify the execution input needed to preserve AC-6.3 — the target gate block reads `COLLECT_OUT`, while the old `run_recipe` supplies it with a preceding real `h_mad_collect_report.py` command. The proposed helper contract only addresses/extracts/substitutes/runs a block and the plan names no environment, preamble, or replacement collector step. Running the current block under strict bash without that value emits `COLLECT_OUT: unbound variable` and the `report_not_collected` halt, so it cannot reach the delivered-report `GATE: PASS` branch. Specify the exact caller/API boundary that obtains and supplies `COLLECT_OUT`, and pin both delivered and missing paths through that boundary.

## Should-fix
None

## Nit
None
