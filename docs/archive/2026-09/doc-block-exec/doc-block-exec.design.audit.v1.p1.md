## Summary
The design implements the FRs and covers all acceptance criteria from the spec, correctly opting for a narrow opt-in selection process and isolating execution in a temporary working directory. All 35 ACs are mapped and implemented as written. However, the design contains contradictions regarding the return type of the extractor and the parsing logic for quoted fences, and it introduces a load-bearing assumption about process group reaping without citing empirical verification.

| AC | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-1.4 | `implemented-as-written` |
| AC-1.5 | `implemented-as-written` |
| AC-1.6 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-2.4 | `implemented-as-written` |
| AC-2.5 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-3.4 | `implemented-as-written` |
| AC-3.5 | `implemented-as-written` |
| AC-3.6 | `implemented-as-written` |
| AC-3.7 | `implemented-as-written` |
| AC-3.8 | `implemented-as-written` |
| AC-3.9 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-4.4 | `implemented-as-written` |
| AC-4.5 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |
| AC-5.2 | `implemented-as-written` |
| AC-5.3 | `implemented-as-written` |
| AC-5.4 | `implemented-as-written` |
| AC-6.1 | `implemented-as-written` |
| AC-6.2 | `implemented-as-written` |
| AC-6.3 | `implemented-as-written` |
| AC-6.4 | `implemented-as-written` |
| AC-6.5 | `implemented-as-written` |
| AC-6.6 | `implemented-as-written` |

## Must-fix
- `extract` return type contradiction — The API table defines `extract` as returning `list[Block]`, and the Architecture Overview implies it returns all candidate blocks for the caller to evaluate (`extract() -> [Block, …]`, then `exactly one? no -> NOT_FOUND | AMBIGUOUS`). However, the Error Handling Strategy states that `extract` itself raises `BlockNotFound` and `AmbiguousBlock`. It cannot simultaneously return a list of multiple candidates AND raise errors when the count is not exactly one. The return type should be a single `Block` if it performs the resolution and raises.
- Broken scanner logic for nested fences — The design claims that a simple boolean toggle ("A line whose lstrip starts with ``` toggles the state") makes AC-1.6 (a fence quoting a tagged fence) fall out for free. However, if an outer block quotes an inner fence, the inner fence's opener will toggle the `in_fence` state back to `False`, causing the parser to treat it as a closing tag and misinterpreting all subsequent lines. To support quoted fences safely, the scanner must match the closing fence's backtick count to the opening fence's count.
- Unverified process group reaping (Assumption verification) — The design claims that `subprocess.Popen(..., start_new_session=True)` combined with `os.killpg(...)` successfully reaps grandchildren on a timeout without leaving orphans. This is a load-bearing assumption introduced in the design to satisfy AC-5.2, but the design fails to execute a throwaway command and cite the observed output proving it behaves as intended on the target environment, violating the Assumption Verification invariant.

## Should-fix
None

## Nit
None
