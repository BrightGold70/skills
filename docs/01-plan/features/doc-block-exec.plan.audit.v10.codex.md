## Summary

The plan covers every functional requirement at plan granularity, but its execution-bound design conflicts with a non-overridable base invariant and leaves the process-group setup required for its timeout guarantee unspecified. It also repeats a premise about the fixture preamble that the source spec's controlled measurement disproves.

| Requirement | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix

- FR-5 plans a private Python/process-group watchdog rather than the required shared time-bounder — the plan calls for `killpg(proc.pid, …)` and says the bound is Python's own, while the binding Base `Portable time bounds` invariant requires `hmad-dispatch run --timeout <s> -- <cmd...>` wherever it is reachable. `hmad-dispatch` is present in this same skill and already owns the process-group watchdog, so the current strategy violates the invariant and duplicates a time-bound implementation that can diverge. Specify the helper's exact use of that wrapper (including capture/rc mapping) or revise the governing invariant before implementation.
- The timeout plan never establishes the launched process group it intends to kill — `killpg(proc.pid, …)` reaches the child group only if the child was made its leader (for example `subprocess.Popen(..., start_new_session=True)`); without that setup the PID normally is not a process-group ID and AC-5.2 can fail or kill nothing. Name the exact launch, TERM/grace/KILL, `wait`/`communicate`, and tempdir-cleanup sequence so the in-group descendant guarantee is implementable and mutation-testable.
- The preamble rationale contradicts the source spec's controlled result — the plan says an unset `COLLECT_OUT` “aborts on `unbound variable` before the recipe is exercised,” but AC-3.11 records `WITHOUT preamble: rc=0`, the `report_not_collected` halt, and only an unbound-variable diagnostic; the source spec says the real limitation is inability to reach `GATE: PASS`. Replace the false causal description with that measured behavior, retaining the preamble boundary because it is necessary for the delivered-path test.

## Should-fix

None

## Nit

None
