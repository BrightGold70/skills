# Design: grok-codex-fallback

## Executive Summary

Grok becomes a third, explicitly armed agent in `hmad-dispatch exec`, with a jq segmenter over
its own `--log` region, a typed and fail-closed `fallback_agent` read in the TDD gate, a
`scan_grok` evidence reader shared by the evidence CLI and the audit-cycle combiner, a closed-world
shape router in `combine()`, a presence-judged `--timeout` sentinel in the assembler, and a
last-`end` model reader. All three log classifiers apply one precedence: agy, then the codex
banner in the log's head, then grok, then codex-text. Every non-grok path keeps its bytes.

## Overview

The design implements spec v1.3 (11 FRs, 58 ACs) under plan v1.3. It keeps the plan's wiring
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

The tree premises were read at `50560eb` (HEAD at v1.0 authoring). `git diff --name-only 1680271
50560eb -- h-mad handoff | wc -l` → 0 files, so plan v1.3's tree premises (read at `1680271`) and
this design's readings describe the same `h-mad/` tree. The v1.1 revision was authored at
`0df3d47`, and `git diff --name-only 50560eb 0df3d47 -- h-mad handoff | wc -l` → 0 files, so every
`50560eb` reading below still describes the tree. The readings new in v1.1 are stamped `0df3d47`.
The v1.2 revision was authored at `0b3f969`. `git diff --name-only 0df3d47 0b3f969 -- h-mad
handoff` → 1 file, `h-mad/invariants.base.md` (the operator's agent-CLI clause, §"Invariant
Compliance"). No script, hook or test changed, so every earlier reading still describes the code.
The readings new in v1.2 are stamped `0b3f969`.

## Supersedes the plan on

Plan v1.3's audit is closed, so the plan is not edited. Two of its statements are superseded by
spec v1.3 and this design, and the Phase-5a impl-plan follows the design on both:

1. **Classifier precedence.** Plan §"Architecture Considerations" says the classifiers apply
   "the same precedence (agy first, then grok, then codex)". Spec v1.3 FR-5 puts the codex
   banner ahead of grok: agy, then the codex banner in the head window, then grok, then
   codex-text. D4, D6 and D7 implement that order, and AC-11.3 tests it on all three surfaces.
   The plan's order would reintroduce the regression AC-11.3 exists to catch: a codex transcript
   that echoes grok-typed lines read as grok.
2. **AC count.** Plan §"Success Criteria" says "All 55 spec ACs across FR-1–FR-11 pass automated
   tests". Spec v1.3 has 58 distinct AC ids (V3). The three added ids are AC-4.10, AC-5.2b and
   AC-11.3, and the Test Plan names all 58. The implementation gate counts against the spec's
   ids, re-derived with V3's command, and never against the plan's 55.

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
   --log ──► hmad-dispatch progress ── _exec_log_format: agy → codex banner (head) → _grok_log_has_events → codex-text
         ──► h_mad_review_evidence.py main: scan() agy → codex banner (head) → scan_grok() → codex-text path
         ──► h_mad_audit_cycle.measure_effort: parsed → codex-text (banner) → grok | grok-truncated → unparseable
                   └─► combine(): closed-world route per shape
         ──► h_mad_resolved_model.py grok --log: last end.modelUsage
 audit-cycle --surfaces agy,grok ──► _cmd_exec grok (per-pass --log) ──► measure_effort / combine
```

Three classifiers read a log's format. `_exec_log_format` is shell and picks a render lens. The
evidence CLI's `main()` and `measure_effort()` are Python and pick a verdict route. They share
three rules, and each rule has one cross-surface test (Test Plan, `test_grok_two_instruments.py`):

- **precedence:** agy, then the codex banner in the head window, then grok, then codex-text
  (spec FR-5). The two Python surfaces call one helper for the banner (D6);
- **grok detection:** a line is a grok event iff it parses as a JSON object whose top-level
  `type` is a string in the seven-type vocabulary, whatever the key order, and whose nesting
  depth is at most 64 (D3.5 "The depth bound", D4, D6);
- **the type vocabulary** itself, one literal per language, asserted equal as sets.

**Class sweep (which readers classify by content).** The needle has to see a classifier that
keys on `scan()` or `agy_events` alone, not only one that names the banner. At `0b3f969`,

```bash
grep -rln 'from h_mad_review_evidence import\|agy_events\|_exec_log_format\|OpenAI Codex' \
  h-mad/scripts h-mad/hooks h-mad/bin | grep -v __pycache__
```

lists exactly 4 source files (unit: files): `hmad-dispatch.sh`, `h_mad_audit_cycle.py`,
`h_mad_review_evidence.py` and `h_mad_archreview_cycle.py`. The first three are the classifiers
above. The rest of the population is:

- `h_mad_archreview_cycle.py`, found by its `from h_mad_review_evidence import scan` and its
  `agy_events` test. It reads logs through `scan()` alone and refuses every non-agy log as
  `unsupported_format`. It stays agy-only (spec Out-of-Scope, "A grok 6a-prime reviewer"), so no
  precedence applies to it. A banner-keyed needle does not find this file (v1.1's needle did not).
- inside `hmad-dispatch.sh`, the `_agent_pv_re()` comment names a codex product line. That
  function identifies an agent in a terminal pane, which is the pane path, outside `exec`.

`h_mad_resolved_model.py` picks its reader from the agent argument, never from content, and the
needle does not list it.
**Residual:** a content classifier that imports none of these names and spells none of these
tokens is outside this sweep. Re-run the command above at 5g.

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
- **Scope of "read error".** `ACTIVE` was already derived from the same file by an earlier
  `jq … | head -1` pipeline. The hook runs `set -euo pipefail`
  (`grep -n '^set ' h-mad/hooks/h-mad-tdd-gate.sh`), so a jq that prints a key and then fails on
  a later entry fails the assignment, and the hook exits there. Executed at `0df3d47` on a
  scratch state `{"orchestrator_state":{"a":{"phase":"step5"},"b":3}}` with that pipeline under
  `set -euo pipefail`: the script never reached the next line, and it exited 5. The first read
  therefore must succeed for the hook to reach this block. The `*)` arm is reached by a jq
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
  already invoke through their `#!/usr/bin/env bash` shebangs, so it is not a new dependency. The
  tool-absent cells run on a symlink farm instead of `/usr/bin` (Test Strategy), and the farm
  carries `env`.

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
  below takes it as its local `pre` and reads the region through one helper,
  `_grok_region <log> <pre>`, whose body is the single region read
  `tail -n "+$(( pre + 1 ))" "$log" 2>/dev/null`. One helper is what keeps row P5's `find` unique:
  the harness requires every anchor to match exactly once, and four inline copies of the same
  `tail` would give P5 four matches. Mutating that one line un-scopes all four readers at once,
  which AC-4.7 observes.
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

All four read only the region, from `pre_lines` to EOF with no tail cap. That is spec NFR
"Performance": region-bounded exactly as `_agy_ndjson_response` is (its region read is
`tail -n "+$(( skip + 1 ))" "$log"`, with no cap). `_agy_last_step` pipes its region through
`tail -n 2000`, and the grok last-tool line deliberately does **not** mirror that cap, because
spec FR-4 counts N over the whole region.

Each helper runs
`_grok_region "$log" "$pre" | jq -nR -r --argjson max "$_GROK_MAX_DEPTH" "$_GROK_JQ_DEFS <program>"`
and **streams** the region: `inputs`, one line at a time, never a slurp (`-s`). All four take
`-r`, because each prints a bare word or a line of text. Without it `_grok_region_state` prints
`"complete"` with its quotes, which is neither `complete` nor `truncated` and so reads `jqfail`
on every run, and the other two lines would carry quotes. Memory is then bounded by what the
program keeps, which is named per helper below. No helper stops before the end of its input
(below, `_grok_region_state`). **Residual (spec NFR):** time is O(region) per parse, and nothing
bounds a very long single dispatch.

**The line filter and the depth bound.** Every jq program in this feature that parses a log line
calls one filter, `_grok_obj`. Those programs are the four readers here, D4's
`_grok_log_has_events` and D5's renderer. The filter is defined once, in one shell variable that
each program is prefixed with:

```bash
_GROK_MAX_DEPTH=64
_GROK_JQ_DEFS='def _grok_over($d): if $d > $max then true
    elif (type == "object" or type == "array") then any(.[]; _grok_over($d + 1))
    else false end;
  def _grok_obj: (fromjson? // empty) | select(type == "object")
    | select(_grok_over(0) | not);'
```

- **Depth.** The depth of a parsed value is the length of the longest path jq's `paths` emits
  from it: 0 for a scalar or an empty container. `_grok_over(0)` is true iff some value sits at
  a path longer than `$max`. A line is a grok event only when its depth is at most 64. The
  Python side applies the same bound to the same definition (D6 step 4), so a line nested beyond
  64 is "not a grok event" on both surfaces. That makes the input domain identical on the depth
  axis.
- **Why depth is computed, not proxied.** jq has no depth builtin. `_grok_over` computes it
  directly, and it stops descending at `$max + 1`, so a line costs at most the nodes in its first
  65 levels. `[paths | length] | max` gives the same number but walks every path of an
  arbitrarily deep line.
- **Why 64, and why the parsers' own ceilings no longer matter.** F0's deepest line has depth 6
  (`jq -nR '[inputs | fromjson? | [paths | length] | max // 0] | max' <F0>` → 6 at `0b3f969`).
  Every parser on this host parses a depth-65 line. That covers jq 1.8.2 (`/opt/homebrew/bin`),
  jq 1.7.1-apple (`/usr/bin`), jq 1.6 (`/opt/anaconda3/bin`), Python 3.11.8 and Python 3.14.7.
  So at the boundary the bound decides, never a parser. Above the bound the ceilings differ: jq
  1.7.1 and 1.6 reject a 1000-deep line; jq 1.8.2 parses 5000 and rejects 10,000; Python 3.11.8
  raises `RecursionError` from 1000; Python 3.14.7 parses 10,000 and raises only at 200,000.
  Every one of those outcomes is "not an event" on both surfaces.
- **Executed at `0b3f969`** on single-line files `{"type":"text","data":"x","n":` + k nested
  arrays + `}`, whose depth is k. The jq side ran `[inputs | _grok_obj] | length` on each of the
  three jq builds. The Python side ran the D6 loop under 3.11.8 and 3.14.7. Unit: events counted
  per file:

  | k | every jq build | Python 3.11.8 | Python 3.14.7 |
  |---|---|---|---|
  | 64 | 1 | 1 | 1 |
  | 65 | 0 | 0 (depth check) | 0 (depth check) |
  | 1000 | 0 | 0 (`RecursionError`) | 0 (depth check) |
  | 5000 | 0 | 0 (`RecursionError`) | 0 (depth check) |
  | 10,000 | 0 | 0 (`RecursionError`) | 0 (depth check) |
  | 200,000 | 0 | 0 (`RecursionError`) | 0 (`RecursionError`) |

  The unbounded v1.1 filter (`fromjson? // empty | select(type == "object")`) counts 1 at k = 65
  on all three jq builds, so the bound, not a parser ceiling, is what zeroes that row.
- **Single-sourced by test.** The bound is written twice, as `_GROK_MAX_DEPTH=64` and as Python's
  `GROK_MAX_DEPTH = 64`. A cross-surface test parses the shell literal and asserts it equals the
  Python constant. The boundary tests (Test Plan, "Depth boundary") kill a change to either
  spelling (rows L3, E6) and the removal of either side's depth filter (rows L4, E8).

Each helper also follows `_agy_last_step`'s hardening:

- `case "$pre" in ''|*[!0-9]*) pre=0 ;; esac`;
- `_grok_obj`, whose `select(type == "object")` comes after `fromjson? // empty`, so a stray
  scalar line cannot abort jq with "Cannot index";
- `2>/dev/null || true` on the three helpers whose empty output is a safe degradation, so a jq
  failure under `set -e` does not abandon `_cmd_exec` before recovery. `_grok_region_state` is the
  exception: it reports the failure as a state (below).

**`_grok_region <log> <pre>`** prints the region and nothing else. It is the only place the
region offset is spelled.

**`_grok_final_message <log> <pre>`** is the FR-4 segmenter. It prints the last non-empty segment
and nothing else:

```jq
reduce (inputs | _grok_obj) as $e
  ({last: "", cur: ""};
   if $e.type == "text" then .cur += (if ($e.data | type) == "string" then $e.data else "" end)
   elif ($e.type == "tool_call" or $e.type == "tool_call_update"
         or $e.type == "usage" or $e.type == "end")
     then (if (.cur | length) > 0 then .last = .cur else . end) | .cur = ""
   else . end)
| if (.cur | length) > 0 then .cur elif (.last | length) > 0 then .last else empty end
```

- It is run as `jq -nR -r`, like every reader here. The state is one string value, so a
  multi-line segment stays one value on output. That is the `_agy_ndjson_response` lesson about `tail -1` truncating a
  multi-line verdict. Memory holds the current and the last non-empty segment, never the region.
- Every other `type`, including `thought`, `available_commands`, unobserved types and a missing
  `type`, is neither appended nor a closer.
- Only `text` data is ever appended. `thought` data, `rawInput`/`rawOutput` and non-JSON lines
  never are (AC-4.3).
- **Executed on F0 at `0df3d47`:** the program above prints `STATUS: DONE` (spec A1). A region
  holding one `text` event whose `data` carries an embedded newline, followed by `end`, prints
  both lines as one value. **Re-executed at `0b3f969`** with the `_GROK_JQ_DEFS` prefix and
  `-r`: F0 still prints `STATUS: DONE`. A region of `text` `a`, then a depth-65 `text` `b`, then
  `end`, prints `a`, because the depth-65 line is not an event.
- The caller's `$(…)` strips trailing newlines, and the success path re-adds exactly one with
  `printf '%s\n'` (AC-4.1).

**`_grok_region_state <log> <pre>`** prints exactly one of four words:

- `complete`: the region holds at least one event whose `type == "end"`;
- `truncated`: it holds none. An empty region counts as `truncated`;
- `nojq`: `command -v jq` fails, so nothing was read;
- `jqfail`: `jq` is on PATH, but the pipeline exited non-zero or printed neither `complete` nor
  `truncated`.

The program is
`reduce (inputs | _grok_obj | select(.type == "end")) as $_ ("truncated"; "complete")`, run as
`jq -nR -r`. It reads the whole region and never exits early. Its rc is captured
(`st="$(…)" || rc=$?`) rather than masked, so a failure is reported and never read as
`truncated`.

- **Why no early exit.** v1.1's program was `any(…; .type == "end")`, which stops at the first
  `end`. Its input is a pipe from `_grok_region`'s `tail`, and the rc is captured under
  `set -o pipefail`. When jq stops while `tail` still has more than a pipe buffer to write,
  `tail` dies of SIGPIPE and the pipeline exits 141. That reads as `jqfail` on a completed run.
  **Executed at `0b3f969`** under `/bin/bash` with `set -euo pipefail`, on a region of one `end`
  line followed by 20,000 `thought` lines. The v1.1 program gave `rc=141` in 3 of 3 runs. The
  reduce form gave `st=complete rc=0` in 3 of 3 runs. On F0 it gives `complete`, on an empty
  region and on F0's first 50 lines `truncated`, and on a depth-65 `end` line alone `truncated`
  (unit: printed word per input).
- **The class and its members.** The class is every new reader whose input is a pipe and whose
  pipeline rc is captured, with a consumer that can stop early. The other members are checked
  and none of them stops early: `_grok_final_message`, `_grok_stop_reason` and `_grok_last_tool`
  reduce all of their input; `_grok_log_has_events` (D4) stops at its first match but reads the
  file itself, not a pipe; and D5 slurps. **Residual:** a reader added later with `first`, `any`,
  `limit` or `halt` over a captured-rc pipe re-enters the class.

**The completeness rule and its residual.** "Complete" means at least one parseable `end` object
in the region, the same rule as `scan_grok()["complete"]` (D6), and one cross-surface test pins
the two (Test Plan).

- **Residual (heartbeat, unmeasured):** `_exec_run` appends `#hmad-beat` lines to the same log
  through a separate O_APPEND fd. Its own comment says a beat "can in principle land mid-line and
  corrupt one JSON event". A grok region has one `end` event, so a beat that splits that one line
  turns a completed run into `truncated`. The run then takes the EMPTY path, prints `TRUNCATED`,
  and returns rc 3 with `verdict recovered from log` when a structured segment survives. On the
  evidence side the same log reads `grok-truncated` → `low_evidence_unmeasurable`. The failure
  direction is always a false cannot-judge, never a false success. Whether grok 1.0.41 writes one
  event in more than one `write()` was **not measured**, so the likelihood is unestablished.
  F-BEAT covers whole-line beats only.

**`_grok_stop_reason <log> <pre>`** prints the last `end` event's
`(.stopReason // "-") | tostring`, reducing over `inputs | _grok_obj | select(.type == "end")`.
Executed at `0b3f969` on F0 with the prefix and `-r`: `end_turn`, unquoted.

**`_grok_last_tool <log> <pre>`** prints `N tool calls completed; last tool: <toolName>
<status>`, or nothing when the region holds no `tool_call` event (the AC-4.9 omission clause).

```jq
reduce (inputs | _grok_obj
        | select(.type == "tool_call" or .type == "tool_call_update")) as $e
  ({names: {}, done: {}, seen: false, last: null};
   (if $e.type == "tool_call" then .seen = true else . end)
   | (if $e.type == "tool_call" and ($e.toolCallId | type) == "string"
      then .names[$e.toolCallId] = ($e.toolName // "?") else . end)
   | (if $e.type == "tool_call_update" and $e.status == "completed"
         and ($e.toolCallId | type) == "string"
      then .done[$e.toolCallId] = true else . end)
   | (if $e.status != null then .last = $e else . end))
| if .seen | not then empty
  else "\(.done | length) tool calls completed; last tool: "
       + (if .last == null then "none"
          else (((.last.toolCallId | strings) as $i | .names[$i]) // "?")
               + " " + (.last.status | tostring) end)
  end
```

- **N** is spec FR-4's rule: the number of distinct string `toolCallId`s that have a
  `tool_call_update` whose `status == "completed"`, counted over the **whole region**. It is the
  same rule as `scan_grok()["ok"]` (D6). A shell and a Python implementation cannot share code,
  so "one rule" is enforced by a cross-surface equality test over five fixtures (Test Plan), not
  by construction. Memory holds one map entry per distinct id.
- The **last tool** is the last `tool_call`/`tool_call_update` event with a non-null `status`.
  Its name is joined from the `tool_call` carrying the same `toolCallId`, and is `?` when the join
  fails. Per P2, `toolName` appears only on `tool_call`. When no tool event has a non-null status,
  the name slot reads `none`, as agy's #77b line does.
- **Executed at `0df3d47`** on each region (unit: the printed line):
  - F0: `2 tool calls completed; last tool: search_replace completed`;
  - F-NOTOOLS: `0 tool calls completed; last tool: search_replace pending`. The region holds 2
    distinct ids and none completed, so a count-every-id mutant prints `2` here;
  - AC-4.10's fixture (F-NOTOOLS minus every `text` event, 89 lines): the same line as
    F-NOTOOLS, which is the spec's expected stderr.
  - Re-executed on F0 at `0b3f969` with the prefix: under `-r` it prints the F0 line above,
    unquoted. Without `-r` the same line comes back wrapped in `"`.

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

1. One line per `grok_state`, each asserted with its exact wording by the test that owns its
   route (Test Plan):
   - `truncated`: `hmad-dispatch: exec: TRUNCATED — no end event in this dispatch's grok stream`;
   - `nojq`: `hmad-dispatch: exec: grok stream not parsed — jq not on PATH`;
   - `jqfail`: `hmad-dispatch: exec: grok stream not parsed — jq failed`.

   Neither `not parsed` line is claimed as a truncation, because nothing was judged. Each names
   its own cause, so a crashing `jq` is never reported as a missing one.
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

**The vocabulary literal.** One shell variable holds the seven types, and both shell detectors
below read it:

```bash
_GROK_TYPES_RE='thought|text|available_commands|tool_call|tool_call_update|usage|end'
```

**`_codex_banner_in_head <logfile>`** returns 0 iff a line of the log's first 4096 bytes begins
`OpenAI Codex v`:

```bash
local h; h="$(head -c 4096 "$1" 2>/dev/null)" || h=""
case $'\n'"$h" in *$'\n''OpenAI Codex v'*) return 0 ;; esac; return 1
```

- There is no pipeline, so `pipefail` and a `grep -q` early exit cannot flip the answer.
- **Executed at `0df3d47` under `/bin/bash` 3.2.57** beside the Python reading
  `re.compile(r"^OpenAI Codex v", re.M).search(text[:4096])` on each input (unit: yes/no per
  input). Both say yes on a banner line followed by F0, and on a banner ending exactly at byte
  4096. Both say no on F0 alone, on a banner one byte past that window, and on a line that quotes
  the banner mid-line.
- **Residual (window units):** Python's window is 4096 **characters** of decoded text and this
  one is 4096 **bytes**. A banner inside the byte window is always inside the character window,
  so the two differ in one direction only: when the text before the banner holds multi-byte
  characters, Python can say yes where the shell says no. Measured: 2041 `é` then a banner line
  (4101 bytes): Python yes, shell no. The consequence is confined to the render lens: `progress`
  may pick `grok-ndjson` for a log both Python surfaces call `codex-text`. The two verdict
  surfaces share one helper (D6), so they never disagree with each other.

**`_grok_log_has_events <logfile>`** returns 0 iff some line is a grok event under the D6 rule
(a JSON object of depth at most 64 whose top-level `type` is a string in the vocabulary). It has
a primary and a fallback route:

```bash
jq -nR -e --argjson max "$_GROK_MAX_DEPTH" --arg re "$_GROK_TYPES_RE" \
  "$_GROK_JQ_DEFS"' ($re | split("|")) as $t
  | first(inputs | _grok_obj
          | select((.type | type) == "string") | .type as $x
          | select(any($t[]; . == $x))) | true' "$log" >/dev/null 2>&1
```

Executed at `0b3f969` with the D3.5 prefix (unit: rc per file): F0 → 0; the depth-64 line → 0;
the depth-65 line → 4; the 200,000-deep line → 4; an empty file → 4.

- **rc 0 → grok. rc 4 → not grok.** Under `-e`, jq exits 4 when no output was produced. Any other
  rc, including `command -v jq` failing or a jq that crashes, takes the fallback. `first(…)` stops
  at the first match, as the grep it replaces did.
- **Key order is irrelevant**, because the object is parsed (spec FR-5, AC-5.2b). The membership
  test is string equality against the split literal, so there is no regex anchoring to get wrong,
  and `tool_call` cannot match `tool_call_update`, nor the reverse.
- **Fallback (jq absent or failed):**
  `grep -aqE "^[[:space:]]*\{.*\"type\"[[:space:]]*:[[:space:]]*\"(${_GROK_TYPES_RE})\"" "$log"`.
  It is key-order independent, and both sides of the alternation are delimited by `"`. It exists
  so that a jq-less `progress` names the stream (D5's `jq not on PATH` line) instead of rendering
  it with the codex lens.

**Agreement with `scan_grok` (spec AC-5.2b), and its exact residual.** Executed at `0df3d47` with
jq 1.8.2 and Python 3.11.8: the jq route and the D6 rule were each run on 27 single-file inputs
(unit: files). The inputs covered key order, `type` values of `[]`, `{}`, `1`, a nested
`type`-bearing object, a truncated object, duplicate `type` members in both orders, two objects on
one line, surrounding whitespace, `NaN`, `Infinity`, `1e400`, a raw tab in a string, invalid
UTF-8, F0 and F-TRUNC. 21 agreed. The 6 that disagreed fall into one class: **a line that one
parser accepts as a JSON object and the other rejects.** That matrix was run on v1.1's
unbounded filter, and its members were:

- a lowercase `nan` token (jq accepts it; `json.loads` does not);
- a leading UTF-8 BOM (jq accepts it; `json.loads` does not);
- a lone surrogate escape `\ud800` (jq rejects it; `json.loads` accepts it), 2 of the 6 inputs;
- nesting 5000 deep (jq 1.8.2 accepts it; Python 3.11 raises `RecursionError`);
- a bare CR between two objects on one line. Python's `read_text` turns it into a line break, and
  jq sees one line with extra data.

**The depth member is closed by the identical-domain rule** (D3.5 "The line filter and the depth
bound"). Nesting is the one axis on which the parsers' ceilings differ by build and by
interpreter, so no single parser acceptance can be shared across them. The bound puts both
surfaces below every ceiling measured on this host, and above it both answer "not an event".
Re-executed at `0b3f969` on a 5000-deep line: jq counts 0, and Python 3.11.8 and 3.14.7 count 0.
The depth member is therefore not a disagreement in v1.2. The 27-input matrix was not re-run as a
whole; its other five inputs do not involve depth, so the bound does not change them.

**Residual (parser grammar, open).** The remaining class is **a line within the depth bound that
one parser's grammar accepts as a JSON object and the other's rejects.** The members measured
are the other four listed above (lowercase `nan`, BOM, lone surrogate, bare CR). Its membership
is not enumerated, because any grammar difference between jq and `json.loads` is a member. On
those lines the two surfaces can still disagree, so spec FR-5's "the same answer on every line"
holds over the depth axis and does not hold over this class. That is a spec-level residual:
FR-5's wording is owed a scoping to this domain, and the design does not rewrite the spec. F0
carries no member: jq and the D6 line
discipline each parse all 110 of F0's lines as objects (unit: lines; `jq -nR '[inputs |
(fromjson? // empty) | select(type=="object")] | length'` → 110, and the D6 loop → 110). That zero
rests on grok 1.0.41 emitting plain compact JSON, which is incidental: a grok build that emitted
a member would disagree only on its own lines.

- **Residual (fallback route only), its input domain stated exactly.** The grep does not parse.
  Its domain is the regex itself: with jq absent or failing, a log is grok iff some line matches
  `^[[:space:]]*\{.*"type"[[:space:]]*:[[:space:]]*"(<the seven types>)"`. It disagrees with
  `scan_grok` on exactly the lines where that match and the parsed rule differ. The parsed rule is
  a JSON object of depth at most 64 whose top-level `type` is a string in the vocabulary. The
  classes measured in that difference are five: a line that is not valid JSON; a qualifying
  `type` member present only in a nested value; duplicate `type` members; a key or value spelled
  with a JSON escape; and a line deeper than the bound. The last was executed at `0b3f969`: the
  depth-65 line and the 200,000-deep line both match the grep, and the parsed rule counts neither.
  The fallback picks a render lens only, and D5 prints `cannot render` on it anyway.
- **Residual (spec FR-5):** a grok stream carrying only unobserved `type` values classifies as
  `codex-text`.

`_exec_log_format` then decides in this order:

1. `missing`;
2. `empty`;
3. the existing agy grep, which prints `agy-ndjson`, unchanged;
4. `elif _codex_banner_in_head "$log"`, which prints `codex-text`;
5. `elif _grok_log_has_events "$log"`, which prints `grok-ndjson`;
6. `else`, which prints `codex-text`.

The header comment's token list gains `grok-ndjson`.

- **Why every existing log keeps its token.** Step 4 prints what step 6 would print, so it can
  change a log's token only when the log also carries grok events. A log with no grok event and
  no agy event reads `codex-text` exactly as today.
- **AC-11.3's shell arm.** A codex banner line followed by all of F0 reads `codex-text`, because
  step 4 comes first.

### D5 — `_render_progress` grok branch (FR-5)

The existing `if [ "$fmt" = agy-ndjson ] && command -v jq …; then … else <codex lens> fi` gains an
`elif [ "$fmt" = grok-ndjson ]; then` arm between the two. Without it, a grok log would fall into
the codex lens and print `(prompt still echoing — no agent output yet)`, because no grok stream
echoes the boundary. Inside the arm:

- **Without `jq`** (`command -v jq` fails), it prints one line,
  `  (grok stream — jq not on PATH, cannot render)`.
- **With `jq`,** it runs `tail -n 400 "$log" | jq -Rs -r <program> | tail -n "$n"`, capturing the
  rendered text and the pipeline's rc. When the rc is non-zero, it prints one line,
  `  (grok stream — jq failed, cannot render)`, in place of any partial output. The two
  cannot-render lines name different causes, and each is asserted with its exact wording by the
  test that owns its route (Test Plan).
- **One line filter.** The program is prefixed with `$_GROK_JQ_DEFS` and given
  `--argjson max "$_GROK_MAX_DEPTH"` (D3.5). It splits the slurped window on `"\n"` and passes
  each line through `_grok_obj`. A line deeper than the bound therefore renders nothing, exactly
  as a non-JSON line does, and it neither ends a run nor starts one.
- **Bound.** The window is the last 400 lines of the whole log, exactly as the agy lens reads it.
  `progress` is a polling lens and takes no `pre_lines` (spec NFR "Performance"). The slurp here
  is bounded by that window, unlike the D3.5 readers.
- The program first builds a `toolCallId → toolName` map from the `tool_call` events in the
  window, then reduces the events with a run-state:

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

- **What ends a run.** A run ends only at an event that renders a line of its own, or at a run
  event of the other kind, or at the end of the window. An event that renders nothing
  (`available_commands`, a `tool_call_update` with `status` null) and a non-JSON line are
  transparent: they neither end a run nor start one. That yields at most one run line per
  maximal run in the spec's sense, which is what AC-5.2 permits, and never more.
- **No delta text reaches any line.** The run lines carry only a count.
- **The field paths were read from F0 at `50560eb`:** `usage` events carry
  `.usage.{input_tokens,output_tokens,reasoning_tokens,…}`; `end` carries `stopReason`,
  `num_turns` and `modelUsage`; `tool_call` carries `toolName`, `status`, `rawInput` and
  `toolCallId`; `tool_call_update` carries `status`, `toolCallId` and `rawOutput`, with no
  `toolName`. Command:

  ```bash
  jq -c 'select(.type=="<t>")|keys' <F0> | sort | uniq -c
  ```

  run once for each of the seven types.
- **AC-5.2 as spec v1.3 states it.** The test asserts four equalities: 2 `pending` tool lines,
  2 `completed` tool lines, 1 `END stopReason=end_turn turns=3` line and 3 `turn usage` lines.
  "Exactly" binds these listed classes only, and run lines may appear beside them. It then asserts
  the spec's two absences:
  - no output line, stripped of surrounding whitespace, equals any single `thought` or `text`
    event's `data` stripped the same way, over every event whose stripped `data` is non-empty;
  - neither F0 text segment (FR-4) occurs anywhere in the output.

  It asserts no total line count. The spec's residual is carried unchanged: a run line that echoed
  a fragment of a `thought` run, shorter than a whole segment and not equal to one delta, would
  not be caught. The design emits no such line, because run lines carry only a count.
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

**Parsing** is the D4 detection rule, written so that each step matches jq's `-R` + `_grok_obj`
(`fromjson?`, `select(type == "object")`, then the depth bound):

1. `for line in log_text.split("\n")`. It is **not** `splitlines()`, which also splits on
   `\r`, `\x0b`, `\x0c`, `\x1c`–`\x1e`, `\x85`, U+2028 and U+2029, where jq `-R` splits on `\n`
   only.
2. `json.loads(line)` inside `try`, catching **`(ValueError, RecursionError)`**. `json.loads`
   already ignores JSON whitespace around the value, so no `strip()` or `startswith("{")` step is
   taken. `RecursionError` is caught because a deeply nested line raises it, and the interpreter
   decides where. Measured at `0b3f969`: Python 3.11.8 raises from 1000 deep, and Python 3.14.7
   only at 200,000 (D3.5's table). The line is skipped, never an abort. Every line that raises it
   on either interpreter is deeper than the bound, so the catch changes no answer that step 4
   would give; it only keeps the reader alive. **The class** is every exception `json.loads` can
   raise on one line, and the rule is that each is caught and the line skipped. **Residual:**
   exception types not measured here, such as `MemoryError` on a huge line.
3. Skip anything that is not a `dict`.
4. **Depth bound:** skip the event when `_json_deeper_than(event, GROK_MAX_DEPTH)`, with
   `GROK_MAX_DEPTH = 64`. The helper is iterative, never recursive: a stack of `(value, depth)`
   pairs, starting at `(event, 0)`, which returns `True` as soon as a popped depth exceeds the
   bound and otherwise pushes each child of a `dict` (its values) or `list` at `depth + 1`. That
   is D3.5's `_grok_over`, the same definition on the same path lengths.
5. **Type-check before membership:** `t = event.get("type")`, and the event counts only when
   `isinstance(t, str) and t in _GROK_TYPES`. The order matters. `[] in frozenset(...)` raises
   `TypeError: cannot use 'list' as a set element (unhashable type: 'list')` (executed at
   `0df3d47`), so a bare `event.get("type") in _GROK_TYPES` would abort evidence reading and audit
   scoring on one malformed line. The class is every unhashable JSON value (`list`, `dict`), and
   the `isinstance` check closes it. A hashable non-string (`1`, `true`, `null`) could not raise,
   but it would also never be a member, so the check changes no answer for it.

When no line qualifies, the function returns `None`.

**Why not `scan()`'s discipline.** `scan()` uses `splitlines()`, `strip()` and a leading-`{`
test. `scan()` is untouched (AC-6.5). `scan_grok` departs from it only where the departure is
what makes the shell and Python detectors agree (AC-5.2b, D4's measured residual).

**Counting:**

- `tools` is the size of the set of `str` `toolCallId`s seen on `tool_call` or `tool_call_update`.
- `ok` is the size of the set of `str` `toolCallId`s seen on a `tool_call_update` whose `status ==
  "completed"`, compared as an exact string on the **parsed** field. Substring matching is
  structurally impossible, which is AC-6.4.
  It is the same rule as `_grok_last_tool`'s N (D3.5, spec FR-4), and the cross-surface test pins
  the two equal.
- `unresolved` is `tools − ok`.
- `thinking` sums `event["usage"]["reasoning_tokens"]` over `type == "usage"` events, keeping only
  `int`/`float` values that are not `bool`. `end.usage` is excluded. The test is spelled
  `type(value) in (int, float)`, which excludes `bool` because `type(True)` is `bool`. It is never
  spelled as `scan()`'s anchored `isinstance(value, (int, float)) and not isinstance(value, bool)`
  (§"Existing mutation anchors", rule 2).
- `complete` is true when any `end` event is present.
- `stop_reason` is the last `end` event's `stopReason` when it is a `str`, else `None`.

**`scan()` is untouched** (AC-6.5).

**The banner step.** Spec FR-5 gives all three classifiers one precedence. The CLI's banner step
is a new helper in this file:

```python
CODEX_BANNER_HEAD = 4096

def codex_banner_in_head(text: str) -> bool:
    return _CODEX_HEADER_RE.search(text[:CODEX_BANNER_HEAD]) is not None
```

- `_CODEX_HEADER_RE` is the existing `re.compile(r"^OpenAI Codex v", re.M)` in this file.
- **Why `measure_effort()` does not call this helper.** Its banner line,
  `    elif _CODEX_BANNER.search(text[:4096]):`, is the `find` of two committed mutation rows in
  `h-mad/tests/mutation-specs/codex_log_not_measured.json` (one anchors the whole line, one the
  call `_CODEX_BANNER.search(text[:4096])`), and `test_h_mad_mutation_harness.py::
  test_committed_mutation_harness_anchor_sweep_is_ok` requires every committed anchor to match
  exactly once. That line therefore stays byte-identical (D7, §"Existing mutation anchors").
- **What is single-sourced, and what is pinned instead.** The pattern is single-sourced:
  `h_mad_audit_cycle.py`'s definition `_CODEX_BANNER = re.compile(r"^OpenAI Codex v",
  re.MULTILINE)` is replaced by an import of `_CODEX_HEADER_RE` under the name `_CODEX_BANNER`.
  The definition line is no anchor (`grep -rnw '_CODEX_BANNER' h-mad/scripts h-mad/tests` at
  `0df3d47` → the definition, the one use, and the two anchor rows). The window `4096` stays
  written twice, once in the anchored line and once as `CODEX_BANNER_HEAD`. The cross-surface
  window-edge test pins the two equal (Test Plan).
- `scan_codex_text()` keeps searching the **whole** text for its header. It measures a codex
  transcript and is unchanged. The head window decides only precedence.

**`main()`.** Inside the existing `if counts["agy_events"] == 0:` branch, **before**
`codex = scan_codex_text(text)`:

```python
grok = None if codex_banner_in_head(text) else scan_grok(text)
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
- The insertion goes after the branch's `# #27` comment block, so the branch's first two lines
  stay byte-identical. They are the anchor of `review_evidence_format.json`'s first row.
- A banner in the head window short-circuits `scan_grok`, so a codex transcript whose tool output
  echoes grok-typed lines at column 0 keeps today's `CODEXEVIDENCE:` + `UNREADABLE
  reason=unsupported_format` output and exit 2 (spec FR-6, AC-11.3).
- The codex and unsupported path runs whenever `grok` is `None`, so it stays byte-identical
  (AC-6.6).
- **Residual (spec FR-5):** a log whose codex header lies only beyond the head window and which
  also carries a grok event reads as grok. `scan_codex_text()` would have found that header, but
  the precedence consults the window only. A log with no grok event still takes today's path.
- **Residual (spec FR-5):** a caller-supplied `--log` holding a prior codex dispatch followed by a
  grok dispatch reads as codex-text on all three surfaces. It is skipped, never falsely gated, and
  FR-4's region parse does not consult this classifier.
- The `UNREADABLE` exit 2 follows the file's existing cannot-judge convention (`no_log`,
  `empty_log`, `unsupported_format`). Base §"Audit-gate signal discipline" permits a non-zero exit
  for unreadable input.
- The `ArgumentParser` `log` help text gains "or grok streaming-json".

### D7 — Audit-cycle shapes and closed-world routing (FR-7)

**Import.** `from h_mad_review_evidence import scan, scan_grok` and
`from h_mad_review_evidence import _CODEX_HEADER_RE as _CODEX_BANNER`, the latter replacing the
module's own `_CODEX_BANNER = re.compile(…)` definition (D6, "The banner step").

**`measure_effort()`.** After `counts = scan(text)`, the classification follows spec FR-7's order:
agy, then the banner, then grok. The existing `if`/`elif` lines are kept byte-identical, and only
the `else` body changes:

```python
if counts.get("agy_events", 0) > 0:
    counts["shape"] = "parsed"                                  # unchanged
elif _CODEX_BANNER.search(text[:4096]):                         # unchanged, now ahead of grok
    counts["shape"] = "codex-text"
else:
    grok = scan_grok(text)
    if grok is not None and grok["complete"]:
        return {"readable": True, "shape": "grok", "agy_events": 0,
                "tools": grok["tools"], "ok": grok["ok"], "unresolved": grok["unresolved"],
                "thinking": grok["thinking"], "stop_reason": grok["stop_reason"]}
    if grok is not None:
        return {"readable": True, "shape": "grok-truncated", "agy_events": 0}   # no counts
    counts["shape"] = "unparseable"                             # unchanged
return counts
```

- **Three committed anchors survive byte-identical:** the `if … > 0:` line with its `parsed`
  line, the `elif` line, and the call inside it (rows of `codex_log_not_measured.json`). The
  explanatory comments between them are unchanged too.
- **AC-11.3's Python arm.** A banner line followed by all of F0 takes the `elif` and reads
  `codex-text`, and `scan_grok` is never called on it.

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
- **What the default can reach.** After the change the only reachable shapes are the seven named
  in the table: `codex-text`, `missing`, `unparseable`, `empty`, `grok-truncated`, `parsed` and
  `grok`. Today `measure_effort()` returns five of them (`missing`, `empty`, `parsed`,
  `codex-text`, `unparseable`; `grep -n '"shape"\] = \|"shape": ' h-mad/scripts/h_mad_audit_cycle.py`
  at `0df3d47` → 5 matching lines, 5 distinct values), and this design adds two. The hand-built
  `shape is None` fallback maps to `parsed` or `missing` before the table. The default is
  therefore reachable only by a future shape nobody routed, and it is never a count.
- **Measured.** Shape literals asserted in the two audit-cycle test files at `50560eb`:

  ```bash
  grep -on "shape[\"']\?\] *== *[\"'][a-z-]*[\"']\|[\"']shape[\"']: *[\"'][a-z-]*[\"']" \
    h-mad/tests/test_h_mad_audit_cycle.py h-mad/tests/test_hmad_dispatch_audit_cycle.py
  ```

  This finds `codex-text` 2, `empty` 1, `missing` 1, `parsed` 3 (2 asserted plus 1 hand-built
  effort dict), `unparseable` 3, and `test_hmad_dispatch_audit_cycle.py` none (unit: matching
  occurrences). No existing test feeds a shape outside those five, so the default changes no
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
- `command_block(..., agent: str = "codex")` keeps its first list element,
  `        f"hmad-dispatch exec codex {q(str(prompt))}{over} \\",`, **byte-identical**. That
  line is the `find` of two committed rows in `h-mad/tests/mutation-specs/assemble_tdd.json`
  (`hardcode-a-model-into-the-block` and `drop-the-model-and-effort-overrides`), and the committed
  anchor sweep requires it to match exactly once. The function's `return "\n".join([` becomes
  `block = "\n".join([`, followed by:

  ```python
  prefix = "hmad-dispatch exec codex "
  if agent != "codex":
      if not block.startswith(prefix):          # never `assert`: `python -O` strips it
          raise RuntimeError("command block no longer starts with the codex line")
      block = f"hmad-dispatch exec {agent} " + block[len(prefix):]
  return block
  ```

  The two existing rows then mutate the grok block too, because it is derived from the same
  line. `main()` passes `agent=args.agent, timeout=timeout`.
- **Rejected alternative.** Rewriting that line as `f"hmad-dispatch exec {agent} …"` was v1.0's
  design. It would leave both committed rows with a `find` that matches nothing, and
  `test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok` would fail
  on a pre-existing test, against FR-11.

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
- `grok_exec.json`, for rows P*, L* and the W1–W5 and W8 force-fires;
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
| P5 (W3b) | `_grok_region` | its one region read `tail -n "+$(( pre + 1 ))"` → `tail -n +1` | AC-4.7 |
| P6 | `_grok_region_state` | always print `complete` | AC-4.5: F-TRUNC's non-empty final segment then takes the success row, so rc is 0 and no `TRUNCATED` line is printed |
| P7 (W4) | `_grok_last_tool` | drop the "no `tool_call` → empty" guard | AC-4.9, with AC-4.6 as its positive pair |
| P8 | `_grok_last_tool` | drop `and $e.status == "completed"` from the `done` condition, so every updated id counts | AC-4.10 (stderr `0 tool calls completed` becomes `2`) |
| P9 | `_grok_region_state` | report a jq failure as `truncated` instead of `jqfail` | the jq-fails exec cell (stderr must carry `jq failed` and no `TRUNCATED`) |
| L1 | `_exec_log_format` | `elif _codex_banner_in_head "$log"` → `elif false` | AC-11.3 `progress` arm (the mutant prints `grok-ndjson`) |
| L2 | `_grok_log_has_events` fallback | `\{.*\"type\"` → `\{[[:space:]]*\"type\"` (first-key only; the `find` carries the backslash before each quote, because the fallback is a double-quoted bash string) | AC-5.2b fallback cell on the jq-absent farm (`{"meta":1,"type":"text",…}` must still read `grok-ndjson`) |
| L3 | `_GROK_MAX_DEPTH` | `_GROK_MAX_DEPTH=64` → `_GROK_MAX_DEPTH=65` | depth-boundary test, `progress` arm (the depth-65 log must read `codex-text`) |
| L4 | `_GROK_JQ_DEFS` | `\| select(_grok_over(0) \| not)` → the empty string (the depth filter dropped) | depth-boundary test, `progress` and `_grok_region_state` arms (F-DEEP65 must read `truncated`) |
| L5 | `_codex_banner_in_head` | `head -c 4096` → `head -c 8192` | format-agreement test on the window-edge log (the mutant's `progress` reads `codex-text`, and `measure_effort` reads `grok`) |
| E1 | `scan_grok` | `ok` from a substring test (`"completed" in line`) | AC-6.4 |
| E2 | CLI | truncated branch prints the counted line | AC-6.3 (asserts no `tools=`) |
| E3 | CLI | `grok = None if codex_banner_in_head(text) else scan_grok(text)` → `grok = scan_grok(text)` | AC-11.3 CLI arm (the mutant prints `format=grok`) |
| E4 | `scan_grok` | `isinstance(t, str) and t in _GROK_TYPES` → `t in _GROK_TYPES` | malformed-type test: a `{"type":[]}` line raises `TypeError` in the mutant |
| E5 | `codex_banner_in_head` | `CODEX_BANNER_HEAD = 4096` → `= 8192` | window-edge equality test on the window-edge log, whose banner starts at character and byte 4096 (the mutant CLI prints the codex output, and `measure_effort` reads `grok`) |
| E6 | `scan_grok` | `GROK_MAX_DEPTH = 64` → `GROK_MAX_DEPTH = 65` | depth-boundary test, `scan_grok` arm (the depth-65 log must give `None`) |
| E7 | `scan_grok` | `except (ValueError, RecursionError):` → `except ValueError:` | malformed-`type` test: its 200,000-deep line raises `RecursionError` under both Python 3.11.8 and 3.14.7 (D3.5's table), so the mutant aborts |
| E8 | `scan_grok` | the depth-skip `if _json_deeper_than(event, GROK_MAX_DEPTH):` → `if False:` | depth-boundary test, `scan_grok` arm (under 3.11.8 a depth-65 line parses, so only the skip removes it) |
| A1 | `_effort_items` | drop the `grok-truncated` rendering | shape-enumeration test (render row must say "not measured") |
| A2 (W7b) | `combine` | delete the `grok-truncated` route | AC-7.4 (the mutant yields `shape_unrouted`) |
| A3 | `measure_effort` | `elif _CODEX_BANNER.search(text[:4096]):` → `elif _CODEX_BANNER.search(text[:4096]) and scan_grok(text) is None:` | AC-11.3 `measure_effort` arm (the mutant reads `grok`) |
| T1 | assembler | `args.timeout is not None` → `args.timeout not in (None, 900)` (value-judged) | AC-8.2 `--agent grok --timeout 900` |
| R1 | resolver | accept the first `modelUsage` key when there are several | AC-9.2 F-TWOMODEL |
| R2 | resolver | first `end` instead of last | AC-9.3 |

**The closer rows are per-branch, and they were executed.** The closer set is an alternation, and
a healthy sibling covers a sick one. On F0 the two text segments are separated by `usage`,
`tool_call` **and** `tool_call_update`. F0's type-run sequence
(`jq -r .type <F0> | uniq -c`) reads `… text×18 available_commands×1 usage×1 tool_call×1
tool_call_update×2 … text×3 available_commands×1 usage×1 end×1`. So dropping any one closer leaves
F0's result unchanged.

Executed at `0df3d47`, with the streaming program in D3.5 and each one-closer-removed mutant
(v1.0 ran the same check on the slurping program at `50560eb`, with the same outcome):

- on F0 every one-closer mutant prints `STATUS: DONE`, identical to healthy, so P1–P3 each
  **survive on F0**;
- each design fixture keeps exactly one closer type between the segments;
- healthy prints `STATUS: DONE` on all three fixtures. On its own fixture, each matching mutant
  prints one merged segment ending `` txt` with the word "probe".STATUS: DONE ``, whose line does
  not start with `STATUS:`. On the other two fixtures, each mutant prints `STATUS: DONE`, so each
  row is killed by its own fixture only.

P4 was executed the same way on F-DECOY built as spec v1.3 places it (the final segment split
into `All ` and `done.` with the `thought` decoy between them, then the `tool_call` decoy and the
bare line): healthy prints `All done.`, and the append-`thought` mutant's output ends
`All STATUS: DONEdone.`.

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
| W1 | AC-3.1 | S4 `if [ "$agent" = grok ]; then` → `if true; then` | row `test`: `test_hmad_dispatch_exec.py::test_codex_exec_runs_headless_with_the_right_flags`; informational: `::test_agy_exec_runs_print_headless_prompt_as_last_arg`. The child is `env … grok …`, there is no `grok` on the test PATH, `env` exits 127, and the capture is never written |
| W2 | AC-3.3 | codex arm's `"$wait_secs" codex "${args[@]}"` → `"$wait_secs" env "${child_env[@]}" codex "${args[@]}"` | AC-3.4 (the codex stub loses the caller's `CLAUDE*`) |
| W3 | AC-4.1 | (a) agy arm's `resp="$(_agy_ndjson_response` → `resp="$(_grok_final_message`; (b) row P5 | (a) `test_hmad_dispatch_exec.py::test_agy_exec_stdout_is_the_response`, via `returncode == 0`: an agy log has no `text` event, so the result is rc 3. (b) AC-4.7 |
| W4 | AC-4.6 | row P7 | AC-4.9 |
| W5 | AC-5.1 / 5.2 | insert `_grok_log_has_events "$log" && { printf 'grok-ndjson'; return 0; }` before the agy grep | AC-5.1 mixed log (`{"event":"init"}` + F0) prints `grok-ndjson` |
| W6 | AC-6.1 | `if counts["agy_events"] == 0:` → `if counts["agy_events"] == 0 or scan_grok(text) is not None:` | mixed agy+F0 CLI test (stdout and rc must equal the agy-alone run) |
| W7 | AC-7.2 / 7.3 / 7.4 | (a) `if counts.get("agy_events", 0) > 0:` → `… > 0 and scan_grok(text) is None:`; (b) row A2 | (a) mixed agy+F0 `measure_effort` test (shape must be `parsed`); (b) AC-7.4 |
| W8 | AC-7.1 | `_cmd_exec "${agent[$i]}"` → `_cmd_exec grok` | `test_hmad_dispatch_audit_cycle.py::test_verb_two_distinct_dispatches` |
| W9 | AC-2.1 BLOCK-GROK cells | row G3 | AC-2.5 and the AC-2.1 grok cells |
| W10 | AC-8.2 | (a) `default="codex"` on `--agent` → `default="grok"`; (b) see residual | (a) AC-8.1 and `test_h_mad_assemble_tdd.py::TestCli::test_a_clean_assembly_prints_pass_and_the_command_block` |
| W11 | AC-9.1 | `if a.agent == "grok":` → `if True:` | row `test`: `test_h_mad_resolved_model.py::test_codex_reads_the_resolved_model_out_of_its_session_header`; informational: `::test_agreement_between_the_two_newest_is_answerable` |

- **One `test` per row.** A harness mutation carries exactly one `test` (the "Spec format" block of
  `h_mad_mutation_harness.py`'s docstring). Where a cell names two nodes, the first is the row's
  `test` and the second is informational, a node the impl-plan may run by hand.
- **The named existing nodes collect at `50560eb`.** The plan's collect command, re-run, prints
  `7 tests collected` (unit: tests).
- **Residual (W1's kill rests on an incidental zero).** W1 kills only because no `grok` resolves
  on the existing tests' `<bindir>:/usr/bin:/bin` PATH. At `0df3d47`,
  `PATH=/usr/bin:/bin command -v grok` fails (rc 1), because every installed `grok` is off that
  PATH: `which -a grok` at `0b3f969` lists `~/.grok/bin/grok`, `~/.local/bin/grok` and
  `/opt/homebrew/bin/grok`, and `/bin/grok` does not exist. That zero is incidental: a `grok` installed into `/usr/bin` would let the
  mutant run the real CLI. The existing tests cannot be edited (FR-11), so the new AC-3.6 cell
  asserts `command -v grok` fails in its own env as a precondition, and the W1 row is re-run
  at 5g.
- **Residual (W10b).** "Agent read from state" is killed by AC-8.5. It has no harness row, because
  the mutant would need a state reader the assembler does not contain, and it cannot be written
  as one replace.
- **Residual (whole table).** Whether each force-fire kills is a prediction until 5d/5e runs it.

### Existing mutation anchors

`test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok` runs the
harness's `--check-anchors` over every committed spec and requires each `find` to match its file
**exactly once**. It is a pre-existing test, so FR-11 forbids breaking it. The axis is every
committed anchor in a file this design edits. Two rules cover it:

1. **No edit changes an anchor's text.** The anchors this design would otherwise have touched,
   and the design's answer to each:
   - `assemble_tdd.json`, two rows on `command_block`'s `exec codex` line: the line is kept, and
     the grok block is derived from it (D9);
   - `codex_log_not_measured.json`, three rows on `measure_effort()`'s `parsed` and banner lines:
     the `if`/`elif` lines are kept, and grok goes into the `else` (D7);
   - `review_evidence_format.json`, one row on `main()`'s `if counts["agy_events"] == 0:` and its
     first comment line: the grok insertion goes after the comment block (D6);
   - `exec_last_step.json`, two rows, one on S6's agy block and one on `_agy_last_step`'s `tail`
     line: both unchanged, and the grok block is a sibling (D3);
   - `codex_log_not_measured.json`, two more rows inside the two audit-cycle functions this
     design edits: `combine()`'s `        if shape == "codex-text":` and `_effort_items()`'s
     `        if effort.get("shape") == "codex-text":`. Both lines are kept, and the grok routes
     are new lines beside them.
   The anchors inside those two functions were listed at `0b3f969` by testing every committed
   `find` whose file is `h_mad_audit_cycle.py` for containment in each function's source text:
   4 rows (unit: mutation rows), namely the two above and the two floor lines under rule 2.
2. **No new code contains an anchor as a substring.** The harness counts
   `source.count(find)` (`h_mad_mutation_harness.py`, the `hits =` line of its anchor check), so
   a single-line anchor also matches any new line that holds the same text at the same or a
   deeper indentation, because the anchor's leading spaces are a suffix of the deeper indent. A
   second match makes the anchor match twice. The near-collisions are new code that does the
   same job as an anchored line, and each has an executable prescription:
   - `scan_grok`'s `thinking` sum beside `scan()`'s anchored
     `if isinstance(value, (int, float)) and not isinstance(value, bool):` + `thinking += int(value)`
     (`audit_effort.json`). `scan_grok` spells the test `type(value) in (int, float)` (D6
     "Counting"), which contains neither anchor line;
   - the `grok` floor in `combine()`, beside the anchored
     `        if result.effort.get("ok", 0) <= DELIVERY_FLOOR:` (`codex_log_not_measured.json`).
     The shape tests in front of that line only `return` or `continue`, so there is nothing to
     widen. Two new lines go after `if shape == "empty":`'s return and before the kept floor
     line: `if shape == "grok-truncated":` returning `low_evidence_unmeasurable:p<i>`, then
     `if shape not in ("parsed", "grok"):` returning `shape_unrouted:p<i>`. The kept floor line
     then serves `parsed` and `grok` alike, and no floor test is written a second time;
   - the `grok` floor in `_effort_items()`, beside the anchored
     `        if effort["ok"] <= DELIVERY_FLOOR:` (`audit_effort.json`). The only shape test in
     front of it is the anchored `codex-text` `continue`. A new `grok-truncated` block beside it
     appends the not-measured line and `continue`s. The unanchored `line = (…)` assignment
     becomes a choice by shape: `if effort.get("shape") == "grok":` builds the grok line, which
     has no `failed` field, and `else:` keeps today's line, re-indented. The kept floor line then
     appends the `low-evidence` suffix to either line;
   - `grok_from_log`'s `--log` handling beside the anchored `    if a.log:` + its comment line
     (`resolved_model.json`). `grok_from_log(path)` takes the path as its parameter, and its
     refusal is spelled `if path is None:`. `main()` calls it as D10 states, and no new line
     reads `if a.log:`;
   - the grok helpers' region read beside `_agy_last_step`'s anchored `tail -n +"$((pre + 1))"`
     line. The different spelling `tail -n "+$(( pre + 1 ))"` keeps them apart (D3.4).

The same exactly-once rule binds the **new** rows: each new `find` must be unique in its landed
file, which is why the region read lives in one helper (D3.4).

**How the population was taken.** At `0df3d47`, the `find` of every row in
`h-mad/tests/mutation-specs/*.json` whose `file` is one of the seven files this design edits or
names (`hmad-dispatch.sh`, `h_mad_audit_cycle.py`, `h_mad_review_evidence.py`,
`h_mad_assemble_tdd.py`, `h_mad_resolved_model.py`, `h-mad-tdd-gate.sh`,
`h_mad_state_schema.json`) was listed. That gave 188 rows (unit: mutation rows), as 91, 44, 10,
39, 4, 0 and 0 respectively. Each was read against the D-sections above. **Residual:** that
reading is by eye. The enforcing check is the committed sweep test, run in the full suite per
task, and a new anchor committed later is covered by it without any change here.

## Verified premises (design-level)

V1–V11 were run at `50560eb`, V12–V17 at `0df3d47`, and V18–V25 at `0b3f969` (the `h-mad/`
code and tests are the same at all three, per §Overview). Scratch artifacts were written under the session
scratchpad or a `TemporaryDirectory` and deleted after the run.

- **V1 — the tree is the plan's tree.** `git diff --name-only 1680271 50560eb -- h-mad handoff |
  wc -l` → 0 files.
- **V2 — F0 is unchanged.**
  `shasum -a 256 docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson` →
  `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`; `git log --format=%h -1 --`
  the same path → `d2fbb96`. Re-read at `0b3f969`: the same hash. The suite never reads this
  path; it reads the in-skill copy (Test Strategy, "One fixture source").
- **V3 — AC census.** `grep -oE '^  - AC-[0-9]+\.[0-9]+[a-z]?'
  docs/01-plan/features/grok-codex-fallback.spec.md | sort -u | wc -l` → 58 distinct ids on spec
  v1.3 at `0df3d47` (55 on spec v1.2 at `50560eb`). The three new ids are AC-4.10, AC-5.2b and
  AC-11.3.
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
  - `ls -la /usr/bin/jq` → present, so `jq` is on the gate tests' `/usr/bin:/bin` PATH. It is
    also on every `<bindir>:/usr/bin:/bin` PATH, which is why omitting `jq` from `bindir` removes
    nothing (Test Strategy, "Tool-absent cells"). `which -a jq` at `0df3d47` lists
    `/opt/homebrew/bin/jq`, `/opt/anaconda3/bin/jq` and `/usr/bin/jq`, and `/bin/jq` does not
    exist;
  - `_bindir()` in `test_hmad_dispatch.py` itself symlinks `shutil.which("jq")` into every bindir
    it builds, so a tool-absent cell cannot use that helper.
- **V11 — gate test harness.** `test_h_mad_tdd_gate_codex.py` builds the env as
  `{"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()), …}`. The hook resolves
  `$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh`, which is the **main tree**
  through the install symlink even when the hook under test is the worktree's. That is harmless
  here because the derive script is unchanged, and it is stated so a later edit to that script is
  not silently tested against the old copy.

Readings new in v1.1, executed at `0df3d47` (scratch files under the session scratchpad, deleted
after the run):

- **V12 — the stubs capture only `HPW_AGENT_BACKEND`.** `h-mad/tests/stubs/codex` and
  `h-mad/tests/stubs/agy` each write the single line
  `printf 'HPW_AGENT_BACKEND=%s\n' "${HPW_AGENT_BACKEND-<unset>}" > "$HMAD_STUB_ENV_CAPTURE"`,
  and nothing records `CLAUDE*` names (read with `cat` on both files).
- **V13 — the D3.5 programs** on F0, F-TRUNC, F-NOTOOLS, F-SHARED's region (`pre = 110`),
  F-BEAT and AC-4.10's fixture, beside a Python implementation of the D6 rules (unit: the printed
  values per fixture):

  | region | `_grok_region_state` | N | `scan_grok` complete / ok / tools |
  |---|---|---|---|
  | F0 | complete | 2 | True / 2 / 2 |
  | F-TRUNC | truncated | 2 | False / 2 / 2 |
  | F-NOTOOLS | complete | 0 | True / 0 / 2 |
  | F-SHARED region | truncated | 2 | False / 2 / 2 |
  | F-BEAT | complete | 2 | True / 2 / 2 |
  | AC-4.10 fixture | complete | 0 | True / 0 / 2 |

  Completeness and N agree with `complete` and `ok` on every row. F-NOTOOLS is where N and the
  all-ids count `tools` differ (0 vs 2).
- **V14 — the D4 detector agreement matrix and the banner window** (D4, both executed).
- **V15 — `json.loads` recursion.** A line nested 200,000 deep raises `RecursionError` under
  Python 3.11.8 (D6).
- **V16 — the hook's first read under `pipefail`** (D2).
- **V17 — the committed anchors** in the edited files (§"Existing mutation anchors").

Readings new in v1.2, executed at `0b3f969` (scratch files under the session scratchpad, deleted
after the run):

- **V18 — the depth bound on both surfaces** (D3.5's table): three jq builds, Python 3.11.8 and
  3.14.7, at depths 64, 65, 1000, 5000, 10,000 and 200,000. Interpreters were read with
  `--version` on `/opt/homebrew/bin/jq`, `/usr/bin/jq`, `/opt/anaconda3/bin/jq`, `python3.11`,
  `python3` and `/opt/anaconda3/bin/python` (the suite's interpreter, 3.11.8).
- **V19 — `_grok_region_state` without early exit** under `pipefail` (D3.5): the v1.1 form
  `rc=141` in 3 of 3 runs, the reduce form `rc=0` in 3 of 3.
- **V20 — the bounded readers on F0** (D3.5, D4): `STATUS: DONE`,
  `2 tool calls completed; last tool: search_replace completed`, `end_turn`, and
  `_grok_log_has_events` rc 0.
- **V21 — row L2's `find` bytes.** With the design's fallback line written to a scratch file,
  Python's `str.count` gave 0 for `\{.*"type"` and 1 for `\{.*\"type\"` (unit: occurrences).
- **V22 — the window-edge log.** A 4095-character first line, then `OpenAI Codex v0.145.0`, then
  F0. The banner starts at character 4096 (`text.index`). The shell window says no at
  `head -c 4096` and yes at `head -c 8192`. Python's `text[:4096]` says no, and `text[:8192]`
  says yes.
- **V23 — the agent-CLI clause.** `grep -n 'Dispatched agent CLIs are not script dependencies'
  h-mad/invariants.base.md` → 1 matching line, in §"No new external dependency".
- **V24 — no `grok` in the tree's code or tests yet.** `grep -rln grok h-mad/scripts h-mad/hooks
  h-mad/bin h-mad/tests` → 0 files. Every future reference is this feature's.
- **V25 — farm facts.** `ls /bin` has no `jq` or `grok`. No current stub (`agy`, `cmux`,
  `codex`, `lsof`, `orca`) has a same-named entry in `/usr/bin`. `_isolated_env` in
  `test_hmad_dispatch.py` sets `e["PATH"] = f"{bindir}:/usr/bin:/bin"` after applying the caller's
  env, and `run()` goes through it (Test Strategy, "Tool-absent cells").

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `fallback_agent` property | `h-mad/scripts/h_mad_state_schema.json` | modify | FR-1, D1 |
| typed fallback read, BLOCK-GROK / BLOCK-INVALID | `h-mad/hooks/h-mad-tdd-gate.sh` | modify | FR-2, D2 |
| `_cmd_exec` S1/S3/S4/S6/S8, grok arm, `child_env`, `local recovered=""` | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-3, FR-4, D3 |
| `_GROK_TYPES_RE`, `_GROK_MAX_DEPTH`, `_GROK_JQ_DEFS`, `_codex_banner_in_head`, `_grok_log_has_events`, `_grok_region`, `_grok_region_state`, `_grok_final_message`, `_grok_stop_reason`, `_grok_last_tool` | `h-mad/scripts/hmad-dispatch.sh` | new | FR-4, FR-5, D3.4, D3.5, D4 |
| `_exec_log_format`, `_render_progress` grok branch | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-5, D4, D5 |
| `_cmd_audit_cycle` `--surfaces` case + message; `_cmd_resolved_model` header | `h-mad/scripts/hmad-dispatch.sh` | modify | FR-7, FR-9, D8, D10 |
| `_GROK_TYPES`, `GROK_MAX_DEPTH`, `_json_deeper_than`, `scan_grok`, `CODEX_BANNER_HEAD`, `codex_banner_in_head`, `main` banner-then-grok branch | `h-mad/scripts/h_mad_review_evidence.py` | new / modify | FR-5, FR-6, D6 |
| imports (`scan_grok`; `_CODEX_HEADER_RE` as `_CODEX_BANNER`, replacing the local definition), `measure_effort` `else` body, `combine`, `_effort_items` | `h-mad/scripts/h_mad_audit_cycle.py` | modify | FR-7, D7 |
| `--agent`, `--timeout` sentinel, `command_block(agent=)` | `h-mad/scripts/h_mad_assemble_tdd.py` | modify | FR-8, D9 |
| `grok_from_log`, `choices`, `main` order | `h-mad/scripts/h_mad_resolved_model.py` | new / modify | FR-9, D10 |
| Phase-5, exec, teammate-leg, never-gate sections | `h-mad/SKILL.md` | modify | FR-10, D12 |
| field semantics | `h-mad/references/state-schema.md` | modify | FR-10 |
| `exec grok` verb | `h-mad/references/agent-substrate.md` | modify | FR-10 |
| grok stub | `h-mad/tests/stubs/grok` | new | FR-3–FR-5, FR-7 |
| opt-in `CLAUDE*`-name capture knob `HMAD_STUB_CLAUDE_ENV_CAPTURE` | `h-mad/tests/stubs/codex`, `h-mad/tests/stubs/agy` | modify (test support) | AC-3.4, W2 (Test Strategy) |
| in-skill copy of F0, byte-identical | `h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson` | new | the root of every grok fixture; the suite runs with the skill alone |
| F0-derived fixture builder | `h-mad/tests/grokfixtures.py` | new | one fixture source |
| new test files (Test Plan) | `h-mad/tests/test_*.py` | new | FR-1–FR-11 |
| mutation specs (six files) | `h-mad/tests/mutation-specs/*.json` | new | AC-2.7, W1–W11, rows above |

## Implementation Order

1. **Fixtures and stubs.** Copy F0 byte-for-byte to
   `h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson`. Build `grokfixtures.py`, which
   carries the copy's sha256 check, every spec fixture and the three F-SEP fixtures; the `stubs/grok`; the opt-in `CLAUDE*` knob in
   `stubs/codex` and `stubs/agy`; and the tool-absent symlink-farm helper. There is no production
   code in this step. The full suite runs after it, to show the knob left every existing test
   unchanged.
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
7. **Cross-surface agreement tests** (`test_grok_two_instruments.py`). These depend on D3.5, D4,
   D6 and D7.
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
  - `grok stream not parsed — jq failed`;
  - `last step reached — N tool calls completed; last tool: <name> <status>`.
- **`hmad-dispatch progress`:** new token `format: grok-ndjson`. A log whose head window carries
  the codex banner keeps `format: codex-text` whatever else it carries. New render lines
  `(grok stream — jq not on PATH, cannot render)` and `(grok stream — jq failed, cannot render)`.
- **`hmad-dispatch audit-cycle --surfaces`:** accepts `grok`.
- **`hmad-dispatch resolved-model grok --log <f>`:** new.
- **`h_mad_review_evidence.py <log>`:**
  - `EVIDENCE: PASS|NONE tools= ok= unresolved= thinking= format=grok [stop_reason=]`, exit 0;
  - `EVIDENCE: UNREADABLE reason=truncated_no_end`, exit 2;
  - a log whose head window carries the codex banner keeps today's output, whatever else it
    carries;
  - new importable `scan_grok(log_text: str) -> dict | None`, `_GROK_TYPES`, `GROK_MAX_DEPTH`,
    `codex_banner_in_head(text: str) -> bool` and `CODEX_BANNER_HEAD`.
- **`h_mad_audit_cycle.measure_effort()`:** may return shapes `grok` and `grok-truncated`.
- **`h_mad_assemble_tdd.py --agent {codex,grok}`:** the default is `codex`. `--timeout`'s default
  becomes the not-given sentinel `None`, resolved to 900, or 1500 for grok.
  `command_block(..., agent: str = "codex")`.
- **`h_mad_resolved_model.py`:** agent `choices` gains `grok`.
  `grok_from_log(path: str | None) -> None`.

## Error Handling Strategy

- **Gate.** Every non-FALL-THROUGH outcome is exit 1 with a `[H-MAD-TDD-GATE] BLOCK:` stderr line,
  which is the hook's existing contract. A failure of the `fallback_agent` read (the second read)
  is BLOCK-INVALID `<unreadable>`, fail-closed. The no-`jq` exit 0 is the existing, disclosed
  fail-open.
  - **Out of scope, pre-existing:** a failure of the first read, which derives `ACTIVE`, exits
    the hook with that pipeline's rc under `set -euo pipefail` before this feature's block is
    reached (D2's scope-of-read-error bullet, V16: rc 5). This design does not change that path.
    Whether the hook runner treats that rc as a block or lets the tool call proceed was not
    measured, so its fail direction is unestablished.
- **Wrapper.** Every grok reader degrades to empty, or to the `nojq`/`jqfail` state, and never
  aborts `_cmd_exec` under `set -euo pipefail` (`|| true` or a captured rc, and `_grok_obj`). A
  missing or failing `jq` routes to the EMPTY path with a "not parsed" line that names which of
  the two happened. That is never a false success, and never a false `TRUNCATED` (row P9). No
  reader exits before its input ends, so a SIGPIPE on the region pipe cannot produce a false
  `jqfail` (D3.5, V19). The one known false `TRUNCATED` is the unmeasured heartbeat residual
  (D3.5), and its direction is a cannot-judge.
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
- **Tool-absent cells run on a symlink farm, never on `/usr/bin`.** The axis is "a cell that
  needs tool X absent while PATH still reaches a system copy of X". `/usr/bin/jq` exists on this
  host (V10), so leaving `jq` out of `bindir` removes nothing. `_bindir()` also links jq itself.
  The rule over the class:
  - The cell's PATH is exactly `<farm>:/bin`. `<farm>` holds the stubs the cell needs, plus one
    symlink for every entry of `/usr/bin` **except** the absent tool, built by one module-scoped
    helper in the new test files. The helper takes the absent names as its argument.
  - **Farm cells never go through `run()` or `_isolated_env`.** `_isolated_env` in
    `test_hmad_dispatch.py` applies the caller's env and then sets
    `e["PATH"] = f"{bindir}:/usr/bin:/bin"` (V25), and `run()` uses it. A farm cell passed through
    `run()` would therefore run on `<farm>:/usr/bin:/bin`, where `/usr/bin/jq` resolves. Each farm
    cell calls `subprocess.run(["bash", WRAPPER, …], env=cell_env)` with an env it builds itself,
    whose `PATH` is exactly `<farm>:/bin`. `BASH_ENV` and `ENV` are removed from that env, because
    a non-interactive `bash` sources `BASH_ENV` and it could extend `PATH`.
  - **Precondition, asserted inside the cell's own env:** `command -v <tool>` fails for every
    absent tool. It runs as `subprocess.run(["bash", "-c", "command -v <tool>"], env=cell_env)`,
    with the very dict passed to the wrapper, never a separately built one. A cell whose
    precondition fails errors, and never passes vacuously.
  - **Stub names win over `/usr/bin` entries.** The helper links the stubs first and skips any
    `/usr/bin` entry whose name is already linked. Otherwise `symlink_to` raises
    `FileExistsError`. No current stub collides on this host (V25).
  - **Second assertion:** stderr carries no `command not found`, so a tool the farm dropped by
    mistake fails loudly for its real reason.
  - **Deviation, announced.** The orchestrator's brief asks for a `<bindir>` holding exactly the
    tools the wrapper needs. This design uses all of `/usr/bin` minus the absent tool. The reason:
    an enumerated tool list is a count carried forward, and it goes stale the first time the
    wrapper calls a new utility. The absence being tested is the same either way. Revert option: a
    fixed tuple `_WRAPPER_TOOLS`, with each name asserted to resolve in the env.
  - **Members of the class, each with its own cell:**
    - exec `nojq`: EMPTY path, stderr has `grok stream not parsed — jq not on PATH` and no
      `TRUNCATED`;
    - `progress` jq-absent: `format: grok-ndjson` through D4's fallback, and the line
      `(grok stream — jq not on PATH, cannot render)`;
    - AC-5.2b on the fallback route (row L2);
    - AC-3.6 (`exec requires the grok CLI on PATH`): the farm excludes nothing, and the
      precondition is `command -v grok` fails. See also W1's residual.
  - **The "jq fails" route is a different cell.** A `jq` shim that exits 127 does not reach the
    absent branch, because `command -v jq` succeeds on the shim. So it is not a substitute for the
    farm. It is kept as its own route: `<bindir>` carries the shim ahead of `/usr/bin`, and the
    cells assert exec's `grok stream not parsed — jq failed` (row P9) and `progress`'s
    `(grok stream — jq failed, cannot render)`.
  - **Residual:** a tool resolved through an absolute path in the wrapper bypasses PATH, and so
    bypasses the farm. `jq` and `grok` are both invoked by bare name (`command -v jq`,
    `command -v "$agent"`).
  - **Residual (portability):** on a merged-`/usr` host, `/bin` is `/usr/bin`, so every farm
    cell's `/bin` still reaches the tool and the cell errors on its precondition. That is loud,
    never vacuous, but those cells cannot run on such a host.
- **The codex and agy stubs gain one opt-in knob, `HMAD_STUB_CLAUDE_ENV_CAPTURE`.** When it is
  set, the stub writes the sorted names of its exported `CLAUDE*` variables, one per line, to that
  file (`compgen -e` filtered by a `case`, as D3.3 does). When it is unset, the stub does nothing
  new.
  - **Opt-in, so existing tests see identical behaviour.** No existing test sets the new
    variable, and the knob writes to its own file. `HMAD_STUB_ENV_CAPTURE`'s single
    `HPW_AGENT_BACKEND=` line is untouched, so every existing reader of that file sees the same
    bytes.
  - **FR-11.** A stub is test support, not a pre-existing test. FR-11's "every pre-existing test
    unmodified" is about test files, and it holds: no `test_*.py` is edited. The stubs' existing
    behaviour is unchanged, and the full suite after Implementation Order step 1 is the evidence.
  - **Observable for AC-3.4 and W2.** AC-3.4 exports `CLAUDECODE` and three more `CLAUDE*` names,
    then runs `exec codex` and `exec agy` with the knob set. It asserts all four names are
    recorded. W2's mutant scrubs the codex child, so the file holds none, and AC-3.4 fails.
- **The grok stub models what the wrapper consumes.** It:
  - records argv to `HMAD_STUB_CAPTURE` as `grok <argv>`;
  - records `HPW_AGENT_BACKEND` to `HMAD_STUB_ENV_CAPTURE`, as the other two stubs do, and every
    `CLAUDE*` name to `HMAD_STUB_CLAUDE_ENV_CAPTURE` (AC-3.3), the same knob and format as theirs;
  - **copies the `--prompt-file` contents** to `HMAD_STUB_GROK_PROMPT_CAPTURE` at invocation;
  - writes the file named by `HMAD_STUB_GROK_STREAM` to stdout line by line;
  - sleeps `HMAD_STUB_GROK_SLEEP` after emitting (AC-4.8);
  - exits `HMAD_STUB_GROK_RC`.
  Knob names follow the existing `HMAD_STUB_<AGENT>_*` convention seen in `stubs/agy` and
  `stubs/codex`.
- **One fixture source, inside the skill.** F0 is copied byte-for-byte to
  `h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson`, as spec §"Fixtures" (the F0 entry)
  allows.
  `grokfixtures.py` reads only that copy, never the `docs/` path. Before deriving anything it
  asserts the copy's sha256 equals F0's committed hash,
  `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569` (V2), written into the
  module as a constant. Every grok stream in every test is built from that copy, so the suite runs
  from a clone holding the skill alone. A dedicated test, `test_grok_fixture_copy_hash` (Test
  Plan), asserts the same hash, so a changed copy fails as one named test, not only as an error
  in every consumer.
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
| `h-mad/tests/grokfixtures.py` | the in-skill F0 copy's path (`h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson`) + sha256 assert against the constant `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`; builders for the depth lines (`{"type":"text","data":"x","n":` + k nested arrays + `}`, depth k, for k = 64 and 65), F-DEEP64 and F-DEEP65 (F-TRUNC followed by a `text` event `DEEP`, a `tool_call_update` with `toolCallId` `deep` and `status` `completed`, and an `end` event with `stopReason` `deep`, each carrying an `"n"` member of depth 64 or 65 respectively), the 200,000-deep line, and for F-TRUNC, F-NOTOOLS, F-NOTEXT, F-NOTOOLTEXT, F-DECOY, F-BEAT, F-SPACED, F-TWOMODEL, F-SHARED, F-SEP-usage, F-SEP-tool_call, F-SEP-tool_call_update, the AC-7.3 three-completed stream, the mixed agy+F0 log, AC-4.10's stream (F-NOTOOLS minus every `text` event), AC-11.3's banner-then-F0 log, and the window-edge log (a first line of exactly 4095 `x` characters and its newline, then `OpenAI Codex v0.145.0`, then F0; the banner starts at character and byte 4096, V22, just outside a 4096 window and inside any window of 4110 or more) |
| `test_h_mad_state_fallback_agent.py` | AC-1.1–1.4 (AC-1.3 over `h-mad/tests/fixtures/state_incident_replay.json`) |
| `test_h_mad_tdd_gate_fallback_agent.py` | AC-2.1 (80 cells, expected value from an in-test transcription of the table), AC-2.1b (24 BLOCK-INVALID + 3 JSON-`null` control + absent control + 8 BLOCK-CODEX), AC-2.2 (16 × 3 against the pinned base), AC-2.3–2.6; design test **read error fails closed** (a `jq` shim in `bindir` that execs the real `jq` except when its filter mentions `fallback_agent`, where it exits 5 → BLOCK-INVALID `<unreadable>`) |
| `test_hmad_dispatch_exec_grok.py` | AC-3.1–3.7 (AC-3.3 through `HMAD_STUB_CLAUDE_ENV_CAPTURE` on the grok stub; AC-3.4 through the same knob on the codex and agy stubs; AC-3.6 on the farm with the `command -v grok` precondition), AC-4.1–4.10 (AC-4.10: AC-4.10's stream, stub rc 0 → rc 3 and stderr contains `0 tool calls completed; last tool: search_replace pending`); design tests: F-SEP ×3 (stdout `STATUS: DONE`); **jq absent** on the farm (precondition `command -v jq` fails; stderr has `grok stream not parsed — jq not on PATH`, no `TRUNCATED`, no `command not found`); **jq fails** with a 127 shim (stderr has `grok stream not parsed — jq failed` and no `TRUNCATED`, row P9) |
| `test_hmad_dispatch_progress_grok.py` | AC-5.1, AC-5.2 (the four per-class equalities and the two absences, D5); design tests: **jq absent** on the farm (`format: grok-ndjson` and `(grok stream — jq not on PATH, cannot render)`); **jq fails** with the shim (`(grok stream — jq failed, cannot render)`) |
| `test_h_mad_review_evidence_grok.py` | AC-6.1–6.4, AC-6.6; mixed agy+F0 CLI equality (W6); design test **malformed `type`**: F0 with `{"type":[]}`, `{"type":{}}`, `{"type":1}`, `{"type":null}` and a line nested 200,000 deep (which raises `RecursionError` under both Python 3.11.8 and 3.14.7, so row E7 is killed on either interpreter) placed **before** the first event and again **between** two events. `scan_grok` returns counts equal to F0's, and the CLI prints F0's `EVIDENCE:` line (row E4) |
| `test_h_mad_audit_cycle_grok.py` | AC-7.2–7.4; shape enumeration: the seven shapes `missing`, `empty`, `parsed`, `grok`, `grok-truncated`, `codex-text`, `unparseable`, each asserted to its D7 route and `_effort_items` rendering, plus a hand-built unknown shape → `shape_unrouted`; mixed agy+F0 `measure_effort` → `parsed` (W7a) |
| `test_hmad_dispatch_audit_cycle_grok.py` | AC-7.1 |
| `test_grok_two_instruments.py` | **Format agreement.** On F0, F-SPACED, F-TRUNC, an agy log, a codex-banner log, the mixed log, AC-11.3's log and the window-edge log, the `format:` of `hmad-dispatch progress` and `measure_effort()["shape"]` agree under the mapping `agy-ndjson ↔ parsed`, `grok-ndjson ↔ grok \| grok-truncated`, `codex-text ↔ codex-text \| unparseable`. The window-edge log is ASCII, so D4's window-units residual does not apply to it: its banner starts at character and byte 4096, both windows miss it, all three surfaces read grok, and the test asserts they agree. That pins the shell's `head -c 4096` (row L5). <br> **Depth boundary (D3.5, D6).** The depth-64 single-line log → `format: grok-ndjson` and `scan_grok(...) is not None`; the depth-65 log → `format: codex-text` and `None` (rows L3, E6, E8). On F-DEEP64 and F-DEEP65, executed at `0b3f969` on both surfaces: F-DEEP64 gives `_grok_region_state` `complete`, final message `DEEP`, N 3, stop reason `deep`, and `scan_grok` complete `True` / ok 3; F-DEEP65 gives exactly F-TRUNC's values, which are `truncated`, `STATUS: DONE`, N 2, no stop reason, and complete `False` / ok 2 (row L4). `progress` on F-DEEP65 prints no `END stopReason=deep` line. The Python constant `GROK_MAX_DEPTH` equals the `_GROK_MAX_DEPTH=` literal parsed out of `hmad-dispatch.sh`. <br> **`test_grok_fixture_copy_hash`.** The sha256 of `h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson` equals `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`. It reads nothing outside `h-mad/`. <br> **AC-5.2b.** The two single-line logs of spec AC-5.2b, through `progress` (jq route, and fallback route on the farm) and through `scan_grok(...) is not None`: key-order line → `grok-ndjson` / non-`None`; bogus-type line → `codex-text` / `None`. <br> **AC-11.3**, one assertion per surface on the banner-then-F0 log: `progress` prints `format: codex-text`; the CLI prints today's codex-text output for those bytes (a `CODEXEVIDENCE:` line, then `EVIDENCE: UNREADABLE reason=unsupported_format`), rc 2, and no line contains `format=grok`; `measure_effort` → `codex-text` (rows L1, E3, A3). <br> **Window-edge equality** between the CLI and `measure_effort` on the window-edge log (row E5). <br> **Completeness and N, single-sourced (brief item 4).** On F0, F-TRUNC, F-NOTOOLS, F-SHARED's region and F-BEAT: `_grok_region_state` (via `run_fn`) is `complete` iff `scan_grok()["complete"]`, and the N in `_grok_last_tool`'s line equals `scan_grok()["ok"]` on the same region text. Expected values are V13's table. <br> **Vocabulary, single-sourced.** The `_GROK_TYPES_RE` literal parsed out of `hmad-dispatch.sh`, split on `\|`, equals `h_mad_review_evidence._GROK_TYPES` as a set (base §"Single-source contract") |
| `test_h_mad_assemble_tdd_agent.py` | AC-8.1–8.5 (AC-8.2 includes `--timeout=900` and `--ti 900` under `--agent grok`) |
| `test_h_mad_resolved_model_grok.py` | AC-9.1–9.3 |
| `test_grok_fallback_docs.py` | AC-10.1 via `docsections.titled_section`, which asserts a missing heading and never skips; AC-10.2 |

- **AC-5.3, AC-6.5, AC-7.5, AC-9.4, AC-11.1 and AC-11.2** are the unchanged pre-existing files
  passing in the full run. AC-5.3 is `test_hmad_dispatch_progress.py`'s existing agy and codex
  rendering tests. The node-id floor (plan Success Criteria) proves no deletion.
- **AC-2.7** is the gate's mutation rows G1–G3, run by the harness (§"Mutation rows and wire
  force-fires"), not a pytest file.
- **AC coverage.** Every one of the spec's 58 distinct AC ids is named in this section. Counted
  at `0df3d47` by extracting every `AC-N.M[x]` token from this section, expanding each range such
  as `AC-4.1–4.10`, and comparing with the spec's `^  - AC-` ids: 58 of 58, and no id named here
  that the spec lacks.
- **F-DECOY placement (spec v1.3).** F0's final segment is its last three `text` events (`STATUS`,
  `:`, ` DONE`). They are replaced by a `text` event `All `, the `thought` decoy (`STATUS: DONE`),
  and a `text` event `done.`, in that order. Then come the `tool_call` decoy and the bare
  `STATUS: DONE` line, all before the `usage` closer that follows. The `thought` decoy sits
  **inside** the final segment, which is what makes row P4 observable: executed, the mutant's
  output ends `All STATUS: DONEdone.`, while healthy prints `All done.`.
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
- **Single-source contract.** It complies. Each rule implemented on both sides of the
  shell/Python line has one cross-surface test in `test_grok_two_instruments.py`:
  - the seven-type vocabulary (`_GROK_TYPES_RE` and `_GROK_TYPES`, asserted equal as sets);
  - grok detection (AC-5.2b, plus D4's measured residual class);
  - the depth bound (`_GROK_MAX_DEPTH` and `GROK_MAX_DEPTH`, asserted equal, and the depth-64/65
    boundary on both surfaces). This makes the two detectors' input domain identical on the depth
    axis. The parser-grammar class stays a stated residual (D4);
  - completeness and N (`_grok_region_state`/`_grok_last_tool` against `scan_grok`'s `complete`
    and `ok`, over five fixtures);
  - banner precedence (AC-11.3 on all three surfaces).
  The banner pattern is single-sourced in Python (`_CODEX_HEADER_RE`, imported by the audit
  cycle). The window `4096` is written twice because one copy is a committed mutation anchor
  (D6), and the window-edge equality test pins the two.
- **Standalone / no plugin dependency; no new external dependency.** It complies. The design adds
  stdlib Python, `jq` where the agy path already requires it, and POSIX `env`. `grok` is covered
  by the clause in base §"No new external dependency" (V23): "Dispatched agent CLIs are not
  script dependencies. `codex`, `agy` and `grok` are optional runtime agents: reached only
  through a `hmad-dispatch` verb …, never imported, required, or invoked by a script or test for
  its own work — tests reach them through stubs". The design meets each condition of it:
  - **Reached only through a verb.** The one invocation is `exec grok`'s child (D3.2). No script
    imports or requires `grok`. `resolved-model grok` (D10) and `scan_grok` (D6) read a log that
    a dispatch already wrote, and never run the CLI.
  - **Tests reach it through stubs.** Every test that dispatches grok puts `stubs/grok` on its
    PATH. The suite makes no
    live call (Test Strategy), and AC-3.6 runs with `command -v grok` failing, asserted as a
    precondition.
  - **An absent `grok` is a dispatch-time condition.** `command -v "$agent"` reports
    `exec requires the grok CLI on PATH` (D3.1), and nothing else in the skill fails.
  - **Not a script.** The Phase-5 live smoke (D13) runs the real `grok` by hand once, as a
    verification step before merge. It is not a script or a test in the suite.
  - **Residual.** W1's mutant would run a real `grok` if one resolved on `/usr/bin:/bin` (§"Wire
    force-fires", W1's residual). None does at `0b3f969`, and the row is re-run at 5g.
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
- **Assumption verification; behavioural premises carry their command.** It complies. V1–V25 and
  every D-section reading carry the command and one reading, at `50560eb`, `0df3d47` or
  `0b3f969` as stamped. The `h-mad/` code and tests are identical at the three; only
  `h-mad/invariants.base.md` differs at `0b3f969` (§Overview).
- **Counts a dispatch reports.** Every count here was re-derived at the sha it is stamped with,
  not carried.
- **Wrapper–runtime reconciliation.** It complies through plan v1.3's live smoke (D13). The
  `--model`/`--sandbox` argv paths stay stub-verified only, as the plan's stated residual.
- **Regression provenance.** No existing test is edited. The codex and agy stubs gain an opt-in
  knob that no existing test sets (Test Strategy), and every committed mutation anchor in an
  edited file is kept byte-identical (§"Existing mutation anchors").
- **Both halves of a doc change.** No documented capability is removed.
- **Reimplementation parity.** Not applicable.

**Project layer (`.h-mad/invariants.md`):**

- **Skill self-containment.** It complies. No code or test reads outside `h-mad/`, apart from the
  documented `~/.claude/...` install path the hook already uses. F0 reaches the suite as the
  in-skill copy `h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson`, checked against F0's
  committed sha256 by `grokfixtures.py` and by `test_grok_fixture_copy_hash`. No test reads the
  `docs/03-analysis/` original. The HemaSuite `_MARKERS`
  reference is a documentation citation only.
- **Skill manifest integrity.** It complies. `SKILL.md`'s frontmatter is untouched, and the entry
  behaviour change is documented in `SKILL.md` (D12).

## Version History
- v1.0: Initial design draft (2026-09-28) from spec v1.2 and plan v1.3, tree read at 50560eb. Typed fail-closed fallback_agent read placed after BLOCK-CODEX; explicit grok arm first in _cmd_exec with S4/S8 else arms made explicit elifs; child-only env -u CLAUDE* scrub; jq segmenter, region state, last-tool readers scoped by pre_lines; grok-ndjson detection helper after agy; scan_grok and closed-world combine routing with a distinct shape_unrouted reason; presence-judged --timeout sentinel (default=None); last-end model reader first in main(); legs_changed switch executed; per-closer F-SEP fixtures and one-replace force-fires for W1-W11.
- v1.1: Design audit cycle 1 owed items and spec v1.3 (2026-09-28), authored at 0df3d47. One precedence in all three classifiers (agy, codex banner in the head window, grok, codex-text): shell _codex_banner_in_head over 4096 bytes with the byte/char window residual stated, CLI codex_banner_in_head, measure_effort keeps its anchored elif ahead of grok. Key-order-independent grok detection: jq route with a grep fallback, agreement with scan_grok measured and its residual class stated. scan_grok type-checks before membership and catches RecursionError. D3.5 readers stream the region through one _grok_region helper with no tail cap; N is completed ids over the whole region, single-sourced with scan_grok ok by test; the false all-fixtures-agree claim and the 2000-line cap are removed. nojq/jqfail as distinct states and wordings. Heartbeat residual beside the completeness rule. Shape count 7. D5 run-state and AC-5.2 per spec v1.3. D9 keeps the anchored exec codex line. New section on existing mutation anchors. Tool-absent cells on a /usr/bin-minus-tool symlink farm with a command -v precondition. Opt-in HMAD_STUB_CLAUDE_ENV_CAPTURE knob in the codex/agy stubs. Test Plan rows for AC-4.10, AC-5.2b, AC-11.3, AC-5.3, AC-2.7; cross-surface completeness/N tests; mutation rows P8, P9, D1, D2, E3-E5, A3.
- v1.2: Corrective revision after design audit round 2 (2026-09-28), authored at 0b3f969; not re-audited. Identical input domain on the depth axis: one bound, _GROK_MAX_DEPTH=64 / GROK_MAX_DEPTH=64, applied through one jq filter _grok_obj in every jq program and an iterative depth check in scan_grok, executed at depths 64/65/1000/5000/10000/200000 on three jq builds and Python 3.11.8/3.14.7; RecursionError catch kept and mutation-rowed (E7) on a 200,000-deep line; the parser-grammar class and the fallback grep's domain stated exactly as residuals. grok compliance now cites the base agent-CLI clause. In-skill F0 copy at h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson with a sha256 test. New section Supersedes the plan on (precedence, 55 vs 58 ACs). Delta-review items: _grok_region_state reads the whole region (no SIGPIPE false jqfail), -r on all four readers, row L2 find bytes, anchor rule 2 as substring with executable prescriptions and two more kept anchors, farm cells bypass run()/_isolated_env, E5 fixture pinned at banner offset 4096 plus row L5, widened class-sweep needle, Error Handling first-read scope; log-format rows renamed L1/L2, W1 install paths, stub-name precedence. New rows L3-L5, E6-E8; V18-V25.
