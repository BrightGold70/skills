## Summary
The plan covers FR-2 and FR-4–FR-6 as written, but it narrows FR-1 and FR-3 in ways that leave required execution and operational-error behaviour unspecified. These are hard spec-reconciliation gaps, not implementation choices, because the omitted cases can otherwise pass the described tests while violating the documented contract.

| FR | Classification |
|---|---|
| FR-1 | restated |
| FR-2 | implemented-as-written |
| FR-3 | restated |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-1 is restated: the spec requires that “the opener's indentation is stripped from body lines only up to that count,” whereas the plan’s relevant contract only says that `fence_aware_end` has “opener and closer indented **0–3 spaces**.” That function only returns a section-end offset, and no extraction algorithm, acceptance test, or mutation in the plan requires `extract` to de-indent a selected fence body. The plan is narrower: it can recognise the fence correctly yet return non-CommonMark block text. Specify the body-normalisation rule on `extract`, with an exact-text 1–3-space fixture and a mutation that removes the stripping.
- FR-3 is restated: the spec requires `_final_write` to “flushes and closes the handle inside the region mapped to `stream_write_failed`,” requires an invalid-UTF-8 preamble to refuse as `preamble_unreadable`, and requires `CLEANUP_FAILED` to include an `os_error:` detail when cleanup raised. The plan instead specifies final output only as “`seek(0); truncate(); write`,” calls only an unreadable *path* out for the preamble, and specifies `CLEANUP_FAILED path=<p>` without its required OS-error detail. This is narrower: buffered close/flush errors can escape the mapped refusal, malformed executable preamble text lacks a stated handling path, and a recorded cleanup error can lose its diagnostic. Carry all three into the concrete CLI/API algorithm and named tests/mutations.

## Should-fix
None

## Nit
None
