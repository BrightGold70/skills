AUDIT-doc-block-exec-design-v96-BEGIN
## Summary

The design states coverage for all 49 acceptance criteria, but its substitution algorithm, launch-error handling, and rollback-test policy leave blocking gaps. Repository inspection and controlled Python 3.11.8 probes support the findings below; historical measurement transcripts were not exhaustively re-executed.

Evidence: 96 files opened, 3 greps run.

The file count includes 88 test files opened for the import-convention census. Axis C classifications describe the stated contract; algorithmic defects are reported separately.

| Spec identifiers | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

## Must-fix

- **Substring checking does not prevent overlapping replacement spans.** With keys `ab→X` and `bc→Y`, the prescribed algorithm accepts `abc abc`, reports both counts as 2, but produces `Xc Xc`: `bc` is replaced zero times. The control `ab bc ab bc` produces `X Y X Y` with both counts correct. This was reproduced on Python 3.11.8 using the prescribed escaped alternation and a recording replacement callback. Define the policy for intersecting matches, reconcile any additional refusal with the spec, and add a discriminating regression test.
  quote: docs/02-design/features/doc-block-exec.design.md › `If any key is a substring of another, the result depends on`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `the reported occurrence count equals the number replaced.`

- **Valid UTF-8 shell text containing NUL has no verdict path.** On Python 3.11.8, otherwise identical `Popen(["bash", "-c", payload], ...)` calls return rc 0 for `"true"` and raise `ValueError: embedded null byte` for `"true" + chr(0)`. A document or preamble can contain that character while passing strict UTF-8 decoding. The documented exception mapping does not handle this failure, so the CLI can exit through a traceback without its required token. Specify a pre-spawn refusal or mapped launch failure, with coverage through both document and preamble inputs.
  quote: docs/02-design/features/doc-block-exec.design.md › `main` catches `DocBlockError` and dispatches on type
  quote: docs/02-design/features/doc-block-exec.design.md › `LaunchFailed or CleanupFailed.`

- **The rollback identity guard is explicitly exempted from discrimination testing.** Calling it a policy constraint does not exempt an implemented deletion guard from the base Test discrimination invariant. The mutation matrix has no mutation removing this identity comparison. Add a fixture that reaches the mismatch branch and demonstrate failure when the comparison alone is removed; amend the permitted injection seams if necessary.
  quote: docs/02-design/features/doc-block-exec.design.md › `its mismatch branch cannot be reached by a test without an additional`
  quote: docs/02-design/features/doc-block-exec.design.md › `seam between the two arms, and adding one for a stated non-goal is not warranted.`

## Should-fix

- **The stamp-check acceptance rule contradicts the exemption immediately above it.** The folded census returns eighteen `after the v1.106 entry` occurrences. The section explicitly permits those lagging stamps, yet its interpretation of the same census declares every older version stale. Make the check distinguish an approved exemption from an unresolved stale stamp.
  quote: docs/02-design/features/doc-block-exec.design.md › `a stamp may lag the shipped version when re-stamping it *in isolation* would`
  quote: docs/02-design/features/doc-block-exec.design.md › `Every hit must name the current entry; any other version is a stale stamp by construction.`

- **The closing compliance paragraph assigns corpus work to the plan that the plan already records as completed.** The plan defines the tracked corpus, publishes its command, and distinguishes historical tracked/glob readings. Replace the outstanding-debt claim with a dated account or identify a specific remaining discrepancy.
  quote: docs/02-design/features/doc-block-exec.design.md › `What the plan owes is the *definition*`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `**The corpus for every `*.md`-scoped measurement below is the tracked one**`

- **The universal import-convention claim remains false.** The current tree contains 88 test files, of which 13 contain the exact `sys.path.insert(0, str(SCRIPT_DIR))` spelling. The plan already describes this as a convention rather than a universal property. Align the design’s justification with that narrower, sufficient claim.
  quote: docs/02-design/features/doc-block-exec.design.md › `mechanism is the one every test in `h-mad/tests/` already uses** for `SCRIPT_DIR`:`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `not a property of the directory`

## Nit

- The PID-file discussion points to “Architecture Considerations” as a section in the design. That heading exists in the plan, not the design; qualify the cross-document reference.

AUDIT-doc-block-exec-design-v96-END