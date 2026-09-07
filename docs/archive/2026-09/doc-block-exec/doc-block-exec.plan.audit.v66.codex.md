## Summary
Axis C reconciliation finds every functional requirement addressed as written; no FR is restated or absent at plan granularity. The plan nevertheless leaves its shared heading-lookup API internally inconsistent, so the proposed `docsections` delegation cannot be implemented from this plan without inventing a normalization rule.

| FR | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- `find_heading` has no coherent input contract across the two planned consumers — the migration calls `dbe.extract(SKILL_MD, "## Second surface — the codex leg")`, matching the spec’s marked-heading selector, while `docsections.titled_section` is explicitly specified to pass its existing `heading` value, whose current public contract is text *after* the `#` marks. The API table only says a heading is “equal to `heading` (stripped)”; it never says whether callers pass ATX source (`## H`), visible text (`H`), or both, nor how level is resolved. That is a task-level type/normalization gap in the single authoritative selector: specify one canonical argument form (and the adapter/parsing at the other call site), plus discriminating tests for both callers, before implementation.

## Should-fix
None

## Nit
None
