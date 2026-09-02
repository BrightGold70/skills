## Summary
The design tracks the plan and implements the spec architecture with one collector, a transport-name gate refusal, wrapper wiring, docs updates, and mutation coverage. Axis C reconciliation found one absent AC detail in the CLI operational-error handling; no restated ACs were found.

| Identifier(s) | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.6a, AC-2.6b, AC-2.7, AC-2.8, AC-2.9 | implemented-as-written |
| AC-2.10 | absent |
| AC-2.11, AC-2.12 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.5a, AC-3.6, AC-3.7 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 | implemented-as-written |

## Must-fix
- AC-2.10 missing-required-flag handling is absent from the design — the spec requires operational errors, including “a missing required flag (`--surface`, `--report`)”, to exit 2 with no `COLLECT:` line, while D2 only enumerates project-root, cycle, surface-validation, and docs-dir checks. This Axis C gap leaves the parser-error contract to inference instead of designing and testing it explicitly.

## Should-fix
- The CLI marker contract is internally inconsistent — D2 says “Every CLI outcome ends with a `[H-MAD]` marker”, but the listed step-1 operational checks only print `ERROR:` on stderr and exit 2. Narrow the claim to verdicts plus readback failures, or specify markers for all operational errors.

## Nit
None
