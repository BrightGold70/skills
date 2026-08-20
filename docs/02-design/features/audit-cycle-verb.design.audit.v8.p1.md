AUDIT-audit-cycle-verb-design-v8-BEGIN
## Summary
The design meticulously translates the specification into a concrete architecture, honoring every AC and base invariant. The division of responsibilities between shell and Python ensures that operational errors are trapped early and that the canonical verdict format has precisely one source of truth. The test strategy is exceptionally strong, covering connection enforcement and providing condition-creating fixtures for shell guards.

### Axis C: Spec Reconciliation

| Spec ID | Status | Notes |
|---|---|---|
| AC-1.1 – AC-1.4 | `implemented-as-written` | Handled via linear shell path, stubbed dispatch counts, and early phase validation. |
| AC-2.1 – AC-2.5 | `implemented-as-written` | Assembly tokens and exit codes govern dispatch decisions; HALT routed to no-pass mode. |
| AC-3.1 – AC-3.5 | `implemented-as-written` | K-pass loop validates bounds; per-pass `--out`/`--log`/report paths isolate streams. |
| AC-4.1 – AC-4.6 | `implemented-as-written` | Reap-first pattern bypasses wait when report exists; `delivered=none` fallback implemented. |
| AC-5.1 – AC-5.7 | `implemented-as-written` | Per-pass gating prevents under-counts; `GATE: INVALID` correctly bypasses counts. |
| AC-6.1 – AC-6.4b | `implemented-as-written` | Cannot-judge explicitly drops counts; reasons distinguished and `delivered=` correctly masked/shown. |
| AC-7.1 – AC-7.5 | `implemented-as-written` | Checklists extracted without resolving files; omission on PASS verified. |
| AC-8.1 – AC-8.4 | `implemented-as-written` | Single `AUDITCYCLE:` string emitted; non-zero exits reserved for operational failures. |
| AC-9.1 – AC-9.5 | `implemented-as-written` | SKILL.md updates and bidirectional docs token pin are included. |
| AC-10.1 – AC-10.5b | `implemented-as-written` | Stub exemptions for real-gate testing and shell-guard fixtures are defined. |

## Must-fix
None

## Should-fix
- Ensure explicit operational error propagation from sub-helpers — The design states that `h_mad_report_wait.py` and `h_mad_extract_report.py` are executed by the Python helper, but does not specify how their operational errors (non-zero exits) are handled. If `subprocess.run(check=True)` isn't explicitly used for these invocations, a crash in the extraction toolchain might be silently swallowed as an empty output (`delivered=none`), yielding a benign `UNVERIFIED` cycle instead of a hard operational crash. Ensure the implementation raises on non-zero exit for these scripts (while continuing to handle exit 2 correctly for the gate).

## Nit
- Omission of `--passes` in the full helper invocation example — The design explicitly states that "Every context arg is forwarded unconditionally, including in no-pass mode: --passes", but `--passes` is omitted from the `Full helper invocation` CLI signature snippet for the normal flow. It should be added to the example for consistency.
AUDIT-audit-cycle-verb-design-v8-END
