## Summary
The design covers most of the spec, but several acceptance criteria are either narrowed in the design text or made unimplementable by contradictions in the proposed mechanics. Axis C classification:

| Classification | ACs |
|---|---|
| implemented-as-written | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-5.1, AC-5.2, AC-5.4, AC-6.1, AC-6.2, AC-6.3, AC-6.5, AC-6.6 |
| restated | AC-1.6, AC-5.3, AC-6.4 |
| absent | None |

## Must-fix
- AC-1.6 is restated into an incorrect scanner rule — spec says, "A tag appearing inside a fence body (a fence that quotes ` ```bash hmad:exec ` as text) is not treated as an opening fence"; design says, "A line whose lstrip starts with ``` toggles the state." That design is narrower than Markdown fence semantics because it does not track fence length or closing-fence grammar, so a quoted triple-backtick opener inside a longer fence can corrupt `in_fence` state instead of remaining body text.
- AC-5.3 is restated as a substring ban instead of an invocation ban — spec says, "The source contains no invocation of `timeout` or `gtimeout`"; design says, "source contains no `timeout`/`gtimeout`" and "AC-5.3 asserts the absence in the source." The design form would reject the intended Python `timeout` parameter, `TimeoutExpired`, and `--shell-timeout` interface, so it conflicts with the feature's own portable bound design.
- AC-6.4 is restated as an underspecified count check — spec says, "The full suite passes, and the count is no lower than the pre-change count plus the tests this feature adds"; design only says "suite count" and lists `python3.11 -m pytest -q`. That drops both the full-suite pass criterion and the lower-bound comparison needed to catch hidden test loss.
- The AC-5.2 test design records the descendant PID in the temp cwd, then requires reading it after timeout while `run_block` removes that cwd in `finally` — this makes the proposed verification evidence disappear precisely on the path where AC-5.4 also requires cleanup.
- The API/error contract for `extract` is internally inconsistent — architecture and signature say `extract()` returns `[Block, ...]` / `list[Block]`, while scanning and error handling say zero or multiple candidates become `NOT_FOUND` / `AMBIGUOUS` and `extract` raises `BlockNotFound` / `AmbiguousBlock`. Implementers cannot tell whether selection/refusal belongs in `extract`, `run_block`, or `main`, and tests for API callers will diverge.
- The CLI error-handling strategy omits the `UNREADABLE` path it promises — the verdict table requires `DOCBLOCK: UNREADABLE reason=doc_unreadable|stream_path_unwritable`, but Error Handling says `main` catches exactly the extraction/substitution/timeout exceptions. Without a named exception or explicit `OSError` mapping, unreadable docs or stream paths can leak as tracebacks instead of verdict tokens.
- The design carries an uncited measured claim, "the failure this repository has four live instances of" — base Assumption verification / Counts discipline requires load-bearing incident counts to cite observed evidence in the document, not rely on the author's memory or a prior report.

## Should-fix
None

## Nit
None
