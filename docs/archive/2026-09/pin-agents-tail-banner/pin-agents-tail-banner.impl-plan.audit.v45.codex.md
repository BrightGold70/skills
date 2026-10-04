AUDIT-pin-agents-tail-banner-impl-plan-v45-BEGIN
## Summary
The task graph, 45-node RED table, and 39-entry mutation spec remain internally coherent. The normative matcher still admits unmeasured prose-shaped lines outside the paired design's claimed grammar, so the FR-1 wrong-pane guard is not closed.

## Must-fix
- `_agent_tail_re` is wider than both its stated grammar and its 29-negative corpus — executing the prescribed block matches `> OpenAI Codex`, `: OpenAI Codex`, `| model: gpt-5.6-terra`, and the symmetric agy forms because `[│|┃╎┆:>[:space:]]` admits Markdown/log punctuation, while the design says the prefix is whitespace or box-drawing only and the only prefixed positive control uses `│`. The codex arm also uses `[^[:space:]]*` after `·`, so `gpt-5.6-terra high ·` matches although the design requires `·` plus a cwd. Historical shell output containing a Markdown blockquote/table cell can therefore become unique identity evidence, violating FR-1/spec AC-1.4 and the base assumption/test-discrimination invariants; either remove the unmeasured punctuation and require a non-empty cwd, or cite live runtime evidence that each accepted shape is necessary, then extend AC-2.12's per-agent negative corpus and add mutations that restore each widening (updating every affected regex anchor).

## Should-fix
None

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v45-END
