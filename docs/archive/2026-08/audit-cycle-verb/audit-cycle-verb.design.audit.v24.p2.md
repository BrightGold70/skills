AUDIT-audit-cycle-verb-design-v24-BEGIN
## Summary
The design is exceptionally thorough, perfectly mapping the shell/Python boundary to the specified requirements without a single architectural contradiction. It fully addresses all edge cases surrounding missing tokens, torn writes, sub-process error codes, and the distinction between cannot-judge (`UNVERIFIED`) and operational errors. Every test and guard mutation requirement—including those for the shell—is accounted for, ensuring high confidence in connection enforcement and test discrimination.

| AC | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-1.4 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
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
| AC-4.4 | `implemented-as-written` |
| AC-4.4b | `implemented-as-written` |
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
| AC-6.4b | `implemented-as-written` |
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
| AC-9.5 | `implemented-as-written` |
| AC-10.1 | `implemented-as-written` |
| AC-10.2 | `implemented-as-written` |
| AC-10.2b | `implemented-as-written` |
| AC-10.2c | `implemented-as-written` |
| AC-10.3 | `implemented-as-written` |
| AC-10.4 | `implemented-as-written` |
| AC-10.5 | `implemented-as-written` |
| AC-10.5b | `implemented-as-written` |

## Must-fix
None

## Should-fix
None

## Nit
- In the Test Plan table, the scenario for `test_collect_report_file_present` reads "report non-empty at reap". Given the intense focus earlier in the design (and in v1.20 history) on the `.done` marker being load-bearing to prevent torn writes, explicitly stating "report non-empty and `.done` present at reap" would make the fixture's state perfectly unambiguous.
- AC-8.1 dictates the verdict line format as `AUDITCYCLE: (PASS|FAIL) must=<N> should=<M> passes=<K>` with per-pass counts and `delivered=` fields. The design includes `size_status=verified` on this line. While this is a highly logical place for it and satisfies AC-2.3 (echoing the size status on the verb's output), it technically extends the format prescribed by AC-8.1.
AUDIT-audit-cycle-verb-design-v24-END
