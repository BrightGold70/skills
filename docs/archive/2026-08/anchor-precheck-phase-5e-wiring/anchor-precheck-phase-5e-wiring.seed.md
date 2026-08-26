# Seed — anchor-precheck-phase-5e-wiring

**Written:** 2026-08-26 · by the session that shipped the five tools (`351b4c7`..`920d204`)
**For:** a FRESH `/h-mad "anchor-precheck-phase-5e-wiring"` run
**Why a seed:** the writing session hit 62.3% of its context window against an 80% run ceiling.
A full cycle from Phase 1 could not have reached 5d/5e/6, which is where every tool this run
exists to exercise actually lives — so it would have halted at Phase 3/4 having dogfooded nothing.
This file carries the decisions so the fresh session spends its window on the cycle, not on
re-deriving them.

**This is not a spec.** Phase 1 (brainstorm) and Phase 2 (spec) still run normally and still need
user approval. Treat everything below as established context, not as approved requirements.

## The feature, in one line

`--check-anchors` is documented in `h-mad/SKILL.md` §Phase-5 and run by hand; **nothing in the
protocol obliges a run to invoke it.** A 5e that skips it still reports `MUTATION: ALL_CAUGHT`
over specs whose anchors have drifted — and a drifted anchor mutates nothing, so its run REFUSES
and the guard it aims at is unverified.

The wiring is what turns an advisory line into a step a run cannot silently skip.

## Why it is worth a cycle (measured, not asserted)

- **7 of 177 anchors across 14 committed specs had drifted** when the sweep was first run
  (2026-08-26). Every one of those guards was unverified while its spec still printed a
  verdict-shaped line.
- **Two of the seven were broken by a refactor made minutes earlier in the same session.**
- The precheck then caught the author's own drift **twice more the same day** — once during the
  task-slicer change, once during the census change — each time before the run could report
  `REFUSED`. That is three self-inflicted drifts in one day, by someone who knew the tool existed.

The recurrence is the argument: the failure is silent, self-inflicted, and frequent.

## Decisions already made — do not re-litigate

| Decision | Value | Evidence |
|---|---|---|
| Dispatch transport | **headless `hmad-dispatch exec`** for 5d/5e | `exec` is pane-independent per SKILL.md §6a-prime; codex CLI is on PATH (`/opt/homebrew/bin/codex`) with a live process |
| `PREFLIGHT: FAIL unresolved=codex` | **not a blocker** | it gates the PANE path only; `pin-agents` cannot resolve codex because it has no title identity by construction (H2/H5) |
| Codex model | `--model gpt-5.5` on every `exec codex` | the config default (`gpt-5.6-luna`) cannot execute tools and fails as a well-formed `STATUS: BLOCKED` |
| Interpreter | `/opt/anaconda3/bin/python3.11` | bare `python3` is 3.14 here and has no pytest; `h_mad_assemble_tdd.py` probes this for you |
| agy | pinned, `term_35383ed5-4485-4a38-a14a-8405409ac0d8` | `hmad-dispatch env` |

Bootstrap was verified clean at seed time: `INSTALL: PASS`, `WIRING: PASS`, no state record for
this feature (so the router returns `start_fresh`), no plan/design/impl-plan yet.

## The dogfood checkpoints — the reason this feature was chosen

Four of the five tools land at their natural phase point during this cycle. **Record what each
one does when it fires**; that observation is the deliverable of the dogfood, separate from the
feature itself.

| Phase | Tool | What to watch for |
|---|---|---|
| 5d | `h_mad_assemble_tdd.py` (task-slicer bound) | the last task of this feature's impl-plan must NOT carry `## Version History` or any trailing section into its prompt. That bound shipped `6c34e60`; this is its first live use. |
| 5e | `--check-anchors` | run it over all specs BEFORE the mutation run, which is exactly the step this feature is wiring in. It should be `ANCHORS_OK` unless the feature's own edits drift something — and if they do, that is the tool working. |
| 6 | `--gated <design> <plan>` | the gate writes a stamp only on PASS. First live use of `1c5d89e`. |
| 6→7 | `--verify-stamp` | read `GATESTAMP:` before Phase 7 closes. `STALE` means the edits that fixed the last cycle are themselves ungated. |

**Two tools have no phase home and need deliberate exercise:**

- `h_mad_identifier_sweep.py` — only fires after a rename/removal. If this feature renames nothing,
  run it against a past rename (`h-mad-advisor-gate.sh`) and record the result rather than
  skipping it. Note it is `LEFTOVERS` by design there: 9 hits, all deliberate explanations.
- `h_mad_ab_dispatch.py` — a probe tool, not a phase step. The honest exercise is the feature's own
  question: **does wiring the precheck into 5e change what a dispatched agent does?** Two prompts
  differing only in whether the 5e instruction names `--check-anchors`, observing whether the agent
  runs it. That is a real `UNCONTROLLED`/`SAME`/`DIFFERENT` question, and `SAME` would be a finding
  about this very feature.

## Open design question for Phase 1/2 to settle

**Where does the obligation live, and what is its failure mode?** At least three shapes exist and
they are not equivalent:

1. **Prose in SKILL.md 5e** — what exists today. Zero enforcement; this is the status quo the
   feature is trying to improve on.
2. **A step inside `h_mad_mutation_harness.py`** — have a normal run refuse, or warn, when its own
   spec's anchors were never swept. Self-contained, but it cannot see the OTHER specs, and the
   measured failure was a spec drifting because a DIFFERENT file was edited.
3. **A precondition in the audit-cycle / Phase-5 gate chain** — like `h_mad_wire_pin_gate.py` at
   5b. Sees all specs, matches how every other obligation here is made mechanical, and costs a new
   verdict token.

Note the house rule this must satisfy either way: a cannot-judge carries **no counts**, and the
verdict must be readable as a token rather than `$?`. `h_mad_new_gate.py` scaffolds exactly that
shape if option 3 wins.

## Resume

```bash
cd /Users/kimhawk/orca/skills
git checkout main
/h-mad "anchor-precheck-phase-5e-wiring"
```

The router will return `start_fresh` — claim the feature, then enter Phase 1.
