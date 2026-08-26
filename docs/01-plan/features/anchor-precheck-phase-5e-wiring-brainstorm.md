# Brainstorm: anchor-precheck-phase-5e-wiring

## Executive Summary

`h_mad_mutation_harness.py --check-anchors` is documented in SKILL.md §Phase-5 and run by hand;
nothing in the protocol obliges a run to invoke it. The harness's own refusal of a drifted anchor is
a **run-scoped and late** backstop — it protects only the specs a run happens to touch, and only at
the moment it touches them — so drift introduced by an edit can sit unnoticed for many cycles while
every downstream gate reads the guard's last green verdict as "enforced".

**Settled design — two mechanisms, different moments:**

1. **A suite test that sweeps the repository's own committed specs.** Rides the full-suite run that
   Phase 5f already performs, so it fires on every cycle regardless of whether that cycle runs any
   mutation. No new verdict token and no phase wiring. **Wider reach — CI, a bare `pytest`, the
   coupled sibling suite — is blocked on F9** (every committed spec pins a machine-specific absolute
   `root`) and is a Phase-2 precondition, not a property this design can claim yet.
2. **An inline sweep at the mutation-run chokepoint.** The harness sweeps the specs beside the one
   being run and **refuses the run if any has drifted**, which protects an ad hoc mutation run
   outside the suite. No receipt, no persistent state, no git.

## Problem Statement

A drifted anchor mutates nothing, so the guard it aims at is unverified while its spec still prints
a verdict-shaped line.

The harness is not blind to this — a run whose spec has a drifted anchor returns
`MUTATION: REFUSED`, and that refusal is loud and correct. But it has three properties that leave a
real gap:

- **Run-scoped.** It only ever speaks about the spec being run. A 5e for module M runs M's spec; an
  edit to shared code that drifts spec Y's anchors produces a clean 5e and leaves Y unverified.
- **Late.** It fires when the drifted spec is *next run*, which may be many cycles after the edit
  that caused the drift. In that interval the guard's recorded status is its last green verdict, and
  nothing distinguishes "enforced" from "unverified since the refactor three cycles ago".
- **Expensive to reach.** A run applies every mutation and runs the suite once per mutation. The
  sweep is file reads only. Discovering drift by running is the costly way to learn something a
  cheap read could have told you first.

The measurement is what these three predict. On 2026-08-26, **7 of 177 anchors across 14 committed
specs had drifted**, and they surfaced only because someone swept the whole tree by hand — no run
had refused them, because no run had touched them. **Two of the seven were broken by a refactor made
minutes earlier in the same session**, and the precheck caught the author's own drift twice more the
same day: three self-inflicted drifts in one day, by someone who knew the tool existed. The
recurrence is the argument — the failure is silent, self-inflicted, and frequent.

So the gap is not "the harness fails to notice drift". It is everything the harness's noticing does
not cover: **specs this cycle's runs do not exercise, and the interval between drift and next run.**
A sweep converts a late, run-scoped, incidental backstop into an early, deliberate one.

### The test suite is blind to this by construction (found during Phase 1)

Verified 2026-08-26 against `h-mad/tests/`: **no test sweeps the repository's own committed specs.**
Every `precheck_spec` call in `test_h_mad_mutation_harness.py` builds a synthetic spec under
`tmp_path`, and every other `mutation-specs` reference in the suite is a string literal for surface
classification. The sweep logic is well tested; the repository's 213 real anchors are not swept by
anything that runs automatically. All seven of the drifted anchors could sit in the tree with the
suite fully green — and did.

The suite does contain `test_skill_documents_the_anchor_sweep`, which asserts that SKILL.md contains
the string `--check-anchors`, under the docstring *"A tool nobody is told to run is a tool nobody
runs."* That is a doc test: it verifies the **documentation of the obligation**, not the obligation.
The A/B probe (F7) is the direct evidence that these are different things — the prose was present in
both arms' repository and only the arm whose *prompt* carried it swept anything.

This is what makes a suite test the natural home for the always-on half of the fix: the gap is
suite-shaped, in a suite that already has a slot for repository-property assertions right beside it.

### What the A/B probe does and does not establish (F7)

Two `exec codex` dispatches, identical but for a paragraph naming `--check-anchors`, returned
`AB: DIFFERENT a=SURVIVED b=REFUSED`. Arm B never swept — zero occurrences in its log. Arm A swept,
re-anchored, and thereby uncovered a genuine survivor the refusal had been masking.

**It establishes**, for this instance: an agent given the instruction followed it precisely and
unprompted; the same agent without it did not sweep at all.

**It does not establish** a general claim about prose. It is n=1 per arm, one model (`gpt-5.5`), one
toy task, one wording, one observable — and `h_mad_ab_dispatch.py` compares an observable without
saying *why* it differed. It is suggestive, not decisive, and the feature does not rest on it: the
7-of-177 measurement is the load-bearing evidence. What the probe usefully rules out is the narrow
hypothesis that the instruction is *ignored when present* — which, had it been true, would have
argued for better wording rather than for wiring.

## Proposed Approach

Two mechanisms covering two different moments. Neither subsumes the other: the test fires whether or
not a mutation runs, and the chokepoint fires whether or not the suite runs.

### Mechanism 1 — a suite test over the repository's own committed specs

A test that globs this project's `tests/mutation-specs/*.json`, sweeps them, and fails naming every
drifted anchor. It closes the always-on half of the problem with no new verdict token, no new
documented step, and no phase wiring — it rides the full-suite run that Phase 5f already performs,
and in principle also an ordinary `pytest` invocation and the coupled sibling repository's suite.

**Blocked on a portability defect found at the Phase-1 gate (F9), which Phase 2 must resolve first.**
All 16 committed specs hardcode `"root": "/Users/kimhawk/orca/skills/h-mad"`. Being absolute, that
resolves identically from every cwd — verified — so off this machine the root does not exist, every
target reads unreadable, and the test would fail everywhere but this box. The same pin means a
mutation run inside a **git worktree mutates the main checkout**, which matters because h-mad's own
Phase-5 fanout creates worktrees.

No portable spelling exists today: the specs need a root two levels up from themselves, omitting
`root` gives one level (`mutation-specs/`), and a relative value resolves against cwd rather than
the spec (F1). Phase 2 chooses between spec-relative resolution for relative roots (the only option
that also fixes the worktree hazard, at the cost of changing `h_mad_mutation_harness.py` behaviour),
a repo-root discovery rule, or scoping Mechanism 1 to this machine and dropping the portability
claim.

**Resolved in Phase 2** (recorded here so this section is not read as still open): spec-relative
resolution for relative roots, with all 17 specs re-rooted — and handoff's additionally re-prefixed,
because its root sits above its own skill and the domain layer forbids that. See spec FR-1, FR-2,
AC-2.6.

This is the strongest form of "unskippable by construction" available here, because the obligation
stops being a step anyone has to remember and becomes a property the suite asserts. It is also the
direct answer to the blindness found above: the suite currently tests the *documentation* of the
sweep and never the specs themselves.

### Mechanism 2 — an inline sweep at the mutation-run chokepoint

**Refuse on any drift in the spec set.**

- Before applying any mutation, `run_spec` sweeps every spec **in the same directory as the spec
  being run** and refuses the whole run if any anchor has drifted.
- Refusal, not warning: an advisory nobody must read is the status quo this feature exists to
  replace.
- The refusal is **set-wide**. Running module M's spec refuses when unrelated spec Y has drifted,
  because the goal is that no run reports success while the tree holds unverified guards.

Three properties decided this shape, each measured rather than assumed:

**The sweep is too cheap to cache.** All 16 h-mad specs — 213 anchors — sweep in **59 ms**. A
receipt exists to avoid redoing expensive work; and verifying a receipt honestly means confirming
the swept files have not changed since, which is re-reading the same files at ~the same cost. The
receipt would save nothing while adding persistent state and a staleness-keying problem.

**It keeps the harness git-free.** `h_mad_mutation_harness.py` touches git **zero** times today — the file contains no
reference to git at all; the only substring match is inside the word *digit*. Keying a receipt to tree state would
put git inside a stdlib-only, VCS-agnostic tool, in a repo whose `git stash` untracked-file hazard
is already documented.

**A chokepoint is unskippable by construction.** It lives inside the thing you must already run,
which is what distinguishes it from every alternative below.

The spec set is scoped to the running spec's own directory: self-scoping, needs no configuration,
keeps `h-mad/` and `handoff/` independent — each project's runs guard that project's specs — and
matches the location-independent default that F1 shows is already the correct resolution rule.

## Alternatives Considered

- **Prose in SKILL.md 5e (status quo)**: zero enforcement, which is the defect. Rejected.
- **A receipt at the same chokepoint**: the originally chosen shape. Rejected **on measurement**,
  not preference — at 59 ms the sweep is cheaper than an honest receipt check, so the receipt caches
  something cheaper than its own cache validation, and it would drag in either git or a content-digest
  scheme to solve a staleness problem that inline sweeping does not have.
- **A Phase-5 gate script** (`h_mad_new_gate.py` scaffold, shaped like `h_mad_wire_pin_gate.py`):
  genuinely considered, and initially retained as the only way to cover a cycle running no mutation.
  Rejected once Mechanism 1 was identified, which covers that same case **strictly better**: the
  gate needs a new verdict token, is itself another documented step — reproducing this feature's own
  complaint one level up — and fires only inside a `/h-mad` run, whereas a suite test needs no token
  and no step. Note the rejection does **not** depend on the wider-reach argument: F9 shows CI and
  the sibling suite are blocked until the `root` pinning is fixed, so on reach alone the two are
  currently comparable. What decides it is the token-and-step cost, which holds regardless. The
  gate's remaining distinctive advantage was dogfooding `h_mad_new_gate.py`, which is a reason to
  record an outcome, never a reason to choose a design.
- **Self-contained: refuse when the run's OWN spec was never swept**: cannot see the other specs,
  and the measured failure is exactly a spec drifting because a *different* file was edited.
  Rejected: it would have caught none of the seven.

## Known Limits

- **`h_mad_new_gate.py` goes unexercised by this feature.** Recorded in the dogfood ledger as such;
  it needs deliberate exercise elsewhere or an honest "not run" row. This is now the *only* residual
  limit — the earlier one ("a cycle that runs no mutation is not covered") is closed by Mechanism 1.
- The suite test asserts drift, not guard quality. A spec whose anchors all match can still aim its
  mutations at the wrong thing; that is what the mutation run itself, and `test`-field
  discrimination, are for.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| A non-spec `.json` sitting in the specs directory is swept, fails to parse, and blocks every run set-wide | M | Verified 2026-08-26: all 16 files in `h-mad/tests/mutation-specs/` carry a `mutations` key and no non-`.json` files are present, so this is a **future** hazard, not a present one — and `h_mad_new_gate.py` writes into that directory, which helps keep it clean. Still worth closing: identify a spec structurally (a `mutations` key) and skip non-specs; never treat "not a spec" as "drifted" |
| An unrelated spec's drift blocks all mutation work until fixed | H | Accepted deliberately as the forcing function. The refusal must name *which* spec drifted and why, so the fix is obvious rather than a hunt |
| Set-wide sweeping makes M's run depend on Y's health, surprising an operator debugging M | M | The refusal text must distinguish "your spec drifted" from "a sibling spec drifted"; they prescribe different actions |
| Inline sweep changes `run_spec`'s contract, and existing callers/tests assume it applies mutations immediately | M | RED first against the existing suite; treat any pre-existing test that breaks under §"Regression provenance" — check whether it pinned the old behaviour deliberately |
| F1's relative-`root` hazard now applies to *every* sibling spec, not just the one being run | M | Sweep resolves each spec's root the same way `precheck_spec` already does; report the resolved root in the refusal |
| The sweep's 59 ms is measured on this tree and could grow | L | It is file reads with a per-file cache; re-measure if the spec count grows by an order of magnitude |
| The suite test locates the specs dir by a path that breaks under the skills symlink, or when run from a sibling repo | M | Resolve relative to the test file (`Path(__file__).resolve().parents[1]`), the idiom the existing doc test already uses; assert the glob found a non-zero number of specs, or an empty glob passes vacuously |
| The suite test passes vacuously if the glob matches nothing | **M** | Assert a non-zero spec count explicitly. Verified 2026-08-26 that the protection exists one layer up but **not** in the layer the test would use: the CLI refuses zero specs via argparse `nargs='+'`, while a test iterating `Path.glob()` over an empty directory simply runs no assertions and passes. Same class as F2's cannot-judge-reads-as-clean — zero specs swept and zero drift found are indistinguishable in a bare loop |
| Committed specs pin a machine-specific absolute `root`, so Mechanism 1 fails off this box and a worktree run mutates the main checkout (F9) | **H** | Verified 2026-08-26 across all 16 specs. Must be resolved in Phase 2 before Mechanism 1 can claim portability; see the Proposed Approach note |
| Two mechanisms drift apart as the sweep's semantics change | L | Both call `precheck_spec()`; neither re-derives the anchor rule. Keep it that way — a second copy of the one-match rule is how `--check-anchors` and the run would disagree |

## Dependencies

None external. Touches `h_mad_mutation_harness.py` (`run_spec` and the sweep helpers), its test
suite and its own mutation spec, SKILL.md §Phase-5e, and the helper-scripts registry entry. The
skills symlink couples this repo's suite to sibling repos: run both before merging.

## Out of Scope

- **F2 — normalizing the sweep CLI's verdict/exit discipline.** `ANCHORS_DRIFTED` is a real verdict
  that exits 2, and an unusable spec JSON collapses into that same word rather than carrying its own
  cannot-judge. Deferred: editing the harness's verdict shape in the same cycle that wires that
  harness in couples two changes whose 5e reverts would have to discriminate each other, and F2
  fails toward re-anchoring — the safe direction.
  **Note the interaction this decision created:** with a set-wide refusal, an unusable spec JSON
  would otherwise block every run. The inline path avoids inheriting that by calling
  `precheck_spec()` directly and making its own unreadable-vs-drifted distinction, leaving the CLI's
  F2 quirk untouched. This is what keeps F2 genuinely out of scope rather than nominally so.
- F1, F3–F6 (see the dogfood ledger): tool defects observed while staging the probe. Monitoring
  rows, filed at Phase 7, not requirements.

## Open Questions

- Does the refusal reuse `MUTATION: REFUSED` with a new reason token, or need a distinct verdict
  word? `REFUSED` already means "nothing was measured", which is exactly right — but it currently
  counts per-mutation refusals, and a set-wide pre-refusal has no mutation count to report.
- Should the inline sweep be suppressible for the harness's own self-tests, which construct specs in
  temp directories? If so, the suppression must not be reachable from ordinary use.
- Does `handoff/tests/mutation-specs/` need the same behaviour, and does the coupled suite catch it?
  Mechanism 1 is per-project by construction (it globs its own project's specs), so `handoff/` needs
  its own copy of the test or it stays uncovered — decide whether that is in scope here.
- Should `test_skill_documents_the_anchor_sweep` change now that Mechanism 1 exists? It asserts the
  prose exists, which this cycle showed is not the obligation. Leaving it is harmless; leaving it
  *unremarked* risks the next reader mistaking it for the enforcement. Out of scope as written, but
  worth a one-line docstring note.

## Version History

- v1.0: Initial brainstorm draft. Direction, failure mode, and A/B-probe timing settled with the
  operator before drafting; A/B result (F7) incorporated as evidence.
- v1.1: Operator revisions at the Phase-1 gate. Phase-5 gate script promoted from rejected
  alternative to live contender. F7 reframe softened — stated as suggestive, with the 7-of-177
  measurement made load-bearing instead. Problem statement reworked from "the hole is only
  cross-spec" to the run-scoped/late/expensive properties of the existing refusal. F2 normalization
  moved out of scope, **reversing the in-scope decision recorded earlier in Phase 1**; recorded here
  so the reversal is explicit rather than silent.
- v1.2: Enforcement point settled ahead of Phase 2. Chokepoint retained; the **receipt dropped on
  measurement** (59 ms / 16 specs / 213 anchors, vs a receipt check that must re-read the same
  files) and the harness kept git-free. Refusal scoped set-wide; spec set scoped to the running
  spec's own directory. Gate shape moved to a reasoned rejection with its uncovered case recorded
  under Known Limits. Non-spec-JSON hazard raised to the top risk, then **corrected down to M after
  checking** — all 16 committed specs carry a `mutations` key and no stray files are present, so it
  is a future hazard, not a present one. F2's newly load-bearing interaction with a set-wide refusal
  recorded in Out of Scope.
- v1.3: Known Limit reconsidered at the operator's direction, which surfaced a finding that changed
  the design: **no test sweeps the repository's own committed specs** — every `precheck_spec` call in
  the suite uses a synthetic `tmp_path` spec, so all 213 real anchors could drift with the suite
  green. Added **Mechanism 1**, a suite test over the committed specs, which closes the
  no-mutation-cycle limit strictly better than the Phase-5 gate that was retained for it in v1.2;
  the gate is now rejected outright. Recorded that `test_skill_documents_the_anchor_sweep` asserts
  the *documentation* of the obligation rather than the obligation. Added the vacuous-empty-glob risk
  — the same cannot-judge-reads-as-clean class as F2.
- v1.4: Advisor-prompted check of the committed specs' `root` fields found **F9**: all 16 hardcode
  `/Users/kimhawk/orca/skills/h-mad`. F1's cwd-relative hazard does not fire, but a worse one does —
  Mechanism 1's portability claim ("fires in CI … and in the coupled sibling suite") was **false as
  written** and is corrected here, and a mutation run inside a git worktree resolves to the main
  checkout. Added as the top risk and as a Phase-2 precondition. No design change: the two
  mechanisms stand.
- v1.5: Corrected the git claim (the file contains no reference to git at all; the only substring match is inside the word digit) and recorded that F9's Phase-2 choice has since been resolved.
