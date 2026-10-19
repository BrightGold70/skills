AUDIT-grok-audit-surface-impl-plan-v1-BEGIN
## Summary

The tables reconcile to 18 tasks, 166 planned mutation rows, and 112 planned marker sites. Six build gaps remain in token exits, mutation discrimination, and refusal assertions; repository files were left unchanged.
Evidence: 14 files opened, 12 greps run.

## Must-fix

- Task 2 leaves argparse's successful help exit outside the token contract — overriding `error()` does not intercept `<mode> --help`. A throwaway parser using the specified subclass exited through `SystemExit(0)` with no token. Specify token-safe help handling or disable automatic help, and cover that path across the modes.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `def error(self, message: str) -> NoReturn: ...`; `So AC-5.1 holds as written: there is no exit without a token.`

- Task 5's static symlink fixtures cannot kill the specified write and parent mutants — the removal pass already unlinks every symlink, including expected files and ancestors, before restoration. Controlled filesystem pairs produced identical live files and unchanged outside sentinels both with and without those guards. Inject the link between the relevant checks, or test the guarded restoration boundary separately, so each named mutant changes an assertion.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `whether or not its`; `path is in the expected tree`; `` `O_NOFOLLOW` is dropped; the ancestor check is skipped ``

- The blanket stderr suppression makes the zero-crash gate blind to unexpected child exceptions — a disarmed guard can produce an internal-error token, fail its assertion, and count as an ordinary kill because its traceback never reaches the harness. A controlled call to the actual `crash_kill` returned `ValueError` with the traceback surfaced and `None` with it suppressed. Surface unexpected stderr on failure, treating deliberately injected last-resort exceptions separately, or add an independent rejection of mutant-caused internal failures.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `message echoes the child's stderr: the last resort prints a traceback there, and the mutation`
  quote: h-mad/scripts/h_mad_mutation_harness.py › `What this CANNOT see is a crash the failing test never surfaced.`

- Probe imports fall outside the harness's bytecode invalidation boundary — the spec root is `h-mad/`, while the imported probe is its sibling under `docs/`. The actual `_run` purges only beneath its root. In a controlled same-size, same-timestamp mutation, source changed from `VALUE = 1` to `VALUE = 2`, but the harness still executed 1 until the external cache was removed. Require fresh compilation or explicit probe-cache invalidation for in-process loads; otherwise a landed mutation need not execute.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `../docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  quote: h-mad/scripts/h_mad_mutation_harness.py › `for cached in root.rglob("__pycache__"):`

- AC-T6.1 contradicts the post-write confirmation fixture — replacing only the read after a successful `update-ref` leaves the real ref changed, whereas the AC requires every refused commit to retain its pre-test value. A temporary-repository control confirmed that distinction. Limit the unchanged-ref assertion to pre-write refusals and assert the actual resulting state for `ref_unconfirmed`, or explicitly design and test a safe rollback.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `` the probe's ref read after `update-ref` replaced to ``; `reads the pre-test value) or no dest file was written, as applies.`

- Task 16 trusts an off-PASS regression test without observing it fail — it is explicitly green at RED, none of the mutation-table rows targets it, and the task adds no mutation or other negative run. This violates Test discrimination. Specify a verified failing run with premature three-surface routing or the protected sentence removed, then restore and verify GREEN.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `which is P at RED`; `**Mutation rows**: none new (K2 is re-anchored, not added).`

## Should-fix

- Task 9's fraction mutant conflicts with the global type-preservation rule — substituting strings for `Fraction` values changes the comparison domain despite the explicit prohibition on type changes. Use a Fraction-preserving numeric mutant that makes the unreduced-equality fixture fail.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.impl-plan.md › `never introduces an exception, an undefined name or a type change`; `` unreduced `f"{a}/{b}"` strings ``

## Nit

None

🌱 graft saved ~201,075 tokens ($0.14 plus <$0.01), 7 calls.
AUDIT-grok-audit-surface-impl-plan-v1-END
