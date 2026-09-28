# Design: grok-codex-fallback

## Executive Summary

Grok becomes a third, explicitly armed agent in `hmad-dispatch exec`, with a jq segmenter over
its own `--log` region, a typed and fail-closed `fallback_agent` read in the TDD gate, a
`scan_grok` evidence reader shared by the evidence CLI and the audit-cycle combiner, a closed-world
shape router in `combine()`, a presence-judged `--timeout` sentinel in the assembler, and a
last-`end` model reader. Every non-grok path keeps its bytes.

## Overview

The design implements spec v1.2 (11 FRs, 55 ACs) under plan v1.3. It keeps the plan's wiring
table W1–W11, its premises P1–P13, its live smoke and its risks. Three decisions carry most of the
design:

1. **No binary agent test may route grok into another agent's arm.** Every multi-arm branch on
   the agent names each agent it serves. The two existing `else` arms that mean "not codex, so
   agy" and "not agy, so codex" become explicit `elif`s. The same class exists in
   `h_mad_resolved_model.main()`, where the agy path is an implicit fall-through, and in
   `_render_progress`, which falls through to the codex lens.
2. **Every "cannot judge" gets its own spelling.** A truncated grok stream never produces a
   count. A `fallback_agent` value the hook cannot read blocks. A shape `combine()` does not
   route gets its own `UNVERIFIED` reason, never the delivery floor.
3. **Each force-fire mutation is expressible as one harness find/replace.** The harness takes one
   `find`/`replace` per row (`h_mad_mutation_harness.py`, the "Spec format" block of its module
   docstring). That fixes the order of arms: the grok arm comes first in `_cmd_exec`'s transport
   chain, and grok is the first branch in `resolved_model.main()`. It also factors grok detection
   into one helper, so a precedence mutation is a single inserted line.

The tree premises were read at `50560eb` (HEAD at authoring). `git diff --name-only 1680271
50560eb -- h-mad handoff | wc -l` → 0 files, so plan v1.3's tree premises (read at `1680271`) and
this design's readings describe the same `h-mad/` tree.

## Architecture Overview

```
 state (.bkit-memory.json)                          operator / orchestrator
   fallback_agent ──read (typed)──► h-mad-tdd-gate.sh        │
                                    BLOCK-CODEX (unchanged)   │ h_mad_assemble_tdd.py --agent grok
                                    BLOCK-GROK / BLOCK-INVALID│   └─► "hmad-dispatch exec grok … --timeout 1500"
                                    FALL-THROUGH              ▼
                                                  hmad-dispatch.sh _cmd_exec grok
                                                    ├─ grok arm: env -u CLAUDE* … grok --prompt-file
                                                    │     >> --log (region = lines after pre_lines)
                                                    ├─ _grok_region_state / _grok_final_message
                                                    │  _grok_stop_reason / _grok_last_tool   (jq)
                                                    └─ EMPTY path: TRUNCATED, last tool, structured recovery
   --log ──► hmad-dispatch progress ── _exec_log_format: agy → _grok_log_has_events → codex-text
         ──► h_mad_review_evidence.py main: scan() agy → scan_grok() → codex-text
         ──► h_mad_audit_cycle.measure_effort: parsed → grok | grok-truncated → codex-text → unparseable
                   └─► combine(): closed-world route per shape
         ──► h_mad_resolved_model.py grok --log: last end.modelUsage
 audit-cycle --surfaces agy,grok ──► _cmd_exec grok (per-pass --log) ──► measure_effort / combine
```

Two instruments classify a grok log. `_exec_log_format` is a shell grep that picks a render lens.
`measure_effort()` is Python and picks a verdict route. They share one type vocabulary, and a test
pins that the two type sets are equal (see Test Plan, "two-instrument agreement").

## Detailed Design

### D1 — `fallback_agent` schema property (FR-1)

Add `fallback_agent` to `properties` of `h-mad/scripts/h_mad_state_schema.json`, placed directly
after `codex_status`. It is not added to `required`.

```json
"fallback_agent": {
  "description": "<see below>",
  "enum": ["grok", "claude", null]
}
```

The `description` states the four facts AC-1.4 requires, in this order:

- The field is read only when codex is out, meaning `HMAD_CODEX_UNAVAILABLE` is non-empty,
  `codex_status` is `unavailable|exhausted`, or `codex` is not on PATH.
- Absent, `null` and `"claude"` are equivalent: Claude covers, test-first, as before.
- `HMAD_CODEX_UNAVAILABLE` does not override `"grok"`. A one-off Claude escape needs
  `--set fallback_agent=claude`.
- Audit-leg routing to grok (`audit-cycle --surfaces agy,grok`) is prose-enforced by `SKILL.md`,
  and no script reads this field for it.

The historical tier is untouched. `h_mad_state_schema_historical.json` has
`additionalProperties: true`, so AC-1.3's tier-preservation claim rests only on the strict schema
gaining an optional key.

### D2 — TDD gate: typed, fail-closed `fallback_agent` read (FR-2)

**Placement.** The new code goes between the closing `fi` of the existing BLOCK-CODEX `if` and the
comment `# Codex unavailable / declared exhausted → fall through`. It is inside the block headed
`# --- Codex-authorship enforcement`. The BLOCK-CODEX `if` exits 1 whenever codex_out is false.
Anything placed after its `fi` therefore runs **only when codex_out is true**, and the placement
realises the table's first row by construction:

- BLOCK-CODEX's condition, stderr and exit are unchanged, byte for byte (AC-2.2).
- The 8 BLOCK-CODEX cells of AC-2.1b hold, because the new read is never reached when codex_out
  is false.
- The exemption `case` blocks and the `.py` filter sit above, so AC-2.6 holds by construction
  (plan P3).

**The read.** `jq -r '.f // "claude"'` is wrong on two counts, measured in plan §"The gate reads
`fallback_agent` type-preservingly": `//` maps `false` to the default, and `-r` prints JSON `null`
and the string `"null"` identically. The design reads the value's **JSON type inside jq** and
emits a tag that is always a plain word, followed by the value's `tojson` only on the invalid
branch:

```bash
FALLBACK_TAG=$(jq -r --arg k "$ACTIVE" '
  (.orchestrator_state[$k] // {}) as $r
  | if ($r | type) != "object" or ($r | has("fallback_agent") | not) then "absent"
    else $r.fallback_agent as $v
    | if   $v == null     then "null"
      elif $v == "grok"   then "grok"
      elif $v == "claude" then "claude"
      else "invalid " + ($v | tojson) end
    end' "$STATE_FILE" 2>/dev/null) || FALLBACK_TAG=""
case "$FALLBACK_TAG" in
  absent|null|claude) ;;                                 # FALL-THROUGH, exactly as today
  grok)       <BLOCK-GROK stderr>;    exit 1 ;;
  "invalid "*) <BLOCK-INVALID stderr, value = ${FALLBACK_TAG#invalid }>; exit 1 ;;
  *)          <BLOCK-INVALID stderr, value = <unreadable>>; exit 1 ;;   # read error: fail closed
esac
```

- **Why the tag is total.** jq compares `$v == "grok"` by type and value, so `false`, `0`, `{}`,
  `[]`, `""`, `"Grok"`, `"null"` and `"codex"` all reach the `invalid` branch. `tojson` renders a
  value on one line, so a multi-line or quoted value cannot forge a tag. The `case` default arm
  catches two things: the empty string a failed `jq` leaves under the `|| FALLBACK_TAG=""`
  assignment, and any output not in the closed set. **That default is the fail-closed
  requirement.**
- **Executed, not reasoned** (scratch state file, then deleted), on `jq` from PATH at `50560eb`,
  running the filter above:

  ```
  ABSENT   -> [absent]          null     -> [null]          "claude" -> [claude]
  "grok"   -> [grok]            "codex"  -> [invalid "codex"]
  false    -> [invalid false]   true     -> [invalid true]  0        -> [invalid 0]
  "null"   -> [invalid "null"]  ""       -> [invalid ""]    "Grok"   -> [invalid "Grok"]
  {}       -> [invalid {}]      []       -> [invalid []]
  corrupt state file -> [] rc=5       (→ the `*)` arm, BLOCK-INVALID <unreadable>)
  ```

  JSON `null` and the string `"null"` diverge (`null` vs `invalid "null"`), and `false` is no
  longer absent. Those are the two collapses plan v1.3 measured on the `//`/`-r` idiom.
- **Scope of "read error".** `ACTIVE` was already derived from the same file by an earlier `jq`
  that must succeed for the hook to reach this block. The `*)` arm is therefore reached by a jq
  failure on the second read, meaning the file changed between reads or jq crashed. It is also
  reached by a future edit to the filter that emits an unforeseen token. Both fail closed.
- **`ACTIVE` scoping (AC-2.5, W9).** The filter indexes `.orchestrator_state[$k]` with the same
  `$ACTIVE` the `codex_status` read uses. No other feature's record is consulted.

**Stderr.** Each new block's first stderr line carries the `[H-MAD-TDD-GATE] BLOCK:` prefix, as
the existing BLOCK-CODEX block's first line does.

- BLOCK-GROK names the four things AC-2.3 lists:
  - `hmad-dispatch exec grok <promptfile>`;
  - `h_mad_assemble_tdd.py … --agent grok`;
  - the escape `h_mad_state_write.py --feature $ACTIVE --set fallback_agent=claude "$STATE_FILE"`;
  - the sentence `HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok`.
- BLOCK-INVALID names the value (`tojson` form, or `<unreadable>`) and the valid set `grok|claude`
  (AC-2.4). It also names the remedy `--set fallback_agent=grok|claude|null`.

**Inherited fail-open (unchanged, stated).** With no `jq` on PATH, the hook exits 0 before this
block, which is plan Risks "No `jq` on PATH". Under `fallback_agent=grok`, Claude can therefore
write when `jq` is absent. This design does not change that. Changing it would alter FR-11's
absent-field regression (AC-2.2).

### D3 — `_cmd_exec`: the agent-arm rule and the grok arm (FR-3, FR-4)

**Census of agent-conditional sites, re-derived at `50560eb`** (grammar from plan v1.3; unit:
matching lines per enclosing function):

```bash
awk '/^_[a-z_]+\(\) *\{/{fn=$1} /"\$agent" (=|!=) |case "\$agent" in/{print fn}' \
  h-mad/scripts/hmad-dispatch.sh | sort | uniq -c
# reading at 50560eb: 8 _cmd_exec()  2 _cmd_launch()  1 _cmd_exec_pane()  1 _cmd_resolve()  1 _cmd_verify()
```

The 8 `_cmd_exec` sites are listed below by content, in file order. Each is located by the quoted
text, never by line. The table gives the treatment for each.

| # | Site (quoted content) | Kind | Treatment |
|---|---|---|---|
| S1 | `case "$agent" in codex\|agy) ;;` and its message `(expected codex\|agy)` | valid set | becomes `codex\|agy\|grok`; the message names `codex\|agy\|grok` (AC-3.6) |
| S2 | `[ "$agent" = codex ] && sandbox="workspace-write"` | one-armed, codex-positive | unchanged. Grok takes "no default", which is FR-3's rule. There is no other agent's arm to fall into |
| S3 | `case "$agent" in` → `codex) : "${HPW_AGENT_BACKEND:=codex}"` / `agy) : "${HPW_AGENT_BACKEND:=gemini}"` | multi-arm | gains an explicit `grok) ;;` arm whose comment says the grok default is applied in the child's environment only (D3.3). The wrapper shell is not assigned (FR-3, OQ2) |
| S4 | `if [ "$agent" = codex ]; then` … `else` (the agy arm) | multi-arm with `else` = agy | the chain becomes `if [ "$agent" = grok ]; then <grok arm>` / `elif [ "$agent" = codex ]; then <codex arm, body unchanged>` / `elif [ "$agent" = agy ]; then <agy arm, body unchanged>` / `fi`. Grok comes first so W1's force-fire is one replace (§"Mutation rows and wire force-fires") |
| S5 | `[ "$agent" = codex ] && [ "$final_empty" -eq 1 ] && refused=…_codex_input_too_large…` | one-armed, codex-positive | unchanged. There is no grok refusal detector (spec Out-of-Scope) |
| S6 | `if [ "$agent" = agy ] && [ -s "$log" ]; then` (the #77b last-step line) | one-armed, agy-positive | unchanged. A sibling `if [ "$agent" = grok ]` block is added after it for the grok last-tool line (D3.5) |
| S7 | `[ "$agent" = codex ] && echo_expected=1` | one-armed, codex-positive | unchanged. `echo_expected` is read only by the codex recovery arm (S8) |
| S8 | `if [ "$agent" = agy ]; then` … `else recovered="$(_verdict_after_boundary …)"` | multi-arm with `else` = codex | the `else` becomes `elif [ "$agent" = grok ]; then <structured recovery>` / `elif [ "$agent" = codex ]; then <the existing line-oriented call, unchanged>`. Also, `local recovered` becomes `local recovered=""` (below) |

**The rule over the axis.** After the change, no `else` or `*)` arm of an agent-conditional in
`_cmd_exec` stands for a named agent. Today two do:

- S4's `else` means agy;
- S8's `else` means codex.

Both become explicit `elif`s. One-armed guards (S2, S5, S6, S7) name the one agent they serve and
have no other arm, so there is nothing for grok to fall into. Each is listed above with the reason
grok's non-match is correct.

**Residual:** a site that branches on the agent through a variable other than `$agent`, or inside
a helper `_cmd_exec` calls, is outside the grammar. That includes `_exec_stamp`, `_exec_run` and
`_cmd_notify`. It was measured at `50560eb`:

```bash
for fn in _exec_stamp _exec_run _exec_completed _cmd_notify; do
  sed -n "/^$fn() *{/,/^}/p" h-mad/scripts/hmad-dispatch.sh | grep -v '^ *#' \
    | grep -cE '(if|case|\[) .*(agent|agy|codex)'; done
# reading: 0 0 0 0 (unit: non-comment matching lines per helper)
```

The zero holds because these helpers take the agent only as a label for stamps, beats and
notifications. It is load-bearing: a later agent branch inside any of them is outside the census
grammar and would need its own grok arm. `_render_progress` branches on the **format** token and is treated in D5. **This census
moves by construction** once S4 and S8 gain `elif`s. Re-measure it at 5g, and never carry this
reading forward.

**Why `local recovered=""` is load-bearing.** The wrapper runs `set -euo pipefail`
(`grep -n '^set -' h-mad/scripts/hmad-dispatch.sh` → `set -euo pipefail`). Under `set -u`, a
`local` that no arm assigns is unbound on read:
`bash -c 'set -u; f(){ local r; echo "[${r}]"; }; f'` → `bash: line 1: r: unbound variable`
(run at `50560eb`). Today every path through S8 assigns `recovered`. With explicit arms, the
initialiser keeps an unmatched agent from turning the recovery block into a crash.

#### D3.1 Valid set, header, option comments

- The header comment of `_cmd_exec` becomes `<codex|agy|grok> …`, with `[grok: --sandbox
  <profile>]` added beside the codex and agy notes.
- The `--sandbox` and `--effort` option comments add grok's translation.
- `command -v "$agent"` already yields `exec requires the grok CLI on PATH` for a missing `grok`
  (AC-3.6).
- `wait_secs="${timeout:-3600}"` is shared unchanged (FR-3).

#### D3.2 Grok argv

Built inline in the grok arm, in this order:

```bash
local gargs=(--cwd "$cd_dir" --always-approve --output-format streaming-json
             --prompt-file "$bounded_prompt")
[ -n "$model" ]   && gargs+=(--model "$model")
[ -n "$effort" ]  && gargs+=(--reasoning-effort "$effort")
[ -n "$sandbox" ] && gargs+=(--sandbox "$sandbox")
```

- `$bounded_prompt` is the same file codex receives on stdin and agy receives as `--print`:
  caller prompt, then coordinator line, then boundary. It is deleted by the existing
  `rm -f "$bounded_prompt"` after the arm. The stub therefore **copies** its contents at
  invocation (plan §"The `grok` stub").
- `-p` and `--single` are never emitted. P11 shows grok 1.0.41 refuses them with `--prompt-file`
  (rc 2).
- There is no OVERSIZE check in the grok arm. The ARG_MAX refusal lives inside the agy arm's body,
  which grok never enters. That is S4's explicit arm doing its job (AC-3.5).
- `$timeout` is not forwarded. Grok has no print-timeout flag, and `$timeout` bounds only
  `wait_secs`.

#### D3.3 Child-only environment

The scrub is an `env` prefix on the child's argv, so it exists only in the grok process image:

```bash
local child_env=() _v
for _v in $(compgen -e); do case "$_v" in CLAUDE*) child_env+=(-u "$_v") ;; esac; done
child_env+=("HPW_AGENT_BACKEND=${HPW_AGENT_BACKEND:-claude}")
```

- **`:-`, not `:=`.** It yields the same child value as spec FR-3's `:=`: a non-empty operator
  value wins, and unset or empty becomes `claude`. It does not assign in the wrapper shell, which
  is what "the wrapper's own environment … untouched" requires.
- **`compgen -e` + `case`, not `env | grep`.** It needs no pipeline that can exit 1 on "no match"
  under `pipefail`. It also sees only exported names, which are exactly what the child inherits.
- **Where `child_env` is built.** It is built **before** the S4 chain and used only in the grok
  arm, so W2's force-fire is one replace that adds `env "${child_env[@]}"` to the codex child
  (§"Mutation rows and wire force-fires").
- **Executed at `50560eb`** under `/bin/bash` 3.2.57, the shim's interpreter
  (`h-mad/bin/hmad-dispatch` begins `#!/bin/bash`), with `CLAUDE_X` and `CLAUDECODE` exported:
  `env "${a[@]}" HPW_AGENT_BACKEND=… /usr/bin/env | grep -c '^CLAUDE'` → 0 lines;
  `HPW_AGENT_BACKEND=claude` in the child; the parent still printed `CLAUDE_X=1`.
- **`env` availability.** `/usr/bin/env` is on the tests' isolated PATH, whose shape is
  `f"{bindir}:/usr/bin:/bin"` in `test_hmad_dispatch.py`. It is a POSIX base utility the scripts
  already invoke through their `#!/usr/bin/env bash` shebangs, so it is not a new dependency.

#### D3.4 Launch and region

```bash
if [ -f "$log" ]; then pre_lines="$(wc -l < "$log" 2>/dev/null | tr -d " ")"; fi
[ -n "$pre_lines" ] || pre_lines=0
_HMAD_EXEC_BEAT_LOG="$log"
( cd "$cd_dir" && _exec_run --heartbeat "$agent" "$label" "$cd_dir" "$heartbeat_sec" \
    "$wait_secs" env "${child_env[@]}" grok "${gargs[@]}" ) < /dev/null >> "$log" 2>&1 || rc=$?
_HMAD_EXEC_BEAT_LOG=""
```

- **`pre_lines`** is captured exactly as the codex and agy arms capture it. Every grok reader
  below takes it and reads `tail -n "+$((pre_lines + 1))"`.
- **`2>&1` into the log**, not `2>/dev/null` as agy uses. That is spec FR-3: grok's diagnostics
  stay in the log, and the readers skip non-JSON lines.
- **`< /dev/null`** is added because grok takes its prompt from `--prompt-file`. `_exec_run`
  otherwise hands the child the caller's stdin (`"$@" <&0 &`), and a grok build that reads a
  non-tty stdin would block on an orchestrator's open pipe.
  **Residual:** whether grok 1.0.41 reads stdin under `--prompt-file` was not probed. The redirect
  is harmless either way, and the Phase-5 live smoke exercises it.
- **No `--complete-log`.** There is no completion-event reaping for grok (spec Out-of-Scope). A
  lingering grok is bounded by `wait_secs`.

#### D3.5 Grok stream readers (new helpers, beside `_agy_ndjson_response` / `_agy_last_step`)

All four read only the region. Each follows `_agy_last_step`'s hardening:

- `case "$pre" in ''|*[!0-9]*) pre=0 ;; esac`;
- `select(type == "object")` after `fromjson? // empty`, so a stray scalar line cannot abort jq
  with "Cannot index";
- `2>/dev/null || true`, so a jq failure under `set -e` degrades rather than abandoning
  `_cmd_exec` before recovery.

Each returns empty (or `unknown`) when `jq` is absent.

**`_grok_final_message <log> <pre_lines>`** is the FR-4 segmenter. It prints the last non-empty
segment and nothing else:

```jq
split("\n") | map(fromjson? // empty | select(type == "object"))
| reduce .[] as $e ({segs: [], cur: ""};
    if $e.type == "text" then .cur += (if ($e.data | type) == "string" then $e.data else "" end)
    elif ($e.type == "tool_call" or $e.type == "tool_call_update"
          or $e.type == "usage" or $e.type == "end")
      then .segs += [.cur] | .cur = ""
    else . end)
| (.segs + [.cur]) | map(select(length > 0)) | last // empty
```

- It is run as `jq -Rs -r`, slurped raw, so a multi-line segment stays one value. That is the
  `_agy_ndjson_response` lesson about `tail -1` truncating a multi-line verdict.
- Every other `type`, including `thought`, `available_commands`, unobserved types and a missing
  `type`, is neither appended nor a closer.
- Only `text` data is ever appended. `thought` data, `rawInput`/`rawOutput` and non-JSON lines
  never are (AC-4.3).
- **Executed on F0 at `50560eb`:** the segments were ``["I'll read `a.txt`, then create `b.txt`
  with the word \"probe\".","STATUS: DONE"]`` and the final message was `STATUS: DONE` (spec A1).
- The caller's `$(…)` strips trailing newlines, and the success path re-adds exactly one with
  `printf '%s\n'` (AC-4.1).

**`_grok_region_state <log> <pre_lines>`** prints `complete` when the region holds at least one
`end` event and `truncated` when it holds none. An empty or missing region counts as `truncated`.
It prints `unknown` when `jq` is absent or fails.

**`_grok_stop_reason <log> <pre_lines>`** prints the last `end` event's
`(.stopReason // "-") | tostring`.

**`_grok_last_tool <log> <pre_lines>`** prints `N tool calls completed; last tool: <toolName>
<status>`, or nothing when the region holds no `tool_call` event (the AC-4.9 omission clause).

- `N` is the number of distinct `toolCallId`s with a `tool_call_update` whose `status ==
  "completed"`. The spec says "N counts distinct `toolCallId`s". The design reads that as
  completed ids, because the line says "completed". On F0 and every spec fixture, all-ids and
  completed-ids agree: both are 2. See the report's owed list.
- The **last tool** is the last `tool_call`/`tool_call_update` event with a non-null `status`.
  Its name is joined from the `tool_call` carrying the same `toolCallId`, and is `?` when the join
  fails. Per P2, `toolName` appears only on `tool_call`.
- Tail-bounded to the region's last 2000 lines, as `_agy_last_step` is.
  **Residual:** a region longer than 2000 lines counts `N` within that window only.

#### D3.6 Grok arm outcome (the FR-4 table)

After the child exits:

```bash
grok_state="$(_grok_region_state "$log" "$pre_lines")"
grok_final="$(_grok_final_message "$log" "$pre_lines")"
if [ "$grok_state" = complete ] && [ -n "$grok_final" ]; then
  verdict="$grok_final"
  [ -n "$out" ] && _out_clobber_ok "$out" "$out_fp" && printf '%s\n' "$grok_final" | _write_out_atomic "$out"
  printf '%s\n' "$grok_final"
  echo "hmad-dispatch: exec: grok stopReason=$(_grok_stop_reason "$log" "$pre_lines")" >&2
  [ -n "$auto_log" ] && _render_progress "$log" 40 >&2 || true
  [ -n "$auto_log" ] && rm -f "$log"
else
  final_empty=1
fi
```

This is the table's first row: complete with a non-empty message. The stopReason line is reported
and never gated. The auto-log digest is the FR-5 renderer, never the raw log, as on the agy path.
Every other row takes `final_empty=1` into the existing EMPTY block, where grok adds the
following, in order after the unchanged `EMPTY final message — …` line:

1. When `grok_state` is `truncated`:
   `hmad-dispatch: exec: TRUNCATED — no end event in this dispatch's grok stream`.
   When it is `unknown`: `hmad-dispatch: exec: grok stream not parsed — jq not on PATH`. Neither
   is claimed as a truncation, because nothing was judged.
2. The S6 sibling block. When `_grok_last_tool` is non-empty, it prints
   `hmad-dispatch: exec: last step reached — <that line>`, which is agy's #77b wording.
3. The S8 grok arm sets `recovered="$grok_final"`, then blanks it unless
   `_recovered_has_verdict "$recovered"`. That is **structured only**: there is no
   `_verdict_after_boundary` fallback on a grok log (FR-4). A complete region that reaches this
   block has no non-empty segment, so recovery is non-empty only on a truncated region. That
   matches rows 3 and 4 of the table.
4. The existing `verdict recovered from log`, `--out` write and tree-delta lines, unchanged.

**rc.** The existing EMPTY-block rule gives the table's rc column with no grok-specific code:
rc 0 becomes 3, any other rc is kept, and a watchdog kill is already 124. AC-4.8's
`a verdict WAS recovered` follows from `verdict="$recovered"` on the recovered path.

### D4 — `_exec_log_format` learns `grok-ndjson` (FR-5)

A new helper, `_grok_log_has_events <logfile>`, returns 0 iff any line matches:

```bash
grep -aqE '^[[:space:]]*\{[[:space:]]*"type"[[:space:]]*:[[:space:]]*"(thought|text|available_commands|tool_call|tool_call_update|usage|end)"' "$log"
```

`_exec_log_format` then decides in this order:

1. `missing`;
2. `empty`;
3. the existing agy grep, which prints `agy-ndjson`;
4. `elif _grok_log_has_events "$log"`, which prints `grok-ndjson`;
5. `else`, which prints `codex-text`.

The header comment's token list gains `grok-ndjson`.

- **Both sides of the alternation are delimited.** The opening `"` precedes it and the closing
  `"` follows it, so `tool_call` cannot match a `tool_call_update` value, nor the reverse, and no
  type matches as a prefix of a longer one. That applies to every one of the seven branches.
- **Residual (key order):** the grep requires `"type"` to be the object's **first** key, which F0
  measures on every line (spec: `grep -c '^{"type":"'` → 110 lines). The agy grep has the same
  property for `"event"`. A grok build that emits `type` later in the object classifies as
  `codex-text` here, while `scan_grok` (D6) still parses it. The two-instrument test uses
  type-first fixtures only, so this residual is outside its reach, and it is stated rather than
  tested.
- **Residual (spec FR-5):** a grok stream carrying only unobserved `type` values classifies as
  `codex-text`.

### D5 — `_render_progress` grok branch (FR-5)

The existing `if [ "$fmt" = agy-ndjson ] && command -v jq …; then … else <codex lens> fi` gains an
`elif [ "$fmt" = grok-ndjson ]; then` arm between the two. Without it, a grok log would fall into
the codex lens and print `(prompt still echoing — no agent output yet)`, because no grok stream
echoes the boundary. Inside the arm:

- **Without `jq`,** it prints one line, `  (grok stream — jq not on PATH, cannot render)`.
- **With `jq`,** it runs `tail -n 400 "$log" | jq -Rs -r <program> | tail -n "$n"`. The program
  first builds a `toolCallId → toolName` map from the `tool_call` events in the window, then
  reduces the events with a run-state:

| event | rendered line |
|---|---|
| `tool_call` | `  · tool <toolName> <status>` plus a space and `rawInput` rendered by `tojson` and cut to its first 70 characters, when `rawInput` is non-null |
| `tool_call_update`, `status` non-null | `  · tool <joined toolName, or ?> <status>` |
| `tool_call_update`, `status` null | nothing |
| `usage` | `  · turn usage (<.usage.output_tokens> out, <.usage.reasoning_tokens> reasoning)` |
| `end` | `  · END stopReason=<.stopReason> turns=<.num_turns>` |
| a maximal run of `thought` | one line, `  · thinking (<k> events)` |
| a maximal run of `text` | one line, `  · reply text (<k> events)` |
| `available_commands` | nothing |
| any other object with a string `type` | `  · <type>` (the "one line per event" default) |

- **No delta text reaches any line.** The run lines carry only a count. That is AC-5.2's "no line
  containing a single `thought` or `text` delta's text alone".
- **The field paths were read from F0 at `50560eb`:** `usage` events carry
  `.usage.{input_tokens,output_tokens,reasoning_tokens,…}`; `end` carries `stopReason`,
  `num_turns` and `modelUsage`; `tool_call` carries `toolName`, `status`, `rawInput` and
  `toolCallId`; `tool_call_update` carries `status`, `toolCallId` and `rawOutput`, with no
  `toolName`. Command:

  ```bash
  jq -c 'select(.type=="<t>")|keys' <F0> | sort | uniq -c
  ```

  run once for each of the seven types.
- **Reading of AC-5.2.** "Prints exactly these lines" is read as exact counts per named class: 2
  `pending`, 2 `completed`, 1 `END stopReason=end_turn turns=3` and 3 `turn usage` lines. The run
  lines are the non-delta lines the AC's second clause exists to police. A reading that forbids
  run lines would make the second clause redundant. See the report's owed list.
- **The `unjoinable → ?` path is load-bearing.** The 400-line window can start after a
  `tool_call` whose updates it still holds.
- **Unchanged.** The header, the exit 0 and the agy and codex branches are unchanged (AC-5.3).

### D6 — `scan_grok` and the evidence CLI (FR-6)

In `h-mad/scripts/h_mad_review_evidence.py`:

```python
_GROK_TYPES = frozenset({"thought", "text", "available_commands", "tool_call",
                         "tool_call_update", "usage", "end"})

def scan_grok(log_text: str) -> dict | None:
```

**Parsing** follows `scan()`'s line discipline: `strip()`, then skip lines not starting with `{`,
then `json.loads` inside `try`, then skip anything that is not a `dict`. An event counts only when
`event.get("type") in _GROK_TYPES`. When no line qualifies, the function returns `None`.

**Counting:**

- `tools` is the size of the set of `str` `toolCallId`s seen on `tool_call` or `tool_call_update`.
- `ok` is the size of the set of `str` `toolCallId`s seen on a `tool_call_update` whose `status ==
  "completed"`, compared as an exact string on the **parsed** field. Substring matching is
  structurally impossible, which is AC-6.4.
- `unresolved` is `tools − ok`.
- `thinking` sums `event["usage"]["reasoning_tokens"]` over `type == "usage"` events, keeping only
  `int`/`float` values that are not `bool`. `end.usage` is excluded.
- `complete` is true when any `end` event is present.
- `stop_reason` is the last `end` event's `stopReason` when it is a `str`, else `None`.

**`scan()` is untouched** (AC-6.5).

**`main()`.** Inside the existing `if counts["agy_events"] == 0:` branch, **before**
`codex = scan_codex_text(text)`:

```python
grok = scan_grok(text)
if grok is not None:
    if not grok["complete"]:
        print(f"ERROR: {path} is a grok stream with no `end` event (killed, still "
              "running, or copied mid-write) — no counts published", file=sys.stderr)
        print("EVIDENCE: UNREADABLE reason=truncated_no_end")
        return 2
    verdict = "PASS" if grok["ok"] >= 1 else "NONE"
    line = (f"EVIDENCE: {verdict} tools={grok['tools']} ok={grok['ok']} "
            f"unresolved={grok['unresolved']} thinking={grok['thinking']} format=grok")
    if grok["stop_reason"]:
        line += f" stop_reason={grok['stop_reason']}"
    print(line)
    return 0
```

- The agy path is unreachable from this insertion, because it sits inside
  `agy_events == 0`.
- The codex and unsupported path runs only when `scan_grok` is `None`, so it stays
  byte-identical (AC-6.6).
- The `UNREADABLE` exit 2 follows the file's existing cannot-judge convention (`no_log`,
  `empty_log`, `unsupported_format`). Base §"Audit-gate signal discipline" permits a non-zero exit
  for unreadable input.
- The `ArgumentParser` `log` help text gains "or grok streaming-json".

### D7 — Audit-cycle shapes and closed-world routing (FR-7)

**Import.** `from h_mad_review_evidence import scan, scan_grok`.

**`measure_effort()`.** After `counts = scan(text)`, the classification is:

```python
if counts.get("agy_events", 0) > 0:
    counts["shape"] = "parsed"                                  # unchanged
    return counts                                               # (existing flow)
grok = scan_grok(text)
if grok is not None and grok["complete"]:
    return {"readable": True, "shape": "grok", "agy_events": 0,
            "tools": grok["tools"], "ok": grok["ok"], "unresolved": grok["unresolved"],
            "thinking": grok["thinking"], "stop_reason": grok["stop_reason"]}
if grok is not None:
    return {"readable": True, "shape": "grok-truncated", "agy_events": 0}   # no counts
# then the existing codex banner → "codex-text", else "unparseable", unchanged
```

- **The grok dict has no `failed` key.** Grok has no observed failure spelling (spec
  Out-of-Scope). A `failed=0` in the effort sidecar would publish a measurement nobody made.
- **`grok-truncated` has no count keys at all.** That keeps it a cannot-judge
  (spec FR-6/FR-7).
- `write_effort_sidecar()` persists whichever dict it gets, unchanged.

**`combine()`: closed-world routing.** Every shape `measure_effort()` returns is routed
explicitly:

| shape | route |
|---|---|
| `codex-text` | `continue` (unchanged) |
| `missing`, `unparseable` | `UNVERIFIED low_evidence_unmeasurable:p<i>` (unchanged) |
| `empty` | `UNVERIFIED low_evidence:p<i>` (unchanged) |
| `grok-truncated` | `UNVERIFIED low_evidence_unmeasurable:p<i>` (**new**) |
| `parsed`, `grok` | `ok <= DELIVERY_FLOOR` → `UNVERIFIED low_evidence:p<i>` (floor, `grok` new) |
| any other shape | `UNVERIFIED shape_unrouted:p<i>` (**new**) |

- **Why `shape_unrouted` and not `low_evidence_unmeasurable`.** With the defensive default spelled
  the same as the `grok-truncated` route, deleting the `grok-truncated` branch would be an
  **equivalent mutant**, because the default would still produce the expected reason and AC-7.4
  would pass. A distinct reason word keeps that mutation observable (§"Mutation rows and wire force-fires", row A2).
- **What the default can reach.** Today the only reachable shapes are the six named. The
  hand-built `shape is None` fallback maps to `parsed` or `missing` before the table. The default
  is therefore reachable only by a future shape nobody routed, and it is never a count.
- **Measured.** Shape literals asserted in the two audit-cycle test files at `50560eb`:

  ```bash
  grep -on "shape[\"']\?\] *== *[\"'][a-z-]*[\"']\|[\"']shape[\"']: *[\"'][a-z-]*[\"']" \
    h-mad/tests/test_h_mad_audit_cycle.py h-mad/tests/test_hmad_dispatch_audit_cycle.py
  ```

  This finds `codex-text` 2, `empty` 1, `missing` 1, `parsed` 3 (2 asserted plus 1 hand-built
  effort dict), `unparseable` 3, and `test_hmad_dispatch_audit_cycle.py` none (unit: matching
  occurrences). No existing test feeds a shape outside the six, so the default changes no
  existing verdict.
- `DELIVERY_FLOOR = 2` (`grep -n '^DELIVERY_FLOOR' h-mad/scripts/h_mad_audit_cycle.py`). AC-7.2's
  F0 (`ok=2`) is `low_evidence`, and AC-7.3's derived stream needs 3 completed ids.

**`_effort_items()`.** It gains two explicit renderings before the generic line. The generic line
indexes `effort['failed']` and would raise `KeyError` on a grok dict.

- `grok`: `p<i> tools=N ok=K unresolved=U thinking=T format=grok`, plus the existing
  `low-evidence (…)` suffix when `ok <= DELIVERY_FLOOR`.
- `grok-truncated`: `p<i> not measured (grok log truncated — no end event; counts withheld)`.

### D8 — `audit-cycle --surfaces grok` (FR-7)

- In `_cmd_audit_cycle`, the `--surfaces` validation `case "$_s" in agy|codex) ;;` becomes
  `agy|codex|grok`, and its message `unknown agent '$_s' (agy|codex)` becomes `(agy|codex|grok)`.
- Nothing else changes. Plan P8 established that the pass loop dispatches `_cmd_exec
  "${agent[$i]}" … --log "${log[$i]}"` per pass, and that the prompt assembly takes no agent. The
  legacy `_surf+=(agy)` default and the same-surface WARNING stay as they are (FR-7, FR-11).
- **`--legs` default.** Where no `--legs` is given, `legs=("${_surf[@]}")`, so a `--surfaces
  agy,grok` cycle records the leg set `agy+grok` with no new code.

**Valid-set census** (plan grammar; unit: matching lines per enclosing function):

```bash
awk '/^_[a-z_]+\(\) *\{/{fn=$1} /codex\|agy|agy\|codex/{print fn}' h-mad/scripts/hmad-dispatch.sh | sort | uniq -c
# reading at 50560eb (15 lines): 3 _cmd_exec()  2 _cmd_audit_cycle()  1 _cmd_resolved_model()
#   3 _cmd_exec_pane()  1 _cmd_launch()  1 _cmd_pin()  1 _cmd_resolve()  1 _cmd_verify()
#   1 _agent_tail_re()  1 _resolve_target()
```

- **Six lines gain `grok`:** `_cmd_exec`'s header comment, its `case` and its message, which is 3
  of 3; `_cmd_audit_cycle`'s `case` and message, 2 of 2; and `_cmd_resolved_model`'s header
  comment, 1 of 1. The other 9 are pane-path functions and stay `codex|agy` (AC-3.7).
- **This grammar cannot see the change**, because `codex|agy|grok` still contains `codex|agy`. The
  15 does not move. The post-change check is
  `grep -c 'codex|agy|grok\|agy|codex|grok' h-mad/scripts/hmad-dispatch.sh`, which must read 6
  matching lines at 5g.

### D9 — Assembler `--agent` and the presence-judged `--timeout` (FR-8)

In `h-mad/scripts/h_mad_assemble_tdd.py`:

- `ap.add_argument("--agent", choices=("codex", "grok"), default="codex")`.
- `ap.add_argument("--timeout", type=int, default=None)`. After parsing:
  `timeout = args.timeout if args.timeout is not None else (1500 if args.agent == "grok" else 900)`.
- `command_block(..., agent: str = "codex")` builds its first line as
  `f"hmad-dispatch exec {agent} {q(str(prompt))}{over} \\"`, and `main()` passes
  `agent=args.agent, timeout=timeout`.

**Why `default=None` is "presence in argv, never value".** With `type=int`, the only way
`args.timeout` is non-`None` is that the flag appeared. `--timeout 900` therefore stays 900 under
grok (AC-8.2).

The sentinel also closes a class that a hand-rolled `"--timeout" in argv` scan would miss. Argparse
accepts `--timeout=900`, and with `allow_abbrev` at its default of true it also accepts the
unambiguous prefix `--ti 900`. **Executed at `50560eb`** on a parser with the assembler's four
`--t…` options (`--task`, `--test-path`, `--template`, `--timeout`): `['--ti','900']` → 900,
`['--timeout=900']` → 900, `[]` → None. Argparse is the single judge of presence, so every
spelling it accepts counts.

- **The prompt file is agent-independent.** `assemble()` takes no agent, so AC-8.3's sha256
  equality holds by construction.
- **State is not read.** `main()` opens no state file (AC-8.5).
- **The existing default output is byte-identical.** `agent="codex"` and `timeout=900` reproduce
  today's block exactly (AC-8.1). The `ASSEMBLE-TDD:` line and the `sandbox_read_only` HALT are
  unchanged.

### D10 — `resolved-model grok` (FR-9)

In `h-mad/scripts/h_mad_resolved_model.py`:

- `choices=("codex", "agy", "grok")`, and the `--log` help text becomes "(codex, grok)".
- A new `grok_from_log(path: str | None)`. It refuses through `_fail()` (stderr `RESOLVED-MODEL:
  UNKNOWN — …`, exit 2) in each of these cases:
  - no `--log`: "a grok model is read only from its stream's `end` event; no grok config source
    has been probed";
  - a missing file;
  - no `end` event;
  - a last `end` whose `modelUsage` is not a non-empty `dict`;
  - more than one key, with the message naming the keys in sorted order (AC-9.2 F-TWOMODEL).
- On success it calls `_emit("grok", key, "-", "resolved", path)`. The **last** `end` event in
  file order is read (AC-9.3 F-SHARED).
- **`main()` order.** The grok branch is the **first** branch:
  `if a.agent == "grok": grok_from_log(a.log); return 0`. It sits before the existing `if a.agent
  == "codex"` and before the agy code, which is today an implicit fall-through after codex.
  `--config` and `--agy-log-dir` are not consulted for grok.
- The header comment of `_cmd_resolved_model` becomes `# <codex|agy|grok> [--log <f>] …`. Its
  body forwards `"$@"` unchanged (plan P10).

### D11 — Legs change when an audit switches `doc-auditor` → `grok` (executed)

The plan read this in `h_mad_audit_gate.py` and did not execute it. The design executed
`exit_check()` at `50560eb` on stamps named in the `_STAMP_NAME_RE` grammar (`<feature>.design.
audit.v<N>.<leg>.md.gated.json`), each carrying `verdict: PASS` and `suite: PASS`. The run used a
`tempfile.TemporaryDirectory`, which removed itself.

| cycles fed (legs per cycle) | `exit_check()` result |
|---|---|
| v1 `[agy, doc-auditor]`, v2 `[agy, grok]` | `BLOCKED legs_changed:agy+doc-auditor\|agy+grok` |
| v1 `[agy, doc-auditor]`, v2 `[agy, grok]`, v3 `[agy, grok]` | `READY`, cycles v2+v3, legs `agy+grok` |
| v2 `[agy, grok]`, v3 `[agy, doc-auditor]` | `BLOCKED legs_changed:agy+grok\|agy+doc-auditor` |

A switch therefore resets the exit streak once: two clean cycles under the new leg set are needed.
Switching back resets it again. The compared value is the recorded `legs` list, so the result holds
whatever name the teammate leg was recorded under.

- **Owed to `SKILL.md`** (FR-10, teammate-leg section): choose the leg set before a document's
  first gating cycle. A mid-document switch costs one cycle, and it interacts with §"Document-audit
  round cap — Phase 5 is the gate".
- **Residual:** `round_check()` was not exercised against a switch.

### D12 — Documentation (FR-10)

Headings verified present at `50560eb` (`grep -cF '<heading>' h-mad/SKILL.md`; unit: matching
lines):

- `Codex authors Phase 5 — enforced, not just instructed`: 1;
- ``Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot``: 1;
- `Teammate audit leg — when codex is unavailable`: 1;
- `Never gate on one audit pass`: 4, of which 1 is a `## ` heading. The rest are prose mentions,
  and a heading locator must match the heading line.

`h-mad/references/agent-substrate.md` has `## Verbs`. `h-mad/references/state-schema.md` exists.

Content per surface. Each needle AC-10.1 and AC-10.2 name is in parentheses.

- **Phase-5 section:**
  - the FR-2 table (`fallback_agent`);
  - OQ1 (`HMAD_CODEX_UNAVAILABLE`);
  - the disclosure that codex writes pass `h-mad/hooks/h-mad-codex-tdd-gate.py` and grok writes
    pass nothing (`no write-time test-first gate`);
  - the inherited no-`jq` fail-open (D2).
- **Exec section:** `exec grok` and `--agent grok` with the 1500 s default, plus the D4 statement.
- **Teammate section:**
  - grok as the preferred independent stand-in (`--surfaces agy,grok`);
  - the D4 statement (`unmeasured`);
  - the one-codex-round-owed rule;
  - the D11 legs-change outcome;
  - the unchanged path when `fallback_agent` is absent or `claude`.
- **Never-gate section:** a cross-reference to the teammate routing.
- **`state-schema.md`:** `fallback_agent` and, per plan P6, its sibling `codex_status`.
- **`agent-substrate.md` §"Verbs":**
  - `exec grok` with its argv, the child-only scrub and `HPW_AGENT_BACKEND`;
  - the inherited `GROK_SANDBOX`;
  - `--always-approve` as a grant wider than codex's `workspace-write`;
  - grok tree-delta as "reported, not trusted" (spec Out-of-Scope, probe finding 6).

### D13 — The Phase-5 live smoke

It is referenced and not redesigned. It is plan v1.3 §"Convention Prerequisites": one bounded
`exec grok` through the **worktree's** `h-mad/bin/hmad-dispatch`, with its recorded `readlink -f`
and the `b.txt` = `probe` read-back. The design adds nothing to its pass conditions. D3.4's `<
/dev/null` and D3.3's `env` prefix are the two design-level mechanisms it exercises that no stub
can falsify.

## Mutation rows and wire force-fires

Every row is one harness `find`/`replace`, as the harness grammar requires. The `find` strings are
written against the landed code at 5d, and the impl-plan owns the literals. The names below are
fixed here.

Spec files are new JSON under `h-mad/tests/mutation-specs/`. Proposed names:

- `tdd_gate_fallback_agent.json`, for rows G*;
- `grok_exec.json`, for rows P* and the W1–W5 and W8 force-fires;
- `review_evidence_grok.json`, for rows E* and W6;
- `audit_cycle_grok.json`, for rows A* and W7;
- `assemble_tdd_agent.json`, for rows T* and W10;
- `resolved_model_grok.json`, for rows R* and W11.

Each spec's `command` follows the house form: 98 of the 99 specs at `50560eb` lead with
`python3.11`, and 1 with `/opt/anaconda3/bin/python3.11`. The count was taken by printing
`command[0]` of each `h-mad/tests/mutation-specs/*.json` and running `uniq -c` (unit: files).
Scoring is on the `MUTATION:` token, never `$?`.

| Row | Target | Mutation | Killed by |
|---|---|---|---|
| G1 (AC-2.7) | gate | the `grok)` arm's `exit 1` → `;;` fall-through | AC-2.1 `"grok"` cells with codex_out true |
| G2 (AC-2.7) | gate | `grok)` arm guarded by `[ -z "${HMAD_CODEX_UNAVAILABLE:-}" ]`, so the env bypasses it | AC-2.1 cells with `HMAD_CODEX_UNAVAILABLE=1`, `"grok"` |
| G3 (AC-2.7) | gate | `.orchestrator_state[$k]` in the fallback read → the first entry whose key `!= $k` | AC-2.1 `"grok"` cells: the matrix fixture carries a **second, non-`step5` feature with no `fallback_agent`**, so the mutant reads `absent` and falls through. AC-2.5 also kills it |
| G4 | gate | typed read → `.fallback_agent // "absent"` form (`//` reintroduced) | AC-2.1b `false` cells |
| G5 | gate | `if $v == null` → `if $v == null or $v == "null"` (the `-r` collapse) | AC-2.1b `"null"` cells against the JSON-`null` control |
| G6 | gate | `*)` read-error arm → `*) ;;` (fail-open) | design test "read error fails closed" (Test Plan) |
| P1 | `_grok_final_message` | drop `or $e.type == "usage"` from the closers | F-SEP-usage (Test Plan). **Survives on F0**, executed below |
| P2 | `_grok_final_message` | drop `$e.type == "tool_call" or` | F-SEP-tool_call |
| P3 | `_grok_final_message` | drop `or $e.type == "tool_call_update"` | F-SEP-tool_call_update |
| P4 | `_grok_final_message` | append `thought` data like `text` | AC-4.3 F-DECOY, with the thought decoy placed inside the final segment (Test Plan) |
| P5 (W3b) | `_grok_final_message` | region read `tail -n "+$(( pre + 1 ))"` → `tail -n +1` | AC-4.7 |
| P6 | `_grok_region_state` | always print `complete` | AC-4.5: F-TRUNC's non-empty final segment then takes the success row, so rc is 0 and no `TRUNCATED` line is printed |
| P7 (W4) | `_grok_last_tool` | drop the "no `tool_call` → empty" guard | AC-4.9, with AC-4.6 as its positive pair |
| E1 | `scan_grok` | `ok` from a substring test (`"completed" in line`) | AC-6.4 |
| E2 | CLI | truncated branch prints the counted line | AC-6.3 (asserts no `tools=`) |
| A1 | `_effort_items` | drop the `grok-truncated` rendering | shape-enumeration test (render row must say "not measured") |
| A2 (W7b) | `combine` | delete the `grok-truncated` route | AC-7.4 (the mutant yields `shape_unrouted`) |
| T1 | assembler | `args.timeout is not None` → `args.timeout not in (None, 900)` (value-judged) | AC-8.2 `--agent grok --timeout 900` |
| R1 | resolver | accept the first `modelUsage` key when there are several | AC-9.2 F-TWOMODEL |
| R2 | resolver | first `end` instead of last | AC-9.3 |

**The closer rows are per-branch, and they were executed.** The closer set is an alternation, and
a healthy sibling covers a sick one. On F0 the two text segments are separated by `usage`,
`tool_call` **and** `tool_call_update`. F0's type-run sequence
(`jq -r .type <F0> | uniq -c`) reads `… text×18 available_commands×1 usage×1 tool_call×1
tool_call_update×2 … text×3 available_commands×1 usage×1 end×1`. So dropping any one closer leaves
F0's result unchanged.

Executed at `50560eb`, with the healthy program above and each one-closer-removed mutant:

- on F0 the drop-`usage` mutant gave `["I'll read …\"probe\".","STATUS: DONE"]`, identical to
  healthy, so P1 **survives on F0**;
- each design fixture keeps exactly one closer type between the segments;
- healthy gives `[2,"STATUS: DONE"]` on all three fixtures, and the matching mutant gives one
  merged segment ending `…"probe\".STATUS: DONE`, whose line does not start with `STATUS:`.

| fixture | derivation from F0 | lines (unit: lines) |
|---|---|---|
| F-SEP-usage | drop every `tool_call` and `tool_call_update` | 104 |
| F-SEP-tool_call | drop every `tool_call_update` and `usage` | 103 |
| F-SEP-tool_call_update | drop every `tool_call` and `usage` | 105 |

The fixtures were derived with
`jq -c --arg k <kept> 'select(.type == $k or ((.type=="tool_call" or .type=="tool_call_update" or .type=="usage") | not))' <F0>`,
and each keeps F0's single `end`.

**Residual (`end` closer):** dropping `end` from the closers is an equivalent mutant on any region
where `end` is the last event, which F0 measures and a single dispatch's region always has. No row
is filed. This residual is exactly the class "text following `end` within one region".

**Wire force-fires W1–W11.** These are plan v1.3's table, bound to design mechanisms.

| Wire | WIRE-PIN (remove the call) | Force-fire (one replace) | Fails |
|---|---|---|---|
| W1 | AC-3.1 | S4 `if [ "$agent" = grok ]; then` → `if true; then` | `test_hmad_dispatch_exec.py::test_codex_exec_runs_headless_with_the_right_flags` and `::test_agy_exec_runs_print_headless_prompt_as_last_arg`: the child is `env … grok …`, there is no `grok` on the test PATH, `env` exits 127, and the capture is never written |
| W2 | AC-3.3 | codex arm's `"$wait_secs" codex "${args[@]}"` → `"$wait_secs" env "${child_env[@]}" codex "${args[@]}"` | AC-3.4 (the codex stub loses the caller's `CLAUDE*`) |
| W3 | AC-4.1 | (a) agy arm's `resp="$(_agy_ndjson_response` → `resp="$(_grok_final_message`; (b) row P5 | (a) `test_hmad_dispatch_exec.py::test_agy_exec_stdout_is_the_response`, via `returncode == 0`: an agy log has no `text` event, so the result is rc 3. (b) AC-4.7 |
| W4 | AC-4.6 | row P7 | AC-4.9 |
| W5 | AC-5.1 / 5.2 | insert `_grok_log_has_events "$log" && { printf 'grok-ndjson'; return 0; }` before the agy grep | AC-5.1 mixed log (`{"event":"init"}` + F0) prints `grok-ndjson` |
| W6 | AC-6.1 | `if counts["agy_events"] == 0:` → `if counts["agy_events"] == 0 or scan_grok(text) is not None:` | mixed agy+F0 CLI test (stdout and rc must equal the agy-alone run) |
| W7 | AC-7.2 / 7.3 / 7.4 | (a) `if counts.get("agy_events", 0) > 0:` → `… > 0 and scan_grok(text) is None:`; (b) row A2 | (a) mixed agy+F0 `measure_effort` test (shape must be `parsed`); (b) AC-7.4 |
| W8 | AC-7.1 | `_cmd_exec "${agent[$i]}"` → `_cmd_exec grok` | `test_hmad_dispatch_audit_cycle.py::test_verb_two_distinct_dispatches` |
| W9 | AC-2.1 BLOCK-GROK cells | row G3 | AC-2.5 and the AC-2.1 grok cells |
| W10 | AC-8.2 | (a) `default="codex"` on `--agent` → `default="grok"`; (b) see residual | (a) AC-8.1 and `test_h_mad_assemble_tdd.py::TestCli::test_a_clean_assembly_prints_pass_and_the_command_block` |
| W11 | AC-9.1 | `if a.agent == "grok":` → `if True:` | `test_h_mad_resolved_model.py::test_codex_reads_the_resolved_model_out_of_its_session_header` and `::test_agreement_between_the_two_newest_is_answerable` |

- **The named existing nodes collect at `50560eb`.** The plan's collect command, re-run, prints
  `7 tests collected` (unit: tests).
- **Residual (W10b).** "Agent read from state" is killed by AC-8.5. It has no harness row, because
  the mutant would need a state reader the assembler does not contain, and it cannot be written
  as one replace.
- **Residual (whole table).** Whether each force-fire kills is a prediction until 5d/5e runs it.

## Verified premises (design-level, executed at `50560eb`)

Each command below was run at `50560eb`. Scratch artifacts were written under the session
scratchpad or a `TemporaryDirectory` and deleted after the run.

- **V1 — the tree is the plan's tree.** `git diff --name-only 1680271 50560eb -- h-mad handoff |
  wc -l` → 0 files.
- **V2 — F0 is unchanged.**
  `shasum -a 256 docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson` →
  `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`; `git log --format=%h -1 --`
  the same path → `d2fbb96`.
- **V3 — AC census.** `grep -oE '^  - AC-[0-9]+\.[0-9]+[a-z]?'
  docs/01-plan/features/grok-codex-fallback.spec.md | sort -u | wc -l` → 55 distinct ids.
- **V4 — the D2 jq read**, on 13 stored values plus a corrupt file (outputs in D2).
- **V5 — the D2 FALL-THROUGH fixture works on the current hook.** The fixture is a
  `TemporaryDirectory` project with `docs/.bkit-memory.json`, feature `feat` at `phase: step5`,
  and a failing `shared/tests/test_widget.py`. The hook was run as `bash
  h-mad/hooks/h-mad-tdd-gate.sh shared/widget.py`, with cwd = project, `CLAUDE_PROJECT_DIR` =
  project and `PATH=<empty bin>:/usr/bin:/bin`. It exited 0 with empty stderr both with
  `codex_status: exhausted` and with codex off PATH.
  - The target must be **relative** with a `shared/`, `hematology-paper-writer/` or
    `clinical-statistics-analyzer/` prefix. `h_mad_derive_test_path.sh` returns empty for every
    other layout, including any absolute path, and that reads as BLOCK `cannot derive test path`,
    which would fail every FALL-THROUGH cell for the wrong reason. Read with
    `sed -n '/^case "\$PROD_PATH"/,/^esac/p' h-mad/scripts/h_mad_derive_test_path.sh`.
  - The AC-2.1 test asserts the derived path exists as a precondition.
- **V6 — the segmenter on F0 and on the three closer fixtures** (D3.5, §"Mutation rows").
- **V7 — the env scrub** (D3.3), and **`set -u` on a bare `local`** (D3).
- **V8 — argparse presence** (D9).
- **V9 — the legs switch** (D11).
- **V10 — interpreter and PATH facts:**
  - `head -1 h-mad/scripts/hmad-dispatch.sh` → `#!/usr/bin/env bash`;
  - `head -1 h-mad/bin/hmad-dispatch` → `#!/bin/bash`, which ends `exec bash "$REAL" "$@"`;
  - `ls -la /usr/bin/jq` → present, so `jq` is on the gate tests' `/usr/bin:/bin` PATH.
- **V11 — gate test harness.** `test_h_mad_tdd_gate_codex.py` builds the env as
  `{"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()), …}`. The hook resolves
  `$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh`, which is the **main tree**
  through the install symlink even when the hook under test is the worktree's. That is harmless
  here because the derive script is unchanged, and it is stated so a later edit to that script is
  not silently tested against the old copy.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `fallback_agent` property | `h-mad/scripts/h_mad_state_schema.json` | modify | FR-1, D1 |
| typed fallback read, BLOCK-GROK / BLOCK-INVALID | `h-mad/hooks/h-mad-tdd-gate.sh` | modify | FR-2, D2 |
| `_cmd_exec` S1/S3/S4/S6/S8, grok arm, `child_env`, `local recovered=""` | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-3, FR-4, D3 |
| `_grok_log_has_events`, `_grok_region_state`, `_grok_final_message`, `_grok_stop_reason`, `_grok_last_tool` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-4, FR-5, D3.5, D4 |
| `_exec_log_format`, `_render_progress` grok branch | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-5, D4, D5 |
| `_cmd_audit_cycle` `--surfaces` case + message; `_cmd_resolved_model` header | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-7, FR-9, D8, D10 |
| `_GROK_TYPES`, `scan_grok`, `main` grok branch | `h-mad/scripts/h_mad_review_evidence.py` | new / modify | FR-6, D6 |
| import, `measure_effort`, `combine`, `_effort_items` | `h-mad/scripts/h_mad_audit_cycle.py` | modify | FR-7, D7 |
| `--agent`, `--timeout` sentinel, `command_block(agent=)` | `h-mad/scripts/h_mad_assemble_tdd.py` | modify | FR-8, D9 |
| `grok_from_log`, `choices`, `main` order | `h-mad/scripts/h_mad_resolved_model.py` | new / modify | FR-9, D10 |
| Phase-5, exec, teammate-leg, never-gate sections | `h-mad/SKILL.md` | modify | FR-10, D12 |
| field semantics | `h-mad/references/state-schema.md` | modify | FR-10 |
| `exec grok` verb | `h-mad/references/agent-substrate.md` | modify | FR-10 |
| grok stub | `h-mad/tests/stubs/grok` | new | FR-3–FR-5, FR-7 |
| F0-derived fixture builder | `h-mad/tests/grokfixtures.py` | new | one fixture source |
| new test files (Test Plan) | `h-mad/tests/test_*.py` | new | FR-1–FR-11 |
| mutation specs (six files) | `h-mad/tests/mutation-specs/*.json` | new | AC-2.7, W1–W11, rows above |

## Implementation Order

1. **Fixtures and stub.** Build `grokfixtures.py`, which carries the F0 sha256 check, every spec
   fixture and the three F-SEP fixtures, and the `stubs/grok`. There is no production code in
   this step.
2. **Leaves:**
   - D1 schema (FR-1);
   - D9 assembler (FR-8);
   - D10 resolver (FR-9);
   - D6 `scan_grok` and CLI (FR-6).
   These are pure, and each is testable from the fixtures alone.
3. **D7 audit-cycle shapes** (FR-7 Python side). This depends on D6.
4. **D3 `_cmd_exec` grok arm and the D3.5 readers** (FR-3, FR-4). D4/D5 follow (FR-5), because
   the auto-log digest calls `_render_progress`.
5. **D8 `--surfaces grok`** (FR-7 transport). This depends on step 4.
6. **D2 gate** (FR-2). It is independent of steps 2–5, but it is sequenced after them so the
   BLOCK-GROK stderr can name the assembler flag that exists by then.
7. **Two-instrument agreement test.** This depends on D4 and D7.
8. **Mutation specs** and the wire-scoped reverts (W1–W11).
9. **D12 documentation** and the heading-located doc test (FR-10), against shipped behaviour.
10. **Full `h-mad/tests` + `handoff/tests` run.** Then the Phase-5 live smoke (D13), and then
    the pre-merge gate.

## Data Model / Schema Changes

- **State record:** new optional `fallback_agent: "grok" | "claude" | null` (D1). No change to
  `required`, `codex_status` or the historical schema.
- **Effort dict, `shape: "grok"`:** `{readable: true, shape, agy_events: 0, tools: int, ok: int,
  unresolved: int, thinking: int, stop_reason: str | null}`. There is no `failed` key.
- **Effort dict, `shape: "grok-truncated"`:** `{readable: true, shape, agy_events: 0}`, with no
  counts.
- **Persistence:** both dicts are written as-is by `write_effort_sidecar()` to
  `<report>.effort.json`.
- **`combine()` reason words:** new `shape_unrouted:p<i>`. `grok-truncated` reuses
  `low_evidence_unmeasurable:p<i>`.

## API / Interface Changes

- **`hmad-dispatch exec grok <promptfile> [--cd] [--model] [--effort] [--out] [--log] [--timeout]
  [--sandbox <profile>]`.** The child runs `env -u CLAUDE* … HPW_AGENT_BACKEND=<v> grok --cwd
  <cd> --always-approve --output-format streaming-json --prompt-file <bounded> [--model]
  [--reasoning-effort] [--sandbox]`. It returns grok's rc, 3 for an rc-0 EMPTY, or 124 on a
  watchdog kill. The new stderr lines are:
  - `grok stopReason=<v>`;
  - `TRUNCATED — no end event …`;
  - `grok stream not parsed — jq not on PATH`;
  - `last step reached — N tool calls completed; last tool: <name> <status>`.
- **`hmad-dispatch progress`:** new token `format: grok-ndjson`.
- **`hmad-dispatch audit-cycle --surfaces`:** accepts `grok`.
- **`hmad-dispatch resolved-model grok --log <f>`:** new.
- **`h_mad_review_evidence.py <log>`:**
  - `EVIDENCE: PASS|NONE tools= ok= unresolved= thinking= format=grok [stop_reason=]`, exit 0;
  - `EVIDENCE: UNREADABLE reason=truncated_no_end`, exit 2;
  - new importable `scan_grok(log_text: str) -> dict | None` and `_GROK_TYPES`.
- **`h_mad_audit_cycle.measure_effort()`:** may return shapes `grok` and `grok-truncated`.
- **`h_mad_assemble_tdd.py --agent {codex,grok}`:** the default is `codex`. `--timeout`'s default
  becomes the not-given sentinel `None`, resolved to 900, or 1500 for grok.
  `command_block(..., agent: str = "codex")`.
- **`h_mad_resolved_model.py`:** agent `choices` gains `grok`.
  `grok_from_log(path: str | None) -> None`.

## Error Handling Strategy

- **Gate.** Every non-FALL-THROUGH outcome is exit 1 with a `[H-MAD-TDD-GATE] BLOCK:` stderr line,
  which is the hook's existing contract. A read failure is BLOCK-INVALID `<unreadable>`,
  fail-closed. The no-`jq` exit 0 is the existing, disclosed fail-open.
- **Wrapper.** Every grok reader degrades to empty or `unknown` and never aborts `_cmd_exec` under
  `set -euo pipefail` (`|| true`, `select(type == "object")`). A missing `jq` routes to the EMPTY
  path with an explicit "not parsed" line. That is never a false success, and never a false
  `TRUNCATED`.
- **Evidence CLI and combiner.** Cannot-judge is spelled distinctly at every layer:
  - `scan_grok` → `None`;
  - the CLI → `UNREADABLE reason=truncated_no_end`, exit 2, with no counts;
  - the combiner shape → `grok-truncated` → `low_evidence_unmeasurable`;
  - an unrouted shape → `shape_unrouted`.
  None of them ever takes the delivery-floor branch.
- **Resolver.** Every unestablished case is `RESOLVED-MODEL: UNKNOWN — <reason>` on stderr, exit 2,
  and it never guesses.
- **Markers.** No orchestrator phase transition is added. The gate's and wrapper's stderr lines
  follow their existing prefixes.

## Test Strategy

- **Unit, pure parsers.** `scan_grok`, `measure_effort`/`combine`/`_effort_items`,
  `grok_from_log` and the assembler are driven in-process from `grokfixtures.py`.
- **Integration, wrapper and hook.** These run as subprocesses against the real `hmad-dispatch.sh`
  and the real hook, with an isolated `PATH=<bindir>:/usr/bin:/bin`.
  - `bindir` symlinks `stubs/grok`, plus `codex`/`agy` where a cell needs them. It follows
    `_bindir` in `test_hmad_dispatch.py`, which also links the real `jq`.
  - No real `grok` is ever on the test PATH, and no test makes a live xAI call.
- **The grok stub models what the wrapper consumes.** It:
  - records argv to `HMAD_STUB_CAPTURE` as `grok <argv>`;
  - records `HPW_AGENT_BACKEND` and every `CLAUDE*` name to `HMAD_STUB_ENV_CAPTURE`;
  - **copies the `--prompt-file` contents** to `HMAD_STUB_GROK_PROMPT_CAPTURE` at invocation;
  - writes the file named by `HMAD_STUB_GROK_STREAM` to stdout line by line;
  - sleeps `HMAD_STUB_GROK_SLEEP` after emitting (AC-4.8);
  - exits `HMAD_STUB_GROK_RC`.
  Knob names follow the existing `HMAD_STUB_<AGENT>_*` convention seen in `stubs/agy` and
  `stubs/codex`.
- **One fixture source.** Every grok stream in every test comes from `grokfixtures.py`, which
  asserts F0's sha256 before deriving.
- **Base comparisons are against a pinned sha, not `merge-base`.** After merge, `merge-base HEAD
  main` is HEAD, and the comparison would become identity. The fork sha recorded at 5c is
  written into the test as a constant.
  - AC-2.2 runs `git show <sha>:h-mad/hooks/h-mad-tdd-gate.sh` to a temp file and runs it.
  - AC-8.1 extracts the base skill with `git archive <sha> h-mad | tar -x -C <tmp>`, because the
    assembler resolves `SKILL_DIR` and `TEMPLATE` from `__file__`. It then runs both assemblers
    and normalises each output's own `SKILL_DIR` prefix before the byte comparison. The block
    embeds `SKILL_DIR/scripts/h_mad_extract_verdict.py`, so un-normalised outputs differ by path
    alone.
- **Full suite per task.** `/opt/anaconda3/bin/python -m pytest h-mad/tests handoff/tests` runs
  per task, never scoped only (plan Convention Prerequisites; AC-11.1/11.2).

## Test Plan

These are new files, and the names are proposals the impl-plan may keep or rename. No existing
test file is edited (FR-11). Each row lists its ACs and the design tests it adds.

| File | Covers |
|---|---|
| `h-mad/tests/grokfixtures.py` | the F0 path + sha256 assert; builders for F-TRUNC, F-NOTOOLS, F-NOTEXT, F-NOTOOLTEXT, F-DECOY, F-BEAT, F-SPACED, F-TWOMODEL, F-SHARED, F-SEP-usage, F-SEP-tool_call, F-SEP-tool_call_update, the AC-7.3 three-completed stream, and the mixed agy+F0 log |
| `test_h_mad_state_fallback_agent.py` | AC-1.1–1.4 (AC-1.3 over `h-mad/tests/fixtures/state_incident_replay.json`) |
| `test_h_mad_tdd_gate_fallback_agent.py` | AC-2.1 (80 cells, expected value from an in-test transcription of the table), AC-2.1b (24 BLOCK-INVALID + 3 JSON-`null` control + absent control + 8 BLOCK-CODEX), AC-2.2 (16 × 3 against the pinned base), AC-2.3–2.6; design test **read error fails closed** (a `jq` shim in `bindir` that execs the real `jq` except when its filter mentions `fallback_agent`, where it exits 5 → BLOCK-INVALID `<unreadable>`) |
| `test_hmad_dispatch_exec_grok.py` | AC-3.1–3.7, AC-4.1–4.9; design tests: F-SEP ×3 (stdout `STATUS: DONE`), **no-jq** EMPTY path (a `bindir` without `jq`, where stderr has `not parsed` and no `TRUNCATED`) |
| `test_hmad_dispatch_progress_grok.py` | AC-5.1, AC-5.2 (per-class counts + no delta text) |
| `test_h_mad_review_evidence_grok.py` | AC-6.1–6.4, AC-6.6; mixed agy+F0 CLI equality (W6) |
| `test_h_mad_audit_cycle_grok.py` | AC-7.2–7.4; shape enumeration: `missing`, `empty`, `parsed`, `grok`, `grok-truncated`, `codex-text`, `unparseable`, each asserted to its D7 route and `_effort_items` rendering, plus a hand-built unknown shape → `shape_unrouted`; mixed agy+F0 `measure_effort` → `parsed` (W7a) |
| `test_hmad_dispatch_audit_cycle_grok.py` | AC-7.1 |
| `test_grok_two_instruments.py` | **two-instrument agreement.** On F0, F-SPACED, F-TRUNC, an agy log, a codex-banner log and the mixed log, the `format:` of `hmad-dispatch progress` and `measure_effort()["shape"]` agree under the mapping `agy-ndjson ↔ parsed`, `grok-ndjson ↔ grok \| grok-truncated`, `codex-text ↔ codex-text \| unparseable`. **Single-source:** the alternation parsed out of `_grok_log_has_events` in `hmad-dispatch.sh` equals `h_mad_review_evidence._GROK_TYPES` as a set (base §"Single-source contract") |
| `test_h_mad_assemble_tdd_agent.py` | AC-8.1–8.5 (AC-8.2 includes `--timeout=900` and `--ti 900` under `--agent grok`) |
| `test_h_mad_resolved_model_grok.py` | AC-9.1–9.3 |
| `test_grok_fallback_docs.py` | AC-10.1 via `docsections.titled_section`, which asserts a missing heading and never skips; AC-10.2 |

- **AC-6.5, AC-7.5, AC-9.4, AC-11.1 and AC-11.2** are the unchanged pre-existing files passing in
  the full run. The node-id floor (plan Success Criteria) proves no deletion.
- **F-DECOY placement (design).** F0's final segment is its last three `text` events (`STATUS`,
  `:`, ` DONE`). They are replaced by one `text` event `All done.`, followed immediately by the
  `thought` decoy, then the `tool_call` decoy, then the bare `STATUS: DONE` line, all before the
  `usage` closer that follows. The `thought` decoy then sits **inside** the final segment, which
  is what makes row P4 observable: the mutant's final message becomes `All done.STATUS: DONE`.
- **Verification commands:**

  ```bash
  /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests
  python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/<spec>.json   # read MUTATION:
  grep -c 'codex|agy|grok\|agy|codex|grok' h-mad/scripts/hmad-dispatch.sh                   # 6 matching lines (D8)
  ```

  The last command's reading is a design expectation, re-measured at 5g.

## Invariant Compliance

**Base layer (`h-mad/invariants.base.md`):**

- **Audit-gate signal discipline.** It complies. The evidence CLI's grok verdicts `PASS`/`NONE`
  exit 0. The `UNREADABLE` exit 2 is the existing cannot-judge convention for unreadable input.
  The `progress` exit is unchanged. The gate hook is a PreToolUse block, where exit 1 is its
  documented contract, not a consumed verdict.
- **Single-source contract.** It complies. The seven-type vocabulary lives in `_GROK_TYPES` and
  in `_grok_log_has_events`, and `test_grok_two_instruments.py` asserts that the two sets are
  equal.
- **Standalone / no plugin dependency; no new external dependency.** It complies. The design adds
  stdlib Python, `jq` where the agy path already requires it, and POSIX `env`. `grok` is a runtime
  option of one verb, never needed by the suite.
- **Portable time bounds.** It complies. The grok child is bounded by `_exec_run`'s watchdog, and
  no `timeout`/`gtimeout` is introduced.
- **Doc-template superset compliance.** It complies. The document carries every Phase-4 template
  section. The precheck and doc-shape check run on the saved file.
- **Operator-override preservation; backward compatibility.** Not touched. No audit-gate change is
  made, and D11 only executes the existing gate.
- **Marker discipline.** No phase transition is added.
- **Mutation verification.** It complies. The gate's effect is verified by exit and stderr re-read
  per cell. The wrapper's `--out` write keeps `_write_out_atomic`. The live smoke reads `b.txt`
  back.
- **Test discrimination.** It complies. Every guard has a named killing row (§"Mutation rows").
  - The alternation-branch rule is applied per branch: three closer fixtures, each executed, with
    the `end` branch declared equivalent and scoped.
  - The BLOCK-INVALID class is exercised one value per case (AC-2.1b).
  - The absence assertion AC-4.9 is paired with the presence assertion AC-4.6.
- **Verifying a review finding; guard narrowing.** No guard is loosened. The gate only gains
  blocks.
- **Connection enforcement.** It complies. W1–W11 each have a wire-scoped revert and a one-replace
  force-fire.
- **Incident replay.** It complies. F0, the real probe transcript, is the root of every fixture.
- **Assumption verification; behavioural premises carry their command.** It complies. V1–V11 and
  every D-section reading carry the command and one reading at `50560eb`.
- **Counts a dispatch reports.** Every count here was re-derived at `50560eb`, not carried.
- **Wrapper–runtime reconciliation.** It complies through plan v1.3's live smoke (D13). The
  `--model`/`--sandbox` argv paths stay stub-verified only, as the plan's stated residual.
- **Regression provenance.** No existing test is edited.
- **Both halves of a doc change.** No documented capability is removed.
- **Reimplementation parity.** Not applicable.

**Project layer (`.h-mad/invariants.md`):**

- **Skill self-containment.** It complies. No code or test reads outside `h-mad/`, apart from the
  documented `~/.claude/...` install path the hook already uses. The HemaSuite `_MARKERS`
  reference is a documentation citation only.
- **Skill manifest integrity.** It complies. `SKILL.md`'s frontmatter is untouched, and the entry
  behaviour change is documented in `SKILL.md` (D12).

## Version History
- v1.0: Initial design draft (2026-09-28) from spec v1.2 and plan v1.3, tree read at 50560eb. Typed fail-closed fallback_agent read placed after BLOCK-CODEX; explicit grok arm first in _cmd_exec with S4/S8 else arms made explicit elifs; child-only env -u CLAUDE* scrub; jq segmenter, region state, last-tool readers scoped by pre_lines; grok-ndjson detection helper after agy; scan_grok and closed-world combine routing with a distinct shape_unrouted reason; presence-judged --timeout sentinel (default=None); last-end model reader first in main(); legs_changed switch executed; per-closer F-SEP fixtures and one-replace force-fires for W1-W11.
