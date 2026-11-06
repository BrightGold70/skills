## Summary
The design assigns coverage to every acceptance criterion, but its Claude authorship fixture and unreadable-plan precedence contain build blockers. The table records proposed AC coverage, not successful execution; the review used source inspection and left the repository unchanged.

Evidence: 24 files opened, 19 greps run (one reported a missing file).

| Acceptance criteria | Axis C classification | Design coverage |
|---|---|---|
| AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 | implemented-as-written | FR-1/FR-2 parser design, Task 1, parser boundaries |
| AC-2.1, AC-2.2, AC-2.3, AC-2.4 | implemented-as-written | Wire-pin retirement, replacement tests and U1/U2 |
| AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 | implemented-as-written | Shared listing, connection mutants, alias/residual host cases |
| AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6 | implemented-as-written | D4, Task 3, judge verdict and import-shortcut tests |
| AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6, AC-5.7, AC-5.8 | implemented-as-written | Claude branch and per-host fixture/selection tests; authorship premise blocked below |
| AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5 | implemented-as-written | Codex five-step branch and host tests |
| AC-7.1, AC-7.2, AC-7.3, AC-7.4 | implemented-as-written | Agy branch and host tests |
| AC-8.1, AC-8.2, AC-8.3, AC-8.4 | implemented-as-written | Invalid-plan/state, absent-plan and doc/data controls; broader FR-8 conflict below |
| AC-9.1, AC-9.2, AC-9.3, AC-9.4, AC-9.5 | implemented-as-written | FR-9 fixture/replay driver, provenance and mutation run |
| AC-10.1, AC-10.2, AC-10.3 | implemented-as-written | Expanded prose sweep and updated documentation assertions |
| AC-11.1, AC-11.2, AC-11.3, AC-11.4, AC-11.5, AC-11.6 | implemented-as-written | Shared predicate, member/exclusion cases, mixed links and per-host suffix mutations |

## Must-fix
- `implementer=null` does not make Claude the author — the proposed Claude fixtures and replay can hit an authorship refusal instead of the required judge verdict. In the current `resolve_implementer`, null selects codex; an available agy is the next choice. Correct the shared spec/design fixture premise and explicitly arrange both peers unavailable for Claude judge cases, while keeping the available-peer authorship control separate. Verify the resulting state token before relying on AC-5.1/5.2/5.8, Claude connection/callee mutants, or the replay; changing existing author-selection behavior would violate the promised unchanged Python path.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `plus `"implementer": null` for the Claude host only (spec AC-5.1's author setting).`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `AC-5.1: With the test absent, a Claude `Write` to `R/scripts/tool.sh` (with `implementer=null` so Claude is the author) is DENY `kind=test-missing`.`
  quote: h-mad/scripts/h_mad_tdd_judge.py › `chosen = "agy" if record.implementer == "agy" else "codex"`

- Readable-plan precedence silently narrows FR-8 — the spec requires fail-closed behavior for an unreadable active impl-plan, but D4 permits judging from another readable plan. Knowing that some name is listed does not establish the required selected name: an unreadable sibling can conceal an earlier listed hard-link basename with different Task tests. The proposed rule can therefore ALLOW from the wrong Task. Require unreadable precedence on this new path and add a multi-record, mixed-readable/unreadable selection test, or obtain an explicit spec revision defining the alternative.
  class: build
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `A readable plan that lists the target outranks an unreadable sibling plan. In that state listing is decided, so FR-8's "cannot be decided" does not apply.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `An active record's impl-plan exists but raises `OSError` or `UnicodeDecodeError` on read.`

- Published behavioral probes lack their runnable commands — the canonicalisation scratch probe, Bash 3.2 line-splitting/array probes, and mutation-anchor census provide conclusions without complete reproducing commands and setup. This breaches “Behavioural premises carry their command”; the alias, transport and anchor premises cannot be independently re-derived from the document. Add the exact commands and observed outputs, preserving the distinction between historical evidence and new verification.
  class: measurement
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `I ran a scratch probe of `canonicalise` on an APFS scratch repo (deleted after the run).`

## Should-fix
- Refresh the source-version pointers and historical rationale — the design still identifies spec v1.5/plan v1.3, although the paired files now contain v1.7/v1.4 and already incorporate the shared-definition decision. Distinguish historical alternatives from the current source contracts so downstream implementers do not reopen a retired copy option.
  class: measurement
  quote: docs/02-design/features/gate-non-py-production-files.design.md › `The spec (v1.5) and the plan (v1.3) fix the rule.`
  quote: docs/01-plan/features/gate-non-py-production-files.spec.md › `v1.7: Corrects FR-9's replay-base text`
  quote: docs/01-plan/features/gate-non-py-production-files.plan.md › `v1.4: Corrections owed by spec v1.6`

## Nit
None
