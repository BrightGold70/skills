## Summary
The plan's counts, task graph, mutation inventory, and matcher corpus are internally well developed, but two prescribed verification steps cannot reliably pass against the intended checkout. Cross-document provenance and requirement labels also retain several non-blocking contradictions.

## Must-fix
- AC-3.14's prescribed `test_tail_pass_call_form_is_source_pinned` fails against the correct implementation — it flattens the entire wrapper and asserts `"if local tout=" not in flat`, while T3 requires a source comment containing exactly ``if local tout="$(...)"``; strip comment lines (or scope the negative assertion to executable code) before flattening so `local-masks-helper-rc` still kills the active-line mutation without rejecting the required rationale.
- AC-6.10 invokes `~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py` instead of the harness in the checkout — outside the symlinked author environment that path may be absent or may name a stale installation, so the required anchor sweep can fail operationally or validate with different harness code; use repo-relative `h-mad/scripts/h_mad_mutation_harness.py` as the other repository verification commands do.

## Should-fix
- The provenance/mapping prose is stale — the header cites design v1.33 although the paired design is v1.34, and T5 still says the design Components table omits the `:1046` Pass-number cross-reference even though the v1.34 table contains that row; update the citation and describe it as a mapped design component.
- The source plan and paired design still call the prose false-positive the wrong-pane class that FR-2 forbids — the spec defines FR-2 as exactly-one cardinality, while the corrected impl-plan identifies this as FR-1 / spec AC-1.4; sweep those two paired documents so traceability agrees.
- T4 says Pass 2 applies the "identical predicate" to `.preview` immediately after correctly stating that Passes 1-2 use prose-permissive `_agent_pv_re` while the tail pass uses `_agent_tail_re` — reword this as the same reject-before-selection rule or ordering, not the same matcher predicate.

## Nit
None
