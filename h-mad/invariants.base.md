# H-MAD Base Invariants — Axis B (workflow-universal)

> Shipped with the `/h-mad` skill. The orchestrator inlines this file verbatim into the
> `INLINE_BASE_INVARIANTS` slot (name written bare — a bracketed mention inside an inlined
> file survives substitution and reaches the reviewer as an unfilled-looking placeholder)
> of every plan / design / impl-plan audit, **before** the
> per-project `<PROJECT_ROOT>/.h-mad/invariants.md` domain layer. These rules apply to every
> project that uses `/h-mad` and are **non-overridable by any project file**: a project's
> invariants file may add domain rules but may not downgrade or delete a base rule. The
> operator `## Acknowledged-not-fixed` sidecar escape hatch still applies to base findings
> (a base item listed under that section in a sidecar `.audit.v<N+1>.md` is a conscious,
> audited deferral — it is excluded from the gate count exactly like any other layer's item).
>
> Axis A (generic adversarial review) is covered by the audit-prompt template — not repeated here.

## Audit-gate signal discipline
- Any gate/check whose verdict the orchestrator consumes MUST communicate PASS/FAIL via an
  explicit **stdout token** and **exit 0** on a normal verdict (PASS or FAIL). Using a non-zero
  process exit to mean "FAIL" is a violation — a non-zero exit registers as a Claude Code tool
  failure (`PostToolUseFailure`) and leaks into coexisting plugins' error handling. A non-zero
  exit is permitted ONLY for genuine operational errors (missing/unreadable input).

## Single-source contract
- A rule applied by more than one surface (e.g. an audit blocking-item count read by both the
  orchestrator gate step and a precondition checker) MUST have exactly one authoritative
  implementation that all surfaces call, OR a test asserting byte-equivalence across surfaces.
  Independent re-implementations that can silently diverge are a violation.
- A contract stated in a template (e.g. an empty-section sentinel) MUST match what the consuming
  gate logic treats as that case. Template guidance and gate behavior disagreeing is a violation.

## Standalone / no plugin dependency
- The skill MUST NOT acquire a **runtime dependency** on any other plugin (OMC, bkit,
  context-mode, etc.) or external skill (spec-kit, b-mad, pdca). Coexistence accommodations
  (sharing a state filename, conforming doc structure to an external validator's required
  sections) are allowed; *requiring another plugin installed at runtime* is a violation.

## No new external dependency
- Scripts MUST use only Python stdlib plus tooling already depended upon by the skill (the
  agent dispatch substrate (cmux or orca, via `hmad-dispatch`); `jq` where the existing hook
  already uses it; `pytest`).
  Introducing a new third-party package or new CLI is a violation.

## Portable time bounds
- A time-bounded command MUST NOT be written as `timeout <s> <cmd>` or `gtimeout <s> <cmd>`.
  **Neither is a macOS system component**, so the form is unportable in both directions.
  A stock box ships neither and the call fails at 127; a box carrying `brew install coreutils`
  runs it fine and the bound silently rests on a CLI h-mad cannot assume is there.
  **What your box has is not an input to this rule.** h-mad already owns a time-bounder that
  reachable wherever `hmad-dispatch` is, so the form is forbidden unconditionally — not because
  of what happens downstream. (Reachable, not universal: where the wrapper itself cannot be
  called the rule below still applies — halt, do not drop the bound.) Do not reason from a local probe to an exemption. For anything committed
  or dispatched the form is additionally a new external CLI dependency (§"No new external
  dependency"); a downstream 127 is how that eventually surfaces, never the reason.
  Do not settle the question by probing: a local `command -v timeout` that succeeds is not
  licence, it proves only that this box has coreutils, and it means the 127 that would have
  exposed the improvisation never fires. Use `hmad-dispatch run --timeout <s> -- <cmd...>`,
  which exits 124 at the deadline.
- Where a 127 does fire, its aftermath is worse than the 127 itself. Measured: the reflex after `timeout: command not found`
  is to re-run the same command **unbounded** and call it "checking directly". That does not fail
  at the deadline, it hangs the phase, and in every log h-mad reads a hang and slow work are the
  same bytes. A plan, a design, or a prompt that leaves an agent no reachable time-bounder is a
  violation; the correct behaviour when none exists is to **halt**, not to drop the bound.

## Doc-template superset compliance
- Generated phase documents whose type is validated by an external doc-structure validator
  (e.g. bkit PDCA: `plan` → `docs/01-plan/...`, `design` → `docs/02-design/...`,
  `report` → `docs/04-report/...`) MUST be supersets that satisfy that validator's required
  sections AND retain the existing h-mad sections. Dropping an h-mad section or failing the
  validator is a violation.
- The contract binds the **saved document**, not only the template it came from. Where such a
  validator reclassifies a document by a substring of its *content* — bkit's `isPlanPlus` promotes
  a plan to a larger required-section list on seeing `Plan-Plus`, `Plan Plus`, `plan-plus`,
  `Brainstorming-Enhanced`, or `Intent Discovery` anywhere in the file — a generated document
  carrying that substring is a violation even though the template is clean. Guard it mechanically
  (`scripts/h_mad_doc_shape_check.py`); the literals are unremarkable prose, so an author cannot
  be expected to avoid them from memory.

## Operator-override preservation
- The `## Acknowledged-not-fixed` sidecar override mechanism MUST remain functional for all
  layers (base + project). Any gate change that causes overridden items to still count as
  blocking, or that ignores the sidecar, is a violation.

## Backward compatibility
- A change to the audit gate MUST preserve the PASS verdict for audit docs that passed before
  the change. Flipping a historically-passing audit to FAIL (absent a real new blocking item)
  is a violation.

## Marker discipline
- Orchestrator phase transitions and halts MUST emit `[H-MAD]` log markers so a run is
  diagnosable from logs alone. Silent state transitions are a violation.

## Mutation verification
- A step that mutates state (a git operation, a file write, a remote/CLI call) MUST verify the
  mutation by **re-reading the resulting state**; an **exit code is not evidence that a mutation
  occurred**. A plan, design, or implementation that treats a zero exit — or an echoed success
  string such as `Sent N bytes` or `{"ok":true}` — as proof of the intended effect is a violation.
- The failure this blocks is silent and looks exactly like success: two `zsh` no-ops (backtick
  execution inside `-m`, a leading-dash path) both exited 0 while doing nothing, and a dispatch
  reported `Sent 7293 bytes` into a dead pane. Where a command reports on its own behaviour, the
  check must read the *thing it was supposed to change*, from a separate call.
- **When several mutations target the SAME line, vary one field and keep the anchor shared.** A
  guard whose failure has separable parts — exit code, stream routing, message content — needs one
  mutation per part, each replacing the same anchor. That shape is what proves a content assertion
  load-bearing: the mutants that keep exit and stream and strip only the text are exactly the ones a
  returncode-only test survives. Two discriminators worth writing into the spec: a
  first-vs-last-occurrence mutant survives whenever the sought item is last in BOTH regions, so the
  discriminating fixture must put the decoys between the markers and leave the tail empty; and
  `survived` has four distinct causes — missing guard, equivalent mutant, weak test, and a mutant
  that never ran — which the verdict token collapses into one word. Diagnose which before acting.

## Test discrimination
- A test or guard MUST be **observed failing against the unfixed code** before it is trusted.
  For a regression test, revert the fix and re-run; for a guard, stub it to its permissive value
  and re-run the suite. **Zero failures is a finding, not a reassurance** — it means the check is
  unenforced, not that the code is safe. Keeping a check that has never been seen to fail is a
  violation.
- A check that cannot fail is decoration, and it is worse than no check because it reports
  coverage that does not exist. Two guards shipped green this way and were caught only by
  stubbing: one passed solely because an unrelated helper stripped the env var its subject read,
  and a documentation test passed with the documented guidance deleted, because both of its
  component words already appeared in nearby prose. Neither was visible to review or to a green run.
- The mutation must itself be verified (§"Mutation verification"): a `.replace()` that matches
  nothing exits 0 and reports the guard as enforced.
- **Mutating a path-resolution function can disable the suite's own isolation.** Tests usually
  isolate by pointing an env override at a temp path, and that override is honoured by a branch —
  the same kind of branch a mutation deletes. Stubbing the override branch in `_pin_file` redirected
  every pin write in the suite onto the developer's live session file and replaced two real agent
  handles, while the run reported 642 passed. Before mutating anything that decides *where* state is
  written, snapshot the real target and restore it, or run in a sandboxed working directory.
- **A stub must model the step the real system CONSUMES.** The rules above are about asserting the
  right thing; this one is about the fixture telling the truth. A stub that replays state the real
  system consumes once makes a test pass before the fix exists: an orca stub replayed an acked
  delivery forever, so a sibling-cache test re-matched from the queue, pinned nothing, and passed
  against unmodified code. Cardinality is part of the model — a fake that writes a path once where
  production writes it twice let a verb never dispatch with 57 tests green. Before trusting a stub,
  ask which of its effects are destructive in production and make the stub destroy them too.

## Verifying a review finding
- **A review finding has three separable parts — facts, concern, prescription — and they fail
  INDEPENDENTLY.** Before applying a prescription, diff it against the RED tests and the spec's
  acceptance criteria. A finding that matches the design doc but breaks tests means the DESIGN
  drifted, not the implementation. Measured: one pass's prescription broke a guard (1 failed, 53
  passed) while its concern was entirely real, and another review's prescription was backwards.
- Test a prescription by applying it as a mutation and reverting it. When two passes dissent, ask
  what the codebase ALREADY does — twice the house pattern beat both readings.

## Guard narrowing
- When a change **deliberately makes a guard accept something it used to reject**, the relaxation
  MUST be shown to be *exactly* the intended case: run a corpus of inputs through the old and new
  logic and diff the verdicts, then account for **every** input whose verdict softened. A green
  suite is not evidence here — it encodes the cases someone already thought of, which is the wrong
  population when the question is "what else did this let through?". This is the inverse of
  §"Mutation verification": that proves a guard still bites, this proves a loosening did not widen.
- The relaxation MUST rest on a **guarantee of the thing being parsed**, not on a heuristic that
  re-implements it. Narrowing a scanner by "ignoring quoted regions" means re-deriving the target
  language's quoting rules in a regex, which is how a bypass gets introduced; narrowing it by a rule
  the language itself guarantees is safe. Verify that guarantee **against the real interpreter**,
  not its documentation (§"Assumption verification").
- Both halves were load-bearing when this was written. Narrowing a heredoc scanner so it stopped
  denying inert prose, a 23-input differential corpus flagged one case as a regression; running the
  shape through real `bash` showed the body genuinely never expands, so the *test expectation* was
  wrong and the code was right. Without the corpus that case ships as either an unnoticed hole or a
  "fix" applied to correct behaviour — and nothing else would have distinguished them. The same run
  confirmed the intended relaxations numbered exactly two, and that the remaining 21 verdicts were
  untouched.
- A narrowing is scoped by **which checks consult the reduced input**, not by the reduction itself.
  Exempting the quoted region from *one* class of check while every other class kept scanning the
  full input is what kept the change from widening; a blanket exemption would have disabled
  detections that were still correct for reasons unrelated to the false positive.

## Connection enforcement
- A task whose deliverable is a **connection** — a call site, an import, a registration, a route, a
  flag or value propagated across a boundary — MUST ship a test that **fails when the connection
  alone is removed and the callee is left intact**. A test that exercises the callee directly is not
  evidence that the callee is reached. Shipping a connection with no such test is a violation.
- **A whole-module revert cannot establish this**, because it removes both sides: the RED split
  returns identically for a wired and an unwired build. The same blindness runs through every other
  layer — a RED phase goes red because the callee is *absent*, an anti-gaming audit finds a
  callee-scoped unit test perfectly discriminating, and a review of the diff sees a call site that is
  *present* and therefore reads as correct. **Presence is not enforcement.** Measured across two
  consecutive wiring tasks: each shipped its single load-bearing decision untested through every
  audit cycle and through the RED phase, and only a mutation scoped to the connection caught it.
- Mutate the connection in **both directions**: remove it → the wire test must fail; force it to fire
  unconditionally → the fall-through/negative test must fail. One direction certifies a connection
  that exists but is unconditional. Verify the mutation landed before trusting the run
  (§"Mutation verification") — a revert that never happened reports as a pass.

## Incident replay
- A fix motivated by a specific observed incident MUST be **replayed against the real artifacts
  already on disk** that motivated it, not only against cases authored alongside the fix.
  **Synthetic cases alone are a violation** whenever such artifacts exist and are reachable.
- Cases written next to a fix inherit the author's model of the bug, so they agree with it by
  construction. A detector validated on 14 handcrafted samples rejected the real historical label
  it was written to accept; the same replay then measured the true rate (7 of 13), which reclassified
  the defect from a one-off into the majority case. Replay is how a fix is told from a belief.

## Assumption verification
- Every **load-bearing assumption** in a plan or design — an API's accepted inputs, a command's
  output shape, a boundary, a default — MUST be **executed as a throwaway command before it is
  written into the design**, and the design **cites the observed output**. An assumption asserted
  without evidence, where evidence was one command away, is a violation.
- Design review cannot catch a wrong assumption: it reads as reasonable, and the implementation
  and its tests are then both built from the same wrong model, so they agree with each other and
  pass. Tracer-bulleting the assumptions of one feature confirmed a `--porcelain` boundary,
  confirmed a base-ref chain, and found a truncation hole — all before any code existed. Separately,
  a selector grammar assumed from a wrapper's own code was wrong in a way that had already let a
  destructive verb run unguarded.
- The evidence belongs in the document, not only in the author's terminal. A cited output is
  checkable by a reviewer; "I verified this" is not.
- **Attributing a failure to a cause requires the controlled PAIR, not just the repro.** Run the
  case with the blamed step and the case without it, and require the observable to differ. A repro
  that reproduces confirms the symptom, never the cause. Measured four times: pane readiness was
  blamed for an `injected:false` that a missing `--inject` flag fully explained, and that causality
  shipped in a doc and a PR body; a title-only reading concluded "no agents running" and the
  operator corrected it; and two carried repros were each falsified by a control that removed the
  step they blamed. Re-run the MEASUREMENT as well as the claim — a brief's conclusion can be right
  while its method is wrong.

## Wrapper–runtime reconciliation
- A wrapper verb over an **external runtime's CLI** MUST be exercised **live against that runtime**
  — a full create → list → remove cycle, or the verb's own equivalent round trip — before it ships,
  and its **output-key extraction fixed against the observed envelope**. Shipping a verb whose
  response shape is known only from stub fixtures is a violation, however green the suite is.
- Stub fixtures encode the author's model of the envelope, so the wrapper and its tests agree with
  each other and both are wrong together — the Incident-replay gap, applied to response parsing.
  Four occurrences: a create-response `.id` read from the envelope (a per-request correlation uuid
  that always exists, so it yielded a plausible but useless handle) in two different verbs; then
  probing a live response for a delivery-id field surfaced `run_required` — the whole structured
  path had been **dead at its first mutation**, and no stub test could see it because the stub had
  no concept of a Run binding. Later the same day the real ack key proved to be `deliveryId` while
  the extraction chain led with `delivery_id`, and the only test covering that loop pinned the
  spelling the runtime never sends.
- The live probe is what finds these, not the review: each was invisible to design review, to the
  suite, and to a careful reading of the vendor guide. Where a live run is impossible (destructive
  verb, no credentials), say so in the doc and name what stayed unverified — an unmeasured shape is
  an open risk, not a pass.

## Regression provenance
- When a change makes an existing test fail, the plan or design MUST establish whether that test
  **asserts current behaviour that the change is fixing** before proposing to edit it. **Changing an
  existing test to pass is a violation unless** the doc states that the test pinned a defect (or
  stale contract) as correct, and cites what it asserted.
- The reflex "make the failing test pass" preserves the bug when the test *was* the bug. Three tests
  in one session asserted the defect as an acceptance criterion — a forwarded selector a live
  runtime rejects, a create-response handle the pane never has, a cwd-relative path — and each would
  have survived a naive "adjust the test" edit. A red pre-existing test is evidence about the test as
  often as about the change.

## Both halves of a doc change
- Removing a documented instruction, flag, or capability MUST be paired with **the executable
  replacement landed** (or an explicit statement that the capability is intentionally dropped, with
  the reason). A test asserting only that the old text is *gone* passes for a deletion that silently
  lost the capability.
- An unexecutable instruction was deleted in one session; a test checking only its absence would
  have gone green while the run lost the ability it named. The gate is: assert the new path works in
  the same change that removes the old one.

## Reimplementation parity
- Replacing a third-party dependency (validator, parser, formatter) with an in-tree implementation
  MUST ship a **differential test asserting identical results against the original** across a corpus
  that covers every construct in use, AND against the **real artifacts on disk**. Shipping the
  reimplementation with tests that exercise only itself is a violation.
- A hand-rolled reimplementation is worth exactly what its differential test catches. A bundled
  JSON-Schema validator agreed with the library on a construct-complete corpus and on the live state
  records; the traps it had to match (annotation-only `format`, `bool` is not `integer`) were
  invisible without the library beside it. Parity on a synthetic corpus alone repeats the
  Incident-replay gap: the corpus shares the author's model of the reimplementation.

---

## How agy uses this file
agy reads this verbatim as the **base** portion of the Axis B rubric, before the project layer.
Any finding that violates a base rule is auto-classified `## Must-fix` and cannot be downgraded.
