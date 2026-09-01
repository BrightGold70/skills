## Summary
The task ordering, file paths, cross-document behavior, and 38-node RED accounting are coherent, but the timeout test scaffold is still not dispatch-ready. One acceptance bound rejects the correct implementation, while two claimed timeout mutations are not discriminated by the tests assigned to them.

## Must-fix
- AC-2.6's required `elapsed >= 0.5 s` rejects the correct `_cmd_run` implementation — the plan itself says the integer-valued `SECONDS` deadline may expire anywhere within the current second, and a read-only controlled run of the prescribed bounder produced a valid rc-124 timeout in **0.376 s**. Remove the nondeterministic lower bound and prove that the read was attempted with a capture/source assertion (the existing `< 2.5 s` upper bound still kills the unbounded direct-call mutant), or change the fixture to a bound whose guaranteed timing interval cannot cross the assertion; otherwise a correct implementation can fail its AC, violating Test discrimination.
- `harness-ambient-timeout-not-scrubbed` is an equivalent mutant under AC-2.5 as written — with the scrub, the child drops the parent's value `9` and a healthy read completes under the default `2`; without the scrub, the same healthy read completes under inherited value `9`. Because the node asserts only rc 0/completion, deleting `e.pop("HMAD_TAIL_READ_TIMEOUT", None)` changes no observable and `MUTATION: ALL_CAUGHT` is unreachable. Use a parent seed whose inheritance is observably wrong (for example an invalid/zero value while a healthy read succeeds after the proper scrub), and correct the mutation's stale reference to nonexistent `AC-2.1b`.
- The `HMAD_TAIL_READ_TIMEOUT=1` override has no mutation that replaces `${HMAD_TAIL_READ_TIMEOUT:-2}` with the fixed default `2`, and AC-2.6 does not discriminate that replacement — six controlled `--timeout 2 -- sleep 3` runs completed at **1.936–2.232 s**, all inside AC-2.6's `>= 0.5 s and < 2.5 s` window with the same mapped rc 1. Add an override-ignored mutation and a deterministic assertion of the value passed to `_cmd_run`; otherwise the explicit override contract is green without being enforced, breaching Test discrimination.

## Should-fix
- AC-2.7's regex is described as a command-position predicate but misses valid quoted command invocations such as `"timeout" 2 orca ...` and `'gtimeout' 2 orca ...` — add these to the reject-direction probe corpus or narrow the AC's claim to the syntax the predicate actually recognizes.
- Task 6 says five mutations target “T2's helper guards,” although `harness-ambient-timeout-not-scrubbed` mutates the Python test harness, and its `_mechanism` text still names `AC-2.1b` after that node was folded into AC-2.5 — align the prose and identifier with the test-name contract.

## Nit
None
