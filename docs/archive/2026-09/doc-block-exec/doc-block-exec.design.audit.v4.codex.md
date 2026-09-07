## Summary
Axis C reconciliation:
| Items | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |
The design/spec/plan are mostly aligned, but the design still contains two hard implementation gaps: its differential-bounder requirement conflicts with the current helper it names, and its AC-5.3 test-plan wording contradicts the invocation-only rule it later states.

## Must-fix
- AC-1.6 and AC-1.7 are incompatible with the existing `h-mad/tests/docsections.py` bounder unless the design also changes that bounder or changes the parity strategy — the design requires the new scanner to be backtick-run-aware for four-backtick enclosing fences, and also requires byte-identical section bounds against `_fence_aware_end` over hostile fixtures. The current `_fence_aware_end` toggles on any stripped line starting with `` ``` ``, so it exits a four-backtick fence on an inner three-backtick quote; a read-only probe over `## H\n````bash\n```bash hmad:exec\n## Not a heading...` returned only `'````bash\n```bash hmad:exec\n'` and stopped at the inner `## Not a heading`. That makes the planned differential test fail for the very CommonMark shape AC-1.6 says must work, while `docsections.py` is not listed under Components Changed and unifying implementations is declared out of scope.
- AC-5.3 is stated two different ways inside the design, leaving an implementer with mutually incompatible tests — the Test Plan row says “source contains no `timeout`/`gtimeout`”, but Invariant Compliance correctly says AC-5.3 bans an invocation, not the substring, because the source legitimately contains `timeout=`, `TimeoutExpired`, `BlockTimeout`, and `--shell-timeout`. A literal substring test would reject the API and exception names the same design requires, so this surface must be narrowed to the invocation-token check.

## Should-fix
None

## Nit
None
