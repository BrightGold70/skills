AUDIT-phase5-gate-feature-scope-design-v2-BEGIN

## Summary

All 88 active acceptance criteria occur in Test Boundaries. The identifier review found three divergences in the specified decisions, plus defects in the wiring tests, discovery deadline and landing evidence.

Evidence: 22 files opened, 10 greps run.

| Spec identifiers, inclusive ranges | Axis C classification |
|---|---|
| AC-1.1–1.9, AC-2.1–2.11 | implemented-as-written |
| AC-3.1–3.4, AC-3.6–3.7, AC-4.1–4.16, AC-5.1–5.6 | implemented-as-written |
| AC-3.5 | restated |
| AC-6.1–6.5, AC-6.7–6.8, AC-7.1–7.6 | implemented-as-written |
| AC-6.6 | restated |
| AC-8.1 | restated |
| AC-8.2–8.4, AC-9.1–9.8, AC-10.1–10.7, AC-11.1–11.6 | implemented-as-written |

## Must-fix

- AC-3.5 loses known command directories — §5 calls the decoder with zero arguments and specifies passing Codex’s `_command_cwd`, which requires the payload. Its resulting `TypeError` selects the malformed-directory sentinel even for a valid explicit directory. Bind the payload in the adapter and supply an absolute string when the absent-field default is the hook’s `Path` root. Assert both the refusal in the named checkout and admission in a known, unrelated checkout through the real hook.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `One naming a directory in no work tree (Definitions) is judged on rules 1 to 3.`
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `when `decode` raises; `decode()` for a non-empty string`
  quote: h-mad/hooks/h-mad-codex-tdd-gate.py › `def _command_cwd(payload: dict[str, Any]) -> object:`

- AC-6.6 narrows admission of ordinary documents on a case-sensitive filesystem — two separately listed, case-distinct hard links can share an inode. That observation does not establish that the directory folds case for a different, absent name. The fallback also equates absent spellings when the mounted filesystem supplies no cased entry. Require a discriminator that distinguishes the two directory entries from a single entry with two spellings, and specify the baseline decision for the inconclusive case. Exercise both with an ordinary absent document.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Other documents and data files keep their present decision while a record applies.`
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `found to be the same device and inode (the filesystem folds) or not (it does not)`

- [redacted: private, operator record] (AC-8.1)
  class: build

- Row 17 cannot kill its “keep every live record” filter mutant — the input chain has already discarded the only `other-checkout` record. The downstream filter cannot recover it, whatever the fixture’s plan lists. Give the listing decision access to the unfiltered applicability results, or move the mutation and its assertion to the boundary that still holds both records. Keep the public `listed` and `not-listed` observations.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `else `active` with the records that apply to the session or the target, else `none`.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `removal keeps every live record (`other-checkout` gives `listed` in place of `not-listed`)`
  quote: h-mad/scripts/h_mad_tdd_judge.py › `result = listing(root, names, chain.records)`

- Mutation A supplies the wrong element type — `scan.records` contains `LiveRecord` values, while refusal formatting consumes `Applied` values with a reason. A hook can consequently return its exception refusal under the mutant and appear to kill it. Construct valid applying entries with reasons, preserve the stage predicate where only applicability is being mutated, and require the intended refusal kind and record in the killing test.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `Status("active", scan.records) if scan.records else`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `every new mutation spec reports all caught, with no crash-only kills`

- Row 9 promises three independently mutable stage connections but §8 computes one shell status before branching — mutating the shared argument changes command, missing-command and workspace-mismatch cases together. Pin that shared calculation once and mutate each branch’s consumption separately, or specify three actual call sites and their individual controls.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `The shell status is computed before the workspace check`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The stage mutants are row 3's, in each of the three places`

- S1 does not prove its new delegation points — restoring the old inline parser, key extraction, executable resolution or wrapper predicate at a caller leaves the baseline-equivalence tests green. The helpers can also retain exactly one definition while the caller ignores them. Add connection-only mutations and observations for the writer CLI and the safe-command decision, keeping each helper available during its caller’s test.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `the writer's three of §6 among them with `main` behaving as before, and `_safe_executable` and `_is_bounded_run`, which `_safe_argv` calls from then on with every decision as before`
  quote: h-mad/invariants.base.md › `alone is removed and the callee is left intact`

- The streaming Git process has no two-second elapsed-time bound — between exchanges it remains alive while Python lists directories and while other Git calls run. A sum of pipe waits can stay below two seconds throughout a much longer process lifetime. Specify one monotonic deadline from launch, including cleanup, or obtain a spec change for an I/O-wait budget. Test elapsed lifetime with prompt Git replies and a delayed traversal.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `The 2 s budget of the streaming process is the sum of its waits.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Every git call this feature adds is bounded (2 s, the bound agy's root lookup already uses)`

- The landing probe passes the record wrapper to a dictionary consumer — the existing liveness reader silently replaces a non-dictionary with an empty dictionary. A live record can therefore lose its owner and heartbeat evidence while the probe still prints a well-formed line. Pass the stored record data and assert the heartbeat evidence in the real CLI output with the other clocks controlled.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `The liveness column is `liveness_evidence(record, lane)`.`
  quote: h-mad/scripts/h_mad_state_ownership.py › `record = record if isinstance(record, dict) else {}`

- The assembler Test Boundaries row mocks the internal wiring check — the assembler launches its sibling checker with the current interpreter and a specific script path. A PATH stub alone does not supply the scratch project’s wiring configuration, so review can halt before it reaches either new condition. Provide a valid scratch wiring configuration, exercise the real checker and require the exact staging reason and unchanged prompt and stamp for each phase.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `agy wiring check by PATH stub`
  quote: h-mad/scripts/h_mad_assemble_tdd.py › `[sys.executable, AGY_WIRING_CHECK, "--agy", "--project-root", str(args.project_root)]`
  quote: h-mad/scripts/h_mad_hook_wiring.py › `path = project_root / ".agents" / "hooks.json"`

- The design’s prototype readings cannot be re-derived at this gate — the named probe directory is absent in the reviewed tree. For example, the command for the 38-case stub comparison depends on an unavailable script. Include the runnable probe text or an accessible, pinned artifact with its invocation for the readings used to choose the design. The scheduled S6 and S11 whole-hook measurements are separate.
  class: measurement
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `made by hand or with scripts that are not in the repository`
  quote: h-mad/invariants.base.md › `MUST carry the exact command that produced it`

## Should-fix

- Define what the S5 walk-count assertion counts — the Python hooks reuse one unfiltered walk for the legacy status but also perform a filtered discovery. Count each traversal separately in S5 and assert the single session discovery from S8, so the test can distinguish reuse from accidentally omitting one input.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `S5 to S7 call `phase5_scan` beside it, so no earlier commit scopes a shell.`

- Define how a mid-scan Git failure affects directories already pruned — the plan counts the failed batch, whereas the design can be read to invalidate the entire scan. Those choices return different file sets after an earlier successful exclusion. Specify whether completed answers stand and assert the exact returned paths after a later exchange fails.
  class: build
  quote: docs/02-design/features/phase5-gate-feature-scope.design.md › `the walk goes on unpruned and each candidate counts.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `A git error for a batch counts every candidate in it.`

## Nit

None

AUDIT-phase5-gate-feature-scope-design-v2-END
