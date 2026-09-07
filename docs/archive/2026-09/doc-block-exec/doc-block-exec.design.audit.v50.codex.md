## Summary
Axis C reconciliation: every spec acceptance criterion is implemented-as-written in the design; there are no restated or absent ACs.

| Spec ACs | Classification |
|---|---|
| AC-1.1–AC-1.9 | implemented-as-written |
| AC-2.1–AC-2.8 | implemented-as-written |
| AC-3.1–AC-3.14 | implemented-as-written |
| AC-4.1–AC-4.6 | implemented-as-written |
| AC-5.1–AC-5.6 | implemented-as-written |
| AC-6.1–AC-6.6 | implemented-as-written |

The design is otherwise cross-document consistent and retains the required single-source, mutation, and connection-enforcement mechanisms.

## Must-fix
- The two real AC-5.5 timeout-race fixtures are not executable as specified: `test_timeout_survives_a_group_that_already_emptied` says its block is `python3 esc.py & exit 0`, and the drain test likewise relies on a Python escapee, but `run_block` always creates a fresh private cwd and the plan never states a preamble or inline `python3 -c` program that creates `esc.py` there before launch. A file created by the test in `tmp_path` is not in the child cwd, so the stated block instead fails immediately and cannot hold stdout, produce the zombie/group-empty race, or kill `poll-before-killpg-removed` / `killpg-esrch-uncaught`; specify the exact executable fixture construction (including the absolute PID-file substitution and cleanup) in Task 3 and the Test Plan.

## Should-fix
None

## Nit
None
