AUDIT-audit-cycle-verb-design-v4-BEGIN
## Summary
The design for the `audit-cycle` verb is well-structured and aligns tightly with the specification and plan. It properly delegates assembly and dispatch to the shell, and collection and gating to the Python helper, ensuring exactly one verdict formatter. All 56 Acceptance Criteria (Axis C) are `implemented-as-written`. However, there are two missing context arguments in the pseudo-code invocations (Axis A) that would cause runtime failures if implemented exactly as written.

| AC | Classification | AC | Classification |
|---|---|---|---|
| AC-1.1 | implemented-as-written | AC-5.6 | implemented-as-written |
| AC-1.2 | implemented-as-written | AC-5.7 | implemented-as-written |
| AC-1.3 | implemented-as-written | AC-6.1 | implemented-as-written |
| AC-1.4 | implemented-as-written | AC-6.2 | implemented-as-written |
| AC-2.1 | implemented-as-written | AC-6.3 | implemented-as-written |
| AC-2.2 | implemented-as-written | AC-6.4 | implemented-as-written |
| AC-2.3 | implemented-as-written | AC-6.4b | implemented-as-written |
| AC-2.4 | implemented-as-written | AC-7.1 | implemented-as-written |
| AC-2.5 | implemented-as-written | AC-7.2 | implemented-as-written |
| AC-3.1 | implemented-as-written | AC-7.3 | implemented-as-written |
| AC-3.2 | implemented-as-written | AC-7.4 | implemented-as-written |
| AC-3.3 | implemented-as-written | AC-7.5 | implemented-as-written |
| AC-3.3b | implemented-as-written | AC-8.1 | implemented-as-written |
| AC-3.4 | implemented-as-written | AC-8.2 | implemented-as-written |
| AC-3.5 | implemented-as-written | AC-8.3 | implemented-as-written |
| AC-4.1 | implemented-as-written | AC-8.4 | implemented-as-written |
| AC-4.1b | implemented-as-written | AC-9.1 | implemented-as-written |
| AC-4.2 | implemented-as-written | AC-9.2 | implemented-as-written |
| AC-4.3 | implemented-as-written | AC-9.3 | implemented-as-written |
| AC-4.4 | implemented-as-written | AC-9.4 | implemented-as-written |
| AC-4.5 | implemented-as-written | AC-9.5 | implemented-as-written |
| AC-4.6 | implemented-as-written | AC-10.1 | implemented-as-written |
| AC-5.1 | implemented-as-written | AC-10.2 | implemented-as-written |
| AC-5.2 | implemented-as-written | AC-10.2b | implemented-as-written |
| AC-5.3 | implemented-as-written | AC-10.2c | implemented-as-written |
| AC-5.4 | implemented-as-written | AC-10.3 | implemented-as-written |
| AC-5.5 | implemented-as-written | AC-10.4 | implemented-as-written |
| | | AC-10.5 | implemented-as-written |
| | | AC-10.5b | implemented-as-written |

## Must-fix
- The `h_mad_assemble_audit.py` invocation in the Architecture Overview omits the context arguments (`--feature`, `--phase`, `--cycle`, `--project-root`). The plan explicitly requires these to be forwarded (Section: Scope), and assembly will fail without them. — This creates a hard gap (Axis A) where the pseudo-code contradicts the plan's forwarding requirement.
- The `no-pass form` of `h_mad_audit_cycle.py` is shown taking only `--halt-reason` and `--size-status`. It must also receive `--feature` to correctly format the `[H-MAD] <feature> audit-cycle <verdict>` marker line (AC-8.3). — Without `--feature`, the helper cannot emit the required marker line format on an assembly halt or prompt divergence, leading to a silent failure of the marker discipline invariant.

## Should-fix
None

## Nit
- In the Test Plan, `test_verb_clears_all_three_channels` states "both removed and asserted before dispatch". It is slightly ambiguous as there are *three* files to clear per pass (report, `.done`, and `out`); phrasing it as "all three removed" would be more precise.
AUDIT-audit-cycle-verb-design-v4-END
