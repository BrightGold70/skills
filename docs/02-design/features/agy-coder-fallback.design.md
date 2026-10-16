# Design: agy-coder-fallback

> **Slug note.** The slug predates brainstorm v1.1. agy is a **peer** Phase-5 implementer with
> Codex's standing, not a fallback (spec §"Slug note").

Sources: spec v1.6 (`c853b207`), plan v1.4 (`29ae3e7b`), brainstorm v1.1. Every "currently" claim
below was read from the tree at `29ae3e7b`. `h-mad/` has not changed since `a8d9ba99`
(`git diff --stat a8d9ba99 29ae3e7b -- h-mad | wc -l` prints `0`), so the spec's and plan's
`h-mad/` readings still describe the code this design changes. Code is cited as `path` plus a
symbol, a heading or a content predicate, never a line number.

## Executive Summary

The judge (`h-mad/scripts/h_mad_tdd_judge.py`) gains the one function that decides who authors a
record, and it carries that decision to the Claude hook as a new **per-record** field on the
`TDD-STATE:` line. The hook stops reading `PATH` and the Codex env var itself. The Codex gate's
shell policy, its operator allowance, its phase-5 activity predicate and its production predicate
move into `h-mad/scripts/h_mad_target_identity.py`, the module both existing gates already share,
and both the Codex gate and the new agy gate import them from there. A new
`h-mad/hooks/h-mad-agy-tdd-gate.py` gates agy's tools through a closed classification, so an unknown
tool is denied. `h_mad_hook_wiring.py --agy` prints `AGY-GATE:`, and the assembler halts on
anything but `WIRED`. The state writer gains a locked `--append`. Phase 7 warns on non-independent,
unrecorded and malformed review entries for every implementer. The FR-9 carve-out stays applied by
prose, and one test binds its six copies to one canonical block.

## Overview — the design obligations and where each is settled

| Obligation | Decision | Section |
|---|---|---|
| DO-1 / DO-1a — `TDD-STATE:` shape | a fifth comma field per record, `codex\|agy\|peers-out\|invalid:<pct>`, between the state file and the fallback tag; no header field moves or is added | §"FR-3" |
| DO-2 — read-only allowlist | 11 names, checked against the 58-name `init.tools` inventory | §"FR-4" |
| DO-3 — `review_independence` add | a writer operation, `--append KEY=JSON`, run inside the writer's existing locked read-modify-write | §"FR-7" |
| DO-4 — invalid `.ts` on both paths | a stdlib RFC 3339 predicate in `h_mad_state_validate.py`, applied outside the validator backend, scoped to `implementer_switch.ts` | §"FR-1" |
| DO-5 — the moved names | 17 functions and 8 constants move into `h_mad_target_identity.py`; the Codex gate imports every one of them by name | §"FR-6" |
| DO-6 — installed path vs worktree | no override in code; tests point `HOME` at a fixture; FR-8 runs after the merge to main | §"FR-5", §"FR-8" |
| DO-7 — where the carve-out is applied | it stays applied by prose; the corpus checks the rule's text; one equivalence test with six per-copy locators | §"FR-9" |

Two items need the operator, and they are listed in §"Open questions for the operator": the
FR-6 module placement (OQ-A) and FR-8's post-merge stage (OQ-B). The design is written under the
recommended answer to each.

## Architecture Overview

```
                  docs/.bkit-memory.json (the root's chain)
                                │
             h_mad_tdd_judge.py ── resolve_implementer(record)   (FR-2, the only resolver)
               │        │                 │
     `state` verb   `implementer` verb   in-process: read_chain / judge
               │        │                 │
   TDD-STATE: line   TDD-IMPLEMENTER:     ├── h-mad-codex-tdd-gate.py ──┐
               │        │                 └── h-mad-agy-tdd-gate.py ────┤ both import the
   h-mad-tdd-gate.sh  orchestrator ──► h_mad_assemble_tdd.py --agent    │ gate policy from
   (Claude's writes)                    └─ agy: h_mad_hook_wiring.py --agy
                                                                        │
                                          h_mad_target_identity.py ◄────┘
```

- The judge is the only place `HMAD_CODEX_UNAVAILABLE`, `HMAD_AGY_UNAVAILABLE` and `PATH` are read
  for authorship. It runs as a child of the Claude hook, so it sees the hook's environment.
- The Claude hook parses the line and refuses. It re-derives nothing.
- The agy gate and the Codex gate share one copy of the shell policy, the allowance file rules,
  the phase-5 activity predicate and the production predicate.

## Detailed Design

### FR-1 — state fields, and the timestamp refusal (DO-4)

**Schema.** Four properties are added to `h-mad/scripts/h_mad_state_schema.json`. `required` does
not change, and `additionalProperties` stays `false`. Every construct below is in the bundled
validator's supported set (`_MiniDraft7`'s docstring, the `Deliberately supports ONLY` paragraph):
`type`, `enum`, `required`, `properties`, `additionalProperties`, `items`. No `oneOf`, `anyOf`,
`const` or `pattern` is used, so the two validator paths cannot disagree on structure.

- `implementer`: `enum` `["codex", "agy", null]`.
- `agy_status`: `enum` `["available", "unavailable", "exhausted", null]`.
- `implementer_switch`: `type` `["object", "null"]`. Properties `from` and `to` take `enum`
  `["codex", "agy", "grok", "claude"]`, `reason` takes `enum` `["env", "status", "cli-absent"]`, and
  `ts` is `type` `string` with `"format": "date-time"` as an annotation only. All four are
  `required`, and `additionalProperties` is `false`.
- `review_independence`: `type` `array`. Its `items` is an object with `leg`
  (`enum` `["5e-review", "5e-verify", "6a-prime"]`), `module` (`type` `["string", "null"]`),
  `reviewer` and `implementer` (each `enum` `["codex", "agy", "grok", "claude"]`) and `independent`
  (`type` `boolean`). All five are `required`, and `additionalProperties` is `false`.

**The `.ts` refusal: a predicate outside the validator backend.** The option chosen is the third of
the three the spec lists, placed in the validator module rather than in the writer, so that a
hand-edited record is refused by `h_mad_state_validate.py` too.
- **The probe it rests on.** Reading at `29ae3e7b`, the plan's command
  (`/opt/anaconda3/bin/python3 -B -c '… Draft7Validator(s).is_valid(x) … v._MiniDraft7(s).is_valid(x)'`
  with `s={"type":"string","format":"date-time"}` and `x="not-a-date"`) prints
  `Draft7Validator: True` and `bundled: True`. `format` is enforced on neither path, so declaring it
  refuses nothing.
- **The predicate.** `h_mad_state_validate.py` gains `rfc3339_datetime(value) -> bool`:
  - `re.fullmatch` with `re.ASCII` over
    `([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(\.[0-9]+)?([Zz]|[+-]([0-9]{2}):([0-9]{2}))`;
  - then `datetime.datetime(y, mo, d, h, mi, s)` must construct, which refuses `2026-02-30`;
  - then an offset's hours must be at most 23 and its minutes at most 59;
  - a non-`str` is refused.

  `fullmatch` and `[0-9]` are deliberate: `$` admits a trailing newline, and `\d` admits non-ASCII
  digits. A scratch probe at `29ae3e7b`, since deleted, returned these results under both
  `/opt/anaconda3/bin/python3` (3.11.8) and `/opt/homebrew/bin/python3` (3.15.0):
  - refused: `not-a-date`, `2026-10-16`, `2026-02-30T00:00:00Z`, an offset of `+24:00`, a seconds
    field of 60, a value with
    full-width digits, the writer's form followed by `\n`, `5` and `None`;
  - accepted: `2026-10-16T07:05:09Z` and `2026-10-16T07:05:09.123+09:00`.
- **Where it applies.** A private `_semantic_ok(record)` returns `False` exactly when
  `implementer_switch` is an object whose `ts` fails `rfc3339_datetime`. `classify` calls it first
  and returns `invalid` when it fails, before either schema tier is tried. That runs whichever
  backend `_make_validator` chose, so both paths refuse. The writer refuses through `classify` as it
  does today (`_mutate`: `classify(record) != "strict"`), and it prints its existing refusal.
- **No library format checker is used.** The `rfc3339-validator` hazard therefore does not bind,
  and AC-1.2's package-absent fixture is not owed, since AC-1.2 makes it conditional on that
  mechanism. Recorded for the reader: at `29ae3e7b`, `rfc3339_validator` imports in
  `/opt/anaconda3/bin/python3`, and `/opt/homebrew/bin/python3` has no `jsonschema`.
- **Not schema-wide.** `started_ts`, `owner_heartbeat_ts` and `halt_ts` stay annotation-only, so
  no existing record can change class. The `classify_store` run the spec asks of a schema-wide
  mechanism is not owed. A reading anyway, taken 2026-10-16 with this repository at `29ae3e7b` and
  HemaSuite at `77fb16f51` (both files are untracked, so the sha does not pin their content): this
  repository's `docs/.bkit-memory.json` has 54 records and HemaSuite's has 7. Zero records in either file carry
  any of the four FR-1 keys. That zero is load-bearing, not incidental: the strict schema has
  `additionalProperties: false`, so the writer has refused those keys until now. A hand-edited
  record is the residual.
- **Residual.** RFC 3339 admits a leap second (a seconds field of 60). The predicate refuses it, because
  `datetime` cannot construct it. That fails toward refusal, and the writer never emits it.

**Fixtures (AC-1.2).** One fixture per value per path, with the bundled path forced through the
existing `_FORCE_FALLBACK` seam. Refused: `not-a-date`, `2026-10-16`, `2026-02-30T00:00:00Z`, and
`2026-10-16T00:00:00Zjunk`. The last one kills a `fullmatch` → `match` mutation. Accepted: the
writer's `_utc_now` form. Each alternative of the zone group has its own fixture, run with that
branch alone: `…Z`, `…z`, `…+09:00` accepted, and `…+24:00` refused.

**The `fallback_agent` description, and the same class on `codex_status`.** Spec FR-1 names the
`fallback_agent` description and its `state-schema.md` row. The class is "a surface that says what
an unavailable Codex lets Claude do". It has two more members in the tree:
- the `codex_status` schema `description`, which ends "permitting Claude to write the fallback
  (still test-first)" and "One switch, both effects";
- its `state-schema.md` row, "An unavailable or exhausted status permits a Phase-5 authoring
  fallback".

Both are false once agy is available. All four surfaces are rewritten to the FR-2 condition.
`test_h_mad_state_fallback_agent.py` `test_fallback_agent_description_states_the_four_facts` keeps
its four substrings, for example "read only when codex is out and agy is out too". No test pins the
`codex_status` wording: `git ls-files 'h-mad/tests/*.py' | xargs grep -ln 'permitting Claude\|One switch, both effects'`
prints nothing at `29ae3e7b`. The spec does not list the `codex_status` pair; see §"Owed by other
documents".

### FR-2 — `resolve_implementer` and the `implementer` verb

**Record.** `Record` gains two trailing fields with defaults: `implementer: str = "absent"` and
`agy_status: str = "available"`. The defaults keep every positional four-argument construction
valid. One exists in the tree: the replace text of a `codex_gate_judge_wiring.json` row
(`git ls-files -z h-mad | xargs -0 grep -l 'Record('` → `h_mad_tdd_judge.py` and that spec,
2 files). `_active_records` fills both through two helpers:
- `_implementer_tag(state)` returns `absent`, `null`, `codex`, `agy` or `invalid:<json>`, built like
  `_fallback_tag`;
- `agy_status` is read the way `codex_status` is: `"available"` when the value is `None` or the key
  is absent, else `str(value)`.

**Resolution.** `resolve_implementer(record, env=None, which=None) -> Implementer` is the only
resolver. `env` defaults to `os.environ` and `which` to `shutil.which`. `Implementer` is a
`NamedTuple` with these fields: `resolved` (`codex|agy|grok|claude|invalid`), `chosen`
(`codex|agy`, or `None` when invalid), `reason` (`env|status|cli-absent`, or `None`),
`invalid_field` (`implementer|fallback_agent`, or `None`) and `invalid_value` (the JSON text, or
`""`).
1. An `invalid:` implementer tag gives `resolved="invalid"` and `invalid_field="implementer"`.
2. `chosen` is `agy` for the tag `agy`, else `codex`.
3. `_cause(peer)` returns the first cause in FR-2's order:
   - `env`: `env.get("HMAD_<PEER>_UNAVAILABLE", "") != ""`;
   - `status`: the record's `<peer>_status` is in `ESCAPE_STATUSES`;
   - `cli-absent`: `which(peer)` is `None`.

   It returns `None` when the peer is available.
4. If `chosen` is available it is resolved. Otherwise the other peer is resolved if it is
   available. Otherwise the record's fallback tag decides: `grok` resolves `grok`; `absent`, `null`
   and `claude` resolve `claude`; an invalid tag gives `invalid_field="fallback_agent"`.
   `reason` is `_cause(chosen)` whenever the resolved author is not `chosen`.

`shutil.which` replaces the hook's `command -v codex`. The equivalence is checked by the existing
differential `test_h_mad_tdd_gate_fallback_agent.py` `test_absent_null_claude_match_the_base_hook`,
which compares the current hook's bytes with the hook at `8ef6009f` over the PATH × env × status
matrix. Residual: that matrix holds only the PATH forms the test builds. Other forms, such as an
empty `PATH` element or a non-executable `codex` file, are not compared.

**The `implementer` verb.** It is a new `implementer` subparser in `main`, with `--root`,
`--feature` and `--record`. It has no `--target`. It reads `<root>/docs/.bkit-memory.json` through
`_state_at`, so it has the same reader and the same error names as the chain. It looks up
`orchestrator_state[feature]` **whatever its phase**, because staging must not depend on the record
already being in `step5`. Exactly one line is printed:

| condition | line |
|---|---|
| file absent, or the key absent | `TDD-IMPLEMENTER: no-record feature=<pct>` |
| `_state_at` gives `unreadable`, or the record is not an object | `TDD-IMPLEMENTER: unreadable file=<pct> error=<name>` (`not-an-object` for the second) |
| `invalid_field` is set | `TDD-IMPLEMENTER: invalid field=<field> value=<pct>` |
| `resolved == chosen` | `TDD-IMPLEMENTER: <resolved> chosen=<chosen> switch=none` |
| a peer switch | `TDD-IMPLEMENTER: <resolved> chosen=<chosen> switch=<chosen>-><resolved> reason=<reason>` |
| peers out | `TDD-IMPLEMENTER: <grok\|claude> chosen=<chosen> switch=peers-out reason=<reason>` |

`<pct>` is the judge's existing `_enc`. With `--record`, any switch other than `none` calls
`h_mad_state_write.merge_fields(state_file, feature, {"implementer_switch": {...}})` with
`from=chosen`, `to=resolved`, `reason` and `ts=_utc_now()`. That is the same write path `--set`
uses. The write is skipped when the stored value has the same `from`, `to` and `reason`. A
`StateWriteError` or an `OSError` appends ` record=failed` to the line. The verb always exits 0
after printing a line, and the caller reads the token.

Residual: the verb reads the root's own state file. The gate folds the whole chain from the target
up to the root. A nested sub-project state file that holds a record with the same key is read by
the gate and not by the verb.

### FR-3 — the `TDD-STATE:` line (DO-1, DO-1a) and the hook's fold

**The shape.** Each record gains a fifth comma field, the **author field**, between the state file
and the fallback tag. The header does not change.

```
TDD-STATE: active codex-escape=<yes|no> blocker=<N> records=<N> fallback=<fold> record=<key>,<codex_status>,<state_file>,<author>,<fallback_tag> …
```

- `<author>` is one of `codex`, `agy`, `peers-out` or `invalid:<pct-json>`. `format_state_line`
  computes it per record through `resolve_implementer`, evaluating `env` and `which` once per call.
  `codex` and `agy` mean that peer is resolved. `invalid:` means the record's `implementer` is
  invalid. `peers-out` means both peers are out, and the fallback tag then decides.
- The new `STATE_ACTIVE_RE`, which is the one literal in `h-mad/hooks/h-mad-tdd-gate.sh` matching
  `^STATE_ACTIVE_RE='(.*)'$`:

  ```
  ^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) records=([1-9][0-9]*) fallback=(none|(grok|invalid):([1-9][0-9]*))( record=[^ ,]+,[^ ,]+,[^ ,]+,(codex|agy|peers-out|invalid:[^ ,]+),(absent|null|grok|claude|invalid:[^ ,]+))+$
  ```

  The new capture group follows `group(4)`, and groups 1 to 6, which the hook reads, keep their
  numbers. No group before it changes, and the grammar uses no construct that Python `re` and POSIX
  ERE read differently.

**P-1..P-5 hold, checked against candidate lines.** A scratch probe at `29ae3e7b`, since deleted,
built lines in this shape. It matched each one with Python `re.fullmatch` and with `[[ =~ ]]` under
both `/bin/bash` 3.2.57, the hook's shebang, and Homebrew bash 5.3:
- P-1: the header is unchanged, so ` records=1 fallback=grok:1 record=` stays contiguous.
- P-2: Python and both bash versions gave the same groups 1, 2, 3, 4 and 6 on a grok fold, an agy
  record and an invalid-implementer record, and `group(4)` equalled the fold.
- P-3: the fallback tag is still the last comma token.
- P-4: the header is unchanged.
- P-5: fields 0, 1 and 2 after the first ` record=` are still the key, the status and the file.

A today-shape line, and a line whose author field is `grok`, matched neither engine. So a missing
or unknown author field refuses `judge-error`, which is the rule FR-3 requires.

**Why the author field's value is right whatever `PATH` holds.** P-1 and P-2 run in-process with
the ambient `PATH`, where `agy` resolves (`which agy` → `/Users/kimhawk/.local/bin/agy` at
`29ae3e7b`). Neither assertion reads the author field, and the grammar admits all four values, so
both stay byte-identical and green. The `fallback=` fold is still computed over the records alone
(`_fallback_fold` is untouched).

**The hook.** `_read_state` keeps its header checks unchanged: the record count, escape against
blocker, and both range checks. `codex-escape=` and `blocker=` are no longer decision inputs. They
stay because P-4 pins them and because they still check the line's integrity. In the record loop,
the author field is taken by stripping three leading fields (`${rest#*,}` three times, then `%%,*`).
The key (`%%,*`), the file (the third field) and the tag (`##*,`) are read exactly as P-5 needs.
The loop sets two values:
- `INVALID_RECORD`: the first record whose author starts with `invalid:`;
- `PEER_RECORD` and `PEER`: the first record whose author is `codex` or `agy`.

The `BLOCKER_RECORD` capture, which only the old authorship block read, is removed. After
`_read_state --target`, the block that tested `HMAD_CODEX_UNAVAILABLE`, `ESCAPE` and
`command -v codex` is replaced by FR-3's precedence:
1. **`INVALID_RECORD` set → `implementer-invalid`.** The text is new:
   `implementer=$VALUE is not valid (valid: codex|agy|null) — refusing the write, fail-closed.` and
   then ``  Fix it: python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $KEY --set implementer=codex|agy|null "$FILE"``.
   `$VALUE` is the decoded JSON.
2. **`PEER_RECORD` set → `codex-authorship` or `agy-authorship`.** The `codex-authorship` text is
   the current literal, byte for byte. Only the variables it interpolates are renamed, from
   `BLOCKER_KEY`/`BLOCKER_FILE` to `PEER_KEY`/`PEER_FILE`, so the rendered bytes for a given record
   are unchanged. The `agy-authorship` text is new and mirrors it. It names
   `hmad-dispatch exec agy <promptfile>` with `h_mad_assemble_tdd.py --agent agy`, the
   `--set agy_status=exhausted` command for `$PEER_KEY`/`$PEER_FILE`,
   `export HMAD_AGY_UNAVAILABLE=1 for a one-off`, and `h_mad_tdd_judge.py implementer` as the way to
   see who resolves.
3. **Otherwise, the existing `fallback_agent` block runs unchanged**, including the `M:F1`
   tag-agreement check. It is reached only when every record's author is `peers-out`, which is
   FR-3's "both peers out" condition. The comment above it,
   `codex-authorship has already refused every case where codex is available`, is rewritten to
   name both peers.

**Fixture consequence (AC-3.2).** Two literals are re-shaped, and nothing else in either file
changes:
- `test_h_mad_tdd_gate_judge.py` `_tree_b`: the default `state_line` gains `,peers-out` before
  `,absent`;
- `test_h_mad_tdd_gate_fallback_agent.py` `RECORD`: it becomes
  `" record=feat,exhausted,/x/docs/.bkit-memory.json,peers-out,"`.

`test_h_mad_tdd_judge.py` `ACTIVE_RE` becomes the grammar above. The new fixture is a today-shape
line → `judge-error`.

**No gate test is unreachable.** This was checked by enumerating the stub sites at `29ae3e7b`:
- `_tree_b(` matches 9 lines in `test_h_mad_tdd_gate_judge.py`, one `def` and 8 call sites. One of
  the 8 passes its own `state_line`, whose lines are none of them `TDD-STATE: active`.
- `_stub_outcome(` matches 6 lines in `test_h_mad_tdd_gate_fallback_agent.py`, one `def` and 5 call
  sites.

Every one reaches its asserted outcome with author `peers-out`:
- the judge-verb stubs reach the judge exactly as today;
- `missing-field`, `unknown-kind` and `position-zero` still fail the grammar on their header;
- the range check and the tag-agreement check still run, because `peers-out` reaches step 3.

The real-judge gate tests build `PATH` as `<bin_dir>:/usr/bin:/bin` (`_gate`'s `path_tail`), with
no `agy`, so their outcomes are FR-2's codex-only outcomes. So no contradiction is reported here.

**Mutation rows that follow the line (R-1).** At `29ae3e7b`:
- 56 rows name the hook and 36 name the judge;
- M-3's pattern matches 8 rows in 3 specs (`claude_gate_judge_wiring.json` 5,
  `tdd_judge_chain.json` 2, `tdd_gate_fallback_agent.json` 1), which reproduces the plan's figure;
- 13 rows anchor inside the regions this design rewrites. In the hook that is 8: 7 in `_read_state`
  and 1 in the authorship block. In the judge it is 5: 1 in `_active_records` and 4 in
  `format_state_line`.

The re-anchoring Task reads every row of both files, not only these, because the regions above are
a proxy. The census is owed as a committed probe (§"Measurements").

### FR-6 — the shared gate policy (DO-5)

**Placement: `h-mad/scripts/h_mad_target_identity.py`, not a new module. This is OQ-A.** The tree
holds hand-built trees that copy the Codex gate beside a stub judge and the identity module, and
nothing else:
- `test_h_mad_codex_tdd_gate_judge.py` `test_codex_gate_judge_timeout_reason` expects
  `kind=judge-timeout` there;
- the same file's `judge-error` parametrisation builds one with no identity module.

A scratch probe at `29ae3e7b`, run in a temporary directory that was then removed, rebuilt the
first of those trees twice:
- with the gate unmodified, the gate printed a `permissionDecision` deny;
- with one top-level `from h_mad_gate_policy import _safe_shell_command` added, it exited 1 with
  `ModuleNotFoundError` and printed nothing.

So a **new** module that the gate imports breaks a test that FR-6 says passes unmodified. The
identity module is in that tree already, as a copy of the live file, so the move keeps the test
green. It also keeps the spec's letter: a shared module, imported by both gates. The cost is
cohesion. The module's docstring, `Canonical filesystem identity shared by the H-MAD TDD gates.`,
is widened to say that it also holds the policy both write gates apply.

**The moved set.** It is 25 names, each moved byte for byte except where noted.
- The 10 functions of `_safe_shell_command`'s call closure, re-derived with `ast` at `29ae3e7b` as
  the plan's M-4 does: `_contained_venv_executable`, `_cwd_escapes_root`, `_load_judge`,
  `_option_value`, `_path_within`, `_payload_cwd_base`, `_safe_argv`, `_safe_hmad_script`,
  `_safe_shell_command` and `_trusted_executable`.
- 7 more functions the agy gate needs, so that none of them is copied:
  - the operator allowance: `_shell_allowance`, `_operator_allowed`, `_is_shell_allowance`, and
    `_read_regular_text`, which `_shell_allowance` reads through;
  - the phase-5 activity predicate: `_state_status` and `_any_phase5_status`;
  - the production predicate: `_is_production_python`. Its `_load_identity().fold_py_suffix` call
    becomes a direct call to the module's own `fold_py_suffix`, the one non-verbatim edit.
- The 8 module constants that those functions read: `SIMPLE_SHELL_COMMAND`, `READ_ONLY_COMMANDS`,
  `SAFE_DISPATCH_VERBS`, `SAFE_HMAD_SCRIPT_OPTIONS`, `TEMP_OUTPUT_OPTIONS`, `SHELL_ALLOW_FILE`,
  `TRUSTED_BIN_DIRS` and `MALFORMED_WORKDIR`.

Not moved: `_load_identity`, which loads this very module; `_relative_target`, `_tmp_report_target`
and `_command_cwd`, which are Codex-payload specific (see the binding rule); `_main_guarded`'s
composition of safe-command → allowance → operator check, which carries the Codex-specific refusal
text and the `M:F2-WIRE` and `M:SA-WIRE` anchors; and the self-check's `unsafe` tuple in `main`.

The moved functions' `Path(__file__).resolve().parents[1]` still names `h-mad/`, because
`scripts/` and `hooks/` are siblings. So `hmad-dispatch` and the scripts root resolve as before.

**Binding.** The Codex gate inserts its `scripts` directory into `sys.path`, as `_load_judge`
already does, and imports all 25 names by name at module level, inside
`try: … except Exception as exc: _POLICY_IMPORT_ERROR = exc`. `main` then denies with
`kind=judge-error` before `_main_guarded` whenever `_POLICY_IMPORT_ERROR` is set. That keeps the
`judge-error` B-tree's expected token and gives a missing module a deny instead of a crash. The
guard gets a mutation row and a fixture: the gate copied without the identity module still prints
one deny. Of the moved names, an existing test reaches these four through the Codex gate module, and
binding all 25 covers them:
- `_safe_shell_command`: `test_h_mad_codex_tdd_gate_judge.py` calls `module._safe_shell_command`;
- `_payload_cwd_base`: the same file monkeypatches it on the module, then calls
  `module._relative_target`. `_relative_target` stays in the Codex gate, so it reads the patched
  binding;
- `SIMPLE_SHELL_COMMAND`: read from `runpy.run_path(...)` globals, in the same file;
- `SAFE_HMAD_SCRIPT_OPTIONS`: read as `hook.SAFE_HMAD_SCRIPT_OPTIONS` in `test_h_mad_codex_runtime.py`.

The four were found with `grep -l "\b<name>\b"` over `git ls-files 'h-mad/tests/*.py'`, once per
moved name. Residual: a test that builds a name at run time is not found by that grep.

**Rows re-pointed (R-3, AC-6.1).** At `29ae3e7b`, 62 rows name the Codex gate. A row is counted when
its `find` starts inside a moved definition's span. 31 rows qualify, in 4 specs:
`codex_gate_judge_wiring.json` 21, `codex_gate_shell_allowance.json` 6,
`assemble_tdd_mutation_rows.json` 2 and `tdd_gate_differential.json` 2. 0 anchors are absent and 0
are non-unique. The plan's 19, which is the 10-function closure alone, is a subset. The 12 added
rows come from the allowance functions, `_read_regular_text`, `SAFE_HMAD_SCRIPT_OPTIONS` and
`_is_production_python`. Each re-pointed row's `file` becomes `h_mad_target_identity.py` under
`h-mad/scripts/` (written relative to `h-mad/`, as every row's `file` is),
and each spec holding one is gated on `MUTATION: ALL_CAUGHT`.
- **The identity module's own rows are rechecked too.** Adding the moved code can make one of the
  module's existing `find` strings occur twice, and the harness then refuses it. The move Task runs
  the anchor precheck over every spec naming that file.
- **AC-6.1's "one definition".** A test asserts that each of the 17 moved functions has exactly one
  `def` across `git ls-files h-mad`.

### FR-4 — the agy write gate (DO-2)

**File and contract.** `h-mad/hooks/h-mad-agy-tdd-gate.py` reads stdin and prints exactly one JSON
object, `{"decision": "allow"}` or `{"decision": "deny", "reason": "<text> kind=<kind>"}`, then
exits 0. `main` builds the decision inside one `try` and prints from a `finally` that emits a
`judge-error` deny if nothing was decided. The judge, the identity module and the policy are
imported inside that `try`. So a failed import still yields JSON (AC-4.2).

**The order of evaluation.**
1. Parse stdin, read with a 2 s bound like the Claude hook's `READER` (the Codex gate's `_payload`
   calls `json.load(sys.stdin)` unbounded). `toolCall.name` must be a `str`, matched exactly and
   case-sensitively.
2. **Class (a) is allowed before any state is read.** Class (a) is allowed whether or not step5 is
   active, so no state read can change its answer.
3. **The root.** It is `git -C <handler cwd>/.. rev-parse --show-toplevel`, canonicalised with the
   identity module's `canonical_directory`.
4. **Activity.** `_any_phase5_status(root)` decides, the same predicate the Codex gate uses for a
   tool with no target. `inactive` allows. `unknown`, a root that cannot be resolved, or a malformed
   payload denies `kind=judge-error`.
5. **The `workspacePaths` cross-check.** When it is a list and no entry resolves inside the root,
   the gate denies `kind=judge-error`.
6. **Classes (b), (c) and (d)**, as below. An exception anywhere after step 2 denies
   `kind=judge-error`.

**Class (a), the read-only allowlist: 11 names.** `view_file`, `list_dir`, `grep_search`,
`find_by_name`, `command_status`, `read_url_content`, `search_web`, `ask_question`, `finish`,
`wait` and `wait_5_seconds`.
- **The rule over the class.** A tool is in (a) only if it appears in a recorded `init.tools`
  inventory, and only if it writes nothing to the filesystem, starts no process, and drives no
  other agent, MCP server or browser.
- `finish` and the two waits are included because denying them leaves a headless agy unable to
  end or pace its turn, and they touch nothing.
- **Inventory.** The `init.tools` array of
  `docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log` holds 58 distinct
  names (parsed as the first `init` event's `tools`, at `29ae3e7b`). All 11 are in it.
- **That log carries no agy version.** Its `init` object has only `cwd`, `tools` and
  `permission_mode`. The installed agy now reports `1.4.0`, while the spec and plan read `1.3.6`.
  So the inventory is re-taken, with `agy --version`, by FR-8 step 1 (§"FR-8").
- **Residual.** Membership is judged from the tool's name and agy's documentation, not observed. A
  tool whose name reads as read-only but which writes would be admitted. The 11 names are the whole
  exposure, and egress over the network is outside this gate.

**Class (b), path-write: 5 names.** `write_to_file`, `replace_file_content`,
`multi_replace_file_content`, `sed_file` and `notebook_edit`.
- **Path keys.** A per-tool table, `PATH_KEYS`, holds only observed keys. At `29ae3e7b` it holds
  `write_to_file` → `TargetFile`. That key was seen in stream-json `tool_info.parameters` in 4
  committed logs under `docs/03-analysis/probes/multi-host-runtime/rehearsal/`
  (`agy-G7-tool-write-then-link-read.log`, `agy-L3-unmapped-tool.log`, `agy-L9-no-step-index.log`,
  `agy-L11-duplicate-index.log`), and never in a hook payload.
- **Fail-closed.** A class-(b) call whose `args` carry no key from its table entry is denied
  `kind=judge-error`. That covers the other four tools until FR-8 step 1 records their keys.
- **Judging a target.** Each recognised key's value is judged:
  - it is canonicalised with `canonicalise(str(root), raw, str(root))`. agy sends no payload cwd,
    so the base is the root;
  - an unresolvable identity denies `judge-error`;
  - a write to the allowance file denies, through `_is_shell_allowance`;
  - inside the root, `_is_production_python(relative)` decides. Production `.py` goes to
    `read_chain(root, absolute)` and `judge(...)`, and a non-ALLOW denies with the judge's kind.
    Everything else is allowed, which includes tests, `docs/` as the first component, and every
    non-`.py` file;
  - outside the root, the write is allowed only when the name is not `.py` after `fold_py_suffix`
    and the resolved path is within `/tmp` or within the payload's `artifactDirectoryPath`, both by
    `_path_within`. Everything else is denied.

**Class (c): `run_command`.** The command is `args.CommandLine`; a missing or non-`str` value denies.
- **The command's directory.** It is `args.Cwd` when that is a non-empty `str` (observed beside
  `CommandLine` in 4 of 630 stream-json `run_command` parameter objects across the committed
  probes, counted as objects, not distinct calls). It is
  `MALFORMED_WORKDIR` when `Cwd` is present but not a `str`, and the root when `Cwd` is absent.
- **Why the gate changes directory first.** `_safe_argv` resolves a relative script against
  `Path.cwd()`, and agy runs a handler in the directory that holds `hooks.json`. So the gate
  changes its own working directory to the command's directory before judging. A failed change
  denies `judge-error`.
- **The composition is the Codex gate's**, reading the shared names: `_safe_shell_command`, then
  `_shell_allowance` (a `str` result denies), then `_operator_allowed`. The refusal tells agy to use
  the class-(b) tools, and names `SHELL_ALLOW_FILE`.
- **Residual.** This six-line composition is the one piece of policy written in both gates. It
  carries different refusal text, and each copy has its own mutation rows. A differential test pins
  them equal: a corpus of commands × allowance-file states, judged by both gates, with the same
  admit/deny in every cell.

**Class (d): everything else → deny, `kind=tool-not-admitted`.** At the inventory above that is
41 names: `ask_custom_permission`, `ask_permission`, `browser_click_element`,
`browser_drag_pixel_to_pixel`, `browser_get_dom`, `browser_get_network_request`, `browser_input`,
`browser_list_network_requests`, `browser_mouse_down`, `browser_mouse_up`, `browser_move_mouse`,
`browser_press_key`, `browser_refresh_page`, `browser_resize_window`, `browser_scroll`,
`browser_scroll_dom`, `browser_select_option`, `browser_subagent`, `call_mcp_tool`,
`capture_browser_console_logs`, `capture_browser_screenshot`, `click_browser_pixel`,
`define_subagent`, `delete_knowledge`, `execute_browser_javascript`, `generate_image`,
`invoke_subagent`, `list_browser_pages`, `list_permissions`, `list_resources`, `manage_inbox`,
`manage_subagents`, `manage_task`, `notebook_execution`, `open_browser_url`, `read_browser_page`,
`read_resource`, `run_workflow`, `schedule`, `send_command_input` and `send_message`. The 41 are
58 − 11 − 5 − 1, derived as a set difference over the parsed inventory. Any name absent from the
inventory, which includes tools added later, also falls here.

**`--self-check`.** It prints `AGY-TDD-GATE: PASS`, or `AGY-TDD-GATE: FAIL <what>` with a nonzero
exit. It checks four things: the classifier puts `view_file` in (a) and `call_mcp_tool` in (d);
`_safe_shell_command` refuses `python3 -c "open('x','w').write('x')"`; the policy names import; and
`JUDGE_BUDGET_S` is readable. AC-6.1's parity with the Codex list is a test, not this self-check.
The test locates the `unsafe` tuple assigned inside the Codex gate's `main` with `ast`, requires
exactly one, and asserts that the agy gate refuses each member.

**Overwrite residual.** agy merges handlers, and a sibling's `overwrite` is a shallow merge into the
tool's arguments (hooks.md §"PreToolUse Contract"). The gate judges the arguments it receives. A
sibling that rewrites a path key after this gate judged it is not seen. At `29ae3e7b` the operator's
global `~/.gemini/config/hooks.json` holds one `PreToolUse` group, `orca-status` with matcher `*`,
whose script prints `{"decision":"ask"}` for `PreToolUse` and never `overwrite`.

**Roles.** The gate cannot tell an implementing agy from a reviewing agy. During active step5, a
5e-review agy in a wired project is therefore held to the same tool and shell rules, as a Codex
verifier is today. 6a-prime runs after step5 ends, so it is unaffected.

**Inherited residual.** The gate decides "active" from the root's own state, as both existing gates
do. `docs/.bkit-memory.json` is untracked in this repository and in HemaSuite
(`git ls-files docs/.bkit-memory.json` prints nothing in either at `29ae3e7b`). How Phase 5c
provisions state inside a worktree was not read for this design, so whether the three gates stand
down in a worktree is not claimed either way.

**Hook timeout.** The floor is `math.ceil(JUDGE_BUDGET_S + 20)`, read from the module. At
`29ae3e7b` `JUDGE_BUDGET_S` is `40.0`, so the floor is 60.

### FR-5 — the wiring check, the assembler, and the worktree (DO-6)

**The check.** `h_mad_hook_wiring.py` gains `--agy`. It calls a new `check_agy(project_root)`,
prints the one line that function returns, and exits with the code beside it. Without `--agy`,
behaviour is unchanged. The reasons are evaluated in FR-5's order, and the first one found is
printed:
1. `<root>/.agents/hooks.json` is absent → `UNWIRED reason=no-hooks-file`, exit 0. When it is
   present but not JSON, or not a JSON object, the line is `UNREADABLE file=<pct> error=<name>`
   with exit 2, and the name is `not-an-object` for the second case.
2. There is no top-level key `h-mad-agy-tdd-gate`, or its value is not an object → `no-entry`.
3. `enabled` is present and is not `true` → `disabled`.
4. No `PreToolUse` group has a `matcher` of exactly `*` or `""` → `matcher-narrow`. An absent or
   empty `PreToolUse` counts here too.
5. No handler in such a group has a `command` whose `shlex.split` equals
   `["python3", "~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py"]` → `bad-command`.
6. That handler's `timeout` is not an `int` ≥ the floor; an absent timeout means agy's default of
   30 → `timeout-below-floor`.
7. `<python3 on PATH> <expanduser(path)> --self-check` must exit 0 and print exactly
   `AGY-TDD-GATE: PASS`, within 30 s. Otherwise → `self-check-failed`. When it passes, the line is
   `AGY-GATE: WIRED`.

Residual: an equivalent spelling of the command (an absolute path, `$HOME`) reads `bad-command`.
That fails toward the halt.

**The assembler.** `--agent` gains `agy`, and the timeout default becomes a table,
`{"codex": 900, "grok": 1500, "agy": 1500}`, with `--timeout` still winning. For `--agent agy`,
`main` runs the check before `assemble`, as a subprocess:
`[sys.executable, AGY_WIRING_CHECK, "--agy", "--project-root", <root>]`, with a 60 s bound.
`AGY_WIRING_CHECK` is a module constant and the tests' seam. Then FR-5's table applies:
- `WIRED` → continue to PASS;
- `UNWIRED` → print `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified`, then the check line indented by
  two spaces, as existing HALT details are. Write no prompt, exit 0;
- `UNREADABLE` → the same two lines, exit 2;
- no `AGY-GATE:` line, or a timeout → `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified check=no-token`,
  exit 2.

The verdict branch does not raise `Halt`, because every `Halt` exits 2. The module docstring's
`exit 0 on PASS, 2 on any HALT` becomes: `exit 0 on PASS and on HALT agy_tdd_hook_unverified after
AGY-GATE: UNWIRED; 2 on every other HALT`. A test pins that sentence, and a test pins that the old
one is absent. `command_block`'s existing prefix rewrite already emits `hmad-dispatch exec agy`, and
`exec agy` accepts `--model`, `--effort` and `--timeout` (`hmad-dispatch.sh` `_cmd_exec`).

**DO-6: no override path in code.**
- **Tests.** Tests of `check_agy` set `HOME` to a fixture directory holding
  `.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py` as a symlink to the gate under test.
  `os.path.expanduser` honours `HOME`, so the shipped code has no worktree switch.
- **This feature's own Phase-5 worktree.** It ships no `.agents/hooks.json`, so `--agent agy` there
  reads `no-hooks-file` and halts. That is correct: this feature's implementer is Codex.
- **An adopting project's worktree.** Its tracked `.agents/hooks.json` reaches the worktree, and
  the installed path is the skills repository's main checkout. So the check reads `WIRED` once this
  feature has merged.
- **This repository's own `.agents/hooks.json`** is committed only by FR-8's post-merge stage, and
  only after its real refusal passes (§"FR-8"). Until then the halt stands here mechanically,
  because the file is absent. Evidence that tracking it needs no `git add -f`: at `29ae3e7b`,
  `.git/info/exclude` holds `/.agents/skills/`, and `git check-ignore -v .agents/hooks.json` prints
  nothing.

### FR-7 — the `review_independence` add (DO-3) and the Phase-7 warnings

**The add.** `h_mad_state_write.py` gains `--append KEY=JSON`, which is repeatable.
- **Strict decoding.** `json.loads` with no string fallback. A decode failure prints `ERROR: …`
  and exits 2, and the store is unchanged.
- **One write.** `--set` fields and `--append` entries apply inside **one** `_mutate` call:
  `record = {**prior, **fields}`, then each appended key becomes `list(prior_value) + [entry]`.
  The prior list is copied, never mutated in place.
- **Refusals.** An existing value that is present and is not a list is refused
  (`cannot append to a non-array value`). The result is validated by `classify`, so FR-1's item
  schema applies on both validator paths. A refusal raises before `_atomic_write` and prints the
  writer's existing `ERROR:` refusal with exit 2.
- **Heartbeat.** An owner's `--session-id` refreshes the heartbeat, as `merge_fields` does.
- **Output.** The `STATE-WRITE: OK` line lists the appended keys with the set keys.
- **Lost-entry detection is not needed, and that is why this mechanism was chosen.** `_mutate`
  holds `fcntl.flock` on the sidecar lock across load, apply and write, so no other writer that
  goes through `_mutate` can interleave between the read and the write. Residual: a writer that
  bypasses `_mutate`, such as a hand edit or another tool's raw write, can still race. That is true
  of every field.
- **The orchestrator's step (SKILL.md, FR-10).** After each 5e-review, 5e-verify and 6a-prime leg,
  it runs `--append review_independence='{"leg":…,"module":…,"reviewer":…,"implementer":…,"independent":…}'`.
  `implementer` is the resolved author of the reviewed code (`implementer_switch.to`, else
  `implementer`, else `codex`), and `independent` is `reviewer != implementer`. This applies for
  every implementer.

**The warnings.** `h_mad_phase7_preconditions.py` `check` calls a new
`_review_independence_warnings(record)` and extends `warnings`. It never touches `blockers`, so
`ready` does not move.
- **Well-formed means validated by the schema, not by a second copy of the value sets.**
  `h_mad_state_validate.py` gains `property_valid(name, value)`, which validates `value` against the
  strict schema's `properties[name]` through `_make_validator`, on both paths. For
  `implementer_switch` it also applies `rfc3339_datetime` to `ts`. An entry is well-formed when
  `property_valid("review_independence", [entry])` holds **and** `entry["independent"] ==
  (entry["reviewer"] != entry["implementer"])`. A boolean that contradicts its own two agents is
  malformed, so it is never read as `independent=true`.
- **`review_independence_malformed`** is emitted for each entry that is not well-formed, and once
  when the field is present and not a list.
- **`review_non_independent`** is emitted for each well-formed entry with `independent=false`,
  naming the leg, the module and the agent.
- **`review_independence_unrecorded`** is emitted when `record.get("archreview")` is in
  `{"READY_TO_MERGE", "WITH_FIXES", "NO"}` and no **well-formed** entry has `leg == "6a-prime"`.
  - The code path has no implementer condition (D-11). The implementer appears only in the detail
    text: `implementer_switch.to` when that object is well-formed, else `implementer`, else
    `codex`.
  - A malformed 6a-prime entry does not count as recorded, so it raises both warnings.
- Each warning prints through the existing `  WARNING <code>: <detail>` loop in `main`.

### FR-8 — the tracer, after the merge (DO-6, R-2) — OQ-B

**Why after the merge.** The tracer needs agy to run the gate at the installed path,
`~/.gemini/config/skills/h-mad/` → `/Users/kimhawk/orca/skills/h-mad`
(`ls -la ~/.gemini/config/skills` at `29ae3e7b`). That path is main, and main gains the gate only
when this feature merges. An override flag would ship a code path that points the check away from
the installed gate. A hand edit of the symlink would also change every live session.

**The stage.** It runs after Phase 7's integrate and before the feature is recorded COMPLETE.
1. **A fixture project.** It is a throwaway git repository with one module task. It has its own
   `docs/.bkit-memory.json` step5 record and its own `.agents/hooks.json`, holding FR-5's exact
   entry. It is created beside this checkout, never under `/tmp`, because agy's trust decision for
   `.agents/hooks.json` may depend on location.
2. **Step 1, payload capture.** The real class-(b) payload keys are recorded, and so is
   `init.tools` with `agy --version`. They land as one commit on main that fills `PATH_KEYS` and
   re-checks the class-(a) inventory. That commit carries tests built from the captured payloads,
   written RED then GREEN, and it lands before step 2. The capture hook is then deleted.
3. **Steps 2, 2a and 3** in the fixture project, as FR-8 states them. Step 2a's delay hook is
   added to, and removed from, the fixture's `hooks.json`, and the before and after
   `shasum -a 256` are recorded.
4. **This repository's adoption.** `.agents/hooks.json` is committed here, and step 2 is re-run
   once in this repository to settle trust at this location.
5. The derived timeout replaces `agy`'s `1500` in the assembler table, as FR-8's formula sets.

Every reading is stamped with the sha and `agy --version` under
`docs/03-analysis/probes/agy-coder-fallback/`.

**AC-8.1's formula check is a probe check, not a suite test.** A committed script asserts that the
assembler's `agy` default equals `max(900, 3 × slower)` rounded up to a multiple of 60 over the
readings it names. A suite test that read a probe file would break when the probe directory is
archived.

### FR-9 — the carve-out stays prose; the corpus, the replay, and AC-9.4 (DO-7)

**Applied by prose.** The verdict needs two facts: which symbol the task creates, and whether the
callee resolves at the RED base. The `WIRE:` value is free text: `h_mad_wire_pin_gate.py`
`_parse_tasks` returns it as one unparsed string (probed at `29ae3e7b` on a sample task, where a
`WIRE:` line naming two dotted symbols came back as a single `wire` string). So a mechanical classifier
would have to guess the caller and the callee from prose. The orchestrator therefore keeps applying the rule at 5d from the RED report, which
must name both. **Residual:** the corpus shows that the rule's **text** selects exactly
`{new-caller}`. It does not show that any one 5d application follows the text.

**The canonical block.** It is held once, as `CANONICAL` in the equivalence test, and it equals
spec FR-9's quoted block. It was extracted at `29ae3e7b` by joining the `>` lines and collapsing
whitespace:

> A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task
> creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove
> the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin
> fails.

**Placement of each copy.** Each copy is appended after an existing sentence, so every pinned
literal stays. Each of the context sentences below occurs exactly once in its file at `29ae3e7b`
(Python `str.count`):
1. Prompt RED item 1, after `Say which case each failing test is.`
2. The prompt's WIRE-PIN paragraph, after `report that and stop rather than accepting it.`
3. The SKILL.md 5d bullet, after ``halt `step5d:red_wrong_reason:<module>`.``
4. The `failure-recovery.md` 5d row, inside the remedy cell's quotes, after
   `only the failure mode can.`
5. `h_mad_assemble_tdd.py` `assemble()`, inside the wiring branch's `lines.append(...)` that holds
   `The WIRE-PIN is this task's single load-bearing test.` The existing literal `"symbol."` becomes
   `"symbol. "`, and the block follows it as further adjacent literals. `never a missing` stays.
6. The prompt's GREEN paragraph, after `keeping tests green.`

**The equivalence test.** It is new: `h-mad/tests/test_h_mad_new_caller_carveout_copies.py`.
- **How a copy is compared.** `collapse(s)` is `" ".join(s.split())`. Each locator returns one span,
  and the test asserts `collapse(span).count(collapse(CANONICAL)) == 1`.
- **Locators fail rather than pass.** Each locator raises when its anchor matches zero spans or more
  than one, so the test fails.

The six locators:
- **L1, prompt RED item 1.** The span runs from the unique line that starts `1. For each FAILING test:`
  to the next `\n2. `. It does not pin the item's number or position beyond items 1 and 2.
- **L2, the WIRE-PIN paragraph.** The prompt is split on blank lines (`\n[ \t]*\n`), and the one
  block whose left-stripped text starts ``**If the dispatch carries a `WIRE:` / `WIRE-PIN:` line``
  is taken. It does not pin where the block sits in the file.
- **L6, the GREEN paragraph.** The same split, taking the one block starting `For GREEN phase (5e):`.
- **L3, the SKILL.md 5d bullet.** `docsections.titled_section(skill, "Phase 5 (Implementation) sub-steps")`
  is split on blank lines, and the one block whose stripped text starts
  ``**The third task shape is `wiring`, and counts cannot gate it.**`` is taken. At `29ae3e7b` that
  selection holds exactly 1 block. It does not pin which 5d list item holds the block.
- **L4, the failure-recovery row.** It is the one table line whose third `|`-cell, stripped, equals
  `` `step5d:red_wrong_reason:<module>` ``. The span is that line's fourth cell. The row holds no
  escaped `\|` at `29ae3e7b`, and the locator splits on unescaped `|` only. It does not pin the
  row's position in the table.
- **L5, the assembler copy.** `ast.parse` the assembler and take the top-level `FunctionDef` named
  `assemble`. Among its `ast.Constant` `str` nodes, take the one containing
  `The WIRE-PIN is this task's single load-bearing test.` The parser joins the adjacent literals.
  This does not pin the literal split, and the mutation row is what pins that.

No span holds more than one copy, so a healthy copy cannot mask a sick one.

**The control.** The new spec `h-mad/tests/mutation-specs/new_caller_carveout_copies.json` holds 8
rows, each with `symbol` set. For a `.md` file that is the enclosing heading, and for the `.py` file
it is `assemble`. Each row's `test` is the equivalence test, and each row is run alone.
- **Six per-copy rows.** Each changes `valid **only** when` to `valid when` in one copy, with a
  `find` that starts at that copy's context sentence above. That context makes the `find` unique in
  its file, which the harness `anchor_status` requires. The `.py` row's `find` is written against
  the committed source bytes, including the adjacent-literal split.
- **Two per-sentence rows**, on the `failure-recovery.md` copy, which is its file's only copy:
  - sentence 2: delete `The RED report must name both. `;
  - sentence 3: change `delete the call only, keep the caller and the callee` to
    `delete the callee only, keep the caller`.

  Sentence 1 in that copy is covered by its per-copy row.
- AC-9.4 asks for six per-copy runs plus one run per sentence in one copy. 8 = 6 + 2, because the
  per-copy row for `failure-recovery.md` is also its sentence-1 row.

**Residual.** The test shows that each copy carries the block. It does not show that no copy has a
contradicting sentence beside it, or that a seventh surface exists. A seventh surface held in a
`str` constant, a comment or non-`.py` text is found by re-running FR-9's union sweep (AC-9.1). One
built at run time is found only by reading the code that builds the dispatch text.

**The differential corpus (AC-9.2).** It is a new suite test,
`h-mad/tests/test_h_mad_wire_pin_new_caller_corpus.py`.
- **The five cases.** For each of `new-caller`, `missing-callee`, `both-missing`,
  `unrelated-import` and `other-symbol`, it builds a fixture repository in `tmp_path` and runs real
  pytest with `sys.executable`, recording the RED's exception line.
- **Callee resolution is executed, never parsed.** A subprocess runs `import <mod>` and
  `getattr(<mod>, "<callee>")` at the RED base.
- **The missing-symbol role** comes from the fixture's declaration. The test asserts that the
  exception line names that symbol.
- **Two classifiers transcribe the two texts.**
  - `old_rule`: a missing-symbol RED (`ImportError`, `ModuleNotFoundError`, `AttributeError` or
    `NameError`) is a halt.
  - `new_rule`: such a RED is valid iff the missing symbol is the caller and the callee resolves.
  - The test also asserts that `CANONICAL`, imported from the equivalence test, contains
    `the missing symbol is the caller the task creates` and `the callee resolves at the RED base`.
    That ties the transcription to the words.
- **Pass:** the set of cases whose verdict changed equals `{new-caller}`.
- **Control:** two rows in the same new spec, each run alone. One drops the callee condition, and
  `both-missing` then changes. The other drops the caller condition, and `other-symbol` and
  `unrelated-import` then change.
- The cases' exception lines and verdicts are also written to
  `docs/03-analysis/probes/agy-coder-fallback/` as the committed reading.

**The incident replay (AC-9.3).** It is a committed probe under
`docs/03-analysis/probes/agy-coder-fallback/`, following FR-9's four steps through `git archive`
exports, so the live clone is never checked out. The premises were re-checked at `29ae3e7b`:
HemaSuite `HEAD` is `77fb16f51`, and `531a6296b`, `7aa0d9dec` and `c2d671f6b` are each ancestors
(`git merge-base --is-ancestor`). Their subjects begin `…Task 4 FR-1 resolver`,
`…Task 5 FR-5 initiali…` and `…Task 6 CLI surface…`. The probe stamps the HemaSuite sha it reads.

### FR-10 — documentation surfaces

These follow the spec's FR-10 list and the plan's doc-pin census. Each rewrite keeps every pinned
literal the census lists, or changes that test's literal in the same commit.
- **SKILL.md §"Codex authors Phase 5 — enforced, not just instructed"** becomes implementer-neutral.
  It states FR-2 and FR-3 and names `agy-authorship`, `implementer-invalid` and
  `h_mad_tdd_judge.py implementer`. The heading and the end anchor
  `Phase 5 implementation is **Codex's job**` stay, or `_phase_5e_text` and `PHASE5_HEADING` move
  in the same commit.
- **SKILL.md §"Exit-code dispatch for 5d/5e"** gains a line that holds both `exec agy` and
  "implement", plus the `TDD-IMPLEMENTER:` staging step.
- **SKILL.md, Phase 7 closure item 7** carries every `WARNING` line, and adds the FR-7 `--append`
  step after each leg, for every implementer.
- **The SKILL.md teammate-audit bullet** separates audit-leg selection from resolved authorship.
- **SKILL.md** states the FR-5 re-run trigger: after any agy upgrade, re-run FR-8 step 2 and step
  2a, and re-take the class-(a) inventory.
- **`agy-runtime.md` §"The TDD gate"** names `h-mad-agy-tdd-gate.py` and `AGY-GATE:`, and keeps the
  halt. Its `SessionStart` claim, on two surfaces, is re-checked against the installed agy, which
  is `1.4.0` at `29ae3e7b`.
- **The prompt** gets a neutral opening and a `Hook:` line that names each gate by implementer,
  with no `<`, `>` or `->`.
- **`state-schema.md` and the schema** get the FR-1 rows, plus the four description rewrites in
  §"FR-1".
- **`failure-recovery.md`** gets copy 4.

## Components Changed / Added

| Path | Change | FR |
|---|---|---|
| `h-mad/scripts/h_mad_state_schema.json` | four properties; `fallback_agent` and `codex_status` descriptions | FR-1 |
| `h-mad/scripts/h_mad_state_validate.py` | `rfc3339_datetime`, `_semantic_ok` in `classify`, `property_valid` | FR-1, FR-7 |
| `h-mad/scripts/h_mad_tdd_judge.py` | `Record` fields, `_implementer_tag`, `Implementer`, `resolve_implementer`, author field, `implementer` verb | FR-2, FR-3 |
| `h-mad/hooks/h-mad-tdd-gate.sh` | `STATE_ACTIVE_RE`, author-field parse, FR-3 precedence | FR-3 |
| `h-mad/scripts/h_mad_target_identity.py` | receives the 25 moved names | FR-6 |
| `h-mad/hooks/h-mad-codex-tdd-gate.py` | guarded import of the 25 names; definitions removed | FR-6 |
| `h-mad/hooks/h-mad-agy-tdd-gate.py` (new) | agy write gate | FR-4 |
| `h-mad/scripts/h_mad_hook_wiring.py` | `--agy`, `check_agy` | FR-5 |
| `h-mad/scripts/h_mad_assemble_tdd.py` | `agy` choice, timeout table, check run, docstring, copy 5 | FR-5, FR-8, FR-9 |
| `h-mad/scripts/h_mad_state_write.py` | `--append` | FR-7 |
| `h-mad/scripts/h_mad_phase7_preconditions.py` | `_review_independence_warnings` | FR-7 |
| `h-mad/references/codex-implementer-prompt.md` | neutral opening, `Hook:` line, copies 1, 2 and 6 | FR-9 |
| `h-mad/SKILL.md`, `h-mad/references/agy-runtime.md`, `h-mad/references/state-schema.md`, `h-mad/references/failure-recovery.md` | §"FR-10" | FR-9, FR-10 |
| `.agents/hooks.json` (new, committed by FR-8's stage) | wiring | FR-5, D-2 |

## Implementation Order

1. FR-1: the schema, the validator predicate and `property_valid`.
2. FR-2: the resolver and the verb.
3. FR-3: the line, the hook, the stub re-shape, `ACTIVE_RE`, and the re-anchoring of every row of
   the two files.
4. FR-6: the move, the guarded import, the 31 re-pointed rows, and the identity module's anchor
   recheck.
5. FR-4, then FR-5.
6. FR-7: `--append`, then the warnings.
7. FR-9 and FR-10: the copies, the equivalence test, the corpus, the doc rewrites, then the replay
   probe.
8. Merge, then FR-8's stage, which is OQ-B.

Each Task runs the full h-mad suite, under `/opt/anaconda3/bin/python3`, in the foreground, and
gates on the summary line.

## Test Plan

| AC | Where |
|---|---|
| AC-1.1 | `test_h_mad_state_validate_fallback.py` gains each FR-1 field × value × path; `test_h_mad_state_fallback_agent.py` stays green |
| AC-1.2 | new fixtures beside it: 4 refused values and the zone-branch fixtures, × 2 paths |
| AC-2.1, AC-2.2 | `test_h_mad_tdd_judge.py`, with `env` and `which` injected; the verb through `_cli` |
| AC-3.1, AC-3.2 | `test_h_mad_tdd_gate_judge.py` and `test_h_mad_tdd_gate_fallback_agent.py` (re-shaped literals only); new kinds in a new `test_h_mad_tdd_gate_peers.py`; a `bin_dir` with an `agy` stub drives `agy-authorship` |
| AC-4.1, AC-4.2 | new `test_h_mad_agy_tdd_gate.py` |
| AC-5.1, AC-5.2 | new `test_h_mad_hook_wiring_agy.py` (a `HOME` fixture), plus `test_h_mad_assemble_tdd_agent.py` |
| AC-6.1 | the existing Codex gate tests unmodified; the one-`def` test; the `unsafe` tuple parity test; the shell differential |
| AC-7.1, AC-7.2 | `test_h_mad_state_write.py` (`--append`) and `test_h_mad_phase7_preconditions.py` |
| AC-8.1, AC-8.2 | probes, §"FR-8" |
| AC-9.1 | the union sweep re-run, plus the three pin files staying green |
| AC-9.2, AC-9.4 | §"FR-9" |
| AC-9.3 | probe |
| AC-X | §"Mutation rows" |

## Mutation rows (AC-X)

Each new guard below gets one row. The fixture that kills it is named beside it.
- **FR-1**
  - `_semantic_ok` call removed from `classify` → `not-a-date` on both paths.
  - The `datetime` construction removed → `2026-02-30T00:00:00Z`.
  - `fullmatch` → `match` → `…Zjunk`.
- **FR-2**
  - Each `_cause` branch removed → that branch's own fixture, with only that cause present.
  - The `other` peer step removed → `chosen=codex` out, agy available.
- **FR-3**
  - The `implementer-invalid` branch removed → the invalid fixture.
  - The `INVALID_RECORD` scan stopped at the first record → `[codex-available, invalid]` expects
    `implementer-invalid`.
  - The `agy` arm removed → the `agy-authorship` fixture.
  - The grammar's `peers-out` alternative removed → every stub test.
- **FR-6:** the import guard removed → the gate without the identity module.
- **FR-4**
  - A class-(a) name moved to (b) or (d) → that class's member fixture.
  - The class-(d) default replaced by allow → an unknown-name fixture.
  - The no-path-key deny removed → that fixture.
  - The `artifactDirectoryPath` `.py` refusal removed → its fixture.
  - The `finally` deny removed → malformed stdin.
- **FR-5:** each of the seven reason checks removed → its fixture; `UNWIRED` returning 2 → the
  AC-5.2 exit fixture.
- **FR-7**
  - `--append` mutating the prior list in place → AC-7.1's two-entry byte check (each earlier entry
    compared as `json.dumps` text before and after).
  - The `independent` consistency check removed → a lying-boolean fixture.
  - The `unrecorded` trigger restricted to `implementer == "agy"` → the `codex` fixture (AC-7.2).
  - A malformed 6a-prime entry counted as recorded → its fixture.
- **FR-9:** the 8 + 2 rows in §"FR-9".

## Residuals

Each is stated where it arises. Collected here:
- the `which` / `command -v` matrix (FR-2);
- the verb reads the root only (FR-2);
- the leap second (FR-1);
- the class-(a) judgement (FR-4);
- the six-line shell composition in both gates (FR-4);
- a sibling `overwrite` (FR-4);
- the review-leg agy is gated too (FR-4);
- worktree state, not claimed either way (FR-4);
- an equivalent command spelling (FR-5);
- a writer that bypasses `_mutate` (FR-7);
- prose application (FR-9);
- a contradicting sentence or a seventh surface (FR-9).

## Measurements

Each figure is one reading at `29ae3e7b`. The committed probes for the census readings are owed
under `docs/03-analysis/probes/agy-coder-fallback/`, and this design writes none of them. The
scratch scripts that produced these figures were deleted. Their method is stated beside each
figure, so a probe can re-derive it.

| Figure | Method | Reading |
|---|---|---|
| DO-1a line census | `git ls-files -z h-mad \| xargs -0 grep -l 'TDD-STATE: active'`, and the plan's four-pattern variant | 6 files; 7 files |
| M-3, rows over the contract | the plan's pattern over the `find` + `replace` of rows naming the two FR-3 files | 8 rows, 3 specs |
| rows inside the regions FR-3 rewrites | the `find` offset inside `_read_state`, the authorship block, `_active_records` or `format_state_line` | 13 rows |
| M-4 over the DO-5 set | the `find` start inside a moved name's `ast` span, for rows naming the Codex gate | 31 of 62 rows, 4 specs |
| class inventory | the first `init` event's `tools` | 58 names: (a) 11, (b) 5, (c) 1, (d) 41 |
| live records with FR-1 keys | a key scan over two state files | 0 of 61 records |

## Open questions for the operator

- **OQ-A — where the shared policy lives (DO-5).** The spec says "a shared module". A **new**
  module breaks `test_codex_gate_judge_timeout_reason` unmodified (§"FR-6", probed).
  - **Recommended:** `h_mad_target_identity.py`, which keeps every test unmodified and keeps the
    spec's letter, at the cost of cohesion.
  - **Alternative 1:** a new module, plus copying it into that test's hand-built tree. That edits
    an existing test, which FR-6 forbids.
  - **Alternative 2:** no move; the agy gate loads the Codex gate file through
    `importlib.util.spec_from_file_location`. This gives one definition with no re-pointing, but it
    departs from FR-6's "moves".
- **OQ-B — FR-8 after the merge (DO-6).** AC-8.1 and AC-8.2 can only pass once main carries the
  gate.
  - **Recommended:** the post-merge stage in §"FR-8", with the feature recorded COMPLETE only after
    it, and this repository's `.agents/hooks.json` committed only on a passed refusal.
  - **Alternative:** a test-pinned override flag that lets the check and the tracer use a worktree
    gate before the merge. It ships a path that points away from the installed gate, and it settles
    trust only for a worktree location.

## Owed by other documents

- **Spec, FR-1 and FR-10.** The `codex_status` schema description and its `state-schema.md` row
  are members of the class FR-1 corrects for `fallback_agent`. Both say an unavailable Codex lets
  Claude author, and both are false once agy is available. This design rewrites them (§"FR-1"). The
  spec's surface list should name them.
- **Spec and plan, the agy version.** Both read `agy --version` → `1.3.6`. At `29ae3e7b` it prints
  `1.4.0`. FR-8 and the `SessionStart` re-check must stamp the version they ran against.
- **Spec, FR-6, if OQ-A takes the recommendation.** "The design moves it to a shared module" holds.
  AC-6.1's "re-pointed rows run against the shared module" names `h_mad_target_identity.py`.
- **Plan.** M-4's 19 rows become 31 over the DO-5 set (§"FR-6"). DO-2's "with that log's agy
  version" cannot be met from the log, which carries none (§"FR-4").
- **Impl-plan.** These become committed probes: the M-3/M-4 censuses, the class inventory, the FR-9
  corpus reading and the replay. Each FR-9/FR-10 Task's RED names the doc-pin census entries it
  moves.

## Version History
- v1.0: Initial design (2026-10-16) from spec v1.6 (c853b207) and plan v1.4 (29ae3e7b), tree read at 29ae3e7b. Settles DO-1..DO-7: per-record author field on TDD-STATE (P-1..P-5 probed in Python re and bash 3.2/5.3 ERE); 11-name class-(a) allowlist over the 58-name init.tools inventory; locked --append writer operation; stdlib RFC 3339 predicate in classify on both validator paths, scoped to implementer_switch.ts; 25 moved names into h_mad_target_identity.py with guarded import (M-4 re-derived: 31 rows, 4 specs); HOME-fixture tests and post-merge FR-8 stage; prose-applied carve-out with six per-copy locators and 8 control rows. Two operator questions (OQ-A placement, OQ-B post-merge tracer); codex_status description owed to the spec.
