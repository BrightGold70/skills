## Summary
Axis C reconciliation found no restated or absent acceptance criteria; the design covers the spec and paired plan at the required identifiers. I found one internal consistency gap in the collector pseudocode that can turn an empty transport/docs pair into `COLLECT: OK`, contrary to the design's own empty-report policy.

| Identifier | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.6a | implemented-as-written |
| AC-2.6b | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-2.8 | implemented-as-written |
| AC-2.9 | implemented-as-written |
| AC-2.10 | implemented-as-written |
| AC-2.11 | implemented-as-written |
| AC-2.12 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.5a | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |

## Must-fix
- `_collect_unguarded()`'s AC-2.11 already-collected short-circuit accepts empty byte-identical files before the completion/size checks — D1 promises `report_path` present but empty with `.done` becomes `MISSING` and never treats an empty report as collected, but the shown `already = collected_path.is_file() and spec.report_path.is_file() and collected_path.read_bytes() == spec.report_path.read_bytes()` branch would return `("report-file", collected_path)` when both files are empty and distinct, causing the CLI to print `COLLECT: OK` for a non-report. Add the non-empty condition or explicitly narrow AC-2.11, and pin the empty-identical docs/RP case.

## Should-fix
None

## Nit
None
