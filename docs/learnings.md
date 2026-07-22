# Learnings — Durable Cross-Session Knowledge

Project-local kernel of gotchas, solutions, and patterns worth surviving
across sessions. Newest entries at the top. One line per entry.

Format: `- ISO-date · category · [confidence] · ` `` `tags` `` ` — pattern text`

Confidence: 0.3=tentative  0.5=moderate  0.7=strong  0.9=near-certain

Search via `grep <term> docs/learnings.md` or
`python3 ~/.claude/skills/handoff/scripts/learn.py search <term>`.
- 2026-07-22 · solution · [0.7] · `orca,h-mad,report-file,handoff:2026-07-22-orca-skills-hardening` — Orca agent verdicts: report-file transport (agent writes <path>+<path>.done; coordinator report-waits) beats TUI scrape — kills the indent/bullet/idle/sentinel fragility; gate reads the clean file
- 2026-07-22 · gotcha · [0.7] · `review,tdd,handoff:2026-07-22-orca-skills-hardening` — Separate review lane is load-bearing: 4 Claude-subagent reviews each caught 1 real bug green tests missed (stub-envelope regression, gate-wait fail-open, find_latest prefix false-match)
- 2026-07-22 · pattern · [0.7] · `orca,handoff,worktree,handoff:2026-07-22-orca-skills-hardening` — Handoff/learnings under Orca multi-worktree: anchor to canonical main worktree via git-common-dir (not show-toplevel); disambiguate by branch with __ separator so feat can't match feat-ab
- 2026-07-22 · gotcha · [0.9] · `h-mad,gap-analysis,verification,handoff:2026-07-22-h-mad-fourteen-issues-shipped` — Checking code against spec alone cannot separate 'code diverged from design' from 'design diverged from spec' — a deliberate narrowing reads as a defect. Classify before recommending a fix.
- 2026-07-22 · pattern · [0.7] · `h-mad,state,schema,handoff:2026-07-22-h-mad-fourteen-issues-shipped` — Validate-before-write at the seam beats documenting a rule: h-mad state drifted to 38 shapes over 53 keys because nothing sat between an invented key and the file, not because the rule was unclear.
- 2026-07-22 · gotcha · [0.7] · `zsh,git,shell,handoff:2026-07-22-h-mad-fourteen-issues-shipped` — zsh executes backticks and glob-fails on # inside git -m messages, producing a silent no-op that looks like success. Use -F <file>; note git merge -F - does not read stdin though git commit does.
- 2026-07-22 · solution · [0.7] · `git,heuristics,handoff:2026-07-22-h-mad-fourteen-issues-shipped` — Counting a feature's commits: rev-list --count <branch> gives whole history; merge-base..<branch> gives 0 once merged. Only --grep for commits naming the feature survives a merge.
- 2026-07-22 · gotcha · [0.9] · `h-mad,testing,verification,handoff:2026-07-22-h-mad-fourteen-issues-shipped` — A green test suite can certify a 0% spec match rate — tests encode the design, and the design can silently diverge from the spec. Test-passing and requirement-satisfying are independent axes.
- 2026-07-22 · gotcha · [0.9] · `h-mad,dispatch,silent-failure,handoff:2026-07-22-h-mad-fourteen-issues-shipped` — Halt conditions phrased as halt-on-bad-value fail open: 'halt on VERDICT: DRIFT' means a scrape with no verdict greps clean, so agent silence reads as approval. Extraction must fail closed.
- 2026-07-21 · gotcha · [0.7] · `orca,automations,worktree,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Orca automations: valid --provider = claude|codex|gemini (NOT agent); worktree create needs --repo; --trigger and --schedule/--cron are mutually exclusive.
- 2026-07-21 · pattern · [0.9] · `orca,e2e,verify,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Stub-green + N doc-audits can't catch schema-extraction bugs; only a live-runtime e2e does. Reconcile verb output KEYS vs the real runtime, not just argv.
- 2026-07-21 · gotcha · [0.7] · `orca,automations,worktree,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Orca automations are agent-driven: valid --provider is claude|codex|gemini (NOT agent); worktree create requires --repo/targeting; --trigger and --schedule/--cron are mutually exclusive.
- 2026-07-21 · pattern · [0.9] · `orca,e2e,verify,handoff:2026-07-21-orca-arc-complete-hemasuite-wiring` — Stub-tested-green + N doc-audits cannot catch schema-extraction bugs; only a live-runtime e2e does. Reconcile verb output-KEYS against the real runtime, not just the input argv.
- 2026-07-20 · solution · [0.7] · `orca,orchestration,handoff:2026-07-20-orca-adaptation-tiers` — Tier-2 orchestration worker can't read coordinator handle from its own shell env — task-create injects it into the task spec (prepended [H-MAD] line) and enforces the pin
- 2026-07-20 · gotcha · [0.7] · `zsh,shell,handoff:2026-07-20-orca-adaptation-tiers` — zsh no-wordsplit: 'env $PINS bash' passes one arg — use prefix-assignment 'VAR=v bash'. Shell exports don't persist across Bash tool calls; inline pins each call
- 2026-07-20 · gotcha · [0.7] · `hmad-dispatch,cmux,handoff:2026-07-20-orca-adaptation-tiers` — hmad-dispatch alive string-matches surface in cmux tree -> false positives; panes may not be at default surface:5/:2 (was Codex=4 agy=5). Pin HMAD_CMUX_*_SURFACE + read pane to confirm REPL
- 2026-07-20 · gotcha · [0.7] · `orca,hmad-dispatch,handoff:2026-07-20-orca-adaptation-tiers` — Reconcile Orca CLI usage vs 'orca agent-context --json' at build time — original hmad-dispatch guessed syntax, shipped broken wait (real: --for tui-idle --timeout-ms) + tail-piped read (real: --limit)

- 2026-07-20 · gotcha · [0.7] · `orca,hmad-dispatch,handoff:2026-07-20-orca-adaptation-tiers` — orca terminal list --json nests terminals under .result.terminals[].handle (no .id/.command) — guessed .[]|select(.id) never matches live Orca; identity = handle pin not command-match
