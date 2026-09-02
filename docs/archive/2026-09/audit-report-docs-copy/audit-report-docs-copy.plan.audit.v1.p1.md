## Summary
The plan comprehensively addresses all functional requirements from the spec, correctly threading the `surface` token and ensuring that the transport file cannot be scored directly. It properly plans for bootstrapping the codex recipe on the live HemaSuite codebase by anticipating the worktree divergence.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- Connection enforcement gap for the wrapper verb — The plan introduces `hmad-dispatch collect-report` to route to `h_mad_collect_report.py` (FR-4) but does not specify a test for this delegation in the Deliverables. Per the "Connection enforcement" base invariant, any routing connection must ship a test that fails when the connection is severed (e.g., verifying `hmad-dispatch collect-report` correctly execs the Python script).

## Should-fix
None

## Nit
- While the plan correctly covers AC-2.8 (removing the `.done` marker), ensure the corresponding test explicitly stats the filesystem to confirm the marker's absence, fulfilling the "Mutation verification" invariant rather than relying on exit codes.
