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

## Doc-template superset compliance
- Generated phase documents whose type is validated by an external doc-structure validator
  (e.g. bkit PDCA: `plan` → `docs/01-plan/...`, `design` → `docs/02-design/...`,
  `report` → `docs/04-report/...`) MUST be supersets that satisfy that validator's required
  sections AND retain the existing h-mad sections. Dropping an h-mad section or failing the
  validator is a violation.

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
