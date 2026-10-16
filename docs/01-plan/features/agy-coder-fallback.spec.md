# Spec — agy as a peer Phase-5 implementer (`agy-coder-fallback`)

> **Slug note.** The slug predates brainstorm v1.1 and is kept because the state record carries it.
> agy is a **peer implementer** with Codex's standing, not a fallback.

Source: `docs/01-plan/features/agy-coder-fallback-brainstorm.md` v1.1 (operator-approved
2026-10-16). Every "currently" claim below was read from the tree at `a8d9ba99`; the command that
read it is named beside it.

## Problem

Codex is the only Phase-5 implementer h-mad accepts. The seams that hard-code it are listed here:

- **State.** `h-mad/scripts/h_mad_state_schema.json` declares `codex_status` and `fallback_agent`
  (`grok|claude|null`) and sets `"additionalProperties": false`. Any new key must therefore be
  declared there, or `h_mad_state_write.py` rejects it. (Read with `cat` on the schema.)
- **Claude-side authorship gate.** `h-mad/hooks/h-mad-tdd-gate.sh` refuses Claude's production write
  as `codex-authorship` when `HMAD_CODEX_UNAVAILABLE` is empty, the state line says
  `codex-escape=no`, and `command -v codex` succeeds. Otherwise it folds `fallback_agent` into
  `fallback-grok` / `fallback-invalid`. (`grep -n 'codex-authorship\|fallback-grok' hooks/h-mad-tdd-gate.sh`.)
- **Single state source.** `h-mad/scripts/h_mad_tdd_judge.py` `read_chain` collects every `step5`
  record on the target's `docs/.bkit-memory.json` chain into `Record(key, codex_status, state_file,
  fallback)`. `format_state_line` prints `TDD-STATE: active codex-escape=… blocker=… records=…
  fallback=… record=…`, and the hook parses that line with `STATE_ACTIVE_RE`. The judge's
  `ESCAPE_STATUSES` is `{"unavailable", "exhausted"}`.
- **Staging.** `h-mad/scripts/h_mad_assemble_tdd.py` accepts `--agent` with `choices=("codex",
  "grok")`. The default timeout is 1500 for grok and 900 otherwise. `command_block` derives a
  non-codex first line from the codex line. The test
  `test_prompt_file_is_agent_independent` pins that the prompt bytes do not depend on `--agent`.
- **Prompt.** `h-mad/references/codex-implementer-prompt.md` opens "You are Codex implementing…"
  and its `Hook:` line names only Codex's and Claude's gates. Because that test pins one prompt
  for every agent, grok is told it is Codex today.
- **Write gate.** `h-mad/hooks/h-mad-codex-tdd-gate.py` speaks Codex's hook contract. Its
  `permissionDecision` deny goes out under `hookSpecificOutput`. agy's contract is
  `{"decision": "deny", "reason": …}` on stdout (`h-mad/references/agy-runtime.md` §"Hooks",
  §"The TDD gate"). No agy gate exists, and that section prescribes the halt
  `step5:agy_tdd_hook_unverified` until one is verified against a real refusal.

## Terms

- **Peer**: `codex` or `agy`. **Fallback**: `fallback_agent`, which is `grok`, `claude`, or
  absent/`null` (equivalent to `claude`).
- **Chosen implementer**: the record's `implementer` field. Absent or `null` reads as `codex`.
- **Resolved implementer**: who actually authors Phase 5 for a record. FR-2 defines it.
- **Active step5**: at least one record on the governing state chain has `phase == "step5"`. This
  is the same predicate both existing gates use.

## Requirements

### FR-1 — State fields

Add to `h_mad_state_schema.json`. Every field is OPTIONAL and additive, so `required` does not
change and records written before this feature stay valid:

| field | values | absent means |
|---|---|---|
| `implementer` | `"codex"` \| `"agy"` \| `null` | `codex` |
| `agy_status` | `"available"` \| `"unavailable"` \| `"exhausted"` \| `null` | `available` |
| `implementer_switch` | object `{from, to, reason, ts}` \| `null` | no switch has happened |
| `review_independence` | array of objects `{leg, module, reviewer, implementer, independent}` | nothing recorded |

- `implementer_switch.from` and `.to` take `codex|agy|grok|claude`. `.reason` takes one of the
  closed set of switch reasons in FR-2. `.ts` is an ISO-8601 timestamp in the RFC 3339
  `date-time` profile (`YYYY-MM-DDTHH:MM:SS[.fraction]` then `Z` or `±HH:MM`), narrowed to
  seconds `00`–`59` (D-14, below). The form the
  writer already emits, `%Y-%m-%dT%H:%M:%SZ` (`h_mad_state_write.py` `_utc_now`), is one instance.
- **An invalid `.ts` is refused on both validator paths.** The store is validated by
  `jsonschema.Draft7Validator` when it imports and by the bundled `_MiniDraft7` in
  `h_mad_state_validate.py` when it does not. Neither enforces `format` today: at `e7730f78`,
  `{"type":"string","format":"date-time"}` accepts `not-a-date` on both (`Draft7Validator(s).is_valid`
  → `True`, `_MiniDraft7(s).is_valid` → `True`). `_MiniDraft7`'s docstring says it ignores
  `format` on purpose, because the production path supplies no format checker. Declaring
  `"format": "date-time"` on `.ts` therefore enforces nothing, and the requirement is the refusal
  itself: a `.ts` that is not an RFC 3339 `date-time` is refused whichever path runs. That covers
  a non-date string, a date with no time (`2026-10-16`), and a calendar-invalid date
  (`2026-02-30T00:00:00Z`).
  - **A leap second is refused too (D-14).** RFC 3339 admits a seconds field of `60`. This spec
    narrows `.ts` to seconds `00`–`59`: a `.ts` whose seconds field is `60`, with or without a
    fraction and whatever its offset, is refused on both paths like any other invalid value.
    Reason: every `.ts` h-mad writes comes from Python `datetime` through the writer
    (`h_mad_state_write.py` `_utc_now` is `datetime.now(timezone.utc).strftime(...)`), and
    `datetime` cannot hold second 60 (`datetime(2016,12,31,23,59,60)` and
    `datetime.fromisoformat('2016-12-31T23:59:60+00:00')` both raise `ValueError: second must be
    in 0..59, not 60`). So the narrowing refuses no value the writer can produce. Residual: a
    hand-supplied `.ts` (for example through `--set`) that names a real leap second is refused,
    and that is intended.
  - **Mechanism: a design obligation.** The design picks one and cites the probe output: extend
    `_MiniDraft7` and its differential corpus; or pass a format checker on the library path and
    match it in the bundled one; or check on the writer side before validation. One hazard binds
    every option that uses the library's format checker. `jsonschema` checks `date-time` only when
    the optional `rfc3339-validator` package imports, and otherwise passes the value silently.
    It imports in `/opt/anaconda3/bin/python3`, where `FORMAT_CHECKER` refuses `not-a-date`.
    Stock `/opt/homebrew/bin/python3` has no `jsonschema` at all, so it takes the bundled path.
    A mechanism that leans on that package must show the refusal with the package absent.
  - **Residual.** Three existing fields already declare `"format": "date-time"`: `started_ts`,
    `owner_heartbeat_ts` and `halt_ts` (`grep -n -B3 '"format"' h-mad/scripts/h_mad_state_schema.json`,
    3 matching lines). They stay annotation-only unless the chosen mechanism is schema-wide. If
    it is, it starts refusing invalid values in those fields too. The design must then run
    `classify_store` over the live state files and report every record that changes class
    before the mechanism ships.
- `review_independence[].leg` takes `5e-review|5e-verify|6a-prime`, and `module` is a string or
  `null`. `reviewer` and `implementer` take `codex|agy|grok|claude`. `independent` is a boolean.
- `h-mad/references/state-schema.md` gains one row per field, with the same value sets.
- **The existing `fallback_agent` description changes on both surfaces that state it.** Its
  `description` in `h_mad_state_schema.json` ("Who covers Phase-5 authoring when Codex is out. The
  field is read only when codex is out: …") and its `state-schema.md` row ("Optional Phase-5
  author when Codex is out.") are both false after FR-3, which reads the field only when **both**
  peers are out for the record. Both are rewritten to the FR-2 condition, so that each names agy
  beside Codex. (`grep -n 'fallback_agent' h-mad/scripts/h_mad_state_schema.json
  h-mad/references/state-schema.md`.)
  - **Pinned literals.** `test_h_mad_state_fallback_agent.py`
    `test_fallback_agent_description_states_the_four_facts` asserts four substrings of the schema
    description: `read only when codex is out`, `are equivalent`, `HMAD_CODEX_UNAVAILABLE does not
    override` and `prose-enforced`. The rewrite either keeps all four (for example "read only when
    codex is out and agy is out too"), or changes the test in the same commit to the new fact.
    The test must never be deleted to make the rewrite pass.
  - **Residual.** The `fallback-grok` refusal text in `h-mad-tdd-gate.sh` says "while codex is
    out". FR-3 keeps it byte-identical. It stays true, because codex is out whenever the refusal
    fires, but it does not mention agy. That is accepted as the price of byte-identity.
- **The existing `codex_status` description changes on both surfaces that state it, for the same
  reason.** Its `description` in `h_mad_state_schema.json` says a production write in step5 "is
  blocked when Codex is available" and that `exhausted`/`unavailable` records that Codex cannot
  author, "permitting Claude to write the fallback". Its `state-schema.md` row says "An unavailable
  or exhausted status permits a Phase-5 authoring fallback". Under FR-2 both are false when agy is
  available: the declaration moves authorship to agy, and FR-3 refuses Claude. Both are rewritten
  so that authorship is stated as FR-2's resolution (Claude only when `resolved` = `claude`). The
  audit-routing half (consumer 2, the teammate leg) is unchanged, per FR-10. (`grep -n
  'codex_status' h-mad/scripts/h_mad_state_schema.json h-mad/references/state-schema.md`.)
  - **Pinned.** No test pins the `codex_status` description text: at `200ffd52`, `git ls-files
    h-mad/tests | xargs grep -l 'permitting Claude to write the fallback\|permits a Phase-5
    authoring fallback\|One switch, both effects\|blocked when Codex is available'` lists 0 files.
    The zero is load-bearing only for this rewrite; a test added later that quotes the text is
    found by re-running the grep. One test pins the property ORDER:
    `test_fallback_agent_description_states_the_four_facts` asserts `fallback_agent`'s index is
    `codex_status`'s index + 1. The FR-1 fields are therefore never inserted between those two.

**Failure modes.** The schema validates only the values that `h_mad_state_write.py` writes. A
hand-edited record can still hold anything, so the judge treats values as follows:
- An `implementer` value outside `{codex, agy, null}` is `invalid` and refuses fail-closed (FR-3).
- An `agy_status` value outside the escape set reads as `available`. This is today's rule for
  `codex_status`, kept for parity. It fails toward refusing Claude, never toward admitting it.
- `implementer_switch` and `review_independence` are read by `h_mad_phase7_preconditions.py`
  only (FR-7). There a malformed entry is reported as the warning `review_independence_malformed`
  and is never read as `independent=true`.

### FR-2 — One resolution function, in the judge

`h_mad_tdd_judge.py` gains a single function that resolves a record. `h-mad-tdd-gate.sh` and the
FR-2 CLI verb both read it, and neither re-derives any part of it. For each record R:

- `codex_avail(R)` = `HMAD_CODEX_UNAVAILABLE` empty ∧ `codex` on `PATH` ∧ `R.codex_status ∉ ESCAPE_STATUSES`
- `agy_avail(R)`   = `HMAD_AGY_UNAVAILABLE` empty ∧ `agy` on `PATH` ∧ `R.agy_status ∉ ESCAPE_STATUSES`
- `chosen(R)` is `R.implementer` (absent/`null` → `codex`), and `other(R)` is the other peer.
- `resolved(R)` = `chosen` if `chosen` is available; otherwise `other` if `other` is available;
  otherwise `R.fallback_agent`, where absent, `null` and `claude` all mean `claude`.

The env-var and PATH evaluation moves from the hook into this function. The judge runs as a child
of the hook and inherits its environment, so the inputs are the same ones the hook reads today.

**Switch reasons (closed set).** A switch happens when the resolved author is not the chosen
peer. The reason is the first unavailability cause of the chosen peer, checked in this order:
`env` (`HMAD_<PEER>_UNAVAILABLE` non-empty), `status` (`<peer>_status` in the escape set),
`cli-absent` (not on `PATH`). The set is closed because these three are the only inputs to
`*_avail`. A new availability input must add a reason here.

**CLI verb.** `python3 h_mad_tdd_judge.py implementer --root <root> --feature <feature> [--record]`
prints exactly one line. Read the token, never `$?`. Its values:

| token | meaning | caller does |
|---|---|---|
| `TDD-IMPLEMENTER: <codex\|agy> chosen=<peer> switch=none` | chosen peer is available | stage `--agent <codex\|agy>` |
| `TDD-IMPLEMENTER: <codex\|agy> chosen=<peer> switch=<peer>-><peer> reason=<env\|status\|cli-absent>` | automatic peer switch | stage the resolved peer; print the line on the dispatch |
| `TDD-IMPLEMENTER: <grok\|claude> chosen=<peer> switch=peers-out reason=<chosen peer's reason>` | both peers out | today's fallback path, unchanged |
| `TDD-IMPLEMENTER: invalid field=<implementer\|fallback_agent> value=<pct-encoded>` | record holds an invalid value | fix the record; never dispatch |
| `TDD-IMPLEMENTER: no-record feature=<pct-encoded>` | no such feature in the state file | halt; the feature name or root is wrong |
| `TDD-IMPLEMENTER: unreadable file=<pct-encoded> error=<name>` | state file cannot be read | halt, same as the gate's unreadable state |

With `--record`, any `switch` other than `none` writes `implementer_switch` to the record through
`h_mad_state_write.py`'s write path, so the claim and session rules apply. The write is skipped
when the stored value already has the same `from`, `to` and `reason`, which keeps re-staging
idempotent. A failed write prints the token with ` record=failed` appended. The caller halts
`step5:implementer_switch_unrecorded`, because a switch that is not in state is exactly the
silent switch the operator decision forbids.

`h_mad_assemble_tdd.py` remains state-independent (`test_state_fallback_agent_is_not_read` stays
green). The orchestrator runs the verb and passes the result as `--agent`.

### FR-3 — Claude-side authorship gate

`h-mad-tdd-gate.sh` folds every `step5` record on the chain, as it does today. Precedence is
first match wins:

1. Any record with an invalid `implementer` refuses as kind **`implementer-invalid`**, naming
   the record's key and file and the `--set implementer=codex|agy|null` remedy.
2. The first record, in chain order, whose `resolved` is a peer refuses as
   **`codex-authorship`** when that peer is `codex` and **`agy-authorship`** when it is `agy`.
   Each message names the dispatch (`hmad-dispatch exec <peer> <promptfile>`), the
   `--set <peer>_status=exhausted` declaration, and the `HMAD_<PEER>_UNAVAILABLE=1` one-off escape.
3. Otherwise, today's `fallback_agent` fold applies unchanged (`fallback-invalid` outranks
   `fallback-grok`; absent/`null`/`claude` everywhere lets Claude proceed to the judge).

**Compatibility, stated exactly.**
- The `codex-authorship` message text is byte-identical to today's.
- The `fallback-grok` and `fallback-invalid` message texts are byte-identical to today's.
- Their trigger conditions change in one deliberate way: they now fire only when **both** peers
  are unavailable for the record (operator decision, 2026-10-16).
- Consequence: on a machine with `agy` on `PATH`, `codex_status=exhausted` used to admit Claude
  or route to grok. It now refuses with `agy-authorship`.
- Existing fixtures that build their own `PATH` without `agy` keep their outcomes. Example:
  `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py` puts `bin_dir:/usr/bin:/bin` on `PATH`, and its
  `codex`-absent assertion runs on that path.

The refusal kinds the gate can emit after this feature are `implementer-invalid`,
`codex-authorship`, `agy-authorship`, `fallback-invalid` and `fallback-grok`, plus the judge's
DENY kinds (the `KINDS` set in `h_mad_tdd_judge.py`, minus `red-measured`). `judge-error` is one
of those DENY kinds. All of them go out in the existing `permissionDecision: deny` JSON form with
exit 0.

The `TDD-STATE:` line is a contract between the judge and the hook. It must carry everything
step 1 and step 2 need, so the hook never reads state or `PATH` itself. Its exact shape is the
design's choice. Every added field gets a closed value set, and an unknown value matches no
alternative of `STATE_ACTIVE_RE`, so it refuses as `judge-error`.

**A field that is missing is not an admitting value.** A line that lacks a field steps 1 or 2
need refuses `judge-error`, like an unknown value. That covers a line in today's shape. It is the
rule the tree already holds for the `fallback=` field:
`test_h_mad_tdd_gate_fallback_agent.py` `test_state_stub_fallback_field_is_judge_error[missing-field]`
asserts `judge-error` for a line that omits it. Reading a missing peer field as "no peer
resolved" would let a judge that stops emitting it admit Claude silently. So the design may not
keep old-shape lines passing by making the new fields optional.

**Consequence for the existing stub-line fixtures (the AC-3.2 exception).** Two gate test files
stub the judge's `state` verb with a `TDD-STATE: active` literal in today's shape:
- `test_h_mad_tdd_gate_judge.py`: the `_tree_b` default `state_line`;
- `test_h_mad_tdd_gate_fallback_agent.py`: the `PREFIX` and `RECORD` constants that its
  `_stub_outcome` lines are built from.

(`git ls-files h-mad/tests | grep 'test_h_mad_tdd_gate_.*\.py$' | xargs grep -l 'TDD-STATE: active'`
finds those two files at `17d73037`.) Under the rule above, those literals would refuse
`judge-error`. So they are re-shaped to the new line. The permitted edit is exactly this: the
text of a string literal that stubs a `TDD-STATE: active` line, plus the minimum code that
composes one, such as a constant that the line is concatenated from. Each re-shaped stub must
carry values for the new fields that reach the outcome the test already asserts. The following
stay byte-identical: every assertion, every expected kind and reason substring, every test name
and every parametrisation id. A test whose asserted outcome cannot be reached by some new-shape
line is a contradiction for the design to report. It is never a licence to change the assertion.

Two other copies of the line are outside AC-3.2, and they follow the line:
- `test_h_mad_tdd_judge.py` `ACTIVE_RE` is a `$`-anchored copy of the grammar. It is updated to
  the new grammar in the same commit, and its existing assertions keep their meaning.
- The mutation rows that quote the line in their `find` or `replace` are re-anchored in the same
  commit, and they gate on `MUTATION: ALL_CAUGHT`.

**Assertions over the real line constrain where new fields go.** Some existing tests run the
real `judge.format_state_line` in-process and assert its output. They are not stubs, so neither
the AC-3.2 exception nor the `ACTIVE_RE` update covers them, and they stay byte-identical:
- in `test_h_mad_tdd_gate_fallback_agent.py` (AC-3.2's byte-identical assertions):
  - `test_format_state_line_emits_the_fallback_fold` asserts the substring
    `" records=1 fallback=grok:1 record="`;
  - `test_fold_outcome_round_trips_through_the_gate_ere` requires `STATE_ACTIVE_RE` to fullmatch
    the real line and its `group(4)` to equal the fold;
- in `test_h_mad_tdd_judge.py`, outside `ACTIVE_RE`:
  - `test_fallback_tag` asserts `line.rsplit(",", 1)[1]` equals the fallback wire tag;
  - `test_state_line_escape_and_blocker` asserts the substring
    `codex-escape=… blocker=… records=N`;
  - `test_state_line_empty_values_encode_as_percent` and `test_state_line_path_with_space_decodes`
    index `line.split(" record=", 1)[1].split(",")` at 0, 1 and 2.

These permit a new-shape line, so FR-3 does not contradict them. They constrain it as follows,
and the design fixes the exact shape inside these limits:
- the header from `codex-escape=` to the first ` record=` stays contiguous. The two substring
  pins cover `codex-escape=… blocker=… records=N` and ` records=1 fallback=grok:1 record=`, so
  no field fits between any two of them. That rules out the slot after `fallback=<fold>` too. The
  only header slot left is between `active ` and `codex-escape=`, and an alternation there adds a
  capture group in front of `group(4)`;
- within a record, the first three comma fields (key, codex status, state file) and the fallback
  tag as the line's last comma token keep their positions. A per-record field between the third
  field and the tag is clear of every pin above;
- `format_state_line` still emits the fallback fold whatever `agy`'s availability is. Both
  `test_h_mad_tdd_gate_fallback_agent.py` tests run with the ambient `PATH`;
- `STATE_ACTIVE_RE` is POSIX ERE (bash `=~`), which has no non-capturing group. So any new
  capture group goes after the fallback capture, or `group(4)` moves.

A design that cannot meet these is a contradiction it must report. It is not a licence to edit
the assertions.

### FR-4 — agy write gate (`h-mad/hooks/h-mad-agy-tdd-gate.py`)

A new PreToolUse handler that speaks agy's contract and reuses the judge (`read_chain`, `judge`)
and the target-identity module that both existing gates use.

**Payload in, decision out.** It reads the camelCase JSON on stdin (`toolCall.name`,
`toolCall.args`, `workspacePaths`, `artifactDirectoryPath`). It prints exactly one JSON object
on stdout, either `{"decision": "allow"}` or `{"decision": "deny", "reason": "<text> kind=<kind>"}`,
and exits 0. An internal exception produces `deny` with `kind=judge-error` whenever the payload
names a tool in classes (b)–(d) below. Stdout that is not JSON blocks nothing in agy, so
**no path may exit without printing**.

**Project root.** The gate is wired per project (FR-5, decision D-2), and agy runs a handler with
its working directory set to the directory that holds `hooks.json`. The root is therefore
`git -C <handler cwd>/.. rev-parse --show-toplevel`, canonicalised the same way the Codex gate
canonicalises its root. `workspacePaths` is a cross-check only. When `workspacePaths` is present
and none of its entries resolves inside the root, the gate denies with `kind=judge-error` during
active step5 and stands down otherwise. This closes the payload-cwd open question: the root never
depends on a payload field.

**Tool classes.** The matcher is `*`, so every tool reaches the gate. While no step5 is active on
the root's state, every tool is allowed. During active step5:

| class | members | rule |
|---|---|---|
| (a) read-only | an explicit allowlist (`view_file`, `list_dir`, `grep_search`, `find_by_name`, `command_status`, …; the design fixes the list) | allow |
| (b) path-write | `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `sed_file`, `notebook_edit` | resolve each target; judge it with the same rules as the Codex gate (production `.py` → test-first judge; test/doc/config paths and the `docs/` first-component rule → allow; out-of-root → deny, except a non-`.py` under `/tmp` and a non-`.py` under the payload's `artifactDirectoryPath`) |
| (c) shell | `run_command` | the Codex gate's shell policy (FR-6) |
| (d) everything else | every tool not in (a)–(c), including tools added in later agy versions | deny, `kind=tool-not-admitted` |

Class (d) closes the class over agy's tool inventory, which is open-ended and changes between
versions. The inventory observed in
`docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log` (the `init.tools`
array) already holds write-capable tools beyond the four that §"Hooks" lists: `sed_file`,
`notebook_edit`, `notebook_execution`, `send_command_input` and `call_mcp_tool`. A matcher written
as a list of names would have missed them.

**Target keys.** `write_to_file` carries its path as `TargetFile`, observed in agy's stream-json
`tool_info.parameters` (`docs/03-analysis/probes/multi-host-runtime/rehearsal/agy-G7-tool-write-then-link-read.log`).
The key in the hook payload's `toolCall.args`, and the keys of the other four path-write tools,
have not been observed. The tracer's payload capture (FR-8 step 1) fixes them. Until then the
rule is fail-closed: a class-(b) tool during active step5 whose args carry no recognised path key
is denied with `kind=judge-error`.

**Hook timeout.** agy's default handler timeout is 30 s
(`~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md`, §"Hook Handler
Fields"). The judge's own budget, `JUDGE_BUDGET_S`, read 40.0 at `a8d9ba99`. The wiring must
therefore set `"timeout"` to at least `JUDGE_BUDGET_S + 20` (60 at that reading). The wiring
check (FR-5) reads `JUDGE_BUDGET_S` from the judge module rather than restating the number, so
the floor moves when the budget does.

### FR-5 — Wiring, and the check that gates on it

- **Where.** In the project's `.agents/hooks.json`, under the hook name `h-mad-agy-tdd-gate`,
  event `PreToolUse`, matcher `*`. The command is
  `python3 ~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py`, where `~` is expanded by
  agy per hooks.md, and the timeout follows FR-4. This mirrors how HemaSuite wires the Codex gate
  in its tracked `.codex/hooks.json`, with a home-relative skill path and no checkout path.
- **Check.** A wiring check prints exactly one line. Read the token, never `$?`. The design names
  the script; extending `h_mad_hook_wiring.py` is preferred.

| token | meaning |
|---|---|
| `AGY-GATE: WIRED` | entry present, matcher `*` or `""`, command names the installed gate, timeout ≥ floor, gate `--self-check` passes |
| `AGY-GATE: UNWIRED reason=<no-hooks-file\|no-entry\|disabled\|matcher-narrow\|bad-command\|timeout-below-floor\|self-check-failed>` | one named defect; the first one found, in this order |
| `AGY-GATE: UNREADABLE file=<pct-encoded> error=<name>` | `hooks.json` is not readable JSON |

- **Enforcement.** `h_mad_assemble_tdd.py --agent agy` runs the check. On anything but `WIRED`,
  it writes no prompt and prints `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified` followed by the
  check's line. The orchestrator then halts `step5:agy_tdd_hook_unverified`, the token
  `agy-runtime.md` §"The TDD gate" already prescribes.
- **Exit codes: a verdict exits 0, and only an operational error exits nonzero.** This follows
  `h-mad/invariants.base.md` §"Audit-gate signal discipline". A nonzero exit registers as a
  tool failure, so it may not carry a normal FAIL. The caller always reads the token, and the
  exit code only says whether a verdict was reached.

  | check line | check exits | assembler prints | assembler exits | kind |
  |---|---|---|---|---|
  | `AGY-GATE: WIRED` | 0 | writes the prompt and prints `ASSEMBLE-TDD: PASS …` | 0 | verdict, pass |
  | `AGY-GATE: UNWIRED reason=<any of the seven>` | 0 | `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified`, then the check line | 0 | verdict, fail |
  | `AGY-GATE: UNREADABLE file=… error=…` | 2 | `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified`, then the check line | 2 | operational: `hooks.json` exists and cannot be read as JSON |
  | no line, or a line with no `AGY-GATE:` token (the check crashed or could not start) | nonzero, or 0 with no token | `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified check=no-token` | 2 | operational |

  - Every `UNWIRED` reason is a verdict, `no-hooks-file` included. The check was able to read
    the project and found the file missing. D-10's residual expects that state in any worktree
    that lacks the file, so it is a normal FAIL. Precedent that goes the other way:
    `h_mad_hook_wiring.py` exits 2 on `WIRING: UNKNOWN reason=no_settings`. The agy check
    differs on purpose, because there a missing file is the defect being reported.
  - `self-check-failed` is a verdict. The gate ran and its self-check failed.
  - In every row the orchestrator's halt is the same, `step5:agy_tdd_hook_unverified`. The exit
    code never changes what the caller does. It only keeps a normal refusal out of the tool-failure
    channel.
  - **Residual.** `h_mad_assemble_tdd.py`'s docstring says "exit 0 on PASS, 2 on any HALT", and
    its existing HALT reasons exit 2. Those reasons are out of scope and keep exit 2. Nobody has
    classified them as verdict or operational, and that is owed to a later feature, not settled
    here. After this feature the docstring's "2 on any HALT" is false, so it is rewritten to say
    that the `agy_tdd_hook_unverified` verdict row exits 0.
- **Residual.** The check is static. It proves the entry exists, not that agy honours it. The
  live proof is the tracer's real refusal (FR-8). If a later agy version changes the contract,
  the check still reads `WIRED` until a live refusal fails, and that is stated in SKILL.md as the
  re-run trigger: re-run the FR-8 refusal step and the FR-8 forced-timeout step after any agy
  upgrade.

### FR-6 — `run_command`: command-shape rule, shared with Codex

During active step5, the agy gate judges `run_command`'s command line (`CommandLine`, the key
shown in hooks.md and observed in
`docs/03-analysis/probes/grok-codex-fallback/plan-audit-v1-p2-agy.log`). It applies the **same
shell policy** as `h-mad-codex-tdd-gate.py`:
- the operator allowance file `.h-mad/phase5-shell-allow`, which the agy gate also refuses to let
  agy write;
- a refusal message that tells agy to use the class-(b) write tools.

There is **one implementation** of the policy. The design moves it to a shared module that both
gates import: the existing `h-mad/scripts/h_mad_target_identity.py`, which the Codex gate already
imports (D-12, operator decision on the design's OQ-A). Below, "the shared module" means that file. The hyphenated hook filename cannot be imported directly, and two copies would
drift. The Codex gate's behaviour is unchanged, and its existing tests pass unmodified.
- **Tests reach the policy through the Codex gate module.** `test_h_mad_codex_tdd_gate_judge.py`
  calls `module._safe_shell_command(...)` on the loaded Codex gate. So after the move, each moved
  name that an existing test reaches must stay bound on the Codex gate module, by import.
  (`grep -n '_safe_shell_command' h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`.)
- **Mutation rows are re-pointed, then green.** Every mutation row whose `file` is
  `h-mad/hooks/h-mad-codex-tdd-gate.py` and whose anchor lies in the moved code is re-pointed to
  the shared module in the same change. Its `find`/`replace` follows the code. Then each spec that
  holds such a row runs `MUTATION: ALL_CAUGHT`.
  - A row left pointing at the old file matches zero times. That reads as
    `step5e:mutation_unverified`, never as caught.
  - Which rows those are is a census over the set the design moves. It is the plan's M-4, and it
    is re-derived once the design fixes that set. It is not restated here.

`send_command_input` (input to a running process) and `notebook_execution` fall in class (d) and
are denied.

**This settles the open question differently from the brainstorm's framing, on purpose.** The
brainstorm offered "a stated residual, parity with Codex's shell". The tree shows Codex's shell is
**not** a stated residual. `_main_guarded` refuses every Bash command outside
`_safe_shell_command` and the operator allowance while step5 is active
(`grep -n 'M:F2-WIRE' hooks/h-mad-codex-tdd-gate.py`). Parity is therefore the command-shape rule.

**Residual, exactly.**
1. Code run by an admitted command: pytest executes test and `conftest` code, and an admitted
   h-mad script runs as itself.
2. Prefixes the operator lists in `.h-mad/phase5-shell-allow`.
3. Tool calls made inside agy subagents, if agy does not fire hooks for them. Class (d) denies
   `invoke_subagent` and `define_subagent` during active step5, so this applies only to a subagent
   already running when step5 arms.
4. Writes by a process that agy started before step5 armed.

The revert test, the independent re-run and the mutation pass still cover all four.

### FR-7 — Non-independent review flag

- **Rule over the axis.** A code-review leg is flagged non-independent when its reviewer agent
  equals the implementer of the code it reviews. The legs are 5e spec review, 5e anti-gaming
  verification and 6a-prime. Phase 3/4/5b audits review documents, not code, and are not legs.
  The rule covers every implementer, Codex included: a Codex reviewer on Codex-written code (for
  example the 5e anti-gaming verifier dispatched to Codex) is flagged exactly as agy on agy is
  (operator decision D-9). The flag is a warning, never a block.
- **Attribution: the implementer is the author of the reviewed code.** An entry's `implementer` is
  the agent whose successful implementation dispatch produced the code the leg reviews, read from
  that dispatch. It is never read from `implementer_switch.to` or from the `implementer` field,
  which record routing, not authorship. `implementer_switch` is historical: Codex out → agy
  dispatched → switch stored; Codex back → Codex dispatched with `switch=none`, and the stored
  `.to` still says `agy`. Attributing from it would mark a Codex reviewer of Codex-written code as
  independent. When the reviewed code came from more than one agent's dispatch, `independent` is
  `false` if the reviewer is any of them, and `implementer` names that agent.
- **Record.** After each leg, the orchestrator adds one `review_independence` entry (FR-1) to the
  record through `h_mad_state_write.py`'s write path, so the claim and session rules apply. No
  verdict word changes, and `h_mad_extract_verdict.py` output is untouched (it prints only
  `<KEY>: <VALUE>`).
  - **The writer has no append today.** `--set KEY=VALUE` JSON-decodes VALUE and replaces the
    whole value (`grep -n '"--set"' -A 6 h-mad/scripts/h_mad_state_write.py`). Adding an entry
    with `--set` is therefore a hand read-modify-write of the whole array, and it drops every
    earlier entry the caller fails to carry.
  - **Requirement.** Adding an entry never removes or alters an existing one. It is validated
    against FR-1 before anything is written. A refused add leaves the store unchanged and prints
    the writer's existing refusal. The design names the mechanism, and this spec does not choose
    it. The preferred mechanism is a writer operation that appends one entry. A read-modify-write
    procedure is acceptable only if it states how it detects an entry lost between the read and
    the write.
  - **Failure the caller sees.** A failed add is a missing record. FR-7's `unrecorded` warning
    surfaces a missing `6a-prime` entry at Phase 7. A missing 5e entry has no warning of its own,
    and that is the stated residual.
- **Surface.** `h_mad_phase7_preconditions.py` emits, as warnings (never blockers):
  - `review_non_independent` for each entry with `independent=false`, naming leg, module and agent;
  - `review_independence_unrecorded` for every implementer (`codex|agy|grok|claude`, the
    `implementer` field and `implementer_switch` alike) when a 6a-prime leg ran — `archreview` is
    `READY_TO_MERGE`, `WITH_FIXES` or `NO` — and there is no `review_independence` entry with
    `leg=6a-prime` (operator decision D-11). "Not recorded" must not read as "independent": without
    the warning, a skipped record would hide a Codex-on-Codex self-review. The other `archreview`
    values already surface on their own and add no `unrecorded` warning: absent or unrecognised is
    the blocker `archreview_not_run`, `SKIPPED_NO_PANE` the blocker `archreview_skipped`, and
    `SKIPPED_OPERATOR_OVERRIDE` the warning `archreview_overridden` — in none of them did a
    6a-prime leg run, so there is nothing to record.
  - **Features that predate this field.** The check applies to every feature whose Phase-7 check
    runs after this ships, with no grandfather rule (D-11). An archived feature is unaffected: the
    only code callers of `h_mad_phase7_preconditions.py` are its own CLI and its tests, so nothing
    re-runs it over closed features. A feature in flight whose 6a-prime ran before the field
    existed reaches Phase 7 with the warning; the orchestrator either adds the missing entry by
    the **Record** mechanism above, from the 6a-prime dispatch log, or carries the warning into the
    report.
  - `review_independence_malformed` per FR-1.

  The CLI prints each one as a `WARNING <code>: …` line, the form it already uses for every
  warning. FR-10 makes the Phase-7 report carry them.

### FR-8 — Live tracer, and the timeout it measures

One real task is staged with `--agent agy` and dispatched headless through
`hmad-dispatch exec agy`. Every reading goes to a committed probe under
`docs/03-analysis/probes/agy-coder-fallback/`, stamped with the sha and with `agy --version`.
- **Version.** This spec fixes no agy version. At `200ffd52`, `agy --version` prints `1.4.0`
  (earlier readings in this feature saw `1.3.6`). Each FR-8 reading stamps the version it ran
  against, and a reading taken under a different version than the gate's other readings is
  re-taken, never carried.
- **When it runs (D-13, operator decision on the design's OQ-B).** FR-8 is a post-merge stage: it
  runs after Phase 7's integrate, against the gate installed from main, and the feature is recorded
  COMPLETE only after the stage passes. Until then the feature is not COMPLETE, and
  `step5:agy_tdd_hook_unverified` stands.

1. **Payload capture.** A temporary capture hook records one real `toolCall` per class-(b) tool
   and per `run_command`. It establishes the arg keys FR-4 leaves open, and whether `workspacePaths`
   is present. The capture hook is removed after use (probe-then-delete), and the probe records
   that it was removed.
2. **Real refusal.** With the operator's real global `~/.gemini/config/hooks.json` loaded (it
   carries the `orca-status` `PreToolUse` `*` hook, which prints `{"decision":"ask"}`), agy is
   told to write a production `.py` with no failing test during active step5.
   - **Pass:** the file does not exist afterwards, and the stream-json log shows the gate's
     reason.
   - This step settles two unknowns: how agy combines a `deny` with a sibling `ask`, and whether
     agy requires workspace trust for `.agents/hooks.json`. It does not settle what agy does when
     a handler times out. An ordinary deny returns well inside the deadline, so no handler times
     out on this step. Step 2a settles that.
   - Until it passes, `step5:agy_tdd_hook_unverified` stands.

2a. **Forced handler timeout.** A temporary delay hook goes in the same project `.agents/hooks.json`
   slot, event `PreToolUse`, matcher `*`. Its `"timeout"` is set to a short value T. It sleeps
   for at least 2T, then prints `{"decision": "deny", "reason": "probe-timeout"}`. The task goes
   through the same transport, `hmad-dispatch exec agy`, and tells agy to write one named non-test
   file under the root. The probe records three readings, each one observed and none inferred
   from the others: whether that file exists afterwards; the wall time from the tool call to
   agy's next event, from the stream-json log; and agy's runtime message for the call. The
   outcome is exactly one of these:

   | outcome | file afterwards | wall time | what it means | what follows |
   |---|---|---|---|---|
   | `timeout-blocks` | absent | ≈ T | agy treats a late handler as a block | the write guarantee holds when the gate overruns its timeout |
   | `timeout-allows` | present | ≈ T | agy proceeds on a late handler (fail-open) | the write guarantee rests on the gate finishing within its timeout. FR-4's floor becomes load-bearing for safety, not only for liveness. This is recorded as a residual in `agy-runtime.md` §"The TDD gate" and raised to the operator as an open question before the gate is called verified. |
   | `timeout-not-enforced` | absent | ≥ 2T | agy waited and honoured the late `deny` | the configured timeout is not a deadline. Record it; FR-4's floor no longer bounds a write's latency. |
   | `session-error` | either | any | agy aborted the call or the session | record the message. The outcome is unclassified and the step is re-run, never read as a pass. |

   - The delay hook is removed after use (probe-then-delete), and the probe records that it was
     removed and that `.agents/hooks.json` is byte-identical to its pre-probe content.
   - The real gate is never slowed for this step. A delay inside `h-mad-agy-tdd-gate.py` would be
     a code path that ships.
   - Until the outcome is recorded, agy's handler-timeout behaviour is **unverified**. No
     document may describe it as settled.
3. **RED then GREEN** on the task.
   - Read `STATUS:` with `h_mad_extract_verdict.py`.
   - Run the independent scoped re-run, the revert test (`git stash push -u`) and the mutation
     pass exactly as for Codex.
   - Check where files landed: every write under the `--cd` root, and no `.py` outside it.
   - The verdict line is a claim. The tree delta and the re-run are the evidence.
4. **Timeout.** Until the tracer runs, `--agent agy` defaults to **1500 s**, the value grok
   uses, because grok is the other implementer whose turn length has not been measured. The tracer
   records the wall time of its RED and of its GREEN dispatch. The default then becomes
   `max(900, 3 × the slower of the two)`, rounded up to a multiple of 60. The derived value names
   its readings in the probe, so a re-measurement moves it. An explicit `--timeout` always wins,
   as it does for grok.

### FR-9 — Implementer-neutral prompt, and the WIRE-PIN new-caller case

- **Neutral.** `h-mad/references/codex-implementer-prompt.md` keeps its filename. 20 tracked files
  under `h-mad/` name it (`git ls-files h-mad | xargs grep -ln 'codex-implementer-prompt'`), and a
  rename is churn this feature does not need. Its text becomes implementer-neutral:
  - the opening line names "the Phase-5 implementer", not Codex;
  - the `Hook:` line names each gate by implementer: Codex → `h-mad-codex-tdd-gate.py`; agy →
    `h-mad-agy-tdd-gate.py`; grok → no write-time gate. For agy it states that the class-(b)
    tools are how writes are made.

  The prompt bytes stay agent-independent, so `test_prompt_file_is_agent_independent` stays green
  and gains `agy`. Residual: the filename still says `codex`.
- **New caller (brief fix 3, #8).** This fix is folded in here because the prompt changes once.
  Today two surfaces call every missing-symbol RED on a `WIRE-PIN` invalid:
  - item 1 of the prompt's "RED acceptance evidence";
  - the paragraph that begins "If the dispatch carries a `WIRE:` / `WIRE-PIN:` line".

  Both target a missing **callee**. When the task **adds a new caller** of a callee that already
  exists at the RED base, the pin's first RED is an `AttributeError`/`ImportError` on the caller.
  That RED is valid (HemaSuite `notebooklm-integration-interface`, analysis F-3: T4 GREEN was
  refused once on a valid RED). The rule written into both surfaces, and into the GREEN variant:
  > A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the
  > task creates, and the callee resolves at the RED base. The RED report must name both. GREEN
  > must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and
  > confirm the pin fails.
  - A missing callee still halts.
  - SKILL.md §"Phase 5 (Implementation) sub-steps", 5d bullet: the halt
    `step5d:red_wrong_reason:<module>` gains the same carve-out, worded identically.
  - `h-mad/references/failure-recovery.md`, the 5d row whose token is
    `step5d:red_wrong_reason:<module>`: its remedy column ("An `ImportError`/`AttributeError`/
    `NameError` RED means the pin tests the callee …") gains the same carve-out, worded
    identically. The token itself is unchanged. `test_h_mad_wiring_task_shape_docs.py` `HALT_TOKENS`
    requires it in both `failure-recovery.md` and SKILL.md.
    (`grep -n 'red_wrong_reason' h-mad/references/failure-recovery.md`.)

  **The surfaces of this rule, closed.** Today the rule "a missing-symbol RED on a `WIRE-PIN` is
  invalid" is stated on five surfaces:
  1. prompt RED item 1;
  2. the prompt's WIRE-PIN paragraph;
  3. the SKILL.md 5d bullet;
  4. the `failure-recovery.md` 5d row;
  5. the wiring-task header that `h-mad/scripts/h_mad_assemble_tdd.py` `assemble()` emits under
     `if shape == "wiring":` ("Its RED must be an assertion about the CALLER's observable
     behaviour, never a missing symbol."). It is written as adjacent Python string literals split
     between `missing ` and `symbol.`.

  The carve-out reaches all five, worded identically, and the prompt's GREEN variant gains it as a
  sixth. In the assembler header the carve-out is appended after the existing sentence, so the
  literal `never a missing` stays.

  **Census method.** A line-oriented `grep` cannot see a phrase that is split across lines.
  Surface 5 was missed that way: its phrase spans two adjacent string literals. The axis is
  "a phrase split across a physical line break", and it has two members in this corpus:
  - Python adjacent string literals. The sweep joins them by reading every `str` constant from
    `ast.parse` (the parser concatenates adjacent literals into one constant).
  - Hard-wrapped markdown. The sweep collapses all whitespace runs to one space before matching.

  The joined reading runs the regex
  `missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError`
  (case-insensitive) over `git ls-files h-mad`: the joined `str` constants of each `.py` file, and
  the whitespace-collapsed text of every other file. (The full sweep adds the line grep and the
  `.py` comment text; see below.) At `9c3b799d` it hits these files:
  - `SKILL.md`, `codex-implementer-prompt.md`, `failure-recovery.md`, `h_mad_assemble_tdd.py`;
  - otherwise only `test_h_mad_agent_definitions.py`, `test_h_mad_wire_pin_gate.py` and the
    fixture log `h-mad/tests/fixtures/codex-text-8-exec.log`. None of those three states the rule.

  The line grep
  `git ls-files h-mad | xargs grep -ln -i 'missing.symbol\|tests the callee\|ImportError.*AttributeError\|AttributeError.*ImportError'`
  hits the same set without `h_mad_assemble_tdd.py`. The pins of each surface are found by
  grepping the surface's own literal, not the regex. Three tests pin literals on these surfaces,
  and the edit keeps those literals:
  - `test_h_mad_agent_definitions.py` `test_implementer_scopes_the_import_error_red_rule_to_wiring_tasks`
    pins item 1's sentences;
  - `HALT_TOKENS` pins the token;
  - `test_h_mad_assemble_tdd.py` `TestWiringShape.test_the_pin_is_told_what_its_red_must_be` pins
    `never a missing` (`git ls-files h-mad | xargs grep -ln "never a missing"` hits only the
    assembler and this test).

  **What the joined reading does not see in a `.py` file, and how the sweep covers it.** `ast.parse`
  yields `str` constants only, so the joined reading is blind to text that is not one. The line
  grep reads that text. So the joined reading is not a superset of the line grep by construction,
  even though it is one at this sha. The axis is "text in a `.py` file that is not a `str` constant".
  It has three members, and each one is handled:
  - **Comments.** The line grep sees a comment on one line. A phrase hard-wrapped across two
    consecutive `#` lines is seen only when the comment text is joined. So the sweep also reads
    each `.py` file's comment tokens (`tokenize`, with the `#` stripped), joined and
    whitespace-collapsed.
  - **A file that `ast.parse` rejects.** It is never skipped silently. The sweep reports it by name
    with a count (`unparsed=N`), its line-grep and comment readings still apply, and a nonzero
    count means the file is read by hand before the sweep counts as clean.
  - **Bytes literals** (`b"…"`) are not `str` constants. The line grep covers them on one line.
    A bytes literal split across lines is the residual of this axis.

  **The sweep is therefore the union** of the line grep over every tracked file and the joined
  reading (the `.py` `str` constants, the joined `.py` comment text, and the whitespace-collapsed
  text of every other file). One measurement at `5f72c2f3` (h-mad last changed at `083a8233`):
  joined reading 7 files, line grep 6 files, line grep minus joined reading 0 files, union
  7 files; comment-token hits 0 files, joined-comment hits 0 files, `unparsed=0`. The comment
  zero is incidental: no comment in `h-mad/` restates the rule today. It is not a property of the
  sweep, and it does not license dropping the comment reading.

  Residual: a later surface that restates the rule is not covered until this sweep is re-run. A
  phrase built at run time (an f-string field, `%`/`.format` interpolation, or a `+` join of names
  rather than literals) is not a `str` constant, so no reading in the sweep sees it.
  Such a surface is found only by reading the code that builds the dispatch text. A bytes literal
  split across lines is the other residual, as stated above.

- **The relaxation is shown to be exactly the intended case (differential corpus).** The carve-out
  makes the 5d RED check accept a RED it used to halt, so `h-mad/invariants.base.md` §"Guard
  narrowing" applies. The rule has no code implementation. At `e7730f78`,
  `git ls-files h-mad | grep -v '\.md$' | xargs grep -ln 'red_wrong_reason\|missing.symbol'`
  hits only two test files (`test_h_mad_wire_pin_gate.py` and `test_h_mad_wiring_task_shape_docs.py`),
  and no script. So the corpus runs over **RED evidence**, not over a function. Each case is
  a fixture repository with a RED base, a WIRE-PIN test and the real pytest RED it produces. The
  four kinds of missing symbol are:

  | case | missing symbol in the RED | callee at the RED base | old verdict | new verdict |
  |---|---|---|---|---|
  | `new-caller` | the caller the task creates | resolves | halt `red_wrong_reason` | **valid** |
  | `missing-callee` | the callee | absent | halt | halt |
  | `both-missing` | the caller the task creates (the callee is also absent) | absent | halt | halt |
  | `unrelated-import` | a symbol the task neither creates nor calls (for example an unrelated module failing to import) | resolves | halt | halt |

  - For each case the probe records the RED's exception line, whether the callee resolves at
    the RED base (shown by importing it at that commit, not by reading the source), and the
    verdict under the old rule text and under the new one. The design names how a verdict is
    derived from rule text: either a classifier function that both texts' prose describes, or a
    stated derivation per case.
  - **Pass:** the set of cases whose verdict changed is exactly `{new-caller}`. Any other member
    is a widening, and it is fixed in the rule text, never in the table.
  - The four rows are one per kind of missing symbol on the RED. The residual axis is the
    exception type: the corpus produces each case's RED as the exception the fixture actually
    raises, and a case whose RED is `NameError` is a fifth fixture only when the new rule's text
    treats `NameError` differently from `ImportError`/`AttributeError`.
- **Incident replay against the real artifacts.** The carve-out was motivated by a real incident,
  so `h-mad/invariants.base.md` §"Incident replay" applies, and the synthetic corpus above does not
  replace the replay. The artifacts are in the HemaSuite checkout (`/Users/kimhawk/orca/HemaSuite`):
  - `docs/archive/2026-10/notebooklm-integration-interface/notebooklm-integration-interface.analysis.md`,
    item **F-3 — WIRE-PIN RED on a new caller (T4/T5/T6 WIRE 2)**. It names the cases and their
    wire-cut evidence: M4.1, M5.1 and the WIRE 2 inline revert;
  - the same directory's `notebooklm-integration-interface.impl-plan.md`, whose WIRE-PIN table
    maps each case to its pin and mutation row;
  - the three pins, each in `hematology-paper-writer/tests/` at its task commit:

    | case | pin (test file `::` test) | task commit (subject locator) |
    |---|---|---|
    | T4 WIRE-PIN 1 | `test_notebooklm_resolver.py::test_resolver_calls_registry_arm_notebook_id_once` | `531a6296b` (`git log --all --oneline --grep='Task 4 FR-1 resolver'`) |
    | T5 WIRE-PIN 1 | `test_notebooklm_initialize.py::test_initialize_entry_point_resolves_through_registry_arm` | `7aa0d9dec` (`--grep='Task 5 FR-5 initialize'`) |
    | T6 WIRE-PIN 2 | `test_notebooklm_status_report.py::test_status_entry_point_resolves_through_registry_arm` | `c2d671f6b` (`--grep='Task 6 CLI surface'`) |

    Each task commit's parent is its RED base. The pin names come from the impl-plan's
    `**WIRE-PIN N**:` lines, and each file was checked with `git show --stat <commit>`.

  **Which form of the pin the replay evaluates.** The committed pins do not share one form:
  - T4 looks the new caller up with two-argument `getattr(integration, "resolve_registry_notebook")`.
    At the RED base this raises `AttributeError`, so the committed pin's RED is a missing symbol.
  - T5 and T6 use the impl-plan's "WIRE-PIN RED scaffold". It is a three-argument
    `getattr(..., None)` (T5: `getattr(integration, "initialize_project_notebook", None)`; T6:
    `getattr(integration.NotebookLMIntegration(), "generate_setup_report", None)`) inside
    `except (Exception, SystemExit)`, followed by an assertion on the spy. Their committed RED is
    an `AssertionError`, which the old rule already accepts.

  So for T5 and T6 the replay evaluates the **direct-call form** of the pin: the scaffold is
  replaced by a two-argument `getattr` on the same name (or a direct call), the `try`/`except` is
  removed, and the spy assertion is unchanged. That is the form whose RED is the missing caller,
  and it is the form the carve-out is about. The replay also records each committed pin's own RED,
  for the record. For T4 the committed pin is already in the direct-call form.

  For each of the three cases, the replay:
  1. reproduces the direct-call form's RED at the RED base, with the pin from the task commit
     (rewritten as above for T5 and T6). The RED must be `AttributeError`/`ImportError` on the
     caller, and the callee must resolve at the RED base (shown by import);
  2. applies the new rule to that RED and records its verdict, which must be **valid**;
  3. records the old rule's verdict on that RED, which must be halt. For T5 and T6 it also records
     the committed scaffolded pin's RED (`AssertionError`) and the old verdict on it, which is
     **valid**: the scaffold is how those tasks avoided the halt;
  4. re-executes the wire-cut at the task commit with the committed pin: delete the call only, keep
     the caller and the callee, and confirm the pin fails. It also locates the original evidence
     (M4.1, M5.1, the WIRE 2 revert) and cites it beside the re-run.

  - The replay is a committed probe under `docs/03-analysis/probes/agy-coder-fallback/`, stamped
    with this repository's sha and the HemaSuite sha it read.
  - A case whose RED does not reproduce, or whose original evidence cannot be located, is recorded
    with the command that failed. It is never dropped from the count.
  - **Residual.** The locators are commit subjects and archive paths. If HemaSuite rewrites
    history or moves the archive, re-locate with `git log --all --grep='notebooklm-integration-interface'`.

### FR-10 — Documentation surfaces

- **SKILL.md** §"Codex authors Phase 5 — enforced, not just instructed" becomes implementer-neutral
  and states FR-2/FR-3. §"Exit-code dispatch for 5d/5e" lists `exec agy` as an implementer
  dispatch beside its review role.
- **`h-mad/references/agy-runtime.md`** §"The TDD gate" names the new gate and FR-5's check, and keeps
  the halt.
- **`h-mad/references/state-schema.md`** gains the FR-1 rows. Its existing `fallback_agent` and
  `codex_status` rows are rewritten, and so are the schema JSON's `fallback_agent` and
  `codex_status` `description`s, all four per FR-1.
- **`h-mad/references/failure-recovery.md`** gets the 5d `red_wrong_reason` row carve-out per
  FR-9.
- **SKILL.md, Phase 7 closure step:** the report carries every `WARNING` line that
  `h_mad_phase7_preconditions.py` prints, the FR-7 warnings included.
- **SKILL.md §"Teammate audit leg — when codex is unavailable"**, the bullet that begins
  `- **It does not license Claude to write Phase 5 production code`. Today it says "but the
  declaration you just made does". Under FR-2 that is false when agy is available: the
  declaration routes the audit leg, but it moves Phase-5 authorship to agy, and FR-3 refuses
  Claude (`agy-authorship`). The rewrite keeps the anchor prefix, which
  `test_h_mad_tdd_gate_docs.py` `_skill_gate_bullet` requires exactly once, and the tokens
  `ACTIVE`, `every`, `unavailable` and `exhausted`, which
  `test_skill_gate_bullet_states_the_every_record_rule` requires. It states two things separately:
  - **Audit-leg selection.** `codex_status` alone routes the 5b audit to the teammate leg.
  - **Resolved authorship.** Claude may write Phase-5 production code only when FR-2's `resolved`
    is `claude` for every ACTIVE `step5` record on the chain. That means both peers are
    unavailable and `fallback_agent` is absent, `null` or `claude`.
  The replaced condition is "the `codex_status` declaration licenses Claude". The new condition is
  "`resolved` = `claude`", and the bullet names `h_mad_tdd_judge.py implementer` as the way to read
  it.
- **Audit legs in Phases 3/4/5b are unchanged.** `codex_status` still routes the second audit
  surface to the teammate leg (SKILL.md §"Teammate audit leg — when codex is unavailable").
  `agy_status` has no audit-routing consumer.

## Acceptance criteria

- **AC-1.1:** The schema accepts each FR-1 field at each listed value and rejects a value outside
  it. A record with none of the fields validates unchanged. The `fallback_agent` description in
  the schema JSON and its `state-schema.md` row state FR-2's both-peers condition. The
  `codex_status` description and row no longer say that an unavailable Codex permits Claude to
  author, and state authorship as FR-2's resolution. `test_h_mad_state_fallback_agent.py` stays
  green. For `implementer_switch.ts`, "the listed value" is FR-1's narrowed profile, leap second
  excluded (D-14); its fixtures are AC-1.2's.
- **AC-1.2:** A record whose `implementer_switch.ts` is `not-a-date`, `2026-10-16`,
  `2026-02-30T00:00:00Z` or the leap second `2016-12-31T23:59:60Z` (D-14) is refused on the library path and, under the test seam that forces it,
  on the bundled path. Each value is its own fixture, run once per path. A `.ts` in the writer's
  form `%Y-%m-%dT%H:%M:%SZ` is accepted on both paths. If the mechanism uses the library's format
  checker, one fixture runs with `rfc3339_validator` made unimportable and still refuses
  `not-a-date`.
- **AC-2.1:** The resolution function: for every combination of {`implementer` absent / `codex` /
  `agy` / invalid} × {`codex_avail`, `agy_avail` ∈ true/false}, `resolved` and `switch` match FR-2.
  Each switch reason is produced by its own fixture, with only that cause present.
- **AC-2.2:** The `implementer` verb prints exactly one line for each of the six token rows, and
  for `record=failed`. `--record` writes `implementer_switch` once and does not rewrite it on an
  identical re-run.
- **AC-3.1:** Each of the five gate-specific refusal kinds is produced by its own fixture. In
  addition, `implementer-invalid` outranks `codex-authorship`, a peer refusal outranks
  `fallback-invalid`, and the chain fold blocks on the FIRST eligible record.
- **AC-3.2:** The `codex-authorship`, `fallback-grok` and `fallback-invalid` message bytes equal
  those at `a8d9ba99`. Every existing `test_h_mad_tdd_gate_*.py` stays green, and the only change
  allowed is FR-3's stub-line exception. In the two files FR-3 names, a string literal that stubs
  a `TDD-STATE: active` line, and the constants it is composed from, are re-shaped to the new
  line. Every assertion, expected kind, reason substring, test name and parametrisation id stays
  byte-identical (checked by diffing the file against `a8d9ba99`). Every other
  `test_h_mad_tdd_gate_*.py` is unmodified. A new fixture shows that a line in today's shape now
  refuses `judge-error`. In `test_h_mad_tdd_judge.py`, `ACTIVE_RE` is the only changed literal, and
  the real-line assertions FR-3 lists stay byte-identical and green (checked by the same diff).
- **AC-4.1:** With step5 inactive, the agy gate allows every tool. With step5 active, it covers:
  - each class with at least one member;
  - an unknown tool name → class (d) deny;
  - a class-(b) payload with no path key → deny;
  - a production `.py` without a failing test → deny, with a judge kind;
  - with a failing test → allow;
  - `/tmp` and `artifactDirectoryPath` non-`.py` → allow, and `.py` there → deny.
- **AC-4.2:** Every exit path prints exactly one JSON object: malformed stdin, an internal
  exception and an unreadable state each still yield parseable stdout.
- **AC-5.1:** The wiring check emits each `UNWIRED` reason from its own fixture. `--agent agy`
  writes no prompt and halts on each of them.
- **AC-5.2:** Each row of FR-5's exit-code table is pinned by its own fixture, and each fixture
  asserts the stdout token and the exit code separately:
  - an `UNWIRED` fixture (one per reason, reusing AC-5.1's) shows check exit 0, and assembler
    `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified` with exit 0;
  - a `hooks.json` holding invalid JSON shows check `UNREADABLE` with exit 2, and the assembler
    HALT with exit 2;
  - a check stubbed to print no token shows the assembler `HALT agy_tdd_hook_unverified check=no-token`
    with exit 2;
  - `WIRED` shows exit 0 on both.

  A mutation that returns 2 on `UNWIRED` is killed.
- **AC-6.1:** The shell policy is imported, not copied: one definition in the tree. The Codex gate's
  existing shell tests pass unmodified. Every mutation row re-pointed under FR-6 runs
  `MUTATION: ALL_CAUGHT` against the shared module, `h_mad_target_identity.py` (D-12). The agy gate refuses each `unsafe` command in the Codex
  gate's `--self-check` list.
- **AC-7.1:** `h_mad_phase7_preconditions.py` emits each of the three FR-7 warnings from its own
  fixture, and none of them moves `ready`. Adding a `review_independence` entry to a record that
  already holds two leaves both earlier entries byte-identical. An entry that fails FR-1 is
  refused, and the store is unchanged.
- **AC-7.2:** `review_independence_unrecorded` fires, with no `leg=6a-prime` entry, for each
  implementer `codex` (field absent included), `agy`, `grok` and `claude`, each from its own
  fixture (`grok` and `claude` through `implementer_switch.to`, the only FR-1 field that takes them), and for each `archreview` value `READY_TO_MERGE`, `WITH_FIXES` and `NO`. It does not fire
  when a `leg=6a-prime` entry exists, nor when `archreview` is absent, `SKIPPED_NO_PANE` or
  `SKIPPED_OPERATOR_OVERRIDE`.
- **AC-8.1:** The probe directory holds the payload capture, the real refusal, and the RED/GREEN
  readings with re-run, revert and mutation results, each stamped with the sha and the
  `agy --version`. The default timeout in `h_mad_assemble_tdd.py` equals FR-8's formula over
  those readings. The readings come from FR-8's post-merge stage (D-13), and the feature is not
  recorded COMPLETE before AC-8.1 and AC-8.2 pass.
- **AC-8.2:** The probe directory holds the forced-handler-timeout reading from FR-8 step 2a,
  stamped with the sha, `agy --version` and the T it used. The reading has three parts: whether
  the file exists, the wall time and agy's message. It names exactly one outcome from step 2a's
  table, and that outcome is consistent with the three readings. It also shows that the delay
  hook was removed and that `.agents/hooks.json` matches its pre-probe bytes. A `session-error`
  outcome does not satisfy this AC. If the outcome is `timeout-allows`, `agy-runtime.md` §"The TDD
  gate" carries the fail-open residual, and the operator question is raised before the gate is
  called verified.
- **AC-9.1:** The prompt contains no implementer-specific opening. `test_prompt_file_is_agent_independent`
  covers `codex`, `grok` and `agy`. The new-caller rule appears in RED item 1, in the WIRE-PIN
  paragraph, in the GREEN variant, in the SKILL.md 5d halt text, in the `failure-recovery.md`
  `step5d:red_wrong_reason:<module>` row and in the wiring-task header that `h_mad_assemble_tdd.py`
  emits. `test_h_mad_wiring_task_shape_docs.py`, `test_h_mad_agent_definitions.py` and
  `test_h_mad_assemble_tdd.py` stay green. FR-9's sweep, re-run on the shipped tree, hits no file
  that states the rule without the carve-out. The sweep is the union FR-9 defines: the line grep
  over every tracked file and the joined reading, which takes in `.py` comment text. The re-run
  reports `unparsed=N`. A nonzero `N` does not satisfy this AC until each unparsed file has been
  read by hand.
- **AC-9.2:** The FR-9 differential corpus runs all four cases (`new-caller`, `missing-callee`,
  `both-missing`, `unrelated-import`) as fixture repositories with real pytest REDs. For each case
  it records the RED's exception line, whether the callee resolves at the RED base (by import) and
  both verdicts. The set of cases whose verdict changed is exactly `{new-caller}`.
- **AC-9.3:** The FR-9 incident replay covers HemaSuite `notebooklm-integration-interface` T4
  WIRE-PIN 1 (`test_notebooklm_resolver.py` at `531a6296b`), T5 WIRE-PIN 1
  (`test_notebooklm_initialize.py` at `7aa0d9dec`) and T6 WIRE-PIN 2
  (`test_notebooklm_status_report.py` at `c2d671f6b`). For each case the committed probe holds:
  - the direct-call form's RED reproduced at the task commit's parent: `AttributeError`/
    `ImportError` on the caller, with the callee resolving by import. For T4 this is the committed
    pin; for T5 and T6 it is the pin with the scaffold replaced, per FR-9;
  - on that RED, the new rule's verdict **valid** and the old rule's verdict halt;
  - for T5 and T6 only, the committed scaffolded pin's RED (`AssertionError`) and the old rule's
    verdict on it, which is valid;
  - a wire-cut re-run at the task commit in which the committed pin fails;
  - a citation of the original evidence (M4.1, M5.1, WIRE 2 revert).

  It is stamped with both repositories' shas. A case that cannot be reproduced is recorded with
  its failing command and counted. It does not satisfy the AC.
- **AC-9.4:** The six copies of the new-caller rule (FR-9 surfaces 1–5 and the GREEN variant) are
  bound to one authority. Either every surface is generated from or checked against one shared
  source, or one test asserts that the carve-out text is equal across all six copies. The plan
  names which mechanism. Whichever it is:
  - **The carve-out text is the whole quoted block in FR-9**, all three sentences: the validity
    condition, "The RED report must name both.", and the wire-cut obligation. A check that binds
    only the first sentence does not meet this AC.
  - **Each copy is read from its own source location.** The span read for one copy contains no
    other copy. Three readings do not meet this AC, because a healthy copy in the same span
    masks a sick one: a contains-check over the whole assembled prompt (the template's copies
    1, 2 and 6 are filled into it beside the header copy); a file-level contains-check over
    `codex-implementer-prompt.md`, which holds three copies; and a file-level check over any
    file that holds more than one copy. The design names each copy's locator. A locator states
    what it does not pin, and the test fails, rather than passing, when a locator matches
    nothing or more than one span.
  - **The control is a mutation of exactly one copy, and it makes the check fail.** It is run
    once per copy, so six times, and once per sentence of the block in at least one copy. Each
    mutation row's `find` is unique in its file, because `h_mad_mutation_harness.py`
    `anchor_status` refuses a `find` that does not occur exactly once. A `find` therefore carries
    copy-specific context, and the `.py` copy's `find` is written against the source bytes,
    including the adjacent-literal split. A row the harness refuses is not a control.
- **AC-X:** Every new guard carries a mutation row that bites (`MUTATION: ALL_CAUGHT` with a `test`
  per row). The full suite passes per task.

## Decisions on the brainstorm's open questions

- **D-1 `run_command`:** command-shape rule shared with Codex (FR-6). Rationale: the tree shows
  that is what Codex parity is.
- **D-2 Hook scope:** per project (`.agents/hooks.json`). Rationale:
  - The Codex gate is wired per project (HemaSuite `.codex/hooks.json`; this repository has no
    `.codex/`).
  - A tracked file reaches every worktree.
  - The handler cwd gives the root without trusting a payload field.
  - No global hook fires in every agy session on the machine.

  Residual: a project without the file has no agy gate. FR-5 turns that into a halt, not a silent
  pass.
- **D-3 Payload cwd:** the root comes from the handler cwd (FR-4), with `workspacePaths` as a
  cross-check.
- **D-4 Timeout:** provisional 1500 s, then FR-8's formula. The hook-handler timeout is a separate
  figure, derived from `JUDGE_BUDGET_S`.
- **D-5 Availability:** CLI on PATH + `agy_status` + `HMAD_AGY_UNAVAILABLE`, symmetric with Codex.
  No liveness probe: the gate runs on every write and must be offline and fast, and a probe spends
  quota. An exhausted agy shows up when the dispatch fails, and the orchestrator records it with
  `--set agy_status=exhausted`.
- **D-6 Project default:** feature record only. A second source doubles the surface the gate
  resolves, and per-feature is the operator decision. A later default can seed the same field at
  `--create`.
- **D-7 Flag location:** a state field (FR-7). It is not on the extracted verdict, because that
  line is `<KEY>: <VALUE>` and its consumers parse it.
- **D-8 Audit legs:** unchanged (FR-10).
- **D-9 Codex reviewing Codex (was OQ-1; operator decision, 2026-10-16):** yes. FR-7's flag fires
  for any `reviewer == implementer`, Codex included, for example the 5e anti-gaming verifier
  dispatched to Codex on a Codex-implemented feature. It is a warning only, never a block.
  Consequence: Codex-implemented features can now carry a `review_non_independent` Phase-7
  warning that has never appeared before.
- **D-10 `.agents/` exclusion (was OQ-2; operator decision, 2026-10-16):** narrow it. Applied in this
  clone by the orchestrator on the operator's answer: the `.git/info/exclude` entry `/.agents/` is now `/.agents/skills/`.
  Evidence at `d65374e9`: `git check-ignore -v .agents/hooks.json` prints nothing (exit 1, not
  ignored), and `git check-ignore -v .agents/skills` still reports the `/.agents/skills/` entry.
  D-2's tracked `.agents/hooks.json` therefore needs no `git add -f`.
  - **Residual / prerequisite.** `.git/info/exclude` is per-clone local configuration and is not
    versioned. Every other clone of this repository, and every other project that adopts the agy
    gate, needs the same narrowing (or a `git add -f`) before its `.agents/hooks.json` can be
    tracked. Linked worktrees share the main clone's `info/exclude` (git's common dir), so they
    inherit the narrowing from the clone they belong to. Where the file is not tracked, FR-5's
    check reads `UNWIRED reason=no-hooks-file` in any worktree that lacks it, so the gap is a halt,
    not a silent pass.
- **D-11 `review_independence_unrecorded` for every implementer (operator decision, 2026-10-16):**
  widened from agy-only to `codex|agy|grok|claude`, matching D-9 (FR-7). Warning only, never a
  block. Rationale: it fires only when the recording step was skipped, so a feature that follows
  the new flow stays quiet; without it, a missing record would hide a Codex-on-Codex self-review,
  which D-9 now flags when it IS recorded.
  - **Pre-existing features — settled, no grandfather rule.** The check applies to every feature
    whose Phase-7 check runs after this ships. Archived features are untouched because nothing
    re-runs the check over them (FR-7). A grandfather rule would need a signal separating "began
    before this shipped" from "skipped the recording step", and the only signal the record offers
    — absence of `review_independence` — is the skip itself, so any such rule would also silence
    the case the warning exists for. A warning on an in-flight feature costs one backfilled entry
    or one report line.
- **D-12 Shared shell-policy module (was the design's OQ-A; operator decision, 2026-10-16):** the
  FR-6 policy moves into the existing `h-mad/scripts/h_mad_target_identity.py`, not a new module.
  The design's reason: `test_h_mad_codex_tdd_gate_judge.py` `test_codex_gate_judge_timeout_reason`
  builds a tree by copying only the Codex gate, a judge stub and `h_mad_target_identity.py`
  (`grep -n -A12 'def test_codex_gate_judge_timeout_reason' h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`),
  so a new module would be missing there, and FR-6 forbids editing that test.
- **D-13 FR-8 timing (was the design's OQ-B; operator decision, 2026-10-16):** FR-8 runs as a
  post-merge stage after Phase 7's integrate, and the feature is recorded COMPLETE only after it.
  Reason: the tracer must run the gate at its installed path, which is main.
- **D-14 Leap-second `.ts` refused (orchestrator decision, design audit cycle 1, 2026-10-16):**
  FR-1 narrows `implementer_switch.ts` to seconds `00`–`59`. Reason: state timestamps are written
  by h-mad's own writer through Python `datetime`, which cannot produce a seconds field of `60`.

## Open questions for the operator

None — OQ-1/OQ-2 settled 2026-10-16; the design's OQ-A/OQ-B settled 2026-10-16 (D-12, D-13).

## Non-goals

- Per-task implementer selection. It can come later on the same field.
- Refusing a peer's production write in that peer's own gate when the other peer is the resolved
  implementer, for example a Codex verifier dispatch writing production code under
  `implementer=agy`. Residual: the test-first judge still applies, and the per-dispatch
  `git status --short` diff (agy-runtime.md §"Author and reviewer roles") is what shows it.
- A write-time gate for grok, and authorship rules for agy as the orchestrating host.
- Routing audit legs by `agy_status`.

## Owed by other documents

None of these are edited by this spec.
- `h-mad/references/agy-runtime.md` says there is no `SessionStart` on two surfaces:
  - §"Hooks" ("There is **no `SessionStart`**");
  - the §"Construct mapping" table's `hook-event` row ("there is no `SessionStart`").

  agy's current hooks.md lists `SessionStart` as a supported event. Both surfaces need a re-check
  against the installed agy (`agy --version` prints 1.4.0 at `200ffd52`), they are corrected
  together, and the correction stamps the version it was checked against.
  (`grep -n 'SessionStart' h-mad/references/agy-runtime.md` at `200ffd52`: 2 matching lines, one
  under each heading.) Residual: this is a content predicate, so a third restatement added later
  is found only by re-running the grep.

## Version History
- v1.0: Initial spec (2026-10-16) from brainstorm v1.1. Settles 8 open questions (D-1..D-8): run_command takes the Codex command-shape rule, not a stated residual; per-project .agents/hooks.json; root from handler cwd; provisional 1500 s timeout then tracer formula; PATH+status+env availability; feature-only implementer; flag in state; audit legs unchanged. Folds brief fix 3 (#8) WIRE-PIN new-caller RED case as FR-9. OQ-1 (Codex-reviews-Codex flag), OQ-2 (.agents exclude) for the operator.
- v1.1: Operator decisions 2026-10-16 (2026-10-16). OQ-1 -> D-9: FR-7 flag fires for any reviewer == implementer, Codex reviewing Codex included; warning only. OQ-2 -> D-10: operator narrowed .git/info/exclude /.agents/ to /.agents/skills/ (check-ignore evidence at d65374e9), no git add -f; per-clone residual stated. Open questions section now empty.
- v1.2: Operator decision 2026-10-16 -> D-11: FR-7 review_independence_unrecorded widened from agy-only to every implementer (codex|agy|grok|claude), matching D-9; warning only. Trigger pinned to a 6a-prime leg that ran (archreview READY_TO_MERGE|WITH_FIXES|NO) with no leg=6a-prime entry; other archreview values already surface. Pre-existing features settled: no grandfather rule, archived features untouched (no batch caller). AC-7.2 added.
- v1.3: Plan-author findings against v1.2 (2026-10-16). FR-3: a missing state-line field refuses judge-error (tree precedent: missing-field fixture), so the two gate stub-line fixtures are re-shaped with assertions byte-identical — the AC-3.2 exception; test_h_mad_tdd_judge.py ACTIVE_RE and line-quoting mutation rows follow the line. FR-7: writer has no append (--set replaces); add-without-loss is a requirement, mechanism a design obligation; AC-7.1 gains the two-entry fixture. FR-6: rows re-pointed to the shared module, then ALL_CAUGHT; moved names stay bound on the Codex gate module. FR-9/AC-9.1/FR-10: failure-recovery.md red_wrong_reason row; rule surfaces closed with sweep. FR-1/FR-10/AC-1.1: fallback_agent description on schema JSON and state-schema.md, pinned literals named. Owed: second SessionStart surface (Construct-mapping hook-event row). All ACs reformatted to the h_mad_ac_census.py grammar (- **AC-n.m:**).
- v1.4: Plan audit cycle 1 findings owned by the spec (2026-10-16). F1 -> FR-5 exit-code table: AGY-GATE WIRED/UNWIRED (all seven reasons, no-hooks-file included) exit 0 and the assembler's agy_tdd_hook_unverified verdict HALT exits 0; UNREADABLE and a no-token check exit 2; existing assembler HALTs keep exit 2 (residual); AC-5.2. F2 -> FR-1: .ts is RFC 3339 date-time; neither validator path enforces format today (probed), so refusal on both paths is the requirement and the mechanism a design obligation; rfc3339-validator hazard; residual for started_ts/owner_heartbeat_ts/halt_ts; AC-1.2. F3 -> FR-9 differential corpus over four missing-symbol cases, changed set == {new-caller}; AC-9.2. F4 -> FR-9 incident replay of HemaSuite notebooklm F-3 (T4/T5 WIRE-PIN 1, T6 WIRE-PIN 2) with wire-cut re-run; AC-9.3. F5 -> FR-8 step 2a forced handler timeout with four classified outcomes; step 2 now settles two unknowns; FR-5 re-run trigger includes it; AC-8.2. F6 -> no contradiction; FR-3 now lists the real-line assertions (two in test_h_mad_tdd_gate_fallback_agent.py, four tests in test_h_mad_tdd_judge.py) as placement constraints; AC-3.2 extended.
- v1.5: Plan audit cycle 2 findings owned by the spec, final corrective revision after the round cap (2026-10-16). B -> FR-10 adds the SKILL.md teammate-audit bullet: audit-leg selection vs resolved authorship (Claude only when resolved=claude), anchor prefix and the four pinned tokens kept. C -> FR-9 surface census gains surface 5, the h_mad_assemble_tdd.py assemble() wiring header (split string literals), and its pin test_h_mad_assemble_tdd.py TestWiringShape.test_the_pin_is_told_what_its_red_must_be; the census method now joins Python adjacent literals via ast and collapses markdown whitespace, measured at 9c3b799d; residual: run-time-built strings. AC-9.1 lists the header. D -> FR-9 replay and AC-9.3 name all three pins with files and commits (531a6296b, 7aa0d9dec, c2d671f6b); T5/T6 replay evaluates the direct-call / two-argument getattr form; the committed scaffolded RED (AssertionError) is recorded as old-verdict valid, correcting the false old-verdict=halt claim. A -> new AC-9.4: the six rule copies bound to one authority, with a per-copy control.
- v1.6: Advisory delta review of plan v1.3 (608e430), spec-owned parts (2026-10-16). Should-fix 3 -> FR-9: the joined reading (ast str constants) is blind to non-str text in a .py file; axis named with three members (comments, files ast.parse rejects, bytes literals). The sweep is now the union of the line grep and the joined reading, which adds joined .py comment tokens; parse failures are reported as unparsed=N and read by hand; residual: run-time-built strings and a bytes literal split across lines. Measured at 5f72c2f3: union 7 files, line-grep-minus-joined 0, comment hits 0 (incidental), unparsed=0. AC-9.1 re-run is the union and reports unparsed=N. Must-fix 1 (spec side) and Should-fix 4 -> AC-9.4: the carve-out text is the whole three-sentence FR-9 block; each copy is read from its own source location, never from the assembled prompt or a file-level contains-check over a file holding more than one copy; a locator matching zero or several spans fails the test; the control mutates exactly one copy, runs once per copy and once per sentence in at least one copy, with a find unique in its file (mutation harness anchor_status), the .py find written against source bytes including the literal split.
- v1.7: Design audit cycle 1, spec-owned items (2026-10-16). S1 (codex C1) -> FR-1/AC-1.1/AC-1.2 + D-14: .ts narrowed to seconds 00-59, a leap second (2016-12-31T23:59:60Z) refused on both paths; reason: every .ts comes from Python datetime via the writer, which cannot hold second 60 (orchestrator decision). S2 (codex C6) -> FR-7 Attribution: an entry's implementer is the author of the reviewed code, from its successful implementation dispatch, never implementer_switch.to (historical) or the implementer field; multi-author code is non-independent if the reviewer is any author. S3 -> FR-1/FR-10/AC-1.1: codex_status schema description and state-schema.md row rewritten to FR-2 authorship (no test pins the text; the fallback_agent-after-codex_status order pin stated); FR-8 Version: 1.4.0 at 200ffd52, each reading stamps its version; Owed SessionStart re-check re-stamped 1.4.0 at 200ffd52; FR-6/AC-6.1 shared module = h_mad_target_identity.py (D-12, OQ-A); FR-8/AC-8.1 post-merge stage, COMPLETE only after it (D-13, OQ-B). Open questions: OQ-A/OQ-B settled.
