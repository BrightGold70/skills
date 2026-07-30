## Summary
The design implements the recovery plan successfully, properly distinguishing clean runs from empty outputs, and cleanly extracting the verdict. It introduces a smart narrowing of the extraction regex to avoid false positives. However, the design violates the Axis B Assumption Verification invariant by failing to cite the output of the newly introduced shell commands.

| Spec AC | Status |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-1.4 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-3.1 | `restated` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-3.4 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |
| AC-5.2 | `implemented-as-written` |
| AC-5.3 | `implemented-as-written` |
| AC-5.4 | `implemented-as-written` |
| AC-6.1 | `implemented-as-written` |
| AC-6.2 | `implemented-as-written` |
| AC-6.3 | `implemented-as-written` |
| AC-7.1 | `implemented-as-written` |
| AC-7.2 | `implemented-as-written` |
| AC-7.3 | `implemented-as-written` |

## Must-fix
- Spec AC-3.1 `restated` — Spec wording: "When the log contains `STATUS: <value>` (codex) or `VERDICT: <value>` (agy), the last such line is emitted to stdout." Design wording: `recovered="$(grep -aE '^(STATUS|VERDICT):' "$log" 2>/dev/null | tail -1)"` (Anchored `^(STATUS|VERDICT):`). The design narrows the match to only lines beginning with the marker to avoid matching the prompt's contract-echo. This is a sensible narrowing but must be explicitly reconciled into the spec.
- Axis B (Assumption verification) — The design introduces load-bearing shell commands (`git -C "$cd_dir" rev-parse --is-inside-work-tree`, `git -C "$cd_dir" status --porcelain | grep -c .`, and `grep -aE '^(STATUS|VERDICT):' | tail -1`) without citing their observed outputs from a throwaway execution. The invariant explicitly states: "An assumption asserted without evidence, where evidence was one command away, is a violation."

## Should-fix
None

## Nit
- In the "Empty-vs-nonempty fork" section, the design mentions `stderr: "EMPTY final message — reporting channel failed; transcript: $log"` executing even if the agent crashed (where rc is not 0). While rc is correctly preserved, the "reporting channel failed" diagnostic might be slightly misleading to a reader if the run actually aborted.
