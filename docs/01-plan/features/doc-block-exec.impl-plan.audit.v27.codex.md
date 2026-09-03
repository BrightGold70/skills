## Summary
The implementation plan is otherwise unusually concrete about task boundaries, exact mutation wiring, and fault-injection transport. One Task 1 grammar contradiction remains between full-form request recognition and the scanner grammar it claims to reuse.

## Must-fix
- Align `find_heading` full-form request detection with the stated CommonMark ATX predicate: the plan says the request uses the scanner’s own predicate, while Task 1 defines that predicate as `1–6 #` followed by a space, excluding the scanner’s accepted tab and end-of-line forms. Consequently valid headings such as `##\tText` and `##` can be scanned as headings but their corresponding full-form requests are treated as bare strings and cannot select them; add tab/EOL request cases plus a mutation that narrows the request predicate, and make the design/spec use the same grammar.

## Should-fix
None

## Nit
None
