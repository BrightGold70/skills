## Summary
The task graph, 40-node 28/12 RED split, 30-mutation inventory, and paired-design citation reconcile. One load-bearing safety premise is falsified by the actual regexes, while two smaller documentation claims should be corrected before dispatch.

## Must-fix
- The plan/design/spec call `_agent_pv_re` “hardened against prose” and use that premise to treat a unique retained-tail match as safe, but the actual patterns match ordinary prose verbatim: `Release notes for OpenAI Codex are available`, `I am comparing model: gpt-5.6-terra with ours`, `The Antigravity CLI documentation changed`, and `Compare Gemini 3.1 Pro with Claude` all matched in direct controlled probes. Because `$scoped` includes generic shell panes and tail text is explicitly historical, a sole shell that printed documentation or release notes can therefore be resolved as an agent; the suite's only prose negative covers a weaker bare-model sentence and AC-3.2 covers only launch commands. This contradicts FR-2/“Never resolve to the wrong pane” and violates the base Assumption-verification rule: add a measured negative corpus and a discriminating wrong-pane test, then either strengthen the evidence rule so those cases decline or explicitly revise the safety contract and risk analysis to acknowledge this new false-resolution class.

## Should-fix
- The T2 code comment and paired design say the shown full filter makes `jq -r` print literal `null` for a missing tail, while the mutation mechanism later states the actual result. With `(.result.terminal.tail? // empty)` and the final `else empty`, a controlled run produced zero bytes at rc 0 with `jq -r` and zero bytes at rc 4 with `jq -re`; `-e` is still load-bearing, but the literal-`null` explanation applies only to the simpler measurement filter and should be corrected on both surfaces.
- Task 6 says every new guard receives a mutation, but the listed spec does not mutate several independently asserted command/stub controls, such as the missing per-handle file's final `exit 1` and retention of `--limit 4000`/`--json`. These nodes are RED-failing and therefore still satisfy the base discrimination requirement, so narrow the “every guard” claim to the enumerated mutated controls or add the missing mutants rather than leaving the deliverable stronger than its inventory.

## Nit
None
