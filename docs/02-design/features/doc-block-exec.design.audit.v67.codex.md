## Summary
Axis C reconciliation finds every spec acceptance criterion implemented as written; the table enumerates all 49 criteria. The design nevertheless leaves its machine-consumed stdout token vulnerable to newline injection from raw caller-controlled diagnostic fields.

| Acceptance criteria (each) | Classification |
|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7, AC-1.8, AC-1.9 | implemented-as-written |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7, AC-2.8 | implemented-as-written |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7, AC-3.8, AC-3.9, AC-3.10, AC-3.11, AC-3.12, AC-3.13, AC-3.14 | implemented-as-written |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6 | implemented-as-written |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | implemented-as-written |

## Must-fix
- Raw diagnostic interpolation can forge verdict lines — the design prints caller/document-controlled values verbatim in fields such as `heading=<h>`, `BAD_SUBST arg=<raw>`, `missing_key: <k>`, and stream-path leftovers. A newline-containing argument/key can add a second `DOCBLOCK:` line (including a forged `RAN rc=` line), contradicting the stated one-line verdict contract and breaking the base audit-gate signal discipline for machine consumers. Specify a single-line escaping/encoding rule for every emitted dynamic field and add CLI tests that prove newline-bearing inputs cannot create another token line.

## Should-fix
None

## Nit
None
