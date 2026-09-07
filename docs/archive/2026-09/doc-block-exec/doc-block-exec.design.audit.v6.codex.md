## Summary
Axis C reconciliation finds all 46 specified acceptance criteria implemented as written; no AC is restated or absent. The design is otherwise coherent, but its stated CLI/API contract has two hard gaps at the subprocess boundary and its test plan misses two useful cross-document safeguards.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- `--shell-timeout` has no finite/domain validation or mapped refusal — `argparse` accepts negative, `nan`, and `inf` floats; a negative timeout reaches `communicate()` and raises an unhandled `ValueError` after `Popen`, while `inf` makes the promised bound unbounded. A nonnumeric argument also follows argparse's ordinary usage/error path rather than the design's promised single `DOCBLOCK:` line. Define and test a finite positive timeout validation before spawn, then add its exception/verdict to the spec, table, registry, and exhaustive cannot-judge test.
- The `RunResult` contract says `stdout: str` and `stderr: str`, and the CLI writes them to held text handles, but the only specified launch is `Popen(["bash", *flags, "-c", text'], start_new_session=True)` — without an explicit `text=True` (and encoding/error policy), `communicate()` returns bytes by default. This is a type-inconsistent API/implementation plan that can make normal stream-artifact writes fail; specify the Popen text/encoding settings and pin non-ASCII and undecodable-output behavior.

## Should-fix
- The plan's Success Criteria promises that exactly one fence is tagged at feature completion, but the design's AC-6.1 test only checks that the Second-surface tag is present — add a tree-wide cardinality assertion so an accidental second opt-in fence cannot satisfy the suite.
- Sequential stream reservation can truncate an already-existing `--stdout` artifact before opening `--stderr` fails, despite the design's claim that no irreversible action occurs before the last refusal — either document that partial artifact mutation is intentional or preflight both destinations without truncation and reserve them only once all checks succeed.

## Nit
None
