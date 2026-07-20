# Learnings — Durable Cross-Session Knowledge

Project-local kernel of gotchas, solutions, and patterns worth surviving
across sessions. Newest entries at the top. One line per entry.

Format: `- ISO-date · category · [confidence] · ` `` `tags` `` ` — pattern text`

Confidence: 0.3=tentative  0.5=moderate  0.7=strong  0.9=near-certain

Search via `grep <term> docs/learnings.md` or
`python3 ~/.claude/skills/handoff/scripts/learn.py search <term>`.
- 2026-07-21 · gotcha · [0.7] · `orca,automations,worktree,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Orca automations: valid --provider = claude|codex|gemini (NOT agent); worktree create needs --repo; --trigger and --schedule/--cron are mutually exclusive.
- 2026-07-21 · pattern · [0.9] · `orca,e2e,verify,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Stub-green + N doc-audits can't catch schema-extraction bugs; only a live-runtime e2e does. Reconcile verb output KEYS vs the real runtime, not just argv.
- 2026-07-21 · gotcha · [0.7] · `orca,automations,worktree,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Orca automations are agent-driven: valid --provider is claude|codex|gemini (NOT agent); worktree create requires --repo/targeting; --trigger and --schedule/--cron are mutually exclusive.
- 2026-07-21 · pattern · [0.9] · `orca,e2e,verify,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Stub-tested-green + N doc-audits cannot catch schema-extraction bugs; only a live-runtime e2e does. Reconcile verb output-KEYS against the real runtime, not just the input argv.
- 2026-07-20 · solution · [0.7] · `orca,orchestration,handoff:2026-07-20-orca-adaptation-tiers` — Tier-2 orchestration worker can't read coordinator handle from its own shell env — task-create injects it into the task spec (prepended [H-MAD] line) and enforces the pin
- 2026-07-20 · gotcha · [0.7] · `zsh,shell,handoff:2026-07-20-orca-adaptation-tiers` — zsh no-wordsplit: 'env $PINS bash' passes one arg — use prefix-assignment 'VAR=v bash'. Shell exports don't persist across Bash tool calls; inline pins each call
- 2026-07-20 · gotcha · [0.7] · `hmad-dispatch,cmux,handoff:2026-07-20-orca-adaptation-tiers` — hmad-dispatch alive string-matches surface in cmux tree -> false positives; panes may not be at default surface:5/:2 (was Codex=4 agy=5). Pin HMAD_CMUX_*_SURFACE + read pane to confirm REPL
- 2026-07-20 · gotcha · [0.7] · `orca,hmad-dispatch,handoff:2026-07-20-orca-adaptation-tiers` — Reconcile Orca CLI usage vs 'orca agent-context --json' at build time — original hmad-dispatch guessed syntax, shipped broken wait (real: --for tui-idle --timeout-ms) + tail-piped read (real: --limit)

- 2026-07-20 · gotcha · [0.7] · `orca,hmad-dispatch,handoff:2026-07-20-orca-adaptation-tiers` — orca terminal list --json nests terminals under .result.terminals[].handle (no .id/.command) — guessed .[]|select(.id) never matches live Orca; identity = handle pin not command-match
