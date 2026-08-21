## Summary
The plan demonstrates excellent adherence to the h-mad invariant rules, particularly in its rigorous test discrimination for connection enforcement and handling of the reap-first race condition. All functional requirements (FR-1 through FR-10) are addressed as specified. However, the plan contains a contradiction regarding how the `ASSEMBLE:` output is parsed given the new per-pass assembly design, and it leaves the absent-token behavior for assembly undefined.

| Functional Requirement | Classification |
|---|---|
| FR-1: One verb, one cycle | `implemented-as-written` |
| FR-2: Assembly is gated | `implemented-as-written` |
| FR-3: Two independent passes | `implemented-as-written` |
| FR-4: Report collection fallback | `implemented-as-written` |
| FR-5: Union gating | `implemented-as-written` |
| FR-6: Cannot-judge verdict | `implemented-as-written` |
| FR-7: Premise-check checklist | `implemented-as-written` |
| FR-8: Verdict line discipline | `implemented-as-written` |
| FR-9: Documentation | `implemented-as-written` |
| FR-10: Tests | `implemented-as-written` |

## Must-fix
- Contradiction in Assembly Output Parsing — The plan correctly identifies that `h_mad_assemble_audit.py` must run "once per pass" (yielding two executions). However, the implementation strategy describes the stdout parsing as if it only runs once ("The `ASSEMBLE:` line is parsed once, line-scoped, by the shell... taking the last match"). This contradicts the two-execution reality. The plan must clarify whether the shell parses both outputs, how it handles a scenario where one pass gets `PASS` and the other gets `HALT`, and which `size_status=` field is forwarded to the helper when there are two executions. (Axis A)
- Missing operational error definition for an absent `ASSEMBLE:` token — The plan explicitly defines that an absent `GATE:` token is treated as an operational error. However, it leaves the absent-token behavior for `ASSEMBLE:` undefined, stating only that "The verdict word routes the dispatch decision". Spec AC-2.5 strictly requires that an exit 0 with no `ASSEMBLE:` token be treated as an operational error, as it is the one case where silence would otherwise read as consent. (Axis A)

## Should-fix
None

## Nit
None
