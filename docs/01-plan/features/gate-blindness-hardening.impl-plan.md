# Implementation Plan: gate-blindness-hardening

> Source: docs/02-design/features/gate-blindness-hardening.design.md (post-audit v1.1)
> Branch target: feature/214-gate-blindness-hardening

## Executive Summary

Six tasks land in the order FR-3 → FR-4 → FR-2 → FR-1, then the two independent tasks FR-5 and
FR-6 — so that no blocker is ever armed before the means of satisfying it exists, and no
protocol text instructs writing a value the schema does not yet accept. The FR-3/FR-4 swap
relative to the plan and design is deliberate and justified in §"Landing order".

## Landing order is a safety property

Tasks 1–4 MUST land in the order given. This repo is the live `~/.claude/skills/h-mad` via
symlink, so each gate change is active for **this feature's own Phase 7** the moment it lands.
Landing Task 4 (FR-1, absent `archreview` blocks) before the tasks that produce the field would
make it mandatory while nothing writes it and no override exists — and the first run to hit that
deadlock is this feature's own closure. Tasks 5 and 6 are independent of the chain; Task 6
depends only on Task 5 existing to name.

**Order corrected at 5b cycle 1 — FR-3 and FR-4 are swapped relative to the plan and design.**
Both documents mandate `FR-4 → FR-3 → FR-2 → FR-1`. That is wrong in one detail, and the audit
caught it: FR-4 makes `SKILL.md` instruct writing `archreview=SKIPPED_OPERATOR_OVERRIDE`, but
FR-3 is what adds that value to the schema enum. Landing FR-4 first documents a value the writer
**refuses**. Verified empirically against the current tree rather than reasoned about:

```
$ h_mad_state_write.py <state> --feature gate-blindness-hardening \
    --set archreview=SKIPPED_OPERATOR_OVERRIDE
ERROR: record for 'gate-blindness-hardening' would not validate (classified historical);
refusing to write.
```

The corrected order is **FR-3 → FR-4 → FR-2 → FR-1**. The safety property the plan actually
protects is *both means before both blockers*, and that is preserved exactly — only the internal
order of the two means changes. FR-3 arms no blocker: it adds an accepted enum value and a
warning branch, so nothing can strand on it.

## Pins re-verified against the tree (2026-08-06, this dispatch)

Every pin below was confirmed against the working tree immediately before this plan was written,
per §"Audit prompt assembly" — a stale pin produces a wrong edit or a fabricated failure.

| Pin | Claim | Verified |
|---|---|---|
| `h_mad_phase7_preconditions.py:86-101` | `archreview` ladder, `if`/`elif`, **no `else`** | yes — ladder ends at the `elif` on :94, `return` on :103 |
| `h_mad_state_schema.json` `archreview` | enum is exactly the 4 values | yes — `READY_TO_MERGE, WITH_FIXES, NO, SKIPPED_NO_PANE` |
| schema description | already says `SKIPPED_NO_PANE` "is never equivalent to READY_TO_MERGE" | yes — A4 holds; FR-2 makes the gate agree with the schema |
| `test_h_mad_phase7_preconditions.py` | 2 pinned assertions | yes — `:113`, `:119` |
| `test_h_mad_archreview_pane_halt.py` | 4 pinned assertions | yes — `:49`, `:57`, `:65`, `:77` |
| `test_h_mad_hostile_fixtures.py` | does not yet exist | yes — absent, so Task 5 creates it |
| `tests/stubs/orca`, `references/codex-implementer-prompt.md`, `test_h_mad_tdd_dispatch_discipline_prompt.py` | exist, to be modified | yes |

**Baseline suite count measured, not carried — it is 1143.** The plan says 1143 and the prior
session's handoff says 1148; the handoff is wrong. Measured on the branch point this dispatch:

```
$ /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ handoff/ -q
1143 passed in 121.68s (0:02:01)
```

**1143** is the AC-5.1 floor. The discrepancy is exactly why the count is re-measured rather than
carried: had the handoff's 1148 been adopted, AC-5.1 would have failed against a correct suite.

## Task 1: The operator override exists (FR-3)

**Production file**: `h-mad/scripts/h_mad_state_schema.json`, `h-mad/scripts/h_mad_phase7_preconditions.py`
**Test file**: `h-mad/tests/test_h_mad_phase7_preconditions.py` (AC-3.1, AC-3.3 — the `check()`
predicate) **and** `h-mad/tests/test_h_mad_state_write.py` (AC-3.2 — the writer round trip).
Two production files with two distinct contracts get two test homes: `check()` is a pure
predicate, the enum is enforced by the writer, and putting a writer round-trip in the gate's
test file would place it outside the boundary it verifies. Both files already exist.
**Task shape**: `new-behaviour`

**Description**: Extend the `archreview` enum with `SKIPPED_OPERATOR_OVERRIDE` and add the
matching `check()` branch: ready, plus a warning coded `archreview_overridden`. The escape must
exist **before** either blocker arms, so a genuinely reviewer-less run has somewhere to go.
`SKIPPED_NO_PANE` is retained in the enum — existing and in-flight records may carry it and
removing it would make them unwritable — with its description updated to state that it now
blocks. The writer's refusal of out-of-schema values is what makes the override un-misspellable:
a typo'd `SKIPPED_OVERRIDE` is rejected at write time rather than falling silently into Task 4's
catch-all.

**Code structure**:
```python
# in check(), inside the archreview ladder — ordering deliberate, see Task 4
elif archreview == "SKIPPED_OPERATOR_OVERRIDE":
    warnings.append({
        "code": "archreview_overridden",
        "detail": (
            "6a-prime was skipped by explicit operator override. Carry "
            "SKIPPED_OPERATOR_OVERRIDE into the Phase 7 report - no architectural "
            "review happened; this is not READY_TO_MERGE."
        ),
    })
```

Schema edit, exact:

```json
"archreview": {
  "description": "Phase 6a-prime outcome. SKIPPED_NO_PANE records that no reviewer pane resolved; it now BLOCKS Phase 7 - a headless `exec agy` review satisfies the gate. SKIPPED_OPERATOR_OVERRIDE is the deliberate operator escape when no reviewer exists at all; it closes the feature but surfaces as a warning. Neither is ever equivalent to READY_TO_MERGE, and both must surface in the Phase 7 report.",
  "enum": ["READY_TO_MERGE", "WITH_FIXES", "NO", "SKIPPED_NO_PANE", "SKIPPED_OPERATOR_OVERRIDE"]
}
```

**Acceptance Criteria**:
- [ ] AC-3.1: `archreview: "SKIPPED_OPERATOR_OVERRIDE"` → `PHASE7: READY` with a **warning** coded
      `archreview_overridden`.
- [ ] AC-3.2: `h_mad_state_write.py` accepts the value and **rejects a misspelling** — asserted as
      a round trip through the writer, so an invented value cannot reach disk.
- [ ] AC-3.3: The warning text requires the override to be carried into the Phase-7 report, so a
      reader cannot believe a review happened. Content assertion, not code-only.

> **AC-3.4 is deliberately NOT in this task** (moved to Task 4). It asserts the override is the
> ONLY value converting a missing review into a ready state. At this task that is false in two
> ways: `SKIPPED_NO_PANE` is still a warning (Task 3 makes it block) and an absent/unrecognised
> value still falls through with no blocker (Task 4 adds the catch-all). It first becomes
> satisfiable at Task 4.

**Dependencies on other tasks**: None — this is the head of the chain. It arms no blocker, so
nothing can strand on it.

---

## Task 2: 6a-prime accepts a headless review and records its verdict (FR-4)

**Production file**: `h-mad/SKILL.md` (§6a-prime)
**Test file**: `h-mad/tests/test_h_mad_archreview_pane_halt.py`
**Task shape**: `new-behaviour`

**Description**: §6a-prime currently mandates a pane preflight (`hmad-dispatch alive agy`) and
halts `step6a-prime:no_reviewer_pane` when no pane resolves — which is the ordinary state of any
session not started beside a reviewer, so the protocol's precondition fails in the common case
and steers the run straight into FR-1's hole. Three edits: the preflight becomes `command -v
agy`; the extracted `ASSESSMENT:` value is written to `orchestrator_state[<feature>].archreview`
immediately after extraction; and the reviewer-less route names `SKIPPED_OPERATOR_OVERRIDE`
rather than `SKIPPED_NO_PANE`. The existing halt `step6a-prime:no_reviewer_pane` is retained but
re-scoped to "the `agy` CLI is absent". This is the **prevent** half of the pair whose **enforce**
half is Task 4 — enforcing an absence still leaves a human to remember; this removes the
remembering.

**Code structure**: no runtime. Protocol text, enforced by doc tests that assert specific
contract phrases (not loose keyword presence), each mutation-checked by deleting the sentence.

**Acceptance Criteria**:
- [ ] AC-4.1: A doc test asserts §6a-prime states `exec agy` satisfies the gate and does not
      require a resolved pane.
- [ ] AC-4.2: A doc test asserts §6a-prime no longer instructs recording `SKIPPED_NO_PANE` as the
      ordinary response to an unresolved pane.
- [ ] AC-4.3: A doc test asserts §6a-prime instructs writing the extracted `ASSESSMENT:` into
      `orchestrator_state[<feature>].archreview` immediately after extraction.
- [ ] AC-4.4: A doc test asserts the halt route for a genuinely unavailable reviewer names
      `SKIPPED_OPERATOR_OVERRIDE`, not `SKIPPED_NO_PANE`.
- [ ] AC-4.5: §6a-prime instructs **verifying the write landed by reading the field back and
      comparing it to the value written** — not by schema validation. `archreview` is **not** in
      the schema's `required` array (verified), so `h_mad_state_validate.py --strict-only` returns
      `STATE: PASS` on a record where the field is *absent*: it cannot distinguish a landed write
      from a dropped one. The instruction must read the thing it was supposed to change:
      ```bash
      python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py "$STATE" \
        --feature "$F" --set archreview="$ASSESSMENT"
      GOT=$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1]))["orchestrator_state"]
            .get(sys.argv[2]) or {}).get("archreview"))' "$STATE" "$F")
      [ "$GOT" = "$ASSESSMENT" ] || { echo "archreview write did not land: got '$GOT'" >&2; exit 1; }
      ```
      A doc test asserts §6a-prime prescribes a read-back comparison, and is mutation-checked by
      substituting the validator call — which must make the test fail.
- [ ] AC-4.6: Four A5 assertions are **retargeted, not deleted** —
      `test_preflight_checks_the_pane_before_dispatching` (→ `command -v agy`),
      `test_names_unresolved_as_the_trigger` (→ CLI absence),
      `test_state_records_a_skipped_review` (→ the override value), and
      `test_skipping_is_explicitly_not_a_pass` (**kept and strengthened** as the continuity
      marker between the old and new contracts). Net assertion count must not fall.

**Dependencies on other tasks**: Task 1 (must complete first — this task documents writing
`SKIPPED_OPERATOR_OVERRIDE`, which Task 1 is what makes writable).

---

## Task 3: A recorded skip blocks (FR-2)

**Production file**: `h-mad/scripts/h_mad_phase7_preconditions.py`
**Test file**: `h-mad/tests/test_h_mad_phase7_preconditions.py`
**Task shape**: `new-behaviour`

**Description**: Move `SKIPPED_NO_PANE` from `warnings` to `blockers`, keeping the code
`archreview_skipped` (same string, different severity). The detail text is load-bearing: it must
name the headless remedy (`exec agy` satisfies the gate), because an operator arriving here has
just been told a pane was unavailable and Task 2's override is the nearer-looking exit. Pointing
them at the remedy rather than the escape is the whole point of the wording.

**Code structure**:
```python
elif archreview == "SKIPPED_NO_PANE":
    blockers.append({          # was: warnings.append
        "code": "archreview_skipped",
        "detail": (
            "6a-prime did not run (no reviewer pane). A headless review satisfies "
            "this gate: `hmad-dispatch exec agy` needs no pane. If no reviewer "
            "exists at all, record archreview=SKIPPED_OPERATOR_OVERRIDE as a "
            "deliberate operator decision - it closes with a warning."
        ),
    })
```

**Acceptance Criteria**:
- [ ] AC-2.1: `archreview: "SKIPPED_NO_PANE"` → `PHASE7: BLOCKED`, code `archreview_skipped`.
- [ ] AC-2.2: The blocker detail states a headless `exec agy` review satisfies the gate.
- [ ] AC-2.4: Two A5 assertions inverted, each asserting the **new** contract positively, **and
      renamed to match what they now assert** — a test called `..._does_not_block` that asserts
      blocking is a name contradicting its body, and the next reader trusts the name:
      - `test_skipped_archreview_does_not_block` → `test_skipped_archreview_blocks`
      - `test_skipped_archreview_is_surfaced_as_a_warning` → `test_skipped_archreview_is_a_blocker_not_a_warning`

      A deletion is not a substitute; net assertion count must not fall. (Task 2's
      `test_skipping_is_explicitly_not_a_pass` keeps its name deliberately — it is the continuity
      marker, and its name is true under both the old and new contracts.)
- [ ] AC-2.5: Rename the enclosing class `TestSkippedArchreviewIsReportedNotBlocking`, whose name
      asserts the **old** contract and becomes false the moment this task lands. Suggested:
      `TestArchreviewLadder`. Same reasoning as AC-2.4 — a container name that contradicts its
      contents is trusted by the next reader over the assertions inside it. Task 1's two override
      tests were added to this class during RED and move with it.

> **AC-2.3 is deliberately NOT in this task.** It requires an unknown `SKIPPED_FOO` to block,
> which is the catch-all `else` that Task 4 adds. At this task an unrecognised value still falls
> through the `if`/`elif` with no blocker (verified: `SKIPPED_FOO` matches no branch today), so
> AC-2.3 would fail unconditionally here. It is carried to Task 4.

**Dependencies on other tasks**: Task 2 (must complete first).

---

## Task 4: An unrecorded review blocks (FR-1)

**Production file**: `h-mad/scripts/h_mad_phase7_preconditions.py`
**Test file**: `h-mad/tests/test_h_mad_phase7_preconditions.py`
**Task shape**: `new-behaviour`

**Description**: Add the terminal `else` that makes the ladder **total**. The defect is
structural, not a wrong branch: every ladder above this one in `check()` handles its own failure
explicitly, and this one alone treats "no data" as "no problem". Known values are matched first
and the catch-all is last, so an unrecognised future value cannot be silently read as ready.
`null` and unknown strings collapse into `archreview_not_run` on purpose — reaching the catch-all
always means "we do not have a review", regardless of how the record got there. Lands **last**
because it is the strictest and the only one that fires on records nobody edited.

**Code structure**:
```python
elif archreview == "READY_TO_MERGE":
    pass                        # ready
else:                           # absent, None, or any unrecognised value
    blockers.append({
        "code": "archreview_not_run",
        "detail": (
            "no architectural review recorded (orchestrator_state[<feature>]"
            ".archreview is absent or unrecognised). Run 6a-prime headlessly with "
            "`hmad-dispatch exec agy`, then record the extracted ASSESSMENT with "
            "`h_mad_state_write.py <state> --feature <feature> --set "
            "archreview=<value>`. A feature cannot close without one."
        ),
    })
```

**Acceptance Criteria**:
- [ ] AC-1.1: `last_completed_phase = 6`, valid analysis at threshold, no open halt, **no
      `archreview` key** → `PHASE7: BLOCKED`, blocker code `archreview_not_run`.
- [ ] AC-1.2: `archreview: null` → `PHASE7: BLOCKED blockers>=1`, same code. Drives `check()`
      directly, **not** through the writer (the enum excludes `null`, so the writer cannot
      produce it; only a hand-edited or legacy store can).
- [ ] AC-1.3: The blocker detail names the field **and how to satisfy it** — a returncode-only
      assertion must not be able to pass this AC.
- [ ] AC-1.4: `archreview: "READY_TO_MERGE"` still returns `PHASE7: READY blockers=0`.
- [ ] AC-1.5: Token/exit discipline unchanged — exit 0 on any verdict, 2 only on operational
      error. A stricter gate must not start registering as a `PostToolUseFailure`.
- [ ] AC-2.3: No warning path silently accepts any `SKIPPED_*` value other than the FR-3
      override — an unknown `SKIPPED_FOO` blocks. Carried from Task 3, where the catch-all did
      not yet exist; this task is the first at which it is satisfiable.
- [ ] AC-3.4: The override is the ONLY value that converts a missing review into a ready state.
      Carried from Task 1, where it was false twice over (`SKIPPED_NO_PANE` was still a warning
      and unrecognised values still fell through). Assert as a full table sweep over every enum
      value **plus** absent, `null`, and an unrecognised string: exactly `READY_TO_MERGE` and
      `SKIPPED_OPERATOR_OVERRIDE` are ready, everything else blocks.
- [ ] AC-1.6: Executed regression, not asserted. Run this exact command and confirm `absent=0`
      across the 9 closed records — that is the count this blocker would fire on:
      Run it from a heredoc, not a `-c` string: the sentinel contains `<`/`>` and the snippet
      needs both quote styles, so a double-quoted `-c` argument makes correctness depend on bash
      unescaping before Python ever parses it. A quoting bug in a verification command is the
      class that produced this feature's motivating defect — do not reintroduce it here.
      ```bash
      python3 - <<'PY'
      import json
      SENTINEL = "<ABSENT>"
      d = json.load(open("docs/.bkit-memory.json"))["orchestrator_state"]
      closed = {k: v.get("archreview", SENTINEL)
                for k, v in d.items() if v.get("last_completed_phase") == 7}
      for k, v in sorted(closed.items()):
          print(f"{v:<26} {k}")
      print(f"--- closed={len(closed)} absent="
            f"{sum(1 for v in closed.values() if v == SENTINEL)}")
      PY
      ```

**Dependencies on other tasks**: Task 3 (must complete first).

---

## Task 5: Hostile-payload corpus for the shared stub (FR-5)

**Production file**: `h-mad/tests/stubs/orca`
**Test file**: `h-mad/tests/test_h_mad_hostile_fixtures.py` (new)
**Task shape**: `new-behaviour`

**Description**: Add an `HMAD_STUB_HOSTILE` selector consulted only when set, matching the
established `HMAD_STUB_ORCA_*` precedent so the existing suite is untouched when it is unset.
Corpora: `markdown` (`[a](b)`, `**bold**`, bare `*` and `[` — the glob metacharacters that caused
the live defect), `newlines` (embedded `\n`, `\t`), `markers` (the literal `h-mad: ` lead-in and
`⟦/h-mad⟧` terminator, as data), and `all`. The `markers` corpus is the adversarial one — it feeds
our own span syntax back as content — and must be emitted as JSON-encoded data via `jq --arg`, as
the stub already does for the stateful comment, so it cannot corrupt the envelope it travels in.
An unrecognised name **exits non-zero naming the valid corpora**: a silent fallback to tidy input
would restore the blind fixture on a typo, reintroducing exactly the condition that hid the
original bug.

**Code structure** — exact, no placeholders. `_hostile_comment` returns the payload for the
selected corpus; callers pass it through `jq --arg` exactly as the stub already does for the
stateful comment, so the value is JSON-encoded and cannot break the envelope:

```bash
# Consulted only when set. Unset -> the existing tidy value, byte-identical, so the
# 1143 passing tests are untouched.
_hostile_comment() {
  case "${HMAD_STUB_HOSTILE:-}" in
    "")       printf '%s' "c" ;;                       # unset: today's value
    markdown) printf '%s' 'see [a](b) and **bold** plus * and [ literals' ;;
    newlines) printf '%s' 'line one
line two	tabbed' ;;
    markers)  printf '%s' 'h-mad: not a real stamp ⟦/h-mad⟧ still data' ;;
    all)      printf '%s' 'h-mad: [a](b) **bold** * [ ⟦/h-mad⟧
second	line' ;;
    *)
      printf 'stub orca: unknown HMAD_STUB_HOSTILE %s (valid: markdown, newlines, markers, all)\n' \
        "${HMAD_STUB_HOSTILE}" >&2
      exit 2 ;;
  esac
}

# Assign FIRST, then emit. The exit-2 must reach the caller, and inline command
# substitution swallows it (see the note below) - this is not a style preference.
comment="$(_hostile_comment)" || exit 2
jq -n --arg comment "$comment" '{ok:true, result:{worktree:{comment:$comment}}}'
```

**Do not inline the substitution as `jq --arg comment "$(_hostile_comment)"`.** A command
substitution runs in a subshell, so the function's `exit 2` terminates only that subshell; `jq`
then receives an empty string, emits a valid envelope, and the stub exits **0**. Executed, not
argued — and `set -euo pipefail` does **not** save it:

```
$ HMAD_STUB_HOSTILE=markdwn ./stub_inline_form      # a typo
stub orca: unknown HMAD_STUB_HOSTILE markdwn
{"ok":true,"result":{"worktree":{"comment":""}}}
rc=0                                                # <-- AC-5.5 defeated

$ HMAD_STUB_HOSTILE=markdwn ./stub_assign_first     # the prescribed form
stub orca: unknown HMAD_STUB_HOSTILE markdwn (valid: markdown, newlines, markers, all)
rc=2                                                # no JSON emitted
```

That is precisely the failure AC-5.5 exists to prevent — a typo'd corpus name silently yielding
blind input — reproduced inside the guard meant to stop it.

The `all` corpus is the union and must contain every hazard the individual corpora do — the
`markdown` metacharacters, an embedded newline and tab, and both marker tokens — so a test that
selects `all` is strictly stronger than any single corpus.

**Acceptance Criteria**:
- [ ] AC-5.1: With the knob **unset**, both coupled suites pass unchanged at **≥1143** — the
      count measured on this branch point (see §"Pins re-verified"), not a carried figure.
- [ ] AC-5.2: The knob accepts `markdown`, `newlines`, `markers`, `all`.
- [ ] AC-5.3: The `markdown` corpus contains at least one literal `[` and one literal `*`,
      asserted **directly** — not by proxy. Their presence is the point of the corpus.
- [ ] AC-5.4: The `markers` corpus round-trips as data — requesting it leaves the stub's own JSON
      envelope valid and parseable.
- [ ] AC-5.5: An unrecognised corpus name exits non-zero with a message naming the valid names —
      and the test must assert the **stub's own exit code and the absence of a JSON envelope**,
      not merely that something was written to stderr. The inline-substitution form prints the
      message *and* exits 0 with a valid envelope, so a stderr-only assertion passes against the
      broken form.

**Dependencies on other tasks**: None — independent of the FR-4→FR-1 chain.

---

## Task 6: The RED-dispatch template mandates hostile payloads (FR-6)

**Production file**: `h-mad/references/codex-implementer-prompt.md`
**Test file**: `h-mad/tests/test_h_mad_tdd_dispatch_discipline_prompt.py`
**Task shape**: `new-behaviour`

**Description**: A convention that lives only in one test file decays to whatever the next author
types; this template is what every 5d dispatch reads. Add a short clause: any fixture value
originating from an agent or a human must be driven with a hostile payload, naming
`HMAD_STUB_HOSTILE`, plus one sentence of rationale — tidy ASCII fixtures let a card-corrupting
defect pass 1063 tests, a clean mutation sweep, five wire-scoped reverts and a clean
architectural review. The rationale ships **with** the rule so a future reader can weigh it
rather than cargo-cult it.

**Code structure**: no runtime. Template prose, enforced by doc tests asserting the specific
clause and the rationale, mutation-checked by deleting each.

**Acceptance Criteria**:
- [ ] AC-6.1: A doc test asserts the template instructs driving hostile payloads for any value
      originating from an agent or a human, **naming the corpus knob**.
- [ ] AC-6.2: A doc test asserts the template states *why* — that tidy ASCII fixtures let a real
      defect through every gate.

**Dependencies on other tasks**: Task 5 (must complete first — the template names the knob Task 5
creates).

---

## Verification (all tasks)

- `pytest h-mad/tests/ handoff/ -q` — both coupled suites, since `~/.claude/skills/h-mad` is a
  symlink into this repo and a change here can fail a sibling suite.
- `h_mad_mutation_harness.py <spec>` per guard, **with `root` passed explicitly** — its default is
  the spec file's directory, so a spec staged in the scratchpad yields `BASELINE_NOT_GREEN` and
  scores nothing. The doc-test guards are mutated too, by deleting the asserted sentence.
- The whole-module revert per task; no task here is `wiring` shape, so no wire-scoped revert
  applies.

## Version History
- v1.0: Initial implementation plan draft. Task order followed the design's §"Implementation
  Order" exactly; all pins re-verified against the tree at authoring time.
- v1.1: 5b audit cycle 1 — 4 must-fix, 0 should-fix. Each premise was checked against the source
  before the prescription was applied; all four held.
  1. **Sequence contradiction (FR-4 before FR-3).** FR-4 documents writing
     `archreview=SKIPPED_OPERATOR_OVERRIDE` while FR-3 is what adds it to the enum, so the
     documented value would be unwritable in the window between them. Confirmed by running the
     writer rather than reasoning about it — it refuses today. Tasks 1 and 2 swapped, and the
     divergence from the plan/design order is stated explicitly in §"Landing order" with the
     argument that the real safety property (both means before both blockers) is preserved.
  2. **AC-2.3 was unsatisfiable in its task.** It requires an unknown `SKIPPED_FOO` to block, but
     the catch-all `else` is Task 4; at Task 3 an unrecognised value still falls through with no
     blocker (verified). Moved to Task 4, with a note in Task 3 saying why it is absent.
  3. **No post-write verification.** AC-4.5 added: §6a-prime must instruct verifying the
     `archreview` write with `h_mad_state_validate.py --strict-only`, the established post-write
     check, rather than trusting the writer's exit code.
  4. **AC type inconsistency and a vague AC.** Unnumbered bullets in Tasks 2/3/4 promoted to
     numbered ACs (AC-4.6, AC-2.4, AC-1.6), and the backward-compatibility probe command is now
     inlined verbatim instead of pointing at the design.
  Also folded in: the measured branch-point suite count (**1143**, not the handoff's 1148) as the
  AC-5.1 floor.
- v1.2: 5b audit cycle 2 — 3 must-fix, 1 should-fix. All four premises checked and held.
  1. **AC-3.4 was unsatisfiable in Task 1** — and v1.1's scoping note did not fix it, it only
     narrowed the sweep. At Task 1 *two* things still convert missing→ready: `SKIPPED_NO_PANE` is
     a warning until Task 3, and absent/unrecognised falls through until Task 4. Moved to Task 4
     and restated as a full table sweep including absent, `null`, and an unrecognised string.
  2. **TBD placeholders removed.** Every `"detail": ...` is now the exact string, and Task 5's
     `case` is complete executable bash with a `_hostile_comment` helper and the `jq --arg`
     emission. The detail strings are asserted by AC-1.3/AC-2.2/AC-3.3, so leaving them as `...`
     would have handed the implementer the job of inventing text the ACs then grade.
  3. **`<v>` placeholder** in the stub's error message replaced with `${HMAD_STUB_HOSTILE}`.
  4. (should-fix) **Inverted tests renamed**, not just re-asserted:
     `test_skipped_archreview_does_not_block` → `test_skipped_archreview_blocks`, and
     `..._is_surfaced_as_a_warning` → `..._is_a_blocker_not_a_warning`. A name that contradicts
     its body is trusted by the next reader over the assertions.
     `test_skipping_is_explicitly_not_a_pass` deliberately keeps its name — it is the A5
     continuity marker and is true under both contracts.
- v1.3: 5b audit cycle 3 — 1 must-fix, 0 should-fix. Premise checked and held. Task 1 named only
  `test_h_mad_phase7_preconditions.py` as its test home while AC-3.2 is a round trip through
  `h_mad_state_write.py` — a writer test landing in the gate predicate's file, outside the
  boundary it verifies. Task 1 now names both homes with the AC split stated explicitly;
  `h-mad/tests/test_h_mad_state_write.py` already exists (verified), so this is placement, not a
  new file.
- v1.4: 5b audit cycle 4 — 2 must-fix, 0 should-fix, 1 nit. Both premises checked and held; one
  was a defect this plan introduced while fixing cycle 2.
  1. **AC-4.5's own verification was vacuous** — the check added in v1.1. `archreview` is not in
     the schema's `required` array, so `h_mad_state_validate.py --strict-only` returns
     `STATE: PASS` on a record where the field is *absent*, and cannot tell a landed write from a
     dropped one. Executed to confirm rather than reasoned about. AC-4.5 now prescribes reading
     the field back and comparing it to the value written, and is mutation-checked by
     substituting the validator call. The reviewer's suggested remedy named
     `h_mad_state_read.py`, which **does not exist** (checked) — the premise was right and the
     prescription was not, so the read-back is done with stdlib `json`.
  2. **Cross-doc contradiction.** The design and plan still mandated `FR-4 → FR-3` after the
     impl-plan corrected it at cycle 1. Both back-propagated to `FR-3 → FR-4` with the evidence
     and a new risk row; design → v1.2, plan → v1.2.
  3. (nit, fixed) The AC-1.6 probe used a double-quoted `python3 -c` whose correctness depended
     on bash unescaping `\"<ABSENT>\"`. Rewritten as a quoted heredoc — a quoting bug in a
     verification command is precisely the defect class this feature exists to catch. The
     rewritten probe was executed to confirm it runs: `closed=9 absent=0`.
- v1.5: 5b audit cycle 5 — 1 must-fix, 0 should-fix. Premise checked, held, and proved worse than
  reported. Task 5's stub called `_hostile_comment` from **inline command substitution**
  (`jq --arg comment "$(_hostile_comment)"`). A substitution runs in a subshell, so the
  unrecognised-corpus `exit 2` terminates only that subshell: `jq` receives an empty string,
  emits a valid envelope, and the stub exits **0**. Reproduced in a throwaway probe — and
  `set -euo pipefail` did **not** prevent it, which is the part the reviewer did not claim and
  the reason the finding is load-bearing rather than stylistic. This is AC-5.5's own failure mode
  (a typo silently restoring blind input) reproduced *inside the guard written to stop it* —
  the same shape as the glob-unsafe replacement that motivated this feature. Fixed by assigning
  to a variable first (`comment="$(_hostile_comment)" || exit 2`), verified across all three
  paths: typo → rc 2 and no JSON; valid name → payload emitted; unset → today's value. AC-5.5
  was also strengthened to assert the **exit code and the absence of an envelope**, because a
  stderr-only assertion passes against the broken form.
