## Summary
The plan is detailed and its fence, execution, and wire tests are generally specified at an implementable level. One remaining migration leaves `docsections` able to choose headings with a second, incompatible grammar before it reaches the new bounder.

## Must-fix
- Task 1 leaves `h-mad/tests/docsections.py:titled_section`s local `re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\\s*$", text)` intact while declaring `_fence_events` the sole owner of ATX-heading recognition — the call still independently selects the section start (including headings inside fences, seven-`#` headings, and a different closing-`#`/tab/indentation grammar) before delegating only the end bound. This violates the single-source contract and can make `docsections` select a different section than `extract`; move the start-heading lookup to a shared scanner-event consumer (exposed if necessary), then add a hostile `titled_section` test plus a connection/mutation guard that fails if its local heading matcher returns.

## Should-fix
- The paired documents specify incompatible scanner event protocols: this implementation plan requires `_FenceEvent.kind == "heading"` with `level`/compared `text` and makes both consumers use it, while the paired design §Scanning still says `_fence_events` yields open/close/body/prose and that heading lookup searches `prose` lines. Reconcile the design, plan, and mutation wording to one event model before implementation so the stated source provenance is real and tests do not encode two contracts.

## Nit
None
