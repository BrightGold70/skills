# Design: pin-agents-tail-banner

## Executive Summary

Insert a standalone tail-evidence pass into `_orca_find` between Pass 2 and Pass 3, reusing
the tail-only `_agent_tail_re` banner grammar against `.result.terminal.tail` — NOT the shared
`_agent_pv_re`, which matches prose 24/24 — resolving only on exactly one match.

## Overview

The pass exists because Passes 0–2 and Pass 3 can all miss the same live pane, and because
the two obvious placements are both wrong: inside Pass 3 it would be gated on `lsof`, and
inside Pass 2 it would be gated on `n == 0` and so never see an ambiguous title. It is
therefore its own step with its own entry condition. Every design choice below is driven by
one asymmetry: an unresolved agent costs a manual pin, a wrongly resolved one dispatches
into a stranger's shell.

## Architecture Overview

```
_orca_find <token>
  ├─ $scoped ............ worktree-scoped terminals, caller's own pane already excluded
  ├─ Pass 0  paneKey join ................... resolve on 1 ─────────────► return
  ├─ Pass 1  title (anchored, rival-rejecting) ... resolve on 1 ───────► return
  │            n>1 ─┐                    n==0 ─┐
  ├─ Pass 2  preview via _agent_pv_re  ◄────────┘  (ONLY when n==0)
  │            resolve on 1 ───────────────────────────────────────────► return
  ├─ Pass 3* tail via _agent_tail_re   ◄──┘  NEW — entered when n != 1, no lsof needed
  │            resolve on exactly 1 ───────────────────────────────────► return
  └─ Pass 4  OS evidence (was Pass 3) ....... needs lsof; unchanged ───► return / decline
```

The new pass is numbered 3 and the OS-evidence pass renumbers to 4. Pass 4's opening
comment currently reads "Reached only when every pass above found nothing" — that sentence
becomes false on insertion and is updated in the same edit.

## Detailed Design

**Entry condition.** Reached whenever control falls past Pass 2 — i.e. `n != 1`. No `lsof`
precondition, no `n == 0` precondition.

**Candidate set: `$scoped`, unconditionally.** Both entry paths use the same pool, because
Passes 1 and 2 are MATCHERS, not filters — they select, they do not remove anything from
consideration. An earlier draft narrowed the `n > 1` case to Pass 1's `$ids` while justifying
the `n == 0` case with "they removed nothing", which is self-contradictory: if nothing was
removed, both pools are `$scoped`. The audit caught the inconsistency and the plan already
said `$scoped` for both, so the narrowing was silent drift, not a decision.

`$scoped` is the right pool on the merits too. It is already worktree-scoped and already
excludes the caller's own pane, and tail evidence is stronger than a title match — so a pane
Pass 1 failed to match on an inherited title is exactly the pane this pass should be able to
identify. Widening does not weaken the safety property — but NOT because a wider pool can only
turn a resolution into a decline. That claim was here until impl-plan audit v23 and it is
backwards: adding one uniquely banner-matching pane turns a decline INTO a resolution, which is
precisely this feature's intended path. The safety rests on three things that hold at any pool
size: `$scoped` is already bounded to the worktree and excludes the caller's own pane, so
widening cannot reach a pane the caller had no business resolving; every candidate must match
the agent's own banner predicate and must NOT match a rival's; and exactly-one still gates the
resolution, so a second matching pane declines rather than picking. A wider pool changes which
panes are eligible, never the test each one has to pass.

**What `_agent_pv_re` actually matches — the banner, never the launch command.** The helper is
left unchanged and continues to serve Passes 1-2; the tail pass does NOT use it (see the
`_agent_tail_re` rule below). It matches *program banners* (`openai codex`, `model: *gpt-`, a model id
paired with a reasoning effort; `antigravity cli`, `gemini [0-9]`) because the bare tokens
`codex`/`agy` were removed from it after a coordinator pane resolved as Codex. Measured
2026-09-01 with passing controls: `codex '--dangerously-bypass-approvals-and-sandbox'` and
`agy '--dangerously-skip-permissions'` are **NO MATCH** for their own agents, while all four
banner and status-line controls MATCH. Spec v1.5 narrows AC-1.1 to the banner and inverts
AC-1.2 accordingly; do not "fix" this by widening `_agent_pv_re`, which would also widen Pass 1's
rival rejection and Pass 2's preview match and re-admit the false-positive class those patterns
exist to exclude.

**The tail pass uses its OWN line-complete banner grammar, `_agent_tail_re`, for BOTH the wanted
and the rival check; `_agent_pv_re` itself is unchanged.** A line anchor alone is not enough and
neither is a leading-position grammar: measured across 24 prose probes, the shipped regex declines
0, a line anchor 7, a leading-position grammar 14, a line-complete shape 19, and only the
bounded, independent `_agent_tail_re` literals — the banner must
consume its whole line, allowing just a version, a `model:` field, an effort word, a `·` and a cwd,
— the banner must consume its line, allowing only a dotted-numeric version, a DOTTED model id, an
effort word, a `·` and a cwd, or an effort/version parenthetical, behind a prefix of whitespace or
box-drawing characters only — declines all 24, with all 12 real banner and status
lines still matching. The rival check uses the same helper: applying the shared `_agent_pv_re` there rejected a
real agent pane for merely MENTIONING the other agent, the mirror false-negative (impl-plan AC-4.6,
mutation `rival-re-prose-unsafe`). The
helper is NOT hardened against prose, and the claim that it was is falsified: measured 2026-09-01,
`Release notes for OpenAI Codex are available`, `I am comparing model: gpt-5.6-terra with ours`,
`The Antigravity CLI documentation changed` and `Compare Gemini 3.1 Pro with Claude` all MATCH it,
and a seven-probe corpus reproduces that 7 for 7. It is hardened against the two examples that
motivated it (`comparing gpt-5 output with ours`, `the codex agent is running`) and no further.
That matters only for THIS pass: `$scoped` includes ordinary shell panes and tail evidence is
historical, so a shell that once printed release notes was resolvable AS THE AGENT — the
wrong-pane class FR-2 forbids. Passes 1 and 2 read short titles and previews rather than arbitrary
scrollback, so the anchor is applied where the tail pass builds its matcher and nothing shared
moves. `_agent_tail_re` is a NEW independent helper — not an anchor applied to the old one, and
not the agent's existing signature. Measured over the 24-probe corpus: 0 of 24 prose probes match and 12 of 12 real banner and
status lines still do. Pinned in two places, deliberately: impl-plan **AC-2.12** tests the helper's own 24/12 corpus in
the task that defines it, and **AC-3.17** tests the caller CONNECTION with a mixed
banner-plus-prose-decoy fixture. Mutations `tail-re-unanchored` and `tail-re-unanchored-agy`
(one per agent arm) are killed by AC-2.12.

**Per-candidate test.** For each candidate handle, read the tail with exactly this command
and match the agent's `_agent_tail_re` grammar; reject a candidate whose tail matches the RIVAL's
signature before counting it:

```sh
_cmd_run --timeout "${HMAD_TAIL_READ_TIMEOUT:-2}" -- \
  orca terminal read --terminal "$h" --cursor 0 --limit 4000 --json
```

**`_cmd_run` in-process, NOT `hmad-dispatch run` as a subprocess.** Naming the verb says *which*
bounder (`timeout`/`gtimeout` are forbidden outright); taken literally it re-execs the wrapper by
name, which is not on the test harness's `PATH` (`_bindir:/usr/bin:/bin`) and costs a process per
candidate. `_cmd_run` is the function `main` dispatches that verb to — same bounder, same exit-124
convention — and bash resolves it at call time, so `_orca_find` calling a function defined below
it is fine.

**`.result.terminal.tail` is a JSON ARRAY of line strings, not a string.** Measured live
2026-09-01 against the pinned codex pane: `type == list`,
`["codex '--dangerously-bypass-approvals-and-sandbox'", "", "…"]`. The response listing below
records the key as *present* and did not record its type, and `h-mad/SKILL.md` already spells it
`.result.terminal.tail[]`. A bare `jq -r '.result.terminal.tail'` on an array prints
pretty-printed JSON — brackets, quotes, commas — which still substring-matches a signature, so
the mistake fails no test written from this design and ships a matcher over a shape nobody chose.
Check the ENVELOPE VERDICT first, then join:

```
if (.ok? // false) != true then empty
else (.result.terminal.tail? // empty) end
| if type == "array" then join("\n") else empty end
```

**`.ok` first.** An Orca error envelope exits 0 and still carries a `result` object, so the
process rc and key-presence both read "fine" while the payload is an error — the F11 class
`_cmd_worktree_rm` is already guarded against. Here it is worse than a wrong rc: partial or stale
tail text inside a FAILED read becomes identity evidence and this pass resolves a handle from it.
That is the only FR-4 direction that RESOLVES; every other one declines. Verified 2026-09-01 that
a real `terminal read --json` carries top-level `ok: true`. Pinned by impl-plan AC-2.9 and mutation
`envelope-ok-false-accepted`.

**`else empty`, not `else tostring`.** The measured live shape is an array; `tostring` accepted
every other non-null type, so a malformed payload that merely CONTAINS a banner became identity
evidence by the same unsafe route. Pinned by impl-plan AC-2.10 and `non-array-tail-accepted`.

`// empty` stays before the type branch as defence in depth, NOT as an independently pinned
guard: with `else empty` on the type branch a null from an absent key is discarded there anyway
(measured identical with and without it on four inputs). `-e` is the load-bearing part, but not
for the reason stated here until impl-plan audit v26: with `// empty` AND the final `else empty`,
`jq -r` on a missing tail emits zero bytes at rc 0 — not the literal `"null"`, which is what the
simpler `.tail | tostring` probe filter produces. The hole `-e` closes is the RC: without it,
empty output exits 0 and an unreadable pane reads as a readable empty one. Audit v21 removed the
mutation that claimed to pin `// empty` alone, because it was equivalent.

**`--cursor 0` is load-bearing and must not be dropped.** Without it the call returns the
most RECENT rows, while the agent's banner sits at the START of scrollback. On the panes
measured 2026-09-01 the mistake is invisible — their whole scrollback is 12–18 lines, so head
and tail coincide and a naive read passes a live check — and it surfaces only later, on a
pane with history, as an UNRESOLVED nobody can explain. The matched field is
`.result.terminal.tail`; `.content`, `.output` and `.preview` are absent and reading them
returns nothing in a way indistinguishable from an empty pane.

`timeout`/`gtimeout` are forbidden unconditionally by the base invariant and are never
INVOKED; AC-4.3 asserts that mechanically, on COMMAND POSITION rather than substring presence,
so the comment above that names them is free.

**Extraction: `jq -re`, never `jq -r`. Measured 2026-09-01:**

```
$ echo '{"result":{"terminal":{"handle":"h1"}}}' | jq -r  '.result.terminal.tail' ; echo rc=$?
null
rc=0
$ echo '{"result":{"terminal":{"handle":"h1"}}}' | jq -re '.result.terminal.tail' ; echo rc=$?
rc=1
```

`-r` prints the literal `null` and exits **0** for an absent key **in the simple
`.result.terminal.tail` probe filter measured here** — NOT in the prescribed filter, which adds
`// empty` and `else empty` and emits zero bytes at rc 0 (see above; `-e` closes the RC hole).
With that caveat the probe still shows why the "no `.terminal.tail`
key → unreadable" requirement (FR-4) would be silently bypassed and a keyless response would
be scored as a pane whose tail is the string "null" — a non-match rather than an unreadable.
`-e` is what makes the missing key a non-zero status.

**Observed response shape, cited rather than asserted** (`orca terminal read --terminal <h>
--cursor 0 --limit 3 --json`, live, 2026-09-01):

```
top-level keys       : ['_meta', 'id', 'ok', 'result']
.result keys         : ['terminal']
.result.terminal keys: ['handle', 'latestCursor', 'limited', 'nextCursor',
                        'oldestCursor', 'returnedLineCount', 'source', 'status',
                        'tail', 'truncated']
.terminal.tail    : present
.terminal.content : ABSENT
.terminal.output  : ABSENT
.terminal.preview : ABSENT
```

That listing also names a field worth knowing for the retention risk: **`.terminal.truncated`**
reports whether the response hit a cap, so a future revision could distinguish "this pane has
no signature" from "this pane's signature scrolled past the 2000-line limit". Out of scope
here — recorded because the shape was measured anyway and the distinction is exactly the one
the Risks table calls the load-bearing unknown.

**The timeout carries its own default, `${HMAD_TAIL_READ_TIMEOUT:-2}`.** `set -u` is on, so a
bare `"$HMAD_TAIL_READ_TIMEOUT"` aborts the whole wrapper the first time this pass runs in a
shell that never exported it — the parameter expansion is not defensive style, it is what
keeps an unset variable from being a crash.

**The bound is sequential and stated exactly, not as "a few seconds".** Reads run one after
another, so the worst case is `candidate_count × HMAD_TAIL_READ_TIMEOUT` plus per-call overhead —
at the default that is 2 s per candidate in `$scoped`, and nothing in the spec caps
`candidate_count`. A worktree with 10 panes and every read hanging therefore costs ~20 s, not
"a few". Two things keep that acceptable rather than needing a cap: a `terminal read` is a local
IPC call so the timeout is nowhere near reached in practice, and the pass only runs at all when
Passes 0–2 failed to resolve, which is the path that otherwise ends in `UNRESOLVED` and a manual
pin. Lower `HMAD_TAIL_READ_TIMEOUT` if a pool is large enough for the product to matter.

**Resolution.** Exactly one surviving match → print it, return 0. Zero or more than one →
fall through to Pass 4 unchanged. The pass never returns non-zero itself; falling through IS
its decline.

**Unreadable is not non-match.** A read that errors, times out, or lacks `.terminal.tail`
excludes the candidate from BOTH the match set and the rival set. It cannot create a false
resolution and cannot suppress a real one by manufacturing ambiguity.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_orca_tail_sig` | `h-mad/scripts/hmad-dispatch.sh` | new | read one pane's tail, bounded; echo it or fail |
| tail-evidence pass | `h-mad/scripts/hmad-dispatch.sh` | modify `_orca_find` | the pass itself, between Pass 2 and Pass 4 |
| Pass 4 comment | `h-mad/scripts/hmad-dispatch.sh` | modify | "every pass above found nothing" is no longer true |
| Retention-cap comment at the new pass | `h-mad/scripts/hmad-dispatch.sh` | new | AC-5.1 + AC-5.2: records the measured 2000-line cap, that agent TUIs do not normally reach it, that a shell-heavy pane fails to UNRESOLVED, and that BELOW the cap a stale banner still resolves |
| `_orca_find` prose | `h-mad/SKILL.md` | modify | line ~320 reads "joins them as **Pass 0**, ahead of the title and preview passes" — incomplete once a tail pass exists between preview and OS evidence |
| `_agent_tail_re` | `h-mad/scripts/hmad-dispatch.sh` | **add** | new top-level helper: the tail-only, line-complete banner grammar per agent. Ships in impl-plan T2 beside `_orca_tail_sig`, unconsumed until T3. |
| tests | `h-mad/tests/test_hmad_dispatch.py` | modify | 16 ACs (count from the spec, never carry it — this cell was stale once) |
| mutation spec | `h-mad/tests/mutation-specs/tail_signature_pass.json` | new | guard discrimination |

## Implementation Order

1. `_orca_tail_sig` **and `_agent_tail_re`** + their unit tests, including the matcher's direct
   24-negative/12-positive corpus (no `_orca_find` change yet — both helpers are proven alone).
   Both land in impl-plan Task 2; step 2 consumes the matcher, so it cannot be deferred past here.
2. The pass, entered on `n != 1`, resolving on exactly one.
3. Rival rejection.
4. Unreadable-candidate handling.
5. Pass 4 comment correction.
6. `h-mad/SKILL.md` prose update — the pass list there is user-facing documentation of this
   exact mechanism, and it is the one surface no test covers, so it is an ordered step rather
   than a tidy-up. Frontmatter is untouched: no entry behaviour changes.
7. Mutation spec.

## Data Model / Schema Changes

None. No state key, no pin-file field, no config.

## API / Interface Changes

None user-facing. TWO new private shell functions:

```sh
_orca_tail_sig <handle>   # stdout: the pane's tail text (possibly empty)
                          # rc 0 = read succeeded; rc 1 = read failed/unreadable
                          # runs: _cmd_run --timeout <s> --   (in-process, not the verb)
                          #         orca terminal read --terminal <h> --cursor 0 --limit 4000 --json
                          # extracts: .result.terminal.tail

_agent_tail_re <codex|agy>  # stdout: the TAIL-ONLY banner/status grammar for that agent
                            # line-complete, bounded; independent literals per agent
                            # NOT a wrapper around _agent_pv_re, which is left to Passes 1-2
                            # used by BOTH the wanted and the rival check in the tail pass
```

**The ONLY sanctioned call form captures stdout and tests the status in one step:**

```sh
local out                              # declare SEPARATELY — see below
if out="$(_orca_tail_sig "$h")"; then
  # $out holds the tail; match it here
fi
```

**`local out` must be its own statement. Never `if local out="$(…)"; then`.** `local` is a
COMMAND, so the compound form returns *`local`'s* status — always 0 — and the helper's rc is
discarded. Measured 2026-09-01:

```
plain assign : took ELSE (correct, rc seen)
local assign : took THEN (WRONG — rc masked by local)
```

The trap is that the broken form is what an implementer practising clean scoping writes. It
reads as tidier, it is syntactically valid, and it silently converts every unreadable pane
into a readable one with an empty tail — defeating FR-4 in the same direction `jq -r` would
have. Two idioms in this one pass fail that way, which is why both are pinned by measurement
rather than described.

Two constraints meet in that line and both are load-bearing. `set -euo pipefail` is on and
rc 1 is an ANSWER, not an error, so the call must sit in a condition context or the wrapper
aborts where it meant to branch. And the helper writes the tail to **stdout**, so a bare
`if _orca_tail_sig "$h"; then …` — which an earlier draft of this design explicitly licensed —
does not capture it, and the pane's entire scrollback streams straight into `_orca_find`'s
own stdout, corrupting the handle it returns. That is the same stdout-contract defect the
Error Handling section fixes for the `[H-MAD]` line, reintroduced one section away by an
example; it is called out here so the next reader sees why the bare form is banned rather
than merely unused.

## Error Handling Strategy

Return codes, never exceptions. **`_orca_find` returns the bare handle on STDOUT — that is
its contract, and every diagnostic in this file goes to stderr for that reason (104 `>&2`
redirections).** The one `[H-MAD]` line this pass emits on a successful resolution therefore
goes to **stderr**, explicitly:

```sh
echo "[H-MAD] $token: bound $h by tail evidence" >&2
```

An earlier draft said "nothing new is written to stderr on the happy path" and then described
emitting that line, which is both self-contradictory and dangerous in one specific direction:
an implementer resolving the contradiction the other way would send it to stdout, and
`_orca_find` would return "handle + log line" to every mechanical consumer — `env`, `resolve`,
`send`, the pin file. The line is worth keeping because it lets an operator tell this pass
from Pass 0/1/2 in `env` output, so it is exempted by name rather than removed.

Declining is silent. Pass 4 already owns the diagnostics for "live process, pane not
determined", and a second explanation for one failure is worse than none.

## Test Strategy

Unit, at the wrapper boundary, using the existing `_bindir`/`run()` harness and a stub
`orca` fed by `HMAD_STUB_ORCA_STDOUT`. The stub must serve BOTH `terminal list` and
`terminal read` — the existing stub answers one payload, so it needs a shape that
discriminates on argv. No live-runtime dependency in the suite; the live check is a
separate manual step in Success Criteria.

## Test Plan

| # | Scenario | Pins |
|---|---|---|
| 1 | one candidate, tail carries the vendor/model banner | AC-1.1 |
| 2 | one candidate, tail carries the launch line ONLY → does NOT resolve | AC-1.2 |
| 3 | `env` reports the handle rather than UNRESOLVED | AC-1.3 |
| 4 | two candidates both match → decline | AC-2.1 |
| 5 | zero matches → decline | AC-2.2 |
| 6 | candidate carrying the RIVAL signature is rejected pre-count | AC-2.3 |
| 7 | Pass 0 resolves → no `terminal read` issued at all | AC-3.1 |
| 8 | a pane excluded from `$scoped` is never selected | AC-3.2 |
| 9 | ambiguous title (>1) reaches the pass; no `lsof` still reaches it | AC-3.3 |
| 10 | unreadable candidate excluded, not counted as non-match | AC-4.1 |
| 11 | all candidates unreadable → decline | AC-4.2 |
| 12 | no line INVOKES `timeout`/`gtimeout`; prose and comments naming them are free | AC-4.3 |
| 13 | retention limit documented at the pass | AC-5.1 |
| 14 | stale-pane limit documented at the pass | AC-5.2 |
| 15 | exit-0 `"ok":false` envelope, and a non-array `.terminal.tail`, both decline rather than resolving | AC-4.4 (impl-plan AC-2.9, AC-2.10) |
| 16 | tail carrying the agent's name only in PROSE declines; real banner and status lines still resolve | AC-1.4 (impl-plan AC-3.17) |
| 17 | a real banner PLUS rival prose still resolves, both directions; real rival banners still rejected | AC-1.4 (impl-plan AC-4.6) |

Test 7 is the one that can pass vacuously — assert on the STUB's call count, not on the
resolution, or it merely restates Pass 0.

**Verification, in order — all three items the plan's Success Criteria require:**

1. **RED before GREEN — per NODE, not blanket.** The 5d dispatch states expected failing and
   passing counts so an unexpected pass halts. It must NOT claim every new test fails: this
   feature's suite contains *preservation* and *negative* nodes that are legitimately green
   before any code exists (the legacy stub path, "a launch-command-only tail does not resolve",
   "zero matches decline", "no read is issued when Pass 0 resolved", "frontmatter unchanged").
   Measured on the node enumeration: **32 of 45 nodes fail at RED and 13 pass**, so a blanket
   claim would halt a correct dispatch on `step5d:red_not_all_failing`.

   Every node green at RED carries a named reject-direction proof instead — a mutation whose
   `mechanism:` line must name that node, or, for the `timeout`-invocation invariant, an explicit
   insert-observe-remove procedure. The impl-plan's §"Test-name contract" is the authoritative
   table; derive counts from it at dispatch time rather than reading a number from prose.

   This is not ceremony here: `cn == 1` with `lsof` present already resolves today, so a
   carelessly written test passes with the whole feature reverted.
2. **Suites and mutation.** `pytest h-mad/tests/test_hmad_dispatch.py -q -k orca_find`, then
   the full `pytest`, then `h_mad_mutation_harness.py` on the new spec, then
   `--check-anchors` under bash (never zsh — it does not word-split the candidate list).
3. **Live check — it must exercise THIS pass, not merely succeed.** `hmad-dispatch env`
   resolving codex is NOT sufficient evidence: Pass 0, the title pass, the preview pass or an
   ambient pin can each satisfy it without a single `terminal read`, so the check would pass
   with the whole feature reverted. Require all four:

   1. Run against an **isolated** `HMAD_ORCA_PIN_FILE`, never the repository's real
      `.h-mad/orca-pins.env` — that file holds the operator's live coordinator and agent pins,
      and clearing it to verify an unrelated feature destroys state the check has no business
      touching. **Seed the isolated file with known dummy pins and confirm they are present**,
      then `pin-agents --clear`, then **re-read and confirm those handles are gone**. On a fresh
      path the file is absent before and after, so absence alone proves nothing — it holds
      equally if the clear never ran.
      Confirming that no `HMAD_ORCA_*_TERMINAL` is exported is necessary but not sufficient: it
      checks the ENVIRONMENT, a different surface from the pin FILE that `--clear` mutates, and a
      pin surviving in the file short-circuits `_orca_find` exactly as an exported one would.
      Verifying a surface other than the one you changed is the mutation-verification failure
      this project has shipped before.
   2. The earlier passes shown NOT to resolve on their own — `worktree ps` does not name the
      pane (Pass 0 blind), title and preview do not match (Passes 1-2 blind).
   3. `env 2>&1` carrying the **`bound <handle> by tail evidence`** marker, which this pass alone
      emits, so it is the only output that proves the tail pass produced the resolution.
   4. If a pane was created for the check, close it and **re-list terminals to confirm the
      removal**. Remove the isolated pin file's `mktemp -d` directory in the
      same step, or each run leaves an empty temporary directory behind — **and re-read to
      confirm it is gone**, since deleting a directory mutates state and the command is not its
      own proof.

## Invariant Compliance

- **Skill self-containment**: complies. The change is confined to `hmad-dispatch.sh` inside
  the h-mad skill; no other skill's internals are imported and no path outside the skill's
  own directory or the documented `~/.claude/...` install locations is introduced.
- **Skill manifest integrity**: complies. No entry behaviour changes, so `SKILL.md`
  frontmatter is untouched. Step 6 of the Implementation Order carries the doc edit. The
  `_orca_find` prose in `SKILL.md` DOES describe the pass
  structure and is updated to say four-plus-one passes rather than four.
- **Portable time bounds** (base): complies. The read is bounded with in-process
  `_cmd_run --timeout` — the function the `hmad-dispatch run` verb dispatches to, never the
  verb re-exec'd as a subprocess. No line INVOKES `timeout`/`gtimeout`; AC-4.3 asserts that on
  command position, so prose and comments naming them are free.
- **Audit-gate signal discipline** (base): not applicable — this pass returns a handle, not
  a verdict token, and emits no gate line.
- **Test discrimination** (base): complies. Every ENUMERATED mutation target is stubbed, and test 7 is
  called out as the vacuous-pass risk with the specific remedy.

## Version History
- v1.0: Initial design draft.
- v1.1: Design audit v1 (both passes, Axis C cross-doc) — the design had DROPPED the exact
  read command and the `--cursor 0` requirement that plan v1.5 mandated. Restored with the
  justification. This is the five-surface value sweep failing on the paired document: the
  fix was applied to the plan and never carried across, which is the surface it is most
  often missed on.
- v1.2: Design audit v2 — `${HMAD_TAIL_READ_TIMEOUT:-2}` given a default (an unset variable
  under `set -u` aborts the wrapper, so this was a crash, not a style point); spec AC-2.1,
  AC-2.2 and AC-4.2 reworded from "declines (rc 1)" to fall-through, since returning non-zero
  from `_orca_find` would short-circuit Pass 4.
- v1.3: Design audit v3 — the candidate pool is `$scoped` unconditionally (the `n > 1`
  narrowing was silent drift from the plan and contradicted this design's own "matchers, not
  filters" justification); the `[H-MAD]` resolution line is explicitly routed to stderr,
  because `_orca_find` returns the bare handle on stdout and the previous wording invited an
  implementer to corrupt it; the AC-5.1 retention comment added to the components table.
- v1.4: Design audit v4 — the helper's call form is pinned to the capturing
  `if out="$(_orca_tail_sig "$h")"; then`, because the previously licensed bare form streams
  the tail into `_orca_find`'s stdout and corrupts the handle (the same defect v1.3 fixed for
  the log line, reintroduced by an example); and the plan's three verification requirements
  (RED-before-GREEN, stated counts, the live check) were restored after being dropped — the
  second plan-to-design drop in this feature, after `--cursor 0`.
- v1.5: Design audit v5 — `h-mad/SKILL.md` added to the components table and as step 6 of the
  Implementation Order. Invariant Compliance had PROMISED that doc update while no component
  row or ordered step carried it, so an implementer following the steps would have shipped
  the code with the skill's own description of `_orca_find` left stale.
- v1.6: Design audit v6 — extraction pinned to `jq -re` with the measurement inline (`jq -r`
  prints `null` and exits 0 on an absent key, which would have bypassed the FR-4 unreadable
  path entirely); and the "confirmed live" claim about the response shape replaced by the
  cited listing, per the Axis B rule that evidence belongs in the document rather than in the
  author's terminal.
- v1.7: Design audit v8 should-fix — `local out` is pinned to its own line, with the
  measurement showing that `if local out="$(…)"` masks the helper's exit status behind
  `local`'s own 0. Third idiom in this pass whose tidy-looking form silently defeats a guard,
  after the bare `if _orca_tail_sig` and `jq -r`.
- v1.8: Back-propagated from impl-plan audit v5 (codex surface, operator-approved) — a new subsection records that _agent_pv_re matches the BANNER and never the launch command (measured with passing controls: both launch lines NO MATCH), which is what made spec AC-1.1 unsatisfiable while this design reused the helper unchanged; widening the helper is explicitly rejected because it would also widen Pass 1 rival rejection and Pass 2. Test Plan rows 1 and 2 inverted accordingly, row 14 added for the stale-pane limit, and the components row now carries AC-5.2: below the 2000-line cap an exited agent's banner still resolves.
- v1.9: Impl-plan audit v7 (codex) — the components table's '13 ACs' cell was stale after spec v1.5 added AC-5.2, and the latency claim 'the worst case stays a few seconds even on a busy pool' was unbounded: reads are sequential, so the real bound is candidate_count x HMAD_TAIL_READ_TIMEOUT and nothing caps the candidate count. Both stated exactly.
- v1.10: Impl-plan audit v8 (codex) — four of five must-fixes were defects in v1.5's own RED table. It was written at AC granularity while --expect-fail counts TEST NODES: two nodes carried two ACs each, putting one node in both columns and double-counting another, so the counts could never have matched a pytest run. Recast as a 35-node enumeration with one RED outcome each (24 FAIL / 11 PASS). The claim that every green-at-RED node was mutation-discriminated was FALSE - six had no proof and two were named by mutations that cannot kill them; seven mutations added (17 total), AC-4.2 withdrawn as genuinely undiscriminable. AC-6.11 gained a real test node. The live check required only that env resolve codex, which Pass 0 or an ambient pin satisfies with the feature reverted; it now requires the tail-evidence stderr marker with pins cleared and earlier passes proven blind. Blanket-RED rule back-propagated out of the design and plan.
- v1.11: Impl-plan audit v9 (codex, high-evidence: it ran five timing probes of its own) plus audit v10 (agy). AC-2.6's elapsed >= 1.0 assertion would have failed on the MAJORITY of correct runs - _cmd_run's watchdog uses bash's integer SECONDS, and ten trials across two independent probes measured 0.89-1.16s at rc=124; bound lowered to 0.5. The prescribed RED-count derivation commands returned 0 and 13 instead of 35 and 11 (one anchored on the wrong column, one unanchored into prose), so their difference would have been passed to --expect-fail as -13; both are now row-anchored and verified. tail-sig-swallows-failure was a THIRD equivalent mutant - return 0 with empty stdout produces the same decline - replaced by tail-sig-fabricates-banner-on-failure, which turns unreadable evidence into a MATCHING candidate. The mutation selector excluded a T5 node one of its own mutations targeted (agy's mechanism for this was wrong: named tests run via target_command + nodeid, never through -k; the selector governs the baseline and the wrong-catcher diagnostic). Design live-check back-propagation was claimed in v1.10's history but absent from the body; applied. _run_bash given a concrete extraction; AC-6.12..6.18 widened to 7 numbers for 7 mutations.
- v1.12: Impl-plan audit v12 (codex) — two of three must-fixes were defects in v1.8's own SIGPIPE fix. AC-4.5 was VACUOUS as written: a rival-only tail fails the wanted check first and never reaches rival rejection, and putting both banners early makes the WANTED check return 141, so the expected decline happens for a reason unrelated to the branch under test - it would pass against a build with rival rejection deleted. Measured both layouts on 240,068-byte tails; only rival-first-wanted-last discriminates (broken: wanted rc 0, rival rc 141; fixed: 0/0), and the AC now specifies that exact fixture. The RED counts were stale on FOUR non-history surfaces, not the three the audit named - it missed plan.md:178 - so the sweep found one more than the finding did; all now 37/11/26. The live check ran pin-agents --clear and then verified only the ENVIRONMENT, never re-reading the pin file the clear was meant to empty: it now records the path env prints and asserts on that file. AC-6.11 claimed an exact-string root assertion while prescribing not os.path.isabs, which any relative value satisfies.
- v1.13: Impl-plan audit v15 (codex) — every must-fix was a correction recorded only where it was FOUND, never on the paired surface. The counts were stale on SIX live sites across three docs (37 where the table now derives 38, 26/11 where it derives 27/11, 'T5's three' where T5 has four). The design still prescribed a subprocess 'hmad-dispatch run' and an untyped .result.terminal.tail, so an implementer following the cited source would have produced exactly the code path T2 rejects - the in-process _cmd_run call and the measured ARRAY shape are now IN the design. The plan's Success Criteria and the design's live check still required only that env resolve codex, which Pass 0 or an ambient file pin satisfies with zero terminal reads; both now carry the pin-FILE re-read (checking the environment is a different surface from the one --clear mutates), earlier-pass blindness, the tail-evidence marker and a cleanup re-list. AC-5.5 gained its exact old/new phrases and test body; _orca_read_dir now makes a fresh directory per call, since mkdir(exist_ok=True) let a previous call's handle file serve a handle the caller deliberately OMITTED. Audit-side note: the reviewer ran the wire-pin gate, which auto-registers and rewrote the wires.jsonl timestamp - it disclosed the mutation rather than reverting it, and the timestamp-only churn was discarded here.
- v1.14: Impl-plan audit v16 (codex) — two corrections. The live check still required only that pins be cleared with no `HMAD_ORCA_*_TERMINAL` exported, despite v1.13's own history claiming the pin-FILE re-read had landed here; the body now carries it as step 1, with the reason stated — `--clear` mutates the pin FILE and the environment is a different surface, so a surviving file pin short-circuits `_orca_find` exactly as an exported one would and the check would pass with the feature reverted. History claiming a fix the body lacks is the recurring shape in this document's own record. Second, the API comment, the invariant-compliance bullet and the traceability row still said `hmad-dispatch run --timeout` and "`timeout`/`gtimeout` appear nowhere"; both now say in-process `_cmd_run` and "no line INVOKES", matching impl-plan AC-2.7's command-position predicate.
- v1.15: Impl-plan audit v19 (codex) — node counts re-derived to 28 FAIL / 11 PASS over 39 after AC-2.9 was added (an exit-0 `ok:false` envelope was being accepted as identity evidence).
- v1.16: Impl-plan audit v20 (codex) — the error-envelope rule was in the impl-plan and not here, so an implementer following the declared source would have omitted a gate the plan calls load-bearing. The exact extraction now appears in the design body with the `.ok` check first and `else empty` in place of `else tostring`, plus the reason for each. Node counts re-derived to 29 / 11 over 40.
- v1.17: Impl-plan audit v21 (codex) — the Components table still said 14 ACs and the Test Plan had no row for spec v1.8's AC-4.4, so the design under-reported the contract it is the source for; both corrected. The `// empty` note is rewritten: it is defence in depth, not an independently pinned guard, because `else empty` on the type branch already discards a null.
- v1.18: Impl-plan audit v22 (codex) — the live check directed the operator at the ambient pin file, destroying live coordinator and agent pins to verify an unrelated feature. It now runs against an isolated `HMAD_ORCA_PIN_FILE` that is seeded with known dummy pins first, so the clear has something observable to remove.
- v1.19: Impl-plan audit v23 (codex) — the `$scoped` justification was backwards. It claimed a wider candidate pool 'can only turn a resolution into a decline, never into a wrong pane', but adding one uniquely banner-matching pane turns a decline INTO a resolution — this feature's intended path. Widening is safe for reasons that hold at any pool size: the scope boundary, the wanted/rival banner predicates, and exactly-one gating. Node counts re-derived to 28 / 12 over 40.
- v1.20: Impl-plan audit v24 (codex) — the live check now removes the isolated pin file's `mktemp -d` directory, matching the impl-plan; without it each run leaks one empty temporary directory.
- v1.21: Impl-plan audit v25 (codex) — same as the plan: the isolated pin file's `mktemp -d` cleanup must be confirmed by re-reading, not assumed from the command's success.
- v1.22: Impl-plan audit v26 (codex) — records that `_agent_pv_re` is NOT hardened against prose (measured 7/7 matches on ordinary sentences) and that the tail pass therefore anchors its matcher to line start, while Passes 1-2 keep the shared helper unchanged. Also corrects the literal-`null` explanation: with `// empty` and `else empty` in place, `jq -r` on a missing tail emits zero bytes at rc 0, so `-e` closes the RC hole rather than a null-printing one. Node counts re-derived to 29 / 12 over 41.
- v1.23: Impl-plan audit v27 (codex) — Test Plan gains a row for spec AC-1.4 (prose declines, real banners resolve), Components corrected to 16 ACs, node counts re-derived to 30 / 12 over 42.
- v1.24: Impl-plan audit v28 (codex) — the design still prescribed the anchor-only rule that audit v27 rejected and diagrammed the pass as `tail via _agent_pv_re`, so the declared source would have reproduced the wrong-pane defect. Architecture, matcher rule, rival rule and Test Plan now carry the line-complete `_agent_tail_re` grammar used for BOTH the wanted and rival checks, with the 19/12 measurement. Node counts re-derived to 31 / 12 over 43.
- v1.25: Impl-plan audit v29 (codex) — matcher description updated to the bounded grammar and the 24/12 corpus, and the stale literal-`null` conclusion in the later Extraction subsection scoped explicitly to the simple probe filter, so the design gives ONE explanation for the load-bearing `-e` guard rather than two.
- v1.26: Impl-plan audit v30 (codex) — the Executive Summary still described the pass as matching `_agent_pv_re`, which is the prose-unsafe helper its own safety rule rejects; corrected to `_agent_tail_re`. Mutation-coverage claim narrowed to enumerated targets, node counts re-derived to 31 / 13 over 44.
- v1.27: Impl-plan audit v31 (codex) — the bounded-grammar paragraph had spliced two continuation lists together, obscuring which suffixes are actually accepted; reduced to one list matching the regex.
- v1.28: Impl-plan audit v32 (codex) — the `_agent_pv_re` subsection still said the helper is 'reused unchanged' by this pass and quoted the superseded anchored measurement (0 of 7); both corrected to the 24-probe corpus and the Passes-1-2 scope.
- v1.29: Impl-plan audit v33 (codex) — `_agent_tail_re` was required by the matcher rule but absent from Components Changed and from the Implementation Order, whose step 1 shipped only `_orca_tail_sig` while step 2 consumed the missing helper. Added to both, mapped to impl-plan T2, with its 24/12 corpus tested there. Node counts re-derived to 32 / 13 over 45.
- v1.30: Impl-plan audit v34 (codex) — v1.29's history claimed `_agent_tail_re` had been added to Components, Implementation Order and API; only Components had it. Step 1 now ships both helpers with the matcher's direct 24/12 corpus, the API section lists TWO private functions with the matcher's interface, and the pin note distinguishes AC-2.12 (the helper's own corpus, in the task that defines it) from AC-3.17 (the caller connection, mixed fixture).
- v1.31: Impl-plan audit v35 (codex) — removed the last phrases implying the tail pass matches 'the agent's existing signature' or layers a grammar over the shared helper; both checks use the independent bounded `_agent_tail_re` literals.
