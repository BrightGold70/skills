## Summary
The plan cleanly collapses the manual audit cycle into a single verb, satisfying all functional requirements from the spec. The decision to use per-pass gating rather than union concatenation is well-argued and structurally sound, and the connection mutation testing strategy precisely addresses the `Connection enforcement` invariant. However, there is a severe lifecycle race/deadlock between the backgrounded `exec` jobs and the 600s `report_wait.py` timeout that must be resolved.

| Requirement | Classification |
|---|---|
| FR-1: One verb, one cycle | `implemented-as-written` |
| FR-2: Assembly is gated | `implemented-as-written` |
| FR-3: Two independent passes | `implemented-as-written` |
| FR-4: Report collection fallback | `implemented-as-written` |
| FR-5: Union gating by per-pass | `implemented-as-written` |
| FR-6: Cannot-judge distinct verdict | `implemented-as-written` |
| FR-7: Premise-check checklist | `implemented-as-written` |
| FR-8: Verdict line & signal discipline | `implemented-as-written` |
| FR-9: Documentation & report-file | `implemented-as-written` |
| FR-10: Tests | `implemented-as-written` |

## Must-fix
- **Missing synchronization strategy between `exec` reaping and `report_wait.py`** — The plan states the `exec` passes are "dispatched in the background and reaped" and that the Python helper invokes `h_mad_report_wait.py` (which has a 600s timeout). This creates a hard gap:
  - If the shell `wait`s for the backgrounded `exec` jobs to exit *before* calling the Python helper, the agent is already dead. If the agent delivered via `--out` rather than `report-file`, `report_wait.py` will needlessly hang for its full 600s timeout waiting for a file that will never arrive.
  - If the shell calls the Python helper *before* reaping the jobs (while they run), `report_wait.py` will hang for 600s if an `exec` process crashes or exits early without writing the file, because `report_wait.py` monitors the file, not the PID.
  The plan must specify exactly how the lifecycle of the backgrounded `exec` jobs interleaves with the Python helper's 600s wait, and how to avoid a 10-minute hang on the fallback path or on agent crash.
- **Unverified state mutation on file removal** — The spec AC-3.3 and the plan state the verb "removes any pre-existing `<path>` and `<path>.done` before dispatching that pass". Under the `Mutation verification` invariant, a file removal is a state mutation and must be verified by re-reading the resulting state (e.g., asserting `[ ! -f <path> ]`), rather than trusting the exit code of `rm`.

## Should-fix
None

## Nit
None
