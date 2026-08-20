AUDIT-audit-cycle-verb-design-v11-BEGIN
## Summary
The design for the `audit-cycle-verb` provides a comprehensive and invariant-compliant blueprint that cleanly partitions shell orchestration from Python logic. It adheres rigorously to the single-source contract and operator-override preservation, ensuring proper signal discipline and test discrimination across all boundaries. All 53 Acceptance Criteria from the Spec have been implemented as written, with no restated or absent requirements, as confirmed in the Axis C reconciliation table below.

**Axis C: Spec Reconciliation**

| Spec AC | Status | Notes |
|---|---|---|
| AC-1.1 to AC-1.4 | `implemented-as-written` | Assembly and shell limits accurately restricted. |
| AC-2.1 to AC-2.5 | `implemented-as-written` | Gating, HALT mapping, and operational error constraints observed. |
| AC-3.1 to AC-3.5 | `implemented-as-written` | Pass counts, path isolation, channel clearing, and prompt identity enforced. |
| AC-4.1 to AC-4.6 | `implemented-as-written` | Four-outcome collection ladder and fallback strictly follow spec. |
| AC-5.1 to AC-5.7 | `implemented-as-written` | Per-pass invocation handles double counting, `INVALID` routing, and `--ack-file`. |
| AC-6.1 to AC-6.4b | `implemented-as-written` | `UNVERIFIED` formatting correctly drops counts and conditionally drops channels. |
| AC-7.1 to AC-7.5 | `implemented-as-written` | Premise checklist extracts cited must-fixes independently of adjudication. |
| AC-8.1 to AC-8.4 | `implemented-as-written` | Token shaping and `[H-MAD]` rendering are cleanly encapsulated. |
| AC-9.1 to AC-9.5 | `implemented-as-written` | Docs changes and bidirectional token pinning fully defined. |
| AC-10.1 to AC-10.5b | `implemented-as-written` | Mutation specs and delayed-delivery test strategies rigorously mapped. |

## Must-fix
- **Axis A Contradiction - `gate()` extraction model**: Under the `premise_items` section, the design states that "`gate()` already reads the collected report to obtain the token, so it extracts the `## Must-fix` findings in the same pass". This contradicts the earlier *`gate` — token* section, which correctly observes that the helper runs `h_mad_audit_gate.py <collected>` as a subprocess and reads the stdout for the token. The report file itself contains the Markdown text, not the `GATE:` token. If the helper is extracting findings using imported primitives, it is opening the file in a second pass independently of the subprocess that obtained the token. This contradiction describes an impossible data model and must be corrected so the implementer understands the token and findings originate from two distinct read pathways.

## Should-fix
None

## Nit
None
AUDIT-audit-cycle-verb-design-v11-END
