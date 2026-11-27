AUDIT-phase5-gate-feature-scope-design-v1-BEGIN
## Summary

All 88 active acceptance criteria have identifiers in the boundary table. The design narrows several required cases, and the S5 callback, discovery error reporting, and mutation definitions need corrections before they can guide implementation.

Evidence: 18 files opened, 10 greps run.

| implemented-as-written | restated | absent |
|---|---|---|
| AC-1.1–1.9 | — | — |
| AC-2.1–2.11 | — | — |
| AC-3.1–3.2, AC-3.4, AC-3.6–3.7 | AC-3.3, AC-3.5 | — |
| AC-4.1–4.8, AC-4.10–4.16 | AC-4.9 | — |
| AC-5.1–5.6 | — | — |
| AC-6.1–6.5, AC-6.7–6.8 | AC-6.6 | — |
| AC-7.1–7.6 | — | — |
| AC-8.2–8.4 | AC-8.1 | — |
| AC-9.2–9.8 | AC-9.1 | — |
| AC-10.3–10.5 | AC-10.1–10.2, AC-10.6–10.7 | — |
| AC-11.1–11.6 | — | — |

## Must-fix

- AC-3.3 is restated by its test boundary. The exclusion removes the two-feature case that distinguishes checkout identity from feature identity. Keep feature A as the caller, make B live in A’s checkout, and assert gating on all five surfaces.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `brainstorm evidence table and spec FR-3 rules | none | same-checkout features`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `With B live and naming this same checkout, a session for A is still gated.`

- AC-3.5 is restated for an explicitly null command directory. The current codex `_command_cwd` and agy `Cwd` decoder use `.get()` and treat null like an omitted key. Once decoded, the shared rule cannot recover that distinction. Preserve key presence and test omission and explicit null separately on both hosts.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `The command directory is `_command_cwd` on codex and `Cwd` on agy; none given means the root.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `a non-string `workdir` or `Cwd`, one naming no directory, or one naming a directory for which git cannot answer, makes every live record apply.`

- AC-4.9 is restated for ordinary production writes. An unparsable sibling file makes the proposed write status unknown even when the target’s chain is readable. In the current codex production branch, `judge.read_chain(root, absolute)` decides that write. Specify separate outcomes for ordinary chain judgement and FR-6 protection. Move the same unparsable file onto and off the chain and assert the baseline decision in each position.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `an unreadable file of either is `unknown`.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `an unreadable, unparsable, non-regular or wrongly shaped discovered file gives the same refusal as before this feature on every surface that consults it.`

- AC-6.6 is restated for absent neighbouring documents. A numeric directory name is identical to its case-swapped spelling on a case-sensitive volume. Its identity therefore cannot establish that two differently cased absent children denote one file. Require a genuinely distinct spelling on the relevant filesystem and test an absent referent beside its case-only neighbour on the case-sensitive fixture.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `folded when the nearest existing ancestor's filesystem resolves a case-swapped spelling of that ancestor to the same file.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Other documents and data files keep their present decision while a record applies.`

- AC-8.1 is restated by excluding shell commands governed by the safe list. A normally refused command can yield the same observation under both unreadable-state policies. Include a normally admitted command on both real shells and compare the outcomes with and without the unreadable file for each specified record combination.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `spec FR-8 grammar; decisions observed from the real hooks | none | shells gated by the safe list`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `and otherwise give each command the decision it gets with the unreadable file removed.`

- AC-9.1 is restated by its boundary. The stage-specific row covers two hosts and leaves out Claude’s production-write decision before the mark. Exercise that write with a live planning record in the named checkout alongside the codex and agy cases.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `codex and agy hooks at both stages`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `a production write through each write surface is refused.`

- AC-10.1 is restated by the arming-command recognizer. A read-only text search can contain a complete writer example as a quoted argument. Re-parsing that data as a command produces a new refusal although no writer runs. Distinguish invocation positions from inert operands and keep a literal-search control beside direct and wrapped writer cases.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `A token holding several words is split and examined the same way.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Every difference is in D1 to D7, each class has at least one difference under at least one of them, and no other allow or refuse changes.`

- AC-10.2 is restated by excluding records with the new fields from the incident replay. Replay the same captured state shape twice, add the main checkout on the second run, and check both checkouts. A separate synthetic scoped fixture cannot establish the second half of the incident replay.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `the plan's oracle, itself checked on typed verdicts; sanitised state shapes | none | records with the new fields`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `once it names the main checkout, the second checkout is not gated and the first still is.`

- AC-10.6 is restated as a writer-only observation. Re-reading a repaired record proves which keys the older writer removed. The criterion also requires running all five surfaces against that resulting store and observing shell enforcement.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `spec FR-10 mixed-writer statements, stores re-read | none | fast-forward mixtures (plan's corpora)`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `After `--drop-undeclared` on a live record, all five surfaces treat it as AC-4.1 and the shell is gated.`

- AC-10.7 is restated by the discovery interface. A failed lane listing and a readable empty directory can both yield an empty path tuple. Give the landing probe the traversal error while preserving the hook’s existing handling. Test a successfully enumerated empty lane and a lane whose directory listing fails, and require different summary tokens.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `A directory is listed with `os.scandir`; a listing error yields no children.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `never prints `NONE` when the listing was incomplete or a lane or file could not be read`

- S5 passes a zero-argument method to a one-argument callback. Section 5 declares `unscoped()`, while §7 calls `judged(spelling)`. As specified, invoking the bound method raises `TypeError` before the hook can distinguish a protected path from an ordinary document. Give both stages one callback signature and exercise the S5 path through each hook.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › ``judged` is the status function for a spelling: `scan.unscoped` in S5, `scan.write` from the scoping step of the surface.`

- S5’s unscoped status has already lost records. Returning every live record in the new, filtered scan cannot recover a record omitted by FR-2. This changes which records arm the S5 protection and makes an inline unscoped mutant insensitive to the excluded-tree control. Source S5’s status from the old discovery and mutate discovery separately from applicability.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › ``unscoped()`: every live record.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `Arming-input protection on every surface, from the session root and from the target's own checkout, under today's arming (every live record)`

- The row 3 reverse mutant has the wrong type and scope. `INACTIVE` is a nonempty status tuple. Substituting it for a Boolean `stage=True` leaves a truth test enabled. Replacing the entire shell result instead also changes session and directory applicability. Specify a stage-only mutant that suppresses an implementing record and require its opposite-stage control to detect it. Row 9 inherits this defect.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › ``stage=True` (S8: `False`) | `stage=False` | `INACTIVE``

- Row 18 assigns the unreadable-root mutants backwards. Its reverse forces the permissive answer, which agrees with the inactive control. That control cannot kill it as claimed. Set removal and reverse separately for the protection IDs and record the active and inactive hook verdict that kills each.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `The unreadable-root ids of rows 14, 15, 17 and 18 are protection, so their reverse is caught by the `[inactive]` part.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `removal by a case that must be refused; reverse by an ordinary case that must be admitted, staged or written`

- The design’s performance conclusion exceeds its measurement. The recorded command times the canonicalisation process on a document. It cannot establish the complete hook median for production and state-file writes, or the no-live process count for those targets. Supply the plan’s per-target readings on both bounded repositories and distinguish the existing prototype timings from them.
  class: measurement
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `medians of 21 interleaved runs at `b29173f1`, document target`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `at most 300 ms added to the median of a Claude hook call on a document, a production and a state-file target`

- The design’s discovery and fail-closed readings lack a runnable command at the audited revision. The prescribed probes directory does not exist at `b29173f1`, and the future subcommand names do not supply the measured scripts or fixtures. Make the exact measurement source and fixture-building invocation available to the reviewer, or identify these as unverified readings until they can be rerun.
  class: measurement
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `Observed at `b29173f1`, git 2.54.0, in scratch repositories (script in `discovery_probe.py`, which S0 commits):`

- The stage predicate has no shared call site in the assembler design. `Scan.shell` tests the stage and §10 prescribes the same comparison for a staging halt. Row 21 mutates the halt condition but never establishes a connection to the shared predicate. Name that predicate and test each caller, or verify equivalent results across the two consumers for every supported stage value.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `only otherwise does a record at `"planning"` give `phase5_stage_planning`.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `One implementation of discovery, applicability, stage and arming-input rules`

## Should-fix

- Keep the writer’s CLI diagnostics when extracting its parser. Today argparse prints help and distinguishes a successful help request from a usage error. A silent `None` for both outcomes is sufficient for the shell classifier but loses information needed by `main`. Pin stdout, stderr and status through the writer CLI.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › ``parse_invocation(argv)`, which returns None when argparse exits and prints nothing. `main` uses the same three.`

## Nit

None
AUDIT-phase5-gate-feature-scope-design-v1-END
