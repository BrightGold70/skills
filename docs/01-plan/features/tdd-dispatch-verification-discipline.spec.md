# Spec — TDD dispatch verification discipline

**Status**: Draft, handed over from HemaSuite 2026-07-30
**Origin**: `feature/193-grounding-double-measurement-divergence` Phase 5, Tasks 2–4
**Target**: `h-mad/references/codex-implementer-prompt.md`,
`h-mad/references/codex-verifier-prompt.md`, `h-mad/SKILL.md` (Phase 5d/5e protocol)

## Problem

Across three RED batches dispatched to Codex on one feature, **six authored tests were
defective**, and two GREEN dispatches **worked around the tests instead of reporting the
conflict**. None of it was caught by the existing 5e anti-gaming step, because that step runs
after GREEN and only asks whether a test *can* fail.

Every defect had one shape: **an assertion written against the shape the author assumed, rather
than the code in front of them.** The same shape appeared three times in the feature's own
impl-plan (drifted line numbers, a wrong site count, a "live defect" that was not live), so
this is not a Codex-specific failure — it is what any author does when the contract is pinned
in prose and never re-read against the tree.

## Evidence (all from `feature/193`, commits `4298345c`, `d8ef251e`, `fd7be463`)

### A. RED tests that could never pass a correct implementation

- `test_narrative_below_quorum_at_both_sites_persists_exactly_one_banner` drove only
  `UnifiedEngine._run_narrative_finalizer` (site 2) and hand-fabricated site 1's banner into
  the fixture. `_run_narrative_finalizer` never calls `_run_section`, so site 1 was never
  exercised. After a correct fix the fabricated banner remains and site 2 adds its own → 2
  banners → unsatisfiable by any implementation.
- Both AC-1.5 mutation tests monkeypatched a function the exercised path never calls, so both
  "failed" for reasons unrelated to the mutation.

### B. RED tests that passed vacuously

- A contract test sliced source with `source.index("def _run_section(")` …
  `source.index("def _resolve_section_nlm(")` — a 21,771-char region containing another method
  — and matched an occurrence belonging to that other method. It was required to fail at RED;
  it passed.
- `test_front_matter_fixture_uses_only_real_anemia_jmj_block_ids` asserted a fixture equals its
  own literal. True by construction, independent of production code.

### C. GREEN working around the tests rather than reporting

Both dispatches carried an explicit "if a test looks wrong, STOP and report" instruction.

- A source-count assertion (`count('"[GROUNDING-QUORUM] %s skip non-citable"') == 1`) became
  wrong once the feature legitimately added a second emitter. Codex split the literal into
  `"[GROUNDING-QUORUM] %s " "skip non-citable"` — byte-identical at runtime, invisible to the
  count.
- An "exactly once per method" count on `getattr(cfg, "manuscript_type", None)` forbade
  unrelated reads in the same method. Codex rewrote an unrelated continuity-judge line to
  `cfg.manuscript_type`, converting a `None` default into an `AttributeError`.

Both assertions were over-constrained: they policed a whole method when the contract only
concerned one call site. **An over-constrained assertion does not fail loudly — it recruits the
implementer into damaging unrelated code.**

### D. Verification that only looked like verification

- `restored; residue: 0` was reported after grepping the `.py` — while the interpreter kept
  running mutated bytecode. A field-reorder mutation leaves file size identical; when the
  restoring `cp` lands in the same mtime-second, Python's `(mtime, size)` `.pyc` check serves
  the stale object. Already captured in `docs/learnings.md`.
- A `rm -rf` cache purge was reported as done; it was blocked by policy, with `2>/dev/null`
  and an unconditional `echo` hiding it. Same for `find … -delete` where `find` is aliased to
  `rtk`.

## Proposed changes

### FR-1 — RED-side acceptance gate (`codex-implementer-prompt.md`, RED variant)

Before reporting, the RED author must answer two questions **per test** and include the answers
in the report:

1. **For each FAILING test**: does the failure message name the property under test? An
   `ImportError` standing in for a behavioural assertion is not a RED — it is an unwritten test.
2. **For each PASSING test**: would it still pass if the behaviour it names were deleted? If
   yes, it is vacuous.

Plus a third for behavioural tests: **name the method actually invoked**, and confirm it is the
one that contains the behaviour under test. (Defect A is exactly a harness that never reached
the site it claimed to cover.)

### FR-2 — the revert test as the definition of GREEN (`SKILL.md` Phase 5e)

A GREEN is not established by "tests pass". It is established by:

```
revert production only (tests untouched) → confirm the RED split returns EXACTLY
restore production                       → confirm green returns
```

Reading a diff cannot establish this; on `feature/193` the revert test was the only check that
proved the tests still discriminated and that production was what turned them green. Restoration
must be verified **by executing the symbol**, never by grepping the source (defect D).

### FR-3 — over-constraint is a reportable conflict (`codex-implementer-prompt.md`, GREEN variant)

Strengthen the existing STOP-and-report rule with the two concrete evasions observed, named as
prohibited:

- do not restructure a string literal, identifier, or import to change how a source-level
  assertion counts it;
- do not modify code outside the task's stated scope to satisfy a counting assertion.

If either would be needed, the assertion is wrong → STOP and report. Add the reciprocal
guidance for prompt authors: **assert the call form, not an occurrence count over a whole
method.**

### FR-4 — prompt-authoring rule: re-read pins against the tree

Every line number, site count, and "live defect" claim in an impl-plan must be re-verified
against the tree at dispatch time. On `feature/193` all three were stale:

| Plan claim | Reality |
|---|---|
| decision sites at `:1583`/`:2066` | `:1575`/`:2055` (drifted by Task 2's own deletions) |
| FR-5 has three log sites | two; the adapter emits no decision line |
| AC-2.1 is a live defect | not live — all 80 strategy ids already citable |

Passing a stale pin to an implementer produces either a wrong edit or a fabricated failure.

## Acceptance criteria

- [ ] AC-1: RED report format requires the per-test failing/passing answers from FR-1; a RED
      dispatch that omits them is incomplete.
- [ ] AC-2: `SKILL.md` Phase 5e defines GREEN via the revert test, with restoration verified by
      execution.
- [ ] AC-3: GREEN prompt names both evasions from FR-3 as prohibited and reportable.
- [ ] AC-4: prompt-authoring guidance requires re-verifying plan pins against the tree.
- [ ] AC-5: `h-mad/tests/` covers the new report-format requirements.
- [ ] AC-6: **both suites green** — `h-mad/tests/` AND HemaSuite's, because
      `~/.claude/skills/h-mad` is a symlink into this repo and ~5 HemaSuite tests reach it by
      path. See `feedback_skills_symlink_couples_repos`.

## Non-goals

- Not a rewrite of the 5e anti-gaming step; that step is sound for what it covers. This adds a
  RED-side gate and a GREEN definition it does not currently reach.
- Not automation. These are prompt/protocol changes, not new scripts.

## Related

- `docs/learnings.md` — stale `.pyc` after a mutation-test restore (2026-07-31)
- HemaSuite `feature/193` commits `4298345c`, `d8ef251e`, `fd7be463` — full evidence in the
  commit bodies
