## Summary

The plan covers all six functional requirements, but its verification narrative still contains reproducibility and consistency defects. Repository checks reproduced the 87-row mutation matrix, two extractor sites, and stamped ledger values; read-only permissions prevented writing the report file and `.done` marker.

Evidence: 14 files opened, 10 greps run.

| Requirement | Axis C classification | Coverage |
|---|---|---|
| FR-1 | implemented-as-written | Tagged extraction, selection, shared bounder |
| FR-2 | implemented-as-written | Literal substitution and refusal guards |
| FR-3 | implemented-as-written | Disposable cwd, shell modes, streams, preamble |
| FR-4 | implemented-as-written | Verdict grammar, exit partition, registry |
| FR-5 | implemented-as-written | Validated timeout and bounded process cleanup |
| FR-6 | implemented-as-written | Executing-consumer migration and wire discrimination |

## Must-fix

- The composite probe’s recorded runtime stamp is not produced by its published command — extracting and executing that heredoc prints the five comparison lines but no `python 3.11.8` line. The subsequent stamp accounting nevertheless treats that line as probe output. This breaches **Behavioural premises carry their command**: add an explicit version-printing command or distinguish separately collected metadata from reproduced stdout.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``Each of the five probes contributes **two**:``; ``table row and the `python 3.11.8` line inside its own recorded output``

## Should-fix

- The mutation-binding correction remains contradictory between Deliverables and Measurements — Deliverables correctly distinguishes the design’s intermediate draft from its shipped row, but Measurements still attributes the wrong killer to the shipped design. The actual row binds the CLI test. Apply the draft-versus-shipped distinction at both sites so reconciliation does not reopen a discharged debt.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `The killer is NOT the one the design shipped`
  quote: docs/02-design/features/doc-block-exec.design.md › ``| `test_cli_subst_overlap_detail_lines` (AC-4.1/4.3 — the subprocess test whose first leg runs the CLI``

- The verification-status register retains an expired exclusion — it covers only the renderer’s 4.2.0 leg because v1.104 ran 2.2.0, although its own rule requires re-entry at the next revision without a run. No v1.106 execution of that leg is recorded, and the register’s defining predicate still names v1.104 as “this one.” Restore the omitted leg with its last-execution stamp and align the predicate with v1.106.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``The markdown-it-py **14-case** grammar corpus, **its `4.2.0` leg only**``; `v1.104. **The predicate names one revision — this one — and never a span**`

- The ledger’s gap-growth claim contradicts its measured series — between `cac6edc` and `0021c77`, maximum cycle and file count each increase by one, leaving the gaps unchanged: codex `88−75 = 89−76 = 13`, teammate `88−16 = 89−17 = 72`. Describe growth conditionally; consecutive report arrivals do not widen either gap.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `forms widens by one on the codex half and by one on the teammate half at every report that lands,`

## Nit

- The batch-stamp paragraph says “two live stamps” immediately after enumerating six; use “all live stamps.”
- The heading-differential paragraph says “ONE FIELD MOVED ON EACH” but identifies two changed fields, `new_only` and `titleless`.
