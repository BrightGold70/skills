# Dogfood ledger — anchor-precheck-phase-5e-wiring

**Opened:** 2026-08-26, Phase 1 · **Feature:** `anchor-precheck-phase-5e-wiring`

The seed names five tools shipped `351b4c7`..`920d204` that had never run inside a live `/h-mad`
cycle. Exercising them is a deliverable **separate from the feature itself**, so observations are
recorded here as they happen rather than reconstructed at Phase 7.

A row is only closed by an observation. "Ran it, looked fine" is not an observation; the verdict
line, the exit code, and what the tool did or failed to do are.

## Checkpoint status

| Phase | Tool | Status | Observation |
|---|---|---|---|
| 5d | `h_mad_assemble_tdd.py` (task-slicer bound, `6c34e60`) | pending | first live use; watch that the last impl-plan task does not drag `## Version History` into its prompt |
| 5e | `h_mad_mutation_harness.py --check-anchors` | **exercised early** (Phase 1) | see F1, F2 below — used to stage the A/B probe |
| 6 | `h_mad_audit_gate.py --gated` (`1c5d89e`) | pending | stamp is written only on PASS |
| 6→7 | `h_mad_audit_gate.py --verify-stamp` | pending | read `GATESTAMP:` before Phase 7 closes |
| — | `h_mad_identifier_sweep.py` | **exercised** (Phase 3) | `LEFTOVERS identifiers=1 leftover=11` — see F10. Seed predicted 9; the count grew because recording the prediction added hits |
| — | `h_mad_ab_dispatch.py` | **exercised** (Phase 1) | see F3–F7; result feeds the spec's rationale |

## Findings

Numbered `F<n>`. Each carries what was measured, not what was inferred.

### F1 — a relative `root` in a mutation spec resolves against the caller's cwd, not the spec

`h_mad_mutation_harness.py` resolves the spec's root as:

```python
root = Path(spec.get("root") or spec_path.parent).resolve()
```

`"root": "."` therefore means **the invoking process's cwd**, not the spec's own directory — while
*omitting* `root` correctly defaults to `spec_path.parent`. Measured: a toy spec carrying
`"root": "."`, swept from `/Users/kimhawk/orca/skills`, reported
`ANCHORS_DRIFTED specs=1 mutations=3 ok=0 drifted=0 unreadable=3`, all three "unreadable" because
it looked for `guard.py` in the repo root.

The counter-intuitive part is the direction: **the explicit value is less correct than the default.**
Dropping the key entirely made the spec location-independent — re-swept from `/tmp`, it returned the
intended `ok=2 drifted=1 unreadable=0`.

Consequence for this feature (updated in v1.3 — the receipt shape this originally addressed was
dropped): both mechanisms sweep **sibling specs the caller did not write**, so each spec's root is
resolved by someone else's declaration. A set-wide refusal must therefore report the *resolved* root
alongside the drifted anchor, or a spec carrying a relative `root` produces a refusal that names a
file the operator cannot find.

### F2 — `ANCHORS_DRIFTED` is a real verdict that exits 2, and it absorbs two distinct cannot-judges

Confirmed against the source (`h_mad_mutation_harness.py:582`, `:594`) and live.

- `return 0 if verdict == "ANCHORS_OK" else 2` — a genuine measurement ("I swept, and found drift")
  exits non-zero. Every other gate in this skill reserves non-zero for operational failure and exits
  0 on a verdict. SKILL.md already tells the reader not to read `$?` here, which mitigates it for a
  careful caller but leaves the shape inconsistent.
- Both an unreadable **target file** and an unusable **spec JSON** collapse into the word
  `ANCHORS_DRIFTED`. The counts distinguish them (`drifted=` vs `unreadable=`); the verdict word
  does not. The target-file case is *reasoned* — the code comments argue "the spec points somewhere
  that is no longer there, which is the same unverified guard by another route" — but a malformed
  spec JSON says nothing whatever about anchors.

F1's live output is the demonstration: `drifted=0 unreadable=3` under the word `DRIFTED`.

**Operator decision (Phase 1, revised at the Phase-1 gate): OUT of scope.** Initially taken in
scope — `ANCHORS_DRIFTED` to exit 0, and the unusable-spec case to get its own cannot-judge word
carrying no drift counts — then deferred at the gate. Rationale: editing the harness's verdict shape
in the same cycle that wires that harness in couples two changes whose 5e reverts would have to
discriminate each other, and F2 fails toward re-anchoring, which is the safe direction. File as a
`docs/skill-monitoring.md` row at Phase 7. Recorded as a reversal so it is not read as a fresh
decision.

### F3 — `h_mad_ab_dispatch.py` controls the prompt but has no notion of controlling the environment

`run_ab` iterates `for arm in ARMS:` strictly sequentially with **no per-arm setup or teardown
hook**. `is_controlled` rigorously proves the two *prompts* differ in exactly one variable — it
re-derives the template from each arm — but nothing constrains the *world* the arms run in.

For any prompt rule whose entire purpose is to make an agent **change something**, arm A's side
effects are still on disk when arm B starts. In this probe that was concrete and fatal: arm A
re-anchoring the drifted spec would have handed arm B a clean spec, and both arms would have
reported the same verdict — a false `SAME`, which is precisely the verdict the tool's own docstring
calls "the most believable lie available here" (said there about a different failure).

Closed for this probe by making the spec location-independent (F1) and instructing **both** arms
identically to copy into a private `mktemp -d` — an environment control expressed in the template,
because the tool offers nowhere else to put one.

### F4 — `_observe` takes the FIRST match; every other extractor in this skill takes the LAST

```python
match = pattern.search(text)
return match.group(1) if match else None
```

`h_mad_extract_verdict.py` and `h_mad_extract_report.py` both deliberately take the **last** match,
to fence off stale scrollback and prior cycles. `_observe` takes the first.

On an accumulating transcript this observes the agent's **earliest** attempt rather than its
outcome. Directly relevant here: an arm that runs the harness, sees a refusal, fixes the anchor and
re-runs emits two verdict lines, and first-match scores the refusal. Because both arms tend to do
the same thing *first*, the bias runs toward `SAME` — again toward the false null.

Worked around rather than fixed: the probe's observable is a `FINAL-VERDICT:` line the contract asks
the agent to emit exactly once, at the end.

### F5 — only `{prompt}` and `{log}` are substituted, so any other per-arm path collides

The runner substitutes exactly two tokens. SKILL.md separately requires that every dispatch get its
**own** `--out` ("it is last-writer-wins … a lost verdict is indistinguishable from a dispatch that
never ran (J29)"), and `exec` additionally refuses to overwrite an `--out` that changed while it ran
— so a shared `--out` across two arms is both a correctness and a refusal hazard.

Worked around by deriving one from the log path: `--out={log}.out`. Substitution is a plain
per-token `str.replace`, so this composes. It works, but it is a trick the caller has to invent.

### F6 — `--run` rejects any argv token beginning with `-` in the space-separated form

Measured, first attempt:

```
h_mad_ab_dispatch.py: error: argument --run: expected one argument
```

`--run --model` makes argparse read `--model` as a flag rather than as `--run`'s value. Every
realistic dispatch argv contains flags, so the usage SKILL.md documents — `--run <argv token>…` —
fails on the first one. The working form is `--run=--model`, which the docs do not mention.

This is a documentation defect at minimum: the tool is usable, but not as written.

### F7 — the A/B result: the prose rule IS causally effective; the defect is delivery, not persuasion

```
AB: DIFFERENT var=PRECHECK a=SURVIVED b=REFUSED
  exits: a=0, b=0
```

Two `exec codex --model gpt-5.5` dispatches, identical but for one paragraph naming
`--check-anchors`. Observable: a `FINAL-VERDICT:` line the contract required exactly once
(chosen to defeat the prompt-echo trap — the template's own `FINAL-VERDICT: <the …>` cannot match
`FINAL-VERDICT: (\w+)`, because `<` is not a word character).

| | arm A (rule present) | arm B (rule absent) |
|---|---|---|
| swept? | yes — `ANCHORS_DRIFTED ok=2/3`, re-anchored, re-swept `ANCHORS_OK ok=3/3` | **no** — zero occurrences of `check-anchors` or `ANCHORS:` in the log |
| harness verdict | `MUTATION: SURVIVED mutations=3 caught=2 survived=1 refused=0` | `MUTATION: REFUSED mutations=3 caught=2 survived=0 refused=1` |
| reported | `STATUS: DONE` | `STATUS: BLOCKED` |

**The seed predicted `SAME`** and called that "a finding about this very feature". The measured
result is the opposite: arm A followed the instruction precisely, unprompted, on the first try,
while arm B never swept at all.

State the strength carefully. This is **one probe** — n=1 per arm, one model (`gpt-5.5`), one toy
task, one wording, one observable — and `h_mad_ab_dispatch.py` compares an observable without
saying *why* it differed. It does not establish a general claim about prose, and the feature must
not rest on it. What it usefully rules out is the narrow hypothesis that the instruction is
*ignored when present*; had that been true, the remedy would have been better wording rather than
wiring. The load-bearing evidence remains the 7-of-177 measurement.

Two secondary observations from the same run:

- **The sweep uncovered a real defect the refusal was masking.** Arm A's re-anchoring turned a
  refusal into `SURVIVED` — mutation 3 genuinely is not discriminated by its named test. A refusal
  says "nothing was measured"; it does not say "and there is a hole behind it". Arm B, stopping at
  the refusal, never learned this. That is the cross-spec failure in miniature.
- **It dogfooded the harness's `test`-field discrimination**, unplanned. The detail line reads
  `named test test_guard.py::test_limit_allows_below PASSED but the suite went red elsewhere
  (test_guard.py::test_limit_refuses_at_boundary) — the mutant is caught by the wrong assertion`.
  Without a `test` field the suite went red, so it would have scored as a clean kill. This is the
  "caught by the wrong catcher" case the field exists for, observed live.

Honesty note on arm B: it ended `BLOCKED` rather than falsely reporting success, so in *this* toy
the harness's own refusal was an adequate backstop. That is because the drift sat in the spec being
run. It does not generalise — see the Problem Statement in the brainstorm for why the cross-spec
case has no such backstop.

### F8 — no test sweeps the repository's own committed specs (found at the Phase-1 gate)

Not a defect in the five dogfooded tools, but found while reconsidering the Known Limit, and it
changed the design — so it is recorded here with the rest of the evidence.

Verified against `h-mad/tests/`: every `precheck_spec` call in `test_h_mad_mutation_harness.py`
builds a synthetic spec under `tmp_path`, and every other `mutation-specs` reference in the suite is
a string literal used for surface classification. **The sweep logic is thoroughly tested; the
repository's own 213 anchors are swept by nothing that runs automatically.** All seven of the
drifted anchors could — and did — sit in the tree with the suite fully green.

The suite does contain `test_skill_documents_the_anchor_sweep`, asserting that SKILL.md contains the
string `--check-anchors`, under the docstring *"A tool nobody is told to run is a tool nobody runs."*
It verifies the **documentation of the obligation**, not the obligation. F7 is the direct evidence
that those differ: the prose was present in the repository for both arms, and only the arm whose
*prompt* carried it swept anything.

Consequence: the always-on half of this feature became a suite test (Mechanism 1 in the brainstorm),
which closes the no-mutation-cycle limit better than the Phase-5 gate that had been retained for it.

### F9 — every committed spec hardcodes a machine-specific absolute `root`

Found at the Phase-1 gate while checking whether F1's cwd-relative hazard fires on the committed
specs. It does not — but a worse one does.

All 16 specs in `h-mad/tests/mutation-specs/` carry
`"root": "/Users/kimhawk/orca/skills/h-mad"`. Because the value is absolute, it resolves to that
exact path **from every cwd** — verified from `/tmp`, `/Users/kimhawk`, and the repo root, all three
yielding the same target. Two consequences, both material to this feature:

- **Mechanism 1 is not portable as the brainstorm originally claimed.** Off this machine — CI, a
  fresh clone, another developer — that root does not exist, so every target reads as unreadable,
  which F2 folds into `ANCHORS_DRIFTED`. The suite test would fail 100% of the time everywhere but
  this box. The claim that it "fires in CI, in a bare pytest, and in the coupled sibling suite" was
  false when written and has been corrected in v1.4.
- **A mutation run inside a git worktree mutates the MAIN checkout.** h-mad's own Phase-5 fanout
  creates worktrees; a spec pinned to the main checkout's absolute path would have the harness apply
  mutations outside the worktree it is running in. The harness restores what it mutates, so this is
  not silent corruption — but it is the wrong tree, and a concurrent fanout module would see it.

There is **no portable way to express the correct root today**, which is why this is a design input
rather than a tidy-up. The specs live at `<repo>/h-mad/tests/mutation-specs/` and need a root of
`<repo>/h-mad/` — two levels up. Omitting `root` yields `mutation-specs/` (wrong level), and a
relative `"../.."` resolves against **cwd**, not the spec (F1). Neither available option expresses
"two levels up from this spec file".

Phase 2 must decide between: spec-relative resolution for relative `root` values (a change to
`h_mad_mutation_harness.py`, and a behaviour change for any caller relying on today's cwd-relative
reading), or a repo-root discovery rule, or accepting non-portability and scoping Mechanism 1 to
this machine. The first is the only one that also fixes the worktree hazard.

### F10 — `h_mad_identifier_sweep.py` exercised against a past rename; all 11 hits deliberate

Run at Phase 3 against the `h-mad-advisor-gate.sh` rename, the exercise the seed prescribes for a
tool with no phase home. Verdict `SWEEP: LEFTOVERS identifiers=1 leftover=11 allowed=0 related=0
history=3`, exit 0.

**The seed predicted 9 and the tool reported 11.** Two of the extra hits are this feature's own
documents — the seed file naming the rename, and the ledger row recording the prediction. Writing
down the expected count changed it. That is the tool's acknowledged noise source (prose naming a
renamed thing is both real signal and the main source of false positives) arriving self-inflicted,
and it is a small argument for why the allowlist is an input rather than something inferred: a
count is not a stable expectation.

All 11 verified deliberate. Ten are prose, comment, or test-docstring explanations of the rename.
The eleventh is the one worth the sweep:

```
h-mad/tests/test_h_mad_advisor_warn.py:38  [test]
GATE = REPO_ROOT / "h-mad" / "hooks" / "h-mad-advisor-gate.sh"
```

That is **code**, not prose, assigning a path to a file that no longer exists — the shape a genuine
stale reference takes. Checked: line 315 is `assert not GATE.exists()`, a guard that the old hook
stays deleted. Deliberate, and correct.

The observation is that the tool did the useful thing: it surfaced the single code-level hit among
ten prose hits and left the judgement to the operator, exactly as its contract says. A verdict of
`LEFTOVERS` is not a claim that anything is wrong.

### F11 — the `Effort:` block caught a double-clean hollow audit cycle on its first live use

Plan audit cycle 1 returned:

```
AUDITCYCLE: PASS must=0 should=0 passes=2 p1=0/0 p2=0/0 delivered=report-file,report-file
Effort:
- p1 tools=2 ok=2 failed=0 thinking=4019  low-evidence
- p2 tools=2 ok=2 failed=0 thinking=14001 low-evidence
```

`ok=2` is exactly the two successful calls the report-file contract itself costs — the
`write_to_file` for the report and the `run_command` that writes the `.done` marker. Confirmed
independently with `h_mad_review_evidence.py`, which returned
`EVIDENCE: PASS tools=2 ok=2 failed=0 thinking=4019 status=SUCCESS` for pass 1. Neither pass read
anything.

This is J49's documented cycle-24 signature almost exactly (that case double-cleaned at 6.2k/4.4k
thinking with the 2 delivery calls each). **At the `AUDITCYCLE:` line alone the cycle is
indistinguishable from a real clean gate** — `PASS must=0 should=0` is what a genuinely clean audit
prints too. The block is what made the difference visible, which is the whole claim J49 makes for
it, observed working.

Per SKILL.md the correct action is to re-dispatch, never to record the PASS, and that is what was
done (cycle 2).

**Two caveats worth keeping.** First, `low-evidence` is a scoring caveat and not a gate: an audit
prompt inlines the plan, spec and both invariant files (54.9 KB here), so a pass genuinely does not
*need* to read the tree, and J49 itself records a 2-call pass that returned a real finding. Second,
this cycle was not entirely hollow — pass 2 returned two Nits and one of them was a real factual
error in the plan (see below). So the honest reading is "insufficient evidence to trust the clean
verdict", not "the passes did nothing".

### F12 — a version-history bump recorded a fix that had not been applied (self-inflicted, Phase 3)

Applying pass 2's nits, the content edit and the version bump were issued in one command. The edit's
anchor did not match — the assumed line wrapping was wrong — so the `python3` block raised and wrote
nothing, while `h_mad_version_history.py`, a separate process in the same command, ran anyway and
appended:

```
- v1.1: Audit v1 nits ... corrected the drift measurement to 7-of-177 ...
```

For one command the plan claimed a correction it did not contain. The document's own change log was
the least reliable statement in it.

`h_mad_version_history.py` behaved exactly as designed — it verified its own splice was
insertion-only and reported truthfully about *its* write. The defect was sequencing: an unconditional
bump after an edit that can fail. This is the same shape as the failure the feature exists to
prevent — an assertion that reports success while the thing it describes did not land — arriving one
command after writing the plan that describes it.

Caught by re-reading the file rather than by any gate. The generalisable rule: **never issue a
version bump in the same command as the edit it describes**, or gate it on the edit's exit status.

### F13 — four clean audit passes missed a conflict between AC-2.5 and a domain invariant

Found by probing the plan against `.h-mad/invariants.md` directly, after two consecutive
`AUDITCYCLE: PASS must=0 should=0` cycles whose four passes were all `low-evidence`.

The repository's Axis B domain layer has exactly two rules, and the first is:

> **Skill self-containment** — A skill MUST remain runnable from a bare clone: no import of another
> skill's internals, no hardcoded path outside the skill's own directory.

The two projects' specs are structurally different in a way that matters:

| | declared `root` | `mutations[].file` | root is the skill dir? |
|---|---|---|---|
| `h-mad` (16 specs) | `<repo>/h-mad` | `scripts/h_mad_*.py` | yes |
| `handoff` (1 spec) | `<repo>` | `handoff/scripts/...` | **no — one level above** |

`handoff`'s spec also runs `pytest handoff/tests/...` in its `command`. So a spec-relative re-root
of it yields `../../..`, which is still the repository root — a path outside the skill's own
directory, and therefore still against invariant #1 even though it is no longer machine-pinned.
Making it genuinely self-contained requires rooting at `../..` **and** stripping the `handoff/`
prefix from all 18 `file` values **and** rewriting the `command` pytest path.

That collides with the feature's own acceptance criterion:

> **AC-2.5**: Re-rooting changes only `root` values — every spec's `mutations`, `command`,
> `target_command`, and anchor text are byte-identical before and after.

AC-2.5 and invariant #1 cannot both hold for the handoff spec. AC-2.5 was written to guard the top
risk (a silent corruption during a bulk edit that the sweep cannot see, because anchor text is
untouched), and it is correct for h-mad's 16 — where root genuinely is the only thing that changes.
It over-generalises to the seventeenth.

Two things this says about the audits. First, the conflict is an Axis B domain-rule violation, which
this repository's own convention classifies as `## Must-fix` — the category the passes are least
entitled to miss. Second, it is exactly the class of defect that requires *reading two documents
against each other*, which a pass making zero tool calls and ~4.5k thinking tokens is poorly placed
to do. F11's caveat said "insufficient evidence to trust the clean verdict" rather than "the passes
did nothing"; this is the evidence that the caution was warranted rather than merely procedural.

### F14 — FR-6 relaxes a guard with no differential corpus, which the base layer requires

Second finding from probing, this time against `invariants.base.md` §"Guard narrowing":

> When a change **deliberately makes a guard accept something it used to reject**, the relaxation
> MUST be shown to be *exactly* the intended case: run a corpus of inputs through the old and new
> logic and diff the verdicts, then account for **every** input whose verdict softened. A green
> suite is not evidence here — it encodes the cases someone already thought of, which is the wrong
> population when the question is "what else did this let through?"

FR-6 is exactly that shape. Today an unusable spec increments `unreadable` and forces
`ANCHORS_DRIFTED`; under FR-6 a JSON file with no `mutations` key is **skipped** and contributes
nothing to the drift count. That is a guard accepting something it used to reject, and the spec's
five ACs describe the intended behaviour without ever proving the relaxation did not widen further
than intended.

The invariant's second clause is satisfied, and was checked rather than assumed. `_load_spec`
requires a non-empty `mutations` list (and a non-empty `command` argv), so "has a `mutations` key"
is a **necessary condition guaranteed by the loader**, not a heuristic re-deriving the format —
verified by reading the real loader, per §"Assumption verification".

The first clause is not satisfied: no AC calls for a differential corpus.

A related under-specification surfaced in the same check. AC-6.1 keys classification on the
`mutations` key alone, while `_load_spec` also demands `command` and per-mutation `name`/`file`/
`find`. A file carrying `mutations` but no `command` is therefore classified as a spec and then
fails to load — which under AC-6.3 is reported as a real finding rather than skipped. That happens
to be the desired outcome, but it is desired by accident: the spec never states which of the
loader's requirements the classifier keys on, so the two could drift apart without anything noticing.

Note what this and F13 have in common: both are Axis B violations, both require reading two
documents against each other, and both were missed by every audit pass — eight of them now, across
four cycles, all `low-evidence`.

## Note on scope

F1–F6 are observations about the **tools**, not requirements for this feature. **None is in scope**
— F2 was taken in scope and then deferred at the Phase-1 gate. All six belong in
`docs/skill-monitoring.md` rows; filing them is a Phase 7 action, not a Phase 1 one.

F7 is evidence *for* the feature, but it is **suggestive rather than load-bearing**: n=1 per arm, one
model, one toy task, one wording. The brainstorm rests on the 7-of-177 measurement instead. What F7
usefully rules out is the narrow hypothesis that the instruction is ignored when present — which
would have argued for better wording rather than for wiring.

## Version History

- v1.0: Ledger opened at Phase 1 with F1–F6 from staging the A/B probe.
- v1.1: F7 added — the A/B probe returned `DIFFERENT`, inverting the seed's `SAME` hypothesis.
- v1.2: Phase-1 gate revisions. F2 moved out of scope (reversal recorded in place); F7's weight
  downgraded from load-bearing to suggestive, matching the brainstorm's softened reframe.
- v1.3: F8 added — no test sweeps the repository's own committed specs; found while
  reconsidering the Known Limit, and it moved the always-on half of the design into a
  suite test.
- v1.4: F9 added — every committed spec hardcodes a machine-specific absolute `root`, breaking
  Mechanism 1 off this machine and pointing worktree runs at the main checkout.
- v1.5: F10 added — identifier sweep exercised at Phase 3; 11 hits, all verified deliberate.
  Checkpoint table updated. Also recorded: `h_mad_doc_shape_check.py` returned its first real
  verdict of this feature (`PASS type=plan`) on the plan; brainstorm, spec and this ledger are
  `SKIP type=none` by design, so the plan is what exercised the checker's non-skip path.
- v1.6: F11 and F12 added — the audit-cycle `Effort:` block caught a double-clean hollow cycle on
  first live use, and a version-history bump recorded an unapplied fix.
- v1.7: F13 added — probing the plan against the domain invariants found an AC-2.5 vs
  self-containment conflict that four clean audit passes missed.
- v1.8: F14 added — FR-6 relaxes a guard without the differential corpus the base layer requires,
  and AC-6.1's classification rule is narrower than what `_load_spec` actually demands.
