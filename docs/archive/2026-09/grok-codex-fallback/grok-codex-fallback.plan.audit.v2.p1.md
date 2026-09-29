AUDIT-grok-codex-fallback-plan-v2-BEGIN
## Summary
The plan addresses all eleven functional requirements in the spec's form. Three verification gaps remain: the live smoke targets the installed checkout, its success check does not verify the requested file write, and W4's force-fire check has no discriminating test.

| Axis C classification | Identifiers |
|---|---|
| implemented-as-written | FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11 |
| restated | None |
| absent | None |

Evidence: 15 files opened, 10 greps run; the installed wrapper path, F0 hash, AC count, and CLI help were checked.
🌱 graft saved ~54,945 tokens (~$0.03) this turn, 1 call.

## Must-fix
- The Phase-5 live smoke invokes the bare `hmad-dispatch` command from a worktree, but PATH resolves it through `~/.claude/skills/h-mad` to the main checkout. Changing cwd does not change that resolution, so the smoke can fail on the old wrapper or validate a different wrapper from the one being shipped. Invoke the feature worktree's `h-mad/bin/hmad-dispatch` explicitly for `exec`, `progress`, and `resolved-model`, and record the resolved script path. — The base wrapper–runtime reconciliation invariant requires a live run of the new verb itself.
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › `hmad-dispatch exec grok <F0 prompt file> --cd <scratch dir> --timeout 300`
  quote: h-mad/bin/hmad-dispatch › `REAL="$BIN_DIR/../scripts/hmad-dispatch.sh"`
- The live smoke's prompt asks Grok to create `b.txt` containing `probe`, yet its pass condition checks only rc, reply, progress, and model. Read back `b.txt` from the scratch directory and require its content to match before recording a pass. — A reply saying `STATUS: DONE` is not evidence that the requested filesystem mutation occurred, violating the base mutation-verification and wrapper-round-trip invariants.
  class: measurement
  quote: docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.prompt.txt › `then create a file b.txt containing the word "probe".`
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › `Pass: rc 0, `--out` holds a line-start `STATUS: DONE`, `progress` names `grok-ndjson`, and`
- W4's force-fire check points to an AC-4.6 “omission clause,” but that AC uses a stream with two tool calls and requires the last-tool line to appear. None of the named W4 checks requires that line to be absent when the region has no `tool_call`. Add a derived no-tool EMPTY-path case with an explicit stderr absence assertion, then show the unconditional-emission mutant fails it. — The proposed force-fire cannot distinguish a correctly conditional call site from an unconditional one, breaching base connection enforcement.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.plan.md › `| W4 | `_cmd_exec` EMPTY path → grok last-tool line | AC-4.6 fails: no `2 tool calls completed` line | line emitted with no `tool_call` in region → the omission clause fails |`
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `and stderr naming `2 tool calls completed; last tool: search_replace completed`.`

## Should-fix
None

## Nit
None
AUDIT-grok-codex-fallback-plan-v2-END
