## Summary

Axis C reconciliation covers all 49 acceptance criteria: 47 are implemented-as-written, and AC-1.6 and AC-3.14 are restated by the design. The two restatements are not explicit spec changes, and the audit also found a cross-document exit-code drift plus an unenforceable stream-write test plan. `I` means implemented-as-written; `R` means restated.

| ACs | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 | I |
| AC-1.6 | R |
| AC-1.7, AC-1.8, AC-1.9 | I |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | I |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13 | I |
| AC-3.14 | R |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | I |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | I |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | I |

## Must-fix
- AC-1.6 is narrowed without a corresponding spec change — Spec: “A tag appearing inside a fence body … is not treated as an opening fence”; Design: scanning carries “the opening fence's backtick run length” and describes only backtick fences. A `~~~` fence containing a tagged ```bash` string is still a fence body under CommonMark but would be parsed as an opener by the stated scanner. Support tilde fences too, or explicitly narrow and approve the spec.
- AC-3.14 has contradictory cleanup selection semantics — Spec: “If removal fails, the API raises `CleanupFailed`”; the design’s controlling flow selects `CleanupFailed` only “if the directory persists,” otherwise it re-raises the pending outcome or returns the result. Its later prose instead treats a recorded `OSError` as failure. A cleanup `OSError` after successful removal is therefore either silently lost or has undefined precedence. Define one rule: any recorded cleanup error **or** a positive `lexists` read-back raises `CleanupFailed`, with the documented cause rule, and test the error-but-gone case.
- The plan and design disagree on the operational exit partition — Plan says exit 2 is reserved for “`UNREADABLE`, `CLEANUP_FAILED)”; Design adds `LAUNCH_FAILED` at exit 2. The spec’s AC-4.2 supports the design, but leaving the plan stale gives implementers two incompatible CLI contracts. Update the plan’s CLI/convention text to name `LAUNCH_FAILED`.
- The stream-write-failure test is not an executable plan — it promises “a stream handle closed under the helper after the run” but gives no hook or mechanism by which the test can close a private held descriptor. Implementing it needs another injection/seam (for example, a named final-write helper or a controlled failing file object), which contradicts the stated “exactly four” fault injections unless that policy is revised. Without an exact mechanism, AC-3.8’s post-run write-error branch is not demonstrably discriminated.
- The load-bearing Markdown assumptions are knowingly deferred rather than verified before design — the supplied spec says there is “no local renderer” and proposes a Phase-5 operator check, while the design relies on CommonMark info-string and fence semantics for both safe selection and continued bash rendering. This breaches the base Assumption verification invariant. Record a real-renderer probe and observed output before clearing the design, or explicitly halt the feature until that verification is available.

## Should-fix
- Define behavior for an empty substitution key passed through the public `substitute(block, subs)` API — CLI parsing rejects it, but the public mapping API does not. `str.replace("", value)` produces surprising boundary insertions and bypasses the CLI’s `BAD_SUBST` policy.
- Specify the artifact state when stdout’s final write succeeds but stderr’s final write then fails — the current design reports `stream_write_failed` but can leave one newly current artifact and one stale/partial artifact. State whether the successfully written counterpart is retained or rolled back, and test that choice.

## Nit
- In the verdict table, “stream paths alias” is described as paths that “resolve to one path”; descriptor identity also catches hard links, which need not resolve to one textual path. Use inode/descriptor wording consistently.

