# Design: preflight-read-enforcement

## Executive Summary

Five new shell helpers in `hmad-dispatch.sh` write a `key=value` receipt beside the session pin file
when `env` concludes `PREFLIGHT: PASS`, remove it when it concludes FAIL, and make `_cmd_send` refuse
to dispatch unless that receipt is present, fresh, and fingerprint-matched against resolution at send
time — plus a conflict guard refusing a dispatch when both agents resolve to one handle.

## Overview

The design intent is to add enforcement without adding a component: every input needed already exists
inside `hmad-dispatch.sh`, so the feature is five private helpers and two call sites, not a new
script. The three constraints that shape it are (a) `env` must keep exit-0-on-both-verdicts, (b)
receipt validation must never treat an unreadable terminal listing as evidence of rotation, and
(c) the wrapper's 530-test suite must not require a global enforcement bypass — a bypass exported
suite-wide would make every enforcement assertion vacuous, which is the failure mode the feature
exists to eliminate.

The key decision is that the receipt path **defaults to the directory of the pin file in effect**.
Because `run()` in the test harness already assigns every invocation a unique absent pin path
(`h-mad/tests/test_hmad_dispatch.py:94`, the J7 fix), receipt isolation follows for free, and no
global `HMAD_SKIP_PREFLIGHT` default is needed anywhere in the suite.

## Architecture Overview

```
hmad-dispatch env                          hmad-dispatch send <agent> <file>
  │                                          │
  ├─ _detect_substrate                       ├─ _preflight_conflict_check  ──► refuse
  ├─ _resolve_target codex ─┐                │     (codex == agy, non-empty)   preflight_agent_conflict
  ├─ _resolve_target agy   ─┤                │
  ├─ liveness / conflict    │                ├─ _receipt_valid  ─────────────► refuse
  ├─ prints PREFLIGHT: X    │                │     absent  → preflight_not_run
  │                         │                │     old     → preflight_expired
  └─ PASS → _receipt_write ─┤                │     fp≠now  → preflight_handles_rotated
     FAIL → _receipt_clear  │                │
                            ▼                ▼
                   _fingerprint         (unchanged)
                "codex=<v>;agy=<v>"     _send_text → substrate delivery
                            │                ▲
                            └────────────────┘
                         same function, both sides

  _receipt_file()  =  ${HMAD_PREFLIGHT_RECEIPT_FILE:-$(dirname $(_pin_file))/preflight.receipt}
```

`clear` and `interrupt` route through `_send_text` / their own paths and are deliberately **not**
guarded — they are the recovery verbs, and requiring a preflight to clear a wedged pane would
obstruct the documented recovery path.

## Detailed Design

### Receipt path resolution — `_receipt_file()`

```
${HMAD_PREFLIGHT_RECEIPT_FILE:-$(dirname "$(_pin_file)")/preflight.receipt}
```

Anchoring the default to `dirname $(_pin_file)` rather than a hardcoded `.h-mad/` is the load-bearing
choice. `_pin_file` already honours `HMAD_ORCA_PIN_FILE` (`hmad-dispatch.sh:91-92`), so any caller
that isolates its pin file automatically isolates its receipt. This gives FR-8 for free in the test
suite and means the receipt inherits — rather than duplicates — the cwd-relativity that J2 has already filed
against the pin file. When J2 is fixed, one fix covers both artifacts; a hardcoded `.h-mad/` path
would need fixing twice and would drift.

An explicit `HMAD_PREFLIGHT_RECEIPT_FILE` overrides unconditionally (AC-8.1).

### Fingerprint — `_fingerprint()`

Emits the literal string `codex=<v>;agy=<v>`, where `<v>` is `_resolve_target <agent>`'s stdout on
success and the literal `UNRESOLVED` on failure.

Deliberately **not hashed**. It is not a secret; a plain string makes a mismatch diagnosable by
reading the file, and it avoids depending on `shasum`/`sha256sum`, whose availability and output
format differ across macOS and Linux — a dependency the skill-self-containment invariant discourages.

Including `UNRESOLVED` as a value (AC-4.2) is what makes pinning a previously-unresolved agent
invalidate the receipt, which is what `SKILL.md`'s existing "re-assert after any re-pin" instruction
already tells the orchestrator to do. Excluding it would leave the code quietly contradicting the
prose.

### Receipt format

Flat `key=value` lines, matching the pin file's existing convention and parsed with the same
`${line#*=}` idiom used by `_pin_lookup` (`hmad-dispatch.sh:104`):

```
verdict=PASS
fingerprint=codex=term_957ddb26…;agy=term_5bb15287…
ts=1784781000
```

`ts` is **epoch seconds**, not ISO-8601. POSIX shell has no date parser, so an ISO timestamp would
require either `date -d` (GNU-only) or `python3` — a runtime dependency the wrapper currently does
not have. `ts` is written with `date +%s`, and freshness is integer arithmetic.

Note the `fingerprint` value itself contains `=`. Parsing with `${line#*=}` (strip through the
**first** `=`) preserves the remainder intact; this is the same idiom the pin file already relies on
and it must not be changed to a greedy strip.

### Write / clear — `_receipt_write()`, `_receipt_clear()`

`_receipt_write` creates the parent directory if absent (as `_cmd_pin` already does at
`hmad-dispatch.sh:442`) and writes the three lines. `_receipt_clear` removes the file with `rm -f`,
so a missing file is not an error.

`_cmd_env` calls exactly one of them, immediately after printing the `PREFLIGHT:` line, keyed on the
verdict variable it already computes. **Ordering matters:** the print happens first, so a failure to
write a receipt can never suppress or alter the token. `env` returns 0 regardless (AC-1.5, AC-2.3).

### Validation — `_receipt_valid()`

Returns 0 when valid; on failure prints the reason token to stdout and returns 1. Checks in order:

1. File absent → `preflight_not_run`
2. `verdict` line is not `PASS` → `preflight_not_run` (a malformed or hand-edited receipt is treated
   as no receipt, never as a pass)
3. `now - ts > ttl` → `preflight_expired`
4. `fingerprint` ≠ `_fingerprint()` recomputed now → `preflight_handles_rotated`

**Why this never spuriously fires on an unreadable listing.** Validation compares *resolved values*,
and `_resolve_target` consults the env pin, then the pin file, then auto-detect — it does not call
`orca terminal list` at all when a pin exists. So an unreadable listing leaves resolution unchanged,
the fingerprint still matches, and the receipt stays valid. The spec's assumption about
`_orca_handle_live`'s rc=2 contract is therefore satisfied structurally rather than by a special
case, and no code needs to reference rc=2.

### Freshness — `HMAD_PREFLIGHT_TTL_SEC`, default `3600`

Chosen against measured run lengths rather than picked round. The longest single blocking step is
`report-wait`, whose documented timeout is 600 s and which this run invoked at 900 s; 3600 s is
comfortably longer than any one dispatch-and-wait, so the TTL never expires *mid-step*. The Wave-2
feature took 110.3 min end to end, so a one-hour TTL does expire at least once inside a full feature
run — which is the intended behavior, not a flaw: it forces a re-assertion at a phase boundary,
exactly as `SKILL.md` already instructs. A receipt left over from a previous session or a previous
day is rejected outright.

The TTL is a backstop. The fingerprint is the real guard, and it is age-independent (FR-4).

### Conflict guard — `_preflight_conflict_check()`

Resolves both agents and refuses when the two values are **equal and both non-empty and neither is
`UNRESOLVED`** (AC-7.4 — two unresolved agents are not one pane). Independent of the receipt, and
not suppressed by `HMAD_SKIP_PREFLIGHT` (AC-6.4): the bypass exists to let an operator dispatch
without having run a preflight, not to let them dispatch into a provably wrong pane.

### Enforcement point and order in `_cmd_send`

Both guards run in `_cmd_send`, before the existing missing-prompt-file check is reached for
delivery, and before either delivery branch. Order is conflict-check first, then receipt: a conflict
is a hard misconfiguration whose diagnostic is more useful than "you didn't run a preflight".

The existing `[ ! -f "$promptfile" ]` guard (`hmad-dispatch.sh:776-779`, return 2) stays **first** of
all, so a caller typo keeps its current distinct exit code rather than being masked by a preflight
refusal.

### Bypass — `HMAD_SKIP_PREFLIGHT`

Tested as `[ -n "${HMAD_SKIP_PREFLIGHT:-}" ]`, so an empty-string assignment counts as unset — this
is what lets a test override the variable to empty in an inherited environment. On bypass, a notice
naming the bypass is printed to stderr (AC-6.2) and the receipt check is skipped; the conflict check
still runs.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_receipt_file` | `h-mad/scripts/hmad-dispatch.sh` | new | Resolve receipt path, defaulting beside the pin file — FR-8 |
| `_fingerprint` | `h-mad/scripts/hmad-dispatch.sh` | new | Deterministic `codex=<v>;agy=<v>` over both agents — FR-1, FR-4 |
| `_receipt_write` | `h-mad/scripts/hmad-dispatch.sh` | new | Write verdict/fingerprint/ts — FR-1 |
| `_receipt_clear` | `h-mad/scripts/hmad-dispatch.sh` | new | Remove receipt on FAIL — FR-2 |
| `_receipt_valid` | `h-mad/scripts/hmad-dispatch.sh` | new | Validate + emit reason token — FR-3, FR-4, FR-5 |
| `_preflight_conflict_check` | `h-mad/scripts/hmad-dispatch.sh` | new | Refuse one-handle-two-agents — FR-7 |
| `_cmd_env` | `h-mad/scripts/hmad-dispatch.sh` | modify | Call write/clear after printing the token — FR-1, FR-2 |
| `_cmd_send` | `h-mad/scripts/hmad-dispatch.sh` | modify | Enforce conflict + receipt before delivery — FR-3, FR-6, FR-7 |
| Receipt lifecycle tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-1, FR-2, FR-8 |
| Enforcement tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-3, FR-4, FR-5, FR-6 |
| Conflict tests | `h-mad/tests/test_hmad_dispatch.py` | modify | FR-7 |
| Existing 12 `send` tests | `h-mad/tests/test_hmad_dispatch.py` | modify | Stage a receipt so they exercise the enforced path |
| Phase-5 preflight prose | `h-mad/SKILL.md` | modify | FR-9 |
| Receipt documentation | `h-mad/references/agent-substrate.md` | modify | FR-9 |

## Implementation Order

Partitioned for Phase-5 dispatch. Independence is stated explicitly because it determines fanout
eligibility.

- **Task 1 — receipt lifecycle** (`_receipt_file`, `_fingerprint`, `_receipt_write`,
  `_receipt_clear`, `_cmd_env` wiring). Satisfies FR-1, FR-2, FR-8.
  *Dependencies on other tasks: None.*
- **Task 2 — conflict guard** (`_preflight_conflict_check` + its `_cmd_send` call). Satisfies FR-7.
  Touches `_cmd_send` but needs nothing from Task 1: it reads resolution only.
  *Dependencies on other tasks: None.*
- **Task 3 — receipt enforcement at dispatch** (`_receipt_valid`, TTL, bypass, `_cmd_send` wiring,
  migration of the 12 existing `send` tests). Satisfies FR-3, FR-4, FR-5, FR-6.
  *Dependencies: Task 1 (needs the receipt to exist) and Task 2 (shares the `_cmd_send` call site).*
- **Task 4 — documentation** (`SKILL.md`, `references/agent-substrate.md`). Satisfies FR-9.
  *Dependencies: Tasks 1–3, since the prose must state the shipped reason tokens.*

Tasks 1 and 2 are mutually independent and touch disjoint code, making them the fanout pair; Tasks 3
and 4 are serial on the shared tree afterwards.

## Data Model / Schema Changes

New on-disk artifact, not a schema change to any existing store. `orchestrator_state`,
`h_mad_state_schema.json`, and `.h-mad/telemetry.jsonl` are untouched.

`preflight.receipt` — three `key=value` lines:

| Key | Type | Example |
|---|---|---|
| `verdict` | literal `PASS` | `PASS` |
| `fingerprint` | string, `codex=<v>;agy=<v>` | `codex=term_957…;agy=term_5bb…` |
| `ts` | integer epoch seconds | `1784781000` |

Written only on PASS, so `verdict` has exactly one legal value; any other value is treated as an
invalid receipt. Not tracked by git (AC-8.4), consistent with `.h-mad/orca-pins.env`, which is also
untracked.

**No `.gitignore` change is required, and this was verified rather than assumed.** `.gitignore:32`
ignores the whole `.h-mad/` directory, so any receipt written to the default path is untracked
automatically; `.h-mad/invariants.md` is tracked only because it was force-added. Confirmed with
`git check-ignore -v .h-mad/preflight.receipt` → `.gitignore:32:.h-mad/`. AC-8.4's test therefore
asserts the ignore rule covers the path, not that a new rule was added — a test asserting a new
`.gitignore` entry would fail against a correct implementation.

## API / Interface Changes

No verb is added or removed. No function signature visible to callers changes.

| Name | Type | Default | Purpose |
|---|---|---|---|
| `HMAD_PREFLIGHT_RECEIPT_FILE` | env var, path | `$(dirname $(_pin_file))/preflight.receipt` | Override receipt location — FR-8 |
| `HMAD_PREFLIGHT_TTL_SEC` | env var, integer seconds | `3600` | Receipt freshness window — FR-5 |
| `HMAD_SKIP_PREFLIGHT` | env var, any non-empty | unset (enforced) | Bypass the receipt requirement — FR-6 |

`env` stdout is unchanged and additive-only — the receipt is a side effect, not a printed line, so
every existing parser of `substrate:`, `<agent> -> <handle>`, `stale pins:`, `CONFLICT:`,
`orchestration:` and `PREFLIGHT:` is unaffected.

`send` gains new non-zero returns. Exit-code contract for `send`:

| Condition | Return | Channel |
|---|---|---|
| Missing prompt file (existing) | 2 | stderr |
| Agent conflict (new) | 1 | stderr, `preflight_agent_conflict` |
| Receipt absent / invalid / expired / rotated (new) | 1 | stderr, reason token |
| Stale handle (existing) | 1 | stderr, `terminal_handle_stale` |
| Success | 0 | — |

## Error Handling Strategy

Refusals are **return codes plus stderr diagnostics**, never stdout tokens. This is the deliberate
distinction the spec records: `invariants.base.md` §"Audit-gate signal discipline" governs gates
whose verdict the orchestrator consumes, which must use a stdout token and exit 0. `env` remains
such a gate and is unchanged. `send` is an operation, and an operation that declines to act reports
non-zero — precisely the shape the existing `terminal_handle_stale` refusal already has
(`hmad-dispatch.sh:757-759`). Adding a stdout verdict token to `send` would be the actual
inconsistency here.

Every refusal names its condition and its recovery in the stderr message, following the existing
refusal's wording pattern ("…; nothing was sent. Re-pin … or relaunch …"). Nothing is delivered on
any refusal path — the guards precede both delivery branches, so this is structural rather than a
property each branch must remember.

`_receipt_valid` prints its reason on stdout to its **caller inside the wrapper** (command
substitution), which then composes the stderr message; the reason token never reaches the user's
stdout.

## Test Strategy

All tests are subprocess-level against the real wrapper via the existing
`run(args, *, substrate, env, capture, cwd)` helper in `h-mad/tests/test_hmad_dispatch.py:94`, with
stub `orca`/`cmux` binaries from `STUBS` on an isolated PATH. No new fixtures or test files: the
module constants are `SKILL`, `WRAPPER`, `STUBS` — verified against the file itself, not assumed
from a sibling.

Two harness facts the design depends on:

- `run()` already does `e.setdefault("HMAD_ORCA_PIN_FILE", _absent_pin_file())`, so with the receipt
  default anchored to the pin file's directory, **every existing test is automatically isolated**
  from a developer's live receipt. No suite-wide `HMAD_SKIP_PREFLIGHT` default is introduced — that
  would make every enforcement assertion vacuous.
- `HMAD_STUB_CAPTURE` (via `capture=`) records stub invocations, which is how AC-3.2 is asserted
  against the **absence of a delivery call**, not merely against an exit code.

The 12 existing `send` tests are migrated by passing a shared explicit
`HMAD_PREFLIGHT_RECEIPT_FILE` and invoking `env` before `send` in the same environment — so they
exercise the real enforced sequence rather than bypassing it.

**Guards must discriminate.** Every refusal test is paired with a negative-case test asserting the
guard does *not* fire when it should not (AC-4.4, AC-7.3), and the existence of the refusal path is
asserted before asserting what it lacks. A test that only ever observes refusals passes forever
against a guard that refuses unconditionally.

## Test Plan

All in `h-mad/tests/test_hmad_dispatch.py`. Verification command:

```bash
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q
```

| Scenario | Asserts |
|---|---|
| `env` PASS writes receipt with all three keys | AC-1.1, AC-1.2 |
| Two `env` runs, same handles → identical fingerprint | AC-1.3 |
| `env` run with a changed handle → different fingerprint | AC-1.4 |
| `env` PASS still prints `PREFLIGHT: PASS`, exits 0 | AC-1.5 |
| `env` FAIL (stale) writes no receipt from a clean start | AC-2.1 |
| `env` FAIL removes a pre-existing valid receipt | AC-2.2 |
| `env` FAIL still prints its `stale=`/`conflict=` fields, exits 0 | AC-2.3 |
| `send` immediately after a FAIL preflight is refused | AC-2.4 |
| `send` with no receipt returns non-zero | AC-3.1 |
| `send` with no receipt makes no delivery call (capture is empty) | AC-3.2 |
| Each refusal emits its distinct token on stderr | AC-3.3, AC-7.2 |
| `send` with a valid receipt delivers; inline vs indirection unchanged by size | AC-3.4 |
| Handle changed after receipt → `preflight_handles_rotated` | AC-4.1 |
| Receipt written while agy `UNRESOLVED`, then agy pinned → refused | AC-4.2 |
| Re-running `env` after the change permits the dispatch, no file edit | AC-4.3 |
| Handles unchanged → **not** refused | AC-4.4 |
| Receipt aged past TTL → `preflight_expired` | AC-5.1 |
| Receipt within TTL, fingerprint matching → permitted | AC-5.2 |
| `HMAD_PREFLIGHT_TTL_SEC` honoured | AC-5.3 |
| Unset TTL yields 3600, not an error or an infinite window | AC-5.4 |
| `HMAD_SKIP_PREFLIGHT=1`, no receipt → delivers | AC-6.1 |
| Bypass emits a stderr notice | AC-6.2 |
| Bypass unset → enforced (the default is fail-closed) | AC-6.3 |
| Bypass set but agents conflict → still refused | AC-6.4 |
| Both agents one handle → `send` to either refused, nothing sent | AC-7.1 |
| Agents on different handles → **not** refused for conflict | AC-7.3 |
| Both `UNRESOLVED` → not a conflict | AC-7.4 |
| `HMAD_PREFLIGHT_RECEIPT_FILE` set → default path untouched | AC-8.1 |
| Unset → default path used | AC-8.2 |
| Receipt path is gitignored/untracked | AC-8.4 |
| `SKILL.md` states refusal behavior and names the reason tokens | AC-9.1 |
| Each reason token has a documented recovery | AC-9.2 |
| `agent-substrate.md` documents receipt + all three variables | AC-9.3 |
| `SKILL.md` frontmatter still has valid `name`/`description` | AC-9.4 |

**AC-8.3 is deliberately not a test.** "Suite pass/fail counts identical with and without a receipt
at the default path" is a property *of* the suite; a test inside it cannot honestly assert it.
Verified by running the suite twice — once with the default receipt path populated, once with it
absent — and comparing **counts only, never the summary line** (an elapsed-time difference in the
line produced a false negative on the previous feature).

## Invariant Compliance

**Base — Audit-gate signal discipline.** Complies. `env` keeps its stdout `PREFLIGHT:` token and
exit 0 on both verdicts; the receipt is a side effect written after the token is printed. `send` is
an operation, not a verdict-consuming gate, so its non-zero refusal is outside this rule's scope and
matches the existing `terminal_handle_stale` precedent. No gate is changed to exit non-zero.

**Base — Single-source contract.** Complies. `_fingerprint` is the single writer *and* reader of the
fingerprint format, called from both `_receipt_write` and `_receipt_valid`, so the two sides cannot
drift. `_receipt_file` is the single resolver of the path.

**Base — No-plugin-dependency.** Complies. No new external command: `date +%s`, `rm`, `grep`,
`dirname` are already used by the wrapper. Hashing was rejected specifically to avoid a
`shasum`/`sha256sum` portability dependency.

**Base — Backward-compatibility.** Partially by design, and stated rather than glossed: `send` gains
a refusal that did not previously exist, which is the feature's entire point. Mitigated by the
documented `HMAD_SKIP_PREFLIGHT` opt-out (FR-6), and by leaving every stdout contract, verb, flag and
existing exit code unchanged. All operator overrides (`HMAD_ORCA_PIN_FILE`, `HMAD_ORCA_*_TERMINAL`,
`HMAD_CMUX_*_SURFACE`, `HMAD_SEND_INLINE_MAX`) retain their current precedence.

**Base — Operator-override preservation.** Complies. Three new overrides added, none removed; the
env-pin-over-pin-file-over-auto-detect precedence in `_resolve_target` is untouched.

**Base — Marker discipline.** Complies. No `[H-MAD]` marker is emitted by `send`; refusals are
stderr diagnostics, matching the existing refusal which also emits no marker.

**Base — Doc-template superset compliance.** Complies. This document carries every heading in the
Phase-4 template.

**Project — Skill self-containment.** Complies. All changes are inside `h-mad/`; no import of another
skill's internals, and no hardcoded path outside the skill directory. The receipt path is derived
from the pin file's directory, which is caller-controlled, not absolute.

**Project — Skill manifest integrity.** Complies. `SKILL.md` frontmatter (`name`, `description`) is
unchanged; the entry behavior of the skill is unchanged. The Phase-5 prose is updated in the same
change that alters wrapper behavior, so contract and documentation ship together (AC-9.1, AC-9.4).

### Cross-cutting decision: substrate applicability

Enforcement applies on **both cmux and orca**, not orca-only. Rationale: `_fingerprint` is built from
`_resolve_target`, which is already substrate-aware and returns surfaces on cmux and handles on
orca — so the mechanism is substrate-agnostic without any branching. `env` prints `PREFLIGHT:` on
both substrates today, so enforcing on only one would make the same token mean two different things.
The stale-detection that motivates it is orca-specific, so a cmux receipt will in practice only ever
fail on conflict or expiry — which is correct, not vacuous. An orca-only carve-out would be an
untested branch guarding a substrate nobody would exercise.

## Version History
- v1.0: Initial design draft.
- v1.1: Resolved the cycle-1 audit Nit — confirmed `.gitignore:32` already ignores `.h-mad/`, so
  AC-8.4 needs no `.gitignore` change and its test asserts the existing rule covers the receipt
  path. No design decision changed; gate was already `PASS must=0 should=0`.
