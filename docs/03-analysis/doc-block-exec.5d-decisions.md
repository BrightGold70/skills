# doc-block-exec — Phase 5d decisions

Decisions settled during 5d, per `h-mad/SKILL.md` §"Document-audit round cap — Phase 5 is
the gate": an open design-logic question surfaces at 5d as a blocked or failing RED and is
settled here, where a wrong choice costs minutes rather than a document round.

The five `OPEN-DECISION (r19, 5d)` lines carried on the impl-plan (Tasks 2/3/4, at
`:2635 :2871 :2873 :3374 :3376`) are NOT settled here. They are reached at their own Tasks.

---

## D1 — `_FenceEvent` field values on non-`open` events (Task 1)

**Raised by**: the Task 1 RED dispatch (`STATUS: NEEDS_CONTEXT`, 5d, session `93d3d858`),
which declined to invent them rather than guessing.

**The gap, exactly.** The impl-plan's `Code structure` block gives neutral-outside-their-kind
values for three of the kind-scoped fields —

    level: int      # heading events only (1-6, the opening-run length); 0 otherwise
    text: str       # heading events only: the compared text (closing-run stripped)
    candidate: bool # scanner-derived: True only for a BACKTICK opener whose first info word is "bash"

— and says nothing about `marker`, `run`, `indent` and `info` on a `close`, `body`, `prose`
or `heading` event. The design describes those four as "the opener's marker character, run
length, indentation and info string", which fixes their meaning on an `open` event and leaves
the other four kinds unstated. AC-1.8's `test_fence_events_trace_on_every_hostile_fixture`
pins **every** field of every event on LF and CRLF copies of each hostile fixture, so the test
cannot be written until this is decided. It is build-class: the 5e production code and that
test differ depending on the answer.

**Decision (operator, 2026-09-06): neutral on every non-`open` event.**

    open   : marker='`'  run=3 indent=<opener indent> info=<raw info string>
    close  : marker=None run=0 indent=0 info=''
    body   : marker=None run=0 indent=0 info=''
    prose  : marker=None run=0 indent=0 info=''
    heading: marker=None run=0 indent=0 info=''   (level and text carry the heading's own values)

**Why this and not the alternatives.**

1. It is the pattern the document already states for every other kind-scoped field: `level`
   is "0 otherwise", `text` is "heading events only", `candidate` is "True only for a
   backtick opener". Three fields neutral outside their kind and four inheriting would be two
   rules where the document reads as one.
2. `marker: str | None` is typed optional. Nothing but a non-opener needs the `None` arm.
3. No consumer reads any of the four on a non-`open` event. `extract` selects on `.candidate`
   and holds the `open` event it de-indents against; `fence_aware_end` reads `.kind`,
   `.level`, `.start` and `.end`; `find_heading` reads `.text`, `.level` and `.end`.
4. Carrying the opener's values onto `body`/`close` would make fence geometry readable off a
   body line, which is the property the design's single-scanner rule exists to prevent
   ("no consumer re-recognises a fence or a heading"). A future consumer could then branch on
   fence state without going through `_fence_events`, which is the shape
   `scanner-duplicated-in-consumer` and `test_extract_has_no_fence_state_of_its_own` guard.

**Residual, stated exactly.** A `close` event does not report the closer's own run length or
indentation, so nothing downstream can distinguish a 3-backtick closer from a 5-backtick one,
or a 0-space closer from a 3-space one. That information is used inside `_fence_events` to
decide closure and is deliberately not exported. If a later task needs it, it is a DESIGN
change and gains its own field and its own mutation row — it is not to be recovered by
re-scanning in a consumer.

**No mutation row follows.** The row list in the impl-plan MIRRORS the design's matrix and
the total is 87 at this batch; adding a row here would put the impl-plan one above the design.
A row for the neutral-fields rule, if the design wants one, is the design's to add. What
stands in for it is the fixture: the AC-1.8 trace test asserts the neutral values on every
non-`open` event of every hostile fixture, on LF and CRLF, so an implementation that carries
opener metadata through fails outright.

---

## D2 — 5d mutation specs are PARKED, not committed unanchored (Task 1)

**Raised by**: the Task 1 RED, which delivered `doc_block_exec.json` (25 rows) and a rewritten
`docsections.json` (8 rows) with anchors omitted or re-pointed at 5e source. Codex followed the
impl-plan's Conventions exactly; the Conventions are what turn out to conflict with an enforced
guard.

**The conflict, measured.** The impl-plan's Conventions say a 5d spec omits `file`/`find`/`replace`
until 5e source exists — "intentionally not yet harness-runnable". But
`h-mad/tests/test_h_mad_mutation_harness.py` sweeps `tests/mutation-specs/*.json` by **filesystem
glob** (`:1900`, `rglob`; also `:81`, `specs_dir.glob`), and `git-hooks/pre-push` sweeps every
tracked `*.json`, and both score an unanchored row as `ANCHORS_UNREADABLE`. Observed with the RED
in the working tree, before any commit:

    FAILED test_h_mad_mutation_harness.py::test_committed_mutation_specs_are_not_drifted
    FAILED test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok
    2 failed, 96 passed

So the Conventions' rule is unreachable as written: there is no state in which an unanchored spec
sits under `tests/mutation-specs/` and the repo's own guards are satisfied.

Second, narrower defect in the same delivery: 6 of `docsections.json`'s 8 rows had their anchors
re-pointed at post-5e source (`_dbe.fence_aware_end(...)`, `assert found`) and 2 stripped entirely
— but `h-mad/tests/docsections.py` is UNCHANGED at RED, so none of those anchors resolves on the
current tree. A guard that worked before this dispatch would have been disabled for the whole
5d-to-5e window.

**Positive control, run before deciding.** With both spec files moved aside and `docsections.json`
reverted, the sweep is `11 passed` and the WIRE-PIN still fails on its call-record assertion. So
the specs are the sole cause of the two failures, and parking them costs the RED nothing.

**Decision (operator, 2026-09-06): park both until 5e.**

- `docs/03-analysis/doc-block-exec.pending-mutation-specs/doc_block_exec.json.pending` — the 25 rows.
- `docs/03-analysis/doc-block-exec.pending-mutation-specs/docsections.json.pending` — the 8-row
  rewrite, including the 4 new rows and the 6 re-pointed anchors.
- `h-mad/tests/mutation-specs/docsections.json` reverted to its committed 4 anchored rows, which
  still resolve against the untouched `docsections.py`, so that guard stays ARMED through the window.

**The `.json.pending` suffix is load-bearing, not cosmetic.** The pre-push hook sweeps every tracked
`*.json` **anywhere in the repository**, not only under `tests/mutation-specs/`, so a parked spec
that still ended in `.json` would block the very push it was parked to unblock.

**At 5e**: move both files back under `h-mad/tests/mutation-specs/`, drop the `.pending` suffix, and
anchor every row against the source that now exists — which is the one moment an anchor can be
verified rather than guessed. The harness refuses any anchor not matching exactly once, so the
anchoring is checked at the moment it is written.

**Verified after parking**, NUL-safe over every tracked `*.json` (a whitespace-split first attempt
inflated the count with phantom paths and had to be redone):

    ANCHORS: ANCHORS_OK specs=46 mutations=490 ok=490 drifted=0 unreadable=0 unclassifiable=0

**Residual, stated exactly.** Nothing detects a parked spec that is never moved back. If 5e lands
without restoring these two files, the feature ships with no mutation coverage for the new module
and the sweep stays green, because a spec that is not under the glob is not a spec. The 5e task is
the only thing that closes this, and the impl-plan's Conventions bullet should be corrected to say
"write the spec at 5e" rather than "write it unanchored at 5d" — that is an `implplan-author`
revision, not an orchestrator edit, and it is owed.

---

## D3 — SETTLED (operator, 2026-09-06): remedy 3, carry the red to 5g

**Decided by the operator on 2026-09-06, which is what §D3 required — the three remedies below
were presented verbatim and remedy 3 was chosen.** Accept the red through 5e and settle it at 5g,
when the implementation is final and one provenance bump covers every drifted pin at once.

Re-derived at `aa89d62` by running the node itself rather than carrying a figure:

    /opt/anaconda3/bin/python3.11 -m pytest \
      "h-mad/tests/test_h_mad_precheck_doc.py::test_noise_floor_on_documents_that_survived_eighty_cycles[docs/01-plan/features/doc-block-exec.impl-plan.md-impl-plan]" \
      -q -p no:cacheprovider --tb=long
    assert 19 <= 12          # issues=19, floor 12

**The obligation this remedy carries is not discharged by the decision.** §D3's own sentence stands:
5e must not be called green on a suite carrying this failure without saying so explicitly. Every
green claim from here to 5g names this red. A grep-derived tally is NOT the figure — `grep -c
PINDRIFT` returns 10 and `grep -c PLACEHOLDER` returns 12 on the same capture, summing to 22, which
is neither the count nor close to it; those are grep OUTPUT LINES inflated by pytest's summary and
its `+ where 19 = len([...])` expansion. The only defensible figure is the one the assertion
derives itself.

**The original finding follows unchanged.**

**Not a decision. A finding, recorded open, owed to 5e/5g.**

`test_noise_floor_on_documents_that_survived_eighty_cycles[...impl-plan]` went red on the RED
commit `954958a`. Re-derived rather than inferred:

    python3 h-mad/scripts/h_mad_precheck_doc.py \
      docs/01-plan/features/doc-block-exec.impl-plan.md --phase impl-plan --root .
    PRECHECK: FAIL issues=13
    PINDRIFT: L369  h-mad/tests/test_docsections.py:77      — changed since provenance 0021c77
    PINDRIFT: L3822 h-mad/tests/test_h_mad_audit_cycle.py:18 — changed since provenance 0021c77
    PLACEHOLDER: x11  (Tasks 2-4 template slots, all pre-existing)

The floor is 12. At `ce9ffe1` the count was exactly 12 — 11 PLACEHOLDER plus the one
`test_h_mad_audit_cycle.py` PINDRIFT that the `#49x` batch introduced — and the test passed, which
is why the 2026-09-06 baseline run was `2617 passed, 0 failed`. The RED commit added a test to
`h-mad/tests/test_docsections.py`, a file the impl-plan pins at L369, and that thirteenth issue
crossed the floor.

**The general shape, which is why this is not just a number to bump.** PINDRIFT means "a pin into a
file that changed since the document's own provenance commit". Phase 5 exists to change exactly
those files. So every 5d/5e commit that touches a file the impl-plan pins drifts another pin, and
the count only rises from here: Task 1 GREEN writes `h-mad/scripts/h_mad_doc_block_exec.py` and
edits `h-mad/tests/docsections.py`, both pinned; Tasks 2-5 add more. The guard cannot distinguish
"stale because nobody maintained it" — the decay it was written to catch — from "stale because the
implementation phase is underway", which is the feature working.

**Three remedies, none of them the orchestrator's to pick alone:**

1. **Bump the impl-plan's provenance sha** as each Phase-5 commit lands. Keeps the guard armed and
   honest, but it is a `implplan-author` revision per dispatch, on a document whose audit loop is
   capped and closed — and it re-stamps a gated document repeatedly, which is the measurement-layer
   churn the class rule was written to stop.
2. **Exempt the feature's own impl-plan while `phase == "step5"`.** Correct in principle — the
   document is by definition mid-implementation — but it is an h-mad tooling change made mid-feature,
   and it disarms the guard for the one document most likely to drift.
3. **Accept the red through 5e and settle it at 5g**, when the implementation is final and one
   provenance bump covers every drifted pin at once. Cheapest, and it leaves the suite reporting a
   failure unrelated to the wire for the whole window — the noise that hides a real one.

**Until it is settled, 5e must not be called green on a suite carrying this failure without saying
so explicitly.** A green claim that silently excludes a known red is the failure mode the whole
verification discipline exists to prevent.

**RED-state suite, for the record** (`954958a`, `--continue-on-collection-errors` required — see
below): `2 failed, 2616 passed, 1 error`. The error and the WIRE-PIN failure are the intended RED;
the second failure is this finding.

## D4 — the suite needs `--continue-on-collection-errors` during 5d

Task 1's prescribed RED is a module-level `import h_mad_doc_block_exec` in a test file, so pytest
raises a **collection** error and then refuses to run anything:

    pytest h-mad/tests -q -p no:cacheprovider
    !!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!
    1 error in 0.49s

Zero tests run — not "two red tests". For the whole 5d-to-5e window the suite gives no signal at
all unless `--continue-on-collection-errors` is passed, which is what produced the numbers in D3.
This is a property of the impl-plan's own prescribed RED shape and resolves itself the moment Task 1
GREEN creates the module. It is recorded because the next person to run the suite in this window
will otherwise read `1 error` as the suite being broken.

---

## D5 — the RED's hostile fixture name is not a legal filename (Task 1)

**Raised by**: the Task 1 GREEN dispatch, `STATUS: BLOCKED`, 22 of 46 tests raising
`FileNotFoundError` before reaching production code.

**Premise: CONFIRMED.** `h-mad/tests/test_h_mad_doc_block_exec.py:44` defines

    def write_doc(tmp_path, text, name="fixture [*] ⟦/h-mad⟧.md"):

and `tmp_path / name` yields

    .../test_duplicate_headings_refuse0/fixture [*] ⟦/h-mad⟧.md
                                                    ^ a path separator

so the write targets a file `h-mad⟧.md` inside a directory `fixture [*] ⟦` that does not exist.

**Prescription: REJECTED.** The dispatch proposed "parent-directory creation while preserving its
hostile name". It does not preserve it. On POSIX a filename cannot contain `/` under any
circumstances — the byte is the separator — so `mkdir(parents=True)` would split the hostile string
across a directory boundary and leave the *file* named `h-mad⟧.md`, which is not hostile at all.
The fixture would then exercise a hostile DIRECTORY name plus a mundane filename while reading, at
the call site, exactly as it does today. That is a worse outcome than the crash, because the crash
is loud.

**Decision (2026-09-06): drop the separator, keep every hostile property that a filename can
actually carry.** Replace U+002F SOLIDUS with **U+2215 DIVISION SLASH `∕`**, which is a legal
filename byte sequence, renders near-identically, and adds a confusable-character axis the ASCII
form did not have:

    name="fixture [*] ⟦∕h-mad⟧.md"

The spaces, `*`, `[`, `]` and the `⟦ ⟧` brackets are unchanged, so every hostile property that
survives contact with a filesystem survives this edit.

**Residual, stated exactly.** A literal `/` inside a single path COMPONENT is not representable on
POSIX, so that axis cannot be tested at the filename level by any fixture, here or elsewhere. If
the feature needs to prove something about a `/` inside a heading, an info string, or a document
BODY, that is a different test with a different input, and this fixture never covered it. Nothing
is lost by the substitution because nothing was ever exercised.

**What this says about the RED gate, and it is the part worth keeping.** The defect was
undetectable at 5d. Task 1's prescribed RED is a module-level `import h_mad_doc_block_exec`, so
every test failed at COLLECTION with `ModuleNotFoundError` and not one test body ran. A RED whose
failure mode is a collection error therefore certifies nothing about the tests it collects — it
proves only that the module is absent, which was already known. Every defect in the test bodies is
invisible until GREEN makes the import succeed, and 22 of them surfaced in the first second of the
first GREEN run. This is a general property of the new-module RED shape, not a fact about this
fixture, and it belongs in the impl-plan's Conventions as a stated limit of that RED — an
`implplan-author` revision, owed, not an orchestrator edit.

---

## D6 — `preamble-composed-with-unsubstituted-text` has no seam at `run_block` (Task 3, OPEN-DECISION `:2871`)

**Raised by**: `docs/01-plan/features/doc-block-exec.impl-plan.audit.v50.codex.md` must 1, carried
to the impl-plan as the first of Task 3's two `OPEN-DECISION (r19, 5d)` lines.

**Premise, re-derived rather than taken.** The signature is
`run_block(block: Block, *, preamble: str | None = None, timeout: float = 30.0) -> RunResult`
(`docs/02-design/features/doc-block-exec.design.md:2404`,
`docs/01-plan/features/doc-block-exec.impl-plan.md:2828`) — **one** `Block`, and the caller has
already substituted it (`dbe.substitute(block, {...})[0]`, the form every Task 3 AC uses). Inside
`run_block` there is therefore no `text` against which `text′` could be preferred: `block.text`
**is** `text′`. The design's mutation table row —

    | `preamble-composed-with-unsubstituted-text` | composition uses `block.text`, not `text′` | `test_preamble_and_substitution_compose` (AC-3.11) |

at `design.md:4335` — describes a distinction that does not exist at the seam it is assigned to.
The mutation as specified is a no-op, so `ALL_CAUGHT` over it would be vacuous. **Codex is right.**

**The property is nonetheless real and is UNGUARDED today.** Task 4's `Mutation rows added here`
list (impl-plan `:3379` onward) holds `subst-split-on-every-equals`, `subst-duplicate-key-last-wins`,
`cli-empty-key-delegated`, `index-nonint-unmapped`, `timeout-nonnumeric-unmapped`,
`preamble-decode-error-unwrapped`, `stream-reserved-with-truncation`,
`final-write-close-not-in-finally`, `verify-deferred-past-second-write`, `final-write-not-verified`,
`nonregular-stream-accepted`, `stream-open-blocking`, `stream-alias-check-removed`,
`exit-partition-flipped`, `rc-leaked-into-refusal`, `field-escape-removed` and the rest — **none of
which asks whether the value `substitute` RETURNED is the one handed on.** Withdrawing the row
would therefore lose coverage rather than remove a duplicate, which is why this is a move and not a
withdrawal.

**Decision (orchestrator, session `22e0a5f1`, 2026-09-06): MOVE it to Task 4, and RENAME it.**

    Task 4 gains: `substitution-result-not-passed-to-run_block`
      mechanism — `main` passes the ORIGINAL block to `run_block` instead of the block
                  `substitute` returned, so a `--subst` key reaches the child unexpanded
      killer    — a Task 4 CLI subprocess test on the SUCCESS path that asserts the executed
                  text carries a substituted VALUE (to be named by `implplan-author` from
                  Task 4's own AC list; it must observe the executed text, not the refusal
                  rendering, because the mutant only moves the success path)
    Task 3 loses: `preamble-composed-with-unsubstituted-text`

The name change is load-bearing: the old name says *preamble*, and the mechanism has nothing to do
with the preamble — any `--subst` success-path test kills it. Moving it under the old name would
carry the wrong mechanism to a new document.

**`test_preamble_and_substitution_compose` STAYS in Task 3**, unchanged, as an AC-3.11 behavioural
test. It stops being any mutation row's `test` key; it does not stop being a test. **Task 3's test
count is unchanged by D6.**

**Residual, stated exactly.** Two things this does not cover. (1) A **library** caller that invokes
`run_block` directly with an unsubstituted block is guarded by nothing, here or elsewhere — that is
the caller's own bug and lies outside this module's surface, and no mutation of this module's source
can express it. (2) The moved row guards the CLI's **pass-through** only; it says nothing about
whether `substitute` computes the right text, which is Task 2's rows' job and is already covered
there.

**Owed elsewhere.**
- `design-author`: the row at `design.md:4335` is now false in all three cells — name, mechanism and
  killer. It is a design change, not a prose repair.
- `implplan-author`: strike the row from Task 3's `Mutation rows added here`, add the renamed row to
  Task 4's with its killer named from Task 4's own AC list, and resolve the `OPEN-DECISION` line at
  `:2871`.

---

## D7 — a timeout the platform cannot represent (Task 3, OPEN-DECISION `:2873`)

**Raised by**: `docs/02-design/features/doc-block-exec.design.audit.v99.codex.md` must 1, carried
to the impl-plan as the second of Task 3's two `OPEN-DECISION (r19, 5d)` lines.

**Premise CONFIRMED — and the filed value understates the surface by five orders of magnitude.**
Measured on the pinned interpreter `/opt/anaconda3/bin/python3.11` (3.11.8, conda-forge, darwin),
run rather than reasoned, each arm carrying its control:

- `math.isfinite(1e300)` is `True` and `1e300 > 0` is `True`, so AC-5.6's guard as written
  (`math.isfinite(t) and t > 0`, design `:2043`) **accepts** it.
- `Popen(["/bin/sh","-c","echo hi"], …).communicate(timeout=1e300)` raises
  `OverflowError: timestamp too large to convert to C _PyTime_t`. It is **not** an `OSError` and
  **not** a `ValueError` — it **is** an `ArithmeticError`. The design's error mapping names none of
  those, so the traceback escapes the helper.
- **The boundary is nowhere near `1e300`.** `1e8` already refuses, with a *different* message,
  `OverflowError: timeout is too large`. The filed premise's `1e300` is true and is not the edge.
- **The exact pair**: `2147483.647` is **accepted**; `2147483.648` is **refused**
  (`timeout is too large`). A tight binary search over `[2147483.0, 2147485.0]` returns largest
  accepted `2147483.6470458433`, smallest refused `2147483.647045844`.
- `(2**31 - 1) / 1000 == 2147483.647` returns **`True`** on the same interpreter. The limit is
  `INT_MAX` **milliseconds** — about 24.855 days — which is what makes the constant derivable rather
  than chosen.
- **It is not deadline-dependent.** The boundary re-measured 3 s later differs by `-1.91e-05` s,
  i.e. search noise, not wall-clock drift. A fixed constant is therefore sound; had the limit been
  an absolute deadline the pair test would have been flaky by construction, so this control is what
  licenses the constant.
- A child that genuinely waits behaves identically: `sleep 0.2; echo y` under
  `communicate(timeout=2147483.0)` returns `('y\n', '')`.

**Decision (orchestrator, session `22e0a5f1`, 2026-09-06): (a) — `BadTimeout` gains a representable
upper bound. `OverflowError` is NOT mapped into the launch-failure path.**

**Why not (b).** The `OverflowError` fires inside `communicate`, which is **after** the spawn and
after `mkdtemp`. Mapping it downstream means launching a child and creating a directory for a bound
already known to be unhonourable — the exact leak AC-5.6's pre-spawn rule exists to prevent, in the
design's own words at `:2076`: *"That is why the refusal must precede the spawn"*. It would also
have to surface as `LaunchFailed(stage="collect")`, filing a caller-input error as a fault of the
launch.

**Why (a).** A bound the platform cannot represent is a bound that cannot be honoured — the same
category as `inf`, which AC-5.6 already refuses for that reason and no other (design `:2081`:
*"it is finite-checked because it is no bound at all"*). The upper bound joins the existing list; it
does not open a new one.

**The change, stated as a diff.**

    design.md:2043    was : `timeout` must satisfy `math.isfinite(t) and t > 0`, else `BadTimeout(value)`
                      now : `timeout` must satisfy `math.isfinite(t) and 0 < t <= _MAX_TIMEOUT_SECONDS`,
                            else `BadTimeout(value)`

    source constant   `_MAX_TIMEOUT_SECONDS = (2**31 - 1) / 1000`   # == 2147483.647
                      Written in THAT form, not as the literal, so the reason is visible: it is
                      CPython's INT_MAX-milliseconds selector limit, not a chosen round number.

    spec.md:577       was : `timeout` must be a finite number greater than zero: `0`, a negative
                            value, `nan`, `inf` and a non-numeric `--shell-timeout` argument all
                            refuse with `DOCBLOCK: BAD_TIMEOUT value="<v>"` …
                      now : the same sentence with the upper bound added to BOTH halves — "a finite
                            number greater than zero and no greater than `(2**31 - 1) / 1000`
                            seconds (the platform's representable bound)", and the refusal list
                            gaining "a value above that bound".

**Test added — ONE, carrying its own control.**

    test_unrepresentable_timeout_refuses_before_spawn  (AC-5.6)
      refusal arm : timeout=2147483.648 -> BadTimeout; the recording `Popen` pass-through was
                    never called and no directory was created (the same three assertions
                    `test_nonpositive_timeout_refuses_before_spawn` already makes)
      control arm : timeout=2147483.647 on a fast block (`echo hi`) RUNS normally
                    -- this is what stops the guard degenerating into "refuse everything large",
                    and it is the arm that fails loudly if a future interpreter moves the limit

**Mutation row added to Task 3.**

    `timeout-upper-bound-removed` — the `<= _MAX_TIMEOUT_SECONDS` clause is dropped, leaving
    `math.isfinite(t) and t > 0` — killed by `test_unrepresentable_timeout_refuses_before_spawn`.

It is **mutually discriminating** with the existing `timeout-validation-removed`
(`design.md:4369`, killed by `test_nonpositive_timeout_refuses_before_spawn`): that row drops the
WHOLE predicate, this one drops only the upper clause, and under this mutant the nonpositive test
stays green — so neither row's killer can stand in for the other's.

**Count consequence — and it must be re-derived, not carried.** Task 3's AC list holds **38**
distinct tests at `8ae4924` (re-derived over the full AC span `2846,2869`, which includes AC-5.5's
continuation lines `2865-2868`; the whole-section span `2688,2970` returns 40, the two extras being
the module filename `test_h_mad_doc_block_exec` and `test_rollback_skips_unlink_on_identity_mismatch`,
which is named outside the AC list). D7 makes it **39**, so
`--expect-fail = 39 - 2 = 37` and `--expect-pass = 57 + 2 = 59` (57 being the module suite's
`passed` at `8ae4924`, re-run, not carried). **Both figures are to be re-derived from the REVISED
impl-plan before `h_mad_assemble_tdd.py` is invoked** — the +1 exists only once the revision lands,
and the assembler's counts must match the section codex is actually handed.

**Residual, stated exactly.** The constant pins CPython's `INT_MAX`-milliseconds limit **as measured
on 3.11.8 / darwin**. On an interpreter or platform whose limit is LOWER, a value between that limit
and this constant would still reach `communicate` and raise an unmapped `OverflowError`. That
residual is deliberately **not** closed by adding an `except OverflowError` backstop: on the pinned
interpreter that branch is unreachable, an unreachable branch cannot be tested or mutation-verified,
and shipping one would be the appearance of coverage rather than coverage. It is closed the way the
design already closes its sibling reading at `:2081` — by re-running the pair probe on any
interpreter this feature is later supported on.

**Owed elsewhere.**
- `spec-author`: AC-5.6's wording, per the diff above.
- `design-author`: the guard sentence at `:2043`, the `_MAX_TIMEOUT_SECONDS` constant, and the new
  `timeout-upper-bound-removed` row in the mutation matrix (with the matrix total re-derived from
  the table, never incremented).
- `implplan-author`: Task 3's `Code structure` (`:2825`, `:2695`) and `:3010`, the AC-5.6 bullet at
  `:2869`, the new mutation row, and the resolution of the `OPEN-DECISION` line at `:2873`.

---

## Orchestrator note on D6/D7 — two measurement corrections worth carrying

1. **A filed premise's VALUE is not its BOUNDARY.** The D7 finding named `1e300`; the real edge is
   `2147483.647`, five orders of magnitude lower and reachable by an ordinary "very large timeout".
   The conclusion was right and the surface it described was ~10^294 times too small. Re-derive the
   edge, not just the example.
2. **A per-bullet `awk` over a markdown checklist scans one line per bullet.** The first count here
   used `awk '/^- \[ \] AC-/'`, which never read AC-5.5's continuation lines `2865-2868`. Re-run
   over the full span `sed -n '2846,2869p'` the figure is the same **38** — but the first command
   could not have shown that, which is the point: it was a vacuous agreement, not a confirmation.

---

## D8 — OPEN: Task 3 GREEN reaches 94 of 96; the two escapee tests fail in TEARDOWN

**Not a decision. A finding, recorded open, owed to the next 5e dispatch.**

Task 3 GREEN (`STATUS: BLOCKED`, codex, 5e) implemented the production module and returned
**94 passed, 2 failed**. The orchestrator re-ran it and reproduced exactly that. codex REFUSED to
go further, on the ground that the failures are in test teardown and repairing tests is outside a
GREEN dispatch's authority. **That refusal is correct** and is the fourth time on this feature a
codex refusal has been right.

**What is established, each by a command that was run:**

- `2 failed, 94 passed`, re-derived by the orchestrator, matching the dispatch's claim.
- The two are `test_wait_after_kill_is_bounded` and `test_drain_wait_oserror_is_launch_failed_collect`
  — **both of the escapee-fixture tests, and only those**.
- **Deterministic, not a race**: 3 consecutive runs, `2 failed` every time.
- **Control passes**: the two non-escapee siblings of the same helper,
  `test_poll_oserror_is_launch_failed_collect` and `test_communicate_oserror_is_launch_failed_collect`,
  return `2 passed`. So the defect is not in `collect_case` as such.
- **The failing line is in the `finally:`, not the assertions.** Isolated with `--tb=long`: it is
  `test_h_mad_doc_block_exec.py:1070`, `kill_if_present(real_killpg, proc.pid)` — the **leader's
  process group**. Every production assertion sits in the `try:` above it and completed.
- `kill_if_present` catches `ProcessLookupError` only. `PermissionError` (EPERM) escapes it.
- Only `h-mad/scripts/h_mad_doc_block_exec.py` changed. No test was weakened; the dispatch reports
  `git diff --check` clean and the orchestrator confirms the test file is untouched since the RED
  commit `0bfcaa7`.

**The obvious hypothesis is FALSIFIED, and that is the useful half.** The first reading was pid /
pgid recycling: the leader is reaped, its pid is freed, a new group takes the number, and `killpg`
answers EPERM because the group is no longer ours — the same shape as the `is_pid_alive` EPERM
finding (EPERM means the target EXISTS and is not yours, never that it is gone). A standalone probe
was written to drive that path:

    /bin/sh -c "python3 esc.py PIDFILE & sleep 300"   under start_new_session
    -> leader 76382 pgid 76382; escapee 76383 pgid 76383 (setsid gives it its own group)
    -> killpg #1 ok; leader reaped, returncode -9
    -> killpg #2 SIGKILL: ProcessLookupError ESRCH (3)
    -> killpg #2 sig 0  : ProcessLookupError ESRCH (3)
    -> escapee still alive, pgid 76383

**ESRCH, which `kill_if_present` already catches — so the escapee/`setsid` arrangement alone does
NOT produce EPERM.** The probe differs from the real fixture in one respect: it has no
monkeypatched `Popen` and no injected `wait`/`communicate` failure. Both failing tests do, and both
non-failing siblings differ from them precisely in the escapee. So the EPERM depends on the
interaction of the fault-injection wrapper with the escapee fixture, and not on either alone.
That is where the next dispatch should look, and it is as far as this session took it.

**Not yet done, and none of it optional before 5e can be called green:** the wire/whole-module
revert test, the mutation harness over Task 3's rows including the new `timeout-upper-bound-removed`,
and the anti-gaming verification pass. None of them can run against a suite that is not green.

**Do NOT repair this by widening `kill_if_present` to swallow `PermissionError`.** That converts a
signal aimed at a process group the test no longer owns into a silent no-op, which is strictly worse
than the failure: `killpg` on a recycled group id would then fire SIGKILL at an unrelated process
group and report success. The repair has to establish WHY the group id is unsignalable at that
moment and stop signalling it, not catch the symptom. This is the same shape as D5 — the
convenient repair hides the mechanism.

**Carried prediction from D5, and it held.** The RED failed exclusively on the missing `run_block`
symbol, so no assertion after that point had ever executed. Task 1 surfaced 22 body defects of 46
at its first GREEN; Task 3 surfaced **2 of 37**, and both are fixture defects rather than assertion
defects. The prediction was right about the class and generous about the count.

---

## D9 — CLOSED: stderr closure and post-collect kill now have discriminating tests

**Closed by executed isolated mutation proofs and the 28-row harness run.**
See [D9 proof](doc-block-exec.d9-proof.md) for the original/mutant outputs,
including the repaired poll test failing alone under mutant B. The test file now
reports `98 passed`; anchors report `mutations=28 ok=28`; the harness reports
`ALL_CAUGHT mutations=28 caught=28 survived=0 refused=0 unreadable=0`.
Production code is unchanged. The original finding and its evidence follow.

**Originally recorded open, blocking 5e:**

The independent verification pass (`references/codex-verifier-prompt.md`, read-only) returned
BLOCKED. It re-derived all five claims it was given and confirmed every one — `96 passed`
(cross-checked as 96 AST definitions and 96 unique collected nodes), 39 added tests, the 26-row
reconciliation, the constant and guard by source, imported value AND bytecode disassembly, and the
full suite at `1 failed, 2715 passed` with D3 as the sole failure. It changed nothing: `git status`
byte-identical before and after, both hashing to `dee785ee…`.

**Then it found two plausible regressions that survive EVERYTHING — the 96-test suite AND the
26-row `ALL_CAUGHT` mutation spec. Both reproduced by the orchestrator:**

1. **The stderr pipe is never closed.**
   `for pipe in (proc.stdout, proc.stderr):` → `for pipe in (proc.stdout,):` → **96 passed**.
   The verifier reports `test_timeout_drain_is_bounded_against_an_escapee` passing with the
   recorded stderr pipe demonstrably still open.

2. **The kill is skipped entirely after a collect failure.**
   Guarding `os.killpg(...)` and `signalled = True` with `if not isinstance(pending, LaunchFailed):`
   → **96 passed**. And the test named for exactly this seam,
   `test_poll_oserror_is_launch_failed_collect`, **passes ALONE under the mutant** (`1 passed`).

**Number 2 is the more serious, and it is a VACUOUS ASSERTION rather than a missing one.** That
test's own `finally` kills the process group, and only then does the assertion check that the group
is gone. The assertion therefore passes whether or not production killed anything — the teardown
manufactures the postcondition the test claims to verify. It is the `#49`/CONTROLS-4 shape at the
fixture level: a zero with no positive control.

**Why 26 mutation rows did not catch either.** A mutation spec can only cover mechanisms someone
wrote a row for. `ALL_CAUGHT` says every row that EXISTS is killed; it is silent about guards with
no row, and neither of these has one. This is the standing rule — *a guard without a row is what
the base Mutation verification invariant refuses* — firing from the direction that is hard to see:
not a row whose killer is wrong, but a property with no row at all. **`ALL_CAUGHT` plus a green
suite is not sufficient, and this pass is the only thing positioned to show it.**

**Original owed list (the D9 guards and assertion repair are now verified above):**
- a discriminating test for stderr closure, and a mutation row `stderr-not-closed` bound to it;
- a discriminating test for the post-collect kill, and a row `kill-skipped-after-collect-failure`;
- **repair `test_poll_oserror_is_launch_failed_collect`'s vacuity** — it must assert the group is
  gone BEFORE its teardown kills anything, or the assertion measures the teardown;
- then re-run the harness, whose count moves 26 → 28, with the totals in all four documents
  re-derived rather than incremented.

**Contract note.** codex ended with `STATUS: BLOCKED — stderr-closure regression survives…`,
appending prose to the token. `h_mad_extract_verdict.py` REFUSED it (exit 2, off-contract) and that
is correct fail-closed behaviour: the token is a fixed vocabulary precisely so it cannot be parsed
loosely. The concern was named beside the token as asked; only its placement broke the contract.

---

## D10 — OPEN: the documents publish ONE 88-row spec; the implementation writes per-task specs

**Not a decision yet. The shared fact set for the 5e document round, derived by the orchestrator at
`aa89d62` and handed identically to all four authors.** Every author re-runs these before using
them — a fact one author derives alone is the defect this section exists to prevent (two authors
independently "corrected" the same figure to 18 and to 20 in one cycle, each document internally
consistent, so no audit leg could see it).

**FACT 1 — what the documents publish.** `impl-plan:19`:

    (`doc_block_exec.json` 88 rows, `doc_block_exec_wire.json` 8, `docsections.json` 8) must report `ALL_CAUGHT`.

**FACT 2 — what is on disk.**

    doc_block_exec.json           32 rows
    doc_block_exec_task3.json     28 rows
    doc_block_exec_wire.json      ABSENT
    docsections.json               8 rows

    for f in h-mad/tests/mutation-specs/*.json; do \
      python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['mutations']), sys.argv[1])" "$f"; done

`doc_block_exec_wire.json` is ABSENT because Task 5 has not run; that is expected and is NOT part
of this finding. Naming it here so nobody re-files it as one.

**FACT 3 — no document names the per-task file.** `doc_block_exec_task3` appears **0** times across
all four documents:

    grep -c 'doc_block_exec_task3' \
      docs/01-plan/features/doc-block-exec.{impl-plan,spec,plan}.md \
      docs/02-design/features/doc-block-exec.design.md      # expect 0 0 0 0

No document names a per-task spec convention at all.

**FACT 4 — D2 says the spec is written at 5e**, and Task 3's was, as
`h-mad/tests/mutation-specs/doc_block_exec_task3.json`.

**THE QUESTION, which is not "26 → 28".** D9 added two rows and the harness now reports
`ALL_CAUGHT mutations=28`, re-derived at `2b64747`. But 28 is the row count of a FILE THE DOCUMENTS
DO NOT NAME. So the owed revision is not a `+2` anywhere; it is whichever of these is true:

1. The per-task split is the intended shape, `impl-plan:19`'s three-spec enumeration is stale as
   written, and the documents must publish the per-task convention plus a total derived across the
   files that exist.
2. `doc_block_exec.json` is meant to hold all 88 and the per-task files are a staging step, in which
   case the documents are right and the IMPLEMENTATION owes a merge — a Phase-5 task, not a
   document revision.

**Do not assume (1) because the disk looks that way, and do not assume (2) because the document
says so.** Read the matrix and say which, with the command that settles it. A `88 → 90` bump applied
without answering this would publish a total for a population that does not exist.

**Anti-pattern this section is guarding.** 107 raw `\b88\b` hits across the four documents
(impl-plan 20, spec 3, plan 73, design 11), and most are line numbers. A value sweep alone cannot
drive this revision; classify every hit before moving any of them.

### D10 — SETTLED at the batch, by the orchestrator's own walk

**Answer: neither reading (1) nor (2) as §D10 posed them, because the question conflated three
things.** The number's AUTHORITY is the design's mutation table; its VALUE is **90**; the file that
REALIZES it is `doc_block_exec.json`, into which the staged per-task file merges. All four authors'
answers are compatible under that split, and the apparent three-way disagreement was three authors
each naming a different one of the three.

**Orchestrator's walk, run at the batch rather than taken from any author.** Scoped to the matrix
table alone (`| mutation | guard it removes (mechanism) | killed by (`test` key) |`), row names
compared AS SETS against each spec's `name` keys:

    MATRIX rows=90 distinct=90
    on-disk 32 + 28 = 60   intersection=0
    NOT-IN-MATRIX = []                       <- closes plan-author's routing
    matrix-not-on-disk = 30                  <- Task 4, unwritten
    ARITHMETIC: 32 + 28 + 30 = 90
    control (drop an on-disk row) -> ['adjacent-heading-skipped']

That reproduces impl-plan's `25 + 7 + 28 + 30 = 90` from a different direction — the design's table
versus the landed specs — and the empty `NOT-IN-MATRIX` is what plan-author asked be re-run here.

**TWO ORCHESTRATOR ERRORS IN THAT WALK, both caught only because a control was demanded.**

1. **The control was vacuous on its first run.** It dropped `registry-row-removed` — a Task 4/5 row
   that is not on disk — so removing it could not change `on-disk MINUS matrix`, and the walk
   reported "still empty" whether or not it worked. A control over a set difference must remove a
   member of the LEFT set. Fixed by dropping an on-disk row, which then surfaced correctly.
2. **The extractor's grammar was wrong and produced 97.** It scoped to every table with a
   backticked first cell (catching a second, 8-row `test_h_mad_collect_report_docs.py` matrix that
   is not part of this population) AND its name pattern `[a-z0-9-]*` excluded UNDERSCORES, silently
   dropping `substitution-result-not-passed-to-run_block` — so the same run was too wide by one
   table and too narrow by one row. 97 was published nowhere.

Neither error changed the answer, and that is exactly why they are recorded: both produced
plausible integers, and only the control separated them from the right one.

**§D10's own FACT 3 is now FALSE, by this round's action.** `doc_block_exec_task3` appeared 0 times
in all four documents at `6a1693c`; it is named in all four now. The sheet measured a state its own
round then changed — the instrument-includes-the-instrument class, recorded rather than quietly
restated.

**§D10 FACT-count UNIT correction, caught by design-author.** The "107 raw `\b88\b` hits
(impl-plan 20, spec 3, plan 73, design 11)" above are OCCURRENCES and the sheet did not say so.
Lines differ: 20/17, 3/3, 73/35, 11/9. Both are defensible; publishing either without its unit is
not.

**What is NOT settled and does not become settled by this batch:** whether the per-task file merges
into `doc_block_exec.json` before 5f. impl-plan records it as a checkable 5e obligation; design
lists it as an open residual; plan declines to ratify either intent. No document, decision sheet or
commit message states the intent behind the per-task naming — plan-author looked and found nothing,
and declined to infer it. That is an operator call, not a reading.

### D10 — the merge question SETTLED by the operator, 2026-09-06: MERGE

**Decision: `doc_block_exec_task3.json` MERGES into `doc_block_exec.json`.** The per-task file was
staging, not a convention. This is the one thing no artifact stated — impl-plan v1.58 recorded a
checkable obligation, design v1.114 an open residual, plan v1.108 declined to ratify either intent,
and `grep` found the intent nowhere — so it could only ever be decided, never read. It is now
decided and this is the record.

**The merge is NOT a file move.** It has four parts, and part 4 exists because the 5e round itself
created it:

1. **Rows.** Fold Task 3's 28 rows into `doc_block_exec.json` (32 → 60). The two files are
   name-disjoint (`intersection = 0`, re-derived at `bdc606e`), so the union is 60 distinct names
   and no row is lost or duplicated. Verify with the same set walk the round used, which must still
   return `NOT-IN-MATRIX = []` against the design's 90-row matrix.
2. **`target_command`.** `doc_block_exec_task3.json` carries an ABSOLUTE
   `/opt/anaconda3/bin/python3.11`. `doc_block_exec.json`'s must be reconciled with it rather than
   silently inheriting either — a spec that hardcodes one machine's interpreter is not portable, and
   this is the moment the difference is visible.
3. **Closure predicate**, from impl-plan v1.58:
   `ls h-mad/tests/mutation-specs/ | grep -cE '_task[0-9]+\.json$'` must print `0`.
4. **The four documents name the file that is about to stop existing.** The 5e round put
   `doc_block_exec_task3` into all four (spec 1, plan 5, impl-plan 6, design 4 matching lines at
   `bdc606e`, where it had been 0/0/0/0 at `6a1693c`). Every one of those references goes stale on
   the merge. This is a document reconciliation, and it is the larger half of the work — do NOT
   merge the files and leave it, or four gated documents point at a deleted path.

**Sequencing (operator, same decision): merge FIRST, then Task 4.** Task 4 adds 30 rows; landing
them into a file whose shape is still unsettled would repeat the D10 problem one task later.

**Do not treat the row counts as carried.** 32 / 28 / 60 / 90 / 30 were derived at `bdc606e`; the
merge changes the first three by construction. Re-derive at the merge commit, and re-run
`--check-anchors` plus a full harness pass on the merged file — a merged spec whose anchors resolve
but whose rows no longer kill is the failure this feature has already met twice.
