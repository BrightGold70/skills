## Summary
The design carefully adheres to the plan's architectural boundaries and introduces a robust testing strategy (including essential connection mutations). However, it introduces significant internal contradictions on Axis A regarding which Python component parses the premise checklist bullets, and the CLI signature omits a required context argument. On Axis C, the collection logic for the report file has been appropriately narrowed from the spec to guard against torn writes.

| Acceptance Criteria | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4 | `implemented-as-written` |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5 | `implemented-as-written` |
| AC-3.1, AC-3.2, AC-3.3, AC-3.3b, AC-3.4, AC-3.5 | `implemented-as-written` |
| AC-4.1 | `restated` |
| AC-4.1b, AC-4.2, AC-4.3, AC-4.4, AC-4.4b, AC-4.5, AC-4.6 | `implemented-as-written` |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6, AC-5.7 | `implemented-as-written` |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.4b | `implemented-as-written` |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5 | `implemented-as-written` |
| AC-8.1, AC-8.2, AC-8.3, AC-8.4 | `implemented-as-written` |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | `implemented-as-written` |
| AC-10.1, AC-10.2, AC-10.2b, AC-10.2c, AC-10.3, AC-10.4, AC-10.5, AC-10.5b | `implemented-as-written` |

## Must-fix
- Contradiction in bullet extraction responsibilities between `gate()` and `premise_items()` — The signature for `gate()` claims it returns `must_fix_bullets` which populate `PassResult.findings` (`→ (verdict, must, should, must_fix_bullets)`), implying `gate()` extracts the bullets. However, the `premise_items()` section states it "imports `h_mad_audit_gate`'s own primitives" to extract bullets, applies the prose fall-back itself, and asserts `len(items_for_pass) == pass.must`. If `gate()` extracts the bullets, `premise_items()` shouldn't re-parse them using the primitives; if `premise_items()` parses them, `gate()` shouldn't return them as a 4-tuple. This leaves the data model and extraction responsibility unresolved (Axis A).
- Missing `--passes` argument in Full helper invocation signature — The "Full helper invocation" block explicitly claims "(every context arg explicit; nothing inferred)" but omits the `--passes K` argument. However, the text immediately below states "Every context arg is forwarded unconditionally, including in no-pass mode: --passes because render() prints passes=K", which means the full invocation must also receive it. This contradicts the "nothing inferred" claim and leaves the helper without the total pass count in normal execution (Axis A).
- Spec AC-4.1 `restated` — Spec AC-4.1 requires "A non-empty file is delivered=report-file with no wait at all." The design restates this as "report_path is non-empty and report_path.done exists". This is a narrower, safer reading that explicitly requires the `.done` sentinel to protect against torn writes, but it must be reconciled with the spec before the gate clears (Axis C).

## Should-fix
None

## Nit
None
