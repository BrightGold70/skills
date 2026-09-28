# Plan: grok-codex-fallback

## Executive Summary

Ship the approved spec's plumbing — an optional `fallback_agent` state field, a TDD-gate branch
that keeps Claude from self-authoring under `fallback_agent=grok`, an `hmad-dispatch exec grok`
backend whose `streaming-json` transcript is parsed for final message, liveness, tool evidence and
resolved model, a `grok` audit-cycle surface, an assembler `--agent` flag, and the documentation
that says what grok has and has not been measured on — without changing any behaviour a caller
that never names grok can observe.

## Overview

When codex is out of quota, h-mad's Phase-5 author and its independent audit surface both fall
back onto Claude, the orchestrator's own model family, so the reviewer shares the author's blind
spots by construction. Grok (xAI) is a third family, and one RED dispatch plus one stream probe
show it can be driven headlessly. This feature makes grok routable; it does **not** establish that
grok is good at the roles (D4). Every quality question stays a separate, measured follow-up.

## Scope

In scope — the systems the spec's FR-1 to FR-11 touch, all inside the `h-mad` skill:

- the per-feature state schema (`h-mad/scripts/h_mad_state_schema.json`);
- the Claude-side Phase-5 hook (`h-mad/hooks/h-mad-tdd-gate.sh`, its codex-authorship block only);
- the dispatch wrapper (`h-mad/scripts/hmad-dispatch.sh`): `_cmd_exec`, `_exec_log_format`,
  `_render_progress`, `_cmd_audit_cycle`'s `--surfaces` validation, and the usage text of
  `_cmd_resolved_model`;
- the evidence reader (`h-mad/scripts/h_mad_review_evidence.py`), the audit-cycle combiner
  (`h-mad/scripts/h_mad_audit_cycle.py`), the TDD assembler (`h-mad/scripts/h_mad_assemble_tdd.py`)
  and the model resolver (`h-mad/scripts/h_mad_resolved_model.py`);
- `h-mad/SKILL.md` and two references (`h-mad/references/state-schema.md`,
  `h-mad/references/agent-substrate.md`);
- tests, a `grok` stub, derived fixtures, and mutation specs under `h-mad/tests/`.

User-visible behaviour: an operator who sets `fallback_agent=grok` is blocked from Claude
self-authoring and told the grok dispatch; `hmad-dispatch exec grok`, `progress`, `resolved-model
grok` and `audit-cycle --surfaces agy,grok` work offline against a stub; `h_mad_assemble_tdd.py
--agent grok` prints a grok command block. Nothing else changes.

## Goals

- Let an operator declare, auditably, who covers when codex is out — FR-1
- Keep Claude from writing Phase-5 production code under `fallback_agent=grok`, with no escape
  through the older env override — FR-2
- Dispatch grok headlessly through the same `exec` machinery codex and agy use — FR-3
- Recover grok's final message and verdict from its own stream region, never from decoys or a
  previous dispatch — FR-4
- Make a running grok dispatch legible in `progress` — FR-5
- Let a grok review pass the "read something" evidence gate on parsed events, and report
  cannot-measure distinctly from measured-zero — FR-6
- Make grok a gateable audit surface — FR-7
- Print a grok Phase-5 command block on explicit request only — FR-8
- Report which grok model actually ran, or refuse — FR-9
- Document the routing and its unmeasured status on every surface that routes to it — FR-10
- Leave every non-grok path byte-identical — FR-11

## Requirements

- FR-1: optional `fallback_agent` state field, enum `grok | claude | null`
- FR-2: TDD-gate outcome is the spec's four-row total function of `codex_out` × `fallback_agent`
- FR-3: `hmad-dispatch exec grok` transport, argv and child-only environment scrub
- FR-4: final-message segmentation, completion, truncation and structured-only recovery
- FR-5: `progress` learns `grok-ndjson`
- FR-6: `scan_grok` and the evidence CLI's grok branch
- FR-7: `grok` as an `audit-cycle` surface, and the `grok` / `grok-truncated` effort shapes
- FR-8: `h_mad_assemble_tdd.py --agent codex|grok`
- FR-9: `resolved-model grok`
- FR-10: documentation, located by heading
- FR-11: regression — every non-grok path unchanged

## Implementation Strategy

**Three layers, built bottom-up, each testable offline.** (1) The pure parsers — the FR-4
segmenter, `scan_grok`, the FR-9 `end`-event reader — are driven straight from F0 and its derived
fixtures. (2) The wrapper and hook consume them: `_cmd_exec`'s grok branch, `progress`,
`audit-cycle`, and the gate. (3) The documentation lands last, against the shipped behaviour, and
is pinned by a heading-located doc test. The assembler (FR-8) and the schema (FR-1) are
independent leaves and can land in any order.

**One fixture source.** F0 (`docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`)
is the only hand-captured grok stream. Every other fixture the spec names (F-TRUNC, F-NOTOOLS,
F-NOTEXT, F-DECOY, F-BEAT, F-SPACED, F-TWOMODEL, F-SHARED) is **derived from F0 inside the test**
by one shared helper, so no second grok stream exists to drift from the real one. Any copy of F0
under `h-mad/tests/fixtures/` asserts its sha256 equals F0's.

**The `grok` stub models what the wrapper consumes.** A new `h-mad/tests/stubs/grok` joins the
existing `codex`/`agy` stubs (reached through `_bindir` in `h-mad/tests/test_hmad_dispatch.py`).
It records argv and environment, **copies the `--prompt-file` contents at invocation time** —
the wrapper deletes the bounded prompt after the child exits, so a stub that only records the
path proves nothing about the bytes — emits a caller-chosen F0-derived stream to stdout, can
sleep after emitting (AC-4.8), and exits with a caller-chosen rc. It follows the existing
`HMAD_STUB_*` knob convention.

**Grok gets an explicit arm at every agent-conditional site in `_cmd_exec`; no binary test may
route it into another agent's arm.** Today `_cmd_exec` decides between agents with binary tests
(`if [ "$agent" = codex ] … else <agy path>`). Adding `grok` to the valid set without touching
them sends grok down the agy arm: `--dangerously-skip-permissions`, the prompt as one `--print`
argv element, and the ARG_MAX `OVERSIZE` refusal FR-3 says does not apply. That is a class, not an
instance, so the rule is over the axis: **every** line in `_cmd_exec` that branches on `$agent`
is re-examined and either given a grok arm or shown (by a named test) to be correct for grok by
fall-through. Census of the sites, at `1680271`, one grammar:

```bash
awk '/^_[a-z_]+\(\) *\{/{fn=$1} /"\$agent" (=|!=) |case "\$agent" in/{print fn}' \
  h-mad/scripts/hmad-dispatch.sh | sort | uniq -c
# reading at 1680271 (unit: matching lines, per enclosing function):
#   8 _cmd_exec()   2 _cmd_launch()   1 _cmd_exec_pane()   1 _cmd_resolve()   1 _cmd_verify()
```

Only the 8 `_cmd_exec()` lines are in scope; the other functions are the pane path, which stays
grok-refusing (AC-3.7). **Residual:** a site that branches on the agent through a variable other
than `$agent`, or inside a helper `_cmd_exec` calls, is outside this grammar; AC-3.1, AC-3.5 and
AC-4.x are the behavioural backstop. This count moves by construction when Phase 5 adds grok arms
— re-measure it at the 5g diff review, never carry this reading forward.

**Valid-set messages.** The literal agent sets are the second axis. Census, `1680271`:

```bash
grep -c 'codex|agy\|agy|codex' h-mad/scripts/hmad-dispatch.sh
# reading at 1680271: 15 (unit: matching lines)
```

Of those lines, the ones inside `_cmd_exec` (its header comment, its `case`, its error message)
and `_cmd_audit_cycle` (its `case`, its error message) gain `grok`; the header comment of
`_cmd_resolved_model` gains `grok`. The rest — `_cmd_exec_pane`, `_cmd_launch`, `_cmd_pin`,
`_cmd_resolve`, `_cmd_verify`, `_agent_tail_re`, and the comment in `_resolve_target` — stay
`codex|agy`, because the pane path is out of scope. Locate by enclosing function
(`awk '/^_[a-z_]+\(\) *\{/{fn=$1} /codex\|agy|agy\|codex/{print fn}' h-mad/scripts/hmad-dispatch.sh`),
never by line.

**The combiner routes by closed-world shape.** `h_mad_audit_cycle.combine()` today routes
`codex-text` (skip), `missing`/`unparseable` (`low_evidence_unmeasurable`) and `empty`
(`low_evidence`) explicitly, and **every other shape falls through to the `DELIVERY_FLOOR` count
check**. A new shape that is not routed is therefore scored as a count — which for
`grok-truncated` is exactly the "measured zero where cannot-judge belongs" defect FR-6 and FR-7
exist to prevent. Rule over the axis: every shape `measure_effort()` can return has an explicit
branch in `combine()`, and only `parsed` and `grok` reach the floor check. A test enumerates the
shapes `measure_effort()` produces across the fixtures and asserts each one's routing.
`_effort_items()` likewise gets an explicit rendering for both grok shapes (it renders
`codex-text` specially today), so a truncated grok log never prints a row of zeros.

**The gate reads `fallback_agent` type-preservingly.** The hook reads `codex_status` with
`jq -r '… // "available"'`. The same idiom is wrong for `fallback_agent`, measured:

```bash
for v in '{}' '{"f":null}' '{"f":false}' '{"f":"grok"}' '{"f":0}'; do
  printf '%s -> %s\n' "$v" "$(echo "$v" | jq -r '.f // "claude"')"; done
# reading 2026-09-28 (jq on PATH): {} -> claude, {"f":null} -> claude, {"f":false} -> claude,
#                                  {"f":"grok"} -> grok, {"f":0} -> 0
```

`//` treats `false` as absent, so `fallback_agent: false` would FALL-THROUGH where the spec's
table demands BLOCK-INVALID; and `jq -r` prints the JSON string `"null"` and JSON `null`
identically, so a string `"null"` would read as absent. The read must distinguish absent, JSON
`null`, the two valid strings, and everything else, and must fail **closed** (BLOCK-INVALID) when
the value cannot be read at all. The class test is now the spec's own **AC-2.1b** (spec v1.1),
which supersedes v1.0's plan-level supplement: each of the 8 values `false`, `true`, `0`,
`"null"`, `""`, `"Grok"`, `{}`, `[]` is its own parametrized case, run under each of the three
codex_out routes alone (`HMAD_CODEX_UNAVAILABLE=1`; `codex_status: "exhausted"`; `codex` off
PATH) — 24 BLOCK-INVALID cells, each asserting exit 1 and AC-2.4's stderr — with a control in
which a stored JSON `null` under the same three routes is FALL-THROUGH (3 cells), as is an absent
key. The control is what separates the string `"null"` from JSON `null`, so it is the cell that
kills a reintroduced `-r` collapse; the `false` cells kill a reintroduced `//`. AC-2.1b also
asserts, in its own words, "The same 8 values with codex_out false yield BLOCK-CODEX, as the
table's first row says." Those 8 BLOCK-CODEX cells are therefore **part of AC-2.1b**, not a plan
addition (plan v1.1 called them one; that was wrong). They are the cells that kill a read which
returns BLOCK-INVALID regardless of `codex_out`, which would pass all 24 BLOCK-INVALID cells. The
same test file carries them (codex on PATH, variable unset, `codex_status` absent), one value per
case.

**Regression is proven against the base, not asserted.** AC-2.2 compares against
`git show <base>:h-mad/hooks/h-mad-tdd-gate.sh`; AC-8.1 against the base commit's assembler
output. `<base>` is the commit the feature branch forks from, recorded in the state record at 5c.

**What we deliberately do not touch:** the pane path; `h_mad_archreview_cycle.py`; `scan()`'s
return keys and values; the `codex_status` enum; `h-mad/references/codex-implementer-prompt.md`;
`h-mad/hooks/h-mad-codex-tdd-gate.py` (the codex-side adapter — see Risks); any wrapper-side
grok size bound.

## Verified premises (commands run at `1680271`)

Each premise below was executed against the tree, not reasoned about. A reading is one reading at
one sha; the command is what a later reader re-runs. The commits since (`805e4f3`, `7d2f780`,
`42511c3`) touch only this feature's documents and probe sidecar:
`git diff --stat 1680271 42511c3 -- h-mad handoff` prints nothing (run at `42511c3`), so the tree
premises P2–P13 and the suite baseline were not re-run for v1.1 and stand at `1680271`. P1 and
the AC census were re-run at `42511c3`. For v1.2, `git diff --name-only 1680271 8c631d3 -- h-mad
handoff | wc -l` → 0 files (run at `8c631d3`), and the commands P8, P10 and P13 had lacked are
now written inline and were run at `8c631d3`, as was P11's new proxy.

- **P1 — F0 matches the spec's figures.** Run:

  ```bash
  F=docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson
  wc -l < "$F"; wc -c < "$F"; shasum -a 256 "$F"
  jq -r .type "$F" | sort | uniq -c
  jq -r 'select(.type=="tool_call_update" and .status=="completed")|.toolCallId' "$F" | sort -u | wc -l
  jq -c 'select(.type=="tool_call_update" and .status==null)' "$F" | wc -l
  jq -s '[.[]|select(.type=="usage")|.usage.reasoning_tokens]|add' "$F"
  jq -c 'select(.type=="end")|[.stopReason,(.modelUsage|keys),.num_turns]' "$F"
  grep -c '^{"type":"' "$F"
  jq -s -c 'to_entries|[(map(select(.value.type=="text"))|last.key),(map(select(.value.type=="usage"))|last.key)]' "$F"
  ```

  Reading: 110 lines, 83,256 bytes, sha256
  `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`; type counts (events)
  `thought` 70, `text` 21, `available_commands` 9, `usage` 3, `tool_call_update` 4,
  `tool_call` 2, `end` 1; 2 distinct completed `toolCallId`s; 2 null-status updates; reasoning
  sum 121; `end` = `end_turn`, one model key `grok-4.7-build`, 3 turns; 110 matching lines;
  last `text` at event index 106, last `usage` at 108 (spec A1 confirmed). F0 ends with a
  newline. F0 was committed at `d2fbb96` and is unchanged since (`git log --format=%h -1 -- "$F"`
  → `d2fbb96`, re-run at `42511c3`, where the size, sha256, null-status and line-prefix figures
  above re-read identically). **Where the commands live:** since `7d2f780` the probe sidecar
  (`docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.md`, section
  "Re-derivation commands") carries all of them except two — the null-status count and the
  `grep -c '^{"type":"'` line-prefix count — and spec v1.1's F0 bullet writes those two inline.
  The plan's v1.0 statement that the sidecar carried none of them is retired. Check:
  `grep -c 'status==null\|\^{"type"' docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.md`
  → 0 matching lines at `42511c3` (unit: lines), confirming exactly those two are absent there.
- **P2 — tool-call join for AC-4.6 and AC-5.2.** `jq -r 'select(.type=="tool_call" or
  .type=="tool_call_update")|[.type,.toolCallId,(.toolName//"-"),(.status//"null")]|@tsv' "$F"`
  shows `read_file` then `search_replace`, each `pending` → `null` → `completed`, with
  `toolName` present only on `tool_call`. So the last completed tool is `search_replace`, and
  the name must be joined by `toolCallId`.
- **P3 — the hook's escape predicate is as the spec states.** The block headed
  `# --- Codex-authorship enforcement` blocks when `HMAD_CODEX_UNAVAILABLE` is empty **and**
  `codex_status` (read with `// "available"`) is neither `unavailable` nor `exhausted` **and**
  `command -v codex` succeeds (`sed -n '/# --- Codex-authorship enforcement/,/^fi$/p'
  h-mad/hooks/h-mad-tdd-gate.sh`). The exemption `case` blocks (test basenames, `*/tests/*`,
  `*/fixtures/*`, docs/config/shell suffixes, non-`.py`) sit **above** that block, so AC-2.6
  holds by construction as long as the new read stays inside it. The hook exits 0 when `jq` is
  absent, before the block — an existing fail-open that `fallback_agent=grok` inherits (Risks).
- **P4 — state writes require the strict tier.** `h_mad_state_write.py` refuses any record whose
  `classify()` is not `strict`, and `_parse_value` JSON-decodes first, so `--set
  fallback_agent=null` writes JSON `null` and `=grok` writes a string (`grep -n 'classify(record)
  != "strict"\|def _parse_value' h-mad/scripts/h_mad_state_write.py`). The schema's root is the
  per-feature record, with `additionalProperties: false` and a `required` list that excludes
  `codex_status` (`python3 -c "import json;s=json.load(open('h-mad/scripts/h_mad_state_schema.json'));print(s['additionalProperties'], 'codex_status' in s['required'])"`
  → `False False`). The stock `python3` here has no `jsonschema`, so the bundled `_MiniDraft7`
  validator in `h_mad_state_validate.py` carries the run; its agreement with `jsonschema` is
  pinned by `h-mad/tests/test_h_mad_state_validate_fallback.py`, which therefore must stay green
  on the new enum (it already contains a `null` member in `codex_status`).
- **P5 — `fallback_agent` exists nowhere in the skill today.** `git ls-files h-mad handoff |
  xargs grep -l fallback_agent` → zero files (the only hits repo-wide are the brainstorm, the spec
  and `docs/handoffs/2026-09-28-main__grok-codex-fallback.md`). This zero is **load-bearing**: it
  is why every existing record stays valid (AC-1.3) — it holds because the feature is unbuilt, and
  it stops holding the moment FR-1 lands, which is the intent.
- **P6 — `codex_status` has four tracked non-test readers/mentions.** `git ls-files h-mad handoff
  | grep -v '/tests/' | xargs grep -l codex_status` → `h-mad/SKILL.md`,
  `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/scripts/h_mad_mutation_harness.py` (a comment),
  `h-mad/scripts/h_mad_state_schema.json` (unit: files). **`h-mad/references/state-schema.md`
  does not mention `codex_status`**, so FR-10's instruction to document `fallback_agent` there
  documents the "who covers" field without its "why codex is out" sibling. The plan documents
  both there (the FR-10 AC is still met; see owed list).
- **P7 — the combiner's fall-through.** In `h_mad_audit_cycle.combine()`, after the findings
  loop, a shape not in `codex-text | missing | unparseable | empty` reaches `ok <= DELIVERY_FLOOR`;
  `DELIVERY_FLOOR = 2` (`grep -n '^DELIVERY_FLOOR' h-mad/scripts/h_mad_audit_cycle.py`). So
  AC-7.2's `ok=2` is `UNVERIFIED low_evidence`, and AC-7.3's derived stream needs 3 completed
  tool calls. `measure_effort()` imports `scan` from `h_mad_review_evidence`; `scan_grok` will be
  imported beside it.
- **P8 — the audit-cycle pass loop is surface-agnostic.** `_cmd_audit_cycle` dispatches each pass
  as `_cmd_exec "${agent[$i]}" …` and assembles every pass's prompt with one
  `h_mad_assemble_audit.py` call that takes no agent argument; only the `--surfaces` `case` and its
  message name agents. `validate_surface()` in `h_mad_audit_cycle.py` accepts any
  `^[A-Za-z0-9][A-Za-z0-9_-]*$` token, and `h-mad/tests/test_h_mad_audit_surface_discovery.py`
  pins the surface set as open. So FR-7's transport change is the `case` plus its message.
  Commands (run at `8c631d3`):

  ```bash
  sed -n '/^_cmd_audit_cycle()/,/^}/p' h-mad/scripts/hmad-dispatch.sh \
    | grep -n '_cmd_exec \|h_mad_assemble_audit\|agy|codex\|case "\$_s"'
  # reading: one `_cmd_exec "${agent[$i]}" "${prompt[$i]}" …` call, one `h_mad_assemble_audit.py
  # --feature … --phase …` call (no agent argument), and `case "$_s" in agy|codex)` with its
  # "unknown agent '$_s' (agy|codex)" message — the only agent names in the function
  grep -n 'SURFACE_RE = \|def validate_surface' h-mad/scripts/h_mad_audit_cycle.py
  # reading: SURFACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$"); validate_surface defined
  ```
- **P9 — the assembler's defaults.** `--timeout` is an argparse `default=900`, and `--model` /
  `--effort` default to `None` (`grep -n 'add_argument("--timeout"\|^DEFAULT_MODEL\|^DEFAULT_EFFORT'
  h-mad/scripts/h_mad_assemble_tdd.py`). FR-8's "1500 when `--timeout` is not given" therefore
  needs a not-given sentinel; an argparse default of 900 cannot tell `--timeout 900` from absence.
  Spec v1.1 makes this explicit: "not given" is judged on presence in argv, never on value, and
  AC-8.2 pins `--agent grok --timeout 900` → `--timeout 900`, never `--timeout 1500` — the one
  case a value-based sentinel (`if timeout == 900`) gets wrong.
  The block's dispatch line is built in one f-string beginning `hmad-dispatch exec codex`.
- **P10 — `resolved-model` pass-through.** `_cmd_resolved_model` forwards `"$@"` to
  `h_mad_resolved_model.py`, whose agent is `choices=("codex", "agy")`. FR-9's wrapper side is a
  usage-comment change; the gate is the `choices` tuple. Commands (run at `8c631d3`):
  `sed -n '/^_cmd_resolved_model()/,/^}/p' h-mad/scripts/hmad-dispatch.sh` → a body of `_need`
  plus `python3 "$(dirname "${BASH_SOURCE[0]}")/h_mad_resolved_model.py" "$@"`, header comment
  `# <codex|agy> [--log <f>]`; `grep -n 'choices=' h-mad/scripts/h_mad_resolved_model.py` → one
  matching line, `ap.add_argument("agent", choices=("codex", "agy"))`.
- **P11 — grok CLI surface (local `grok --help`, no model call).** `grok --version` →
  `grok 1.0.41`. `--reasoning-effort` lists `[aliases: --effort]`; `--output-format` lists
  `streaming-json` ("NDJSON: one ACP session update per line"); `-p, --single` and
  `--prompt-file` both exist; `--sandbox <PROFILE>` lists no values and reads **`[env:
  GROK_SANDBOX=]`**. An operator's exported `GROK_SANDBOX` therefore reaches the grok child and
  applies a sandbox although FR-3 supplies no default (Risks). Plan v1.0 raised this; spec v1.1
  now mandates it — FR-3 states the variable is inherited, neither scrubbed nor set, FR-10
  requires `agent-substrate.md` to disclose it, and AC-10.2 pins the needle `GROK_SANDBOX` there;
  scrubbing or defaulting it is spec Out-of-Scope. **`-p` with `--prompt-file` exits rc 2** —
  plan v1.1 carried this unverified from the brainstorm; v1.2 executed it with no possibility of
  a model call, network denied by the macOS sandbox and an empty `HOME` (so no stored
  credential), at `8c631d3`:

  ```bash
  printf 'hi\n' > pf.txt; mkdir -p h
  HOME=$PWD/h perl -e 'alarm 20; exec @ARGV' \
    sandbox-exec -p '(version 1)(allow default)(deny network*)' grok -p x --prompt-file pf.txt
  echo rc=$?; rm -f pf.txt; rmdir h
  # reading (grok 1.0.41): rc=2, stderr "error: the argument '--single <PROMPT>' cannot be used
  # with '--prompt-file <PATH>'" — a clap argument conflict, raised before any session starts
  ```

  `grok --help` alone is not a proxy: it lists `-p, --single <PROMPT>` and `--prompt-file
  <PATH>` but prints no conflict wording (`grok --help 2>&1 | grep -ci conflict` → 0 lines). The
  scratch files were deleted after the run.
- **P12 — the evidence verdict extractor.** `h_mad_extract_verdict.py <file> --key STATUS` on a
  file holding only `All done.` exits 2 and prints `ERROR: no STATUS: line in scrape …`
  (executed with a scratch file, then deleted). AC-4.3's expectation is therefore the tool's
  existing behaviour, not a new requirement on it.
- **P13 — the codex write gate does not cover grok.** `h-mad/hooks/h-mad-codex-tdd-gate.py` is
  a Codex PreToolUse adapter wired through Codex's own `hooks.json`
  (`h-mad/references/codex-runtime.md`). No grok-side adapter exists in this skill. Commands (run
  at `8c631d3`): `grep -c 'h-mad-codex-tdd-gate' h-mad/references/codex-runtime.md` → 2 matching
  lines (unit: lines), the first naming the adapter's wiring "through the active Codex `hooks.json`"; `git ls-files h-mad/hooks` →
  4 files, `h-mad-advisor-warn.sh`, `h-mad-codex-tdd-gate.py`, `h-mad-tdd-gate.sh`,
  `memory-index-guard.sh` (unit: files); `git ls-files h-mad | grep -ci grok` → 0 paths (unit:
  tracked paths; zero because the feature is unbuilt — load-bearing only in that it confirms no
  grok adapter exists yet, and it moves the moment Phase 5 adds `h-mad/tests/stubs/grok`). Whether
  grok offers a hook surface at all was not probed, so a grok Phase-5 dispatch writes
  production code with **no write-time test-first gate**. What remains is the RED/GREEN
  verdicts, the orchestrator's independent pytest re-run, and the 5e revert test that
  establishes GREEN (`h-mad/SKILL.md`, "GREEN is established by the revert test"). The operator
  has made the gap out of scope: spec v1.1 carries it as an Out-of-Scope entry, FR-10 requires
  the Phase-5 section to disclose it, and AC-10.1 pins the needle `no write-time test-first gate`
  in that section. Plan v1.0's "the spec does not state this" is closed.

**Suite baseline.** Commands, at `1680271`:

```bash
pytest --collect-only -q h-mad/tests 2>&1 | tail -1     # 3552 tests collected
pytest --collect-only -q handoff/tests 2>&1 | tail -1   # 201 tests collected
pytest -q -p no:cacheprovider h-mad/tests handoff/tests 2>&1 | tail -2
# 1 failed, 3752 passed, 1 warning in 579.33s — the failure is
# h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches,
# which reads the locally installed Claude Code binary; environment-dependent, not this feature's.
```

Under this machine's RTK command-rewrite hook, a bare `pytest --collect-only` prints `Pytest: No
tests collected` — the summary is rewritten, not the collection. Run the counts as `rtk proxy
pytest …` there. **Interpreter.** Bare `pytest` here is `/opt/anaconda3/bin/pytest`, whose
shebang is `#!/opt/anaconda3/bin/python` (`which pytest; head -1 "$(which pytest)"`, run at
`8c631d3`), so every `pytest` command in this plan is `/opt/anaconda3/bin/python -m pytest` —
the same interpreter the audit gate's `--suite-cmd "/opt/anaconda3/bin/python -m pytest h-mad/tests
-q"` names. Bare `python3` resolves first to `/opt/homebrew/bin/python3`, which has no pytest;
never substitute it. These counts **move by construction**: every test this feature adds raises
them. Re-measure at 5c on the branch base and again at the pre-merge gate; the floor is defined
over node ids (Success Criteria), not over this number.

Per-file collected counts at `1680271` (`pytest --collect-only -q h-mad/tests/<file> | tail -1`;
unit: tests): `test_hmad_dispatch_exec.py` 76, `test_hmad_dispatch_exec_completion.py` 8,
`test_hmad_dispatch_exec_stamp.py` 56, `test_hmad_dispatch_progress.py` 18,
`test_h_mad_review_evidence.py` 37, `test_h_mad_audit_cycle.py` 138,
`test_hmad_dispatch_audit_cycle.py` 40, `test_h_mad_resolved_model.py` 10,
`test_h_mad_assemble_tdd.py` 81, `test_h_mad_tdd_gate_codex.py` 6,
`test_h_mad_tdd_gate_state_resolution.py` 7, `test_h_mad_state_validate.py` 20,
`test_h_mad_state_validate_fallback.py` 6, `test_h_mad_state_write.py` 55.

**No mutation spec targets the TDD gate today.** `grep -l 'h-mad-tdd-gate.sh'
h-mad/tests/mutation-specs/*.json` → zero files. Why it is zero was not established (other hooks,
e.g. `h-mad-advisor-warn.sh`, do have specs); it is not load-bearing for this plan, and it means
AC-2.7's spec is the gate's first.

## Architecture Considerations

- **Live-skill coupling.** `~/.claude/skills/h-mad` and `~/.claude/skills/handoff` are symlinks
  into this checkout (`ls -la ~/.claude/skills/h-mad ~/.claude/skills/handoff`). Editing the
  main working tree edits the installed skill mid-run. Per `h-mad/SKILL.md` §"Editing this skill
  while a run is in flight", the feature is built on a feature branch **in a git worktree**, and
  both coupled suites (`h-mad/tests`, `handoff/tests`) run before merge.
- **Bootstrap: this feature cannot use itself.** The live hook and the live `h_mad_state_write.py`
  read the main tree until merge. Until then, `--set fallback_agent=grok` is refused as an
  undeclared key, and the live hook does not know the field. If codex is out during this
  feature's own Phase 5, the fallback is today's (`codex_status=exhausted`, Claude test-first),
  not grok.
- **Two instruments, one vocabulary.** `_exec_log_format` (shell, picks a render lens) and
  `measure_effort()` (Python, picks a verdict route) must classify a grok log the same way, with
  the same precedence (agy first, then grok, then codex). The seven observed `type` values are
  the shared criterion; the plan requires one test that feeds the same fixtures to both and
  asserts agreement (F0, F-SPACED, F-TRUNC, an agy log, a codex banner log, and the mixed
  agy+F0 log that discriminates the precedence — see W5–W7).
- **Child-only environment.** The `^CLAUDE` scrub and the `HPW_AGENT_BACKEND:=claude` default
  apply to the grok child's process only. `_exec_run` launches the child; the scrub must not
  leak into the wrapper shell (AC-3.3's "after the dispatch" clause) or into the codex/agy
  children (AC-3.4). Today `HPW_AGENT_BACKEND` is exported into the wrapper shell for codex/agy;
  that stays byte-identical.
- **Region scoping reuses `pre_lines`.** The grok branch captures `pre_lines` exactly as the agy
  branch does, and every grok reader (final message, last-tool line, truncation check,
  auto-log digest) reads only lines after it. **Residual (reasoned from `wc -l` counting
  newlines, not executed):** a caller log without a trailing newline merges its last line with
  grok's first, which the line-skipping parsers then drop — the agy path's `pre_lines` has the
  same property.
- **Self-containment.** The HemaSuite `_MARKERS` path in FR-3 is a documentation citation only.
  No code or test in this feature reads a path outside the skill's own directory
  (`.h-mad/invariants.md` §"Skill self-containment").
- **No new dependency.** `jq` is already required on the agy parse paths; the grok CLI is a
  runtime option of `exec grok`, never needed by the suite, which runs against the stub.

## Deliverables

| Deliverable | Target file(s) | Satisfies |
|---|---|---|
| `fallback_agent` optional property with the four-part `description` | `h-mad/scripts/h_mad_state_schema.json` | FR-1 |
| Type-preserving, fail-closed `fallback_agent` read for `ACTIVE`, and the BLOCK-GROK / BLOCK-INVALID branches, inside the codex-authorship block | `h-mad/hooks/h-mad-tdd-gate.sh` | FR-2 |
| `exec grok`: valid set, argv builder with `--prompt-file`, option translation, child-only env scrub, `pre_lines` capture, direct `>>` redirect into `--log` | `h-mad/scripts/hmad-dispatch.sh` (`_cmd_exec`) | FR-3 |
| Grok final-message segmenter, completion check, structured-only recovery, stopReason line, last-tool line, auto-log digest | `h-mad/scripts/hmad-dispatch.sh` (new helpers beside `_agy_ndjson_response` / `_agy_last_step`; `_cmd_exec` EMPTY path) | FR-4 |
| `grok-ndjson` token and its renderer | `h-mad/scripts/hmad-dispatch.sh` (`_exec_log_format`, `_render_progress`) | FR-5 |
| `scan_grok()` and the CLI's grok branch | `h-mad/scripts/h_mad_review_evidence.py` | FR-6 |
| `--surfaces` accepts `grok` | `h-mad/scripts/hmad-dispatch.sh` (`_cmd_audit_cycle`) | FR-7 |
| `grok` / `grok-truncated` effort shapes, closed-world `combine()` routing, `_effort_items()` rendering | `h-mad/scripts/h_mad_audit_cycle.py` (`measure_effort`, `combine`, `_effort_items`) | FR-7 |
| `--agent {codex,grok}`, not-given `--timeout` sentinel (judged on presence in argv, never on value, so an explicit `--timeout 900` under grok stays 900), 1500 s grok default | `h-mad/scripts/h_mad_assemble_tdd.py` | FR-8 |
| `grok` agent: last-`end` `modelUsage` reader and its refusals | `h-mad/scripts/h_mad_resolved_model.py`; usage comment of `_cmd_resolved_model` | FR-9 |
| Phase-5 (incl. the `no write-time test-first gate` disclosure), exec, teammate-leg and never-gate-on-one-pass sections; D4 statement in two places | `h-mad/SKILL.md` | FR-10 |
| `fallback_agent` (and `codex_status`, P6) field semantics | `h-mad/references/state-schema.md` | FR-10 |
| `exec grok` verb, argv, env handling, inherited `GROK_SANDBOX` (FR-3; AC-10.2 needle) | `h-mad/references/agent-substrate.md` §"Verbs" | FR-10 |
| `grok` stub | `h-mad/tests/stubs/grok` | FR-3–FR-5, FR-7 |
| F0-derived fixture builder (one helper) and F0 sha256 check | `h-mad/tests/` (new helper module) | FR-4–FR-7, FR-9 |
| New test files for FR-1–FR-10, including the 80-cell gate matrix, the 16-cell × 3 base comparison, AC-2.1b's 24 BLOCK-INVALID cells with its 3-cell JSON-`null` control and its 8 BLOCK-CODEX cells, the two-instrument agreement test, and the mixed agy+F0 precedence fixture (W5–W7) | `h-mad/tests/` (new files) | FR-1–FR-11 |
| Heading-located doc test (fails, never skips, on a missing heading) | `h-mad/tests/` (new file) | FR-10 |
| Gate mutation spec, three rows (AC-2.7) | `h-mad/tests/mutation-specs/` (new JSON) | FR-2 |
| Mutation specs for the parser, evidence and shape guards (see Success Criteria) | `h-mad/tests/mutation-specs/` (new JSON) | FR-4, FR-6, FR-7 |

## Connection enforcement (the feature is partly wiring-shaped)

Several deliverables are connections: an existing caller must reach a new callee. Each is a
`wiring`-shaped task with a `WIRE` / `WIRE-PIN`, and Phase 5 runs the wire-scoped revert —
remove the call site only, callee and tests intact — plus the force-fire mutation in the other
direction (`invariants.base.md` §"Connection enforcement"). A RED whose reason is a missing
symbol is a wrong-reason RED and halts.

| Wire | Call site → callee | `WIRE-PIN` (remove) | Force-fire must fail |
|---|---|---|---|
| W1 | `_cmd_exec` agent dispatch → grok argv builder | AC-3.1 fails: argv lacks `--prompt-file`, carries `--print` | grok argv builder taken for every agent → `test_hmad_dispatch_exec.py::test_codex_exec_runs_headless_with_the_right_flags` and `::test_agy_exec_runs_print_headless_prompt_as_last_arg` fail: the codex/agy stub's recorded argv carries `--prompt-file`/`--always-approve`, not its own flags |
| W2 | `_cmd_exec` → grok child env scrub | AC-3.3 fails: a `CLAUDE*` var reaches the stub | scrub applied to codex/agy → AC-3.4 fails: the codex/agy stub no longer sees the caller's `CLAUDE*` vars |
| W3 | `_cmd_exec` → grok segmenter, scoped by `pre_lines` | AC-4.1 fails: stdout is not `STATUS: DONE` | (a) segmenter run for every agent → `test_hmad_dispatch_exec.py::test_agy_exec_stdout_is_the_response` fails: an agy log holds no grok `text` event, so stdout is empty and rc is 3; (b) scoping forced off (segmenter reads the whole `--log`) → AC-4.7 fails: the previous dispatch's `STATUS: DONE` is recovered and rc is 0 |
| W4 | `_cmd_exec` EMPTY path → grok last-tool line | AC-4.6 fails: no `2 tool calls completed` line | line emitted with no `tool_call` in region → the omission clause fails |
| W5 | `_exec_log_format` → `grok-ndjson` → `_render_progress` grok branch | AC-5.1/5.2 fail | grok checked before agy → AC-5.1's "one agy `{"event":"init"}` line and F0 prints `format: agy-ndjson`" fails (prints `grok-ndjson`). Discriminates: the log holds both families, so only the order decides |
| W6 | evidence CLI `main` → `scan_grok` | AC-6.1 fails: F0 prints `UNREADABLE reason=unsupported_format` | `scan_grok` consulted before agy → the **mixed agy+F0 test** fails: the CLI's stdout and rc on (agy transcript + F0) must be byte-identical to its stdout and rc on the agy transcript alone, and the mutant prints a `format=grok` line. The existing agy-only CLI tests do **not** kill this: on an agy-only log `scan_grok` returns `None` and the mutant falls through to the agy path |
| W7 | `measure_effort` → `scan_grok`; `combine` → `grok-truncated` routing | AC-7.2/7.3 fail; AC-7.4 fails | (a) `scan_grok` consulted before `scan()`'s agy count → the **mixed agy+F0 test** fails: `measure_effort()` on the mixed log must equal its result on the agy transcript alone (shape `parsed`), and the mutant returns shape `grok`; (b) `grok-truncated` scored as a count → AC-7.4 fails |
| W8 | `_cmd_audit_cycle --surfaces` → `_cmd_exec grok` | AC-7.1 fails | every pass dispatched as `grok` regardless of its surface token → `test_hmad_dispatch_audit_cycle.py::test_verb_two_distinct_dispatches` fails its `argv[:1] == ["agy"]` assertion on each `_cmd_exec` call |
| W9 | hook → `fallback_agent` of `ACTIVE` | AC-2.1 BLOCK-GROK cells fail | read from another feature → AC-2.5 fails |
| W10 | assembler `--agent` → dispatch line and timeout default | AC-8.2 fails (incl. its explicit `--timeout 900` case) | (a) grok block emitted with no `--agent` → AC-8.1 (byte-identical to base) and `test_h_mad_assemble_tdd.py::TestCli::test_a_clean_assembly_prints_pass_and_the_command_block` (asserts `hmad-dispatch exec codex`) fail; (b) agent read from state → AC-8.5 fails |
| W11 | `h_mad_resolved_model` `choices` → grok reader | AC-9.1 fails (argparse refuses `grok`) | grok reader used for every agent → `test_h_mad_resolved_model.py::test_codex_reads_the_resolved_model_out_of_its_session_header` and `::test_agreement_between_the_two_newest_is_answerable` fail: a codex session header and an agy cli-log dir carry no `end` event, so the grok reader exits 2 with `RESOLVED-MODEL: UNKNOWN` |

**Rule over the column.** A force-fire must (1) name a mutation that makes the new callee run
where it must not, (2) name an existing or planned test whose input **contains what the callee
matches**, so the mutant's output differs, and (3) name the observation that differs. A
precedence mutation (a new reader consulted before an old one) is killed only by an input both
readers accept; an input only the old reader accepts is a fall-through and kills nothing — v1.1's
W6 had exactly that flaw. Sweep of all eleven rows against the rule: W1, W3, W8, W10 and W11 now
name existing nodes whose inputs the forced callee rejects or misreads; W2, W4 and W9 name spec
ACs whose inputs discriminate (AC-3.4 sets `CLAUDE*` vars; AC-4.6's omission clause has no
`tool_call`; AC-2.5 stores a different feature's value); **W5** was already sound, because AC-5.1
itself feeds a log holding both an agy line and F0; **W6 and W7(a)** shared the fall-through flaw,
since `measure_effort()` uses the same agy-first order, and both now use the mixed agy+F0
fixture. The mixed fixture is a **plan-authored test, not a spec AC**: an agy transcript of one
`view_file` step `ACTIVE` then `DONE`, followed by F0's 110 lines, built by the shared F0 helper.

**The mixed fixture already discriminates on today's tree** (executed at `8c631d3` with scratch
files, then deleted): on the agy two-line transcript alone and on that transcript + F0,
`h_mad_review_evidence.py` printed the same `EVIDENCE: PASS tools=1 ok=1 failed=0 thinking=0`
with rc 0 both times (`cmp` → identical); `_exec_log_format` returned `agy-ndjson` for both; and
`measure_effort()` returned the same dict (shape `parsed`, `agy_events` 2) for both. So the
equality holds on the unmutated code and the only way to break it is to let a grok reader win on
a log that also carries agy events. Residual: whether each force-fire *kills* is a prediction
until Phase 5 runs the mutation — the mutants cannot exist before the grok code does.

Every existing node named above collects, verified at `8c631d3` (unit: tests):

```bash
T=h-mad/tests; /opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider \
  "$T/test_hmad_dispatch_exec.py::test_codex_exec_runs_headless_with_the_right_flags" \
  "$T/test_hmad_dispatch_exec.py::test_agy_exec_runs_print_headless_prompt_as_last_arg" \
  "$T/test_hmad_dispatch_exec.py::test_agy_exec_stdout_is_the_response" \
  "$T/test_hmad_dispatch_audit_cycle.py::test_verb_two_distinct_dispatches" \
  "$T/test_h_mad_resolved_model.py::test_codex_reads_the_resolved_model_out_of_its_session_header" \
  "$T/test_h_mad_resolved_model.py::test_agreement_between_the_two_newest_is_answerable" \
  "$T/test_h_mad_assemble_tdd.py::TestCli::test_a_clean_assembly_prints_pass_and_the_command_block" \
  2>&1 | tail -1
# reading at 8c631d3: 7 tests collected
```

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| A binary `codex`/else test in `_cmd_exec` routes grok into the agy arm | grok receives agy's argv, and the OVERSIZE refusal fires on a file-delivered prompt | Every `$agent`-branching line in `_cmd_exec` gets a grok arm or a named test (census above); AC-3.1 and AC-3.5 are the behavioural backstop |
| The gate reads `fallback_agent` with `//` or `-r` | `false` and the string `"null"` fall through and let Claude write | Type-preserving read; AC-2.1b (8 values × 3 codex_out routes, each alone, with the JSON-`null` control, and its 8 BLOCK-CODEX cells with codex_out false); fail-closed on read failure |
| `combine()` scores an unrouted `grok-truncated` as a count | A cannot-measure leg reads as hollow, or as delivered | Closed-world shape routing plus a shape-enumeration test; W7 force-fire |
| Two instruments classify a grok log differently | `progress` shows one lens while the gate routes another | Shared seven-type criterion and one agreement test over both |
| A2: grok's stream schema changes | Parsers misread; a false zero or a false verdict | `None` / `UNREADABLE` / `grok-truncated` paths keep it a cannot-judge; FR-5's residual documented; the F0 sha check makes a fixture edit visible |
| Grok writes with no write-time test-first gate (P13) | A grok GREEN can land untested production code; nothing blocks it at write time | Accepted, operator-decided: spec Out-of-Scope. RED/GREEN verdicts, the orchestrator's pytest re-run and the 5e revert test that establishes GREEN remain mandatory; the Phase-5 section discloses the gap (FR-10, AC-10.1 needle `no write-time test-first gate`) |
| `GROK_SANDBOX` in the operator's environment silently sandboxes the child (P11) | A dispatch fails or behaves differently with no flag in argv | Spec-mandated disclosure: FR-3 states the inheritance, FR-10 requires it in `agent-substrate.md`, AC-10.2 pins the needle `GROK_SANDBOX`; not scrubbed or defaulted (spec Out-of-Scope) |
| `--always-approve` grants unrestricted tool execution in `<cd_dir>` | Wider than codex's `workspace-write` default | Stated in FR-10 docs; accepted by the operator's choice of `fallback_agent=grok` |
| Stray `graft/` directory seen in the probe (finding 6) | Tree-delta output after a grok run over-counts | Tree delta reported, not trusted, for grok until a clean re-probe (spec Out-of-Scope) |
| Switching the audit legs from `doc-auditor` to `grok` mid-document | `h_mad_audit_gate.py` emits a `legs_changed:` reason when two cycles' leg sets differ (`grep -n legs_changed h-mad/scripts/h_mad_audit_gate.py`); its effect on a doc switching to `grok` was read, not executed | Phase 4 executes the case and the teammate-leg section documents the observed outcome |
| `exec grok` ships verified only against the stub, whose envelope is the author's model of F0 | The wrapper meets the real CLI for the first time in an operator's run | One bounded live smoke of `exec grok` before merge (Convention Prerequisites); a disagreement with F0 fixes the parsers against the observed envelope; a smoke that cannot run halts Phase 5 for the operator |
| No `jq` on PATH | The hook exits 0 before the block (existing fail-open); `exec grok` cannot parse | Hook behaviour unchanged by design and documented; `exec grok` takes the EMPTY path, never a false success (spec NFR) |
| The feature edits the live skill | A run in flight reads a half-built skill | Feature branch in a git worktree; both coupled suites before merge |
| A pre-existing test is deleted or edited while the count floor stays green | FR-11's guarantee silently false | Node-id floor (Success Criteria), and `git diff --numstat <base>` over pre-existing test files shows zero deleted lines |

## Convention Prerequisites

- Branch `feature/grok-codex-fallback` off `main`, created **as a git worktree**
  (`hmad-dispatch worktree-create` or `git worktree add`), at 5c. Record the fork sha as the
  feature's base; AC-2.2 and AC-8.1 compare against it.
- Codex authors Phase 5 under the TDD gate, RED before GREEN per module. If codex is out during
  this feature's own Phase 5, the fallback is today's `codex_status=exhausted` path — the
  feature's own `fallback_agent` does not exist on the live skill until merge (Architecture).
- **No AC and no pytest test makes a live xAI call** (spec: "No AC in this spec may require a
  live xAI call"); the grok CLI is never on the test `PATH`, only the stub is. **Exactly one live
  call is planned: a plumbing smoke of the new verb, not a quality measurement (D4 stays
  deferred).** `h-mad/invariants.base.md` requires "A wrapper verb over an **external runtime's
  CLI** MUST be exercised **live against that runtime**", and the only live grok run so far (F0)
  went through `hmad-dispatch run`, not `exec grok`. So, in Phase 5, **after** the tasks that
  ship FR-3 and FR-4 are GREEN and **before** merge, the orchestrator runs once from the feature
  worktree, in a scratch directory holding an `a.txt`, with F0's own prompt
  (`docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.prompt.txt`, about
  $0.04 at F0's measured `total_cost_usd=0.0393`):

  ```bash
  hmad-dispatch exec grok <F0 prompt file> --cd <scratch dir> --timeout 300 \
    --out <scratch>/smoke.out --log <scratch>/smoke.log; echo "rc=$?"
  grep -c '^STATUS: DONE' <scratch>/smoke.out      # a line-start STATUS: DONE (unit: lines)
  hmad-dispatch progress <scratch>/smoke.log       # must print format: grok-ndjson
  hmad-dispatch resolved-model grok --log <scratch>/smoke.log   # one RESOLVED-MODEL line, rc 0
  ```

  The record — the command, the rc, the `--out` content, the `progress` output and the
  `resolved-model` output — goes into the Phase-5 report and the feature's probe directory.
  Pass: rc 0, `--out` holds a line-start `STATUS: DONE`, `progress` names `grok-ndjson`, and
  `resolved-model` prints one validated line. Any other result is a halt: if the live envelope
  disagrees with F0, the parsers are fixed against the observed envelope (the invariant's second
  clause) and the smoke re-runs. **If the smoke cannot run** — no key, no quota, no grok on
  PATH — Phase 5 halts and asks the operator; a skipped smoke never passes silently, and merge
  does not proceed on "not run".
- Every guard mutation-verified with `h_mad_mutation_harness.py`; score on its `MUTATION:` token,
  never on `$?`. `SURVIVED` / `REFUSED` halts.
- Every wire in §"Connection enforcement" declared `wiring`-shaped with `WIRE` / `WIRE-PIN`, so the
  5b wire-pin gate sees it.
- Both coupled suites (`h-mad/tests`, `handoff/tests`) run in full — not scoped — before merge.
- Any probe written to confirm a suspected defect is deleted after it answers.

## Success Criteria

- All 54 spec ACs across FR-1–FR-11 pass automated tests. (Count: `grep -oE '^  - AC-[0-9]+\.[0-9]+[a-z]?'
  docs/01-plan/features/grok-codex-fallback.spec.md | sort -u | wc -l` → 54 distinct AC ids at
  `42511c3`; unit: distinct ids. It moves only if the spec is revised. v1.0's grammar
  `AC-[0-9]+\.[0-9]+` still reads 53 at `42511c3` because it truncates `AC-2.1b` to `AC-2.1` and
  deduplicates it away — the new id is invisible to it, so the grammar gained the letter suffix.
  Cross-check: `grep -oE 'AC-[0-9]+\.[0-9]+[a-z]?'` over the whole spec, any indentation, also
  reads 54, and the two id sets are equal under `comm -3`.)
- **Node-id floor.** Every test node id collected from `h-mad/tests` and `handoff/tests` at the
  base is collected at HEAD and passes, except the one environment-dependent failure named in
  the baseline if it still fails for the same reason. Command: `pytest --collect-only -q
  h-mad/tests handoff/tests 2>&1 | grep '::' | sort` at base and at HEAD, then `comm -23 base.txt
  head.txt` must print nothing. A count floor is not used, because a deletion and an addition
  cancel in a count.
- Pre-existing test files are append-only: `git diff --numstat <base> -- <each pre-existing test
  file touched>` shows `0` in the deleted column.
- AC-2.1b (counted in the 54 above) in full, including its own 8 BLOCK-CODEX cells: each of the
  8 values alone with codex_out false yields BLOCK-CODEX.
- The two-instrument agreement test passes on F0, F-SPACED, F-TRUNC, an agy log, a codex
  banner log and the mixed agy+F0 log (§"Connection enforcement"), on which both instruments
  must pick agy.
- The Phase-5 live wrapper smoke (Convention Prerequisites) ran and its record is complete; a
  skipped smoke is a halt, not a pass.
- The shape-enumeration test asserts an explicit `combine()` route for every shape
  `measure_effort()` returns.
- Mutation verification `ALL_CAUGHT` for: the three AC-2.7 gate rows; and, as further rows, the
  invalid-class read (`//` reintroduced, killed by AC-2.1b's `false` cells; `-r` string/`null`
  collapse reintroduced, killed by AC-2.1b's `"null"` cells against its JSON-`null` control),
  segment closers (drop `usage` from the closer set),
  decoy exclusion (`thought` data appended), `pre_lines` scoping dropped, `ok` counted by
  substring, the truncated evidence branch publishing counts, and `grok-truncated` removed from
  its `combine()` route.
- Each of W1–W11 fails its `WIRE-PIN` under a wire-scoped revert, with a caller-behaviour RED
  reason, and each force-fire row fails its named test.
- The doc test fails, rather than skipping, when any FR-10 heading is removed (verified by
  deleting one heading in a scratch copy and running the test).
- Both coupled suites green in full before merge.

## Out-of-Scope (confirmed from spec)

- Live measurement (D4): grok GREEN, mutation-kill, wiring-pin and audit-leg precision, cost,
  quota and latency — a separate follow-up feature. The single Phase-5 plumbing smoke of `exec
  grok` (Convention Prerequisites) is in scope and measures none of these.
- The grok pane path: `send`, `ask`, `launch`, `exec-pane`, `pin`, `verify`, `resolve` (AC-3.7).
- A grok 6a-prime reviewer; `h_mad_archreview_cycle.py` stays agy-only.
- A failed-tool-status branch; `unresolved` stands in until a failure spelling is captured.
- Choosing a grok `--sandbox` profile, and scrubbing or defaulting `GROK_SANDBOX` (FR-3).
- A write-time test-first gate for grok (P13); the Phase-5 section discloses it (FR-10).
- A grok input-size ceiling or refusal detector.
- Completion-event reaping (`--complete-log`) for grok.
- The stray `graft/` directory seen in the probe; grok tree-delta is reported, not trusted.
- Rewording `h-mad/references/codex-implementer-prompt.md`.
- Any change to the `codex_status` enum (D1).

## Next Steps

Operator reviews and approves v1.2 → Phase 3 audit cycle on the live skill's surfaces (grok is
not a surface until this feature merges; if codex is out, the teammate leg per `h-mad/SKILL.md`
§"Teammate audit leg — when codex is unavailable" applies) → gate until must-fix = 0 → Phase 4 design.
Of v1.0's owed items, the sidecar commands and the P13 write-gate disclosure are closed by spec
v1.1 and `7d2f780`; the `state-schema.md` sibling-field note (P6) stays, as an
orchestrator-approved superset of FR-10.

## Version History
- v1.0: Initial plan draft (2026-09-28), from spec v1.0 at 1680271. Premises P1-P13 and the suite baseline executed at 1680271; adds the closed-world combine() routing rule, the type-preserving fallback_agent read with an invalid-class supplement, the _cmd_exec agent-arm census, the node-id suite floor, and the W1-W11 wiring table.
- v1.1: Revised to spec v1.1 at 42511c3 (2026-09-28). The invalid-class supplement folds into the spec AC-2.1b (8 values x 3 codex_out routes = 24 BLOCK-INVALID cells, JSON-null FALL-THROUGH control); the plan keeps 8 BLOCK-CODEX cells beyond it. P1 records that the sidecar carries the re-derivation commands since 7d2f780, except the null-status and line-prefix counts the spec writes inline. P11 and P13 cite the now spec-mandated GROK_SANDBOX disclosure and write-gate Out-of-Scope entry, the latter mitigated also by the 5e revert test. FR-8 sentinel is presence-judged (AC-8.2 explicit 900). AC census re-derived with a suffix-aware grammar: 54 distinct ids (the v1.0 grammar hid AC-2.1b).
- v1.2: Answers plan audit cycle 1 at 8c631d3 (2026-09-28). One bounded live plumbing smoke of exec grok added as a Phase-5 pre-merge step (not an AC, not a D4 measurement; a smoke that cannot run halts for the operator). Wiring table: force-fire named for W1, W3, W8, W10 and W11 against existing test nodes (collection verified); W6 and W7 precedence mutations killed by a new mixed agy+F0 fixture, executed as equal on the unmutated tree; W5 confirmed to discriminate via AC-5.1. The 8 BLOCK-CODEX cells are reworded as part of AC-2.1b, not a plan addition. P8, P10 and P13 carry their commands; the P11 rc-2 claim executed under a network-denied sandbox. Interpreter pinned to /opt/anaconda3/bin/python -m pytest.
