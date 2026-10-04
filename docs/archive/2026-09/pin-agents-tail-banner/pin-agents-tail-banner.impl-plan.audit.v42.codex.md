## Summary
The task graph, RED split, wire declarations, and 38-entry mutation inventory re-derive cleanly, but the normative tail matcher is wider than the safety grammar the plan and design claim. One cross-document provenance/mapping row is also stale after the latest design revision.

## Must-fix
- `_agent_tail_re` accepts malformed and non-dotted pseudo-versions that its own rationale says must decline — the prescribed Codex arm makes `\(?` and `\)?` independently optional and uses `[0-9]+(\.[0-9]+)*`, while the agy version arms also permit zero dots. Executing the block shows `OpenAI Codex (v0.145.0`, `OpenAI Codex v0.145.0)`, `OpenAI Codex 2026`, and `Gemini 3.1 Pro (2026)` all match; these are outside the design's paired-parenthesis/dotted-numeric grammar and can turn historical prose or release headings into wrong-pane identity evidence, violating FR-1 / spec AC-1.4. Express paired Codex forms as alternatives, require the documented dotted shape where intended, and add these boundary cases plus discriminating mutations to AC-2.12 before trusting the 24/12 corpus.

## Should-fix
- The design provenance/mapping is one revision stale — the header cites design v1.34 although the paired design now ends at v1.35, and the mapping row describes design step 1 as only `_orca_tail_sig` even though the current step ships both `_orca_tail_sig` and `_agent_tail_re`; update both so dispatchers do not read an incomplete source-to-task mapping.

## Nit
None
