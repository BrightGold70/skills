AUDIT-grok-audit-surface-design-v1-BEGIN
## Summary

Design v1.0 has blocking contract inconsistencies and missing outcome requirements despite preserving the existing wrapper and gate behavior. All 51 acceptance criteria were reconciled, three targeted wrapper tests passed, and the repository remained unchanged.

Evidence: 12 files opened, 10 greps run.

Validation: targeted wrapper tests passed (3 tests); pytest’s process-leak check was skipped because the sandbox denied `ps`. OneContext history was unavailable in this environment.

| Acceptance criterion | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | restated |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | restated |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | restated |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | restated |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | restated |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | restated |
| AC-4.4 | implemented-as-written |
| AC-4.5 | restated |
| AC-5.1 | restated |
| AC-5.2 | implemented-as-written |
| AC-5.3 | restated |
| AC-5.4 | restated |
| AC-5.5 | implemented-as-written |
| AC-6.1 | absent |
| AC-6.2 | implemented-as-written |
| AC-6.2a | implemented-as-written |
| AC-6.3 | restated |
| AC-6.4 | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-7.2 | absent |
| AC-7.3 | implemented-as-written |
| AC-7.4 | implemented-as-written |
| AC-8.1 | implemented-as-written |
| AC-8.2 | implemented-as-written |
| AC-8.3 | implemented-as-written |
| AC-9.1 | implemented-as-written |
| AC-9.2 | implemented-as-written |
| AC-9.3 | implemented-as-written |
| AC-9.4 | implemented-as-written |
| AC-9.5 | implemented-as-written |
| AC-10.1 | implemented-as-written |
| AC-10.2 | implemented-as-written |
| AC-10.3 | implemented-as-written |

## Must-fix

- AC-1.3 — restated: D11 narrows non-`none` delivery plus a scored report to `report-file` delivery only. The existing collector writes a full collected report for `delivered=out`; running the gate on that file is more than reading a final-message verdict alone. Either accept that case or land the stricter transport requirement in the spec before implementation.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``Report delivery is shown by `COLLECT: OK`, or by a non-`none` `delivered=` field on the `AUDITCYCLE:` line, together with a `GATE:` token scored from the report file.``
  quote: docs/02-design/features/grok-audit-surface.design.md › ```no_delivery`: the grok pass's `delivered=` field is not `report-file`, or its `GATE:` token is neither `PASS` nor `FAIL`.``

- AC-1.6 — restated: root acceptance inherits the narrower D11 delivery predicate. A non-UNVERIFIED cycle with an extracted, collected and gate-scored report can therefore be called a root refusal, potentially dropping codex or failing the smoke despite satisfying the spec’s acceptance predicate. Reconcile this independently with AC-1.6.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``A surface **accepts** the root when its pass delivers a report (the AC-1.3 evidence) AND the cycle's `AUDITCYCLE:` is not `UNVERIFIED```
  quote: docs/02-design/features/grok-audit-surface.design.md › ``the surface has no delivery evidence by the rule above, or its verdict word is `UNVERIFIED`.``

- AC-2.2 — restated: D4 checks the omitted class, document sizes and global totals, but omits one-of-each validation within each document. An in-memory counterexample changes d1 to C2,C2,C4 and d4 to C1,C3,C3: all nine document sizes, all omitted classes and totals 6/7/7/7 remain valid. Require each document’s class multiset to equal its three-class complement, and test this balanced counterexample.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``Document k omits class `((k−1) mod 4) + 1` and carries one seed of each of the other three.``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``The ledger must hold exactly 3 seeds per document for all 9 documents, document `d<k>` must omit class `((k−1) mod 4)+1`, and the totals must come out as derived from that rule``

- AC-2.7 — restated: the main leak check exists only inside `rescore`, whose interface and algorithm require a score sha. Smoke failure explicitly produces no score sha, leaving no executable path for the required calibration-sha-only main leak check before publishing that outcome. Add that path and synthetic coverage for its three triggers.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `the blob's sha256 equals that of a calibration data file at the score sha, or at the calibration sha when there is no score sha`
  quote: docs/02-design/features/grok-audit-surface.design.md › ```rescore --repo . --calibration-sha <sha40> --score-sha <sha40> [--remote origin]```

- AC-3.6 — restated: D9 specifies sha/ref citations and D10 mentions the grok smoke’s model line, but no design step captures all three agent versions and each surface’s resolved-model line for publication. Specify the commands, retained outputs and measurement fields; a pointer to FR-6 does not define this missing provenance.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``the grok, agy and codex versions, and each surface's `RESOLVED-MODEL` line are recorded once in the measurement doc.``
  quote: docs/02-design/features/grok-audit-surface.design.md › ``the AC-1.4 `RESOLVED-MODEL` line (published only)``

- AC-4.3 — restated: D13 enumerates missing/invalid labels but never rejects multiple label records for one id. Two individually valid records, such as REAL and FABRICATED for the same finding, satisfy the listed checks while violating exactly-one labeling and making scoring order-dependent. Require unique label ids and test both identical and conflicting duplicates.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `Each must-fix gets exactly one label:`
  quote: docs/02-design/features/grok-audit-surface.design.md › ```label:<id>` fires on a finding with no label, a label for an unknown id, a value outside `HIT:<seed-id> REAL FABRICATED UNDECIDABLE```

- AC-4.5 — restated: D12 extracts only Must-fix findings and D13 reports only those results. There is no extraction, labeling or publication route for observational Should-fix hits. Add a separate path that publishes them while excluding them from recall and D3, or amend the spec explicitly.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `Should-fix hits are published separately and never enter the bar.`
  quote: docs/02-design/features/grok-audit-surface.design.md › ``for each scored report, the `## Must-fix` section's content lines go through `h_mad_audit_gate._bullet_groups`.``

- AC-5.1 — restated: unexpected operational failures may exit without any token. This contradicts the promised final-token interface and prevents token-only callers from recognizing UNREADABLE. Define mappings for expected I/O/parsing failures, or obtain a spec amendment for the no-token branch; retain the smoke-specific error grammar when appropriate.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``The probe ends on one token line: `SEEDSCORE: PASS|MISS|INCONCLUSIVE|UNREADABLE`, with `reason=` on every verdict other than PASS.``
  quote: docs/02-design/features/grok-audit-surface.design.md › `otherwise prints a Python traceback on stderr and exits 2 with **no** token`

- AC-5.3 — restated: D13 fixes an unstated precedence by making seeds_undetected outrank an otherwise valid D3 PASS. For example, zero hits with strictly lower grok fabrication satisfies the spec’s PASS predicate and its no-seeds INCONCLUSIVE clause simultaneously. The design’s resolution is defensible, but its own owed-to-spec note must be closed with an explicit precedence amendment.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `**PASS**: D3 holds when every one of grok's UNDECIDABLE is counted as fabricated and every one of agy's is counted as not fabricated.` ; `The second applies when no surface, codex included, hit any seed, which means the seeds measure nothing.`
  quote: docs/02-design/features/grok-audit-surface.design.md › `*Owed to the spec:* make that precedence explicit.`

- AC-5.4 — restated: D12 explicitly expands `cycle_token` beyond absent/unparseable recorded AUDITCYCLE lines to unexpected cycles, invalid commands and missing delivered reports. D4 likewise expands `seed_rebuild` to placement violations. These may be sensible checks, but the closed failure contract must be amended before the design gate clears, rather than left as an item owed to the spec.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ```cycle_token:<cycle>` (AC-3.2): the cycle has no recorded `AUDITCYCLE:` line at the score sha, or its recorded line does not parse as an `AUDITCYCLE:` token.``
  quote: docs/02-design/features/grok-audit-surface.design.md › `*Owed to the spec:* AC-5.4 names only "no recorded line" and "does not parse".`

- AC-6.1 — absent: the design does not state that the measurement document will publish the build-class/four-class transfer limit and that real-defect recall is unmeasured. The component table’s FR-6 reference supplies no content or acceptance check. Add the required residual to the S3 document contract.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `The doc states the transfer residual: seeds are build-class shapes from the four classes in AC-2.1, and the doc says whether a real-defect recall would match is not measured.`
  quote: docs/02-design/features/grok-audit-surface.design.md › ``| Measurement doc | `docs/03-analysis/grok-audit-surface.measurement.md` | new (S3) | FR-6 plus the runbook (D8) |``

- AC-6.3 — restated: D14 gives the same fractions-and-pointer replacement to all scored outcomes but omits the INCONCLUSIVE explanation and reason required in SKILL.md. Add an explicit outcome branch and assertion for each INCONCLUSIVE reason; retaining fallback routing alone does not satisfy the text requirement.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `On INCONCLUSIVE the text says the bar was not decidable on this set, gives the reason, and grok stays fallback-only.`
  quote: docs/02-design/features/grok-audit-surface.design.md › ``It is replaced by the measured fractions and the pointer `docs/03-analysis/grok-audit-surface.measurement.md`, while `unmeasured` stays for GREEN, mutation and wiring.``

- AC-7.2 — absent: the PASS text/test work enumerates AC-7.1, AC-7.3 and AC-8.3 but omits availability fallback. Specify both missing-grok fallback and fallback after the same grok pass is UNVERIFIED twice, using `codex,agy` and the actual legs in stamps.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``If `command -v grok` fails, the first gate runs `--passes 2 --surfaces codex,agy`.`` ; ``The same applies when the grok pass is the `pN` named in an `UNVERIFIED reason=…:pN` on both the first run and its one re-dispatch: the cycle is then re-run as `codex,agy`.``
  quote: docs/02-design/features/grok-audit-surface.design.md › `**AC-7.1, 7.3 and 8.3 (S4, PASS only)** are as the spec states.`

- Operational refusal tokens contradict one another — D1 requires SEEDSCORE for every non-smoke refusal, whereas D9 and Error Handling require COMMIT/RECORD refusals. An implementer cannot meet both interfaces. Choose one grammar per mode, reconcile the advertised closed reason set, and pin the exact stdout token in subprocess tests.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``Every refusal in every mode except `smoke` prints `SEEDSCORE: UNREADABLE reason=<r>``` ; ``**Operational modes** refuse with their own tokens: `RECORD:` refuses as `cycle_token:<cycle-id>```

- The smoke ordering fixture is unsatisfiable — D11 makes every grok `no_delivery` also imply `nongit_root_refused:grok`. Executing those predicates gives `truncated,no_delivery,nongit_root_refused:grok`, never the promised two-reason result. Correct that assertion and explicitly reconcile the spec’s impossible demand for a no-delivery-only fixture without dropping the acceptance predicate.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ```test_smoke_two_reasons_in_order` (`truncated,no_delivery`)`` ; ``the surface has no delivery evidence by the rule above, or its verdict word is `UNVERIFIED`.``
  quote: docs/01-plan/features/grok-audit-surface.spec.md › ``Each of the two UNREADABLE reasons, `PASS`, and each `FAIL` reason gets its own fixture test, run with that trigger alone.``

- M4’s opposed-input fixtures validate the wrong authority — delivery is decided by `collect`, while the prescribed authority check invokes the gate. A GATE verdict cannot establish whether the raw inputs produce `none`, `out` or `report-file`, so it cannot prove the two required opposing delivery shapes. Drive the real collector for both directions and separately verify the gate result.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``| M4 AC-1.3 and AC-3.4 delivery | `h_mad_audit_cycle.collect` |`` ; ``and `h_mad_audit_gate.py` for M4.``

- The persisted key can silently reassign findings to another surface — D13 validates only id sets and `(report,text)`. In-memory execution confirms that changing a key row’s surface from grok to agy leaves both checks unchanged. Validate doc/cycle/pass/surface against the authoritative cycle and command mapping, and reject duplicate ids; otherwise a corrupted key can change the promotion verdict while passing re-extraction.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``the multiset of `(report, text)` that the findings joined with the key give`` ; ``**Pass → surface** is read from `command.txt`'s `--surfaces` list by pass index``

- Root provenance has no declared recording input — D5 promises that record-cycle appends the exact ROOT line, including calibration/list commit and list blob, but D2 supplies only root/stem paths and the wrapper’s stdout/command. D5 does not persist a root manifest, and the wrapper capture contains no ROOT line. Add a retained root-record input or an explicit manifest and verify its association with the dispatched root.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ```record-cycle` appends the S1 and S2 root lines to `roots.jsonl` on the branch.`` ; ```record-cycle --stem <dir> --root <dir> --stdout <file> --command <file> --dest <dir>```

- The classify connection is not discrimination-tested — the only mismatch fixture injects a counter directly into the helper. It does not exercise the production call that obtains the counter from `classify`; removing that connection while leaving the helper intact need not fail it. Add a test through the production extraction/scoring path and mutate the classify-to-extractor connection in both directions, as required by Connection enforcement.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``covered by the import itself, plus the `must_count_mismatch:<report>` fixture`` ; ```extract_findings(text, *, must_count=<classify's must_count>)```

- FR-6’s observational breakdowns have no producer or publication contract — D13 emits totals per surface only; the design never specifies the required per-phase and per-class results. Define these outputs and tests that prove they are observational and cannot move D3.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `the observational per-phase and per-class split`
  quote: docs/02-design/features/grok-audit-surface.design.md › ``Each surface prints `SURFACE: <s> recall=<hits>/27 musts=<n> fabricated=<f> undecidable=<u> fab_rate=<f>/<n−u> delivered=<counts> low_evidence=<count>`.``

## Should-fix

- The P-row census counts sites rather than rows — the listed 32 marker sites expand to 35 rows because the missing-vocabulary site gets three rows and the nongit site two. Derive the reported row count from the generated mutation list, and keep marker-site count as a separate unit.
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › `Each gets one row per alternative fixture (three and two)` ; ``The final P-row count is derived by Phase 5e from the probe's markers (`grep -c 'M:GAS-'` over the probe)``

- Pin ledger/seeded-copy identity across the two shas — the drift check permits all changes inside calibration/, while score reads the score-sha ledger and rebuilt dispatch roots use the calibration-sha ledger. Two independently rebuildable ledgers could therefore describe different seeds. Compare the ledger and seeded blobs across those commits, or make their immutability an explicit validated precondition.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › ``the first path not under the calibration directory refuses `calibration_drift:<path>`.`` ; ```check-ledger` on the export; `build-root --purpose rescore` for `d1`…`d9` from the calibration sha``

## Nit

- The Overview says every live root serves exactly one cycle, but D5 deliberately shares the S1 root across its three cycles. Scope the Overview’s statement to S2.

🌱 graft saved ~179,328 tokens (~$0.13) this turn, 7 calls.
AUDIT-grok-audit-surface-design-v1-END
