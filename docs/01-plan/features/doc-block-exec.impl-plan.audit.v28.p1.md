## Summary
The implementation plan is exceptionally thorough, precise with its file paths, and adheres strictly to the defined exceptions hierarchy and previous design constraints. A minor variable naming oversight in a teardown routine and an unspecified exception constructor argument were identified.

## Must-fix
- `SIGKILL` is used without the `signal.` prefix in the teardown of AC-4.6 (`test_reap_failure_is_a_verdict_within_the_drain_bound`) and AC-5.5 (`test_wait_after_kill_is_bounded`) — `real_killpg(pgid, SIGKILL)` will raise a `NameError` since `SIGKILL` is not imported directly (the helper imports `signal`, and earlier lines in the tests correctly use `signal.SIGKILL`). This crashes the test's teardown, masking test results and leaving processes unkilled.

## Should-fix
- AC-5.5's `test_wait_after_kill_is_bounded` states the wrapper "raises `subprocess.TimeoutExpired`" without arguments — the `subprocess.TimeoutExpired` constructor requires `cmd` and `timeout` positional arguments in Python 3.11; failing to provide them will raise a `TypeError` instead of simulating the timeout.

## Nit
- None
