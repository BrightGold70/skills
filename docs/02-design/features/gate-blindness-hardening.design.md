# Design: gate-blindness-hardening

## Executive Summary

`h_mad_phase7_preconditions.check()` gains a total `archreview` ladder — every value, including
absence, produces a verdict — the schema enum gains one override value, `SKILL.md` §6a-prime
switches its preflight from pane resolution to `command -v agy` and records the assessment it
extracts, and the shared `orca` stub gains an opt-in hostile-payload corpus.

## Overview

The gate is a pure predicate over a state record plus an analysis file, so FR-1/2/3 are
unit-testable with no runtime. The protocol changes (FR-4, FR-6) have no runtime at all and are
enforced by doc tests, as this repo already does elsewhere. The only stateful surface is the
stub corpus. The binding constraint is not technical difficulty but **ordering**: this repo is
the live `~/.claude/skills/h-mad`, so each change is active for this feature's own Phase 7 the
moment it lands.

## Architecture Overview

```
h_mad_phase7_preconditions.check(record, analysis_path)
  ├─ phase / analysis / match-rate ladder            (unchanged)
  ├─ halt ladder                                     (unchanged)
  └─ archreview ladder                               ← TOTAL after this change
       READY_TO_MERGE            → (nothing)                       ready
       WITH_FIXES | NO           → blocker archreview_failed        (unchanged)
       SKIPPED_NO_PANE           → blocker archreview_skipped       (was: warning)
       SKIPPED_OPERATOR_OVERRIDE → warning archreview_overridden    (new)
       absent | null | unknown   → blocker archreview_not_run       (new; was: silence)

SKILL.md §6a-prime
  preflight: `command -v agy`        (was: `hmad-dispatch alive agy`)
  dispatch : exec agy                (pane-independent)
  extract  : ASSESSMENT: → h_mad_state_write.py --set archreview=<value>   ← new, mandatory
  no agy   : archreview=SKIPPED_OPERATOR_OVERRIDE  (was: SKIPPED_NO_PANE)

tests/stubs/orca
  HMAD_STUB_HOSTILE=markdown|newlines|markers|all   ← opt-in, unset = today
```

## Detailed Design

### The `archreview` ladder becomes total

The defect is structural, not a wrong branch: the existing `if/elif` has no `else`, so the
*absence* of a review falls through to success. Every ladder above it in `check()` already
handles its own failure explicitly; this one alone treats "no data" as "no problem".

The replacement is a total mapping. Ordering inside the ladder is deliberate — the known values
are matched first and the catch-all is last, so an unrecognised future value cannot be silently
read as ready:

| `archreview` | Result | Code |
|---|---|---|
| `READY_TO_MERGE` | ready | — |
| `WITH_FIXES`, `NO` | **blocker** | `archreview_failed` |
| `SKIPPED_NO_PANE` | **blocker** | `archreview_skipped` |
| `SKIPPED_OPERATOR_OVERRIDE` | ready + **warning** | `archreview_overridden` |
| absent, `null`, anything else | **blocker** | `archreview_not_run` |

`null` and unknown values collapse into `archreview_not_run` on purpose. The schema enum
excludes `null`, so `h_mad_state_write.py` cannot produce it — it can only arrive from a
hand-edited or legacy store, which is exactly the case that must not read as success. Reaching
the catch-all is always "we do not have a review", regardless of how the record got there.

Blocker/warning entries keep the established `{"code", "detail"}` shape and `check()`'s return
contract (`{"ready": not blockers, "blockers", "warnings"}`) is unchanged, so every existing
caller and the CLI's token/exit discipline (exit 0 on a verdict, 2 on operational error) are
untouched.

**Detail text is load-bearing, not decoration.** Two of the codes exist to redirect an operator
who is about to take the wrong path:

- `archreview_skipped` must name the headless remedy (`exec agy` satisfies the gate), because
  the operator arriving here has just been told a pane was unavailable and the override is the
  nearer-looking exit.
- `archreview_not_run` must name the field and how to populate it, so it reads as "record the
  review you ran" rather than "this gate is broken".

A returncode-only test cannot distinguish these from a bare failure, so the ACs assert content.

### Schema: one enum value

`archreview` is already an enum of four values, so this is an extension, not a new field:

```
enum: [READY_TO_MERGE, WITH_FIXES, NO, SKIPPED_NO_PANE, SKIPPED_OPERATOR_OVERRIDE]
```

Adding a value cannot invalidate records using the existing four (all 9 closed features carry
`READY_TO_MERGE`). The writer's refusal of out-of-schema values is what makes FR-3's override
un-misspellable — a typo'd `SKIPPED_OVERRIDE` is rejected at write time rather than silently
falling into the catch-all blocker.

`SKIPPED_NO_PANE` is **retained** in the enum although the gate now blocks on it: existing and
in-flight records may carry it, and removing it would make those records unwritable. Its schema
description is updated to say it now blocks.

### `SKILL.md` §6a-prime

Three edits, each with a doc test:

1. **Preflight** becomes `command -v agy` rather than `hmad-dispatch alive agy`. The section's
   own rationale for the preflight — refuse to proceed with no reviewer — is preserved; only
   the definition of "a reviewer is available" changes, from a resolved pane to an available
   CLI. This matches §"Reviewing a skill with agy", which already states `exec` is
   pane-independent and that a `PREFLIGHT: FAIL` from a stale pin does not block it.
2. **Record the assessment.** Immediately after extracting `ASSESSMENT:` with
   `h_mad_extract_verdict.py`, write it:
   `h_mad_state_write.py --feature <f> --set archreview=<value>`. This is the "prevent" half of
   the pair whose "enforce" half is FR-1. Enforcing an absence still leaves a human to remember;
   this removes the remembering.
3. **The reviewer-less route** names `SKIPPED_OPERATOR_OVERRIDE`, and says plainly that it is an
   operator decision that will surface as a warning in the Phase-7 report — not the ordinary
   response to an unresolved pane, which is now "dispatch headless".

The existing halt `step6a-prime:no_reviewer_pane` is retained but re-scoped: it fires when the
`agy` CLI is absent, not when a pane fails to resolve.

### Hostile-payload corpus

The stub gains a selector consulted only when set, matching `HMAD_STUB_ORCA_WT_PS_STDOUT` /
`HMAD_STUB_ORCA_TASKLIST_STDOUT` / `HMAD_STUB_ORCA_STATE`:

| `HMAD_STUB_HOSTILE` | Payload contains |
|---|---|
| `markdown` | `[a](b)`, `**bold**`, bare `*` and `[` — the glob metacharacters that caused the live defect |
| `newlines` | embedded `\n` and `\t` |
| `markers` | the literal `h-mad: ` lead-in and `⟦/h-mad⟧` terminator, as data |
| `all` | the union |
| unset | today's tidy value — this is what keeps 1143 tests passing |
| unrecognised | **exit non-zero with a message naming the valid corpora** |

The unrecognised case is a loud failure rather than a fallback because a silent fallback to
tidy input would restore the blind fixture on a typo — reintroducing precisely the condition
that hid the original bug.

The `markers` corpus is the adversarial one: it feeds our own span syntax back as content. It
must be emitted as JSON-encoded data (via `jq --arg`, as the stub already does for the stateful
comment) so it cannot corrupt the envelope it travels in.

### Implementer-template mandate

`references/codex-implementer-prompt.md` gains a short clause: any fixture value that
originates from an agent or a human must be driven with a hostile payload, naming
`HMAD_STUB_HOSTILE`, plus one sentence of rationale — tidy ASCII fixtures let a
card-corrupting defect pass 1063 tests, a clean mutation sweep, five wire-scoped reverts and an
architectural review. The rationale is included so a future reader can weigh the rule rather
than cargo-cult it.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `archreview` ladder | `h-mad/scripts/h_mad_phase7_preconditions.py` | modify | Total mapping; FR-1, FR-2, FR-3 |
| `archreview` enum + descriptions | `h-mad/scripts/h_mad_state_schema.json` | modify | FR-3 |
| §6a-prime protocol | `h-mad/SKILL.md` | modify | FR-4 |
| Hostile corpus + selector | `h-mad/tests/stubs/orca` | modify | FR-5 |
| Fixture mandate | `h-mad/references/codex-implementer-prompt.md` | modify | FR-6 |
| Gate tests (invert 2, add ladder cases) | `h-mad/tests/test_h_mad_phase7_preconditions.py` | modify | FR-1–FR-3 |
| 6a-prime doc tests (retarget 4) | `h-mad/tests/test_h_mad_archreview_pane_halt.py` | modify | FR-4 |
| Template doc test | `h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py` | modify | FR-6 |
| Corpus tests | `h-mad/tests/test_h_mad_hostile_fixtures.py` | new | FR-5 |

## Implementation Order

Follows the plan's landing order exactly; the chain is a safety property, not a preference.

1. **FR-4** — `SKILL.md` preflight + auto-record + override route, with its doc tests. Until
   this lands nothing produces an `archreview` value in the ordinary case.
2. **FR-3** — enum value + `archreview_overridden` warning branch. The escape must exist before
   either blocker arms.
3. **FR-2** — `SKIPPED_NO_PANE` warning → blocker, with the remedy text.
4. **FR-1** — the catch-all `archreview_not_run` blocker. Last: strictest, and the only one that
   fires on records nobody edited.
5. **FR-5** — stub corpus (independent of the chain).
6. **FR-6** — template mandate (depends on FR-5 existing to name).

## Data Model / Schema Changes

One enum extension in `h_mad_state_schema.json`: `archreview` gains
`"SKIPPED_OPERATOR_OVERRIDE"`. `SKIPPED_NO_PANE` is retained for record compatibility with its
description updated to state that it now blocks. No new field, no migration — absence is
already the pre-change state of every record that never recorded a review.

## API / Interface Changes

- **New blocker codes**: `archreview_not_run`, and `archreview_skipped` changes from a warning
  code to a blocker code (same string, different severity).
- **New warning code**: `archreview_overridden`.
- **New state value**: `archreview: "SKIPPED_OPERATOR_OVERRIDE"`.
- **New test-only env var**: `HMAD_STUB_HOSTILE` (unset → today's behaviour).
- Unchanged: `check()`'s signature and return shape, the `PHASE7:` token grammar, exit
  discipline, and every other ladder.

## Error Handling Strategy

Gate verdicts are data, never exceptions: `check()` returns blockers/warnings and the CLI prints
`PHASE7: READY|BLOCKED` at exit 0, reserving exit 2 for operational errors (unreadable state).
That discipline is unchanged — a stricter gate must not start registering as a tool failure,
which is the base invariant on audit-gate signal discipline.

The stub's unrecognised-corpus case is the deliberate exception: it exits non-zero, because it
is a *test-authoring* error rather than a verdict about the system under test, and silence there
would restore the blindness this feature removes.

## Test Strategy

- **Unit, no runtime** — the whole `archreview` ladder via `p7.check(record, analysis)`, as the
  existing tests already do. Every row of the table gets a case, including the catch-all reached
  three different ways (absent, `null`, unknown string).
- **Doc tests** — `SKILL.md` and the implementer template, asserting specific contract phrases,
  not loose keyword presence. Mutation-checked by deleting the sentence.
- **Stub-level** — the corpus content asserted directly (`[` and `*` must be literally present),
  and a round-trip proving `markers` survives as data.
- **Regression** — the full suite with `HMAD_STUB_HOSTILE` unset must stay at ≥1143.
- **Inverted assertions** — each of the six pinned in the plan must assert the new contract
  positively; net assertion count must not fall. A deletion is not a substitute.

## Test Plan

| Scenario | Asserts | AC |
|---|---|---|
| record without `archreview` | `PHASE7: BLOCKED`, code `archreview_not_run` | AC-1.1 |
| `archreview: null` | blocked, same code | AC-1.2 |
| blocker detail names the field + remedy | content, not just the code | AC-1.3 |
| `READY_TO_MERGE` | `PHASE7: READY blockers=0` | AC-1.4 |
| verdict/exit discipline | exit 0 on both verdicts, 2 on unreadable state | AC-1.5 |
| `SKIPPED_NO_PANE` | blocked, code `archreview_skipped` | AC-2.1 |
| its detail names `exec agy` as the remedy | content | AC-2.2 |
| no other `SKIPPED_*` is accepted as a warning | unknown `SKIPPED_FOO` → blocked | AC-2.3 |
| `SKIPPED_OPERATOR_OVERRIDE` | ready + warning `archreview_overridden` | AC-3.1 |
| writer accepts it; rejects a misspelling | `h_mad_state_write.py` round trip | AC-3.2 |
| warning text requires carrying into the report | content | AC-3.3 |
| only the override converts missing → ready | table sweep | AC-3.4 |
| §6a-prime states `exec agy` satisfies the gate | doc | AC-4.1 |
| §6a-prime no longer prescribes `SKIPPED_NO_PANE` as ordinary | doc | AC-4.2 |
| §6a-prime instructs writing `archreview` after extraction | doc | AC-4.3 |
| reviewer-less route names the override | doc | AC-4.4 |
| full suite, knob unset | ≥1143 passed, 0 failed | AC-5.1 |
| corpus selector accepts the four names | stub | AC-5.2 |
| `markdown` contains a literal `[` and `*` | direct assertion | AC-5.3 |
| `markers` round-trips as data | envelope still valid JSON | AC-5.4 |
| unrecognised corpus name | non-zero exit + message naming valid names | AC-5.5 |
| template mandates hostile payloads, names the knob | doc | AC-6.1 |
| template states the rationale | doc | AC-6.2 |

Verification: `pytest h-mad/tests/ handoff/ -q`, then `h_mad_mutation_harness.py <spec>` with
`root` passed explicitly (its default is the spec file's directory).

## Invariant Compliance

**Base — audit-gate signal discipline.** The gate keeps exit 0 on every verdict; only
operational errors exit non-zero. A stricter gate that started exiting non-zero would register
as a `PostToolUseFailure` and leak into coexisting plugins — the exact defect that discipline
exists for. Complies.

**Base — single-source contract.** The `archreview` ladder exists in exactly one place
(`check()`); `SKILL.md` describes it rather than re-implementing it. The corpus strings live in
one stub. Complies.

**Base — no new external dependency.** Stdlib Python, bash, `jq` (already required). Complies.

**Base — backward compatibility.** Enum extended, not narrowed; `SKIPPED_NO_PANE` retained so
existing records stay writable; the stub knob defaults to today's behaviour. The claim that no
closed record trips the new blocker is executed, not asserted:

```
$ python3 -c "import json; d=json.load(open('docs/.bkit-memory.json'))['orchestrator_state']; \
  closed={k:v.get('archreview','<ABSENT>') for k,v in d.items() if v.get('last_completed_phase')==7}; \
  [print(f'{v:<16} {k}') for k,v in sorted(closed.items())]; \
  print(f'--- closed={len(closed)} absent={sum(1 for v in closed.values() if v==chr(60)+chr(65)+chr(66)+chr(83)+chr(69)+chr(78)+chr(84)+chr(62))}')"
READY_TO_MERGE   cycle-telemetry-fidelity
READY_TO_MERGE   dispatch-resolve-verb
READY_TO_MERGE   exec-missing-report-recovery
READY_TO_MERGE   exec-path-hardening
READY_TO_MERGE   fanout-integrity-and-defects
READY_TO_MERGE   orca-git-native-checkpoints-and-merge-gate
READY_TO_MERGE   preflight-read-enforcement
READY_TO_MERGE   preflight-signal-discipline
READY_TO_MERGE   tdd-dispatch-verification-discipline
--- closed=9 absent=0
```

`absent=0` is the load-bearing number: it is the count of records the new `archreview_not_run`
blocker would fire on. Complies.

**Base — operator-override preservation.** Strengthened: the escape becomes explicit and
recorded rather than an unchecked omission, and it surfaces as a warning that must reach the
report.

**Base — mutation verification.** Every new guard, including the doc guards, is mutated to its
permissive value with a content assertion.

**Base — marker discipline.** No new `[H-MAD]` marker; the gate's existing marker line is
unchanged.

**Project — skill self-containment.** All changes are inside `h-mad/`; no cross-skill import and
no path outside the skill. Complies.

**Project — skill manifest integrity.** `SKILL.md` §6a-prime changes its stated behaviour, so
the entry contract is updated in the same commit; frontmatter `name`/`description` unchanged.
Complies.

## Version History

- v1.0: Initial design draft.
- v1.1: Design audit cycle 1 — 1 must-fix. The backward-compatibility claim said "all 9 closed
  records carry READY_TO_MERGE (verified)" without the command or its output, which the
  assumption-verification invariant treats as unverified by construction: a reviewer cannot
  check it. The probe was re-run fresh (a carried result is not evidence) and its command and
  full output are now inlined, with `absent=0` called out as the load-bearing number — it is
  the count of records the new `archreview_not_run` blocker would fire on.
