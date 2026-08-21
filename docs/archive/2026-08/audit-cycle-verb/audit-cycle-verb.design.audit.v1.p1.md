## Summary
The design correctly structures the `audit-cycle` verb into a shell orchestrator and a Python helper, maintaining process isolation and accurately addressing the gating requirements. However, it drops several requirements specified in the spec, notably the aggregation and forwarding of `size_status`, the forwarding of essential CLI context (such as `--project-root` and `--ack-file`) across the shell-Python boundary, and explicit constraints against looping or accepting invalid phase arguments.

| Spec AC | Classification |
|---|---|
| AC-1.1 | `absent` |
| AC-1.2 | `absent` |
| AC-1.3 | `absent` |
| AC-1.4 | `absent` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `restated` |
| AC-2.4 | `implemented-as-written` |
| AC-2.5 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-3.3b | `implemented-as-written` |
| AC-3.4 | `implemented-as-written` |
| AC-3.5 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.1b | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-4.4 | `restated` |
| AC-4.5 | `implemented-as-written` |
| AC-4.6 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |
| AC-5.2 | `implemented-as-written` |
| AC-5.3 | `implemented-as-written` |
| AC-5.4 | `implemented-as-written` |
| AC-5.5 | `implemented-as-written` |
| AC-5.6 | `implemented-as-written` |
| AC-5.7 | `implemented-as-written` |
| AC-6.1 | `implemented-as-written` |
| AC-6.2 | `implemented-as-written` |
| AC-6.3 | `implemented-as-written` |
| AC-6.4 | `implemented-as-written` |
| AC-7.1 | `implemented-as-written` |
| AC-7.2 | `implemented-as-written` |
| AC-7.3 | `implemented-as-written` |
| AC-7.4 | `implemented-as-written` |
| AC-7.5 | `implemented-as-written` |
| AC-8.1 | `implemented-as-written` |
| AC-8.2 | `implemented-as-written` |
| AC-8.3 | `implemented-as-written` |
| AC-8.4 | `implemented-as-written` |
| AC-9.1 | `implemented-as-written` |
| AC-9.2 | `implemented-as-written` |
| AC-9.3 | `implemented-as-written` |
| AC-9.4 | `implemented-as-written` |
| AC-9.5 | `absent` |
| AC-10.1 | `implemented-as-written` |
| AC-10.2 | `implemented-as-written` |
| AC-10.2b | `implemented-as-written` |
| AC-10.2c | `implemented-as-written` |
| AC-10.3 | `implemented-as-written` |
| AC-10.4 | `implemented-as-written` |
| AC-10.5 | `implemented-as-written` |
| AC-10.5b | `implemented-as-written` |

## Must-fix
- **Spec AC-1.1 absent** — The design does not explicitly address the requirement that the verb exits without re-invoking itself (i.e., avoiding an implicit loop).
- **Spec AC-1.2 absent** — The design omits the test to assert that on a FAIL verdict, the verb makes no further `exec agy` dispatch.
- **Spec AC-1.3 absent** — The design does not explicitly state that it writes no files under `docs/01-plan/` or `docs/02-design/` other than the per-pass audit reports.
- **Spec AC-1.4 absent** — The design omits explicit validation to reject unknown `--phase` values before any dispatch.
- **Spec AC-2.3 restated** — Spec: "The size_status= field is echoed on the verb's own output... With multiple passes the worst value across them is reported". Design: Omits how the shell parses `size_status` from the `ASSEMBLE:` tokens and computes the worst value to pass to the helper. This is a gap because the helper cannot report it without receiving it.
- **Spec AC-4.4 restated** — Spec: "...and the paths are named on the verb's output." Design: Example outputs show the token line, but do not specify how or where the report paths are named on stdout. This drops an observability requirement.
- **Spec AC-9.5 absent** — The design does not mention updating `SKILL.md` to state that `audit-cycle` runs one cycle and that the revision loop remains the orchestrator's.
- **Gap: CLI context not forwarded across boundary** — The Python helper `h_mad_audit_cycle.py` is invoked by the shell with `--pass <i>...`, but essential context args (`--feature`, `--phase`, `--cycle`, `--grace`, `--ack-file`, `--project-root`, `--size-status`) are missing from the specified shell invocation signature.
- **Cross-doc contradiction: `--project-root` omitted from fallback** — The Plan stated `--project-root` is forwarded to `h_mad_extract_report.py`. The Design explicitly runs `h_mad_extract_report.py <out_path> --feature --phase --cycle --after-marker` in step 3, dropping `--project-root`.

## Should-fix
None

## Nit
None
