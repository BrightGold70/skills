# Design: exec-path-hardening

## Executive Summary

Three new bash helpers in `hmad-dispatch.sh` — a payload-sharing worktree resolver, a
segment-replacing comment composer, and a bounded best-effort stamp emitter — are driven from
a `_cmd_exec` whose two execution shapes collapse into one background-and-poll path, with the
codex `--log` redirect changed to append.

## Overview

Design intent is that observability is *structurally* incapable of affecting the dispatch:
every stamp is emitted from a helper that swallows its own failures, writes nothing to stdout,
and is wrapped in the same watchdog the agent is. The two hard constraints are the shared
mutable comment field (a stamp must never destroy a `handoff` checkpoint) and the verdict
channel (stdout must stay byte-identical). The key structural finding is that
`_run_with_timeout` has exactly two callers, both inside `_cmd_exec` — verified below — so
unifying the execution shape is a contained change rather than a cross-verb one.

## Architecture Overview

```
_cmd_exec
  ├─ parse flags, build bounded_prompt (unchanged)
  ├─ _exec_stamp start                     ─┐
  ├─ _exec_run <secs|""> <cmd...>           │   all stamps flow through
  │    └─ poll loop (kill -0, 0.25s)        │   ONE emitter
  │         ├─ deadline check (skipped when secs empty)
  │         └─ every HMAD_EXEC_HEARTBEAT_SEC → _exec_stamp beat
  ├─ capture verdict / recovery (unchanged) │
  ├─ _exec_stamp exit <rc> <verdict>       ─┘
  └─ _cmd_notify <title> <body>

_exec_stamp <kind> [args]          # best-effort; never returns non-zero to caller
  └─ _exec_wt_target <cd_dir>      # ONE `orca worktree ps` → selector + current comment
       └─ (no usable entry) ─────► abandon: emit nothing, zero `worktree set`
  └─ _exec_comment_compose <cur> <stamp>
       └─ replace our segment wherever it sits, else append once
  └─ orca worktree set --comment   # bounded
```

## Detailed Design

### `_exec_wt_target <cd_dir>` — resolve target and read comment in one call

Emits **two lines**: line 1 the selector, line 2 the current comment **base64-encoded** — or
nothing with rc 1. One `orca worktree ps --limit 200 --json` call serves both needs (plan A3).

The encoding is not incidental. A worktree comment is free text and may contain newlines (and
tabs), which `jq -r` emits literally. A `<selector>\t<comment>` line consumed with `read -r`
would silently keep only the first line of a multi-line comment, and the composer would then
write that truncated value back — turning the no-clobber design into a **partial**-clobber
bug that only manifests for multi-line comments and would pass every single-line test.
Base64 makes the transport total: the comment survives newlines, tabs, leading/trailing
whitespace, and the empty string, and it decodes to bytes the composer treats as opaque.
A test asserts round-trip fidelity for a comment containing a newline.

Envelope note: `_cmd_worktree_ps` emits `.result | tojson`, so the shape seen from the CLI is
already unwrapped. A helper calling `orca` directly must read `.result.worktrees[]` and
`.result.truncated`, matching `_worktree_path`'s existing jq paths.

Selection ladder, evaluated against the single payload:

1. entry whose `.path` equals `cd_dir`, or — for `--cd` into a subdirectory — the longest
   `.path` that contains `cd_dir` **on a directory boundary**: `.path == cd_dir` or
   `cd_dir` starts with `.path + "/"`. A bare string-prefix test is a wrong-worktree
   **clobber** bug, not a cosmetic one: `/x/repo` is a string prefix of `/x/repo-other`, so a
   dispatch in `repo-other` would stamp over `repo`'s comment — destroying a checkpoint on a
   worktree the run never touched, which is the same A4 data loss arriving by a different
   route. Both paths are compared after trailing-slash normalisation.
2. else the entry with `.isActive == true` → use its `.worktreeId` and `.comment`.
3. else → rc 1. Caller abandons the stamp.

`truncated` is deliberately **not** disqualifying on its own. This diverges from
`_worktree_path`, which returns rc 1 whenever `.result.truncated == true`, and the divergence
is intentional: `_worktree_path` guards worktree *destruction*, where an incomplete listing
could mean a match was hidden and a wrong worktree removed. Here the only question is whether
*our own* entry is present with its comment; if it is, a truncated tail changes nothing, and
if it is not, rule 3 already abandons. The stricter rule would silently disable stamping
whenever a user has more than 200 worktrees.

A worktree whose `.comment` key is absent is distinct from one whose comment is the empty
string; both are usable (treated as empty), because the payload was read. The extraction is
therefore **`(.comment // "") | @base64`** — the `// ""` is mandatory, not defensive. Per A7,
the bare `.comment | @base64` does not fail on null; it emits base64 of the literal string
`null`, which would be decoded, treated as foreign text, and preserved into the comment
forever.

### `_exec_comment_compose <current> <stamp>` — segment-located replacement

Takes a **complete** stamp string from `_exec_stamp` (see above) and decides only where it
goes; it parses no fields and assembles none. It recognises a span by its fixed `h-mad: `
lead-in and fixed `⟦/h-mad⟧` terminator. Composition:

- `current` contains a `h-mad: … ⟦/h-mad⟧` span → replace **that span in place**, preserving
  every byte before and after it.
- `current` is empty → emit the stamp alone.
- otherwise → `<current> · <stamp>`, appended exactly once.

Locating by content rather than by prefix is the whole point: a prefix rule appends to a
human comment, after which the string no longer starts with our stamp, so every later
heartbeat appends again — unbounded growth on the field the feature exists to protect.

Idempotency is therefore a property of the composer alone and is testable without any agent:
composing N times over its own output must yield exactly one span and a length independent of
N.

The terminator must be a byte sequence a human is vanishingly unlikely to type, and the
composer must tolerate a malformed half-span (lead-in present, terminator missing — e.g. a
comment truncated by another writer) by treating it as *not* a span and appending, rather
than replacing to an unbounded end offset.

### `_exec_stamp <kind> [rc] [verdict]` — the only writer

1. Resolve via `_exec_wt_target`; rc 1 → return 0 having done nothing.
2. Build the stamp text. **`_exec_stamp` owns the whole span; the composer never assembles
   fields.** `_exec_comment_compose` takes an already-complete stamp string and only decides
   *where* it goes, so exactly one function knows the format. The span is always:

   ```
   h-mad: <agent> <label> · <state>⟦/h-mad⟧
   ```

   where `<agent>` is `codex`/`agy` and `<label>` is the `--cd` basename — both present in
   **every** kind, including `start` and `beat`. Only `<state>` varies:

   | kind | `<state>` |
   |---|---|
   | `start` | `running · 0m` |
   | `beat` | `running · <elapsed>` — seconds below a minute (`42s`), minutes above it (`7m`), measured from the dispatch start marker `_HMAD_EXEC_T0` set by `_cmd_exec` |
   | `exit` | `rc=<rc> · <verdict\|no-verdict>` |

   So an exit span reads `h-mad: codex skills · rc=0 · DONE⟦/h-mad⟧`, carrying all three
   AC-1.2 elements — agent token, `rc=<n>`, verdict. Draft v1.0 listed the per-kind text
   without the `<agent> <label>` lead-in, leaving it ambiguous whether the composer inserted
   them; it does not, and a `start`/`beat` stamp missing the agent token would have shipped.
3. Compose against the read comment.
4. `orca worktree set --worktree <sel> --comment <composed> --json`, bounded, stdout and
   stderr both discarded.
5. `return 0` unconditionally.

**Every `orca` call on the stamp path MUST be bounded and MUST redirect stdin from
`/dev/null` — the read as well as the write.** `_exec_wt_target`'s `orca worktree ps` runs
*first* on every stamp, so it is the more exposed of the two: an unguarded read can hang the
poll loop indefinitely, and during a heartbeat it inherits the same open prompt descriptor
described below. Both calls take the identical form:

```bash
_exec_run "$stamp_timeout" orca worktree ps --limit 200 --json </dev/null 2>/dev/null
_exec_run "$stamp_timeout" orca worktree set … --json      </dev/null >/dev/null 2>&1
```

The read differs only in that its stdout is captured rather than discarded. A read that
times out, like a read that fails, yields rc 1 → the stamp is abandoned. `_exec_run` hands its own
stdin to the backgrounded child via `<&0`, which exists so `codex exec -` receives the piped
prompt. A stamp that inherits that stdin is a data-corruption hazard, and the dangerous case
is the heartbeat rather than the start stamp:

- the `start` stamp runs in `_cmd_exec`'s frame, so `<&0` is whatever the caller's stdin is —
  wrong to consume, but not the agent's prompt;
- the `beat` stamp runs **inside `_exec_run`'s poll loop**, where stdin *is* the open
  `bounded_prompt` file that codex is concurrently reading. A backgrounded `orca` inheriting
  that descriptor shares its **file offset**, so any read would advance codex's own position
  and silently truncate or corrupt the prompt mid-dispatch.

So the call form is fixed:

```bash
_exec_run "$stamp_timeout" orca worktree set … --json </dev/null >/dev/null 2>&1 || true
```

`_exec_run` is still reused rather than duplicated — a second watchdog would be exactly the
kind of independent re-implementation the single-source invariant forbids — but `</dev/null`
at the call site is mandatory, not stylistic, and is pinned by a test asserting that a stamp
cannot consume bytes from the dispatch's stdin.

**The heartbeat is opt-in per invocation, or the reuse is an infinite recursion.**
`_exec_run` owns the heartbeat hook and `_exec_stamp` calls `_exec_run`, so an inner
invocation that evaluated the heartbeat condition would call `_exec_stamp beat` → `_exec_run`
→ `_exec_stamp beat` → … unbounded. It is not a theoretical edge: any
`HMAD_EXEC_HEARTBEAT_SEC` smaller than the stamp timeout reaches it, which a test setting a
1-second interval to exercise multi-interval behaviour does by construction.

So the heartbeat is **never** implied by `_exec_run`; it is requested explicitly:

```bash
_exec_run --heartbeat "$agent" "$label" "$cd_dir" "$hb_secs" "$timeout" codex …   # ONLY in _cmd_exec
_exec_run "$stamp_timeout" orca worktree … </dev/null   # every stamp call — no flag, no heartbeat
```

Relying on `HMAD_EXEC_HEARTBEAT_SEC=0` inside `_exec_stamp` would also break the cycle, but it
couples the guard to an env var a caller can set and makes recursion-safety a property of
configuration rather than of the call. The flag makes the non-heartbeat path the default, so
forgetting it is safe and requesting it is deliberate. A re-entrancy sentinel (`_exec_run`
refuses `--heartbeat` when already inside a heartbeat-enabled frame) is kept as belt-and-braces
and is mutation-tested.

Nesting `_exec_run` inside its own poll loop is therefore a supported case and carries two
constraints the implementation must honour: `set -m` is toggled per invocation and restored
from the state captured at *that* invocation's entry (the outer loop runs with `-m` already
restored to off, so the inner toggle is self-contained), and `wait` is always called with an
explicit pid so the inner reap cannot consume the outer child.

Not reused: `_cmd_worktree_comment`, because it calls `_require_orca` (which prints) and
`_orca_json` (which echoes a whole error envelope to stderr on `ok:false`). Both are correct
for an operator-invoked verb and wrong for a silent background stamp that must not pollute the
stderr a caller reads for `EMPTY final message` diagnostics. The emitter issues the `orca`
call directly and discards both streams. Substrate gating is an explicit
`[ "$(_detect_substrate)" = orca ] || return 0` at the top, so cmux issues zero calls.

### `_exec_run [--heartbeat <agent> <label> <cd_dir> <interval>] <secs> <cmd...>` — the unified shape

`_run_with_timeout` is renamed/extended rather than duplicated. `secs` empty means "no
deadline": the loop still backgrounds, polls, and reaps, but skips the deadline comparison —
so heartbeats fire identically with and without `--timeout`, which spec AC-2.4 requires be
pinned by a test.

Verified contained: `grep -n "_run_with_timeout" scripts/hmad-dispatch.sh` returns its
definition plus exactly two call sites, both inside `_cmd_exec` (the codex and agy branches).
No other verb is affected.

Every existing behaviour is preserved and is treated as a regression guard, not as
refactorable detail: `<&0` explicit stdin handoff (without it bash redirects a backgrounded
child's stdin from `/dev/null` and codex starves), `set -m` for a fresh process group with the
prior `-m` state restored, group-signalled `TERM` → 2 s polled grace → `KILL`, an absolute
deadline off `SECONDS` rather than counted sleeps, and `return 124` on timeout.

Heartbeat inside the loop is a wall-clock floor, not a per-tick action: stamp when
`SECONDS - last_beat >= HMAD_EXEC_HEARTBEAT_SEC`, with `0` disabling it entirely.

### codex `--log` append

**One call site, because unification removed the other.** Today the codex branch has two
invocations — `_run_with_timeout … > "$log"` and a bare `codex … > "$log"` — selected by
whether `--timeout` was given. Step 5 collapses them into a single `_exec_run "$timeout" …`
where an empty `timeout` means "no deadline", so after that step there is exactly **one**
codex invocation and exactly one redirect to change: `> "$log"` becomes `>> "$log"`. The same
holds for agy, whose two invocations also collapse to one. (Draft v1.0 said "both codex call
sites", which described the pre-unification file and contradicted its own strategy.) agy's
transcript append is separately `cat "$resp_file" >> "$log"` and already correct.

A single shared implementation is not available: codex appends by redirecting a **live process
stream**, agy by concatenating a **captured file**. Collapsing them would re-plumb how each
backend produces output, reaching into the shipped recovery path. The base invariant's
alternative — a test asserting byte-equivalence across surfaces — is therefore what this design
takes, as one parameterised test over both backends.

The auto-log path (`mktemp` when `--log` is absent) is unaffected: a fresh temp file appends
into emptiness.

## Verified assumptions (design-level probe evidence)

**A7 — `jq @base64` on a null/missing comment does NOT crash; it silently corrupts.** The
cycle-3 audit predicted `jq: error: null (null) cannot be base64-encoded`. That premise is
**false**, and the real behaviour is worse than the predicted crash. Observed:

```
$ echo '{"comment":null}' | jq -r '.comment | @base64'
bnVsbA==                       # rc=0  — base64 of the literal string "null"
$ echo '{"comment":null}' | jq -r '(.comment // "") | @base64'
                               # rc=0  — empty, correct
$ echo '{}'              | jq -r '(.comment // "") | @base64'
                               # rc=0  — empty, correct
```

A crash would have been safe: `_exec_wt_target` returns rc 1 and the stamp is abandoned.
Instead the unguarded form decodes to the four literal bytes `null`, which the composer would
treat as pre-existing foreign text and dutifully **preserve** — writing `null · h-mad: …`
into the worktree comment and keeping it there forever. So `// ""` is mandatory, and the test
must assert the **decoded value is empty**, not that the command exited 0: a crash-shaped test
passes on exactly the corrupting behaviour.

Round-trip fidelity confirmed on the same probe:

```
$ printf '%s' '{"comment":"line1\nline2\ttab "}' | jq -r '(.comment // "") | @base64' | base64 -d | od -c
0000000  l i n e 1 \n l i n e 2 \t t a b
```

**A8 — nested `_run_with_timeout` under command substitution works.** Driving the real
function (extracted verbatim from `scripts/hmad-dispatch.sh`) with an outer "agent" reading a
prompt on stdin and an inner "stamp" fired mid-flight and captured via `$(…)`:

```
inner captured: [SEL|Y29tbWVudA==]
outer rc=0
agent saw: [PROMPT-SENTINEL-COMPLETE]
```

The inner watchdog captured both lines, the outer reaped cleanly, and the agent received its
complete prompt. `set -m` nesting and explicit-pid `wait` behaved as the design assumed.

**A9 — the `</dev/null` guard is load-bearing, and the mechanism is shared-offset, not
"a second reader".** A first negative control fired an unguarded reader with its own
`< "$PROMPT"` redirect: it read 12 bytes *and the agent still saw the whole prompt*, because
two redirects are two `open()`s and therefore two independent offsets. That control did not
reproduce the hazard and would have wrongly cleared the guard. The correct control inherits
**one** open description, which is the real `_exec_run` shape (`<&0`, no re-open):

```
stamp stole: [AAAABBBB]
agent got:   [CCCCDDDD-AGENT-TAIL]     # first 8 bytes gone
```

The agent's prompt is silently truncated. This is why the guard is mandatory rather than
defensive, and why the corresponding test must inherit the descriptor rather than re-open the
file — a re-opening test passes with the guard removed.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_exec_wt_target` | `h-mad/scripts/hmad-dispatch.sh` | new | One-payload selector + comment resolution (FR-6) |
| `_exec_comment_compose` | `h-mad/scripts/hmad-dispatch.sh` | new | Segment-located, idempotent composition (FR-1, FR-2) |
| `_exec_stamp` | `h-mad/scripts/hmad-dispatch.sh` | new | Sole comment writer; best-effort, silent (FR-1, FR-2) |
| `_run_with_timeout` → `_exec_run` | `h-mad/scripts/hmad-dispatch.sh` | modify | Optional deadline; heartbeat hook (FR-2) |
| `_cmd_exec` | `h-mad/scripts/hmad-dispatch.sh` | modify | Stamp start/exit, notify, append `--log` (FR-1, FR-3, FR-5) |
| orca stub | `h-mad/tests/stubs/orca` | modify | Optional stateful comment round-trip (FR-1, FR-2) |
| exec tests | `h-mad/tests/test_hmad_dispatch_exec.py` | modify | Stub `orca`, capture argv, new assertions |
| mutation spec | `h-mad/tests/` | new | Guard mutations (FR-4) |
| `:1898` boundary comment | `h-mad/scripts/hmad-dispatch.sh` | modify | Its stated rationale assumes surviving caller `--log` content; append makes that true (FR-5) |
| Skill docs | `h-mad/SKILL.md` | modify | `HMAD_EXEC_HEARTBEAT_SEC` knob; `--log` append contract in §"A missing report on the `exec` path" |

## Implementation Order

1. `_exec_comment_compose` — pure string function, no runtime; testable in isolation and the
   home of the growth defect. First because everything else depends on its contract.
2. Stub statefulness (`HMAD_STUB_ORCA_STATE`) — must exist before any test that would
   otherwise be blind to growth.
3. `_exec_wt_target` — resolution ladder + abandon path.
4. `_exec_stamp` — composition of 1 and 3; substrate gate; silence guarantees.
5. `_exec_run` — deadline-optional unification, keeping the existing timeout tests green.
6. Wire W1/W3 (start/exit) and W4 (notify) into `_cmd_exec`.
7. Wire W2 (heartbeat) into the poll loop; W5 (resolver) is exercised by 3–4.
8. codex `--log` append + cross-surface equivalence test.
9. Docs.

## Data Model / Schema Changes

None. No state-schema field, no new file format. The worktree comment gains an internal
convention (the delimited `h-mad:` span), which is a string convention, not a schema.

## API / Interface Changes

- **New env var** `HMAD_EXEC_HEARTBEAT_SEC` (integer seconds, default `120`, `0` disables).
  **Read only by `_cmd_exec`**, which forwards the value to `_exec_run` as the `--heartbeat`
  group's `<interval>` argument. `_exec_run` never reads the environment: a zero-argument flag
  could not supply `_exec_stamp beat` with its agent/label/cd_dir, and sourcing the interval
  from the environment inside the poll loop would make recursion-safety a property of
  configuration rather than of the call.
- **New test-only env var** `HMAD_STUB_ORCA_STATE` (path). Unset → stub behaves exactly as
  today, matching the existing "consulted only when explicitly set" precedent for
  `HMAD_STUB_ORCA_WT_PS_STDOUT` and `HMAD_STUB_ORCA_TASKLIST_STDOUT`.
- **Behaviour change, no signature change**: `exec codex --log <f>` appends rather than
  truncates. No flag added, removed, or renamed; no parsing change.
- Unchanged: `exec`'s stdout contract, exit codes (`0`/agent rc/`124`/`3`), `--out`, prompt
  delivery, boundary append, verdict recovery, `tree delta`.

## Error Handling Strategy

Two disjoint classes, and the design's core rule is that they never mix.

**Dispatch errors** keep today's contract exactly: `rc` is the agent's own exit code, `124`
on watchdog kill, `3` on empty-final-message-with-exit-0; diagnostics go to stderr; the
verdict goes to stdout.

**Observability errors are not errors.** Every stamp path returns 0 unconditionally. A failed,
hanging, or `ok:false` `orca` call, an unreadable listing, a missing worktree entry, or a
non-orca substrate all resolve to "no stamp emitted". Nothing is logged to stderr — a silent
stamp failure must not be mistaken for a dispatch diagnostic. `set -e` safety: every stamp
call site is `|| true`-guarded so a non-zero cannot propagate.

The one asymmetry worth stating: an unreadable comment causes the stamp to be **abandoned, not
retried with an assumed-empty value**. Writing on an unread comment is the A4 data-loss path,
and it would trigger exactly when the runtime is already unhealthy.

## Test Strategy

Boundary: the `orca` CLI, stubbed at the PATH level by the existing `_bindir` symlink factory —
never mocked in-process. `HMAD_STUB_CAPTURE` already records every argv (line 2 of the stub),
so invocation counting needs wiring, not machinery.

- **Pure unit** — `_exec_comment_compose` driven directly via `bash -c` source-and-call: the
  growth, replacement, empty, and malformed-half-span cases. No orca, no agent.
- **Stubbed integration** — full `exec` runs with `codex`/`agy`/`orca` stubbed, asserting argv
  counts and content from the capture file.
- **Stateful integration** — `HMAD_STUB_ORCA_STATE` pointed at the test's own `tmp_path` so
  `worktree set` → `worktree ps` round-trips, which is what makes multi-interval growth
  observable. Never a shared or defaulted path (J18: mutation testing that clobbered live
  state while reporting green).
- **Regression** — all 45 existing exec tests unchanged; the timeout/stdin/pgroup tests are
  the guard for step 5.
- **Mutation** — every new guard, asserting message/behaviour content, not exit codes.

## Test Plan

`h-mad/tests/test_hmad_dispatch_exec.py` unless noted.

| Scenario | Asserts | AC |
|---|---|---|
| compose over empty / human / handoff / own-span / malformed-half-span | correct span placement, foreign bytes preserved | FR-1 |
| compose N=5 times over own output | exactly one span; length independent of N | FR-2 |
| orca run, clean codex | ≥2 `worktree set` calls, one before agent start | AC-1.1 |
| exit stamp content | contains agent token **and** `rc=<n>` **and** verdict | AC-1.2 |
| substrate cmux | zero `worktree set`; stdout/stderr/rc identical to no-feature run | AC-1.3 |
| stubbed `orca` exits non-zero on set | agent rc preserved, stdout unchanged | AC-1.4 |
| stubbed `orca` hangs on set | dispatch completes; bounded | AC-1.5 |
| N≥3 intervals, stateful stub, pre-existing `handoff:` comment | >1 heartbeat; foreign text intact; one span | AC-2.1, AC-2.2 |
| `HMAD_EXEC_HEARTBEAT_SEC=0` | zero heartbeats; start/exit still emitted | AC-2.3 |
| **no `--timeout`**, N≥3 intervals | heartbeats fire at same cadence as with `--timeout` | AC-2.4 |
| notify | exactly one invocation, after exit, body has `rc=<n>` | AC-3.1–3.2 |
| notify stubbed failing non-zero | `rc` and stdout unchanged; pins `_cmd_notify`'s unconditional `return 0` | **AC-3.3** |
| recursion guard: `HMAD_EXEC_HEARTBEAT_SEC` shorter than the stamp timeout | dispatch terminates; stamp calls emit no nested heartbeat; no unbounded recursion | AC-2.5 |
| `SKILL.md` + `:1898` comment vs code | all three state the same `--log` contract (append) | **AC-5.4** |
| stdout byte-compare, surfaces on vs off — clean and rc-3 paths | byte-identical, incl. recovered verdict + `tree delta:` | AC-4.1, AC-4.2 |
| all surfaces stubbed failing × {0, crash, 124, 3} | agent rc returned in every case | AC-4.3 |
| codex + agy `--log` with pre-existing content | preserved verbatim, transcript appended (one parameterised test) | AC-5.1–5.2 |
| `test_agy_empty_response_recovers_verdict_from_caller_log` | passes **unchanged** | AC-5.3 |
| `--cd` inside listed worktree | targets that `worktreeId`, not `active` | AC-6.1 |
| worktrees `/x/repo` and `/x/repo-other` both listed; `--cd /x/repo-other` | targets `repo-other`; `repo`'s comment byte-identical after | AC-6.1 |
| `--cd` into a **subdirectory** of a listed worktree | targets the enclosing worktree | AC-6.1 |
| comment containing a newline, tab, and trailing space | round-trips byte-identically through resolve → compose → write | AC-1.3, FR-1 |
| stamp call with a sentinel on the dispatch's stdin, **inheriting the descriptor** (not re-opening) | sentinel still fully readable by the agent; **neither** the `worktree ps` read nor the `worktree set` write consumed any of it. Per A9 a re-opening test passes with the guard removed and is therefore not acceptable | AC-4.1 |
| `.comment` null / key absent | decoded comment is **empty**, never the literal `null`; composed result carries no `null` text | FR-1 |
| `orca worktree ps` hangs | dispatch completes; stamp abandoned; poll loop not stalled | AC-1.5 |
| heartbeat fires mid-dispatch with prompt on stdin | codex receives the complete prompt; no offset drift | AC-2.5, AC-4.3 |
| `start`/`beat` span content | contains agent token and label, not only the state | AC-1.2 |
| `--cd` unlisted, `active` present | targets `active` | AC-6.2 |
| listing unreadable / no usable entry | **zero** `worktree set`; comment byte-identical | AC-6.3 |
| `truncated` listing containing the target | stamps normally | AC-6.3 |

### Wire-scoped revert tests (W1–W5) — carried from the plan

The plan declared this feature `wiring`-shaped: every callee already exists and works, so the
deliverable is the *call*. A whole-module revert removes callee and call site together and its
RED split is identical whether or not the wire exists. These rows are therefore not optional
and were dropped from design v1.0–v1.3 by omission.

For each wire: revert the **call site only**, leaving the callee and the tests intact, and
confirm the named `WIRE-PIN` fails. Module suite still green → halt
`step5e:wire_unenforced:<module>`. Each RED reason must be an assertion about the **caller's**
observable behaviour; an `ImportError`/`AttributeError`/`NameError` RED proves only that the
callee is absent and is a wrong-reason RED.

| Wire | Call site reverted | `WIRE-PIN` fails with |
|---|---|---|
| W1 | `_cmd_exec` → `_exec_stamp start` | no comment invocation recorded before the agent process starts (capture file has zero pre-agent `worktree set`) |
| W2 | `_exec_run` poll → `_exec_stamp beat` | a run spanning N≥3 intervals records **zero** heartbeat stamps; total writes fall to the 2 start/exit |
| W3 | `_cmd_exec` → `_exec_stamp exit` | no comment carrying all three AC-1.2 elements (agent token, `rc=<n>`, verdict) |
| W4 | `_cmd_exec` → `_cmd_notify` | zero notify invocations recorded for a completed dispatch |
| W5 | `_exec_stamp` → `_exec_wt_target` | the comment targets `active` even though `--cd` is inside a listed worktree |

Unconditional-fire mutations in the other direction: heartbeat forced to fire with
`HMAD_EXEC_HEARTBEAT_SEC=0` (the AC-2.3 test must fail), and a stamp forced under substrate
`cmux` (the AC-1.3 zero-call test must fail).

Revert mechanics per the skill's GREEN protocol: `git add -N -- <paths>` before
`git stash push -- <paths>` (a `stash push` of an untracked path stashes nothing and exits 0,
so the revert silently no-ops and reports a pass), then `git diff --quiet || echo "REVERT DID
NOT LAND"` before trusting the run.

Verification: `pytest h-mad/tests/ -v` and the `handoff` suite (symlink-coupled), then
`h_mad_mutation_harness.py <spec.json>` reading `MUTATION:` (**AC-4.4**).

## Invariant Compliance

**Base — audit-gate signal discipline.** No new script emits a verdict token; the stamp
emitter has no verdict semantics and returns 0 always. Complies.

**Base — single-source contract.** The `--log` append rule is applied by two surfaces because
one implementation is infeasible (live process redirect vs captured-file concat); the
invariant's stated alternative, a cross-surface byte-equivalence test, is taken. Comment
composition has exactly one implementation (`_exec_comment_compose`), used by all three stamp
kinds. Complies.

**Base — no new external dependency.** bash builtins, `jq` (already required and already
symlinked into the test PATH), and the `orca` CLI already used. Complies.

**Base — backward compatibility.** No flag or state-schema change. `HMAD_EXEC_HEARTBEAT_SEC`
and `HMAD_STUB_ORCA_STATE` both default to prior behaviour when unset (the stub's existing
"consulted only when explicitly set" precedent). cmux is a zero-call no-op. The one intended
behaviour change is codex `--log` append, carved out in the plan's Scope. Complies.

**Base — operator-override preservation.** Strengthened, not weakened: a human or `handoff`
comment is preserved by composition, and an unreadable comment abandons the write.

**Base — mutation verification.** Every new guard has a mutation with a content assertion;
the harness refuses an anchor not matching exactly once.

**Base — connection enforcement.** W1–W5 are declared wiring with `WIRE-PIN`s asserting
caller-observable behaviour, plus wire-scoped reverts and unconditional-fire mutations.

**Base — marker discipline.** No new `[H-MAD]` marker; stamps are worktree comments, not
markers.

**Project — skill self-containment.** All changes are inside `h-mad/`; no import of another
skill's internals and no path outside the skill. The `handoff` skill's comment convention is
*honoured by prefix agreement*, not by calling into `handoff` — no code coupling. Complies.

**Project — skill manifest integrity.** `SKILL.md` gains the `HMAD_EXEC_HEARTBEAT_SEC` knob
and the `--log` contract; frontmatter `name`/`description` unchanged, and entry behaviour is
unchanged. Complies.

## Version History

- v1.0: Initial design draft.
- v1.1: Design audit cycle 1 — 3 must-fix, 2 should-fix, all four hazards landing on the
  stamp path. (1) **Stdin stealing**: `_exec_run` hands its stdin to the backgrounded child
  via `<&0`, so a stamp bounded by it inherits that descriptor. The dangerous case is the
  *heartbeat*, which runs inside the poll loop where stdin is the open prompt file codex is
  concurrently reading — a shared file offset, so any read by `orca` would corrupt the
  prompt mid-dispatch. `</dev/null` is now mandatory at every stamp call site, pinned by a
  test, with the `_exec_run` nesting constraints (`set -m` scope, explicit-pid `wait`) stated.
  (2) **Prefix match**: `/x/repo` is a string prefix of `/x/repo-other`, so the resolver would
  stamp over a worktree the run never touched. Now requires a directory-boundary match.
  (3) **Call-site contradiction**: "both codex call sites" described the pre-unification file;
  after step 5 there is exactly one. (4) **Multi-line comments**: `<selector>\t<comment>`
  consumed by `read -r` would keep only the first line and write the truncation back — a
  partial-clobber bug invisible to single-line tests. The comment is now base64 on its own
  line. (5) Stamp assembly ownership fixed: `_exec_stamp` owns the whole span, the composer
  only places it, and `<agent> <label>` is present in every kind — v1.0's per-kind text would
  have shipped `start`/`beat` spans with no agent token.
- v1.2: Design audit cycle 2 — 1 must-fix, 1 should-fix. v1.1 bounded and `</dev/null`-guarded
  the `worktree set` write but left `_exec_wt_target`'s `worktree ps` read unguarded, even
  though the read runs *first* on every stamp and therefore carries the same hazards sooner:
  an unbounded hang would stall the poll loop, and during a heartbeat it inherits the same
  open prompt descriptor. Both calls now take the identical bounded, stdin-null form, with a
  read timeout treated as rc 1 → stamp abandoned. Also corrected the components table, which
  attributed the `:1898` comment to `SKILL.md` when it lives in `scripts/hmad-dispatch.sh`.
- v1.3: Design audit cycle 3 — both must-fix items demanded executed evidence, so all three
  assumptions were probed and recorded as A7–A9. The `jq` finding's stated premise
  (`@base64` crashes on null) is **false**; the probe showed rc=0 emitting base64 of the
  literal string `null`, which is worse than the predicted crash because a crash would abandon
  the stamp while this silently writes `null` into the comment permanently. `// ""` is now
  mandated with the reason, and the test asserts the decoded value is empty rather than that
  the command exited 0 — a crash-shaped test would pass on the corrupting behaviour. Nested
  `_run_with_timeout` under command substitution was driven for real and works (A8). The
  `</dev/null` guard was validated by negative control, and the **first control was wrong**:
  it re-opened the prompt, giving two independent offsets, so it failed to reproduce the
  hazard and would have cleared the guard. The corrected control inherits one descriptor and
  shows the agent's prompt truncated by exactly the bytes the stamp consumed (A9); the test
  is now required to inherit rather than re-open. Probes deleted after use.
- v1.5: Phase 6a-prime finding. The `beat` state was specified as `<elapsed>m` and shipped
  hardcoded as `running · 0m`; the elapsed field is now measured from a dispatch-start marker
  and reported in seconds below a minute. Minute granularity was itself part of the defect's
  cover: it reads `0m` for the whole first minute, so no short test could observe the field
  advancing, and the monotonic AC was satisfied vacuously by a constant. See the report's
  §"What 6a-prime caught".
- v1.4: Design audit cycle 4 — 5 must-fix. (1) **Infinite recursion**: `_exec_run` owns the
  heartbeat hook and `_exec_stamp` calls `_exec_run`, so any `HMAD_EXEC_HEARTBEAT_SEC` shorter
  than the stamp timeout recursed `_exec_stamp → _exec_run → _exec_stamp` unbounded — reachable
  by construction from any test using a 1-second interval to exercise multi-interval
  behaviour. The heartbeat is now opt-in via an explicit `--heartbeat` flag passed only by the
  agent dispatch, so the safe path is the default, plus a mutation-tested re-entrancy sentinel.
  (2) **Wire-scoped reverts dropped**: the plan declared W1–W5 wiring-shaped and mandated
  call-site-only reverts with caller-behaviour RED reasons; design v1.0–v1.3 omitted them
  entirely, relying on content mutation alone. Restored as a dedicated section with per-wire
  failure assertions, unconditional-fire mutations, and the `git add -N` revert mechanics.
  (3–5) AC-3.3, AC-4.4 and AC-5.4 were covered in prose but unmapped by identifier; each now
  has an explicit test-plan row.
