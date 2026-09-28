# grok `--output-format streaming-json` probe — 2026-09-28

Probe run in session 8a0b0625 to answer open question 3 of `docs/01-plan/features/grok-codex-fallback-brainstorm.md`. Raw artifacts sit beside this file: `stream-json.2026-09-28.ndjson` (110 lines, 83,256 B) and `stream-json.2026-09-28.prompt.txt`.

## Command

```bash
env -u CLAUDE_CODE_SESSION_ID -u CLAUDE_CODE_SESSION_ATTENDED -u CLAUDE_EFFORT -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
  HPW_AGENT_BACKEND=claude hmad-dispatch run --timeout 400 -- \
  grok --cwd <ws> --always-approve --prompt-file <prompt> --output-format streaming-json > stream.ndjson
```

The prompt asked grok to read `a.txt`, write `b.txt`, and end with `STATUS: DONE`.

## Results

- **rc=0.** `b.txt` was written with the content `probe`, and nothing went to stderr.
- Model `grok-4.7-build`, grok 1.0.41: `stopReason=end_turn`, `num_turns=3`, `total_cost_usd=0.0393`.

Every line is a flat JSON object. Its `type` is one of the following (count in this run):

| type | n | shape |
|---|---|---|
| `thought` | 70 | `{"data": "<delta>"}`, a reasoning delta |
| `text` | 21 | `{"data": "<delta>"}`, an assistant text delta |
| `available_commands` | 9 | `tools[]`, `commands[]` |
| `tool_call` | 2 | `toolCallId`, `toolName`, `title`, `kind`, `status:"pending"`, `rawInput` |
| `tool_call_update` | 4 | `toolCallId`, `status` (`null`, then `"completed"`), `rawOutput`, `locations` |
| `usage` | 3 | per-turn `usage{input_tokens, output_tokens, reasoning_tokens, …}` |
| `end` | 1 | `stopReason`, `sessionId`, `num_turns`, `total_cost_usd`, `modelUsage{<model-id>: …}`, `usage` |

## Findings that bind the design

1. **Concatenating the text deltas loses turn boundaries.** Joining every `text.data` gives `I'll read \`a.txt\`, then create \`b.txt\` with the word "probe".STATUS: DONE`. Here `STATUS:` is **not at line start**, so `h_mad_extract_verdict.py` (the key must start the line) would return no verdict. ~~The final message has to be the text deltas after the last `tool_call`/`tool_call_update`/`usage` event.~~ **Corrected by spec-author (2026-09-28): that rule is wrong.** A trailing `usage` event and the `end` event come after the last `text` delta (event order `…text,available_commands,usage,end`), so the rule yields an empty message. The correct rule treats `tool_call`, `tool_call_update`, `usage` and `end` as boundaries that close a text segment. The final message is the last non-empty segment, which on this fixture is `STATUS: DONE`.
2. **Tool-call evidence** can be counted as a `tool_call_update` with `status == "completed"`, keyed by `toolCallId`. This is the analogue of agy's `DONE`. A failed status value was not observed. Capture one before writing a failure branch; do not guess its spelling.
3. **The model id is available** at `end.modelUsage` (its keys), which gives `resolved-model` a grok branch backed by evidence.
4. **A completion signal exists:** a single `end` event with `stopReason`. A stream without `end` is a truncated run.
5. `--sandbox <PROFILE>` lists no possible values in `--help`. `--permission-mode` takes `default, acceptEdits, auto, dontAsk, bypassPermissions, plan`. The trial used `--always-approve`, and no sandbox profile was probed.
6. A stray `graft/` directory appeared in the workspace. The cause is unverified: it may be a graft hook inherited through the environment, not grok itself. Before trusting tree-delta reporting for grok, re-check it with a clean environment.
