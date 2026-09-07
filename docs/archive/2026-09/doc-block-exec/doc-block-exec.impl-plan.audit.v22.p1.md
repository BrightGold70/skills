## Summary
The implementation plan is mature, meticulously detailed, and highly consistent across its tasks. The exception taxonomy precisely aligns with the CLI verdict table, the exact file paths and typing are correct, and all mutation targets carry type-safe replacements.

## Must-fix
None

## Should-fix
None

## Nit
- In Task 3's `test_wait_after_kill_is_bounded` teardown description, `real_killpg(pgid, SIGKILL)` omits the `signal.` prefix, whereas the adjacent `os.kill(pid, signal.SIGKILL)` correctly includes it.
