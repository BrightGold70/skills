## Summary
The design meticulously translates the audit-cycle spec into a two-process architecture, clearly dividing responsibilities between shell orchestration and Python text handling. It properly implements the fallbacks, the isolated per-pass gating, and correctly handles operational errors versus valid cannot-judge verdicts. However, there is a hard contradiction in the testing strategy regarding how subprocesses are mocked, which must be resolved to preserve test isolation.

| Spec AC | Classification |
|---|---|
| AC-10.4 | `restated` |

## Must-fix
- **Spec reconciliation: AC-10.4 restated** — Spec AC-10.4 says "A test asserts that a `## Must-fix`-less report yields UNVERIFIED, not PASS." The design restates this as "test_combine_invalid_yields_unverified | header-less report from one pass...". This narrowing to a "header-less" report (lacking both must-fix and should-fix headers) is correct and necessary, because a report lacking only `## Must-fix` but containing `## Should-fix` represents a clean passing audit and must yield `PASS`, not `UNVERIFIED`.
- **Contradiction between script resolution and test stubbing** — The design claims the helper "resolves its sibling scripts relative to its own `__file__`" (Skill self-containment), but the Test Strategy claims the tests mock these subprocesses by replacing them with "stub executables on PATH". If the helper uses an absolute path derived from `__file__`, the OS will bypass the `$PATH` lookup entirely. Placing stubs on `$PATH` will have no effect, and the tests will silently execute the real scripts instead. This violates the **Test discrimination** invariant, as the tests for mocked behaviors (like `GATE: INVALID` or delayed delivery) will be running against the real un-mocked scripts, leaving those error paths effectively untested despite a green suite. The design must reconcile how the tests intercept absolute-path subprocess calls (e.g., via `unittest.mock.patch` on the resolution function, or a test-only environment variable override) without relying on `$PATH`.

## Should-fix
- **Scope of `test_prose_plus_bullet_not_concatenated`** — The design states this test "invokes `h_mad_audit_gate.py` directly" to pin the real parser's under-count behavior. However, AC-10.3 requires asserting that the *cycle* (or the helper's union logic) correctly yields `FAIL` with the prose finding counted when given these two distinct reports. If the test only invokes the gate on the concatenated file to prove it under-counts, it proves the *premise* of the design but fails to test that the *helper itself* correctly bypasses this trap to return `must=2`. The test should invoke the helper's `gate()` or `combine()` logic using the un-stubbed, real `h_mad_audit_gate.py` for both passes to verify the end-to-end union logic succeeds where concatenation would fail.

## Nit
None
