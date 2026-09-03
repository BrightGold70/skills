## Summary
The design implements every source-spec acceptance criterion as written; the reconciliation matrix below contains no restatement or absence. Its remaining hard gap is in the planned real-process cleanup for the injected reap failure: the test requires a process handle that `run_block` does not expose and the plan does not arrange to capture.

| Spec AC identifiers | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- The AC-4.6 `killpg`-PermissionError test is not executable as specified: `run_block` owns its local `Popen`, raises `LaunchFailed`, and exposes neither that object nor a reaping hook, yet the proposed test says its `finally` calls `proc.wait()` on a handle it holds. — Without an explicitly specified recording pass-through around the real `Popen` (or an equivalent test-only handle seam), the test cannot perform the required reap or prove the asserted postcondition; it can leak a zombie/live process and violates the real-process cleanup and test-discrimination contract. State that seam, its restoration, and the exact teardown ordering in the design and test plan.

## Should-fix
- Specify the first-stream-write-failure branch as precisely as the documented stderr-second failure branch. — The design defines `written: stdout` / `failed: stderr` only when stderr fails; it does not state whether a stdout failure suppresses stderr, what partial-state details are emitted, or which registry rows cover that path, leaving AC-3.8 implementation and registry coverage needlessly ambiguous.

## Nit
None
