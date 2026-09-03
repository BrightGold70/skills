## Summary
Axis C reconciliation: every specified AC is covered as written; no AC is restated or absent.

| Spec ACs | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

The design otherwise has three must-fix failure-path/test-discrimination gaps that can leave a process running, accept a broken duplicate-substitution guard, or emit a traceback during cleanup.

## Must-fix
- `test_timeout_survives_a_group_that_already_emptied` is specified only as an `os.killpg` monkeypatch that raises `ProcessLookupError` under a timed-out block, with neither a fixture that makes the group genuinely empty nor teardown that reaps what the fake left running — production treats this exception as evidence that the group is already gone, but a simple fake leaves the timed-out `sleep` live; the subsequent drain/`wait()` can hang or leak it. This violates the base test-discrimination rule that a stub model the consumed production state. Specify an empty-group-plus-pipe-holder fixture (and escapee teardown), or have the fake arrange/reap the real group before raising.
- The mutation table claims every guard is mutation-verified but has no independently killable duplicate-key mutation: `subst-split-on-every-equals` combines “split on every `=` / last-wins on repeat” yet is bound only to `test_subst_value_may_contain_equals`. A mutant that preserves first-`=` splitting and merely overwrites duplicate keys survives that named test, so the `duplicate_key` refusal is not verified as required by the mutation/test-discrimination invariant. Add a separate last-wins duplicate mutation bound to `test_duplicate_substitution_key_refuses` (or equivalent) and require its named RED run.
- The specified chmod-failure rollback is `chmod fails → rmdir → LAUNCH_FAILED`, but no handling/read-back is defined if that `rmdir` itself raises. That can bypass the promised `DocBlockError`/verdict mapping with a traceback after a cwd was created, contrary to AC-3.13/AC-4.6’s cleanup and helper-failure contract. Route this pre-spawn rollback through the same recorded-error plus read-back cleanup selection, with a test for an injected rollback-removal failure.

## Should-fix
None

## Nit
None
