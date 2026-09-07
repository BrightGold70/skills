## Summary
Axis C reconciliation finds all 49 acceptance criteria implemented-as-written; none is restated or absent.

| Spec ACs | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

The design is otherwise aligned with the plan and invariant set, but its post-spawn outcome taxonomy and its real-process fault-test teardown are internally inconsistent.

## Must-fix
- The claim that “Exactly four non-`RAN` outcomes can follow a spawn” omits `UNREADABLE reason=stream_close_failed` — later the design explicitly makes a backstop-close failure after a timed-out spawned block outrank `TIMEOUT` and emit that fifth outcome. The authoritative precedence/taxonomy must include this reachable post-spawn outcome (and its relation to `CLEANUP_FAILED`/`LAUNCH_FAILED`) so implementation and the verdict-table test cannot implement incompatible state machines.
- The AC-4.6 reap-failure test cannot perform the stated “real `os.killpg`” teardown after `monkeypatch.setattr(dbe.os, "killpg", fake)` unless it captures the original function first — `dbe.os` is the process-global `os` module, so both the stated kill and the final `killpg(pgid, 0)` assertion otherwise call the fake. Specify `real_killpg = os.killpg` before patching and use it for teardown/verification; without that, the named fault test can fail its cleanup or leak the live `sleep`, contradicting its process-reaping claim.

## Should-fix
- Make artifact verification explicitly per-stream and immediately after each `_final_write`: a silent stdout no-op is diagnosed only by read-back, while the current wording can be read as writing stderr before checking stdout. State and test that a stdout verification failure yields `failed: stdout` / `skipped: stderr` and leaves the stderr artifact untouched, preserving AC-3.8’s first-stream failure rule for the mutation-verification path too.

## Nit
None
