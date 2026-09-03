## Summary
The design implements the `doc-block-exec` helper and wire migration exactly as specified, comprehensively covering all 46 acceptance criteria including the updated timeout races and verified cleanup. Axis C reconciliation confirms all ACs are implemented-as-written. However, there is a critical contradiction under Axis A regarding how substitution is applied to the block text during composition, which would result in substitutions being ignored.

| AC | Classification |
|---|---|
| AC-1.1 – 1.9 | implemented-as-written |
| AC-2.1 – 2.7 | implemented-as-written |
| AC-3.1 – 3.14 | implemented-as-written |
| AC-4.1 – 4.5 | implemented-as-written |
| AC-5.1 – 5.5 | implemented-as-written |
| AC-6.1 – 6.6 | implemented-as-written |

## Must-fix
- Contradiction in substitution and text composition (Axis A) — The Architecture Overview shows `substitute()` producing `text'` which is then executed. However, the API section defines `run_block` with a `subs` parameter, and the composition rule explicitly states: "Composition is `preamble.rstrip('\n') + '\n' + block.text`". Using `block.text` directly ignores the substitution step entirely, breaking FR-2. If `run_block` performs the substitution internally using the `subs` parameter, it must compose the preamble with the *substituted* result, not the original `block.text`. (Note: Spec AC-3.11 contains this same `block.text` phrasing, but the design must resolve the contradiction to ensure the executed block actually contains the substituted text).

## Should-fix
None

## Nit
None
