## Summary
The plan cleanly addresses the prior audit findings, correctly swapping the implementation order to prevent an unwritable state window and accurately placing the cross-referenced ACs. However, the design document was not updated to reflect the new implementation order, leaving a cross-doc contradiction, and the post-write verification prescribed in Task 2 uses a schema validator that will silently pass if the mutation drops.

## Must-fix
- **Mutation verification violation (Task 2 AC-4.5)** — The protocol instructs operators to verify the state mutation landed using `h_mad_state_validate.py --strict-only`. Because the schema edit in Task 1 does not add `archreview` to the `required` array (which would break backward compatibility), a silent write failure that leaves the field absent will still perfectly pass strict validation. To verify the write landed, the protocol must explicitly read the *thing it was supposed to change* (e.g., via `h_mad_state_read.py <state> --feature <f> | jq -r .archreview`).
- **Cross-doc consistency (Implementation Order contradiction)** — The Implementation Plan explicitly corrects the landing order to `FR-3 -> FR-4` to prevent a window where the documented protocol instructs writing an unwritable schema value. However, the Design document's "Implementation Order" section was never updated and still mandates `1. FR-4 ... 2. FR-3`. The Design document must be updated to align with the safe landing order to remove this contradiction.

## Should-fix
None

## Nit
- **Brittle bash quoting in AC-1.6** — The python snippet embedded in a double-quoted bash string relies on bash unescaping `\"<ABSENT>\"` into `"<ABSENT>"` before Python parses the f-string. While technically functional, this is fragile compared to the Design document's approach of using `chr(60)+...` to bypass quoting collisions entirely.
