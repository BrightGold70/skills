# Spec: grok-codex-fallback

## Executive Summary

A new optional state field, `fallback_agent` (`grok | claude`), declares who covers when codex is
out. Under `fallback_agent=grok`, three things change. The TDD gate keeps Claude from writing
production code. Phase 5 and the independent audit leg route through a new `hmad-dispatch exec grok`
backend, whose `streaming-json` transcript is parsed for its final message, its liveness, its
tool-call evidence and its resolved model. Every existing record and caller that omits the field
behaves exactly as today.

## Goal

When codex is out of quota, the author of Phase-5 production code and the independent audit surface
come from a model family different from the orchestrator's. Today both fall back onto Claude, and a
reviewer from the same family shares the author's blind spots by construction.

## Scope and measurement boundary (D4)

This feature ships **plumbing and documentation only**. Grok has been measured on exactly two
things:

- **One RED dispatch.** HemaSuite #28 Task 2: rc=0, 543 s, a planned 5 fail / 1 pass split,
  reproduced by the operator.
- **One `streaming-json` probe.** `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.md`
  and the `.ndjson` beside it.

GREEN quality, mutation-kill quality, wiring-pin quality, audit-leg precision, cost and latency are
**unmeasured**. They are not acceptance criteria here, and every surface this feature documents must
say so (FR-10). No AC in this spec may require a live xAI call. Each one runs offline, against a stub
`grok` binary or against a fixture derived from the committed probe transcript.

## Fixtures

Every grok-parsing AC below names one of these fixtures. **F0** is the committed probe transcript.
Every other fixture is derived from F0 inside the test, so no second hand-written grok stream
exists to drift from the real one.

- **F0**: `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`. One reading:
  110 lines, 83,256 bytes, sha256
  `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`, at commit `d2fbb96`.
  - The commands that re-derive these figures are in the probe sidecar
    (`docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.md`), section
    "Re-derivation commands". Two figures below are not in that section, and each carries its own
    command here: the `status: null` count and the line-prefix count. A test may copy F0 under
    `h-mad/tests/fixtures/`, but it must assert that the copy's sha256 equals F0's.
  - Measured on F0 with `jq`: event `type` counts are `thought` 70, `text` 21,
    `available_commands` 9, `usage` 3, `tool_call_update` 4, `tool_call` 2, `end` 1.
  - It has 2 distinct `toolCallId`s whose `tool_call_update.status == "completed"`, and 2
    `tool_call_update` events with `status: null`, counted with
    `jq -c 'select(.type=="tool_call_update" and .status==null)' <F0> | wc -l`.
  - The sum of `usage.reasoning_tokens` over the 3 `usage` events is 121.
  - `end.modelUsage` has exactly one key, `grok-4.7-build`, and `end.stopReason` is `end_turn`.
  - Every line begins with the bytes `{"type":"`. That gives 110 matching lines, counted with
    `grep -c '^{"type":"'`.
- **F-TRUNC**: F0 with its single `end` line removed. This is a killed or crashed run.
- **F-NOTOOLS**: F0 with every `tool_call_update.status` set to `null`. It has tool calls, and
  none of them completed.
- **F-NOTEXT**: F0 with every `text` event removed. It has an `end` event and no final message.
- **F-NOTOOLTEXT**: F0 with every `tool_call`, `tool_call_update` and `text` event removed. The
  derivation filters on `type` only, so F0's single `end` event survives: the region is complete,
  has no non-empty segment, and takes the EMPTY path while holding no `tool_call`. One reading on
  F0 at the sha256 stated above: 83 lines remain (`thought` 70, `available_commands` 9, `usage` 3,
  `end` 1), derived with
  `jq -c 'select(.type!="tool_call" and .type!="tool_call_update" and .type!="text")' <F0>`.
- **F-DECOY**: F0 with its final text segment (`STATUS: DONE`) replaced by `All done.` and three
  decoys inserted, none of which may be recovered as a verdict:
  - a `thought` event whose `data` is `STATUS: DONE`, placed **inside the final text segment**:
    the replacement segment is split into two `text` deltas (`All ` and `done.`) and the `thought`
    sits between them. A `thought` is not a segment closer (FR-4), so the segment stays
    `All done.`, and a mutant that appends `thought` data yields `All STATUS: DONEdone.`, which
    AC-4.3 observes;
  - a `tool_call` whose `rawInput` contains the string `STATUS: DONE`;
  - a bare non-JSON line `STATUS: DONE`.
- **F-BEAT**: F0 with a `#hmad-beat` wrapper heartbeat line and a blank line inserted between
  every pair of events.
- **F-SPACED**: F0 re-serialized with a space after every `:` and `,`, as `json.dumps` does by
  default.
- **F-TWOMODEL**: F0 with a second key added to `end.modelUsage`.
- **F-SHARED**: F0, followed by the lines of F-TRUNC. This is a caller-supplied `--log` that
  already holds a previous, completed dispatch.

## Functional Requirements

### FR-1: `fallback_agent` state field

- **Description**: `h-mad/scripts/h_mad_state_schema.json` gains an OPTIONAL property,
  `fallback_agent`, on the per-feature record, beside `codex_status`.
  - The field is not in `required`, and its `enum` is `["grok", "claude", null]`.
  - `codex_status` keeps its enum (`available|unavailable|exhausted|null`) and its single meaning,
    *why codex is out*. `fallback_agent` means *who covers*.
  - The field is **not** a status. It is read only when codex is out, as defined in FR-2.
  - Absent and `null` mean the same thing as `claude`: Claude covers, exactly as today.
  - `codex` and `agy` are deliberately excluded from the enum. Codex cannot stand in for itself,
    and agy is not a Phase-5 implementer.
  - The record's `additionalProperties: false` is why the property must be declared.
    `h_mad_state_write.py` refuses an undeclared key.
- **Acceptance Criteria**:
  - AC-1.1: The following command writes the value, and the record then validates under
    `h_mad_state_validate.py`. The same holds for `=claude`, and for `=null`, which writes JSON
    `null`.

    ```
    h_mad_state_write.py --feature <f> --set fallback_agent=grok <state>
    ```

  - AC-1.2: `--set fallback_agent=codex` is refused, and so are `=agy` and `=Grok` (the enum is
    case-sensitive). The state file is byte-identical afterwards.
  - AC-1.3: A record that carries no `fallback_agent` key keeps its tier. For every record in
    `h-mad/tests/fixtures/state_incident_replay.json`, `h_mad_state_validate.classify()` returns
    the same `strict|historical|invalid` value before and after the schema change.
  - AC-1.4: The property's `description` states all four of the following:
    - the field is read only when codex is out;
    - absent, `null` and `claude` are equivalent;
    - `HMAD_CODEX_UNAVAILABLE` does not override `grok` (FR-2);
    - the audit-leg routing is prose-enforced (FR-10).

### FR-2: TDD gate — Claude never self-authors under `fallback_agent=grok`

- **Description**: `h-mad/hooks/h-mad-tdd-gate.sh`, in its codex-authorship block (the block
  headed `# --- Codex-authorship enforcement`), reads `fallback_agent` for the same `ACTIVE`
  feature it reads `codex_status` for. The rest of the hook is unchanged: the state-file
  resolution, the `step5` detection, the exemptions for tests, docs and config, and the test-first
  gate below the block.

  Define **codex_out** as true when any of these holds. This is exactly today's escape predicate:

  - `HMAD_CODEX_UNAVAILABLE` is non-empty;
  - `codex_status` is `unavailable` or `exhausted`;
  - `codex` is not on PATH.

  The block's outcome is then a total function:

  | codex_out | `fallback_agent` (for the ACTIVE feature) | outcome |
  |---|---|---|
  | false | any value, or absent | **BLOCK-CODEX**: today's exit 1 and today's stderr, byte for byte |
  | true | absent, `null`, or `"claude"` | **FALL-THROUGH** to the test-first gate, exactly as today |
  | true | `"grok"` | **BLOCK-GROK**: exit 1 |
  | true | any other JSON value (another string, a number, a boolean, an object or an array) | **BLOCK-INVALID**: exit 1, fail-closed |

  - **OQ1 (binding):** `HMAD_CODEX_UNAVAILABLE` means only "codex is out". It never lets Claude
    write under `fallback_agent=grok`. A one-off Claude escape needs `fallback_agent=claude`.
  - A `codex_status` value outside its enum is read as `available`, which is today's behaviour
    and is unchanged.
  - Grok writes through its own process, so its writes never reach this PreToolUse hook. The same
    is true of codex.
- **Acceptance Criteria**:
  - AC-2.1 (**gate matrix**): One parametrized test covers the full cartesian product of four
    axes, 80 cells in all (4 × 5 × 2 × 2):

    - `codex_status` ∈ {absent, `available`, `unavailable`, `exhausted`};
    - `fallback_agent` ∈ {absent, `null`, `"claude"`, `"grok"`, `"codex"`};
    - `HMAD_CODEX_UNAVAILABLE` ∈ {unset, `1`};
    - `codex` on PATH ∈ {yes, no}.

    Each cell asserts two things:
    - the exit code and outcome class the table above predicts;
    - for FALL-THROUGH, that the hook exits 0 on a fixture where the test-first gate passes. That
      fixture is a production `.py` target that does not exist yet, whose derived test file does
      exist.

    The expected value is computed by a function in the test that transcribes the table. It is
    never computed by calling the hook.
  - AC-2.1b (**the BLOCK-INVALID class, each member alone**): AC-2.1 draws only `"codex"` from the
    invalid row, so this test exercises one representative of every JSON type the row covers,
    plus the values most easily mistaken for absent or `null`. The axis is the JSON type of the
    stored value; the members are:
    - `false` and `true` (boolean);
    - `0` (number);
    - `"null"`, `""` and `"Grok"` (string: the word null, the empty string, and a case variant of
      a valid value);
    - `{}` (object);
    - `[]` (array).

    Each of the 8 values is its own parametrized case, never a combined fixture, so a healthy
    sibling cannot cover a sick one. Each case runs under each of the three codex_out routes
    alone: `HMAD_CODEX_UNAVAILABLE=1` with `codex_status` absent and `codex` on PATH;
    `codex_status: "exhausted"` with the variable unset and `codex` on PATH; and `codex` off PATH
    with the variable unset and `codex_status` absent. That is 24 cells, and each asserts exit 1,
    the BLOCK-INVALID class, and AC-2.4's stderr. The same 8 values with codex_out false yield
    BLOCK-CODEX, as the table's first row says.

    **Control:** a stored JSON `null` under the same three routes is FALL-THROUGH (3 cells), and so
    is an absent key. The string `"null"` and the JSON `null` must therefore produce different
    outcomes. **Residual:** other strings are covered by the table's rule and are exercised only
    by `"codex"` (AC-2.1) and the three strings above; numbers other than `0` are not exercised.
  - AC-2.2 (**regression, absent field**): For `fallback_agent` absent, the hook's exit code and
    stderr in each of the 16 cells equal those of the hook at the feature's base commit, byte for
    byte. The 16 cells are 4 `codex_status` × 2 env × 2 PATH, and the base hook is read with
    `git show <base>:h-mad/hooks/h-mad-tdd-gate.sh`. The same 16-cell comparison passes for
    `fallback_agent: null` and for `"claude"`.
  - AC-2.3: BLOCK-GROK's stderr names all of the following:
    - the dispatch `hmad-dispatch exec grok`;
    - the assembler flag `--agent grok` (FR-8);
    - the escape `--set fallback_agent=claude`;
    - the fact that `HMAD_CODEX_UNAVAILABLE` does not override `fallback_agent=grok`.
  - AC-2.4: BLOCK-INVALID's stderr names the offending value and the valid set `grok|claude`.
  - AC-2.5: `fallback_agent=grok` on a *different* feature in the same state file, one that is not
    `ACTIVE`, does not change the ACTIVE feature's outcome.
  - AC-2.6: The files the hook exempts today stay exempt under `fallback_agent=grok` with codex
    out: test files, `*/tests/*`, `*/fixtures/*`, docs, config, shell, and every non-`.py` target.
  - AC-2.7: A committed mutation spec under `h-mad/tests/mutation-specs/` has one row for each of
    three mutations, and each row is killed by an AC-2.1 cell:
    - dropping the BLOCK-GROK branch;
    - letting a non-empty `HMAD_CODEX_UNAVAILABLE` bypass BLOCK-GROK;
    - reading `fallback_agent` from a feature other than `ACTIVE`.

### FR-3: `hmad-dispatch exec grok` transport

- **Description**: `_cmd_exec` in `h-mad/scripts/hmad-dispatch.sh` accepts `grok` beside `codex`
  and `agy`. It shares everything `exec` already has:
  - the live-template-slot advisory;
  - the `--cd`, `--model`, `--effort`, `--out`, `--log`, `--timeout` and `--sandbox` options;
  - the 3600 s wait ceiling when there is no `--timeout`;
  - the `--out` fingerprint and clobber check, and the atomic `--out` write;
  - the coordinator-handle line and the `_dispatch_boundary` suffix on the bounded prompt;
  - the heartbeat, the start and exit stamps, the notify call, and the rc-124 wording.

  The grok child is invoked as:

  ```
  grok --cwd <cd_dir> --always-approve --output-format streaming-json --prompt-file <bounded-prompt-file> [--model <m>] [--reasoning-effort <e>] [--sandbox <s>]
  ```

  - **`--prompt-file` points at the bounded prompt file.** That is the caller's prompt plus the
    coordinator line and the boundary, the same bytes codex and agy receive.
  - **Never `-p` or `--single`.** Grok's argparse exits rc=2 when either is combined with
    `--prompt-file`.
  - **Option translation:**
    - `--effort` becomes `--reasoning-effort`. This is grok's own flag; `--effort` is its alias,
      from `grok --help` at 1.0.41.
    - `--sandbox <s>` is passed through verbatim, and no default is supplied. No profile value has
      been probed, and grok's `--help` lists none.
    - **`GROK_SANDBOX` is inherited, not scrubbed.** At 1.0.41 `grok --help` shows `--sandbox`
      reading `[env: GROK_SANDBOX=]`. An operator's exported `GROK_SANDBOX` therefore reaches the
      grok child and selects a sandbox profile although argv carries no `--sandbox`. The wrapper
      neither removes nor sets it, and the spec supplies no default. When `--sandbox <s>` is given
      it is in argv beside any inherited value; which one grok honours was not probed. FR-10
      discloses this.
    - `--timeout` bounds only the wrapper's watchdog. Grok has no print-timeout flag.
  - **Transcript:** the child runs with working directory `<cd_dir>`. Its stdout and stderr are
    appended to `--log` with a direct redirect, as the codex path does. That preserves grok's rc
    and keeps grok's own diagnostics in the log, and the parsers of FR-4 to FR-6 skip every
    non-JSON line.
  - **Environment of the grok child only (OQ2, binding).** The wrapper's own environment and the
    codex and agy paths are untouched.
    - Every variable whose name begins with `CLAUDE` is removed. The class is `^CLAUDE`, so it
      covers `CLAUDECODE` and every `CLAUDE_*` name.
    - `HPW_AGENT_BACKEND` is defaulted with `:=` to `claude`. An operator's non-empty value always
      wins. An empty value is replaced, which is `:=` semantics.
    - **Residual:** markers of other families are not removed. These are `CODEX_SESSION_ID`,
      `CODEX_THREAD_ID`, `GEMINI_CLI` and `ANTIGRAVITY_AGENT`, the names listed in
      `_MARKERS` of `/Users/kimhawk/orca/HemaSuite/shared/agent_backend.py`, a file in another
      repository. That module lets an explicit
      `HPW_AGENT_BACKEND` outrank marker detection, which is what makes the default sufficient.
      A non-HPW consumer of a `CLAUDE*` variable, such as `CLAUDE_CONFIG_DIR`, also loses it
      inside the grok child. That is accepted.
  - **The ARG_MAX `OVERSIZE` refusal does not apply to grok.** The prompt travels as a file, not an
    argv element. No wrapper-side size bound is added, because grok's input ceiling is unmeasured.
    See Out-of-Scope.
- **Acceptance Criteria** (stub `grok` on PATH, in the style of the existing `HMAD_STUB_*`
  harness in `h-mad/tests/test_hmad_dispatch_exec.py`):
  - AC-3.1: The stub records its argv. The argv contains `--cwd <cd_dir>`, `--always-approve`,
    `--output-format streaming-json` and `--prompt-file <path>`, and never `-p` or `--single`. The
    file at `<path>` contains the caller's prompt followed by the `_dispatch_boundary` line.
  - AC-3.2: `--model m1 --effort high --sandbox s1` reach the stub as `--model m1`,
    `--reasoning-effort high` and `--sandbox s1`. With none given, none of the three flags appear.
  - AC-3.3: The stub records its environment. It contains no variable whose name matches
    `^CLAUDE`, even when the caller exported `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`,
    `CLAUDE_CODE_SESSION_ID` and `CLAUDE_EFFORT`. `HPW_AGENT_BACKEND` is `claude` when the caller
    left it unset or empty, and `gemini` when the caller exported `gemini`. After the dispatch,
    the wrapper's own shell still carries the caller's `CLAUDE*` variables.
  - AC-3.4: `exec codex` and `exec agy` stubs still receive the caller's `CLAUDE*` variables, and
    `HPW_AGENT_BACKEND` defaults of `codex` and `gemini` respectively. The existing behaviour is
    unchanged.
  - AC-3.5: With a prompt larger than `getconf ARG_MAX`, `exec grok` does not print `OVERSIZE`
    and does not return 2. The stub receives a `--prompt-file` whose size in bytes is at least the
    caller's prompt size.
  - AC-3.6: `exec grok` with no `grok` on PATH returns 2, and stderr contains
    `exec requires the grok CLI on PATH`. `exec gpt` returns 2 and names the valid set
    `codex|agy|grok`.
  - AC-3.7: `exec-pane grok`, `launch grok`, `pin grok <h>`, `verify grok` and `resolve grok`
    keep returning 2 with their existing unknown-agent message. The pane path is out of scope.

### FR-4: Final message and verdict recovery from the grok stream

- **Description**: `exec grok` derives the final message from the dispatch's **own region** of
  `--log`, meaning the lines after the pre-dispatch line count. It uses the same `pre_lines`
  scoping the agy path uses.

  **Segmentation rule (OQ3, as corrected, see Assumptions A1):**
  - Walk the region's lines in order. Skip any line that is not a JSON object.
  - A `text` event appends its `data` string to the current segment.
  - An event whose `type` is `tool_call`, `tool_call_update`, `usage` or `end` closes the current
    segment.
  - Every other type is neither appended nor a closer. That includes `thought`,
    `available_commands`, any unobserved `type`, and events with no `type`.
  - The **final message** is the last non-empty segment.
  - On F0 the segments are ``I'll read `a.txt`, then create `b.txt` with the word "probe".`` and
    `STATUS: DONE`, so the final message is `STATUS: DONE`, beginning at line start.

  **Completion:** a region holding at least one `end` event is complete. A region with none is
  **truncated** (probe finding 4). The outcomes:

  | region state | stdout / `--out` | rc | stderr adds |
  |---|---|---|---|
  | complete, final message non-empty | the final message | grok's rc | `grok stopReason=<v>` (reported, never gated) |
  | complete, no non-empty segment | nothing (EMPTY path) | grok's rc, or 3 if that was 0 | the existing `EMPTY final message` line, plus the tree delta |
  | truncated, last segment carries a verdict (`_recovered_has_verdict`) | the last segment (recovered) | grok's rc, or 3 if that was 0; 124 on watchdog kill | `EMPTY final message`, `TRUNCATED — no end event`, `verdict recovered from log`, the tree delta |
  | truncated, no verdict-carrying segment | nothing | as above | `EMPTY final message`, `TRUNCATED — no end event`, the tree delta |

  - Recovery for grok is **structured only**. The line-oriented `_verdict_after_boundary` fallback
    is not used on a grok log, because a `^STATUS:` anchor can only match non-grok content there.
  - Only `text` deltas ever form a message. `thought` data, tool `rawInput`/`rawOutput`, and
    non-JSON lines never do.
  - On the EMPTY path, stderr also names the last step reached:
    `N tool calls completed; last tool: <toolName> <status>`. This mirrors agy's #77b line, and
    the stderr line is omitted when the region holds no `tool_call`.
    - **N** is the number of distinct `toolCallId`s that have a `tool_call_update` whose
      `status == "completed"`, counted over the **whole region**. It is the same number as
      `scan_grok`'s `ok` (FR-6) on the same lines, and the two must be derived by one rule, not
      two. A `toolCallId` that appears only in a `tool_call`, or whose updates are all `null` or
      another status, does not count.
  - When `--log` was not given, a successful run's auto-log is dumped to stderr as the FR-5 digest,
    never raw, and then removed. This matches the agy path.
- **Acceptance Criteria**:
  - AC-4.1: A stub emitting F0 with rc 0: stdout is exactly `STATUS: DONE` plus a newline, `--out`
    holds the same bytes, rc is 0, and stderr contains `stopReason=end_turn`.
  - AC-4.2: F-BEAT and F-SPACED give the same stdout as F0.
  - AC-4.3: For F-DECOY, stdout is `All done.` and `h_mad_extract_verdict.py <--out file>
    --key STATUS` exits 2 and prints no `STATUS:` value. The `thought`, `rawInput` and
    bare-line decoys are not recovered.
  - AC-4.4: For F-NOTEXT with stub rc 0, rc is 3, stdout is empty, and stderr contains
    `EMPTY final message`.
  - AC-4.5: For F-TRUNC with stub rc 0, rc is 3 and stderr contains `TRUNCATED — no end event`.
    The verdict-carrying last segment `STATUS: DONE` is recovered to stdout and `--out`, and stderr
    contains `verdict recovered from log`.
  - AC-4.6: F-TRUNC with the final `STATUS` segment removed gives rc 3, empty stdout, `--out` not
    written, and stderr naming `2 tool calls completed; last tool: search_replace completed`.
  - AC-4.7 (**scoping**): The caller's `--log` already holds F0, a previous completed dispatch.
    The stub then appends the lines of F-TRUNC with its final `STATUS: DONE` text segment removed.
    Nothing is recovered from the previous dispatch's `STATUS: DONE`, stdout is empty, and rc is 3.
  - AC-4.8: With the stub killed by the watchdog (`--timeout 1`, a stub that sleeps after emitting
    F-TRUNC), rc is 124 and the existing rc-124 line reads `a verdict WAS recovered`.
  - AC-4.9 (**omission clause**): For F-NOTOOLTEXT with stub rc 0, rc is 3, stderr contains
    `EMPTY final message`, and stderr contains **no** `tool calls completed`. This pins "the stderr
    line is omitted when the region holds no `tool_call`": a mutant that emits the line
    unconditionally passes AC-4.6 and fails here. AC-4.6 is its positive pair, because an absence
    assertion alone passes vacuously when the line is never emitted at all.
  - AC-4.10 (**N counts completed, not seen**): F-NOTOOLS with every `text` event removed (its
    `end` survives, so the region is complete and takes the EMPTY path), stub rc 0: rc is 3 and
    stderr contains `0 tool calls completed; last tool: search_replace pending`. The region holds
    2 distinct `toolCallId`s and none completed, so a mutant counting every id prints `2` and
    fails here. The last tool is the `search_replace` `tool_call`, because every
    `tool_call_update` status is `null`. One reading on F0 at the sha256 stated under Fixtures:
    89 lines, 0 completed ids, last non-null-status tool event `search_replace pending`, 1 `end`,
    derived with
    `jq -c 'if .type=="tool_call_update" then .status=null else . end | select(.type!="text")' <F0>`
    and, on that output,
    `jq -s '[.[]|select(.type=="tool_call_update" and .status=="completed")|.toolCallId]|unique|length'`.

### FR-5: `hmad-dispatch progress` learns `grok-ndjson`

- **Description**: `_exec_log_format` returns one of five tokens: `agy-ndjson | grok-ndjson |
  codex-text | empty | missing`.
  - `grok-ndjson` is chosen when any line matches, whitespace-tolerantly, a JSON object whose
    `"type"` value is one of the seven types observed in F0: `thought`, `text`,
    `available_commands`, `tool_call`, `tool_call_update`, `usage`, `end`.
    - The match is **independent of key order**: `{"meta":1,"type":"text","data":"x"}` is a grok
      line exactly as `{"type":"text","data":"x"}` is. The shell detector and the Python
      detector (`scan_grok`'s non-`None` test, FR-6) must return the same answer on every line,
      whatever the key order and whatever the whitespace. How the shell side achieves that is the
      design's choice.
  - **Precedence:** `agy-ndjson` first, then the **codex banner**, then `grok-ndjson`, then
    `codex-text` by default.
    - The codex banner is `^OpenAI Codex v` (the existing `_CODEX_BANNER` in
      `h-mad/scripts/h_mad_audit_cycle.py`) found within the log's head window: `text[:4096]` as
      `measure_effort` reads it today. The shell equivalent reads the first 4096 bytes. The two
      windows differ only when the head holds multi-byte characters, and the banner is ASCII at
      line 1 of a codex transcript.
    - A log carrying agy events therefore renders exactly as today. A codex transcript whose tool
      output echoes grok-typed JSON lines at column 0 stays `codex-text`.
    - This precedence is shared by all three classifiers: this one, the
      `h_mad_review_evidence.py` CLI (FR-6) and `measure_effort` (FR-7).
  - **Residuals:**
    - A grok stream carrying only unobserved `type` values classifies as `codex-text`.
    - A caller-supplied `--log` that holds a prior codex dispatch followed by a grok dispatch
      carries the banner in its head, so it reads as `codex-text` in all three classifiers. That
      log is **skipped** as codex-text is today; it is never falsely gated. FR-4's final-message
      derivation reads the dispatch's own region and does not consult this classifier.

  `_render_progress` renders `grok-ndjson` one line per event, with these exceptions:
  - a `tool_call` renders `tool <toolName> <status>` plus an `rawInput` digest of at most 70
    characters;
  - a `tool_call_update` with a non-null `status` renders `tool <toolName> <status>`, where
    `toolName` is joined from its `tool_call` by `toolCallId` and `?` when unjoinable;
  - `usage` renders `turn usage (<output_tokens> out, <reasoning_tokens> reasoning)`;
  - `end` renders `END stopReason=<v> turns=<num_turns>`;
  - each maximal run of consecutive `thought` events collapses to **at most one** line, and so
    does each run of `text` events;
  - `available_commands` and `null`-status updates render nothing.

  The header is format-agnostic and unchanged: the `format:`, `liveness:` and `lines`/`bytes`
  fields. `progress` still exits 0 in every state.
- **Acceptance Criteria**:
  - AC-5.1: `progress` on F0 prints `format: grok-ndjson`, and F-SPACED does too. A log holding one
    agy `{"event":"init"}` line and F0 prints `format: agy-ndjson`.
  - AC-5.2: `progress --lines 400` on F0 prints **exactly** these per-class counts for the
    listed classes:
    - 2 lines matching `tool read_file|tool search_replace` with status `pending`;
    - 2 lines with status `completed`;
    - 1 `END stopReason=end_turn turns=3` line;
    - 3 `turn usage` lines.

    "Exactly" binds the listed classes only. Beside them, the output MAY carry the collapsed
    `thought` and `text` run lines (at most one per maximal run), plus the unchanged header. No
    output line carries delta text. Because F0's deltas are tokens (36 of its 91 `thought`/`text`
    events have a `data` of 1 to 3 characters, counted with
    `jq -r 'select(.type=="thought" or .type=="text")|.data|length' <F0> | awk '$1<=3' | wc -l`),
    a per-delta substring test cannot be written, so "no delta text" is tested as two
    assertions:
    - no output line, stripped of surrounding whitespace, equals any single `thought` or `text`
      event's `data` stripped the same way, over every event whose stripped `data` is non-empty;
    - neither F0 text segment (``I'll read `a.txt`, then create `b.txt` with the word "probe".``
      and `STATUS: DONE`, FR-4) occurs anywhere in the output.

    The test asserts the four counts with equality and these two absences. It does not assert a
    total line count. **Residual:** a collapsed run line that echoes a fragment of a `thought` run
    shorter than a whole segment and not equal to one delta is not caught.
  - AC-5.2b (**key order**): A log whose single line is `{"meta":1,"type":"text","data":"x"}` gives
    `format: grok-ndjson` from `progress`, and `scan_grok` returns non-`None` on the same text.
    A log whose single line is `{"meta":1,"type":"bogus","data":"x"}` gives `format: codex-text`,
    and `scan_grok` returns `None`. The shell and Python detectors agree on both lines.
  - AC-5.3: The `progress` test suite's existing agy and codex rendering tests pass unchanged.

### FR-6: Tool-call evidence for grok in `h_mad_review_evidence.py`

- **Description**: A new function, `scan_grok(log_text) -> dict | None`, sits beside
  `scan_codex_text`. `scan()` itself is unchanged: it stays agy-only, and its return keys and
  values on every input are identical to today's.

  `scan_grok` returns `None` when the text carries no JSON object whose `type` is one of the seven
  observed types, and the caller must not read that as zero. Otherwise it returns:
  - `tools`: the distinct `toolCallId`s appearing in a `tool_call` or `tool_call_update`;
  - `ok`: the distinct `toolCallId`s with a `tool_call_update` whose `status == "completed"`
    (probe finding 2);
  - `unresolved`: `tools − ok`.
    - This is **not** called `failed`. A failure status has never been observed and its spelling
      is not invented here. Any non-null, non-`completed` status lands in `unresolved`.
  - `thinking`: the sum of `usage.reasoning_tokens` over `usage` events. Non-numeric and boolean
    values are skipped. `end.usage` is not added, because it is the total of the per-turn values.
  - `complete`: whether at least one `end` event is present.
  - `stop_reason`: the last `end.stopReason`, or `None`.

  - `ok` is the same number as FR-4's `N tool calls completed` on the same lines, derived by one
    rule (FR-4).

  The CLI's order follows FR-5's precedence. Agy events present → today's path, byte-identical.
  Otherwise, the codex banner in the head window (FR-5) → today's codex-text path, byte-identical,
  and `scan_grok` is not consulted. Otherwise `scan_grok` is consulted:
  - **complete** → `EVIDENCE: <PASS|NONE> tools=N ok=K unresolved=U thinking=T format=grok` with
    ` stop_reason=<v>` appended when present. PASS iff `ok >= 1`, the same rule as agy. Exit 0.
  - **not complete** → `EVIDENCE: UNREADABLE reason=truncated_no_end`, exit 2, and **no counts**.
    "Could not measure" never takes the branch "measured zero" takes.
  - **`None`** → today's codex-text and unsupported-format path, byte-identical.
- **Acceptance Criteria**:
  - AC-6.1 (**positive control**): On F0 the CLI prints exactly
    `EVIDENCE: PASS tools=2 ok=2 unresolved=0 thinking=121 format=grok stop_reason=end_turn`
    and exits 0.
  - AC-6.2: On F-NOTOOLS it prints `EVIDENCE: NONE tools=2 ok=0 unresolved=2 thinking=121
    format=grok stop_reason=end_turn` and exits 0.
  - AC-6.3: On F-TRUNC it prints `EVIDENCE: UNREADABLE reason=truncated_no_end`, exits 2, and the
    line carries no `tools=`.
  - AC-6.4: A `text` delta whose `data` is the string `"status":"completed"` does not raise `ok`.
    The count is derived from parsed events, never from a substring.
  - AC-6.5: `scan()` on F0 returns `agy_events == 0` and `tools == 0`, as it does today, and every
    existing test in `h-mad/tests/test_h_mad_review_evidence.py` passes unchanged.
  - AC-6.6: The codex-text fixtures used by the existing tests still print their existing
    `CODEXEVIDENCE:` and `EVIDENCE: UNREADABLE reason=unsupported_format` lines, byte for byte.

### FR-7: Grok as an audit-cycle surface

- **Description**: This FR is the audit-leg transport that D2 needs.
  - `hmad-dispatch audit-cycle --surfaces` accepts `grok` beside `agy` and `codex`. The
    unknown-agent message names `agy|codex|grok`.
  - A `grok` pass is dispatched through `_cmd_exec grok` with a per-pass `--log`, exactly as the
    other surfaces are, and the same-surface warning applies unchanged.
  - `h_mad_audit_cycle.py` gains a log **shape** `grok`, with the same shape precedence as FR-5.
    The effort reader computes this order:
    - agy events → `parsed`, as today;
    - else the codex banner in the head window (`_CODEX_BANNER` over `text[:4096]`, the check
      `measure_effort` makes today) → `codex-text`, as today;
    - else, when `scan_grok` returns non-`None` and `complete` → shape `grok`, with `ok`/`tools`
      from `scan_grok`;
    - else, when `scan_grok` is non-`None` but not complete → shape `grok-truncated`;
    - else `unparseable`, as today.
  - The shapes are then scored as follows:
    - `grok` is scored against `DELIVERY_FLOOR` exactly as `parsed` is. That makes a grok leg
      **gateable**, unlike `codex-text`, which is skipped.
    - `grok-truncated` routes to `UNVERIFIED low_evidence_unmeasurable:p<i>`. It is never scored
      as a count.
- **Acceptance Criteria**:
  - AC-7.1: `audit-cycle --surfaces agy,grok` with stub `agy` and `grok` dispatches pass 2 through
    `exec grok` with its own `--log`. `--surfaces agy,gpt` returns 2 naming `agy|codex|grok`.
  - AC-7.2: The combine step on a pass whose log is F0, with `ok=2 <= DELIVERY_FLOOR` and a CLEAN
    report, yields `UNVERIFIED low_evidence:p<i>`. It is scored, not skipped.
  - AC-7.3: The same pass with a derived F0 carrying `DELIVERY_FLOOR + 1` completed tool calls and
    a CLEAN report does not trip the low-evidence floor.
  - AC-7.4: A pass whose log is F-TRUNC yields `UNVERIFIED low_evidence_unmeasurable:p<i>`.
  - AC-7.5: Every existing test in `h-mad/tests/test_h_mad_audit_cycle.py` and
    `h-mad/tests/test_hmad_dispatch_audit_cycle.py` passes unchanged.

### FR-8: `h_mad_assemble_tdd.py --agent codex|grok`

- **Description** (OQ4, binding):
  - The assembler gains `--agent {codex,grok}`, with default `codex`. It does **not** read
    `fallback_agent` from state.
  - `--agent grok` changes the printed command block's dispatch line to `hmad-dispatch exec grok`.
  - It changes the default `--timeout` to **1500** when `--timeout` is not given. That is the
    trial's value; codex's default stays 900. An explicit `--timeout` always wins.
    - "Not given" means `--timeout` is absent from the assembler's argv. It is judged on presence,
      never on value, so an explicit `--timeout 900` under `--agent grok` stays 900.
  - The assembled prompt file is **byte-identical** across agents, because the template is shared
    and unchanged.
  - `--model` and `--effort` are forwarded unchanged. `exec grok` translates them (FR-3).
  - The `--sandbox read-only` HALT is agent-independent, and the `ASSEMBLE-TDD:` token grammar is
    unchanged.
- **Acceptance Criteria**:
  - AC-8.1: With no `--agent`, stdout is byte-identical to the base commit's output for the same
    arguments, and so is the prompt file.
  - AC-8.2: `--agent grok` prints a block whose first line begins
    `hmad-dispatch exec grok ` and contains `--timeout 1500`. `--agent grok --timeout 600`
    contains `--timeout 600`, and `--agent grok --timeout 900` contains `--timeout 900`, never
    `--timeout 1500`. `--agent codex` with no `--timeout` contains `--timeout 900`.
  - AC-8.3: The prompt files written by `--agent codex` and `--agent grok` for identical other
    arguments have equal sha256.
  - AC-8.4: `--agent gpt` exits 2 with argparse's usage error and writes no prompt file.
  - AC-8.5: With `fallback_agent: "grok"` in the project's state and no `--agent`, the block still
    names `exec codex`. That pins that state is not read.

### FR-9: `resolved-model` grok branch

- **Description** (OQ5, binding):
  - `h_mad_resolved_model.py` accepts `grok` as its agent. `hmad-dispatch resolved-model grok`
    passes through to it as it does today.
  - With `--log <f>`, it reads the **last** `end` event in the file. When that event's
    `modelUsage` object has exactly one key, it prints:

    ```
    RESOLVED-MODEL agent=grok model=<key> effort=- resolved=1 source=<f>
    ```

    and exits 0. The `end` event carries no effort, so `effort=-`.
  - Every other case prints `RESOLVED-MODEL: UNKNOWN — <reason>` to stderr and exits 2. It never
    guesses, and there is no config fallback, because no grok config source has been probed. The
    cases are:
    - no `--log`;
    - a missing file;
    - no `end` event;
    - an `end` with no `modelUsage` object, or an empty one;
    - more than one key.
  - `--config` and `--agy-log-dir` are not consulted for grok.
- **Acceptance Criteria**:
  - AC-9.1: `resolved-model grok --log F0` prints `RESOLVED-MODEL agent=grok model=grok-4.7-build
    effort=- resolved=1 source=<F0 path>` and exits 0.
  - AC-9.2: Each of the following exits 2 with `RESOLVED-MODEL: UNKNOWN`:
    - F-TRUNC;
    - F-TWOMODEL, whose message names both keys;
    - no `--log`;
    - a nonexistent path.
  - AC-9.3: F-SHARED resolves from the last `end`, and a derived log whose second dispatch's `end`
    names a different model resolves to that second model.
  - AC-9.4: Every existing test in `h-mad/tests/test_h_mad_resolved_model.py` passes unchanged.

### FR-10: Documentation

- **Description**: Each surface below is located by heading, never by line.
  - `h-mad/SKILL.md` §"Codex authors Phase 5 — enforced, not just instructed" documents
    `fallback_agent` and the FR-2 table. It states that `HMAD_CODEX_UNAVAILABLE` does not override
    `fallback_agent=grok`.
    - It also discloses that grok writes have **no write-time test-first gate**: codex's writes
      pass through `h-mad/hooks/h-mad-codex-tdd-gate.py` and grok's pass through nothing. The
      enforcement that remains is the one named in Out-of-Scope ("A write-time test-first gate
      for grok").
  - §"Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot" documents
    `exec grok` and `--agent grok`, with its 1500 s default.
  - §"Teammate audit leg — when codex is unavailable" documents grok as the **preferred
    independent** stand-in when `codex_status≠available` and `fallback_agent=grok`.
    - It is dispatched with `audit-cycle --surfaces agy,grok`.
    - It replaces the same-family `doc-auditor` gating leg.
    - With `fallback_agent` absent or `claude`, the teammate leg applies exactly as today.
  - §"Never gate on one audit pass" cross-references that routing.
  - `h-mad/references/state-schema.md` documents the field.
  - `h-mad/references/agent-substrate.md` §"Verbs" documents `exec grok`, its argv and its
    environment handling, including the inherited `GROK_SANDBOX` (FR-3).
  - **D4 statement.** The teammate-leg section, and the `exec grok` documentation, each state all
    three of the following:
    - grok's quality is measured only on one RED (HemaSuite #28) and one stream probe; the one
      live `exec grok` smoke before merge is a plumbing check, not a measurement;
    - its GREEN, mutation, wiring and audit precision are unmeasured;
    - the one-codex-round-owed rule applies to grok-gated documents as it does to teammate-gated
      ones.
- **Acceptance Criteria**:
  - AC-10.1: A doc test locates each named heading by its exact text, and the test **fails** when
    a heading is absent. It never skips. Within each section it asserts:
    - in the Phase-5 section: `fallback_agent`, `HMAD_CODEX_UNAVAILABLE` and
      `no write-time test-first gate`;
    - in the exec section: `exec grok` and `--agent grok`;
    - in the teammate section: `--surfaces agy,grok` and `unmeasured`.
    **Residual:** a renamed heading fails the test, and the fix is to update the test's heading
    string in the same commit as the rename.
  - AC-10.2: `h-mad/references/state-schema.md` contains `fallback_agent`, and
    `h-mad/references/agent-substrate.md` contains both `exec grok` and `GROK_SANDBOX`.

### FR-11: Regression — every non-grok path is unchanged

- **Description**: A caller that never names grok and never sets `fallback_agent` observes no
  change:
  - the gate (AC-2.2);
  - `exec codex` and `exec agy` argv, environment, stdout and rc;
  - `progress` on agy and codex logs;
  - `scan()` and the CLI on agy and codex logs;
  - `audit-cycle` with its default or with agy and codex surfaces;
  - the assembler without `--agent`;
  - `resolved-model codex|agy`.
- **Acceptance Criteria**:
  - AC-11.1: The full suite (`pytest h-mad/tests`) passes with every pre-existing test unmodified.
  - AC-11.2: The existing exec tests pass unchanged. These are `test_hmad_dispatch_exec.py`,
    `test_hmad_dispatch_exec_completion.py`, `test_hmad_dispatch_exec_stamp.py` and
    `test_hmad_dispatch_progress.py`. It is the full-suite run that proves this, not a scoped one.
  - AC-11.3 (**codex banner wins**): A log whose first line is a codex banner line beginning
    `OpenAI Codex v`, followed by every line of F0 (so it carries grok-typed lines at column 0,
    including `end`), keeps its codex classification on all three surfaces:
    - `progress` prints `format: codex-text`;
    - the `h_mad_review_evidence.py` CLI prints what today's codex-text path prints for the same
      bytes, and no line containing `format=grok`;
    - `measure_effort` reports shape `codex-text`, never `grok` or `grok-truncated`.

## Non-Functional Requirements

- **Performance**:
  - No new polling process is added; grok rides `_exec_run`'s existing heartbeat.
  - The FR-4 parsers (final message, stop reason, and the `N tool calls completed` line) are
    **region-bounded**, exactly as `_agy_ndjson_response` is: each reads from the dispatch's
    `pre_lines` offset to EOF, with no tail cap. N is counted over the whole region (FR-4).
    **Residual:** a very long single dispatch costs O(region) per parse, and nothing bounds it.
  - FR-5's `progress` rendering is a polling lens, not a dispatch-scoped reader, and takes no
    `pre_lines`. It is bounded as the agy `progress` lens is today, by the last 400 lines of the
    log.
  - Grok latency is unmeasured beyond the one 543 s trial, which is why the assembler default is
    1500 s (FR-8).
- **Security**:
  - `--always-approve` gives grok unrestricted tool execution in `<cd_dir>`. The wrapper applies
    no sandbox profile by default, because none has been probed; an operator's `GROK_SANDBOX` can
    still apply one (FR-3). That is a wider grant than codex's default
    `workspace-write`, the operator accepts it by setting `fallback_agent=grok`, and FR-10
    documents it.
  - The wrapper never reads, logs or forwards `XAI_API_KEY` itself. Grok inherits it from the
    environment.
- **Compatibility**:
  - FR-11.
  - `~/.claude/skills/h-mad` is a symlink into this repository, so the installed skill changes on
    merge.
  - The requirement is grok CLI ≥ 1.0.41, the version the probe and trial ran.
  - `jq` is required on the grok parse paths in `hmad-dispatch.sh`, as it already is for agy.
    Without `jq`, the final message cannot be derived, and the run takes the EMPTY path. It never
    takes a false success.
- **Offline testability**: every AC runs against a stub `grok` or a fixture derived from F0. No AC
  needs network access or `XAI_API_KEY`.

## Out-of-Scope

- **Live measurement (D4).** This covers grok GREEN, mutation-kill, wiring-pin and audit-leg
  precision, cost, quota and latency. It is a separate follow-up feature.
- **The grok pane path.** That is `send`, `ask`, `launch`, `exec-pane`, `pin`, `verify` and
  `resolve` for grok (AC-3.7).
- **A grok 6a-prime reviewer.** `h_mad_archreview_cycle.py` stays agy-only, and a grok log there
  stays `UNREADABLE reason=unsupported_format`.
- **A failed-tool-status branch.** No failure spelling has been observed (probe finding 2), and
  `unresolved` stands in until one is captured.
- **Choosing a grok `--sandbox` profile** (probe finding 5), and scrubbing or defaulting
  `GROK_SANDBOX` (FR-3).
- **A write-time test-first gate for grok.**
  - Codex's writes are gated at write time by `h-mad/hooks/h-mad-codex-tdd-gate.py`, wired
    through Codex's own `hooks.json` (`h-mad/references/codex-runtime.md`). No grok equivalent
    exists in this skill, and whether grok offers any hook surface at all was not probed. A grok
    Phase-5 dispatch therefore writes production code with no write-time test-first gate.
  - The mitigation is what remains mandatory: the RED and GREEN verdicts, the orchestrator's
    independent pytest re-run, and the 5e revert test that establishes GREEN (`h-mad/SKILL.md`,
    "GREEN is established by the revert test").
  - FR-10 discloses the gap in the Phase-5 section.
- **A grok input-size ceiling or refusal detector.** No codex-style `input_too_large` analogue
  exists until a refusal is captured.
- **Completion-event reaping (`--complete-log`) for grok.** No grok linger has been observed.
- **The stray `graft/` directory** seen in the probe workspace (probe finding 6).
  - Tree-delta output for grok is reported, not trusted, until a clean-environment re-probe.
- **Rewording `h-mad/references/codex-implementer-prompt.md`.** It addresses the agent as Codex,
  and grok receives it unchanged, as in the trial.
- **Any change to the `codex_status` enum.** That is D1.

## Assumptions

- **A1: the final message is the last text segment.** The probe document's finding 1, and the
  OQ3 decision derived from it, say to take "text deltas after the last
  `tool_call`/`tool_call_update`/**`usage`** event". That wording is **refuted by F0**.
  - Measured with `jq` over F0's event indices: the last `usage` (index 108) follows the last
    `text` (index 106). Taken literally, that rule yields an empty final message.
  - FR-4's segmentation rule meets the decision's intent: a line-start `STATUS:`, with turn
    boundaries preserved.
  - On F0 it selects the same text as "after the last `tool_call`/`tool_call_update`" does.
- **A2: the probed schema holds.** Grok's `streaming-json` event schema at 1.0.41 is the one F0
  records.
  - A schema change that renames `type`, `data`, `toolCallId`, `status`, `modelUsage` or `end`
    breaks FR-4 to FR-7 and FR-9.
  - The FR-5 residual, and the `None` returns in FR-6, keep that failure a cannot-judge rather
    than a false zero.
- **A3: grok never reaches the hook.** Grok's file writes happen in its own process and never
  reach Claude Code's PreToolUse hook. This is the same premise the gate already relies on for
  codex.
- **A4: `claude` must be on PATH for HPW.** `HPW_AGENT_BACKEND=claude` inside the grok child
  needs `claude` on PATH, because HemaSuite's resolver checks the selected backend with
  `augmented_which`. It held in the trial.

## Version History
- v1.0: Initial specification draft (2026-09-28). The brainstorm's decisions D1–D4 are applied, and so are the orchestrator's decisions on OQ1–OQ5. OQ3's final-message wording is corrected by measurement against F0 (Assumption A1).
- v1.1: Plan-v1.0 owed items, operator-decided (2026-09-28). F0 bullet names the sidecar's Re-derivation commands section and carries the two commands it lacks. AC-2.1b exercises the BLOCK-INVALID class one value at a time (false, true, 0, "null", "", "Grok", {}, []) with a JSON-null FALL-THROUGH control. FR-3 and FR-10 disclose the inherited GROK_SANDBOX. Out-of-Scope adds the missing grok write-time test-first gate, disclosed by FR-10. FR-8 defines not-given as absent from argv, with AC-8.2 pinning an explicit 900.
- v1.2: Plan audit round 2 owed items (2026-09-28): plan.audit.v2.p1 codex must 3 and plan.delta-review.v1.2 must 2 / should 2. New fixture F-NOTOOLTEXT (F0 minus every tool_call, tool_call_update and text event; end survives, 83 lines) and new AC-4.9 pinning the FR-4 omission clause (EMPTY path, no tool calls completed line), with AC-4.6 as its positive pair. FR-10 D4 statement reworded to a QUALITY claim so the plan v1.2 live exec grok plumbing smoke does not falsify it (orchestrator decision); the AC-10.1 needle unmeasured is unchanged.
- v1.3: Design audit cycle 1 owed items, orchestrator-decided (2026-09-28). NFR: the FR-4 parsers are region-bounded like _agy_ndjson_response (pre_lines to EOF, no tail cap, residual O(region)); progress stays bounded like the agy lens. FR-5/FR-6/FR-7: the head-window codex banner takes precedence over grok detection in all three classifiers, with the prior-codex-then-grok --log residual (skipped, never falsely gated) and new AC-11.3. FR-5: grok detection is key-order independent and the shell and Python detectors agree (new AC-5.2b). FR-4: N is distinct toolCallIds with a completed update over the whole region, single-sourced with scan_grok ok (new AC-4.10 on F-NOTOOLS minus text). AC-5.2 exactness binds the listed classes; collapsed run lines may appear without delta text. F-DECOY pins the thought decoy inside the final text segment. AC census 55 to 58 distinct IDs.
