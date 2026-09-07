## Summary
All six functional requirements are implemented-as-written at plan granularity, but the plan has three hard internal/contract gaps: it undercounts the specification, contradicts itself about the affected extractor, and promises descendant cleanup that its process-group mitigation cannot provide. The CLI’s two optional stream paths also lack the alias refusal needed to preserve their stated separate-artifact semantics.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- The success criterion and v1.4 history say there are “38 ACs,” but the cited spec contains 39: AC-1 has 7, AC-2 has 7, AC-3 has 10, AC-4 has 5, AC-5 has 4, and AC-6 has 6. A 38-AC completion gate can declare success while one acceptance criterion is unaccounted for; correct both plan surfaces and enumerate/trace the complete test set.
- The risks table says tagging the gate fence breaks both bare-opener extractors at `h-mad/tests/test_h_mad_collect_report_docs.py:270` and `:412`, directly contradicting the plan’s measured statement (and FR-6) that only `:270` selects the tagged gate block while `:412` selects the untagged `exec codex` block. This leaves a false scope/mitigation signal for the migration; change the risk to `:270` only and preserve the deliberate non-executing `:412` scan.
- AC-5.2 promises that “no descendant process” survives, but the plan’s sole mitigation is to reap the subprocess process group. A descendant can create a new session/process group (for example through `setsid`) and escape that kill, so the stated implementation cannot establish the AC for arbitrary tagged shell text. Either narrow the spec/plan contract and test to descendants remaining in the launched process group, or specify and test real process-tree containment; do not claim the stronger result from a group-only cleanup.
- The CLI permits `--stdout <path>` and `--stderr <path>` without defining the same-path case, although it calls them “separate artifacts” that each receive their stream verbatim. One path cannot hold two different verbatim streams, so an allowed invocation necessarily overwrites or merges an artifact; add a pre-run alias refusal (with a named token/reason) and a no-execution regression test.

## Should-fix
None

## Nit
None
