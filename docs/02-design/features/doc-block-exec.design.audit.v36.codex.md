## Summary
All acceptance criteria except AC-1.8 are implemented-as-written; the proposed prefix-state mechanism silently narrows AC-1.8 despite restating its arbitrary-offset promise. The design otherwise aligns with the plan and the stated invariant contracts.

| AC(s) | Classification |
|---|---|
| AC-1.1–1.7 | implemented-as-written |
| AC-1.8 | restated |
| AC-1.9 | implemented-as-written |
| AC-2.1–2.8 | implemented-as-written |
| AC-3.1–3.14 | implemented-as-written |
| AC-4.1–4.6 | implemented-as-written |
| AC-5.1–5.6 | implemented-as-written |
| AC-6.1–6.6 | implemented-as-written |

## Must-fix
- AC-1.8’s arbitrary-offset bounder contract is narrowed by the proposed prefix scan — the spec says `start may lie anywhere -- inside an open fence included`, while the design says fence state is established over `text[:start]` first. If `start` falls immediately after the marker run in a non-closing line such as ````trailing`, the truncated prefix makes that line look like a valid closer (only blanks follow), even though the complete line has trailing text; the next fenced `#` can then terminate the section. Establish state using complete source lines through the line containing `start` (then begin considering boundaries after `start`) and add a hostile counterexample plus a named mutation, so the mechanism actually meets AC-1.8 rather than only claiming it.

## Should-fix
None

## Nit
None
