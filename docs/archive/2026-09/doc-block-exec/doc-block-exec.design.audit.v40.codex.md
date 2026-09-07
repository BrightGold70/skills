## Summary
Axis C reconciliation: every listed spec acceptance criterion is implemented-as-written; none is restated or absent.

| Spec ACs | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

The design nevertheless has two blocking gaps in the executable launch contract and its required parity guard.

## Must-fix
- The normative `Popen(["bash", *flags, "-c", ...])` launch omits `cwd=cwd` — creating and chmodding a temporary directory does not make it the child process’s working directory; an implementation following the only concrete launch signature runs in the caller/repository cwd, violating AC-3.1 and AC-3.2. Specify `cwd=cwd` in the architecture and execution contract, and anchor it with a mutation that removes/replaces that keyword.
- `test_extract_and_bounder_agree_on_every_hostile_fixture` is unimplementable as stated — `extract` exposes only tagged backtick/bash candidates, while `fence_aware_end` returns one boundary offset and necessarily skips all fence kinds (including the hostile tilde fence); therefore their “set of candidate openers” and “set of fence spans” cannot be observed through these APIs or be equal. Replace it with an observable shared-scanner event-trace assertion, or with per-consumer boundary/candidate assertions, and mutation-test that guard.

## Should-fix
None

## Nit
None
